# Step 1 questions (reply e.g. "all recommended except 6, 13")

Q-numbers are referenced from the spec files. [R] = recommended answer.

## Interface and scope
1. **IN_OUT pin name.** You wrote "UDT Data"; identifiers can't contain spaces. [R] `UDT_Data`.
2. **Helper DFBs.** The core types nest `T_Alarm`, `T_AlmLim`, `T_Mode`, `T_RunTime`, `T_Intlk`. [R] Add `FB_AlmCore`, `FB_Alarm`, `FB_AlmLim`, `FB_Mode`, `FB_RunTime` to the run; `FB_Intlk` is the "interlock" core type.
3. **Second export (format blocker for every DFB after the pilot's first stage).** Please export from 16.2 one throw-away DFB `DFB_FmtTest` whose interface has: an IN BOOL with an initial value; an OUT BOOL and an OUT REAL; an IN_OUT of a test DDT that contains a nested DDT, an `ARRAY[0..3] OF BOOL`, and one member each of TIME, DT, STRING[8], UDINT, DINT, WORD, LREAL (one with an initial value and a comment); privates: an instance of another user DFB, an `R_TRIG`, a `TON`, a BOOL with a comment; one ST section using `(* comment *)`, `>`, `>=`, `<>`, `&` is not needed. Also export the test DDT alone (`.XDD`). [R] Yes; until then only `FB_AlmCore` can be generated from verified elements alone.
4. **Pilot order.** `FB_AI` needs nested `FB_AlmLim`/`FB_Alarm` instances (not demonstrated). [R] Pilot in two stages: 2a `FB_AlmCore` alone (pins in/out, TON/TOF, no DDT) to prove `outputParameters` and the generator; 2b `FB_Alarm`, `FB_AlmLim`, `FB_AI` after the Q3 export.
5. **T_DO.** Approve the proposed type in `03_DO_PROPOSAL.md` (29 members)? [R] Yes as written; I add it to `gen_pclib.py` only after approval, and the Ignition UDT / Appendix I follow through the steward queue.

## Standard and type conflicts (raise, don't fix here)
6. **Operator stop in Auto.** Std 10.3.1: in Auto, operator start/stop/open/close commands are ignored. With `Prog_Lock` held the operator can't stop the device from the HMI at all. [R] Follow the standard exactly; queue a standard question whether `Cmd_Stop` should always be honoured.
7. **DValve permissive scope.** Type: "Inp_PermOK TRUE = may leave safe position". [R] "Safe position" = interlock position (`Cfg_IntlkOpen`); the permissive blocks moves away from it, never towards it.
8. **Output patterns for valves.**
   a. Single-coil `T_DValve`: `Out_Open` is documented as "open (energise)", which only fits fail-closed valves. [R] `Out_Open` = the one coil, energised to drive away from the fail position (`Out_Open := xOpenReq XOR Cfg_FailOpen`); README explains it; propose renaming to `Out_Coil` later.
   b. OOS dual-coil valve: both coils off = valve stays where it is. [R] Accept (that is "de-energized"); note it in the README.
   c. OOS `T_CValve`: [R] `Out_CV := Cfg_FailPos` (not raw 0).
9. **KnownState for Maint -> Manual** (std: "e.g. valve closed, motor stopped"). [R] DValve: confirmed at fail position; CValve: `ABS(Val_Dev) <= Cfg_DevLim`; Motor/VFD: `Sts_Stopped`; DO: `Sts_Off`.
10. **`Sts_Avail`** ("available to Auto/program control"). [R] mode Auto or Manual (std: Manual devices can still be acquired) AND not local AND no trip/fault.
11. **DI while bad.** No `Cfg_BadAction` in T_DI. [R] `Val` holds the last good value; `Sts_Bad`, `Alm_Bad`.
12. **Local/Remote.** No `Cfg_HasRemote`; `Inp_Remote` FALSE = local. [R] Tie the `Remote` pin TRUE when no switch is fitted; in Local the PLC outputs are FALSE (hand control is outside the PLC), commands are cleared, travel/fail-start alarms are suppressed, state = not available.
13. **Simulation.** "Ignore field I/O, logic generates feedback". [R] In sim the `Out_*` members show the simulated command but the field OUT pins are forced FALSE / 0, so a real device can't move while simulated. DValve sim travel time T#2S fixed. E-stop and AvailOK are still honoured in sim.
14. **Maintained `Cmd_` members** (prompt asked me to flag them): `Cmd_Jog` (doc: maintained), `Cmd_Rev` (direction level), `Cmd_Spd`, `Cmd_ManPos` (REAL setpoints). [R] Keep maintained. Risk: a lost OPC UA session can leave `Cmd_Jog` TRUE; jog stops when the mode leaves Maint. Propose a `Cfg_JogMax` TIME member later if you want a dead-man limit.
15. **Trips that need `Cmd_Reset`.** [R] Motor: OL, FailStart, E-stop; VFD adds DrvFault, CommFail. Interlock loss stops immediately but is not a device trip (latching belongs to `Intlk.Cfg_Latch`). Reset never starts the motor; the run request is cleared by any trip, and by an interlock stop unless Auto + `Cfg_AutoRestart`.
16. **`Prog_*` semantics.** Pairs (`Prog_Start`/`Prog_Stop`, `Prog_Open`/`Prog_Close`, `Prog_Auto`/`Prog_Man`, `Prog_Acquire`/`Prog_Release`) read like requests. [R] Edge-triggered requests (the DFB acts on the FALSE->TRUE change using a stored previous value and does **not** clear them; owner logic owns the bits). `Prog_Lock`, `Prog_Pos`, `Prog_Spd`, `Prog_Rev` are levels.
17. **Ownership.** [R] Acquire allowed in Auto or Manual, refused in Maint/OOS and when `Inp_ReqOwnerID` = 0; entering Maint/OOS or `Cmd_ForceRelease` frees the owner and also ignores `Prog_Lock` until the owner re-acquires. Auto does not require an owner.
18. **VFD comms loss.** [R] Trip (stop request, reset required) + `Alm_CommFail`; the drive's own comm-loss setting does the physical stop.
19. **Starts in the last hour (`T_RunTime.Val_StartsLastHr`).** A true rolling hour needs a timestamp per start (array). [R] 6 x 10-minute buckets (private `ARRAY[0..5] OF INT` + one TON), i.e. a rolling hour with 10 min resolution. Needs arrays (Q3).
20. **CValve travel and reversals.** [R] Computed from `Out_CV` (deterministic, no feedback noise); reversals counted only for moves larger than 0.5 %.
21. **CValve `Sts_Closed`.** [R] `Inp_ZSC OR Val_Pos <= 0.5 %`.
22. **`T_Intlk.Alm_Trip`.** For permissive groups (`Cfg_Latch` FALSE) "tripped" would alarm whenever a start permissive is simply not met. [R] Condition = `NOT Out_OK AND Cfg_Latch`.
23. **Standard conflicts to queue (doc-steward):** (a) 10.8 says "Off/Manual/Auto/Lockout" but 10.3.1 defines A/M/MT/L for these types; (b) 10.5 asks for a structured condition type with per-condition timestamp, `T_Intlk` uses parallel arrays and has no timestamp; (c) 10.3.1 says OOS should survive a power cycle, `T_Mode` can't (TBD in the standard); (d) 10.8 header asks for "author", prompt asks name/version/date/purpose. [R] Queue all four; the DFBs follow 10.3.1, `T_Intlk` as-is, `Cfg_PowerUpMode` on cold start, header includes author "EFC Controls".
24. **VFD details.** [R] `Out_SpdRef` = 0.0 when not running; `Inp_DrvWarn` -> NE107 S; direction change accepted only while stopped; jog uses `Cmd_Spd`.

## Platform, files, process
25. **`RRTC_DT`** (alarm timestamps, used by the old FB_Alarm) and `TIME_TO_DINT`: Control Expert functions. [R] Keep; you confirm they exist in your 16.2 library at pilot 2b (I can't verify).
26. **Bit packing for `Sts_CondWord` etc.** [R] Build with `SHL`/`OR` on WORD, not `word.n` bit extraction (that needs a project option).
27. **Line endings in git.** Root `.gitattributes` has `* text=auto eol=lf`; only `PCLib/` exempts `*.xdb`. A committed `.XDB` under `types/` would lose its CRLF. [R] Add `*.xdb *.xdd *.xsy *.st -text` (types/ and root) before anything is committed; byte-check after checkout.
28. **Reference files location.** The prompt expects `types/dfb/_reference/DFB_Device.XDB` and `XDB_FORMAT_REFERENCE.md`; they are only in my scratchpad. [R] I copy them into `types/dfb/_reference/` at step 2 (with the .gitattributes fix).
29. **Cold vs warm start.** Without `%S0`/`%S1` a DFB can only detect a cold start (privates reset). On a warm start T_ data, bypasses, latches and timers carry on. [R] Accept; document it.
30. **Syntax gate.** `PCLib/tests/` has MatIEC. [R] Run MatIEC on each `.st` as an extra lint; reports will say a MatIEC pass does not prove Control Expert acceptance.
