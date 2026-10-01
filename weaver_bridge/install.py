"""Weaver Bridge installer (Windows). Safe to re-run: updates what is there, keeps your settings.

    py install.py                         install / update everything
    py install.py --home D:\\weaver_bridge  another place for venvs, logs, secrets (default C:\\weaver_bridge)
    py install.py --telegram              (re)enter the Telegram bot token and chat id
    py install.py --no-autostart          do not start the bridge with Windows
    py install.py --dry-run               only show what was found

What it does:
  1. home folder (C:\\weaver_bridge): Python venv, the MCP servers of Cinema 4D / Houdini / Nuke / Fusion
     (downloaded from GitHub and patched), cloudflared, logs, secrets.json;
  2. finds the programs: Cinema 4D installs (2026.4+ = Maxon's built-in MCP on 5556, others = plugin on 5555),
     Houdini, Nuke, Fusion -> config.json next to this file (edit paths there if something is wrong);
  3. puts the hooks into the programs: C4D plugin (+ MCP socket autostart), Houdini pythonrc.py, Nuke menu.py;
  4. secrets.json: new gateway token, the Cinema 4D 2026.4 MCP token (from ~/.claude.json), Telegram bot;
  5. stops the old Studio Bridge / RenderWatch processes, starts Weaver Bridge, and (unless --no-autostart)
     makes Windows start it at logon.
"""
from __future__ import annotations

import argparse
import ctypes
import glob
import json
import os
import re
import secrets as pysecrets
import shutil
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common  # noqa: E402

IS_WIN = os.name == "nt"
NO_WINDOW = 0x08000000 if IS_WIN else 0
REPOS = {
    "cinema4d-mcp": "https://github.com/ttiimmaacc/cinema4d-mcp.git",
    "houdini-mcp": "https://github.com/eetumartola/houdini-mcp.git",
    "nuke-mcp": "https://github.com/kleer001/nuke-mcp.git",
    "fusion-studio-mcp": "https://github.com/bigsbypuglise/fusion-studio-mcp.git",
}
HOUDINI_PORT = 19876
NUKE_PORT = 54321
BLOCK_BEGIN = "# >>> weaver_bridge"
BLOCK_END = "# <<< weaver_bridge"


# ------------------------------------------------------------------ output
def step(msg):
    print("\n==> " + msg, flush=True)


def ok(msg):
    print("    " + msg, flush=True)


def warn(msg):
    print("    ! " + msg, flush=True)


def sh(cmd, cwd=None, check=True):
    print("    $ " + " ".join(str(c) for c in cmd), flush=True)
    r = subprocess.run(cmd, cwd=cwd)
    if check and r.returncode != 0:
        raise SystemExit("command failed (%s): %s" % (r.returncode, " ".join(map(str, cmd))))
    return r.returncode


# ------------------------------------------------------------------ detection
def file_version(path):
    """(major, minor, build, rev) from the exe's version resource, or None."""
    if not IS_WIN:
        return None
    try:
        ver = ctypes.windll.version
        size = ver.GetFileVersionInfoSizeW(path, None)
        if not size:
            return None
        buf = ctypes.create_string_buffer(size)
        ver.GetFileVersionInfoW(path, 0, size, buf)
        p = ctypes.c_void_p()
        n = ctypes.c_uint()
        ver.VerQueryValueW(buf, "\\", ctypes.byref(p), ctypes.byref(n))

        class VS(ctypes.Structure):
            _fields_ = [("sig", ctypes.c_uint32), ("sv", ctypes.c_uint32), ("ms", ctypes.c_uint32),
                        ("ls", ctypes.c_uint32), ("pms", ctypes.c_uint32), ("pls", ctypes.c_uint32)]
        vs = VS.from_address(p.value)
        return (vs.pms >> 16, vs.pms & 0xFFFF, vs.pls >> 16, vs.pls & 0xFFFF)
    except Exception:
        return None


def c4d_version(exe):
    """2026.4 -> (2026, 4). From the version resource, else from the folder name."""
    v = file_version(exe)
    if v and v[0] >= 2023:
        return (v[0], v[1])
    m = re.search(r"(20\d\d)[ ._-]?(\d)", os.path.dirname(exe))
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def drives():
    if not IS_WIN:
        return ["/"]
    return ["%s:\\" % d for d in "CDEFGH" if os.path.isdir("%s:\\" % d)]


