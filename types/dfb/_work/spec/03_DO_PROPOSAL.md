# Step 1 spec: proposed T_DO and FB_DO

No `T_DO` exists. Proposal for review (answer 4). Nothing here changes `gen_pclib.py`, the Ignition
UDTs or Appendix I until you approve it; adding it means a `gen_pclib.py` entry, regenerated `.xdd`,
an Ignition UDT and an Appendix I row (doc-steward queue).

Scope: a plain discrete output with optional feedback (beacon, horn, heater contactor without
current, purge solenoid, permissive-to-package signal). Motors and valves keep their own types.
MTP nearest: BinManInt / BinVlv-lite. Built from the same conventions as T_DValve / T_Motor.

## Proposed members (29)

| Member | Type | Init | Description |
|---|---|---|---|
| `Cfg_Tag` | STRING[20] | | Equipment / instrument tag |
| `Cfg_Desc` | STRING[40] | | Description shown on HMI faceplate |
| `Mode` | T_Mode | | Mode block |
| `Inp_Fbk` | BOOL | | Feedback (aux contact, pressure switch), optional |
| `Inp_IntlkOK` | BOOL | | Interlocks healthy (FALSE forces output off) |
| `Inp_PermOK` | BOOL | | Permissives healthy (TRUE = may switch on) |
| `Inp_IOFault` | BOOL | | I/O channel or comms fault |
| `Cfg_HasFbk` | BOOL | | Feedback fitted |
| `Cfg_FbkTime` | TIME | T#5S | Time allowed for feedback to follow the output |
| `Cfg_PulseTime` | TIME | T#0S | 0 = maintained output; > 0 = output pulses for this time on each On |
| `Cmd_On` | BOOL | | Operator on (one-shot) |
| `Cmd_Off` | BOOL | | Operator off (one-shot) |
| `Cmd_Reset` | BOOL | | Fault reset (one-shot) |
| `Prog_On` | BOOL | | Program on request (Auto) |
| `Prog_Off` | BOOL | | Program off request (Auto) |
| `Out_On` | BOOL | | Output to field |
| `Sim_En` | BOOL | | Simulation: feedback follows output |
| `Sts_On` | BOOL | | On (feedback confirmed, or output if no feedback) |
| `Sts_Off` | BOOL | | Off (confirmed) |
| `Sts_Avail` | BOOL | | Available to Auto/program control |
| `Sts_Intlk` | BOOL | | Interlock not healthy |
| `Sts_NotPerm` | BOOL | | Permissive not healthy |
| `Sts_Fault` | BOOL | | Any fault present |
| `Sts_Sim` | BOOL | | Simulation active |
| `Sts_State` | INT | | 0=Off 1=On 2=Fault 3=Not available |
| `Sts_NE107` | INT | | NAMUR NE107 status |
| `Alm_FbkFail` | T_Alarm | | Feedback does not follow output within Cfg_FbkTime |
| `Alm_IntlkTrip` | T_Alarm | | Switched off by interlock |
| `Run` | T_RunTime | | On-time and operation counter |

Deliberately left out (keep it small; say if you want them): `Perm`/`Intlk` T_Intlk groups,
`Inp_Remote`, `Cmd_Jog`.

## FB_DO

(a) Pins: `UDT_Data : T_DO` (IN_OUT); `Fbk`, `IntlkOK`, `PermOK`, `IOFault : BOOL` (IN); `On : BOOL` (OUT = `Out_On`).

(b) Member logic: same patterns as FB_DValve with one output. On-request latch from `Cmd_On/Off`
(Man, Maint) or `Prog_On/Off` (Auto); `PermOK` blocks Off->On; `IntlkOK` FALSE forces off and clears
the request; `Cfg_PulseTime` > 0 -> TON one-shot pulse; `Alm_FbkFail` when `Cfg_HasFbk` and fbk <> out
for `Cfg_FbkTime`; `Sts_Fault` = IOFault OR Alm_FbkFail active; `Cmd_Reset` -> alarms' ResetIn.
Sim: fbk := Out; field `On` pin forced FALSE (Q13).

(c) Modes: common mode table. OOS: Out_On FALSE. KnownState (Maint->Man) := `Sts_Off`.
(d) Alarms: Alm_FbkFail (time `Cfg_FbkTime`), Alm_IntlkTrip (cond: interlock forced the output off while it was on; clears when IntlkOK).
