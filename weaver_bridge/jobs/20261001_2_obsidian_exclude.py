"""One-off bridge job: hide _archive/ and __pycache__/ from Obsidian search ("Excluded files").
Obsidian rewrites its settings while it runs, so this waits (exit 75) until Obsidian is closed."""
import json
import os
import shutil
import subprocess
import sys
import time

VAULT = os.environ.get("WEAVER_VAULT") or os.getcwd()
ADD = ["_archive/", "__pycache__/"]
if os.name == "nt":
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Obsidian.exe", "/NH"], capture_output=True, text=True).stdout
    if "obsidian.exe" in out.lower():
        print("допишу исключения Obsidian, когда он будет закрыт")
        sys.exit(75)
path = os.path.join(VAULT, ".obsidian", "app.json")
try:
    cfg = json.load(open(path, encoding="utf-8"))
except Exception:
    cfg = {}
flt = cfg.get("userIgnoreFilters", [])
add = [x for x in ADD if x not in flt]
if add:
    hist = os.path.join(VAULT, "Agent", "History", time.strftime("%Y-%m-%d"))
    os.makedirs(hist, exist_ok=True)
    if os.path.exists(path):
        shutil.copy2(path, os.path.join(hist, time.strftime("%H%M%S_") + "app.json"))
    cfg["userIgnoreFilters"] = flt + add
    json.dump(cfg, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("исключено из поиска Obsidian: " + (", ".join(add) if add else "уже было"))
