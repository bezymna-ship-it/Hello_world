"""Patch cinema4d-mcp's mcp_server_plugin.pyp (idempotent, run by install.py):
the socket server (port 5555) starts by itself when Cinema 4D opens - no menu click.

Not for Cinema 4D 2026.4+: it has Maxon's own MCP server (port 5556), and Maxon advises against
attaching a second server to the same Cinema. Set C4D_MCP_NO_AUTOSTART=1 to switch the autostart off.

    python patch_c4d_autostart.py <path to mcp_server_plugin.pyp>
"""
import sys

path = sys.argv[1]
src = open(path, encoding="utf-8").read()
MARK = "# >>> weaver_bridge autostart"
if MARK in src:
    print("already patched")
    raise SystemExit(0)

old = "        SocketServerPlugin(),\n    )"
assert old in src, "RegisterCommandPlugin call not found - cinema4d-mcp changed, update this patch"
src = src.replace(old, "        _WB_PLUGIN,\n    )", 1)

block = '''
''' + MARK + '''
# The command plugin instance is shared, so the menu entry and the autostart use the same dialog/server.
_WB_PLUGIN = SocketServerPlugin()


def PluginMessage(id, data):
    if id == c4d.C4DPL_PROGRAM_STARTED:
        import os as _wb_os
        if c4d.GetC4DVersion() >= 2026400 or _wb_os.environ.get("C4D_MCP_NO_AUTOSTART"):
            return False
        try:
            _WB_PLUGIN.Execute(c4d.documents.GetActiveDocument())
            if _WB_PLUGIN.dialog is not None and _WB_PLUGIN.dialog.server is None:
                _WB_PLUGIN.dialog.StartServer()
            print("[weaver_bridge] C4D MCP socket server autostarted on 127.0.0.1:5555")
        except Exception as e:
            print("[weaver_bridge] C4D MCP autostart failed: %s" % e)
    return False
# <<< weaver_bridge autostart

'''
anchor = 'if __name__ == "__main__":'
assert src.count(anchor) == 1, "__main__ block not found"
src = src.replace(anchor, block + anchor, 1)
open(path, "w", encoding="utf-8").write(src)
print("patched")
