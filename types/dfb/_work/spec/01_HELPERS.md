# Step 1 spec: helper DFBs (building blocks nested in the core types)

Written-by key: **PLC** = this DFB, **HMI** = Ignition, **Owner** = other PLC logic (phase, device DFB), **Pin** = copied from a DFB pin.

## FB_AlmCore (no data type)

(a) Pins, all IN except where noted: `Cond, Supp, OOSIn, Enabled, LatchCfg, NoAck, Ack, Rst, Shelve, Unshelve, RemoveSvc, ReturnSvc : BOOL; OnDly, OffDly, MaxShelf : TIME`.
OUT: `Active, Unack, Shelved, Suppressed, OOS, EvtActive, EvtRTN : BOOL; State : INT; ShelfLeft : TIME`.
Private: `tonShelf, tonOn : TON; tofOff : TOF;` memories `xOOS, xShelved, xLatch, xUnack, xActivePrev, xInitDone`.
Logic = old FB_AlmCore plus `OOSIn` (inhibit, State 7) and prev-state edge detection.

## FB_Alarm (`T_Alarm`) and FB_AlmLim (`T_AlmLim`)

(a) Pins

| Pin | Dir | Type | Purpose |
|---|---|---|---|
| `UDT_Data` | IN_OUT | `T_Alarm` / `T_AlmLim` | alarm object |
| `PV` | IN | REAL | FB_AlmLim only: value compared with `Cfg_Lim` |
| `IsHigh` | IN | BOOL | FB_AlmLim only: TRUE = high alarm |
| `SuppressIn` | IN | BOOL | design suppression from owner (e.g. PV bad) |
| `OOSIn` | IN | BOOL | owner device Out of Service -> state H |
| `ResetIn` | IN | BOOL | owner device `Cmd_Reset` |

(b) Members (T_AlmLim = T_Alarm + `Cfg_Lim`, `Cfg_DB`)

| Member | Type | Written by | Logic |
|---|---|---|---|
| `Cfg_Lim` | REAL | HMI | AlmLim: high: cond set when PV > Lim; low: PV < Lim |
| `Cfg_DB` | REAL | HMI | AlmLim: high clears at PV <= Lim-DB, low at PV >= Lim+DB; negative DB treated as 0 |
| `Inp_Cond` | BOOL | Owner (Alarm) / PLC (AlmLim) | raw condition into FB_AlmCore |
| `Inp_Suppress` | BOOL | Owner | ORed with `SuppressIn` -> state G |
| `Cfg_En` | BOOL | HMI | FALSE -> inhibited, state H(7) |
| `Cfg_Latch` | BOOL | HMI | latch until reset after RTN (state E) |
| `Cfg_NoAck` | BOOL | HMI | never unacked |
| `Cfg_OnDly` | TIME | HMI | TON on condition |
| `Cfg_OffDly` | TIME | HMI | TOF on condition |
| `Cfg_Priority` | INT | HMI | passthrough (Ignition priority) |
| `Cfg_Class` | INT | HMI | passthrough |
| `Cfg_MaxShelf` | TIME | HMI | shelve timer PT |
| `Cmd_Ack` | BOOL | HMI | clears `Sts_Unack`; cleared by PLC |
| `Cmd_Reset` | BOOL | HMI | (OR `ResetIn`) clears latch if cond gone; cleared by PLC |
| `Cmd_Shelve` | BOOL | HMI | shelve if enabled and in service; cleared |
| `Cmd_Unshelve` | BOOL | HMI | unshelve; cleared |
| `Cmd_RemoveSvc` | BOOL | HMI | out of service (state H); cleared. "Permit required" = Ignition role |
| `Cmd_ReturnSvc` | BOOL | HMI | return to service; cleared |
| `Sts_Active` | BOOL | PLC | delayed cond OR latch |
| `Sts_Unack` | BOOL | PLC | set on activation unless NoAck; cleared by Ack or inhibit |
| `Sts_Shelved` | BOOL | PLC | shelve memory |
| `Sts_Suppressed` | BOOL | PLC | suppressed by design |
| `Sts_OOS` | BOOL | PLC | removed from service (Cmd_RemoveSvc) OR `OOSIn` |
| `Sts_State` | INT | PLC | 0..7 per ISA-18.2 (old FB_AlmCore order) |
| `Sts_ShelfLeft` | TIME | PLC | MaxShelf - ET while shelved, else 0 |
| `Val_Count` | UDINT | PLC | +1 on each activation |
| `Val_LastActive` | DT | PLC | PLC clock (`RRTC_DT`) on activation |
| `Val_LastRTN` | DT | PLC | PLC clock on return to normal |

