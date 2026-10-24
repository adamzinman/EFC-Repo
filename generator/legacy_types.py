"""
Legacy (pre-EFCLib v1) type switch for the generators: bind every template and dynamic window to the OLD UDT set
(DDT_Valve, DDT_Device, DDT_Process_Value, DDT_Station, MEM_Interlock_List and the library's own PID_ControlValve /
PID_Loop) instead of the EFCLib v1 T_ types. The view paths stay the same, so a project can switch between the two
builds without re-wiring its screens.

Switch (first match wins):
  1. environment EFC_LEGACY_DDT=1 / 0      (build.py --legacy-ddt sets it)
  2. VERSION.json  "types": "legacy-ddt"   (committed on the claude/legacy-ddt-fork branch so plain `python3 build.py`
                                             and CI build the legacy-bound library there)
  otherwise the EFCLib v1 T_ build.

The MAPS below are the T_ member -> legacy member tables, one per device class, with the source of each mapping.
They are documentation AND code: the generators import the few names they need from here, and
`python3 generator/legacy_types.py --table` prints the markdown tables in docs/legacy-ddt-fork.md.
A legacy member of None means "no equivalent" - the generator hides or drops that element (listed in the docs).
Reference UDT definitions: tags/legacy/*.json (extracted from a live RGTCR tag export, see tools/extract_legacy_udts.py).
"""
import json, os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _enabled():
    env = os.environ.get("EFC_LEGACY_DDT")
    if env is not None:
        return env.strip().lower() not in ("", "0", "false", "no", "off")
    try:
        return json.load(open(os.path.join(REPO, "VERSION.json"))).get("types") == "legacy-ddt"
    except (OSError, ValueError):
        return False


ENABLED = _enabled()

# Template / window tType -> legacy type name (what the views' tType param and efc.ui.BY_TYPE use in the legacy build)
TTYPE = {"T_DValve": "DDT_Valve", "T_CValve": "PID_ControlValve", "T_Motor": "DDT_Device", "T_VFD": "DDT_Device",
         "T_Heater": "DDT_Device", "T_AI": "DDT_Process_Value", "T_KPI": "DDT_Process_Value", "T_PID": "PID_Loop",
         "T_Station": "DDT_Station", "T_HeatEx": None, "native": "native"}

# Sources quoted in the tables
S_PID = "generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39)"
S_DFB = "DFB_Device.XDB v0.28 ladder (types/dfb/_reference at 7cb7e30) + DDT_Device v0.09 in the RGTCR XSY export"
S_PV = "generator/build_pv.py before e710de8 (DDT_Process_Value bindings)"
S_FIX = "steward/tools/fix_station.py MAP, inverted"
S_LOOP = "generator/pid_loops/generate_loops.py before 8e719f8 (PID_Loop UDT)"
S_KPI = "T_KPI card members read as DDT_Process_Value (same members as the PV templates)"
S_UDT = "tags/legacy UDT definition (live RGTCR export)"
S_NONE = "no legacy member"

