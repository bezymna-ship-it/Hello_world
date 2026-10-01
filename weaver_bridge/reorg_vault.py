"""Weaver: reorganise the vault (2026-10-01). Nothing is deleted - old things go to _archive/ (hidden in Obsidian).

Run from the VAULT ROOT, with Obsidian closed:
    cd /d G:\\todoist_obsidian_claude
    py weaver_claude\\reorg_vault.py          dry run: prints the plan, changes nothing
    py weaver_claude\\reorg_vault.py --go     do it

What it does:
  * Studio_bridge/weaver_bridge  -> weaver_claude/bridge   (the bridge is stopped first and re-installed after)
  * the old bridge, RenderWatch, old agent docs (START, MAP, Workflow, Agent Context), old skill copies -> _archive/
  * project-only knowledge goes into its project (tree-growth skill -> Projects/claude/Tree_growth/Context/)
  * CLAUDE.md, AGENTS.md, Weaver.md <- weaver_claude/_next/ (the old ones go to Agent/History)
  * paths in the notes and the bridge code are updated; _archive/ and __pycache__/ are hidden in Obsidian
Log: Agent/Migrations/2026-10-01-reorg/log.md
"""
import json
import os
import shutil
import subprocess
import sys
import time

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAY = "2026-10-01"
ARCH = "_archive/" + DAY
OLD_BRIDGE = "Studio_bridge/weaver_bridge"
NEW_BRIDGE = "weaver_claude/bridge"
TG_NOTE = "Projects/claude/Tree_growth/Context/Как устроено.md"

MOVES = [
    # (from, to, why)
    (OLD_BRIDGE, NEW_BRIDGE, "мост - в weaver_claude"),
    ("Studio_bridge/Context.md", NEW_BRIDGE + "/Context.md", "история моста - к мосту"),
    ("Studio_bridge/Studio_bridge.md", ARCH + "/Studio_bridge.md", "карточка старого моста (пульт - bridge/weaver_bridge.md)"),
    ("Studio_bridge/test_claude_v02-claude-mcp-cinema-houdini-cloud-fvh761", ARCH + "/studio-bridge-old",
     "старый мост, копия репозитория с venv"),
    ("Studio_bridge/RenderWatch", ARCH + "/RenderWatch", "RenderWatch 2.0 - уже внутри бота weaver_watcher"),
    ("Studio_bridge/Output", ARCH + "/Studio_bridge-Output", "лишняя папка Output у моста"),
    ("weaver_claude/Claude outputs", "Agent/Inbox/Claude outputs", "выгрузки облачных сессий - сырьё, не правила"),
    ("weaver_claude/skills/tree-growth.md", TG_NOTE, "знание одной задачи - в саму задачу"),
    ("Agent/Agent Context.md", ARCH + "/agent-old/Agent Context.md", "80 КБ истории - сведено в weaver_claude"),
    ("Agent/START.md", ARCH + "/agent-old/START.md", "заменён weaver_claude/00_start.md"),
    ("Agent/MAP.md", ARCH + "/agent-old/MAP.md", "заменён weaver_claude/02_map.md"),
    ("Agent/Workflow.md", ARCH + "/agent-old/Workflow.md", "устарел, сведён в weaver-system"),
    ("Agent/Pending_rule_changes_20261001.md", ARCH + "/agent-old/Pending_rule_changes_20261001.md",
     "правки уже в 01_rules"),
    (".claude/rules", ARCH + "/claude-old/rules", "старые правила Claude Code - сведены в 01_rules"),
    (".claude/skills", ARCH + "/claude-old/skills", "старые копии скиллов - источник теперь weaver_claude/skills"),
    (".agents/skills", ARCH + "/agents-old/skills", "копии скиллов для Codex - теперь AGENTS.md -> weaver_claude"),
    ("weaver_claude/cmd_claude/.claude/skills", ARCH + "/cmd_claude-skills", "третьи копии старых скиллов"),
]
SWAPS = [
    # (prepared file, target): the target's old version goes to Agent/History/<day>/
    ("weaver_claude/_next/CLAUDE.md", "CLAUDE.md"),
    ("weaver_claude/_next/AGENTS.md", "AGENTS.md"),
    ("weaver_claude/_next/Weaver.md", "Weaver.md"),
    ("weaver_claude/cmd_claude/start_claude.bat.txt", "weaver_claude/cmd_claude/start_claude.bat"),
]
REPLACE = [
    ("Studio_bridge/weaver_bridge", NEW_BRIDGE),
    ("Studio_bridge\\weaver_bridge", NEW_BRIDGE.replace("/", "\\")),
    ("Studio_bridge\\\\weaver_bridge", NEW_BRIDGE.replace("/", "\\\\")),
    ("weaver_claude/skills/tree-growth", TG_NOTE[:-3]),
    # the cloud entry context: the 15 KB project digest only on request
    ('for gen in ("Agent/STATE.md", "Agent/PROJECTS.md"):', 'for gen in ("Agent/STATE.md",):'),
]
REPLACE_IN = ["weaver_claude", "Library/Library.md"]       # folders / files whose text is updated
REPLACE_EXT = (".md", ".py", ".json", ".js", ".txt")
IGNORE_ADD = ["_archive/", "__pycache__/"]

GO = "--go" in sys.argv
LOG = []


def say(msg):
    print(msg, flush=True)
    LOG.append(msg)


def p(rel):
    return os.path.join(VAULT, *rel.split("/"))


def hist(name):
    d = p("Agent/History/" + DAY + "/reorg")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, time.strftime("%H%M%S_") + name.replace("/", "__"))


def obsidian_running():
    if os.name != "nt":
        return False
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Obsidian.exe", "/NH"], capture_output=True, text=True).stdout
    return "obsidian.exe" in out.lower()