(c) Modes: none of its own; `OOSIn` from owner.
(d) It is the alarm. Delay/deadband/limit from its own members.

## FB_Mode (`T_Mode`)

(a) Pins: `UDT_Data : T_Mode` (IN_OUT); `KnownState : BOOL` (IN, device says Maint->Man allowed).
OUT: none (device DFB reads `UDT_Data.Mode.Sts_*`).

(b) Members

| Member | Type | Written by | Logic |
|---|---|---|---|
| `Cmd_Auto` | BOOL | HMI | Man->Auto; cleared |
| `Cmd_Man` | BOOL | HMI | Auto->Man (not while Prog_Lock), Maint->Man (if KnownState), OOS->Man; cleared |
| `Cmd_Maint` | BOOL | HMI | Man->Maint if not owned and not Cfg_NoMaint; cleared |
| `Cmd_OOS` | BOOL | HMI | Man/Maint->OOS; cleared |
| `Prog_Auto` | BOOL | Owner | Man->Auto (see Q16) |
| `Prog_Man` | BOOL | Owner | Auto->Man, ignores Prog_Lock |
| `Prog_Lock` | BOOL | Owner | blocks Cmd_Man in Auto (level) |
| `Prog_Acquire` | BOOL | Owner | if free and mode is Auto or Man: Val_OwnerID := Inp_ReqOwnerID (see Q17) |
| `Prog_Release` | BOOL | Owner | if Inp_ReqOwnerID = Val_OwnerID: free |
| `Inp_ReqOwnerID` | DINT | Owner | requester ID; 0 invalid (acquire refused) |
| `Cmd_ForceRelease` | BOOL | HMI | frees ownership (Supervisor role in Ignition); cleared |
| `Cfg_PowerUpMode` | INT | HMI | mode on cold start; invalid -> 2 |
| `Cfg_NoMaint` | BOOL | HMI | blocks Cmd_Maint |
| `Sts_Auto` | BOOL | PLC | Sts_Mode = 3 |
| `Sts_Man` | BOOL | PLC | = 2 |
| `Sts_Maint` | BOOL | PLC | = 1 |
| `Sts_OOS` | BOOL | PLC | = 0 |
| `Sts_Mode` | INT | PLC | current mode |
| `Sts_Owned` | BOOL | PLC | Val_OwnerID <> 0 |
| `Val_OwnerID` | DINT | PLC | owner ID, 0 = free; cleared on cold start, entering Maint/OOS |

(c) Mode table: see 00_COMMON transitions. (d) Alarms: none.

## FB_RunTime (`T_RunTime`)

(a) Pins: `UDT_Data : T_RunTime` (IN_OUT). Owner writes `Inp_Running` before the call.

(b) Members

| Member | Type | Written by | Logic |
|---|---|---|---|
| `Inp_Running` | BOOL | Owner | running |
| `Cfg_MaintHrs` | REAL | HMI | 0 = off |
| `Cmd_ResetMaint` | BOOL | HMI | Val_HrsSinceMaint := 0; cleared |
| `Cmd_ResetAll` | BOOL | HMI | all counters 0; cleared (Supervisor role in Ignition) |
| `Val_RunSecs` | UDINT | PLC | +1 per full second running (ms remainder kept in a private TIME) |
| `Val_RunHrs` | REAL | PLC | Val_RunSecs / 3600.0 |
| `Val_Starts` | UDINT | PLC | +1 on Inp_Running FALSE->TRUE |
| `Val_StartsLastHr` | INT | PLC | rolling 60 min (see Q19) |
| `Val_LastRun` | TIME | PLC | duration of the last completed run (TON ET captured on stop) |
| `Val_HrsSinceMaint` | REAL | PLC | accumulates run time |
| `Sts_MaintDue` | BOOL | PLC | Cfg_MaintHrs > 0 AND Val_HrsSinceMaint >= Cfg_MaintHrs |

(c) Modes: owner stops calling `Inp_Running` TRUE in OOS. MT counts (standard). (d) Alarms: none (MaintDue feeds NE107 M).

## FB_Intlk (`T_Intlk`), core type "interlock"

