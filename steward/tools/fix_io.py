"""Rule: x80 I/O SlotTile click opens the dw_IOCard dynamic window (decision 23/24) instead of the card popup.
The full faceplate popup stays reachable from the window's FULL FACEPLATE button.
Usage: python3 -I steward/tools/fix_io.py <viewtools dir> [apply]
"""
import json, sys
sys.path.insert(0, sys.argv[1])
from viewtools import Fixer

DW_PARAMS = {"tType": "native", "dockId": "dw_IOCard", "dwTagPath": ""}

def fix(view, ctx):
    before = json.dumps(view, sort_keys=True)
    for c in ctx.components(view):
        ev = c.get("events", {}).get("dom", {}).get("onClick", {})
        if "Templates/IO/Faceplates/" in ev.get("config", {}).get("script", "") or "IO/Faceplates/" in ev.get("config", {}).get("script", ""):
            ev["config"]["script"] = "\tif self.view.params.model:\n\t\tefc.ui.openDynamic(self)"
            for k, d in DW_PARAMS.items():
                view.setdefault("params", {}).setdefault(k, d)
                view.setdefault("propConfig", {}).setdefault(f"params.{k}", {"paramDirection": "input", "persistent": True})
    return json.dumps(view, sort_keys=True) != before

apply = len(sys.argv) > 2 and sys.argv[2] == "apply"
Fixer(root="imported", select="IO/Parts/SlotTile", apply=apply, backup=False).run(fix)
