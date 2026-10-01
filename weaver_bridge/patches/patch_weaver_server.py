"""Build weaver-server/weaver_server.py from the Studio Bridge one (idempotent, run by install.py).

The only change: weaver_context loads weaver_claude/ (the consolidated rules) plus the generated
Agent/STATE.md and Agent/PROJECTS.md, and falls back to CLAUDE.md when weaver_claude/ is missing.

    python patch_weaver_server.py <old weaver_server.py> <new weaver_server.py>
"""
import sys

NEW = r'''
def _expand_imports(root: Path, text: str, out: list[str], depth: int = 0) -> None:
    """Copy `text` into `out`, replacing lines `@path.md` with that file (one level of nesting)."""
    for line in text.splitlines():
        m = re.match(r"^@(\S+\.md)\s*$", line.strip())
        if not m:
            out.append(line)
            continue
        sub = (root / m.group(1)).resolve()
        try:
            sub.relative_to(root)
            body = _read_text(sub)[:40_000]
        except (ValueError, OSError):
            out.append(f"(unavailable: {m.group(1)})")
            continue
        out.append(f"\n----- {m.group(1)} -----")
        if depth < 1:
            _expand_imports(root, body, out, depth + 1)
        else:
            out.append(body)
        out.append(f"----- end {m.group(1)} -----\n")


@mcp.tool()
def weaver_context() -> str:
    """Load the vault's entry context. Call this first when starting work.
    Source of truth: the weaver_claude/ folder (00_start.md, rules, map, bridge) plus the generated
    Agent/STATE.md and Agent/PROJECTS.md. Falls back to CLAUDE.md if weaver_claude/ is missing.
    In this cloud session use the weaver__ tools instead of direct file access."""
    root = _vroot()
    hub = root / "weaver_claude"
    out: list[str] = []
    if (hub / "00_start.md").is_file():
        out.append("# Weaver - context from weaver_claude/ (the rules the user edits: Weaver/Правила.md)\n")
        _expand_imports(root, "@weaver_claude/00_start.md", out)
        files = sorted(p.relative_to(root).as_posix() for p in hub.rglob("*.md"))
        out.append("\nFiles in weaver_claude/ (read with vault_read when needed):\n" + "\n".join("- " + f for f in files))
        for gen in ("Agent/STATE.md",):
            if (root / gen).is_file():
                _expand_imports(root, "@" + gen, out)
        return "\n".join(out)
    entry = root / "CLAUDE.md"
    if not entry.is_file():
        raise FileNotFoundError(f"Neither weaver_claude/00_start.md nor CLAUDE.md found in {root}")
    _expand_imports(root, _read_text(entry), out, depth=1)
    return "\n".join(out)


'''

src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()
if "def _expand_imports(" not in s:
    a = s.index("@mcp.tool()\ndef weaver_context()")
    b = s.index("@mcp.tool()\ndef vault_list(")
    s = s[:a] + NEW.lstrip("\n") + s[b:]
    s = s.replace('"""Weaver MCP server: the Obsidian vault', '"""Weaver MCP server (Weaver Bridge): the Obsidian vault', 1)
open(dst, "w", encoding="utf-8", newline="").write(s)
print("weaver_server.py ready")
