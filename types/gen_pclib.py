"""
PCLib - Process Control DDT library generator for Schneider EcoStruxure Control Expert.

Single source of truth for every DDT. Running this script produces:
  xdd/PCLib_All.xdd        all DDTs, dependency-ordered (import this one)
  xdd/<Type>.xdd           one file per DDT (import its dependencies first)
  export/PCLib_CE_V16.2.xdd     Control Expert Classic V16.2 import file (all DDTs)
  export/PCLib_Ignition81.json  Ignition 8.1 UDT definitions (Tag Browser > Data Types > Import)
  PCLib_Members.csv        flat member list (Type, ISA88Role, MTP, Member, DataType, Init, Comment)
  README.md                conventions + member reference for every type

Usage:
  python gen_pclib.py                 # default prefix T_, LREAL totals
  python gen_pclib.py --prefix DDT_   # different type-name prefix
  python gen_pclib.py --no-lreal      # replace LREAL with REAL (older CPUs)
"""
import argparse
import csv
import json
import datetime as dt
import os
import re
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

LIB_VERSION = "1.00"

# ---------------------------------------------------------------------------
# Member helper.  M(name, type, comment, init)
# Types written as "@Name" are library DDTs; "@" is replaced by the prefix.
# ---------------------------------------------------------------------------
def M(name, typ, comment, init=None):
    return (name, typ, comment, init)


HDR = [
    M("Cfg_Tag", "STRING[20]", "Equipment / instrument tag, e.g. FT-101"),
    M("Cfg_Desc", "STRING[40]", "Description shown on HMI faceplate"),
]

SIM = [M("Sim_En", "BOOL", "Simulation: ignore field I/O, logic generates feedback")]

# ISA-18.2 / IEC 62682 alarm state model (states A-H of the standard's state diagram)
ALARM_STATES = ("0=A Normal 1=B Unack 2=C Acked 3=D RTN-Unack 4=E Latched "
                "5=F Shelved 6=G Suppressed-by-design 7=H Out-of-service")

ALARM_CORE = [
    M("Inp_Cond", "BOOL", "Raw alarm condition (written by owner logic)"),
    M("Inp_Suppress", "BOOL", "Suppressed-by-design: state-based suppression by logic (ISA-18.2 state G)"),
    M("Cfg_En", "BOOL", "Alarm configured (FALSE = not an alarm, e.g. instrument not fitted)", "TRUE"),
    M("Cfg_Latch", "BOOL", "Latching alarm: active until Cmd_Reset after RTN (ISA-18.2 state E)"),
    M("Cfg_NoAck", "BOOL", "No acknowledge required - use only for alarms rationalised as such"),
    M("Cfg_OnDly", "TIME", "On-delay (ISA-18.2 chattering control)", "T#0S"),
    M("Cfg_OffDly", "TIME", "Off-delay (ISA-18.2 chattering control)", "T#0S"),
    M("Cfg_Priority", "INT", "Rationalised priority: 1=Emergency 2=High 3=Medium 4=Low", "3"),
    M("Cfg_Class", "INT", "Alarm class (alarm philosophy): 0=General 1=Safety 2=Environmental 3=Quality 4=Asset", "0"),
    M("Cfg_MaxShelf", "TIME", "Maximum shelve duration (shelving must be time-limited)", "T#8H"),
    M("Cmd_Ack", "BOOL", "Operator acknowledge (one-shot)"),
    M("Cmd_Reset", "BOOL", "Reset latched alarm (one-shot)"),
    M("Cmd_Shelve", "BOOL", "Operator shelve (one-shot)"),
    M("Cmd_Unshelve", "BOOL", "Operator unshelve (one-shot)"),
    M("Cmd_RemoveSvc", "BOOL", "Remove from service for maintenance (one-shot, permit required)"),
    M("Cmd_ReturnSvc", "BOOL", "Return to service (one-shot)"),
    M("Sts_Active", "BOOL", "Alarm active (after delays and latch)"),
    M("Sts_Unack", "BOOL", "Alarm unacknowledged"),
    M("Sts_Shelved", "BOOL", "Shelved by operator (ISA-18.2 state F)"),
    M("Sts_Suppressed", "BOOL", "Suppressed by design (ISA-18.2 state G)"),
    M("Sts_OOS", "BOOL", "Out of service (ISA-18.2 state H)"),
    M("Sts_State", "INT", ALARM_STATES),
    M("Sts_ShelfLeft", "TIME", "Shelve time remaining"),
    M("Val_Count", "UDINT", "Activation counter (alarm performance KPIs)"),
    M("Val_LastActive", "DT", "Date/time of last activation"),
    M("Val_LastRTN", "DT", "Date/time of last return to normal"),
]

# NAMUR NE107 diagnostic status (also used by VDI/VDE/NAMUR 2658 / MTP)
NE107_TXT = "0=Good 1=Failure (F) 2=Function check (C) 3=Out of specification (S) 4=Maintenance required (M)"
NE107_STS = [M("Sts_NE107", "INT", "NAMUR NE107 status: " + NE107_TXT)]
NE107_FULL = [M("Inp_NE107", "INT", "NE107 status reported by smart device (HART / fieldbus)", "0")] + NE107_STS

# ISA-88 equipment (physical) state - site-defined per the standard; these are the common ones
EQSTATE = "0=Available-clean 1=In use 2=Dirty 3=Cleaning (CIP) 4=Sterilising (SIP) 5=Maintenance 6=Out of service"

# ISA-88 Part 1 example procedural state model and commands
PHASE_STATES = ("0=Idle 1=Running 2=Complete 3=Pausing 4=Paused 5=Holding 6=Held "
                "7=Restarting 8=Stopping 9=Stopped 10=Aborting 11=Aborted")
PHASE_CMDS = "1=Start 2=Stop 3=Hold 4=Restart 5=Abort 6=Reset 7=Pause 8=Resume"


def A(name, comment):            # discrete alarm member
    return M(name, "@Alarm", comment)


def AL(name, comment):           # limit alarm member
    return M(name, "@AlmLim", comment)


# Shared motor members (used by Motor and VFD)
MOTOR_INPUTS = [
    M("Inp_RunFbk", "BOOL", "Run feedback (contactor aux / drive running)"),
    M("Inp_Remote", "BOOL", "Local/Remote switch in REMOTE"),
    M("Inp_AvailOK", "BOOL", "MCC available: breaker closed, control power OK"),
    M("Inp_EStopOK", "BOOL", "Field E-stop circuit healthy"),
    M("Inp_IntlkOK", "BOOL", "Interlocks healthy (TRUE = may run; FALSE trips)"),
    M("Inp_PermOK", "BOOL", "Permissives healthy (TRUE = may start)"),
    M("Inp_IOFault", "BOOL", "I/O channel or comms fault"),
]
MOTOR_CFG = [
    M("Cfg_FbkTime", "TIME", "Time allowed for run feedback after start/stop", "T#5S"),
    M("Cfg_RestartDly", "TIME", "Minimum stopped time before restart", "T#0S"),
    M("Cfg_NoFbk", "BOOL", "No run feedback wired (feedback follows output)"),
    M("Cfg_AutoRestart", "BOOL", "Auto mode restarts after power loss / interlock clears"),
    M("Cfg_RatedAmps", "REAL", "Motor nameplate full-load current (A)", "0.0"),
    M("Cfg_MaxStartsHr", "INT", "Maximum starts per hour, 0 = no limit", "0"),
]
MOTOR_CMDS = [
    M("Cmd_Start", "BOOL", "Operator start (one-shot)"),
    M("Cmd_Stop", "BOOL", "Operator stop (one-shot)"),
    M("Cmd_Reset", "BOOL", "Fault / trip reset (one-shot)"),
    M("Cmd_Jog", "BOOL", "Maintenance jog (maintained, Maint mode only)"),
    M("Prog_Start", "BOOL", "Program / sequence start request (Auto mode)"),
    M("Prog_Stop", "BOOL", "Program / sequence stop request (Auto mode)"),
]
MOTOR_STS = [
    M("Sts_Running", "BOOL", "Running (feedback confirmed)"),
    M("Sts_Stopped", "BOOL", "Stopped (feedback confirmed)"),
    M("Sts_Starting", "BOOL", "Start commanded, waiting for feedback"),
    M("Sts_Stopping", "BOOL", "Stop commanded, waiting for feedback"),
    M("Sts_Avail", "BOOL", "Available to Auto/program control"),
    M("Sts_Ready", "BOOL", "Ready to start now (all permissives, no trip)"),
    M("Sts_Intlk", "BOOL", "Interlock not healthy"),
    M("Sts_NotPerm", "BOOL", "Permissive not healthy"),
    M("Sts_Local", "BOOL", "In local control"),
    M("Sts_Tripped", "BOOL", "Tripped - reset required"),
    M("Sts_Fault", "BOOL", "Any fault present"),
    M("Sts_Sim", "BOOL", "Simulation active"),
    M("Sts_State", "INT", "0=Stopped 1=Starting 2=Running 3=Stopping 4=Tripped 5=Not available"),
    M("Sts_RestartLeft", "TIME", "Restart-delay time remaining"),
] + NE107_STS
MOTOR_ALM = [
    A("Alm_FailStart", "No run feedback within Cfg_FbkTime"),
    A("Alm_FailStop", "Run feedback still present after stop"),
    A("Alm_Uncmd", "Running without a command"),
    A("Alm_EStop", "E-stop activated"),
    A("Alm_IntlkTrip", "Tripped by interlock"),
    A("Alm_ExcessStarts", "Start blocked: Cfg_MaxStartsHr exceeded"),
]

# ---------------------------------------------------------------------------
# Type definitions, in dependency order.  (name, comment, members)
# ---------------------------------------------------------------------------
TYPES = []


def T(name, comment, members, group):
    TYPES.append((name, comment, members, group))


# Standards metadata per type: (ISA-88 role, MTP data-assembly equivalent, standards)
S88 = "ISA-88 / IEC 61512-1"
S182 = "ISA-18.2 / IEC 62682"
MTP = "VDI/VDE/NAMUR 2658-4 (MTP)"
NE43 = "NAMUR NE43"
NE107 = "NAMUR NE107"
S51 = "ISA-5.1"
S101 = "ISA-101.01"
S84 = "ISA-84 / IEC 61511 (BPCS layer only)"
DEVICE = [S88, S51, S182, S101, NE107, MTP]
META = {
    "Alarm":      ("Support (alarm object)", "Alarm/Warning/Tolerance limit attributes", [S182, S101]),
    "AlmLim":     ("Support (alarm object)", "e.g. VAHLim / VAHEn / VAHAct", [S182, S101]),
    "Mode":       ("Support (mode + ownership)", "OpMode (Offline/Operator/Automatic) + SrcMode", [S88, MTP]),
    "RunTime":    ("Support (asset data)", "-", [NE107 + " (feeds Maintenance required)"]),
    "AI":         ("Control module", "AnaMon", DEVICE + [NE43]),
    "DI":         ("Control module", "BinMon", DEVICE),
    "DValve":     ("Control module", "MonBinVlv", DEVICE),
    "CValve":     ("Control module", "MonAnaVlv", DEVICE),
    "Motor":      ("Control module", "MonBinDrv", DEVICE),
    "VFD":        ("Control module", "MonAnaDrv", DEVICE),
    "Heater":     ("Control module", "MonBinDrv (on/off) / MonAnaDrv (SSR, SCR)", DEVICE + ["IEC 60947-4-3 (semiconductor controllers, non-motor loads)", "NFPA 86 (excess-temperature limit)"]),
    "PID":        ("Control module", "PIDCtrl", [S88, S51, S182, S101, MTP]),
    "PumpProt":   ("Control module", "-", [S88, S182, S101]),
    "PumpDS":     ("Equipment module", "-", [S88, S182, S101]),
    "Agitator":   ("Equipment module", "MonAnaDrv (drive)", [S88, S182, S101]),
    "Compressor": ("Equipment module", "MonAnaDrv (drive)", [S88, S182, S101]),
    "Conveyor":   ("Equipment module", "MonBinDrv (drive)", [S88, S182, S101]),
    "Tank":       ("Equipment module / Unit vessel", "-", [S88, S51, S182, S101]),
    "Totalizer":  ("Control module", "-", [S88, S51, S182, S101]),
    "HeatEx":     ("Control module (monitoring)", "-", [S88, S182, S101]),
    "DosePump":   ("Equipment module", "MonAnaDrv (drive)", [S88, S182, S101]),
    "Analyzer":   ("Control module", "AnaMon", DEVICE),
    "GasDet":     ("Control module", "AnaMon", DEVICE + [NE43, S84]),
    "Station":    ("Equipment module", "-", [S88, S182, S101, NE107]),
    "IOCard":     ("Support (diagnostics)", "-", [NE107, S182, S101]),
    "IORack":     ("Support (diagnostics)", "-", [NE107, S182, S101]),
    "Intlk":      ("Support (interlock group)", "LockView16", [S84, S182, S101, MTP]),
    "ESD":        ("Support (shutdown group)", "-", [S84, S182, S101]),
    "Phase":      ("Equipment phase (procedural)", "Service (state machine)", [S88 + " Part 1 state model", MTP]),
    "Unit":       ("Unit (physical)", "-", [S88, S182, S101]),
}


# ---------------- Common building blocks ----------------
T("Alarm", "Discrete alarm, ISA-18.2 / IEC 62682 state model, shelving, suppression, out-of-service",
  ALARM_CORE, "Common")

T("AlmLim", "Analog limit alarm: limit + deadband + ISA-18.2 / IEC 62682 alarm", [
    M("Cfg_Lim", "REAL", "Alarm limit (EU) - from rationalisation / master alarm database", "0.0"),
    M("Cfg_DB", "REAL", "Deadband for return to normal (EU, ISA-18.2 chattering control)", "0.0"),
] + [  # limit alarms stay disabled until a rationalised limit is entered
    M(n, t, "Alarm enabled - set TRUE once Cfg_Lim is rationalised", None) if n == "Cfg_En" else (n, t, c, i)
    for n, t, c, i in ALARM_CORE
], "Common")