def bridge_python():
    cfg = {}
    for b in (OLD_BRIDGE, NEW_BRIDGE):
        try:
            cfg = json.load(open(p(b + "/config.json"), encoding="utf-8-sig"))
            break
        except Exception:
            continue
    home = cfg.get("home", r"C:\weaver_bridge")
    py = os.path.join(home, "venv", "Scripts", "python.exe")
    return py if os.path.isfile(py) else sys.executable


def main():
    say("# Реорганизация хранилища %s — %s\n" % (DAY, "ВЫПОЛНЕНО" if GO else "сухой прогон (ничего не меняется)"))
    if os.path.normcase(os.getcwd()).startswith(os.path.normcase(p(OLD_BRIDGE))):
        sys.exit("Запусти из корня хранилища: cd /d %s, затем py weaver_claude\\reorg_vault.py" % VAULT)
    if GO and obsidian_running():
        sys.exit("Закрой Obsidian и запусти ещё раз (он перезаписывает свои настройки и держит файлы).")

    bridge_moves = os.path.isdir(p(OLD_BRIDGE)) and not os.path.exists(p(NEW_BRIDGE))
    say("## 1. Мост")
    if bridge_moves:
        say("- остановить мост (сторож, шлюз, туннель, бот; программы остаются открытыми)")
        if GO:
            subprocess.run([bridge_python(), p(OLD_BRIDGE + "/supervisor.py"), "stop"])
            time.sleep(3)
    else:
        say("- мост уже на новом месте или не найден — не трогаю")

    say("\n## 2. Переносы")
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
                say("  ! не перенесено: %s (открыто в программе или окне cmd? закрой и запусти ещё раз)" % exc)

    say("\n## 3. Новые CLAUDE.md, AGENTS.md, Weaver.md, start_claude.bat")
    for new, target in SWAPS:
        n, t = p(new), p(target)
        if not os.path.exists(n):
            say("- пропуск (нет): `%s`" % new)
            continue
        say("- `%s` ← `%s` (старый → Agent/History/%s/reorg/)" % (target, new, DAY))
        if GO:
            if os.path.exists(t):
                shutil.copy2(t, hist(target))
            os.replace(n, t)
    if GO and os.path.isdir(p("weaver_claude/_next")) and not os.listdir(p("weaver_claude/_next")):
        os.rmdir(p("weaver_claude/_next"))

    say("\n## 4. Пути в заметках и коде")
    roots = [p(x) for x in REPLACE_IN]
    if not GO and bridge_moves:
        roots.append(p(OLD_BRIDGE))          # dry run: the bridge is still at the old place
    n_files = 0
    for r in roots:
        walk = [(os.path.dirname(r), [], [os.path.basename(r)])] if os.path.isfile(r) else os.walk(r)
        for root, dirs, files in walk:
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".venv", "_next")]
            for f in files:
                if not f.endswith(REPLACE_EXT) or f == "reorg_vault.py":
                    continue
                path = os.path.join(root, f)
                try:
                    text = open(path, encoding="utf-8").read()
                except (OSError, UnicodeDecodeError):
                    continue
                new = text
                for a, b in REPLACE:
                    new = new.replace(a, b)
                if new != text:
                    n_files += 1
                    say("- `%s`" % os.path.relpath(path, VAULT).replace(os.sep, "/"))
                    if GO:
                        shutil.copy2(path, hist(os.path.relpath(path, VAULT).replace(os.sep, "/")))
                        with open(path, "w", encoding="utf-8", newline="") as fh:
                            fh.write(new)
    if not n_files:
        say("- нечего менять")

    say("\n## 5. Скрыть в Obsidian: %s" % ", ".join(IGNORE_ADD))
    app = p(".obsidian/app.json")
    try:
        cfg = json.load(open(app, encoding="utf-8"))
    except Exception:
        cfg = {}
    flt = cfg.get("userIgnoreFilters", [])
    add = [x for x in IGNORE_ADD if x not in flt]
    say("- уже скрыто" if not add else "- добавить: %s" % ", ".join(add))
    if GO and add:
        shutil.copy2(app, hist(".obsidian/app.json"))
        cfg["userIgnoreFilters"] = flt + add
        json.dump(cfg, open(app, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    say("\n## 6. Пустые папки")
    for d in ("Studio_bridge", ".agents"):
        if os.path.isdir(p(d)):
            left = os.listdir(p(d))
            if left and not GO:
                say("- `%s`: останется, если там что-то кроме переносимого (сейчас: %s)" % (d, ", ".join(left)))
            elif GO and not left:
                os.rmdir(p(d))
                say("- `%s` — пустая, убрана" % d)
            elif GO:
                say("- `%s` — не пустая (%s), оставлена" % (d, ", ".join(left)))

    say("\n## 7. Переустановить мост с нового места")
    if bridge_moves or not GO:
        say("- `py %s\\install.py` — пути, автозапуск с Windows, перезапуск. Адрес коннектора сменится: /url в боте."
            % NEW_BRIDGE.replace("/", "\\"))
        if GO and os.path.isfile(p(NEW_BRIDGE + "/install.py")):
            subprocess.run([sys.executable, p(NEW_BRIDGE + "/install.py")], cwd=VAULT)

    say("\n" + ("Готово. Открой Obsidian; в Telegram — /url и обнови коннектор в claude.ai." if GO
                else "Это сухой прогон. Выполнить: закрой Obsidian → py weaver_claude\\reorg_vault.py --go"))
    if GO:
        out = p("Agent/Migrations/" + DAY + "-reorg")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "log.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(LOG) + "\n")
        print("\nЖурнал: Agent/Migrations/%s-reorg/log.md" % DAY)


if __name__ == "__main__":
    main()
