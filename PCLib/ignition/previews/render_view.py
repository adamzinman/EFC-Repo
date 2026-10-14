"""
Render the Perspective views in EFC_SequenceBar.zip to HTML, exactly as they are imported, for a preview PNG.

It reads view.json from the project zip and evaluates every expression and tag binding against
PCLib_SeqBar_Demo_Tags.json. Styles come from the project's own style classes and from the real
EFC_Styles classes in efc-ignition-library_1.zip. Flex containers, labels and embedded views are laid
out the way Perspective lays them out; vh units are converted to px for a 1920 x 1080 session.

Usage:  python render_view.py <efc-ignition-library_1.zip> <out.html> [view path, default Templates/Sequence/_Demo]
Then:   chrome --headless --screenshot=SequenceBar.png --window-size=700,540 out.html
"""
import html
import json
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
IGN = os.path.dirname(HERE)
PERSP = "com.inductiveautomation.perspective"
VH_PX = 10.8                                    # 1 vh at 1080p


# ------------------------------------------------------------------ Ignition expression subset
class Expr:
    """Recursive-descent evaluator for the expression functions the views use."""
    TOK = re.compile(r'\s*(?:(\d+\.\d*|\d+)|("(?:[^"\\]|\\.)*")|(\{[^}]+\})|([A-Za-z_]\w*)|(<=|>=|==|!=|&&|\|\||[-+*/<>(),\[\]!]))')

    def __init__(self, text, ref):
        self.t, self.ref, self.p = [], ref, 0
        pos = 0
        while pos < len(text.rstrip()):
            m = self.TOK.match(text, pos)
            if not m:
                raise SyntaxError(f"bad token at {text[pos:pos + 20]!r}")
            pos = m.end()
            num, s, r, name, op = m.groups()
            self.t.append(("num", float(num)) if num else ("str", json.loads(s)) if s else
                          ("ref", r[1:-1]) if r else ("name", name) if name else ("op", op))

    def peek(self):
        return self.t[self.p] if self.p < len(self.t) else (None, None)

    def take(self, v=None):
        tok = self.t[self.p]
        if v and tok[1] != v:
            raise SyntaxError(f"expected {v}, got {tok[1]}")
        self.p += 1
        return tok

    def run(self):
        v = self.cmp()
        if self.p != len(self.t):
            raise SyntaxError("trailing tokens")
        return v

    # each level returns a thunk so try() can catch errors lazily
    def cmp(self):
        a = self.add()
        while self.peek()[1] in ("<", ">", "<=", ">=", "==", "!="):
            op = self.take()[1]
            b, l = self.add(), a
            f = {"<": lambda x, y: x < y, ">": lambda x, y: x > y, "<=": lambda x, y: x <= y,
                 ">=": lambda x, y: x >= y, "==": lambda x, y: x == y, "!=": lambda x, y: x != y}[op]
            a = (lambda l, b, f: lambda: f(l(), b()))(l, b, f)
        return a

    def add(self):
        a = self.mul()
        while self.peek()[1] in ("+", "-"):
            op = self.take()[1]
            b, l = self.mul(), a

            def f(l=l, b=b, op=op):
                x, y = l(), b()
                if op == "+":
                    return (str(x) + str(y)) if isinstance(x, str) or isinstance(y, str) else x + y
                return x - y
            a = f
        return a

    def mul(self):
        a = self.post()
        while self.peek()[1] in ("*", "/"):
            op = self.take()[1]
            b, l = self.post(), a
            a = (lambda l, b, op: lambda: l() * b() if op == "*" else l() / b())(l, b, op)
        return a

    def post(self):
        a = self.prim()
        while self.peek()[1] == "[":
            self.take("[")
            i = self.cmp()
            self.take("]")
            a = (lambda a, i: lambda: a()[int(i())])(a, i)
        return a

    def prim(self):
        kind, v = self.take()
        if kind in ("num", "str"):
            return lambda: v
        if kind == "ref":
            return lambda: self.ref(v)
        if kind == "op" and v == "(":
            e = self.cmp()
            self.take(")")
            return e
        if kind == "op" and v == "-":
            e = self.post()
            return lambda: -e()
        if kind == "op" and v == "!":
            e = self.prim()
            return lambda: not e()
        if kind == "name":
            if v in ("true", "false"):
                return lambda: v == "true"
            self.take("(")
            args = []
            while self.peek()[1] != ")":
                args.append(self.cmp())
                if self.peek()[1] == ",":
                    self.take(",")
            self.take(")")
            return self.fn(v, args)
        raise SyntaxError(f"unexpected {v}")

    @staticmethod
    def fn(name, a):
        def case():
            x = a[0]()
            for k in range(1, len(a) - 1, 2):
                if a[k]() == x:
                    return a[k + 1]()
            return a[-1]() if len(a) % 2 == 0 else None

        def tryf():
            try:
                return a[0]()
            except Exception:
                return a[1]()

        def nf():
            x, f = a[0](), a[1]()
            dec = len(f.split(".")[1]) if "." in f else 0
            return f"{x:,.{dec}f}" if "," in f else f"{x:.{dec}f}"
        fns = {"case": case, "try": tryf, "numberFormat": nf,
               "coalesce": lambda: next((x for x in (f() for f in a) if x is not None), None),
               "toStr": lambda: (lambda x: "" if x is None else ("true" if x is True else "false" if x is False else
                                                                 str(int(x)) if isinstance(x, float) and x.is_integer() else str(x)))(a[0]()),
               "if": lambda: a[1]() if a[0]() else a[2](),
               "isNull": lambda: a[0]() is None,
               "len": lambda: len(a[0]())}
        if name not in fns:
            raise NameError(f"expression function {name}() not supported by the renderer")
        return fns[name]


