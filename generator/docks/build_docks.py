#!/usr/bin/env python3
"""
EFC_Docks: the dynamic windows (Docks/*), their shared parts (Docks/Parts/*), the screen region (Docks/Region)
and the efc.ui script library. Merged into EFC_Library by build.py.

Every window is 400 x 860 at 1080p (37.04vh x 79.63vh, decision 25), binds one EFCLib v1 T_ type through
view.params.tagPath and uses EFC_Styles classes only. Role levels (efc.ui.ROLES): 1 Operator commands and
setpoints, 2 Maintenance MAINT/OOS/JOG/simulate/maint reset, 3 Supervisor bypass + shelving (reason, audit),
4 Engineer limits, configuration and tuning. Controls below the user's level are hidden, not greyed.
"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common import PERSPECTIVE, dump, write, resource_json, project_json, project_dir

PROJECT = "EFC_Docks"
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 400, 860
def v(px): return f"{px / 10.8:.3f}vh"

# ----------------------------------------------------------------- component helpers
def comp(t, name, props=None, pos=None, pc=None, children=None, events=None):
    d = {"type": t, "version": 0, "meta": {"name": name}, "position": pos or {"shrink": 0}, "props": props or {}}
    if pc: d["propConfig"] = pc
    if children is not None: d["children"] = children
    if events: d["events"] = events
    return d

def expr(e): return {"binding": {"type": "expr", "config": {"expression": e}}}
def tag(member, ref="{view.params.tagPath}", bidi=False):
    return {"binding": {"type": "tag", "config": {"mode": "indirect", "tagPath": "{0}/" + member, "references": {"0": ref},
                                                  "bidirectional": bidi, "fallbackDelay": 2.5}}}
def script(body): return {"type": "script", "scope": "G", "config": {"script": "\t" + body.replace("\n", "\n\t")}}
def on_click(body): return {"dom": {"onClick": script(body)}}
def on_action(body): return {"component": {"onActionPerformed": script(body)}}

def flex(name, direction, children, basis=None, cls="", grow=0, extra=None, pc=None, events=None):
    props = {"direction": direction, "alignItems": "stretch", "style": {"classes": cls}}
    props.update(extra or {})
    pos = {"shrink": 0, "grow": grow}
    if basis: pos["basis"] = basis
    return comp("ia.container.flex", name, props, pos, pc, children, events)

def label(name, text="", cls="Text/Label", grow=0, basis=None, pc=None):
    pos = {"shrink": 0, "grow": grow}
    if basis: pos["basis"] = basis
    return comp("ia.display.label", name, {"text": text, "style": {"classes": cls}}, pos, pc)

def button(name, text, body, cls="Button/Command", show=None, enabled=None, grow=1):
    pc = {}
    if show: pc["position.display"] = expr(show)
    if enabled: pc["props.enabled"] = expr(enabled)
    return comp("ia.input.button", name, {"text": text, "style": {"classes": cls}}, {"shrink": 0, "grow": grow, "basis": v(32)},
                pc or None, events=on_action(body))

def lvl(n): return f"{{view.custom.level}} >= {n}"
OP, MAINT, SUP, ENG = 1, 2, 3, 4

class View:
    """Collects the T_ members a window reads; each becomes custom.<key> with an indirect tag binding."""
    def __init__(self):
        self.custom, self.pc = {"level": 0}, {
            "custom.level": {"binding": {"type": "property", "config": {"path": "session.props.auth.user.roles"},
                                         "transforms": [{"type": "script", "code": "\treturn efc.ui.level(value)"}]}}}
    def m(self, member):
        k = "m_" + re.sub(r"\W", "_", member)
        if k not in self.custom:
            self.custom[k] = None
            self.pc["custom." + k] = tag(member)
        return "{view.custom." + k + "}"
    def c(self, key, e, init=None):
        self.custom[key] = init
        if e is not None:
            self.pc["custom." + key] = expr(e)
        return "{view.custom." + key + "}"

def section(name, title, children, show=None, collapsible=False, vw=None):
    head = [label("Title", title, "Text/Subheader Text/Mod/Upper", grow=1)]
    body = flex("Body", "column", children, extra={"style": {"classes": "", "gap": v(4)}})
    pc = {"position.display": expr(show)} if show else None
    if collapsible:
        key = vw.c("open_" + name, None, False)
        head.append(label("Chevron", "", "Text/Caption", pc={"props.text": expr(f"if({key}, '▾', '▸')")}))
        body["propConfig"] = {"position.display": expr(key)}
        hdr = flex("Header", "row", head, extra={"alignItems": "center"},
                   events=on_click(f"self.view.custom.open_{name} = not self.view.custom.open_{name}"))
    else:
        hdr = flex("Header", "row", head, extra={"alignItems": "center"})
    return flex(name, "column", [hdr, body], cls="Container/GroupBox", pc=pc,
                extra={"style": {"classes": "Container/GroupBox", "gap": v(4)}})

def row(name, text, value_expr, unit_expr=None, show=None):
    kids = [label("Lbl", text, "Text/Caption Text/Mod/Upper", grow=1),
            label("Val", "", "Text/Value Text/Mod/Right Text/Mod/Tabular", pc={"props.text": expr(value_expr)})]
    if unit_expr is not None:
        kids.append(label("EU", "", "Text/Units", basis=v(40), pc={"props.text": expr(unit_expr)}))
    return flex(name, "row", kids, basis=v(22), pc={"position.display": expr(show)} if show else None,
                extra={"alignItems": "center", "style": {"classes": "", "gap": v(6)}})

def fmt(e, f="#,##0.0"): return f"numberFormat({e}, '{f}')"

def entry(vw, name, text, member, minlvl, unit="", enabled=None, show=None, fmtstr="#,##0.0"):
    """Numeric setpoint bound bidirectionally to the member; hidden below minlvl."""
    pc = {"props.value": tag(member, bidi=True), "props.enabled": expr(enabled or "true")}
    num = comp("ia.input.numeric-entry-field", "Entry", {"format": fmtstr, "style": {"classes": "Input/Setpoint"}},
               {"shrink": 0, "basis": v(120)}, pc)
    s = lvl(minlvl) + (f" && ({show})" if show else "")
    return flex(name, "row", [label("Lbl", text, "Text/Caption Text/Mod/Upper", grow=1), num, label("EU", unit, "Text/Units", basis=v(40))],
                basis=v(28), pc={"position.display": expr(s)}, extra={"alignItems": "center", "style": {"classes": "", "gap": v(6)}})

def check(name, text, member, minlvl):
    return comp("ia.input.checkbox", name, {"text": text, "style": {"classes": "Input/Check"}}, {"shrink": 0, "basis": v(24)},
                {"props.selected": tag(member, bidi=True), "props.enabled": expr(lvl(minlvl))})

# ----------------------------------------------------------------- shared window blocks
def header(vw):
    return flex("Header", "row", [
        flex("Names", "column", [label("Tag", "", "Text/TagName", pc={"props.text": expr(vw.m("Cfg_Tag"))}),
                                 label("Desc", "", "Text/Caption Text/Mod/Ellipsis", pc={"props.text": expr(vw.m("Cfg_Desc"))})], grow=1),
        button("Close", "✕", "efc.ui.closeDynamic(self)", cls="Button/Icon", grow=0)],
        basis=v(56), cls="Container/PopupHeader", extra={"alignItems": "center", "style": {"classes": "Container/PopupHeader"}})

def banner(vw, cases, chips):
    """cases: [(condition, TEXT, State/x class)] first match wins; chips: [(condition, TEXT)]."""
    t, c = "'UNKNOWN'", "'State/Unknown'"
    for cond, text, cls in reversed(cases):
        t, c = f"if({cond}, {text if text.startswith(chr(39)) or '(' in text else repr(text)}, {t})", f"if({cond}, '{cls}', {c})"
    kids = [label("State", "", "Text/Status Text/Size/L", grow=1, pc={"props.text": expr(t)})]
    for i, (cond, text) in enumerate(chips):
        kids.append(label(f"Chip{i}", text, "Indicator/Badge", pc={"position.display": expr(cond)}))
    return flex("Banner", "row", kids, basis=v(40), pc={"props.style.classes": expr(c)},
                extra={"alignItems": "center", "style": {"classes": "", "gap": v(6)}})

def mode_section(vw, base="Mode/"):
    m = lambda x: vw.m(base + x)
    cur = f"if({m('Sts_OOS')}, 'OOS', if({m('Sts_Maint')}, 'MAINT', if({m('Sts_Man')}, 'MAN', 'AUTO')))"
    btn = lambda n, t, mem, lv, active: button(n, t, f"efc.ui.cmd(self, '{base}{mem}', True, {lv}, audit={lv >= MAINT})",
                                               show=lvl(lv), cls="Button/Toggle/Off")
    b = [btn("Auto", "AUTO", "Cmd_Auto", OP, "Sts_Auto"), btn("Man", "MAN", "Cmd_Man", OP, "Sts_Man"),
         btn("Maint", "MAINT", "Cmd_Maint", MAINT, "Sts_Maint"), btn("OOS", "OOS", "Cmd_OOS", MAINT, "Sts_OOS")]
    for x, s in zip(b, ["Sts_Auto", "Sts_Man", "Sts_Maint", "Sts_OOS"]):
        x["propConfig"]["props.style.classes"] = expr(f"if({m(s)}, 'Button/Toggle/On', 'Button/Toggle/Off')")
    return section("Mode", "Mode", [row("Current", "Mode", cur), flex("Buttons", "row", b, basis=v(32), extra={"style": {"classes": "", "gap": v(4)}})])

def ready_expr(vw, perm=True, avail=True, mode=True):
    parts = []
    if mode: parts.append(vw.m("Mode/Sts_Man"))
    if avail: parts.append(vw.m("Sts_Avail"))
    parts += ["!" + vw.m("Sts_Intlk"), "!" + vw.m("Sts_Local")]
    if perm: parts.append("!" + vw.m("Sts_NotPerm"))
    return " && ".join(parts)

def commands(vw, buttons, extra=(), hint="Enabled in MAN, available, permitted, not interlocked, not LOCAL"):
    """buttons: [(TEXT, member, class, minlvl, enabled_expr or None)] - uniform size, one row of up to four."""
    b = [button(f"B{i}", t, f"efc.ui.cmd(self, '{mem}', True, {lv})", cls=cls, show=lvl(lv), enabled=en)
         for i, (t, mem, cls, lv, en) in enumerate(buttons)]
    kids = [flex("Buttons", "row", b, basis=v(32), extra={"style": {"classes": "", "gap": v(4)}})] + list(extra)
    if hint:
        kids.append(label("Hint", hint, "Text/Micro Text/Color/Muted"))
    return section("Commands", "Commands", kids, show=lvl(OP))

def intlk(name, title, sub):
    """Embedded Docks/Parts/IntlkList for the T_Intlk member `sub` (Perm or Intlk)."""
    return comp("ia.display.view", name, {"path": "Docks/Parts/IntlkList", "useDefaultViewHeight": True,
                                          "params": {"tagPath": "", "title": title}}, {"shrink": 0},
                {"props.params.tagPath": expr(f"{{view.params.tagPath}} + '/{sub}'")})

def alarms(vw, items):
    """items: [(member, text)] - T_Alarm / T_AlmLim members; ACK acknowledges the unacked ones."""
    rows = []
    for i, (mem, text) in enumerate(items):
        a, u = vw.m(mem + "/Sts_Active"), vw.m(mem + "/Sts_Unack")
        p = vw.m(mem + "/Cfg_Priority")
        pri = f"case(toInt({p}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium')"
        cls = f"if({a}, 'Alarm/' + {pri} + if({u}, '/Unacked', '/Fill'), if({u}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))"
        rows.append(label(f"A{i}", text, "Text/Caption", pc={"props.style.classes": expr(cls)}))
    names = [m for m, _ in items]
    any_a = " || ".join(vw.m(m + "/Sts_Active") for m in names)
    return section("Alarms", "Alarms", [
        label("None", "No active alarms", "Text/Caption Text/Color/Muted", pc={"position.display": expr(f"!({any_a})")}),
        flex("List", "column", rows, extra={"style": {"classes": "", "gap": v(2)}}),
        button("Ack", "ACK", f"efc.ui.ackAll(self, {names!r})", cls="Button/Default", show=lvl(OP), grow=0)])

def trend(pens, title="History"):
    """Embedded Docks/Parts/Trend; its expanded param (in/out) grows the graph to about 400 x 760 inside the window
    (decision 26: never wider; the window scrolls to the sections below)."""
    return comp("ia.display.view", "Trend", {"path": "Docks/Parts/Trend", "params": {"tagPath": "", "pens": pens, "expanded": False}},
                {"shrink": 0, "basis": v(170)},
                {"props.params.tagPath": expr("{view.params.tagPath}"),
                 "position.basis": expr(f"if({{this.props.params.expanded}}, '{v(760)}', '{v(170)}')")})

def maint(vw, extra=()):
    r = lambda n, t, mem, f="#,##0": row(n, t, fmt(vw.m(mem), f))
    kids = [r("Hrs", "Run hours", "Run/Val_RunHrs"), r("Starts", "Starts", "Run/Val_Starts"),
            r("StartsHr", "Starts last hr", "Run/Val_StartsLastHr"), r("SinceMaint", "Hrs since maint", "Run/Val_HrsSinceMaint"),
            row("Due", "Maint due", f"if({vw.m('Run/Sts_MaintDue')}, 'YES', 'no')"), *extra,
            flex("Buttons", "row", [button("ResetMaint", "RESET MAINT", "efc.ui.cmd(self, 'Run/Cmd_ResetMaint', True, 2, audit=True)", cls="Button/Default"),
                                    button("Sim", "SIMULATE", "efc.ui.cmd(self, 'Sim_En', not self.view.custom.m_Sim_En, 2, audit=True)", cls="Button/Default")],
                 basis=v(32), extra={"style": {"classes": "", "gap": v(4)}})]
    vw.m("Sim_En")
    return section("Maintenance", "Maintenance", kids, show=lvl(MAINT))

def config(vw, entries, name="Configuration", title="Configuration"):
    """entries: [(text, member, unit)]; values are shown to all, editable Engineer+ (collapsed by default)."""
    kids = []
    for i, (text, mem, unit) in enumerate(entries):
        if mem.startswith("?"):                                    # boolean
            kids.append(check(f"C{i}", text, mem[1:], ENG))
        else:
            kids.append(row(f"R{i}", text, fmt(vw.m(mem), "#,##0.###"), repr(unit), show="!(" + lvl(ENG) + ")"))
            kids.append(entry(vw, f"E{i}", text, mem, ENG, unit, fmtstr="#,##0.###"))
    return section(name, title, kids, collapsible=True, vw=vw)

GAPS = {v(2): "Util/Gap/XS", v(4): "Util/Gap/S", v(6): "Util/Gap/M", v(8): "Util/Gap/L"}
def classify(o):
    """EFC_Styles classes only: fold the generator's flex gaps into Util/Gap/* classes."""
    if isinstance(o, dict):
        st = o.get("props", {}).get("style") if isinstance(o.get("props"), dict) else None
        if isinstance(st, dict) and "gap" in st:
            st["classes"] = " ".join(x for x in (st.get("classes", ""), GAPS[st.pop("gap")]) if x)
        for x in o.values(): classify(x)
    elif isinstance(o, list):
        for x in o: classify(x)
    return o

