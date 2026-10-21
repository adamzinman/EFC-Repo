"""
PCLib DFB generator - IEC 61131-3 Structured Text function blocks for Control Expert Classic V16.2.

Produces:
  dfb/<FB>.st                          IEC 61131-3 textual POU (FUNCTION_BLOCK ... END_FUNCTION_BLOCK)
  export/PCLib_DFB_AI_CE_V16.2.xdb     Control Expert DFB import file (includes the DDTs it needs)

DFBs (in dependency order):
  FB_AlmCore  ISA-18.2 / IEC 62682 alarm state machine (plain parameters, reusable)
  FB_Alarm    wraps FB_AlmCore for a T_Alarm
  FB_AlmLim   limit + deadband comparison, wraps FB_AlmCore for a T_AlmLim
  FB_AI       analog input processing for a T_AI

Usage:  python gen_dfb.py      (run gen_pclib.py first if the DDTs changed)
"""
import datetime as dt
import os
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

import gen_pclib as lib

PREFIX = "T_"
PRODUCT = "EcoStruxure Control Expert Classic V16.2"
HERE = os.path.dirname(os.path.abspath(__file__))


def V(name, typ, comment, init=None):
    return (name, typ, comment, init)


# ---------------------------------------------------------------------------
# FB_AlmCore
# ---------------------------------------------------------------------------
ALMCORE = dict(
    name="FB_AlmCore",
    comment="ISA-18.2 / IEC 62682 alarm state machine: chattering delays, latching, "
            "acknowledge, time-limited shelving, suppression, out-of-service",
    inputs=[
        V("Cond", "BOOL", "Raw alarm condition"),
        V("Supp", "BOOL", "Suppressed by design (logic)"),
        V("Enabled", "BOOL", "Alarm configured / enabled"),
        V("LatchCfg", "BOOL", "Latching alarm"),
        V("NoAck", "BOOL", "No acknowledge required"),
        V("OnDly", "TIME", "On-delay"),
        V("OffDly", "TIME", "Off-delay"),
        V("MaxShelf", "TIME", "Maximum shelve time"),
        V("Ack", "BOOL", "Acknowledge command"),
        V("Rst", "BOOL", "Reset latched alarm command"),
        V("Shelve", "BOOL", "Shelve command"),
        V("Unshelve", "BOOL", "Unshelve command"),
        V("RemoveSvc", "BOOL", "Remove from service command"),
        V("ReturnSvc", "BOOL", "Return to service command"),
    ],
    inouts=[],
    outputs=[
        V("Active", "BOOL", "Alarm active (annunciated)"),
        V("Unack", "BOOL", "Unacknowledged"),
        V("Shelved", "BOOL", "Shelved"),
        V("Suppressed", "BOOL", "Suppressed by design"),
        V("OOS", "BOOL", "Out of service"),
        V("State", "INT", lib.ALARM_STATES),
        V("ShelfLeft", "TIME", "Shelve time remaining"),
        V("EvtActive", "BOOL", "Pulse: alarm became active"),
        V("EvtRTN", "BOOL", "Pulse: alarm returned to normal"),
    ],
    private=[
        V("xOOS", "BOOL", "Out-of-service memory"),
        V("xShelved", "BOOL", "Shelved memory"),
        V("xInhibit", "BOOL", "Alarm inhibited (OOS, shelved, suppressed, disabled)"),
        V("xCond", "BOOL", "Condition after on/off delays"),
        V("xLatch", "BOOL", "Latched memory"),
        V("xActive", "BOOL", "Active"),
        V("xUnack", "BOOL", "Unacknowledged memory"),
        V("tonShelf", "TON", "Shelve timer"),
        V("tonOn", "TON", "On-delay timer"),
        V("tofOff", "TOF", "Off-delay timer"),
        V("rtActive", "R_TRIG", "Active rising edge"),
        V("ftActive", "F_TRIG", "Active falling edge"),
    ],
    code=r"""
(* ---- Out of service (ISA-18.2 state H) ---- *)
IF RemoveSvc THEN
    xOOS := TRUE;
END_IF;
IF ReturnSvc THEN
    xOOS := FALSE;
END_IF;

(* ---- Shelving (ISA-18.2 state F), always time-limited ---- *)
IF Shelve AND Enabled AND NOT xOOS THEN
    xShelved := TRUE;
END_IF;
IF Unshelve OR xOOS OR NOT Enabled THEN
    xShelved := FALSE;
END_IF;
tonShelf(IN := xShelved, PT := MaxShelf);
IF tonShelf.Q THEN
    xShelved := FALSE;
END_IF;
IF xShelved THEN
    ShelfLeft := MaxShelf - tonShelf.ET;
ELSE
    ShelfLeft := T#0S;
END_IF;

xInhibit := xOOS OR xShelved OR Supp OR NOT Enabled;

(* ---- Chattering control: on-delay / off-delay ---- *)
tonOn(IN := Cond AND NOT xInhibit, PT := OnDly);
tofOff(IN := tonOn.Q, PT := OffDly);
xCond := tofOff.Q AND NOT xInhibit;

(* ---- Latching (ISA-18.2 state E): reset only after return to normal ---- *)
IF xInhibit OR NOT LatchCfg THEN
    xLatch := FALSE;
ELSIF xCond THEN
    xLatch := TRUE;
ELSIF Rst THEN
    xLatch := FALSE;
END_IF;

xActive := xCond OR xLatch;

(* ---- Annunciation and acknowledge ---- *)
rtActive(CLK := xActive);
ftActive(CLK := xActive);
IF rtActive.Q AND NOT NoAck THEN
    xUnack := TRUE;
END_IF;
IF Ack OR xInhibit OR NoAck THEN
    xUnack := FALSE;
END_IF;

(* ---- State per ISA-18.2 / IEC 62682 state model ---- *)
IF xOOS OR NOT Enabled THEN
    State := 7;
ELSIF Supp THEN
    State := 6;
ELSIF xShelved THEN
    State := 5;
ELSIF xLatch AND NOT xCond THEN
    State := 4;
ELSIF xActive AND xUnack THEN
    State := 1;
ELSIF xActive THEN
    State := 2;
ELSIF xUnack THEN
    State := 3;
ELSE
    State := 0;
END_IF;

Active := xActive;
Unack := xUnack;
Shelved := xShelved;
Suppressed := Supp AND Enabled AND NOT xOOS;
OOS := xOOS;
EvtActive := rtActive.Q;
EvtRTN := ftActive.Q AND NOT xInhibit;
""")