T("Mode", "Control-module mode and ISA-88 ownership (arbitration); maps to MTP OpMode", [
    M("Cmd_Auto", "BOOL", "Operator request Automatic (one-shot)"),
    M("Cmd_Man", "BOOL", "Operator request Manual (one-shot)"),
    M("Cmd_Maint", "BOOL", "Request Maintenance (one-shot)"),
    M("Cmd_OOS", "BOOL", "Request Out-of-Service (one-shot)"),
    M("Prog_Auto", "BOOL", "Owner request Automatic"),
    M("Prog_Man", "BOOL", "Owner request Manual"),
    M("Prog_Lock", "BOOL", "Owner locks current mode (operator cannot change)"),
    M("Prog_Acquire", "BOOL", "ISA-88 arbitration: owner (phase / EM) acquires this module"),
    M("Prog_Release", "BOOL", "ISA-88 arbitration: owner releases this module"),
    M("Inp_ReqOwnerID", "DINT", "ID of the phase / equipment module requesting ownership"),
    M("Cmd_ForceRelease", "BOOL", "Supervisor forces release of ownership (one-shot)"),
    M("Cfg_PowerUpMode", "INT", "Mode at cold start: 0=OOS 1=Maint 2=Man 3=Auto", "2"),
    M("Cfg_NoMaint", "BOOL", "Maintenance mode not allowed"),
    M("Sts_Auto", "BOOL", "In Automatic (commanded by owner) - MTP Automatic"),
    M("Sts_Man", "BOOL", "In Manual (commanded by operator) - MTP Operator"),
    M("Sts_Maint", "BOOL", "In Maintenance"),
    M("Sts_OOS", "BOOL", "Out of service - MTP Offline"),
    M("Sts_Mode", "INT", "0=OOS 1=Maint 2=Man 3=Auto  (MTP: 0=Offline 2=Operator 3=Automatic)"),
    M("Sts_Owned", "BOOL", "Acquired by an owner"),
    M("Val_OwnerID", "DINT", "ID of current owner, 0 = free"),
], "Common")

T("RunTime", "Run-hours, starts and maintenance counters", [
    M("Inp_Running", "BOOL", "Equipment running (from owner logic)"),
    M("Cfg_MaintHrs", "REAL", "Maintenance interval in run hours, 0 = off", "0.0"),
    M("Cmd_ResetMaint", "BOOL", "Reset hours-since-maintenance (one-shot)"),
    M("Cmd_ResetAll", "BOOL", "Reset all counters (one-shot, supervisor)"),
    M("Val_RunSecs", "UDINT", "Total run time (s) - master counter"),
    M("Val_RunHrs", "REAL", "Total run hours (display)"),
    M("Val_Starts", "UDINT", "Total starts / cycles"),
    M("Val_StartsLastHr", "INT", "Starts in the last 60 min (rolling)"),
    M("Val_LastRun", "TIME", "Duration of last run"),
    M("Val_HrsSinceMaint", "REAL", "Run hours since last maintenance reset"),
    M("Sts_MaintDue", "BOOL", "Maintenance due"),
], "Common")

# ---------------- Core ----------------
T("AI", "Analog input: scaling, filtering, NE43 range check, alarms, sim", HDR + [
    M("Cfg_EU", "STRING[12]", "Engineering units text"),
    M("Inp_Raw", "INT", "Raw counts from analog channel"),
    M("Inp_ChFault", "BOOL", "Channel / module diagnostic fault"),
    M("Cfg_RawMin", "INT", "Raw counts at 0% (M340/M580 4-20mA default 0)", "0"),
    M("Cfg_RawMax", "INT", "Raw counts at 100% (M340/M580 4-20mA default 10000)", "10000"),
    M("Cfg_EUMin", "REAL", "PV at 0% (EU)", "0.0"),
    M("Cfg_EUMax", "REAL", "PV at 100% (EU)", "100.0"),
    M("Cfg_FiltTC", "REAL", "1st-order filter time constant (s), 0 = off", "0.0"),
    M("Cfg_SqrtExtract", "BOOL", "Square-root extraction (DP flow)"),
    M("Cfg_LoCutoff", "REAL", "Low cutoff (% span): PV forced to EUMin below this, 0 = off", "0.0"),
    M("Cfg_BadLoPct", "REAL", "Bad below this % span (NE43 3.6mA = -2.5%)", "-2.5"),
    M("Cfg_BadHiPct", "REAL", "Bad above this % span (NE43 21mA = 106.25%)", "106.25"),
    M("Cfg_BadAction", "INT", "On bad PV: 0=Hold last good 1=Substitute 2=EUMin 3=EUMax", "0"),
    M("Cfg_SubstPV", "REAL", "Substitute PV used when Cfg_BadAction = 1", "0.0"),
    M("Sim_En", "BOOL", "Simulation enabled"),
    M("Sim_PV", "REAL", "Simulated PV (EU)", "0.0"),
    M("Val_PV", "REAL", "Process value (EU) - use this in logic"),
    M("Val_PVPct", "REAL", "Process value (% of span)"),
    M("Val_ROC", "REAL", "Rate of change (EU/s, 1 s window) - input to Alm_ROC"),
    M("Sts_Bad", "BOOL", "PV bad (out of range or channel fault)"),
    M("Sts_URng", "BOOL", "Under range"),
    M("Sts_ORng", "BOOL", "Over range"),
    M("Sts_Sim", "BOOL", "Simulation active"),
    M("Sts_Subst", "BOOL", "Substitute / held value in use"),
    M("Sts_Quality", "INT", "0=Good 1=Uncertain (simulation, NE107 C or S) 2=Bad"),
    *NE107_FULL,
    AL("Alm_HH", "High-high alarm"),
    AL("Alm_H", "High alarm"),
    AL("Alm_L", "Low alarm"),
    AL("Alm_LL", "Low-low alarm"),
    AL("Alm_ROC", "Rate-of-change alarm (Cfg_Lim in EU/s)"),
    A("Alm_Bad", "Bad PV alarm"),
], "Core")

T("DI", "Digital input: invert, debounce, sim, optional state alarm", HDR + [
    M("Inp_Raw", "BOOL", "Raw input from channel"),
    M("Inp_ChFault", "BOOL", "Channel / module diagnostic fault"),
    M("Cfg_Invert", "BOOL", "Invert raw signal (fail-safe NC contacts)"),
    M("Cfg_OnDly", "TIME", "Debounce on-delay", "T#0S"),
    M("Cfg_OffDly", "TIME", "Debounce off-delay", "T#0S"),
    M("Cfg_AlmMode", "INT", "0=No alarm 1=Alarm when Val TRUE 2=Alarm when Val FALSE", "0"),
    M("Cfg_TrueText", "STRING[16]", "HMI text for TRUE state, e.g. OPEN"),
    M("Cfg_FalseText", "STRING[16]", "HMI text for FALSE state, e.g. CLOSED"),
    M("Sim_En", "BOOL", "Simulation enabled"),
    M("Sim_Val", "BOOL", "Simulated value"),
    M("Val", "BOOL", "Conditioned value - use this in logic"),
    M("Sts_Bad", "BOOL", "Channel fault"),
    M("Sts_Sim", "BOOL", "Simulation active"),
    *NE107_STS,
    M("Val_Transitions", "UDINT", "Count of FALSE->TRUE transitions"),
    A("Alm", "State alarm (see Cfg_AlmMode)"),
    A("Alm_Bad", "Channel fault alarm"),
], "Core")

T("DValve", "On/off valve: single or dual solenoid, limit switches, travel alarms", HDR + [
    M("Mode", "@Mode", "Mode block"),
    M("Inp_ZSO", "BOOL", "Open limit switch"),
    M("Inp_ZSC", "BOOL", "Closed limit switch"),
    M("Inp_Remote", "BOOL", "Local/Remote switch in REMOTE (if fitted)"),
    M("Inp_IntlkOK", "BOOL", "Interlocks healthy (FALSE drives to interlock position)"),
    M("Inp_PermOK", "BOOL", "Permissives healthy (TRUE = may leave safe position)"),
    M("Inp_IOFault", "BOOL", "I/O channel or comms fault"),
    M("Cfg_HasZSO", "BOOL", "Open limit switch fitted", "TRUE"),
    M("Cfg_HasZSC", "BOOL", "Closed limit switch fitted", "TRUE"),
    M("Cfg_FailOpen", "BOOL", "Fail position: TRUE = fail open, FALSE = fail closed"),
    M("Cfg_IntlkOpen", "BOOL", "Interlock drives valve: TRUE = open, FALSE = closed"),
    M("Cfg_DualCoil", "BOOL", "Dual solenoid (uses Out_Open and Out_Close)"),
    M("Cfg_TravelTime", "TIME", "Maximum travel time before failure alarm", "T#10S"),
    M("Cmd_Open", "BOOL", "Operator open (one-shot)"),
    M("Cmd_Close", "BOOL", "Operator close (one-shot)"),
    M("Cmd_Reset", "BOOL", "Fault reset (one-shot)"),
    M("Prog_Open", "BOOL", "Program open request (Auto)"),
    M("Prog_Close", "BOOL", "Program close request (Auto)"),
    M("Out_Open", "BOOL", "Solenoid output: open (energise)"),
    M("Out_Close", "BOOL", "Solenoid output: close (dual-coil only)"),
] + SIM + [
    M("Sts_Opened", "BOOL", "Confirmed open"),
    M("Sts_Closed", "BOOL", "Confirmed closed"),
    M("Sts_Opening", "BOOL", "Travelling open"),
    M("Sts_Closing", "BOOL", "Travelling closed"),
    M("Sts_Avail", "BOOL", "Available to Auto/program control"),
    M("Sts_Intlk", "BOOL", "Interlock not healthy"),
    M("Sts_NotPerm", "BOOL", "Permissive not healthy"),
    M("Sts_Local", "BOOL", "In local control"),
    M("Sts_Fault", "BOOL", "Any fault present"),
    M("Sts_Sim", "BOOL", "Simulation active"),
    M("Sts_State", "INT", "0=Transit/unknown 1=Closed 2=Open 3=Opening 4=Closing 5=Fault"),
    *NE107_STS,
    A("Alm_FailOpen", "Failed to open within travel time"),
    A("Alm_FailClose", "Failed to close within travel time"),
    A("Alm_PosConflict", "Both limit switches made"),
    A("Alm_Uncmd", "Left commanded position without a command"),
    A("Alm_IntlkTrip", "Driven to safe position by interlock"),
    M("Run", "@RunTime", "Cycle counter (Val_Starts = operations)"),
], "Core")

T("CValve", "Modulating control valve: limits, rate limit, positioner feedback", HDR + [
    M("Mode", "@Mode", "Mode block"),
    M("Inp_PosFbk", "REAL", "Position feedback (%)"),
    M("Inp_FbkBad", "BOOL", "Feedback signal bad"),
    M("Inp_ZSC", "BOOL", "Closed limit switch (optional)"),
    M("Inp_IntlkOK", "BOOL", "Interlocks healthy (FALSE drives to Cfg_IntlkPos)"),
    M("Inp_IOFault", "BOOL", "I/O channel or comms fault"),
    M("Cfg_HasFbk", "BOOL", "Position feedback fitted"),
    M("Cfg_FailPos", "REAL", "Fail position (%): 0 = fail closed, 100 = fail open", "0.0"),
    M("Cfg_IntlkPos", "REAL", "Position driven to on interlock (%)", "0.0"),
    M("Cfg_OutMin", "REAL", "Minimum output (%)", "0.0"),
    M("Cfg_OutMax", "REAL", "Maximum output (%)", "100.0"),
    M("Cfg_RateUp", "REAL", "Opening rate limit (%/s), 0 = none", "0.0"),
    M("Cfg_RateDn", "REAL", "Closing rate limit (%/s), 0 = none", "0.0"),
    M("Cfg_TightShut", "REAL", "Demand below this (%) forces 0 for tight shut-off", "0.0"),
    M("Cfg_ReverseAct", "BOOL", "Reverse-acting output (100% signal = closed)"),
    M("Cfg_RawMin", "INT", "Analog output raw counts at 0%", "0"),
    M("Cfg_RawMax", "INT", "Analog output raw counts at 100%", "10000"),
    M("Cfg_DevLim", "REAL", "Position deviation alarm limit (%)", "5.0"),
    M("Cfg_DevTime", "TIME", "Deviation must persist this long", "T#15S"),
    M("Cmd_ManPos", "REAL", "Operator manual demand (%)", "0.0"),
    M("Cmd_Reset", "BOOL", "Fault reset (one-shot)"),
    M("Prog_Pos", "REAL", "Program / PID demand (%) - Auto mode", "0.0"),
    M("Out_CV", "REAL", "Output demand (%) after limits and rate limit"),
    M("Out_CVRaw", "INT", "Output in raw counts for AO channel"),
] + SIM + [
    M("Val_Demand", "REAL", "Active demand before rate limit (%)"),
    M("Val_Pos", "REAL", "Position (%) - feedback, or demand if no feedback"),
    M("Val_Dev", "REAL", "Demand minus position (%)"),
    M("Val_Travel", "REAL", "Accumulated travel (% of full stroke, summed) for diagnostics"),
    M("Val_Reversals", "UDINT", "Direction reversal count"),
    M("Sts_Closed", "BOOL", "Valve closed"),
    M("Sts_Intlk", "BOOL", "Interlock active"),
    M("Sts_RateLim", "BOOL", "Output is being rate limited"),
    M("Sts_Fault", "BOOL", "Any fault present"),
    M("Sts_Sim", "BOOL", "Simulation active"),
    *NE107_FULL,
    A("Alm_PosDev", "Position deviation"),
    A("Alm_FbkBad", "Feedback bad"),
    A("Alm_IntlkTrip", "Driven to interlock position"),
], "Core")

T("Motor", "Direct-on-line / star-delta / soft-start motor", HDR + [
    M("Mode", "@Mode", "Mode block"),
] + MOTOR_INPUTS + [
    M("Inp_OL", "BOOL", "Overload / motor protection relay tripped"),
    M("Inp_Current", "REAL", "Motor current (A), optional"),
] + MOTOR_CFG + MOTOR_CMDS + [
    M("Out_Run", "BOOL", "Run output to contactor / starter"),
] + SIM + MOTOR_STS + [
    M("Val_Current", "REAL", "Motor current (A)"),
    M("Val_LoadPct", "REAL", "Load (% of Cfg_RatedAmps)"),
] + MOTOR_ALM + [
    A("Alm_OL", "Overload trip"),
    AL("Alm_HiCurrent", "High current (A)"),
    M("Run", "@RunTime", "Run hours / starts"),
], "Core")

