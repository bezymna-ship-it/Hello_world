"""Weaver: tidy the vault into 4 visible folders (2026-10-01). Nothing is deleted - old things go to _archive/.

Close Obsidian, then in cmd:
    cd /d G:\\todoist_obsidian_claude
    py Studio_bridge\\weaver_bridge\\reorg_vault.py          dry run: prints the plan, changes nothing
    py Studio_bridge\\weaver_bridge\\reorg_vault.py --go     do it (and restart the bridge with the new code)

Visible in Obsidian afterwards:
    Projects/        tasks
    Library/         refs, tutorials, ...
    Weaver/          Weaver.md (home page) + Правила.md (the agents' rules, edited by the user)
    Studio_bridge/   Studio_bridge.md - the bridge panel with all the buttons (guard, bridge, programs)
Hidden (CSS snippet weaver-hide + Excluded files), still in place for the agents:
    weaver_claude/ (core, PC map, skills, cmd_claude), Studio_bridge/weaver_bridge/ (the bridge code - it does
    NOT move, so the installed bridge, hooks and Windows autostart keep working), Agent/, Eagle_lib/, _archive/
Log: Agent/Migrations/2026-10-01-reorg/log.md
"""
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(os.path.dirname(HERE))
NEXT = "Studio_bridge/weaver_bridge/vault_next"
DAY = "2026-10-01"
ARCH = "_archive/" + DAY
TG_NOTE = "Projects/claude/Tree_growth/Context/Как устроено.md"

