#!/usr/bin/env python3
"""Controls Standard tool. Run from the repo root. Output is capped by default.

  std.py brief <chapter>      INDEX summary, open items, open comments, lint count
  std.py outline <chapter>    section labels with line ranges
  std.py show <label>         print one section by its \\label (with line numbers)
  std.py lint [files]         mechanical checks
  std.py status               one line per chapter
  std.py types [--plc f..] [--ignition f..]   doc type tables vs exports
  std.py hw [sheet] [--both]  \\pn{} parts vs approved hardware sheet
  std.py req [out.csv]        shall/should -> requirements matrix CSV
  std.py comments <file> [name]   reviewer comments -> review-comments.csv
  std.py redline [rev-X]      latexdiff redline PDF since a tag
  std.py changelog <X>        CHANGELOG draft since last tag

<chapter> = file name or part of it ("04", "networks", "A1").
Add --all to any command to disable the output cap.
"""
import collections, csv, glob, io, os, re, runpy, subprocess, sys, contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
CAP = 20
SCRIPTS = {"lint": "lint.py", "status": "status.py", "types": "sync_types.py",
           "hw": "sync_hardware.py", "req": "req_matrix.py",
           "comments": "comments_intake.py", "changelog": "changelog_draft.py"}
SECT = ["chapter", "section", "subsection", "subsubsection"]
SECT_RX = re.compile(r"^[^%]*\\(chapter|section|subsection|subsubsection)\*?\{")

def run_script(name, args):
    buf, code = io.StringIO(), 0
    sys.argv = [name] + args
    sys.path.insert(0, HERE)
    with contextlib.redirect_stdout(buf):
        try:
            runpy.run_path(os.path.join(HERE, name), run_name="__main__")
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
            if isinstance(e.code, str): print(e.code)
    return buf.getvalue().splitlines(), code

def cap(lines, full):
    """Keep summary lines; if findings exceed CAP, group counts and show the first CAP."""
    finds = [l for l in lines if re.search(r"\[[\w-]+\]", l)]
    other = [l for l in lines if l not in finds]
    if full or len(finds) <= CAP:
        return lines
    by = collections.Counter()
    for l in finds:
        f = l.split(":", 1)[0] if ":" in l and not l.startswith("[") else "-"
        by[(f, re.search(r"\[([\w-]+)\]", l).group(1))] += 1
    out = ["counts by file/check:"]
    out += [f"  {f}  {c}: {n}" for (f, c), n in sorted(by.items())]
    out += [f"first {CAP} of {len(finds)}:"] + finds[:CAP]
    out += other + ["(capped; rerun on one file, or add --all)"]
    return out

def chapter(q):
    files = sorted(glob.glob("chapters/*.tex"))
    hit = [f for f in files if q.lower() in os.path.basename(f).lower()]
    if len(hit) != 1:
        sys.exit(f"'{q}' matches {len(hit)} chapter files: " + ", ".join(map(os.path.basename, hit[:8])))
    return hit[0]

def index_block(base):
    if not os.path.exists("INDEX.md"):
        return []
    out, on = [], False
    for l in open("INDEX.md", encoding="utf-8"):
        if l.startswith("## "):
            on = base in l
        if on:
            out.append(l.rstrip())
    return out

def brief(q, full):
    f = chapter(q)
    base = os.path.basename(f)
    blk = index_block(base) or [f"## {base} (no INDEX entry)"]
    print("\n".join(blk))
    m = re.search(r"\|\s*(?:Ch|App)\.?\s*([\w.]+)\s*\|", blk[0])
    ch = m.group(1) if m else base.split("-")[0].lstrip("0")
    keys = {ch, base, base.rsplit(".", 1)[0], base.split("-")[0]}
    if os.path.exists("open-items.csv"):
        rows = [r for r in csv.DictReader(open("open-items.csv", encoding="utf-8"))
                if r.get("status", "").strip() == "open" and r.get("chapter", "").strip() in keys]
        print(f"open items: {len(rows)}")
        for r in rows[:CAP]: print(f"  {r['id']} ({r.get('owner','')}): {r.get('question','')[:100]}")
    if os.path.exists("review-comments.csv"):
        rows = [r for r in csv.DictReader(open("review-comments.csv", encoding="utf-8"))
                if r.get("status") == "open" and re.match(rf"{re.escape(ch)}(\.|\s|$)", r.get("location", ""))]
        print(f"open review comments: {len(rows)}")
        for r in rows[:CAP]: print(f"  {r['id']} {r['author']}: {r['comment'][:100]}")
    lines, _ = run_script("lint.py", [f])
    print("lint: " + (lines[-1] if lines else "?"))

def sections(f):
    ls = open(f, encoding="utf-8", errors="replace").read().splitlines()
    heads = []
    for i, l in enumerate(ls, 1):
        m = SECT_RX.search(l)
        if m:
            lab = re.search(r"\\label\{([^}]+)\}", l) or (i < len(ls) and re.search(r"^\s*\\label\{([^}]+)\}", ls[i]))
            t = re.search(r"\{((?:[^{}]|\{[^{}]*\})*)\}", l[m.end() - 1:])
            heads.append([i, SECT.index(m.group(1)), lab.group(1) if lab else "-",
                          t.group(1) if t else "", len(ls)])
    for k, h in enumerate(heads):
        for n in heads[k + 1:]:
            if n[1] <= h[1]:
                h[4] = n[0] - 1; break
    return ls, heads

def outline(q):
    f = chapter(q)
    _, heads = sections(f)
    print(f)
    for start, lvl, lab, title, end in heads:
        print(f"{'  ' * lvl}{start}-{end}  {lab}  {title[:60]}")

def show(label, full):
    for f in sorted(glob.glob("chapters/*.tex")):
        ls, heads = sections(f)
        for start, lvl, lab, title, end in heads:
            if lab == label:
                if lvl == 0 and not full:
                    sys.exit(f"'{label}' is a whole chapter ({end-start+1} lines); use outline, or --all")
                print(f"{f}:{start}-{end}")
                for i in range(start, end + 1):
                    print(f"{i:5}| {ls[i-1]}")
                return
    sys.exit(f"label '{label}' not found at a section heading")

def main():
    a = sys.argv[1:]
    full = "--all" in a
    a = [x for x in a if x != "--all"]
    if not a or a[0] in ("-h", "--help", "help"):
        print(__doc__); return 0
    cmd, rest = a[0], a[1:]
    if cmd == "brief" and rest: return brief(rest[0], full)
    if cmd == "outline" and rest: return outline(rest[0])
    if cmd == "show" and rest: return show(rest[0], full)
    if cmd == "redline":
        return subprocess.call(["bash", os.path.join(HERE, "redline.sh")] + rest)
    if cmd in SCRIPTS:
        lines, code = run_script(SCRIPTS[cmd], rest)
        print("\n".join(cap(lines, full)))
        return code
    print(__doc__); return 2

if __name__ == "__main__":
    sys.exit(main() or 0)
