"""
PCLib phase generator - ISA-88 equipment phase DFBs for Control Expert Classic V16.2,
the T_SeqBar sequence-bar DDT and the matching Ignition 8.1 Perspective sequence bar.

Produces:
  dfb/FB_PhaseCore.st, dfb/FB_Phase.st, dfb/FB_PhFill.st, dfb/FB_PhFeed.st
                                         IEC 61131-3 textual POUs (review / version control)
  export/PCLib_DFB_Phase_CE_V16.2.xdb    Control Expert DFB import file (T_Phase, T_SeqBar and the DFBs)
  export/T_SeqBar.xdd                    Control Expert DDT import file (T_SeqBar only)
  examples/XeFill_Unit.st                Example unit program: feed + 6 stations (MAST ST section)
  ignition/PCLib_SeqBar_UDT.json         Ignition UDT _types_/PCLib/T_SeqBar (OPC tags)
  ignition/PCLib_SeqBar_Demo_Tags.json   Memory-tag copy of the UDT plus three demo instances
  ignition/EFC_SequenceBar.zip           Perspective project: Templates/Sequence/SequenceBar + _Demo

DFBs:
  FB_PhaseCore  ISA-88 Part 1 state machine, commands, modes, ownership, watchdog,
                alarms and sequence bar. Shared by every phase; never edited per phase.
  FB_Phase      TEMPLATE. Copy it, rename it FB_Ph<Name>, add pins and write the
                sequence in its open area. It calls FB_PhaseCore.
  FB_PhFill     Example: fill one xenon cylinder to a target weight (one per station).
  FB_PhFeed     Example: source cylinder + diaphragm compressor pressurising the fill header.

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
                               section B. Add a 4: branch only if equipment must
                               keep running while the phase is paused.
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
# FB_PhFill - example: fill one xenon cylinder by weight
# ---------------------------------------------------------------------------------
FILL_SEQ = r"""
(* =====================================================================
   C. SEQUENCE LOGIC - xenon cylinder fill by weight (one station)
   Parameters (Ph.Prm_Real):  1 target net weight (kg)   2 tolerance + (kg)
       3 tolerance - (kg)     4 fast -> slow change-over before target (kg)
       5 preact / in-flight (kg)   6 heel recovered down to (bar g)
       7 evacuation target (mbar abs)   8 leak check max rise (mbar)
       9 maximum cylinder fill pressure (bar g)
   Parameters (Ph.Prm_DInt):  1 sample required (0/1)   2 max top-ups
       3 leak check time (s)   4 settle time (s)   5 slow fill pulse on (ms)
       6 slow fill pulse off (ms)   7 sample fill time (s)
   Reports:  Rpt_Real 1 final net weight (kg)  2 final pressure (bar g)
             3 run time (s)  4 leak check rise (mbar);  Rpt_DInt 1 top-ups
   Xenon is never vented to atmosphere: the heel goes to the recovery header,
   and Hold / Stop / Abort isolate the cylinder.
   ===================================================================== *)
rTarget := Ph.Prm_Real[1];
IF rTarget > 0.0 THEN
    rPct := NetWt * 100.0 / rTarget;
ELSE
    rPct := 0.0;
END_IF;

CASE Ph.Sts_State OF

