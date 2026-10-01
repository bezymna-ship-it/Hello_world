"""Weaver Bridge gateway.

Joins several local MCP servers (Cinema 4D, Houdini, Fusion, Nuke, Weaver ...) into one
Streamable HTTP MCP endpoint, so one custom connector in claude.ai reaches all of them
through a tunnel.

    python gateway.py --config C:\\weaver_bridge\\servers.json --secrets C:\\weaver_bridge\\secrets.json
                      --control <vault>\\Studio_bridge\\weaver_bridge\\control.json

Two kinds of downstream server (key "type" in servers.json):
  "stdio" (default)  a program the gateway starts itself: {"command", "args", "cwd", "env", "timeout"}
  "http"             a server that already runs, e.g. the MCP server built into Cinema 4D 2026.4:
                     {"url": "http://127.0.0.1:5556/mcp", "bearer_secret": "c4d26_bearer", "timeout"}
                     "bearer_secret" names a key in secrets.json; the token never sits in servers.json.

The endpoint is http://HOST:PORT/<token>/mcp (token from secrets.json "gateway_token"); the random
path is the only protection once it is exposed through a tunnel, so keep the URL private.

Tools are re-exported with a prefix (c4d__..., c4d26__..., houdini__...), plus built-ins:
  bridge_status   what is connected, and the autostart switches
  bridge_control  watchdog mode (off / crash / keep) and which programs it watches

The last tool list of every server is cached on disk, so the tools stay visible in claude.ai while
a program is closed (a call then answers "not running yet" instead of the tool disappearing).
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import anyio
import mcp.types as types
import uvicorn
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from mcp.shared.exceptions import McpError

SEP = "__"
log = logging.getLogger("weaver-bridge")


class Downstream:
    """One MCP server, kept alive by its own supervisor task.

    The transport/session contexts are entered and exited inside `run()` only, which keeps
    anyio's cancel scopes in a single task. Request handlers use `self.session` and call
    `restart()` if it breaks.
    """

    def __init__(self, name: str, spec: dict[str, Any], base_dir: Path, secrets: dict[str, Any], state_dir: Path):
        self.name = name
        self.kind = spec.get("type", "stdio")
        self.timeout = float(spec.get("timeout", 120))
        self.label = spec.get("label", name)
        # http servers belong to a program the user opens and closes: retry often and quietly
        self.max_delay = float(spec.get("retry_max_s", 15 if self.kind == "http" else 60))
        self.log_path = base_dir / "logs" / f"{name}.log"
        self.cache_path = state_dir / f"tools_{name}.json"
        if self.kind == "http":
            self.url = spec["url"]
            self.headers = dict(spec.get("headers", {}))
            secret = spec.get("bearer_secret")
            if secret:
                value = secrets.get(secret)
                if value:
                    self.headers["Authorization"] = f"Bearer {value}"
                else:
                    log.warning("[%s] secret %r is empty in secrets.json", name, secret)
        else:
            cwd = spec.get("cwd")
            if cwd and not Path(cwd).is_absolute():
                cwd = str((base_dir / cwd).resolve())
            self.params = StdioServerParameters(
                command=spec["command"],
                args=list(spec.get("args", [])),
                env={**os.environ, **{k: str(v) for k, v in spec.get("env", {}).items()}},
                cwd=cwd,
            )
        self.session: ClientSession | None = None
        self.last_error: str | None = None
        self.down_since: float | None = time.time()
        self._ready = anyio.Event()
        self._restart = anyio.Event()
        self._cached: list[types.Tool] = self._load_cache()

    # ---- tool cache -------------------------------------------------------------------
    def _load_cache(self) -> list[types.Tool]:
        try:
            raw = json.loads(self.cache_path.read_text(encoding="utf-8"))
            return [types.Tool.model_validate(t) for t in raw]
        except Exception:  # noqa: BLE001 - no cache yet or an old format
            return []

    def _save_cache(self, tools: list[types.Tool]) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            data = [t.model_dump(mode="json", exclude_none=True) for t in tools]
            tmp = self.cache_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, self.cache_path)
        except Exception as exc:  # noqa: BLE001
            log.warning("[%s] tool cache not saved: %s", self.name, exc)

    # ---- connection supervisor ----------------------------------------------------------
    @contextlib.asynccontextmanager
    async def _transport(self, errlog):
        if self.kind == "http":
            async with streamablehttp_client(self.url, headers=self.headers or None,
                                             timeout=15, sse_read_timeout=self.timeout + 60) as (read, write, _):
                yield read, write
        else:
            async with stdio_client(self.params, errlog=errlog) as (read, write):
                yield read, write

    async def run(self) -> None:
        delay = 2.0
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            errlog = open(self.log_path, "a", encoding="utf-8", errors="replace")  # the server's stderr
            try:
                async with self._transport(errlog) as (read, write):
                    async with ClientSession(read, write) as session:
                        with anyio.fail_after(30):
                            await session.initialize()
                        self.session, self.last_error, self.down_since = session, None, None
                        delay = 2.0
                        log.info("[%s] connected", self.name)
                        self._ready.set()
                        tools = await self._fetch_tools(session)
                        if tools:
                            self._cached = tools
                            self._save_cache(tools)
                        await self._restart.wait()
            except Exception as exc:  # noqa: BLE001 - keep supervising whatever happens
                err = _root_cause(exc)
                if err != self.last_error:
                    log.warning("[%s] down: %s", self.name, err)
                self.last_error = err
                self._ready.set()  # wake waiters so they see the error instead of hanging
            errlog.close()
            self.session = None
            self.down_since = self.down_since or time.time()
            self._restart = anyio.Event()
            self._ready = anyio.Event()
            await anyio.sleep(delay)
            delay = min(delay * 2, self.max_delay)

    async def _fetch_tools(self, session: ClientSession, timeout: float = 30) -> list[types.Tool]:
        try:
            with anyio.fail_after(timeout):
                return (await session.list_tools()).tools
        except Exception as exc:  # noqa: BLE001 - a dead program: reconnect in the background
            log.warning("[%s] list_tools failed: %s", self.name, _root_cause(exc) or "timeout")
            if session is self.session:
                self.last_error = f"list_tools: {_root_cause(exc)}"
                self.restart()
            return []

    def restart(self) -> None:
        self.session = None
        self._restart.set()

    async def get_session(self, wait: float = 15) -> ClientSession | None:
        if self.session is None and self.last_error is not None:
            return None  # known to be down: don't stall the request, the supervisor keeps retrying
        with anyio.move_on_after(wait):
            await self._ready.wait()
        return self.session

    async def list_tools(self) -> list[types.Tool]:
        session = await self.get_session()
        if session is None:
            return self._cached
        tools = await self._fetch_tools(session, timeout=8)  # claude.ai waits for the whole list
        if tools:
            if [t.name for t in tools] != [t.name for t in self._cached]:
                self._save_cache(tools)
            self._cached = tools
            return tools
        return self._cached

    async def call_tool(self, tool: str, arguments: dict[str, Any]) -> types.CallToolResult:
        session = await self.get_session()
        if session is None:
            return _error(f"{self.label} is not connected right now ({self.last_error}). "
                          "If the watchdog is on it starts the program by itself: check bridge_status "
                          "in a minute and retry.")
        try:
            with anyio.fail_after(self.timeout):
                return await session.call_tool(tool, arguments)
        except TimeoutError:
            return _error(f"{self.name}: '{tool}' timed out after {self.timeout:.0f}s")
        except McpError as exc:  # the server answered with an error; the connection is fine
            return _error(f"{self.name}: {exc.error.message}")
        except Exception as exc:  # noqa: BLE001 - transport broke; reconnect in the background
            self.last_error = f"call_tool: {_root_cause(exc)}"
            self.restart()
            return _error(f"{self.name} connection lost ({exc}); reconnecting, retry in a few seconds")

    def state(self) -> str:
        if self.session is not None:
            return "ok"
        since = f", {int(time.time() - self.down_since)}s" if self.down_since else ""
        return f"DOWN{since} - {self.last_error or 'connecting'}"


def _root_cause(exc: BaseException) -> str:
    while isinstance(exc, BaseExceptionGroup) and len(exc.exceptions) == 1:
        exc = exc.exceptions[0]
    return f"{type(exc).__name__}: {exc}"


def _error(text: str) -> types.CallToolResult:
    return types.CallToolResult(content=[types.TextContent(type="text", text=text)], isError=True)


def _text(text: str) -> types.CallToolResult:
    return types.CallToolResult(content=[types.TextContent(type="text", text=text)])


# ---------------------------------------------------------------------------- control.json
MODES = {
    "off": "off - the watchdog does nothing",
    "crash": "crash - restarts a program only after it crashed (the user is at the PC)",
    "keep": "keep - keeps the watched programs open: starts them, restarts after a crash or a hang (nobody at the PC)",
}


class Control:
    """The switches the watchdog reads every loop (the same file the Obsidian card and the bot edit)."""

    def __init__(self, path: Path | None):
        self.path = path

    def read(self) -> dict[str, Any]:
        if not self.path:
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8-sig"))
        except Exception:  # noqa: BLE001
            return {}

    def write(self, data: dict[str, Any], who: str) -> None:
        data["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        data["updated_by"] = who
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def summary(self) -> str:
        c = self.read()
        if not c:
            return "watchdog: unknown (control.json not found)"
        apps = c.get("apps", {})
        on = [k for k, v in apps.items() if v]
        off = [k for k, v in apps.items() if not v]
        return ("watchdog mode: %s\n  watched: %s\n  not watched: %s\n  changed %s by %s" % (
            MODES.get(c.get("mode"), c.get("mode")), ", ".join(on) or "-", ", ".join(off) or "-",
            c.get("updated", "?"), c.get("updated_by", "?")))


def build_server(downstreams: dict[str, Downstream], control: Control) -> Server:
    server = Server("weaver-bridge")

    status_tool = types.Tool(
        name="bridge_status",
        description="Show which programs on the user's PC (Cinema 4D, Houdini, Fusion, Nuke, Weaver ...) "
        "are connected to the Weaver Bridge, how many tools each has, and whether the watchdog "
        "(autostart and restart after a crash) is on.",
        inputSchema={"type": "object", "properties": {}},
    )
    control_tool = types.Tool(
        name="bridge_control",
        description="Show or change the watchdog on the user's PC. Modes: " + "; ".join(MODES.values()) + ". "
        "action 'mode' with value off/crash/keep sets the mode; action 'watch' / 'unwatch' with target "
        "(c4d, c4d26, houdini, nuke, fusion) adds or removes one program; action 'show' prints the state. "
        "Only change it when the user asks.",
        inputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["show", "mode", "watch", "unwatch"]},
                "value": {"type": "string", "enum": list(MODES)},
                "target": {"type": "string"},
            },
            "required": ["action"],
        },
    )

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        tools = [status_tool, control_tool]
        for name, ds in downstreams.items():
            for t in await ds.list_tools():
                tools.append(t.model_copy(update={
                    "name": f"{name}{SEP}{t.name}",
                    # the client rejects text-only replies (errors, timeouts) when a schema is declared
                    "outputSchema": None,
                    "description": f"[{ds.label}] {t.description or ''}".strip(),
                }))
        return tools

    @server.call_tool(validate_input=False)
    async def call_tool(name: str, arguments: dict[str, Any]) -> types.CallToolResult:
        arguments = arguments or {}
        if name == "bridge_status":
            lines = []
            for ds_name, ds in downstreams.items():
                tools = await ds.list_tools() if ds.session else ds._cached
                lines.append(f"{ds_name}: {ds.state()}, {len(tools)} tools" if ds.session
                             else f"{ds_name}: {ds.state()} ({len(tools)} tools cached)")
            lines.append("")
            lines.append(control.summary())
            return _text("\n".join(lines))
        if name == "bridge_control":
            return _control(control, arguments, list(downstreams))
        prefix, sep, tool = name.partition(SEP)
        ds = downstreams.get(prefix)
        if not sep or ds is None:
            return _error(f"Unknown tool: {name}")
        return await ds.call_tool(tool, arguments)

    return server


def _control(control: Control, args: dict[str, Any], names: list[str]) -> types.CallToolResult:
    if not control.path:
        return _error("control.json is not configured (--control)")
    action = str(args.get("action", "show")).lower()
    if action == "show":
        return _text(control.summary())
    data = control.read() or {"mode": "off", "apps": {}}
    apps = data.setdefault("apps", {})
    if action == "mode":
        value = str(args.get("value") or "").lower()
        if value not in MODES:
            return _error("value must be one of: " + ", ".join(MODES))
        data["mode"] = value
    elif action in ("watch", "unwatch"):
        target = str(args.get("target") or "").lower()
        if target not in apps:
            return _error(f"Unknown target {target!r}. One of: {', '.join(sorted(apps))}")
        apps[target] = action == "watch"
    else:
        return _error("action must be show, mode, watch or unwatch")
    control.write(data, "claude (bridge_control)")
    return _text("done\n" + control.summary())


def make_app(config: dict[str, Any], secrets: dict[str, Any], base_dir: Path, control: Control):
    token = secrets.get("gateway_token") or config.get("token")
    if not token or len(token) < 16:
        raise SystemExit("gateway_token in secrets.json must be at least 16 characters")
    state_dir = base_dir / "state"
    downstreams = {
        name: Downstream(name, spec, base_dir, secrets, state_dir)
        for name, spec in config["servers"].items()
        if spec.get("enabled", True)
    }
    manager = StreamableHTTPSessionManager(
        app=build_server(downstreams, control),
        stateless=False,
        # The Host header is the tunnel's hostname; the secret path is the protection.
        security_settings=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )
    mcp_path = f"/{token}/mcp"

    @contextlib.asynccontextmanager
    async def lifespan():
        async with anyio.create_task_group() as tg:
            for ds in downstreams.values():
                tg.start_soon(ds.run)
            async with manager.run():
                log.info("Serving %d server(s): %s", len(downstreams), ", ".join(downstreams))
                yield
            tg.cancel_scope.cancel()

    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            await receive()
            ctx = lifespan()
            try:
                await ctx.__aenter__()
            except Exception as exc:  # noqa: BLE001
                await send({"type": "lifespan.startup.failed", "message": str(exc)})
                return
            await send({"type": "lifespan.startup.complete"})
            msg = await receive()
            assert msg["type"] == "lifespan.shutdown"
            await ctx.__aexit__(None, None, None)
            await send({"type": "lifespan.shutdown.complete"})
            return
        if scope["type"] == "http" and scope["path"].rstrip("/") == mcp_path:
            await manager.handle_request(scope, receive, send)
            return
        if scope["type"] == "http" and scope["path"] == "/health":
            # local health check for the supervisor and the bot (no secrets, no tool calls)
            body = json.dumps({n: d.state() for n, d in downstreams.items()}).encode()
            await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
            await send({"type": "http.response.body", "body": body})
            return
        # Anything else (including wrong tokens) looks like an empty server.
        await send({"type": "http.response.start", "status": 404, "headers": [(b"content-type", b"text/plain")]})
        await send({"type": "http.response.body", "body": b"not found"})

    return app


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))  # PowerShell 5 writes a BOM


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True, help="servers.json")
    parser.add_argument("--secrets", default="", help="secrets.json (gateway_token, bearer tokens)")
    parser.add_argument("--control", default="", help="control.json with the watchdog switches")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s", stream=sys.stderr)
    logging.getLogger("mcp").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    config_path = Path(args.config).resolve()
    config = _read_json(config_path)
    # servers.local.json (next to servers.json) survives install: its entries add to or replace the generated ones
    local_path = config_path.with_name("servers.local.json")
    if local_path.is_file():
        local = _read_json(local_path)
        config["servers"].update(local.get("servers", {}))
        log.info("servers.local.json applied: %s", ", ".join(local.get("servers", {})) or "(empty)")
    secrets = _read_json(Path(args.secrets)) if args.secrets else {}
    control = Control(Path(args.control) if args.control else None)
    uvicorn.run(make_app(config, secrets, config_path.parent, control), host=args.host, port=args.port,
                log_level="warning")


if __name__ == "__main__":
    main()
