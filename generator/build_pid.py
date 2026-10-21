"""
PID_Symbols: one template per controlled-device symbol (design notes 20-21; see docs/design-notes.md).
  - Parameters: tagPath (type instance), tType, dockId / dwTagPath (window override), useButton, dblCmd
  - The symbol is a Perspective Drawing (ia.shapes.svg) embedded in the template; element paints bound to state (v5.1)
  - Kept from notes 1-19: tag above / status below (centered), bottom-left actuation button, P left / I right clear of the
    process line, yellow mode letter, actuator head = command / body = feedback, EFC_Styles colors
  - Alarm outline: highest active alarm (priority 1-4) on any member of the UDT instance (isAlarmActiveFiltered)
  - Bound to EFCLib v1 types (T_DValve, T_CValve, T_Motor / T_VFD, T_Heater); click on the symbol opens the dynamic window
    (efc.ui.openDynamic); double-tap in touch mode commands two-state devices (efc.ui.dblCmd); control valve: no actuation button
  Normally run from the repo root:  python3 build.py
"""
import json, os, shutil, zipfile
import pid_common as v3
from pid_common import (expr, prop, tag, pin, script, label, frac, status_group, badges, resource_json, LAYOUT, PAL,
                      W_ALARM, W_OUTLINE, svg_tokens, source_expr, source_static, atom, BASE)
from active import resolve as resolve_role
_hex = lambda e: e   # v5.1: colors are plain #RRGGBB (bound straight onto Drawing element paints, no data URI)
from active import SYMS, BY, colors

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build", "pid")   # gitignored build output

# ---------------------------------------------------------------- shared custom props (all driven from the UDT)
# v5.1: isAlarmActiveFiltered returns Bad_NotFound quality when nothing under the instance has an alarm configured
# (seen on DDT_Valve). Each call is coalesced and forced to good quality, so "no alarms" reads as 0 and the bad quality
# can no longer propagate into line / lw.
def _alm(p):
    return ('forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", %d, %d, 0, 1, 0), false), false))' % (p, p))
ALARM = "if(%s, 4, if(%s, 3, if(%s, 2, if(%s, 1, 0))))" % (_alm(4), _alm(3), _alm(2), _alm(1))
FILL = _hex('case({view.custom.state}, 0, "%s", 1, "%s", 2, "%s", 3, "%s", "%s")'
            % (PAL["stopped"], PAL["running"], PAL["transition"], PAL["fault"], PAL["transition"]))
HEAD = _hex('if({view.custom.command} < 0, {view.custom.fill}, if({view.custom.command} = 1, "%s", "%s"))' % (PAL["running"], PAL["stopped"]))
LINE = _hex('if({view.custom.state} = 3, "%s", case({view.custom.alarm}, 1, "%s", 2, "%s", 3, "%s", 4, "%s", "%s"))'
            % (PAL["fault_border"], PAL["alarm"][1], PAL["alarm"][2], PAL["alarm"][3], PAL["alarm"][4], PAL["outline"]))
CON = _hex('if({view.custom.state} = 3, "%s", "%s")' % (PAL["con_light"], PAL["con_dark"]))
TAGNAME = ('if(len(coalesce({view.custom.name}, "")) > 0, {view.custom.name}, '
           'substring({view.params.tagPath}, lastIndexOf({view.params.tagPath}, "/") + 1))')
TAG_CLS = "Text/TagName Text/Mod/Center Text/Mod/NoWrap"

def color_props(s, custom, cfg):
    c = colors(s)
    custom.update({"alarm": 0, "fill": _hex(c["state"]), "head": _hex(c["head"]), "line": _hex(c["line"]),
                   "lw": round(c["lw"], 3), "con": _hex(c["con"])})
    cfg.update({"custom.alarm": expr(ALARM), "custom.fill": expr(FILL), "custom.head": expr(HEAD), "custom.line": expr(LINE),
                "custom.con": expr(CON),
                "custom.lw": expr(f"if({{view.custom.alarm}} > 0 || {{view.custom.state}} = 3, {round(W_ALARM * s.k, 3)}, {round(W_OUTLINE * s.k, 3)})")})

