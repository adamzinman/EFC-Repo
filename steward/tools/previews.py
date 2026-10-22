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
DOCK_DW, DOCK_DH = 400, 860  # dynamic window per decision 25: 400 x 860 at 1080p = 37.04 vh x 79.63 vh (800 x 1720 at 4K)
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
            f'<figcaption><code>{esc(item)}</code><br>{tt} &middot; dynamic window <code>{esc(dock)}</code>{extra}</figcaption></figure>')


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
    extra = "<br>click symbol: open dynamic window" + (" &middot; dbl-tap (touch, Manual, canCmd): toggle" if dbl else "") + new_note
    return frame(item, inner, dw, dh, ttype, dock_for(item), extra)


# ---------- new dynamic-window proposals ----------
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
def role(lbl):
    return f'<span class="role" title="visible to {lbl} and higher">{lbl}+</span>'


EXPAND = '<button data-c="Button/Icon" class="xp" title="expand graph within the window">&#x2922;</button>'


def grp(title, body, note=""):
    if title.startswith("HISTORY"):
        note = note + EXPAND
    return f'<div data-c="Container/GroupBox" class="grp"><div class="gh"><span data-c="Text/Subheader">{title}</span>{note}</div>{body}</div>'


def cond(state, text, first=False, byp=True):
    led = {"ok": "Indicator/LED/On", "fail": "Indicator/LED/Fault", "byp": "Indicator/LED/Unknown", "latch": "Indicator/LED/Fault"}[state]
    tag = {"ok": "", "fail": '<span data-c="Text/Color/Fault">NOT OK</span>', "byp": '<span data-c="Indicator/Badge" title="Sts_BypLeft[n]">BYPASSED 3h12 left</span>', "latch": '<span data-c="Text/Color/Fault">LATCHED</span>'}[state]
    fo = '<span data-c="Indicator/Badge" title="first out">1st</span>' if first else ""
    b = f'<button data-c="Button/Small">{"UNBYP" if state == "byp" else "BYPASS"}</button>{role("Sup")}' if byp else ""
    audit = ('<div data-c="Text/Caption" class="audit">bypassed by jsmith (Supervisor) 07:30 &middot; "Level transmitter LT-100 replaced, verifying"</div>'
             if state == "byp" else "")
    return f'<div class="cond"><span data-c="{led}" class="led"></span><span data-c="Text/Body" style="flex:1">{text}</span>{fo}{tag}{b}</div>{audit}'


def history_strip():
    segs = [("closed", 30), ("open", 18), ("closed", 22), ("open", 25), ("closed", 5)]
    col = {"open": "#4D4D4D", "closed": "#C4C4C4", "fault": "#D50000"}
    bar = "".join(f'<div style="flex:{w};background:{col[k]}" title="{k}"></div>' for k, w in segs)
    ev = "".join(f'<div data-c="Table/{"Row" if i % 2 else "RowAlt"}" class="ev"><span>{t}</span><span>{e}</span></div>'
                 for i, (t, e) in enumerate([("10:42:07", "CLOSED"), ("10:41:59", "Cmd Close (op: jsmith)"), ("09:15:30", "OPEN"), ("09:15:22", "Cmd Open (auto)")]))
    return (f'<div class="strip">{bar}</div><div class="axis"><span>-30 min</span><span>-15 min</span><span>now</span></div>'
            f'<div class="legend2"><i style="background:#4D4D4D"></i>open <i style="background:#C4C4C4"></i>closed <i style="background:#D50000"></i>fault</div>{ev}')


def valve_discrete():
    head = ('<div data-c="Container/PopupHeader" class="hdr"><div style="flex:1;min-width:0"><div data-c="Text/TagName Text/Color/Inverse">XV-101</div>'
            '<div data-c="Text/Caption Text/Color/Inverse">Feed tank inlet valve</div></div><button data-c="Button/Icon" class="x" title="close returns the right dock to the screen&#39;s default view">&#x2715;</button></div>')
    state = ('<div class="row st"><span data-c="State/Stopped" class="big">CLOSED</span><span data-c="Indicator/Badge">NE107 OK</span>'
             '<span data-c="Mode/Simulated" class="dim">SIM</span><span data-c="Mode/Local" class="dim">LOCAL</span></div>'
             '<div class="row"><span data-c="Indicator/LED/Off" class="led"></span><span data-c="Text/Label">ZSO open</span>'
             '<span data-c="Indicator/LED/On" class="led"></span><span data-c="Text/Label">ZSC closed</span>'
             '<span data-c="Text/Label" style="margin-left:auto">travel 5 s</span></div>')
    mode = ('<div class="row"><span data-c="Text/Label" class="lbl">MODE</span><button data-c="Button/Default">AUTO</button><button data-c="Button/Default Button/Toggle/On">MAN</button>'
            f'<button data-c="Button/Default">MAINT</button>{role("Maint")}<button data-c="Button/Default">OOS</button>{role("Maint")}</div>')
    cmd = ('<div class="row"><span data-c="Text/Label" class="lbl">CMD</span><button data-c="Button/Default">OPEN</button><button data-c="Button/Default Button/Toggle/On">CLOSE</button>'
           '<button data-c="Button/Default">RESET</button></div>'
           '<div data-c="Text/Caption" class="hint">Enabled in MAN, available, not interlocked, not LOCAL</div>')
    perm = grp("PERMISSIVES", cond("ok", "Seal water pressure OK") + cond("fail", "Downstream valve XV-102 closed", byp=True) + cond("ok", "Tank T-100 not high-high"),
               '<span data-c="Indicator/PermissiveBadge" class="mini">P</span>')
    intl = grp("INTERLOCKS", cond("latch", "Tank T-100 low-low", first=True) + cond("byp", "Pump P-101 running") + cond("ok", "ESD-1 healthy", byp=False)
               + f'<div class="row"><button data-c="Button/Small">RESET LATCHED</button><span data-c="Text/Caption">reset required</span></div>',
               '<span data-c="Indicator/InterlockBadge" class="mini">I</span>')
    alarms = grp("ALARMS", "".join(f'<div class="cond"><span data-c="{c}" class="led"></span><span data-c="Text/Body" style="flex:1">{t}</span><span data-c="Text/Caption">{s}</span></div>'
                                   for c, t, s in [("Alarm/High/Fill", "Fail to close", "active, unacked"), ("Alarm/Medium/Fill", "Interlock trip", "active"),
                                                   ("Indicator/LED/Off", "Fail to open", ""), ("Indicator/LED/Off", "Position conflict", ""), ("Indicator/LED/Off", "Uncommanded move", "")])
                 + '<div class="row"><button data-c="Button/Small">ACK</button></div>')
    hist = grp("HISTORY (30 min)", history_strip())
    maint = details("MAINTENANCE", '<div class="kv"><span data-c="Text/Label">CYCLES</span><span data-c="Text/Value">12 408</span>'
                '<span data-c="Text/Label">HRS SINCE MAINT</span><span data-c="Text/Value">1 102</span>'
                f'<span data-c="Text/Label">MAINT DUE</span><span data-c="Text/Value">no</span></div><div class="row"><button data-c="Button/Small">RESET MAINT</button>{role("Maint")}<button data-c="Button/Small">SIMULATE</button>{role("Maint")}</div>')
    cfg = '<details data-c="Container/GroupBox" class="grp"><summary data-c="Text/Subheader">CONFIGURATION</summary>fail-open: no &middot; interlock-to-open: no &middot; dual-coil: no</details>'
    return head + '<div class="body">' + state + mode + cmd + perm + intl + alarms + hist + maint + cfg + "</div>"



def hdr(tag, desc):
    return ('<div data-c="Container/PopupHeader" class="hdr"><div style="flex:1;min-width:0">'
            f'<div data-c="Text/TagName Text/Color/Inverse">{tag}</div><div data-c="Text/Caption Text/Color/Inverse">{desc}</div></div>'
            '<button data-c="Button/Icon" class="x" title="close returns the right dock to the screen&#39;s default view">&#x2715;</button></div>')