Used standalone (own `T_Intlk` instance) and nested (`Perm`, `Intlk` in devices; the device DFB calls it).
Owner logic writes `Inp_Cond[n]` before the call (arrays cannot be pins).

(a) Pins: `UDT_Data : T_Intlk` (IN_OUT); `BypassPerm : BOOL` (IN -> `Inp_BypassPerm`, key switch / permit);
`ResetIn : BOOL` (IN, owner device reset); `OOSIn : BOOL` (IN, owner OOS, for its alarms).
OUT: `OK : BOOL` (= `Out_OK`).
Private: one free-running TON for dt; `xOKPrev`; `fbAlmTrip, fbAlmByp : FB_Alarm`.

(b) Members (n = 0..15)

| Member | Type | Written by | Logic |
|---|---|---|---|
| `Cfg_Tag`, `Cfg_Desc` | STRING | HMI | HMI-only / passthrough |
| `Inp_Cond[n]` | BOOL[16] | Owner | TRUE = healthy |
| `Cfg_Used[n]` | BOOL[16] | HMI | unused conditions count as healthy, cannot bypass/latch |
| `Cfg_CondDesc[n]` | STRING[32][16] | HMI | HMI-only / passthrough |
| `Cfg_Bypassable[n]` | BOOL[16] | HMI | bypass allowed (std 7: never for safety signals) |
| `Cfg_Latch` | BOOL | HMI | TRUE = interlock (failed conditions latch), FALSE = permissive |
| `Cfg_BypassMax` | TIME | HMI | bypass duration |
| `Cmd_Bypass[n]` | BOOL[16] | HMI | accepted if Used AND Bypassable AND Inp_BypassPerm; starts timer; cleared |
| `Cmd_Unbypass[n]` | BOOL[16] | HMI | remove bypass; cleared |
| `Cmd_UnbypassAll` | BOOL | HMI | remove all; cleared |
| `Inp_BypassPerm` | BOOL | Pin | bypass authorisation |
| `Cmd_Reset` | BOOL | HMI | (OR ResetIn) clears `Sts_Latched[n]` where `Inp_Cond[n]` is TRUE; cleared |
| `Out_OK` | BOOL | PLC | AND over used n of (`Sts_Bypassed[n]` OR (`Inp_Cond[n]` AND NOT `Sts_Latched[n]`)) |
| `Sts_OKNoByp` | BOOL | PLC | same without bypasses |
| `Sts_Bypassed[n]` | BOOL[16] | PLC | bypass active |
| `Sts_Latched[n]` | BOOL[16] | PLC | Cfg_Latch AND used AND NOT Inp_Cond AND NOT bypassed -> set |
| `Sts_FirstOut` | INT | PLC | on Out_OK TRUE->FALSE: lowest failed n; held until Out_OK TRUE again; -1 = none |
| `Sts_NumBypassed` | INT | PLC | count |
| `Sts_BypLeft[n]` | TIME[16] | PLC | counts down by dt; at 0 the bypass ends |
| `Sts_BypassLeft` | TIME | PLC | smallest non-zero `Sts_BypLeft[n]` (bypass that ends first) |
| `Sts_ResetReq` | BOOL | PLC | any latched AND every latched condition now healthy |
| `Sts_CondWord` | WORD | PLC | bit n = Inp_Cond[n] (built with SHL/OR, no bit extraction) |
| `Sts_BypWord` | WORD | PLC | bit n = Sts_Bypassed[n] |
| `Sts_LatchWord` | WORD | PLC | bit n = Sts_Latched[n] |
| `Alm_Trip` | T_Alarm | PLC | Inp_Cond := NOT Out_OK AND Cfg_Latch (see Q22) |
| `Alm_Bypass` | T_Alarm | PLC | Inp_Cond := Sts_NumBypassed > 0 |

16 bypass timers use the dt accumulator, not 16 TON instances (arrays of FB instances not demonstrated).
`FOR n := 0 TO 15` loops are bounded (standard 10.1 allows bounded iteration in ST).

(c) Modes: none of its own. Interlocks are never bypassed by a mode (std 10.3.1); only by this timed bypass.
(d) Alarms: Alm_Trip, Alm_Bypass; delays from their own members.

Std 10.5 gaps the type cannot meet (raise as type change, not fixed here): per-condition timestamp,
"structured condition type rather than parallel arrays", bypass restart policy (cold start clears bypasses because the DDT re-initialises; warm start keeps them).
