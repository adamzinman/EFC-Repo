"""HTML mock-up of Templates/Sequence/SequenceBar with the demo tag values, for the preview PNG.
Usage: python make_preview.py out.html, then screenshot it (e.g. chrome --headless --screenshot)."""
import html
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import gen_phase as g
px = lambda v: re.sub(r"([\d.]+)vh", lambda m: f"{float(m.group(1)) * 10.8:.1f}px", v)
css = []
for cls, st in g.STYLE_CLASSES.items():
    d = dict(g.SEG_BASE); d.update(st)
    name = cls.split("/")[-1]
    css.append(".seg." + name + "{" + ";".join(f"{re.sub('([A-Z])', lambda m: '-' + m.group(1).lower(), k)}:{px(v)}" for k, v in d.items()) + "}")
STATE = ["IDLE","RUNNING","COMPLETE","PAUSING","PAUSED","HOLDING","HELD","RESTARTING","STOPPING","STOPPED","ABORTING","ABORTED"]
def chip(st, fail):
    if fail or st in (10, 11): return "background:#3A3A3A;color:#fff;border-color:#000"
    if st in (1, 3, 7): return "background:#FFFFFF;color:#1F1F1F"
    if st in (0, 2, 9): return "background:#9E9E9E;color:#1F1F1F"
    return "background:#C4C4C4;color:#1F1F1F"
cards = []
for name, title, labels, segs, st, mode, step, msg, ms, pct, fail in g.DEMO:
    s = "".join(f'<div class="seg {g.SEG_NAMES[v]}">{html.escape(t)}</div>' for t, v in zip(labels, segs))
    m = {1: ("MAN", "background:#595959;color:#fff"), 2: ("SEMI", "background:#E6E6E6"), 3: ("AUTO", "background:#E6E6E6")}[mode]
    cards.append(f'''<div class="card"><div class="row"><div class="title">{title}</div><div class="cap">Step {step}</div>
<div class="chip" style="{m[1]}">{m[0]}</div><div class="chip" style="{chip(st, fail)}">{STATE[st]}</div></div>
<div class="segs">{s}</div><div class="row"><div class="msg" style="{'color:#3A3A3A;font-weight:700' if fail else ''}">{html.escape(msg)}</div>
<div class="cap">{str(pct) + ' %' if pct else ''}</div><div class="cap" style="margin-left:8px">{ms // 1000} s</div></div></div>''')
legend = "".join(f'<div class="seg {n}" style="flex:0 0 96px">{n if n != "Held" else "Held / waiting"}</div>' for n in g.SEG_NAMES)
doc = f'''<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;background:#D9D9D9;font-family:'Noto Sans','Segoe UI',Arial,sans-serif;color:#1F1F1F;padding:24px;width:700px}}
h1{{font-size:20px;margin:0 0 4px}} .hint{{font-size:12px;color:#4D4D4D;margin-bottom:12px}}
.card{{background:#F0F0F0;border:1px solid #A6A6A6;border-radius:4px;padding:8px 10px;margin-bottom:10px;width:620px;box-shadow:0 1px 2px rgba(0,0,0,.15)}}
.row{{display:flex;align-items:center}} .title{{flex:1;font-weight:700;font-size:15px}} .cap{{font-size:12px;color:#4D4D4D;margin-right:8px;font-variant-numeric:tabular-nums}}
.chip{{font-size:11px;font-weight:700;letter-spacing:.04em;border:1px solid #7F7F7F;border-radius:2px;padding:1px 6px;margin-left:4px}}
.segs{{display:flex;height:28px;margin:6px 0}} .seg{{flex:1;display:flex;align-items:center;margin:0 1px;font-size:12px;white-space:nowrap;overflow:hidden}}
.msg{{flex:1;font-size:14px}} .legend{{display:flex;gap:6px;height:24px;margin-top:6px}}
{"".join(css)}</style></head><body><h1>Templates/Sequence/SequenceBar - preview</h1>
<div class="hint">Mock-up of the Perspective view with the SeqBar_Demo tags (640 x 104 @1080p). Colours from the EFC ISA-101 palette.</div>
{"".join(cards)}<div class="hint" style="margin-top:6px">Segment states (T_SeqBar.Sts_Seg)</div><div class="legend">{legend}</div></body></html>'''
open(sys.argv[1], "w").write(doc)