def window(path, ttype, vw, blocks):
    root = flex("root", "column", blocks, extra={"style": {"classes": "Container/Faceplate Container/Scroll", "gap": v(6)}})
    params = {"tagPath": "", "tType": ttype}
    pc = dict(vw.pc)
    for p in params:
        pc["params." + p] = {"paramDirection": "input", "persistent": True}
    return path, {"custom": vw.custom, "params": params, "propConfig": pc,
                  "props": {"defaultSize": {"width": W, "height": H}}, "root": root}

# ----------------------------------------------------------------- windows
def common_chips(vw, local=True):
    c = [(vw.m("Sts_Sim"), "SIM")]
    if local: c.append((vw.m("Sts_Local"), "LOCAL"))
    return c + [(vw.m("Sts_Intlk"), "INTLK")]

def ne107(vw):
    return f"case(toInt({vw.m('Sts_NE107')}), 0, 'NE107 OK', 1, 'NE107 F', 2, 'NE107 C', 3, 'NE107 S', 4, 'NE107 M', '')"

def valve_discrete():
    vw = View(); m = vw.m
    rd = ready_expr(vw)
    return window("Docks/ValveDiscrete", "T_DValve", vw, [
        header(vw),
        banner(vw, [(m("Sts_Fault"), "FAULT", "State/Fault"), (m("Sts_Opening"), "OPENING", "State/Transition"),
                    (m("Sts_Closing"), "CLOSING", "State/Transition"), (m("Sts_Opened"), "OPEN", "State/Running"),
                    (m("Sts_Closed"), "CLOSED", "State/Stopped")], common_chips(vw) + [(m("Sts_NotPerm"), "NOT PERM")]),
        mode_section(vw),
        commands(vw, [("OPEN", "Cmd_Open", "Button/Start", OP, rd), ("CLOSE", "Cmd_Close", "Button/Stop", OP, rd),
                      ("RESET", "Cmd_Reset", "Button/Default", OP, None)]),
        section("Feedback", "Feedback", [row("ZSO", "Open limit (ZSO)", f"if({m('Inp_ZSO')}, 'ON', 'off')", show=m("Cfg_HasZSO")),
                                         row("ZSC", "Closed limit (ZSC)", f"if({m('Inp_ZSC')}, 'ON', 'off')", show=m("Cfg_HasZSC")),
                                         row("NE107", "Diagnostics", ne107(vw))]),
        intlk("Perm", "Permissives", "Perm"), intlk("Intlk", "Interlocks", "Intlk"),
        alarms(vw, [("Alm_FailOpen", "Fail to open"), ("Alm_FailClose", "Fail to close"), ("Alm_PosConflict", "Position conflict"),
                    ("Alm_Uncmd", "Uncommanded move"), ("Alm_IntlkTrip", "Interlock trip")]),
        trend(["Out_Open", "Sts_Opened"]),
        maint(vw),
        config(vw, [("Travel time", "Cfg_TravelTime", "s"), ("Has open limit", "?Cfg_HasZSO", ""), ("Has closed limit", "?Cfg_HasZSC", "")]),
    ])

