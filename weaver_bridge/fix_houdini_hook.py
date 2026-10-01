"""Weaver Bridge: make Houdini start its MCP server by itself (run once, then restart Houdini).

    py fix_houdini_hook.py

Why: the first installer put the start-up code into pythonrc.py, which Houdini runs BEFORE its interface exists,
so the code skipped itself. This script moves it to scripts\\123.py and scripts\\456.py (they run with the UI up:
123.py when Houdini starts without a file, 456.py when it starts with one), refreshes weaver_hook.py in
Documents\\houdiniXX.X\\python3.Xlibs and removes the old block from pythonrc.py. Your own code in those files stays.
Same thing `py install.py --hooks` does in the newer installer.
"""
import glob
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common  # noqa: E402

BEGIN, END = "# >>> weaver_bridge", "# <<< weaver_bridge"
PORT = 19876
BLOCK = '''try:
    import hou
    if hou.isUIAvailable():
        import weaver_hook
        weaver_hook.houdini_start(port=%d)
except Exception as _wb_exc:
    print("[weaver_bridge] Houdini hook skipped: %%s" %% _wb_exc)''' % PORT


def put_block(path, body):
    text = open(path, encoding="utf-8", errors="ignore").read() if os.path.isfile(path) else ""
    block = "%s\n%s\n%s\n" % (BEGIN, body, END)
    pat = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", re.S)
    text = pat.sub(lambda _m: block, text) if pat.search(text) else (text.rstrip("\n") + "\n\n" if text.strip() else "") + block
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)


def remove_block(path):
    if not os.path.isfile(path):
        return
    text = open(path, encoding="utf-8", errors="ignore").read()
    new = re.sub(r"\n*" + re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", "\n", text, flags=re.S)
    if new != text:
        open(path, "w", encoding="utf-8").write(new.strip("\n") + "\n" if new.strip() else "")
        print("   removed the old block from " + path)


def main():
    cfg = common.load_config()
    hook = open(os.path.join(HERE, "hooks", "weaver_hook.py"), encoding="utf-8").read().replace("__WEAVER_HOME__", cfg["home"])
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    prefs = [p for p in glob.glob(os.path.join(docs, "houdini*")) if re.search(r"houdini\d+\.\d+$", p)]
    if not prefs:
        sys.exit("No Documents\\houdiniXX.X folder found - open Houdini once and run this again.")
    mod = os.path.join(cfg["home"], "apps", "houdini-mcp", "houdini_mcp.py")
    for h in prefs:
        for pv in ("python3.9libs", "python3.10libs", "python3.11libs", "python3.12libs"):
            dst = os.path.join(h, pv)
            os.makedirs(dst, exist_ok=True)
            if os.path.isfile(mod):
                shutil.copyfile(mod, os.path.join(dst, "houdini_mcp.py"))
            open(os.path.join(dst, "weaver_hook.py"), "w", encoding="utf-8").write(hook)
            remove_block(os.path.join(dst, "pythonrc.py"))
        for name in ("123.py", "456.py"):
            put_block(os.path.join(h, "scripts", name), BLOCK)
        print("OK  %s: hook is in scripts\\123.py and 456.py" % h)
    print("\nNow close Houdini completely and open it again. In the status bar (bottom) you should see:\n"
          "  Weaver Bridge: Houdini MCP on localhost:%d\nThen /bridge in Telegram shows Houdini with MCP on." % PORT)


if __name__ == "__main__":
    main()
