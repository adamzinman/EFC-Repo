#!/usr/bin/env python3
"""One line per chapter: status, lines, shall/should counts, open items, lint failures.
Usage: python3 scripts/status.py
"""
import glob, os, re, subprocess, sys

def index_status():
    st = {}
    if os.path.exists("INDEX.md"):
        for l in open("INDEX.md", encoding="utf-8"):
            m = re.match(r"##\s*(\S+\.tex)\s*\|.*\|\s*(\w[\w ]*?)\s*$", l)
            if m: st[m.group(1)] = m.group(2)
    return st

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    st = index_status()
    print(f"{'file':28} {'status':16} {'lines':>5} {'shall':>5} {'should':>6} {'OI':>3} {'lint':>4}")
    tot = [0, 0, 0, 0, 0]
    for f in sorted(glob.glob("chapters/*.tex")):
        src = open(f, encoding="utf-8", errors="replace").read()
        code = re.sub(r"(?<!\\)%.*", "", src)
        r = subprocess.run([sys.executable, os.path.join(here, "lint.py"), f,
                            "--only", "refs,norm,terms,secrets,items,todo"],
                           capture_output=True, text=True)
        lint = int(re.search(r"(\d+) failure", r.stdout).group(1)) if "failure" in r.stdout else 0
        v = [src.count("\n") + 1, len(re.findall(r"\bshall\b", code, re.I)),
             len(re.findall(r"\bshould\b", code, re.I)), code.count("\\openitem{"), lint]
        tot = [a + b for a, b in zip(tot, v)]
        b = os.path.basename(f)
        print(f"{b[:28]:28} {st.get(b, '?')[:16]:16} {v[0]:>5} {v[1]:>5} {v[2]:>6} {v[3]:>3} {v[4]:>4}")
    print(f"{'TOTAL':28} {'':16} {tot[0]:>5} {tot[1]:>5} {tot[2]:>6} {tot[3]:>3} {tot[4]:>4}")

if __name__ == "__main__":
    main()