# Shared mapping between a T_Alarm / T_AlmLim instance ("Alm") and FB_AlmCore
CORE_MAP = r"""
fbCore(Cond := Alm.Inp_Cond,
       Supp := Alm.Inp_Suppress OR SuppressIn,
       Enabled := Alm.Cfg_En,
       LatchCfg := Alm.Cfg_Latch,
       NoAck := Alm.Cfg_NoAck,
       OnDly := Alm.Cfg_OnDly,
       OffDly := Alm.Cfg_OffDly,
       MaxShelf := Alm.Cfg_MaxShelf,
       Ack := Alm.Cmd_Ack,
       Rst := Alm.Cmd_Reset,
       Shelve := Alm.Cmd_Shelve,
       Unshelve := Alm.Cmd_Unshelve,
       RemoveSvc := Alm.Cmd_RemoveSvc,
       ReturnSvc := Alm.Cmd_ReturnSvc);

Alm.Sts_Active := fbCore.Active;
Alm.Sts_Unack := fbCore.Unack;
Alm.Sts_Shelved := fbCore.Shelved;
Alm.Sts_Suppressed := fbCore.Suppressed;
Alm.Sts_OOS := fbCore.OOS;
Alm.Sts_State := fbCore.State;
Alm.Sts_ShelfLeft := fbCore.ShelfLeft;

(* ---- Alarm performance data (ISA-18.2 monitoring) ---- *)
IF fbCore.EvtActive THEN
    Alm.Val_Count := Alm.Val_Count + 1;
    RRTC_DT(OUT => Alm.Val_LastActive);
END_IF;
IF fbCore.EvtRTN THEN
    RRTC_DT(OUT => Alm.Val_LastRTN);
END_IF;

(* ---- Operator commands are one-shot: clear after use ---- *)
Alm.Cmd_Ack := FALSE;
Alm.Cmd_Reset := FALSE;
Alm.Cmd_Shelve := FALSE;
Alm.Cmd_Unshelve := FALSE;
Alm.Cmd_RemoveSvc := FALSE;
Alm.Cmd_ReturnSvc := FALSE;
"""