MOVES = [
    # (from, to, why)
    ("weaver_claude/01_rules.md", "Weaver/Правила.md", "правила агентов - на виду, в Weaver"),
    ("Weaver.md", ARCH + "/Weaver-old.md", "старая главная (новая - Weaver/Weaver.md)"),
    ("Studio_bridge/Studio_bridge.md", ARCH + "/Studio_bridge-old-card.md", "карточка старого моста (новый пульт ниже)"),
    ("Studio_bridge/weaver_bridge/weaver_bridge.md", ARCH + "/weaver_bridge-card.md", "пульт переехал в Studio_bridge.md"),
    ("Studio_bridge/weaver_bridge/tidy_vault.py", ARCH + "/scripts/tidy_vault.py", "заменён этим скриптом"),
    ("weaver_claude/reorg_vault.py", ARCH + "/scripts/reorg_vault-v1.py", "заменён этим скриптом"),
    ("weaver_claude/weaver_claude.md", ARCH + "/weaver_claude-card.md", "его плитки теперь в Weaver.md"),
    ("weaver_claude/_next/Weaver.md", ARCH + "/scripts/Weaver-next-v1.md", "черновик, заменён новым"),
    ("Studio_bridge/test_claude_v02-claude-mcp-cinema-houdini-cloud-fvh761", ARCH + "/studio-bridge-old",
     "старый мост, копия репозитория с venv"),
    ("Studio_bridge/RenderWatch", ARCH + "/RenderWatch", "RenderWatch 2.0 - уже внутри бота weaver_watcher"),
    ("Studio_bridge/Output", ARCH + "/Studio_bridge-Output", "лишняя папка Output у моста"),
    ("weaver_claude/Claude outputs", "Agent/Inbox/Claude outputs", "выгрузки облачных сессий - сырьё, не правила"),
    ("weaver_claude/skills/tree-growth.md", TG_NOTE, "знание одной задачи - в саму задачу"),
    ("Agent/Agent Context.md", ARCH + "/agent-old/Agent Context.md", "80 КБ истории - сведено в weaver_claude"),
    ("Agent/START.md", ARCH + "/agent-old/START.md", "заменён weaver_claude/00_start.md"),
    ("Agent/MAP.md", ARCH + "/agent-old/MAP.md", "заменён weaver_claude/02_map.md"),
    ("Agent/Workflow.md", ARCH + "/agent-old/Workflow.md", "устарел, сведён в skills/weaver-system"),
    ("Agent/Pending_rule_changes_20261001.md", ARCH + "/agent-old/Pending_rule_changes_20261001.md", "правки уже в Правилах"),
    (".claude/rules", ARCH + "/claude-old/rules", "старые правила Claude Code - сведены в Правила"),
    (".claude/skills", ARCH + "/claude-old/skills", "старые копии скиллов - источник теперь weaver_claude/skills"),
    (".agents/skills", ARCH + "/agents-old/skills", "копии скиллов для Codex - теперь AGENTS.md -> weaver_claude"),
    ("weaver_claude/cmd_claude/.claude/skills", ARCH + "/cmd_claude-skills", "третьи копии старых скиллов"),
]
PUT = [
    # (prepared file, target): an existing target is first copied to Agent/History/<day>/reorg/
    (NEXT + "/Weaver.md", "Weaver/Weaver.md"),
    (NEXT + "/Studio_bridge.md", "Studio_bridge/Studio_bridge.md"),
    (NEXT + "/weaver-hide.css", ".obsidian/snippets/weaver-hide.css"),
    ("weaver_claude/_next/CLAUDE.md", "CLAUDE.md"),
    ("weaver_claude/_next/AGENTS.md", "AGENTS.md"),
    ("weaver_claude/cmd_claude/start_claude.bat.txt", "weaver_claude/cmd_claude/start_claude.bat"),
]
REPLACE = [
    # paths first, then words
    ("| `weaver_claude/bridge/` | мост облако → ПК: код, пульт `weaver_bridge.md`, `control.json` |",
     "| `Studio_bridge/` | мост облако → ПК: пульт `Studio_bridge.md` (guard, мост, программы); код и `control.json` "
     "— в скрытой `weaver_bridge/` |"),
    ("| `weaver_claude/` | правила, карта ПК", "| `Weaver/` | главная `Weaver.md`, правила `Правила.md` |\n"
     "| `weaver_claude/` (скрыта) | ядро, карта ПК"),
    ("Studio_bridge/weaver_bridge/weaver_bridge.md", "Studio_bridge/Studio_bridge.md"),
    ("Studio_bridge/weaver_bridge/weaver_bridge", "Studio_bridge/Studio_bridge"),
    ("weaver_claude/bridge/", "Studio_bridge/weaver_bridge/"),
    ("weaver_claude/bridge", "Studio_bridge/weaver_bridge"),
    ("weaver_claude\\bridge", "Studio_bridge\\weaver_bridge"),
    ("weaver_claude/01_rules.md", "Weaver/Правила.md"),
    ("weaver_claude/01_rules", "Weaver/Правила"),
    ("weaver_claude\\01_rules.md", "Weaver\\Правила.md"),
    ("weaver_claude/weaver_claude.md", "Weaver/Weaver.md"),
    ("weaver_claude/weaver_claude", "Weaver/Weaver"),
    ("weaver_claude/skills/tree-growth", TG_NOTE[:-3]),
    ("01_rules", "Правила"),
    ("off / crash / keep", "off / on / keep"),
    ("off/crash/keep", "off/on/keep"),
    ('edit the rules there: Weaver/Правила.md', 'the rules the user edits: Weaver/Правила.md'),
    ('for gen in ("Agent/STATE.md", "Agent/PROJECTS.md"):', 'for gen in ("Agent/STATE.md",):'),
]
WORDS = [(re.compile(r"\bСторож(а|ем|у|е)?\b"), "Guard"), (re.compile(r"\bсторож(а|ем|у|е)?\b"), "guard")]
REPLACE_IN = ["weaver_claude", "Weaver", "Studio_bridge/weaver_bridge", "Library/Library.md", "CLAUDE.md", "AGENTS.md"]
REPLACE_EXT = (".md", ".py", ".txt")
SKIP_DIRS = {"__pycache__", ".venv", "vault_next", "cmd_claude", "apps"}
SKIP_FILES = {"reorg_vault.py", "render_watchdog_base.py", "_sources.md"}
IGNORE_ADD = ["_archive/", "__pycache__/"]
SNIPPET = "weaver-hide"

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


def venv(name):
    try:
        home = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8-sig")).get("home")
    except Exception:
        home = None
    exe = os.path.join(home or r"C:\weaver_bridge", "venv", "Scripts", name)
    return exe if os.path.isfile(exe) else sys.executable