# v5.1: the symbol is embedded as a Perspective Drawing (ia.shapes.svg). Every SVG element lives in the view JSON and its
# fill / stroke paint (and outline width) is bound to the state-driven custom props -- no image link, no data URI.
DYN_FILL = {"state": "fill", "head": "head", "cfill": "con"}
DYN_STROKE = {"state": "line", "body": "line", "head": "line", "cstroke": "con"}
def drawing_elements(s):
    from active import colors as _c
    c = _c(s); els, binds = [], {}
    for i, e in enumerate(s.elems):
        t, role, g, kw = e
        f, st, sw = resolve_role(e, s, c)
        el = {"type": t, "name": f"{role}{i}"}
        el.update({k: v for k, v in g.items()})
        el["fill"] = {"paint": f if f != "none" else "transparent"}
        if st != "none" or role in DYN_STROKE:
            el["stroke"] = {"paint": st, "width": round(sw, 3), "linejoin": "round"}
        else:
            el["stroke"] = {"paint": "transparent", "width": 0}
        els.append(el)
        if role in DYN_FILL: binds[f"props.elements[{i}].fill.paint"] = expr("{view.custom.%s}" % DYN_FILL[role])
        if role in DYN_STROKE: binds[f"props.elements[{i}].stroke.paint"] = expr("{view.custom.%s}" % DYN_STROKE[role])
        if role in ("state", "body", "head"): binds[f"props.elements[{i}].stroke.width"] = expr("{view.custom.lw}")
    return els, binds

def image(s, L, custom):
    els, binds = drawing_elements(s)
    return {"type": "ia.shapes.svg", "version": 0, "meta": {"name": "Symbol"}, "position": frac(L["sym"], L["size"]),
            "props": {"viewBox": f"0 0 {s.vb[0]} {s.vb[1]}", "preserveAspectRatio": "xMidYMid", "elements": els},
            "propConfig": binds}

def image_v4(s, L, custom):
    toks = svg_tokens(s)
    return {"type": "ia.display.image", "version": 0, "meta": {"name": "Symbol"}, "position": frac(L["sym"], L["size"]),
            "props": {"source": source_static(toks, custom), "fit": {"mode": "contain"}},
            "propConfig": {"props.source": expr(source_expr(toks))}}

def tag_label(L):
    return label("Tag", frac(L["tag"], L["size"]), "", TAG_CLS,
                 {"props.text": expr(TAGNAME), "meta.tooltip.text": expr('coalesce({view.custom.desc}, "")'),
                  "meta.tooltip.enabled": expr('len(coalesce({view.custom.desc}, "")) > 0')}, meta={"tooltip": {"enabled": False, "text": ""}})


# notes: P and I sit just outside the valve actuator, an equal gap from each side, centered on the actuator height
BADGE_GAP = 3   # px at 1080p
def valve_layout(s, base):
    import re as _re
    L = dict(base); sx, sy, sw, sh = L["sym"]; sc = sw / s.vb[0]
    t, role, g, kw = next(e for e in s.elems if e[1] == "head")
    if t == "rect":   x0, x1, y0, y1 = g["x"], g["x"] + g["width"], g["y"], g["y"] + g["height"]
    elif t == "circle": x0, x1, y0, y1 = g["cx"] - g["r"], g["cx"] + g["r"], g["cy"] - g["r"], g["cy"] + g["r"]
    else:              x0, x1, y0, y1 = 28, 72, 16, 32                 # diaphragm dome (Valve_Control): 28..72 wide, 16..32 tall
    ax0, ax1 = sx + x0 * sc, sx + x1 * sc; acy = sy + (y0 + y1) / 2 * sc
    bw, bh = L["P"][2], L["P"][3]
    L["P"] = (round(ax0 - BADGE_GAP - bw, 1), round(acy - bh / 2, 1), bw, bh)
    L["I"] = (round(ax1 + BADGE_GAP, 1), round(acy - bh / 2, 1), bw, bh)
    return L

def status_label(L, status_expr, cls_expr, m_vis=None):
    """Status below the symbol: a bordered state chip sized to its text, centered on the symbol (flex wrapper).
    m_vis: expression; when true a yellow 'M' segment (Mode/ManualSplit) joins the chip's left side at the same height."""
    kids = []
    if m_vis:
        # Hidden M must take zero width so the flex row centres the status chip alone on the symbol centreline:
        # meta.visible false removes it, and Util/Collapsed (display:none, 0 width/padding/border) guarantees no residual space.
        kids.append(label("M", None, "M", "Util/Collapsed",
                          {"meta.visible": expr(m_vis), "props.style.classes": expr(f'if({m_vis}, "Mode/ManualSplit", "Util/Collapsed")')},
                          position={"basis": "auto", "shrink": 0, "grow": 0}))
        cls_expr = f'{cls_expr} + if({m_vis}, " Mode/ManualJoined", "")'
    kids.append(label("Status", None, "", "State/Stopped", {"props.text": expr(status_expr), "props.style.classes": expr(cls_expr)},
                      position={"basis": "auto", "shrink": 0}))
    return {"type": "ia.container.flex", "version": 0, "meta": {"name": "StatusGroup"}, "position": frac(L["status"], L["size"]),
            "props": {"direction": "row", "justify": "center", "alignItems": "stretch", "style": {"classes": ""}}, "children": kids}

