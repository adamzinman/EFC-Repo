"""
PCLib phase generator - ISA-88 equipment phase DFBs for Control Expert Classic V16.2,
the T_SeqBar sequence-bar DDT and the matching Ignition 8.1 Perspective sequence bar.

Produces:
  dfb/FB_PhaseCore.st, dfb/FB_Phase.st, dfb/FB_PhXeFill.st
                                         IEC 61131-3 textual POUs (review / version control)
  export/PCLib_DFB_Phase_CE_V16.2.xdb    Control Expert DFB import file (T_Phase, T_SeqBar, T_FillStn, T_XeFill, DFBs)
  export/T_SeqBar.xdd                    Control Expert DDT import file (T_SeqBar only)
  examples/XeFill_Unit.st                Example unit program: one fill sequence for 6 stations
  ignition/PCLib_XeFill_UDTs.json        Ignition UDTs _types_/PCLib/T_SeqBar and XeFill_Station (OPC tags)
  ignition/PCLib_XeFill_Demo_Tags.json   Memory-tag demo: SeqBar_Demo and XeFill_Demo (bar + six stations)
  ignition/EFC_XeFill_HMI.zip            Perspective project: SequenceBar, the EFC Station faceplates
                                         (ignition/station_views, unchanged), Station_Tile, XeFill/Overview

DFBs:
  FB_PhaseCore  ISA-88 Part 1 state machine, commands, modes, ownership, watchdog,
                alarms and sequence bar. Shared by every phase; never edited per phase.
  FB_Phase      TEMPLATE. Copy it, rename it FB_Ph<Name>, add pins and write the
                sequence in its open area. It calls FB_PhaseCore.
  FB_PhXeFill   Example: ONE sequence fills any number of xenon stations by weight from the
                source cylinder and compressor; each station's inlet closes as it finishes.

The DFBs reuse FB_Alarm / FB_AlmCore and T_Alarm from PCLib_DFB_AI_CE_V16.2.xdb (gen_dfb.py).
Import that file first, or pass its path with --alarm-xdb to copy those types into this export.

Usage:  python gen_phase.py [--alarm-xdb export/PCLib_DFB_AI_CE_V16.2.xdb]
"""
import argparse
import datetime as dt
import json
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from xml.sax.saxutils import escape, quoteattr

LIB_VERSION = "1.00"
PRODUCT = "EcoStruxure Control Expert Classic V16.2"
HERE = os.path.dirname(os.path.abspath(__file__))
NSEG = 10                      # sequence-bar segments carried by T_SeqBar


def V(name, typ, comment, init=None):
    return (name, typ, comment, init)


PHASE_STATES = ("ISA-88 state: 0=Idle 1=Running 2=Complete 3=Pausing 4=Paused 5=Holding 6=Held "
                "7=Restarting 8=Stopping 9=Stopped 10=Aborting 11=Aborted")
SEG_STATES = "0=Pending 1=Active 2=Done 3=Fault 4=Held/Paused/Waiting 5=Skipped"

# ---------------------------------------------------------------------------------
# DDTs
# ---------------------------------------------------------------------------------
# T_Phase: copied from PCLib (gen_pclib.py). Keep identical; the import asks Keep/Replace.
T_PHASE = dict(
    name="T_Phase",
    comment="ISA-88 equipment phase: Part 1 state model, commands, modes, parameters, reports",
    members=[
        V("Cfg_Tag", "STRING[20]", "Equipment / instrument tag, e.g. FT-101"),
        V("Cfg_Desc", "STRING[40]", "Description shown on HMI faceplate"),
        V("Cfg_PhaseID", "INT", "Phase ID (unique in the unit) for batch server / unit procedure"),
        V("Cfg_UnitID", "INT", "ID of the unit this phase belongs to"),
        V("Cfg_StepTimeout", "TIME", "Step watchdog, T#0S = off", "T#0S"),
        V("Cmd_Auto", "BOOL", "Operator request Automatic mode (one-shot)"),
        V("Cmd_SemiAuto", "BOOL", "Operator request Semi-automatic mode (one-shot)"),
        V("Cmd_Man", "BOOL", "Operator request Manual mode (one-shot)"),
        V("Cmd_Start", "BOOL", "Operator Start (one-shot)"),
        V("Cmd_Stop", "BOOL", "Operator Stop (one-shot)"),
        V("Cmd_Hold", "BOOL", "Operator Hold (one-shot)"),
        V("Cmd_Restart", "BOOL", "Operator Restart from Held (one-shot)"),
        V("Cmd_Abort", "BOOL", "Operator Abort (one-shot)"),
        V("Cmd_Reset", "BOOL", "Operator Reset to Idle (one-shot)"),
        V("Cmd_Pause", "BOOL", "Operator Pause at next transition (one-shot)"),
        V("Cmd_Resume", "BOOL", "Operator Resume from Paused (one-shot)"),
        V("Cmd_Advance", "BOOL", "Advance to next step in Semi-automatic (one-shot)"),
        V("Cmd_TakeOwn", "BOOL", "Operator takes control from the recipe (one-shot)"),
        V("Prog_Cmd", "INT", "Command from batch server / unit procedure: 1=Start 2=Stop 3=Hold "
                             "4=Restart 5=Abort 6=Reset 7=Pause 8=Resume"),
        V("Prog_Acquire", "BOOL", "Recipe (batch server / unit procedure) takes ownership"),
        V("Prog_Release", "BOOL", "Recipe releases ownership"),
        V("Prog_ReqAck", "BOOL", "Batch server acknowledges Sts_ReqCode"),
        V("Prm_Real", "ARRAY[1..16] OF REAL", "Recipe parameters (REAL) - control recipe formula"),
        V("Prm_DInt", "ARRAY[1..8] OF DINT", "Recipe parameters (DINT) - control recipe formula"),
        V("Rpt_Real", "ARRAY[1..16] OF REAL", "Report values (REAL) returned to batch record"),
        V("Rpt_DInt", "ARRAY[1..8] OF DINT", "Report values (DINT) returned to batch record"),
        V("Val_BatchID", "STRING[32]", "Batch ID of the control recipe running this phase"),
        V("Val_StateTime", "TIME", "Time in current state"),
        V("Val_RunTime", "TIME", "Running time excluding Held / Paused"),
        V("Val_FailText", "STRING[40]", "Failure description for HMI / batch record"),
        V("Sts_State", "INT", PHASE_STATES),
        V("Sts_PrevState", "INT", "Previous state (for Restart / diagnostics)"),
        V("Sts_Mode", "INT", "ISA-88 mode: 1=Manual 2=Semi-automatic 3=Automatic"),
        V("Sts_Owner", "INT", "0=Operator 1=Recipe (batch server / unit procedure)"),
        V("Sts_CmdMask", "WORD", "Commands valid in current state (bit n = command n of Prog_Cmd) - for HMI"),
        V("Sts_CmdRejected", "BOOL", "Last command was not valid in the current state"),
        V("Sts_Step", "INT", "Active step number within the state logic"),
        V("Sts_WaitAdvance", "BOOL", "Semi-automatic: waiting for Cmd_Advance"),
        V("Sts_ReqCode", "INT", "Request to batch server (e.g. download params, upload reports), 0 = none"),
        V("Sts_FailCode", "INT", "Failure code, 0 = none"),
        V("Alm_Fail", "T_Alarm", "Phase failure"),
        V("Alm_StepTimeout", "T_Alarm", "Step exceeded Cfg_StepTimeout"),
    ])

T_SEQBAR = dict(
    name="T_SeqBar",
    comment="Sequence bar for a T_Phase: segment labels and states for the HMI step bar",
    members=[
        V("Cfg_Title", "STRING[24]", "Title shown on the sequence bar"),
        V("Cfg_NumSeg", "INT", f"Segments shown (1..{NSEG}); 0 = labels not loaded yet", "0"),
        V("Cfg_SegText", f"ARRAY[1..{NSEG}] OF STRING[12]", "Segment labels"),
        V("Sts_Seg", f"ARRAY[1..{NSEG}] OF INT", "Segment state: " + SEG_STATES),
        V("Sts_Skip", f"ARRAY[1..{NSEG}] OF BOOL", "Segment skipped this run (set by phase logic, cleared at Start)"),
        V("Sts_ActSeg", "INT", "Active segment, 0 = none"),
        V("Sts_PhState", "INT", "Copy of T_Phase.Sts_State"),
        V("Sts_Mode", "INT", "Copy of T_Phase.Sts_Mode"),
        V("Sts_Owner", "INT", "Copy of T_Phase.Sts_Owner"),
        V("Sts_Step", "INT", "Copy of T_Phase.Sts_Step"),
        V("Sts_WaitAdv", "BOOL", "Semi-automatic: waiting for Advance"),
        V("Sts_Fail", "BOOL", "Phase failure active"),
        V("Val_Msg", "STRING[40]", "Operator message: step text, state or failure text"),
        V("Val_StepTime", "TIME", "Time in the current step"),
        V("Val_StepPct", "INT", "Progress within the active segment, 0..100"),
    ])

