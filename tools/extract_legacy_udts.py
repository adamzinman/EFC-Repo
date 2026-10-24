#!/usr/bin/env python3
"""Pull the legacy (pre-EFCLib v1) UDT definitions out of an Ignition tag export and write one importable
Tag Browser JSON per type into tags/legacy/.

    python3 -I tools/extract_legacy_udts.py <RGTCR_ignition_tags.json> [DDT_Valve DDT_Device ...]

The export this branch used is samples/xsy-import/RGTCR_ignition_tags.json at commit 0b91606 (a live-gateway
export of the RGTCR tag provider). With no type names, the default legacy set is extracted (LEGACY_TYPES).
Each output file is {"name": <type>, "tagType": "UdtType", ...} exactly as the gateway exported it (OPC item
paths with the {OPC Prefix}{Tag}.{TagName} convention and the UDT's parameters), so it imports into
Data Types unchanged. The docs/legacy-ddt-fork.md table and tools/check_bindings.py read these files.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tags", "legacy")
LEGACY_TYPES = ["DDT_Valve", "DDT_Device", "DDT_Process_Value", "DDT_Station", "MEM_Interlock_List"]


def find_types(node, path=""):
    out = []
    if node.get("tagType") == "UdtType":
        out.append((path, node))
    for c in node.get("tags", []):
        out.extend(find_types(c, path + "/" + node.get("name", "")))
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    export = json.load(open(sys.argv[1], encoding="utf-8"))
    want = sys.argv[2:] or LEGACY_TYPES
    by_name = {t["name"]: (p, t) for p, t in find_types(export)}
    os.makedirs(OUT, exist_ok=True)
    for name in want:
        if name not in by_name:
            sys.exit(f"{name}: not in {sys.argv[1]}")
        folder, t = by_name[name]
        p = os.path.join(OUT, f"{name}_UDT.json")
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(t, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        n = sum(1 for _ in walk(t))
        print(f"{name:22s} {n:3d} members  (export folder {folder or '/'}) -> {os.path.relpath(p, ROOT)}")


def walk(t):
    for c in t.get("tags", []):
        yield c
        if c.get("tagType") in ("Folder", "UdtInstance"):
            yield from walk(c)


if __name__ == "__main__":
    main()
