# -*- coding: utf-8 -*-
"""Weaver Bridge plugin for Cinema 4D (install.py copies it as plugins/weaver_bridge/weaver_bridge.pyp
into every Cinema 4D preferences folder, next to weaver_hook.py).

Every 2 s it writes:
  * <home>/state/c4d/status_<pid>.json - render heartbeat for the Telegram watcher (based on RenderWatch 2.0:
    is Picture Viewer / Render Queue rendering, scene, frame range, output folders, queue jobs);
  * <home>/state/alive/<pid>.json      - which scene is open; on a normal close it is marked "closed",
    so the supervisor can tell a crash from a close.
After a crash it re-opens the scene the supervisor asked for (once the UI is up).
It never sends anything anywhere. Console output is ASCII only (the MCP bridge breaks on other text).
"""
import os
import sys
import time

import c4d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weaver_hook  # noqa: E402

PLUGIN_ID = 1000008     # test range id (1000001-1000010); RenderWatch 2.0 uses 1000010
BEAT_MS = 2000
STATUS_DIR = os.path.join(weaver_hook.STATE, "c4d")
STATUS_FILE = os.path.join(STATUS_DIR, "status_%d.json" % os.getpid())


def _const(name):
    return getattr(c4d, name, None)


RM_PROGRESS = _const("RM_PROGRESS")
STATUS_NAMES = {}
for _n in ("RM_NOTSTARTED", "RM_PROGRESS", "RM_FINISHED", "RM_STOPPED", "RM_ERROR", "RM_ERROR2"):
    _v = _const(_n)
    if _v is not None and _v not in STATUS_NAMES:
        STATUS_NAMES[_v] = _n[3:].lower()


def write_status(st):
    weaver_hook._write(STATUS_FILE, st)


def doc_file(doc):
    try:
        folder = doc.GetDocumentPath()
        return os.path.join(folder, doc.GetDocumentName()) if folder else None
    except Exception:
        return None


def frame_range(doc, rd):
    fps = doc.GetFps()
    seq = rd[c4d.RDATA_FRAMESEQUENCE]
    if seq == _const("RDATA_FRAMESEQUENCE_CURRENTFRAME"):
        a = b = doc.GetTime()
    elif seq == _const("RDATA_FRAMESEQUENCE_ALLFRAMES"):
        a, b = doc.GetMinTime(), doc.GetMaxTime()
    elif seq == _const("RDATA_FRAMESEQUENCE_PREVIEWRANGE"):
        a, b = doc.GetLoopMinTime(), doc.GetLoopMaxTime()
    else:
        a, b = rd[c4d.RDATA_FRAMEFROM], rd[c4d.RDATA_FRAMETO]
    step = rd[c4d.RDATA_FRAMESTEP] or 1
    return [a.GetFrame(fps), b.GetFrame(fps), int(step)]


def output_dirs(doc, rd):
    """Folders the frames land in (regular Save + Multi-Pass); $tokens are cut off."""
    raw = []
    for on, path in ((c4d.RDATA_SAVEIMAGE, c4d.RDATA_PATH),
                     (c4d.RDATA_MULTIPASS_SAVEIMAGE, c4d.RDATA_MULTIPASS_FILENAME)):
        try:
            if rd[on] and rd[path]:
                raw.append(str(rd[path]))
        except Exception:
            pass
    base = doc.GetDocumentPath()
    res = []
    for p in raw:
        if "$" in p:
            p = p[:p.index("$")]
        d = p if p.endswith(("/", "\\")) else os.path.dirname(p)
        if not os.path.isabs(d):
            if not base:
                continue
            d = os.path.join(base, d)
        d = os.path.normpath(d)
        if d not in res:
            res.append(d)
    return res


def current_take(doc):
    try:
        td = doc.GetTakeData()
        cur = td.GetCurrentTake()
        if cur and cur != td.GetMainTake():
            return cur.GetName()
    except Exception:
        pass
    return None


def job_info(doc):
    rd = doc.GetActiveRenderData()
    return {
        "doc": doc.GetDocumentName(),
        "path": doc_file(doc),
        "dirty": bool(doc.GetChanged()),
        "take": current_take(doc),
        "frames": frame_range(doc, rd),
        "out_dirs": output_dirs(doc, rd),
        "fps": float(rd[c4d.RDATA_FRAMERATE] or doc.GetFps()),
    }


