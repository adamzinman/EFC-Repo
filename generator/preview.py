"""Browser preview of the v3 templates (mirrors the Perspective expressions) + active symbols + static SVG library sheet.
Demo tags come from build_pid.UDTS / build_pid.DEMO (EFCLib T_ member names); driven by preview_pid.py."""
import os, html, re
from active import SYMS, BY, svg
from pid_common import LAYOUT
from build_pid import UDTS

CSS = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build", "styles", "style_preview.html")).read().split("<style>")[1].split("</style>")[0]
CSS += """body{margin:0;padding:20px;background:#C8C8C8;font-family:Arial} h2{font:600 17px Arial;margin:18px 0 8px}
.row{display:flex;flex-wrap:wrap;gap:26px;background:#D9D9D9;padding:16px;border-radius:4px}
.t{position:relative;background:#D9D9D9}.a{position:absolute;display:flex;align-items:center;justify-content:center;box-sizing:border-box}
.line{position:absolute;height:2px;background:#333;left:-12px;right:-12px}
.mrow{display:flex;align-items:stretch;justify-content:center}.mrow>span{box-sizing:border-box;height:100%;display:flex;align-items:center}
figure{margin:0;display:grid;gap:6px;justify-items:center}figcaption{font:12px Arial;color:#333;text-align:center;max-width:280px}"""

def tagfmt(n): return re.sub(r'^([A-Z]+)', lambda m: m.group(1) + '-', n)

def box(b): x, y, w, h = b; return f"left:{x}px;top:{y}px;width:{w}px;height:{h}px"

def flat(members, prefix=""):
    """UDT member list (nested Folders) -> {"Group/Member": value}."""
    out = {}
    for m in members:
        k = prefix + m["name"]
        if m["tagType"] == "Folder": out.update(flat(m["tags"], k + "/"))
        else: out[k] = m["value"]
    return out

# run / stop members per type (build_pid.RUN_MEMBERS); status words per type
RUN = {"T_Motor_Demo": ("Out_Run", "Sts_Running", "Sts_Stopped", ("STOPPED", "RUNNING", "STARTING", "STOPPING")),
       "T_VFD_Demo":   ("Out_Run", "Sts_Running", "Sts_Stopped", ("STOPPED", "RUNNING", "STARTING", "STOPPING")),
       "T_Heater_Demo": ("Out_Contactor", "Sts_On", "Sts_Off", ("OFF", "ON", "SWITCHING ON", "SWITCHING OFF"))}

def evaluate(udt, ov, tpl, p, name=""):
    """Evaluates the bindings build_pid.py puts on each template (custom.* values and status text)."""
    t = flat(UDTS[udt]); t.update(ov)
    man, oos, local, intlk = bool(t["Mode/Sts_Man"]), bool(t["Mode/Sts_OOS"]), t["Sts_Local"], t["Sts_Intlk"]
    perm_missing = bool(t.get("Sts_NotPerm", False)) if tpl != "ControlValve" else False
    if tpl == "AutoValve":
        cmd_v, opened, closed, fault = t["Out_Open"], t["Sts_Opened"], t["Sts_Closed"], t["Sts_Fault"]
        st = 3 if fault else (1 if opened else 0 if closed else 2)
        cmd = (1 if cmd_v else 0) if (t["Cfg_HasZSO"] or t["Cfg_HasZSC"]) else -1
        status = {0: "CLOSED", 1: "OPEN", 2: "OPENING" if cmd_v else "CLOSING", 3: "FAULT"}[st]
        sym = BY[p.get("symbol", "Valve_OnOff_Pneumatic")]
        canCmd = man and t["Sts_Avail"] and not local and not oos and (cmd_v or (not perm_missing and not intlk))
    elif tpl == "ControlValve":
        fb = t["Cfg_HasFbk"]; v = t["Val_Pos"] if fb else t["Val_Demand"]
        st = 3 if t["Sts_Fault"] else (1 if v > 1 else 0)
        cmd = (1 if t["Val_Demand"] > 1 else 0) if fb else -1
        status = "FAULT" if st == 3 else f"{v:.0f} %"
        sym = BY[p.get("symbol", "Valve_Control")]
        canCmd = False   # no actuation button on control valves
    else:
        cmd_k, on_k, off_k, words = RUN[udt]
        cmd_v = t[cmd_k]
        st = 3 if (t["Sts_Fault"] or t["Sts_Tripped"]) else (1 if t[on_k] else 0 if t[off_k] else 2)
        cmd = -1
        if st == 1 and udt == "T_VFD_Demo": on_word = f"{t['Val_Spd']:.1f} {t['Cfg_SpdEU']}"
        else: on_word = words[1]
        status = {0: words[0], 1: on_word, 2: words[2] if cmd_v else words[3], 3: "FAULT"}[st]
        sym = BY[p.get("symbol", "Rotating/Pump_Centrifugal").split("/")[-1]]
        canCmd = man and t["Sts_Avail"] and not local and not oos and (cmd_v or (not perm_missing and not intlk))
    t.update({"_TAG": t["Cfg_Tag"] or tagfmt(name), "_P": perm_missing, "_I": intlk, "_MAN": man, "_EN": canCmd})
    return t, st, cmd, status, sym