1, 3:   (* ---------- RUNNING / PAUSING: the procedure ---------- *)
    IF NOT Ph.Sts_WaitAdvance THEN                  (* Semi-automatic: the step waits for Advance *)
    CASE Ph.Sts_Step OF
    10: (* Check the recipe and the cylinder *)
        iSeg := 1;
        sMsg := 'Checking cylinder and recipe';
        iTopUp := 0;
        xTopUp := FALSE;
        tonOk(IN := VesselOK AND WtStable AND NOT fbCore.StepEntry, PT := T#3S);
        IF (rTarget <= 0.0) OR (Ph.Prm_Real[9] <= 0.0) OR (Ph.Prm_Real[5] < 0.0)
           OR (Ph.Prm_Real[4] < Ph.Prm_Real[5]) THEN
            iFail := 100;
            sFail := 'Invalid recipe parameters';
        ELSIF tonOk.Q THEN
            iNext := 20;
            xTrans := TRUE;
        END_IF;

    20: (* Recover the heel to the recovery header *)
        iSeg := 2;
        sMsg := 'Recovering heel';
        xRecover := TRUE;
        IF PT <= Ph.Prm_Real[6] THEN
            iNext := 30;
            xTrans := TRUE;
        END_IF;

    30: (* Evacuate *)
        iSeg := 2;
        sMsg := 'Evacuating cylinder';
        xVac := TRUE;
        IF VacPT <= Ph.Prm_Real[7] THEN
            iNext := 40;
            xTrans := TRUE;
        END_IF;

    40: (* Vacuum hold: leak check *)
        iSeg := 2;
        sMsg := 'Vacuum hold - leak check';
        IF fbCore.StepEntry THEN
            rVacRef := VacPT;
        END_IF;
        tHold := DINT_TO_TIME(Ph.Prm_DInt[3] * 1000);
        tStepMax := tHold + T#60S;
        Ph.Rpt_Real[4] := VacPT - rVacRef;
        IF fbCore.StepTime >= tHold THEN
            IF VacPT - rVacRef > Ph.Prm_Real[8] THEN
                iFail := 101;
                sFail := 'Leak check failed';
            ELSE
                iNext := 50;
                xTrans := TRUE;
            END_IF;
        END_IF;

    50: (* Tare the evacuated cylinder *)
        iSeg := 3;
        sMsg := 'Taring scale';
        xTare := fbCore.StepTime < T#1S;                (* 1 s tare pulse to the scale *)
        tonOk(IN := WtStable AND (fbCore.StepTime >= T#2S) AND NOT fbCore.StepEntry, PT := T#2S);
        IF tonOk.Q THEN
            iNext := 60;
            xTrans := TRUE;
        END_IF;

    60: (* Wait for feed pressure from the compressor *)
        iSeg := 3;
        sMsg := 'Waiting for feed pressure';
        xFeedReq := TRUE;
        xWdogOff := TRUE;                               (* may wait for other stations *)
        IF FeedReady THEN
            iNext := 70;
            xTrans := TRUE;
        END_IF;

    70: (* Fast fill *)
        iSeg := 4;
        sMsg := 'Fast fill';
        xFeedReq := TRUE;
        xInlet := FeedReady;                            (* inlet closes if feed pressure is lost *)
        iPct := REAL_TO_INT(LIMIT(0.0, rPct, 100.0));
        IF PT >= Ph.Prm_Real[9] THEN
            iFail := 102;
            sFail := 'Cylinder above max fill pressure';
        ELSIF NetWt >= rTarget - Ph.Prm_Real[4] THEN
            iNext := 80;
            xTrans := TRUE;
        END_IF;

    80: (* Slow fill: pulsed inlet *)
        iSeg := 4;
        sMsg := 'Slow fill';
        IF fbCore.StepEntry AND xTopUp THEN             (* entered from 90 for a top-up *)
            iTopUp := iTopUp + 1;
            xTopUp := FALSE;
        END_IF;
        xFeedReq := TRUE;
        tPulseOn := DINT_TO_TIME(Ph.Prm_DInt[5]);
        tPulseOff := DINT_TO_TIME(Ph.Prm_DInt[6]);
        dCyc := TIME_TO_DINT(tPulseOn + tPulseOff);
        IF (dCyc > 0) AND (tPulseOff > T#0S) THEN
            xInlet := FeedReady AND ((TIME_TO_DINT(fbCore.StepTime) MOD dCyc) < TIME_TO_DINT(tPulseOn));
        ELSE
            xInlet := FeedReady;
        END_IF;
        iPct := REAL_TO_INT(LIMIT(0.0, rPct, 100.0));
        IF PT >= Ph.Prm_Real[9] THEN
            iFail := 102;
            sFail := 'Cylinder above max fill pressure';
        ELSIF NetWt >= rTarget - Ph.Prm_Real[5] THEN
            iNext := 90;
            xTrans := TRUE;
        END_IF;

    90: (* Settle, then check the weight *)
        iSeg := 4;
        sMsg := 'Settling - checking weight';
        xFeedReq := TRUE;                               (* keep feed for a top-up *)
        iPct := REAL_TO_INT(LIMIT(0.0, rPct, 100.0));
        tonOk(IN := WtStable AND (fbCore.StepTime >= DINT_TO_TIME(Ph.Prm_DInt[4] * 1000))
                    AND NOT fbCore.StepEntry, PT := T#1S);
        IF tonOk.Q THEN
            IF NetWt > rTarget + Ph.Prm_Real[2] THEN
                iFail := 103;
                sFail := 'Overfill - above tolerance';
            ELSIF NetWt < rTarget - Ph.Prm_Real[3] THEN
                IF iTopUp < DINT_TO_INT(Ph.Prm_DInt[2]) THEN
                    xTopUp := TRUE;                     (* counted on entry to step 80 *)
                    iNext := 80;
                    xTrans := TRUE;
                ELSE
                    iFail := 104;
                    sFail := 'Under weight after max top-ups';
                END_IF;
            ELSE
                iNext := 100;
                xTrans := TRUE;
            END_IF;
        END_IF;

    100: (* Sample (optional) *)
        iSeg := 5;
        IF Ph.Prm_DInt[1] = 0 THEN
            Bar.Sts_Skip[5] := TRUE;
            sMsg := 'No sample required';
            iNext := 110;
            xTrans := TRUE;
        ELSE
            sMsg := 'Filling sample cylinder';
            xSample := TRUE;
            IF fbCore.StepTime >= DINT_TO_TIME(Ph.Prm_DInt[7] * 1000) THEN
                iNext := 110;
                xTrans := TRUE;
            END_IF;
        END_IF;

    110: (* Fill complete: reports *)
        iSeg := 6;
        sMsg := 'Fill complete';
        Ph.Rpt_Real[1] := NetWt;
        Ph.Rpt_Real[2] := PT;
        Ph.Rpt_Real[3] := DINT_TO_REAL(TIME_TO_DINT(Ph.Val_RunTime)) / 1000.0;
        Ph.Rpt_DInt[1] := INT_TO_DINT(iTopUp);
        xDone := TRUE;
    END_CASE;
    END_IF;

5:  (* ---------- HOLDING: all station valves closed, feed released (section B) ---------- *)
    xDone := TRUE;

7:  (* ---------- RESTARTING: re-establish feed before resuming a fill step ---------- *)
    IF (fbCore.RunStep >= 60) AND (fbCore.RunStep <= 90) THEN
        xFeedReq := TRUE;
        IF FeedReady THEN
            xDone := TRUE;
        END_IF;
    ELSE
        xDone := TRUE;
    END_IF;

8:  (* ---------- STOPPING: isolate the cylinder ---------- *)
    xDone := TRUE;

10: (* ---------- ABORTING: isolate the cylinder ---------- *)
    xDone := TRUE;

END_CASE;
"""

FILL = dict(
    name="FB_PhFill",
    comment="EXAMPLE phase: fill one xenon cylinder by weight - check, heel recovery, evacuation, leak check, "
            "tare, fast / slow fill, settle and top-up, optional sample. One instance per fill station",
    inputs=PH_INPUTS + [
        V("VesselOK", "BOOL", "Cylinder connected and its valve confirmed open"),
        V("NetWt", "REAL", "Scale net weight (kg)"),
        V("WtStable", "BOOL", "Scale motion-free"),
        V("PT", "REAL", "Station pressure (bar g)"),
        V("VacPT", "REAL", "Station vacuum gauge (mbar abs)"),
        V("FeedReady", "BOOL", "Fill header at pressure (FB_PhFeed.FeedReady)"),
    ],
    inouts=PH_INOUTS,
    outputs=PH_OUTPUTS + [
        V("Out_Inlet", "BOOL", "Request: fill inlet valve open"),
        V("Out_Recover", "BOOL", "Request: recovery valve open (heel to recovery header)"),
        V("Out_Vac", "BOOL", "Request: vacuum valve open"),
        V("Out_Sample", "BOOL", "Request: sample valve open"),
        V("Out_Tare", "BOOL", "Request: tare the scale (pulse)"),
        V("FeedReq", "BOOL", "This station needs feed pressure"),
    ],
    private=PH_PRIVATE + [
        V("xInlet", "BOOL", "Inlet request"),
        V("xRecover", "BOOL", "Recovery request"),
        V("xVac", "BOOL", "Vacuum request"),
        V("xSample", "BOOL", "Sample request"),
        V("xTare", "BOOL", "Tare request"),
        V("xFeedReq", "BOOL", "Feed request"),
        V("rTarget", "REAL", "Target net weight (kg)"),
        V("rPct", "REAL", "Fill progress (% of target)"),
        V("rVacRef", "REAL", "Vacuum at start of leak check (mbar abs)"),
        V("tHold", "TIME", "Leak check time"),
        V("iTopUp", "INT", "Top-ups done"),
        V("xTopUp", "BOOL", "Top-up requested by step 90"),
        V("tPulseOn", "TIME", "Slow fill pulse on"),
        V("tPulseOff", "TIME", "Slow fill pulse off"),
        V("dCyc", "DINT", "Slow fill pulse cycle (ms)"),
        V("tonOk", "TON", "Condition-stable timer"),
    ],
    code=phase_code(
        "Cylinder fill", ["Vessel", "Vac", "Prefill", "Fill", "Sample", "Done"],
        """
xInlet := FALSE;
xRecover := FALSE;
xVac := FALSE;
xSample := FALSE;
xTare := FALSE;
xFeedReq := FALSE;""",
        FILL_SEQ,
        """
Out_Inlet := xInlet;
Out_Recover := xRecover;
Out_Vac := xVac;
Out_Sample := xSample;
Out_Tare := xTare;
FeedReq := xFeedReq;"""))

# ---------------------------------------------------------------------------------
# FB_PhFeed - example: source cylinder + compressor pressurising the fill header
# ---------------------------------------------------------------------------------
FEED_SEQ = r"""
(* =====================================================================
   C. SEQUENCE LOGIC - xenon feed: large source cylinder -> diaphragm
   compressor -> fill header for the six stations
   Parameters (Ph.Prm_Real):  1 header pressure setpoint (bar g)
       2 load band below setpoint (bar)   3 header maximum, unload above (bar g)
       4 minimum suction pressure (bar g)  5 source cylinder minimum heel (kg)
   Parameters (Ph.Prm_DInt):  1 idle time with no requests before shutdown (s)
       2 unloaded cool-down before stop (s)
   Reports:  Rpt_Real 1 source weight at start (kg)  2 source weight at end (kg)
             3 xenon delivered (kg)  4 run time (s)
   ===================================================================== *)
rSP := Ph.Prm_Real[1];
rBand := Ph.Prm_Real[2];

CASE Ph.Sts_State OF

1, 3:   (* ---------- RUNNING / PAUSING: the procedure ---------- *)
    IF NOT Ph.Sts_WaitAdvance THEN                  (* Semi-automatic: the step waits for Advance *)
    CASE Ph.Sts_Step OF
    10: (* Line-up check *)
        iSeg := 1;
        sMsg := 'Checking line-up';
        IF (rSP <= 0.0) OR (rBand <= 0.0) OR (Ph.Prm_Real[3] <= rSP) THEN
            iFail := 200;
            sFail := 'Invalid recipe parameters';
        ELSIF SrcWt <= Ph.Prm_Real[5] THEN
            iFail := 201;
            sFail := 'Source cylinder at minimum heel';
        ELSIF CompRdy THEN
            Ph.Rpt_Real[1] := SrcWt;                    (* source weight at start *)
            iNext := 20;
            xTrans := TRUE;
        END_IF;

    20: (* Open the source cylinder *)
        iSeg := 2;
        sMsg := 'Opening source cylinder';
        xSrc := TRUE;
        tonOk(IN := (SuctPT >= Ph.Prm_Real[4]) AND NOT fbCore.StepEntry, PT := T#2S);
        IF tonOk.Q THEN
            iNext := 30;
            xTrans := TRUE;
        END_IF;

    30: (* Start the compressor unloaded *)
        iSeg := 3;
        sMsg := 'Starting compressor';
        xSrc := TRUE;
        xRun := TRUE;
        xRecyc := TRUE;
        tonOk(IN := CompRun AND NOT fbCore.StepEntry, PT := T#5S);
        IF tonOk.Q THEN
            iNext := 40;
            xTrans := TRUE;
        END_IF;

    40: (* Pressurise the fill header *)
        iSeg := 4;
        sMsg := 'Pressurising fill header';
        xSrc := TRUE;
        xRun := TRUE;
        xLoad := HdrPT < Ph.Prm_Real[3];
        xRecyc := NOT xLoad;
        iPct := REAL_TO_INT(LIMIT(0.0, HdrPT * 100.0 / rSP, 100.0));
        IF NOT CompRun THEN
            iFail := 202;
            sFail := 'Compressor stopped';
        ELSIF HdrPT >= rSP THEN
            iNext := 50;
            xTrans := TRUE;
        END_IF;

    50: (* Supply: hold header pressure while stations request feed *)
        iSeg := 5;
        xWdogOff := TRUE;                               (* runs as long as there is demand *)
        xSrc := TRUE;
        xRun := TRUE;
        IF HdrPT >= rSP THEN
            xLoadMem := FALSE;
        ELSIF HdrPT <= rSP - rBand THEN
            xLoadMem := TRUE;
        END_IF;
        xLoad := xLoadMem AND (HdrPT < Ph.Prm_Real[3]);
        xRecyc := NOT xLoad;
        xReady := HdrPT >= rSP - rBand;
        IF FeedReqs > 0 THEN
            sMsg := 'Supplying stations';
        ELSE
            sMsg := 'Supply - no requests';
        END_IF;
        tonIdle(IN := (FeedReqs <= 0) AND NOT fbCore.StepEntry, PT := DINT_TO_TIME(Ph.Prm_DInt[1] * 1000));
        IF NOT CompRun THEN
            iFail := 202;
            sFail := 'Compressor stopped';
        ELSIF SrcWt <= Ph.Prm_Real[5] THEN
            iFail := 201;
            sFail := 'Source cylinder at minimum heel';
        ELSIF tonIdle.Q THEN
            iNext := 60;
            xTrans := TRUE;
        END_IF;

    60: (* Shut down: cool down unloaded, then stop *)
        iSeg := 6;
        sMsg := 'Compressor cool-down';
        xRun := fbCore.StepTime < DINT_TO_TIME(Ph.Prm_DInt[2] * 1000);
        xRecyc := xRun;
        IF NOT xRun AND NOT CompRun THEN
            Ph.Rpt_Real[2] := SrcWt;
            Ph.Rpt_Real[3] := Ph.Rpt_Real[1] - SrcWt;
            Ph.Rpt_Real[4] := DINT_TO_REAL(TIME_TO_DINT(Ph.Val_RunTime)) / 1000.0;
            xDone := TRUE;
        END_IF;
    END_CASE;
    END_IF;

4:  (* ---------- PAUSED: keep the compressor running unloaded; stations do not fill ---------- *)
    xSrc := CompRun;
    xRun := CompRun;
    xRecyc := CompRun;

5:  (* ---------- HOLDING: stop the compressor, isolate the source (section B) ---------- *)
    xDone := NOT CompRun;

7:  (* ---------- RESTARTING: open the source and start unloaded, then resume ---------- *)
    CASE Ph.Sts_Step OF
    10: xSrc := TRUE;
        tonOk(IN := (SuctPT >= Ph.Prm_Real[4]) AND NOT fbCore.StepEntry, PT := T#2S);
        IF tonOk.Q THEN
            iNext := 20;
            xTrans := TRUE;
        END_IF;
    20: xSrc := TRUE;
        xRun := TRUE;
        xRecyc := TRUE;
        tonOk(IN := CompRun AND NOT fbCore.StepEntry, PT := T#5S);
        IF tonOk.Q THEN
            xDone := TRUE;
        END_IF;
    END_CASE;

8:  (* ---------- STOPPING: stop the compressor, isolate the source ---------- *)
    xDone := NOT CompRun;

10: (* ---------- ABORTING: everything off at once ---------- *)
    xDone := TRUE;

END_CASE;
"""

FEED = dict(
    name="FB_PhFeed",
    comment="EXAMPLE phase: xenon feed - large source cylinder and diaphragm compressor pressurise the fill "
            "header and hold it at setpoint while stations request feed",
    inputs=PH_INPUTS + [
        V("SrcWt", "REAL", "Source cylinder net weight (kg)"),
        V("SuctPT", "REAL", "Compressor suction pressure (bar g)"),
        V("HdrPT", "REAL", "Fill header pressure (bar g)"),
        V("CompRdy", "BOOL", "Compressor ready to start (no trip, in Auto)"),
        V("CompRun", "BOOL", "Compressor running feedback"),
        V("FeedReqs", "INT", "Number of stations requesting feed"),
    ],
    inouts=PH_INOUTS,
    outputs=PH_OUTPUTS + [
        V("Out_SrcVlv", "BOOL", "Request: source cylinder valve open"),
        V("Out_CompRun", "BOOL", "Request: compressor run"),
        V("Out_CompLoad", "BOOL", "Request: compressor loaded"),
        V("Out_Recycle", "BOOL", "Request: recycle / bypass valve open"),
        V("FeedReady", "BOOL", "Fill header at pressure: stations may fill"),
    ],
    private=PH_PRIVATE + [
        V("xSrc", "BOOL", "Source valve request"),
        V("xRun", "BOOL", "Compressor run request"),
        V("xLoad", "BOOL", "Compressor load request"),
        V("xRecyc", "BOOL", "Recycle valve request"),
        V("xReady", "BOOL", "Header ready"),
        V("xLoadMem", "BOOL", "Load / unload hysteresis memory"),
        V("rSP", "REAL", "Header pressure setpoint (bar g)"),
        V("rBand", "REAL", "Load band (bar)"),
        V("tonOk", "TON", "Condition-stable timer"),
        V("tonIdle", "TON", "No-demand timer"),
    ],
    code=phase_code(
        "Xenon feed", ["Lineup", "Source", "Start", "Pressurise", "Supply", "Done"],
        """
xSrc := FALSE;
xRun := FALSE;
xLoad := FALSE;
xRecyc := FALSE;
xReady := FALSE;""",
        FEED_SEQ,
        """
Out_SrcVlv := xSrc;
Out_CompRun := xRun;
Out_CompLoad := xLoad;
Out_Recycle := xRecyc;
FeedReady := xReady AND fbCore.Running;"""))

DFBS = [CORE, TEMPLATE, FILL, FEED]
DDTS = [T_PHASE, T_SEQBAR]

# ---------------------------------------------------------------------------------
# Example unit program: 1 feed phase + 6 station fill phases
# ---------------------------------------------------------------------------------
NSTN = 6


def unit_program():
    calls = []
    for n in range(1, NSTN + 1):
        calls.append(
            f"fbStn{n}(PermOK := Stn_Perm[{n}], IntlkOK := Stn_IntlkOK[{n}], IntlkAbort := FALSE, EStop := EStopAct,\n"
            f"       VesselOK := Stn_Vessel[{n}], NetWt := Stn_Wt[{n}], WtStable := Stn_Stable[{n}],\n"
            f"       PT := Stn_PT[{n}], VacPT := Stn_Vac[{n}], FeedReady := fbFeed.FeedReady,\n"
            f"       Ph := PH_Stn[{n}], Bar := BAR_Stn[{n}],\n"
            f"       Out_Inlet => Stn_InletReq[{n}], Out_Recover => Stn_RecoverReq[{n}], Out_Vac => Stn_VacReq[{n}],\n"
            f"       Out_Sample => Stn_SampleReq[{n}], Out_Tare => Stn_TareReq[{n}], FeedReq => Stn_FeedReq[{n}]);")
    stn_fbs = ", ".join(f"fbStn{n}" for n in range(1, NSTN + 1))
    return f"""PROGRAM XeFill_Unit
(* =====================================================================
   EXAMPLE unit program: xenon cylinder filling
   One large source cylinder -> diaphragm compressor -> fill header -> {NSTN} fill
   stations, each filling one cylinder by weight.
     PH_Feed / fbFeed : FB_PhFeed   pressurises the header, owned by this unit
                                    logic and started when a station asks for feed
     PH_Stn[n] / fbStnN : FB_PhFill fills the cylinder on station n, started by
                                    the operator (or a batch server via Prog_Cmd)
   In Control Expert: create the VAR block below in the Data Editor (DFB
   instances cannot be arrays, so there is one fbStnN per station) and paste
   the body into an ST section of the MAST task.
   PCLib {LIB_VERSION} - generated by gen_phase.py
   ===================================================================== *)
VAR
    EStopAct : BOOL;                        (* E-stop active, from the safety relay *)
    FeedAuto : BOOL := TRUE;                (* HMI: the unit runs the feed phase *)
    xFeedOwned : BOOL;                      (* the unit owned the feed phase last scan *)
    xInit : BOOL := TRUE;                   (* first scan of this program *)
    nFeedReq : INT;                         (* stations asking for feed *)
    i : INT;

    PH_Feed : T_Phase;                      (* feed phase *)
    BAR_Feed : T_SeqBar;
    fbFeed : FB_PhFeed;
    Feed_PermOK : BOOL := TRUE;             (* feed start permissives (T_Intlk group) *)
    Feed_IntlkOK : BOOL := TRUE;            (* feed interlocks healthy (T_Intlk group) *)
    Src_Wt : REAL;                          (* WT-100 source cylinder net weight (kg) *)
    Suct_PT : REAL;                         (* PT-101 compressor suction (bar g) *)
    Hdr_PT : REAL;                          (* PT-110 fill header (bar g) *)
    Comp_Rdy : BOOL;                        (* K-100 ready *)
    Comp_Run : BOOL;                        (* K-100 running *)
    Src_VlvReq : BOOL;                      (* -> XV-100 source cylinder valve *)
    Comp_RunReq : BOOL;                     (* -> K-100 run *)
    Comp_LoadReq : BOOL;                    (* -> K-100 load *)
    Recycle_VlvReq : BOOL;                  (* -> XV-105 recycle / bypass *)

    PH_Stn : ARRAY[1..{NSTN}] OF T_Phase;         (* station fill phases *)
    BAR_Stn : ARRAY[1..{NSTN}] OF T_SeqBar;
    {stn_fbs} : FB_PhFill;
    Stn_Perm : ARRAY[1..{NSTN}] OF BOOL;          (* station start permissives *)
    Stn_IntlkOK : ARRAY[1..{NSTN}] OF BOOL;       (* station interlocks healthy *)
    Stn_Vessel : ARRAY[1..{NSTN}] OF BOOL;        (* cylinder connected, valve open *)
    Stn_Wt : ARRAY[1..{NSTN}] OF REAL;            (* WT-1n1 net weight (kg) *)
    Stn_Stable : ARRAY[1..{NSTN}] OF BOOL;        (* scale motion-free *)
    Stn_PT : ARRAY[1..{NSTN}] OF REAL;            (* PT-1n1 station pressure (bar g) *)
    Stn_Vac : ARRAY[1..{NSTN}] OF REAL;           (* PT-1n2 vacuum gauge (mbar abs) *)
    Stn_InletReq : ARRAY[1..{NSTN}] OF BOOL;      (* -> XV-1n1 fill inlet *)
    Stn_RecoverReq : ARRAY[1..{NSTN}] OF BOOL;    (* -> XV-1n2 to recovery header *)
    Stn_VacReq : ARRAY[1..{NSTN}] OF BOOL;        (* -> XV-1n3 vacuum *)
    Stn_SampleReq : ARRAY[1..{NSTN}] OF BOOL;     (* -> XV-1n4 sample *)
    Stn_TareReq : ARRAY[1..{NSTN}] OF BOOL;       (* -> WT-1n1 tare *)
    Stn_FeedReq : ARRAY[1..{NSTN}] OF BOOL;       (* station asks for feed *)
END_VAR

(* ---- 1. Inputs: map from the control modules, e.g. PCLib T_AI / T_DI ----
   Stn_Wt[1] := WT_111.Val_PV;    Stn_PT[1] := PT_111.Val_PV;    Stn_Vac[1] := PT_112.Val_PV;
   Src_Wt := WT_100.Val_PV;       Hdr_PT := PT_110.Val_PV;       Comp_Run := K_100.Sts_Running;
   Stn_IntlkOK[1] := ILK_111.Sts_OK;  (T_Intlk group: e.g. PT-111 HH, XV-1n3 not open with XV-1n1) *)

(* ---- 2. Feed phase: owned by the unit, started on demand, reset when complete ----
   The operator takes the feed for manual work with Cmd_TakeOwn; that also turns FeedAuto off. *)
IF FeedAuto AND (PH_Feed.Sts_Owner = 0) THEN
    IF xFeedOwned THEN
        FeedAuto := FALSE;                  (* operator took the phase *)
    ELSE
        PH_Feed.Prog_Acquire := TRUE;
    END_IF;
END_IF;
IF NOT FeedAuto AND (PH_Feed.Sts_Owner = 1) THEN
    PH_Feed.Prog_Release := TRUE;
END_IF;
xFeedOwned := PH_Feed.Sts_Owner = 1;

nFeedReq := 0;
FOR i := 1 TO {NSTN} DO
    IF Stn_FeedReq[i] THEN
        nFeedReq := nFeedReq + 1;
    END_IF;
END_FOR;
IF PH_Feed.Sts_Owner = 1 THEN
    IF (PH_Feed.Sts_State = 0) AND (nFeedReq > 0) THEN
        PH_Feed.Prog_Cmd := 1;              (* Start *)
    ELSIF PH_Feed.Sts_State = 2 THEN
        PH_Feed.Prog_Cmd := 6;              (* Reset: ready for the next demand *)
    END_IF;
END_IF;

(* ---- 3. Phases ---- *)
fbFeed(PermOK := Feed_PermOK, IntlkOK := Feed_IntlkOK, IntlkAbort := FALSE, EStop := EStopAct,
       SrcWt := Src_Wt, SuctPT := Suct_PT, HdrPT := Hdr_PT, CompRdy := Comp_Rdy, CompRun := Comp_Run,
       FeedReqs := nFeedReq, Ph := PH_Feed, Bar := BAR_Feed,
       Out_SrcVlv => Src_VlvReq, Out_CompRun => Comp_RunReq, Out_CompLoad => Comp_LoadReq,
       Out_Recycle => Recycle_VlvReq);

{chr(10).join(calls)}

(* ---- 4. First scan: bar titles and phase IDs (after the DFBs have loaded their labels) ---- *)
IF xInit THEN
    BAR_Feed.Cfg_Title := 'Xenon feed';
    PH_Feed.Cfg_PhaseID := 100;
    FOR i := 1 TO {NSTN} DO
        PH_Stn[i].Cfg_PhaseID := 100 + i;
    END_FOR;
{chr(10).join(f"    BAR_Stn[{n}].Cfg_Title := 'Station {n} fill';" for n in range(1, NSTN + 1))}
    xInit := FALSE;
END_IF;

(* ---- 5. Requests to the control modules, e.g. PCLib T_DValve / T_Motor in Auto ----
   XV_111.Prog_Open := Stn_InletReq[1];      XV_100.Prog_Open := Src_VlvReq;
   K_100.Prog_Start := Comp_RunReq;          K_100.Prog_Stop := NOT Comp_RunReq;
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
    ("Stn1_Filling", "Station 1 fill", ["Vessel", "Vac", "Prefill", "Fill", "Sample", "Done"],
     [2, 2, 2, 1, 0, 0], 1, 3, 70, "Fast fill", 84000, 62, False),
    ("Stn2_Fault", "Station 2 fill", ["Vessel", "Vac", "Prefill", "Fill", "Sample", "Done"],
     [2, 3, 0, 0, 0, 0], 6, 3, 10, "Leak check failed", 12000, 0, True),
    ("Stn3_Complete", "Station 3 fill", ["Vessel", "Vac", "Prefill", "Fill", "Sample", "Done"],
     [2, 2, 2, 2, 5, 2], 2, 3, 110, "Complete", 3000, 100, False),
    ("Feed_SemiAuto", "Xenon feed", ["Lineup", "Source", "Start", "Pressurise", "Supply", "Done"],
     [2, 2, 4, 0, 0, 0], 1, 2, 30, "Waiting for Advance", 6000, 0, False),
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
    return {"tags": [folder("_types_", [folder("PCLib_Demo", [dtype])]), folder("SeqBar_Demo", inst)]}


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
    return {"custom": {}, "params": {"tagPath": "[default]SeqBar_Demo/Stn1_Filling"}, "propConfig": custom_pc,
            "props": {"defaultSize": {"width": 640, "height": 104}}, "root": root}


def demo_view():
    kids = [label("Title", "Text/Title", "Sequence bar - demo", FIX("auto")),
            label("Hint", "Text/Caption Text/Mod/Wrap",
                  "Demo tags: [default]SeqBar_Demo (memory-tag copies of T_SeqBar). Segment states: "
                  "pending, active, done, fault, held / paused / waiting, skipped.", FIX("auto"))]
    for name, *_ in DEMO:
        kids.append(comp("ia.display.view", name,
                         {"path": "Templates/Sequence/SequenceBar",
                          "params": {"tagPath": f"[default]SeqBar_Demo/{name}"}, "useDefaultViewHeight": True},
                         {"basis": "auto", "grow": 0, "shrink": 0}))
    root = flex("root", "column", kids, "Container/Screen Util/Pad/L")
    return {"custom": {}, "params": {}, "props": {"defaultSize": {"width": 700, "height": 620}}, "root": root}


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
PROJECT = "EFC_SequenceBar"
PERSP = "com.inductiveautomation.perspective"


def resource_json(files, now):
    return json.dumps({"scope": "G", "version": 1, "restricted": False, "overridable": True, "files": files,
                       "attributes": {"lastModification": {"actor": "gen_phase.py",
                                                           "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ")}}},
                      indent=2)


def write_project(path, now):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("project.json", json.dumps({"title": PROJECT, "description": "PCLib T_Phase / T_SeqBar sequence bar",
                                               "parent": "EFC_Styles", "enabled": True, "inheritable": True}, indent=2))
        for vpath, body in (("Templates/Sequence/SequenceBar", seqbar_view()),
                            ("Templates/Sequence/_Demo", demo_view())):
            z.writestr(f"{PERSP}/views/{vpath}/view.json", json.dumps(body, indent=2, ensure_ascii=False))
            z.writestr(f"{PERSP}/views/{vpath}/resource.json", resource_json(["view.json"], now))
        for cls, st in STYLE_CLASSES.items():
            style = dict(SEG_BASE)
            style.update(st)
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
    write(os.path.join(ign, "PCLib_SeqBar_UDT.json"),
          json.dumps({"tags": [folder("_types_", [folder("PCLib", [seqbar_udt()])])]}, indent=2) + "\n", crlf=False)
    write(os.path.join(ign, "PCLib_SeqBar_Demo_Tags.json"), json.dumps(demo_tags(), indent=2) + "\n", crlf=False)
    write_project(os.path.join(ign, PROJECT + ".zip"), now)
    print(f"{len(DFBS)} DFBs -> dfb/*.st, export/PCLib_DFB_Phase_CE_V16.2.xdb"
          f"{' (with T_Alarm, FB_AlmCore, FB_Alarm)' if alarm else ''}, export/T_SeqBar.xdd, ignition/*")


if __name__ == "__main__":
    main()