# ---------------------------------------------------------------------------------
# FB_PhaseCore
# ---------------------------------------------------------------------------------
CORE = dict(
    name="FB_PhaseCore",
    comment="ISA-88 phase core for a T_Phase: state machine, commands, modes, ownership, step watchdog, "
            "alarms and T_SeqBar sequence bar. Called by every FB_Ph* phase after its sequence logic",
    inputs=[
        V("PermOK", "BOOL", "Start permissives OK (blocks Start and Restart only)"),
        V("IntlkOK", "BOOL", "Interlocks healthy. FALSE while running -> Holding (or Aborting)"),
        V("IntlkAbort", "BOOL", "TRUE = interlock trip aborts instead of holding"),
        V("EStop", "BOOL", "Emergency stop active -> Aborting"),
        V("Trans", "BOOL", "Sequence: go to NextStep (Pause / Semi-auto applied here)"),
        V("NextStep", "INT", "Sequence: step to go to"),
        V("StateDone", "BOOL", "Sequence: logic of the current state finished"),
        V("FailCode", "INT", "Sequence: failure code, 0 = none (-> Holding)"),
        V("FailText", "STRING[40]", "Sequence: failure text"),
        V("Seg", "INT", "Sequence: sequence-bar segment of the active step"),
        V("Msg", "STRING[40]", "Sequence: operator message for the active step"),
        V("Pct", "INT", "Sequence: progress within the segment, 0..100"),
        V("StepTmo", "TIME", "Sequence: watchdog for this step, T#0S = Ph.Cfg_StepTimeout"),
        V("WdogOff", "BOOL", "Sequence: no watchdog in this step"),
    ],
    inouts=[
        V("Ph", "T_Phase", "Phase object"),
        V("Bar", "T_SeqBar", "Sequence bar for the HMI"),
    ],
    outputs=[
        V("StepEntry", "BOOL", "TRUE for the first scan of a step (read by the sequence on the next call)"),
        V("StepTime", "TIME", "Time in the current step"),
        V("ScanTime", "TIME", "Time since the previous call (for timers kept in arrays)"),
        V("RunStep", "INT", "Running step the phase resumes at after Restart"),
        V("Running", "BOOL", "State Running or Pausing"),
        V("Held", "BOOL", "State Held"),
        V("Complete", "BOOL", "State Complete"),
        V("Failed", "BOOL", "Failure active (Ph.Sts_FailCode <> 0)"),
    ],
    private=[
        V("xFirst", "BOOL", "First scan after cold / warm start", "TRUE"),
        V("tonClk", "TON", "Free-running clock for elapsed time"),
        V("xClkRst", "BOOL", "Clock restart"),
        V("tClkLast", "TIME", "Clock value on previous scan"),
        V("tDelta", "TIME", "Time since previous scan"),
        V("iSt", "INT", "State at the start of the scan"),
        V("iReq", "INT", "Requested state"),
        V("iCmd", "INT", "Command this scan (Prog_Cmd numbering)"),
        V("iCmdSt", "INT", "State the command leads to"),
        V("xValid", "BOOL", "Command valid in the current state"),
        V("xRej", "BOOL", "Command rejected this scan"),
        V("xAnyCmd", "BOOL", "A command arrived this scan"),
        V("xOkStart", "BOOL", "Start valid"),
        V("xOkStop", "BOOL", "Stop valid"),
        V("xOkHold", "BOOL", "Hold valid"),
        V("xOkRestart", "BOOL", "Restart valid"),
        V("xOkAbort", "BOOL", "Abort valid"),
        V("xOkReset", "BOOL", "Reset valid"),
        V("xOkPause", "BOOL", "Pause valid"),
        V("xOkResume", "BOOL", "Resume valid"),
        V("iMask", "INT", "Command mask being built"),
        V("xRunSt", "BOOL", "Requested state executes the procedure (1, 3, 4, 7)"),
        V("xWait", "BOOL", "Semi-automatic: step waiting for Advance"),
        V("xAdv", "BOOL", "Advance given this scan: the waiting step starts"),
        V("iRunStep", "INT", "Running step saved on Hold / Stop / Abort"),
        V("iLastState", "INT", "State on previous scan", "-1"),
        V("iLastStep", "INT", "Step on previous scan"),
        V("tStep", "TIME", "Time in step"),
        V("tLimit", "TIME", "Watchdog limit for the step"),
        V("iSeg", "INT", "Active sequence-bar segment"),
        V("nSeg", "INT", "Segments in use"),
        V("iBar", "INT", "Segment state being built"),
        V("i", "INT", "Loop index"),
        V("fbFail", "FB_Alarm", "Phase failure alarm"),
        V("fbTmo", "FB_Alarm", "Step timeout alarm"),
    ],
    code=r"""
(* ===== 1. Elapsed time since previous scan (free-running TON, restarts hourly) ===== *)
tonClk(IN := NOT xClkRst, PT := T#1H);
xClkRst := tonClk.Q;
IF tonClk.ET >= tClkLast THEN
    tDelta := tonClk.ET - tClkLast;
ELSE
    tDelta := T#0S;
END_IF;
tClkLast := tonClk.ET;

(* ===== 2. First scan: defaults ===== *)
IF xFirst THEN
    IF (Ph.Sts_State < 0) OR (Ph.Sts_State > 11) THEN
        Ph.Sts_State := 0;
    END_IF;
    IF (Ph.Sts_Mode < 1) OR (Ph.Sts_Mode > 3) THEN
        Ph.Sts_Mode := 3;
    END_IF;
END_IF;
iSt := Ph.Sts_State;
iReq := iSt;
xRej := FALSE;
xAnyCmd := FALSE;

(* ===== 3. Ownership (ISA-88 arbitration) and mode ===== *)
IF Ph.Prog_Acquire THEN
    Ph.Sts_Owner := 1;
END_IF;
IF Ph.Prog_Release OR Ph.Cmd_TakeOwn THEN
    Ph.Sts_Owner := 0;
END_IF;
IF Ph.Sts_Owner = 1 THEN
    Ph.Sts_Mode := 3;                                   (* recipe control runs in Automatic *)
    IF Ph.Cmd_Auto OR Ph.Cmd_SemiAuto OR Ph.Cmd_Man THEN
        xRej := TRUE;
        xAnyCmd := TRUE;
    END_IF;
ELSIF Ph.Cmd_Auto THEN
    Ph.Sts_Mode := 3;
ELSIF Ph.Cmd_SemiAuto THEN
    Ph.Sts_Mode := 2;
ELSIF Ph.Cmd_Man THEN
    Ph.Sts_Mode := 1;
END_IF;

(* ===== 4. Commands valid in the current state (ISA-88 Part 1 state model) ===== *)
xOkStart := (iSt = 0) AND PermOK AND IntlkOK AND NOT EStop AND (Ph.Sts_Mode <> 1);
xOkStop := (iSt = 1) OR (iSt = 3) OR (iSt = 4) OR (iSt = 5) OR (iSt = 6) OR (iSt = 7);
xOkHold := (iSt = 1) OR (iSt = 3) OR (iSt = 4) OR (iSt = 7);
xOkRestart := (iSt = 6) AND PermOK AND IntlkOK AND NOT EStop AND (Ph.Sts_Mode <> 1);
xOkAbort := xOkStop OR (iSt = 8);
xOkReset := (iSt = 2) OR (iSt = 9) OR (iSt = 11);
xOkPause := (iSt = 1);
xOkResume := (iSt = 3) OR (iSt = 4);

iMask := 0;                                             (* bit n = command n of Prog_Cmd *)
IF xOkStart THEN iMask := iMask + 2; END_IF;
IF xOkStop THEN iMask := iMask + 4; END_IF;
IF xOkHold THEN iMask := iMask + 8; END_IF;
IF xOkRestart THEN iMask := iMask + 16; END_IF;
IF xOkAbort THEN iMask := iMask + 32; END_IF;
IF xOkReset THEN iMask := iMask + 64; END_IF;
IF xOkPause THEN iMask := iMask + 128; END_IF;
IF xOkResume THEN iMask := iMask + 256; END_IF;
Ph.Sts_CmdMask := INT_TO_WORD(iMask);

(* ===== 5. Command source: recipe (Prog_Cmd) or operator (Cmd_) ===== *)
(* The operator can always Hold, Stop or Abort. Start, Restart, Reset, Pause and
   Resume need ownership (Sts_Owner = 0) while a recipe owns the phase. *)
iCmd := 0;
IF Ph.Prog_Cmd <> 0 THEN
    xAnyCmd := TRUE;
    IF (Ph.Sts_Owner = 1) AND (Ph.Prog_Cmd >= 1) AND (Ph.Prog_Cmd <= 8) THEN
        iCmd := Ph.Prog_Cmd;
    ELSE
        xRej := TRUE;
    END_IF;
END_IF;
IF Ph.Cmd_Abort THEN
    iCmd := 5;
ELSIF Ph.Cmd_Stop THEN
    iCmd := 2;
ELSIF Ph.Cmd_Hold THEN
    iCmd := 3;
ELSIF Ph.Cmd_Start OR Ph.Cmd_Restart OR Ph.Cmd_Reset OR Ph.Cmd_Pause OR Ph.Cmd_Resume THEN
    IF Ph.Sts_Owner = 0 THEN
        IF Ph.Cmd_Start THEN
            iCmd := 1;
        ELSIF Ph.Cmd_Restart THEN
            iCmd := 4;
        ELSIF Ph.Cmd_Reset THEN
            iCmd := 6;
        ELSIF Ph.Cmd_Pause THEN
            iCmd := 7;
        ELSE
            iCmd := 8;
        END_IF;
    ELSE
        xRej := TRUE;
        xAnyCmd := TRUE;
    END_IF;
END_IF;

CASE iCmd OF
    1: xValid := xOkStart;   iCmdSt := 1;
    2: xValid := xOkStop;    iCmdSt := 8;
    3: xValid := xOkHold;    iCmdSt := 5;
    4: xValid := xOkRestart; iCmdSt := 7;
    5: xValid := xOkAbort;   iCmdSt := 10;
    6: xValid := xOkReset;   iCmdSt := 0;
    7: xValid := xOkPause;   iCmdSt := 3;
    8: xValid := xOkResume;  iCmdSt := 1;
ELSE
    xValid := FALSE;
    iCmdSt := iSt;
END_CASE;
IF iCmd <> 0 THEN
    xAnyCmd := TRUE;
    IF xValid THEN
        iReq := iCmdSt;
    ELSE
        xRej := TRUE;
    END_IF;
END_IF;
IF xAnyCmd THEN
    Ph.Sts_CmdRejected := xRej;
END_IF;

(* ===== 6. Protective conditions override commands ===== *)
xRunSt := (iReq = 1) OR (iReq = 3) OR (iReq = 4) OR (iReq = 7);
IF EStop AND (xRunSt OR (iReq = 5) OR (iReq = 6) OR (iReq = 8)) THEN
    iReq := 10;
ELSIF NOT IntlkOK AND xRunSt THEN
    IF IntlkAbort THEN
        iReq := 10;
    ELSE
        iReq := 5;
    END_IF;
ELSIF (Ph.Sts_Mode = 1) AND xRunSt THEN
    iReq := 5;                                          (* Manual mode: phase logic must not drive *)
END_IF;

(* ===== 7. Requests from the sequence (only when no state change is pending) ===== *)
IF iReq = iSt THEN
    IF (FailCode <> 0) AND (Ph.Sts_FailCode = 0) THEN
        Ph.Sts_FailCode := FailCode;
        Ph.Val_FailText := FailText;
        IF (iSt = 1) OR (iSt = 3) OR (iSt = 4) OR (iSt = 7) THEN
            iReq := 5;
        END_IF;
    ELSIF StateDone THEN
        CASE iSt OF
            1, 3: iReq := 2;
            5: iReq := 6;
            7: iReq := 1;
            8: iReq := 9;
            10: iReq := 11;
        END_CASE;
    ELSIF Trans THEN
        Ph.Sts_Step := NextStep;
        IF iSt = 3 THEN
            iReq := 4;                                  (* Pausing: pause before the next step runs *)
        ELSIF (iSt = 1) AND (Ph.Sts_Mode = 2) THEN
            xWait := TRUE;                              (* Semi-automatic: next step waits for Advance *)
        END_IF;
    END_IF;
END_IF;
xAdv := FALSE;
IF xWait AND (iReq = 1) AND (Ph.Cmd_Advance OR (Ph.Sts_Mode = 3)) THEN
    xWait := FALSE;
    xAdv := TRUE;                                       (* the waiting step starts now *)
END_IF;
IF xWait AND (iReq = 3) THEN
    iReq := 4;                                          (* already at a step boundary *)
END_IF;

(* ===== 8. State change and entry actions ===== *)
IF iReq <> iSt THEN
    Ph.Sts_PrevState := iSt;
    Ph.Sts_State := iReq;
    Ph.Val_StateTime := T#0S;
    CASE iReq OF
        0:  (* Reset to Idle *)
            Ph.Sts_Step := 0;
            Ph.Sts_FailCode := 0;
            Ph.Val_FailText := '';
            iRunStep := 0;
            iSeg := 0;
        1:  IF iSt = 0 THEN                             (* Start *)
                Ph.Sts_Step := 10;
                Ph.Val_RunTime := T#0S;
                Ph.Sts_FailCode := 0;
                Ph.Val_FailText := '';
                FOR i := 1 TO 16 DO
                    Ph.Rpt_Real[i] := 0.0;
                END_FOR;
                FOR i := 1 TO 8 DO
                    Ph.Rpt_DInt[i] := 0;
                END_FOR;
                FOR i := 1 TO 10 DO
                    Bar.Sts_Skip[i] := FALSE;
                END_FOR;
                iRunStep := 0;
                iSeg := 0;
            ELSIF iSt = 7 THEN                          (* Restarting finished: resume *)
                Ph.Sts_Step := iRunStep;
            END_IF;                                     (* from Pausing / Paused: continue at Sts_Step *)
        5, 8, 10:
            IF (iSt = 1) OR (iSt = 3) OR (iSt = 4) THEN
                iRunStep := Ph.Sts_Step;
            END_IF;
            Ph.Sts_Step := 10;
        7:  (* Restart: failure is cleared; it is reported again if the cause persists *)
            Ph.Sts_Step := 10;
            Ph.Sts_FailCode := 0;
            Ph.Val_FailText := '';
    END_CASE;
    xWait := FALSE;
END_IF;
Ph.Sts_WaitAdvance := xWait AND (Ph.Sts_State = 1);

(* ===== 9. Step entry and times ===== *)
StepEntry := xFirst OR xAdv OR (Ph.Sts_State <> iLastState) OR (Ph.Sts_Step <> iLastStep);
IF StepEntry THEN
    tStep := T#0S;
ELSE
    tStep := tStep + tDelta;
END_IF;
iLastState := Ph.Sts_State;
iLastStep := Ph.Sts_Step;
IF iReq = iSt THEN
    Ph.Val_StateTime := Ph.Val_StateTime + tDelta;
END_IF;
IF (Ph.Sts_State = 1) OR (Ph.Sts_State = 3) THEN
    Ph.Val_RunTime := Ph.Val_RunTime + tDelta;
END_IF;

(* ===== 10. Step watchdog and alarms (ISA-18.2 via FB_Alarm) ===== *)
IF StepTmo > T#0S THEN
    tLimit := StepTmo;
ELSE
    tLimit := Ph.Cfg_StepTimeout;
END_IF;
Ph.Alm_StepTimeout.Inp_Cond := (tLimit > T#0S) AND (tStep > tLimit) AND NOT WdogOff
                               AND NOT Ph.Sts_WaitAdvance
                               AND ((Ph.Sts_State = 1) OR (Ph.Sts_State = 3) OR (Ph.Sts_State = 5)
                                    OR (Ph.Sts_State = 7) OR (Ph.Sts_State = 8) OR (Ph.Sts_State = 10));
fbTmo(SuppressIn := FALSE, Alm := Ph.Alm_StepTimeout);
Ph.Alm_Fail.Inp_Cond := Ph.Sts_FailCode <> 0;
fbFail(SuppressIn := FALSE, Alm := Ph.Alm_Fail);

(* ===== 11. Batch server request handshake ===== *)
IF Ph.Prog_ReqAck THEN
    Ph.Sts_ReqCode := 0;
    Ph.Prog_ReqAck := FALSE;
END_IF;

(* ===== 12. Sequence bar ===== *)
IF ((iSt = 1) OR (iSt = 3)) AND (Seg >= 1) AND (Seg <= 10) AND (Ph.Sts_State <> 0) THEN
    iSeg := Seg;                                        (* latched: kept while held / stopped *)
END_IF;
nSeg := LIMIT(0, Bar.Cfg_NumSeg, 10);
FOR i := 1 TO 10 DO
    IF (i > nSeg) OR (Ph.Sts_State = 0) THEN
        iBar := 0;
    ELSIF Ph.Sts_State = 2 THEN
        IF Bar.Sts_Skip[i] THEN iBar := 5; ELSE iBar := 2; END_IF;
    ELSIF i < iSeg THEN
        IF Bar.Sts_Skip[i] THEN iBar := 5; ELSE iBar := 2; END_IF;
    ELSIF i > iSeg THEN
        iBar := 0;
    ELSIF (Ph.Sts_FailCode <> 0) OR (Ph.Sts_State = 10) OR (Ph.Sts_State = 11) THEN
        iBar := 3;
    ELSIF (Ph.Sts_State = 1) AND NOT Ph.Sts_WaitAdvance THEN
        iBar := 1;
    ELSIF Ph.Sts_State = 3 THEN
        iBar := 1;
    ELSE
        iBar := 4;                                      (* paused, held, stopped or waiting *)
    END_IF;
    Bar.Sts_Seg[i] := iBar;
END_FOR;
Bar.Sts_ActSeg := iSeg;
Bar.Sts_PhState := Ph.Sts_State;
Bar.Sts_Mode := Ph.Sts_Mode;
Bar.Sts_Owner := Ph.Sts_Owner;
Bar.Sts_Step := Ph.Sts_Step;
Bar.Sts_WaitAdv := Ph.Sts_WaitAdvance;
Bar.Sts_Fail := Ph.Sts_FailCode <> 0;
Bar.Val_StepTime := tStep;
IF Ph.Sts_FailCode <> 0 THEN
    Bar.Val_Msg := Ph.Val_FailText;
ELSIF Ph.Sts_WaitAdvance THEN
    Bar.Val_Msg := 'Waiting for Advance';
ELSE
    CASE Ph.Sts_State OF
        0: Bar.Val_Msg := 'Idle';
        1, 3: Bar.Val_Msg := Msg;
        2: Bar.Val_Msg := 'Complete';
        4: Bar.Val_Msg := 'Paused';
        5: Bar.Val_Msg := 'Holding';
        6: Bar.Val_Msg := 'Held';
        7: Bar.Val_Msg := 'Restarting';
        8: Bar.Val_Msg := 'Stopping';
        9: Bar.Val_Msg := 'Stopped';
        10: Bar.Val_Msg := 'Aborting';
        11: Bar.Val_Msg := 'Aborted';
    END_CASE;
END_IF;
IF Ph.Sts_State = 2 THEN
    Bar.Val_StepPct := 100;
ELSIF (Ph.Sts_State = 1) OR (Ph.Sts_State = 3) OR (Ph.Sts_State = 4) THEN
    Bar.Val_StepPct := LIMIT(0, Pct, 100);
ELSE
    Bar.Val_StepPct := 0;
END_IF;

(* ===== 13. Pins; operator and recipe commands are one-shot: clear after use ===== *)
StepTime := tStep;
ScanTime := tDelta;
RunStep := iRunStep;
Running := (Ph.Sts_State = 1) OR (Ph.Sts_State = 3);
Held := Ph.Sts_State = 6;
Complete := Ph.Sts_State = 2;
Failed := Ph.Sts_FailCode <> 0;

Ph.Cmd_Auto := FALSE;
Ph.Cmd_SemiAuto := FALSE;
Ph.Cmd_Man := FALSE;
Ph.Cmd_Start := FALSE;
Ph.Cmd_Stop := FALSE;
Ph.Cmd_Hold := FALSE;
Ph.Cmd_Restart := FALSE;
Ph.Cmd_Abort := FALSE;
Ph.Cmd_Reset := FALSE;
Ph.Cmd_Pause := FALSE;
Ph.Cmd_Resume := FALSE;
Ph.Cmd_Advance := FALSE;
Ph.Cmd_TakeOwn := FALSE;
Ph.Prog_Cmd := 0;
Ph.Prog_Acquire := FALSE;
Ph.Prog_Release := FALSE;
xFirst := FALSE;
""")