def valve_analog():
    vw = View(); m = vw.m
    rd = f"{m('Mode/Sts_Man')} && !{m('Sts_Intlk')}"
    presets = [button(f"P{p}", f"{p}%", f"efc.ui.cmd(self, 'Cmd_ManPos', {float(p)}, 1)", cls="Button/Default", enabled=rd) for p in (0, 25, 50, 75, 100)]
    return window("Docks/ValveAnalog", "T_CValve", vw, [
        header(vw),
        banner(vw, [(" || ".join(f"isNull({m(x)}) || !isGood({m(x)})" for x in ("Val_Pos", "Sts_Closed")), "UNKNOWN", "State/Unknown"),
                    (m("Sts_Fault"), "FAULT", "State/Fault"), (m("Sts_Intlk"), "INTERLOCKED", "State/Fault"),
                    (m("Sts_Closed"), "CLOSED", "State/Stopped"), ("true", f"'OPEN ' + {fmt(m('Val_Pos'), '0')} + ' %'", "State/Running")],
               [(m("Sts_Sim"), "SIM"), (m("Sts_RateLim"), "RATE LIM")]),
        mode_section(vw),
        commands(vw, [("RESET", "Cmd_Reset", "Button/Default", OP, None)],
                 extra=[entry(vw, "Pos", "Manual position", "Cmd_ManPos", OP, "%", enabled=rd),
                        flex("Presets", "row", presets, basis=v(32), extra={"style": {"classes": "", "gap": v(4)}})],
                 hint="Position entry and presets enabled in MAN, not interlocked"),
        section("Values", "Values", [row("Dem", "Demand", fmt(m("Val_Demand")), "'%'"),
                                     row("Pos", "Position", fmt(m("Val_Pos")), "'%'", show=m("Cfg_HasFbk")),
                                     row("Dev", "Deviation", fmt(m("Val_Dev")), "'%'", show=m("Cfg_HasFbk")),
                                     row("Trv", "Travel", fmt(m("Val_Travel"), "#,##0"), "'%'"),
                                     row("Rev", "Reversals", fmt(m("Val_Reversals"), "#,##0")), row("NE107", "Diagnostics", ne107(vw))]),
        intlk("Intlk", "Interlocks", "Intlk"),
        alarms(vw, [("Alm_PosDev", "Position deviation"), ("Alm_FbkBad", "Feedback bad"), ("Alm_IntlkTrip", "Interlock trip")]),
        trend(["Val_Demand", "Val_Pos"]),
        config(vw, [("Output min", "Cfg_OutMin", "%"), ("Output max", "Cfg_OutMax", "%"), ("Rate up", "Cfg_RateUp", "%/s"),
                    ("Rate down", "Cfg_RateDn", "%/s"), ("Deviation limit", "Cfg_DevLim", "%"), ("Deviation time", "Cfg_DevTime", "s"),
                    ("Tight shutoff", "Cfg_TightShut", "%")]),
    ])

