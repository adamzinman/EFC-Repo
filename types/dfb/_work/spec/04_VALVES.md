# Step 1 spec: FB_DValve (T_DValve) and FB_CValve (T_CValve)

Mode behaviour follows the common mode table (00_COMMON). Only the device-specific parts are below.

## FB_DValve

(a) Pins

| Pin | Dir | Type | Purpose |
|---|---|---|---|
| `UDT_Data` | IN_OUT | T_DValve | HMI interface |
| `ZSO` | IN | BOOL | open limit switch -> `Inp_ZSO` |
| `ZSC` | IN | BOOL | closed limit switch -> `Inp_ZSC` |
| `Remote` | IN | BOOL | L/R switch in Remote -> `Inp_Remote` (tie TRUE if none fitted, Q12) |
| `IntlkOK` | IN | BOOL | external interlock -> `Inp_IntlkOK` |
| `PermOK` | IN | BOOL | external permissive -> `Inp_PermOK` |
| `IOFault` | IN | BOOL | channel / comms fault -> `Inp_IOFault` |
| `BypassPerm` | IN | BOOL | bypass permit for `Perm` and `Intlk` groups |
| `Open` | OUT | BOOL | = `Out_Open` |
| `Close` | OUT | BOOL | = `Out_Close` |

Effective healthy signals: `xIntlkOK := Inp_IntlkOK AND Intlk.Out_OK`, `xPermOK := Inp_PermOK AND Perm.Out_OK` (type docs: "Out_OK ANDed with Inp_...").
Positions: "interlock position" = open if `Cfg_IntlkOpen` else closed. "Fail position" = open if `Cfg_FailOpen` else closed.

(b) Members

| Member | Type | Written by | Logic |
|---|---|---|---|
| `Cfg_Tag`, `Cfg_Desc` | STRING | HMI | passthrough |
| `Mode` | T_Mode | PLC/HMI | FB_Mode; KnownState := confirmed at fail position (Q9) |
| `Perm` | T_Intlk | PLC/HMI/Owner | FB_Intlk; Owner writes `Perm.Inp_Cond[]` |
| `Intlk` | T_Intlk | PLC/HMI/Owner | FB_Intlk; Owner writes `Intlk.Inp_Cond[]` |
| `Inp_ZSO`, `Inp_ZSC` | BOOL | Pin | feedback (ignored in sim / if not fitted) |
| `Inp_Remote` | BOOL | Pin | FALSE -> local |
| `Inp_IntlkOK` | BOOL | Pin | see effective |
| `Inp_PermOK` | BOOL | Pin | see effective |
| `Inp_IOFault` | BOOL | Pin | -> Sts_Fault, NE107 F |
| `Cfg_HasZSO`, `Cfg_HasZSC` | BOOL | HMI | not fitted: that end confirmed by travel timer expiry with no conflict |
| `Cfg_FailOpen` | BOOL | HMI | fail position; OOS output pattern (Q8) |
| `Cfg_IntlkOpen` | BOOL | HMI | interlock position |
| `Cfg_DualCoil` | BOOL | HMI | output pattern |
| `Cfg_TravelTime` | TIME | HMI | travel TON PT |
| `Cmd_Open`, `Cmd_Close` | BOOL | HMI | demand in Man/Maint; cleared |
| `Cmd_Reset` | BOOL | HMI | -> alarms' ResetIn, groups' ResetIn; cleared |
| `Prog_Open`, `Prog_Close` | BOOL | Owner | demand in Auto (Q16) |
| `Out_Open` | BOOL | PLC | single coil: see Q8; dual: demand open |
| `Out_Close` | BOOL | PLC | dual: demand closed; single: FALSE |
| `Sim_En` | BOOL | HMI | feedback := demand after `T#2S` (Q13) |
| `Sts_Opened`, `Sts_Closed` | BOOL | PLC | confirmed end position |
| `Sts_Opening`, `Sts_Closing` | BOOL | PLC | demand <> confirmed position, travel timer running |
| `Sts_Avail` | BOOL | PLC | (Auto or Man) AND NOT local AND NOT Sts_Fault (Q10) |
| `Sts_Intlk` | BOOL | PLC | NOT xIntlkOK |
| `Sts_NotPerm` | BOOL | PLC | NOT xPermOK |
| `Sts_Local` | BOOL | PLC | NOT Inp_Remote |
| `Sts_Fault` | BOOL | PLC | IOFault OR any of FailOpen/FailClose/PosConflict/Uncmd alarm active |
| `Sts_Sim` | BOOL | PLC | = Sim_En |
| `Sts_State` | INT | PLC | 5 fault, 3 opening, 4 closing, 2 open, 1 closed, else 0 |
| `Sts_NE107` | INT | PLC | common rule; M from Run.Sts_MaintDue |
| `Alm_FailOpen` ... `Alm_IntlkTrip` | T_Alarm | PLC | see (d) |
| `Run` | T_RunTime | PLC | Inp_Running := Sts_Opened (Val_Starts = open operations) |

