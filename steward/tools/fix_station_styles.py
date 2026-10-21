"""Rule: EFC_Styles classes only - move the Station views' static inline styles into generated classes
Station/<view>/<component> (identical styles share one class), written into imported/EFC_StationFaceplates.
Usage: python3 -I steward/tools/fix_station_styles.py <viewtools dir> [apply]
"""
import os, sys
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "generator"))
from viewtools import Fixer
from common import extract_inline, write_classes

import json, glob
SC = "imported/EFC_StationFaceplates/com.inductiveautomation.perspective/style-classes/"
CLASSES = {f[len(SC):-len("/style.json")]: json.load(open(f))["base"]["style"]       # existing ones: reuse, never overwrite
           for f in glob.glob(SC + "Station/**/style.json", recursive=True)}
N0 = len(CLASSES)
apply = len(sys.argv) > 2 and sys.argv[2] == "apply"
fx = Fixer(root="imported", select="Templates/Station", apply=apply, backup=False)
NAMES = [str(rel).replace("\\", "/").rstrip("/").rsplit("/", 1)[-1] for _, rel, _ in fx.views()]   # run() visits in this order

def fix(view, ctx):
    before = str(view)
    extract_inline(view, "Station/" + NAMES.pop(0).replace("Station_", ""), CLASSES)
    return str(view) != before

fx.run(fix)
print(f"{len(CLASSES) - N0} new style classes")
if apply:
    write_classes("imported/EFC_StationFaceplates", CLASSES, "fix_station_styles.py")