# ---------------------------------------------------------------------------------
# Phase DFBs: common pins, request variables and the core call
# ---------------------------------------------------------------------------------
PH_INPUTS = [
    V("PermOK", "BOOL", "Start permissives OK"),
    V("IntlkOK", "BOOL", "Interlocks healthy (FALSE while running -> Holding)"),
    V("IntlkAbort", "BOOL", "TRUE = interlock trip aborts instead of holding"),
    V("EStop", "BOOL", "Emergency stop active -> Aborting"),
]
PH_INOUTS = [
    V("Ph", "T_Phase", "Phase object"),
    V("Bar", "T_SeqBar", "Sequence bar for the HMI"),
]
PH_OUTPUTS = [
    V("Running", "BOOL", "Phase Running or Pausing"),
    V("Held", "BOOL", "Phase Held"),
    V("Complete", "BOOL", "Phase Complete"),
    V("Failed", "BOOL", "Phase failure active"),
]
PH_PRIVATE = [
    V("xFirst", "BOOL", "First scan: load sequence-bar labels", "TRUE"),
    V("fbCore", "FB_PhaseCore", "ISA-88 phase core"),
    V("xTrans", "BOOL", "Request: go to iNext"),
    V("iNext", "INT", "Request: next step"),
    V("xDone", "BOOL", "Request: current state logic finished"),
    V("iFail", "INT", "Request: failure code"),
    V("sFail", "STRING[40]", "Request: failure text"),
    V("iSeg", "INT", "Sequence-bar segment of the active step"),
    V("sMsg", "STRING[40]", "Operator message of the active step"),
    V("iPct", "INT", "Progress within the segment, 0..100"),
    V("tStepMax", "TIME", "Watchdog for this step, T#0S = Ph.Cfg_StepTimeout"),
    V("xWdogOff", "BOOL", "No watchdog in this step"),
]

CLEAR_REQUESTS = r"""
xTrans := FALSE;
iNext := 0;
xDone := FALSE;
iFail := 0;
sFail := '';
sMsg := '';
iPct := 0;
tStepMax := T#0S;
xWdogOff := FALSE;
"""

CORE_CALL = r"""
(* ---- D. Core: ISA-88 states, commands, modes, ownership, watchdog, alarms, sequence bar ---- *)
fbCore(PermOK := PermOK, IntlkOK := IntlkOK, IntlkAbort := IntlkAbort, EStop := EStop,
       Trans := xTrans, NextStep := iNext, StateDone := xDone,
       FailCode := iFail, FailText := sFail,
       Seg := iSeg, Msg := sMsg, Pct := iPct,
       StepTmo := tStepMax, WdogOff := xWdogOff,
       Ph := Ph, Bar := Bar);

(* ---- E. Outputs ---- *)
Running := fbCore.Running;
Held := fbCore.Held;
Complete := fbCore.Complete;
Failed := fbCore.Failed;
"""


def bar_labels(title, labels):
    lines = ["(* ---- A. Sequence-bar labels (first scan, or after the T_SeqBar is re-initialised) ---- *)",
             "IF xFirst OR (Bar.Cfg_NumSeg = 0) THEN",
             f"    Bar.Cfg_Title := '{title}';",
             f"    Bar.Cfg_NumSeg := {len(labels)};"]
    lines += [f"    Bar.Cfg_SegText[{n}] := '{t}';" for n, t in enumerate(labels, 1)]
    lines += ["    xFirst := FALSE;", "END_IF;"]
    return "\n".join(lines)


def phase_code(title, labels, clear_outputs, sequence, outputs):
    return "\n".join([
        "",
        bar_labels(title, labels),
        "",
        "(* ---- B. Requests to the core and equipment requests: cleared every scan, set by the active step ---- *)",
        CLEAR_REQUESTS.strip("\n"),
        clear_outputs.strip("\n"),
        "",
        sequence.strip("\n"),
        CORE_CALL.rstrip("\n"),
        outputs.strip("\n"),
        ""])


OPEN_AREA_HELP = r"""
(* =====================================================================
   C. SEQUENCE LOGIC  >>> OPEN AREA - write the phase logic here <<<

   Read:   Ph.Sts_State        1 Running, 3 Pausing, 5 Holding, 7 Restarting,
                               8 Stopping, 10 Aborting. Nothing runs in Paused (4)
                               or while Ph.Sts_WaitAdvance: outputs fall back to
                               section B. If equipment must keep running between
                               steps (a compressor), keep it on in a 4: branch and
                               in an ELSE of the IF NOT Ph.Sts_WaitAdvance.
           Ph.Sts_Step         active step inside that state (starts at 10)
           fbCore.StepEntry    TRUE on the first scan of a step
           fbCore.StepTime     time in the active step
           fbCore.RunStep      running step the phase resumes at after Restart
           Ph.Prm_Real[] / Ph.Prm_DInt[]   recipe parameters
   Write:  iSeg                sequence-bar segment of this step (1..Bar.Cfg_NumSeg)
           sMsg                operator message for this step (40 characters)
           iPct                progress within the segment, 0..100 (optional)
           Bar.Sts_Skip[n]     segment n skipped this run (optional)
           tStepMax            watchdog for this step, T#0S = Ph.Cfg_StepTimeout
           xWdogOff            TRUE = no watchdog in this step (open-ended waits)
           iNext + xTrans      go to step iNext. Pausing pauses here, and in
                               Semi-automatic step iNext waits for Advance
           xDone               this state's logic is finished:
                               Running -> Complete, Holding -> Held,
                               Restarting -> Running at RunStep,
                               Stopping -> Stopped, Aborting -> Aborted
           iFail + sFail       failure code and text: the phase goes to Holding
           Ph.Rpt_Real[] / Ph.Rpt_DInt[]   report values (cleared at Start)
           Ph.Sts_ReqCode      request to the batch server (cleared by Prog_ReqAck)
   Rules:  - Number steps 10, 20, 30 ... so steps can be inserted later.
           - Set outputs in the active step only; section B clears them every scan.
           - Do one-time work (counters, captured values) on fbCore.StepEntry,
             not in the transition branch: a transition is dropped and asked
             again when a command arrives in the same scan.
           - Never write Ph.Sts_State or Ph.Sts_Step; use xTrans and xDone.
           - Holding, Stopping and Aborting must leave the equipment safe.
           - Timers: call them every scan they are used, and gate IN with
             NOT fbCore.StepEntry so they restart in each step.
   ===================================================================== *)
""".strip("\n")

# ---------------------------------------------------------------------------------
# FB_Phase - the template
# ---------------------------------------------------------------------------------
TEMPLATE_SEQ = OPEN_AREA_HELP + r"""
CASE Ph.Sts_State OF

1, 3:   (* ---------- RUNNING / PAUSING: the procedure ---------- *)
    IF NOT Ph.Sts_WaitAdvance THEN                  (* Semi-automatic: the step waits for Advance *)
    CASE Ph.Sts_Step OF
    10: (* <Step 10 description> *)
        iSeg := 1;
        sMsg := 'Describe what step 10 is doing';
        (* actions:     xOutA := TRUE;                                              *)
        (* failure:     IF <fault> THEN iFail := 1; sFail := 'Fault text'; END_IF; *)
        (* transition:  IF <condition> THEN iNext := 20; xTrans := TRUE; END_IF;   *)

        (* PLACEHOLDER so the template runs in the simulator. Delete it.
           Completes 5 s after Start. *)
        IF fbCore.StepTime >= T#5S THEN
            xDone := TRUE;
        END_IF;

    (* Add the next steps here, for example:
       20:  iSeg := 2;
            sMsg := 'Describe what step 20 is doing';
            ...
       90:  iSeg := 3;
            Ph.Rpt_Real[1] := ...;
            xDone := TRUE;
       Comments cannot be nested in Control Expert: keep step comments on one line. *)
    END_CASE;
    END_IF;

5:  (* ---------- HOLDING: bring the equipment to a safe hold ---------- *)
    (* Equipment requests are already off (section B).
       Wait for confirmation if needed, e.g. xDone := <valves closed>; *)
    xDone := TRUE;

7:  (* ---------- RESTARTING: prepare to resume at fbCore.RunStep ---------- *)
    xDone := TRUE;

8:  (* ---------- STOPPING: controlled stop ---------- *)
    xDone := TRUE;

10: (* ---------- ABORTING: fastest safe shutdown ---------- *)
    xDone := TRUE;

END_CASE;
(* ========================= END OF OPEN AREA ========================= *)
"""

TEMPLATE = dict(
    name="FB_Phase",
    comment="TEMPLATE ISA-88 equipment phase for a T_Phase + T_SeqBar. Copy, rename FB_Ph<Name>, add pins "
            "and write the sequence in the open area. FB_PhaseCore does states, modes, commands and the bar",
    inputs=PH_INPUTS + [],
    inouts=PH_INOUTS,
    outputs=PH_OUTPUTS + [],
    private=PH_PRIVATE + [],
    code=phase_code(
        "Phase", ["Prepare", "Run", "Done"],
        "(* Equipment requests of this phase, e.g. xOutA := FALSE; *)",
        TEMPLATE_SEQ,
        "(* Equipment outputs, e.g. Out_A := xOutA; *)"))

# ---------------------------------------------------------------------------------
# FB_PhXeFill - example: ONE phase fills any number of stations (one sequence, one bar)
# ---------------------------------------------------------------------------------
NSTN = 6                       # fill stations; Prm_Real[1..NSTN] are the station targets

STN_STATES = ("Station state: 0=Not selected 1=Waiting 2=Recovering heel 3=Evacuating 4=Evacuated "
              "5=Ready to fill 6=Fast fill 7=Slow fill 8=Settling 9=Filled 10=Fault")

T_FILLSTN = dict(
    name="T_FillStn",
    comment="One xenon fill station inside a T_XeFill: I/O, station state and results",
    members=[
        V("Cfg_Sel", "BOOL", "Station selected for the run (filled when selected and its target > 0)", "TRUE"),
        V("Cmd_Select", "BOOL", "Operator: toggle Cfg_Sel (one-shot; only while the station is free)"),
        V("Cmd_Tare", "BOOL", "Operator: tare the scale (one-shot; only while the station is free)"),
        V("Cmd_Zero", "BOOL", "Operator: zero the scale (one-shot; only while the station is free)"),
        V("Cmd_Reset", "BOOL", "Operator: clear a filled or faulted station (one-shot; only while free)"),
        V("Inp_VesselOK", "BOOL", "Cylinder connected and its valve confirmed open"),
        V("Inp_IntlkOK", "BOOL", "Station interlocks healthy; FALSE drops the station (fault 105)", "TRUE"),
        V("Inp_NetWt", "REAL", "Scale net weight (kg)"),
        V("Inp_GrossWt", "REAL", "Scale gross weight (kg), display only"),
        V("Inp_TareWt", "REAL", "Scale tare weight (kg), display only"),
        V("Inp_WtStable", "BOOL", "Scale motion-free"),
        V("Inp_PT", "REAL", "Station pressure (bar g)"),
        V("Inp_VacPT", "REAL", "Station vacuum gauge (mbar abs)"),
        V("Out_Inlet", "BOOL", "Request: fill inlet (direction valve from the header to this station)"),
        V("Out_Recover", "BOOL", "Request: recovery valve (heel to recovery header)"),
        V("Out_Vac", "BOOL", "Request: vacuum valve"),
        V("Out_Tare", "BOOL", "Request: tare the scale (pulse)"),
        V("Out_Zero", "BOOL", "Request: zero the scale (pulse)"),
        V("Sts_State", "INT", STN_STATES),
        V("Sts_FailCode", "INT", "Station fault: 101 leak check, 102 over pressure, 103 overfill, "
                                 "104 under weight, 105 station interlock"),
        V("Sts_TopUps", "INT", "Top-ups used"),
        V("Val_Pct", "INT", "Fill progress, % of target"),
        V("Val_FinalWt", "REAL", "Final net weight (kg)"),
        V("Val_LeakRise", "REAL", "Leak check pressure rise (mbar)"),
    ])

T_XEFILL = dict(
    name="T_XeFill",
    comment="Xenon fill unit for FB_PhXeFill: source cylinder, compressor, fill header and the fill stations",
    members=[
        V("Cfg_HdrMax", "REAL", "Header maximum: compressor unloads above (bar g)", "40.0"),
        V("Cfg_SuctMin", "REAL", "Minimum compressor suction (bar g)", "2.0"),
        V("Cfg_SrcHeel", "REAL", "Source cylinder minimum heel (kg)", "5.0"),
        V("Inp_SrcWt", "REAL", "Source cylinder net weight (kg)"),
        V("Inp_SuctPT", "REAL", "Compressor suction pressure (bar g)"),
        V("Inp_HdrPT", "REAL", "Fill header pressure (bar g)"),
        V("Inp_CompRdy", "BOOL", "Compressor ready to start (no trip, in Auto)"),
        V("Inp_CompRun", "BOOL", "Compressor running feedback"),
        V("Out_SrcVlv", "BOOL", "Request: source cylinder valve"),
        V("Out_CompRun", "BOOL", "Request: compressor run"),
        V("Out_CompLoad", "BOOL", "Request: compressor loaded"),
        V("Out_Recycle", "BOOL", "Request: recycle / bypass valve"),
        V("Sts_NumSel", "INT", "Stations selected this run"),
        V("Sts_NumDone", "INT", "Stations filled"),
        V("Sts_NumFault", "INT", "Stations dropped with a fault"),
        V("Stn", f"ARRAY[1..{NSTN}] OF T_FillStn", "Fill stations"),
    ])