# note 25: vertical position indicator for analog valves (fill = actual Pos, blue pointer = commanded Out)
BAR_TRACK, BAR_FILL, BAR_CMD = "#FFFFFF", "#4D4D4D", "#1F4E99"
def position_bar(L):
    """v5.1: embedded Drawing. Track rect, fill rect (y/height bound to Pos), command pointer (path d bound to Out)."""
    els = [{"type": "rect", "name": "track", "x": 8, "y": 2, "width": 11, "height": 96,
            "fill": {"paint": BAR_TRACK}, "stroke": {"paint": "#595959", "width": 1.5}},
           {"type": "rect", "name": "pos", "x": 8, "y": 98, "width": 11, "height": 0,
            "fill": {"paint": BAR_FILL}, "stroke": {"paint": "transparent", "width": 0}},
           {"type": "path", "name": "cmd", "d": "M0 91 L7 98 L0 105 Z",
            "fill": {"paint": BAR_CMD}, "stroke": {"paint": "transparent", "width": 0}}]
    return {"type": "ia.shapes.svg", "version": 0, "meta": {"name": "PositionBar", "tooltip": {"enabled": True, "text": ""}},
            "position": frac(L["bar"], L["size"]),
            "props": {"viewBox": "0 -6 20 112", "preserveAspectRatio": "none", "elements": els},
            "propConfig": {"props.elements[1].y": expr("98 - 0.96 * {view.custom.posC}"),
                           "props.elements[1].height": expr("0.96 * {view.custom.posC}"),
                           "props.elements[2].d": expr('"M0 " + toStr(91 - 0.96 * {view.custom.outC}) + " L7 " + toStr(98 - 0.96 * {view.custom.outC}) + " L0 " + toStr(105 - 0.96 * {view.custom.outC}) + " Z"'),
                           "meta.tooltip.text": expr('"Position " + numberFormat({view.custom.posC}, "0") + " % / Command " + numberFormat({view.custom.outC}, "0") + " %"')}}

def view(path_default, custom, cfg, kids, size, use_button=False):
    params = {"tagPath": path_default}
    if use_button: params["useButton"] = True          # True: manual command button; False: click the symbol, yellow M shows Manual
    pc = {f"params.{k}": pin() for k in params}; pc.update(cfg)
    return {"custom": custom, "params": params, "propConfig": pc,
            "props": {"defaultSize": {"width": size[0], "height": size[1]}},
            "root": {"type": "ia.container.coord", "version": 0, "meta": {"name": "root"}, "props": {"mode": "percent"}, "children": kids}}

# ---------------------------------------------------------------- EFCLib v1 (PCLib T_ types) bindings
# Click on the symbol opens the dynamic window (efc.ui.openDynamic); double-click / double-tap in touch mode
# (useButton = false) toggles two-state devices through efc.ui.dblCmd. Commands write the type's one-shot Cmd_ members.
OPEN_DW = script("\tefc.ui.openDynamic(self)")
DBL_CMD = script("\tefc.ui.dblCmd(self)")
def ftag(m):   # tag member of the instance, or of an embedded group / mode block ("Mode/Sts_Man")
    return tag(m)
def first_out(group):
    """Description of the group's first-out condition (empty when none)."""
    return {"binding": {"type": "tag", "config": {"mode": "indirect", "fallbackDelay": 2.5,
            "references": {"0": "{view.params.tagPath}", "1": "{view.custom.firstOut}"}, "tagPath": "{0}/" + group + "/Cfg_CondDesc/{1}"}}}
I_TIP = ('"Interlock active - " + {view.custom.blockVerb} + " blocked" + '
         'if({view.custom.firstOut} >= 0 && len(coalesce({view.custom.firstDesc}, "")) > 0, ": " + {view.custom.firstDesc}, "")')

