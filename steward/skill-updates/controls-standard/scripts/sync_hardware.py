#!/usr/bin/env python3
"""Compare part numbers in the standard (\\pn{...}) with the hardware spreadsheet.
Prints ONLY differences.

Usage: python3 scripts/sync_hardware.py [sheet.xlsx|.csv] [--column "Part Number"] [--both]
Defaults come from config.json keys hardware_sheet / hardware_column.
--both also lists sheet parts that the standard never mentions.
"""
import csv, glob, re, sys
from _cfg import cfg

norm = lambda s: re.sub(r"\s+", "", str(s)).upper()

def sheet_parts(path, col):
    rows = []
    if path.lower().endswith((".xlsx", ".xlsm")):
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        for ws in wb.worksheets:
            it = ws.iter_rows(values_only=True)
            for hdr in it:
                if hdr and any(h and col.lower() in str(h).lower() for h in hdr):
                    k = next(i for i, h in enumerate(hdr) if h and col.lower() in str(h).lower())
                    rows += [r[k] for r in it if r and k < len(r) and r[k]]
                    break
    else:
        with open(path, encoding="utf-8-sig") as h:
            r = csv.DictReader(h)
            k = next((f for f in r.fieldnames if col.lower() in f.lower()), None)
            if k is None:
                sys.exit(f"no column like '{col}' in {path}")
            rows = [x[k] for x in r if x[k]]
    return {norm(p): str(p).strip() for p in rows}

def main():
    args, c = sys.argv[1:], cfg()
    both = "--both" in args
    args = [x for x in args if x != "--both"]
    col = c.get("hardware_column", "Part Number")
    if "--column" in args:
        k = args.index("--column"); col = args[k + 1]; del args[k:k + 2]
    sheet = args[0] if args else c.get("hardware_sheet")
    if not sheet:
        print("no spreadsheet given (arg or config.json hardware_sheet)"); return 2
    approved = sheet_parts(sheet, col)
    used = {}
    for f in sorted(glob.glob("chapters/*.tex")):
        for i, l in enumerate(open(f, encoding="utf-8", errors="replace"), 1):
            for p in re.findall(r"\\pn\{([^}]+)\}", l):
                used.setdefault(norm(p), (p, f"{f}:{i}"))
    n = 0
    for k, (p, loc) in sorted(used.items()):
        if k not in approved:
            print(f"{loc}: [hw] {p} not in approved list"); n += 1
    if both:
        for k in sorted(set(approved) - set(used)):
            print(f"[hw] {approved[k]} approved but not mentioned in standard"); n += 1
    print(f"{n} difference(s); {len(used)} part(s) in doc, {len(approved)} in sheet")
    return 1 if n else 0

if __name__ == "__main__":
    sys.exit(main())