XEFILL_SEQ = r"""
(* =====================================================================
   C. SEQUENCE LOGIC - xenon fill: ONE sequence for every selected station
   Large source cylinder -> diaphragm compressor -> fill header -> stations.
   A station is filled when it is selected (U.Stn[n].Cfg_Sel, the faceplate
   Select button) and has a target weight (Prm_Real[n] > 0).
   Common steps run all selected stations together; inside a step each
   station has its own state (U.Stn[n].Sts_State) and its valves close as
   soon as that station is finished. A station with a fault is dropped
   (valves closed, Sts_FailCode set) and the others carry on.

   Ph.Prm_Real  1..NSTN target net weight per station (kg), 0 = not filled
       NSTN+1 tolerance + (kg)            NSTN+2 tolerance - (kg)
       NSTN+3 fast -> slow change-over (kg before target)
       NSTN+4 preact / in-flight (kg)     NSTN+5 heel recovered to (bar g)
       NSTN+6 evacuation target (mbar abs) NSTN+7 leak check max rise (mbar)
       NSTN+8 max cylinder pressure (bar g) NSTN+9 header setpoint (bar g)
       NSTN+10 header band (bar)
   Ph.Prm_DInt  1 max top-ups  2 leak check time (s)  3 settle time (s)
       4 slow fill pulse on (ms)  5 pulse off (ms)  6 compressor cool-down (s)
   Reports  Rpt_Real 1..NSTN final net weight per station (kg),
       NSTN+1 total filled (kg), NSTN+2 / NSTN+3 source weight start / end (kg),
       NSTN+4 run time (s);  Rpt_DInt 1 stations filled, 2 stations faulted
   Xenon is never vented to atmosphere: heels go to the recovery header.
   ===================================================================== *)
rSP := Ph.Prm_Real[NSTN+9];
rBand := Ph.Prm_Real[NSTN+10];
xExec := ((Ph.Sts_State = 1) OR (Ph.Sts_State = 3)) AND NOT Ph.Sts_WaitAdvance;

(* Every scan the procedure runs: station timers, station interlocks, fill progress *)
nPct := 0;
rPctSum := 0.0;
FOR i := 1 TO NSTN DO
    IF xExec THEN
        tStn[i] := tStn[i] + fbCore.ScanTime;
        IF (U.Stn[i].Sts_State >= 2) AND (U.Stn[i].Sts_State <= 8) AND NOT U.Stn[i].Inp_IntlkOK THEN
            U.Stn[i].Sts_State := 10;                   (* drop this station only *)
            U.Stn[i].Sts_FailCode := 105;
        END_IF;
    END_IF;
    IF (U.Stn[i].Sts_State >= 6) AND (U.Stn[i].Sts_State <= 9) AND (Ph.Prm_Real[i] > 0.0) THEN
        U.Stn[i].Val_Pct := REAL_TO_INT(LIMIT(0.0, U.Stn[i].Inp_NetWt * 100.0 / Ph.Prm_Real[i], 100.0));
        rPctSum := rPctSum + INT_TO_REAL(U.Stn[i].Val_Pct);
        nPct := nPct + 1;
    ELSIF U.Stn[i].Sts_State < 6 THEN
        U.Stn[i].Val_Pct := 0;
    END_IF;
END_FOR;

CASE Ph.Sts_State OF

1, 3:   (* ---------- RUNNING / PAUSING ---------- *)
    IF NOT Ph.Sts_WaitAdvance THEN                  (* Semi-automatic: the step waits for Advance *)
    CASE Ph.Sts_Step OF
    10: (* Line-up: select stations, check cylinders, recipe, source and compressor *)
        iSeg := 1;
        sMsg := 'Checking line-up';
        nSel := 0;
        xAllOK := TRUE;
        FOR i := 1 TO NSTN DO
            U.Stn[i].Sts_FailCode := 0;
            U.Stn[i].Sts_TopUps := 0;
            U.Stn[i].Val_FinalWt := 0.0;
            U.Stn[i].Val_LeakRise := 0.0;
            tStn[i] := T#0S;
            IF (Ph.Prm_Real[i] > 0.0) AND U.Stn[i].Cfg_Sel THEN
                U.Stn[i].Sts_State := 1;
                nSel := nSel + 1;
                xAllOK := xAllOK AND U.Stn[i].Inp_VesselOK AND U.Stn[i].Inp_WtStable AND U.Stn[i].Inp_IntlkOK;
            ELSE
                U.Stn[i].Sts_State := 0;
            END_IF;
        END_FOR;
        tonOk(IN := xAllOK AND U.Inp_CompRdy AND NOT fbCore.StepEntry, PT := T#3S);
        IF nSel = 0 THEN
            iFail := 300;
            sFail := 'No station selected';
        ELSIF (Ph.Prm_Real[NSTN+1] < 0.0) OR (Ph.Prm_Real[NSTN+2] < 0.0) OR (Ph.Prm_Real[NSTN+4] < 0.0)
              OR (Ph.Prm_Real[NSTN+3] < Ph.Prm_Real[NSTN+4]) OR (Ph.Prm_Real[NSTN+8] <= 0.0)
              OR (rSP <= 0.0) OR (rBand <= 0.0) OR (U.Cfg_HdrMax <= rSP) THEN
            iFail := 200;
            sFail := 'Invalid recipe parameters';
        ELSIF U.Inp_SrcWt <= U.Cfg_SrcHeel THEN
            iFail := 201;
            sFail := 'Source cylinder at minimum heel';
        ELSIF tonOk.Q THEN
            Ph.Rpt_Real[NSTN+2] := U.Inp_SrcWt;         (* source weight at start *)
            iNext := 20;
            xTrans := TRUE;
        END_IF;

    20: (* Recover each heel, then evacuate: per station, its valves close as it finishes *)
        iSeg := 2;
        sMsg := 'Recovering heels and evacuating';
        nBusy := 0;
        FOR i := 1 TO NSTN DO
            iSt := U.Stn[i].Sts_State;
            IF iSt = 1 THEN
                iSt := 2;
            END_IF;
            IF iSt = 2 THEN
                IF U.Stn[i].Inp_PT <= Ph.Prm_Real[NSTN+5] THEN
                    iSt := 3;
                ELSE
                    U.Stn[i].Out_Recover := TRUE;
                END_IF;
            END_IF;
            IF iSt = 3 THEN
                IF U.Stn[i].Inp_VacPT <= Ph.Prm_Real[NSTN+6] THEN
                    iSt := 4;
                ELSE
                    U.Stn[i].Out_Vac := TRUE;
                END_IF;
            END_IF;
            IF iSt <> U.Stn[i].Sts_State THEN
                U.Stn[i].Sts_State := iSt;
                tStn[i] := T#0S;
            END_IF;
            IF (iSt >= 1) AND (iSt <= 3) THEN
                nBusy := nBusy + 1;
            END_IF;
        END_FOR;
        IF nBusy = 0 THEN
            iNext := 30;
            xTrans := TRUE;
        END_IF;

    30: (* Leak check: every evacuated station isolated and watched together *)
        iSeg := 3;
        sMsg := 'Vacuum hold - leak check';
        tHold := DINT_TO_TIME(Ph.Prm_DInt[2] * 1000);
        tStepMax := tHold + T#60S;
        nGood := 0;
        FOR i := 1 TO NSTN DO
            IF U.Stn[i].Sts_State = 4 THEN
                IF fbCore.StepEntry THEN
                    rVacRef[i] := U.Stn[i].Inp_VacPT;
                END_IF;
                U.Stn[i].Val_LeakRise := U.Stn[i].Inp_VacPT - rVacRef[i];
                IF fbCore.StepTime >= tHold THEN
                    IF U.Stn[i].Val_LeakRise > Ph.Prm_Real[NSTN+7] THEN
                        U.Stn[i].Sts_State := 10;       (* drop this station *)
                        U.Stn[i].Sts_FailCode := 101;
                    ELSE
                        U.Stn[i].Sts_State := 5;
                    END_IF;
                END_IF;
            END_IF;
            IF U.Stn[i].Sts_State = 5 THEN
                nGood := nGood + 1;
            END_IF;
        END_FOR;
        IF fbCore.StepTime >= tHold THEN
            IF nGood = 0 THEN
                iFail := 301;
                sFail := 'No station left to fill';
            ELSE
                iNext := 40;
                xTrans := TRUE;
            END_IF;
        END_IF;

    40: (* Tare the evacuated cylinders *)
        iSeg := 4;
        sMsg := 'Taring scales';
        xAllOK := TRUE;
        FOR i := 1 TO NSTN DO
            IF U.Stn[i].Sts_State = 5 THEN
                U.Stn[i].Out_Tare := fbCore.StepTime < T#1S;
                xAllOK := xAllOK AND U.Stn[i].Inp_WtStable;
            END_IF;
        END_FOR;
        tonOk(IN := xAllOK AND (fbCore.StepTime >= T#2S) AND NOT fbCore.StepEntry, PT := T#2S);
        IF tonOk.Q THEN
            iNext := 50;
            xTrans := TRUE;
        END_IF;

    50: (* Open the source cylinder *)
        iSeg := 4;
        sMsg := 'Opening source cylinder';
        U.Out_SrcVlv := TRUE;
        tonOk(IN := (U.Inp_SuctPT >= U.Cfg_SuctMin) AND NOT fbCore.StepEntry, PT := T#2S);
        IF tonOk.Q THEN
            iNext := 60;
            xTrans := TRUE;
        END_IF;

    60: (* Start the compressor unloaded *)
        iSeg := 4;
        sMsg := 'Starting compressor';
        U.Out_SrcVlv := TRUE;
        U.Out_CompRun := TRUE;
        U.Out_Recycle := TRUE;
        tonOk(IN := U.Inp_CompRun AND NOT fbCore.StepEntry, PT := T#5S);
        IF tonOk.Q THEN
            iNext := 70;
            xTrans := TRUE;
        END_IF;

    70: (* Pressurise the fill header *)
        iSeg := 4;
        sMsg := 'Pressurising fill header';
        U.Out_SrcVlv := TRUE;
        U.Out_CompRun := TRUE;
        U.Out_CompLoad := U.Inp_HdrPT < U.Cfg_HdrMax;
        U.Out_Recycle := NOT U.Out_CompLoad;
        iPct := REAL_TO_INT(LIMIT(0.0, U.Inp_HdrPT * 100.0 / rSP, 100.0));
        IF NOT U.Inp_CompRun THEN
            iFail := 202;
            sFail := 'Compressor stopped';
        ELSIF U.Inp_HdrPT >= rSP THEN
            xLoadMem := FALSE;
            xHdrOK := TRUE;
            iNext := 80;
            xTrans := TRUE;
        END_IF;

    80: (* Fill: every station fills to its own target; its inlet closes as it finishes *)
        iSeg := 5;
        sMsg := 'Filling stations';
        xWdogOff := TRUE;                               (* stations are guarded one by one *)
        U.Out_SrcVlv := TRUE;
        U.Out_CompRun := TRUE;
        IF U.Inp_HdrPT >= rSP THEN                      (* compressor load / unload *)
            xLoadMem := FALSE;
        ELSIF U.Inp_HdrPT <= rSP - rBand THEN
            xLoadMem := TRUE;
        END_IF;
        U.Out_CompLoad := xLoadMem AND (U.Inp_HdrPT < U.Cfg_HdrMax);
        U.Out_Recycle := NOT U.Out_CompLoad;
        IF U.Inp_HdrPT >= rSP - rBand THEN              (* inlets only open on a pressurised header *)
            xHdrOK := TRUE;
        ELSIF U.Inp_HdrPT < rSP - 2.0 * rBand THEN
            xHdrOK := FALSE;
        END_IF;
        IF nPct > 0 THEN
            iPct := REAL_TO_INT(rPctSum / INT_TO_REAL(nPct));
        END_IF;
        tPulseOn := DINT_TO_TIME(Ph.Prm_DInt[4]);
        tPulseOff := DINT_TO_TIME(Ph.Prm_DInt[5]);
        dCyc := TIME_TO_DINT(tPulseOn + tPulseOff);
        nBusy := 0;
        nGood := 0;
        FOR i := 1 TO NSTN DO
            iSt := U.Stn[i].Sts_State;
            rTgt := Ph.Prm_Real[i];
            rNet := U.Stn[i].Inp_NetWt;
            IF iSt = 5 THEN
                iSt := 6;
            END_IF;
            IF (iSt >= 6) AND (iSt <= 8) AND (U.Stn[i].Inp_PT >= Ph.Prm_Real[NSTN+8]) THEN
                iSt := 10;
                U.Stn[i].Sts_FailCode := 102;
            END_IF;
            IF iSt = 6 THEN                             (* fast fill *)
                IF rNet >= rTgt - Ph.Prm_Real[NSTN+3] THEN
                    iSt := 7;
                ELSE
                    U.Stn[i].Out_Inlet := xHdrOK;
                END_IF;
            END_IF;
            IF iSt = 7 THEN                             (* slow fill, pulsed inlet *)
                IF rNet >= rTgt - Ph.Prm_Real[NSTN+4] THEN
                    iSt := 8;
                ELSIF (dCyc > 0) AND (tPulseOff > T#0S) THEN
                    U.Stn[i].Out_Inlet := xHdrOK AND ((TIME_TO_DINT(tStn[i]) MOD dCyc) < TIME_TO_DINT(tPulseOn));
                ELSE
                    U.Stn[i].Out_Inlet := xHdrOK;
                END_IF;
            END_IF;
            IF (iSt = 8) AND U.Stn[i].Inp_WtStable                  (* settle, then check *)
               AND (tStn[i] >= DINT_TO_TIME(Ph.Prm_DInt[3] * 1000)) THEN
                IF rNet > rTgt + Ph.Prm_Real[NSTN+1] THEN
                    iSt := 10;
                    U.Stn[i].Sts_FailCode := 103;
                ELSIF rNet < rTgt - Ph.Prm_Real[NSTN+2] THEN
                    IF U.Stn[i].Sts_TopUps < DINT_TO_INT(Ph.Prm_DInt[1]) THEN
                        U.Stn[i].Sts_TopUps := U.Stn[i].Sts_TopUps + 1;
                        iSt := 7;
                    ELSE
                        iSt := 10;
                        U.Stn[i].Sts_FailCode := 104;
                    END_IF;
                ELSE
                    iSt := 9;                           (* filled: this station's inlet stays closed *)
                    U.Stn[i].Val_FinalWt := rNet;
                END_IF;
            END_IF;
            IF iSt <> U.Stn[i].Sts_State THEN
                U.Stn[i].Sts_State := iSt;
                tStn[i] := T#0S;
            END_IF;
            IF (iSt >= 6) AND (iSt <= 8) THEN
                nBusy := nBusy + 1;
            ELSIF iSt = 9 THEN
                nGood := nGood + 1;
            END_IF;
        END_FOR;
        IF NOT U.Inp_CompRun THEN
            iFail := 202;
            sFail := 'Compressor stopped';
        ELSIF U.Inp_SrcWt <= U.Cfg_SrcHeel THEN
            iFail := 201;
            sFail := 'Source cylinder at minimum heel';
        ELSIF nBusy = 0 THEN
            IF nGood = 0 THEN
                iFail := 301;
                sFail := 'No station left to fill';
            ELSE
                iNext := 90;
                xTrans := TRUE;
            END_IF;
        END_IF;

    90: (* Shut down: source closed, compressor cools down unloaded, then stops; reports *)
        iSeg := 6;
        sMsg := 'Compressor cool-down';
        U.Out_CompRun := fbCore.StepTime < DINT_TO_TIME(Ph.Prm_DInt[6] * 1000);
        U.Out_Recycle := U.Out_CompRun;
        IF NOT U.Out_CompRun AND NOT U.Inp_CompRun THEN
            rSum := 0.0;
            nGood := 0;
            nBad := 0;
            FOR i := 1 TO NSTN DO
                Ph.Rpt_Real[i] := U.Stn[i].Val_FinalWt;
                rSum := rSum + U.Stn[i].Val_FinalWt;
                IF U.Stn[i].Sts_State = 9 THEN
                    nGood := nGood + 1;
                ELSIF U.Stn[i].Sts_State = 10 THEN
                    nBad := nBad + 1;
                END_IF;
            END_FOR;
            Ph.Rpt_Real[NSTN+1] := rSum;
            Ph.Rpt_Real[NSTN+3] := U.Inp_SrcWt;
            Ph.Rpt_Real[NSTN+4] := DINT_TO_REAL(TIME_TO_DINT(Ph.Val_RunTime)) / 1000.0;
            Ph.Rpt_DInt[1] := INT_TO_DINT(nGood);
            Ph.Rpt_DInt[2] := INT_TO_DINT(nBad);
            xDone := TRUE;
        END_IF;
    END_CASE;
    ELSE                                            (* waiting for Advance: like Paused *)
        U.Out_SrcVlv := U.Inp_CompRun;
        U.Out_CompRun := U.Inp_CompRun;
        U.Out_Recycle := U.Inp_CompRun;
    END_IF;

4:  (* ---------- PAUSED: stations isolated; compressor kept running unloaded ---------- *)
    U.Out_SrcVlv := U.Inp_CompRun;
    U.Out_CompRun := U.Inp_CompRun;
    U.Out_Recycle := U.Inp_CompRun;

5:  (* ---------- HOLDING: every station valve and the source closed, compressor stopped (section B) ---------- *)
    xDone := NOT U.Inp_CompRun;

7:  (* ---------- RESTARTING: restart the feed if it was running, then resume ---------- *)
    FOR i := 1 TO NSTN DO
        tStn[i] := T#0S;                                (* settling stations settle again *)
    END_FOR;
    IF fbCore.RunStep >= 60 THEN
        CASE Ph.Sts_Step OF
        10: U.Out_SrcVlv := TRUE;
            tonOk(IN := (U.Inp_SuctPT >= U.Cfg_SuctMin) AND NOT fbCore.StepEntry, PT := T#2S);
            IF tonOk.Q THEN
                iNext := 20;
                xTrans := TRUE;
            END_IF;
        20: U.Out_SrcVlv := TRUE;
            U.Out_CompRun := TRUE;
            U.Out_Recycle := TRUE;
            tonOk(IN := U.Inp_CompRun AND NOT fbCore.StepEntry, PT := T#5S);
            IF tonOk.Q THEN
                xLoadMem := TRUE;
                xHdrOK := FALSE;
                xDone := TRUE;
            END_IF;
        END_CASE;
    ELSE
        xDone := TRUE;
    END_IF;

8:  (* ---------- STOPPING: everything closed, compressor stopped ---------- *)
    xDone := NOT U.Inp_CompRun;

10: (* ---------- ABORTING: everything off at once ---------- *)
    xDone := TRUE;

END_CASE;

(* Station faceplate commands: only while the station is free (phase not running, or the
   station not taking part / finished). Commands are one-shot and cleared here. *)
xPhActive := (Ph.Sts_State = 1) OR ((Ph.Sts_State >= 3) AND (Ph.Sts_State <= 8)) OR (Ph.Sts_State = 10);
FOR i := 1 TO NSTN DO
    xFree := NOT xPhActive OR (U.Stn[i].Sts_State = 0) OR (U.Stn[i].Sts_State >= 9);
    IF xFree THEN
        IF U.Stn[i].Cmd_Select THEN
            U.Stn[i].Cfg_Sel := NOT U.Stn[i].Cfg_Sel;
        END_IF;
        IF U.Stn[i].Cmd_Tare THEN
            U.Stn[i].Out_Tare := TRUE;
        END_IF;
        IF U.Stn[i].Cmd_Zero THEN
            U.Stn[i].Out_Zero := TRUE;
        END_IF;
        IF U.Stn[i].Cmd_Reset AND (U.Stn[i].Sts_State >= 9) THEN
            U.Stn[i].Sts_State := 0;
            U.Stn[i].Sts_FailCode := 0;
        END_IF;
    END_IF;
    U.Stn[i].Cmd_Select := FALSE;
    U.Stn[i].Cmd_Tare := FALSE;
    U.Stn[i].Cmd_Zero := FALSE;
    U.Stn[i].Cmd_Reset := FALSE;
END_FOR;

(* Unit summary for the HMI *)
U.Sts_NumSel := 0;
U.Sts_NumDone := 0;
U.Sts_NumFault := 0;
FOR i := 1 TO NSTN DO
    IF U.Stn[i].Sts_State > 0 THEN
        U.Sts_NumSel := U.Sts_NumSel + 1;
    END_IF;
    IF U.Stn[i].Sts_State = 9 THEN
        U.Sts_NumDone := U.Sts_NumDone + 1;
    ELSIF U.Stn[i].Sts_State = 10 THEN
        U.Sts_NumFault := U.Sts_NumFault + 1;
    END_IF;
END_FOR;
""".replace("NSTN+10", str(NSTN + 10)).replace("NSTN+9", str(NSTN + 9)).replace("NSTN+8", str(NSTN + 8)) \
   .replace("NSTN+7", str(NSTN + 7)).replace("NSTN+6", str(NSTN + 6)).replace("NSTN+5", str(NSTN + 5)) \
   .replace("NSTN+4", str(NSTN + 4)).replace("NSTN+3", str(NSTN + 3)).replace("NSTN+2", str(NSTN + 2)) \
   .replace("NSTN+1", str(NSTN + 1)).replace("NSTN", str(NSTN))