def env_info():
    info = {"version": c4d.GetC4DVersion()}
    try:
        info["c4d_dir"] = c4d.storage.GeGetStartupPath()
    except Exception:
        pass
    try:
        info["prefs_dir"] = c4d.storage.GeGetC4DPath(c4d.C4D_PATH_PREFS)
    except Exception:
        pass
    return info


ENV = env_info()
ALIVE = weaver_hook.Alive(weaver_hook.app_key("c4d26" if ENV["version"] >= 2026400 else "c4d", ENV.get("c4d_dir")))


class WeaverC4D(c4d.plugins.MessageData):

    def __init__(self):
        self.job = None
        self.rq_cache = {}
        self.reopened = False

    def GetTimer(self):
        return BEAT_MS

    def CoreMessage(self, id, bc):
        if id == c4d.MSG_TIMER:
            try:
                if not self.reopened:
                    self.reopened = True
                    self.reopen()
                self.beat()
            except Exception as e:
                weaver_hook._say("beat: %s" % e)
        return True

    def reopen(self):
        path = weaver_hook.consume_reopen(ALIVE.app)
        if path:
            try:
                c4d.documents.LoadFile(path)
                weaver_hook._say("reopened after a crash: %s" % path)
            except Exception as e:
                weaver_hook._say("reopen failed: %s" % e)

    def rq_info(self, path):
        info = {"doc": os.path.basename(path), "path": path, "dirty": False,
                "take": None, "frames": None, "out_dirs": []}
        try:
            doc = c4d.documents.LoadDocument(path, getattr(c4d, "SCENEFILTER_NONE", 0), None)
            if doc:
                info.update(job_info(doc))
                info.update(doc=os.path.basename(path), path=path, dirty=False)
        except Exception as e:
            weaver_hook._say("queue job settings not read: %s" % e)
        return info

    def beat(self):
        active = c4d.documents.GetActiveDocument()
        ALIVE.update(doc_file(active) if active else None)

        br = c4d.documents.GetBatchRender()
        queue, current = [], None
        for i in range(br.GetElementCount()):
            code = br.GetElementStatus(i)
            path = str(br.GetElement(i) or "")
            try:
                enabled = bool(br.GetEnableElement(i))
            except Exception:
                enabled = True
            queue.append({"file": os.path.basename(path), "path": path, "code": int(code),
                          "status": STATUS_NAMES.get(code, str(code)), "enabled": enabled})
            if current is None and code == RM_PROGRESS:
                current = (i, path)
        rq_on = bool(br.IsRendering()) or current is not None
        pv_on = (not rq_on) and bool(c4d.CheckIsRunning(c4d.CHECKISRUNNING_EXTERNALRENDERING))

        st = {"pid": os.getpid(), "time": time.time(), "app": ALIVE.app, "rendering": rq_on or pv_on}
        st.update(ENV)
        if rq_on:
            for e in queue:
                try:
                    key = (e["path"], os.path.getmtime(e["path"]))
                except OSError:
                    continue
                if key not in self.rq_cache:
                    self.rq_cache[key] = self.rq_info(e["path"])
                info = self.rq_cache[key]
                e.update(frames=info.get("frames"), out_dirs=info.get("out_dirs"), fps=info.get("fps"))
        st["queue"] = queue

        if pv_on:
            if not self.job or self.job.get("mode") != "pv":
                self.job = dict(job_info(active), mode="pv", started=time.time())
        elif rq_on and current:
            i, path = current
            j = self.job
            if not j or j.get("mode") != "rq" or j.get("job_index") != i or j.get("path") != path:
                self.job = dict(self.rq_info(path), mode="rq", job_index=i,
                                job_count=len(queue), path=path, started=time.time())
        elif not rq_on:
            self.job = None
        if self.job and st["rendering"]:
            st.update(self.job)
        write_status(st)


def PluginMessage(id, data):
    if id == c4d.C4DPL_ENDACTIVITY:   # a normal close: not a crash
        ALIVE.close()
        write_status({"pid": os.getpid(), "time": time.time(), "app": ALIVE.app,
                      "rendering": False, "closed": True})
    return False


if __name__ == "__main__":
    c4d.plugins.RegisterMessagePlugin(PLUGIN_ID, "Weaver Bridge", 0, WeaverC4D())
