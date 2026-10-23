# Step 1 spec: FB_Motor (T_Motor) and FB_VFD (T_VFD)

FB_VFD = FB_Motor logic + drive, speed and direction parts. Shared rows are written once under FB_Motor.

## FB_Motor

(a) Pins

| Pin | Dir | Type | Purpose |
|---|---|---|---|
| `UDT_Data` | IN_OUT | T_Motor | HMI interface |
| `RunFbk` | IN | BOOL | contactor aux -> `Inp_RunFbk` |
| `Remote` | IN | BOOL | L/R in Remote -> `Inp_Remote` (tie TRUE if none, Q12) |
| `AvailOK` | IN | BOOL | MCC breaker / control power -> `Inp_AvailOK` |
| `EStopOK` | IN | BOOL | E-stop circuit healthy -> `Inp_EStopOK` |
| `IntlkOK` | IN | BOOL | -> `Inp_IntlkOK` |
| `PermOK` | IN | BOOL | -> `Inp_PermOK` |
| `IOFault` | IN | BOOL | -> `Inp_IOFault` |
| `OL` | IN | BOOL | overload tripped -> `Inp_OL` |
| `Current` | IN | REAL | amps -> `Inp_Current` (0 if not wired) |
| `BypassPerm` | IN | BOOL | bypass permit for `Perm` / `Intlk` |
| `Run` | OUT | BOOL | = `Out_Run` |

Effective: `xIntlkOK := Inp_IntlkOK AND Intlk.Out_OK`; `xPermOK := Inp_PermOK AND Perm.Out_OK`.
Run request: private `xRunReq`. Trip memory: private `xTrip` (reset required) -> `Sts_Tripped`.

Start allowed (`Sts_Ready` when stopped) = xPermOK AND xIntlkOK AND Inp_EStopOK AND Inp_AvailOK AND NOT xTrip
AND NOT local AND restart delay done AND NOT starts/hour limit AND mode in {Auto, Man, Maint}.

(b) Members

| Member | Type | Written by | Logic |
|---|---|---|---|
| `Cfg_Tag`, `Cfg_Desc` | STRING | HMI | passthrough |
| `Mode` | T_Mode | PLC/HMI | FB_Mode; KnownState := Sts_Stopped |
| `Perm`, `Intlk` | T_Intlk | PLC/HMI/Owner | FB_Intlk x2; Owner writes `Inp_Cond[]` |
| `Inp_RunFbk` | BOOL | Pin | feedback; replaced by Out_Run when Cfg_NoFbk or sim |
| `Inp_Remote` | BOOL | Pin | FALSE -> local |
| `Inp_AvailOK` | BOOL | Pin | FALSE: start blocked, running motor -> stop, state 5 (no trip) |
| `Inp_EStopOK` | BOOL | Pin | FALSE: run request cleared, trip (reset required, Q15), Alm_EStop |
| `Inp_IntlkOK` | BOOL | Pin | FALSE: stop; see trip rule below |
| `Inp_PermOK` | BOOL | Pin | blocks start only |
| `Inp_IOFault` | BOOL | Pin | Sts_Fault, NE107 F (no trip) |
| `Inp_OL` | BOOL | Pin | trip, Alm_OL |
| `Inp_Current` | REAL | Pin | -> Val_Current |
| `Cfg_FbkTime` | TIME | HMI | TON PT for FailStart / FailStop |
| `Cfg_RestartDly` | TIME | HMI | TON on stopped; blocks start; Sts_RestartLeft |
| `Cfg_NoFbk` | BOOL | HMI | feedback := Out_Run; FailStart/Stop/Uncmd not evaluated |
| `Cfg_AutoRestart` | BOOL | HMI | Auto only: keep run request through an interlock trip / loss of AvailOK; restart when healthy |
| `Cfg_RatedAmps` | REAL | HMI | Val_LoadPct divisor (0 -> LoadPct 0) |
| `Cfg_MaxStartsHr` | INT | HMI | 0 = no limit; blocks start when Run.Val_StartsLastHr >= limit |
| `Cmd_Start`, `Cmd_Stop` | BOOL | HMI | Man/Maint run request set / clear; cleared |
| `Cmd_Reset` | BOOL | HMI | clears xTrip if its cause is gone; alarms' / groups' ResetIn; cleared. Never starts the motor (std 5) |
| `Cmd_Jog` | BOOL | HMI | **maintained**; Maint only; runs while TRUE if start allowed (Q14) |
| `Prog_Start`, `Prog_Stop` | BOOL | Owner | Auto run request set / clear (Q16) |
| `Out_Run` | BOOL | PLC | (xRunReq OR jog) AND start/run allowed AND NOT xTrip AND mode <> OOS AND NOT local |
| `Sim_En` | BOOL | HMI | feedback := Out_Run; OL, IOFault ignored; EStopOK, AvailOK still used (Q13) |
| `Sts_Running` | BOOL | PLC | fbk AND Out_Run |
| `Sts_Stopped` | BOOL | PLC | NOT fbk AND NOT Out_Run |
| `Sts_Starting` | BOOL | PLC | Out_Run AND NOT fbk |
| `Sts_Stopping` | BOOL | PLC | NOT Out_Run AND fbk |
| `Sts_Avail` | BOOL | PLC | (Auto or Man) AND NOT local AND Inp_AvailOK AND NOT xTrip (Q10) |
| `Sts_Ready` | BOOL | PLC | stopped AND start allowed |
| `Sts_Intlk` | BOOL | PLC | NOT xIntlkOK |
| `Sts_NotPerm` | BOOL | PLC | NOT xPermOK |
| `Sts_Local` | BOOL | PLC | NOT Inp_Remote |
| `Sts_Tripped` | BOOL | PLC | xTrip |
| `Sts_Fault` | BOOL | PLC | xTrip OR IOFault OR FailStop/Uncmd alarm active |
| `Sts_Sim` | BOOL | PLC | = Sim_En |
| `Sts_State` | INT | PLC | 5 if OOS, local or NOT AvailOK; 4 tripped; 1 starting; 2 running; 3 stopping; 0 stopped |
| `Sts_RestartLeft` | TIME | PLC | Cfg_RestartDly - ET while waiting, else 0 |
| `Sts_NE107` | INT | PLC | common rule; M from Run.Sts_MaintDue |
| `Val_Current` | REAL | PLC | = Inp_Current |
| `Val_LoadPct` | REAL | PLC | Current / RatedAmps x 100, guarded |
| `Alm_*` (7 + HiCurrent) | T_Alarm / T_AlmLim | PLC | see (d) |
| `Run` | T_RunTime | PLC | Inp_Running := Sts_Running |