XEFILL = dict(
    name="FB_PhXeFill",
    comment="EXAMPLE phase: one xenon fill sequence for any number of stations - line-up, heel recovery and "
            "evacuation, leak check, tare, source and compressor start, fill by weight (each station's inlet "
            "closes as it finishes), shutdown. One T_Phase, one T_SeqBar, one T_XeFill",
    inputs=PH_INPUTS,
    inouts=PH_INOUTS + [V("U", "T_XeFill", "Xenon fill unit: source, compressor, header and stations")],
    outputs=PH_OUTPUTS,
    private=PH_PRIVATE + [
        V("xExec", "BOOL", "The procedure runs this scan"),
        V("xPhActive", "BOOL", "Phase active (stations locked)"),
        V("xFree", "BOOL", "Station free for faceplate commands"),
        V("i", "INT", "Station index"),
        V("iSt", "INT", "Station state being worked out"),
        V("nSel", "INT", "Stations selected"),
        V("nBusy", "INT", "Stations still working in the step"),
        V("nGood", "INT", "Stations ready / filled"),
        V("nBad", "INT", "Stations faulted"),
        V("nPct", "INT", "Stations counted in the progress"),
        V("rPctSum", "REAL", "Sum of station progress (%)"),
        V("rSum", "REAL", "Total filled (kg)"),
        V("rTgt", "REAL", "Station target (kg)"),
        V("rNet", "REAL", "Station net weight (kg)"),
        V("rSP", "REAL", "Header setpoint (bar g)"),
        V("rBand", "REAL", "Header band (bar)"),
        V("xAllOK", "BOOL", "Every selected station ready"),
        V("xLoadMem", "BOOL", "Compressor load / unload memory"),
        V("xHdrOK", "BOOL", "Header pressurised: inlets may open"),
        V("tHold", "TIME", "Leak check time"),
        V("tPulseOn", "TIME", "Slow fill pulse on"),
        V("tPulseOff", "TIME", "Slow fill pulse off"),
        V("dCyc", "DINT", "Slow fill pulse cycle (ms)"),
        V("tStn", f"ARRAY[1..{NSTN}] OF TIME", "Time in station state"),
        V("rVacRef", f"ARRAY[1..{NSTN}] OF REAL", "Vacuum at start of leak check (mbar abs)"),
        V("tonOk", "TON", "Condition-stable timer"),
    ],
    code=phase_code(
        "Xenon fill", ["Lineup", "Evacuate", "Leak check", "Pressurise", "Fill", "Done"],
        f"""
U.Out_SrcVlv := FALSE;
U.Out_CompRun := FALSE;
U.Out_CompLoad := FALSE;
U.Out_Recycle := FALSE;
FOR i := 1 TO {NSTN} DO
    U.Stn[i].Out_Inlet := FALSE;
    U.Stn[i].Out_Recover := FALSE;
    U.Stn[i].Out_Vac := FALSE;
    U.Stn[i].Out_Tare := FALSE;
    U.Stn[i].Out_Zero := FALSE;
END_FOR;""",
        XEFILL_SEQ,
        "(* Equipment requests are written straight into U (T_XeFill); the unit program maps them to the control modules *)"))

DFBS = [CORE, TEMPLATE, XEFILL]
DDTS = [T_PHASE, T_SEQBAR, T_FILLSTN, T_XEFILL]


# ---------------------------------------------------------------------------------
# Example unit program
# ---------------------------------------------------------------------------------
def unit_program():
    maps_in = "\n".join(
        f"   XE.Stn[{n}].Inp_NetWt := WT_1{n}1.Val_PV;   XE.Stn[{n}].Inp_PT := PT_1{n}1.Val_PV;   "
        f"XE.Stn[{n}].Inp_VacPT := PT_1{n}2.Val_PV;" for n in (1, 2))
    return f"""PROGRAM XeFill_Unit
(* =====================================================================
   EXAMPLE unit program: xenon cylinder filling, ONE sequence
   One large source cylinder -> diaphragm compressor -> fill header -> {NSTN} fill
   stations. FB_PhXeFill runs the whole fill as one ISA-88 phase with one
   sequence bar. The operator (or a batch server) selects stations by
   entering a target weight per station (PH_XeFill.Prm_Real[1..{NSTN}], 0 = not
   filled) and presses Start. Each station's inlet (direction) valve closes
   as that station reaches its weight; the sequence finishes when every
   selected station is filled or dropped with a fault.
   In Control Expert: create the VAR block below in the Data Editor and
   paste the body into an ST section of the MAST task.
   PCLib {LIB_VERSION} - generated by gen_phase.py
   ===================================================================== *)
VAR
    EStopAct : BOOL;                        (* E-stop active, from the safety relay *)
    PermOK : BOOL := TRUE;                  (* unit start permissives (T_Intlk group) *)
    IntlkOK : BOOL := TRUE;                 (* unit interlocks healthy (T_Intlk group) *)
    xInit : BOOL := TRUE;                   (* first scan of this program *)
    PH_XeFill : T_Phase;                    (* the fill sequence *)
    BAR_XeFill : T_SeqBar;                  (* its sequence bar on the HMI *)
    XE : T_XeFill;                          (* source, compressor, header and stations *)
    fbXeFill : FB_PhXeFill;
END_VAR

(* ---- 1. Inputs: map from the control modules, e.g. PCLib T_AI / T_DI ----
{maps_in}
   ... one line per station ...
   XE.Stn[1].Inp_GrossWt := WT_111.Val_Gross;  XE.Stn[1].Inp_TareWt := WT_111.Val_Tare;  (display only)
   XE.Stn[1].Inp_IntlkOK := ILK_111.Sts_OK;   (station T_Intlk: PT-111 HH, scale fault ...)
   XE.Inp_SrcWt := WT_100.Val_PV;   XE.Inp_SuctPT := PT_101.Val_PV;   XE.Inp_HdrPT := PT_110.Val_PV;
   XE.Inp_CompRdy := K_100.Sts_Ready;   XE.Inp_CompRun := K_100.Sts_Running; *)

(* ---- 2. The fill sequence ---- *)
fbXeFill(PermOK := PermOK, IntlkOK := IntlkOK, IntlkAbort := FALSE, EStop := EStopAct,
         Ph := PH_XeFill, Bar := BAR_XeFill, U := XE);

(* ---- 3. First scan: phase ID ---- *)
IF xInit THEN
    PH_XeFill.Cfg_PhaseID := 100;
    xInit := FALSE;
END_IF;

(* ---- 4. Requests to the control modules, e.g. PCLib T_DValve / T_Motor in Auto ----
   XV_111.Prog_Open := XE.Stn[1].Out_Inlet;    (direction valve, header -> station 1)
   XV_112.Prog_Open := XE.Stn[1].Out_Recover;  XV_113.Prog_Open := XE.Stn[1].Out_Vac;
   WT_111.Cmd_Tare  := XE.Stn[1].Out_Tare;     WT_111.Cmd_Zero := XE.Stn[1].Out_Zero;
   ... one block per station ...
   The Station faceplates write XE.Stn[n].Cmd_Select / Cmd_Tare / Cmd_Zero / Cmd_Reset directly
   (Ignition UDT PCLib/XeFill_Station); FB_PhXeFill acts on them and clears them.
   XV_100.Prog_Open := XE.Out_SrcVlv;          XV_105.Prog_Open := XE.Out_Recycle;
   K_100.Prog_Start := XE.Out_CompRun;         K_100.Prog_Load := XE.Out_CompLoad;
   Valve-to-valve interlocks (never vacuum and inlet open together, never recovery
   and inlet) belong in the control modules' interlocks, not only in the sequence. *)
END_PROGRAM
"""