def find_c4d():
    cands = set()
    for d in drives():
        for pat in ("Program Files/Maxon*/Cinema 4D.exe", "Program Files/Maxon*/*/Cinema 4D.exe",
                    "*Cinema*4*/Cinema 4D.exe", "*Cinema*4*/*/Cinema 4D.exe", "Maxon*/*/Cinema 4D.exe"):
            cands.update(glob.glob(os.path.join(d, pat)))
    return sorted(((c4d_version(e), e) for e in cands), reverse=True)


def find_first(patterns):
    for d in drives():
        for pat in patterns:
            hits = sorted(glob.glob(os.path.join(d, pat)), reverse=True)
            if hits:
                return hits[0]
    return ""


def detect_apps(old):
    apps = {}
    c4ds = find_c4d()
    for v, e in c4ds:
        ok("Cinema 4D %d.%d: %s" % (v[0], v[1], e))
    new = [e for v, e in c4ds if v >= (2026, 4)]
    rest = [e for v, e in c4ds if v < (2026, 4)]
    # the clean bridge Cinema of the old setup wins for 5555, if it is still there
    pref = [e for e in rest if "cinema4d_2026_3" in e.lower()]
    if new:
        apps["c4d26"] = {"label": "Cinema 4D 2026.4 (встроенный MCP, порт 5556)", "exe": new[0], "port": 5556,
                         "crash_globs": [r"%APPDATA%\Maxon\*\_bugreports\*"], "trust_exit_hook": True}
    if pref or rest:
        apps["c4d"] = {"label": "Cinema 4D (плагин, порт 5555)", "exe": (pref or rest)[0], "port": 5555,
                       "crash_globs": [r"%APPDATA%\Maxon\*\_bugreports\*"], "trust_exit_hook": True}
    hou = find_first([r"Steam\steamapps\common\Houdini*\bin\hindie.steam.exe",
                      r"SteamLibrary\steamapps\common\Houdini*\bin\hindie.steam.exe",
                      r"Program Files (x86)\Steam\steamapps\common\Houdini*\bin\hindie.steam.exe",
                      r"Program Files\Side Effects Software\Houdini*\bin\houdinifx.exe",
                      r"Program Files\Side Effects Software\Houdini*\bin\houdini.exe"])
    if hou:
        apps["houdini"] = {"label": "Houdini", "exe": hou, "port": HOUDINI_PORT,
                           "crash_globs": [r"%TEMP%\houdini_temp\crash*"]}
        if "steam" in hou.lower():
            apps["houdini"]["steam_appid"] = "502570"
    nuke = find_first([r"Program Files\Nuke*\Nuke[0-9]*.exe"])   # not nukeCrashFeedback.exe
    if nuke:
        apps["nuke"] = {"label": "Nuke", "exe": nuke, "port": NUKE_PORT, "crash_globs": []}
    fus = find_first([r"Program Files\Blackmagic Design\Fusion 2*\Fusion.exe",
                      r"Program Files\Blackmagic Design\Fusion*\Fusion.exe"])
    if fus:
        apps["fusion"] = {"label": "Fusion Studio", "exe": fus, "port": None, "crash_globs": []}
    # what the user corrected by hand in config.json stays
    for k, spec in (old or {}).items():
        if k in apps:
            keep = {kk: vv for kk, vv in spec.items() if vv not in (None, "")}
            if kk_exe_bad(keep.get("exe")):
                keep.pop("exe", None)      # a wrong exe picked by an older installer
            apps[k].update(keep)
        else:
            apps[k] = spec
    for k, spec in apps.items():
        if not os.path.isfile(spec.get("exe", "")):
            warn("%s: exe not found (%s) - fix the path in config.json" % (k, spec.get("exe")))
        else:
            ok("%s -> %s" % (k, spec["exe"]))
    return apps


def kk_exe_bad(exe):
    return bool(exe) and re.search(r"(?i)crash|feedback|uninstall|updater", os.path.basename(exe)) is not None


