# PCLib additions marked NEEDS UPDATE (2026-10-19)
#
# Paste into gen_pclib.py after the T("DiaComp", ...) block from gen_pclib_DiaComp.patch,
# and add the two ROLE entries below to the role table. Re-run gen_pclib.py.
#
# These types are added AS THE TEMPLATES USE THEM TODAY so the dynamic windows have a type to
# bind to. They do not follow PCLib conventions yet (no Cfg_/Inp_/Sts_ prefixes, no T_Mode,
# no T_Alarm members, toggle commands instead of one-shots). Every description starts with
# [NEEDS UPDATE]; don't build new PLC logic on them until they are converted.
#
# Role table entries:
#     "Station": ("Equipment module [NEEDS UPDATE]", "-", [S88, S101]),
#     "Heater":  ("Control module [NEEDS UPDATE]", "MonBinDrv", [S88, S101]),

T("Station", "[NEEDS UPDATE] Fill station (scale + fill sequence). Copied from DDT_Station; member names unchanged", [
    M("StationName", "STRING[20]", "Station name, e.g. Station 1"),
    M("ScaleName", "STRING[20]", "Scale tag, e.g. WT101"),
    M("Units", "STRING[8]", "Weight units text"),
    M("StatusEnum", "INT", "Station status / sequence step"),
    M("Msg", "STRING[40]", "Status message"),
    M("Selected", "BOOL", "Station selected"),
    M("Active", "BOOL", "Fill cycle active"),
    M("Disabled", "BOOL", "Station disabled"),
    M("Filling", "BOOL", "Filling"),
    M("Complete", "BOOL", "Fill complete"),
    M("Failed", "BOOL", "Fill failed"),
    M("Recovering", "BOOL", "Recovering"),
    M("Venting", "BOOL", "Venting"),
    M("Vacuuming", "BOOL", "Vacuum in progress"),
    M("Vacuumed", "BOOL", "Vacuum complete"),
    M("Vessel_Present", "BOOL", "Vessel present"),
    M("ReadyToStart", "BOOL", "Ready to start"),
    M("ReadyToFill", "BOOL", "Ready to fill"),
    M("Press_Balanced", "BOOL", "Pressure balanced"),
    M("PT_Valid", "BOOL", "Pressure transmitter valid"),
    M("NetWeight", "REAL", "Net weight"),
    M("GrossWeight", "REAL", "Gross weight"),
    M("TareWeight", "REAL", "Tare weight"),
    M("TotalWeight", "REAL", "Total weight"),
    M("TargetWeight", "REAL", "Target net weight (setpoint)"),
    M("SampleWeight", "REAL", "Sample weight (setpoint)"),
    M("Deadband", "REAL", "Weight deadband"),
    M("PT", "REAL", "Vessel pressure"),
    M("PT_Diff", "REAL", "Pressure difference"),
    M("Press_Max", "REAL", "Maximum pressure (setpoint)"),
    M("SamplePress", "REAL", "Sample / prefill pressure (setpoint)"),
    M("InletREQ", "BOOL", "Inlet valve requested"),
    M("InletCMD", "BOOL", "Inlet valve command"),
    M("SampleREQ", "BOOL", "Sample valve requested"),
    M("SampleCMD", "BOOL", "Sample valve command"),
    M("VacuumREQ", "BOOL", "Vacuum valve requested"),
    M("VacuumCMD", "BOOL", "Vacuum valve command"),
    M("TareCMD", "BOOL", "Tare command (HMI pulse)"),
    M("ZeroCMD", "BOOL", "Zero command (HMI pulse)"),
    M("HMI_Reset", "BOOL", "Reset command (HMI pulse)"),
    M("HMI_Select", "BOOL", "Select command (HMI pulse)"),
], "Process")

T("Heater", "[NEEDS UPDATE] Electric heater. Members are the ones Templates/HeatTransfer/Heater_Electric reads today (PID_Motor demo UDT)", [
    M("Name", "STRING[20]", "Tag text"),
    M("Description", "STRING[40]", "Description"),
    M("Run", "BOOL", "Heater on (contactor feedback)"),
    M("Cmd", "BOOL", "On command (HMI toggles)"),
    M("Fault", "BOOL", "Heater fault"),
    M("Mode", "INT", "Mode, as the template reads it today"),
    M("Intlk", "BOOL", "Interlock active"),
    M("PermOK", "BOOL", "Start permissive OK"),
], "Rotating")