# ---------------------------------------------------------------------------------
# Control Expert writers (same layout as gen_dfb.py)
# ---------------------------------------------------------------------------------
def st_text(fb):
    out = [f"FUNCTION_BLOCK {fb['name']}", f"(* {fb['comment']} *)",
           f"(* PCLib {LIB_VERSION} - generated by gen_phase.py; edit the generator, not this file *)", ""]
    for kw, key in (("VAR_INPUT", "inputs"), ("VAR_IN_OUT", "inouts"),
                    ("VAR_OUTPUT", "outputs"), ("VAR", "private")):
        if not fb[key]:
            continue
        out.append(kw)
        for n, t, c, i in fb[key]:
            init = f" := {i}" if i is not None else ""
            out.append(f"    {n} : {t}{init};".ljust(44) + f"(* {c} *)")
        out.append("END_VAR")
        out.append("")
    out.append(fb["code"].strip("\n"))
    out.append("")
    out.append("END_FUNCTION_BLOCK")
    return "\n".join(out) + "\n"


def file_header(now, content):
    return [f'<fileHeader company="Schneider Automation" product="{PRODUCT}" '
            f'dateTime="date_and_time#{now.year}-{now.month}-{now.day}-{now:%H:%M:%S}" '
            f'content="{content}" DTDVersion="41"></fileHeader>',
            f'<contentHeader name="PCLib" version="{LIB_VERSION}"></contentHeader>']


def ddt_lines(ddt, now):
    L = [f'<DDTSource DDTName={quoteattr(ddt["name"])} version="{LIB_VERSION}" dateTime="{now:dt#%Y-%m-%d-%H:%M:%S}">',
         f"\t<comment>{escape(ddt['comment'])}</comment>", "\t<structure>"]
    for n, t, c, i in ddt["members"]:
        L.append(f"\t\t<variables name={quoteattr(n)} typeName={quoteattr(t)}>")
        L.append(f"\t\t\t<comment>{escape(c)}</comment>")
        if i is not None:
            L.append(f"\t\t\t<variableInit value={quoteattr(i)}></variableInit>")
        L.append("\t\t</variables>")
    L += ["\t</structure>", "</DDTSource>"]
    return L


def xdb_vars(tag, items, pin_start):
    L = [f"\t<{tag}>"]
    pin = pin_start
    for n, t, c, i in items:
        L.append(f"\t\t<variables name={quoteattr(n)} typeName={quoteattr(t)}>")
        L.append(f"\t\t\t<comment>{escape(c)}</comment>")
        if pin is not None:
            L.append(f'\t\t\t<attribute name="PositionPin" value="{pin}"></attribute>')
            pin += 1
        if i is not None:
            L.append(f"\t\t\t<variableInit value={quoteattr(i)}></variableInit>")
        L.append("\t\t</variables>")
    L.append(f"\t</{tag}>")
    return L, pin


def fb_lines(fb, now):
    L = [f'<FBSource nameOfFBType={quoteattr(fb["name"])} version="{LIB_VERSION}" dateTime="{now:dt#%Y-%m-%d-%H:%M:%S}">',
         f"\t<comment>{escape(fb['comment'])}</comment>"]
    pin = 1
    for tag, key in (("inputParameters", "inputs"), ("inOutParameters", "inouts"), ("outputParameters", "outputs")):
        if fb[key]:
            block, pin = xdb_vars(tag, fb[key], pin)
            L += block
    if fb["private"]:
        L += xdb_vars("privateLocalVariables", fb["private"], None)[0]
    L += ['\t<FBProgram name="Main">',
          f"\t\t<STSource>{escape(fb['code'].strip(chr(10)))}</STSource>",
          "\t</FBProgram>", "</FBSource>"]
    return L


def alarm_parts(path):
    """T_Alarm DDT and FB_AlmCore / FB_Alarm DFBs copied from PCLib_DFB_AI_CE_V16.2.xdb."""
    txt = open(path, encoding="utf-8").read()
    parts = []
    for pat in (r'<DDTSource DDTName="T_Alarm".*?</DDTSource>',
                r'<FBSource nameOfFBType="FB_AlmCore".*?</FBSource>',
                r'<FBSource nameOfFBType="FB_Alarm".*?</FBSource>'):
        m = re.search(pat, txt, re.S)
        if not m:
            raise SystemExit(f"{path}: {pat.split(chr(34))[1]} not found")
        parts.append(m.group(0).replace("\r\n", "\n"))
    return parts


def xdb_text(now, alarm=None):
    L = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', "<FBExchangeFile>"]
    L += file_header(now, "Function Block source file")
    if alarm:
        L += alarm[0].split("\n")
    for d in DDTS:
        L += ddt_lines(d, now)
    if alarm:
        L += alarm[1].split("\n") + alarm[2].split("\n")
    for fb in DFBS:
        L += fb_lines(fb, now)
    L.append("</FBExchangeFile>")
    return "\n".join(L) + "\n"


def xdd_text(now, ddt):
    L = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', "<DDTExchangeFile>"]
    L += file_header(now, "Derived Data Type source file")
    L += ddt_lines(ddt, now)
    L.append("</DDTExchangeFile>")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------------
# Ignition 8.1: UDT, demo tags, Perspective sequence bar
# ---------------------------------------------------------------------------------
UDT_TAGS = [  # member, Ignition data type, writable (only Cfg_ per PCLib convention)
    ("Cfg_Title", "String", True), ("Cfg_NumSeg", "Int2", True), ("Cfg_SegText", "StringArray", True),
    ("Sts_Seg", "Int2Array", False), ("Sts_ActSeg", "Int2", False), ("Sts_PhState", "Int2", False),
    ("Sts_Mode", "Int2", False), ("Sts_Owner", "Int2", False), ("Sts_Step", "Int2", False),
    ("Sts_WaitAdv", "Boolean", False), ("Sts_Fail", "Boolean", False), ("Val_Msg", "String", False),
    ("Val_StepTime", "Int4", False), ("Val_StepPct", "Int2", False),
]
UDT_DOC = ("PCLib T_SeqBar sequence bar. Val_StepTime is the PLC TIME in ms. "
           "OPC item path = {NodePrefix}{Prefix}.<member>; Prefix is the PLC variable, e.g. BAR_Stn[1].")


def folder(name, tags):
    return {"name": name, "tagType": "Folder", "tags": tags}


def seqbar_udt():
    tags = []
    for n, t, w in UDT_TAGS:
        tag = {"name": n, "tagType": "AtomicTag", "valueSource": "opc", "dataType": t,
               "opcServer": {"bindType": "parameter", "binding": "{OPCServer}"},
               "opcItemPath": {"bindType": "parameter", "binding": "{NodePrefix}{Prefix}." + n}}
        if not w:
            tag["readOnly"] = True
        tags.append(tag)
    return {"name": "T_SeqBar", "tagType": "UdtType", "documentation": UDT_DOC,
            "parameters": {"OPCServer": {"dataType": "String", "value": "BMENUA0100"},
                           "NodePrefix": {"dataType": "String", "value": "ns=2;s="},
                           "Prefix": {"dataType": "String", "value": ""}},
            "tags": tags}


DEMO = [  # instance, title, labels, segment states, state, mode, step, msg, step time ms, pct, fail
    ("XeFill_Filling", "Xenon fill", ["Lineup", "Evacuate", "Leak check", "Pressurise", "Fill", "Done"],
     [2, 2, 2, 2, 1, 0], 1, 3, 80, "Filling stations", 42000, 64, False),
    ("XeFill_Held", "Xenon fill", ["Lineup", "Evacuate", "Leak check", "Pressurise", "Fill", "Done"],
     [2, 2, 2, 2, 3, 0], 6, 3, 10, "Compressor stopped", 9000, 0, True),
    ("XeFill_Complete", "Xenon fill", ["Lineup", "Evacuate", "Leak check", "Pressurise", "Fill", "Done"],
     [2, 2, 2, 2, 2, 2], 2, 3, 90, "Complete", 5000, 100, False),
    ("XeFill_SemiAuto", "Xenon fill", ["Lineup", "Evacuate", "Leak check", "Pressurise", "Fill", "Done"],
     [2, 2, 2, 4, 0, 0], 1, 2, 60, "Waiting for Advance", 4000, 0, False),
]


def demo_tags():
    mem = []
    for n, t, w in UDT_TAGS:
        tag = {"name": n, "tagType": "AtomicTag", "valueSource": "memory", "dataType": t}
        if t.endswith("Array"):
            tag["value"] = [""] * NSEG if t == "StringArray" else [0] * NSEG
        mem.append(tag)
    dtype = {"name": "T_SeqBar", "tagType": "UdtType", "documentation": "Memory-tag copy of T_SeqBar for the demo",
             "tags": mem}
    inst = []
    for name, title, labels, segs, st, mode, step, msg, ms, pct, fail in DEMO:
        vals = {"Cfg_Title": title, "Cfg_NumSeg": len(labels),
                "Cfg_SegText": labels + [""] * (NSEG - len(labels)),
                "Sts_Seg": segs + [0] * (NSEG - len(segs)),
                "Sts_ActSeg": max([k + 1 for k, s in enumerate(segs) if s in (1, 3, 4)] or [0]),
                "Sts_PhState": st, "Sts_Mode": mode, "Sts_Owner": 0, "Sts_Step": step,
                "Sts_WaitAdv": mode == 2 and st == 1, "Sts_Fail": fail, "Val_Msg": msg,
                "Val_StepTime": ms, "Val_StepPct": pct}
        inst.append({"name": name, "tagType": "UdtInstance", "typeId": "PCLib_Demo/T_SeqBar",
                     "tags": [{"name": k, "tagType": "AtomicTag", "value": v} for k, v in vals.items()]})
    unit = [dict(json.loads(json.dumps(i)), name="SeqBar") for i in inst if i["name"] == "XeFill_Filling"]
    unit += station_demo_instances()
    return {"tags": [folder("_types_", [folder("PCLib_Demo", [dtype, station_demo_type()])]),
                     folder("SeqBar_Demo", inst), folder("XeFill_Demo", unit)]}


# --- Perspective (same helper style as build_io.py) ---
def comp(ctype, name, props=None, position=None, children=None, pc=None, meta=None):
    c = {"type": ctype, "version": 0, "meta": {"name": name}, "position": position or {}, "props": props or {}}
    if meta:
        c["meta"].update(meta)
    if pc:
        c["propConfig"] = pc
    if children is not None:
        c["children"] = children
    return c


def label(name, classes, text="", position=None, pc=None, meta=None, style=None):
    st = {"classes": classes}
    if style:
        st.update(style)
    return comp("ia.display.label", name, {"text": text, "style": st}, position, pc=pc, meta=meta)


def flex(name, direction, children, classes="", position=None, align="stretch", style=None):
    st = {"classes": classes}
    if style:
        st.update(style)
    return comp("ia.container.flex", name, {"direction": direction, "justify": "flex-start", "alignItems": align,
                                            "wrap": "nowrap", "style": st}, position, children)


FIX = lambda b: {"basis": b, "grow": 0, "shrink": 0}
GROW = {"basis": "0", "grow": 1, "shrink": 1}
TP = "{view.params.tagPath}"


def b_expr(e):
    return {"binding": {"type": "expr", "config": {"expression": e}}}


def b_tag(rel):
    return {"binding": {"type": "tag", "config": {"mode": "indirect", "tagPath": "{0}/" + rel,
                                                  "references": {"0": TP}, "fallbackDelay": 2.5}}}


STATE_TXT = ('case(coalesce({view.custom.state}, -1), 0, "IDLE", 1, "RUNNING", 2, "COMPLETE", 3, "PAUSING", '
             '4, "PAUSED", 5, "HOLDING", 6, "HELD", 7, "RESTARTING", 8, "STOPPING", 9, "STOPPED", '
             '10, "ABORTING", 11, "ABORTED", "?")')
STATE_CLS = ('if(coalesce({view.custom.fail}, false), "State/Fault", '
             'case(coalesce({view.custom.state}, -1), 1, "State/Running", 3, "State/Running", 7, "State/Running", '
             '0, "State/Stopped", 2, "State/Stopped", 9, "State/Stopped", 10, "State/Fault", 11, "State/Fault", '
             '-1, "State/Unknown", "State/Transition"))')
MODE_TXT = 'case(coalesce({view.custom.mode}, 0), 1, "MAN", 2, "SEMI", 3, "AUTO", "?")'
MODE_CLS = 'case(coalesce({view.custom.mode}, 0), 1, "Mode/Manual", "Mode/Auto")'
SEG_NAMES = ("Pending", "Active", "Done", "Fault", "Held", "Skipped")


def seg_label(i):
    k = i - 1
    seg = f"try({{view.custom.seg}}[{k}], 0)"
    cls = (f'"Seq/Step/" + case({seg}, 1, "Active", 2, "Done", 3, "Fault", 4, "Held", 5, "Skipped", "Pending")'
           ' + " Text/Size/XS Text/Mod/Ellipsis"')
    tip = (f'try(toStr({{view.custom.txt}}[{k}]), "") + ": " + '
           f'case({seg}, 1, "active", 2, "done", 3, "fault", 4, "held / paused / waiting", 5, "skipped", "pending")')
    return label(f"Seg{i:02d}", "Seq/Step/Pending Text/Size/XS Text/Mod/Ellipsis", "", dict(GROW),
                 pc={"props.text": b_expr(f'try(toStr({{view.custom.txt}}[{k}]), "")'),
                     "props.style.classes": b_expr(cls),
                     "position.display": b_expr(f"{i} <= coalesce({{view.custom.num}}, 0)"),
                     "meta.tooltip.text": b_expr(tip)},
                 meta={"tooltip": {"enabled": True, "text": ""}},
                 style={"margin": "0 0.093vh"})


