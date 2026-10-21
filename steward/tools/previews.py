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
DOCK_DW, DOCK_DH = 400, 940  # right dock at 1080p: 400 wide (800 @ 4K, screen-layout-standard); height pending header size
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
PLACEHOLDER = [("tag", "XV-101"), ("header", "XV-101"), ("name", "XV-101"), ("desc", "Description"), ("unit", "kPa"),
               ("status", "CLOSED"), ("state", "CLOSED"), ("chip", "OK"), ("mode", "AUTO"), ("sp", "40.0"), ("out", "55 %"),
               ("op", "55 %"), ("pv", "42.7"), ("val", "42.7"), ("dev", "+2.7"), ("min", "0"), ("max", "100"), ("msg", "Ready"),
               ("net", "12.40"), ("tare", "0.85"), ("total", "13.25"), ("pct", "62 %")]


def placeholder(name):
    n = name.lower()
    for k, v in PLACEHOLDER:
        if n == k or n.startswith(k) or n.endswith(k):
            return v
    return ""


def run(*a):
    return subprocess.run([sys.executable, STEWARD, "--root", R, *a], capture_output=True, text=True).stdout


def show(item):
    txt = run("show", item)
    return json.loads(txt[txt.index("{"):])


def slim(item):
    txt = run("slim", item, "--keep", "props,style")
    return json.loads(txt[txt.index("{"):])


def positions(item, file):
    """Only the layout keys (position, container mode/direction) from the raw view, keyed by name path."""
    out = {}
    def walk(c, path):
        out[path] = {"position": c.get("position", {}), "mode": c.get("props", {}).get("mode")}
        for k in c.get("children", []) or []:
            walk(k, path + (k.get("meta", {}).get("name", ""),))
    walk(json.load(open(f"{R}/{file}"))["root"], ("root",))
    return out


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


def dim(v, mode):
    if isinstance(v, str):
        return v if v.strip().endswith(("%", "px")) else f"{v}px"
    return f"{v * 100:.3f}%" if mode == "percent" and abs(v) <= 1.0001 else f"{v}px"


def place(pos, parent_kind, mode):
    if parent_kind == "coord":
        return "position:absolute;" + ";".join(f"{k}:{dim(pos[j], mode)}" for k, j in (("left", "x"), ("top", "y"), ("width", "width"), ("height", "height")) if j in pos)
    if parent_kind == "flex":
        return f"flex:{pos.get('grow', 0)} {pos.get('shrink', 1)} {dim(pos['basis'], None) if 'basis' in pos and pos['basis'] != 'auto' else 'auto'};min-width:0;min-height:0"
    return "width:100%;height:100%"


def comp(c, P, path=("root",), parent="root", hit=False):
    t, name, p = c.get("type", ""), c.get("name", ""), c.get("props", {})
    cls = (p.get("style") or {}).get("classes", "") if isinstance(p.get("style"), dict) else ""
    dc = f' data-c="{esc(cls)}"' if cls else ""
    L = P.get(path, {})
    parent_mode = P.get(path[:-1], {}).get("mode") if len(path) > 1 else None
    st = place(L.get("position", {}), parent, parent_mode)
    if "Util/Collapsed" in cls:
        return ""
    if t == "shapes.svg":
        body = "".join(svg_el(e) for e in p.get("elements", []))
        svg = f'<svg viewBox="{p.get("viewBox", "0 0 100 100")}" preserveAspectRatio="{p.get('preserveAspectRatio', 'xMidYMid') if p.get('preserveAspectRatio') == 'none' else p.get('preserveAspectRatio', 'xMidYMid') + ' meet'}" width="100%" height="100%">{body}</svg>'
        h = ' class="hit" title="click: open dynamic window"' if hit and name == "Symbol" else ""
        return f'<div{h} style="{st};display:flex">{svg}</div>'
    if t == "display.label":
        txt = p.get("text") if p.get("text") not in (None, "") else placeholder(name)
        return f'<span style="{st};display:flex;align-items:center;overflow:hidden"{dc}>{esc(str(txt))}</span>'
    if t == "input.button":
        return f'<button style="{st}"{dc}>{esc(p.get("text") or placeholder(name))}</button>'
    if t.startswith("input."):
        return f'<span style="{st};display:flex;align-items:center"{dc} class="inp">0.0</span>'
    if t.startswith("container"):
        kind = "coord" if "coord" in t else "flex" if "flex" in t else "other"
        kids = "".join(comp(k, P, path + (k.get("name", ""),), kind, hit) for k in c.get("children", []))
        lay = "position:relative" if kind == "coord" else f"display:flex;flex-direction:{'row' if 'row' in str(p.get('direction', 'row')) else 'column'};justify-content:{p.get('justify', 'flex-start')};align-items:{p.get('alignItems', 'stretch')}" if kind == "flex" else "display:flex;flex-direction:column"
        return f'<div style="{st};{lay}"{dc}>{kids}</div>'
    if "image" in t:
        return f'<div style="{st}"></div>'
    if "repeater" in t:
        return f'<div style="{st};display:flex;gap:2px">' + '<div class="ph">item</div>' * 3 + "</div>"
    if "view" in t:
        return f'<div class="ph" style="{st}">{esc(str(p.get("path", name)).split("/")[-1])}</div>'
    return f'<div class="ph" style="{st}">{esc(t.split(".")[-1])}</div>'


