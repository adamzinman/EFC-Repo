# DFB work notes (read these instead of re-reading sources)

## Decisions (user, step 0 answers)
- Types source: `EFC-Repo/types/` (files say "PCLib v1.00" = EFCLib v1). Generator `types/gen_pclib.py`, DDTs `types/xdd/T_*.xdd`, docs `types/README.md` (= `UDT Standards.md`).
- IN_OUT pin: user said "UDT Data" -> identifier `UDT_Data` (no spaces in IEC identifiers). Confirm at step 1 STOP.
- DFB names `FB_<type minus T_>`. Version 1.0 (XDB writes `1.00`, sample style MAJOR.MINOR two-digit minor).
- DO: propose a `T_DO` (no type exists). Don't modify existing T_ types.
- Modes: four (A/M/MT/L) per standard 10.3.1, not three.
- Field I/O: DFB copies IN pins -> `UDT_Data.Inp_*`, drives OUT pins from `UDT_Data.Out_*`.
- Alarms: follow T_Alarm ISA-18.2 model (Ack vs Reset distinct). Fix the convention accordingly.
- Nested alarms: shared FB_Alarm / FB_AlmLim (+ FB_AlmCore) instances; request a 2nd small export as needed.
- Cmd_: act on TRUE level, clear to FALSE at end of DFB (no R_TRIG needed for commands).
- Checksums: try omit -> copy sample -> read back. Generator switch `--checksums omit|copy|value`.
- DDTSource: embed every T_ DDT used (incl. nested) in dependency order; test omission on pilot.
- T_Intlk parallel arrays conflict with std 10.5 -> implement as-is, raise as std/type change.
- Old `types/gen_dfb.py` + `types/dfb/FB_*.st`: reference ST only; st2xdb replaces its XML writer.

## XDB format (from XDB_FORMAT_REFERENCE.md, binding)
- Reference files copied from user zip: scratchpad `zip/DFB Converter Prompt/`. Need to be committed to `types/dfb/_reference/` (prompt expects them there).
- CRLF, tabs, ASCII, `<x></x>` never `<x/>`, no CDATA, escape & < >.
- fileHeader: `company="Schneider Automation" product="Control Expert V16.2 - 250430" dateTime="date_and_time#Y-M-D-H:M:S"(unpadded) content="Function Block source file" DTDVersion="41"`.
- FBSource/DDTSource dateTime `dt#YYYY-MM-DD-HH:MM:SS` padded. Versions `X.YY`.
- Block order: inputParameters, inOutParameters, publicLocalVariables, privateLocalVariables, FBProgram*. outputParameters NOT demonstrated.
- PositionPin attribute on in/inout pins, 1-based. Locals have no children.
- ST body col 0, CRLF, `</STSource>` col 0.
- Not demonstrated: outputParameters, EBOOL, arrays, R_TRIG/F_TRIG, nested user DFB instances, DDT in DDT, comments/initial values on variables, ST comments, `>`/`&` in ST, TIME/STRING/DT/UDINT/DINT/UINT/WORD/LREAL types.
- Existing `types/xdd/*.xdd` (generator-written, NOT a real export, import status unknown) use `<comment>` and `<variableInit value="">` children, nested `typeName="T_AlmLim"`, arrays `typeName="ARRAY[0..15] OF BOOL"`. Header differs from real export.