def find_fusion_dll(apps):
    if apps.get("fusion"):
        d = os.path.join(os.path.dirname(apps["fusion"]["exe"]), "fusionscript.dll")
        if os.path.isfile(d):
            return d
    return find_first([r"Program Files\Blackmagic Design\Fusion*\fusionscript.dll",
                       r"Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"])


# ------------------------------------------------------------------ secrets
def bearer_from_claude_json():
    """Cinema 4D 2026.4's 'Update Selected Client' wrote url + Bearer token into ~/.claude.json."""
    path = os.path.join(os.path.expanduser("~"), ".claude.json")
    data = common.read_json(path, {}) or {}
    found = []

    def walk(o):
        if isinstance(o, dict):
            url = str(o.get("url", ""))
            if ":5556" in url:
                auth = (o.get("headers") or {}).get("Authorization") or (o.get("headers") or {}).get("authorization")
                if auth and auth.lower().startswith("bearer "):
                    found.append(auth[7:].strip())
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(data)
    return found[0] if found else ""


def bearer_from_c4d_prefs():
    """Fallback: a client config Cinema 4D keeps in <prefs>/mcp (format may change between versions)."""
    for f in glob.glob(os.path.join(os.environ.get("APPDATA", ""), "Maxon", "*2026_4*", "mcp", "**", "*.json"),
                       recursive=True):
        txt = open(f, encoding="utf-8", errors="ignore").read()
        m = re.search(r"Bearer\s+([A-Za-z0-9._\-]{16,})", txt)
        if m:
            return m.group(1)
    return ""


def renderwatch_bot():
    cfg = common.read_json(os.path.join(os.path.dirname(HERE), "RenderWatch", "watchdog", "config.json"), {}) or {}
    tok, chat = str(cfg.get("telegram_token", "")), str(cfg.get("chat_id", ""))
    if re.match(r"^\d{6,}:[\w-]{20,}$", tok) and re.match(r"^-?\d{5,}$", chat):
        return tok, chat
    return "", ""