def common_cfg(custom, cfg, perm=True):
    """Members every bound device template reads: identity, mode, availability, permissive / interlock."""
    custom.update({"name": "", "desc": "", "man": False, "oos": False, "avail": True, "local": False, "intlk": False,
                   "permMissing": False, "firstOut": -1, "firstDesc": "", "mode": 0})
    cfg.update({"custom.name": ftag("Cfg_Tag"), "custom.desc": ftag("Cfg_Desc"), "custom.man": ftag("Mode/Sts_Man"),
                "custom.oos": ftag("Mode/Sts_OOS"), "custom.avail": ftag("Sts_Avail"), "custom.local": ftag("Sts_Local"),
                "custom.intlk": ftag("Sts_Intlk"), "custom.firstOut": ftag("Intlk/Sts_FirstOut"), "custom.firstDesc": first_out("Intlk"),
                "custom.mode": expr("if({view.custom.man}, 1, 0)")})
    if perm: cfg["custom.permMissing"] = ftag("Sts_NotPerm")

def dw_params(params, ttype, dbl):
    """Dynamic-window parameters: tType picks the window (efc.ui), dockId / dwTagPath override it; dblCmd enables double-tap."""
    params.update({"tType": ttype, "dockId": "", "dwTagPath": ""})
    if dbl: params["dblCmd"] = True

def symbol(s, L, custom, dbl):
    img = image(s, L, custom)
    img["props"]["style"] = {"classes": "Util/Pointer"}
    img["meta"]["tooltip"] = {"enabled": True, "text": "Open dynamic window" + (" (double-tap: command, touch mode)" if dbl else "")}
    img["events"] = {"dom": {"onClick": OPEN_DW, **({"onDoubleClick": DBL_CMD} if dbl else {})}}
    return img

def i_badge_tip(kids, verb):
    for k in kids:
        if k["meta"]["name"] == "I":
            k["propConfig"]["meta.tooltip.text"] = expr(I_TIP.replace("{view.custom.blockVerb}", f'"{verb}"'))

# ---------------------------------------------------------------- discrete valve: T_DValve
def onoff_template(s, demo_path):
    L = valve_layout(s, LAYOUT["AutoValve"])
    custom = {"cmd": False, "opened": False, "closed": True, "fault": False, "hasZso": True, "hasZsc": True, "state": 0, "command": 0}
    cfg = {"custom.cmd": ftag("Out_Open"), "custom.opened": ftag("Sts_Opened"), "custom.closed": ftag("Sts_Closed"),
           "custom.fault": ftag("Sts_Fault"), "custom.hasZso": ftag("Cfg_HasZSO"), "custom.hasZsc": ftag("Cfg_HasZSC"),
           "custom.state": expr("if({view.custom.fault}, 3, if({view.custom.opened}, 1, if({view.custom.closed}, 0, 2)))"),
           "custom.command": expr("if({view.custom.hasZso} || {view.custom.hasZsc}, if({view.custom.cmd}, 1, 0), -1)")}
    common_cfg(custom, cfg)
    color_props(s, custom, cfg)
    status = 'case({view.custom.state}, 0, "CLOSED", 1, "OPEN", 2, if({view.custom.cmd}, "OPENING", "CLOSING"), 3, "FAULT", "???")'
    cls = 'case({view.custom.state}, 0, "State/Stopped", 1, "State/Running", 2, "State/Transition", 3, "State/Fault", "State/Unknown")'
    click = script("\tm = 'Cmd_Close' if self.view.custom.cmd else 'Cmd_Open'\n\tsystem.tag.writeBlocking([self.view.params.tagPath + '/' + m], [True])")
    custom["canCmd"] = False
    cfg["custom.canCmd"] = expr("{view.custom.man} && {view.custom.avail} && !{view.custom.local} && !{view.custom.oos} && "
                                "({view.custom.cmd} || (!{view.custom.permMissing} && !{view.custom.intlk}))")
    btn = {"type": "ia.input.button", "version": 0, "meta": {"name": "PB", "tooltip": {"enabled": True, "text": "Open"}},
           "position": frac(L["pb"], L["size"]), "props": {"text": "", "enabled": False, "style": {"classes": "Button/Command"}},
           "propConfig": {"meta.visible": expr("{view.params.useButton} && {view.custom.man}"),
                          "props.enabled": expr("{view.custom.canCmd}"),
                          "meta.tooltip.text": expr('if({view.custom.local}, "Local control", if(!{view.custom.man}, "Manual mode required", '
                                                    'if({view.custom.cmd}, "Close", "Open")))')},
           "events": {"component": {"onActionPerformed": click}}}
    kids = [tag_label(L), symbol(s, L, custom, True)] + badges(L, p_vis="{view.custom.permMissing}", i_vis="{view.custom.intlk}") + \
           [status_label(L, status, cls, m_vis="!{view.params.useButton} && {view.custom.man}"), btn]
    i_badge_tip(kids, "open")
    v = view(demo_path, custom, cfg, kids, L["size"], use_button=True)
    dw_params(v["params"], "T_DValve", True); v["propConfig"].update({f"params.{k}": pin() for k in v["params"]})
    return v