## Controls Standard rev I (Drive: Controls Standard folder; decoded copy in scratchpad cs/10-plc-standards.tex)
Chapter order (master tex): 1 overview, 2 terminology, 3 design process, 4 contractors, 5 process definition, 6 hardware, 7 software, 8 networking, 9 accounts, 10 PLC standards, 11 SCADA, 12 reference. App. I = data-types-future (T_ types).
- 5.1 Permissives, Interlocks, SIFs: permissive = must be satisfied before action may start OR continue; control interlock prevents or stops an action.
- 5.x Protective Function Requirements (future): no auto reset/restart where hazardous; reset must not initiate motion; reset clears latch only after cause gone.
- 7.x Online changes: safety signals never bypassed in software; HMI bypass only on Cfg_Bypassable process conditions.
- 10.3 Operating Modes and Commands: HMI requests never drive outputs directly; Manual must not bypass protective functions; start-up must not create unexpected start.
- 10.3.1 Mode Definitions (PCLib): A=Auto(3) Prog_ cmds, operator start/stop/open/close ignored. M=Manual(2) Cmd_ cmds, Prog_ ignored. MT=Maint(1) Maintenance role, Prog_ ignored, cannot be acquired. L=OOS(0) outputs de-energized (safe), all cmds ignored.
  - Every mode: interlocks (Inp_IntlkOK) stop running equipment, incl. M and MT; bypass only via T_Intlk timed bypass. Permissives (Inp_PermOK) block a start in Auto and Manual. Sim is not a mode. PLC decides mode change, reports Sts_Mode.
  - MT table: permissives active (product/batch-only ones may be marked bypassable in MT per table; default none); interlocks active; process alarms may be suppressed by design, device-fault/health alarms stay; run-time/start counters counted; leave MT -> Manual only.
  - Transitions all via Manual: M->A (Cmd_Auto or Prog_Auto, no bump: owner matches state); A->M (Cmd_Man or Prog_Man; blocked while Prog_Lock; outputs hold); M->MT (Cmd_Maint; only if no owner; Cmd_ForceRelease; not if Cfg_NoMaint); MT->M (device in known state e.g. valve closed, motor stopped); M or MT -> L (Cmd_OOS; outputs safe, alarms OOS state H); L->M (Cmd_Man).
  - Power-up: Cfg_PowerUpMode (default Man). OOS should survive power cycle - T_Mode doesn't yet (TBD).
- 10.3.2 Setpoint Limits: PLC clamps/rejects out-of-limit operator values.
- 10.4 Data types: analog scaling handles /0, invalid cfg, under/over range, bad quality; alarm compare uses scaled value only when quality OK.
- 10.5 Interlocks and First-Out: structured condition type (not parallel arrays); per condition enable/raw/active/latched/bypassed/first-out/message/timestamp; summary any-active/trip-active/reset-permitted/bypass-present/first-out index; fail to defined state on bad/stale inputs when risk assessment requires; reset never clears active cause; bypass restart behaviour per policy.
- 10.8 Reusable FBs, Design Rules: DDT as IN_OUT; no direct I/O or globals; fail-safe defaults for every input; header comment purpose/revision/author/date; "Off/Manual/Auto/Lockout" pattern (CONFLICT with 10.3.1, which governs T_ types); interlock and E-stop inputs as pins, visible at the call.

## T_ type facts
- Conventions: Cmd_ booleans one-shot, logic clears. `...OK` booleans TRUE = healthy (FALSE default = fail-safe). Interlock stops running eqpt; permissive only blocks start.
- Nesting: T_AI(5 AlmLim,1 Alarm); T_DI(2 Alarm); T_DValve(Mode,Perm,Intlk,5 Alarm,Run); T_CValve(Mode,Intlk,3 Alarm); T_Motor(Mode,Perm,Intlk,7 Alarm,AlmLim,Run); T_VFD(Mode,Perm,Intlk,10 Alarm,Run); T_Intlk(2 Alarm, arrays[0..15]).
- `Perm`/`Intlk` groups: "Out_OK ANDed with Inp_IntlkOK / Inp_PermOK".
- Maintained-looking Cmd_: Cmd_Jog (doc says maintained), Cmd_Rev (direction level), Cmd_Spd / Cmd_ManPos (REAL setpoints).
- Old FB_AI/FB_AlmCore logic reviewed (types/dfb/*.st): uses R_TRIG/F_TRIG, RRTC_DT, TIME_TO_DINT, free-running 1 h TON for dt. Good base for AI and alarms.

## Step 1 answers (2026-10-21): user said "use your best judgement" -> all [R] answers in spec/QUESTIONS.md adopted.
- Pilot 2a = FB_AlmCore only (no DDT). 2b (FB_Alarm, FB_AlmLim, FB_AI) waits for the DFB_FmtTest export (Q3).
- .gitattributes: exchange files + *.st are -text (Q27). Reference files copied to types/dfb/_reference/ (Q28).
- No MatIEC binary in the container (Q30 not possible here).
- Raw XDB indentation: variables 3 tabs, pin attribute 4 tabs (reference .md section 8 says 4/5; raw wins).
- Output pins numbered after inputs in one sequence; outputParameters after inputParameters (unverified).
