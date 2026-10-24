# Legacy DDT_ fork (`claude/legacy-ddt-fork`)

This branch builds the **same library, with every template and dynamic window bound to the old UDT set** instead of the
EFCLib v1 `T_` types: `DDT_Valve`, `DDT_Device`, `DDT_Process_Value`, `DDT_Station`, `MEM_Interlock_List` (the
`InterlockList` member of `DDT_Valve`), plus the library's own pre-v1 UDTs `PID_ControlValve` and `PID_Loop` where the
plant never had a `DDT_`. View paths are unchanged (`Templates/...`, `Templates/Dynamic Window/...`), so an HMI project
can switch between this branch's `EFC_Library_PROJECT.zip` and the main one without re-wiring its screens.

## How the switch works
- `generator/legacy_types.py` holds the switch and the member maps. It is on when `EFC_LEGACY_DDT=1` is set (or
  `python3 build.py --legacy-ddt`), or when `VERSION.json` has `"types": "legacy-ddt"`. **This branch commits that key**,
  so plain `python3 build.py` (and CI) produce the legacy-bound `projects/EFC_Library`; `EFC_LEGACY_DDT=0 python3 build.py`
  on the same branch reproduces the main-branch build byte for byte (only `efc.ui` gains the additive legacy tables).
- The same generators emit both builds: `build_pid.py` (`onoff_legacy`, `control_legacy`, `motor_legacy`),
  `build_pv.py` (the pre-e710de8 `DDT_Process_Value` bindings and alarm script), `pid_loops/generate_loops.py`
  (`PID_Loop` members), `analog_indicators/gen_analog_indicators.py` (`DDT_Process_Value` members),
  `docks/legacy_windows.py` (the dynamic windows), `docks/efc_ui.py` (`LEGACY = True`, legacy `BY_TYPE`, `LEGACY_DBL`,
  `pulse()`).
- The Designer-built Station faceplates (`imported/EFC_StationFaceplates`) are not edited: `build.py` runs
  `tools/legacy_station.py` on them while merging, the exact inverse of `steward/tools/fix_station.py`. The member sets
  of the rebuilt `Station_Tile`, `Station_Fill` and `Templates/Dynamic Window/Station/Station` are identical to the
  pre-e710de8 originals (checked with a diff of every `{0}/Member` and `"/Member"` reference).
- `tags/legacy/*.json` are the legacy UDT definitions (see `tags/legacy/README.md`); `tools/check_bindings.py` walks every
  `view.json` in `projects/EFC_Library`, resolves each `{0}/Member` binding, script tag path, `efc.ui.cmd` / `pulse`
  member and trend pen to the view's type and asserts the member exists. Result on this branch:
  **38 typed views, 656 member references, 0 unknown, no T_-only member name left.** `python3 tools/check_bindings.py --t`
  runs the same check on a T_ build against `types/export/PCLib_Ignition81.json`.

