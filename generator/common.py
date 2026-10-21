"""Shared helpers for build_pv.py: repo paths, version stamp and deterministic writers (LF, trailing newline, fixed timestamps)."""
import json, os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_V = json.load(open(os.path.join(REPO, "VERSION.json")))
VERSION, DATE = _V["version"], _V["date"]
PERSPECTIVE = "com.inductiveautomation.perspective"

def dump(obj):
    return json.dumps(obj, indent=2) + "\n"

def write(path, text, binary=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if binary:
        open(path, "wb").write(text)
    else:
        with open(path, "w", newline="\n", encoding="utf-8") as fh:
            fh.write(text)

def resource_json(files, actor):
    """8.1 resource.json. The timestamp comes from VERSION.json so rebuilds are byte-identical."""
    return dump({"scope": "G", "version": 1, "restricted": False, "overridable": True, "files": files,
                 "attributes": {"lastModification": {"actor": "efc-ignition-library", "timestamp": DATE + "T00:00:00Z"}}})

def project_json(title, description, parent=""):
    return dump({"title": title, "description": f"{description} (v{VERSION}, generated)", "parent": parent,
                 "enabled": True, "inheritable": True})

def project_dir(name):
    return os.path.join(REPO, "projects", name)

def extract_inline(view, prefix, classes):
    """EFC_Styles classes only: move each component's static inline style (everything but `classes`) into a
    generated style class <prefix>/<component name>; identical styles share one class. Bound style props
    (propConfig) are left alone. `classes` collects {name: style} for write_classes()."""
    by_style = {json.dumps(s, sort_keys=True): n for n, s in classes.items()}
    def walk(c):
        st = c.get("props", {}).get("style")
        bound = c.get("propConfig", {}).get("props.style.classes", {}).get("binding")
        if bound and bound.get("type") == "property" and not bound.get("transforms") and isinstance(st, dict):
            path = bound["config"]["path"]               # plain property binding -> equivalent expression we can append to
            bound.clear(); bound.update({"type": "expr", "config": {"expression": "{%s}" % path}})
        if bound and bound.get("type") != "expr":
            bound, st = None, None                       # property/tag-bound classes: leave the inline style
        if isinstance(st, dict) and any(k != "classes" for k in st):
            body = {k: v for k, v in st.items() if k != "classes"}
            key = json.dumps(body, sort_keys=True)
            name = by_style.get(key)
            if not name:
                base = f"{prefix}/{c.get('meta', {}).get('name', 'x')}"
                name, i = base, 2
                while name in classes:
                    name, i = f"{base}{i}", i + 1
                classes[name], by_style[key] = body, name
            c["props"]["style"] = {"classes": " ".join(x for x in (st.get("classes", ""), name) if x)}
            if bound:                                    # expression-bound classes replace the static ones: append there
                bound["config"]["expression"] = f"({bound['config']['expression']}) + ' {name}'"
        for k in c.get("children", []):
            walk(k)
    walk(view["root"])
    return view

def write_classes(proj, classes, actor):
    for name, style in classes.items():
        d = os.path.join(proj, PERSPECTIVE, "style-classes", *name.split("/"))
        write(os.path.join(d, "style.json"), dump({"base": {"style": style}, "variants": []}))
        write(os.path.join(d, "resource.json"), resource_json(["style.json"], actor))