Demand: one private BOOL `xOpenReq`. Set/cleared by `Cmd_Open/Close` (Man, Maint) or `Prog_Open/Close` (Auto).
`xPermOK` FALSE blocks a move **away from the interlock position**, not a move to it (Q7).
`xIntlkOK` FALSE forces demand to the interlock position in every mode except OOS; in Manual/Maint the request is overwritten (no return when the interlock clears); in Auto the owner re-issues.
Local: outputs FALSE (hand control is outside the PLC), demand tracks feedback, no travel alarms (Q12).

(c) Mode table (device-specific columns)

| Mode | Demand source | Outputs | Notes |
|---|---|---|---|
| Auto | Prog_Open/Close | demand | operator Cmd_Open/Close cleared unused |
| Manual | Cmd_Open/Close | demand | on Auto->Man demand held (bumpless) |
| Maint | Cmd_Open/Close | demand | Maint->Man only when KnownState |
| OOS | none | Out_Open, Out_Close FALSE (de-energized) | dual-coil valve stays where it is (Q8); alarms H |
| any, interlock not OK | interlock position | forced | Alm_IntlkTrip |
| local | none | FALSE | Sts_Local, not available |

(d) Alarms

| Alarm | Condition | Time / delay from |
|---|---|---|
| Alm_FailOpen | demand open AND NOT Sts_Opened after travel time | `Cfg_TravelTime` (TON) + `Alm_FailOpen.Cfg_OnDly` |
| Alm_FailClose | demand closed AND NOT Sts_Closed after travel time | `Cfg_TravelTime` |
| Alm_PosConflict | Cfg_HasZSO AND Cfg_HasZSC AND ZSO AND ZSC | `Alm_PosConflict.Cfg_OnDly` |
| Alm_Uncmd | had reached demanded position, then lost it with no demand change | `Alm_Uncmd.Cfg_OnDly` |
| Alm_IntlkTrip | interlock moved (or holds) the valve away from the requested position | `Alm_IntlkTrip.Cfg_OnDly` |

All suppressed in sim? No: in sim feedback is generated, so they never fire; not suppressed. Local: travel/uncmd alarms suppressed (SuppressIn).

## FB_CValve

(a) Pins

| Pin | Dir | Type | Purpose |
|---|---|---|---|
| `UDT_Data` | IN_OUT | T_CValve | HMI interface |
| `PosFbk` | IN | REAL | position feedback % -> `Inp_PosFbk` |
| `FbkBad` | IN | BOOL | feedback signal bad -> `Inp_FbkBad` |
| `ZSC` | IN | BOOL | closed switch -> `Inp_ZSC` |
| `IntlkOK` | IN | BOOL | -> `Inp_IntlkOK` |
| `IOFault` | IN | BOOL | -> `Inp_IOFault` |
| `NE107` | IN | INT | -> `Inp_NE107` |
| `BypassPerm` | IN | BOOL | bypass permit for `Intlk` group |
| `CVRaw` | OUT | INT | = `Out_CVRaw` (AO counts) |
| `CV` | OUT | REAL | = `Out_CV` (% for fieldbus positioners) |

(b) Members