def ask(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


# ------------------------------------------------------------------ installing parts
def make_venv(venv_dir, packages):
    """Create (once) and update a venv; returns its python.exe."""
    py = os.path.join(venv_dir, "Scripts", "python.exe") if IS_WIN else os.path.join(venv_dir, "bin", "python")
    if not os.path.isfile(py):
        sh([sys.executable, "-m", "venv", venv_dir])
    sh([py, "-m", "pip", "install", "-q", "--upgrade", "pip"])
    if packages:
        sh([py, "-m", "pip", "install", "-q"] + packages)
    return py


def sync_repo(url, d):
    if os.path.isdir(os.path.join(d, ".git")):
        sh(["git", "-C", d, "checkout", "-q", "--", "."])     # drop our patches before updating
        sh(["git", "-C", d, "pull", "-q", "--ff-only"], check=False)
    else:
        sh(["git", "clone", "-q", "--depth", "1", url, d])


def with_home(src_file, home):
    return open(src_file, encoding="utf-8").read().replace("__WEAVER_HOME__", home)


def put_block(path, body, comment="#"):
    """Insert or replace our marked block in a user script (pythonrc.py, menu.py) - their own code stays."""
    text = open(path, encoding="utf-8", errors="ignore").read() if os.path.isfile(path) else ""
    block = "%s\n%s\n%s\n" % (BLOCK_BEGIN, body.strip("\n"), BLOCK_END)
    pat = re.compile(re.escape(BLOCK_BEGIN) + r".*?" + re.escape(BLOCK_END) + r"\n?", re.S)
    if pat.search(text):
        text = pat.sub(lambda _m: block, text)
    else:
        text = (text.rstrip("\n") + "\n\n" if text.strip() else "") + block
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


HOUDINI_BLOCK = '''
try:
    import hou
    if hou.isUIAvailable():
        import weaver_hook
        weaver_hook.houdini_start(port=%d)
except Exception as _wb_exc:
    print("[weaver_bridge] Houdini hook skipped: %%s" %% _wb_exc)
''' % HOUDINI_PORT

NUKE_BLOCK = '''
try:
    import nuke
    if nuke.GUI:
        import weaver_hook
        weaver_hook.nuke_start(port=%d)
except Exception as _wb_exc:
    print("[weaver_bridge] Nuke hook skipped: %%s" %% _wb_exc)
''' % NUKE_PORT


def c4d_prefs_dirs():
    root = os.path.join(os.environ.get("APPDATA", ""), "Maxon")
    out = []
    for d in sorted(glob.glob(os.path.join(root, "*"))):
        name = os.path.basename(d)
        if not os.path.isdir(d) or not re.search(r"(?i)cinema", name) or re.search(r"_[a-z]$", name):
            continue  # skip _c / _x / _w (Commandline, Team Render)
        m = re.search(r"(20\d\d)[ ._-](\d)", name)
        out.append((d, (int(m.group(1)), int(m.group(2))) if m else (0, 0)))
    return out


def install_c4d(home, apps_dir):
    step("Cinema 4D: MCP server (port 5555) + Weaver plugin")
    d = os.path.join(apps_dir, "cinema4d-mcp")
    sync_repo(REPOS["cinema4d-mcp"], d)
    py = make_venv(os.path.join(d, ".venv"), ["-e", d, "mcp>=1.2,<2"])
    plugin_src = os.path.join(d, "c4d_plugin", "mcp_server_plugin.pyp")
    sh([py, os.path.join(HERE, "patches", "patch_c4d_autostart.py"), plugin_src])
    prefs = c4d_prefs_dirs()
    if not prefs:
        warn("no Cinema 4D preferences folder in %APPDATA%\\Maxon - open each Cinema 4D once, then re-run")
    for p, ver in prefs:
        wb = os.path.join(p, "plugins", "weaver_bridge")
        os.makedirs(wb, exist_ok=True)
        with open(os.path.join(wb, "weaver_hook.py"), "w", encoding="utf-8") as f:
            f.write(with_home(os.path.join(HERE, "hooks", "weaver_hook.py"), home))
        shutil.copyfile(os.path.join(HERE, "hooks", "weaver_c4d_plugin.py"), os.path.join(wb, "weaver_bridge.pyp"))
        if ver >= (2026, 4):
            ok("%s: Weaver plugin (MCP = Maxon's built-in, port 5556: Edit > Preferences > MCP > Allow MCP Server)"
               % os.path.basename(p))
        else:
            dst = os.path.join(p, "plugins", "cinema4d-mcp")
            os.makedirs(dst, exist_ok=True)
            shutil.copyfile(plugin_src, os.path.join(dst, "mcp_server_plugin.pyp"))
            ok("%s: Weaver plugin + MCP socket plugin (starts by itself, port 5555)" % os.path.basename(p))
        if os.path.isdir(os.path.join(p, "plugins", "render_watch")) or os.path.isdir(os.path.join(p, "plugins", "RenderWatch")):
            warn("%s: RenderWatch plugin is also installed - harmless, but Weaver replaces it (you may remove it)"
                 % os.path.basename(p))
    return {"type": "stdio", "label": "Cinema 4D (плагин 5555)", "command": py, "args": ["main.py"], "cwd": d,
            "timeout": 180, "env": {"C4D_HOST": "127.0.0.1", "C4D_PORT": "5555"}}


def install_houdini(home, apps_dir):
    step("Houdini: MCP server (port %d) + hook" % HOUDINI_PORT)
    d = os.path.join(apps_dir, "houdini-mcp")
    sync_repo(REPOS["houdini-mcp"], d)
    py = make_venv(os.path.join(d, ".venv"), ["mcp[cli]>=1.2,<2"])
    srv = os.path.join(d, "houdini_mcp_server.py")
    code = open(srv, encoding="utf-8").read()
    code = re.sub(r"(\n\s*)description=", r"\1instructions=", code)        # FastMCP(description=) was renamed
    code = code.replace("port=9876", 'port=int(os.environ.get("HOUDINI_PORT", "9876"))')
    open(srv, "w", encoding="utf-8").write(code)
    mod = os.path.join(d, "houdini_mcp.py")
    open(mod, "w", encoding="utf-8").write(open(mod, encoding="utf-8").read().replace("port=9876", "port=%d" % HOUDINI_PORT))
    sh([py, os.path.join(HERE, "patches", "patch_houdini.py"), srv])
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    prefs = [p for p in glob.glob(os.path.join(docs, "houdini*")) if re.search(r"houdini\d+\.\d+$", p)]
    if not prefs:
        warn("no Documents\\houdiniXX.X folder (open Houdini once, then re-run)")
    hook = with_home(os.path.join(HERE, "hooks", "weaver_hook.py"), home)
    for h in prefs:
        for pv in ("python3.9libs", "python3.10libs", "python3.11libs", "python3.12libs"):
            dst = os.path.join(h, pv)
            os.makedirs(dst, exist_ok=True)
            shutil.copyfile(mod, os.path.join(dst, "houdini_mcp.py"))
            with open(os.path.join(dst, "weaver_hook.py"), "w", encoding="utf-8") as f:
                f.write(hook)
            put_block(os.path.join(dst, "pythonrc.py"), HOUDINI_BLOCK)
        ok("%s: MCP module + weaver_hook + pythonrc.py block (MCP starts with Houdini)" % h)
    return {"type": "stdio", "label": "Houdini", "command": py, "args": ["houdini_mcp_server.py"], "cwd": d,
            "timeout": 300, "env": {"HOUDINI_PORT": str(HOUDINI_PORT)}}


def install_nuke(home, apps_dir):
    step("Nuke: MCP server (port %d) + addon + menu.py hook" % NUKE_PORT)
    d = os.path.join(apps_dir, "nuke-mcp")
    sync_repo(REPOS["nuke-mcp"], d)
    py = make_venv(os.path.join(d, ".venv"), ["-e", d])
    dot = os.path.join(os.path.expanduser("~"), ".nuke")
    os.makedirs(dot, exist_ok=True)
    shutil.copyfile(os.path.join(d, "nuke_addon", "nuke_mcp_addon.py"), os.path.join(dot, "nuke_mcp_addon.py"))
    with open(os.path.join(dot, "weaver_hook.py"), "w", encoding="utf-8") as f:
        f.write(with_home(os.path.join(HERE, "hooks", "weaver_hook.py"), home))
    put_block(os.path.join(dot, "menu.py"), NUKE_BLOCK)
    ok("%s: addon + weaver_hook + menu.py block (NukeMCP starts with Nuke)" % dot)
    return {"type": "stdio", "label": "Nuke", "command": py,
            "args": ["-c", "from nukemcp.server import main; main()", "--port", str(NUKE_PORT)], "cwd": d,
            "timeout": 300}


def install_fusion(home, apps_dir, dll):
    step("Fusion: MCP server")
    d = os.path.join(apps_dir, "fusion-studio-mcp")
    sync_repo(REPOS["fusion-studio-mcp"], d)
    py = make_venv(os.path.join(d, ".venv"), ["-e", d])
    shim = os.path.join(HERE, "fusion-shim")
    if dll and os.path.isfile(dll):
        ok("fusionscript.dll: " + dll)
    else:
        warn("fusionscript.dll not found - set apps.fusion.fusionscript in config.json and re-run")
    return {"type": "stdio", "label": "Fusion Studio", "command": py, "args": ["-m", "fusion_mcp.server"], "cwd": d,
            "timeout": 600, "env": {"PYTHONPATH": shim + ";" + os.path.join(d, "src"), "FUSION_SCRIPT_LIB": shim,
                                    "FUSION_DLL": dll or "", "FUSION_APP_NAME": "Fusion",
                                    "FUSION_MCP_LOG_DIR": os.path.join(home, "logs")}}


def download_cloudflared(home):
    cf = os.path.join(home, "bin", "cloudflared.exe")
    if os.path.isfile(cf):
        return cf
    step("cloudflared (tunnel)")
    os.makedirs(os.path.dirname(cf), exist_ok=True)
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    urllib.request.urlretrieve(url, cf + ".part")
    os.replace(cf + ".part", cf)
    ok(cf)
    return cf


# ------------------------------------------------------------------ old setup
def stop_old(bridge_dir):
    """Old Studio Bridge (gateway.py / watchdog.py of studio-bridge) and RenderWatch fight with the new one."""
    step("Stopping the old Studio Bridge / RenderWatch")
    try:
        import psutil
    except ImportError:
        warn("psutil not available yet - skipped")
        return
    hits = 0
    for p in psutil.process_iter(["pid", "cmdline", "exe"]):
        try:
            cmd = " ".join(p.info["cmdline"] or []).lower()
            exe = (p.info["exe"] or "").lower()
        except Exception:
            continue
        if bridge_dir.lower() in cmd:
            continue  # ours
        old = (("studio-bridge" in cmd and ("gateway.py" in cmd or "watchdog.py" in cmd or "start.ps1" in cmd))
               or ("studio-bridge" in exe and exe.endswith("cloudflared.exe"))
               or "render_watchdog.py" in cmd)
        if old:
            try:
                for c in p.children(recursive=True):
                    c.kill()
                p.kill()
                hits += 1
                ok("stopped pid %d: %s" % (p.info["pid"], cmd[:120]))
            except Exception as exc:
                warn("could not stop pid %d: %s" % (p.info["pid"], exc))
    startup = startup_dir()
    for name in ("RenderWatch.vbs",):
        f = os.path.join(startup, name)
        if os.path.isfile(f):
            os.replace(f, f + ".disabled")
            ok("RenderWatch autostart disabled (%s.disabled) - Weaver Bridge's bot replaces it" % f)
    if not hits:
        ok("nothing old was running")


def startup_dir():
    return os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")


def write_launchers(home, venv_py):
    pyw = venv_py.replace("python.exe", "pythonw.exe")
    sup = os.path.join(HERE, "supervisor.py")
    files = {
        "start.cmd": '@echo off\r\nstart "" "%s" "%s"\r\necho Weaver Bridge started in the background.\r\ntimeout /t 8 >nul\r\n"%s" "%s" status\r\npause\r\n' % (pyw, sup, venv_py, sup),
        "stop.cmd": '@echo off\r\n"%s" "%s" stop\r\npause\r\n' % (venv_py, sup),
        "status.cmd": '@echo off\r\n"%s" "%s" status\r\npause\r\n' % (venv_py, sup),
        "url.cmd": '@echo off\r\n"%s" "%s" url\r\n"%s" "%s" url | clip\r\necho (copied to clipboard)\r\npause\r\n' % (venv_py, sup, venv_py, sup),
        "autostart_on.cmd": '@echo off\r\n"%s" "%s" --autostart-only on\r\npause\r\n' % (sys.executable, os.path.join(HERE, "install.py")),
        "autostart_off.cmd": '@echo off\r\n"%s" "%s" --autostart-only off\r\npause\r\n' % (sys.executable, os.path.join(HERE, "install.py")),
    }
    for name, body in files.items():
        with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="") as f:
            f.write(body)
    ok("start.cmd, stop.cmd, status.cmd, url.cmd, autostart_on.cmd, autostart_off.cmd")


