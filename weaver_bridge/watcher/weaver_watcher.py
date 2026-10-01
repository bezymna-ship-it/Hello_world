"""weaver_watcher - the Telegram bot of Weaver Bridge (started by supervisor.py).

The render part is RenderWatch 2.0 (render_watchdog_base.py, copied from Studio_bridge/RenderWatch by
install.py): C4D render start / frames with previews / finish / mp4 video, alarms, auto-restart of a
crashed render through Commandline, /settings /status /preview /video. On top of it:

  * two Cinema 4D at once: the Weaver C4D plugin writes one heartbeat per process
    (<home>/state/c4d/status_<pid>.json) and the bot follows the one that renders;
  * folder renders (Houdini, Nuke, Fusion, anything): new frames in the folders of config.json
    "watch_render_dirs" (Projects/*/*/Passes ...) -> start, frames with previews, finish + mp4;
    new mp4 in Output/Videos are sent as they are;
  * the bridge: pages Мост (what runs), Guard (off / on / keep), Программы (which ones guard watches),
    Запустить, Адрес (connector URL), and the supervisor's events (crash, restart, new URL);
  * a keyboard under the chat (Telegram reply keyboard) - every function is a button, nothing to type.

Only the owner chat (telegram_chat_id in <home>/secrets.json) is answered.
"""
from __future__ import annotations

import glob
import json
import os
import socket
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import common  # noqa: E402

CFG_B = common.load_config()
SECRETS = common.load_secrets(CFG_B)
WDIR = common.home_path(CFG_B, "state", "watcher")
os.makedirs(WDIR, exist_ok=True)

import render_watchdog_base as rw  # noqa: E402  (RenderWatch 2.0, unchanged)

# --- RenderWatch, pointed at our files and our bot ---------------------------------------------
rw.WATCH_DIR = WDIR
rw.STATUS_FILE = os.path.join(WDIR, "status.json")          # unused: see pick_status()
rw.SETTINGS_FILE = os.path.join(WDIR, "settings.json")
rw.LOG_FILE = common.home_path(CFG_B, "logs", "watcher.log")
rw.PID_FILE = os.path.join(WDIR, "watcher.pid")
rw.CONFIG_ERROR = None
rw.CFG.update(telegram_token=SECRETS.get("telegram_token", ""), chat_id=str(SECRETS.get("telegram_chat_id", "")),
              machine_name=CFG_B.get("machine_name") or rw.CFG.get("machine_name") or socket.gethostname())
_saved = common.read_json(rw.SETTINGS_FILE, {}) or {}
rw.CFG.update({k: v for k, v in _saved.items() if k in rw.USER_DEFAULTS})
LOCK_PORT = 47292
C4D_STATUS_DIR = common.home_path(CFG_B, "state", "c4d")
SUP_STATUS = common.home_path(CFG_B, "state", "supervisor.json")
EVENTS = common.home_path(CFG_B, "state", "events.jsonl")
REQ_DIR = common.home_path(CFG_B, "state", "requests")
URL_FILE = common.home_path(CFG_B, "connector-url.txt")
VAULT = CFG_B.get("vault", "")
log = rw.log

LOUD_EVENTS = {"crash", "hang", "loop", "launch_fail", "port", "closed_unknown", "child", "url"}
QUIET_EVENTS = {"launch", "port_ok", "mode", "dialog"}
# the bridge's own housekeeping (code updates, jobs, restarts) is not for the chat: the bot is about
# the programs and the renders. These stay in <home>/logs/supervisor.log and state/events.jsonl.
HIDDEN_EVENTS = {"update", "update_bad", "job", "job_wait", "job_fail", "start"}
HELLO_EVERY = 12 * 3600          # the "on air" message (it brings the keyboard back) at most twice a day
APP_EMOJI = {"ok": "🟢", "running, MCP off": "🟡", "starting": "🟡", "waiting": "⏳", "hung": "🧊",
             "closed": "⚪", "parked": "⚪", "paused": "🛑", "no exe": "❌"}


def _b(text, data):
    return {"text": text, "callback_data": data}


# the keyboard under the chat: button text -> what it does
MENU = [["🔌 Мост", "🛡 Guard", "🧩 Программы"],
        ["🎞 Рендер", "🖼 Превью", "🎬 Видео"],
        ["🚀 Запустить", "⚙️ Настройки", "🔗 Адрес"]]
