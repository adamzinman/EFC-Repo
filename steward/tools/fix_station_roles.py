"""Rule: Docks/Station (imported Station_Sidebar) setpoints and commands are Operator+ (role level 1, efc.ui.level).
Adds custom.level (session roles -> efc.ui.level) and gates every Input/Setpoint field and Button/* by it.
Usage: python3 -I steward/tools/fix_station_roles.py <viewtools dir> [apply]
"""
import json, sys
sys.path.insert(0, sys.argv[1])
from viewtools import Fixer

LEVEL = {"binding": {"type": "property", "config": {"path": "session.props.auth.user.roles"},
                     "transforms": [{"type": "script", "code": "\treturn efc.ui.level(value)"}]}}
GATE = "{view.custom.level} >= 1"

def fix(view, ctx):
    before = json.dumps(view, sort_keys=True)
    view.setdefault("custom", {})["level"] = view.get("custom", {}).get("level", 0)
    view.setdefault("propConfig", {})["custom.level"] = LEVEL
    for c in ctx.components(view):
        cls = c.get("props", {}).get("style", {}).get("classes", "")
        if "closeDynamic" in json.dumps(c.get("events", {})):
            continue                                       # close stays available to every role
        if c.get("type") in ("ia.input.numeric-entry-field", "ia.input.button") and ("Input/Setpoint" in cls or cls.startswith("Button/")):
            pc = c.setdefault("propConfig", {})
            old = pc.get("props.enabled", {}).get("binding", {}).get("config", {}).get("expression")
            if old and GATE in old:
                continue
            if "props.enabled" in pc and not old:
                continue                                   # non-expression enable binding: leave it, report below
            pc["props.enabled"] = {"binding": {"type": "expr", "config": {"expression": f"{GATE} && ({old})" if old else GATE}}}
    return json.dumps(view, sort_keys=True) != before

apply = len(sys.argv) > 2 and sys.argv[2] == "apply"
Fixer(root="imported", select="Templates/Station/Station_Sidebar", apply=apply, backup=False).run(fix)
