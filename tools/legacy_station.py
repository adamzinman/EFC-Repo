#!/usr/bin/env python3
"""Rebind the Designer-built Station faceplates (imported/EFC_StationFaceplates) from EFCLib v1 T_Station back to
the legacy DDT_Station members: the exact inverse of steward/tools/fix_station.py, driven by the same table
(generator/legacy_types.py STATION, T_Station member -> DDT_Station member).

build.py applies legacy_view() to every Station view while merging the library in the legacy-ddt build, so
imported/ stays the Designer export and the switch is the same one the generators use. The CLI rewrites files:

    python3 tools/legacy_station.py imported/EFC_StationFaceplates [apply]      # dry run lists the changes

What changes in each view.json:
  {0}/<T_ member>            indirect tag bindings           -> {0}/<DDT_ member>
  "/<T_ member>"             tag paths built in scripts      -> "/<DDT_ member>"
  {"Tare": "Cmd_Tare", ...}  the confirm-dialog command map  -> TareCMD / ZeroCMD / HMI_Reset
  params.tType "T_Station"   dynamic-window type             -> "DDT_Station"
The command pulses (write 1, then 0 after 1 s) and the efc.ui.openDynamic / closeDynamic calls are left as they are:
HMI_Select, HMI_Reset, TareCMD and ZeroCMD were pulsed the same way in the original DDT_Station faceplates.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "generator"))
from legacy_types import STATION                      # T_Station member -> DDT_Station member

NAMES = "|".join(sorted(STATION, key=len, reverse=True))


def legacy_text(t):
    """Apply the inverse mapping to the JSON text of a view (keeps the Designer's formatting outside the matches)."""
    t = re.sub(r"\{0\}/(%s)(?![A-Za-z_])" % NAMES, lambda m: "{0}/" + STATION[m.group(1)], t)               # tag bindings
    t = re.sub(r'\\"/(%s)\\"' % NAMES, lambda m: '\\"/' + STATION[m.group(1)] + '\\"', t)                  # "/Member" in scripts
    t = re.sub(r'(\{\\"Tare\\": \\")Cmd_Tare(\\", \\"Zero\\": \\")Cmd_Zero(\\", \\"Reset\\": \\")Cmd_Reset',
               r"\1TareCMD\2ZeroCMD\3HMI_Reset", t)                                                        # confirm-dialog command map
    t = t.replace('"tType": "T_Station"', '"tType": "DDT_Station"')
    return t


def legacy_view(view):
    """In-place on a parsed view dict (build.py). Returns True when something changed."""
    before = json.dumps(view, sort_keys=True)
    v = json.loads(legacy_text(json.dumps(view)))
    view.clear(); view.update(v)
    return json.dumps(view, sort_keys=True) != before


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    root, apply = sys.argv[1], len(sys.argv) > 2 and sys.argv[2] == "apply"
    n = 0
    for d, _, fs in os.walk(root):
        if "view.json" not in fs or "/Station" not in d.replace(os.sep, "/"):
            continue
        p = os.path.join(d, "view.json")
        old = open(p, encoding="utf-8").read()
        new = legacy_text(old)
        if new == old:
            continue
        n += 1
        changed = sorted(set(re.findall(r"\{0\}/([A-Za-z_]+)", new)) - set(re.findall(r"\{0\}/([A-Za-z_]+)", old)))
        print(("rewrote " if apply else "would rewrite ") + os.path.relpath(p, ROOT) + ": " + ", ".join(changed))
        if apply:
            open(p, "w", encoding="utf-8", newline="\n").write(new)
    print(f"{n} view(s) {'rewritten' if apply else 'would change'}")


if __name__ == "__main__":
    main()