def mode_row():
    return ('<div class="row"><span data-c="Text/Label" class="lbl">MODE</span><button data-c="Button/Default">AUTO</button><button data-c="Button/Default Button/Toggle/On">MAN</button>'
            f'<button data-c="Button/Default">MAINT</button>{role("Maint")}<button data-c="Button/Default">OOS</button>{role("Maint")}</div>')


def leds(*items):
    return '<div class="row">' + "".join(f'<span data-c="Indicator/LED/{st}" class="led"></span><span data-c="Text/Label" style="margin-right:6px">{t}</span>' for st, t in items) + "</div>"


def alarm_grp(rows):
    act = [r for r in rows if r[2]]
    ina = [r for r in rows if not r[2]]
    line = lambda c, t, st: f'<div class="cond"><span data-c="{c}" class="led"></span><span data-c="Text/Body" style="flex:1">{t}</span><span data-c="Text/Caption">{st}</span></div>'
    body = ("".join(line(*r) for r in act) or '<div data-c="Text/Caption">No active alarms</div>')
    body += f'<details><summary data-c="Text/Caption">+ {len(ina)} inactive</summary>' + "".join(line(*r) for r in ina) + "</details>"
    return grp("ALARMS", body + '<div class="row"><button data-c="Button/Small">ACK</button></div>')
    body = "".join(f'<div class="cond"><span data-c="{c}" class="led"></span><span data-c="Text/Body" style="flex:1">{t}</span><span data-c="Text/Caption">{st}</span></div>' for c, t, st in rows)
    return grp("ALARMS", body + '<div class="row"><button data-c="Button/Small">ACK</button></div>')


def bar(lbl, val, pct, cls="Value/Normal", marker=None, entry=False):
    m = f'<div style="position:absolute;left:{marker}%;top:-3px;bottom:-3px;width:2px;background:#1F4E99" title="setpoint"></div>' if marker is not None else ""
    v = f'<span data-c="Input/Setpoint" class="num">{val}</span>' if entry else f'<span data-c="{cls}" class="num">{val}</span>'
    return (f'<div class="barrow"><span data-c="Text/Label" class="bl">{lbl}</span><div data-c="Bar/Track" class="trk">'
            f'<div data-c="Bar/Fill" style="width:{pct}%;height:100%"></div>{m}</div>{v}</div>')


def trend(series, legend, strip=None):
    W, H = 360, 70
    paths = ""
    for pts, color, dash in series:
        n = len(pts) - 1
        d = " ".join(f"{'M' if i == 0 else 'L'}{i * W / n:.1f},{H - p * H / 100:.1f}" for i, p in enumerate(pts))
        paths += f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.5"{" stroke-dasharray=\"4 3\"" if dash else ""}/>'
    grid = "".join(f'<line x1="0" x2="{W}" y1="{y}" y2="{y}" stroke="#D0D0D0" stroke-width="1"/>' for y in (H / 4, H / 2, 3 * H / 4))
    st = ""
    if strip:
        col = {"run": "#4D4D4D", "stop": "#C4C4C4", "fault": "#D50000"}
        st = '<div class="strip" style="height:8px">' + "".join(f'<div style="flex:{w};background:{col[k]}"></div>' for k, w in strip) + "</div>"
    lg = '<div class="legend2">' + "".join(f'<i style="background:{c}"></i>{t} ' for t, c in legend) + "</div>"
    return (f'<svg viewBox="0 0 {W} {H}" width="100%" height="{H}" style="border:1px solid #9E9E9E;background:#FAFAFA;display:block">{grid}{paths}</svg>'
            f'{st}<div class="axis"><span>-30 min</span><span>-15 min</span><span>now</span></div>{lg}')


def kv(*pairs):
    return '<div class="kv">' + "".join(f'<span data-c="Text/Label">{k}</span><span data-c="Text/Value">{v}</span>' for k, v in pairs) + "</div>"


def details(title, body):
    return f'<details data-c="Container/GroupBox" class="grp"><summary data-c="Text/Subheader">{title}</summary>{body}</details>'


def wave(n, base, amp, seed):
    import math
    return [max(0, min(100, base + amp * math.sin(i / 3.0 + seed) + amp * 0.4 * math.sin(i * 1.7 + seed))) for i in range(n)]


def valve_analog():
    dem = wave(40, 55, 10, 0.3); pos = [d - 1.2 for d in dem]
    return hdr("FV-101", "Reactor feed control valve") + '<div class="body">' + (
        '<div class="row st"><span data-c="State/Running" class="big">54.6 %</span><span data-c="Indicator/Badge">NE107 OK</span>'
        '<span data-c="Indicator/Badge" class="dim">RATE LIM</span><span data-c="Mode/Simulated" class="dim">SIM</span></div>'
        + grp("POSITION", bar("DEMAND", "55.0 %", 55) + bar("POSITION", "54.6 %", 54.6) + kv(("DEVIATION", "-0.4 %  (limit 5 %)"))
              + leds(("On", "Feedback OK"), ("Off", "ZSC closed")))
        + mode_row()
        + '<div class="row"><span data-c="Text/Label" class="lbl">MAN</span><span data-c="Input/Setpoint" class="num" style="width:70px">55.0 %</span>'
          + "".join(f'<button data-c="Button/Small" class="preset">{v}</button>' for v in ("0", "25", "50", "75", "100")) + '</div><div class="row"><span data-c="Text/Label" class="lbl">CMD</span><button data-c="Button/Default">RESET</button></div>'
          '<div data-c="Text/Caption" class="hint">Entry enabled in MAN, not interlocked</div>'
        + grp("INTERLOCKS", cond("ok", "Reactor pressure not HH") + cond("byp", "Agitator running")
              + '<div data-c="Text/Caption">On trip the valve goes to 0 % (Cfg_IntlkPos)</div>', '<span data-c="Indicator/InterlockBadge" class="mini">I</span>')
        + alarm_grp([("Indicator/LED/Off", "Position deviation", ""), ("Indicator/LED/Off", "Feedback bad", ""), ("Indicator/LED/Off", "Interlock trip", "")])
        + grp("HISTORY (30 min)", trend([(dem, "#1F4E99", True), (pos, "#262626", False)], [("demand", "#1F4E99"), ("position", "#262626")]))
        + grp("MAINTENANCE", kv(("TRAVEL", "18 240 %"), ("REVERSALS", "9 812")))
        + details("CONFIGURATION", "fail position 0 % &middot; interlock position 0 % &middot; output 0-100 % &middot; rate 10 %/s up / 10 %/s down &middot; tight shut-off 2 % &middot; direct acting")
    ) + "</div>"