# (T_ member, legacy member or None, note, source)
MAPS = {
 "DDT_Valve (T_DValve: Valve_Solenoid, Valve_OnOff_Pneumatic, Valve_MOV, dw_ValveDiscrete)": [
    ("Cfg_Tag", "Name", "memory member, defaults to the {Tag} parameter", S_PID),
    ("Cfg_Desc", "Description", "", S_PID),
    ("Out_Open", "CMD", "open command to the field", S_PID),
    ("Sts_Opened", "ZSO", "open limit", S_PID),
    ("Sts_Closed", "ZSC", "closed limit", S_PID),
    ("Sts_Opening / Sts_Closing", "CMD && !ZSO / !CMD && !ZSC", "derived; the window banner uses it", S_PID),
    ("Sts_Fault", "ZSO && ZSC", "derived (both limits made); no fault bit on DDT_Valve", S_PID),
    ("Cfg_HasZSO / Cfg_HasZSC / Inp_ZSO / Inp_ZSC", "Feedback_Enabled / ZSO / ZSC", "one feedback flag covers both limits", S_PID),
    ("Mode/Sts_Auto", "Auto", "", S_PID),
    ("Mode/Sts_Man", "Manual", "", S_PID),
    ("Mode/Sts_OOS", "Off", "", S_PID),
    ("Mode/Sts_Maint", None, "no maintenance mode; LockedOut is the 4th legacy mode (shown as LOCKOUT)", S_NONE),
    ("Sts_Avail", "!LockedOut", "derived", S_PID),
    ("Sts_Local", None, "no local/remote on DDT_Valve", S_NONE),
    ("Sts_Intlk", "Interlock", "", S_PID),
    ("Sts_NotPerm", "Permissive", "TRUE = permissive missing (as the pre-switch template read it)", S_PID),
    ("Intlk/* (T_Intlk)", "InterlockList (MEM_Interlock_List)", "document {InterlockName[], Used[], Description[], Status[]}; names of the used entries", S_PID),
    ("Intlk/Sts_FirstOut, Intlk/Cfg_CondDesc/n", "InterlockList.Used[n], .InterlockName[n], .Description[n]", "tooltip and legacy IntlkList part; Status[] polarity undocumented, not bound", S_PID),
    ("Perm/* (T_Intlk)", None, "only the Permissive bit exists; list dropped", S_NONE),
    ("Cmd_Open / Cmd_Close", "HMI_CMD = TRUE / FALSE", "level, not one-shot (DFB resets it on mode change)", S_PID),
    ("Mode/Cmd_Auto / Cmd_Man / Cmd_OOS", "HMI_Auto / HMI_Manual / HMI_Off (1 s pulse)", "rising-edge contacts in the DFB; efc.ui.pulse", S_DFB),
    ("Mode/Cmd_Maint", "HMI_Lockout (1 s pulse)", "window button LOCKOUT (Maintenance+)", S_DFB),
    ("Cmd_Reset", None, "no device reset; dropped", S_NONE),
    ("Alm_* (T_Alarm members)", None, "legacy alarms are Ignition tag alarms, not members; Alarms section dropped", S_NONE),
    ("Run/Val_RunHrs ... Run/Cmd_ResetMaint, Sim_En", "Cycle_Count, Reset_Count", "Counters section: cycle count + RESET COUNT", S_UDT),
    ("Cfg_TravelTime, Sts_NE107", None, "dropped", S_NONE),
    ("(not bound)", "REQ, Auto_Perm, Man_Perm", "automation request and per-mode permissives (equal in the DFB)", S_UDT),
 ],
 "DDT_Device (T_Motor / T_VFD / T_Heater: Rotating/*, HX_AirCooled, Heater_Electric, dw_Rotating, dw_VFD, dw_Heater)": [
    ("Cfg_Tag", "Name", "", S_UDT),
    ("Cfg_Desc", "Description", "", S_UDT),
    ("Out_Run / Out_Contactor", "CMD", "", S_DFB),
    ("Sts_Running / Sts_On", "YI", "run feedback (the DFB counts runtime while YI)", S_DFB),
    ("Sts_Stopped / Sts_Off", "!YI", "derived", S_DFB),
    ("Sts_Starting / Sts_Stopping", "CMD && !YI / !CMD && YI", "derived", S_PID),
    ("Cfg_NoFbk", "!FB_Enb", "feedback enabled flag", S_UDT),
    ("Sts_Fault", "Alarm", "device alarm bit", S_UDT),
    ("Sts_Tripped", None, "YIF exists on DDT_Device but its meaning is not documented anywhere in the repo; not bound (GUESS avoided)", S_NONE),
    ("Mode/Sts_Auto / Sts_Man / Sts_OOS", "Auto / Manual / Off", "", S_DFB),
    ("Mode/Sts_Maint", None, "LockedOut shown as LOCKOUT instead", S_NONE),
    ("Sts_Avail", "!LockedOut", "derived", S_PID),
    ("Sts_Local", None, "", S_NONE),
    ("Sts_Intlk", "Interlock", "", S_UDT),
    ("Sts_NotPerm", "!(Manual ? Man_Perm : Auto_Perm)", "in DFB_Device v0.28 both perms are !Estop && !Interlock, so P lights with I", S_DFB),
    ("Perm/*, Intlk/* (T_Intlk)", None, "no interlock list on DDT_Device; chips only", S_NONE),
    ("Cmd_Start / Cmd_Stop / Cmd_On / Cmd_Off", "HMI_CMD = TRUE / FALSE", "level; CMD := HMI_CMD && Manual && Man_Perm", S_DFB),
    ("Mode/Cmd_Auto / Cmd_Man / Cmd_OOS / Cmd_Maint", "HMI_Auto / HMI_Manual / HMI_Off / HMI_Lockout (1 s pulse)", "", S_DFB),
    ("Cmd_Reset, Cmd_Jog", None, "dropped", S_NONE),
    ("Val_Current, Val_LoadPct, Cfg_RatedAmps, Val_Spd, Val_SpdRef, Cmd_Spd, Cmd_Rev, Val_Torque, Val_Power", None, "no electrical / drive data on DDT_Device; VFD and heater windows show the DDT_Device data", S_NONE),
    ("Run/Val_RunHrs", "Runtime (Run_Hour + Run_Min/60)", "", S_DFB),
    ("Run/Cmd_ResetMaint", "Reset_Runtime (one-shot, DFB clears it)", "", S_DFB),
    ("Run/Val_Starts, Run/Val_StartsLastHr, Run/Sts_MaintDue, Sim_En", None, "dropped", S_NONE),
    ("Alm_* (T_Alarm members)", "Warning (chip only)", "Alarms section dropped", S_NONE),
    ("Cfg_* (configuration)", "FB_Enb, Enable_Stalling, Comp_Ratio, Stall_Time", "compressor stall detection; Curr_Comp_Ratio and Stalled shown", S_UDT),
    ("(not bound)", "YIF, REQ, Run_Sec, Run_Min", "", S_UDT),
 ],
 "PID_ControlValve (T_CValve: Valve_Control, dw_ValveAnalog) - library UDT, no plant DDT_ for analog valves": [
    ("Cfg_Tag / Cfg_Desc", "Name / Description", "", S_PID),
    ("Val_Demand", "Out", "", S_PID),
    ("Val_Pos", "Pos", "", S_PID),
    ("Cfg_HasFbk", "Feedback_Enabled", "", S_PID),
    ("Sts_Fault", "Fault", "", S_PID),
    ("Sts_Intlk", "Intlk", "", S_PID),
    ("Sts_NotPerm", "!PermOK", "", S_PID),
    ("Mode/Sts_Man", "Mode = 1", "library convention (pre-switch motor template: mode 1 = Manual)", S_PID),
    ("Mode/Sts_Auto", "Mode = 0", "", S_PID),
    ("Cmd_ManPos", "Out (write, Manual only)", "window entry and presets write Out", S_LOOP),
    ("Mode/Cmd_Man / Cmd_Auto", "Mode := 1 / 0", "", S_PID),
    ("Sts_Closed / Sts_RateLim / Sts_Sim / Val_Dev / Val_Travel / Val_Reversals / Alm_* / Cfg_* / Cmd_Reset", None, "dropped (deviation shown as Out - Pos)", S_NONE),
 ],
 "DDT_Process_Value (T_AI: PV_StatusStrip, PV_RangeBar, dw_ProcessValue; T_KPI: AnalogIndicator/*)": [
    ("Val_PV", "PV", "", S_PV),
    ("Cfg_Tag / Cfg_Desc / Cfg_EU", "Name / Description / Units", "memory members", S_PV),
    ("Cfg_EUMin / Cfg_EUMax", "Eng_Min / Eng_Max", "", S_PV),
    ("Cfg_RawMin / Cfg_RawMax", "Raw_Min / Raw_Max", "", S_UDT),
    ("Sts_Bad", "HW_Fault", "", S_PV),
    ("Sts_ORng / Sts_URng", "Overrange / Underrange", "", S_PV),
    ("Alm_HH|H|L|LL/Cfg_Lim", "HH|H|L|LL/SP", "", S_PV),
    ("Alm_x/Sts_Suppressed", "x/Inhibit", "", S_PV),
    ("Alm_x/Cfg_En", "x/Enabled", "", S_UDT),
    ("Alm_x/Sts_Active", "x/Alarm", "", S_PV),
    ("Alm_x/Sts_Unack, Alm_x/Cfg_Priority, Alm_Bad", "Ignition tag alarms on x/Alarm, HW_Fault, Overrange, Underrange", "PV templates query system.alarm.queryStatus (pre-switch script); KPI cards: unack false, priority Medium", S_PV),
    ("Alm_x/Cfg_DB (deadband), on-delay", "x/DB, x/DLY", "shown and editable (Engineer) in dw_ProcessValue", S_UDT),
    ("Val_PVPct", "(PV - Eng_Min) / (Eng_Max - Eng_Min)", "derived", S_PV),
    ("Cfg_ShortDesc", "Description", "", S_KPI),
    ("Cfg_IdealLo / Cfg_IdealHi", None, "no ideal band; KPI cards show the alarm zones only", S_NONE),
    ("Sts_Quality", "HW_Fault ? 2 : 0", "derived (2 = bad)", S_KPI),
    ("Val_ROC, Alm_ROC, Sts_NE107, Sim_En, Sim_PV, Cfg_FiltTC, Cfg_LoCutoff, Cfg_SqrtExtract, Sts_Sim, Sts_Subst", None, "dropped", S_NONE),
    ("(not bound)", "x/Notification, x/Default, Type, Edits", "", S_UDT),
 ],
 "PID_Loop (T_PID: Loops/Loop_B1..B4, dw_Loop) - library UDT, no plant DDT_ loop type": [
    ("Val_PV / Val_SP / Out_CV", "PV / SP / OUT", "", S_LOOP),
    ("Sts_Mode (0 Man 1 Auto 2 Cas)", "Mode (0 MAN 1 AUTO 2 CAS)", "", S_LOOP),
    ("Sts_Man / Sts_Auto / Sts_Cas", "Mode = 0 / 1 / 2", "derived", S_LOOP),
    ("Cmd_Man / Cmd_Auto / Cmd_Cas", "Mode := 0 / 1 / 2", "", S_LOOP),
    ("Cmd_SP / Cmd_CV", "SP / OUT (bidirectional)", "", S_LOOP),
    ("Cfg_PVEU / Cfg_PVMin / Cfg_PVMax", "PV.engUnit / PV.engLow / PV.engHigh", "tag properties of the PV member", S_LOOP),
    ("Alm_DevH/Cfg_Lim, Alm_DevL/Cfg_Lim", "AlmHi, AlmLo (absolute limits), AlmDev", "cards: alarm = PV >= AlmHi or PV <= AlmLo", S_LOOP),
    ("Alm_DevH/Sts_Active, Alm_DevL/Sts_Active", "PV >= AlmHi, PV <= AlmLo", "derived", S_LOOP),
    ("Cfg_Kp / Cfg_Ti / Cfg_Td / Cfg_DirectAct", "Kp / Ti / Td / Action (0 reverse 1 direct)", "Ti, Td in seconds (no TIME scaling)", S_LOOP),
    ("Cfg_SPMin / Cfg_SPMax / Cfg_CVMin / Cfg_CVMax", "SP_Lo / SP_Hi / OUT_Lo / OUT_Hi", "", S_LOOP),
    ("Cfg_Desc", "Description", "", S_LOOP),
    ("Val_Err", "PV - SP", "derived", S_LOOP),
    ("Sts_Intlk, Sts_Track, Sts_WindupHi/Lo, Sts_SPRamping, Cfg_DB, Cfg_SPRate, Cfg_CVRate, Alm_PVBad, Intlk/*", None, "dropped", S_NONE),
 ],
 "DDT_Station (T_Station: Station_Tile, Station_Fill, dw_Station) - imported Designer views, mapped at build time by tools/legacy_station.py": [
    ("Sts_Active", "Active", "", S_FIX), ("Sts_Complete", "Complete", "", S_FIX), ("Prm_Deadband", "Deadband", "", S_FIX),
    ("Sts_Disabled", "Disabled", "", S_FIX), ("Sts_Failed", "Failed", "", S_FIX), ("Sts_Filling", "Filling", "", S_FIX),
    ("Val_Gross", "GrossWeight", "", S_FIX), ("Cmd_Reset", "HMI_Reset", "1 s pulse", S_FIX), ("Cmd_Select", "HMI_Select", "1 s pulse", S_FIX),
    ("Out_InletCmd", "InletCMD", "", S_FIX), ("Sts_InletReq", "InletREQ", "", S_FIX), ("Sts_Msg", "Msg", "", S_FIX),
    ("Val_Net", "NetWeight", "", S_FIX), ("Val_PT", "PT", "", S_FIX), ("Val_PTDiff", "PT_Diff", "", S_FIX), ("Inp_PTValid", "PT_Valid", "", S_FIX),
    ("Sts_PressBalanced", "Press_Balanced", "", S_FIX), ("Prm_MaxPress", "Press_Max", "", S_FIX), ("Sts_ReadyToFill", "ReadyToFill", "", S_FIX),
    ("Sts_ReadyToStart", "ReadyToStart", "", S_FIX), ("Sts_Recovering", "Recovering", "", S_FIX), ("Out_SampleCmd", "SampleCMD", "", S_FIX),
    ("Prm_PrefillPress", "SamplePress", "", S_FIX), ("Sts_SampleReq", "SampleREQ", "", S_FIX), ("Prm_SampleWt", "SampleWeight", "", S_FIX),
    ("Cfg_ScaleName", "ScaleName", "", S_FIX), ("Sts_Selected", "Selected", "", S_FIX), ("Cfg_Desc", "StationName", "", S_FIX),
    ("Sts_State", "StatusEnum", "", S_FIX), ("Cmd_Tare", "TareCMD", "1 s pulse", S_FIX), ("Val_Tare", "TareWeight", "", S_FIX),
    ("Prm_TargetWt", "TargetWeight", "", S_FIX), ("Val_Total", "TotalWeight", "", S_FIX), ("Cfg_EU", "Units", "", S_FIX),
    ("Out_VacuumCmd", "VacuumCMD", "", S_FIX), ("Sts_VacuumReq", "VacuumREQ", "", S_FIX), ("Sts_Vacuumed", "Vacuumed", "", S_FIX),
    ("Sts_Vacuuming", "Vacuuming", "", S_FIX), ("Sts_Venting", "Venting", "", S_FIX), ("Inp_VesselPresent", "Vessel_Present", "", S_FIX),
    ("Cmd_Zero", "ZeroCMD", "", S_FIX),
 ],
 "T_HeatEx (dw_HeatTransfer) - no legacy type": [
    ("every member", None, "no DDT_ carries heat-exchanger calculations; the window is a placeholder that names the tag", S_NONE),
 ],
 "Native x80 DDTs (Templates/IO/*, dw_IOCard)": [
    ("(unchanged)", "(unchanged)", "the I/O faceplates bind the Control Expert x80 device DDTs, not T_ types", "build.py IMPORTED_PARTS"),
 ],
}

# Inverse of steward/tools/fix_station.py MAP (T_Station member -> DDT_Station member), consumed by tools/legacy_station.py
STATION = {t: d for cls, rows in MAPS.items() if cls.startswith("DDT_Station") for t, d, _, _ in rows}


def table():
    out = []
    for cls, rows in MAPS.items():
        n_map = sum(1 for _, d, _, _ in rows if d and not str(d).startswith("("))
        n_drop = sum(1 for _, d, _, _ in rows if d is None)
        out.append(f"### {cls}\n\n{n_map} rows mapped, {n_drop} rows with no legacy equivalent.\n")
        out.append("| T_ member | Legacy member | Note | Source |\n|---|---|---|---|")
        for t, d, note, src in rows:
            out.append(f"| `{t}` | {('`' + d + '`') if d else '-'} | {note} | {src} |")
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    if "--table" in sys.argv:
        print(table())
    else:
        print("legacy-ddt build:", ENABLED)
