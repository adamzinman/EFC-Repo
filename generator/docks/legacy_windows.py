"""
Legacy-ddt dynamic windows (generator/legacy_types.py): the same view paths as build_docks.py, bound to the old UDT set.
  Templates/Dynamic Window/Valves/ValveDiscrete       DDT_Valve
  Templates/Dynamic Window/Valves/ValveAnalog         PID_ControlValve (library UDT; no plant DDT_ for analog valves)
  Templates/Dynamic Window/Rotating/Rotating, VFD     DDT_Device
  Templates/Dynamic Window/HeatTransfer/Heater        DDT_Device (ON / OFF words)
  Templates/Dynamic Window/HeatTransfer/HeatTransfer  placeholder: no legacy type carries heat-exchanger calculations
  Templates/Dynamic Window/ProcessValues/ProcessValue DDT_Process_Value
  Templates/Dynamic Window/Loops/Loop                 PID_Loop (library UDT; no plant DDT_ loop type)
  Templates/Dynamic Window/IO/IOCard                  unchanged (native x80 DDTs)
  Templates/Dynamic Window/Parts/IntlkList            MEM_Interlock_List (DDT_Valve.InterlockList)
  Templates/Dynamic Window/Parts/Trend                unchanged
  (Parts/BypassConfirm is not built: the legacy types have no bypass)
Legacy commands are levels (HMI_CMD TRUE / FALSE through efc.ui.cmd); mode requests are rising edges in the DFBs and go
through efc.ui.pulse (TRUE, then FALSE after 1 s). Sections whose data the legacy type does not carry (T_Alarm lists,
maintenance counters, most configuration) are left out; docs/legacy-ddt-fork.md lists every reduction.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_docks import (comp, expr, flex, label, button, lvl, OP, MAINT, SUP, ENG, View, section, row, fmt, entry, check,
                         banner, trend, config, window, v, io_card, trend_part, W)

DW = "Templates/Dynamic Window/"


# ----------------------------------------------------------------- shared legacy blocks
TAIL = "substring({view.params.tagPath}, lastIndexOf({view.params.tagPath}, '/') + 1)"


def header(vw, name=None):
    """Name / Description (memory members on the legacy UDTs; PID_Loop has only Description) and the close button."""
    name = name or f"if(len(coalesce({vw.m('Name')}, '')) > 0, {vw.m('Name')}, {TAIL})"
    return flex("Header", "row", [
        flex("Names", "column", [label("Tag", "", "Text/TagName", pc={"props.text": expr(name)}),
                                 label("Desc", "", "Text/Caption Text/Mod/Ellipsis", pc={"props.text": expr(vw.m("Description"))})], grow=1),
        button("Close", "✕", "efc.ui.closeDynamic(self)", cls="Button/Icon", grow=0)],
        basis=v(56), cls="Container/PopupHeader", extra={"alignItems": "center", "style": {"classes": "Container/PopupHeader"}})


def mode_section(vw):
    """DDT_Valve / DDT_Device modes: Auto, Manual, Off and LockedOut bits; HMI_* requests are rising edges (pulse)."""
    m = vw.m
    cur = f"if({m('LockedOut')}, 'LOCKOUT', if({m('Off')}, 'OFF', if({m('Manual')}, 'MAN', if({m('Auto')}, 'AUTO', '---'))))"
    spec = [("Auto", "AUTO", "HMI_Auto", OP, "Auto"), ("Man", "MAN", "HMI_Manual", OP, "Manual"),
            ("Off", "OFF", "HMI_Off", MAINT, "Off"), ("Lock", "LOCKOUT", "HMI_Lockout", MAINT, "LockedOut")]
    b = []
    for n, t, mem, lv, sts in spec:
        x = button(n, t, f"efc.ui.pulse(self, '{mem}', {lv}, audit={lv >= MAINT})", show=lvl(lv), cls="Button/Toggle/Off")
        x["propConfig"]["props.style.classes"] = expr(f"if({m(sts)}, 'Button/Toggle/On', 'Button/Toggle/Off')")
        b.append(x)
    return section("Mode", "Mode", [row("Current", "Mode", cur), flex("Buttons", "row", b, basis=v(32), extra={"style": {"classes": "", "gap": v(4)}})])


def commands(buttons, extra=(), hint=""):
    """buttons: [(TEXT, script body, class, minlvl, enabled_expr or None)]"""
    b = [button(f"B{i}", t, body, cls=cls, show=lvl(lv), enabled=en) for i, (t, body, cls, lv, en) in enumerate(buttons)]
    kids = [flex("Buttons", "row", b, basis=v(32), extra={"style": {"classes": "", "gap": v(4)}})] + list(extra)
    if hint:
        kids.append(label("Hint", hint, "Text/Micro Text/Color/Muted"))
    return section("Commands", "Commands", kids, show=lvl(OP))


def level_cmd(member, value):
    return f"efc.ui.cmd(self, '{member}', {value}, 1)"


def ready(vw, on_extra=()):
    """Manual, not locked out, not Off (+ the extra FALSE conditions needed to switch on)."""
    m = vw.m
    parts = [m("Manual"), "!" + m("LockedOut"), "!" + m("Off")] + ["!" + x for x in on_extra]
    return " && ".join(parts)


def intlk_embed(vw, active_member="Interlock"):
    """Embedded Parts/IntlkList on the DDT_Valve InterlockList member (a MEM_Interlock_List instance)."""
    return comp("ia.display.view", "Intlk", {"path": DW + "Parts/IntlkList", "useDefaultViewHeight": True,
                                             "params": {"tagPath": "", "title": "Interlocks", "active": False}}, {"shrink": 0},
                {"props.params.tagPath": expr("{view.params.tagPath} + '/InterlockList'"),
                 "props.params.active": expr(vw.m(active_member))})


def onoff(x): return f"if({x}, 'ON', 'off')"


# ----------------------------------------------------------------- windows
def valve_discrete():
    vw = View(); m = vw.m
    fb = m("Feedback_Enabled")
    rd_off, rd_on = ready(vw), ready(vw, [m("Interlock"), m("Permissive")])
    return window(DW + "Valves/ValveDiscrete", "DDT_Valve", vw, [
        header(vw),
        banner(vw, [(f"{m('ZSO')} && {m('ZSC')}", "FAULT", "State/Fault"),
                    (f"!{fb} && {m('CMD')}", "OPEN", "State/Running"), (f"!{fb} && !{m('CMD')}", "CLOSED", "State/Stopped"),
                    (f"{m('CMD')} && !{m('ZSO')}", "OPENING", "State/Transition"), (f"!{m('CMD')} && !{m('ZSC')}", "CLOSING", "State/Transition"),
                    (m("ZSO"), "OPEN", "State/Running"), (m("ZSC"), "CLOSED", "State/Stopped")],
               [(m("LockedOut"), "LOCKED OUT"), (m("Interlock"), "INTLK"), (m("Permissive"), "NOT PERM")]),
        mode_section(vw),
        commands([("OPEN", level_cmd("HMI_CMD", True), "Button/Start", OP, rd_on), ("CLOSE", level_cmd("HMI_CMD", False), "Button/Stop", OP, rd_off)],
                 hint="Enabled in MAN, not locked out, not OFF. OPEN also needs the permissive and no interlock (HMI_CMD is a level)"),
        section("Feedback", "Feedback", [row("ZSO", "Open limit (ZSO)", onoff(m("ZSO")), show=fb), row("ZSC", "Closed limit (ZSC)", onoff(m("ZSC")), show=fb),
                                         row("NoFb", "Feedback", "'not fitted: state follows CMD'", show="!" + fb),
                                         row("Req", "Automation request (REQ)", onoff(m("REQ"))),
                                         row("Cycles", "Cycle count", fmt(m("Cycle_Count"), "#,##0"))]),
        intlk_embed(vw),
        trend(["CMD", "ZSO"]),
        section("Counters", "Counters", [button("ResetCount", "RESET CYCLE COUNT", "efc.ui.pulse(self, 'Reset_Count', 2, audit=True)", cls="Button/Default", grow=0)],
                show=lvl(MAINT)),
        config(vw, [("Feedback (limit switches) fitted", "?Feedback_Enabled", "")]),
    ])


def valve_analog():
    vw = View(); m = vw.m
    fb = m("Feedback_Enabled")
    pos = f"if({fb}, {m('Pos')}, {m('Out')})"
    rd = f"{m('Mode')} = 1 && !{m('Intlk')}"
    presets = [button(f"P{p}", f"{p}%", f"efc.ui.cmd(self, 'Out', {float(p)}, 1)", cls="Button/Default", enabled=rd) for p in (0, 25, 50, 75, 100)]
    mb = []
    for n, t, val in (("Auto", "AUTO", 0), ("Man", "MAN", 1)):
        x = button(n, t, f"efc.ui.cmd(self, 'Mode', {val}, 1)", show=lvl(OP), cls="Button/Toggle/Off")
        x["propConfig"]["props.style.classes"] = expr(f"if({m('Mode')} = {val}, 'Button/Toggle/On', 'Button/Toggle/Off')")
        mb.append(x)
    return window(DW + "Valves/ValveAnalog", "PID_ControlValve", vw, [
        header(vw),
        banner(vw, [(f"isNull({m('Out')}) || !isGood({m('Out')})", "UNKNOWN", "State/Unknown"),
                    (m("Fault"), "FAULT", "State/Fault"), (m("Intlk"), "INTERLOCKED", "State/Fault"),
                    (f"({pos}) <= 1", "CLOSED", "State/Stopped"), ("true", f"'OPEN ' + {fmt(pos, '0')} + ' %'", "State/Running")],
               [(f"!{m('PermOK')}", "NOT PERM")]),
        section("Mode", "Mode", [row("Current", "Mode", f"if({m('Mode')} = 1, 'MAN', 'AUTO')"),
                                 flex("Buttons", "row", mb, basis=v(32), extra={"style": {"classes": "", "gap": v(4)}})]),
        commands([], extra=[entry(vw, "Pos", "Manual position (Out)", "Out", OP, "%", enabled=rd),
                            flex("Presets", "row", presets, basis=v(32), extra={"style": {"classes": "", "gap": v(4)}})],
                 hint="Position entry and presets write Out; enabled in MAN, not interlocked"),
        section("Values", "Values", [row("Dem", "Demand (Out)", fmt(m("Out")), "'%'"),
                                     row("Pos", "Position (Pos)", fmt(m("Pos")), "'%'", show=fb),
                                     row("Dev", "Deviation (Out - Pos)", fmt(f"{m('Out')} - {m('Pos')}"), "'%'", show=fb)]),
        trend(["Out", "Pos"]),
        config(vw, [("Feedback (position transmitter) fitted", "?Feedback_Enabled", "")]),
    ])


def device(path, ttype_label, words, verbs):
    """DDT_Device window. words: (off, on, switching on, switching off); verbs: (START, STOP) button texts."""
    vw = View(); m = vw.m
    fb = m("FB_Enb")
    perm_missing = f"!if({m('Manual')}, {m('Man_Perm')}, {m('Auto_Perm')})"
    rd_off, rd_on = ready(vw), ready(vw, [m("Interlock"), f"!{m('Man_Perm')}"])
    stall = m("Enable_Stalling")
    return window(path, "DDT_Device", vw, [
        header(vw),
        banner(vw, [(m("Alarm"), "FAULT", "State/Fault"), (m("Stalled"), "STALLED", "State/Fault"),
                    (f"!{fb} && {m('CMD')}", words[1], "State/Running"), (f"!{fb} && !{m('CMD')}", words[0], "State/Stopped"),
                    (f"{m('CMD')} && !{m('YI')}", words[2], "State/Transition"), (f"!{m('CMD')} && {m('YI')}", words[3], "State/Transition"),
                    (m("YI"), words[1], "State/Running"), ("true", words[0], "State/Stopped")],
               [(m("Warning"), "WARNING"), (m("LockedOut"), "LOCKED OUT"), (m("Interlock"), "INTLK"), (perm_missing, "NOT PERM")]),
        mode_section(vw),
        commands([(verbs[0], level_cmd("HMI_CMD", True), "Button/Start", OP, rd_on), (verbs[1], level_cmd("HMI_CMD", False), "Button/Stop", OP, rd_off)],
                 hint=f"Enabled in MAN, not locked out, not OFF. {verbs[0]} also needs Man_Perm and no interlock (HMI_CMD is a level)"),
        section("Values", "Values", [row("Fb", "Run feedback (YI)", onoff(m("YI")), show=fb),
                                     row("NoFb", "Feedback", "'not fitted: state follows CMD'", show="!" + fb),
                                     row("Req", "Automation request (REQ)", onoff(m("REQ"))),
                                     row("Hrs", "Run time", fmt(m("Runtime"), "#,##0.0"), "'h'"),
                                     row("Ratio", "Compression ratio", fmt(m("Curr_Comp_Ratio"), "#,##0.00") + " + ' / ' + " + fmt(m("Comp_Ratio"), "#,##0.00"), show=stall),
                                     row("StallT", "Stall time", fmt(m("Stall_Time"), "#,##0"), show=stall)]),
        trend(["CMD", "YI"]),
        section("Maintenance", "Maintenance", [
            row("RunHMS", "Run time counter", f"toInt({m('Run_Hour')}) + ' h ' + toInt({m('Run_Min')}) + ' min ' + toInt({m('Run_Sec')}) + ' s'"),
            button("ResetRun", "RESET RUN TIME", "efc.ui.cmd(self, 'Reset_Runtime', True, 2, audit=True)", cls="Button/Default", grow=0)], show=lvl(MAINT)),
        config(vw, [("Run feedback fitted", "?FB_Enb", ""), ("Stall detection", "?Enable_Stalling", ""),
                    ("Compression ratio limit", "Comp_Ratio", ""), ("Stall time", "Stall_Time", "")]),
    ])


def rotating():
    return device(DW + "Rotating/Rotating", "DDT_Device", ("STOPPED", "RUNNING", "STARTING", "STOPPING"), ("START", "STOP"))


def vfd():   # same DDT_Device data; no speed on the legacy type
    return device(DW + "Rotating/VFD", "DDT_Device", ("STOPPED", "RUNNING", "STARTING", "STOPPING"), ("START", "STOP"))


def heater():
    return device(DW + "HeatTransfer/Heater", "DDT_Device", ("OFF", "ON", "SWITCHING ON", "SWITCHING OFF"), ("ON", "OFF"))


def heat_transfer():
    """No legacy type carries heat-exchanger calculations: a placeholder that names the tag, so the view path exists."""
    vw = View()
    hdr = flex("Header", "row", [
        flex("Names", "column", [label("Tag", "", "Text/TagName", pc={"props.text": expr(TAIL)}),
                                 label("Desc", "Heat exchanger", "Text/Caption Text/Mod/Ellipsis")], grow=1),
        button("Close", "✕", "efc.ui.closeDynamic(self)", cls="Button/Icon", grow=0)],
        basis=v(56), cls="Container/PopupHeader", extra={"alignItems": "center", "style": {"classes": "Container/PopupHeader"}})
    note = section("Note", "Legacy types", [label("Txt", "The legacy (DDT_) type set has no heat-exchanger calculation block: duty, LMTD, UA and "
                                                     "cleanliness are only available with the EFCLib v1 T_HeatEx type. Open the fan or pump "
                                                     "of this exchanger for its DDT_Device window.", "Text/Caption Text/Mod/Wrap")])
    return window(DW + "HeatTransfer/HeatTransfer", "none", vw, [hdr, note])


def process_value():
    vw = View(); m = vw.m
    eu = m("Units")
    pct = f"({m('PV')} - {m('Eng_Min')}) / max({m('Eng_Max')} - {m('Eng_Min')}, 0.000001) * 100"
    inh = " || ".join(m(f"{k}/Inhibit") for k in ("HH", "H", "L", "LL"))
    lim_rows = []
    for k, txt in (("HH", "High high"), ("H", "High"), ("L", "Low"), ("LL", "Low low")):
        a, en, ih, sp = m(f"{k}/Alarm"), m(f"{k}/Enabled"), m(f"{k}/Inhibit"), m(f"{k}/SP")
        led = comp("ia.display.label", "LED", {"text": "", "style": {"classes": "Indicator/LED/Off"}}, {"shrink": 0, "basis": v(12)},
                   {"props.style.classes": expr(f"if({ih}, 'Indicator/LED/Unknown', if({a}, 'Indicator/LED/Fault', if({en}, 'Indicator/LED/On', 'Indicator/LED/Off')))")})
        lim_rows.append(flex(f"L{k}", "row", [
            led, label("Lbl", f"{txt} ({k})", "Text/Caption Text/Mod/Upper", grow=1),
            label("State", "", "Indicator/Badge", pc={"props.text": expr(f"if({ih}, 'INHIBITED', if(!{en}, 'DISABLED', if({a}, 'ALARM', '')))"),
                                                       "position.display": expr(f"{ih} || !{en} || {a}")}),
            label("Val", "", "Text/Value Text/Mod/Right Text/Mod/Tabular", pc={"props.text": expr(fmt(sp, "#,##0.##"))}),
            label("EU", "", "Text/Units", basis=v(40), pc={"props.text": expr(eu)})],
            basis=v(22), extra={"alignItems": "center", "style": {"classes": "", "gap": v(6)}}))
    inhibit = [check(f"I{k}", f"Inhibit {k}", f"{k}/Inhibit", SUP) for k in ("HH", "H", "L", "LL")]
    return window(DW + "ProcessValues/ProcessValue", "DDT_Process_Value", vw, [
        header(vw),
        banner(vw, [(m("HW_Fault"), "HW FAULT", "State/Fault"),
                    ("true", f"{fmt(m('PV'))} + ' ' + {eu}", "State/Stopped")],
               [(m("Overrange"), "OVER"), (m("Underrange"), "UNDER"), (inh, "INH")]),
        section("Values", "Values", [row("PV", "Value", fmt(m("PV")), eu), row("Pct", "Of range", fmt(pct, "0"), "'%'"),
                                     row("Rng", "Range", f"{fmt(m('Eng_Min'), '#,##0.##')} + ' .. ' + {fmt(m('Eng_Max'), '#,##0.##')}", eu),
                                     row("Raw", "Raw range", f"toStr({m('Raw_Min')}) + ' .. ' + toStr({m('Raw_Max')})")]),
        section("Alarms", "Alarm limits", lim_rows + [label("Hint", "Acknowledge in the alarm status table (Ignition tag alarms on the x/Alarm bits).",
                                                             "Text/Micro Text/Color/Muted")]),
        section("Inhibit", "Inhibit (Supervisor)", inhibit, show=lvl(SUP)),
        trend(["PV"]),
        config(vw, [(f"{k} limit", f"{k}/SP", "") for k in ("HH", "H", "L", "LL")], name="Limits", title="Alarm limits (edit)"),
        config(vw, [x for k in ("HH", "H", "L", "LL") for x in ((f"{k} enabled", f"?{k}/Enabled", ""), (f"{k} deadband", f"{k}/DB", ""), (f"{k} delay", f"{k}/DLY", ""))],
               name="AlarmCfg", title="Alarm configuration"),
        config(vw, [("EU min", "Eng_Min", ""), ("EU max", "Eng_Max", ""), ("Raw min", "Raw_Min", ""), ("Raw max", "Raw_Max", "")]),
    ])


def loop():
    vw = View(); m = vw.m
    eu = m("PV.engUnit")
    b = []
    for n, t, val in (("Man", "MAN", 0), ("Auto", "AUTO", 1), ("Cas", "CAS", 2)):
        x = button(n, t, f"efc.ui.cmd(self, 'Mode', {val}, 1)", cls="Button/Toggle/Off", show=lvl(OP))
        x["propConfig"]["props.style.classes"] = expr(f"if({m('Mode')} = {val}, 'Button/Toggle/On', 'Button/Toggle/Off')")
        b.append(x)
    hi, lo, dev = f"{m('PV')} >= {m('AlmHi')}", f"{m('PV')} <= {m('AlmLo')}", f"abs({m('PV')} - {m('SP')}) > {m('AlmDev')}"
    return window(DW + "Loops/Loop", "PID_Loop", vw, [
        header(vw, name=TAIL),
        banner(vw, [(f"{m('Mode')} = 2", "CASCADE", "State/Running"), (f"{m('Mode')} = 1", "AUTO", "State/Running"),
                    (f"{m('Mode')} = 0", "MANUAL", "State/Stopped")],
               [(hi, "HIGH"), (lo, "LOW"), (dev, "DEVIATION")]),
        section("Mode", "Mode", [flex("Buttons", "row", b, basis=v(32), extra={"style": {"classes": "", "gap": v(4)}})], show=lvl(OP)),
        section("Values", "Values", [row("PV", "PV", fmt(m("PV")), eu), row("SP", "SP", fmt(m("SP")), eu),
                                     row("CV", "Output", fmt(m("OUT")), "'%'"), row("Err", "Error", fmt(f"{m('PV')} - {m('SP')}"), eu),
                                     entry(vw, "SPe", "Setpoint", "SP", OP, "", enabled=f"{m('Mode')} != 2"),
                                     entry(vw, "CVe", "Output", "OUT", OP, "%", enabled=f"{m('Mode')} = 0")]),
        section("Alarms", "Alarm limits", [row("Hi", "High", fmt(m("AlmHi")), eu), row("Lo", "Low", fmt(m("AlmLo")), eu),
                                           row("Dev", "Deviation", fmt(m("AlmDev")), eu)]),
        trend(["PV", "SP", "OUT"]),
        config(vw, [("Gain (Kp)", "Kp", ""), ("Integral (Ti)", "Ti", "s"), ("Derivative (Td)", "Td", "s"),
                    ("Action (0 reverse, 1 direct)", "Action", "")], name="Tuning", title="Tuning"),
        config(vw, [("High alarm", "AlmHi", ""), ("Low alarm", "AlmLo", ""), ("Deviation alarm", "AlmDev", ""),
                    ("SP min", "SP_Lo", ""), ("SP max", "SP_Hi", ""), ("Output min", "OUT_Lo", "%"), ("Output max", "OUT_Hi", "%")]),
    ])


# ----------------------------------------------------------------- parts
N_ILIST = 20   # MEM_Interlock_List arrays have 20 entries


def intlk_list():
    """Parts/IntlkList on a MEM_Interlock_List instance: the used entries' names and descriptions. The parent's
    Interlock bit arrives as the `active` param (the list's Status[] polarity is undocumented, so it is not shown)."""
    vw = View(); m = vw.m
    names, used, desc = m("InterlockName"), m("Used"), m("Description")
    rows = []
    for i in range(N_ILIST):
        u = f"try({{view.custom.m_Used[{i}]}}, false)"
        txt = (f"try({{view.custom.m_InterlockName[{i}]}}, '') + "
               f"if(len(try({{view.custom.m_Description[{i}]}}, '')) > 0, ' - ' + try({{view.custom.m_Description[{i}]}}, ''), '')")
        rows.append(flex(f"C{i}", "row", [
            label("Dot", "•", "Text/Caption", basis=v(12)),
            label("Desc", "", "Text/Caption Text/Mod/Ellipsis", grow=1, pc={"props.text": expr(txt)})],
            basis=v(22), pc={"position.display": expr(u)}, extra={"alignItems": "center", "style": {"classes": "", "gap": v(4)}}))
    any_used = " || ".join(f"try({{view.custom.m_Used[{i}]}}, false)" for i in range(N_ILIST))
    root = flex("root", "column", [
        flex("Header", "row", [label("Title", "", "Text/Subheader Text/Mod/Upper", grow=1, pc={"props.text": expr("{view.params.title}")}),
                               label("Ok", "", "Indicator/Badge", pc={"props.text": expr("if({view.params.active}, 'ACTIVE', 'OK')"),
                                                                      "props.style.classes": expr("if({view.params.active}, 'Indicator/Interlock', 'Indicator/Permissive')")})],
             extra={"alignItems": "center"}),
        *rows,
        label("None", "No interlocks configured", "Text/Caption Text/Color/Muted", pc={"position.display": expr(f"!({any_used})")}),
    ], extra={"style": {"classes": "Container/GroupBox", "gap": v(2)}})
    params = {"tagPath": "", "title": "", "active": False}
    pc = dict(vw.pc, **{"params." + p: {"paramDirection": "input", "persistent": True} for p in params})
    return DW + "Parts/IntlkList", {"custom": vw.custom, "params": params, "propConfig": pc,
                                    "props": {"defaultSize": {"width": W - 16, "height": 120}}, "root": root}


VIEWS = [valve_discrete, valve_analog, rotating, vfd, heater, heat_transfer, process_value, loop, io_card, intlk_list, trend_part]
