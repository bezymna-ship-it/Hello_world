# -*- coding: utf-8 -*-
"""Weaver Bridge hook, loaded INSIDE Cinema 4D, Houdini and Nuke (install.py copies it there).

It does three small things and must never break the program it lives in:
  1. starts the program's MCP server when the program opens (Houdini, Nuke; C4D via its plugin patch);
  2. keeps a marker  <home>/state/alive/<pid>.json : which scene is open and whether the program was
     closed normally - the supervisor tells a crash from a normal close by it;
  3. after a crash, re-opens the scene the supervisor asked for (<home>/state/reopen/<app>.txt),
     at most 3 times in 15 minutes (crash-loop guard).
Output is ASCII only: Cinema 4D's console bridge breaks on other characters.
"""
import atexit
import json
import os
import time

HOME = os.environ.get("WEAVER_HOME") or r"__WEAVER_HOME__"
STATE = os.path.join(HOME, "state")
ALIVE_DIR = os.path.join(STATE, "alive")
REOPEN_DIR = os.path.join(STATE, "reopen")


def _say(msg):
    try:
        print("[weaver_bridge] " + str(msg).encode("ascii", "replace").decode("ascii"))
    except Exception:
        pass


def _read(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write(path, data):
    try:
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, path)
    except Exception:
        pass


def app_key(default, exe_dir=None):
    """Which program of config.json this is: WEAVER_APP (set when the supervisor started it),
    else the program folder matched against <home>/state/apps.json, else `default`."""
    k = os.environ.get("WEAVER_APP")
    if k:
        return k
    if exe_dir:
        mine = os.path.normcase(os.path.normpath(exe_dir))
        for key, a in (_read(os.path.join(STATE, "apps.json"), {}) or {}).items():
            exe = a.get("exe") or ""
            if exe and os.path.normcase(os.path.normpath(os.path.dirname(exe))) == mine:
                return key
    return default


class Alive(object):
    def __init__(self, app):
        self.app = app
        self.path = os.path.join(ALIVE_DIR, "%d.json" % os.getpid())
        self.data = {"pid": os.getpid(), "app": app, "doc": None, "closed": False,
                     "started": time.time(), "time": time.time()}
        self.last_write = 0.0
        self._cleanup()
        self._flush()
        atexit.register(self.close)

    def _cleanup(self):
        # markers of processes that ended days ago are useless
        try:
            now = time.time()
            for n in os.listdir(ALIVE_DIR):
                p = os.path.join(ALIVE_DIR, n)
                if now - os.path.getmtime(p) > 3 * 86400:
                    os.remove(p)
        except Exception:
            pass

    def _flush(self):
        self.data["time"] = time.time()
        _write(self.path, self.data)
        self.last_write = time.time()

    def update(self, doc=None):
        """Call often; writes only when the scene changed or once a minute."""
        if doc is not None and doc != self.data.get("doc"):
            self.data["doc"] = doc
            self._flush()
        elif time.time() - self.last_write > 60:
            self._flush()

    def close(self):
        if not self.data.get("closed"):
            self.data["closed"] = True
            self._flush()


def consume_reopen(app):
    """The scene to open after a crash, or None. The request file is used up either way."""
    req = os.path.join(REOPEN_DIR, app + ".txt")
    if not os.path.isfile(req):
        return None
    try:
        with open(req, encoding="utf-8") as f:
            path = f.read().strip()
        os.remove(req)
    except Exception:
        return None
    if not path or not os.path.isfile(path):
        return None
    guard = os.path.join(REOPEN_DIR, app + ".guard.json")
    now = time.time()
    recent = [t for t in (_read(guard, []) or []) if now - t < 900]
    if len(recent) >= 3:
        _say("reopen skipped: crash-loop guard (3 in 15 min)")
        return None
    _write(guard, recent + [now])
    return path


# ------------------------------------------------------------------ Houdini
_HOU = {}


def houdini_start(port=19876):
    """Called from scripts/123.py and scripts/456.py: once per Houdini session, the second call is a no-op."""
    if _HOU.get("alive"):
        return _HOU["alive"]
    import hou
    import hdefereval

    alive = _HOU["alive"] = Alive(app_key("houdini", os.path.dirname(os.environ.get("HFS", "") + os.sep + "bin" + os.sep)))

    def current():
        p = hou.hipFile.path()
        return None if hou.hipFile.isNewFile() or not os.path.isfile(p) else p

    def on_file(event_type):
        try:
            alive.update(current())
        except Exception:
            pass

    try:
        hou.hipFile.addEventCallback(on_file)
    except Exception as exc:
        _say("hip callback failed: %s" % exc)

    def mcp():
        try:
            import houdini_mcp
            houdini_mcp.start_server(port=port)
            hou.ui.setStatusMessage("Weaver Bridge: Houdini MCP on localhost:%d" % port)
        except Exception as exc:
            _say("Houdini MCP start failed: %s" % exc)

    def reopen():
        path = consume_reopen(alive.app)
        if path:
            try:
                hou.hipFile.load(path, suppress_save_prompt=True, ignore_load_warnings=True)
                hou.ui.setStatusMessage("Weaver Bridge reopened " + path)
            except Exception as exc:
                _say("reopen failed: %s" % exc)
        alive.update(current())

    hdefereval.executeDeferred(mcp)
    hdefereval.executeDeferred(reopen)
    return alive


# ------------------------------------------------------------------ Nuke
def nuke_start(port=54321):
    import nuke

    exe_dir = os.path.dirname(getattr(nuke, "EXE_PATH", "") or "")
    alive = Alive(app_key("nuke", exe_dir))

    def current():
        try:
            p = nuke.root().name()
            return p if p and p != "Root" and os.path.isfile(p) else None
        except Exception:
            return None

    def on_file():
        alive.update(current())

    try:
        nuke.addOnScriptSave(on_file)
        nuke.addOnScriptLoad(on_file)
    except Exception as exc:
        _say("nuke callbacks failed: %s" % exc)

    def later():
        try:
            import nuke_mcp_addon
            nuke_mcp_addon.start(port=port)
        except Exception as exc:
            _say("NukeMCP start failed: %s" % exc)
        path = consume_reopen(alive.app)
        if path:
            try:
                nuke.scriptOpen(path)
            except Exception as exc:
                _say("reopen failed: %s" % exc)
        alive.update(current())

    try:
        try:
            from PySide6.QtCore import QTimer
        except ImportError:
            from PySide2.QtCore import QTimer
        QTimer.singleShot(3000, later)   # after the UI is up
    except Exception:
        later()
    return alive
