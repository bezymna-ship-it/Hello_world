"""One-off bridge job: tidy the vault (Projects · Library · Weaver · Studio_bridge). See ../reorg_vault.py."""
import os
import runpy
import sys

sys.argv = ["reorg_vault.py", "--go"]
runpy.run_path(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reorg_vault.py"),
               run_name="__main__")