ALARM = dict(
    name="FB_Alarm",
    comment="Discrete alarm for a T_Alarm. Owner logic writes Alm.Inp_Cond before the call",
    inputs=[V("SuppressIn", "BOOL", "Additional design suppression from owner logic")],
    inouts=[V("Alm", PREFIX + "Alarm", "Alarm object")],
    outputs=[],
    private=[V("fbCore", "FB_AlmCore", "Alarm state machine")],
    code=CORE_MAP)

ALMLIM = dict(
    name="FB_AlmLim",
    comment="Limit alarm for a T_AlmLim: high or low limit with deadband, ISA-18.2 state machine",
    inputs=[
        V("PV", "REAL", "Value compared with Alm.Cfg_Lim (EU)"),
        V("IsHigh", "BOOL", "TRUE = high alarm (PV above limit), FALSE = low alarm"),
        V("SuppressIn", "BOOL", "Additional design suppression from owner logic (e.g. bad PV)"),
    ],
    inouts=[V("Alm", PREFIX + "AlmLim", "Limit alarm object")],
    outputs=[],
    private=[
        V("fbCore", "FB_AlmCore", "Alarm state machine"),
        V("xRaw", "BOOL", "Limit comparison with deadband"),
    ],
    code=r"""
(* ---- Limit comparison with deadband (ISA-18.2 chattering control) ---- *)
IF IsHigh THEN
    IF PV > Alm.Cfg_Lim THEN
        xRaw := TRUE;
    ELSIF PV <= Alm.Cfg_Lim - Alm.Cfg_DB THEN
        xRaw := FALSE;
    END_IF;
ELSE
    IF PV < Alm.Cfg_Lim THEN
        xRaw := TRUE;
    ELSIF PV >= Alm.Cfg_Lim + Alm.Cfg_DB THEN
        xRaw := FALSE;
    END_IF;
END_IF;
Alm.Inp_Cond := xRaw;
""" + CORE_MAP)