MENU_ACTIONS = {"🔌 мост": "bridge", "🛡 guard": "guard", "🧩 программы": "apps", "🎞 рендер": "renders",
                "🖼 превью": "/preview", "🎬 видео": "/video", "🚀 запустить": "run", "⚙️ настройки": "/settings",
                "🔗 адрес": "url"}
TYPED = {"/bridge": "bridge", "мост": "bridge", "/guard": "guard", "guard": "guard", "/mode": "guard",
         "режим": "guard", "/apps": "apps", "программы": "apps", "/run": "run", "/url": "url", "адрес": "url",
         "/renders": "renders", "рендеры": "renders", "/help": "help", "помощь": "help", "/menu": "menu",
         "/start": "menu", "меню": "menu", "/keyboard": "menu"}
GUARD = [("off", "⏸", "off"), ("on", "🛡", "on"), ("keep", "🔒", "keep")]


def keyboard():
    return {"keyboard": [[{"text": x} for x in r] for r in MENU], "resize_keyboard": True, "is_persistent": True,
            "input_field_placeholder": "кнопки внизу ↓"}


def edit_or_send(msg, text, rows):
    markup = json.dumps({"inline_keyboard": rows}, ensure_ascii=False)
    if msg:
        try:
            rw.tg("editMessageText", {"chat_id": rw.CFG["chat_id"], "message_id": msg["message_id"],
                                      "text": text, "reply_markup": markup})
            return
        except Exception:
            pass  # "message is not modified"
    rw.tg("sendMessage", {"chat_id": rw.CFG["chat_id"], "text": text, "reply_markup": markup,
                          "disable_notification": "true"})


# ------------------------------------------------------------------ several C4D heartbeats
def pick_status(job_pid=None):
    """The heartbeat to follow: the job's own process, else a Cinema that renders, else the freshest."""
    sts = []
    for f in glob.glob(os.path.join(C4D_STATUS_DIR, "status_*.json")):
        st = common.read_json(f, None)
        if isinstance(st, dict) and st.get("pid"):
            sts.append(st)
    if not sts:
        return None
    if job_pid:
        for st in sts:
            if st.get("pid") == job_pid:
                return st
    now = time.time()
    fresh = [s for s in sts if now - s.get("time", 0) < rw.CFG["hang_sec"]]
    rendering = [s for s in fresh if s.get("rendering") and not s.get("closed")]
    pool = rendering or fresh or sts
    return max(pool, key=lambda s: s.get("time", 0))


def cleanup_status_files():
    now = time.time()
    for f in glob.glob(os.path.join(C4D_STATUS_DIR, "status_*.json")):
        try:
            if now - os.path.getmtime(f) > 86400:
                os.remove(f)
        except OSError:
            pass