def motor_body(vfd=False):
    cur = wave(40, 62, 6, 1.1)
    spd = wave(40, 80, 5, 0.5)
    rows = [("Indicator/LED/Off", "Fail to start", ""), ("Indicator/LED/Off", "Fail to stop", ""), ("Indicator/LED/Off", "Uncommanded run/stop", ""),
            ("Indicator/LED/Off", "E-stop", ""), ("Indicator/LED/Off", "Interlock trip", ""), ("Indicator/LED/Off", "Excess starts", "")]
    rows += ([("Indicator/LED/Off", "Drive fault", ""), ("Alarm/Low/Fill", "Drive warning", "active"), ("Indicator/LED/Off", "Comm fail", ""), ("Indicator/LED/Off", "Speed deviation", "")]
             if vfd else [("Indicator/LED/Off", "Overload", ""), ("Indicator/LED/Off", "High current", "")])
    badges = ('<span data-c="Indicator/Badge">AT SPEED</span><span data-c="Indicator/Badge" class="dim">REV</span><span data-c="Indicator/Badge" class="dim">COMM FAIL</span>'
              if vfd else "")
    state = (f'<div class="row st"><span data-c="State/Running" class="big">RUNNING</span><span data-c="Indicator/Badge">NE107 OK</span>{badges}'
             '<span data-c="Mode/Simulated" class="dim">SIM</span><span data-c="Mode/Local" class="dim">LOCAL</span></div>')
    fb = (leds(("On", "Run fbk"), ("On", "Ready"), ("On", "E-stop OK"), ("Off", "Drive fault"), ("Off", "Warn")).replace("</div>", '<span data-c="Text/Label">FAULT CODE 0</span></div>')
          if vfd else leds(("On", "Run fbk"), ("On", "Ready"), ("On", "E-stop OK"), ("Off", "Overload")))
    cmd = ('<div class="row"><span data-c="Text/Label" class="lbl">CMD</span><button data-c="Button/Default Button/Toggle/On">START</button><button data-c="Button/Default">STOP</button>'
           f'<button data-c="Button/Default">RESET</button><button data-c="Button/Default">JOG</button>{role("Maint")}</div>')
    if vfd:
        cmd += ('<div class="row"><span data-c="Text/Label" class="lbl">DIR</span><button data-c="Button/Default Button/Toggle/On">FWD</button><button data-c="Button/Default">REV</button>'
                '<span data-c="Text/Caption">shown if Cfg_Reversible</span></div>')
    cmd += '<div data-c="Text/Caption" class="hint">Enabled in MAN, available, permitted, not interlocked, not LOCAL</div>'
    if vfd:
        drive = grp("SPEED", bar("SETPOINT", "48.0 Hz", 80, entry=True) + bar("SPEED", "47.9 Hz", 79.8, marker=80)
                    + kv(("CURRENT", "61.0 A (71 %)"), ("TORQUE", "64 %"), ("POWER", "28.4 kW"), ("ENERGY", "41 220 kWh")).replace('class="kv"', 'class="kv kv4"'))
        hist = trend([(spd, "#1F4E99", True), ([x - 0.5 for x in spd], "#262626", False), (cur, "#8D6E63", False)],
                     [("speed SP", "#1F4E99"), ("speed", "#262626"), ("current", "#8D6E63")], strip=[("stop", 20), ("run", 70), ("stop", 4), ("run", 6)])
    else:
        drive = grp("LOAD", bar("CURRENT", "38.2 A", 64) + kv(("RATED", "60 A"), ("LOAD", "64 %")))
        hist = trend([(cur, "#262626", False)], [("current", "#262626")], strip=[("stop", 20), ("run", 70), ("stop", 4), ("run", 6)])
    restart = ""  # restart-delay countdown line is shown only while Sts_RestartLeft > 0
    maint = details("MAINTENANCE", kv(("RUN HOURS", "1 284"), ("STARTS", "3 120"), ("STARTS LAST HR", "2 / 6"), ("HRS SINCE MAINT", "412"), ("MAINT DUE", "no"))
                + f'<div class="row"><button data-c="Button/Small">RESET MAINT</button>{role("Maint")}<button data-c="Button/Small">SIMULATE</button>{role("Maint")}</div>')
    perm = grp("PERMISSIVES", cond("ok", "Suction valve XV-201 open") + cond("ok", "Seal flush flow OK"), '<span data-c="Indicator/PermissiveBadge" class="mini">P</span>')
    intl = grp("INTERLOCKS", cond("ok", "Discharge pressure not HH") + cond("byp", "Tank T-200 not LL"), '<span data-c="Indicator/InterlockBadge" class="mini">I</span>')
    cfgtxt = ("speed 0-50 Hz &middot; deviation 2 Hz / 10 s &middot; reversible: no &middot; " if vfd else "") + "auto restart: no &middot; restart delay 5 s &middot; rated 60 A &middot; max 6 starts/h &middot; feedback time 3 s"
    tagdesc = ("P-201", "Circulation pump (VFD)") if vfd else ("P-101", "Transfer pump")
    return hdr(*tagdesc) + '<div class="body">' + state + fb + restart + mode_row() + cmd + drive + perm + intl + alarm_grp(rows) + grp("HISTORY (30 min)", hist) + maint + details("CONFIGURATION", cfgtxt) + "</div>"


def bypass_popup():
    return ('<div data-c="Container/PopupHeader" class="hdr"><div style="flex:1"><div data-c="Text/TagName Text/Color/Inverse">BYPASS CONDITION</div>'
            '<div data-c="Text/Caption Text/Color/Inverse">P-201 &middot; Interlocks &middot; condition 3</div></div><button data-c="Button/Icon" class="x">&#x2715;</button></div>'
            '<div class="body">'
            '<div data-c="Text/Body"><b>Tank T-200 not LL</b></div>'
            '<div data-c="Text/Caption">Currently: NOT OK &middot; bypassable &middot; max 8 h (Cfg_BypassMax)</div>'
            '<div class="row"><span data-c="Text/Label" class="lbl" style="width:70px">DURATION</span>'
            + "".join(f'<button data-c="{c}">{t}</button>' for t, c in (("1 h", "Button/Small"), ("2 h", "Button/Small"), ("4 h", "Button/Small Button/Toggle/On"), ("8 h", "Button/Small"))) +
            '</div><div class="row"><span data-c="Text/Label" style="width:70px">REASON</span><span data-c="Input/Field" style="flex:1;min-height:38px;padding:2px 4px">'
            'Level transmitter LT-100 replaced, verifying</span></div>'
            '<div data-c="Text/Caption">Required. Logged with your user name and time (IEC 61511 bypass record).</div>'
            '<div class="row" style="justify-content:flex-end;margin-top:6px"><button data-c="Button/Default">CANCEL</button><button data-c="Button/Danger">BYPASS</button></div>'
            '<div data-c="Text/Caption">Signed in as jsmith (Supervisor). Hidden below Supervisor; BYPASS also needs Inp_BypassPerm.</div>'
            '</div>')


def lim_table(rows, ideal=False):
    h = ('<div class="lt"><span data-c="Text/Label">LIMIT</span><span data-c="Text/Label">VALUE</span><span data-c="Text/Label">EN</span>'
         '<span data-c="Text/Label">PRI</span><span data-c="Text/Label">STATE</span>')
    for n, v, en, pri, st in rows:
        h += (f'<span data-c="Text/Body">{n}</span><span data-c="Input/Setpoint" class="num gatedS">{v}</span><span data-c="Text/Body">{"&#x2611;" if en else "&#x2610;"}</span>'
              f'<span data-c="Text/Caption">{pri}</span><span data-c="{"Text/Color/Fault" if st else "Text/Caption"}">{st or "-"}</span>')
    return h + "</div>"


def range_bar(pv_pct, marks, ideal=None):
    z = f'<div style="position:absolute;left:{ideal[0]}%;width:{ideal[1] - ideal[0]}%;top:0;bottom:0;background:#9DB4D0"></div>' if ideal else ""
    m = "".join(f'<div class="mk" style="left:{x}%"><span>{t}</span></div>' for t, x in marks)
    return (f'<div class="rb"><div data-c="Bar/Track" class="rbt">{z}<div data-c="Bar/Fill" style="width:{pv_pct}%;height:100%;opacity:.85"></div>{m}</div>'
            '<div class="axis"><span>0</span><span>50</span><span>100 kPa</span></div></div>')


