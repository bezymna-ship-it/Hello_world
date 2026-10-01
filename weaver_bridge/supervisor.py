"""Weaver Bridge supervisor: one background process that keeps the bridge alive.

    pythonw supervisor.py            run (started by Windows at logon, see install.py)
    python  supervisor.py status     what runs right now
    python  supervisor.py stop       stop the supervisor, gateway, tunnel and bot (programs stay open)
    python  supervisor.py url        print the connector URL (secret - do not share)

What it keeps alive:
  * gateway   - the MCP gateway (gateway/gateway.py), restarted in place if it dies or stops answering;
  * tunnel    - cloudflared (quick tunnel) or ngrok, so claude.ai can reach the gateway;
  * watcher   - the Telegram bot (watcher/weaver_watcher.py), if secrets.json has a bot token;
  * programs  - Cinema 4D (two installs), Houdini, Nuke, Fusion, by the guard mode in control.json:
        off    nothing is started or killed;
        on     a program is started again only after it CRASHED (a normal close is left alone);
               crash / error dialogs of our programs are closed;
        keep   watched programs are kept open: started if closed, restarted after a crash or a hang.
    After a crash the program re-opens the scene it had open (hooks/ inside each program do that).

control.json (next to this file) is the switchboard: the Obsidian card, the Telegram bot and the
bridge_control tool all edit it, and it is re-read every loop.

Updates apply by themselves (nothing to run on the PC):
  * new code: every 10 s the .py files (and config.json) are checked; changed ones are syntax-checked first (an error is
    reported to the bot and the old code keeps running), then only the changed part restarts -
    the gateway, the bot, or the supervisor itself (programs stay open);
  * one-off jobs: a .py file put into jobs/ runs once (vault as working folder), then moves to
    jobs/done/ (or jobs/failed/); exit code 75 = "not now, try again in 5 minutes". Output: logs/jobs/.
"""
from __future__ import annotations

import glob
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

try:
    import psutil
except ImportError:  # the venv from install.py has it; plain python may not
    psutil = None

IS_WIN = os.name == "nt"
NO_WINDOW = 0x08000000 if IS_WIN else 0
DETACHED = (0x00000008 | 0x00000200 | 0x01000000) if IS_WIN else 0  # DETACHED | NEW_GROUP | BREAKAWAY
VERSION = 3
LOCK_PORT = 47290
LOOP_S = 5
APPS_EVERY_S = 10

CFG = common.load_config()
HOME = CFG["home"]
LOG = common.home_path(CFG, "logs", "supervisor.log")
STATE_DIR = common.home_path(CFG, "state")
ALIVE_DIR = os.path.join(STATE_DIR, "alive")
REOPEN_DIR = os.path.join(STATE_DIR, "reopen")
REQ_DIR = os.path.join(STATE_DIR, "requests")   # the bot asks for things here: launch_<app>[.txt = scene]
STATUS_FILE = os.path.join(STATE_DIR, "supervisor.json")
PID_FILE = os.path.join(STATE_DIR, "supervisor.pid")
STOP_FLAG = os.path.join(STATE_DIR, "stop.flag")
URL_FILE = common.home_path(CFG, "connector-url.txt")
VENV_PY = common.home_path(CFG, "venv", "Scripts" if IS_WIN else "bin", "python.exe" if IS_WIN else "python")
JOBS_DIR = os.path.join(common.BRIDGE_DIR, "jobs")
JOB_LOGS = common.home_path(CFG, "logs", "jobs")
JOB_RETRY = 75                 # a job's exit code for "not now, try again later"
CODE = {                       # which files belong to which part (relative to this folder)
    "supervisor": ["supervisor.py", "common.py", "config.json"],
    "gateway": ["gateway/*.py", "weaver-server/*.py", "fusion-shim/*.py"],
    "watcher": ["watcher/*.py", "common.py"],
}

APP_DEFAULTS = {
    "hang_limit": 300,   # s "Not Responding" before a kill (only in keep mode)
    "port_limit": 600,   # s of a closed MCP port before an event (never a kill)
    "cooldown": 90,      # s between launches
    "max_launches": 4,   # per 30 min, then a pause
}


def log(msg):
    common.log_to(LOG, msg)


def event(kind, text, **extra):
    log("event %s: %s" % (kind, text.replace("\n", " | ")))
    common.emit_event(CFG, kind, text, **extra)


# ------------------------------------------------------------------ helpers
def port_open(port, host="127.0.0.1"):
    if not port:
        return None
    try:
        with socket.create_connection((host, int(port)), timeout=1.0):
            return True
    except OSError:
        return False


def run(cmd, timeout=30):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, creationflags=NO_WINDOW,
                              timeout=timeout, errors="ignore").stdout
    except Exception:
        return ""


def norm(p):
    return os.path.normcase(os.path.normpath(p or ""))