# ---------------------------------------------------------------- control valve: T_CValve (interlocks only); no actuation button
def control_template(s, demo_path):
    L = valve_layout(s, LAYOUT["ControlValve"])
    custom = {"out": 0.0, "pos": 0.0, "fb": True, "fault": False, "state": 0, "command": 0}
    cfg = {"custom.out": ftag("Val_Demand"), "custom.pos": ftag("Val_Pos"), "custom.fb": ftag("Cfg_HasFbk"), "custom.fault": ftag("Sts_Fault"),
           "custom.state": expr("if({view.custom.fault}, 3, if((if({view.custom.fb}, {view.custom.pos}, {view.custom.out})) > 1, 1, 0))"),
           "custom.command": expr("if({view.custom.fb}, if({view.custom.out} > 1, 1, 0), -1)")}
    common_cfg(custom, cfg, perm=False)
    color_props(s, custom, cfg)
    status = 'if({view.custom.state} = 3, "FAULT", numberFormat(if({view.custom.fb}, {view.custom.pos}, {view.custom.out}), "0") + " %")'
    cls = 'case({view.custom.state}, 0, "State/Stopped", 1, "State/Running", 2, "State/Transition", 3, "State/Fault", "State/Unknown") + " Text/Mod/Tabular"'
    custom.update({"posC": 0.0, "outC": 0.0})
    cfg.update({"custom.posC": expr("max(0, min(100, coalesce({view.custom.pos}, 0)))"),
                "custom.outC": expr("max(0, min(100, coalesce({view.custom.out}, 0)))")})
    kids = [tag_label(L), symbol(s, L, custom, False)] + badges(L, p_vis="false", i_vis="{view.custom.intlk}") + \
           [status_label(L, status, cls, m_vis="{view.custom.man}"), position_bar(L)]
    i_badge_tip(kids, "control")
    v = view(demo_path, custom, cfg, kids, L["size"])
    dw_params(v["params"], "T_CValve", False); v["propConfig"].update({f"params.{k}": pin() for k in v["params"]})
    return v

# ---------------------------------------------------------------- running equipment: T_Motor (or T_VFD), T_Heater
RUN_MEMBERS = {
    "T_Motor":  {"cmd": "Out_Run", "on": "Sts_Running", "off": "Sts_Stopped", "trip": "Sts_Tripped", "nofb": "Cfg_NoFbk",
                 "start": "Cmd_Start", "stop": "Cmd_Stop", "words": ("STOPPED", "RUNNING", "STARTING", "STOPPING"), "verbs": ("Start", "Stop")},
    "T_Heater": {"cmd": "Out_Contactor", "on": "Sts_On", "off": "Sts_Off", "trip": "Sts_Tripped", "nofb": None,
                 "start": "Cmd_On", "stop": "Cmd_Off", "words": ("OFF", "ON", "SWITCHING ON", "SWITCHING OFF"), "verbs": ("Switch on", "Switch off")},
}
def ttype_for(s):
    return "T_Heater" if s.name == "Heater_Electric" else "T_Motor"