Trips (`xTrip`, reset required): OL, FailStart, EStop. Interlock loss is **not** a latched motor trip: the stop is
immediate; in Man/Maint the run request is cleared (operator must start again); in Auto it is cleared unless
`Cfg_AutoRestart`. Latching of the interlock itself is `Intlk.Cfg_Latch` (FB_Intlk). (Q15)

(c) Mode table

| Mode | Run request from | Jog | Interlock / E-stop | Output |
|---|---|---|---|---|
| Auto | Prog_Start/Stop | no | stop | per request |
| Manual | Cmd_Start/Stop | no | stop | per request; Auto->Man keeps running (bumpless) |
| Maint | Cmd_Start/Stop | Cmd_Jog | stop | per request / jog; Maint->Man only when stopped |
| OOS | none (cleared) | no | - | FALSE; alarms H; counters stop |
| local (any mode) | none | no | - | FALSE; state 5 (Q12) |
| first scan | cleared | - | - | FALSE |

(d) Alarms

| Alarm | Condition | Time from |
|---|---|---|
| Alm_FailStart | Out_Run AND NOT fbk after `Cfg_FbkTime` (not NoFbk) -> trip | `Cfg_FbkTime` TON |
| Alm_FailStop | NOT Out_Run AND fbk after `Cfg_FbkTime` | `Cfg_FbkTime` TON |
| Alm_Uncmd | fbk while Out_Run FALSE and the motor had been confirmed stopped | `Alm_Uncmd.Cfg_OnDly` |
| Alm_EStop | NOT Inp_EStopOK | `Alm_EStop.Cfg_OnDly` |
| Alm_IntlkTrip | interlock lost while Out_Run was TRUE; holds until IntlkOK | `Alm_IntlkTrip.Cfg_OnDly` |
| Alm_ExcessStarts | Cfg_MaxStartsHr > 0 AND starts last hour >= limit AND stopped | `.Cfg_OnDly` |
| Alm_OL | Inp_OL (not sim) | `.Cfg_OnDly` |
| Alm_HiCurrent | FB_AlmLim high on Val_Current; suppressed while not running | `Alm_HiCurrent.Cfg_Lim/DB/OnDly` |

## FB_VFD (differences from FB_Motor)