T("VFD", "Variable speed drive (fieldbus or hardwired)", HDR + [
    M("Mode", "@Mode", "Mode block"),
] + MOTOR_INPUTS + [
    M("Inp_DrvReady", "BOOL", "Drive ready"),
    M("Inp_DrvFault", "BOOL", "Drive faulted"),
    M("Inp_DrvWarn", "BOOL", "Drive warning / alarm"),
    M("Inp_FaultCode", "UINT", "Drive fault code"),
    M("Inp_CommOK", "BOOL", "Drive communications healthy", "TRUE"),
    NE107_FULL[0],
    M("Inp_SpdFbk", "REAL", "Speed feedback (Cfg_SpdEU)"),
    M("Inp_Current", "REAL", "Motor current (A)"),
    M("Inp_Torque", "REAL", "Motor torque (%)"),
    M("Inp_Power", "REAL", "Motor power (kW)"),
] + MOTOR_CFG + [
    M("Cfg_SpdEU", "STRING[8]", "Speed units text (%, Hz, rpm)"),
    M("Cfg_SpdMin", "REAL", "Minimum speed reference", "0.0"),
    M("Cfg_SpdMax", "REAL", "Maximum speed reference", "100.0"),
    M("Cfg_SpdDevLim", "REAL", "Speed deviation alarm limit", "5.0"),
    M("Cfg_SpdDevTime", "TIME", "Speed deviation delay", "T#20S"),
    M("Cfg_Reversible", "BOOL", "Reverse direction allowed"),
] + MOTOR_CMDS + [
    M("Cmd_Spd", "REAL", "Operator manual speed reference", "0.0"),
    M("Cmd_Rev", "BOOL", "Operator direction: TRUE = reverse"),
    M("Prog_Spd", "REAL", "Program / PID speed reference (Auto)", "0.0"),
    M("Prog_Rev", "BOOL", "Program direction: TRUE = reverse"),
    M("Out_Run", "BOOL", "Run command to drive"),
    M("Out_Rev", "BOOL", "Reverse command to drive"),
    M("Out_SpdRef", "REAL", "Speed reference to drive (limited)"),
    M("Out_FltReset", "BOOL", "Fault reset pulse to drive"),
] + SIM + MOTOR_STS + [
    M("Sts_AtSpd", "BOOL", "At speed (feedback within deviation limit)"),
    M("Sts_Rev", "BOOL", "Running in reverse"),
    M("Sts_CommFail", "BOOL", "Communication failure"),
    M("Val_SpdRef", "REAL", "Active speed reference"),
    M("Val_Spd", "REAL", "Speed"),
    M("Val_Current", "REAL", "Motor current (A)"),
    M("Val_Torque", "REAL", "Torque (%)"),
    M("Val_Power", "REAL", "Power (kW)"),
    M("Val_Energy", "LREAL", "Energy (kWh), integrated from power"),
] + MOTOR_ALM + [
    A("Alm_DrvFault", "Drive fault"),
    A("Alm_DrvWarn", "Drive warning"),
    A("Alm_CommFail", "Drive comms failure"),
    A("Alm_SpdDev", "Speed deviation"),
    M("Run", "@RunTime", "Run hours / starts"),
], "Core")

T("Heater", "Electric heater: on/off contactor, time-proportioned SSR, or SCR power controller", HDR + [
    M("Mode", "@Mode", "Mode block"),
    M("Inp_ContactorFbk", "BOOL", "Main / isolating contactor closed (aux contact)"),
    M("Inp_Remote", "BOOL", "Local/Remote switch in REMOTE"),
    M("Inp_AvailOK", "BOOL", "Supply available: breaker closed, control power OK"),
    M("Inp_HiLimitOK", "BOOL", "Independent excess-temperature limit healthy (hardwired, latching; PLC monitors only)"),
    M("Inp_IntlkOK", "BOOL", "Interlocks healthy (TRUE = may heat; FALSE trips)"),
    M("Inp_PermOK", "BOOL", "Permissives healthy (TRUE = may switch on)"),
    M("Inp_IOFault", "BOOL", "I/O channel or comms fault"),
    M("Inp_Current", "REAL", "Heater current from CT or SCR controller (A), optional"),
    M("Inp_ScrAlarm", "BOOL", "SCR controller alarm relay (fuse / partial load failure / overtemp)"),
    M("Cfg_CtrlType", "INT", "0 = on/off (contactor), 1 = time-proportioned SSR on a PLC output, 2 = SCR power controller (analog reference)", "0"),
    M("Cfg_CycleTime", "TIME", "Time-proportioning cycle (type 1): output is ON for Val_Duty % of each cycle", "T#4S"),
    M("Cfg_MinPulse", "TIME", "Shortest ON or OFF pulse (type 1); shorter pulses are skipped", "T#100MS"),
    M("Cfg_ScrFiring", "INT", "SCR firing mode set in the controller (type 2, documentation): 0 = burst / zero-cross, 1 = single-cycle, 2 = phase angle", "0"),
    M("Cfg_PwrMin", "REAL", "Minimum power demand when on (%)", "0.0"),
    M("Cfg_PwrMax", "REAL", "Maximum power demand (%)", "100.0"),
    M("Cfg_PwrRate", "REAL", "Power ramp limit (%/s), 0 = none (soft start for cold elements)", "0.0"),
    M("Cfg_RatedKW", "REAL", "Heater rated power at 100 % (kW)", "0.0"),
    M("Cfg_RatedAmps", "REAL", "Heater current at 100 % (A); 0 = no current monitoring", "0.0"),
    M("Cfg_LoadFailPct", "REAL", "Partial load failure: current below this % of expected while heating", "80.0"),
    M("Cfg_LeakAmps", "REAL", "Current above this while the output is off = SSR / SCR shorted (A)", "1.0"),
    M("Cfg_FbkTime", "TIME", "Time allowed for contactor feedback and current to settle", "T#3S"),
    M("Cmd_On", "BOOL", "Operator on (one-shot)"),
    M("Cmd_Off", "BOOL", "Operator off (one-shot)"),
    M("Cmd_Reset", "BOOL", "Fault / trip reset (one-shot)"),
    M("Cmd_Pwr", "REAL", "Operator power demand (%), Manual mode, types 1 and 2"),
    M("Prog_On", "BOOL", "Program / sequence on request (Auto mode)"),
    M("Prog_Off", "BOOL", "Program / sequence off request (Auto mode)"),
    M("Prog_Pwr", "REAL", "Program power demand (%), Auto mode, e.g. a T_PID Out_CV"),
    M("Out_Contactor", "BOOL", "Main / isolating contactor (opened on trip, high limit or shorted SSR)"),
    M("Out_SSR", "BOOL", "Time-proportioned output to the SSR (type 1)"),
    M("Out_PwrRef", "REAL", "Power reference to the SCR controller, 0-100 % (type 2)"),
] + SIM + [
    M("Sts_On", "BOOL", "On: contactor closed and enabled to heat"),
    M("Sts_Off", "BOOL", "Off"),
    M("Sts_Heating", "BOOL", "Output conducting now (on/off: on; SSR: inside the ON part of the cycle; SCR: reference > 0)"),
    M("Sts_Avail", "BOOL", "Available to Auto/program control"),
    M("Sts_Intlk", "BOOL", "Interlock not healthy"),
    M("Sts_NotPerm", "BOOL", "Permissive not healthy"),
    M("Sts_Local", "BOOL", "In local control"),
    M("Sts_HiLimit", "BOOL", "Excess-temperature limit tripped (reset at the limit device)"),
    M("Sts_LoadFail", "BOOL", "Partial load failure (element, fuse or phase lost)"),
    M("Sts_Shorted", "BOOL", "Current while output off: SSR / SCR failed shorted, contactor opened"),
    M("Sts_Tripped", "BOOL", "Tripped - reset required"),
    M("Sts_Fault", "BOOL", "Any fault present"),
    M("Sts_Sim", "BOOL", "Simulation active"),
    M("Sts_State", "INT", "0=Off 1=Switching on 2=On 3=Switching off 4=Tripped 5=Not available"),
] + NE107_STS + [
    M("Val_PwrDemand", "REAL", "Power demand after limits and ramp (%)"),
    M("Val_Duty", "REAL", "Applied duty / power (%): on/off 0 or 100, SSR ON-time fraction, SCR reference"),
    M("Val_Power", "REAL", "Estimated power (kW) = Val_Duty x Cfg_RatedKW, or from current"),
    M("Val_Current", "REAL", "Heater current (A)"),
    M("Val_LoadPct", "REAL", "Measured current as % of expected at the present duty"),
    M("Val_Energy", "LREAL", "Energy total (kWh)"),
    A("Alm_HiLimit", "Excess-temperature limit tripped"),
    A("Alm_Shorted", "SSR / SCR shorted - current with output off"),
    A("Alm_LoadFail", "Partial load failure"),
    A("Alm_FailOn", "No contactor feedback / current within Cfg_FbkTime"),
    A("Alm_FailOff", "Contactor feedback still present after off"),
    A("Alm_ScrFault", "SCR controller alarm"),
    A("Alm_IntlkTrip", "Tripped by interlock"),
    M("Run", "@RunTime", "On hours / switch-on count"),
], "Core")

T("PID", "PID loop wrapper (maps onto PIDFF EFB), Man/Auto/Cas, tracking", HDR + [
    M("Cfg_PVEU", "STRING[12]", "PV engineering units text"),
    M("Inp_PV", "REAL", "Process value (EU)"),
    M("Inp_PVBad", "BOOL", "PV bad quality"),
    M("Inp_CasSP", "REAL", "Cascade (remote) setpoint from master loop"),
    M("Inp_FF", "REAL", "Feed-forward input (% CV)"),
    M("Inp_TrackEn", "BOOL", "Output tracking enable"),
    M("Inp_TrackVal", "REAL", "Output tracking value (%)"),
    M("Inp_IntlkOK", "BOOL", "Interlocks healthy (FALSE forces Cfg_IntlkCV)"),
    M("Cmd_Man", "BOOL", "Operator request Manual (one-shot)"),
    M("Cmd_Auto", "BOOL", "Operator request Auto (one-shot)"),
    M("Cmd_Cas", "BOOL", "Operator request Cascade (one-shot)"),
    M("Cmd_SP", "REAL", "Operator setpoint (EU)", "0.0"),
    M("Cmd_CV", "REAL", "Operator manual output (%)", "0.0"),
    M("Prog_SP", "REAL", "Program setpoint (EU), used when Cfg_ProgSP", "0.0"),
    M("Cfg_ProgSP", "BOOL", "Setpoint owned by program instead of operator"),
    M("Cfg_Kp", "REAL", "Proportional gain", "1.0"),
    M("Cfg_Ti", "TIME", "Integral time, T#0S = no integral", "T#10S"),
    M("Cfg_Td", "TIME", "Derivative time", "T#0S"),
    M("Cfg_DirectAct", "BOOL", "TRUE = direct acting (CV rises with PV); FALSE = reverse"),
    M("Cfg_PVMin", "REAL", "PV range low (EU)", "0.0"),
    M("Cfg_PVMax", "REAL", "PV range high (EU)", "100.0"),
    M("Cfg_SPMin", "REAL", "Setpoint low limit (EU)", "0.0"),
    M("Cfg_SPMax", "REAL", "Setpoint high limit (EU)", "100.0"),
    M("Cfg_CVMin", "REAL", "Output low limit (%)", "0.0"),
    M("Cfg_CVMax", "REAL", "Output high limit (%)", "100.0"),
    M("Cfg_SPRate", "REAL", "Setpoint ramp rate (EU/s), 0 = step", "0.0"),
    M("Cfg_CVRate", "REAL", "Output rate limit (%/s), 0 = none", "0.0"),
    M("Cfg_DB", "REAL", "Error deadband (EU)", "0.0"),
    M("Cfg_FFGain", "REAL", "Feed-forward gain", "0.0"),
    M("Cfg_PVTrack", "BOOL", "Setpoint tracks PV while in Manual (bumpless)"),
    M("Cfg_IntlkCV", "REAL", "Output forced on interlock (%)", "0.0"),
    M("Cfg_BadPVAction", "INT", "On bad PV: 0=Hold CV 1=Go Manual 2=Go Cfg_IntlkCV", "1"),
    M("Out_CV", "REAL", "Controller output (%)"),
    M("Val_SP", "REAL", "Active setpoint after ramp and limits (EU)"),
    M("Val_SPTarget", "REAL", "Target setpoint before ramp (EU)"),
    M("Val_PV", "REAL", "Process value (EU)"),
    M("Val_Err", "REAL", "Error SP - PV (EU)"),
    M("Sts_Man", "BOOL", "In Manual"),
    M("Sts_Auto", "BOOL", "In Auto"),
    M("Sts_Cas", "BOOL", "In Cascade"),
    M("Sts_Track", "BOOL", "Output tracking"),
    M("Sts_Intlk", "BOOL", "Interlock active"),
    M("Sts_WindupHi", "BOOL", "Output at high limit"),
    M("Sts_WindupLo", "BOOL", "Output at low limit"),
    M("Sts_SPRamping", "BOOL", "Setpoint ramping"),
    M("Sts_Mode", "INT", "0=Man 1=Auto 2=Cas 3=Track 4=Intlk"),
    AL("Alm_DevH", "High deviation (PV - SP), EU"),
    AL("Alm_DevL", "Low deviation (SP - PV), EU"),
    A("Alm_PVBad", "PV bad"),
], "Core")

# ---------------- Rotating extras ----------------
T("PumpProt", "Pump protection layer: dry run, low flow, deadhead, seal, bearing", HDR + [
    M("Inp_Running", "BOOL", "Pump running (from Motor / VFD Sts_Running)"),
    M("Inp_SuctPress", "REAL", "Suction pressure (EU)"),
    M("Inp_DischPress", "REAL", "Discharge pressure (EU)"),
    M("Inp_Flow", "REAL", "Pump flow (EU)"),
    M("Inp_DryRun", "BOOL", "Dry-run switch / low level active"),
    M("Inp_SealLeak", "BOOL", "Seal leak / seal pot alarm"),
    M("Inp_BrgTemp", "REAL", "Bearing temperature (degC)"),
    M("Inp_Vib", "REAL", "Vibration (mm/s)"),
    M("Cfg_MinFlow", "REAL", "Minimum continuous flow (EU)", "0.0"),
    M("Cfg_MinFlowDly", "TIME", "Low-flow delay after start", "T#30S"),
    M("Cfg_DeadheadDP", "REAL", "Differential pressure indicating deadhead (EU)", "0.0"),
    M("Cfg_DryRunDly", "TIME", "Dry-run delay", "T#5S"),
    M("Cfg_TripDryRun", "BOOL", "Trip on dry run", "TRUE"),
    M("Cfg_TripLowFlow", "BOOL", "Trip on low flow"),
    M("Cfg_TripDeadhead", "BOOL", "Trip on deadhead", "TRUE"),
    M("Cfg_TripSeal", "BOOL", "Trip on seal leak"),
    M("Cmd_Reset", "BOOL", "Reset latched trips (one-shot)"),
    M("Out_IntlkOK", "BOOL", "Protections healthy - wire to Motor/VFD Inp_IntlkOK"),
    M("Val_DP", "REAL", "Differential pressure (EU)"),
    A("Alm_DryRun", "Dry run"),
    A("Alm_LowFlow", "Low flow (below minimum continuous flow)"),
    A("Alm_Deadhead", "Deadhead (high DP, no flow)"),
    A("Alm_SealLeak", "Seal leak"),
    AL("Alm_BrgTemp", "High bearing temperature"),
    AL("Alm_Vib", "High vibration"),
    AL("Alm_LoSuct", "Low suction pressure"),
], "Rotating")