def seqbar_view():
    header = flex("Header", "row", [
        label("Title", "Text/Size/S Text/Weight/Bold Text/Mod/Ellipsis", "", dict(GROW),
              pc={"props.text": b_expr('coalesce({view.custom.title}, "")')}),
        label("Step", "Text/Caption Text/Mod/Tabular", "", FIX("auto"),
              pc={"props.text": b_expr('"Step " + toStr(coalesce({view.custom.step}, 0))')},
              style={"marginRight": "0.37vh"}),
        label("Mode", "Mode/Auto", "AUTO", FIX("auto"),
              pc={"props.text": b_expr(MODE_TXT), "props.style.classes": b_expr(MODE_CLS)},
              style={"marginRight": "0.37vh"}),
        label("State", "State/Stopped", "IDLE", FIX("auto"),
              pc={"props.text": b_expr(STATE_TXT), "props.style.classes": b_expr(STATE_CLS)}),
    ], "", FIX("auto"), align="center")
    segs = flex("Segments", "row", [seg_label(i) for i in range(1, NSEG + 1)], "", FIX("2.6vh"), align="stretch",
                style={"marginTop": "0.37vh", "marginBottom": "0.37vh"})
    footer = flex("Footer", "row", [
        label("Msg", "Text/Size/S Text/Mod/Ellipsis", "", dict(GROW),
              pc={"props.text": b_expr('coalesce({view.custom.msg}, "")'),
                  "props.style.classes": b_expr('if(coalesce({view.custom.fail}, false), '
                                                '"Text/Size/S Text/Mod/Ellipsis Text/Color/Fault", '
                                                '"Text/Size/S Text/Mod/Ellipsis")')}),
        label("Pct", "Text/Caption Text/Mod/Tabular", "", FIX("auto"),
              pc={"props.text": b_expr('if(coalesce({view.custom.pct}, 0) > 0, '
                                       'toStr({view.custom.pct}) + " %", "")')},
              style={"marginRight": "0.74vh"}),
        label("StepTime", "Text/Caption Text/Mod/Tabular", "", FIX("auto"),
              pc={"props.text": b_expr('numberFormat(coalesce({view.custom.stime}, 0) / 1000, "#,##0") + " s"')}),
    ], "", FIX("auto"), align="center")
    root = flex("root", "column", [header, segs, footer], "Container/Card Util/Pad/S")
    custom_pc = {f"custom.{k}": b_tag(m) for k, m in (
        ("title", "Cfg_Title"), ("num", "Cfg_NumSeg"), ("txt", "Cfg_SegText"), ("seg", "Sts_Seg"),
        ("state", "Sts_PhState"), ("mode", "Sts_Mode"), ("step", "Sts_Step"), ("fail", "Sts_Fail"),
        ("msg", "Val_Msg"), ("stime", "Val_StepTime"), ("pct", "Val_StepPct"))}
    custom_pc["params.tagPath"] = {"paramDirection": "input", "persistent": True}
    return {"custom": {}, "params": {"tagPath": "[default]SeqBar_Demo/XeFill_Filling"}, "propConfig": custom_pc,
            "props": {"defaultSize": {"width": 640, "height": 76}}, "root": root}


def demo_view():
    kids = [label("Title", "Text/Title", "Sequence bar - demo", FIX("auto")),
            label("Hint", "Text/Caption Text/Mod/Wrap",
                  "Demo tags: [default]SeqBar_Demo (memory-tag copies of T_SeqBar). Segment states: "
                  "pending, active, done, fault, held / paused / waiting, skipped.", FIX("auto"))]
    for name, *_ in DEMO:
        kids.append(comp("ia.display.view", name,
                         {"path": "Templates/Sequence/SequenceBar",
                          "params": {"tagPath": f"[default]SeqBar_Demo/{name}"}, "useDefaultViewHeight": True,
                          "style": {"marginTop": "0.741vh"}},
                         {"basis": "auto", "grow": 0, "shrink": 0}))
    root = flex("root", "column", kids, "Container/Screen Util/Pad/L")
    return {"custom": {}, "params": {}, "props": {"defaultSize": {"width": 700, "height": 470}}, "root": root}


# ---------------------------------------------------------------------------------
# Station faceplates (EFC_StationFaceplates, 2026-10-06 export v6.2) on the XeFill sequence
# ---------------------------------------------------------------------------------
# Station_Sidebar and Station_Fill are used exactly as exported (ignition/station_views/). They bind to
# DDT_Station member names, so the UDT below presents T_XeFill.Stn[n] and the phase recipe under those names.
STATION_VIEWS = {"Templates/Station/Station_Sidebar": "Station_Sidebar.view.json",
                 "Templates/Station/Station_Fill": "Station_Fill.view.json"}
STN_PLC = [  # T_FillStn members read over OPC into the PLC folder of each station
    ("Sts_State", "Int2"), ("Sts_FailCode", "Int2"), ("Sts_TopUps", "Int2"), ("Val_Pct", "Int2"),
    ("Val_FinalWt", "Float4"), ("Val_LeakRise", "Float4"), ("Cfg_Sel", "Boolean"), ("Inp_VesselOK", "Boolean"),
    ("Inp_IntlkOK", "Boolean"), ("Inp_WtStable", "Boolean"), ("Inp_NetWt", "Float4"), ("Inp_GrossWt", "Float4"),
    ("Inp_TareWt", "Float4"), ("Inp_PT", "Float4"), ("Inp_VacPT", "Float4"), ("Out_Inlet", "Boolean"),
    ("Out_Recover", "Boolean"), ("Out_Vac", "Boolean")]
STN_FAIL_TEXT = {101: "Leak check failed", 102: "Over max fill pressure", 103: "Overfill - above tolerance",
                 104: "Under weight after top-ups", 105: "Station interlock"}
STN_STATE_TEXT = {0: "Not selected", 1: "Waiting for line-up", 2: "Recovering heel", 3: "Evacuating",
                  4: "Evacuated - leak check", 5: "Ready to fill", 6: "Fast fill", 7: "Slow fill",
                  8: "Settling - checking weight", 9: "Filled", 10: "Station fault"}
STATUS_ENUM = {0: 0, 1: 10, 2: 60, 3: 70, 4: 70, 5: 20, 6: 30, 7: 30, 8: 30, 9: 40, 10: 50}   # DFB_Station StatusEnum
ST = "{[.]PLC/Sts_State}"
# DDT_Station member -> (Ignition data type, how it is made). Kinds: ("expr", expression), ("opc", item path),
# ("opcw", writable item path), ("mem", value). The rules are the same ones station_demo() applies.
STATION_MEMBERS = {
    "StationName": ("String", ("expr", '"{StationName}"')),
    "ScaleName": ("String", ("expr", '"{ScaleName}"')),
    "Units": ("String", ("mem", "kg")),
    "NetWeight": ("Float4", ("expr", "{[.]PLC/Inp_NetWt}")),
    "GrossWeight": ("Float4", ("expr", "{[.]PLC/Inp_GrossWt}")),
    "TareWeight": ("Float4", ("expr", "{[.]PLC/Inp_TareWt}")),
    "TotalWeight": ("Float4", ("expr", "{[.]PLC/Val_FinalWt}")),
    "TargetWeight": ("Float4", ("opcw", "{NodePrefix}{Phase}.Prm_Real[{Stn}]")),
    "Deadband": ("Float4", ("opcw", f"{{NodePrefix}}{{Phase}}.Prm_Real[{NSTN + 1}]")),
    "Press_Max": ("Float4", ("opcw", f"{{NodePrefix}}{{Phase}}.Prm_Real[{NSTN + 8}]")),
    "SampleWeight": ("Float4", ("mem", 0.0)),
    "SamplePress": ("Float4", ("mem", 0.0)),
    "PT": ("Float4", ("expr", "{[.]PLC/Inp_PT}")),
    "PT_Valid": ("Boolean", ("expr", "isGood({[.]PLC/Inp_PT})")),
    "PT_Diff": ("Float4", ("expr", "{[.]PLC/Hdr_PT} - {[.]PLC/Inp_PT}")),
    "Vessel_Present": ("Boolean", ("expr", "{[.]PLC/Inp_VesselOK}")),
    "Selected": ("Boolean", ("expr", "{[.]PLC/Cfg_Sel} && {[.]TargetWeight} > 0")),
    "Disabled": ("Boolean", ("expr", "false")),
    "Failed": ("Boolean", ("expr", f"{ST} = 10")),
    "Complete": ("Boolean", ("expr", f"{ST} = 9")),
    "Filling": ("Boolean", ("expr", f"{ST} >= 6 && {ST} <= 8")),
    "Vacuuming": ("Boolean", ("expr", f"{ST} = 3")),
    "Vacuumed": ("Boolean", ("expr", f"{ST} >= 4 && {ST} <= 9")),
    "Recovering": ("Boolean", ("expr", f"{ST} = 2")),
    "Venting": ("Boolean", ("expr", "false")),
    "Active": ("Boolean", ("expr", f"{ST} >= 1 && {ST} <= 8")),
    "ReadyToStart": ("Boolean", ("expr", f"{{[.]Selected}} && {ST} <= 1")),
    "ReadyToFill": ("Boolean", ("expr", f"{ST} = 5")),
    "Press_Balanced": ("Boolean", ("expr", f"{ST} >= 6 && {ST} <= 9")),
    "InletREQ": ("Boolean", ("expr", "{[.]PLC/Out_Inlet}")),
    "InletCMD": ("Boolean", ("expr", "{[.]PLC/Out_Inlet}")),
    "VacuumREQ": ("Boolean", ("expr", "{[.]PLC/Out_Vac}")),
    "VacuumCMD": ("Boolean", ("expr", "{[.]PLC/Out_Vac}")),
    "SampleREQ": ("Boolean", ("expr", "false")),
    "SampleCMD": ("Boolean", ("expr", "false")),
    "Msg": ("String", ("expr", f"if({ST} = 10, case({{[.]PLC/Sts_FailCode}}, "
                               + ", ".join(f'{k}, "{v}"' for k, v in STN_FAIL_TEXT.items()) + ', "Station fault"), '
                               + f"case({ST}, " + ", ".join(f'{k}, "{v}"' for k, v in STN_STATE_TEXT.items() if k < 10)
                               + ', ""))')),
    "StatusEnum": ("Int2", ("expr", f"case({ST}, " + ", ".join(f"{k}, {v}" for k, v in STATUS_ENUM.items()) + ", 0)")),
    "HMI_Select": ("Boolean", ("opcw", "{NodePrefix}{Unit}.Stn[{Stn}].Cmd_Select")),
    "TareCMD": ("Boolean", ("opcw", "{NodePrefix}{Unit}.Stn[{Stn}].Cmd_Tare")),
    "ZeroCMD": ("Boolean", ("opcw", "{NodePrefix}{Unit}.Stn[{Stn}].Cmd_Zero")),
    "HMI_Reset": ("Boolean", ("opcw", "{NodePrefix}{Unit}.Stn[{Stn}].Cmd_Reset")),
}
STATION_DOC = ("PCLib XeFill station for the EFC Station faceplates. Presents T_XeFill.Stn[{Stn}] and the "
               "FB_PhXeFill recipe under the DDT_Station member names the faceplates bind to. TargetWeight is "
               "Prm_Real[{Stn}]; Deadband (tolerance +) and Press_Max are shared by every station.")


def opc_tag(name, typ, path, writable):
    t = {"name": name, "tagType": "AtomicTag", "valueSource": "opc", "dataType": typ,
         "opcServer": {"bindType": "parameter", "binding": "{OPCServer}"},
         "opcItemPath": {"bindType": "parameter", "binding": path}}
    if not writable:
        t["readOnly"] = True
    return t


def station_udt():
    plc = [opc_tag(n, t, "{NodePrefix}{Unit}.Stn[{Stn}]." + n, n == "Cfg_Sel") for n, t in STN_PLC]
    plc += [opc_tag("Hdr_PT", "Float4", "{NodePrefix}{Unit}.Inp_HdrPT", False),
            opc_tag("Ph_State", "Int2", "{NodePrefix}{Phase}.Sts_State", False)]
    tags = [folder("PLC", plc)]
    for name, (typ, (kind, arg)) in STATION_MEMBERS.items():
        if kind == "expr":
            tags.append({"name": name, "tagType": "AtomicTag", "valueSource": "expr", "dataType": typ, "expression": arg})
        elif kind in ("opc", "opcw"):
            tags.append(opc_tag(name, typ, arg, kind == "opcw"))
        else:
            tags.append({"name": name, "tagType": "AtomicTag", "valueSource": "memory", "dataType": typ, "value": arg})
    return {"name": "XeFill_Station", "tagType": "UdtType", "documentation": STATION_DOC,
            "parameters": {"OPCServer": {"dataType": "String", "value": "BMENUA0100"},
                           "NodePrefix": {"dataType": "String", "value": "ns=2;s="},
                           "Unit": {"dataType": "String", "value": "XE"},
                           "Phase": {"dataType": "String", "value": "PH_XeFill"},
                           "Stn": {"dataType": "Integer", "value": 1},
                           "StationName": {"dataType": "String", "value": "Station 1"},
                           "ScaleName": {"dataType": "String", "value": "WT-111"}},
            "tags": tags}


def station_demo(n, st, tgt, net, fail=0, sel=True, pt=None, hdr=28.5):
    """DDT_Station member values for a demo station, worked out with the same rules as station_udt()."""
    sel_ = sel and tgt > 0
    pt = (net - 1.013 if st >= 6 else (-1.012 if st >= 3 else 3.2)) if pt is None else pt
    v = {"StationName": f"Station {n}", "ScaleName": f"WT-1{n}1", "Units": "kg", "NetWeight": net,
         "GrossWeight": 50.0 + net, "TareWeight": 50.0, "TotalWeight": net if st == 9 else 0.0, "TargetWeight": tgt,
         "Deadband": 0.2, "Press_Max": 60.0, "SampleWeight": 0.0, "SamplePress": 0.0, "PT": pt, "PT_Valid": True,
         "PT_Diff": hdr - pt, "Vessel_Present": True, "Selected": sel_, "Disabled": False,
         "Failed": st == 10, "Complete": st == 9, "Filling": 6 <= st <= 8, "Vacuuming": st == 3,
         "Vacuumed": 4 <= st <= 9, "Recovering": st == 2, "Venting": False, "Active": 1 <= st <= 8,
         "ReadyToStart": sel_ and st <= 1, "ReadyToFill": st == 5, "Press_Balanced": 6 <= st <= 9,
         "InletREQ": st in (6, 7), "InletCMD": st in (6, 7), "VacuumREQ": st == 3, "VacuumCMD": st == 3,
         "SampleREQ": False, "SampleCMD": False,
         "Msg": STN_FAIL_TEXT.get(fail, "Station fault") if st == 10 else STN_STATE_TEXT[st],
         "StatusEnum": STATUS_ENUM[st], "HMI_Select": False, "TareCMD": False, "ZeroCMD": False, "HMI_Reset": False}
    return v