def process_value():
    pv = wave(40, 45, 9, 0.9)
    big = ('<div class="row st"><span data-c="Value/Normal" class="pvbig">42.7</span><span data-c="Text/Units">kPa</span>'
           '<span data-c="Indicator/Badge">NE107 OK</span><span data-c="Indicator/Badge" class="dim">BAD</span><span data-c="Indicator/Badge" class="dim">SUBST</span>'
           '<span data-c="Mode/Simulated" class="dim">SIM</span></div>'
           '<div data-c="Text/Caption">Quality good &middot; rate of change +0.2 kPa/min</div>')
    rng = grp("RANGE", range_bar(42.7, [("LL", 5), ("L", 15), ("H", 75), ("HH", 90)], ideal=(30, 60))
              + '<div data-c="Text/Caption">Blue band = ideal range (T_KPI only)</div>')
    lims = grp("ALARM LIMITS", lim_table([("HH", "90.0", True, "High", ""), ("H", "75.0", True, "Medium", ""), ("L", "15.0", True, "Medium", ""),
                                         ("LL", "5.0", True, "High", ""), ("ROC", "10.0/min", False, "Low", "")])
               + '<div class="row"><button data-c="Button/Small">APPLY</button>' + role("Eng") + '<span data-c="Text/Caption">limit changes go to the audit log</span></div>')
    alarms = alarm_grp([("Indicator/LED/Off", "PV high-high", ""), ("Indicator/LED/Off", "PV high", ""), ("Indicator/LED/Off", "PV low", ""),
                        ("Indicator/LED/Off", "PV low-low", ""), ("Indicator/LED/Off", "Rate of change", ""), ("Indicator/LED/Off", "Bad PV / channel fault", "")])
    alarms = alarms.replace('<button data-c="Button/Small">ACK</button>', '<button data-c="Button/Small">ACK</button><button data-c="Button/Small">SHELVE</button>' + role("Sup") + '<span data-c="Text/Caption">shelving is audit-logged</span>')
    hist = grp("HISTORY (30 min)", trend([(pv, "#262626", False), ([75] * 40, "#E68A00", True), ([15] * 40, "#E68A00", True)], [("PV", "#262626"), ("H / L limits", "#E68A00")]))
    sim = '<div class="row"><button data-c="Button/Small">SIMULATE</button>' + role("Maint") + '<span data-c="Input/Setpoint" class="num">42.7</span></div>'
    cfg = details("CONFIGURATION", "EU 0-100 kPa &middot; raw 0-32000 &middot; filter 1.0 s &middot; square root: no &middot; low cut-off 0 % &middot; bad below -5 % / above 105 % &middot; on bad: hold last &middot; substitute 0.0"
                  + '<div data-c="Text/Caption">Editable by Engineer+</div>')
    return hdr("PT-101", "Header pressure") + '<div class="body">' + big + rng + lims + alarms + hist + sim + cfg + "</div>"


def heat_exchanger():
    hot_in, hot_out = wave(40, 82, 3, 0.2), wave(40, 41, 3, 1.4)
    svg = ('<svg viewBox="0 0 360 110" width="100%" height="110" style="display:block">'
           '<rect x="125" y="25" width="110" height="60" rx="8" fill="#E0E0E0" stroke="#262626" stroke-width="2"/>'
           '<path d="M132 55 L148 40 L164 70 L180 40 L196 70 L212 40 L228 55" fill="none" stroke="#262626" stroke-width="2"/>'
           '<line x1="4" y1="40" x2="125" y2="40" stroke="#262626" stroke-width="2"/><line x1="235" y1="70" x2="356" y2="70" stroke="#262626" stroke-width="2"/>'
           '<line x1="4" y1="70" x2="125" y2="70" stroke="#7F7F7F" stroke-width="2"/><line x1="235" y1="40" x2="356" y2="40" stroke="#7F7F7F" stroke-width="2"/>'
           '<text x="4" y="33" font-size="11">HOT IN 82.4 &#176;C</text><text x="242" y="88" font-size="11">HOT OUT 41.0 &#176;C</text>'
           '<text x="4" y="88" font-size="11" fill="#595959">COLD IN 18.2 &#176;C</text><text x="242" y="33" font-size="11" fill="#595959">COLD OUT 36.5 &#176;C</text>'
           '<text x="148" y="104" font-size="11" fill="#595959">counter-flow</text></svg>')
    flows = kv(("HOT FLOW", "12.4 m&#179;/h"), ("COLD FLOW", "16.8 m&#179;/h"), ("HOT DP", "0.42 bar"), ("COLD DP", "0.35 bar")).replace('class="kv"', 'class="kv kv4"')
    perf = grp("PERFORMANCE", kv(("DUTY", "212 kW"), ("HEAT BALANCE", "3.1 %"), ("LMTD", "33.4 K"), ("UA", "6.35 kW/K"),
                                 ("CLEANLINESS", "82 %"), ("APPROACH", "22.8 K"), ("EFFECTIVENESS", "64 %"), ("CALC", "valid")).replace('class="kv"', 'class="kv kv4"')
               + bar("CLEAN", "82 %", 82))
    lims = grp("ALARM LIMITS", lim_table([("Fouling (clean <)", "70 %", True, "Low", ""), ("Hot DP >", "0.80 bar", True, "Medium", ""),
                                         ("Cold DP >", "0.80 bar", True, "Medium", ""), ("Heat balance >", "10 %", True, "Low", ""), ("Hot out T >", "50 &#176;C", True, "Medium", "")])
               + '<div class="row"><button data-c="Button/Small">APPLY</button>' + role("Eng") + '<span data-c="Text/Caption">limit changes go to the audit log</span></div>')
    alarms = alarm_grp([("Indicator/LED/Off", "Fouling", ""), ("Indicator/LED/Off", "Hot side DP high", ""), ("Indicator/LED/Off", "Cold side DP high", ""),
                        ("Indicator/LED/Off", "Heat balance", ""), ("Indicator/LED/Off", "Hot outlet temperature high", "")])
    hist = grp("HISTORY (30 min)", trend([(hot_in, "#B71C1C", False), (hot_out, "#E57373", False), (wave(40, 82, 4, 2.0), "#1F4E99", True)],
                                      [("hot in", "#B71C1C"), ("hot out", "#E57373"), ("cleanliness %", "#1F4E99")]))
    rel = '<div class="row"><span data-c="Text/Label" class="lbl" style="width:auto">RELATED</span><button data-c="Button/Default" style="width:auto;padding:0 8px">FAN P-101 &#x25B8;</button><span data-c="Text/Caption">opens dw_Rotating</span></div>'
    cfg = details("CONFIGURATION", "Cp hot 4.18 / cold 4.18 kJ/kg K &middot; design UA 7.8 kW/K &middot; min flow 1.0 m&#179;/h &middot; calc filter 30 s"
                  + '<div data-c="Text/Caption">Editable by Engineer+</div>')
    return hdr("E-401", "Product cooler") + '<div class="body">' + svg + flows + perf + lims + alarms + hist + rel + cfg + "</div>"