T("PumpDS", "Duty/standby/lead-lag coordinator for up to 4 pumps", HDR + [
    M("Mode", "@Mode", "Mode block (Auto = Prog_NumReq, Man = Cmd_NumReq)"),
    M("Inp_Avail", "ARRAY[1..4] OF BOOL", "Pump n available (Motor Sts_Avail)"),
    M("Inp_Running", "ARRAY[1..4] OF BOOL", "Pump n running"),
    M("Inp_Fault", "ARRAY[1..4] OF BOOL", "Pump n faulted"),
    M("Inp_RunHrs", "ARRAY[1..4] OF REAL", "Pump n run hours (for equalisation)"),
    M("Cfg_NumPumps", "INT", "Number of pumps in group (1-4)", "2"),
    M("Cfg_Strategy", "INT", "Rotation: 0=Fixed lead 1=Rotate on stop 2=Equalise hours 3=Timed", "1"),
    M("Cfg_RotateHrs", "REAL", "Timed rotation interval (h)", "168.0"),
    M("Cfg_StageDly", "TIME", "Delay between staging pumps on/off", "T#10S"),
    M("Cfg_ChgOnFault", "BOOL", "Automatic changeover to standby on fault", "TRUE"),
    M("Cmd_NumReq", "INT", "Operator: number of pumps required (Manual)", "0"),
    M("Cmd_Lead", "INT", "Operator-selected lead pump (Fixed strategy)", "1"),
    M("Cmd_Rotate", "BOOL", "Force rotation now (one-shot)"),
    M("Prog_NumReq", "INT", "Program: number of pumps required (Auto)", "0"),
    M("Out_RunReq", "ARRAY[1..4] OF BOOL", "Run request to pump n (wire to Prog_Start)"),
    M("Sts_Order", "ARRAY[1..4] OF INT", "Rank of pump n: 1=Lead 2=Lag1 ..."),
    M("Sts_Lead", "INT", "Current lead pump"),
    M("Sts_NumRunning", "INT", "Pumps running"),
    M("Sts_NumAvail", "INT", "Pumps available"),
    M("Val_HrsToRotate", "REAL", "Hours until next timed rotation"),
    A("Alm_NoStandby", "No standby pump available"),
    A("Alm_NoneAvail", "Demand present but no pump available"),
    M("Sts_ChgOver", "BOOL", "Automatic changeover occurred (event, not an alarm - ISA-18.2)"),
    M("Val_ChgOverCount", "UDINT", "Automatic changeover counter"),
], "Rotating")

T("Agitator", "Agitator / mixer: VFD + submergence, seal and gearbox protection", [
    M("Drv", "@VFD", "Drive (fixed-speed agitators: ignore speed members)"),
    M("Inp_Level", "REAL", "Vessel level (EU)"),
    M("Inp_SealOK", "BOOL", "Seal / seal support system healthy"),
    M("Inp_GbxTemp", "REAL", "Gearbox oil temperature (degC)"),
    M("Inp_Vib", "REAL", "Vibration (mm/s)"),
    M("Cfg_MinLevel", "REAL", "Minimum level to run (impeller submergence)", "0.0"),
    M("Cfg_LvlHyst", "REAL", "Level hysteresis (EU)", "0.0"),
    M("Cfg_TripLowLvl", "BOOL", "Trip running agitator on low level", "TRUE"),
    M("Out_IntlkOK", "BOOL", "Wire to Drv.Inp_IntlkOK"),
    M("Out_PermOK", "BOOL", "Wire to Drv.Inp_PermOK"),
    M("Sts_LvlOK", "BOOL", "Level above minimum"),
    A("Alm_LowLvlRun", "Running / start requested below minimum level"),
    A("Alm_Seal", "Seal fault"),
    AL("Alm_GbxTemp", "High gearbox temperature"),
    AL("Alm_Vib", "High vibration"),
], "Rotating")

T("Compressor", "Compressor / blower: load-unload, anti-cycle, lube and thermal protection", [
    M("Drv", "@VFD", "Drive (fixed-speed: ignore speed members)"),
    M("Inp_SuctPress", "REAL", "Suction pressure (EU)"),
    M("Inp_DischPress", "REAL", "Discharge / header pressure (EU)"),
    M("Inp_DischTemp", "REAL", "Discharge temperature (degC)"),
    M("Inp_OilPress", "REAL", "Lube oil pressure (EU)"),
    M("Inp_OilTemp", "REAL", "Lube oil temperature (degC)"),
    M("Inp_Vib", "REAL", "Vibration (mm/s)"),
    M("Inp_LoadFbk", "BOOL", "Loaded feedback (inlet valve open)"),
    M("Cfg_LoadPress", "REAL", "Load (cut-in) pressure", "0.0"),
    M("Cfg_UnloadPress", "REAL", "Unload (cut-out) pressure", "0.0"),
    M("Cfg_MinRun", "TIME", "Minimum run time", "T#5M"),
    M("Cfg_MinStop", "TIME", "Minimum stop time (anti-cycle)", "T#2M"),
    M("Cfg_IdleTime", "TIME", "Unloaded run time before auto stop", "T#10M"),
    M("Cfg_OilBypass", "TIME", "Low oil pressure bypass after start", "T#10S"),
    M("Out_Load", "BOOL", "Load solenoid / inlet valve"),
    M("Out_BlowOff", "BOOL", "Blow-off / recycle valve open"),
    M("Out_IntlkOK", "BOOL", "Wire to Drv.Inp_IntlkOK"),
    M("Sts_Loaded", "BOOL", "Loaded"),
    M("Sts_Idle", "BOOL", "Running unloaded"),
    M("Sts_AntiCycle", "BOOL", "Waiting on minimum stop time"),
    M("Sts_State", "INT", "0=Off 1=Starting 2=Unloaded 3=Loaded 4=Idle stop 5=Anti-cycle 6=Tripped"),
    M("Val_TimeToStart", "TIME", "Anti-cycle time remaining"),
    M("Val_PressRatio", "REAL", "Compression ratio (absolute)"),
    AL("Alm_HiDischPress", "High discharge pressure"),
    AL("Alm_HiDischTemp", "High discharge temperature"),
    AL("Alm_LoOilPress", "Low lube oil pressure"),
    AL("Alm_HiOilTemp", "High lube oil temperature"),
    AL("Alm_Vib", "High vibration"),
    AL("Alm_LoSuct", "Low suction pressure"),
], "Rotating")

T("Conveyor", "Belt / screw conveyor: start warning, zero-speed, pull-cord, alignment", [
    M("Mtr", "@Motor", "Drive motor"),
    M("Inp_MotionOK", "BOOL", "Zero-speed switch: motion detected"),
    M("Inp_PullCordOK", "BOOL", "Pull-cord / lanyard switches healthy"),
    M("Inp_AlignLOK", "BOOL", "Belt alignment left healthy"),
    M("Inp_AlignROK", "BOOL", "Belt alignment right healthy"),
    M("Inp_ChuteOK", "BOOL", "Chute not blocked"),
    M("Inp_BeltRipOK", "BOOL", "Belt rip detector healthy"),
    M("Inp_DownstrRun", "BOOL", "Downstream conveyor running"),
    M("Inp_Rate", "REAL", "Belt scale rate (t/h), optional"),
    M("Cfg_UseDownstr", "BOOL", "Require downstream running (cascade start/trip)"),
    M("Cfg_WarnTime", "TIME", "Pre-start warning horn time", "T#10S"),
    M("Cfg_MotionDly", "TIME", "Time after start to detect motion", "T#5S"),
    M("Cfg_PurgeTime", "TIME", "Run-out time before stopping (empty belt)", "T#0S"),
    M("Out_Horn", "BOOL", "Start warning horn"),
    M("Out_Beacon", "BOOL", "Start warning beacon"),
    M("Out_IntlkOK", "BOOL", "Wire to Mtr.Inp_IntlkOK"),
    M("Out_PermOK", "BOOL", "Wire to Mtr.Inp_PermOK"),
    M("Out_StartReq", "BOOL", "Start request to Mtr after warning completes"),
    M("Sts_Warning", "BOOL", "Pre-start warning in progress"),
    M("Sts_Purging", "BOOL", "Running out before stop"),
    M("Sts_State", "INT", "0=Stopped 1=Warning 2=Starting 3=Running 4=Purging 5=Tripped"),
    M("Val_Total", "LREAL", "Total conveyed (t)"),
    A("Alm_ZeroSpd", "Zero-speed / belt slip"),
    A("Alm_PullCord", "Pull-cord operated"),
    A("Alm_Misalign", "Belt misalignment"),
    A("Alm_Chute", "Chute blocked"),
    A("Alm_BeltRip", "Belt rip"),
    A("Alm_DownstrStop", "Tripped by downstream conveyor"),
], "Rotating")

# ---------------- Process extras ----------------
T("Tank", "Tank / vessel: level-to-volume, inventory, fill/drain permissives, alarms", HDR + [
    M("Cfg_Product", "STRING[24]", "Stored product"),
    M("Cfg_LvlEU", "STRING[8]", "Level units text"),
    M("Cfg_VolEU", "STRING[8]", "Volume units text"),
    M("Inp_Level", "REAL", "Level (Cfg_LvlEU) from AI Val_PV"),
    M("Inp_LevelBad", "BOOL", "Level signal bad"),
    M("Inp_LSHH", "BOOL", "High-high level switch active"),
    M("Inp_LSLL", "BOOL", "Low-low level switch active"),
    M("Inp_Temp", "REAL", "Temperature (degC)"),
    M("Inp_Press", "REAL", "Pressure (EU)"),
    M("Cfg_MaxLevel", "REAL", "Level at 100% full", "100.0"),
    M("Cfg_Capacity", "REAL", "Volume at 100% full", "100.0"),
    M("Cfg_Shape", "INT", "0=Vertical / linear 1=Horizontal cylinder 2=Strapping table", "0"),
    M("Cfg_Strap", "ARRAY[0..10] OF REAL", "Strapping table: volume at 0,10..100% level"),
    M("Cfg_SG", "REAL", "Specific gravity (for mass)", "1.0"),
    M("Cfg_FillStop", "REAL", "Fill permissive removed above this level", "90.0"),
    M("Cfg_DrainStop", "REAL", "Drain permissive removed below this level", "5.0"),
    M("Cfg_RateWindow", "TIME", "Window for net-flow (rate of change) calc", "T#1M"),
    M("Prog_EqState", "INT", "ISA-88 equipment state request from unit / phase logic"),
    M("Out_FillPerm", "BOOL", "Filling permitted (wire to inlet pump / valve)"),
    M("Out_DrainPerm", "BOOL", "Draining permitted (wire to outlet pump / valve)"),
    M("Val_Volume", "REAL", "Volume (Cfg_VolEU)"),
    M("Val_PctFull", "REAL", "Volume (% of capacity)"),
    M("Val_Ullage", "REAL", "Remaining capacity (Cfg_VolEU)"),
    M("Val_Mass", "REAL", "Mass (t, from volume x SG)"),
    M("Val_NetFlow", "REAL", "Net in/out flow (Cfg_VolEU per min, + = filling)"),
    M("Val_MinToFull", "REAL", "Minutes to full at current rate"),
    M("Val_MinToEmpty", "REAL", "Minutes to empty at current rate"),
    M("Sts_Filling", "BOOL", "Level rising"),
    M("Sts_Draining", "BOOL", "Level falling"),
    M("Sts_EqState", "INT", "ISA-88 equipment state: " + EQSTATE),
    AL("Alm_HH", "High-high level"),
    AL("Alm_H", "High level"),
    AL("Alm_L", "Low level"),
    AL("Alm_LL", "Low-low level"),
    A("Alm_LSHH", "High-high level switch"),
    A("Alm_LSLL", "Low-low level switch"),
    A("Alm_LvlDisc", "Analog level disagrees with level switch"),
    AL("Alm_HiTemp", "High temperature"),
    AL("Alm_HiPress", "High pressure"),
], "Process")

T("Totalizer", "Flow totalizer + batch delivery: analog or pulse, day/hour totals", HDR + [
    M("Cfg_RateEU", "STRING[12]", "Rate units text, e.g. m3/h"),
    M("Cfg_TotEU", "STRING[12]", "Total units text, e.g. m3"),
    M("Inp_Rate", "REAL", "Flow rate (Cfg_RateEU)"),
    M("Inp_RateBad", "BOOL", "Rate signal bad"),
    M("Inp_Pulses", "UDINT", "Raw pulse counter (pulse mode)"),
    M("Cfg_UsePulses", "BOOL", "Totalise from pulses instead of rate"),
    M("Cfg_PulseWt", "REAL", "Total units per pulse", "1.0"),
    M("Cfg_TimeBase", "REAL", "Seconds per rate time unit: 1=/s 60=/min 3600=/h", "3600.0"),
    M("Cfg_Conv", "REAL", "Conversion rate units -> total units", "1.0"),
    M("Cfg_LoCutoff", "REAL", "Rates below this are not totalised", "0.0"),
    M("Cfg_BadAction", "INT", "On bad rate: 0=Stop totalising 1=Use last good rate", "0"),
    M("Cfg_DayStartHr", "INT", "Hour the production day starts (0-23)", "0"),
    M("Cfg_BatchSP", "REAL", "Batch target quantity", "0.0"),
    M("Cfg_PreAct", "REAL", "Pre-act (in-flight) quantity", "0.0"),
    M("Cfg_AutoPreAct", "BOOL", "Learn pre-act from overrun"),
    M("Cfg_SlowPct", "REAL", "Dribble / slow-fill at this % of batch", "90.0"),
    M("Cmd_Start", "BOOL", "Operator batch start (one-shot)"),
    M("Cmd_Hold", "BOOL", "Operator batch hold (one-shot)"),
    M("Cmd_Reset", "BOOL", "Operator batch reset (one-shot)"),
    M("Prog_Start", "BOOL", "Program batch start"),
    M("Prog_Hold", "BOOL", "Program batch hold"),
    M("Prog_Reset", "BOOL", "Program batch reset"),
    M("Out_Slow", "BOOL", "Slow-fill / dribble"),
    M("Out_BatchDone", "BOOL", "Batch target reached (close valve)"),
    M("Val_Batch", "LREAL", "Batch total"),
    M("Val_Remaining", "REAL", "Batch remaining"),
    M("Val_Overrun", "REAL", "Last batch overrun"),
    M("Val_GrandTotal", "LREAL", "Grand total (non-resettable)"),
    M("Val_ThisHr", "LREAL", "Total this hour"),
    M("Val_LastHr", "LREAL", "Total last hour"),
    M("Val_Today", "LREAL", "Total this production day"),
    M("Val_Yday", "LREAL", "Total previous production day"),
    M("Sts_Running", "BOOL", "Batch running"),
    M("Sts_Hold", "BOOL", "Batch held"),
    M("Sts_Done", "BOOL", "Batch complete"),
    AL("Alm_HiRate", "High flow rate"),
    AL("Alm_LoRate", "Low flow rate"),
    AL("Alm_Overrun", "Batch overrun"),
    A("Alm_RateBad", "Rate signal bad while totalising"),
], "Process")

