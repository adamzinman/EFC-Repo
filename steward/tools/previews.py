"""Build the review contact sheet: steward/previews/<item>.html fragments + index.html.

Existing items are drawn from `steward.py slim` output only (no raw view reads).
New items (docks, VFD template) are design proposals described by DOCKS / NEW below.
CSS comes from the EFC_Styles style-classes, one shared block in index.html.
Usage: python3 -I steward/tools/previews.py <repo> <steward.py>
"""
import glob, html, json, os, re, subprocess, sys

R, STEWARD = sys.argv[1], sys.argv[2]
OUT = f"{R}/steward/previews"
tm = json.load(open(f"{R}/steward/type_map.json"))
cfg = json.load(open(f"{R}/steward.config.json"))
CARD_W = 240  # px, width of a template card; docks use DOCK_W
DOCK_W, DOCK_H = 230, 640  # right dock, 360 x 1000 at 1080p
slug = lambda p: p.replace("/", "_")
esc = html.escape


def dock_for(item):
    best = max((k for k in cfg["dock_map"] if item.startswith(k)), key=len, default=None)
    return cfg["dock_map"].get(best, "-")


# ---------- shared CSS from EFC_Styles ----------
def kebab(k):
    return re.sub(r"([A-Z])", lambda m: "-" + m.group(1).lower(), k)


def vh(v):
    return re.sub(r"(-?\d*\.?\d+)vh", r"calc(\1 * var(--vh))", str(v))


def css_block():
    out = []
    for p in cfg["projects"]:
        base = f"{R}/{p}/com.inductiveautomation.perspective/style-classes"
        for f in glob.glob(f"{base}/**/style.json", recursive=True):
            name = os.path.relpath(os.path.dirname(f), base)
            d = json.load(open(f))
            sel = f'[data-c~="{name}"]'
            st = d.get("base", {}).get("style", {})
            out.append(sel + "{" + ";".join(f"{kebab(k)}:{vh(v)}" for k, v in st.items()) + "}")
            for var in d.get("variants", []):
                ps = (var.get("pseudo") or "").strip(":")
                if ps in ("hover", "active", "disabled") and var.get("style"):
                    out.append(f"{sel}:{ps}{{" + ";".join(f"{kebab(k)}:{vh(v)}" for k, v in var["style"].items()) + "}")
    return "\n".join(sorted(out))


# ---------- slim -> HTML ----------
PLACEHOLDER = {"Tag": "XV-101", "Status": "CLOSED", "Value": "42.7", "PV": "42.7", "Units": "kPa", "SP": "40.0", "OP": "55 %"}


def run(*a):
    return subprocess.run([sys.executable, STEWARD, "--root", R, *a], capture_output=True, text=True).stdout


def show(item):
    txt = run("show", item)
    return json.loads(txt[txt.index("{"):])


def slim(item):
    txt = run("slim", item, "--keep", "props,style")
    return json.loads(txt[txt.index("{"):])


def svg_el(e):
    t = e.get("type")
    if t == "group":
        return "<g>" + "".join(svg_el(c) for c in e.get("elements", [])) + "</g>"
    fill = (e.get("fill") or {}).get("paint", "none")
    st = e.get("stroke") or {}
    attrs = {k: e[k] for k in ("d", "x", "y", "width", "height", "cx", "cy", "r", "rx", "ry", "x1", "y1", "x2", "y2", "points") if k in e}
    a = " ".join(f'{k}="{esc(str(v))}"' for k, v in attrs.items())
    a += f' fill="{fill}" stroke="{st.get("paint", "none")}" stroke-width="{st.get("width", 0)}" stroke-linejoin="round"'
    if t == "text":
        return f'<text {a} font-size="{e.get("font", {}).get("size", 10)}">{esc(str(e.get("text", "")))}</text>'
    return f"<{t} {a}/>" if t in ("path", "rect", "circle", "ellipse", "line", "polygon", "polyline") else ""