def loop():
    pv, sp = wave(40, 58, 6, 0.4), [60] * 40
    cv = wave(40, 46, 9, 2.2)
    big = ('<div class="pvsp"><div><span data-c="Text/Label">PV</span><span data-c="Value/Normal" class="pvbig">118.4</span><span data-c="Text/Units">&#176;F</span></div>'
           '<div><span data-c="Text/Label">SP</span><span data-c="Input/Setpoint" class="pvbig">120.0</span><span data-c="Text/Units">&#176;F</span></div>'
           '<div><span data-c="Text/Label">CV</span><span data-c="Value/Output" class="pvbig">46.0</span><span data-c="Text/Units">%</span></div></div>'
           '<div class="row st"><span data-c="Indicator/Badge">AUTO</span><span data-c="Indicator/Badge" class="dim">TRACK</span><span data-c="Indicator/Badge" class="dim">SP RAMP</span>'
           '<span data-c="Indicator/Badge" class="dim">WINDUP HI</span><span data-c="Indicator/Badge" class="dim">WINDUP LO</span><span data-c="Indicator/Badge" class="dim">PV BAD</span></div>')
    bars = grp("LOOP", bar("PV", "118.4 &#176;F", 59.2, marker=60) + bar("SP", "120.0 &#176;F", 60, entry=True) + bar("CV", "46.0 %", 46, cls="Value/Output")
               + kv(("ERROR", "-1.6 &#176;F"), ("SP TARGET", "120.0 &#176;F")))
    mode = ('<div class="row"><span data-c="Text/Label" class="lbl">MODE</span><button data-c="Button/Default">MAN</button>'
            '<button data-c="Button/Default Button/Toggle/On">AUTO</button><button data-c="Button/Default">CAS</button></div>'
            '<div data-c="Text/Caption" class="hint">SP entry in AUTO, CV entry in MAN; CAS shown if a cascade source is configured</div>')
    intl = grp("INTERLOCKS", cond("ok", "Heater E-401 available") + '<div data-c="Text/Caption">On trip the output goes to 0 % (Cfg_IntlkCV)</div>',
               '<span data-c="Indicator/InterlockBadge" class="mini">I</span>')
    alarms = alarm_grp([("Indicator/LED/Off", "Deviation high", ""), ("Indicator/LED/Off", "Deviation low", ""), ("Indicator/LED/Off", "PV bad", "")])
    hist = grp("HISTORY (30 min)", trend([(pv, "#262626", False), (sp, "#1F4E99", True), (cv, "#8D6E63", False)], [("PV", "#262626"), ("SP", "#1F4E99"), ("CV", "#8D6E63")]))
    tune = details("TUNING", kv(("KP", "1.20"), ("TI", "45 s"), ("TD", "0 s"), ("ACTION", "reverse"), ("DEADBAND", "0.0"), ("FF GAIN", "0.0"),
                                ("SP LIMITS", "50-250 &#176;F"), ("CV LIMITS", "0-100 %"), ("SP RATE", "5 &#176;F/min"), ("CV RATE", "10 %/s")).replace('class="kv"', 'class="kv kv4"')
                   + '<div class="row"><button data-c="Button/Small">APPLY</button>' + role("Eng") + '<span data-c="Text/Caption">replaces the LoopConfig popup</span></div>')
    return hdr("TIC-101", "Reactor jacket temperature") + '<div class="body">' + big + bars + mode + intl + alarms + hist + tune + "</div>"


def cfg_form(rows, who="Eng"):
    h = '<div class="cf">'
    for lbl, val, unit in rows:
        if val in ("yes", "no"):
            inp = f'<span data-c="Input/Check" class="chk">{"&#x2611;" if val == "yes" else "&#x2610;"}</span>'
        elif isinstance(val, list):
            inp = f'<span data-c="Input/Dropdown" class="dd">{val[0]} &#x25BE;</span>'
        else:
            inp = f'<span data-c="Input/Setpoint" class="num">{val}</span>'
        h += f'<span data-c="Text/Label">{lbl}</span>{inp}<span data-c="Text/Units">{unit}</span>'
    return (h + '</div><div class="row"><button data-c="Button/Small">APPLY</button>' + role(who)
            + '<button data-c="Button/Small">REVERT</button><span data-c="Text/Caption">changes go to the audit log (old -> new, user, time)</span></div>')


CFG = {
    "Docks/HeatTransfer": ("CONFIGURATION", [("Hot side Cp", "4.18", "kJ/kg K"), ("Cold side Cp", "4.18", "kJ/kg K"), ("Counter-flow", "yes", ""),
                                             ("Design UA", "7.80", "kW/K"), ("Min flow for calc", "1.0", "m&#179;/h"), ("Calc filter", "30", "s")]),
    "Docks/ProcessValue": ("CONFIGURATION", [("EU min", "0.0", "kPa"), ("EU max", "100.0", "kPa"), ("Units", "kPa", ""), ("Raw min", "0", "counts"), ("Raw max", "32000", "counts"),
                                             ("Filter time constant", "1.0", "s"), ("Square-root extract", "no", ""), ("Low cut-off", "0.0", "%"),
                                             ("Bad below", "-5.0", "%"), ("Bad above", "105.0", "%"), ("On bad PV", ["Hold last", "Substitute", "Use raw"], ""), ("Substitute value", "0.0", "kPa")]),
    "Docks/Loop": ("TUNING", [("Gain Kp", "1.20", ""), ("Integral Ti", "45.0", "s"), ("Derivative Td", "0.0", "s"), ("Action", ["Reverse", "Direct"], ""),
                              ("Deadband", "0.0", "&#176;F"), ("Feedforward gain", "0.0", ""), ("PV range", "0 - 300", "&#176;F"), ("SP low / high limit", "50 / 250", "&#176;F"),
                              ("CV low / high limit", "0 / 100", "%"), ("SP rate limit", "5.0", "&#176;F/min"), ("CV rate limit", "10.0", "%/s"), ("Interlock CV", "0.0", "%"),
                              ("PV tracking in MAN", "yes", ""), ("On bad PV", ["Hold CV", "Go to MAN", "Interlock CV"], ""), ("SP from program", "no", "")]),
    "Docks/Heater": ("CONFIGURATION", [("Control type", ["SSR, time-proportioned", "On/off contactor", "SCR, analog reference"], ""), ("Cycle time", "4.0", "s"),
                                       ("Minimum pulse", "100", "ms"), ("Power min / max", "0 / 100", "%"), ("Power ramp", "0.0", "%/s"), ("Rated power", "12.0", "kW"),
                                       ("Rated current", "17.4", "A"), ("Load-failure below", "80", "% of expected"), ("Shorted if off and above", "1.0", "A"), ("Feedback time", "3.0", "s")]),
}


def heater():
    duty = wave(40, 62, 12, 0.7)
    cyc = "".join(f'<div style="flex:{w};background:{"#4D4D4D" if on else "#E0E0E0"}"></div>' for on, w in ((1, 62), (0, 38), (1, 62), (0, 38), (1, 62), (0, 38)))
    return hdr("EH-301", "Jacket heater zone 1") + '<div class="body">' + (
        '<div class="row st"><span data-c="State/Running" class="big">ON</span><span data-c="Indicator/Badge">HEATING</span><span data-c="Indicator/Badge">NE107 OK</span>'
        '<span data-c="Indicator/Badge" class="dim">SHORTED</span><span data-c="Indicator/Badge" class="dim">LOAD FAIL</span><span data-c="Mode/Local" class="dim">LOCAL</span></div>'
        + leds(("On", "Contactor"), ("On", "High limit OK"), ("On", "Supply OK"), ("Off", "SCR alarm"))
        + mode_row()
        + '<div class="row"><span data-c="Text/Label" class="lbl">CMD</span><button data-c="Button/Default Button/Toggle/On">ON</button><button data-c="Button/Default">OFF</button><button data-c="Button/Default">RESET</button></div>'
        + grp("POWER", bar("DEMAND", "62.0 %", 62, entry=True) + bar("APPLIED", "62.0 %", 62)
              + '<div data-c="Text/Caption">SSR, 4 s cycle: ON 2.5 s / OFF 1.5 s</div><div class="strip" style="height:10px">' + cyc + '</div>'
              + kv(("POWER", "7.4 kW"), ("CURRENT", "10.8 A"), ("LOAD", "100 % of expected"), ("ENERGY", "3 410 kWh")).replace('class="kv"', 'class="kv kv4"')
              + '<div data-c="Text/Caption">Demand entry in MAN (SSR and SCR types); on/off type shows ON/OFF only</div>')
        + grp("PERMISSIVES", cond("ok", "Circulation pump P-301 running"), '<span data-c="Indicator/PermissiveBadge" class="mini">P</span>')
        + grp("INTERLOCKS", cond("ok", "Jacket temperature not HH") + cond("ok", "Flow switch FS-301 made", byp=True), '<span data-c="Indicator/InterlockBadge" class="mini">I</span>')
        + alarm_grp([("Indicator/LED/Off", "Excess-temperature limit", ""), ("Indicator/LED/Off", "SSR / SCR shorted", ""), ("Indicator/LED/Off", "Partial load failure", ""),
                     ("Indicator/LED/Off", "Fail to switch on", ""), ("Indicator/LED/Off", "Fail to switch off", ""), ("Indicator/LED/Off", "SCR controller alarm", ""), ("Indicator/LED/Off", "Interlock trip", "")])
        + grp("HISTORY (30 min)", trend([(duty, "#262626", False), ([d * 0.95 for d in duty], "#8D6E63", False)], [("applied %", "#262626"), ("current % of rated", "#8D6E63")]))
        + details("MAINTENANCE", kv(("ON HOURS", "2 940"), ("SWITCH-ONS", "1 204")))
        + details("CONFIGURATION", "control type SSR &middot; cycle 4 s &middot; rated 12 kW / 17.4 A")
    ) + "</div>"