def motor_like(path, ttype, extra_values, extra_alarms, extra_cmd, extra_cfg, pens):
    vw = View(); m = vw.m
    rd = ready_expr(vw)
    vals = [row("Cur", "Current", fmt(m("Val_Current")), "'A'"), row("Rated", "Rated", fmt(m("Cfg_RatedAmps"), "#,##0"), "'A'"),
            row("Load", "Load", fmt(m("Val_LoadPct"), "0"), "'%'"), row("NE107", "Diagnostics", ne107(vw))]
    return window(path, ttype, vw, [
        header(vw),
        banner(vw, [(m("Sts_Tripped"), "TRIPPED", "State/Fault"), (m("Sts_Fault"), "FAULT", "State/Fault"),
                    (m("Sts_Starting"), "STARTING", "State/Transition"), (m("Sts_Stopping"), "STOPPING", "State/Transition"),
                    (m("Sts_Running"), "RUNNING", "State/Running"), (m("Sts_Stopped"), "STOPPED", "State/Stopped")],
               common_chips(vw) + [(m("Sts_NotPerm"), "NOT PERM")]),
        mode_section(vw),
        commands(vw, [("START", "Cmd_Start", "Button/Start", OP, rd), ("STOP", "Cmd_Stop", "Button/Stop", OP, None),
                      ("RESET", "Cmd_Reset", "Button/Default", OP, None), ("JOG", "Cmd_Jog", "Button/Momentary", MAINT, rd)],
                 extra=extra_cmd(vw) if extra_cmd else ()),
        section("Values", "Values", vals + (extra_values(vw) if extra_values else [])),
        intlk("Perm", "Permissives", "Perm"), intlk("Intlk", "Interlocks", "Intlk"),
        alarms(vw, [("Alm_FailStart", "Fail to start"), ("Alm_FailStop", "Fail to stop"), ("Alm_Uncmd", "Uncommanded run/stop"),
                    ("Alm_EStop", "E-stop"), ("Alm_IntlkTrip", "Interlock trip"), ("Alm_ExcessStarts", "Excess starts")] + extra_alarms),
        trend(pens),
        maint(vw),
        config(vw, [("Feedback time", "Cfg_FbkTime", "s"), ("Restart delay", "Cfg_RestartDly", "s"), ("Rated current", "Cfg_RatedAmps", "A"),
                    ("Max starts / hr", "Cfg_MaxStartsHr", ""), ("Auto restart", "?Cfg_AutoRestart", "")] + extra_cfg),
    ])

def rotating():
    return motor_like("Docks/Rotating", "T_Motor", None,
                      [("Alm_OL", "Overload"), ("Alm_HiCurrent", "High current")], None,
                      [("High current limit", "Alm_HiCurrent/Cfg_Lim", "A")], ["Val_Current", "Sts_Running"])

def vfd():
    def cmd(vw):
        rd = f"{vw.m('Mode/Sts_Man')} && {vw.m('Sts_Avail')}"
        return [entry(vw, "Spd", "Speed", "Cmd_Spd", OP, "", enabled=rd),
                flex("Dir", "row", [button("Fwd", "FWD", "efc.ui.cmd(self, 'Cmd_Rev', False, 1)", cls="Button/Default", enabled=rd),
                                    button("Rev", "REV", "efc.ui.cmd(self, 'Cmd_Rev', True, 1)", cls="Button/Default", enabled=rd)],
                     basis=v(32), pc={"position.display": expr(vw.m("Cfg_Reversible"))}, extra={"style": {"classes": "", "gap": v(4)}})]
    def vals(vw):
        m = vw.m; eu = m("Cfg_SpdEU")
        return [row("Ref", "Speed ref", fmt(m("Val_SpdRef")), eu), row("Spd", "Speed", fmt(m("Val_Spd")), eu),
                row("Trq", "Torque", fmt(m("Val_Torque")), "'%'"), row("Pwr", "Power", fmt(m("Val_Power")), "'kW'"),
                row("Code", "Drive fault code", fmt(m("Inp_FaultCode"), "0"), show=m("Sts_Fault"))]
    return motor_like("Docks/VFD", "T_VFD", vals,
                      [("Alm_DrvFault", "Drive fault"), ("Alm_DrvWarn", "Drive warning"), ("Alm_CommFail", "Drive comm fail"),
                       ("Alm_SpdDev", "Speed deviation")], cmd,
                      [("Speed min", "Cfg_SpdMin", ""), ("Speed max", "Cfg_SpdMax", ""), ("Speed dev limit", "Cfg_SpdDevLim", ""),
                       ("Speed dev time", "Cfg_SpdDevTime", "s")], ["Val_Spd", "Val_SpdRef", "Val_Current"])