(a) Extra pins: IN `DrvReady, DrvFault, DrvWarn : BOOL`, `FaultCode : UINT`, `CommOK : BOOL`, `NE107 : INT`,
`SpdFbk, Torque, Power : REAL` (and `Current`; no `OL` pin, the type has none).
OUT: `Run : BOOL`, `Rev : BOOL`, `SpdRef : REAL`, `FltReset : BOOL`.

(b) Extra / different members

| Member | Type | Written by | Logic |
|---|---|---|---|
| `Inp_DrvReady` | BOOL | Pin | start permissive (not a trip) |
| `Inp_DrvFault` | BOOL | Pin | trip, Alm_DrvFault |
| `Inp_DrvWarn` | BOOL | Pin | Alm_DrvWarn, NE107 S (Q-list) |
| `Inp_FaultCode` | UINT | Pin | HMI-only / passthrough |
| `Inp_CommOK` | BOOL | Pin | FALSE: Sts_CommFail, Alm_CommFail, run request cleared, trip (Q18) |
| `Inp_NE107` | INT | Pin | device status into NE107 |
| `Inp_SpdFbk` | REAL | Pin | Val_Spd; sim: Val_Spd := Out_SpdRef |
| `Inp_Torque`, `Inp_Power` | REAL | Pin | -> Val_Torque, Val_Power |
| `Cfg_SpdEU` | STRING[8] | HMI | passthrough |
| `Cfg_SpdMin`, `Cfg_SpdMax` | REAL | HMI | clamp of Cmd_Spd / Prog_Spd; Min > Max -> config fault, no start |
| `Cfg_SpdDevLim`, `Cfg_SpdDevTime` | REAL/TIME | HMI | Sts_AtSpd, Alm_SpdDev |
| `Cfg_Reversible` | BOOL | HMI | FALSE -> Out_Rev always FALSE |
| `Cmd_Spd` | REAL | both | Man/Maint/jog speed; **maintained setpoint**; clamped and written back; tracks Val_SpdRef outside Man/Maint |
| `Cmd_Rev` | BOOL | HMI | **maintained level** (direction select); applied only while stopped (Q14) |
| `Prog_Spd`, `Prog_Rev` | REAL/BOOL | Owner | Auto speed / direction (direction applied only while stopped) |
| `Out_Rev` | BOOL | PLC | latched direction AND Cfg_Reversible |
| `Out_SpdRef` | REAL | PLC | Val_SpdRef while Out_Run, else 0.0 (Q-list) |
| `Out_FltReset` | BOOL | PLC | 1 s pulse (TON) on Cmd_Reset while Inp_DrvFault |
| `Sts_AtSpd` | BOOL | PLC | running AND ABS(Val_Spd - Val_SpdRef) <= Cfg_SpdDevLim |
| `Sts_Rev` | BOOL | PLC | running AND Out_Rev |
| `Sts_CommFail` | BOOL | PLC | NOT Inp_CommOK (sim: FALSE) |
| `Val_SpdRef` | REAL | PLC | active clamped reference |
| `Val_Spd` | REAL | PLC | Inp_SpdFbk (sim: Out_SpdRef) |
| `Val_Torque`, `Val_Power` | REAL | PLC | from Inp_ |
| `Val_Energy` | LREAL | PLC | += Val_Power x dt / 3600 (kWh), only while Power > 0 |
| `Sts_Tripped` | BOOL | PLC | as Motor plus DrvFault, CommFail |
| `Sts_NE107` | INT | PLC | F: trip/IOFault/CommFail; C: sim/MT/OOS; S: DrvWarn or device S; M: MaintDue or device M |

Start allowed additionally needs `Inp_DrvReady`, `Inp_CommOK`, valid speed config.

(c) Mode table: as FB_Motor; jog runs at `Cmd_Spd`.

(d) Alarms: FB_Motor list minus Alm_OL and Alm_HiCurrent (not in T_VFD), plus:

| Alarm | Condition | Time from |
|---|---|---|
| Alm_DrvFault | Inp_DrvFault (not sim) -> trip | `.Cfg_OnDly` |
| Alm_DrvWarn | Inp_DrvWarn (not sim) | `.Cfg_OnDly` |
| Alm_CommFail | NOT Inp_CommOK (not sim) -> trip | `.Cfg_OnDly` |
| Alm_SpdDev | running AND NOT Sts_AtSpd for `Cfg_SpdDevTime` | TON `Cfg_SpdDevTime` + `.Cfg_OnDly` |
