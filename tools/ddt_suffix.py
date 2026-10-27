#!/usr/bin/env python3
"""
Name-suffix a built Perspective project so it can sit next to the main library in one gateway.

Every view under Templates/ gets SUFFIX (default _DDT) on its last path segment, e.g.
    Templates/Valves/Valve_Solenoid                 ->  Templates/Valves/Valve_Solenoid_DDT
    Templates/Dynamic Window/Station/Station        ->  Templates/Dynamic Window/Station/Station_DDT
and every string that names one of those views (embedded views, flex repeaters, openPopup calls, the efc.ui
dynamic-window table) is rewritten to match. Styles/ views, style classes, the stylesheet and the script library
are not renamed. The project title gets the suffix too.

    python3 tools/ddt_suffix.py projects/EFC_Library /tmp/EFC_Library_DDT
"""
import json, os, re, shutil, sys

VIEWS = "com.inductiveautomation.perspective/views"
SUFFIX = "_DDT"
TEXT = (".json", ".py")


def view_paths(root):
    """View paths (relative to the views folder, '/' separated) of every view in the project."""
    vroot = os.path.join(root, VIEWS)
    return sorted(os.path.relpath(d, vroot).replace(os.sep, "/")
                  for d, _, fs in os.walk(vroot) if "view.json" in fs)


def suffix_tree(src, dest, suffix=SUFFIX, title=None, description=None):
    """Copy project folder src to dest with the Templates/ views renamed. Returns (renamed paths, replacements)."""
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    vroot = os.path.join(dest, VIEWS)
    renamed = [p for p in view_paths(dest) if p.startswith("Templates/") and not p.endswith(suffix)]
    for p in sorted(renamed, key=len, reverse=True):
        os.rename(os.path.join(vroot, *p.split("/")), os.path.join(vroot, *(p + suffix).split("/")))

    # longest path first, so a path that is a prefix of another is never matched inside it
    pats = [(re.compile(r'(?<![A-Za-z0-9_])' + re.escape(p) + r'(?![A-Za-z0-9_])'), p + suffix)
            for p in sorted(renamed, key=len, reverse=True)]
    count = 0
    for d, _, fs in os.walk(dest):
        for f in fs:
            if not f.endswith(TEXT) or f == "project.json":
                continue
            fp = os.path.join(d, f)
            txt = open(fp, encoding="utf-8").read()
            out = txt
            for pat, new in pats:
                out, n = pat.subn(lambda _m, new=new: new, out)
                count += n
            if out != txt:
                open(fp, "w", encoding="utf-8", newline="").write(out)

    pj = os.path.join(dest, "project.json")
    meta = json.load(open(pj))
    meta["title"] = title or meta.get("title", "") + suffix
    if description:
        meta["description"] = description
    with open(pj, "w") as f:
        json.dump(meta, f, indent=2); f.write("\n")
    return renamed, count


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    renamed, count = suffix_tree(sys.argv[1], sys.argv[2])
    print(f"{len(renamed)} views renamed, {count} path references rewritten -> {sys.argv[2]}")


if __name__ == "__main__":
    main()