def heater():
    vw = View(); m = vw.m
    rd = ready_expr(vw)
    pwr = f"{m('Cfg_CtrlType')} > 0"
    ctype = f"case(toInt({m('Cfg_CtrlType')}), 0, 'On/off', 1, 'Time-proportioned (SSR)', 2, 'SCR phase angle', '?')"
    return window("Docks/Heater", "T_Heater", vw, [
        header(vw),
        banner(vw, [(m("Sts_HiLimit"), "HIGH LIMIT", "State/Fault"), (m("Sts_Tripped"), "TRIPPED", "State/Fault"),
                    (m("Sts_Fault"), "FAULT", "State/Fault"), (m("Sts_Heating"), "HEATING", "State/Running"),
                    (m("Sts_On"), "ON", "State/Running"), (m("Sts_Off"), "OFF", "State/Stopped")],
               common_chips(vw) + [(m("Sts_NotPerm"), "NOT PERM")]),
        mode_section(vw),
        commands(vw, [("ON", "Cmd_On", "Button/Start", OP, rd), ("OFF", "Cmd_Off", "Button/Stop", OP, None),
                      ("RESET", "Cmd_Reset", "Button/Default", OP, None)],
                 extra=[entry(vw, "Pwr", "Power demand", "Cmd_Pwr", OP, "%", enabled=rd, show=pwr)]),
        section("Values", "Values", [row("Type", "Control", ctype), row("Dem", "Power demand", fmt(m("Val_PwrDemand")), "'%'", show=pwr),
                                     row("Duty", "Duty", fmt(m("Val_Duty")), "'%'", show=pwr), row("Pwr", "Power", fmt(m("Val_Power")), "'kW'"),
                                     row("Cur", "Current", fmt(m("Val_Current")), "'A'"), row("Load", "Load", fmt(m("Val_LoadPct"), "0"), "'%'"),
                                     row("NE107", "Diagnostics", ne107(vw))]),
        intlk("Perm", "Permissives", "Perm"), intlk("Intlk", "Interlocks", "Intlk"),
        alarms(vw, [("Alm_HiLimit", "High-limit trip"), ("Alm_Shorted", "Shorted SSR/SCR"), ("Alm_LoadFail", "Element load failure"),
                    ("Alm_FailOn", "Fail to energise"), ("Alm_FailOff", "Fail to de-energise"), ("Alm_ScrFault", "SCR fault"),
                    ("Alm_IntlkTrip", "Interlock trip")]),
        trend(["Val_Power", "Val_PwrDemand", "Val_Current"]),
        maint(vw),
        config(vw, [("Cycle time", "Cfg_CycleTime", "s"), ("Min pulse", "Cfg_MinPulse", "s"), ("Power min", "Cfg_PwrMin", "%"),
                    ("Power max", "Cfg_PwrMax", "%"), ("Power rate", "Cfg_PwrRate", "%/s"), ("Rated power", "Cfg_RatedKW", "kW"),
                    ("Rated current", "Cfg_RatedAmps", "A"), ("Load fail", "Cfg_LoadFailPct", "%"), ("Leak current", "Cfg_LeakAmps", "A"),
                    ("Feedback time", "Cfg_FbkTime", "s")]),
    ])

def heat_transfer():
    vw = View(); m = vw.m
    t = lambda n, txt, mem, u: row(n, txt, fmt(m(mem)), repr(u))
    return window("Docks/HeatTransfer", "T_HeatEx", vw, [
        header(vw),
        banner(vw, [(m("Sts_CalcValid"), "CALC VALID", "State/Running"), ("true", "CALC INVALID", "State/Unknown")], []),
        section("Values", "Values", [t("HI", "Hot in", "Inp_HotInT", "°C"), t("HO", "Hot out", "Inp_HotOutT", "°C"),
                                     t("CI", "Cold in", "Inp_ColdInT", "°C"), t("CO", "Cold out", "Inp_ColdOutT", "°C"),
                                     t("HF", "Hot flow", "Inp_HotFlow", ""), t("CF", "Cold flow", "Inp_ColdFlow", ""),
                                     t("Duty", "Duty", "Val_Duty", "kW"), t("LMTD", "LMTD", "Val_LMTD", "K"), t("UA", "UA", "Val_UA", "kW/K"),
                                     t("Clean", "Cleanliness", "Val_Clean", "%"), t("App", "Approach", "Val_Approach", "K"),
                                     row("Eff", "Effectiveness", fmt(m("Val_Effect") + " * 100"), repr("%"))]),   # PCLib Val_Effect is 0-1: show as %
        alarms(vw, [("Alm_Fouling", "Fouling"), ("Alm_HotDP", "Hot side dP high"), ("Alm_ColdDP", "Cold side dP high"),
                    ("Alm_HeatBal", "Heat balance error"), ("Alm_HiOutT", "Outlet temperature high")]),
        trend(["Val_Clean", "Val_UA"]),
        config(vw, [("Design UA", "Cfg_DesignUA", "kW/K"), ("Min flow", "Cfg_MinFlow", ""), ("Calc filter", "Cfg_CalcFilt", "s"),
                    ("Fouling limit", "Alm_Fouling/Cfg_Lim", "%"), ("Hot dP limit", "Alm_HotDP/Cfg_Lim", ""),
                    ("Cold dP limit", "Alm_ColdDP/Cfg_Lim", ""), ("Outlet T limit", "Alm_HiOutT/Cfg_Lim", "°C")]),
    ])