def trend_expanded():
    pv, cv = wave(90, 58, 6, 0.4), wave(90, 46, 9, 2.2)
    W, H = 384, 600
    def path(pts, c, dash=False):
        n = len(pts) - 1
        d = " ".join(f"{'M' if i == 0 else 'L'}{i * W / n:.1f},{H - p * H / 100:.1f}" for i, p in enumerate(pts))
        return f'<path d="{d}" fill="none" stroke="{c}" stroke-width="2"{" stroke-dasharray=\"6 4\"" if dash else ""}/>'
    grid = "".join(f'<line x1="0" x2="{W}" y1="{y}" y2="{y}" stroke="#D0D0D0"/>' for y in range(60, H, 60)) + "".join(f'<line y1="0" y2="{H}" x1="{x}" x2="{x}" stroke="#E0E0E0"/>' for x in range(64, W, 64))
    rng = "".join(f'<button data-c="Button/Small{" Button/Toggle/On" if t == "30 m" else ""}">{t}</button>' for t in ("5 m", "30 m", "1 h", "8 h", "24 h"))
    pens = "".join(f'<div class="row"><i style="display:inline-block;width:14px;height:4px;background:{c}"></i><span data-c="Text/Label">{n}</span><span data-c="Text/Body">{v}</span></div>'
                   for n, c, v in (("PV", "#262626", "118.4 &#176;F"), ("SP", "#1F4E99", "120.0 &#176;F"), ("CV", "#8D6E63", "46.0 %")))
    return (hdr("dw_Loop &middot; TIC-101", "Reactor jacket temperature").replace("close returns the right dock to the screen&#39;s default view", "close returns the right dock to the screen&#39;s default view")
            + f'<div class="body"><div class="row">{rng}<span style="flex:1"></span><button data-c="Button/Icon" class="xp" title="collapse graph">&#x2921;</button></div>'
            '<div class="row"><button data-c="Button/Small">&#x23F8; PAUSE</button><button data-c="Button/Small">&#x21BB; LIVE</button></div>'
            f'<svg viewBox="0 0 {W} {H}" width="100%" height="{H}" style="border:1px solid #9E9E9E;background:#FAFAFA">{grid}{path(pv, "#262626")}{path([60] * 90, "#1F4E99", True)}{path(cv, "#8D6E63")}</svg>'
            '<div class="axis"><span>10:12</span><span>10:17</span><span>10:22</span><span>10:27</span><span>10:32</span><span>10:37</span><span>10:42</span></div>'
            + pens + '</div>')


def io_card():
    chans = [("00", "XV-101 ZSO", "ON", ""), ("01", "XV-101 ZSC", "OFF", ""), ("02", "P-101 RUN", "ON", ""), ("03", "P-101 OL", "OFF", ""),
             ("04", "LSH-200", "OFF", ""), ("05", "FS-301", "ON", ""), ("06", "spare", "-", ""), ("07", "PS-410", "OFF", "WIRE BREAK")]
    rows = "".join(f'<div data-c="Table/{"Row" if i % 2 else "RowAlt"}" class="ch"><span>{c}</span><span>{t}</span><span>{v}</span>'
                   f'<span data-c="{"Text/Color/Fault" if e else "Text/Caption"}">{e or "OK"}</span></div>' for i, (c, t, v, e) in enumerate(chans))
    return hdr("R0-S3 BMXDDI1602", "Discrete input, 16 ch, 24 VDC sink") + '<div class="body">' + (
        '<div class="row st"><span data-c="State/Running" class="big">RUNNING</span><span data-c="Indicator/Badge">NE107 MAINT</span>'
        '<span data-c="Indicator/Badge">1 CH FAULT</span><span data-c="Indicator/Badge" class="dim">MODULE FAULT</span></div>'
        + grp("MODULE", kv(("RACK / SLOT", "0 / 3"), ("DROP", "Main rack (CPU)"), ("FIRMWARE", "V2.4"), ("FIELD POWER", "OK"),
                           ("I/O ERROR", "1 channel"), ("BUS", "OK")).replace('class="kv"', 'class="kv kv4"')
              + leds(("On", "Module OK"), ("On", "Field supply"), ("Fault", "Channel error"), ("On", "Bus comm")))
        + grp("CHANNELS 0-7", '<div class="ch chh"><span>CH</span><span>TAG</span><span>VALUE</span><span>STATUS</span></div>' + rows
              + '<div class="row"><button data-c="Button/Small">CH 0-7</button><button data-c="Button/Small">CH 8-15</button></div>')
        + alarm_grp([("Alarm/Low/Fill", "Channel 07 wire break", "active, unacked"), ("Indicator/LED/Off", "Module fault", ""),
                     ("Indicator/LED/Off", "Field power lost", ""), ("Indicator/LED/Off", "Module missing / wrong type", "")])
        + '<div class="row"><span data-c="Text/Label" style="width:auto">RELATED</span><button data-c="Button/Default" style="width:auto;padding:0 8px">RACK 0 &#x25B8;</button>'
          '<button data-c="Button/Default" style="width:auto;padding:0 8px">PS-410 &#x25B8;</button></div>'
        + details("CONFIGURATION", "card type BMXDDI1602 &middot; rack 0 slot 3 &middot; channel tags from the I/O list &middot; diagnostics from the module status words")
    ) + "</div>"


DOCK_CSS = """.dock2{height:100%;display:flex;flex-direction:column;box-sizing:border-box}.dock2 .hdr{display:flex;align-items:center;gap:6px;padding:4px 8px}
.dock2 .x{width:28px;height:28px}.dock2 .body{flex:1;overflow:hidden;padding:2px 8px;display:flex;flex-direction:column;gap:3px}
.dock2 .row{display:flex;gap:4px;align-items:center;flex-wrap:wrap;margin:1px 0}.dock2 .lbl{width:40px}.dock2 .big{font-size:16px;padding:2px 10px}
.dock2 .dim{opacity:.35}.dock2 .hint{margin-top:-3px}.dock2 .grp{padding:3px 6px}.dock2 .gh{display:flex;justify-content:space-between;align-items:center;margin-bottom:2px}
.dock2 .cond{display:flex;gap:5px;align-items:center;min-height:20px}.dock2 .led{width:10px;height:10px;border-radius:50%;display:inline-block;flex:none}
.dock2 .audit{margin:-2px 0 2px 15px;font-style:italic}.dock2 .mini{width:14px;height:14px;font-size:10px;display:inline-flex;align-items:center;justify-content:center}
.role{font-size:9px;color:#5E35B1;border:1px dashed #5E35B1;border-radius:3px;padding:0 2px}
.strip{display:flex;height:12px;border:1px solid #7F7F7F}.axis{display:flex;justify-content:space-between;font-size:9px;color:#616161}
.legend2{font-size:9px;color:#424242}.legend2 i{display:inline-block;width:8px;height:8px;margin:0 2px 0 6px}.ev{display:flex;justify-content:space-between;font-size:11px;padding:1px 3px}
.dock2 details summary{cursor:pointer}.dock2 button[data-c~="Button/Default"]{width:72px;height:30px;padding:0;justify-content:center;text-align:center}.dock2 button[data-c~="Button/Small"]{min-width:64px;height:22px;padding:0 6px;justify-content:center}.dock2 button.preset{min-width:0;width:38px}.dock2 button.gated{outline:1.5px dashed #5E35B1;outline-offset:1px}.barrow{display:flex;align-items:center;gap:5px;margin:2px 0}.bl{width:64px}
.kv4{grid-template-columns:auto 1fr auto 1fr}.ch{display:grid;grid-template-columns:.4fr 1.6fr .7fr 1.1fr;gap:4px;font-size:12px;padding:1px 3px}.chh{font-weight:700;color:#595959}.xp{width:22px;height:22px;padding:0;margin-left:4px}.cf{display:grid;grid-template-columns:1.3fr 1.3fr .7fr;gap:4px 6px;align-items:center}.cf .num{min-width:0;text-align:right}.dd{border:1px solid #9E9E9E;background:#fff;padding:1px 4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.chk{font-size:16px}.pvbig{font-size:26px !important;font-weight:700 !important;margin:0 4px;line-height:1.1}.lt{display:grid;grid-template-columns:1.4fr 1fr .4fr .8fr .8fr;gap:2px 6px;align-items:center}.lt .num{min-width:0}.rb{margin:16px 0 4px}.rbt{position:relative;height:14px}.mk{position:absolute;top:-4px;bottom:-4px;width:2px;background:#E68A00}.mk span{position:absolute;top:-12px;left:-6px;font-size:9px;color:#595959}.pvsp{display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px}.pvsp>div{display:flex;flex-direction:column;align-items:flex-start}.trk{flex:1;height:10px;position:relative}.num{min-width:62px;text-align:right}"""