T("HeatEx", "Heat exchanger performance monitor: duty, LMTD, UA, fouling, DP", HDR + [
    M("Inp_HotInT", "REAL", "Hot side inlet temperature (degC)"),
    M("Inp_HotOutT", "REAL", "Hot side outlet temperature (degC)"),
    M("Inp_ColdInT", "REAL", "Cold side inlet temperature (degC)"),
    M("Inp_ColdOutT", "REAL", "Cold side outlet temperature (degC)"),
    M("Inp_HotFlow", "REAL", "Hot side mass flow (kg/s)"),
    M("Inp_ColdFlow", "REAL", "Cold side mass flow (kg/s)"),
    M("Inp_HotDP", "REAL", "Hot side differential pressure (kPa)"),
    M("Inp_ColdDP", "REAL", "Cold side differential pressure (kPa)"),
    M("Cfg_HotCp", "REAL", "Hot side specific heat (kJ/kg.K)", "4.186"),
    M("Cfg_ColdCp", "REAL", "Cold side specific heat (kJ/kg.K)", "4.186"),
    M("Cfg_CounterFlow", "BOOL", "Counter-current (FALSE = co-current) for LMTD", "TRUE"),
    M("Cfg_DesignUA", "REAL", "Clean design UA (kW/K)", "0.0"),
    M("Cfg_MinFlow", "REAL", "Below this flow the calculations are frozen (kg/s)", "0.0"),
    M("Cfg_CalcFilt", "REAL", "Filter time constant for calculated values (s)", "60.0"),
    M("Val_DutyHot", "REAL", "Heat released by hot side (kW)"),
    M("Val_DutyCold", "REAL", "Heat absorbed by cold side (kW)"),
    M("Val_Duty", "REAL", "Average duty (kW)"),
    M("Val_HeatBal", "REAL", "Heat balance error (%)"),
    M("Val_LMTD", "REAL", "Log mean temperature difference (K)"),
    M("Val_UA", "REAL", "Actual UA (kW/K)"),
    M("Val_Clean", "REAL", "Cleanliness: UA as % of design"),
    M("Val_Approach", "REAL", "Approach temperature (K)"),
    M("Val_Effect", "REAL", "Thermal effectiveness (0-1)"),
    M("Sts_CalcValid", "BOOL", "Inputs valid, calculations live"),
    AL("Alm_Fouling", "Low cleanliness (Val_Clean below limit)"),
    AL("Alm_HotDP", "High hot side DP"),
    AL("Alm_ColdDP", "High cold side DP"),
    AL("Alm_HeatBal", "Heat balance error (possible instrument fault)"),
    AL("Alm_HiOutT", "High process outlet temperature"),
], "Process")

T("DosePump", "Chemical dosing / metering pump: manual, flow-paced, trim, batch", [
    M("Mtr", "@Motor", "Pump motor / enable"),
    M("Cfg_RateEU", "STRING[8]", "Dose rate units text, e.g. L/h"),
    M("Cfg_DoseMode", "INT", "0=Manual rate 1=Flow-paced 2=Flow-paced + trim 3=Batch volume", "0"),
    M("Cfg_MaxRate", "REAL", "Pump rate at 100% output (L/h)", "0.0"),
    M("Cfg_CalFactor", "REAL", "Calibration factor from drawdown test", "1.0"),
    M("Cfg_DoseConc", "REAL", "Target dose in process (mg/L)", "0.0"),
    M("Cfg_ChemConc", "REAL", "Chemical strength (% w/w)", "100.0"),
    M("Cfg_ChemSG", "REAL", "Chemical specific gravity", "1.0"),
    M("Cfg_TankCap", "REAL", "Chemical day tank capacity (L)", "0.0"),
    M("Cfg_NoFlowDly", "TIME", "Flow verification delay", "T#30S"),
    M("Inp_PaceFlow", "REAL", "Process flow for pacing (m3/h)"),
    M("Inp_TrimPct", "REAL", "Trim from residual PID (%, -100..+100)"),
    M("Inp_FlowOK", "BOOL", "Flow verification switch: dosing detected"),
    M("Inp_ChemLvl", "REAL", "Chemical day tank level (%)"),
    M("Inp_Leak", "BOOL", "Leak detector / bund alarm"),
    M("Cmd_Rate", "REAL", "Operator dose rate (L/h)", "0.0"),
    M("Prog_Rate", "REAL", "Program dose rate (L/h)", "0.0"),
    M("Cmd_CalDone", "BOOL", "Calibration complete, stamp date (one-shot)"),
    M("Out_Rate", "REAL", "Speed / stroke output to pump (%)"),
    M("Out_IntlkOK", "BOOL", "Wire to Mtr.Inp_IntlkOK"),
    M("Val_RateSP", "REAL", "Active dose rate (L/h)"),
    M("Val_Total", "LREAL", "Total dosed (L)"),
    M("Val_Today", "REAL", "Dosed today (L)"),
    M("Val_DaysLeft", "REAL", "Days of chemical remaining at current usage"),
    M("Val_LastCal", "DT", "Date of last calibration"),
    M("Sts_RateLimited", "BOOL", "Demand exceeds pump capacity"),
    A("Alm_NoFlow", "No flow detected while running"),
    AL("Alm_LoChem", "Low chemical level (%)"),
    AL("Alm_LoLoChem", "Low-low chemical level (%) - stops pump"),
    A("Alm_Leak", "Leak detected"),
    A("Alm_RateLim", "Dose demand exceeds pump capacity"),
], "Process")

# ---------------- Analyzers & safety ----------------
T("Analyzer", "Process analyzer (pH, ORP, conductivity, DO, turbidity, Cl2 ...)", [
    M("AI", "@AI", "Measured value, scaling and alarms"),
    M("Cfg_AnType", "INT", "1=pH 2=ORP 3=Conductivity 4=DO 5=Turbidity 6=Free Cl2 7=TOC 8=Other", "1"),
    M("Inp_Temp", "REAL", "Sample / compensation temperature (degC)"),
    M("Inp_DevFault", "BOOL", "Transmitter diagnostic fault"),
    M("Inp_DevMaint", "BOOL", "Transmitter in maintenance / calibration"),
    M("Inp_DevWarn", "BOOL", "Transmitter warning (e.g. sensor ageing)"),
    *NE107_FULL,
    M("Inp_SampleOK", "BOOL", "Sample flow healthy (flow switch)"),
    M("Inp_Slope", "REAL", "Sensor slope from transmitter (e.g. pH mV/pH)"),
    M("Cfg_HoldMax", "TIME", "Maximum hold time before alarm", "T#1H"),
    M("Cfg_CalDays", "INT", "Calibration interval (days)", "30"),
    M("Cfg_FrozenTime", "TIME", "PV unchanged for this long = frozen sensor", "T#30M"),
    M("Cfg_FrozenBand", "REAL", "Band within which PV is considered unchanged", "0.0"),
    M("Cmd_Hold", "BOOL", "Hold PV and suppress alarms for calibration (one-shot)"),
    M("Cmd_Release", "BOOL", "Release hold (one-shot)"),
    M("Cmd_CalDone", "BOOL", "Calibration completed, stamp date (one-shot)"),
    M("Val_PV", "REAL", "Value for control - held value while in hold"),
    M("Val_HeldPV", "REAL", "Value captured at start of hold"),
    M("Val_LastCal", "DT", "Date/time of last calibration"),
    M("Val_DaysSinceCal", "REAL", "Days since last calibration"),
    M("Sts_Hold", "BOOL", "In hold / calibration"),
    M("Sts_CalDue", "BOOL", "Calibration due"),
    A("Alm_DevFault", "Transmitter fault"),
    A("Alm_NoSample", "No sample flow"),
    A("Alm_Frozen", "Frozen / stuck reading"),
    A("Alm_CalDue", "Calibration overdue"),
    A("Alm_HoldLong", "Hold exceeded Cfg_HoldMax"),
], "Safety")

T("GasDet", "Fixed gas detector (4-20mA): latching A1/A2/A3, inhibit, fault", HDR + [
    M("Cfg_Gas", "STRING[12]", "Gas, e.g. CH4, H2S, CO, O2"),
    M("Cfg_EU", "STRING[8]", "Units, e.g. %LEL, ppm, %vol"),
    M("Inp_Raw", "INT", "Raw counts from analog channel"),
    M("Inp_ChFault", "BOOL", "Channel / module diagnostic fault"),
    M("Cfg_RawMin", "INT", "Raw counts at 4 mA", "0"),
    M("Cfg_RawMax", "INT", "Raw counts at 20 mA", "10000"),
    M("Cfg_RangeMax", "REAL", "Concentration at 20 mA", "100.0"),
    M("Cfg_O2Mode", "BOOL", "Oxygen depletion: A1/A2 act on falling concentration"),
    M("Cfg_FaultmA", "REAL", "Signal below this (mA) = detector fault", "3.0"),
    M("Cfg_MaintLomA", "REAL", "Maintenance / inhibit signal band low (mA), vendor-specific", "0.0"),
    M("Cfg_MaintHimA", "REAL", "Maintenance / inhibit signal band high (mA), vendor-specific", "0.0"),
    M("Cfg_OverRngmA", "REAL", "Signal above this (mA) = over-range (treat as alarm)", "20.5"),
    M("Cfg_InhibitMax", "TIME", "Maximum operator inhibit time", "T#2H"),
    M("Cmd_Inhibit", "BOOL", "Operator inhibit for maintenance (one-shot)"),
    M("Cmd_Uninhibit", "BOOL", "Remove inhibit (one-shot)"),
    M("Cmd_Reset", "BOOL", "Reset latched alarms (one-shot)"),
    M("Sim_En", "BOOL", "Simulation enabled"),
    M("Sim_mA", "REAL", "Simulated signal (mA)", "4.0"),
    M("Out_A1", "BOOL", "Alarm level 1 active (to voting / beacons)"),
    M("Out_A2", "BOOL", "Alarm level 2 active"),
    M("Out_A3", "BOOL", "Alarm level 3 active"),
    M("Out_Fault", "BOOL", "Detector fault / unavailable"),
    M("Val_mA", "REAL", "Signal (mA)"),
    M("Val_Conc", "REAL", "Gas concentration (Cfg_EU)"),
    M("Val_Peak", "REAL", "Peak concentration since last reset"),
    M("Sts_Inhibit", "BOOL", "Operator inhibit active"),
    M("Sts_DetMaint", "BOOL", "Detector signalling maintenance"),
    M("Sts_InhibitLeft", "TIME", "Inhibit time remaining"),
    M("Sts_Sim", "BOOL", "Simulation active"),
    *NE107_FULL,
    AL("Alm_A1", "Alarm level 1 (low) - set Cfg_Latch as required"),
    AL("Alm_A2", "Alarm level 2 (high) - set Cfg_Latch as required"),
    AL("Alm_A3", "Alarm level 3 (high-high / STEL)"),
    A("Alm_Fault", "Detector fault"),
    A("Alm_OverRng", "Over-range"),
    A("Alm_InhibitLong", "Inhibit timed out"),
], "Safety")

T("Intlk", "Interlock / permissive group: 16 conditions, first-out, timed bypass", HDR + [
    M("Inp_Cond", "ARRAY[0..15] OF BOOL", "Condition n: TRUE = healthy / permitted"),
    M("Cfg_Used", "ARRAY[0..15] OF BOOL", "Condition n is configured"),
    M("Cfg_CondDesc", "ARRAY[0..15] OF STRING[32]", "HMI text for condition n"),
    M("Cfg_Bypassable", "ARRAY[0..15] OF BOOL", "Condition n may be bypassed"),
    M("Cfg_Latch", "BOOL", "Latch failures until Cmd_Reset (interlock); FALSE = permissive"),
    M("Cfg_BypassMax", "TIME", "Maximum bypass duration", "T#8H"),
    M("Cmd_Bypass", "ARRAY[0..15] OF BOOL", "Bypass condition n (one-shot)"),
    M("Cmd_Unbypass", "ARRAY[0..15] OF BOOL", "Remove bypass on condition n (one-shot)"),
    M("Cmd_UnbypassAll", "BOOL", "Remove all bypasses (one-shot)"),
    M("Inp_BypassPerm", "BOOL", "Bypass authorisation (key switch / HMI permit) - IEC 61511 bypass management"),
    M("Cmd_Reset", "BOOL", "Reset latched conditions (one-shot)"),
    M("Out_OK", "BOOL", "All used conditions healthy or bypassed - wire to Inp_IntlkOK / Inp_PermOK"),
    M("Sts_OKNoByp", "BOOL", "All used conditions healthy without bypasses"),
    M("Sts_Bypassed", "ARRAY[0..15] OF BOOL", "Condition n bypassed"),
    M("Sts_Latched", "ARRAY[0..15] OF BOOL", "Condition n latched failed"),
    M("Sts_FirstOut", "INT", "First condition to fail (-1 = none)"),
    M("Sts_NumBypassed", "INT", "Number of bypassed conditions"),
    M("Sts_BypassLeft", "TIME", "Time left on the oldest bypass"),
    M("Sts_ResetReq", "BOOL", "Conditions healthy, reset required"),
    M("Sts_CondWord", "WORD", "Packed Inp_Cond (bit n = condition n) for SCADA"),
    M("Sts_BypWord", "WORD", "Packed Sts_Bypassed for SCADA"),
    M("Sts_LatchWord", "WORD", "Packed Sts_Latched for SCADA"),
    A("Alm_Trip", "Interlock tripped"),
    A("Alm_Bypass", "One or more conditions bypassed"),
], "Safety")