| Member | Type | Written by | Logic |
|---|---|---|---|
| `Cfg_Tag`, `Cfg_Desc` | STRING | HMI | passthrough |
| `Mode` | T_Mode | PLC/HMI | FB_Mode; KnownState := ABS(Val_Dev) <= Cfg_DevLim (Q9) |
| `Intlk` | T_Intlk | PLC/HMI/Owner | FB_Intlk |
| `Inp_PosFbk` | REAL | Pin | used if Cfg_HasFbk AND NOT FbkBad AND NOT sim |
| `Inp_FbkBad` | BOOL | Pin | Alm_FbkBad |
| `Inp_ZSC` | BOOL | Pin | -> Sts_Closed |
| `Inp_IntlkOK` | BOOL | Pin | ANDed with Intlk.Out_OK |
| `Inp_IOFault` | BOOL | Pin | Sts_Fault, NE107 F |
| `Cfg_HasFbk` | BOOL | HMI | feedback fitted |
| `Cfg_FailPos` | REAL | HMI | OOS output (Q8) |
| `Cfg_IntlkPos` | REAL | HMI | demand on interlock, no rate limit |
| `Cfg_OutMin`, `Cfg_OutMax` | REAL | HMI | clamp (not applied to tight shut-off 0, interlock, OOS) ; Min > Max -> config fault, output to FailPos |
| `Cfg_RateUp`, `Cfg_RateDn` | REAL | HMI | %/s with dt, 0 = none |
| `Cfg_TightShut` | REAL | HMI | demand below -> 0 % |
| `Cfg_ReverseAct` | BOOL | HMI | raw uses 100 - CV |
| `Cfg_RawMin`, `Cfg_RawMax` | INT | HMI | AO scaling; equal -> config fault |
| `Cfg_DevLim`, `Cfg_DevTime` | REAL/TIME | HMI | Alm_PosDev |
| `Cmd_ManPos` | REAL | both | Man/Maint demand; **maintained setpoint**; clamped and written back; tracks Val_Demand outside Man/Maint (bumpless Auto->Man) |
| `Cmd_Reset` | BOOL | HMI | resets alarms/group; cleared |
| `Prog_Pos` | REAL | Owner | Auto demand, clamped |
| `Out_CV` | REAL | PLC | demand after limits and rate limit |
| `Out_CVRaw` | INT | PLC | RawMin + CV% x span, limited to INT range |
| `Sim_En` | BOOL | HMI | Val_Pos := Out_CV |
| `Val_Demand` | REAL | PLC | active demand before rate limit |
| `Val_Pos` | REAL | PLC | feedback, or Out_CV if no/bad feedback or sim |
| `Val_Dev` | REAL | PLC | Out_CV - Val_Pos (rate-limited demand, so rate limiting does not raise deviation) |
| `Val_Travel` | REAL | PLC | sum of ABS(change of Out_CV) (Q20) |
| `Val_Reversals` | UDINT | PLC | direction changes of Out_CV (Q20) |
| `Sts_Closed` | BOOL | PLC | Inp_ZSC OR (Val_Pos <= 0.5 %) (Q21) |
| `Sts_Intlk` | BOOL | PLC | NOT effective IntlkOK |
| `Sts_RateLim` | BOOL | PLC | Out_CV <> Val_Demand because of rate limit |
| `Sts_Fault` | BOOL | PLC | IOFault OR config fault OR Alm_PosDev/Alm_FbkBad active |
| `Sts_Sim` | BOOL | PLC | = Sim_En |
| `Inp_NE107` | INT | Pin | device status |
| `Sts_NE107` | INT | PLC | common rule |
| `Alm_PosDev`, `Alm_FbkBad`, `Alm_IntlkTrip` | T_Alarm | PLC | see (d) |

(c) Mode table

| Mode | Demand | Output |
|---|---|---|
| Auto | Prog_Pos | rate-limited, clamped |
| Manual | Cmd_ManPos | rate-limited, clamped; entering Man: Cmd_ManPos := current Val_Demand (hold) |
| Maint | Cmd_ManPos | same |
| OOS | none | Out_CV := Cfg_FailPos, no rate limit (Q8); alarms H |
| interlock not OK (any mode but OOS) | Cfg_IntlkPos | immediate |
| First scan | - | Out_CV := Cfg_FailPos until mode applied |

(d) Alarms

| Alarm | Condition | Limit / delay |
|---|---|---|
| Alm_PosDev | Cfg_HasFbk AND NOT FbkBad AND ABS(Val_Dev) > Cfg_DevLim | TON `Cfg_DevTime` + `Alm_PosDev.Cfg_OnDly` |
| Alm_FbkBad | Cfg_HasFbk AND Inp_FbkBad (not sim) | `Alm_FbkBad.Cfg_OnDly` |
| Alm_IntlkTrip | interlock not OK AND demand before interlock <> Cfg_IntlkPos | `Alm_IntlkTrip.Cfg_OnDly` |
