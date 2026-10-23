# Step 1 spec: common architecture and patterns

Applies to every DFB in this set. Per-type files only list what differs.

## DFB set and call tree

| DFB | Data (`UDT_Data`) | Calls | Notes |
|---|---|---|---|
| `FB_AlmCore` | none (pins only) | TON x3, TOF x1 | ISA-18.2 state machine, shared |
| `FB_Alarm` | `T_Alarm` | `FB_AlmCore` | discrete alarm |
| `FB_AlmLim` | `T_AlmLim` | `FB_AlmCore` | limit + deadband alarm |
| `FB_Mode` | `T_Mode` | - | mode + ISA-88 ownership |
| `FB_RunTime` | `T_RunTime` | TON | run hours, starts, starts/hour |
| `FB_Intlk` | `T_Intlk` | `FB_Alarm` x2, TON | core type "interlock" |
| `FB_AI` | `T_AI` | `FB_AlmLim` x5, `FB_Alarm` | core |
| `FB_DI` | `T_DI` | `FB_Alarm` x2, TON, TOF | core |
| `FB_DO` | `T_DO` (proposed) | `FB_Mode`, `FB_Alarm` x2, `FB_RunTime` | core, needs the new type first |
| `FB_DValve` | `T_DValve` | `FB_Mode`, `FB_Intlk` x2, `FB_Alarm` x5, `FB_RunTime` | core |
| `FB_CValve` | `T_CValve` | `FB_Mode`, `FB_Intlk`, `FB_Alarm` x3 | core |
| `FB_Motor` | `T_Motor` | `FB_Mode`, `FB_Intlk` x2, `FB_Alarm` x7, `FB_AlmLim`, `FB_RunTime` | core |
| `FB_VFD` | `T_VFD` | `FB_Mode`, `FB_Intlk` x2, `FB_Alarm` x10, `FB_RunTime` | core |

The helper DFBs are needed because the core types nest `T_Alarm`, `T_AlmLim`, `T_Mode`, `T_RunTime`
and `T_Intlk`. Writing their logic inline would repeat the alarm state machine up to 17 times per DFB.
**Nested user-DFB instances are not demonstrated in the reference export** (see Q-list).

Import order (each `.XDB` also embeds its DDTs): `FB_AlmCore`, `FB_Alarm`, `FB_AlmLim`, `FB_Mode`,
`FB_RunTime`, `FB_Intlk`, then the device DFBs.

## Pin conventions

- Pin 1: `UDT_Data`, IN_OUT, the `T_` type. This is what Ignition reads/writes over OPC UA.
- Pins 2..n: field inputs (IN), in member order of the type. Name = member name without `Inp_`
  (`Inp_RunFbk` -> pin `RunFbk`). Each scan the DFB copies the pin to the member **first**, so Ignition
  sees the raw field value and the logic only reads the member.
- Then field outputs (OUT). Name = member name without `Out_`. Each scan the DFB writes the member,
  then copies it to the pin **last**.
- Interlock / permissive / E-stop inputs are pins (standard 10.8 "keep protective logic visible").
- BOOL defaults are FALSE. Every `...OK` pin is TRUE = healthy, so an unwired pin fails safe
  (standard 10.8 "fail-safe default values"). No pin needs an initial value.
- `Inp_NE107`, `Inp_Current` and other optional analog inputs are pins too, default 0.
- No EBOOL, no arrays on pins.

## Common patterns