DOCKS = {
    "dw_ValveDiscrete": ("T_DValve", "valve_discrete"),
    "dw_ValveAnalog": ("T_CValve", "valve_analog"),
    "dw_Rotating": ("T_Motor", "motor"),
    "dw_VFD": ("T_VFD", "vfd"),
    "dw_Heater": ("T_Heater", "heater"),
    "dw_HeatTransfer": ("T_HeatEx", "heat_exchanger"),
    "dw_ProcessValue": ("T_AI / T_KPI", "process_value"),
    "dw_Loop": ("T_PID", "loop"),
    "dw_IOCard": ("native: x80 device DDT", "io_card"),
}


def gate(h):
    return re.sub(r'<button ([^>]*)>([^<]*)</button><span class="role" title="([^"]*)">[^<]*</span>', r'<button \1 class="gated" title="\3">\2</button>', h)


def dock_card(did, path, ttype, parts):
    REV2 = {"valve_discrete": valve_discrete, "valve_analog": valve_analog, "motor": motor_body, "vfd": lambda: motor_body(True), "heat_exchanger": heat_exchanger, "process_value": process_value, "loop": loop, "heater": heater, "io_card": io_card}
    if isinstance(parts, str) and parts in REV2:  # rev 2 designs
        inner = f'<div data-c="Container/Faceplate" class="dock2">{gate(REV2[parts]())}</div>'
        return frame(path, inner, DOCK_DW, DOCK_DH, ttype, did, "<br><b>rev 2 - design proposal</b> &middot; 400 x 860 at 1080p (37.04 vh x 79.63 vh; 800 x 1720 at 4K) &middot; dashed purple outline = role-gated (hover for role)" + ("<br>binds to the Modicon x80 device DDT imported from Control Expert" if parts == "io_card" else ""), maxh=600)
    body = "".join(SECTIONS.get(p, p) for p in parts)
    head = (f'<div data-c="Container/PopupHeader" class="row"><span data-c="Text/TagName">XV-101</span>'
            f'<span data-c="Text/Caption" style="flex:1">Description</span><button data-c="Button/Icon" title="close returns the right dock to the screen&#39;s default view">&#x2715;</button></div>'
            f'<div class="row"><span data-c="State/Stopped">CLOSED</span><span data-c="Text/Caption">NE107: OK</span></div>')
    inner = f'<div data-c="Container/Faceplate" class="dock">{head}{body}</div>'
    return frame(path, inner, DOCK_DW, DOCK_DH, ttype.replace("GAP ", "gap:"), did, "<br><b>NEW - design proposal</b> &middot; 400 x 860 at 1080p (800 x 1720 at 4K) &middot; close &#x2715; returns the right dock to the screen's default view", maxh=600)


# ---------- screen layout (decision 31: Perspective right dock, push mode; supersedes 24) ----------
EV_LABEL = "Right dock efcDynamic (push): Docks/Host shows the window from openDock params (efc.ui)"
SYMS = [("Rotating/Pump_Centrifugal", 40, 120, True), ("Valves/Valve_OnOff_Pneumatic", 360, 120, False), ("Valves/Valve_Control", 640, 120, False),
        ("Rotating/Blower", 40, 480, False), ("Rotating/Motor", 360, 480, False)]


def layout_card():
    W, H, HEAD, MENU, ALARM = 1920, 1080, 80, 120, 140
    RW = 400
    PW, MH = W - MENU - RW, H - HEAD - ALARM
    lab = lambda t, pos="": f'<div class="rl" style="{pos}">{t}</div>'
    pipes = f'<svg width="{PW}" height="{MH}" style="position:absolute;inset:0" fill="none" stroke="#7F7F7F" stroke-width="6">'
    pipes += '<path d="M160,170 H360 M440,170 H640 M720,170 H' + str(min(PW - 20, 1000)) + '"/><path d="M160,530 H360"/></svg>'
    syms = ""
    for rel, x, y, sel in SYMS:
        if x + 160 > PW:
            continue
        syms += (f'<img src="../../docs/previews/templates/{rel}.png" style="position:absolute;left:{x}px;top:{y}px;width:160px;height:auto"'
                 f'{" class=hit" if sel else ""}>')
    sel_note = '<div class="rl" style="left:20px;top:300px;color:#00A3E0">click symbol: efc.ui.openDynamic opens the right dock with the window path + tagPath</div>'
    proc = (f'<div data-c="Container/ProcessArea" class="reg" style="left:{MENU}px;top:{HEAD}px;width:{PW}px;height:{MH}px">{pipes}{syms}{sel_note}'
            + lab(f"Process area &middot; {PW} x {MH} px at 1080p &middot; {2 * PW} x {2 * MH} px at 4K", "left:20px;bottom:10px"))
    proc += "</div>"
    if True:
        sc = (MH - 56 - 66) / DOCK_DH
        inner = f'<div data-c="Container/Faceplate" class="dock2">{gate(motor_body())}</div>'
        win = (f'<div style="position:absolute;left:0;top:56px;width:{RW}px;height:{DOCK_DH}px;transform:scale({sc:.4f});transform-origin:0 0">{inner}</div>')
        note = "dw_Rotating (Docks/Rotating)"
    wtxt = "37.04 vh"
    right = (f'<div data-c="Container/TrendPanel" class="reg ev" style="left:{W - RW}px;top:{HEAD}px;width:{RW}px;height:{MH}px">'
             f'<div class="rl evl">{EV_LABEL}</div>{win}'
             + lab(f"Right dock (push) &middot; {RW} x {MH} px at 1080p ({wtxt}) &middot; {2 * RW} x {2 * MH} px at 4K &middot; {note}", f"left:0;right:0;bottom:0;border:none;border-top:1px solid #7F7F7F;font-size:19px;height:66px"))
    right += "</div>"
    head = (f'<div data-c="Container/Header" class="reg" style="left:0;top:0;width:{W}px;height:{HEAD}px;display:flex;align-items:center;gap:20px;padding:0 20px;box-sizing:border-box">'
            '<span data-c="Text/TagName">EFC &middot; Reactor area</span><span data-c="Text/Caption" style="flex:1">Screen header</span>'
            '<span data-c="Text/Caption">jsmith &middot; Supervisor</span>'
            + lab(f"Header &middot; {W} x {HEAD} px at 1080p &middot; 3840 x 160 px at 4K", "position:static;margin-left:auto") + "</div>")
    menu = (f'<div data-c="Container/Menu" class="reg" style="left:0;top:{HEAD}px;width:{MENU}px;height:{MH}px;display:flex;flex-direction:column;align-items:center;gap:10px;padding-top:12px;box-sizing:border-box">'
            + "".join('<button data-c="Button/Icon" style="width:40px;height:40px">&#x25A3;</button>' for _ in range(5))
            + f'<div class="rl" style="writing-mode:vertical-rl;left:8px;bottom:10px;top:auto;white-space:nowrap;font-size:19px">Menu {MENU} x {MH} px at 1080p &middot; {2*MENU} x {2*MH} px at 4K</div></div>')
    alarm = (f'<div data-c="Container/AlarmBar" class="reg" style="left:0;top:{H - ALARM}px;width:{W}px;height:{ALARM}px;display:flex;align-items:center;gap:20px;padding:0 20px;box-sizing:border-box">'
             '<span data-c="Alarm/High/Fill" style="padding:4px 12px">HIGH</span><span data-c="Text/Body" style="flex:1">10:42:07 &middot; TIC-101 Reactor jacket temperature high &middot; unacked</span>'
             '<button data-c="Button/Default">ACK</button>'
             + lab(f"Alarm bar &middot; {W} x {ALARM} px at 1080p &middot; 3840 x 280 px at 4K", "position:static;margin-left:auto") + "</div>")
    shell = f'<div style="position:relative;width:{W}px;height:{H}px;background:#fff">{head}{menu}{proc}{right}{alarm}</div>'
    name = "Screen_Layout_normal"
    cap = ("Normal: 400 x 860 right dock (37.04 vh x 79.63 vh; 800 x 1720 at 4K) shows the open dynamic window (here dw_Rotating, drawn scaled to leave room for the labels); close returns the dock to the screen's default view. "
           "Dynamic windows open in a Perspective right dock in push mode, Dock ID efcDynamic (decision 31, supersedes 24): the process area shrinks, nothing is covered. The dock never changes width; an expanded graph fills the window (decision 26). All shell sizes double at 4K.")
    fig = (f'<figure class="card wide" id="{name}"><div class="view" style="width:960px;height:540px"><div class="stage" style="width:{W}px;height:{H}px;transform:scale(0.5)">{shell}</div></div>'
           f'<figcaption><code>{name.replace("_", " ")}</code><br><b class="ok">1920 x 1080 shell</b> &middot; normal<br>{cap}</figcaption></figure>')
    return name, fig