def process_value():
    vw = View(); m = vw.m
    eu = m("Cfg_EU")
    lim = [(f"{k} limit", f"Alm_{k}/Cfg_Lim", "") for k in ("HH", "H", "L", "LL")]
    return window("Docks/ProcessValue", "T_AI", vw, [
        header(vw),
        banner(vw, [(m("Sts_Bad"), "BAD QUALITY", "State/Fault"),
                    ("true", f"{fmt(m('Val_PV'))} + ' ' + {eu}", "State/Stopped")],
               [(m("Sts_Sim"), "SIM"), (m("Sts_Subst"), "SUBST"), (m("Sts_ORng"), "OVER"), (m("Sts_URng"), "UNDER")]),
        section("Values", "Values", [row("PV", "Value", fmt(m("Val_PV")), eu), row("Pct", "Of range", fmt(m("Val_PVPct"), "0"), "'%'"),
                                     row("ROC", "Rate of change", fmt(m("Val_ROC"), "#,##0.###"), eu + " + '/s'"),
                                     row("Rng", "Range", f"{fmt(m('Cfg_EUMin'), '#,##0.##')} + ' .. ' + {fmt(m('Cfg_EUMax'), '#,##0.##')}", eu),
                                     row("NE107", "Diagnostics", ne107(vw))]),
        alarms(vw, [("Alm_HH", "High high"), ("Alm_H", "High"), ("Alm_L", "Low"), ("Alm_LL", "Low low"),
                    ("Alm_ROC", "Rate of change"), ("Alm_Bad", "Bad quality")]),
        trend(["Val_PV"]),
        section("Maintenance", "Maintenance", [check("Sim", "Simulate", "Sim_En", MAINT),
                                               entry(vw, "SimPV", "Simulated value", "Sim_PV", MAINT, "", show=m("Sim_En"))], show=lvl(MAINT)),
        config(vw, lim + [("ROC limit", "Alm_ROC/Cfg_Lim", "/s")], name="Limits", title="Alarm limits"),
        config(vw, [("EU min", "Cfg_EUMin", ""), ("EU max", "Cfg_EUMax", ""), ("Raw min", "Cfg_RawMin", ""), ("Raw max", "Cfg_RawMax", ""),
                    ("Filter TC", "Cfg_FiltTC", "s"), ("Low cutoff", "Cfg_LoCutoff", ""), ("Square root", "?Cfg_SqrtExtract", "")]),
    ])

def loop():
    vw = View(); m = vw.m
    eu = m("Cfg_PVEU")
    mb = lambda n, t, mem, sts: button(n, t, f"efc.ui.cmd(self, '{mem}', True, 1)", cls="Button/Toggle/Off", show=lvl(OP))
    b = []
    for n, t, mem, sts in (("Man", "MAN", "Cmd_Man", "Sts_Man"), ("Auto", "AUTO", "Cmd_Auto", "Sts_Auto"), ("Cas", "CAS", "Cmd_Cas", "Sts_Cas")):
        x = mb(n, t, mem, sts); x["propConfig"]["props.style.classes"] = expr(f"if({m(sts)}, 'Button/Toggle/On', 'Button/Toggle/Off')"); b.append(x)
    return window("Docks/Loop", "T_PID", vw, [
        header(vw),
        banner(vw, [(m("Sts_Intlk"), "INTERLOCKED", "State/Fault"), (m("Sts_Track"), "TRACKING", "State/Transition"),
                    (m("Sts_Cas"), "CASCADE", "State/Running"), (m("Sts_Auto"), "AUTO", "State/Running"), (m("Sts_Man"), "MANUAL", "State/Stopped")],
               [(m("Sts_WindupHi"), "WINDUP HI"), (m("Sts_WindupLo"), "WINDUP LO"), (m("Sts_SPRamping"), "RAMPING")]),
        section("Mode", "Mode", [flex("Buttons", "row", b, basis=v(32), extra={"style": {"classes": "", "gap": v(4)}})], show=lvl(OP)),
        section("Values", "Values", [row("PV", "PV", fmt(m("Val_PV")), eu), row("SP", "SP", fmt(m("Val_SP")), eu),
                                     row("CV", "Output", fmt(m("Out_CV")), "'%'"), row("Err", "Error", fmt(m("Val_Err")), eu),
                                     entry(vw, "SPe", "Setpoint", "Cmd_SP", OP, "", enabled=f"!{m('Sts_Cas')}"),
                                     entry(vw, "CVe", "Output", "Cmd_CV", OP, "%", enabled=m("Sts_Man"))]),
        intlk("Intlk", "Interlocks", "Intlk"),
        alarms(vw, [("Alm_DevH", "Deviation high"), ("Alm_DevL", "Deviation low"), ("Alm_PVBad", "PV bad")]),
        trend(["Val_PV", "Val_SP", "Out_CV"]),
        config(vw, [("Gain (Kp)", "Cfg_Kp", ""), ("Integral (Ti)", "Cfg_Ti", "s"), ("Derivative (Td)", "Cfg_Td", "s"),
                    ("Deadband", "Cfg_DB", ""), ("SP rate", "Cfg_SPRate", "/s"), ("CV rate", "Cfg_CVRate", "%/s"),
                    ("Direct acting", "?Cfg_DirectAct", "")], name="Tuning", title="Tuning"),
        config(vw, [("Dev high limit", "Alm_DevH/Cfg_Lim", ""), ("Dev low limit", "Alm_DevL/Cfg_Lim", ""), ("SP min", "Cfg_SPMin", ""),
                    ("SP max", "Cfg_SPMax", ""), ("CV min", "Cfg_CVMin", "%"), ("CV max", "Cfg_CVMax", "%"), ("PV min", "Cfg_PVMin", ""),
                    ("PV max", "Cfg_PVMax", "")]),
    ])