# ------------------------------------------------------------------ folder renders
class FolderRenders:
    """Image sequences that appear in the watched folders (Houdini / Nuke / Fusion / any renderer)."""

    IDLE_MIN = 180          # s without a new frame before "finished" (or 3x the average frame time)

    def __init__(self, watcher):
        self.w = watcher
        self.since = time.time()
        self.dir_mtime = {}
        self.seqs = {}       # dir -> {"files": {name: mtime}, "first", "newest", "announced", "notified"}
        self.videos = {}     # mp4 path -> (size, first_seen)
        self.sent_videos = set()

    def roots(self):
        pats = CFG_B.get("watch_render_dirs") or ["Projects/*/*/Passes", "Projects/*/*/Output/Videos"]
        out = []
        for p in pats:
            out += [d for d in glob.glob(os.path.join(VAULT, p)) if os.path.isdir(d)]
        return out

    def c4d_dirs(self):
        job = rw.Watcher.current_view(self.w)   # the C4D job RenderWatch follows (not folder jobs)
        return {os.path.normcase(os.path.normpath(d)) for d in (rw.watch_dirs(job) if job else [])}

    def scan(self):
        now = time.time()
        skip = self.c4d_dirs()
        for root in self.roots():
            for cur, subdirs, _files in os.walk(root):
                if os.path.normpath(cur).count(os.sep) - os.path.normpath(root).count(os.sep) >= 3:
                    subdirs[:] = []
                try:
                    m = os.path.getmtime(cur)
                except OSError:
                    continue
                if m < self.since or self.dir_mtime.get(cur) == m:
                    continue
                self.dir_mtime[cur] = m
                if os.path.normcase(os.path.normpath(cur)) in skip:
                    continue      # RenderWatch already reports this C4D job
                self.read_dir(cur)
        for d, s in list(self.seqs.items()):
            self.check(d, s, now)
        self.check_videos(now)

    def read_dir(self, d):
        try:
            entries = list(os.scandir(d))
        except OSError:
            return
        for e in entries:
            if not e.is_file():
                continue
            stem, ext = os.path.splitext(e.name)
            ext = ext.lower()
            try:
                mt = e.stat().st_mtime
            except OSError:
                continue
            if mt < self.since:
                continue
            if ext in (".mp4", ".mov") and "videos" in d.lower():
                self.videos.setdefault(e.path, [e.stat().st_size, time.time()])
                continue
            if ext not in rw.IMG_EXT or not rw.FRAME_RE.search(stem):
                continue
            s = self.seqs.setdefault(d, {"files": {}, "first": mt, "newest": mt, "announced": False,
                                         "notified": 0, "finished": False})
            if e.name not in s["files"]:
                s["finished"] = False
            s["files"][e.name] = mt
            s["newest"] = max(s["newest"], mt)
            s["first"] = min(s["first"], mt)

    def job(self, d, s):
        name = os.path.relpath(d, VAULT) if VAULT and d.lower().startswith(VAULT.lower()) else d
        return {"mode": "folder", "doc": name, "frames": None, "out_dirs": [d], "started": s["first"] - 1,
                "fps": float(CFG_B.get("folder_render_fps", 25))}

    def check(self, d, s, now):
        n = len(s["files"])
        if s["finished"]:
            return
        if not s["announced"] and n >= 2:
            s["announced"] = True
            rw.send("▶️ Рендер в папке\n📁 %s\n(%s, новые кадры появляются)" % (self.job(d, s)["doc"], guess_app(d)),
                    "start" in rw.CFG["silent_events"])
        every = int(rw.CFG["notify_frames"])
        if s["announced"] and every > 0 and n // every > s["notified"] // every:
            avg = (s["newest"] - s["first"]) / max(n - 1, 1)
            text = "🎞 Кадр готов: %d\n📁 %s\nсреднее на кадр: %s" % (n, self.job(d, s)["doc"], rw.dur(avg))
            if rw.CFG["preview_frames"]:
                rw.preview_async([d], s["first"] - 1, text, "frame" in rw.CFG["silent_events"])
            else:
                rw.send(text, "frame" in rw.CFG["silent_events"])
        s["notified"] = n
        avg = (s["newest"] - s["first"]) / max(n - 1, 1)
        if s["announced"] and now - s["newest"] > max(self.IDLE_MIN, 3 * avg):
            s["finished"] = True
            took = rw.dur(s["newest"] - s["first"])
            rw.send("✅ Кадры перестали появляться — похоже, рендер готов\n📁 %s\nкадров: %d · время: %s" % (
                self.job(d, s)["doc"], n, took), "finish" in rw.CFG["silent_events"])
            if rw.CFG["video_on_finish"] and n >= 2:
                rw.video_async(self.job(d, s), "finish" in rw.CFG["silent_events"])
            self.w.last_folder_job = self.job(d, s)
        if not s["announced"] and now - s["newest"] > 600:
            del self.seqs[d]           # a single image, not a render

    def check_videos(self, now):
        for p, (size, first) in list(self.videos.items()):
            try:
                cur = os.path.getsize(p)
            except OSError:
                self.videos.pop(p, None)
                continue
            if cur != size:
                self.videos[p] = [cur, now]
                continue
            if now - first < 15 or p in self.sent_videos:
                continue
            self.sent_videos.add(p)
            self.videos.pop(p, None)
            name = os.path.relpath(p, VAULT) if VAULT else p
            if cur > 49 * 1024 * 1024:
                rw.send("🎬 Новое видео (больше 50 МБ, Telegram не примет):\n%s" % name, True)
            else:
                threading.Thread(target=rw.send_file, args=("video", p, "🎬 Новое видео\n📁 %s" % name, True),
                                 daemon=True).start()

    def text(self):
        live = [(d, s) for d, s in self.seqs.items() if s["announced"] and not s["finished"]]
        if not live:
            return "📁 Рендеров по папкам сейчас нет."
        lines = ["📁 Рендеры по папкам:"]
        for d, s in live:
            lines.append("• %s — %d кадр., последний %s назад" % (self.job(d, s)["doc"], len(s["files"]),
                                                                  rw.dur(time.time() - s["newest"])))
        return "\n".join(lines)


