#!/usr/bin/env python3
"""
EFC Ignition library build (EFC_Styles, PID_Symbols, EFC_PID_Library, EFC_ProcessValues + any imported projects).

    python3 build.py              regenerate everything tracked in git (projects/, tags/, symbols/, docs/style-class-index.md)
    python3 build.py --preview    also render docs/previews/*.png (needs Playwright + Chromium)
    python3 build.py --dist       also write importable zips to dist/ (gitignored)
    python3 build.py --check      check the committed projects/ only (no regeneration); used by CI

The generator (generator/) is the source of truth. projects/ holds the generated Perspective projects
unzipped in the gateway's own folder layout (data/projects/<Name>/...), so every change shows as a
readable JSON diff and the folders can be copied straight onto a gateway.
"""
import argparse, json, os, shutil, subprocess, sys, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(ROOT, "generator")
BUILD = os.path.join(ROOT, "build")
DIST = os.path.join(ROOT, "dist")
PROJECTS = os.path.join(ROOT, "projects")
VERSION = json.load(open(os.path.join(ROOT, "VERSION.json")))
COMBINED = "EFC_PID_Library"


def run(*args, **kw):
    subprocess.run([sys.executable, *args], cwd=GEN, check=True, **kw)


def unzip_to(zp, dest):
    """Replace dest with the zip's contents (files only; directory entries are implied)."""
    if os.path.exists(dest):
        shutil.rmtree(dest)
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist():
            if n.endswith("/"):
                continue
            p = os.path.join(dest, n)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            data = z.read(n)
            if n.endswith(".json"):          # normalise: LF endings + trailing newline for clean diffs
                data = data.replace(b"\r\n", b"\n").rstrip(b"\n") + b"\n"
            open(p, "wb").write(data)


def zip_dir(src, zp):
    """Zip a project folder the way a Designer export looks (project.json first, then folder entries)."""
    sys.path.insert(0, GEN)
    from make_project_zip import redo
    raw = zp + ".raw"
    with zipfile.ZipFile(raw, "w", zipfile.ZIP_DEFLATED) as z:
        for d, _, fs in sorted(os.walk(src)):
            for f in sorted(fs):
                p = os.path.join(d, f)
                z.write(p, os.path.relpath(p, src).replace(os.sep, "/"))
    redo(raw, zp)
    os.remove(raw)


def replace_tree(src, dest):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def project_json(title, description, parent=""):
    return {"title": title, "description": description, "parent": parent, "enabled": True, "inheritable": True}


def generate(preview):
    os.environ["EFC_BUILD_TIMESTAMP"] = VERSION["date"] + "T00:00:00Z"
    v = VERSION["version"]
    run("build_styles.py", stdout=subprocess.DEVNULL)
    run("build_pid.py")
    if preview:
        run("preview_pid.py")

    # projects/: EFC_Styles, PID_Symbols (child of EFC_Styles), EFC_PID_Library (both merged, no parent)
    unzip_to(os.path.join(BUILD, "styles", "EFC_Styles.zip"), os.path.join(PROJECTS, "EFC_Styles"))
    unzip_to(os.path.join(BUILD, "pid", "PID_Symbols_PROJECT.zip"), os.path.join(PROJECTS, "PID_Symbols"))
    for name, desc, parent in (("EFC_Styles", f"EFC ISA-101 style class library v{v} (generated)", ""),
                               ("PID_Symbols", f"EFC controlled-device templates v{v} (generated). Parent: EFC_Styles", "EFC_Styles")):
        with open(os.path.join(PROJECTS, name, "project.json"), "w") as f:
            json.dump(project_json(name, desc, parent), f, indent=2); f.write("\n")
    comb = os.path.join(PROJECTS, COMBINED)
    if os.path.exists(comb):
        shutil.rmtree(comb)
    for name in ("EFC_Styles", "PID_Symbols"):
        shutil.copytree(os.path.join(PROJECTS, name), comb, dirs_exist_ok=True)
    with open(os.path.join(comb, "project.json"), "w") as f:
        json.dump(project_json(COMBINED, f"EFC_Styles + PID controlled-device templates v{v} in one project (generated). "
                                         "Import standalone, or make it the parent of an HMI project."), f, indent=2); f.write("\n")

    # tags/: overwrite the generated PID files only; imported tag files (e.g. Station demo) are kept
    os.makedirs(os.path.join(ROOT, "tags"), exist_ok=True)
    for f in os.listdir(os.path.join(BUILD, "pid", "tags")):
        shutil.copy(os.path.join(BUILD, "pid", "tags", f), os.path.join(ROOT, "tags", f))
    replace_tree(os.path.join(BUILD, "pid", "symbols"), os.path.join(ROOT, "symbols"))
    shutil.copy(os.path.join(BUILD, "styles", "style_index.md"), os.path.join(ROOT, "docs", "style-class-index.md"))
    run("build_pv.py")                    # EFC_ProcessValues -> projects/, tags/PV_Demo_Tags.json, docs/pv-style-index.md
    if preview:
        os.makedirs(os.path.join(ROOT, "docs", "previews"), exist_ok=True)
        shutil.copy(os.path.join(BUILD, "pid", "preview.png"), os.path.join(ROOT, "docs", "previews", "templates.png"))


def make_dist():
    os.makedirs(DIST, exist_ok=True)
    v = VERSION["version"]
    out = []
    for name in sorted(os.listdir(PROJECTS)):          # every project folder, generated or imported
        if not os.path.isfile(os.path.join(PROJECTS, name, "project.json")):
            continue
        zp = os.path.join(DIST, f"{name}_PROJECT.zip")
        zip_dir(os.path.join(PROJECTS, name), zp)
        out.append(zp)
    bundle = os.path.join(DIST, f"EFC_Ignition_Library_v{v}.zip")     # everything in one download for people without git
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as z:
        for sub in ("tags", "symbols"):
            for d, _, fs in sorted(os.walk(os.path.join(ROOT, sub))):
                for f in sorted(fs):
                    p = os.path.join(d, f)
                    z.write(p, f"EFC_Ignition_Library_v{v}/" + os.path.relpath(p, ROOT))
        for zp in out:
            z.write(zp, f"EFC_Ignition_Library_v{v}/" + os.path.basename(zp))
        for f in ("README.md", "CHANGELOG.md"):
            z.write(os.path.join(ROOT, f), f"EFC_Ignition_Library_v{v}/{f}")
    return out


def check(zips):
    run("check_81.py", *zips)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preview", action="store_true", help="render docs/previews/templates.png (Playwright)")
    ap.add_argument("--dist", action="store_true", help="write importable project zips to dist/")
    ap.add_argument("--check", action="store_true", help="only run the 8.1 import check on the committed projects/")
    a = ap.parse_args()
    if not a.check:
        generate(a.preview)
    zips = make_dist() if (a.dist or a.check) else None
    if zips is None:                      # check from temporary zips so the check always runs
        import tempfile
        global DIST
        DIST = tempfile.mkdtemp()
        zips = make_dist()
    check(zips)
    print(f"v{VERSION['version']} OK" + (f"  ->  {DIST}" if a.dist else ""))


if __name__ == "__main__":
    main()