def motor_template(s, demo_path):
    tt = ttype_for(s); M = RUN_MEMBERS[tt]
    L = dict(LAYOUT["Motor"])
    if s.badge_i == "low": L["I"] = L["I_low"]
    custom = {"cmd": False, "on": False, "off": True, "fault": False, "trip": False, "state": 0, "command": -1}
    cfg = {"custom.cmd": ftag(M["cmd"]), "custom.on": ftag(M["on"]), "custom.off": ftag(M["off"]),
           "custom.fault": ftag("Sts_Fault"), "custom.trip": ftag(M["trip"]),
           "custom.state": expr("if({view.custom.fault} || {view.custom.trip}, 3, if({view.custom.on}, 1, if({view.custom.off}, 0, 2)))")}
    common_cfg(custom, cfg)
    color_props(s, custom, cfg)
    w = M["words"]
    status = f'case({{view.custom.state}}, 0, "{w[0]}", 1, "{w[1]}", 2, if({{view.custom.cmd}}, "{w[2]}", "{w[3]}"), 3, "FAULT", "???")'
    cls = 'case({view.custom.state}, 0, "State/Stopped", 1, "State/Running", 2, "State/Transition", 3, "State/Fault", "State/Unknown")'
    custom["canCmd"] = False
    cfg["custom.canCmd"] = expr("{view.custom.man} && {view.custom.avail} && !{view.custom.local} && !{view.custom.oos} && "
                                "({view.custom.cmd} || (!{view.custom.permMissing} && !{view.custom.intlk}))")
    click = script(f"\tm = '{M['stop']}' if self.view.custom.cmd else '{M['start']}'\n"
                   "\tsystem.tag.writeBlocking([self.view.params.tagPath + '/' + m], [True])")
    pb = {"type": "ia.input.button", "version": 0, "meta": {"name": "PB", "tooltip": {"enabled": True, "text": M["verbs"][0]}},
          "position": frac(L["pb"], L["size"]), "props": {"text": "", "enabled": False, "style": {"classes": "Button/Command"}},
          "propConfig": {"meta.visible": expr("{view.params.useButton} && {view.custom.man}"),
                         "props.enabled": expr("{view.custom.canCmd}"),
                         "meta.tooltip.text": expr(f'if({{view.custom.cmd}}, "{M["verbs"][1]}", "{M["verbs"][0]}")')},
          "events": {"component": {"onActionPerformed": click}}}
    dbl = tt == "T_Motor"   # decision 1: double-tap command on two-state T_DValve / T_Motor only
    kids = [tag_label(L), symbol(s, L, custom, dbl)] + badges(L) + \
           [status_label(L, status, cls, m_vis="!{view.params.useButton} && {view.custom.man}"), pb]
    for k in kids:   # P badge reads the type's NotPerm status
        if k["meta"]["name"] == "P": k["propConfig"]["meta.visible"] = expr("{view.custom.permMissing}")
    i_badge_tip(kids, "start" if tt == "T_Motor" else "switch-on")
    v = view(demo_path, custom, cfg, kids, L["size"], use_button=True)
    dw_params(v["params"], tt, dbl); v["propConfig"].update({f"params.{k}": pin() for k in v["params"]})
    return v

def template_for(s):
    if s.kind == "onoff":   return onoff_template
    if s.kind == "control": return control_template
    return motor_template

# ---------------------------------------------------------------- demo tags: memory stand-ins with the EFCLib v1 member names
# (the real types are in types/export/PCLib_Ignition81.json; point templates at real instances instead)
def _grp():
    return {"name": "Intlk", "tagType": "Folder", "tags": [atom("Sts_FirstOut", "Int2", -1), atom("Out_OK", "Boolean", True),
            {"name": "Cfg_CondDesc", "tagType": "Folder", "tags": [atom(str(i), "String", "") for i in range(16)]}]}
def _mode():
    return {"name": "Mode", "tagType": "Folder", "tags": [atom(n, "Boolean", n == "Sts_Auto") for n in ("Sts_Auto", "Sts_Man", "Sts_Maint", "Sts_OOS")]}
def _demo_udt(atoms, perm=True):
    base = [atom("Cfg_Tag", "String", ""), atom("Cfg_Desc", "String", ""), atom("Sts_Avail", "Boolean", True), atom("Sts_Local", "Boolean", False),
            atom("Sts_Intlk", "Boolean", False), atom("Sts_Fault", "Boolean", False)] + ([atom("Sts_NotPerm", "Boolean", False)] if perm else [])
    return base + atoms + [_mode(), _grp()]