XEFILL_DEMO_STATIONS = [  # station, state, target, net, fail, selected
    (1, 6, 20.0, 12.8, 0, True), (2, 9, 10.0, 9.95, 0, True), (3, 0, 0.0, 0.0, 0, True),
    (4, 10, 15.0, 0.0, 101, True), (5, 0, 18.0, 0.0, 0, False), (6, 8, 25.0, 24.88, 0, True)]


def station_demo_type():
    return {"name": "XeFill_Station", "tagType": "UdtType", "documentation": "Memory-tag copy of XeFill_Station",
            "tags": [{"name": k, "tagType": "AtomicTag", "valueSource": "memory", "dataType": typ}
                     for k, (typ, _) in STATION_MEMBERS.items()]}


def station_demo_instances():
    out = []
    for n, st, tgt, net, fail, sel in XEFILL_DEMO_STATIONS:
        vals = station_demo(n, st, tgt, net, fail, sel)
        out.append({"name": f"Station_{n}", "tagType": "UdtInstance", "typeId": "PCLib_Demo/XeFill_Station",
                    "tags": [{"name": k, "tagType": "AtomicTag", "value": v} for k, v in vals.items()]})
    return out


def b_tagp(ref, rel):
    return {"binding": {"type": "tag", "config": {"mode": "indirect", "tagPath": "{0}/" + rel,
                                                  "references": {"0": ref}, "fallbackDelay": 2.5}}}


TILE_WORD = ('if({view.custom.failed}, "FAULT", if({view.custom.complete}, "COMPLETE", if({view.custom.filling}, '
             '"FILLING", if({view.custom.vac}, "VACUUMING", if({view.custom.rec}, "RECOVERING", if({view.custom.active}, '
             '"ACTIVE", if({view.custom.sel}, "READY", "IDLE")))))))')
TILE_CHIP = ('if({view.custom.failed}, "State/Fault", if({view.custom.complete}, "State/Stopped", '
             'if({view.custom.filling} || {view.custom.active}, if({view.custom.vac} || {view.custom.rec}, '
             '"State/Transition", "State/Running"), "State/Stopped")))')


def station_tile_view():
    """Overview tile (220 x 96): click opens the Station_Sidebar dock."""
    pct = 'if(coalesce({view.custom.tgt}, 0) > 0, min(1, coalesce({view.custom.net}, 0) / ({view.custom.tgt} * 1.08)), 0)'
    over = 'coalesce({view.custom.tgt}, 0) > 0 && {view.custom.net} > {view.custom.tgt} + coalesce({view.custom.db}, 0)'
    head = flex("Head", "row", [
        label("Name", "Text/Subheader Text/Mod/Ellipsis", "", dict(GROW),
              pc={"props.text": b_expr('coalesce({view.custom.name}, "Station")')}),
        label("Chip", "State/Stopped", "IDLE", FIX("auto"),
              pc={"props.text": b_expr(TILE_WORD), "props.style.classes": b_expr(TILE_CHIP)}),
    ], "", FIX("auto"), align="center")
    vals = flex("Vals", "row", [
        label("Net", "Text/ValueLarge Text/Mod/Tabular", "", FIX("auto"),
              pc={"props.text": b_expr('numberFormat(coalesce({view.custom.net}, 0), "0.000")')}),
        label("Tgt", "Text/Caption Text/Mod/Tabular", "", dict(GROW),
              pc={"props.text": b_expr('" / " + numberFormat(coalesce({view.custom.tgt}, 0), "0.000") + " kg"')},
              style={"marginLeft": "0.37vh"}),
    ], "", FIX("auto"), align="center")
    bar = comp("ia.container.coord", "Bar", {"mode": "percent", "style": {"classes": "Bar/Track Util/Clip",
                                                                         "marginTop": "0.278vh"}},
               {"basis": "0.926vh", "grow": 0, "shrink": 0},
               [label("Fill", "Bar/Fill", "", {"x": 0, "y": 0, "width": 0.5, "height": 1},
                      pc={"position.width": b_expr(pct),
                          "props.style.classes": b_expr(f'if({over}, "Bar/FillAlarm", "Bar/Fill")')})])
    msg = label("Msg", "Text/Caption Text/Mod/Ellipsis", "", FIX("auto"),
                pc={"props.text": b_expr('coalesce({view.custom.msg}, "")')}, style={"marginTop": "0.278vh"})
    root = flex("root", "column", [head, vals, bar, msg], "Container/Card Util/Pad/S Util/Pointer")
    root["events"] = {"dom": {"onClick": {"type": "script", "scope": "G", "config": {"script":
        '\tsystem.perspective.openDock("StationSidebar", params={"tagPath": self.view.params.tagPath})'}}}}
    custom_pc = {f"custom.{k}": b_tagp(TP, m) for k, m in (
        ("name", "StationName"), ("net", "NetWeight"), ("tgt", "TargetWeight"), ("db", "Deadband"),
        ("failed", "Failed"), ("complete", "Complete"), ("filling", "Filling"), ("vac", "Vacuuming"),
        ("rec", "Recovering"), ("active", "Active"), ("sel", "Selected"), ("msg", "Msg"))}
    custom_pc["params.tagPath"] = {"paramDirection": "input", "persistent": True}
    return {"custom": {}, "params": {"tagPath": "[default]XeFill_Demo/Station_1"}, "propConfig": custom_pc,
            "props": {"defaultSize": {"width": 220, "height": 96}}, "root": root}


def xefill_overview_view():
    """One screen for the fill: the sequence bar, then a Station_Fill faceplate per station."""
    UP = "{view.params.unitPath}"
    seq = comp("ia.display.view", "SequenceBar", {"path": "Templates/Sequence/SequenceBar", "params": {"tagPath": ""},
                                                  "useDefaultViewHeight": True},
               {"basis": "auto", "grow": 0, "shrink": 0}, pc={"props.params.tagPath": b_expr(f'{UP} + "/SeqBar"')})
    stations = [comp("ia.display.view", f"Station_{n}",
                     {"path": "Templates/Station/Station_Fill", "params": {"tagPath": ""},
                      "useDefaultViewHeight": True, "useDefaultViewWidth": True,
                      "style": {"marginRight": "0.741vh"}},
                     {"basis": "auto", "grow": 0, "shrink": 0},
                     pc={"props.params.tagPath": b_expr(f'{UP} + "/Station_{n}"')}) for n in range(1, NSTN + 1)]
    root = flex("root", "column", [
        label("Title", "Text/Title", "Xenon fill", FIX("auto")),
        label("Hint", "Text/Caption", "", FIX("auto"),
              pc={"props.text": b_expr(f'"Unit: " + {UP} + "   -   select stations and enter targets on the '
                                       f'faceplates, then start the sequence"')}),
        flex("SeqRow", "row", [dict(seq, position={"basis": "0", "grow": 1, "shrink": 1})], "", FIX("auto"),
             style={"marginTop": "0.741vh", "marginBottom": "0.741vh"}),
        flex("Stations", "row", stations, "", FIX("auto"), align="flex-start"),
    ], "Container/Screen Util/Pad/L")
    pc = {"params.unitPath": {"paramDirection": "input", "persistent": True}}
    return {"custom": {}, "params": {"unitPath": "[default]XeFill_Demo"}, "propConfig": pc,
            "props": {"defaultSize": {"width": 1880, "height": 600}}, "root": root}


STATION_STYLE_CLASSES = {   # copied from EFC_StationFaceplates (style-classes/Station/Step/*, Bar/Band/Deadband)
    "Station/Step/Done": {"backgroundColor": "#595959", "border": "0.093vh solid #595959", "borderRadius": "0.093vh"},
    "Station/Step/Active": {"backgroundColor": "#FFFFFF", "border": "0.093vh solid #1F1F1F", "borderRadius": "0.093vh"},
    "Station/Step/Pending": {"backgroundColor": "#CFCFCF", "border": "0.093vh solid #A6A6A6", "borderRadius": "0.093vh"},
    "Station/Step/Fault": {"backgroundColor": "#3A3A3A",
                           "backgroundImage": "repeating-linear-gradient(135deg, #3A3A3A 0 0.278vh, #FFFFFF 0.278vh 0.463vh)",
                           "border": "0.093vh solid #000000", "borderRadius": "0.093vh"},
    "Bar/Band/Deadband": {"backgroundColor": "rgba(31,78,153,0.18)"},
}


VH = lambda px: f"{px * 100 / 1080:.3f}vh"          # 1080p pixels -> vh, as EFC_Styles does
FONT = "'Noto Sans', 'Segoe UI', Arial, sans-serif"
SEG_BASE = {"fontFamily": FONT, "fontWeight": "600", "textAlign": "center", "justifyContent": "center",
            "borderRadius": VH(2), "padding": f"0 {VH(4)}", "letterSpacing": "0.02em"}
STYLE_CLASSES = {   # ISA-101 greys (isa101-color-palette.md); fault is dark grey, not red
    "Seq/Step/Pending": {"backgroundColor": "#E6E6E6", "color": "#5A5A5A", "border": f"{VH(1)} solid #A6A6A6"},
    "Seq/Step/Active": {"backgroundColor": "#FFFFFF", "color": "#1F1F1F", "border": f"{VH(2)} solid #1F1F1F",
                        "fontWeight": "700"},
    "Seq/Step/Done": {"backgroundColor": "#9E9E9E", "color": "#1F1F1F", "border": f"{VH(1)} solid #7F7F7F"},
    "Seq/Step/Fault": {"backgroundColor": "#3A3A3A", "color": "#FFFFFF", "border": f"{VH(1)} solid #000000",
                       "fontWeight": "700"},
    "Seq/Step/Held": {"backgroundColor": "#FFFFFF", "color": "#1F1F1F", "border": f"{VH(2)} dashed #595959"},
    "Seq/Step/Skipped": {"backgroundColor": "#D9D9D9", "color": "#9A9A9A", "border": f"{VH(1)} dashed #A6A6A6",
                         "textDecoration": "line-through"},
}
PROJECT = "EFC_XeFill_HMI"
PERSP = "com.inductiveautomation.perspective"


def resource_json(files, now):
    return json.dumps({"scope": "G", "version": 1, "restricted": False, "overridable": True, "files": files,
                       "attributes": {"lastModification": {"actor": "gen_phase.py",
                                                           "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ")}}},
                      indent=2)


def write_project(path, now):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("project.json", json.dumps({"title": PROJECT, "description": "PCLib xenon fill: sequence bar, "
                                               "station faceplates and overview",
                                               "parent": "EFC_Styles", "enabled": True, "inheritable": True}, indent=2))
        views = [("Templates/Sequence/SequenceBar", seqbar_view()), ("Templates/Sequence/_Demo", demo_view()),
                 ("Templates/Station/Station_Tile", station_tile_view()),
                 ("Templates/XeFill/Overview", xefill_overview_view())]
        for vpath, src in STATION_VIEWS.items():               # the original faceplates, byte for byte
            views.append((vpath, open(os.path.join(HERE, "ignition", "station_views", src), encoding="utf-8").read()))
        for vpath, body in views:
            text = body if isinstance(body, str) else json.dumps(body, indent=2, ensure_ascii=False)
            z.writestr(f"{PERSP}/views/{vpath}/view.json", text)
            z.writestr(f"{PERSP}/views/{vpath}/resource.json", resource_json(["view.json"], now))
        classes = {k: dict(SEG_BASE, **v) for k, v in STYLE_CLASSES.items()}
        classes.update(STATION_STYLE_CLASSES)
        for cls, style in classes.items():
            z.writestr(f"{PERSP}/style-classes/{cls}/style.json",
                       json.dumps({"base": {"style": style}, "variants": []}, indent=2))
            z.writestr(f"{PERSP}/style-classes/{cls}/resource.json", resource_json(["style.json"], now))


# ---------------------------------------------------------------------------------
def write(path, text, crlf=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\r\n" if crlf else "\n") as f:
        f.write(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--alarm-xdb", help="PCLib_DFB_AI_CE_V16.2.xdb: copy T_Alarm, FB_AlmCore and FB_Alarm into the export")
    a = ap.parse_args()
    now = dt.datetime.now().replace(microsecond=0)
    alarm = alarm_parts(a.alarm_xdb) if a.alarm_xdb else None

    for fb in DFBS:
        write(os.path.join(HERE, "dfb", fb["name"] + ".st"), st_text(fb))
    write(os.path.join(HERE, "examples", "XeFill_Unit.st"), unit_program())
    xdb = xdb_text(now, alarm)
    ET.fromstring(xdb.encode("utf-8"))                                  # well-formedness check
    write(os.path.join(HERE, "export", "PCLib_DFB_Phase_CE_V16.2.xdb"), xdb)
    xdd = xdd_text(now, T_SEQBAR)
    ET.fromstring(xdd.encode("utf-8"))
    write(os.path.join(HERE, "export", "T_SeqBar.xdd"), xdd)

    ign = os.path.join(HERE, "ignition")
    write(os.path.join(ign, "PCLib_XeFill_UDTs.json"),
          json.dumps({"tags": [folder("_types_", [folder("PCLib", [seqbar_udt(), station_udt()])])]}, indent=2) + "\n",
          crlf=False)
    write(os.path.join(ign, "PCLib_XeFill_Demo_Tags.json"), json.dumps(demo_tags(), indent=2) + "\n", crlf=False)
    write_project(os.path.join(ign, PROJECT + ".zip"), now)
    print(f"{len(DFBS)} DFBs -> dfb/*.st, export/PCLib_DFB_Phase_CE_V16.2.xdb"
          f"{' (with T_Alarm, FB_AlmCore, FB_Alarm)' if alarm else ''}, export/T_SeqBar.xdd, ignition/*")


if __name__ == "__main__":
    main()