T("ESD", "Emergency shutdown group (BPCS layer): de-energise-to-trip, MOS, first-out", HDR + [
    M("Cfg_Level", "INT", "ESD level, e.g. 0=Plant 1=Unit 2=Equipment", "1"),
    M("Inp_OK", "ARRAY[0..15] OF BOOL", "Trip input n: TRUE = healthy"),
    M("Inp_UpstrOK", "BOOL", "Higher-level ESD healthy (cascade)", "TRUE"),
    M("Inp_ManTripOK", "BOOL", "Field ESD push-button circuit healthy"),
    M("Inp_ResetPB", "BOOL", "Field reset push-button"),
    M("Inp_MOSKey", "BOOL", "Maintenance override key switch enabled"),
    M("Inp_FinalSafe", "BOOL", "All final elements confirmed in safe state"),
    M("Cfg_Used", "ARRAY[0..15] OF BOOL", "Input n configured"),
    M("Cfg_InDesc", "ARRAY[0..15] OF STRING[32]", "HMI text for input n"),
    M("Cfg_MOSAllowed", "ARRAY[0..15] OF BOOL", "Override allowed on input n"),
    M("Cfg_MOSMax", "TIME", "Maximum override duration", "T#4H"),
    M("Cfg_FieldReset", "BOOL", "Field reset push-button required to reset"),
    M("Cfg_SafeTime", "TIME", "Time for final elements to reach safe state", "T#30S"),
    M("Cmd_ManTrip", "BOOL", "HMI manual trip (one-shot)"),
    M("Cmd_Reset", "BOOL", "HMI reset (one-shot)"),
    M("Cmd_MOS", "ARRAY[0..15] OF BOOL", "Apply override on input n (one-shot)"),
    M("Cmd_MOSOff", "ARRAY[0..15] OF BOOL", "Remove override on input n (one-shot)"),
    M("Out_Healthy", "BOOL", "TRUE = run permitted (energised); FALSE = trip"),
    M("Sts_Tripped", "BOOL", "Group tripped"),
    M("Sts_ResetReady", "BOOL", "All inputs healthy, reset possible"),
    M("Sts_FirstOut", "INT", "First input to trip (-1 none, 16=manual, 17=upstream)"),
    M("Sts_MOS", "ARRAY[0..15] OF BOOL", "Override active on input n"),
    M("Sts_NumMOS", "INT", "Number of active overrides"),
    M("Sts_InWord", "WORD", "Packed Inp_OK for SCADA"),
    M("Sts_LatchWord", "WORD", "Packed latched trips for SCADA"),
    M("Sts_MOSWord", "WORD", "Packed Sts_MOS for SCADA"),
    M("Val_TripTime", "DT", "Date/time of last trip"),
    M("Val_TripCount", "UDINT", "Trip counter"),
    A("Alm_Trip", "ESD trip"),
    A("Alm_FailSafe", "Final elements failed to reach safe state"),
    A("Alm_MOS", "Maintenance override active"),
    A("Alm_MOSLong", "Override exceeded Cfg_MOSMax"),
], "Safety")

# ---------------- ISA-88 batch / procedural ----------------
T("Station", "Weigh-fill station: vessel on a scale, inlet / sample / vacuum valves, net-weight fill to target", HDR + [
    M("Cfg_ScaleName", "STRING[20]", "Scale tag shown on the HMI, e.g. WT-101"),
    M("Cfg_EU", "STRING[8]", "Weight units text (kg, lb)"),
    M("Mode", "@Mode", "Mode block"),
    M("Perm", "@Intlk", "Fill permissives (vessel present, PT valid, pressure balanced, ...)"),
    M("Inp_Gross", "REAL", "Gross weight from the scale (Cfg_EU)"),
    M("Inp_ScaleOK", "BOOL", "Scale healthy (no overload / comms fault)", "TRUE"),
    M("Inp_PT", "REAL", "Vessel pressure"),
    M("Inp_PTValid", "BOOL", "Pressure reading valid"),
    M("Inp_VesselPresent", "BOOL", "Vessel detected on the station"),
    M("Prm_TargetWt", "REAL", "Fill target, net weight (operator setpoint)"),
    M("Prm_SampleWt", "REAL", "Sample draw weight (operator setpoint)"),
    M("Prm_MaxPress", "REAL", "Maximum vessel pressure during fill (operator setpoint)"),
    M("Prm_PrefillPress", "REAL", "Prefill pressure (operator setpoint)"),
    M("Prm_Deadband", "REAL", "Fill deadband, net weight (operator setpoint)"),
    M("Cmd_Select", "BOOL", "Select this station (one-shot)"),
    M("Cmd_Tare", "BOOL", "Tare the scale (one-shot; blocked while active)"),
    M("Cmd_Zero", "BOOL", "Zero the scale (one-shot; blocked while active)"),
    M("Cmd_Reset", "BOOL", "Reset a failed / complete station (one-shot)"),
    M("Out_InletCmd", "BOOL", "Inlet valve command"),
    M("Out_SampleCmd", "BOOL", "Sample valve command"),
    M("Out_VacuumCmd", "BOOL", "Vacuum valve command"),
] + SIM + [
    M("Sts_Selected", "BOOL", "Station selected"),
    M("Sts_Active", "BOOL", "Station in a fill cycle"),
    M("Sts_Disabled", "BOOL", "Station disabled"),
    M("Sts_InletReq", "BOOL", "Sequence requests the inlet valve open"),
    M("Sts_SampleReq", "BOOL", "Sequence requests the sample valve open"),
    M("Sts_VacuumReq", "BOOL", "Sequence requests the vacuum valve open"),
    M("Sts_Vacuuming", "BOOL", "Evacuating the vessel"),
    M("Sts_Vacuumed", "BOOL", "Vessel evacuated"),
    M("Sts_Filling", "BOOL", "Filling"),
    M("Sts_Venting", "BOOL", "Venting"),
    M("Sts_Recovering", "BOOL", "Recovering"),
    M("Sts_Complete", "BOOL", "Fill complete"),
    M("Sts_Failed", "BOOL", "Fill failed - reset required"),
    M("Sts_ReadyToStart", "BOOL", "Ready to start (all start permissives)"),
    M("Sts_ReadyToFill", "BOOL", "Ready to fill"),
    M("Sts_PressBalanced", "BOOL", "Vessel and header pressures balanced"),
    M("Sts_Sim", "BOOL", "Simulation active"),
    M("Sts_State", "INT", "0=Idle 1=Selected 2=Vacuum 3=Prefill 4=Fill 5=Sample 6=Complete 7=Failed 8=Disabled"),
    M("Sts_Msg", "STRING[40]", "Status message for the HMI"),
] + NE107_STS + [
    M("Val_Net", "REAL", "Net weight (Cfg_EU)"),
    M("Val_Gross", "REAL", "Gross weight (Cfg_EU)"),
    M("Val_Tare", "REAL", "Tare weight (Cfg_EU)"),
    M("Val_Total", "REAL", "Total filled this cycle (Cfg_EU)"),
    M("Val_Remaining", "REAL", "Target minus net (Cfg_EU)"),
    M("Val_PctDone", "REAL", "Net as % of target"),
    M("Val_PT", "REAL", "Vessel pressure"),
    M("Val_PTDiff", "REAL", "Vessel minus header pressure"),
    A("Alm_Failed", "Fill failed"),
    A("Alm_OverFill", "Net weight above target plus deadband"),
    AL("Alm_PressHi", "Vessel pressure high (uses Prm_MaxPress)"),
    A("Alm_ScaleFault", "Scale fault"),
], "Process")

T("IOCard", "Modicon x80 I/O module diagnostics: module and channel health, field power", HDR + [
    M("Cfg_Model", "STRING[16]", "Module reference, e.g. BMXDDI1602"),
    M("Cfg_Kind", "INT", "0=DI 1=DO 2=AI 3=AO 4=TC/RTD 5=Counter 6=Other", "0"),
    M("Cfg_Rack", "INT", "Rack number", "0"),
    M("Cfg_Slot", "INT", "Slot number", "0"),
    M("Cfg_Drop", "STRING[20]", "Drop / station name (main rack or eRIO drop)"),
    M("Cfg_NumCh", "INT", "Channels on the module", "16"),
    M("Cfg_ChUsed", "ARRAY[0..63] OF BOOL", "Channel n is wired (spares FALSE)"),
    M("Inp_ModHealth", "BOOL", "Module health bit from the module device DDT / IODDT (TRUE = healthy)"),
    M("Inp_ModFltWord", "WORD", "Module fault byte(s) from the device DDT, for diagnosis"),
    M("Inp_ChHealth", "ARRAY[0..63] OF BOOL", "Channel n healthy (no wire break, short, out of range)"),
    M("Inp_FieldPwrOK", "BOOL", "External field power supply present", "TRUE"),
    M("Inp_Missing", "BOOL", "Module missing or wrong type in the slot"),
    M("Sts_OK", "BOOL", "Module healthy and all used channels healthy"),
    M("Sts_ChFault", "ARRAY[0..63] OF BOOL", "Used channel n faulted"),
    M("Sts_NumChFault", "INT", "Number of faulted used channels"),
    M("Sts_FirstChFault", "INT", "Lowest faulted channel (-1 = none)"),
    M("Sts_ChWord", "ARRAY[0..3] OF WORD", "Sts_ChFault packed, 16 channels per word, for SCADA"),
] + NE107_STS + [
    A("Alm_ModFault", "Module fault"),
    A("Alm_ChFault", "One or more channels faulted"),
    A("Alm_FieldPwr", "Field power lost"),
    A("Alm_Missing", "Module missing or wrong type"),
], "IO")

T("IORack", "Modicon x80 rack / drop diagnostics: power supply, slot health, communications", HDR + [
    M("Cfg_Rack", "INT", "Rack number", "0"),
    M("Cfg_Drop", "STRING[20]", "Drop / station name"),
    M("Cfg_Remote", "BOOL", "Remote drop (eRIO / DIO): communications monitored"),
    M("Cfg_NumSlots", "INT", "Slots on the backplane (4, 6, 8 or 12)", "12"),
    M("Cfg_PSModel", "STRING[16]", "Power supply reference, e.g. BMXCPS3500"),
    M("Cfg_SlotUsed", "ARRAY[0..11] OF BOOL", "Slot n holds a configured module"),
    M("Inp_PSOK", "BOOL", "Power supply healthy", "TRUE"),
    M("Inp_PSRedOK", "BOOL", "Redundant power supply healthy (if fitted)", "TRUE"),
    M("Inp_CommOK", "BOOL", "Drop communications healthy (remote drops)", "TRUE"),
    M("Inp_SlotOK", "ARRAY[0..11] OF BOOL", "Module in slot n healthy (from T_IOCard Sts_OK)"),
    M("Sts_OK", "BOOL", "Power, communications and every used slot healthy"),
    M("Sts_NumFaulted", "INT", "Number of used slots not healthy"),
    M("Sts_SlotWord", "WORD", "Faulted used slots packed (bit n = slot n), for SCADA"),
] + NE107_STS + [
    A("Alm_PSFault", "Power supply fault"),
    A("Alm_PSRedFault", "Redundant power supply fault"),
    A("Alm_CommLoss", "Drop communications lost"),
    A("Alm_SlotFault", "One or more modules faulted"),
], "IO")

T("Phase", "ISA-88 equipment phase: Part 1 state model, commands, modes, parameters, reports", HDR + [
    M("Cfg_PhaseID", "INT", "Phase ID (unique in the unit) for batch server / unit procedure"),
    M("Cfg_UnitID", "INT", "ID of the unit this phase belongs to"),
    M("Cfg_StepTimeout", "TIME", "Step watchdog, T#0S = off", "T#0S"),
    M("Cmd_Auto", "BOOL", "Operator request Automatic mode (one-shot)"),
    M("Cmd_SemiAuto", "BOOL", "Operator request Semi-automatic mode (one-shot)"),
    M("Cmd_Man", "BOOL", "Operator request Manual mode (one-shot)"),
    M("Cmd_Start", "BOOL", "Operator Start (one-shot)"),
    M("Cmd_Stop", "BOOL", "Operator Stop (one-shot)"),
    M("Cmd_Hold", "BOOL", "Operator Hold (one-shot)"),
    M("Cmd_Restart", "BOOL", "Operator Restart from Held (one-shot)"),
    M("Cmd_Abort", "BOOL", "Operator Abort (one-shot)"),
    M("Cmd_Reset", "BOOL", "Operator Reset to Idle (one-shot)"),
    M("Cmd_Pause", "BOOL", "Operator Pause at next transition (one-shot)"),
    M("Cmd_Resume", "BOOL", "Operator Resume from Paused (one-shot)"),
    M("Cmd_Advance", "BOOL", "Advance to next step in Semi-automatic (one-shot)"),
    M("Cmd_TakeOwn", "BOOL", "Operator takes control from the recipe (one-shot)"),
    M("Prog_Cmd", "INT", "Command from batch server / unit procedure: " + PHASE_CMDS),
    M("Prog_Acquire", "BOOL", "Recipe (batch server / unit procedure) takes ownership"),
    M("Prog_Release", "BOOL", "Recipe releases ownership"),
    M("Prog_ReqAck", "BOOL", "Batch server acknowledges Sts_ReqCode"),
    M("Prm_Real", "ARRAY[1..16] OF REAL", "Recipe parameters (REAL) - control recipe formula"),
    M("Prm_DInt", "ARRAY[1..8] OF DINT", "Recipe parameters (DINT) - control recipe formula"),
    M("Rpt_Real", "ARRAY[1..16] OF REAL", "Report values (REAL) returned to batch record"),
    M("Rpt_DInt", "ARRAY[1..8] OF DINT", "Report values (DINT) returned to batch record"),
    M("Val_BatchID", "STRING[32]", "Batch ID of the control recipe running this phase"),
    M("Val_StateTime", "TIME", "Time in current state"),
    M("Val_RunTime", "TIME", "Running time excluding Held / Paused"),
    M("Val_FailText", "STRING[40]", "Failure description for HMI / batch record"),
    M("Sts_State", "INT", "ISA-88 state: " + PHASE_STATES),
    M("Sts_PrevState", "INT", "Previous state (for Restart / diagnostics)"),
    M("Sts_Mode", "INT", "ISA-88 mode: 1=Manual 2=Semi-automatic 3=Automatic"),
    M("Sts_Owner", "INT", "0=Operator 1=Recipe (batch server / unit procedure)"),
    M("Sts_CmdMask", "WORD", "Commands valid in current state (bit n = command n of Prog_Cmd) - for HMI"),
    M("Sts_CmdRejected", "BOOL", "Last command was not valid in the current state"),
    M("Sts_Step", "INT", "Active step number within the state logic"),
    M("Sts_WaitAdvance", "BOOL", "Semi-automatic: waiting for Cmd_Advance"),
    M("Sts_ReqCode", "INT", "Request to batch server (e.g. download params, upload reports), 0 = none"),
    M("Sts_FailCode", "INT", "Failure code, 0 = none"),
    A("Alm_Fail", "Phase failure"),
    A("Alm_StepTimeout", "Step exceeded Cfg_StepTimeout"),
], "Batch")