# ---------------------------------------------------------------------------
# FB_AI
# ---------------------------------------------------------------------------
AI = dict(
    name="FB_AI",
    comment="Analog input for a T_AI: scaling, square root, low cut-off, NAMUR NE43 range check, "
            "NE107 status, filter, bad-value action, simulation, rate of change, ISA-18.2 alarms",
    inputs=[],
    inouts=[V("AI", PREFIX + "AI", "Analog input object")],
    outputs=[
        V("PV", "REAL", "Process value (EU) = AI.Val_PV"),
        V("Bad", "BOOL", "PV bad = AI.Sts_Bad"),
    ],
    private=[
        V("xFirst", "BOOL", "First scan after cold / warm start", "TRUE"),
        V("tonClk", "TON", "Free-running clock for elapsed time"),
        V("xClkRst", "BOOL", "Clock restart"),
        V("tClkLast", "TIME", "Clock value on previous scan"),
        V("tDelta", "TIME", "Time since previous scan"),
        V("rDt", "REAL", "Time since previous scan (s)"),
        V("xRawErr", "BOOL", "Raw span not configured"),
        V("xEUErr", "BOOL", "EU span not configured"),
        V("rPctRaw", "REAL", "Signal in % of span, before characterisation"),
        V("rPct", "REAL", "Signal in % of span, after characterisation"),
        V("rEU", "REAL", "Unfiltered PV (EU)"),
        V("rFilt", "REAL", "Filtered PV (EU)"),
        V("rOut", "REAL", "Final PV (EU)"),
        V("rLastGood", "REAL", "Last good PV (EU)"),
        V("xFieldBad", "BOOL", "Field signal bad (ignores simulation)"),
        V("xBad", "BOOL", "PV bad"),
        V("xBadPrev", "BOOL", "PV bad on previous scan"),
        V("xSimPrev", "BOOL", "Simulation on previous scan"),
        V("xReinit", "BOOL", "Re-initialise filter and rate of change this scan"),
        V("tRocAcc", "TIME", "Rate-of-change window time"),
        V("rRocRef", "REAL", "PV at start of rate-of-change window"),
        V("rRoc", "REAL", "Rate of change (EU/s)"),
        V("fbHH", "FB_AlmLim", "High-high alarm"),
        V("fbH", "FB_AlmLim", "High alarm"),
        V("fbL", "FB_AlmLim", "Low alarm"),
        V("fbLL", "FB_AlmLim", "Low-low alarm"),
        V("fbROC", "FB_AlmLim", "Rate-of-change alarm"),
        V("fbBad", "FB_Alarm", "Bad PV alarm"),
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
rDt := DINT_TO_REAL(TIME_TO_DINT(tDelta)) * 0.001;

(* ===== 2. Configuration check ===== *)
xRawErr := AI.Cfg_RawMax = AI.Cfg_RawMin;
xEUErr := AI.Cfg_EUMax = AI.Cfg_EUMin;

(* ===== 3. Raw counts to % of span ===== *)
IF NOT xRawErr THEN
    rPctRaw := (INT_TO_REAL(AI.Inp_Raw) - INT_TO_REAL(AI.Cfg_RawMin)) * 100.0
               / (INT_TO_REAL(AI.Cfg_RawMax) - INT_TO_REAL(AI.Cfg_RawMin));
ELSE
    rPctRaw := 0.0;
END_IF;

(* ===== 4. Signal validation: NAMUR NE43 limits, channel and device diagnostics ===== *)
AI.Sts_URng := rPctRaw < AI.Cfg_BadLoPct;
AI.Sts_ORng := rPctRaw > AI.Cfg_BadHiPct;
xFieldBad := AI.Sts_URng OR AI.Sts_ORng OR AI.Inp_ChFault OR (AI.Inp_NE107 = 1)
             OR xRawErr OR xEUErr;

(* ===== 5. Characterisation: square root extraction, low cut-off ===== *)
rPct := rPctRaw;
IF AI.Cfg_SqrtExtract THEN
    IF rPct > 0.0 THEN
        rPct := SQRT(rPct * 0.01) * 100.0;
    ELSE
        rPct := 0.0;
    END_IF;
END_IF;
IF (AI.Cfg_LoCutoff > 0.0) AND (rPct < AI.Cfg_LoCutoff) THEN
    rPct := 0.0;
END_IF;
rEU := AI.Cfg_EUMin + rPct * 0.01 * (AI.Cfg_EUMax - AI.Cfg_EUMin);

(* ===== 6. Simulation replaces the field signal ===== *)
AI.Sts_Sim := AI.Sim_En;
IF AI.Sim_En THEN
    rEU := AI.Sim_PV;
    xBad := FALSE;
ELSE
    xBad := xFieldBad;
END_IF;

(* ===== 7. First-order filter, re-initialised on start, recovery or sim change ===== *)
xReinit := xFirst OR (xBadPrev AND NOT xBad) OR (AI.Sim_En <> xSimPrev);
IF xReinit OR (AI.Cfg_FiltTC <= 0.0) THEN
    rFilt := rEU;
ELSIF NOT xBad AND (rDt > 0.0) THEN
    rFilt := rFilt + (rEU - rFilt) * rDt / (AI.Cfg_FiltTC + rDt);
END_IF;
xBadPrev := xBad;
xSimPrev := AI.Sim_En;

(* ===== 8. Bad value action ===== *)
IF xBad THEN
    CASE AI.Cfg_BadAction OF
        1: rOut := AI.Cfg_SubstPV;
        2: rOut := AI.Cfg_EUMin;
        3: rOut := AI.Cfg_EUMax;
    ELSE
        rOut := rLastGood;
    END_CASE;
    AI.Sts_Subst := TRUE;
ELSE
    rOut := rFilt;
    rLastGood := rFilt;
    AI.Sts_Subst := FALSE;
END_IF;

AI.Val_PV := rOut;
AI.Sts_Bad := xBad;
IF NOT xEUErr THEN
    AI.Val_PVPct := (rOut - AI.Cfg_EUMin) * 100.0 / (AI.Cfg_EUMax - AI.Cfg_EUMin);
ELSE
    AI.Val_PVPct := 0.0;
END_IF;

(* ===== 9. Quality and NAMUR NE107 status ===== *)
IF xBad THEN
    AI.Sts_Quality := 2;
ELSIF AI.Sim_En OR (AI.Inp_NE107 = 2) OR (AI.Inp_NE107 = 3) THEN
    AI.Sts_Quality := 1;
ELSE
    AI.Sts_Quality := 0;
END_IF;

IF xBad THEN
    AI.Sts_NE107 := 1;                          (* F: failure *)
ELSIF AI.Sim_En OR (AI.Inp_NE107 = 2) THEN
    AI.Sts_NE107 := 2;                          (* C: function check, incl. simulation *)
ELSIF AI.Inp_NE107 = 3 THEN
    AI.Sts_NE107 := 3;                          (* S: out of specification *)
ELSIF AI.Inp_NE107 = 4 THEN
    AI.Sts_NE107 := 4;                          (* M: maintenance required *)
ELSE
    AI.Sts_NE107 := 0;                          (* good *)
END_IF;

(* ===== 10. Rate of change over a 1 s window (EU/s), no spike on recovery / sim change ===== *)
IF xReinit OR xBad THEN
    rRocRef := rOut;
    tRocAcc := T#0S;
    rRoc := 0.0;
ELSE
    tRocAcc := tRocAcc + tDelta;
    IF tRocAcc >= T#1S THEN
        rRoc := (rOut - rRocRef) / (DINT_TO_REAL(TIME_TO_DINT(tRocAcc)) * 0.001);
        rRocRef := rOut;
        tRocAcc := T#0S;
    END_IF;
END_IF;
AI.Val_ROC := rRoc;

(* ===== 11. Alarms (ISA-18.2): process alarms suppressed by design while PV is bad ===== *)
fbHH(PV := rOut, IsHigh := TRUE, SuppressIn := xBad, Alm := AI.Alm_HH);
fbH(PV := rOut, IsHigh := TRUE, SuppressIn := xBad, Alm := AI.Alm_H);
fbL(PV := rOut, IsHigh := FALSE, SuppressIn := xBad, Alm := AI.Alm_L);
fbLL(PV := rOut, IsHigh := FALSE, SuppressIn := xBad, Alm := AI.Alm_LL);
fbROC(PV := ABS(rRoc), IsHigh := TRUE, SuppressIn := xBad, Alm := AI.Alm_ROC);

AI.Alm_Bad.Inp_Cond := xFieldBad AND NOT AI.Sim_En;
fbBad(SuppressIn := FALSE, Alm := AI.Alm_Bad);

(* ===== 12. Pins ===== *)
PV := rOut;
Bad := xBad;
xFirst := FALSE;
""")

DFBS = [ALMCORE, ALARM, ALMLIM, AI]


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------
def st_text(fb):
    out = [f"FUNCTION_BLOCK {fb['name']}", f"(* {fb['comment']} *)",
           f"(* PCLib {lib.LIB_VERSION} - generated by gen_dfb.py *)", ""]
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


def xdb_text(dfbs, ddts, now):
    dts = now.strftime("dt#%Y-%m-%d-%H:%M:%S")
    L = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', "<FBExchangeFile>"]
    L += lib.file_header(now, PRODUCT, "Function Block source file")
    L += lib.ddt_source_lines(ddts, now)
    for fb in dfbs:
        L.append(f'<FBSource nameOfFBType={quoteattr(fb["name"])} version="{lib.LIB_VERSION}" '
                 f'dateTime="{dts}">')
        L.append(f"\t<comment>{escape(fb['comment'])}</comment>")
        pin = 1
        for tag, key in (("inputParameters", "inputs"), ("inOutParameters", "inouts"),
                         ("outputParameters", "outputs")):
            if fb[key]:
                block, pin = xdb_vars(tag, fb[key], pin)
                L += block
        if fb["private"]:
            L += xdb_vars("privateLocalVariables", fb["private"], None)[0]
        L.append('\t<FBProgram name="Main">')
        L.append(f"\t\t<STSource>{escape(fb['code'].strip(chr(10)))}</STSource>")
        L.append("\t</FBProgram>")
        L.append("</FBSource>")
    L.append("</FBExchangeFile>")
    return "\n".join(L) + "\n"


def main():
    types = lib.resolve(lib.TYPES, PREFIX, True)
    by_name = {t[0]: t for t in types}
    ddts = [by_name[PREFIX + n] for n in ("Alarm", "AlmLim", "AI")]
    now = dt.datetime.now().replace(microsecond=0)

    os.makedirs(os.path.join(HERE, "dfb"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "export"), exist_ok=True)
    for fb in DFBS:
        with open(lib.lp(os.path.join(HERE, "dfb", fb["name"] + ".st")), "w",
                  encoding="utf-8", newline="\r\n") as f:
            f.write(st_text(fb))

    txt = xdb_text(DFBS, ddts, now)
    ET.fromstring(txt.encode("utf-8"))      # well-formedness check
    with open(lib.lp(os.path.join(HERE, "export", "PCLib_DFB_AI_CE_V16.2.xdb")), "w",
              encoding="utf-8", newline="\r\n") as f:
        f.write(txt)
    print(f"{len(DFBS)} DFBs -> dfb/*.st and export/PCLib_DFB_AI_CE_V16.2.xdb")


if __name__ == "__main__":
    main()
