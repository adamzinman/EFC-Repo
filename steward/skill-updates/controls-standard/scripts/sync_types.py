#!/usr/bin/env python3
"""Compare type tables in the standard with real type exports. Prints ONLY differences.

Doc side: put '% sync-type: DDT_Device' on the line before a tabular/longtable.
Rows are 'Member & Type & ...'; header rows (Member/Name/Element) and rules are skipped.
Source side (paths from args or config.json keys types_plc / types_ignition):
  Control Expert DDT exports (.xdd/.xsy/.xml, DDTSource/variables elements)
  Ignition UDT exports (.json, tagType "UdtType")
Usage: python3 scripts/sync_types.py [--plc files...] [--ignition files...] [tex files...]
Ignition types are compared by member name only (type names differ by platform).
"""
import glob, json, re, sys, xml.etree.ElementTree as ET
from _cfg import cfg, clean

def doc_types(files):
    out = {}
    for f in files:
        ls = open(f, encoding="utf-8", errors="replace").read().splitlines()
        i = 0
        while i < len(ls):
            m = re.search(r"%\s*sync-type:\s*(\S+)", ls[i])
            if not m:
                i += 1; continue
            name, rows, j = m.group(1), {}, i + 1
            while j < len(ls) and not re.search(r"\\end\{(tabular|longtable|tabularx)", ls[j]):
                line = re.sub(r"\\(hline|toprule|midrule|bottomrule|endhead|endfirsthead)", "", ls[j])
                if "&" in line:
                    cells = [clean(c) for c in line.split("\\\\")[0].split("&")]
                    if cells[0] and cells[0].lower() not in ("member", "name", "element", "field"):
                        rows[cells[0]] = cells[1] if len(cells) > 1 else ""
                j += 1
            out[name] = (rows, f"{f}:{i+1}")
            i = j
    return out

def plc_types(files):
    out = {}
    for f in files:
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError as e:
            print(f"{f}: cannot parse ({e})"); continue
        for d in root.iter():
            if d.tag.split("}")[-1] != "DDTSource":
                continue
            st = next((c for c in d if c.tag.split("}")[-1] == "structure"), None)
            if st is None:
                continue
            out[d.get("DDTName")] = {v.get("name"): v.get("typeName", "")
                                     for v in st if v.tag.split("}")[-1] == "variables"}
    return out

def ign_types(files):
    out = {}
    def walk(n):
        if isinstance(n, dict):
            if n.get("tagType") == "UdtType":
                out[n.get("name")] = {t.get("name"): t.get("dataType", "")
                                      for t in n.get("tags", [])}
            for t in n.get("tags", []):
                walk(t)
        elif isinstance(n, list):
            for t in n: walk(t)
    for f in files:
        walk(json.load(open(f, encoding="utf-8")))
    return out

def compare(doc, src, label, check_type):
    n = 0
    for name, (rows, loc) in sorted(doc.items()):
        if name not in src:
            continue
        real = src[name]
        for m in sorted(set(real) - set(rows)):
            print(f"{loc}: [{label}] {name}.{m} missing from doc (source type {real[m]})"); n += 1
        for m in sorted(set(rows) - set(real)):
            print(f"{loc}: [{label}] {name}.{m} in doc but not in source"); n += 1
        if check_type:
            for m in sorted(set(rows) & set(real)):
                if rows[m].upper() != real[m].upper():
                    print(f"{loc}: [{label}] {name}.{m} type doc={rows[m]} source={real[m]}"); n += 1
    for name in sorted(set(src) - set(doc)):
        print(f"[{label}] type {name} exists in source but has no sync-type table")
        n += 1
    return n

def main():
    a, mode = {"--plc": [], "--ignition": [], "tex": []}, "tex"
    for x in sys.argv[1:]:
        if x in a: mode = x
        else: a[mode].append(x)
    c = cfg()
    plc = a["--plc"] or (sorted(glob.glob(c["types_plc"], recursive=True)) if c.get("types_plc") else [])
    ign = a["--ignition"] or (sorted(glob.glob(c["types_ignition"], recursive=True)) if c.get("types_ignition") else [])
    tex = a["tex"] or sorted(glob.glob("chapters/*.tex"))
    if not plc and not ign:
        print("no type exports given (use --plc/--ignition or config.json)"); return 2
    doc = doc_types(tex)
    n = 0
    if plc: n += compare(doc, plc_types(plc), "plc", True)
    if ign: n += compare(doc, ign_types(ign), "ignition", False)
    print(f"{n} difference(s); {len(doc)} doc table(s) checked")
    return 1 if n else 0

if __name__ == "__main__":
    sys.exit(main())