def io_card():
    """Native x80 device DDT (decision 23): summary + FULL FACEPLATE opens the card's existing faceplate popup."""
    vw = View(); m = vw.m
    full = ("model = self.view.params.model\nif model:\n\tp = self.view.params.tagPath\n"
            "\tsystem.perspective.openPopup('io_' + p, 'Templates/IO/Faceplates/' + model, params={'cardPath': p},\n"
            "\t\ttitle='', showCloseIcon=False, draggable=True, resizable=False, modal=False)")
    blocks = [
        header(vw),
        banner(vw, [(f"isNull({m('Module/MOD_ERROR')}) || !isGood({m('Module/MOD_ERROR')})", "UNKNOWN", "State/Unknown"),
                    (m("Module/MOD_ERROR"), "MODULE ERROR", "State/Fault"), ("true", "OK", "State/Running")], []),
        section("Card", "Card", [row("Model", "Model", "{view.params.model}"), row("Rack", "Rack", m("Rack")), row("Slot", "Slot", m("Slot")),
                                 row("Desc", "Description", m("CardDesc")), row("Diag", "Diagnostic", m("Module/HMI/DiagText")),
                                 button("Full", "FULL FACEPLATE", full, cls="Button/Primary", grow=0)]),
    ]
    for k in ("Cfg_Tag", "Cfg_Desc"):                       # native DDTs have no Cfg_Tag / Cfg_Desc: show the card instead
        vw.custom.pop("m_" + k); vw.pc.pop("custom.m_" + k)   # must happen before window() copies vw.pc
    path, view = window("Docks/IOCard", "native", vw, blocks)
    hdr = view["root"]["children"][0]["children"][0]["children"]
    hdr[0]["propConfig"]["props.text"] = expr("'Rack ' + " + m("Rack") + " + ' / slot ' + " + m("Slot"))
    hdr[1]["propConfig"]["props.text"] = expr("{view.params.model}")
    view["params"]["model"] = ""; view["propConfig"]["params.model"] = {"paramDirection": "input", "persistent": True}
    return path, view

# ----------------------------------------------------------------- parts
def intlk_list():
    """Docks/Parts/IntlkList: one T_Intlk (16 conditions). Bypass/unbypass Supervisor+ (reason, audit); reset Maint+."""
    vw = View()
    m = vw.m
    rows = []
    for i in range(16):
        used, ok, byp = m(f"Cfg_Used/{i}"), m(f"Inp_Cond/{i}"), m(f"Sts_Bypassed/{i}")
        desc, bpa, left = m(f"Cfg_CondDesc/{i}"), m(f"Cfg_Bypassable/{i}"), m(f"Sts_BypLeft/{i}")
        led = comp("ia.display.label", "LED", {"text": "", "style": {"classes": "Indicator/LED/Off"}}, {"shrink": 0, "basis": v(12)},
                   {"props.style.classes": expr(f"if({byp}, 'Indicator/LED/Unknown', if({ok}, 'Indicator/LED/On', 'Indicator/LED/Fault'))")})
        rows.append(flex(f"C{i}", "row", [
            led, label("Desc", "", "Text/Caption Text/Mod/Ellipsis", grow=1, pc={"props.text": expr(desc)}),
            label("Left", "", "Indicator/Badge", pc={"props.text": expr(f"'BYPASSED ' + toInt({left} / 60000) + ' min'"),
                                                     "position.display": expr(byp)}),
            button("Byp", "BYPASS", f"system.perspective.openPopup('efcBypass', 'Docks/Parts/BypassConfirm', params={{'tagPath': self.view.params.tagPath, 'idx': {i}, 'desc': self.view.custom.m_Cfg_CondDesc_{i}}}, modal=True, showCloseIcon=False)",
                   cls="Button/Small", show=f"{lvl(SUP)} && {bpa} && !{byp}", grow=0),
            button("Unbyp", "UNBYP", f"efc.ui.unbypass(self, self.view.params.tagPath, {i})", cls="Button/Small", show=f"{lvl(SUP)} && {byp}", grow=0),
        ], basis=v(24), pc={"position.display": expr(used)}, extra={"alignItems": "center", "style": {"classes": "", "gap": v(4)}}))
    root = flex("root", "column", [
        flex("Header", "row", [label("Title", "", "Text/Subheader Text/Mod/Upper", grow=1, pc={"props.text": expr("{view.params.title}")}),
                               label("Ok", "", "Indicator/Badge", pc={"props.text": expr(f"if({m('Out_OK')}, 'OK', 'NOT OK')"),
                                                                      "props.style.classes": expr(f"if({m('Out_OK')}, 'Indicator/Permissive', 'Indicator/Interlock')")})],
             extra={"alignItems": "center"}),
        *rows,
        button("Reset", "RESET", "efc.ui.cmd(self, 'Cmd_Reset', True, 2, audit=True)", cls="Button/Default",
               show=f"{lvl(MAINT)} && {m('Sts_ResetReq')}", grow=0),
    ], extra={"style": {"classes": "Container/GroupBox", "gap": v(2)}})
    params = {"tagPath": "", "title": ""}
    pc = dict(vw.pc, **{"params." + p: {"paramDirection": "input", "persistent": True} for p in params})
    return "Docks/Parts/IntlkList", {"custom": vw.custom, "params": params, "propConfig": pc,
                                     "props": {"defaultSize": {"width": W - 16, "height": 120}}, "root": root}

def bypass_confirm():
    vw = View()
    ok = ("if efc.ui.bypass(self, self.view.params.tagPath, self.view.params.idx, self.view.custom.reason):\n"
          "\tsystem.perspective.closePopup('efcBypass')")
    root = flex("root", "column", [
        label("Title", "Bypass condition", "Text/Title"),
        label("Desc", "", "Text/Body", pc={"props.text": expr("{view.params.desc}")}),
        label("Note", "Supervisor or higher. The reason and your user name go to the audit log; the bypass times out "
                      "at the block's Cfg_BypassMax.", "Text/Caption Text/Mod/Wrap"),
        comp("ia.input.text-field", "Reason", {"placeholder": "Reason (required)", "style": {"classes": "Input/Field"}},
             {"shrink": 0, "basis": v(32)}, {"props.text": {"binding": {"type": "property", "config": {"path": "view.custom.reason", "bidirectional": True}}}}),
        flex("Buttons", "row", [button("Cancel", "CANCEL", "system.perspective.closePopup('efcBypass')", cls="Button/Default"),
                                button("Ok", "BYPASS", ok, cls="Button/Danger",
                                       enabled=f"{lvl(SUP)} && len(trim({{view.custom.reason}})) > 0")],
             basis=v(36), extra={"style": {"classes": "", "gap": v(6)}}),
    ], extra={"style": {"classes": "Container/Popup", "gap": v(8)}})
    vw.custom["reason"] = ""
    params = {"tagPath": "", "idx": 0, "desc": ""}
    pc = dict(vw.pc, **{"params." + p: {"paramDirection": "input", "persistent": True} for p in params})
    return "Docks/Parts/BypassConfirm", {"custom": vw.custom, "params": params, "propConfig": pc,
                                         "props": {"defaultSize": {"width": 360, "height": 260}}, "root": root}