def bar(done, total, width=14):
    """Text progress bar: ████░░░░ ."""
    fill = int(round(width * min(done, total) / float(total))) if total else 0
    return "█" * fill + "░" * (width - fill)


def guess_app(path):
    p = path.lower()
    for key, name in (("houdini", "Houdini"), ("nuke", "Nuke"), ("fusion", "Fusion"), ("c4d", "Cinema 4D"),
                      ("redshift", "Redshift"), ("ae", "After Effects")):
        if os.sep + key in p or "/" + key in p or p.endswith(key):
            return name
    return "программа не ясна"


# ------------------------------------------------------------------ the bot
class WeaverWatcher(rw.Watcher):

    def __init__(self):
        super().__init__()
        self.folders = FolderRenders(self)
        self.last_folder_job = None
        self.ev_pos = os.path.getsize(EVENTS) if os.path.exists(EVENTS) else 0
        self.prog = None             # the live progress message of the C4D render that is running
        rw.read_status = lambda: pick_status((self.job or {}).get("pid"))

    # ---- bridge pages
    def bridge_text(self):
        st = common.read_json(SUP_STATUS, None)
        if not st:
            return "🔌 Мост: статуса нет (supervisor не запущен?)"
        age = time.time() - st.get("time", 0)
        lines = ["🔌 Weaver Bridge%s" % ("  ⚠️ статус устарел (%s) — supervisor не работает?" % rw.dur(age)
                                         if age > 60 else ""),
                 "🛡 Guard: %s" % common.MODE_TEXT.get(common.MODE_ALIASES.get(st.get("mode"), st.get("mode")),
                                                     st.get("mode")),
                 "🌐 мост (доступ Claude из облака): %s" % ("on" if st.get("bridge", True) else "off"),
                 "🌐 шлюз: %s · туннель: %s" % (st.get("gateway"), st.get("tunnel")), ""]
        for k in common.APP_ORDER + tuple(a for a in st.get("apps", {}) if a not in common.APP_ORDER):
            a = st.get("apps", {}).get(k)
            if not a:
                continue
            port = {True: " · MCP ✅", False: " · MCP ❌", None: ""}[a.get("port")]
            lines.append("%s %s — %s%s%s" % (APP_EMOJI.get(a["state"], "•"), a["label"], a["state"], port,
                                             "" if a.get("watched") else " · guard не следит"))
        return "\n".join(lines)

    def bridge_rows(self):
        on = common.read_control().get("bridge", True)
        return [[_b("🛡 Guard ›", "wb|mode"), _b("🧩 Программы ›", "wb|apps")],
                [_b("🚀 Запустить ›", "wb|runmenu"), _b("🔄 Обновить", "wb|bridge")],
                [_b("🌐 Мост: %s → %s" % (("on", "off") if on else ("off", "on")), "wb|bridgeask"),
                 _b("♻️ Перезапустить мост", "wb|restart")]]

    def bridge_ask(self):
        on = common.read_control().get("bridge", True)
        if not on:
            return self.set_bridge(True)
        return ("🌐 Выключить мост?\n\nClaude из облака перестанет видеть программы на ПК, пока не включишь "
                "обратно (здесь или на пульте в Obsidian). Бот и guard продолжат работать.",
                [[_b("Да, выключить", "wb|bridgeset:off"), _b("Нет", "wb|bridge")]])

    def set_bridge(self, on):
        ctl = common.read_control()
        ctl["bridge"] = bool(on)
        common.write_control(ctl, "telegram")
        return self.bridge_text() + "\n\n" + ("🌐 мост включаю (до 30 с)" if on else "🌐 мост выключен"), \
            self.bridge_rows()

    def mode_page(self):
        cur = common.read_control()["mode"]
        text = ("🛡 Guard — что делать с программами\n\n"
                "⏸ off — ничего не запускает и не трогает\n"
                "🛡 on — если программа упала: закрывает окно ошибки и открывает её снова со сценой. "
                "Закрыла сама — не трогает (я за компом)\n"
                "🔒 keep — держит открытыми: запускает закрытые, поднимает после падения и зависания (меня нет)\n\n"
                "Сейчас: %s" % common.MODE_TEXT[cur])
        rows = [[_b(("✅ " if cur == m else "") + icon + " " + label, "wb|setmode:" + m) for m, icon, label in GUARD]]
        return text, rows + [[_b("‹ Мост", "wb|bridge")]]

    def apps_page(self):
        ctl = common.read_control()
        st = common.read_json(SUP_STATUS, {}) or {}
        labels = {k: a.get("label", k) for k, a in (st.get("apps") or {}).items()}
        rows = [[_b("%s %s" % ("✅" if v else "❌", labels.get(k, k)), "wb|toggle:" + k)]
                for k, v in sorted(ctl["apps"].items(), key=lambda kv: common.APP_ORDER.index(kv[0])
                                   if kv[0] in common.APP_ORDER else 99)]
        return "🧩 За какими программами следит guard (✅ — следит)", rows + [[_b("‹ Мост", "wb|bridge")]]

    def run_page(self):
        st = common.read_json(SUP_STATUS, {}) or {}
        rows = [[_b("🚀 %s" % a.get("label", k), "wb|run:" + k)] for k, a in (st.get("apps") or {}).items()
                if not a.get("pids")]
        return ("🚀 Запустить программу (то, что уже открыто, не показано)",
                (rows or [[_b("всё уже открыто", "wb|bridge")]]) + [[_b("‹ Мост", "wb|bridge")]])

    def request_run(self, key, doc=None):
        os.makedirs(REQ_DIR, exist_ok=True)
        with open(os.path.join(REQ_DIR, "launch_%s.txt" % key), "w", encoding="utf-8") as f:
            f.write(doc or "")

    # ---- incoming
    def handle_update(self, u):
        cq = u.get("callback_query")
        if cq and (cq.get("data") or "").startswith("wb|"):
            msg = cq.get("message") or {}
            if str(msg.get("chat", {}).get("id")) == str(rw.CFG["chat_id"]):
                self.wb_button(cq, msg)
            return
        m = u.get("message") or {}
        if not cq and str(m.get("chat", {}).get("id")) == str(rw.CFG["chat_id"]):
            txt = (m.get("text") or "").strip()
            low = txt.lower()
            act = MENU_ACTIONS.get(low)
            if act and self.alarm:
                self.stop_alarm(announce=True)        # any button also silences an alarm
            if act and act.startswith("/"):
                m["text"] = act                       # RenderWatch's own commands
                return super().handle_update(u)
            act = act or TYPED.get(low)
            if low.startswith("/run ") and len(txt) > 5:
                arg = txt[5:].strip().lower()
                self.request_run(arg)
                return rw.send("🚀 Попросила guard запустить %s" % arg, True)
            if act:
                return self.menu_action(act)
        return super().handle_update(u)

    def menu_action(self, act):
        if act == "bridge":
            return edit_or_send(None, self.bridge_text(), self.bridge_rows())
        if act == "guard":
            return edit_or_send(None, *self.mode_page())
        if act == "apps":
            return edit_or_send(None, *self.apps_page())
        if act == "run":
            return edit_or_send(None, *self.run_page())
        if act == "url":
            try:
                url = open(URL_FILE, encoding="utf-8").read().strip()
            except OSError:
                url = ""
            return rw.send(("🔗 Адрес коннектора (секрет, никому не пересылай):\n%s" % url) if url
                           else "Адреса пока нет (туннель не поднялся?)", True)
        if act == "renders":
            return rw.send(self.folders.text() + "\n\n" + self.status_text(), True)
        if act == "help":
            return rw.send(HELP, True, keyboard())
        return rw.send("Кнопки — внизу чата ↓", True, keyboard())

    def wb_button(self, cq, msg):
        action = cq["data"][3:]
        note = ""
        if action.startswith("setmode:"):
            ctl = common.read_control()
            ctl["mode"] = action[8:]
            common.write_control(ctl, "telegram")
            note = "Guard: " + ctl["mode"]
            text, rows = self.mode_page()
        elif action.startswith("toggle:"):
            ctl = common.read_control()
            k = action[7:]
            ctl["apps"][k] = not ctl["apps"].get(k, False)
            common.write_control(ctl, "telegram")
            text, rows = self.apps_page()
        elif action.startswith("run:"):
            self.request_run(action[4:])
            note = "Запускаю " + action[4:]
            text, rows = self.run_page()
        elif action.startswith("runscene:"):
            key, _, doc = action[9:].partition("|")
            self.request_run(key, self.pending_docs.get(doc))
            note = "Запускаю " + key
            text, rows = self.bridge_text(), self.bridge_rows()
        elif action == "restart":
            os.makedirs(REQ_DIR, exist_ok=True)
            open(os.path.join(REQ_DIR, "restart.txt"), "w").close()
            note = "Перезапускаю мост, ~30 с"
            text, rows = self.bridge_text() + "\n\n♻️ перезапускаю мост (программы не трогаю)", self.bridge_rows()
        elif action == "bridgeask":
            text, rows = self.bridge_ask()
        elif action.startswith("bridgeset:"):
            text, rows = self.set_bridge(action[10:] == "on")
            note = "Мост: " + action[10:]
        elif action == "mode":
            text, rows = self.mode_page()
        elif action == "apps":
            text, rows = self.apps_page()
        elif action == "runmenu":
            text, rows = self.run_page()
        else:
            text, rows = self.bridge_text(), self.bridge_rows()
        try:
            rw.tg("answerCallbackQuery", {"callback_query_id": cq["id"], "text": note})
        except Exception:
            pass
        edit_or_send(msg, text, rows)

    pending_docs = {}

    # ---- supervisor events -> chat
    def events_tick(self):
        try:
            size = os.path.getsize(EVENTS)
        except OSError:
            return
        if size < self.ev_pos:
            self.ev_pos = 0          # rotated
        if size == self.ev_pos:
            return
        with open(EVENTS, encoding="utf-8", errors="ignore") as f:
            f.seek(self.ev_pos)
            lines = f.readlines()
            self.ev_pos = f.tell()
        for line in lines:
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            kind, text = ev.get("kind"), ev.get("text", "")
            if kind in HIDDEN_EVENTS or (kind == "url" and not ev.get("changed")):
                continue
            markup = None
            if kind == "closed_unknown" and ev.get("app"):
                tag = str(len(self.pending_docs))
                self.pending_docs[tag] = ev.get("doc")
                markup = {"inline_keyboard": [[_b("🚀 Запустить" + (" со сценой" if ev.get("doc") else ""),
                                                 "wb|runscene:%s|%s" % (ev["app"], tag))]]}
            if (kind == "crash" and "crash" in rw.CFG["alarm_events"] and not self.job
                    and not self.restart and not self.alarm):
                self.raise_alarm("crash", text)   # same alarm waves as RenderWatch (when no render runs)
            else:
                rw.send(text, kind in QUIET_EVENTS, markup)

    # ---- one live message: bar with rendered / total frames, edited in place
    def _ptext(self, body):
        return "🖥 %s\n%s" % (rw.CFG["machine_name"], body)

    def _pbody(self, job, sc, state=""):
        exp = rw.expected(job)
        done = sc["frames"]
        if exp:
            line = "%s  %d из %d · %d%%" % (bar(done, exp), min(done, exp), exp, int(100 * min(done, exp) / exp))
        else:
            line = "кадров записано: %d" % done
        head = {"done": "✅ Рендер готов", "stopped": "⏹ Рендер остановлен"}.get(state, "🎞 Идёт рендер")
        tail = "" if state else rw.eta(job, sc)
        return "%s\n📄 %s\n%s%s" % (head, job.get("doc") or "?", line, tail)

    def progress_tick(self, now):
        p = self.prog
        job = self.job
        if job is None:
            if p and not p.get("closed"):
                job = p["job"]
                sc = rw.scan(rw.watch_dirs(job), job["started"])
                exp = rw.expected(job)
                state = "done" if (exp and sc["frames"] >= exp) else "stopped"
                self._pedit(p, self._pbody(job, sc, state))
                p["closed"] = True
            return
        if not rw.watch_dirs(job):
            return
        key = rw.job_key(job)
        if p is None or p["key"] != key:
            sc = rw.scan(rw.watch_dirs(job), job["started"])
            text = self._pbody(job, sc)
            mid = self._psend(text)
            self.prog = p = {"key": key, "mid": mid, "text": text, "t": now, "job": job, "closed": False}
            return
        if now - p["t"] < 10:                   # Telegram: do not edit more often than every few seconds
            return
        p["t"] = now
        p["job"] = job
        sc = rw.scan(rw.watch_dirs(job), job["started"])
        self._pedit(p, self._pbody(job, sc))

    def _psend(self, body):
        params = {"chat_id": rw.CFG["chat_id"], "text": self._ptext(body), "disable_notification": "true"}
        try:
            return rw.tg("sendMessage", params).get("result", {}).get("message_id")
        except Exception as e:
            log("progress send: %s" % e)
            return None

    def _pedit(self, p, body):
        if body == p.get("text"):
            return
        p["text"] = body
        if not p.get("mid"):
            p["mid"] = self._psend(body)
            return
        try:
            rw.tg("editMessageText", {"chat_id": rw.CFG["chat_id"], "message_id": p["mid"], "text": self._ptext(body)})
        except Exception as e:
            log("progress edit: %s" % e)        # e.g. the message was deleted: next time a new one is sent
            p["mid"] = None

    def tick(self, now=None):
        super().tick(now)
        try:
            with self.lock:
                self.events_tick()
                self.progress_tick(now or time.time())
        except Exception as e:
            log("events: %s" % e)

    def folders_loop(self):
        while True:
            time.sleep(15)
            try:
                with self.lock:
                    self.folders.scan()
            except Exception as e:
                log("folders: %s" % e)

    def current_view(self):
        return super().current_view() or self.last_folder_job


