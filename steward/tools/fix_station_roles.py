"""Rule (decisions 20, 36): the Station setpoints and commands are Operator+ (level 1) and audit-logged. Applies to
Templates/Dynamic Window/Station/Station (imported Station_Sidebar) and Templates/Station/Station_Fill.
- custom.level binds session.props.auth.securityLevels -> efc.ui.level (same as the generated windows).
- Input/Setpoint fields stay greyed out below Operator (no lock). They read their tag one way (no bidirectional binding)
  and an onChange script commits a user's edit through efc.ui.setValue (level re-checked, old -> new audited); a refused
  or failed write refreshes the binding (issue #4).
- Command buttons (Button/*, except the dynamic-window close button and the local-only Cancel) stay enabled below Operator
  and show the lock icon + "Requires Operator access" tooltip (like generator/docks/build_docks.py button(need=...)).
  Their scripts go through efc.ui.cmd (audit=True) / efc.ui.denied so a press below level opens the AccessDenied popup.
  ConfirmBtn re-checks the lock state (s.tzLocked / s.resetLocked) before it writes, so a command picked while idle is
  not sent once a cycle has started.
Idempotent: re-running on an already patched view changes nothing.
Usage (repo root): python3 -I steward/tools/fix_station_roles.py <viewtools dir> [apply]
  <viewtools dir> = the folder holding viewtools.py (the ignition-library-steward skill's scripts/ dir). build.py consumes the
  patched imported/ tree as-is, so after "apply" run: python3 build.py
"""
import json, re, sys
sys.path.insert(0, sys.argv[1])
from viewtools import Fixer

LEVEL = {"binding": {"type": "property", "config": {"path": "session.props.auth.securityLevels"},
                     "transforms": [{"type": "script", "code": "\treturn efc.ui.level(value)"}]}}
LOCKED = "{view.custom.level} < 1"
OLD_GATE = re.compile(r"^\{view\.custom\.level\} >= 1(?: && \((.*)\))?$", re.S)
NEW_GATE = re.compile(r"^\(\{view\.custom\.level\} < 1\)(?: \|\| \((.*)\))?$", re.S)


REL = ("\t\tdef _release(p=path):\n\t\t\timport time\n\t\t\ttime.sleep(1.0)\n\t\t\tsystem.tag.writeBlocking([p], [False])\n"
       "\t\tsystem.util.invokeAsynchronous(_release)")
def _deny_or(name, body):
    return f"\tif efc.ui.userLevel(self) < 1:\n\t\tefc.ui.denied(self, 1, '{name}')\n\telse:\n\t\t{body}"
SCRIPTS = {
    # momentary pulse: efc.ui.cmd writes <tagPath>/<member> (or opens AccessDenied); release 1 s later only if the write went through
    "Select": ("\t# Momentary pulse: set the PLC bit, release it 1 s later (harmless if the PLC clears it first).\n"
               "\tif efc.ui.cmd(self, 'Cmd_Select', True, 1, audit=True):\n\t\tpath = self.view.params.tagPath + \"/Cmd_Select\"\n" + REL),
    # Tare/Zero/Reset only open the confirm step; the tag write is ConfirmBtn's. Below level: AccessDenied popup instead.
    "Tare": _deny_or("Tare", 'self.view.custom.pendingCmd = "Tare"'),
    "Zero": _deny_or("Zero", 'self.view.custom.pendingCmd = "Zero"'),
    "Reset": _deny_or("Reset", 'self.view.custom.pendingCmd = "Reset"'),
    "ConfirmBtn": ("\tcmd = self.view.custom.pendingCmd\n\tself.view.custom.pendingCmd = \"\"\n"
                   "\tmember = {\"Tare\": \"Cmd_Tare\", \"Zero\": \"Cmd_Zero\", \"Reset\": \"Cmd_Reset\"}.get(cmd)\n"
                   "\t# Re-check the lock at confirm time: the state may have changed since the command was picked.\n"
                   "\tlocked = self.view.custom.s.resetLocked if cmd == \"Reset\" else self.view.custom.s.tzLocked\n"
                   "\tif member and not locked and efc.ui.cmd(self, member, True, 1, audit=True):\n\t\tpath = self.view.params.tagPath + \"/\" + member\n" + REL),
}
LOCK_BUTTONS = tuple(SCRIPTS)      # Cancel is local-only (clears pendingCmd): not a command

def original(expr):
    """The component's own enable condition, with any earlier level gate stripped."""
    if expr is None:
        return None
    m = OLD_GATE.match(expr) or NEW_GATE.match(expr)
    return m.group(1) if m else expr

def commit(pc):
    """props.value: drop bidirectional, add the efc.ui.setValue onChange commit. Already converted: unchanged."""
    v = pc.get("props.value", {})
    cfg = v.get("binding", {}).get("config", {})
    member = cfg.get("tagPath", "").split("/")[-1]
    if not cfg.get("bidirectional") or not member:
        return
    cfg.pop("bidirectional")
    v["onChange"] = {"enabled": None, "script": (
        "\tif origin == 'Browser' and currentValue.value is not None:\n"
        f"\t\tif not efc.ui.setValue(self, '{member}', currentValue.value, 1):\n"
        "\t\t\tself.refreshBinding('props.value')")}

def fix(view, ctx):
    before = json.dumps(view, sort_keys=True)
    view.setdefault("custom", {})["level"] = view.get("custom", {}).get("level", 0)
    view.setdefault("propConfig", {})["custom.level"] = LEVEL
    for c in ctx.components(view):
        cls = c.get("props", {}).get("style", {}).get("classes", "")
        if "closeDynamic" in json.dumps(c.get("events", {})):
            continue                                       # close stays available to every role
        t, name = c.get("type"), c.get("meta", {}).get("name")
        if t not in ("ia.input.numeric-entry-field", "ia.input.button") or not ("Input/Setpoint" in cls or cls.startswith("Button/")):
            continue
        pc = c.setdefault("propConfig", {})
        e = pc.get("props.enabled")
        old = (e or {}).get("binding", {}).get("config", {}).get("expression")
        if e and not old:
            print("  non-expression enable binding left alone:", name)
            continue
        old = original(old)
        ex = lambda s: {"binding": {"type": "expr", "config": {"expression": s}}}
        if t == "ia.input.numeric-entry-field":            # setpoint fields: disabled below Operator, no lock
            pc["props.enabled"] = ex(f"{{view.custom.level}} >= 1 && ({old})" if old else "{view.custom.level} >= 1")
            commit(pc)
        elif name in LOCK_BUTTONS:
            c.setdefault("props", {})["image"] = {"icon": {"path": "", "color": "#1F1F1F"}, "position": "left", "width": 14, "height": 14}
            pc["props.image.icon.path"] = ex(f"if({LOCKED}, 'material/lock', '')")
            pc["meta.tooltip.enabled"] = ex(LOCKED)
            c["meta"]["tooltip"] = {"enabled": False, "text": "Requires Operator access"}
            if old:
                pc["props.enabled"] = ex(f"({LOCKED}) || ({old})")
            else:
                pc.pop("props.enabled", None)
            c["events"]["component"]["onActionPerformed"]["config"]["script"] = SCRIPTS[name]
        elif name == "Cancel":
            pc["props.enabled"] = ex("{view.custom.level} >= 1")
        else:
            print("  unhandled Button/* left alone:", name)
    return json.dumps(view, sort_keys=True) != before

apply = len(sys.argv) > 2 and sys.argv[2] == "apply"
for view in ("Templates/Station/Station_Sidebar", "Templates/Station/Station_Fill"):
    Fixer(root="imported", select=view, apply=apply, backup=False).run(fix)