def comp(c, hit=False):
    t, name, p = c.get("type", ""), c.get("name", ""), c.get("props", {})
    cls = (p.get("style") or {}).get("classes", "") if isinstance(p.get("style"), dict) else ""
    dc = f' data-c="{esc(cls)}"' if cls else ""
    kids = "".join(comp(k, hit) for k in c.get("children", []))
    if t == "shapes.svg":
        body = "".join(svg_el(e) for e in p.get("elements", []))
        svg = f'<svg viewBox="{p.get("viewBox", "0 0 100 100")}" preserveAspectRatio="xMidYMid meet">{body}</svg>'
        if name != "Symbol":
            return f'<div class="sym2">{svg}</div>'
        return f'<div class="sym{" hit" if hit else ""}" title="click: open dynamic window">{svg}</div>'
    if t == "display.label":
        if "Util/Collapsed" in cls:
            return ""
        txt = p.get("text") or PLACEHOLDER.get(name, name)
        pos = f' class="badge b{name}"' if name in ("P", "I") else ""
        return f"<span{pos}{dc}>{esc(str(txt))}</span>"
    if t == "input.button":
        return f'<button{dc}>{esc(p.get("text") or "")}</button>'
    if t.startswith("container") or t == "ia.container.flex":
        d = p.get("direction", "column")
        return f'<div class="box" style="flex-direction:{"row" if "row" in str(d) else "column"}"{dc}>{kids}</div>'
    if "view" in t and "embed" in t or t == "ia.display.view":
        return f'<div class="ph">embedded: {esc(str(p.get("path", name)))}</div>'
    if "repeater" in t:
        return '<div class="box" style="flex-direction:row">' + '<div class="ph">item</div>' * 3 + "</div>"
    return f'<div class="ph">{esc(t.split(".")[-1])}: {esc(name)}</div>'


def frame(item, inner, w, h, ttype, dock, extra=""):
    gap = ttype.startswith("gap:")
    tt = f'<b class="{"gap" if gap else "ok"}">{esc(ttype.replace("gap:", "GAP "))}</b>'
    return (f'<figure class="card" id="{slug(item)}"><div class="view" style="width:{w}px;min-height:{h}px;--vh:{10.8 * w / max(int(w0[item]), 1):.3f}px">{inner}</div>'
            f'<figcaption><code>{esc(item)}</code><br>{tt} &middot; dock <code>{esc(dock)}</code>{extra}</figcaption></figure>')


w0 = {}


def template_card(item, ttype, new_note=""):
    src = item if not new_note else "Templates/Rotating/Motor"
    info, sl = show(src), slim(src)
    size = info.get("default_size") or {"width": 120, "height": 100}
    w0[item] = size["width"]
    w, h = CARD_W, round(CARD_W * size["height"] / size["width"])
    inner = comp(sl["root"], hit=True)
    if 'class="sym hit"' not in inner:  # no symbol: whole view is the click target
        inner = f'<div class="hit" style="display:contents">{inner}</div>'
        new_note = new_note or ""
    if "/Valves/" not in item:
        inner = inner.replace(">CLOSED<", ">STOPPED<")
    if new_note:
        inner += '<div class="box" style="flex-direction:row"><div data-c="Bar/Track" style="flex:1;height:6px"><div data-c="Bar/Fill" style="width:62%;height:100%"></div></div><span data-c="Text/Value">48.2 Hz</span></div>'
        h += 24
    dbl = ttype in ("T_DValve", "T_Motor")
    extra = "<br>click symbol: open dock" + (" &middot; dbl-tap (touch, Manual, canCmd): toggle" if dbl else "") + new_note
    return frame(item, inner, w, h, ttype, dock_for(item), extra)


# ---------- new dock proposals ----------
SECTIONS = {
    "mode": '<div class="row"><span data-c="Text/Label">MODE</span><button data-c="Mode/Auto">AUTO</button><button data-c="Mode/Manual">MAN</button><button data-c="Button/Subtle">MAINT</button><button data-c="Button/Subtle">OOS</button></div>',
    "perm": '<div data-c="Container/GroupBox"><span data-c="Text/Subheader">PERMISSIVES / INTERLOCKS</span><div class="row"><span data-c="Indicator/LED/On"></span><span data-c="Text/Body">Perm 1 - Seal water OK</span></div><div class="row"><span data-c="Indicator/LED/Fault"></span><span data-c="Text/Body">Intlk 2 - Tank LL</span></div></div>',
    "alarms": '<div data-c="Container/GroupBox"><span data-c="Text/Subheader">ALARMS</span><div data-c="Table/Row">Fail to open &middot; 2 &middot; unacked</div><div data-c="Table/RowAlt">Position conflict &middot; 3</div></div>',
    "trend": '<div data-c="Container/TrendPanel" class="ph" style="height:70px">trend (last 1 h)</div>',
    "run": '<div class="kv"><span data-c="Text/Label">STARTS / HR</span><span data-c="Text/Value">2</span><span data-c="Text/Label">RUN HOURS</span><span data-c="Text/Value">1 284</span></div>',
}