def processes():
    """[(pid, name, exe)] of every process we can see."""
    out = []
    if psutil is None:
        return out
    for p in psutil.process_iter(["pid", "name", "exe", "status"]):
        try:
            if p.info["status"] == psutil.STATUS_ZOMBIE:
                continue
            out.append((p.info["pid"], (p.info["name"] or ""), p.info["exe"] or ""))
        except Exception:
            continue
    return out


def hung_pids():
    if not IS_WIN:
        return set()
    pids = set()
    for line in run(["tasklist", "/FI", "STATUS eq NOT RESPONDING", "/FO", "CSV", "/NH"]).splitlines():
        parts = line.strip().strip('"').split('","')
        if len(parts) >= 2 and parts[1].isdigit():
            pids.add(int(parts[1]))
    return pids


def kill_tree(pid):
    if IS_WIN:
        run(["taskkill", "/F", "/T", "/PID", str(pid)])
    elif psutil:
        try:
            p = psutil.Process(pid)
            for c in p.children(recursive=True):
                c.kill()
            p.kill()
        except Exception:
            pass


def close_crash_dialogs(pids):
    """Close crash dialogs that belong to our programs and Windows Error Reporting (WerFault)."""
    if not IS_WIN:
        return []
    import ctypes
    import ctypes.wintypes as wt
    user32 = ctypes.windll.user32
    closed = []
    proto = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def cb(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value not in pids:
            return True
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, buf, 256)
        if re.search(r"(?i)application error|has stopped working|crash|fatal|unhandled exception|bug ?report",
                     buf.value):
            user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
            closed.append((pid.value, buf.value))
        return True

    user32.EnumWindows(proto(cb), 0)
    for pid, name, _exe in processes():
        if name.lower() == "werfault.exe":
            kill_tree(pid)
            closed.append((pid, "WerFault"))
    return closed


