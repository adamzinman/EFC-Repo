#!/usr/bin/env python3
"""Mechanical checks for the Controls Standard. Prints ONLY failures.

Usage: python3 scripts/lint.py [files...] [--only refs,norm,terms,secrets,items,todo,chktex]
Run from the repo root. With no files, checks chapters/*.tex and main.tex.
Lines ending in '% lint-ok' are skipped. Exit code 1 if any failure.
"""
import csv, glob, os, re, shutil, subprocess, sys

ALL = ["refs", "norm", "terms", "secrets", "items", "todo", "chktex"]
out = []

def fail(f, n, code, msg):
    out.append(f"{f}:{n}: [{code}] {msg}")

def strip_comment(line):
    return re.sub(r"(?<!\\)%.*", "", line)

def load(files):
    data = {}
    for f in files:
        with open(f, encoding="utf-8", errors="replace") as h:
            data[f] = [l.rstrip("\n") for l in h]
    return data

def lines(data):
    for f, ls in data.items():
        for i, raw in enumerate(ls, 1):
            if raw.rstrip().endswith("% lint-ok"):
                continue
            yield f, i, strip_comment(raw)

def check_refs(data, all_data):
    labels = {}
    for f, i, l in lines(all_data):
        for lab in re.findall(r"\\label\{([^}]+)\}", l):
            labels.setdefault(lab, []).append((f, i))
    for lab, locs in labels.items():
        if len(locs) > 1 and any(f in data for f, _ in locs):
            f, i = locs[1]
            fail(f, i, "dup-label", f"'{lab}' also at {locs[0][0]}:{locs[0][1]}")
    for f, i, l in lines(data):
        for cmd, keys in re.findall(r"\\(ref|autoref|cref|Cref|pageref|nameref)\{([^}]+)\}", l):
            for k in keys.split(","):
                if k.strip() not in labels:
                    fail(f, i, "undef-ref", f"\\{cmd}{{{k.strip()}}} has no \\label")
        if re.search(r"\b(?:[Ss]ection|[Cc]hapter|[Tt]able)\s+\d+(\.\d+)*\b", l):
            fail(f, i, "hard-ref", "hand-written section/table number; use \\ref")

NORM = [
    (r"\bmust\b", "use 'shall'"),
    (r"\b(has|have) to\b", "use 'shall'"),
    (r"\bneeds? to\b", "use 'shall'"),
    (r"\b(is|are) required to\b", "use 'shall'"),
    (r"\bSHALL\b|\bSHOULD\b", "lowercase normative keywords"),
    (r"\b(appropriate|adequate|as needed|as required|sufficient)\b", "vague; make it verifiable"),
]
def check_norm(data):
    for f, i, l in lines(data):
        for pat, msg in NORM:
            m = re.search(pat, l)
            if m:
                fail(f, i, "norm", f"'{m.group(0)}': {msg}")

def check_terms(data):
    if not os.path.exists("glossary.txt"):
        return
    rules = []
    for row in open("glossary.txt", encoding="utf-8"):
        if row.startswith("#") or "|" not in row:
            continue
        parts = [p.strip() for p in row.split("|")]
        pref = parts[0]
        av = parts[1] if len(parts) > 1 else ""
        av = re.sub(r"^avoid:\s*", "", av)
        for a in [x.strip() for x in av.split(",") if x.strip()]:
            rules.append((re.compile(r"\b" + re.escape(a) + r"\b", re.I), a, pref))
    for f, i, l in lines(data):
        for rx, a, pref in rules:
            if rx.search(l):
                fail(f, i, "term", f"'{a}' -> use '{pref}'")

SECRETS = [
    (r"\b(password|passwd|pwd|passcode|api[_ ]?key|secret|token)\s*[:=]", "possible credential"),
    (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "IP address; add '% lint-ok' if it is a placeholder"),
]
def check_secrets(data):
    for f, i, l in lines(data):
        for pat, msg in SECRETS:
            if re.search(pat, l, re.I):
                fail(f, i, "secret", msg)

def check_items(data):
    reg = {}
    if os.path.exists("open-items.csv"):
        with open("open-items.csv", encoding="utf-8") as h:
            for r in csv.DictReader(h):
                reg[r.get("id", "").strip()] = r.get("status", "").strip().lower()
    for f, i, l in lines(data):
        for oid in re.findall(r"\\openitem\{([^}]+)\}", l):
            if oid not in reg:
                fail(f, i, "item", f"{oid} not in open-items.csv")
            elif reg[oid] == "closed":
                fail(f, i, "item", f"{oid} is closed; remove the \\openitem")
        if re.search(r"\\textcolor\{orange\}", l) and "\\newcommand" not in l:
            fail(f, i, "item", "raw orange note; convert to \\openitem{OI-NNN}{...}")

def check_todo(data):
    for f, i, l in lines(data):
        if re.search(r"\b(TODO|FIXME|TBD|XXX)\b", l):
            fail(f, i, "todo", "unresolved marker")

def check_chktex(data):
    if not shutil.which("chktex"):
        return
    for f in data:
        r = subprocess.run(["chktex", "-q", "-v0", "-n1", "-n8", "-n24", "-n36", f],
                           capture_output=True, text=True)
        for row in r.stdout.splitlines():
            if row.strip():
                out.append(f"{row} [chktex]")

def main():
    args = sys.argv[1:]
    only = ALL
    if "--only" in args:
        k = args.index("--only")
        only = args[k + 1].split(",")
        del args[k:k + 2]
    every = sorted(glob.glob("chapters/*.tex")) + (["main.tex"] if os.path.exists("main.tex") else [])
    files = args or every
    if not files:
        print("no .tex files found"); return 2
    data = load(files)
    all_data = load(sorted(set(every) | set(files)))
    for c in only:
        if c == "refs": check_refs(data, all_data)
        else: globals()["check_" + c](data)
    for o in out:
        print(o)
    print(f"{len(out)} failure(s) in {len(files)} file(s)")
    return 1 if out else 0

if __name__ == "__main__":
    sys.exit(main())