def cmds(*b):
    return '<div class="row">' + "".join(f'<button data-c="{c}">{t}</button>' for t, c in b) + "</div>"


def analog(*rows):
    out = '<div data-c="Container/GroupBox">'
    for lbl, val, pct, cls in rows:
        out += (f'<div class="kv"><span data-c="Text/Label">{lbl}</span><span data-c="{cls}">{val}</span></div>'
                f'<div data-c="Bar/Track" style="height:6px"><div data-c="Bar/Fill" style="width:{pct}%;height:100%"></div></div>')
    return out + "</div>"


OPENCLOSE = cmds(("OPEN", "Button/Primary"), ("CLOSE", "Button/Default"), ("RESET", "Button/Subtle"))
STARTSTOP = cmds(("START", "Button/Start"), ("STOP", "Button/Stop"), ("RESET", "Button/Subtle"))
DOCKS = {
    "dw_ValveDiscrete": ("T_DValve", ["mode", OPENCLOSE, "perm", "alarms", "run"]),
    "dw_ValveAnalog": ("T_CValve", ["mode", analog(("POSITION SP", "55.0 %", 55, "Input/Setpoint"), ("POSITION FBK", "54.6 %", 54, "Value/Normal")), "perm", "alarms", "trend"]),
    "dw_Rotating": ("T_Motor", ["mode", STARTSTOP, analog(("CURRENT", "38.2 A", 64, "Value/Normal")), "perm", "alarms", "run"]),
    "dw_VFD": ("T_VFD", ["mode", STARTSTOP, analog(("SPEED SP", "48.0 Hz", 80, "Input/Setpoint"), ("SPEED", "47.9 Hz", 80, "Value/Normal"), ("CURRENT", "61.0 A", 71, "Value/Normal")), "perm", "alarms", "trend", "run"]),
    "dw_HeatTransfer": ("T_HeatEx", [analog(("T IN", "82.4 &deg;C", 70, "Value/Normal"), ("T OUT", "41.0 &deg;C", 35, "Value/Normal"), ("DUTY", "212 kW", 58, "Value/Normal")), "alarms", "trend"]),
    "dw_ProcessValue": ("T_AI / T_KPI", [analog(("PV", "42.7 kPa", 43, "Value/Normal")), '<div class="kv"><span data-c="Text/Label">HH</span><span data-c="Input/Setpoint">90</span><span data-c="Text/Label">H</span><span data-c="Input/Setpoint">75</span><span data-c="Text/Label">L</span><span data-c="Input/Setpoint">15</span><span data-c="Text/Label">LL</span><span data-c="Input/Setpoint">5</span></div>', "alarms", "trend"]),
    "dw_Loop": ("T_PID", ["mode", analog(("PV", "42.7 kPa", 43, "Value/Normal"), ("SP", "40.0 kPa", 40, "Input/Setpoint"), ("OP", "55 %", 55, "Value/Output")), cmds(("TUNING", "Button/Default"), ("CASCADE", "Button/Subtle")), "alarms", "trend"]),
    "dw_IOCard": ("GAP T_IOCard", ['<div class="kv"><span data-c="Text/Label">CARD</span><span data-c="Text/Value">BMXDDI1602 &middot; rack 0 slot 3</span></div>', '<div data-c="Container/GroupBox"><span data-c="Text/Subheader">CHANNELS</span>' + "".join(f'<div data-c="Table/{"Row" if i % 2 else "RowAlt"}">Ch {i:02d} &middot; {"ON" if i % 3 else "OFF"}</div>' for i in range(6)) + "</div>", '<div data-c="Container/GroupBox"><span data-c="Text/Subheader">DIAGNOSTICS</span><div class="row"><span data-c="Indicator/LED/On"></span><span data-c="Text/Body">Module OK</span></div></div>']),
}