HELP = ("Всё — кнопками внизу чата:\n"
        "🔌 Мост — что открыто и подключено; там же мост on/off\n"
        "🛡 Guard — off / on / keep\n"
        "🧩 Программы — за какими следит guard\n"
        "🚀 Запустить — открыть программу на ПК\n"
        "🎞 Рендер · 🖼 Превью · 🎬 Видео — рендер сейчас, последний кадр, видео из кадров\n"
        "⚙️ Настройки — уведомления, тревоги, авторестарт рендера\n"
        "🔗 Адрес — адрес коннектора для claude.ai (секрет)\n\n"
        "Пропали кнопки — нажми ☰ Меню → «Кнопки» или /menu.")


def main():
    if not (rw.CFG["telegram_token"] and rw.CFG["chat_id"]):
        sys.exit("telegram_token / telegram_chat_id are empty in secrets.json (py install.py --telegram)")
    lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        lock.bind(("127.0.0.1", LOCK_PORT))
    except OSError:
        sys.exit("weaver_watcher is already running")
    with open(rw.PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    cleanup_status_files()
    try:
        rw.tg("setMyCommands", {"commands": json.dumps([
            {"command": "menu", "description": "Кнопки"},
            {"command": "help", "description": "Что умеет бот"}], ensure_ascii=False)})
    except Exception as e:
        log("commands menu: %s" % e)
    log("weaver_watcher started")
    w = WeaverWatcher()
    hello = os.path.join(WDIR, "hello.txt")
    try:
        last = float(open(hello).read().strip())
    except (OSError, ValueError):
        last = 0.0
    if time.time() - last > HELLO_EVERY:
        rw.send("🟢 weaver_watcher на связи (RenderWatch %s внутри)\nКнопки — внизу чата ↓" % rw.VERSION, True,
                keyboard())
        with open(hello, "w") as f:
            f.write(str(time.time()))
    threading.Thread(target=w.updates_loop, daemon=True).start()
    threading.Thread(target=w.alarm_loop, daemon=True).start()
    threading.Thread(target=w.folders_loop, daemon=True).start()
    while True:
        try:
            w.tick()
        except Exception as e:
            log("loop: %s" % e)
        time.sleep(rw.CFG["check_every_sec"])


if __name__ == "__main__":
    main()