# ------------------------------------------------------------------ project, styles, tags
def load(efc_lib_zip):
    proj = zipfile.ZipFile(os.path.join(IGN, "EFC_SequenceBar.zip"))
    views = {n.split("/views/")[1].rsplit("/", 1)[0]: json.loads(proj.read(n))
             for n in proj.namelist() if n.endswith("view.json")}
    styles = {}
    lib = zipfile.ZipFile(efc_lib_zip)
    for z in (lib, proj):                       # project classes override EFC_Styles
        for n in z.namelist():
            if n.endswith("/style.json") and "/style-classes/" in n and ("EFC_Styles" in n or z is proj):
                styles[n.split("/style-classes/")[1].rsplit("/", 1)[0]] = json.loads(z.read(n))["base"]["style"]
    tags = {}
    demo = json.load(open(os.path.join(IGN, "PCLib_SeqBar_Demo_Tags.json")))
    for folder in demo["tags"]:
        if folder["name"] == "_types_":
            continue
        for inst in folder["tags"]:
            for t in inst["tags"]:
                tags[f"[default]{folder['name']}/{inst['name']}/{t['name']}"] = t["value"]
    return views, styles, tags


def css(style):
    out = []
    for k, v in style.items():
        if k == "classes":
            continue
        v = re.sub(r"(-?[\d.]+)vh", lambda m: f"{float(m.group(1)) * VH_PX:.2f}px", str(v))
        out.append(re.sub(r"[A-Z]", lambda m: "-" + m.group(0).lower(), k) + ":" + v)
    return ";".join(out)