def dock_card(did, path, ttype, parts):
    body = "".join(SECTIONS.get(p, p) for p in parts)
    head = (f'<div data-c="Container/PopupHeader" class="row"><span data-c="Text/TagName">XV-101</span>'
            f'<span data-c="Text/Caption" style="flex:1">Description</span><button data-c="Button/Icon" title="close: back to screen default dock">&#x2715;</button></div>'
            f'<div class="row"><span data-c="State/Stopped">CLOSED</span><span data-c="Text/Caption">NE107: OK</span></div>')
    w0[path] = 360
    inner = f'<div data-c="Container/Faceplate" class="dock">{head}{body}</div>'
    return frame(path, inner, DOCK_W, DOCK_H, ttype.replace("GAP ", "gap:"), did, "<br><b>NEW - design proposal</b> &middot; close &#x2715; reopens the screen's defaultDock")


PAGE_CSS = """body{margin:0;padding:16px;background:#E6E6E6;font:12px 'Noto Sans','Segoe UI',Arial,sans-serif;color:#1F1F1F}
h1{font-size:16px;margin:0 0 4px}h2{font-size:13px;margin:18px 0 6px;border-bottom:1px solid #BDBDBD}
.grid{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-start}.card{margin:0;background:#F2F2F2;border:1px solid #C4C4C4;padding:6px}
.card figcaption{font-size:10px;line-height:1.4;margin-top:4px;max-width:240px}.gap{color:#B71C1C}.ok{color:#1B5E20}
.view{position:relative;overflow:hidden;background:#DADADA;display:flex;flex-direction:column}
.box{display:flex;gap:2px;align-items:center;justify-content:center}.row{display:flex;gap:4px;align-items:center;margin:3px 0;flex-wrap:wrap}
.kv{display:grid;grid-template-columns:auto 1fr;gap:2px 6px;margin:3px 0}.sym{height:150px;display:flex;flex:none}.sym svg,.sym2 svg{width:100%;height:100%}.sym2{height:28px;display:flex}
.view:has(>.hit){outline:1.5px dashed #00A3E0}.hit{outline:1.5px dashed #00A3E0;outline-offset:-1px;cursor:pointer}.badge{position:absolute;top:2px}.bP{left:2px}.bI{right:2px}.view>.box:first-child{padding:0 22px}
.ph{border:1px dashed #9E9E9E;color:#616161;font-size:10px;padding:2px;margin:1px;text-align:center;flex:1}
.dock{height:100%;box-sizing:border-box;overflow:hidden;padding:6px}.legend{font-size:11px;color:#424242}
@media(max-width:600px){body{padding:16px}.card{width:100%}}"""

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    groups = {}
    for item, t in tm["items"].items():
        exists = any(os.path.exists(f"{R}/{p}/com.inductiveautomation.perspective/views/{item}/view.json") for p in cfg["projects"])
        frag = template_card(item, t) if exists else template_card(item, t, "<br><b>NEW - design proposal</b> (Motor symbol + speed)")
        open(f"{OUT}/{slug(item)}.html", "w").write(frag)
        groups.setdefault(item.rsplit("/", 1)[0], []).append(frag)
    for did, path in tm["docks"].items():
        if did in DOCKS:
            t, parts = DOCKS[did]
            frag = dock_card(did, path, t, parts)
        else:  # existing dock view: draw it like a template
            frag = template_card(path, "gap:T_Station").replace("click symbol: open dock", "existing dock view")
        open(f"{OUT}/{slug(path)}.html", "w").write(frag)
        groups.setdefault("Docks (dynamic windows)", []).append(frag)
    body = "".join(f'<h2>{esc(g)}</h2><div class="grid">{"".join(fr)}</div>' for g, fr in groups.items())
    page = (f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>EFC Library Previews</title><style>{PAGE_CSS}\n/* EFC_Styles */\n{css_block()}</style></head><body>'
            f'<h1>EFC Library - review contact sheet</h1><p class="legend">Dashed blue = click target (opens dock). Red type = gap (no EFCLib v1 type). '
            f'Templates are drawn from slim output (layout approximate); docks and VFD are new design proposals.</p>{body}</body></html>')
    open(f"{OUT}/index.html", "w").write(page)
    print(f"fragments {sum(len(v) for v in groups.values())} -> {OUT}/index.html ({os.path.getsize(OUT + '/index.html') // 1024} KB)")