def frame(item, inner, dw, dh, ttype, dock, extra="", cw=None, maxh=320):
    sc = min((cw or CARD_W) / dw, maxh / dh)
    cw = round(dw * sc)
    gap = ttype.startswith("gap:")
    tt = f'<b class="{"gap" if gap else "ok"}">{esc(ttype.replace("gap:", "GAP "))}</b>'
    return (f'<figure class="card" id="{slug(item)}"><div class="view" style="width:{cw}px;height:{round(dh * sc)}px">'
            f'<div class="stage" style="width:{dw}px;height:{dh}px;transform:scale({sc:.4f})">{inner}</div></div>'
            f'<figcaption><code>{esc(item)}</code><br>{tt} &middot; dock <code>{esc(dock)}</code>{extra}</figcaption></figure>')


def template_card(item, ttype, new_note=""):
    src = item if not new_note else "Templates/Rotating/Motor"
    info, sl = show(src), slim(src)
    size = info.get("default_size") or {"width": 120, "height": 100}
    dw, dh = size["width"], size["height"]
    P = positions(src, info["file"])
    rel = (f"../../docs/previews/templates/{src.split('Templates/', 1)[1]}.png" if src.startswith("Templates/")
           else f"renders/AnalogIndicator/{src.rsplit('/', 1)[1]}.png")  # renders/ made by render_views.py in a temp copy
    if os.path.exists(os.path.normpath(f"{OUT}/{rel}")):
        # real render (generator/render_views.py, demo tags bound) + click target at the Symbol's real position
        sym = P.get(("root", "Symbol"))
        tgt = place(sym["position"], "coord", P[("root",)]["mode"]) if sym else "position:absolute;inset:0"
        inner = (f'<img src="{rel}" style="position:absolute;inset:0;width:100%;height:100%">'
                 f'<div class="hit" style="{tgt};pointer-events:none" title="click: open dynamic window"></div>')
        new_note += "" if new_note else ("<br><i>render with planned fix 7 (alignItems: stretch); as committed the zone bars collapse</i>"
                                         if rel.startswith("renders/") else "<br><i>render of the real view</i>")
    else:
        inner = comp(sl["root"], P, hit=True)
        new_note += "" if new_note else "<br><i>mockup from slim (bound geometry not shown)</i>"
    if 'class="hit"' not in inner:  # no symbol: whole view is the click target
        inner = f'<div class="hit" style="position:absolute;inset:0;pointer-events:none"></div>{inner}'
    if "/Valves/" not in item:
        inner = inner.replace(">CLOSED<", ">STOPPED<")
    if "NEW" in new_note:
        dh += 14
        inner = (f'<div style="position:relative;width:100%;height:{dh - 14}px">{inner}</div>'
                 '<div style="display:flex;flex:none;gap:4px;align-items:center;height:14px"><div data-c="Bar/Track" style="flex:1;height:5px"><div data-c="Bar/Fill" style="width:62%;height:100%"></div></div><span data-c="Text/Caption">48.2 Hz</span></div>')
    dbl = ttype in ("T_DValve", "T_Motor")
    extra = "<br>click symbol: open dock" + (" &middot; dbl-tap (touch, Manual, canCmd): toggle" if dbl else "") + new_note
    return frame(item, inner, dw, dh, ttype, dock_for(item), extra)


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
    inner = f'<div data-c="Container/Faceplate" class="dock">{head}{body}</div>'
    return frame(path, inner, DOCK_DW, DOCK_DH, ttype.replace("GAP ", "gap:"), did, "<br><b>NEW - design proposal</b> &middot; close &#x2715; reopens the screen's defaultDock", maxh=600)