RANGES = [("24h", 1440), ("8h", 480), ("1h", 60), ("30m", 30), ("5m", 5)]
def trend_part():
    """Docks/Parts/Trend: history of the pens, default 30 min. The expand toggle is an in/out param the window
    uses to grow the graph vertically (never wider, decision 26); the range box shows while expanded."""
    sw, sh = 360, 100
    tr = {"type": "script", "code": "\treturn efc.ui.trend(self.view.params.tagPath, list(self.view.params.pens or []), self.view.custom.range, %d, %d)" % (sw, sh)}
    custom = {"range": 30, "hist": {"d": ["", "", ""], "lo": "", "hi": ""}}
    pc = {"custom.hist": {"binding": {"type": "expr", "config": {"expression": "{view.custom.range} + toMillis(now(10000)) * 0"}, "transforms": [tr]}}}
    for p, d in (("tagPath", "input"), ("pens", "input"), ("expanded", "inout")):
        pc["params." + p] = {"paramDirection": d, "persistent": True}
    els = [{"type": "path", "name": f"pen{i}", "d": "", "fill": {"paint": "transparent"},
            "stroke": {"paint": c, "width": 1.5}} for i, c in enumerate(["#1F1F1F", "#1F4E99", "#7F7F7F"])]
    svg = comp("ia.shapes.svg", "Graph", {"viewBox": f"0 0 {sw} {sh}", "preserveAspectRatio": "none", "elements": els,
                                          "style": {"classes": "Container/Inset"}}, {"shrink": 0, "grow": 1, "basis": "0px"},
               {f"props.elements[{i}].d": expr(f"try({{view.custom.hist.d[{i}]}}, '')") for i in range(3)})
    rng = [button(f"R{n}", n, f"self.view.custom.range = {mins}", cls="Button/Small", grow=0) for n, mins in RANGES]
    for b, (n, mins) in zip(rng, RANGES):
        b.setdefault("propConfig", {})["props.style.classes"] = expr(f"if({{view.custom.range}} = {mins}, 'Button/TabActive', 'Button/Tab')")
    head = flex("Header", "row", [
        label("Title", "", "Text/Subheader Text/Mod/Upper", grow=1,
              pc={"props.text": expr("'History (' + case({view.custom.range}, 1440, '24 h', 480, '8 h', 60, '1 h', 5, '5 min', '30 min') + ')'")}),
        flex("Ranges", "row", rng, pc={"position.display": expr("{view.params.expanded}")}, extra={"style": {"classes": "", "gap": v(2)}}),
        button("Expand", "⤢", "self.view.params.expanded = not self.view.params.expanded", cls="Button/Icon", grow=0)],
        basis=v(26), extra={"alignItems": "center", "style": {"classes": "", "gap": v(4)}})
    axis = flex("Axis", "row", [label("Lo", "", "Text/Micro", pc={"props.text": expr("try({view.custom.hist.lo}, '')")}),
                                label("Span", "", "Text/Micro Text/Mod/Center", grow=1,
                                      pc={"props.text": expr("'-' + case({view.custom.range}, 1440, '24 h', 480, '8 h', 60, '1 h', 5, '5 min', '30 min') + '  ..  now'")}),
                                label("Hi", "", "Text/Micro", pc={"props.text": expr("try({view.custom.hist.hi}, '')")})], basis=v(14))
    root = flex("root", "column", [head, svg, axis], extra={"style": {"classes": "Container/TrendPanel", "gap": v(2)}})
    return "Docks/Parts/Trend", {"custom": custom, "params": {"tagPath": "", "pens": [], "expanded": False}, "propConfig": pc,
                                 "props": {"defaultSize": {"width": W - 16, "height": 170}}, "root": root}

def region():
    """Docks/Region: the screen's right region (400 x 860). Put one on each screen and set defaultDock to that
    screen's default view; templates replace it with their dynamic window, close returns to the default."""
    tr = {"type": "script", "code": "\treturn efc.ui.region(value, self.page.props.pageId)"}
    dw = comp("ia.display.view", "Window", {"path": "", "params": {}, "useDefaultViewWidth": False, "useDefaultViewHeight": False},
              {"shrink": 0, "grow": 1, "basis": "0px"},
              {"props.path": {"binding": {"type": "property", "config": {"path": "view.custom.dw"}, "transforms": [
                  {"type": "script", "code": "\treturn (value or {}).get('path') or ''"}]}},
               "props.params": {"binding": {"type": "property", "config": {"path": "view.custom.dw"}, "transforms": [
                   {"type": "script", "code": "\treturn dict((value or {}).get('params') or {})"}]}}})
    root = flex("root", "column", [dw], extra={"style": {"classes": "Container/Panel"}},
                events={"system": {"onStartup": script("efc.ui.setDefaultDock(self, self.view.params.defaultDock, self.view.params.defaultParams)")}})
    pc = {"custom.dw": {"binding": {"type": "property", "config": {"path": "session.custom.efcDw"}, "transforms": [tr]}},
          "params.defaultDock": {"paramDirection": "input", "persistent": True},
          "params.defaultParams": {"paramDirection": "input", "persistent": True}}
    return "Docks/Region", {"custom": {"dw": {"path": "", "params": {}}}, "params": {"defaultDock": "", "defaultParams": {}},
                            "propConfig": pc, "props": {"defaultSize": {"width": W, "height": H}}, "root": root}

# ----------------------------------------------------------------- write
VIEWS = [valve_discrete, valve_analog, rotating, vfd, heater, heat_transfer, process_value, loop, io_card,
         intlk_list, bypass_confirm, trend_part, region]

def build():
    proj = project_dir(PROJECT)
    if os.path.exists(proj):
        import shutil; shutil.rmtree(proj)
    write(os.path.join(proj, "project.json"), project_json(PROJECT, "EFC dynamic windows, parts, screen region and efc.ui"))
    for fn in VIEWS:
        path, view = fn()
        classify(view["root"])
        d = os.path.join(proj, PERSPECTIVE, "views", path)
        write(os.path.join(d, "view.json"), dump(view))
        write(os.path.join(d, "resource.json"), resource_json(["view.json"], "build_docks.py"))
    d = os.path.join(proj, "ignition", "script-python", "efc", "ui")
    write(os.path.join(d, "code.py"), open(os.path.join(HERE, "efc_ui.py")).read())
    write(os.path.join(d, "resource.json"), resource_json(["code.py"], "build_docks.py").replace('"scope": "G"', '"scope": "A"'))
    print(f"{PROJECT}: {len(VIEWS)} views + efc.ui -> {proj}")

if __name__ == "__main__":
    build()
