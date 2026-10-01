"""Shared bits of Weaver Bridge: paths, config, control switches, events (stdlib only).

Two places on the PC:
  * the vault folder  <vault>\\Studio_bridge\\weaver_bridge   code, config.json, control.json (hidden in Obsidian;
    the switches are the card Studio_bridge\\Studio_bridge.md)
    (readable and editable from the cloud through the weaver__ tools);
  * the home folder   C:\\weaver_bridge (config "home")   venvs, downloaded MCP servers, cloudflared, logs,
    state and secrets.json - NOTHING secret ever sits in the vault.
"""
from __future__ import annotations

import json
import os
import time

BRIDGE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BRIDGE_DIR, "config.json")
CONTROL_FILE = os.path.join(BRIDGE_DIR, "control.json")

# guard: what the supervisor does with the programs ("crash" is the old name of "on")
MODES = ("off", "on", "keep")
MODE_ALIASES = {"crash": "on"}
MODE_TEXT = {
    "off": "off — ничего не запускает и не трогает",
    "on": "on — поднимает программу, если она упала (закрыла сама — не трогает)",
    "keep": "keep — держит открытыми: запускает закрытые, поднимает после падения и зависания",
}
APP_ORDER = ("c4d", "c4d26", "houdini", "nuke", "fusion")


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def load_config():
    cfg = read_json(CONFIG_FILE, {}) or {}
    cfg.setdefault("home", r"C:\weaver_bridge")
    cfg.setdefault("vault", os.path.dirname(os.path.dirname(BRIDGE_DIR)))
    cfg.setdefault("gateway_port", 8765)
    cfg.setdefault("tunnel", {"type": "cloudflare"})
    cfg.setdefault("apps", {})
    return cfg


def home_path(cfg, *parts):
    return os.path.join(cfg["home"], *parts)


def load_secrets(cfg):
    return read_json(home_path(cfg, "secrets.json"), {}) or {}


def read_control():
    c = read_json(CONTROL_FILE, None)
    if not isinstance(c, dict):
        c = {}
    c["mode"] = MODE_ALIASES.get(c.get("mode"), c.get("mode"))
    if c["mode"] not in MODES:
        c["mode"] = "off"
    c.setdefault("bridge", True)
    c.setdefault("apps", {})
    return c


def write_control(c, who):
    c["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    c["updated_by"] = who
    write_json(CONTROL_FILE, c)


def log_to(path, msg, limit=500_000):
    line = "%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path) and os.path.getsize(path) > limit:
            os.replace(path, path + ".old")
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass


def emit_event(cfg, kind, text, **extra):
    """Supervisor -> bot: one JSON line per event in <home>/state/events.jsonl."""
    ev = dict(extra, time=time.time(), kind=kind, text=text)
    path = home_path(cfg, "state", "events.jsonl")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path) and os.path.getsize(path) > 2_000_000:
            os.replace(path, path + ".old")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except OSError:
        pass