# ------------------------------------------------------------------ child processes
class Child:
    """A helper process we own (gateway, tunnel, bot): started, watched, restarted with backoff."""

    def __init__(self, name, cmd_fn, cwd=None, health=None):
        self.name, self.cmd_fn, self.cwd, self.health = name, cmd_fn, cwd, health
        self.proc = None
        self.logf = None
        self.started = 0.0
        self.fails = 0
        self.next_try = 0.0
        self.bad_health = 0
        self.log_path = common.home_path(CFG, "logs", name + ".log")

    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def start(self):
        cmd = self.cmd_fn()
        if not cmd:
            return False
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if os.path.exists(self.log_path) and os.path.getsize(self.log_path) > 2_000_000:
            os.replace(self.log_path, self.log_path + ".old")
        self.logf = open(self.log_path, "a", encoding="utf-8", errors="replace")
        self.logf.write("\n==== %s start: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), self.name))
        self.logf.flush()
        try:
            self.proc = subprocess.Popen(cmd, cwd=self.cwd, stdout=self.logf, stderr=subprocess.STDOUT,
                                         creationflags=NO_WINDOW)
        except Exception as exc:
            log("%s: start failed: %s" % (self.name, exc))
            self.proc = None
            self.fails += 1
            self.next_try = time.time() + min(300, 10 * self.fails)
            return False
        self.started = time.time()
        self.bad_health = 0
        log("%s: started pid %d" % (self.name, self.proc.pid))
        return True

    def stop(self):
        if self.running():
            kill_tree(self.proc.pid)
            log("%s: stopped" % self.name)
        self.proc = None
        if self.logf:
            self.logf.close()
            self.logf = None

    def ensure(self, want=True):
        now = time.time()
        if not want:
            self.stop()
            return
        if self.running():
            if self.health and now - self.started > 30:
                if self.health():
                    self.bad_health, self.fails = 0, 0
                else:
                    self.bad_health += 1
                    if self.bad_health >= 4:
                        log("%s: not answering, restarting" % self.name)
                        self.stop()
            return
        if self.proc is not None:  # it died
            code = self.proc.poll()
            log("%s: exited with code %s" % (self.name, code))
            self.proc = None
            self.fails += 1
            self.next_try = now + min(300, 5 * 2 ** min(self.fails, 6))
            if self.fails in (3, 10):
                event("child", "⚠️ %s падает (%d раз подряд), лог: %s" % (self.name, self.fails, self.log_path))
        if now >= self.next_try:
            self.start()


def gateway_cmd():
    gw = os.path.join(common.BRIDGE_DIR, "gateway", "gateway.py")
    servers = common.home_path(CFG, "servers.json")
    secrets = common.home_path(CFG, "secrets.json")
    if not (os.path.isfile(VENV_PY) and os.path.isfile(servers)):
        log("gateway: run install.py first (no venv or servers.json)")
        return None
    return [VENV_PY, gw, "--config", servers, "--secrets", secrets, "--control", common.CONTROL_FILE,
            "--port", str(CFG["gateway_port"])]


def gateway_health():
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/health" % CFG["gateway_port"], timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def find_ngrok(configured=None):
    """ngrok.exe: the configured path, PATH, or where winget / choco / scoop put it
    (a supervisor started before the install does not see the new PATH)."""
    import shutil
    if configured and os.path.isfile(configured):
        return configured
    hit = shutil.which(configured or "ngrok") or shutil.which("ngrok")
    if hit:
        return hit
    la = os.environ.get("LOCALAPPDATA", "")
    pats = [os.path.join(la, "Microsoft", "WinGet", "Links", "ngrok.exe"),
            os.path.join(la, "Microsoft", "WinGet", "Packages", "Ngrok.Ngrok*", "ngrok.exe"),
            os.path.join(la, "ngrok", "ngrok.exe"),
            r"C:\ProgramData\chocolatey\bin\ngrok.exe",
            os.path.join(os.path.expanduser("~"), "scoop", "shims", "ngrok.exe"),
            os.path.join(os.path.expanduser("~"), "Downloads", "ngrok*", "ngrok.exe"),
            os.path.join(os.path.expanduser("~"), "Downloads", "ngrok.exe"),
            common.home_path(CFG, "bin", "ngrok.exe")]
    for pat in pats:
        found = glob.glob(pat)
        if found:
            return found[0]
    return None


def tunnel_cmd(kind):
    t = CFG.get("tunnel") or {}
    port = str(CFG["gateway_port"])
    if kind == "ngrok":
        if not t.get("ngrok_domain"):
            log("tunnel: tunnel.ngrok_domain is empty in config.json")
            return None
        exe = find_ngrok(t.get("ngrok_path"))
        if not exe:
            return None
        return [exe, "http", "--url=" + t["ngrok_domain"], port, "--log=stdout"]
    if kind == "cloudflare":
        cf = common.home_path(CFG, "bin", "cloudflared.exe")
        if not os.path.isfile(cf):
            log("tunnel: %s not found (run install.py)" % cf)
            return None
        return [cf, "tunnel", "--no-autoupdate", "--protocol", "http2", "--url", "http://127.0.0.1:" + port]
    return None  # "none": the user runs an own tunnel (tunnel.public_url)


def watcher_cmd():
    s = common.load_secrets(CFG)
    if not (s.get("telegram_token") and s.get("telegram_chat_id")):
        return None
    py = VENV_PY.replace("python.exe", "pythonw.exe") if IS_WIN else VENV_PY
    return [py, os.path.join(common.BRIDGE_DIR, "watcher", "weaver_watcher.py")]


class Tunnel(Child):
    """cloudflared or ngrok. If ngrok cannot run (not installed, no authtoken, the domain busy), the bridge
    falls back to a cloudflared quick tunnel for this session and says why - claude.ai keeps working."""

    def __init__(self):
        super().__init__("tunnel", lambda: tunnel_cmd(self.kind()))
        self.base = None
        self.read_pos = 0
        self.fallback = None         # why ngrok was given up (then cloudflared runs)
        self.quick_exits = 0

    def kind(self):
        k = (CFG.get("tunnel") or {}).get("type", "cloudflare")
        return "cloudflare" if (k == "ngrok" and self.fallback) else k

    def ensure(self, want=True):
        if self.kind() == "none":      # the user runs an own tunnel: nothing to start
            return
        if self.kind() == "ngrok" and self.proc is not None and self.proc.poll() is not None:
            self.quick_exits = self.quick_exits + 1 if time.time() - self.started < 60 else 0
            if self.quick_exits >= 3:
                self.give_up_ngrok(self.ngrok_error() or "ngrok сразу закрывается")
        super().ensure(want)

    def ngrok_error(self):
        try:
            with open(self.log_path, encoding="utf-8", errors="ignore") as f:
                f.seek(self.read_pos)
                text = f.read()
        except OSError:
            return None
        m = re.search(r"(ERR_NGROK_\d+)", text)
        hints = {"ERR_NGROK_4018": "нет authtoken: ngrok config add-authtoken <токен с dashboard.ngrok.com>",
                 "ERR_NGROK_334": "домен уже занят другим ngrok (закрой лишний ngrok)",
                 "ERR_NGROK_108": "ngrok уже запущен в другом месте (закрой лишний ngrok)"}
        return (m.group(1) + (" — " + hints[m.group(1)] if m.group(1) in hints else "")) if m else None

    def give_up_ngrok(self, why):
        if self.fallback:
            return
        self.fallback = why
        self.fails, self.next_try, self.base = 0, 0.0, None
        event("tunnel_fallback", "⚠️ ngrok не работает: %s.\nВременно включила запасной туннель cloudflare — "
              "адрес будет другой (пришлю). Когда ngrok починишь: ♻️ Перезапустить мост." % why)

    def start(self):
        if self.cmd_fn() is None:
            if self.kind() == "ngrok":
                self.give_up_ngrok("ngrok.exe не найден (поставь: winget install ngrok.ngrok)")
                return False
            self.next_try = time.time() + 60
            return False
        if self.kind() == "cloudflare":
            self.base = None           # a quick tunnel gets a new address every start
        ok = super().start()
        self.read_pos = os.path.getsize(self.log_path) if os.path.exists(self.log_path) else 0
        return ok

    def poll_url(self):
        t = CFG.get("tunnel") or {}
        kind = self.kind()
        base = None
        if kind == "ngrok" and t.get("ngrok_domain") and self.running() and time.time() - self.started > 8:
            base = "https://" + t["ngrok_domain"]
        elif kind == "none" and t.get("public_url"):
            base = t["public_url"].rstrip("/")
        elif kind == "cloudflare" and self.running():
            try:
                with open(self.log_path, encoding="utf-8", errors="ignore") as f:
                    f.seek(self.read_pos)
                    m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", f.read())
                if m:
                    base = m.group(0)
            except OSError:
                pass
        if base and base != self.base:
            self.base = base
            token = common.load_secrets(CFG).get("gateway_token", "")
            url = "%s/%s/mcp" % (base, token)
            try:
                with open(URL_FILE, "w", encoding="utf-8") as f:
                    f.write(url + "\n")
            except OSError:
                pass
            changed = kind == "cloudflare"
            event("url", "🔗 Адрес коннектора %s. Сам адрес — кнопка 🔗 Адрес в боте (целиком, с /mcp на конце)"
                  % ("ИЗМЕНИЛСЯ — обнови коннектор в claude.ai" if changed else "готов"), changed=changed)


# ------------------------------------------------------------------ programs
class App:
    def __init__(self, key, spec):
        self.key = key
        self.spec = dict(APP_DEFAULTS, **spec)
        self.label = spec.get("label", key)
        self.exe = spec.get("exe", "")
        self.pids = set()
        self.last_launch = 0.0
        self.launches = []
        self.hung_since = None
        self.port_down_since = None
        self.port_warned = False
        self.pending = None          # {"why", "reopen", "at"} - start after cooldown
        self.parked = False          # the user closed it on purpose (guard "on" leaves it closed)
        self.state = "closed"
        self.port = None

    def find(self, procs):
        exe = norm(self.exe)
        if not exe:
            return set()
        return {pid for pid, _n, e in procs if norm(e) == exe}

    def marker(self, pid):
        return common.read_json(os.path.join(ALIVE_DIR, "%d.json" % pid), None)

    def launch(self, why, reopen=None):
        now = time.time()
        self.launches = [t for t in self.launches if now - t < 1800]
        if len(self.launches) >= self.spec["max_launches"]:
            if self.state != "paused":
                event("loop", "🛑 %s: %d запусков за 30 мин — пауза. Проверь сцену/программу." % (
                    self.label, len(self.launches)), app=self.key)
            self.state = "paused"
            self.pending = None
            return
        if not os.path.isfile(self.exe):
            self.state = "no exe"
            log("%s: exe not found: %s" % (self.key, self.exe))
            self.pending = None
            return
        os.makedirs(REOPEN_DIR, exist_ok=True)
        rp = os.path.join(REOPEN_DIR, self.key + ".txt")
        if reopen and os.path.isfile(reopen):
            with open(rp, "w", encoding="utf-8") as f:
                f.write(reopen)
        elif os.path.exists(rp):
            os.remove(rp)
        env = dict(os.environ, WEAVER_APP=self.key, WEAVER_HOME=HOME)
        try:
            if self.spec.get("steam_appid") and IS_WIN:
                os.startfile("steam://rungameid/%s" % self.spec["steam_appid"])
            else:
                args = [self.exe] + list(self.spec.get("args", []))
                subprocess.Popen(args, cwd=os.path.dirname(self.exe), env=env, creationflags=DETACHED,
                                 close_fds=True)
        except Exception as exc:
            log("%s: launch failed: %s" % (self.key, exc))
            event("launch_fail", "❌ %s не запустилась: %s" % (self.label, exc), app=self.key)
            self.pending = None
            return
        self.launches.append(now)
        self.last_launch = now
        self.pending = None
        self.hung_since = None
        self.port_down_since = None
        self.state = "starting"
        log("%s: launched (%s)%s" % (self.key, why, (" reopen " + reopen) if reopen else ""))
        event("launch", "🚀 %s запущена (%s)%s" % (self.label, why, ("\n📄 открою: %s" % os.path.basename(reopen))
                                                     if reopen else ""), app=self.key)

    def tick(self, procs, hung, mode, watched):
        now = time.time()
        pids = self.find(procs)
        self.port = port_open(self.spec.get("port"))
        if pids:
            self.parked = False
            self.pending = None
            gone = self.pids - pids
            self.pids = pids
            if gone:
                self._closed(gone, mode, watched, still_running=True)
            # hang: only killed in keep mode (the user may be waiting on a long operation)
            if pids & hung:
                self.hung_since = self.hung_since or now
                self.state = "hung"
                if mode == "keep" and watched and now - self.hung_since > self.spec["hang_limit"]:
                    reopen = self._doc_of(pids)
                    for pid in pids:
                        kill_tree(pid)
                    event("hang", "🧊 %s не отвечала %d с — закрыла, перезапускаю" % (
                        self.label, now - self.hung_since), app=self.key)
                    self.pids = set()
                    self.hung_since = None
                    self.pending = {"why": "после зависания", "reopen": reopen, "at": now + 15}
                return
            self.hung_since = None
            # MCP port: only reported, never a reason to kill (that once cost the user their work)
            if self.port is False:
                self.port_down_since = self.port_down_since or max(now, self.last_launch)
                self.state = "running, MCP off"
                if now - self.port_down_since > self.spec["port_limit"] and not self.port_warned:
                    self.port_warned = True
                    event("port", "🔌 %s открыта, но MCP-порт %s закрыт уже %d мин" % (
                        self.label, self.spec.get("port"), (now - self.port_down_since) // 60), app=self.key)
            else:
                if self.port_warned:
                    event("port_ok", "🔌 %s: MCP снова на связи" % self.label, app=self.key)
                self.port_down_since, self.port_warned = None, False
                self.state = "ok"
            return
        if self.pids:  # it was running a moment ago
            gone, self.pids = self.pids, set()
            self._closed(gone, mode, watched)
        if not watched or mode == "off":
            self.state = "parked" if self.parked else "closed"
            self.pending = None
            return
        if self.pending is None and mode == "keep" and now - self.last_launch > self.spec["cooldown"]:
            self.pending = {"why": "режим «держать открытой»", "reopen": None, "at": now}
        if self.pending and now >= self.pending["at"] and now - self.last_launch > self.spec["cooldown"]:
            self.launch(self.pending["why"], self.pending.get("reopen"))
        elif self.state not in ("paused", "no exe"):
            self.state = "waiting" if self.pending else ("parked" if self.parked else "closed")

    def _doc_of(self, pids):
        for pid in pids:
            m = self.marker(pid) or {}
            if m.get("doc"):
                return m["doc"]
        return None

    def _evidence(self):
        """A sign that the program really crashed: a crash dialog or a fresh crash report file."""
        now = time.time()
        if now - CRASH_SEEN.get(self.key, 0) < 180:
            return "окно ошибки"
        for g in self.spec.get("crash_globs") or []:
            for f in glob.glob(os.path.expandvars(g)):
                try:
                    if now - os.path.getmtime(f) < 300:
                        return os.path.basename(f)
                except OSError:
                    pass
        return None

    def _closed(self, gone, mode, watched, still_running=False):
        markers = [m for m in (self.marker(pid) for pid in gone) if m]
        doc = next((m["doc"] for m in markers if m.get("doc")), None)
        if markers and all(m.get("closed") for m in markers):
            log("%s: closed normally" % self.key)
            if not still_running:
                self.parked = True
            return
        evidence = self._evidence()
        # C4D reports a normal close reliably (C4DPL_ENDACTIVITY): an unclosed marker is a crash.
        # Houdini / Nuke / Fusion: only with evidence, so a normal close is never "repaired".
        if (markers and self.spec.get("trust_exit_hook")) or evidence:
            event("crash", "💥 %s УПАЛА%s%s" % (self.label, (" (%s)" % evidence) if evidence else "",
                                               ("\n📄 сцена: %s" % doc) if doc else ""), app=self.key)
            if watched and mode in ("on", "keep") and not still_running:
                self.pending = {"why": "после падения", "reopen": doc, "at": time.time() + 10}
        else:
            event("closed_unknown", "❔ %s закрылась, падение не подтверждено — сама не запускаю.\n"
                  "Запустить: кнопка ниже или 🚀 Запустить%s" % (self.label, ("\n📄 сцена: %s" % doc) if doc else ""),
                  app=self.key, doc=doc)
            if not still_running:
                self.parked = True


CRASH_SEEN = {}


# ------------------------------------------------------------------ self-update and jobs
def pythonw():
    py = VENV_PY if os.path.isfile(VENV_PY) else sys.executable
    return py.replace("python.exe", "pythonw.exe") if IS_WIN else py


def code_stamp(pats):
    out = []
    for pat in pats:
        for f in sorted(glob.glob(os.path.join(common.BRIDGE_DIR, pat))):
            try:
                out.append((f, os.path.getmtime(f), os.path.getsize(f)))
            except OSError:
                pass
    return tuple(out)


def syntax_error(files):
    """None, or the first syntax error in these files (checked before any restart)."""
    for f in files:
        try:
            with open(f, encoding="utf-8-sig") as fh:
                text = fh.read()
            if f.endswith(".json"):
                json.loads(text)
            else:
                compile(text, f, "exec")
        except ValueError as exc:
            return "%s: %s" % (os.path.relpath(f, common.BRIDGE_DIR), exc)
        except SyntaxError as exc:
            return "%s, строка %s: %s" % (os.path.relpath(f, common.BRIDGE_DIR), exc.lineno, exc.msg)
        except (OSError, UnicodeDecodeError) as exc:
            return "%s: %s" % (os.path.relpath(f, common.BRIDGE_DIR), exc)
    return None


def tail(path, lines=12, limit=1500):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = "".join(f.readlines()[-lines:]).strip()
    except OSError:
        return ""
    return text[-limit:]


class Updater:
    """New code -> restart the part it belongs to; files in jobs/ -> run once."""

    def __init__(self, sup):
        self.sup = sup
        self.stamps = {k: code_stamp(v) for k, v in CODE.items()}
        self.bad = {}
        self.last = 0.0
        self.job = None
        self.retry_at = {}
        self.told_wait = set()

    def tick(self):
        now = time.time()
        if now - self.last < 10:
            return
        self.last = now
        self.code(now)
        self.jobs(now)

    def code(self, now):
        for part, pats in CODE.items():
            st = code_stamp(pats)
            if st == self.stamps[part] or st == self.bad.get(part):
                continue
            if any(now - m < 3 for _f, m, _s in st):
                continue                       # still being written
            err = syntax_error([f for f, _m, _s in st])
            if err:
                self.bad[part] = st
                event("update_bad", "⚠️ Новый код (%s) с ошибкой — оставила старый, всё работает.\n%s" % (part, err))
                continue
            self.stamps[part] = st
            self.bad.pop(part, None)
            log("update: %s changed" % part)
            if part == "supervisor":
                event("update", "♻️ Обновляю мост (новый код), ~30 с — программы не трогаю")
                self.sup.restart_self()
                return
            child = self.sup.gateway if part == "gateway" else self.sup.watcher
            event("update", "♻️ %s: новый код, перезапускаю" % {"gateway": "шлюз", "watcher": "бот"}[part])
            child.stop()
            child.fails, child.next_try = 0, 0.0

    def jobs(self, now):
        if self.job:
            p, name, path, logf, log_path, started = self.job
            code = p.poll()
            if code is None:
                if now - started < 900:
                    return
                kill_tree(p.pid)
                code = -1
            logf.close()
            self.job = None
            out = tail(log_path)
            if code == JOB_RETRY:
                self.retry_at[name] = now + 300
                if name not in self.told_wait:
                    self.told_wait.add(name)
                    event("job_wait", "⏳ Задача %s ждёт: %s" % (name, out.splitlines()[-1] if out else "повторю позже"))
                return
            dest = os.path.join(JOBS_DIR, "done" if code == 0 else "failed")
            os.makedirs(dest, exist_ok=True)
            try:
                os.replace(path, os.path.join(dest, time.strftime("%Y%m%d-%H%M%S_") + name))
            except OSError as exc:
                log("job %s: not moved: %s" % (name, exc))
                self.retry_at[name] = now + 3600
            if code == 0:
                event("job", "✅ Задача %s выполнена%s" % (name, ("\n" + out) if out else ""))
            else:
                event("job_fail", "❌ Задача %s не удалась (код %s)%s" % (name, code, ("\n" + out) if out else ""))
            return
        for path in sorted(glob.glob(os.path.join(JOBS_DIR, "*.py"))):
            name = os.path.basename(path)
            try:
                if now - os.path.getmtime(path) < 3 or self.retry_at.get(name, 0) > now:
                    continue
            except OSError:
                continue
            os.makedirs(JOB_LOGS, exist_ok=True)
            log_path = os.path.join(JOB_LOGS, name[:-3] + ".log")
            logf = open(log_path, "w", encoding="utf-8", errors="replace")
            env = dict(os.environ, WEAVER_JOB="1", WEAVER_VAULT=CFG["vault"], WEAVER_HOME=HOME,
                       PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
            try:
                p = subprocess.Popen([VENV_PY if os.path.isfile(VENV_PY) else sys.executable, path], cwd=CFG["vault"],
                                     env=env, stdout=logf, stderr=subprocess.STDOUT, creationflags=NO_WINDOW)
            except Exception as exc:
                logf.close()
                log("job %s: start failed: %s" % (name, exc))
                self.retry_at[name] = now + 300
                continue
            log("job %s: started" % name)
            self.job = (p, name, path, logf, log_path, now)
            return


# ------------------------------------------------------------------ main loop
class Supervisor:
    def __init__(self):
        self.gateway = Child("gateway", gateway_cmd, cwd=common.BRIDGE_DIR, health=gateway_health)
        self.tunnel = Tunnel()
        self.watcher = Child("watcher", watcher_cmd, cwd=common.BRIDGE_DIR)
        self.apps = {}
        self.last_apps = 0.0
        self.last_mode = None
        self.vault_status, self.vault_status_t = None, 0.0
        self.updater = Updater(self)
        self.restarting = False

    def restart_self(self):
        """A fresh supervisor (new code) takes over: it asks this one to stop, then starts itself."""
        if self.restarting:
            return
        self.restarting = True
        try:
            subprocess.Popen([pythonw(), os.path.abspath(__file__), "restart"], cwd=common.BRIDGE_DIR,
                             creationflags=DETACHED | NO_WINDOW, close_fds=True)
        except Exception as exc:
            self.restarting = False
            log("restart failed: %s" % exc)

    def sync_apps(self):
        specs = CFG.get("apps", {})
        for key, spec in specs.items():
            if key not in self.apps:
                self.apps[key] = App(key, spec)
        # the hooks inside the programs find their own key by the program folder
        common.write_json(os.path.join(STATE_DIR, "apps.json"),
                          {k: {"exe": a.exe, "label": a.label, "port": a.spec.get("port")}
                           for k, a in self.apps.items()})

    def tick(self):
        ctl = common.read_control()
        want_bridge = bool(ctl.get("bridge", True))
        self.gateway.ensure(want_bridge)
        self.tunnel.ensure(want_bridge and self.gateway.running())
        if want_bridge:
            self.tunnel.poll_url()
        self.watcher.ensure(True)

        self.windows_autostart(ctl)
        mode = ctl["mode"]
        if mode != self.last_mode:
            if self.last_mode is not None:
                event("mode", "🛡 Guard: %s" % common.MODE_TEXT[mode])
            self.last_mode = mode
        now = time.time()
        if now - self.last_apps >= APPS_EVERY_S:
            self.last_apps = now
            procs = processes()
            ours = set()
            for a in self.apps.values():
                ours |= a.find(procs)
            for pid, title in close_crash_dialogs(ours) if mode != "off" else []:
                for a in self.apps.values():
                    if pid in a.pids:
                        CRASH_SEEN[a.key] = now
                event("dialog", "🪟 закрыла окно ошибки: %s" % title)
            hung = hung_pids() if ours else set()
            self.requests()
            for a in self.apps.values():
                try:
                    a.tick(procs, hung, mode, bool(ctl["apps"].get(a.key, False)))
                except Exception as exc:
                    log("%s: tick error: %r" % (a.key, exc))
        self.write_status(ctl)
        try:
            self.updater.tick()
        except Exception as exc:
            log("updater: %r" % (exc,))

    def windows_autostart(self, ctl):
        """control.json "windows_autostart": the Startup-folder entry that starts this supervisor at logon."""
        if not IS_WIN:
            return
        want = bool(ctl.get("windows_autostart", True))
        vbs = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs",
                           "Startup", "WeaverBridge.vbs")
        if want == os.path.isfile(vbs):
            return
        try:
            if want:
                pyw = VENV_PY.replace("python.exe", "pythonw.exe")
                with open(vbs, "w", encoding="utf-16") as f:
                    f.write('CreateObject("WScript.Shell").Run """%s"" ""%s""", 0, False\r\n'
                            % (pyw, os.path.abspath(__file__)))
            else:
                os.remove(vbs)
            event("autostart", "🪟 Запуск моста вместе с Windows: %s" % ("включён" if want else "выключен"))
        except OSError as exc:
            log("windows autostart: %s" % exc)

    def requests(self):
        """Manual launches asked for by the bot (/run c4d): work in any mode."""
        try:
            names = os.listdir(REQ_DIR)
        except OSError:
            return
        for n in names:
            path = os.path.join(REQ_DIR, n)
            m = re.match(r"^launch_(\w+?)(\.txt)?$", n)
            try:
                doc = open(path, encoding="utf-8").read().strip() or None
                os.remove(path)
            except OSError:
                continue
            if n.startswith("restart"):    # the bot / the card: "restart the bridge"
                event("update", "🔄 Перезапускаю мост по кнопке (~30 с, программы не трогаю)")
                self.restart_self()
                continue
            a = self.apps.get(m.group(1)) if m else None
            if a is None:
                continue
            if a.pids:
                event("launch", "ℹ️ %s уже открыта" % a.label, app=a.key)
            else:
                a.launches = []            # a manual start resets the crash-loop pause
                a.launch("по запросу", doc)

    def write_status(self, ctl):
        st = {
            "time": time.time(), "pid": os.getpid(), "version": VERSION, "mode": ctl["mode"], "bridge": ctl.get("bridge", True),
            "windows_autostart": bool(ctl.get("windows_autostart", True)),
            "gateway": "up" if self.gateway.running() and gateway_health() else "down",
            "tunnel_kind": self.tunnel.kind(), "tunnel_note": self.tunnel.fallback,
            "tunnel": "external" if self.tunnel.kind() == "none" else
                      (("up" if self.tunnel.base else "starting") if self.tunnel.running() else "down"),
            "watcher": "up" if self.watcher.running() else "off",
            "apps": {k: {"label": a.label, "state": a.state, "pids": sorted(a.pids), "port": a.port,
                         "watched": bool(ctl["apps"].get(k, False))} for k, a in self.apps.items()},
        }
        common.write_json(STATUS_FILE, st)
        # a copy next to control.json for the Obsidian card (no secrets in it); written only when
        # something changed or once a minute, so the vault is not rewritten every few seconds
        same = {k: v for k, v in st.items() if k not in ("time", "pid")}
        if same != self.vault_status or time.time() - self.vault_status_t > 60:
            self.vault_status, self.vault_status_t = same, time.time()
            try:
                common.write_json(os.path.join(common.BRIDGE_DIR, "status.json"), st)
            except OSError:
                pass

    def shutdown(self):
        for c in (self.watcher, self.tunnel, self.gateway):
            c.stop()


def acquire_lock():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", LOCK_PORT))
        return s
    except OSError:
        return None


def cmd_stop():
    """Ask the running supervisor to stop its helpers and exit. Never a tree kill: the programs it
    started (Cinema 4D, Houdini ...) count as its children on Windows and must stay open."""
    if acquire_lock_probe():
        print("supervisor is not running")
        return
    os.makedirs(STATE_DIR, exist_ok=True)
    open(STOP_FLAG, "w").close()
    for _ in range(30):
        time.sleep(1)
        if acquire_lock_probe():
            print("supervisor stopped (programs stay open)")
            return
    pid = None
    try:
        pid = int(open(PID_FILE).read().strip())
    except Exception:
        pass
    if pid and psutil:
        try:
            psutil.Process(pid).kill()   # only the supervisor itself
            print("supervisor did not answer, killed pid %d" % pid)
        except Exception as exc:
            print("could not stop pid %s: %s" % (pid, exc))


def acquire_lock_probe():
    s = acquire_lock()
    if s is None:
        return False
    s.close()
    return True


def cleanup_stale():
    """Helpers left over by a supervisor that was killed: they would hold the ports."""
    if psutil is None:
        return
    gw = os.path.join(common.BRIDGE_DIR, "gateway", "gateway.py").lower()
    bot = os.path.join(common.BRIDGE_DIR, "watcher", "weaver_watcher.py").lower()
    cf = common.home_path(CFG, "bin", "cloudflared.exe").lower()
    for p in psutil.process_iter(["pid", "cmdline", "exe"]):
        try:
            cmd = " ".join(p.info["cmdline"] or []).lower()
            if gw in cmd or bot in cmd or (p.info["exe"] or "").lower() == cf:
                kill_tree(p.info["pid"])
                log("killed a leftover helper pid %d" % p.info["pid"])
        except Exception:
            continue


def cmd_status():
    st = common.read_json(STATUS_FILE, None)
    if not st:
        print("no status yet (is the supervisor running?)")
        return
    age = time.time() - st.get("time", 0)
    print("supervisor pid %s, updated %ds ago%s" % (st.get("pid"), age, "  (STALE: not running?)" if age > 60 else ""))
    print("guard: %s | bridge: %s | gateway: %s | tunnel: %s | bot: %s" % (
        common.MODE_TEXT.get(st.get("mode"), st.get("mode")), st.get("bridge"), st.get("gateway"),
        st.get("tunnel"), st.get("watcher")))
    for k, a in st.get("apps", {}).items():
        print("  %-8s %-40s %-18s watched=%s port=%s" % (k, a["label"], a["state"], a["watched"], a["port"]))


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "run"
    if arg == "restart":               # take over from a running supervisor (new code)
        cmd_stop()
        for _ in range(30):
            if acquire_lock_probe():
                break
            time.sleep(1)
    if arg == "stop":
        return cmd_stop()
    if arg == "status":
        return cmd_status()
    if arg == "url":
        try:
            print(open(URL_FILE, encoding="utf-8").read().strip())
        except OSError:
            print("no URL yet")
        return
    lock = acquire_lock()
    if lock is None:
        print("supervisor already running")
        return
    if arg == "restart":
        cleanup_stale()
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    if psutil is None:
        log("psutil missing: programs are not watched (run install.py)")
    if os.path.exists(STOP_FLAG):
        os.remove(STOP_FLAG)
    cleanup_stale()
    sup = Supervisor()
    sup.sync_apps()
    log("supervisor started (pid %d), mode %s" % (os.getpid(), common.read_control()["mode"]))
    event("start", "🟢 Weaver Bridge запущен. Guard: %s" % common.MODE_TEXT[common.read_control()["mode"]])
    try:
        while not os.path.exists(STOP_FLAG):
            try:
                sup.tick()
            except Exception as exc:
                log("loop error: %r" % (exc,))
            time.sleep(LOOP_S)
        log("stop requested")
    finally:
        sup.shutdown()
        lock.close()
        try:
            os.remove(STOP_FLAG)
        except OSError:
            pass


if __name__ == "__main__":
    main()