UDTS = {
    "T_DValve_Demo": _demo_udt([atom("Out_Open", "Boolean", False), atom("Sts_Opened", "Boolean", False), atom("Sts_Closed", "Boolean", True),
                                atom("Cfg_HasZSO", "Boolean", True), atom("Cfg_HasZSC", "Boolean", True)]),
    "T_CValve_Demo": _demo_udt([atom("Val_Demand", "Float4", 0.0), atom("Val_Pos", "Float4", 0.0), atom("Cfg_HasFbk", "Boolean", True)], perm=False),
    "T_Motor_Demo":  _demo_udt([atom("Out_Run", "Boolean", False), atom("Sts_Running", "Boolean", False), atom("Sts_Stopped", "Boolean", True),
                                atom("Sts_Tripped", "Boolean", False)]),
    "T_Heater_Demo": _demo_udt([atom("Out_Contactor", "Boolean", False), atom("Sts_On", "Boolean", False), atom("Sts_Off", "Boolean", True),
                                atom("Sts_Tripped", "Boolean", False)]),
}
for m in UDTS["T_Motor_Demo"]:   # demo alarm so the outline can be seen: Sts_Fault = 1 raises a High alarm
    if m["name"] == "Sts_Fault": m["alarms"] = [{"name": "Fault", "mode": "Equality", "setpointA": 1.0, "priority": "High"}]

def _man(on=True): return {"Mode/Sts_Man": on, "Mode/Sts_Auto": not on}
DEMO = [  # instance, UDT, member overrides ("Group/Member" for nested), template symbol
    ("XV101", "T_DValve_Demo", {"Out_Open": True, "Sts_Opened": True, "Sts_Closed": False, "Cfg_Tag": "XV-101", "Cfg_Desc": "N2 supply isolation"}, "Valve_OnOff_Pneumatic"),
    ("XV102", "T_DValve_Demo", {**_man(), "Sts_NotPerm": True, "Cfg_Tag": "XV-102"}, "Valve_Solenoid"),
    ("XV103", "T_DValve_Demo", {**_man(), "Out_Open": True, "Sts_Closed": False, "Cfg_Tag": "XV-103"}, "Valve_MOV"),
    ("XV104", "T_DValve_Demo", {"Mode/Sts_OOS": True, "Mode/Sts_Auto": False, "Sts_Intlk": True, "Intlk/Sts_FirstOut": 0,
                                "Intlk/Cfg_CondDesc/0": "PSH-201 high pressure", "Cfg_Tag": "XV-104"}, "Valve_OnOff_Pneumatic"),
    ("XV105", "T_DValve_Demo", {"Sts_Local": True, "Sts_Fault": True, "Sts_Closed": False, "Cfg_Tag": "XV-105"}, "Valve_OnOff_Pneumatic"),
    ("FV101", "T_CValve_Demo", {"Val_Demand": 45.0, "Val_Pos": 43.0, "Cfg_Tag": "FV-101"}, "Valve_Control"),
    ("FV102", "T_CValve_Demo", {"Val_Demand": 20.0, "Val_Pos": 20.0, **_man(), "Cfg_Tag": "FV-102"}, "Valve_Control"),
    ("P101", "T_Motor_Demo", {"Out_Run": True, "Sts_Running": True, "Sts_Stopped": False, "Cfg_Tag": "P-101"}, "Pump_Centrifugal"),
    ("P102", "T_Motor_Demo", {"Sts_NotPerm": True, "Sts_Intlk": True, "Cfg_Tag": "P-102"}, "Pump_PD_Rotary"),
    ("K201", "T_Motor_Demo", {"Out_Run": True, "Sts_Running": True, "Sts_Stopped": False, **_man(), "Cfg_Tag": "K-201"}, "Compressor_Diaphragm"),
    ("K202", "T_Motor_Demo", {"Sts_Fault": True, "Cfg_Tag": "K-202"}, "Compressor_Centrifugal"),
    ("B301", "T_Motor_Demo", {"Out_Run": True, "Sts_Stopped": False, "Cfg_Tag": "B-301"}, "Blower"),
    ("PV501", "T_Motor_Demo", {"Out_Run": True, "Sts_Running": True, "Sts_Stopped": False, **_man(), "Cfg_Tag": "PV-501"}, "Pump_Vacuum"),
    ("E401", "T_Heater_Demo", {"Out_Contactor": True, "Sts_On": True, "Sts_Off": False, "Cfg_Tag": "E-401"}, "Heater_Electric"),
]
NO_BUTTON = {"XV103", "PV501"}   # demo instances shown with useButton = false
def tpl_path(s): return f"Templates/{s.cat}/{s.name}"   # imports straight into Views/Templates

