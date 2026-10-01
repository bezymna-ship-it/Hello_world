"""One-off bridge job: Houdini starts its MCP server by itself (see ../fix_houdini_hook.py).
Takes effect the next time Houdini opens."""
import os
import runpy

runpy.run_path(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fix_houdini_hook.py"),
               run_name="__main__")