| Pattern | Rule |
|---|---|
| Header comment | `(* <DFB> v1.00 <date> EFC. <purpose> *)` plus author (standard 10.8 asks for author). |
| Commands (`Cmd_*`, one-shot) | Read the TRUE level in this scan; at the **end** of the DFB write every one-shot `Cmd_*` back to FALSE, whether or not it was accepted (rejected commands do not linger and fire later). No R_TRIG needed. |
| Maintained `Cmd_*` | `Cmd_Jog`, `Cmd_Rev`, and the REAL setpoints `Cmd_Spd`, `Cmd_ManPos` are **not** cleared. |
| `Prog_*` | Owner logic writes them; never cleared by the DFB. Request pairs act on the rising edge (stored previous value), `Prog_Lock`/`Prog_Pos`/`Prog_Spd`/`Prog_Rev` are levels (Q16). |
| Elapsed time | One free-running `TON` (PT = T#1H, restarts itself) per DFB that needs dt (filter, rate limit, bypass timers, energy). `tDelta` = ET change since last scan. No scan counting. (Pattern from the old FB_AI.) |
| Delays | `TON`/`TOF` instances only, PT from the `Cfg_*TIME` member. |
| First scan | Private `xInitDone : BOOL` (default FALSE, no initial value needed). While FALSE: outputs off, run requests cleared, mode := `Cfg_PowerUpMode`, ownership cleared, internal latches cleared; then set TRUE. Detects **cold start** only (privates survive a warm start; `%S1` is a system bit and not allowed). |
| Alarms | Device logic writes `Alm_x.Inp_Cond`, then calls `fbAlm_x(OOSIn := <device OOS>, ResetIn := <device Cmd_Reset>, SuppressIn := ..., Alm := UDT_Data.Alm_x)`. |
| Alarm limits / delays | Always from the nested `T_Alarm` / `T_AlmLim` members (`Cfg_OnDly`, `Cfg_OffDly`, `Cfg_Lim`, `Cfg_DB`). The DFB adds its own timer only where the type has a dedicated `Cfg_*Time` (travel, feedback, deviation). |
| Priority | `Cfg_Priority`, `Cfg_Class` are passthrough for Ignition. The PLC never uses them. |
| Clamping | Operator REAL setpoints are clamped to their `Cfg_` limits (standard 10.3.2). Clamped value written back to the `Cmd_` member so Ignition shows what the PLC accepted. |
| Divide | Every division is guarded (`IF den <> 0.0 THEN ... ELSE 0.0`). |
| NE107 (`Sts_NE107`) | 1 F = I/O fault, bad signal or trip fault; 2 C = simulation, Maintenance or OOS; 3 S = device reports S; 4 M = maintenance due or device reports M; 0 otherwise. Priority F > C > S > M. |

## Alarm helpers (changes to the old FB_AlmCore)

Old `FB_AlmCore` / `FB_Alarm` / `FB_AlmLim` logic is kept (reviewed, matches ISA-18.2 and `T_Alarm` docs). Changes:

1. New input `OOSIn` (owner device is Out of Service): alarm shows state 7 (H) and is inhibited,
   without touching `Sts_OOS` set by `Cmd_RemoveSvc`. Standard 10.3.1: "M or MT -> L: the device's alarms go out of service (state H)".
2. New input `ResetIn` (owner's `Cmd_Reset`): ORed with `Cmd_Reset` so one device reset clears that
   device's latched alarms whose condition is gone.
3. **Acknowledge** clears `Sts_Unack` only. **Reset** clears a latch only after the condition is gone.
   This is the `T_Alarm` model (replaces the prompt's "ack clears latch" convention, per answer 7).
4. `R_TRIG`/`F_TRIG` replaced by a stored previous-state BOOL (one pattern everywhere; R_TRIG not demonstrated).
5. `RRTC_DT` (read PLC clock) kept for `Val_LastActive`/`Val_LastRTN`. **Flag:** confirm it is in the 16.2 library on M580.
6. Cold start: all latches, shelve, unack cleared (alarms cleared, per prompt).

## Common mode table (devices with `T_Mode`: DO, DValve, CValve, Motor, VFD)

Source: standard 10.3.1. `FB_Mode` decides the mode; the device DFB applies it.

| Mode (`Sts_Mode`) | Accepts | Outputs | Interlocks | Permissives | Alarms | Counters |
|---|---|---|---|---|---|---|
| Auto (3) | `Prog_*` only; operator `Cmd_` start/stop/open/close/position ignored and cleared | follow owner request | active, trip | block start/open | active | count |
| Manual (2) | `Cmd_*` only; `Prog_*` ignored | follow operator | active, trip | block start/open | active | count |
| Maintenance (1) | `Cmd_*` incl. `Cmd_Jog`; `Prog_*` ignored; cannot be acquired | follow operator | active, trip | active (no MT bypass: type has no per-condition "bypassable in MT" flag; default "nothing bypassed") | active (no design suppression by default) | count |
| Out of service (0) | nothing; all `Cmd_`/`Prog_` cleared | de-energized (safe) state | n/a (outputs already off) | n/a | all device alarms state H | stop |
| any + `Sim_En` | sim is not a mode: field inputs replaced by simulated feedback | see Q-list Q13 | unchanged | unchanged | unchanged | count |

Mode transitions (FB_Mode):

| From -> To | Request | Accepted when |
|---|---|---|
| Man -> Auto | `Cmd_Auto` or `Prog_Auto` | always (no-bump is the owner's job) |
| Auto -> Man | `Cmd_Man` or `Prog_Man` | `Cmd_Man`: not while `Prog_Lock`. `Prog_Man`: always |
| Man -> Maint | `Cmd_Maint` | `NOT Sts_Owned AND NOT Cfg_NoMaint` |
| Maint -> Man | `Cmd_Man` | device pin `KnownState` TRUE (device defines it) |
| Man or Maint -> OOS | `Cmd_OOS` | always |
| OOS -> Man | `Cmd_Man` | always |
| Auto -> Maint / OOS, Maint/OOS -> Auto | - | never (must pass through Manual) |
| cold start | - | `Cfg_PowerUpMode` (0..3; out of range -> Manual) |

Roles (Operator vs Maintenance vs Supervisor) are enforced by Ignition security, not the PLC.