def tags_files():
    d = os.path.join(OUT, "tags"); os.makedirs(d, exist_ok=True)
    for n, members in UDTS.items():
        json.dump({"name": n, "tagType": "UdtType", "tags": members}, open(os.path.join(d, f"{n}_UDT.json"), "w"), indent=2)
    def nest(ov):
        root = {}
        for k, v in ov.items():
            parts = k.split("/"); d = root
            for p_ in parts[:-1]: d = d.setdefault(p_, {})
            d[parts[-1]] = v
        def emit(d):
            return [{"name": k, "tagType": "Folder", "tags": emit(v)} if isinstance(v, dict) else {"name": k, "tagType": "AtomicTag", "value": v}
                    for k, v in d.items()]
        return emit(root)
    inst = [{"name": n, "tagType": "UdtInstance", "typeId": u, "tags": nest(ov)} for n, u, ov, _ in DEMO]
    json.dump({"name": "PID_Demo", "tagType": "Folder", "tags": inst}, open(os.path.join(d, "PID_Demo_Instances.json"), "w"), indent=2)

def demo_view():
    items = []
    for n, u, ov, sym in DEMO:
        s = BY[sym]; L = LAYOUT["AutoValve" if s.kind == "onoff" else "ControlValve" if s.kind == "control" else "Motor"]
        w, h = L["size"]
        prm = {"tagPath": f"[default]PID_Demo/{n}"}
        if n in NO_BUTTON: prm["useButton"] = False
        items.append(v3.item(tpl_path(s), prm, w * 1.5, h * 1.5, f"{n} · {sym}" + (" · useButton=false" if n in NO_BUTTON else "")))
    return {"custom": {}, "params": {}, "props": {"defaultSize": {"width": 1920, "height": 1080}},
            "root": {"type": "ia.container.flex", "version": 0, "meta": {"name": "root"},
                     "props": {"direction": "column", "style": {"classes": "Container/Screen", "gap": "10px", "padding": "10px", "overflowY": "auto"}},
                     "children": [v3.section("Templates bound to [default]PID_Demo (1.5x). Params: tagPath (+ useButton on valves and running equipment)", items)]}}


# ---------------------------------------------------------------- null-safety (live-gateway fix 2026-10-06)
# Tag-bound customs read null while a member is missing, bad or still loading (e.g. the new Permissive member);
# null inside && / || / if() puts the dependent bindings in error. Wrap every read of a tag-bound custom in coalesce().
NULL_DEFAULTS = {"cmd": "false", "opened": "false", "closed": "false", "hasZso": "false", "hasZsc": "false", "fb": "true",
                 "permMissing": "false", "intlk": "false", "man": "false", "oos": "false", "avail": "true", "local": "false",
                 "on": "false", "off": "false", "trip": "false", "fault": "false", "mode": "0", "out": "0", "pos": "0", "firstOut": "-1"}
def _harden_expr(e):
    import re as _re
    e = _re.sub(r"\{view\.custom\.(\w+)\}", lambda m: f"coalesce({{view.custom.{m.group(1)}}}, {NULL_DEFAULTS[m.group(1)]})"
                if m.group(1) in NULL_DEFAULTS else m.group(0), e)
    return e
def harden(o):
    if isinstance(o, dict):
        if o.get("type") == "expr" and "expression" in o.get("config", {}):
            o["config"]["expression"] = _harden_expr(o["config"]["expression"])
        for v in o.values(): harden(v)
    elif isinstance(o, list):
        for v in o: harden(v)
    return o

def build():
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    views = {}
    for s in SYMS:
        demo = next((f"[default]PID_Demo/{n}" for n, _, _, sym in DEMO if sym == s.name),
                    "[default]PID_Demo/" + {"onoff": "XV101", "control": "FV101"}.get(s.kind, "P101"))
        views[tpl_path(s)] = harden(template_for(s)(s, demo))
    views["Templates/_Demo"] = demo_view()
    raw = os.path.join(OUT, "_raw.zip")
    with zipfile.ZipFile(raw, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("project.json", json.dumps({"title": "PID_Symbols", "description": "EFC controlled-device templates (generated). Parent: EFC_Styles",
                                               "parent": "EFC_Styles", "enabled": True, "inheritable": True}, indent=2))
        for p, v in views.items():
            z.writestr(f"{BASE}/views/{p}/view.json", json.dumps(v, indent=2))
            z.writestr(f"{BASE}/views/{p}/resource.json", resource_json(["view.json"]))
    from make_project_zip import redo
    redo(raw, os.path.join(OUT, "PID_Symbols_PROJECT.zip")); os.remove(raw)
    tags_files()
    v3.OUT = OUT; n = v3.static_symbols()
    print(f"{len(views) - 1} templates, {n} SVGs")

if __name__ == "__main__":
    build()

# Packaging, project export and checks live in ../build.py (repo root).
