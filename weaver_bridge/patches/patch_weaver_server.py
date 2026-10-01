"""Build weaver-server/weaver_server.py from the Studio Bridge one (idempotent, run by install.py).

The only change: weaver_context loads weaver_claude/ (the consolidated rules) plus the generated
Agent/STATE.md and Agent/PROJECTS.md, and falls back to CLAUDE.md when weaver_claude/ is missing.

    python patch_weaver_server.py <old weaver_server.py> <new weaver_server.py>
"""
import sys

NEW = 'def _expand_imports(root: Path, text: str, out: list[str], depth: int = 0) -> None:\n    """Copy `text` into `out`, replacing lines `@path.md` with that file (one level of nesting)."""\n    for line in text.splitlines():\n        m = re.match(r"^@(\\S+\\.md)\\s*$", line.strip())\n        if not m:\n            out.append(line)\n            continue\n        sub = (root / m.group(1)).resolve()\n        try:\n            sub.relative_to(root)\n            body = _read_text(sub)[:40_000]\n        except (ValueError, OSError):\n            out.append(f"(unavailable: {m.group(1)})")\n            continue\n        out.append(f"\\n----- {m.group(1)} -----")\n        if depth < 1:\n            _expand_imports(root, body, out, depth + 1)\n        else:\n            out.append(body)\n        out.append(f"----- end {m.group(1)} -----\\n")\n\n\n@mcp.tool()\ndef weaver_context() -> str:\n    """Load the vault\'s entry context. Call this first when starting work.\n    Source of truth: the weaver_claude/ folder (00_start.md, rules, map, bridge) plus the generated\n    Agent/STATE.md and Agent/PROJECTS.md. Falls back to CLAUDE.md if weaver_claude/ is missing.\n    In this cloud session use the weaver__ tools instead of direct file access."""\n    root = _vroot()\n    hub = root / "weaver_claude"\n    out: list[str] = []\n    if (hub / "00_start.md").is_file():\n        out.append("# Weaver - context from weaver_claude/ (edit the rules there: weaver_claude/01_rules.md)\\n")\n        _expand_imports(root, "@weaver_claude/00_start.md", out)\n        files = sorted(p.relative_to(root).as_posix() for p in hub.rglob("*.md"))\n        out.append("\\nFiles in weaver_claude/ (read with vault_read when needed):\\n" + "\\n".join("- " + f for f in files))\n        for gen in ("Agent/STATE.md", "Agent/PROJECTS.md"):\n            if (root / gen).is_file():\n                _expand_imports(root, "@" + gen, out)\n        return "\\n".join(out)\n    entry = root / "CLAUDE.md"\n    if not entry.is_file():\n        raise FileNotFoundError(f"Neither weaver_claude/00_start.md nor CLAUDE.md found in {root}")\n    _expand_imports(root, _read_text(entry), out, depth=1)\n    return "\\n".join(out)\n\n\n'

src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()
MARK = "def _expand_imports("
if MARK not in s:
    a = s.index("@mcp.tool()\ndef weaver_context()")
    b = s.index("@mcp.tool()\ndef vault_list(")
    s = s[:a] + NEW + s[b:]
    s = s.replace('"""Weaver MCP server: the Obsidian vault', '"""Weaver MCP server (Weaver Bridge): the Obsidian vault', 1)
open(dst, "w", encoding="utf-8", newline="").write(s)
print("weaver_server.py ready")
