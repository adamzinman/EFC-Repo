#!/usr/bin/env python3
"""Export every shall/should statement to a CSV requirements matrix.

Usage: python3 scripts/req_matrix.py [out.csv]   (default requirements-matrix.csv)
IDs follow chapter/section/subsection counters plus enumerate item number,
e.g. 7.3.2 item 4 -> 7.3.2-4; prose outside lists -> 7.3.2-p1. Appendix
chapters are lettered. Numbering is computed, so spot-check it against the PDF.
Prints only a one-line summary.
"""
import csv, glob, re, sys
from _cfg import clean

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "requirements-matrix.csv"
    files, main_appx = [], None
    try:
        main_src = re.sub(r"(?<!\\)%.*", "", open("main.tex", encoding="utf-8").read())
        for m in re.finditer(r"\\appendix\b|\\(?:include|input)\{([^}]+)\}", main_src):
            if m.group(1) is None:
                main_appx = len(files)
            else:
                x = m.group(1); files.append(x if x.endswith(".tex") else x + ".tex")
    except FileNotFoundError:
        pass
    if not files:
        files = sorted(glob.glob("chapters/*.tex"))
    rows, ctr, appx, title = [], [0, 0, 0], False, ""
    for n, f in enumerate(files):
        if n == main_appx:
            appx, ctr[0] = True, 0
        try:
            ls = open(f, encoding="utf-8", errors="replace").read().splitlines()
        except FileNotFoundError:
            continue
        stack, buf, start, pcount = [], [], 0, 0

        def secno():
            ch = chr(64 + ctr[0]) if appx else str(ctr[0])
            return ".".join([ch] + [str(x) for x in ctr[1:] if x]) if ctr[0] else "0"

        def flush():
            nonlocal buf, pcount
            text = clean(" ".join(buf))
            buf = []
            if not re.search(r"\b(shall|should)\b", text, re.I):
                return
            lvl = "shall" if re.search(r"\bshall\b", text, re.I) else "should"
            if stack:
                rid = f"{secno()}-" + ".".join(str(x) for x in stack)
            else:
                pcount += 1; rid = f"{secno()}-p{pcount}"
            rows.append([rid, lvl, title, text, f"{f}:{start}"])

        for i, l in enumerate(ls, 1):
            code = re.sub(r"(?<!\\)%.*", "", l)
            if re.search(r"\\appendix\b", code):
                appx, ctr[0] = True, 0
            m = re.search(r"\\(chapter|section|subsection)(\*?)\{((?:[^{}]|\{[^{}]*\})*)\}", code)
            if m:
                flush()
                if not m.group(2):
                    lvl = ["chapter", "section", "subsection"].index(m.group(1))
                    ctr[lvl] += 1
                    for k in range(lvl + 1, 3): ctr[k] = 0
                    pcount = 0
                    title = clean(m.group(3))
                continue
            b = re.search(r"\\begin\{(enumerate|itemize)\}(\[[^]]*\])?", code)
            if b:
                flush(); stack.append(0); code = code[b.end():]
                if not code.strip(): continue
            if re.search(r"\\end\{(enumerate|itemize)\}", code):
                flush(); stack and stack.pop(); continue
            if "\\item" in code and stack:
                flush(); stack[-1] += 1; start = i
                code = code.split("\\item", 1)[1]
            if not code.strip():
                flush(); continue
            if not buf: start = i
            buf.append(code)
        flush()
    with open(out, "w", newline="", encoding="utf-8") as h:
        w = csv.writer(h)
        w.writerow(["req_id", "level", "section", "requirement", "source", "compliant", "evidence"])
        w.writerows(rows)
    print(f"{len(rows)} requirement(s) -> {out}")

if __name__ == "__main__":
    main()