T("Unit", "ISA-88 unit: allocation, batch identity, procedural and equipment state", HDR + [
    M("Cfg_UnitID", "INT", "Unit ID"),
    M("Cfg_UnitClass", "STRING[24]", "Unit class name (master recipe equipment requirement)"),
    M("Cfg_CleanHold", "TIME", "Clean hold time - clean status expires after this", "T#72H"),
    M("Inp_ReqOwnerID", "DINT", "ID of control recipe requesting allocation"),
    M("Prog_Acquire", "BOOL", "Allocate unit to requesting control recipe"),
    M("Prog_Release", "BOOL", "Release unit"),
    M("Cmd_ForceRelease", "BOOL", "Supervisor forces release (one-shot)"),
    M("Prog_EqState", "INT", "Equipment state request from phase logic"),
    M("Cmd_EqState", "INT", "Operator equipment state change (e.g. to Maintenance)"),
    M("Val_OwnerID", "DINT", "Allocated control recipe ID, 0 = free"),
    M("Val_BatchID", "STRING[32]", "Batch ID"),
    M("Val_RecipeName", "STRING[32]", "Control recipe / master recipe name"),
    M("Val_RecipeVer", "INT", "Recipe version"),
    M("Val_ProductCode", "STRING[24]", "Product / material code"),
    M("Val_BatchSize", "REAL", "Batch size (scaled)"),
    M("Val_BatchStart", "DT", "Batch start date/time"),
    M("Val_LastClean", "DT", "Date/time of last completed clean"),
    M("Sts_Allocated", "BOOL", "Unit allocated to a control recipe"),
    M("Sts_ProcState", "INT", "Unit procedure state: " + PHASE_STATES),
    M("Sts_Mode", "INT", "Unit procedure mode: 1=Manual 2=Semi-automatic 3=Automatic"),
    M("Sts_ActivePhase", "INT", "Cfg_PhaseID of the active phase, 0 = none"),
    M("Sts_EqState", "INT", "ISA-88 equipment state: " + EQSTATE),
    M("Sts_CleanExpired", "BOOL", "Clean hold time exceeded"),
    A("Alm_CleanExpired", "Clean status expired"),
], "Batch")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
RESERVED = {
    # IEC / Control Expert keywords and standard function names to avoid
    "ABS", "ACTION", "AND", "ARRAY", "BY", "CASE", "CONSTANT", "DO", "ELSE", "ELSIF", "END",
    "EXIT", "FALSE", "FOR", "FUNCTION", "IF", "IN", "LIMIT", "MAX", "MIN", "MOD", "MOVE", "MUX",
    "NOT", "OF", "ON", "OR", "R", "RETURN", "S", "SEL", "STEP", "STRUCT", "THEN", "TIME", "TO",
    "TRANSITION", "TRUE", "TYPE", "UNTIL", "VAR", "WHILE", "XOR", "EN", "ENO", "Q", "N", "P",
}
IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9]*(_[A-Za-z0-9]+)*$")
ELEMENTARY = re.compile(
    r"^(BOOL|INT|UINT|DINT|UDINT|REAL|LREAL|TIME|DT|WORD|DWORD|BYTE|STRING\[\d+\])$")
ARRAY = re.compile(r"^ARRAY\[(\d+)\.\.(\d+)\] OF (.+)$")


def validate(types):
    missing = {t[0] for t in types} ^ set(META)
    assert not missing, f"META / TYPES mismatch: {missing}"
    defined = set()
    for name, _, members, _ in types:
        assert IDENT.match(name) and len(name) <= 32, f"bad type name {name}"
        seen = set()
        for mname, mtype, comment, _ in members:
            assert IDENT.match(mname), f"{name}.{mname}: invalid identifier"
            assert len(mname) <= 32, f"{name}.{mname}: >32 chars"
            assert mname.upper() not in RESERVED, f"{name}.{mname}: reserved word"
            assert mname.upper() not in seen, f"{name}.{mname}: duplicate"
            assert len(comment) <= 1024, f"{name}.{mname}: comment too long"
            seen.add(mname.upper())
            base = mtype
            m = ARRAY.match(mtype)
            if m:
                base = m.group(3)
            base = base.lstrip("@")
            if not ELEMENTARY.match(base):
                assert base in defined, f"{name}.{mname}: type {base} not defined earlier"
        defined.add(name)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def resolve(types, prefix, lreal):
    out = []
    for name, comment, members, group in types:
        rm = []
        for mname, mtype, mcomment, init in members:
            mtype = mtype.replace("@", prefix)
            if not lreal:
                mtype = mtype.replace("LREAL", "REAL")
            rm.append((mname, mtype, mcomment, init))
        out.append((prefix + name, comment, rm, group))
    return out


def deps(types):
    names = {t[0] for t in types}
    d = {}
    for name, _, members, _ in types:
        direct = set()
        for _, mtype, _, _ in members:
            m = ARRAY.match(mtype)
            base = m.group(3) if m else mtype
            if base in names:
                direct.add(base)
        allp = set(direct)
        for x in direct:
            allp |= d[x]
        d[name] = allp
    return d


def file_header(now, product, content):
    stamp = f"{now.year}-{now.month}-{now.day}-{now.hour}:{now.minute}:{now.second}"
    return [f'<fileHeader company="Schneider Automation" product={quoteattr(product)} '
            f'dateTime="date_and_time#{stamp}" content="{content}" DTDVersion="41"></fileHeader>',
            f'<contentHeader name="PCLib" version="{LIB_VERSION}"></contentHeader>']


def ddt_source_lines(types, now):
    dts = now.strftime("dt#%Y-%m-%d-%H:%M:%S")
    L = []
    for name, comment, members, _ in types:
        L.append(f'<DDTSource DDTName={quoteattr(name)} version="{LIB_VERSION}" dateTime="{dts}">')
        L.append(f"\t<comment>{escape(comment)}</comment>")
        L.append("\t<structure>")
        for mname, mtype, mcomment, init in members:
            L.append(f"\t\t<variables name={quoteattr(mname)} typeName={quoteattr(mtype)}>")
            L.append(f"\t\t\t<comment>{escape(mcomment)}</comment>")
            if init is not None:
                L.append(f"\t\t\t<variableInit value={quoteattr(init)}></variableInit>")
            L.append("\t\t</variables>")
        L.append("\t</structure>")
        L.append("</DDTSource>")
    return L


def xdd_text(types, now, product="Control Expert"):
    L = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', "<DDTExchangeFile>"]
    L += file_header(now, product, "Derived Data Type source file")
    L += ddt_source_lines(types, now)
    L.append("</DDTExchangeFile>")
    return "\n".join(L) + "\n"


GROUP_TITLES = {
    "Common": "Common building blocks",
    "Core": "Core instruments and devices",
    "Rotating": "Rotating equipment",
    "Process": "Process equipment",
    "Safety": "Analyzers and safety",
    "Batch": "ISA-88 batch and procedural",
    "IO": "I/O and system diagnostics",
}

STANDARDS = [
    ("ISA-88.00.01 / IEC 61512-1", "Batch control: physical and procedural models, modes, states",
     "Every type has an ISA-88 role (control module, equipment module, unit, phase). `Prog_` members are "
     "commands from the owning phase or equipment module. `{p}Mode` adds arbitration (acquire / release / "
     "owner ID). `{p}Phase` uses the Part 1 example state model (12 states) and commands (Start, Stop, Hold, "
     "Restart, Abort, Reset, Pause, Resume), with Automatic / Semi-automatic / Manual modes, recipe "
     "parameters and reports. `{p}Unit` holds allocation, batch identity and equipment state (clean, dirty, "
     "in use...)."),
    ("ISA-18.2 / IEC 62682", "Alarm management",
     "`{p}Alarm` uses the standard's state model (A Normal to H Out-of-service), including latching, "
     "time-limited shelving, suppressed-by-design and out-of-service. Chattering control (deadband, "
     "on/off delay), priority and class come from rationalisation. Events that need no operator action are "
     "status bits, not alarms (e.g. pump changeover)."),
    ("ISA-101.01", "HMI design",
     "Modes, states and NE107 status are integers, so graphics can use consistent symbols without colour "
     "logic in the PLC. `Sts_CmdMask` lets the HMI grey out invalid phase commands. Tag and description "
     "are in the type for faceplates."),
    ("ISA-5.1", "Instrument identification",
     "`Cfg_Tag` holds the ISA-5.1 tag (e.g. FT-101). Limit alarms follow HH / H / L / LL naming."),
    ("NAMUR NE107", "Field device diagnostics",
     "`Sts_NE107` on every field-device control module (Good / F / C / S / M). `Inp_NE107` takes the "
     "status from HART or fieldbus devices."),
    ("NAMUR NE43", "4-20 mA failure signal levels",
     "`{p}AI` bad-signal limits default to NE43 (below 3.6 mA, above 21 mA). `{p}GasDet` fault and "
     "over-range thresholds are configurable."),
    ("VDI/VDE/NAMUR 2658-4 (MTP)", "Module Type Package data objects for modular plants",
     "Each type lists its nearest MTP data assembly (AnaMon, BinMon, MonBinVlv, MonAnaVlv, MonBinDrv, "
     "MonAnaDrv, PIDCtrl, LockView16). Mode values map to MTP Offline / Operator / Automatic. Member "
     "names are not MTP attribute names, so an MTP export needs a mapping layer."),
    ("ISA-84 / IEC 61511", "Safety instrumented systems",
     "`{p}Intlk` and `{p}ESD` follow the bypass-management requirements (authorisation, time limit, "
     "indication, logging data), first-out, manual reset after trip and de-energise-to-trip. They are "
     "**basic process control (BPCS) functions only**, not SIFs."),
    ("IEC 61131-3", "PLC languages and data types",
     "Elementary IEC data types only. Identifiers are checked against the 32-character limit and IEC / "
     "Control Expert reserved words."),
    ("ISA-95 / IEC 62264", "Enterprise-control integration",
     "Level 1-2 data. `{p}Unit` and `{p}Phase` expose batch ID, recipe, product and reports for MES "
     "collection."),
]


PLATFORM_IMPORT = """## Platform import files (`export/`)

| File | Target | Import into |
|---|---|---|
| `PCLib_CE_V16.2.xdd` | EcoStruxure Control Expert Classic V16.2 | Project Browser > Derived Data Types > Import |
| `PCLib_Ignition81.json` | Ignition 8.1 (Perspective) | Designer > Tag Browser > Data Types > Import Tags |

### Control Expert Classic V16.2

1. Import `export/PCLib_CE_V16.2.xdd` as described above, then **Analyze Project**.
2. Declare one instance per piece of equipment (e.g. `P101 : {p}Motor`).
3. For Ignition (or any OPC UA client) to read the instances by name, enable symbolic access:
   **Tools > Project Settings > PLC embedded data > Data dictionary**, then rebuild and download.
   Instances must be unlocated variables.

### Ignition 8.1 Perspective

The JSON holds 26 UDT definitions in a `PCLib` folder, matching the DDTs member for member.
Nested DDTs (`Mode`, `Alm_*`, `Run`, `Drv`...) are nested UDT instances. Arrays are folders with one tag per element.

1. In the Designer Tag Browser, select **Data Types**, click **Import Tags** (or right-click > Import Tags) and
   choose `export/PCLib_Ignition81.json`.
2. Create an OPC UA connection to the PLC (Gateway > Config > OPC Client > OPC Connections). Use the M580
   embedded OPC UA server, a BMENUA0100 module, or EcoStruxure OPC UA Server Expert.
3. Create an instance of a UDT under **Tags** (e.g. `P101` of type `PCLib/{p}Motor`) and set its parameters:

| Parameter | Meaning | Example |
|---|---|---|
| `OPCServer` | Ignition OPC connection name | `M580_Line1` |
| `PathPrefix` | Node-ID prefix used by your OPC server | `ns=2;s=` (check with the OPC Quick Client) |
| `BaseTag` | PLC instance name | `P101` |

   Each tag's OPC path is `{PathPrefix}{BaseTag}.<Member>`. Browse one variable in the OPC Quick Client
   first and copy its prefix, because the namespace index and path syntax differ between Schneider OPC servers.
4. In Perspective, bind faceplates to the instance (e.g. `[default]P101/Sts_State`). `Cfg_`, `Cmd_`, `Sim_`
   and `Prm_` tags are writable; everything else is read-only (ISA-101: the HMI never writes PLC status).

**Data type mapping**

| Control Expert | Ignition | Note |
|---|---|---|
| BOOL | Boolean | |
| INT | Int2 | |
| UINT, WORD, DINT | Int4 | |
| UDINT | Int8 | |
| REAL / LREAL | Float4 / Float8 | |
| TIME | Int4 | milliseconds (`engUnit` = ms) |
| DT | DateTime | if your OPC server delivers DT as a number, change these tags to Int8 |
| STRING[n] | String | |

**Alarms:** each `{p}Alarm` / `{p}AlmLim` UDT has an Ignition alarm on `Sts_Active`, so PLC alarms appear in the
Perspective Alarm Status Table and alarm journal. The alarm is enabled by `Cfg_En`, and its priority comes from
`Cfg_Priority` (1=Critical 2=High 3=Medium 4=Low). Acknowledging in Ignition runs a tag event script that writes
`Cmd_Ack` to the PLC, so the PLC alarm state (ISA-18.2) stays authoritative. Shelving is done in the PLC through
`Cmd_Shelve`; Ignition's own shelving only hides the alarm in Ignition.

"""