# ------------------------------------------------------------------ renderer
class View:
    def __init__(self, views, styles, tags, path, params):
        self.views, self.styles, self.tags = views, styles, tags
        self.v = views[path]
        self.params = dict(self.v.get("params", {}))
        self.params.update(params)
        self.custom = {}
        for key, cfg in self.v.get("propConfig", {}).items():
            if key.startswith("custom."):
                self.custom[key[7:]] = self.binding(cfg["binding"])

    def ref(self, path):
        if path.startswith("view.params."):
            return self.params[path[12:]]
        if path.startswith("view.custom."):
            return self.custom.get(path[12:])
        raise KeyError(path)

    def binding(self, b):
        cfg = b["config"]
        if b["type"] == "expr":
            return Expr(cfg["expression"], self.ref).run()()
        if b["type"] == "tag":
            refs = {k: str(Expr(v, self.ref).run()()) for k, v in cfg["references"].items()}
            p = re.sub(r"\{(\w+)\}", lambda m: refs[m.group(1)], cfg["tagPath"])
            val = self.tags.get(p)
            return float(val) if isinstance(val, int) and not isinstance(val, bool) else val
        raise ValueError(b["type"])

    def resolve(self, c):
        """Copy of the component with every bound property replaced by its value."""
        c = json.loads(json.dumps(c))
        for key, cfg in c.get("propConfig", {}).items():
            val = self.binding(cfg["binding"])
            node, parts = c, key.split(".")
            for p in parts[:-1]:
                node = node.setdefault(p, {})
            node[parts[-1]] = val
        return c

    def style_of(self, props):
        st = {}
        for cl in str(props.get("style", {}).get("classes", "")).split():
            st.update(self.styles.get(cl, {}))
        st.update({k: v for k, v in props.get("style", {}).items() if k != "classes"})
        return st

    def comp(self, c, parent_dir):
        c = self.resolve(c)
        pos, props = c.get("position", {}), c.get("props", {})
        if pos.get("display") is False:
            return ""
        st = self.style_of(props)
        lay = {"box-sizing": "border-box", "min-width": "0", "min-height": "0"}
        if parent_dir:
            lay["flex"] = f"{pos.get('grow', 0)} {pos.get('shrink', 1)} {pos.get('basis', 'auto')}"
        tip = c.get("meta", {}).get("tooltip", {})
        title = f' title="{html.escape(str(tip.get("text", "")))}"' if tip.get("enabled") else ""
        t = c["type"]
        if t == "ia.container.flex":
            lay.update({"display": "flex", "flex-direction": props.get("direction", "row"),
                        "justify-content": props.get("justify", "flex-start"),
                        "align-items": props.get("alignItems", "stretch"), "flex-wrap": props.get("wrap", "nowrap")})
            kids = "".join(self.comp(k, props.get("direction", "row")) for k in c.get("children", []))
            return f'<div style="{css(lay)};{css(st)}"{title}>{kids}</div>'
        if t == "ia.display.label":
            lay.update({"display": "flex", "align-items": "center"})
            text = html.escape(str(props.get("text", "")))
            if "Ellipsis" in str(props.get("style", {}).get("classes", "")):
                text = f'<span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;width:100%;text-align:inherit">{text}</span>'
            return f'<div style="{css(lay)};{css(st)}"{title}>{text}</div>'
        if t == "ia.display.view":
            sub = View(self.views, self.styles, self.tags, props["path"], props.get("params", {}))
            size = sub.v["props"]["defaultSize"]
            if props.get("useDefaultViewHeight"):
                lay["height"] = f"{size['height']}px"
            lay["width"] = f"{size['width']}px"
            lay["display"] = "flex"
            return f'<div style="{css(lay)};{css(st)}">{sub.render_root()}</div>'
        return f'<div style="{css(lay)}">[{t}]</div>'

    def render_root(self):
        # the root fills the view; the caller wraps it in a flex box of the view's size
        return self.comp(dict(self.v["root"], position={"basis": "100%", "grow": 1, "shrink": 1}), "row")


def main():
    lib, out = sys.argv[1], sys.argv[2]
    path = sys.argv[3] if len(sys.argv) > 3 else "Templates/Sequence/_Demo"
    views, styles, tags = load(lib)
    v = View(views, styles, tags, path, {})
    size = v.v["props"]["defaultSize"]
    page = (f'<!doctype html><html><head><meta charset="utf-8"><style>body{{margin:0;background:#D9D9D9;'
            f"font-family:'Noto Sans','Segoe UI',Arial,sans-serif;color:#1F1F1F}}</style></head><body>"
            f'<div style="width:{size["width"]}px;height:{size["height"]}px;display:flex">{v.render_root()}</div></body></html>')
    open(out, "w", encoding="utf-8").write(page)
    print(f"{path}: {size['width']} x {size['height']} -> {out}")


if __name__ == "__main__":
    main()
