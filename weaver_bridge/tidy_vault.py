"""Weaver: tidy the vault (2026-10-01). Nothing is deleted - old things go to _archive/, hidden in Obsidian.

    py tidy_vault.py          dry run: prints what would happen
    py tidy_vault.py --go     do it (close Obsidian first: it overwrites .obsidian/app.json on exit)

Log: Agent/Migrations/2026-10-01-tidy/log.md
"""
import json
import os
import shutil
import subprocess
import sys
import time

VAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DAY = "2026-10-01"
ARCH = "_archive/" + DAY
MOVES = [
    ("Studio_bridge/test_claude_v02-claude-mcp-cinema-houdini-cloud-fvh761", ARCH + "/studio-bridge-old",
     "старый мост (заменён weaver_bridge), копия репозитория с venv"),
    ("Studio_bridge/RenderWatch", ARCH + "/RenderWatch", "RenderWatch 2.0 - уже внутри бота weaver_watcher"),
    ("Studio_bridge/Output", ARCH + "/Studio_bridge-Output", "лишняя папка Output у моста (1 картинка)"),
    ("weaver_claude/Claude outputs", "Agent/Inbox/Claude outputs", "выгрузки облачных сессий - сырьё, не правила"),
    ("Agent/Pending_rule_changes_20261001.md", "Agent/History/" + DAY + "/Pending_rule_changes_20261001.md",
     "правки уже перенесены в weaver_claude/01_rules"),
]
REPLACE = [  # (new file, target): the target's old version goes to Agent/History
    ("weaver_claude/cmd_claude/start_claude.bat.txt", "weaver_claude/cmd_claude/start_claude.bat",
     "запуск Claude Code после переноса cmd_claude в weaver_claude"),
]
IGNORE_ADD = ["_archive/", "__pycache__/"]
FIND = ["test_claude_v02-claude-mcp", "Studio_bridge/RenderWatch", "Studio_bridge\\RenderWatch", "Claude outputs"]
SKIP_DIRS = {".git", ".obsidian", "_archive", "History", "Migrations", "Eagle_lib", "node_modules", ".venv",
             "__pycache__", ".cache", "gsg_sheets", "apps"}

GO = "--go" in sys.argv
LOG = []


def say(msg):
    print(msg)
    LOG.append(msg)


def p(rel):
    return os.path.join(VAULT, *rel.split("/"))


def obsidian_running():
    if os.name != "nt":
        return False
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Obsidian.exe", "/NH"], capture_output=True, text=True).stdout
    return "obsidian.exe" in out.lower()


def main():
    say("# Уборка хранилища %s — %s\n" % (DAY, "ВЫПОЛНЕНО" if GO else "сухой прогон (ничего не меняется)"))
    say("Хранилище: %s\n" % VAULT)

    say("## Переносы")
    for src, dst, why in MOVES:
        s, d = p(src), p(dst)
        if not os.path.exists(s):
            say("- пропуск (нет): `%s`" % src)
            continue
        if os.path.exists(d):
            say("- пропуск (уже есть): `%s`" % dst)
            continue
        say("- `%s` → `%s` — %s" % (src, dst, why))
        if GO:
            os.makedirs(os.path.dirname(d), exist_ok=True)
            try:
                os.rename(s, d)
            except OSError as exc:
                say("  ! не перенесено: %s (файл открыт в программе? закрой и запусти ещё раз)" % exc)

    say("\n## Замены файлов")
    for new, target, why in REPLACE:
        n, t = p(new), p(target)
        if not os.path.exists(n):
            say("- пропуск (нет): `%s`" % new)
            continue
        say("- `%s` ← `%s` — %s (старый → Agent/History/%s/)" % (target, new, why, DAY))
        if GO:
            hist = p("Agent/History/" + DAY)
            os.makedirs(hist, exist_ok=True)
            if os.path.exists(t):
                shutil.copy2(t, os.path.join(hist, time.strftime("%H%M%S_") + os.path.basename(t)))
            os.replace(n, t)

    say("\n## Скрыть в Obsidian")
    app = p(".obsidian/app.json")
    try:
        cfg = json.load(open(app, encoding="utf-8"))
    except Exception:
        cfg = {}
    flt = cfg.get("userIgnoreFilters", [])
    add = [x for x in IGNORE_ADD if x not in flt]
    if not add:
        say("- уже скрыто: %s" % ", ".join(IGNORE_ADD))
    elif GO and obsidian_running():
        say("- ! Obsidian открыт — не трогаю app.json (он перезапишет). Закрой Obsidian и запусти `py tidy_vault.py --go` ещё раз,"
            " или вручную: Настройки → Файлы и ссылки → Исключённые файлы → добавить %s" % ", ".join(add))
    else:
        say("- добавить в исключённые файлы: %s" % ", ".join(add))
        if GO:
            shutil.copy2(app, p("Agent/History/" + DAY) + os.sep + "app.json")
            cfg["userIgnoreFilters"] = flt + add
            json.dump(cfg, open(app, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    say("\n## Где ещё упоминаются старые пути (проверить глазами, скрипт их не правит)")
    hits = 0
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f == "tidy_vault.py" or not f.endswith((".md", ".py", ".json", ".js", ".bat", ".cmd")):
                continue
            path = os.path.join(root, f)
            try:
                if os.path.getsize(path) > 2_000_000:
                    continue
                text = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            found = [x for x in FIND if x in text]
            if found:
                hits += 1
                say("- `%s`: %s" % (os.path.relpath(path, VAULT).replace(os.sep, "/"), ", ".join(found)))
    if not hits:
        say("- нигде")

    say("\n" + ("Готово. Открой Obsidian." if GO else "Это сухой прогон. Выполнить: закрой Obsidian → `py tidy_vault.py --go`."))
    if GO:
        out = p("Agent/Migrations/" + DAY + "-tidy")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "log.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(LOG) + "\n")
        print("\nЖурнал: Agent/Migrations/%s-tidy/log.md" % DAY)


if __name__ == "__main__":
    main()