PAGE_CSS = """body{margin:0;padding:16px;background:#E6E6E6;font:12px 'Noto Sans','Segoe UI',Arial,sans-serif;color:#1F1F1F}
h1{font-size:16px;margin:0 0 4px}h2{font-size:13px;margin:18px 0 6px;border-bottom:1px solid #BDBDBD}
.grid{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-start}.card{margin:0;background:#F2F2F2;border:1px solid #C4C4C4;padding:6px}
.card figcaption{font-size:10px;line-height:1.4;margin-top:4px;width:240px}.gap{color:#B71C1C}.ok{color:#1B5E20}
.view{position:relative;overflow:hidden;background:#DADADA}.stage{position:relative;transform-origin:0 0;--vh:10.8px;display:flex;flex-direction:column}.stage>div:first-of-type{flex:1}
.box{display:flex;gap:2px;align-items:center;justify-content:center}.row{display:flex;gap:4px;align-items:center;margin:3px 0;flex-wrap:wrap}
.kv{display:grid;grid-template-columns:auto 1fr;gap:2px 6px;margin:3px 0}.sym{height:150px;display:flex;flex:none}.sym svg,.sym2 svg{width:100%;height:100%}.sym2{height:28px;display:flex}
.hit{outline:1.5px dashed #00A3E0;outline-offset:-1px;cursor:pointer}.badge{position:absolute;top:2px}.bP{left:2px}.bI{right:2px}.view>.box:first-child{padding:0 22px}
.inp{background:#fff;border:1px solid #BDBDBD;padding:0 3px}.ph{border:1px dashed #9E9E9E;color:#616161;font-size:10px;box-sizing:border-box;padding:2px;margin:1px;text-align:center;flex:1}
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
            frag = template_card(path, "gap:T_Station").replace("click symbol: open dock", "existing dock view; planned: move to <code>Docks/Station</code>, resize 300 to 400 px wide")
        open(f"{OUT}/{slug(path)}.html", "w").write(frag)
        groups.setdefault("Docks (dynamic windows)", []).append(frag)
    body = "".join(f'<h2>{esc(g)}</h2><div class="grid">{"".join(fr)}</div>' for g, fr in groups.items())
    page = (f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>EFC Library Previews</title><style>{PAGE_CSS}\n/* EFC_Styles */\n{css_block()}</style></head><body>'
            f'<h1>EFC Library - review contact sheet</h1><p class="legend">Dashed blue = click target (opens dock). Red type = gap (no EFCLib v1 type). '
            f'Templates are drawn from slim output (layout approximate); docks and VFD are new design proposals.</p>{body}</body></html>')
    import base64  # inline the renders so index.html is self-contained
    page = re.sub(r'src="([^"]+\.png)"', lambda m: 'src="data:image/png;base64,' + base64.b64encode(open(os.path.normpath(f"{OUT}/{m.group(1)}"), "rb").read()).decode() + '"', page)
    open(f"{OUT}/index.html", "w").write(page)
    print(f"fragments {sum(len(v) for v in groups.values())} -> {OUT}/index.html ({os.path.getsize(OUT + '/index.html') // 1024} KB)")