## Gateway setup
1. Tag Browser → Data Types: import `tags/legacy/MEM_Interlock_List_UDT.json`, then `DDT_Valve`, `DDT_Device`,
   `DDT_Process_Value`, `DDT_Station` (`PID_ControlValve`, `PID_Loop` if you use the analog valve / loop templates). Point
   their `OPC Server` / `OPC Prefix` / `Tag` parameters at your M580 (the files keep the RGTCR gateway's defaults).
2. Import `EFC_Library_PROJECT.zip` from this branch. Templates take `tagPath` = the instance path, as before.
3. Optional demo tags: `tags/PID_Demo_Instances.json` (DDT_Valve_Demo / DDT_Device_Demo / PID_ControlValve),
   `tags/PV_Demo_Tags.json`, `tags/PID_Loops/*.json`, `tags/DDT_Station_Demo_UDT.json` + `tags/Station_Demo_Instances.json`.
4. The `dw_Right` dock and `efc.ui` work as on main. Legacy `tType` values the templates send: `DDT_Valve`,
   `PID_ControlValve`, `DDT_Device` (VFD and Heater templates add `dockId` `dw_VFD` / `dw_Heater`), `DDT_Process_Value`,
   `PID_Loop`, `DDT_Station`.

## Command semantics on the legacy types
- `HMI_CMD` is a **level** (DFB: `CMD := HMI_CMD AND Manual AND Man_Perm`; the DFB resets it on a mode change or an
  interlock in Manual). OPEN / START write `HMI_CMD = TRUE`, CLOSE / STOP write `FALSE`; the template button and the
  double-tap write the opposite of the current `CMD`. All go through `efc.ui.cmd` (Operator re-check).
- `HMI_Auto`, `HMI_Manual`, `HMI_Off`, `HMI_Lockout` are **rising-edge** contacts in the DFB: `efc.ui.pulse` writes TRUE,
  then FALSE after 1 s (the scheme the Station faceplates already used for `HMI_Select`, `TareCMD`, `ZeroCMD`,
  `HMI_Reset`). `Reset_Count` (DDT_Valve) is pulsed the same way; `Reset_Runtime` (DDT_Device) is written TRUE once
  because the DFB clears it itself.
- Role levels are unchanged: Operator commands and setpoints, Maintenance OFF / LOCKOUT / counters, Supervisor alarm
  inhibit (DDT_Process_Value `x/Inhibit`), Engineer configuration entries.

## What each window loses (no legacy data)
| Window | Kept | Dropped or replaced |
|---|---|---|
| ValveDiscrete (DDT_Valve) | state banner, LOCKED OUT / INTLK / NOT PERM chips, Mode (AUTO / MAN / OFF / LOCKOUT), OPEN / CLOSE, ZSO / ZSC / REQ / cycle count, interlock list (names + descriptions from `InterlockList`), trend CMD / ZSO, RESET CYCLE COUNT, Feedback-fitted config | Permissive list (only the `Permissive` bit exists), T_Alarm list + ACK, NE107, run-hours / starts / maintenance-due, simulate, travel-time config, RESET |
| ValveAnalog (PID_ControlValve) | UNKNOWN / FAULT / INTERLOCKED / CLOSED / OPEN x % banner, NOT PERM chip, AUTO / MAN (`Mode` 0 / 1), manual position entry + presets (write `Out`), Demand / Position / Deviation, trend Out / Pos, feedback-fitted config | interlock list, alarms, SIM / RATE LIM chips, travel / reversals, rate / deviation / tight-shutoff config, RESET |
| Rotating / VFD / Heater (DDT_Device) | FAULT / STALLED / STARTING / STOPPING / RUNNING / STOPPED banner (ON / OFF words on Heater), WARNING / LOCKED OUT / INTLK / NOT PERM chips, Mode, START / STOP (ON / OFF), YI / REQ / run time / compression ratio / stall time, trend CMD / YI, run-time counter + RESET RUN TIME, FB_Enb / stall config | permissive and interlock lists, alarms, JOG, RESET, current / load / rated amps, drive speed / torque / power / direction (VFD), power demand / duty / high limit (Heater), starts counters, simulate, feedback-time / restart / auto-restart config |
| HeatTransfer | header (tag name) + a note | everything: no legacy type carries heat-exchanger calculations (the HX_AirCooled fan symbol opens the DDT_Device window) |
| ProcessValue (DDT_Process_Value) | HW FAULT banner, PV + Units, OVER / UNDER / INH chips, value / % of range / EU range / raw range, per-limit rows (alarm LED, INHIBITED / DISABLED / ALARM, SP), Supervisor inhibit checkboxes, trend PV, Engineer edit of SP / Enabled / DB / DLY / Eng range / Raw range | ACK button (acknowledge in the alarm status table: the alarms are Ignition tag alarms), rate of change, NE107, simulate, filter / cutoff / square-root config |
| Loop (PID_Loop) | MANUAL / AUTO / CASCADE banner, HIGH / LOW / DEVIATION chips, mode buttons (`Mode` 0 / 1 / 2), PV / SP / Output / Error, SP and OUT entries, alarm limits, trend PV / SP / OUT, tuning (Kp, Ti, Td, Action), limits (AlmHi / AlmLo / AlmDev, SP and OUT range) | INTERLOCKED / TRACKING / windup / ramping, interlock list, PV-bad alarm, deadband / rate config |
| Parts/IntlkList | the used entries of a `MEM_Interlock_List` (name - description), header badge from the parent's `Interlock` bit | per-condition OK / bypassed LEDs, BYPASS / UNBYPASS, reset (`Status[]` exists but its polarity is undocumented, so it is not shown) |
| Parts/BypassConfirm | - | not built (no bypass on the legacy types) |
| Station (imported) | everything, on the DDT_Station members | - |
| IOCard, Parts/Trend | unchanged | - |

Templates: the P&ID symbols keep their full behaviour (state, P / I badges, yellow M, button, double-tap). The I-badge
tooltip lists the used `InterlockList` entries (the pre-switch script). `PV_StatusStrip` / `PV_RangeBar` are the
pre-switch design (alarm letters from `system.alarm.queryStatus` on the instance's tag alarms). The AnalogIndicator cards
read `DDT_Process_Value`; they show alarm chips in Medium styling (no priority on the DDT) and have no ideal band.

## Mapped with less than full certainty (flagged)
- `DDT_Device.YIF`: present on the DDT, not used by the ladder in the reference export, meaning undocumented → **not bound**
  (`Sts_Tripped` has no legacy equivalent). `YI` is the run feedback (the DFB counts runtime while `YI`).
- `DDT_Device` permissive: in DFB_Device v0.28 `Auto_Perm = Man_Perm = NOT Estop AND NOT Interlock`, so the P badge
  lights together with the I badge on the plant logic. Bound as `!(Manual ? Man_Perm : Auto_Perm)`.
- `DDT_Valve.Permissive` is read as "permissive **missing**" (P badge visible when TRUE), exactly as the pre-switch
  template did on the live gateway; `Permissive` is not in the RGTCR XSY export (DDT_Valve v0.03) but is in the gateway
  UDT.
- `MEM_Interlock_List.Status[]` polarity is unknown (derived tag, expression not exported) → not displayed.
- `Reset_Count` (DDT_Valve): pulsed 1 s (works for edge- or level-triggered PLC logic). `Stall_Time` (INT) and
  `DDT_Process_Value.x/DLY` (INT) are shown without a unit (not documented).
- `PID_ControlValve.Mode`: 0 Auto, 1 Manual is the library's own convention (pre-switch motor template); the window's
  AUTO / MAN buttons write 0 / 1.
- AnalogIndicator alarm priority: `DDT_Process_Value` carries none; the cards use Medium for every active limit and
  cannot show unacknowledged state.
- `DDT_Intlk` (named in the task) exists only as a `ddtsync` test configuration name; the gateway's interlock type is
  `MEM_Interlock_List`. `DDT_PV` is likewise only the ddtsync alias of `DDT_Process_Value`.

## Member maps
Generated from `generator/legacy_types.py` (`python3 generator/legacy_types.py --table`). "Legacy member" is a member
path on the legacy type, an expression on legacy members (derived), or `-` when the T_ member has no equivalent.

### DDT_Valve (T_DValve: Valve_Solenoid, Valve_OnOff_Pneumatic, Valve_MOV, dw_ValveDiscrete)

21 rows mapped, 6 rows with no legacy equivalent.

| T_ member | Legacy member | Note | Source |
|---|---|---|---|
| `Cfg_Tag` | `Name` | memory member, defaults to the {Tag} parameter | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Cfg_Desc` | `Description` |  | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Out_Open` | `CMD` | open command to the field | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Sts_Opened` | `ZSO` | open limit | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Sts_Closed` | `ZSC` | closed limit | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Sts_Opening / Sts_Closing` | `CMD && !ZSO / !CMD && !ZSC` | derived; the window banner uses it | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Sts_Fault` | `ZSO && ZSC` | derived (both limits made); no fault bit on DDT_Valve | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Cfg_HasZSO / Cfg_HasZSC / Inp_ZSO / Inp_ZSC` | `Feedback_Enabled / ZSO / ZSC` | one feedback flag covers both limits | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Mode/Sts_Auto` | `Auto` |  | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Mode/Sts_Man` | `Manual` |  | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Mode/Sts_OOS` | `Off` |  | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Mode/Sts_Maint` | - | no maintenance mode; LockedOut is the 4th legacy mode (shown as LOCKOUT) | no legacy member |
| `Sts_Avail` | `!LockedOut` | derived | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Sts_Local` | - | no local/remote on DDT_Valve | no legacy member |
| `Sts_Intlk` | `Interlock` |  | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Sts_NotPerm` | `Permissive` | TRUE = permissive missing (as the pre-switch template read it) | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Intlk/* (T_Intlk)` | `InterlockList (MEM_Interlock_List)` | document {InterlockName[], Used[], Description[], Status[]}; names of the used entries | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Intlk/Sts_FirstOut, Intlk/Cfg_CondDesc/n` | `InterlockList.Used[n], .InterlockName[n], .Description[n]` | tooltip and legacy IntlkList part; Status[] polarity undocumented, not bound | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Perm/* (T_Intlk)` | - | only the Permissive bit exists; list dropped | no legacy member |
| `Cmd_Open / Cmd_Close` | `HMI_CMD = TRUE / FALSE` | level, not one-shot (DFB resets it on mode change) | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Mode/Cmd_Auto / Cmd_Man / Cmd_OOS` | `HMI_Auto / HMI_Manual / HMI_Off (1 s pulse)` | rising-edge contacts in the DFB; efc.ui.pulse | DFB_Device.XDB v0.28 ladder (types/dfb/_reference at 7cb7e30) + DDT_Device v0.09 in the RGTCR XSY export |
| `Mode/Cmd_Maint` | `HMI_Lockout (1 s pulse)` | window button LOCKOUT (Maintenance+) | DFB_Device.XDB v0.28 ladder (types/dfb/_reference at 7cb7e30) + DDT_Device v0.09 in the RGTCR XSY export |
| `Cmd_Reset` | - | no device reset; dropped | no legacy member |
| `Alm_* (T_Alarm members)` | - | legacy alarms are Ignition tag alarms, not members; Alarms section dropped | no legacy member |
| `Run/Val_RunHrs ... Run/Cmd_ResetMaint, Sim_En` | `Cycle_Count, Reset_Count` | Counters section: cycle count + RESET COUNT | tags/legacy UDT definition (live RGTCR export) |
| `Cfg_TravelTime, Sts_NE107` | - | dropped | no legacy member |
| `(not bound)` | `REQ, Auto_Perm, Man_Perm` | automation request and per-mode permissives (equal in the DFB) | tags/legacy UDT definition (live RGTCR export) |

### DDT_Device (T_Motor / T_VFD / T_Heater: Rotating/*, HX_AirCooled, Heater_Electric, dw_Rotating, dw_VFD, dw_Heater)

19 rows mapped, 7 rows with no legacy equivalent.

| T_ member | Legacy member | Note | Source |
|---|---|---|---|
| `Cfg_Tag` | `Name` |  | tags/legacy UDT definition (live RGTCR export) |
| `Cfg_Desc` | `Description` |  | tags/legacy UDT definition (live RGTCR export) |
| `Out_Run / Out_Contactor` | `CMD` |  | DFB_Device.XDB v0.28 ladder (types/dfb/_reference at 7cb7e30) + DDT_Device v0.09 in the RGTCR XSY export |
| `Sts_Running / Sts_On` | `YI` | run feedback (the DFB counts runtime while YI) | DFB_Device.XDB v0.28 ladder (types/dfb/_reference at 7cb7e30) + DDT_Device v0.09 in the RGTCR XSY export |
| `Sts_Stopped / Sts_Off` | `!YI` | derived | DFB_Device.XDB v0.28 ladder (types/dfb/_reference at 7cb7e30) + DDT_Device v0.09 in the RGTCR XSY export |
| `Sts_Starting / Sts_Stopping` | `CMD && !YI / !CMD && YI` | derived | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Cfg_NoFbk` | `!FB_Enb` | feedback enabled flag | tags/legacy UDT definition (live RGTCR export) |
| `Sts_Fault` | `Alarm` | device alarm bit | tags/legacy UDT definition (live RGTCR export) |
| `Sts_Tripped` | - | YIF exists on DDT_Device but its meaning is not documented anywhere in the repo; not bound (GUESS avoided) | no legacy member |
| `Mode/Sts_Auto / Sts_Man / Sts_OOS` | `Auto / Manual / Off` |  | DFB_Device.XDB v0.28 ladder (types/dfb/_reference at 7cb7e30) + DDT_Device v0.09 in the RGTCR XSY export |
| `Mode/Sts_Maint` | - | LockedOut shown as LOCKOUT instead | no legacy member |
| `Sts_Avail` | `!LockedOut` | derived | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Sts_Local` | - |  | no legacy member |
| `Sts_Intlk` | `Interlock` |  | tags/legacy UDT definition (live RGTCR export) |
| `Sts_NotPerm` | `!(Manual ? Man_Perm : Auto_Perm)` | in DFB_Device v0.28 both perms are !Estop && !Interlock, so P lights with I | DFB_Device.XDB v0.28 ladder (types/dfb/_reference at 7cb7e30) + DDT_Device v0.09 in the RGTCR XSY export |
| `Perm/*, Intlk/* (T_Intlk)` | - | no interlock list on DDT_Device; chips only | no legacy member |
| `Cmd_Start / Cmd_Stop / Cmd_On / Cmd_Off` | `HMI_CMD = TRUE / FALSE` | level; CMD := HMI_CMD && Manual && Man_Perm | DFB_Device.XDB v0.28 ladder (types/dfb/_reference at 7cb7e30) + DDT_Device v0.09 in the RGTCR XSY export |
| `Mode/Cmd_Auto / Cmd_Man / Cmd_OOS / Cmd_Maint` | `HMI_Auto / HMI_Manual / HMI_Off / HMI_Lockout (1 s pulse)` |  | DFB_Device.XDB v0.28 ladder (types/dfb/_reference at 7cb7e30) + DDT_Device v0.09 in the RGTCR XSY export |
| `Cmd_Reset, Cmd_Jog` | - | dropped | no legacy member |
| `Val_Current, Val_LoadPct, Cfg_RatedAmps, Val_Spd, Val_SpdRef, Cmd_Spd, Cmd_Rev, Val_Torque, Val_Power` | - | no electrical / drive data on DDT_Device; VFD and heater windows show the DDT_Device data | no legacy member |
| `Run/Val_RunHrs` | `Runtime (Run_Hour + Run_Min/60)` |  | DFB_Device.XDB v0.28 ladder (types/dfb/_reference at 7cb7e30) + DDT_Device v0.09 in the RGTCR XSY export |
| `Run/Cmd_ResetMaint` | `Reset_Runtime (one-shot, DFB clears it)` |  | DFB_Device.XDB v0.28 ladder (types/dfb/_reference at 7cb7e30) + DDT_Device v0.09 in the RGTCR XSY export |
| `Run/Val_Starts, Run/Val_StartsLastHr, Run/Sts_MaintDue, Sim_En` | - | dropped | no legacy member |
| `Alm_* (T_Alarm members)` | `Warning (chip only)` | Alarms section dropped | no legacy member |
| `Cfg_* (configuration)` | `FB_Enb, Enable_Stalling, Comp_Ratio, Stall_Time` | compressor stall detection; Curr_Comp_Ratio and Stalled shown | tags/legacy UDT definition (live RGTCR export) |
| `(not bound)` | `YIF, REQ, Run_Sec, Run_Min` |  | tags/legacy UDT definition (live RGTCR export) |

### PID_ControlValve (T_CValve: Valve_Control, dw_ValveAnalog) - library UDT, no plant DDT_ for analog valves

11 rows mapped, 1 rows with no legacy equivalent.

| T_ member | Legacy member | Note | Source |
|---|---|---|---|
| `Cfg_Tag / Cfg_Desc` | `Name / Description` |  | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Val_Demand` | `Out` |  | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Val_Pos` | `Pos` |  | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Cfg_HasFbk` | `Feedback_Enabled` |  | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Sts_Fault` | `Fault` |  | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Sts_Intlk` | `Intlk` |  | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Sts_NotPerm` | `!PermOK` |  | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Mode/Sts_Man` | `Mode = 1` | library convention (pre-switch motor template: mode 1 = Manual) | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Mode/Sts_Auto` | `Mode = 0` |  | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Cmd_ManPos` | `Out (write, Manual only)` | window entry and presets write Out | generator/pid_loops/generate_loops.py before 8e719f8 (PID_Loop UDT) |
| `Mode/Cmd_Man / Cmd_Auto` | `Mode := 1 / 0` |  | generator/build_pid.py before e710de8 (DDT_Valve bindings verified on a live gateway, design note 39) |
| `Sts_Closed / Sts_RateLim / Sts_Sim / Val_Dev / Val_Travel / Val_Reversals / Alm_* / Cfg_* / Cmd_Reset` | - | dropped (deviation shown as Out - Pos) | no legacy member |

### DDT_Process_Value (T_AI: PV_StatusStrip, PV_RangeBar, dw_ProcessValue; T_KPI: AnalogIndicator/*)

15 rows mapped, 2 rows with no legacy equivalent.

| T_ member | Legacy member | Note | Source |
|---|---|---|---|
| `Val_PV` | `PV` |  | generator/build_pv.py before e710de8 (DDT_Process_Value bindings) |
| `Cfg_Tag / Cfg_Desc / Cfg_EU` | `Name / Description / Units` | memory members | generator/build_pv.py before e710de8 (DDT_Process_Value bindings) |
| `Cfg_EUMin / Cfg_EUMax` | `Eng_Min / Eng_Max` |  | generator/build_pv.py before e710de8 (DDT_Process_Value bindings) |
| `Cfg_RawMin / Cfg_RawMax` | `Raw_Min / Raw_Max` |  | tags/legacy UDT definition (live RGTCR export) |
| `Sts_Bad` | `HW_Fault` |  | generator/build_pv.py before e710de8 (DDT_Process_Value bindings) |
| `Sts_ORng / Sts_URng` | `Overrange / Underrange` |  | generator/build_pv.py before e710de8 (DDT_Process_Value bindings) |
| `Alm_HH|H|L|LL/Cfg_Lim` | `HH|H|L|LL/SP` |  | generator/build_pv.py before e710de8 (DDT_Process_Value bindings) |
| `Alm_x/Sts_Suppressed` | `x/Inhibit` |  | generator/build_pv.py before e710de8 (DDT_Process_Value bindings) |
| `Alm_x/Cfg_En` | `x/Enabled` |  | tags/legacy UDT definition (live RGTCR export) |
| `Alm_x/Sts_Active` | `x/Alarm` |  | generator/build_pv.py before e710de8 (DDT_Process_Value bindings) |
| `Alm_x/Sts_Unack, Alm_x/Cfg_Priority, Alm_Bad` | `Ignition tag alarms on x/Alarm, HW_Fault, Overrange, Underrange` | PV templates query system.alarm.queryStatus (pre-switch script); KPI cards: unack false, priority Medium | generator/build_pv.py before e710de8 (DDT_Process_Value bindings) |
| `Alm_x/Cfg_DB (deadband), on-delay` | `x/DB, x/DLY` | shown and editable (Engineer) in dw_ProcessValue | tags/legacy UDT definition (live RGTCR export) |
| `Val_PVPct` | `(PV - Eng_Min) / (Eng_Max - Eng_Min)` | derived | generator/build_pv.py before e710de8 (DDT_Process_Value bindings) |
| `Cfg_ShortDesc` | `Description` |  | T_KPI card members read as DDT_Process_Value (same members as the PV templates) |
| `Cfg_IdealLo / Cfg_IdealHi` | - | no ideal band; KPI cards show the alarm zones only | no legacy member |
| `Sts_Quality` | `HW_Fault ? 2 : 0` | derived (2 = bad) | T_KPI card members read as DDT_Process_Value (same members as the PV templates) |
| `Val_ROC, Alm_ROC, Sts_NE107, Sim_En, Sim_PV, Cfg_FiltTC, Cfg_LoCutoff, Cfg_SqrtExtract, Sts_Sim, Sts_Subst` | - | dropped | no legacy member |
| `(not bound)` | `x/Notification, x/Default, Type, Edits` |  | tags/legacy UDT definition (live RGTCR export) |

### PID_Loop (T_PID: Loops/Loop_B1..B4, dw_Loop) - library UDT, no plant DDT_ loop type

12 rows mapped, 1 rows with no legacy equivalent.

| T_ member | Legacy member | Note | Source |
|---|---|---|---|
| `Val_PV / Val_SP / Out_CV` | `PV / SP / OUT` |  | generator/pid_loops/generate_loops.py before 8e719f8 (PID_Loop UDT) |
| `Sts_Mode (0 Man 1 Auto 2 Cas)` | `Mode (0 MAN 1 AUTO 2 CAS)` |  | generator/pid_loops/generate_loops.py before 8e719f8 (PID_Loop UDT) |
| `Sts_Man / Sts_Auto / Sts_Cas` | `Mode = 0 / 1 / 2` | derived | generator/pid_loops/generate_loops.py before 8e719f8 (PID_Loop UDT) |
| `Cmd_Man / Cmd_Auto / Cmd_Cas` | `Mode := 0 / 1 / 2` |  | generator/pid_loops/generate_loops.py before 8e719f8 (PID_Loop UDT) |
| `Cmd_SP / Cmd_CV` | `SP / OUT (bidirectional)` |  | generator/pid_loops/generate_loops.py before 8e719f8 (PID_Loop UDT) |
| `Cfg_PVEU / Cfg_PVMin / Cfg_PVMax` | `PV.engUnit / PV.engLow / PV.engHigh` | tag properties of the PV member | generator/pid_loops/generate_loops.py before 8e719f8 (PID_Loop UDT) |
| `Alm_DevH/Cfg_Lim, Alm_DevL/Cfg_Lim` | `AlmHi, AlmLo (absolute limits), AlmDev` | cards: alarm = PV >= AlmHi or PV <= AlmLo | generator/pid_loops/generate_loops.py before 8e719f8 (PID_Loop UDT) |
| `Alm_DevH/Sts_Active, Alm_DevL/Sts_Active` | `PV >= AlmHi, PV <= AlmLo` | derived | generator/pid_loops/generate_loops.py before 8e719f8 (PID_Loop UDT) |
| `Cfg_Kp / Cfg_Ti / Cfg_Td / Cfg_DirectAct` | `Kp / Ti / Td / Action (0 reverse 1 direct)` | Ti, Td in seconds (no TIME scaling) | generator/pid_loops/generate_loops.py before 8e719f8 (PID_Loop UDT) |
| `Cfg_SPMin / Cfg_SPMax / Cfg_CVMin / Cfg_CVMax` | `SP_Lo / SP_Hi / OUT_Lo / OUT_Hi` |  | generator/pid_loops/generate_loops.py before 8e719f8 (PID_Loop UDT) |
| `Cfg_Desc` | `Description` |  | generator/pid_loops/generate_loops.py before 8e719f8 (PID_Loop UDT) |
| `Val_Err` | `PV - SP` | derived | generator/pid_loops/generate_loops.py before 8e719f8 (PID_Loop UDT) |
| `Sts_Intlk, Sts_Track, Sts_WindupHi/Lo, Sts_SPRamping, Cfg_DB, Cfg_SPRate, Cfg_CVRate, Alm_PVBad, Intlk/*` | - | dropped | no legacy member |

### DDT_Station (T_Station: Station_Tile, Station_Fill, dw_Station) - imported Designer views, mapped at build time by tools/legacy_station.py

41 rows mapped, 0 rows with no legacy equivalent.

| T_ member | Legacy member | Note | Source |
|---|---|---|---|
| `Sts_Active` | `Active` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_Complete` | `Complete` |  | steward/tools/fix_station.py MAP, inverted |
| `Prm_Deadband` | `Deadband` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_Disabled` | `Disabled` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_Failed` | `Failed` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_Filling` | `Filling` |  | steward/tools/fix_station.py MAP, inverted |
| `Val_Gross` | `GrossWeight` |  | steward/tools/fix_station.py MAP, inverted |
| `Cmd_Reset` | `HMI_Reset` | 1 s pulse | steward/tools/fix_station.py MAP, inverted |
| `Cmd_Select` | `HMI_Select` | 1 s pulse | steward/tools/fix_station.py MAP, inverted |
| `Out_InletCmd` | `InletCMD` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_InletReq` | `InletREQ` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_Msg` | `Msg` |  | steward/tools/fix_station.py MAP, inverted |
| `Val_Net` | `NetWeight` |  | steward/tools/fix_station.py MAP, inverted |
| `Val_PT` | `PT` |  | steward/tools/fix_station.py MAP, inverted |
| `Val_PTDiff` | `PT_Diff` |  | steward/tools/fix_station.py MAP, inverted |
| `Inp_PTValid` | `PT_Valid` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_PressBalanced` | `Press_Balanced` |  | steward/tools/fix_station.py MAP, inverted |
| `Prm_MaxPress` | `Press_Max` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_ReadyToFill` | `ReadyToFill` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_ReadyToStart` | `ReadyToStart` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_Recovering` | `Recovering` |  | steward/tools/fix_station.py MAP, inverted |
| `Out_SampleCmd` | `SampleCMD` |  | steward/tools/fix_station.py MAP, inverted |
| `Prm_PrefillPress` | `SamplePress` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_SampleReq` | `SampleREQ` |  | steward/tools/fix_station.py MAP, inverted |
| `Prm_SampleWt` | `SampleWeight` |  | steward/tools/fix_station.py MAP, inverted |
| `Cfg_ScaleName` | `ScaleName` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_Selected` | `Selected` |  | steward/tools/fix_station.py MAP, inverted |
| `Cfg_Desc` | `StationName` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_State` | `StatusEnum` |  | steward/tools/fix_station.py MAP, inverted |
| `Cmd_Tare` | `TareCMD` | 1 s pulse | steward/tools/fix_station.py MAP, inverted |
| `Val_Tare` | `TareWeight` |  | steward/tools/fix_station.py MAP, inverted |
| `Prm_TargetWt` | `TargetWeight` |  | steward/tools/fix_station.py MAP, inverted |
| `Val_Total` | `TotalWeight` |  | steward/tools/fix_station.py MAP, inverted |
| `Cfg_EU` | `Units` |  | steward/tools/fix_station.py MAP, inverted |
| `Out_VacuumCmd` | `VacuumCMD` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_VacuumReq` | `VacuumREQ` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_Vacuumed` | `Vacuumed` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_Vacuuming` | `Vacuuming` |  | steward/tools/fix_station.py MAP, inverted |
| `Sts_Venting` | `Venting` |  | steward/tools/fix_station.py MAP, inverted |
| `Inp_VesselPresent` | `Vessel_Present` |  | steward/tools/fix_station.py MAP, inverted |
| `Cmd_Zero` | `ZeroCMD` |  | steward/tools/fix_station.py MAP, inverted |

### T_HeatEx (dw_HeatTransfer) - no legacy type

0 rows mapped, 1 rows with no legacy equivalent.

| T_ member | Legacy member | Note | Source |
|---|---|---|---|
| `every member` | - | no DDT_ carries heat-exchanger calculations; the window is a placeholder that names the tag | no legacy member |

### Native x80 DDTs (Templates/IO/*, dw_IOCard)

0 rows mapped, 0 rows with no legacy equivalent.

| T_ member | Legacy member | Note | Source |
|---|---|---|---|
| `(unchanged)` | `(unchanged)` | the I/O faceplates bind the Control Expert x80 device DDTs, not T_ types | build.py IMPORTED_PARTS |