def render(name, udt, ov, tpl, p, use_button=True):
    L = LAYOUT[tpl]; t, st, cmd, status, sym = evaluate(udt, ov, tpl, p, name)
    W, H = L["size"]; sx, sy, sw, sh = L["sym"]
    s = svg(sym, st, cmd, p.get("alarm", 0), px=sw)
    o = [f"<div class='t' style='width:{W}px;height:{H}px'>"]
    if sym.kind != "motor" or sym.name not in ("Agitator", "Motor"):
        o.append(f"<div class='line' style='top:{sy + L['line'] * sh - 1}px'></div>")
    o.append(f"<div class='a psc-Text_TagName' style='{box(L['tag'])}'>{t['_TAG']}</div>")
    o.append(f"<div class='a' style='{box(L['sym'])}'>{s}</div>")
    if t["_P"]: o.append(f"<div class='a psc-Indicator_PermissiveBadge' style='{box(L['P'])}'>P</div>")
    if t["_I"]:
        ib = L["I_low"] if (tpl == "Motor" and sym.badge_i == "low") else L["I"]
        o.append(f"<div class='a psc-Indicator_InterlockBadge' style='{box(ib)}'>I</div>")
    if tpl == "Motor":
        cls = {0: "State_Stopped", 1: "State_Running", 2: "State_Transition", 3: "State_Fault"}[st]
        scls = f"psc-{cls}"
    else:
        scls = "psc-" + {0: "State_Stopped", 1: "State_Running", 2: "State_Transition", 3: "State_Fault"}[st]
    manual = t["_MAN"]
    showm = bool(manual and (tpl == "ControlValve" or not use_button))   # status M segment: !useButton && man (control valve: man)
    m = "<span class='a psc-Mode_ManualSplit' style='position:static'>M</span>" if showm else \
        ("<span class='a psc-Util_Collapsed' style='position:static'>M</span>" if tpl != "ControlValve" else "")   # mirrors Perspective: hidden M collapses to 0 width
    o.append(f"<div class='a mrow' style='{box(L['status'])}'>{m}<span class='a {scls}{' psc-Mode_ManualJoined' if showm else ''}' style='position:static'>{status}</span></div>")
    if tpl == "ControlValve" and "bar" in L:
        pos = max(0, min(100, t["Val_Pos"])); out = max(0, min(100, t["Val_Demand"]))
        bar = (f"<svg viewBox='0 -6 20 112' preserveAspectRatio='none' width='{L['bar'][2]}' height='{L['bar'][3]}'>"
               f"<rect x='8' y='2' width='11' height='96' fill='#FFFFFF' stroke='#595959' stroke-width='1.5'/>"
               f"<rect x='8' y='{98-0.96*pos}' width='11' height='{0.96*pos}' fill='#4D4D4D'/>"
               f"<path d='M0 {91-0.96*out} L7 {98-0.96*out} L0 {105-0.96*out} Z' fill='#1F4E99'/></svg>")
        o.append(f"<div class='a' style='{box(L['bar'])}'>{bar}</div>")
    if use_button and L["pb"] and manual:   # button only in Manual
        o.append(f"<button class='a psc-Button_Command' {'' if t['_EN'] else 'disabled'} style='{box(L['pb'])}'></button>")
    o.append("</div>")
    return "".join(o)