def main():
    say("# Уборка хранилища %s — %s\n" % (DAY, "ВЫПОЛНЕНО" if GO else "сухой прогон (ничего не меняется)"))
    if GO and obsidian_running():
        sys.exit("Закрой Obsidian и запусти ещё раз (он перезаписывает свои настройки и держит файлы).")

    say("## 1. Переносы")
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

    say("\n## 2. Новые файлы: главная, пульт, CLAUDE.md, AGENTS.md, скрытие, start_claude.bat")
    for new, target in PUT:
        n, t = p(new), p(target)
        if not os.path.exists(n):
            say("- пропуск (нет): `%s`" % new)
            continue
        say("- `%s` ← `%s`%s" % (target, new, " (старый → Agent/History/%s/reorg/)" % DAY if os.path.exists(t) else ""))
        if GO:
            if os.path.exists(t):
                shutil.copy2(t, hist(target))
            os.makedirs(os.path.dirname(t), exist_ok=True)
            os.replace(n, t)
    if GO:
        for d in ("weaver_claude/_next", NEXT):
            if os.path.isdir(p(d)) and not os.listdir(p(d)):
                os.rmdir(p(d))

    say("\n## 3. Пути и слова в заметках и коде (weaver_claude/bridge → Studio_bridge, 01_rules → Правила, сторож → guard)")
    n_files = 0
    for r in REPLACE_IN:
        root_path = p(r)
        if not os.path.exists(root_path):
            continue
        walk = [(os.path.dirname(root_path), [], [os.path.basename(root_path)])] if os.path.isfile(root_path) \
            else os.walk(root_path)
        for root, dirs, files in walk:
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                if not f.endswith(REPLACE_EXT) or f in SKIP_FILES:
                    continue
                path = os.path.join(root, f)
                try:
                    text = open(path, encoding="utf-8").read()
                except (OSError, UnicodeDecodeError):
                    continue
                new = text
                for a, b in REPLACE:
                    new = new.replace(a, b)
                if f.endswith(".md"):
                    for rx, b in WORDS:
                        new = rx.sub(b, new)
                if new != text:
                    n_files += 1
                    say("- `%s`" % os.path.relpath(path, VAULT).replace(os.sep, "/"))
                    if GO:
                        shutil.copy2(path, hist(os.path.relpath(path, VAULT).replace(os.sep, "/")))
                        with open(path, "w", encoding="utf-8", newline="") as fh:
                            fh.write(new)
    if not n_files:
        say("- нечего менять")

    say("\n## 4. Obsidian: исключённые файлы %s, фрагмент CSS «%s» включён" % (", ".join(IGNORE_ADD), SNIPPET))
    app_json = p(".obsidian/app.json")
    try:
        cfg = json.load(open(app_json, encoding="utf-8"))
    except Exception:
        cfg = {}
    flt = cfg.get("userIgnoreFilters", [])
    add = [x for x in IGNORE_ADD if x not in flt]
    say("- исключения: " + ("уже есть" if not add else "добавить " + ", ".join(add)))
    ap_json = p(".obsidian/appearance.json")
    try:
        ap = json.load(open(ap_json, encoding="utf-8"))
    except Exception:
        ap = {}
    snip_on = SNIPPET in ap.get("enabledCssSnippets", [])
    say("- фрагмент CSS: " + ("уже включён" if snip_on else "включить"))
    if GO:
        if add:
            shutil.copy2(app_json, hist(".obsidian/app.json"))
            cfg["userIgnoreFilters"] = flt + add
            json.dump(cfg, open(app_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        if not snip_on:
            if os.path.exists(ap_json):
                shutil.copy2(ap_json, hist(".obsidian/appearance.json"))
            ap["enabledCssSnippets"] = ap.get("enabledCssSnippets", []) + [SNIPPET]
            json.dump(ap, open(ap_json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    say("\n## 5. Пустые папки")
    for d in (".agents", "weaver_claude/_next"):
        if os.path.isdir(p(d)):
            left = os.listdir(p(d))
            if GO and not left:
                os.rmdir(p(d))
                say("- `%s` — пустая, убрана" % d)
            else:
                say("- `%s`: %s" % (d, "останется: " + ", ".join(left) if left else "уберу, когда опустеет"))

    say("\n## 6. Перезапуск моста с новым кодом (guard on/off/keep, кнопки в боте). Программы не закрываются.")
    if GO:
        sup = os.path.join(HERE, "supervisor.py")
        subprocess.run([venv("python.exe"), sup, "stop"])
        for _ in range(30):                       # wait until the old supervisor has let its lock go
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.bind(("127.0.0.1", 47290))
                break
            except OSError:
                time.sleep(1)
            finally:
                s.close()
        flags = (0x00000008 | 0x00000200) if os.name == "nt" else 0
        subprocess.Popen([venv("pythonw.exe"), sup], cwd=HERE, creationflags=flags, close_fds=True)
        say("- мост запущен заново; через ~30 с бот пришлёт «на связи» с кнопками")

    say("\n" + ("Готово. Открой Obsidian: слева Projects · Library · Weaver · Studio_bridge." if GO
                else "Это сухой прогон. Выполнить: закрой Obsidian → py Studio_bridge\\weaver_bridge\\reorg_vault.py --go"))
    if GO:
        out = p("Agent/Migrations/" + DAY + "-reorg")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "log.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(LOG) + "\n")
        print("\nЖурнал: Agent/Migrations/%s-reorg/log.md" % DAY)


if __name__ == "__main__":
    main()