def set_autostart(on, venv_py):
    """autostart_on.cmd / autostart_off.cmd: the same switch as "windows_autostart" in control.json."""
    if os.path.isfile(common.CONTROL_FILE):
        ctl = common.read_control()
        ctl["windows_autostart"] = bool(on)
        common.write_control(ctl, "autostart_%s.cmd" % ("on" if on else "off"))
    vbs = os.path.join(startup_dir(), "WeaverBridge.vbs")
    if on:
        pyw = venv_py.replace("python.exe", "pythonw.exe")
        with open(vbs, "w", encoding="utf-16") as f:
            f.write('CreateObject("WScript.Shell").Run """%s"" ""%s""", 0, False\r\n'
                    % (pyw, os.path.join(HERE, "supervisor.py")))
        ok("Weaver Bridge starts with Windows (%s)" % vbs)
    elif os.path.isfile(vbs):
        os.remove(vbs)
        ok("autostart with Windows removed")
    else:
        ok("autostart with Windows was already off")


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--home", default="")
    ap.add_argument("--vault", default="")
    ap.add_argument("--gsg", default=r"E:\assets\Greyscalegorilla Studio\assets\Greyscalegorilla_Library")
    ap.add_argument("--telegram", action="store_true")
    ap.add_argument("--no-autostart", action="store_true")
    ap.add_argument("--autostart-only", choices=["on", "off"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip", default="", help="comma list: c4d,houdini,nuke,fusion")
    args = ap.parse_args()

    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11+ is needed (this is %s): winget install Python.Python.3.12" % sys.version.split()[0])
    cfg = common.read_json(common.CONFIG_FILE, {}) or {}
    home = args.home or cfg.get("home") or r"C:\weaver_bridge"
    vault = args.vault or cfg.get("vault") or os.path.dirname(os.path.dirname(HERE))
    venv_py = os.path.join(home, "venv", "Scripts", "python.exe") if IS_WIN else os.path.join(home, "venv", "bin", "python")
    if args.autostart_only:
        return set_autostart(args.autostart_only == "on", venv_py)

    step("Finding programs")
    apps = detect_apps(cfg.get("apps"))
    if args.dry_run:
        print(json.dumps(apps, ensure_ascii=False, indent=2))
        return
    if not shutil.which("git"):
        raise SystemExit("git not found: winget install Git.Git (then open a new terminal)")
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    for d in ("bin", "logs", "state", "apps"):
        os.makedirs(os.path.join(home, d), exist_ok=True)

    step("Python environment for the gateway, supervisor and bot: " + home + "\\venv")
    venv_py = make_venv(os.path.join(home, "venv"), ["mcp>=1.26,<2", "uvicorn>=0.30", "psutil", "pillow", "imageio-ffmpeg"])
    stop_old(HERE)

    apps_dir = os.path.join(home, "apps")
    servers = {}
    if "c4d" in apps and "c4d" not in skip:
        servers["c4d"] = install_c4d(home, apps_dir)
    if "c4d26" in apps and "c4d" not in skip:
        if "c4d" not in apps:       # the Weaver plugin still has to go into the 2026.4 prefs
            install_c4d(home, apps_dir)
        servers["c4d26"] = {"type": "http", "label": "Cinema 4D 2026.4", "url": "http://127.0.0.1:5556/mcp",
                            "bearer_secret": "c4d26_bearer", "timeout": 300}
    if "houdini" in apps and "houdini" not in skip:
        servers["houdini"] = install_houdini(home, apps_dir)
    if "nuke" in apps and "nuke" not in skip:
        servers["nuke"] = install_nuke(home, apps_dir)
    if "fusion" in apps and "fusion" not in skip:
        dll = (apps["fusion"].get("fusionscript") or find_fusion_dll(apps))
        apps["fusion"]["fusionscript"] = dll
        servers["fusion"] = install_fusion(home, apps_dir, dll)
    step("Weaver server (vault + GSG)")
    ws_dst = os.path.join(HERE, "weaver-server", "weaver_server.py")
    olds = glob.glob(os.path.join(os.path.dirname(HERE), "*", "studio-bridge", "weaver-server", "weaver_server.py"))
    ws_src = ws_dst if os.path.isfile(ws_dst) else (olds[0] if olds else "")
    if ws_src:
        os.makedirs(os.path.dirname(ws_dst), exist_ok=True)
        sh([venv_py, os.path.join(HERE, "patches", "patch_weaver_server.py"), ws_src, ws_dst])
    else:
        warn("weaver_server.py not found (neither here nor in the old studio-bridge) - weaver__ tools will be missing")
    servers["weaver"] = {"type": "stdio", "label": "Weaver", "command": venv_py,
                         "args": [os.path.join(HERE, "weaver-server", "weaver_server.py")],
                         "cwd": os.path.join(HERE, "weaver-server"), "timeout": 120,
                         "env": {"WEAVER_VAULT": vault, "WEAVER_GSG": args.gsg, "PYTHONUTF8": "1"}}
    common.write_json(os.path.join(home, "servers.json"), {"servers": servers})
    ok("servers.json: " + ", ".join(servers))
    download_cloudflared(home)

    step("Secrets (" + os.path.join(home, "secrets.json") + " - outside the vault, never share it)")
    sec_path = os.path.join(home, "secrets.json")
    sec = common.read_json(sec_path, {}) or {}
    if not sec.get("gateway_token"):
        sec["gateway_token"] = pysecrets.token_hex(24)
        ok("new gateway token (the connector URL changes once: add the new one in claude.ai)")
    if "c4d26" in servers:
        b = bearer_from_claude_json() or bearer_from_c4d_prefs() or sec.get("c4d26_bearer", "")
        if b:
            sec["c4d26_bearer"] = b
            ok("Cinema 4D 2026.4 MCP token found")
        else:
            warn("Cinema 4D 2026.4 MCP token not found. In C4D 2026.4: Edit > Preferences > MCP > Allow MCP Server, "
                 "Clients > Claude Code > Update Selected Client, then re-run install.py")
    if args.telegram or not sec.get("telegram_token"):
        tok, chat = renderwatch_bot()
        if tok and not args.telegram:
            ok("Telegram bot taken from RenderWatch config.json")
        else:
            print("    Telegram bot (Enter = skip). @BotFather -> /newbot gives the token; @userinfobot gives your id.")
            tok = ask("    bot token: ")
            chat = ask("    your chat id: ") if tok else ""
        if tok and chat:
            sec["telegram_token"], sec["telegram_chat_id"] = tok, chat
    common.write_json(sec_path, sec)
    if IS_WIN:
        subprocess.run(["icacls", sec_path, "/inheritance:r", "/grant:r", "%s:F" % os.environ.get("USERNAME", "")],
                       capture_output=True)

    step("config.json and control.json (in the vault, next to this file)")
    cfg.update(home=home, vault=vault, apps=apps)
    cfg.setdefault("gateway_port", 8765)
    cfg.setdefault("tunnel", {"type": "cloudflare", "ngrok_domain": "", "public_url": ""})
    cfg.setdefault("watch_render_dirs", ["Projects/*/*/Passes", "Projects/*/*/Output/Videos"])
    common.write_json(common.CONFIG_FILE, cfg)
    ctl = common.read_control() if os.path.isfile(common.CONTROL_FILE) else {"mode": "crash", "bridge": True, "apps": {}}
    for k in apps:
        ctl["apps"].setdefault(k, True)
    ctl["windows_autostart"] = not args.no_autostart
    common.write_control(ctl, "install.py")
    ok("mode: %s; watched: %s" % (ctl["mode"], ", ".join(k for k, v in ctl["apps"].items() if v)))

    step("Telegram bot core (RenderWatch 2.0)")
    rw_src = os.path.join(os.path.dirname(HERE), "RenderWatch", "watchdog", "render_watchdog.py")
    rw_dst = os.path.join(HERE, "watcher", "render_watchdog_base.py")
    if os.path.isfile(rw_src):
        shutil.copyfile(rw_src, rw_dst)
        ok("render_watchdog.py -> watcher/render_watchdog_base.py")
    elif not os.path.isfile(rw_dst):
        warn("RenderWatch not found at %s - the Telegram bot cannot start without it" % rw_src)

    step("Launchers and autostart")
    write_launchers(home, venv_py)
    set_autostart(not args.no_autostart, venv_py)

    step("Starting Weaver Bridge")
    sup = os.path.join(HERE, "supervisor.py")
    subprocess.run([venv_py, sup, "stop"], capture_output=True)
    time.sleep(2)
    pyw = venv_py.replace("python.exe", "pythonw.exe")
    subprocess.Popen([pyw if os.path.isfile(pyw) else venv_py, sup], cwd=HERE,
                     creationflags=(0x00000008 | 0x00000200) if IS_WIN else 0, close_fds=True)
    print("    waiting for the tunnel (up to 60 s) ...", flush=True)
    url = ""
    for _ in range(60):
        time.sleep(1)
        try:
            url = open(os.path.join(home, "connector-url.txt"), encoding="utf-8").read().strip()
        except OSError:
            continue
        if url:
            break
    subprocess.run([venv_py, sup, "status"])
    print()
    if url:
        print("Connector URL (secret!):\n  " + url)
        try:
            subprocess.run("clip", input=url.encode(), shell=True)
            print("  (copied to clipboard) -> claude.ai > Settings > Connectors > Add custom connector")
        except Exception:
            pass
    else:
        warn("no tunnel URL yet - run url.cmd in a minute (log: %s\\logs\\tunnel.log)" % home)
    print("\nDone. The switches: Obsidian card Studio_bridge/weaver_bridge/weaver_bridge.md, the Telegram bot, "
          "or bridge_control from Claude.")


if __name__ == "__main__":
    main()