PAGE_CSS = """body{margin:0;padding:16px;background:#E6E6E6;font:12px 'Noto Sans','Segoe UI',Arial,sans-serif;color:#1F1F1F}
h1{font-size:16px;margin:0 0 4px}h2{font-size:13px;margin:18px 0 6px;border-bottom:1px solid #BDBDBD}
.grid{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-start}.card{margin:0;background:#F2F2F2;border:1px solid #C4C4C4;padding:6px}
.card figcaption{font-size:10px;line-height:1.4;margin-top:4px;width:240px}.gap{color:#B71C1C}.ok{color:#1B5E20}
.view{position:relative;overflow:hidden;background:#DADADA}.stage{position:relative;transform-origin:0 0;--vh:10.8px;display:flex;flex-direction:column}.stage>div:first-of-type{flex:1}
.box{display:flex;gap:2px;align-items:center;justify-content:center}.row{display:flex;gap:4px;align-items:center;margin:3px 0;flex-wrap:wrap}
.kv{display:grid;grid-template-columns:auto 1fr;gap:2px 6px;margin:3px 0}.sym{height:150px;display:flex;flex:none}.sym svg,.sym2 svg{width:100%;height:100%}.sym2{height:28px;display:flex}
.hit{outline:1.5px dashed #00A3E0;outline-offset:-1px;cursor:pointer}.badge{position:absolute;top:2px}.bP{left:2px}.bI{right:2px}.view>.box:first-child{padding:0 22px}
.inp{background:#fff;border:1px solid #BDBDBD;padding:0 3px}.ph{border:1px dashed #9E9E9E;color:#616161;font-size:10px;box-sizing:border-box;padding:2px;margin:1px;text-align:center;flex:1}
.dock{height:100%;box-sizing:border-box;overflow:hidden;padding:6px}.card.wide figcaption{width:auto;font-size:11px}.reg{position:absolute;box-sizing:border-box;overflow:hidden}.rl{position:absolute;font-size:22px;line-height:1.2;background:rgba(255,255,255,.85);color:#1F1F1F;padding:2px 8px;border:1px solid #7F7F7F;z-index:5}.reg.ev{outline:3px dashed #00A3E0;outline-offset:-3px}.evl{left:0;top:0;right:0;background:#E0F4FC;border:none;border-bottom:1px solid #00A3E0;color:#005A7D;font-size:15px;line-height:1.25;padding:3px 6px;box-sizing:border-box;height:56px}.legend{font-size:11px;color:#424242}
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
            frag = template_card(path, "gap:T_Station").replace("click symbol: open dynamic window", "existing dock view; planned: move to <code>Docks/Station</code>, resize 300 x 800 to 400 x 860 (decision 25)")
        open(f"{OUT}/{slug(path)}.html", "w").write(frag)
        groups.setdefault("Dynamic windows", []).append(frag)
    for path, (title, rows) in CFG.items():
        body = f'<div class="body">{grp(title + " (expanded)", cfg_form(rows))}</div>'
        f2 = frame(path + " - " + title.lower() + " expanded", f'<div data-c="Container/Faceplate" class="dock2">{body}</div>', 400, 110 + 27 * len(rows) + 22 * sum(isinstance(r[1], list) for r in rows), "review", path.split("/")[1],
                   "<br>section shown open; collapsed by default", maxh=600)
        open(f"{OUT}/{slug(path)}_{title.lower()}_expanded.html", "w").write(f2)
        groups.setdefault("Expanded sections", []).append(f2)
    f3 = frame("Docks/Parts/TrendExpanded", f'<div data-c="Container/Popup" class="dock2">{trend_expanded()}</div>', 400, 860, "any", "popup",
               "<br><b>NEW</b> &middot; expanded graph: fills the dynamic window; window stays 400 x 860; other sections hidden until collapsed (decision 26)", cw=400, maxh=860)
    open(f"{OUT}/Docks_Parts_TrendExpanded.html", "w").write(f3)
    groups.setdefault("Expanded sections", []).append(f3)
    fr = frame("Docks/Parts/BypassConfirm", f'<div data-c="Container/Popup" class="dock2">{bypass_popup()}</div>', 400, 330, "T_Intlk", "popup",
               "<br><b>NEW - design proposal</b> &middot; opened by every Bypass button (Supervisor+)", maxh=600)
    open(f"{OUT}/Docks_Parts_BypassConfirm.html", "w").write(fr)
    groups.setdefault("Dynamic windows", []).append(fr)
    for _ in (0,):
        nm, fg = layout_card()
        open(f"{OUT}/{nm}.html", "w").write(fg)
        groups.setdefault("Screen layout", []).append(fg)
    body = "".join(f'<h2>{esc(g)}</h2><div class="grid">{"".join(fr)}</div>' for g, fr in groups.items())
    page = (f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>EFC Library Previews</title><style>{PAGE_CSS}\n{DOCK_CSS}\n/* EFC_Styles */\n{css_block()}</style></head><body>'
            f'<h1>EFC Library - review contact sheet</h1><p class="legend">Dashed blue = click target (opens the dynamic window). Red type = gap (no EFCLib v1 type). '
            f'Templates are drawn from slim output (layout approximate); dynamic windows and VFD are new design proposals.</p>{body}</body></html>')
    import base64  # inline the renders so index.html is self-contained
    page = re.sub(r'src="([^"]+\.png)"', lambda m: 'src="data:image/png;base64,' + base64.b64encode(open(os.path.normpath(f"{OUT}/{m.group(1)}"), "rb").read()).decode() + '"', page)
    open(f"{OUT}/index.html", "w").write(page)
    print(f"fragments {sum(len(v) for v in groups.values())} -> {OUT}/index.html ({os.path.getsize(OUT + '/index.html') // 1024} KB)")