def readme(types, d, prefix, lreal):
    out = []
    w = out.append
    meta = {name: META[name[len(prefix):]] for name, *_ in types}
    w("# PCLib - Process Control DDT Library for EcoStruxure Control Expert\n")
    w(f"Version {LIB_VERSION}. {len(types)} Derived Data Types for common process-industry "
      "equipment, built for HMI faceplates and aligned with ISA-88, ISA-18.2, ISA-101, NAMUR NE107 "
      "and the other standards listed below.\n")
    w("Generated by `gen_pclib.py`. Edit the definitions there and re-run; do not hand-edit the .xdd files.\n")
    w("## Files\n")
    w("| File | Purpose |\n|---|---|")
    w("| `xdd/PCLib_All.xdd` | Every DDT in dependency order. **Import this one.** |")
    w("| `xdd/<Type>.xdd` | One DDT per file. Import its dependencies first (listed below). |")
    w("| `PCLib_Members.csv` | Flat member list with ISA-88 role and MTP mapping |")
    w("| `gen_pclib.py` | Source of truth / generator |\n")
    w("## Importing into Control Expert\n")
    w("1. Open the project. In the Project Browser, right-click **Derived Data Types** and choose **Import...**")
    w("2. Select `xdd/PCLib_All.xdd`. If a type already exists, choose whether to keep or replace it.")
    w("3. Run **Build > Analyze Project** to check the types.")
    w("4. Declare instances in the Data Editor, e.g. `P101 : " + prefix + "Motor;`, `FT101 : " + prefix + "AI;`.\n")
    w("The `.xdd` files leave out the checksum attributes; Control Expert works them out on import. "
      "If your version rejects the file header, export any DDT from your project and copy its "
      "`<fileHeader>` line into the generator.\n")
    if lreal:
        w("Totals use `LREAL`. If your CPU or firmware does not support LREAL, regenerate with "
          "`python gen_pclib.py --no-lreal`.\n")
    w(PLATFORM_IMPORT.replace("{p}", prefix))
    w("## Standards alignment\n")
    w("The standards define models, behaviour and terminology. Apart from MTP, they do not prescribe PLC "
      "data layouts. PCLib carries the data each model needs, so the DFBs you write can implement the "
      "behaviour. Alignment is by design; it is not a third-party certification. Values such as alarm "
      "priorities, limits and equipment states come from your own alarm philosophy, HMI philosophy and "
      "rationalisation.\n")
    w("| Standard | Scope | How PCLib applies it |\n|---|---|---|")
    for std, scope, how in STANDARDS:
        w(f"| {std} | {scope} | {how.format(p=prefix)} |")
    w("")
    w("### ISA-88 physical and procedural model\n")
    w("| ISA-88 level | PCLib types |\n|---|---|")
    roles = {}
    for name, *_ in types:
        roles.setdefault(meta[name][0].split(" (")[0], []).append(f"`{name}`")
    for role, names in roles.items():
        w(f"| {role} | {', '.join(names)} |")
    w("")
    w("Control modules take `Prog_` commands only from the owner that has acquired them through "
      "`Mode.Prog_Acquire` (ISA-88 arbitration). Out-of-service and Maintenance modes are site extensions; "
      "ISA-88 itself defines Automatic, Semi-automatic and Manual.\n")
    w("### Alarm state model (ISA-18.2 / IEC 62682)\n")
    w("`Sts_State`: " + ALARM_STATES + "\n")
    w("### Phase state model (ISA-88 Part 1)\n")
    w("`Sts_State`: " + PHASE_STATES + "  \nCommands (`Prog_Cmd`, `Sts_CmdMask` bit n): " + PHASE_CMDS + "\n")
    w("MTP services use a PackML-derived state model (Execute, Completing, Unholding...). If a phase is "
      "exposed as an MTP service, map Running to Execute, Complete to Completed, and so on.\n")
    w("### Equipment state (ISA-88)\n")
    w("`Sts_EqState` on `" + prefix + "Unit` and `" + prefix + "Tank`: " + EQSTATE + "\n")
    w("## Conventions\n")
    w("| Prefix | Meaning | Written by |\n|---|---|---|")
    w("| `Inp_` | Field / upstream input | I/O mapping or upstream logic |")
    w("| `Cfg_` | Configuration / tuning | Engineer (HMI with access control) |")
    w("| `Cmd_` | Operator command. Booleans are **one-shot**: the logic clears them after acting | HMI |")
    w("| `Prog_` | Command from the ISA-88 owner (phase, equipment module, batch server) | Owner logic |")
    w("| `Prm_` / `Rpt_` | ISA-88 recipe parameters / report values | Batch server / phase logic |")
    w("| `Out_` | Output to field or downstream logic | Equipment logic |")
    w("| `Sts_` | Status | Equipment logic |")
    w("| `Val_` | Calculated value | Equipment logic |")
    w("| `Alm_` | Alarm (" + prefix + "Alarm / " + prefix + "AlmLim) | Equipment logic sets `Inp_Cond` |")
    w("| `Sim_` | Simulation | Engineer |\n")
    w("- Booleans ending in `OK` are **TRUE = healthy**, so a broken wire or lost signal reads as unhealthy. "
      "Other `Inp_` booleans are TRUE when the condition is present.")
    w("- Interlocks (`Inp_IntlkOK`) stop running equipment. Permissives (`Inp_PermOK`) only block a start.")
    w("- `Sts_State` / `Sts_Mode` / `Sts_NE107` integers are for HMI animation. The values are listed in each member comment.")
    w("- These are **data types only**. Pair each one with a DFB (or ST section) holding the behaviour. "
      "Most types are laid out so a DFB can take the whole DDT as one IN_OUT parameter.\n")
    w("> **Safety:** `" + prefix + "ESD`, `" + prefix + "Intlk` and `" + prefix + "GasDet` are for the basic "
      "process control layer and HMI. Safety Instrumented Functions with a SIL target must run in a "
      "certified safety controller (e.g. M580 Safety, SAFE task) and follow IEC 61511.\n")
    w("## Type index\n")
    w("| Type | ISA-88 role | MTP equivalent | Members | Depends on |\n|---|---|---|---|---|")
    for name, comment, members, group in types:
        dep = ", ".join(sorted(d[name])) or "-"
        role, mtp, _ = meta[name]
        w(f"| [`{name}`](#{name.lower()}) | {role} | {mtp} | {len(members)} | {dep} |")
    w("")
    for g in GROUP_TITLES:
        w(f"## {GROUP_TITLES[g]}\n")
        for name, comment, members, group in types:
            if group != g:
                continue
            role, mtp, stds = meta[name]
            w(f"### {name}\n")
            w(f"{comment}.\n")
            w(f"**ISA-88 role:** {role} | **MTP:** {mtp} | **Standards:** {', '.join(stds)}\n")
            w("| Member | Type | Init | Description |\n|---|---|---|---|")
            for mname, mtype, mcomment, init in members:
                w(f"| `{mname}` | `{mtype}` | {init or ''} | {mcomment.replace('|', '/')} |")
            w("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Ignition 8.1 UDT export (Designer > Tag Browser > Data Types > Import Tags)
# ---------------------------------------------------------------------------
IGN_TYPES = {
    "BOOL": "Boolean", "INT": "Int2", "UINT": "Int4", "WORD": "Int4", "DINT": "Int4",
    "UDINT": "Int8", "REAL": "Float4", "LREAL": "Float8", "TIME": "Int4", "DT": "DateTime",
}
# Prefixes the HMI may write. Everything else is written by the PLC and is read-only in Ignition.
IGN_WRITABLE = {"Cfg", "Cmd", "Sim", "Prm"}
IGN_FOLDER = "PCLib"
IGN_PARAMS = {
    "OPCServer": "Name of the OPC UA connection to the PLC (Gateway > OPC Connections)",
    "PathPrefix": "Node ID prefix for the PLC server, e.g. ns=2;s=",
    "BaseTag": "PLC instance name of this DDT, e.g. P101",
}

# Ignition AlarmPriority: 0=Diagnostic 1=Low 2=Medium 3=High 4=Critical
IGN_PRIORITY = "case({[.]Cfg_Priority}, 1, 4, 2, 3, 3, 2, 4, 1, 2)"
IGN_ACK_SCRIPT = ("\t# Operator acknowledged in Ignition -> write Cmd_Ack to the PLC alarm object\n"
                  "\tbase = str(tagPath).rsplit('/', 1)[0]\n"
                  "\tsystem.tag.writeBlocking([base + '/Cmd_Ack'], [True])")


def _pbind(expr):
    return {"bindType": "parameter", "binding": expr}


def _ign_atomic(name, ctype, comment, plc_path):
    base_t = ctype
    tag = {
        "name": name,
        "tagType": "AtomicTag",
        "valueSource": "opc",
        "opcServer": _pbind("{OPCServer}"),
        "opcItemPath": _pbind("{PathPrefix}{BaseTag}." + plc_path),
        "documentation": comment,
        "tooltip": comment,
    }
    if base_t.startswith("STRING"):
        tag["dataType"] = "String"
    else:
        tag["dataType"] = IGN_TYPES[base_t]
    if base_t == "TIME":
        tag["engUnit"] = "ms"
    if name.split("_")[0] not in IGN_WRITABLE:
        tag["readOnly"] = True
    return tag


def ign_member(mname, mtype, comment, udt_names, sub_name=None, path=None):
    name = sub_name or mname
    path = path or mname
    m = ARRAY.match(mtype)
    if m:
        lo, hi, base = int(m.group(1)), int(m.group(2)), m.group(3)
        tags = [ign_member(mname, base, f"{comment} [{i}]", udt_names, str(i), f"{path}[{i}]")
                for i in range(lo, hi + 1)]
        return {"name": name, "tagType": "Folder", "tags": tags}
    if mtype in udt_names:
        return {
            "name": name,
            "tagType": "UdtInstance",
            "typeId": f"{IGN_FOLDER}/{mtype}",
            "documentation": comment,
            "parameters": {
                "OPCServer": {"dataType": "String", "value": _pbind("{OPCServer}")},
                "PathPrefix": {"dataType": "String", "value": _pbind("{PathPrefix}")},
                "BaseTag": {"dataType": "String", "value": _pbind("{BaseTag}." + path)},
            },
        }
    # sub_name set => array element: writability follows the array member name
    tag = _ign_atomic(mname, mtype, comment, path)
    tag["name"] = name
    return tag


def ignition_json(types, prefix):
    udt_names = {t[0] for t in types}
    alarm_types = {prefix + "Alarm", prefix + "AlmLim"}
    udts = []
    for name, comment, members, _ in types:
        tags = [ign_member(mn, mt, mc, udt_names) for mn, mt, mc, _ in members]
        if name in alarm_types:
            for t in tags:
                if t["name"] == "Sts_Active":
                    t["alarms"] = [{
                        "name": "Alarm",
                        "mode": "Equality",
                        "setpointA": 1.0,
                        "enabled": {"bindType": "Expression", "value": "{[.]Cfg_En}"},
                        "priority": {"bindType": "Expression", "value": IGN_PRIORITY},
                    }]
                    t["eventScripts"] = [{"eventid": "alarmAcknowledged", "script": IGN_ACK_SCRIPT}]
        udts.append({
            "name": name,
            "tagType": "UdtType",
            "documentation": comment,
            "parameters": {k: {"dataType": "String", "value": ""} for k in IGN_PARAMS},
            "tags": tags,
        })
    return {"name": IGN_FOLDER, "tagType": "Folder", "tags": udts}


def lp(path):
    """Long-path safe file name on Windows (paths over 260 chars)."""
    path = os.path.abspath(path)
    if os.name == "nt" and not path.startswith("\\\\?\\"):
        path = "\\\\?\\" + path
    return path


def count_ign(node):
    if node.get("tagType") == "AtomicTag":
        return 1
    return sum(count_ign(t) for t in node.get("tags", []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="T_")
    ap.add_argument("--no-lreal", action="store_true")
    ap.add_argument("--ce-product", default="EcoStruxure Control Expert Classic V16.2",
                    help="Product string written to the .xdd file header")
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()

    validate(TYPES)
    types = resolve(TYPES, a.prefix, not a.no_lreal)
    d = deps(types)
    now = dt.datetime.now().replace(microsecond=0)

    xdir = os.path.join(a.out, "xdd")
    os.makedirs(xdir, exist_ok=True)
    files = {"PCLib_All.xdd": xdd_text(types, now, a.ce_product)}
    for t in types:
        files[f"{t[0]}.xdd"] = xdd_text([t], now, a.ce_product)
    for fn, txt in files.items():
        ET.fromstring(txt.encode("utf-8"))           # well-formedness check
        with open(lp(os.path.join(xdir, fn)), "w", encoding="utf-8", newline="\r\n") as f:
            f.write(txt)

    # Platform import files
    exp = os.path.join(a.out, "export")
    os.makedirs(exp, exist_ok=True)
    with open(lp(os.path.join(exp, "PCLib_CE_V16.2.xdd")), "w", encoding="utf-8",
              newline="\r\n") as f:
        f.write(files["PCLib_All.xdd"])
    ign = ignition_json(types, a.prefix)
    ign_txt = json.dumps(ign, indent=2)
    json.loads(ign_txt)
    with open(lp(os.path.join(exp, "PCLib_Ignition81.json")), "w", encoding="utf-8") as f:
        f.write(ign_txt)
    print(f"Ignition: {len(ign['tags'])} UDT definitions, {count_ign(ign)} atomic tags")

    with open(lp(os.path.join(a.out, "PCLib_Members.csv")), "w", encoding="utf-8-sig", newline="") as f:
        cw = csv.writer(f)
        cw.writerow(["Type", "ISA88Role", "MTP", "Member", "DataType", "Init", "Comment"])
        for name, _, members, _ in types:
            role, mtp, _ = META[name[len(a.prefix):]]
            for mname, mtype, mcomment, init in members:
                cw.writerow([name, role, mtp, mname, mtype, init or "", mcomment])

    with open(lp(os.path.join(a.out, "README.md")), "w", encoding="utf-8") as f:
        f.write(readme(types, d, a.prefix, not a.no_lreal))

    total = sum(len(t[2]) for t in types)
    print(f"{len(types)} DDTs, {total} members -> {xdir}")


if __name__ == "__main__":
    main()
