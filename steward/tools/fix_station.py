"""Rule: bind the Station faceplates (imported/, Designer-built) to EFCLib v1 T_Station and the dynamic-window scheme.
- DDT_Station member names -> T_Station members (bindings, write scripts, command map)
- Station_Tile click -> efc.ui.openDynamic(self) (tType T_Station); Sidebar close -> efc.ui.closeDynamic(self)
- Station_Sidebar (moved to Docks/Station by build.py) sized 400 x 860 (decision 25)
Usage: python3 -I steward/tools/fix_station.py <viewtools dir> [apply]
"""
import json, re, sys
sys.path.insert(0, sys.argv[1])
from viewtools import Fixer

MAP = {"Active": "Sts_Active", "Complete": "Sts_Complete", "Deadband": "Prm_Deadband", "Disabled": "Sts_Disabled",
       "Failed": "Sts_Failed", "Filling": "Sts_Filling", "GrossWeight": "Val_Gross", "HMI_Reset": "Cmd_Reset",
       "HMI_Select": "Cmd_Select", "InletCMD": "Out_InletCmd", "InletREQ": "Sts_InletReq", "Msg": "Sts_Msg",
       "NetWeight": "Val_Net", "PT": "Val_PT", "PT_Diff": "Val_PTDiff", "PT_Valid": "Inp_PTValid",
       "Press_Balanced": "Sts_PressBalanced", "Press_Max": "Prm_MaxPress", "ReadyToFill": "Sts_ReadyToFill",
       "ReadyToStart": "Sts_ReadyToStart", "Recovering": "Sts_Recovering", "SampleCMD": "Out_SampleCmd",
       "SamplePress": "Prm_PrefillPress", "SampleREQ": "Sts_SampleReq", "SampleWeight": "Prm_SampleWt",
       "ScaleName": "Cfg_ScaleName", "Selected": "Sts_Selected", "StationName": "Cfg_Desc", "StatusEnum": "Sts_State",
       "TareCMD": "Cmd_Tare", "TareWeight": "Val_Tare", "TargetWeight": "Prm_TargetWt", "TotalWeight": "Val_Total",
       "Units": "Cfg_EU", "VacuumCMD": "Out_VacuumCmd", "VacuumREQ": "Sts_VacuumReq", "Vacuumed": "Sts_Vacuumed",
       "Vacuuming": "Sts_Vacuuming", "Venting": "Sts_Venting", "Vessel_Present": "Inp_VesselPresent", "ZeroCMD": "Cmd_Zero"}
NAMES = "|".join(sorted(MAP, key=len, reverse=True))
DW_PARAMS = {"tType": "T_Station", "dockId": "", "dwTagPath": ""}

def fix(view, ctx):
    before = json.dumps(view, sort_keys=True)
    t = json.dumps(view)
    t = re.sub(r"\{0\}/(%s)(?![A-Za-z_])" % NAMES, lambda m: "{0}/" + MAP[m.group(1)], t)              # tag bindings
    t = re.sub(r'\\"/(%s)\\"' % NAMES, lambda m: '\\"/' + MAP[m.group(1)] + '\\"', t)                 # "/Member" in scripts
    t = re.sub(r'(\{\\"Tare\\": \\")TareCMD(\\", \\"Zero\\": \\")ZeroCMD(\\", \\"Reset\\": \\")HMI_Reset', r"\1Cmd_Tare\2Cmd_Zero\3Cmd_Reset", t)
    t = re.sub(r'system\.perspective\.openDock\(\\"StationSidebar\\"[^)]*\)', "efc.ui.openDynamic(self)", t)
    t = re.sub(r'system\.perspective\.closeDock\(\\"[A-Za-z_]*\\"\)', "efc.ui.closeDynamic(self)", t)
    v = json.loads(t)
    if "efc.ui.openDynamic" in t:                        # the view that opens the window needs the dynamic-window params
        for k, d in DW_PARAMS.items():
            v.setdefault("params", {}).setdefault(k, d)
            v.setdefault("propConfig", {}).setdefault(f"params.{k}", {"paramDirection": "input", "persistent": True})
    if "efc.ui.closeDynamic" in t:                       # the sidebar is the dw_Station dynamic window
        v.setdefault("props", {})["defaultSize"] = {"width": 400, "height": 860}
    view.clear(); view.update(v)
    return json.dumps(view, sort_keys=True) != before

apply = len(sys.argv) > 2 and sys.argv[2] == "apply"
Fixer(root="imported", select="Templates/Station", apply=apply, backup=False).run(fix)
