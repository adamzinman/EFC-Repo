# Station fill screen

Covers `Templates/Station/Station_Fill`.
Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/Station/Station_Fill/view.json` (same content as the copy in `imported/EFC_StationFaceplates/`).
Related overview tile: [Station_Tile](Station_Tile.md).

## Overview

The filling view for one T_Station instance: the station header with the select toggle, the live net, gross, tare and total weights, the fill bar with deadband band and target marker, the vessel pressure, the four setpoint entry fields, and the Tare, Zero and Reset commands with a confirm step.

- **Default size:** 300 x 400 (`props.defaultSize`).
- **Bound to:** one T_Station instance through `params.tagPath`. It is the only param.
- **Opening or embedding:** no `efc.ui` function opens this view, and it has no embedded views (`ia.display.view`). A screen places it with `tagPath` set. `Templates/Station/_Demo` does this in `Left/Fills` for stations 1 to 4. `docs/station-faceplates.md` describes it as the filling screen.
- **Dock:** none. It is not a dynamic window.

## Start here: what `t` and `s` are

Almost everything on this view reads two view custom properties with one-letter names:

- **`t` = tags.** The raw values read from the PLC. It holds 36 members, each a tag binding to `{tagPath}/<member>`.
- **`s` = state.** The display-ready values the screen shows: formatted text, style class names, bar positions and lock flags. It is one property binding on `view.custom.t` with a script transform. Every calculation on this view lives in that transform.

Data flows one way:

**PLC tags → `t` → script transform → `s` → screen elements**

To find them in the Designer, select the view root and open **Custom** in the Property Editor. To see the calculations, open the binding on `custom.s` and read its Script transform.

Three things that make the view harder to follow than it looks:

- **`t` uses the old station popup's names, not the PLC names.** The table below maps them. For example, `t.NetWeight` reads `Val_Net` and `t.SamplePress` reads `Prm_PrefillPress`.
- **A missing or bad tag silently becomes `false`, `0` or blank** inside the transform. A bad value does not raise an error on screen. It shows as a normal 0, off or blank state. Only the quality marker on `custom.t` in the Designer shows it.
- **Not every `s` key is shown.** The view binds 26 of the 51 keys. The other 25 are computed and unused here (the Tag section and the Notes say which are unused).

The transform is identical to the one in [Station dynamic window](../Dynamic%20Window/Station/Station.md) and in [Station_Tile](Station_Tile.md). It is the same code in three places.

### `t`: raw tag values

Each key is a read-only indirect tag binding (`{0}` = `{view.params.tagPath}`). The four setpoint entries on the view are separate bidirectional bindings and are not in this list.

| `t` key | PLC member |
|---|---|
| `Active` | `Sts_Active` |
| `Complete` | `Sts_Complete` |
| `Deadband` | `Prm_Deadband` |
| `Disabled` | `Sts_Disabled` |
| `Failed` | `Sts_Failed` |
| `Filling` | `Sts_Filling` |
| `GrossWeight` | `Val_Gross` |
| `InletCMD` | `Out_InletCmd` |
| `InletREQ` | `Sts_InletReq` |
| `Msg` | `Sts_Msg` |
| `NetWeight` | `Val_Net` |
| `PT` | `Val_PT` |
| `PT_Diff` | `Val_PTDiff` |
| `PT_Valid` | `Inp_PTValid` |
| `Press_Balanced` | `Sts_PressBalanced` |
| `Press_Max` | `Prm_MaxPress` |
| `ReadyToFill` | `Sts_ReadyToFill` |
| `ReadyToStart` | `Sts_ReadyToStart` |
| `Recovering` | `Sts_Recovering` |
| `SampleCMD` | `Out_SampleCmd` |
| `SamplePress` | `Prm_PrefillPress` |
| `SampleREQ` | `Sts_SampleReq` |
| `SampleWeight` | `Prm_SampleWt` |
| `ScaleName` | `Cfg_ScaleName` |
| `Selected` | `Sts_Selected` |
| `StationName` | `Cfg_Desc` |
| `TareWeight` | `Val_Tare` |
| `TargetWeight` | `Prm_TargetWt` |
| `TotalWeight` | `Val_Total` |
| `Units` | `Cfg_EU` |
| `VacuumCMD` | `Out_VacuumCmd` |
| `VacuumREQ` | `Sts_VacuumReq` |
| `Vacuumed` | `Sts_Vacuumed` |
| `Vacuuming` | `Sts_Vacuuming` |
| `Venting` | `Sts_Venting` |
| `Vessel_Present` | `Inp_VesselPresent` |

### `s`: how each key is calculated

The derived-state transform is the same code as in `Templates/Dynamic Window/Station/Station`. The tables below are copied from [Station dynamic window](../Dynamic%20Window/Station/Station.md), where they were checked against the transform.

Bound on this view (26 keys): `chip`, `dbW`, `dbX`, `dis`, `fillCls`, `fillW`, `gross`, `hiCls`, `msg`, `name`, `net`, `pct`, `pt`, `ptSmallCls`, `rem`, `resetLocked`, `scale`, `selCls`, `selText`, `tare`, `target`, `tgtX`, `total`, `tzLocked`, `units`, `word`. The other 25 keys (`sel`, `busy`, `db`, `steps`, `stepText`, `permLed`, `permTxt`, `inReq`, `inCmd`, `inIlk`, `smReq`, `smCmd`, `smIlk`, `vaReq`, `vaCmd`, `vaIlk`, `ptCls`, `ptd`, `ptW`, `preX`, `maxX`, `pre`, `pmax`, `ptBad`, `foot`) are computed and not bound.

**Header and selection**

| `s` member | Calculation |
|---|---|
| `name`, `scale` | `StationName` (or "Station" if blank), `ScaleName` |
| `units` | `Units`; blank, `---`, `null` or `None` becomes `kg` |
| `sel`, `selText`, `selCls`, `hiCls` | From `Selected`: button text SELECTED or SELECT, button style on or off, and the `Util/Highlight` class on the status panel |
| `dis` | `Disabled` |

**Status chip and message (`word`, `chip`, `msg`, `busy`)**

The transform takes the first of these that is true:

| Order | `t` member | Chip text (`word`) | Chip style (`chip`) |
|---|---|---|---|
| 1 | `Disabled` | DISABLED | `State/OutOfService` |
| 2 | `Failed` | FAULT | `State/Fault` |
| 3 | `Complete` | COMPLETE | `State/Stopped` |
| 4 | `Filling` | FILLING | `State/Running` |
| 5 | `SampleCMD` | SAMPLING | `State/Running` |
| 6 | `Vacuuming` | VACUUMING | `State/Transition` |
| 7 | `Venting` | VENTING | `State/Transition` |
| 8 | `Recovering` | RECOVERING | `State/Transition` |
| 9 | `Active` | ACTIVE | `State/Running` |
| 10 | `ReadyToStart` or `ReadyToFill` | READY | `State/Stopped` |
| none | | IDLE | `State/Stopped` |

- `msg` is the PLC's `Msg` text, or a default sentence for the state (for example "Filling primary vessel") when `Msg` is blank.
- `busy` is true when the chip is `State/Running` or `State/Transition`.

**Weight**

| `s` member | Calculation |
|---|---|
| `net`, `target`, `db`, `gross`, `tare`, `total` | The tag value as text, 3 decimals |
| `rem` | target − net, never below 0 |
| `pct` | net ÷ target × 100, 1 decimal. "OVER " in front when net > target + deadband. "-" when the target is 0 |
| `fillCls` | `Bar/FillAlarm` when over, otherwise `Bar/Fill` |
| `fillW`, `tgtX`, `dbX`, `dbW` | Bar positions as 0–1 fractions of a bar that spans 108 % of target: fill = net, marker = target, deadband band = target ± deadband (minimum width 0.012) |

**Pressure**

| `s` member | Calculation |
|---|---|
| `pt` | `PT` as `#,##0.0`, or `-----` when `PT_Valid` is false |
| `ptBad`, `ptCls`, `ptSmallCls` | `Value/BadQuality` styling and the BAD QUALITY label when `PT_Valid` is false |
| `ptd` | "dP x.x psi" from `PT_Diff` |
| `ptW`, `preX`, `maxX` | Bar positions on a bar that spans 110 % of `Press_Max`: fill = `PT` (0 when invalid), markers at the prefill pressure and at `Press_Max` |
| `pre`, `pmax` | Prefill and maximum pressure as `#,##0.0` |

**Step strip (`steps`, `stepText`)**

Each of the six steps is Pending, Active, Done or Fault. `steps[n]` is the segment class (`Station/Step/*`) and `stepText[n]` is the caption class.

| Step | Done when | Active when |
|---|---|---|
| Vessel | `Vessel_Present` | never |
| Vac | `Vacuumed` | `Vacuuming` |
| Prefill | `Press_Balanced` | `Active` and `Vacuumed` and not `Filling` |
| Fill | `Complete` or `SampleCMD` | `Filling` |
| Sample | `Complete` | `SampleCMD` |
| Done | `Complete` | never |

When `Disabled`, every step is Pending. When `Failed`, the first step that is not Done is drawn as Fault.

**Permissives and valves**

| `s` member | Calculation |
|---|---|
| `permLed[0..4]`, `permTxt[0..4]` | LED on or off, and darker text when true, for `Vessel_Present`, `PT_Valid`, `Press_Balanced`, `ReadyToStart`, `ReadyToFill` |
| `inReq`/`inCmd`, `smReq`/`smCmd`, `vaReq`/`vaCmd` | LED for each valve's request and command (Inlet, Sample, Vacuum) |
| `inIlk`, `smIlk`, `vaIlk` | The `I` badge: request on and command off |

**Commands**

| `s` member | Calculation |
|---|---|
| `tzLocked` | `busy` or `Disabled`. Locks Tare and Zero |
| `resetLocked` | not (`Complete` or `Failed`). Locks Reset |
| `foot` | "Station disabled: commands unavailable", else "Tare and Zero locked while active" when `tzLocked`, else blank |

## How it operates

**State word, chip and header.** The `custom.s` transform works out the state word and chip exactly as the overview tile does. The condition order is Disabled, Failed, Complete, Filling, SampleCMD (SAMPLING), Vacuuming, Venting, Recovering, Active, ReadyToStart or ReadyToFill (READY), and IDLE otherwise. Chip classes: DISABLED `State/OutOfService`; FAULT `State/Fault`; COMPLETE, READY and IDLE `State/Stopped`; FILLING, SAMPLING and ACTIVE `State/Running`; VACUUMING, VENTING and RECOVERING `State/Transition`. When the station is selected, the header adds `Util/Highlight`.

**Select toggle.** The button at the right of the header shows `SELECTED` or `SELECT`, with `Button/Toggle/On` or `Button/Toggle/Off`. It is enabled when the station is not disabled, or when the user is below Operator level (decision 33). Below Operator it shows a lock icon with the tooltip "Requires Operator access". A click pulses `Cmd_Select` through `efc.ui.cmd`: it writes True, and after 1 s a background thread writes False. Below Operator the press writes nothing and opens the AccessDenied popup. There is no confirm step.

**Message line.** The line under the header shows `Sts_Msg`. When that is empty it shows the fallback text for the state, for example "Filling primary vessel" or "Station disabled".

**Net block.** The target is shown with its units. The net value is shown with its units and the percent of target (`OVER` prefix when over). The bar is `Bar/Fill`, or `Bar/FillAlarm` when over target + deadband. It has a deadband band from target - deadband to target + deadband and a target marker. Below the bar, "Remaining" is max(0, target - net), and "Gross" is the gross weight.

**Boxes.** Tare and Total show the tare and total weights with their units. PT shows the vessel pressure in psig. When `Inp_PTValid` is false it shows `-----` with the bad-quality class `Value/BadQuality`.

**Setpoints.** Four numeric entry fields are bidirectional tag bindings, so an edit writes straight to the tag. Each field is enabled only at Operator level or above and when the station is not disabled; below Operator the fields are greyed (no lock), as in the Station window. Target and Sample show 3 decimals and take their units from `Cfg_EU`. Max press and Prefill press show 1 decimal and the fixed unit `psig`.

**Commands and confirm step.** Tare, Zero and Reset do not write when pressed. Each stores its name in `view.custom.pendingCmd`. The button row is hidden while `pendingCmd` is set, and the confirm strip is shown instead. It reads, for example, "Tare WT101?" (the scale name followed by "?"). Confirm clears `pendingCmd` and pulses the matching `Cmd_*` member, which is True and then False 1 s later. Cancel only clears `pendingCmd`. Below Operator level, Tare, Zero and Reset stay enabled with a lock icon and the tooltip "Requires Operator access". A press opens the AccessDenied popup and stores no command.

**Enable rules.**

| Control | Enabled when | Expression |
|---|---|---|
| Select | station not disabled, or below Operator (locked) | `({view.custom.level} < 1) || (!{view.custom.s.dis})` |
| Target, Sample, Max press, Prefill fields | station not disabled | `!{view.custom.s.dis}` |
| Tare, Zero | below Operator (locked), or not locked | `({view.custom.level} < 1) || (!{view.custom.s.tzLocked})`. `tzLocked` = busy or disabled, where busy means the state chip is Running or Transition (FILLING, SAMPLING, ACTIVE, VACUUMING, VENTING, RECOVERING). |
| Reset | below Operator (locked), or not locked | `({view.custom.level} < 1) || (!{view.custom.s.resetLocked})`. `resetLocked` = not (Complete or Failed), so Reset is enabled only when Complete or Failed is true. |
| Confirm, Cancel | while a command is pending | visibility only: `{view.custom.pendingCmd} != ""`. The Confirm button has no enable expression. |

**Commands and security.** Select, Tare, Zero, Reset (through Confirm) write to tags only through `efc.ui`. `custom.level` binds `session.props.auth.securityLevels` through `efc.ui.level`. Below Operator (level 1) the four command buttons stay visible and pressable with a lock icon. Their scripts call `efc.ui.cmd` (Select, Confirm) or `efc.ui.userLevel` and `efc.ui.denied` (Tare, Zero, Reset), so a press below level writes nothing, logs a warning and opens `Templates/Dynamic Window/Parts/AccessDenied`. The four setpoint fields write through bidirectional tag bindings, not `efc.ui.cmd`; they are greyed below Operator (see Notes).

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `""` | T_Station instance. All tag bindings and all command writes use it as `{view.params.tagPath}`. | Caller (the screen, or `_Demo`). Read by every binding and script. |

The param has `paramDirection: input` and `persistent: true`. There are no output params.

### View-level custom properties (`custom`)

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.s` | dict of 51 keys (sample values, for example `name` = `"Station 1"`) | property on `view.custom.t`, with a script transform | Script transform (see Scripts reference) | Display model. The bindings read 26 of its keys (see Bindings reference). The other 25 are computed and never bound. |
| `view.custom.t` | dict of 36 keys, each `null` | none on the dict itself. Each key has its own tag binding. | Tag members, listed below | Raw values mirrored from the station tag. It is the only input to the `s` transform. |
| `view.custom.pendingCmd` | `""` | none (no binding) | Set by the Tare, Zero, Reset, Cancel and Confirm scripts | Name of the command waiting for confirmation (`Tare`, `Zero` or `Reset`). Empty when no command is pending. It is view state, not session state. |
| `view.custom.level` | `0` | property on `session.props.auth.securityLevels`, with a script transform `return efc.ui.level(value)` | Role level from the Perspective session (0 Guest to 5 Admin) | The user's level. The command buttons read it for the lock icon, tooltip and enable rule (decision 33). |

**Tag mirrors.** The 36 keys of `view.custom.t` each take their value from one T_Station member through an indirect tag binding (`mode: indirect`, `{0}` = `{view.params.tagPath}`, fallback delay 2.5 s). The mirror bindings are read-only. The four setpoint fields are separate bidirectional bindings (see Bindings reference).

| Group | Members (`custom.t.<key>` = PCLib member) |
|---|---|
| Config | StationName = `Cfg_Desc`; ScaleName = `Cfg_ScaleName`; Units = `Cfg_EU` |
| Setpoint mirrors | TargetWeight = `Prm_TargetWt`; Deadband = `Prm_Deadband`; Press_Max = `Prm_MaxPress`; SamplePress = `Prm_PrefillPress`; SampleWeight = `Prm_SampleWt` (bound but never read, see Notes) |
| Weights | NetWeight = `Val_Net`; GrossWeight = `Val_Gross`; TareWeight = `Val_Tare`; TotalWeight = `Val_Total` |
| Pressure | PT = `Val_PT`; PT_Diff = `Val_PTDiff`; PT_Valid = `Inp_PTValid`; Press_Balanced = `Sts_PressBalanced` |
| Message | Msg = `Sts_Msg` |
| Permissives | Vessel_Present = `Inp_VesselPresent`; ReadyToStart = `Sts_ReadyToStart`; ReadyToFill = `Sts_ReadyToFill` |
| Valve requests | InletREQ = `Sts_InletReq`; InletCMD = `Out_InletCmd`; SampleREQ = `Sts_SampleReq`; SampleCMD = `Out_SampleCmd`; VacuumREQ = `Sts_VacuumReq`; VacuumCMD = `Out_VacuumCmd` |
| Status | Active = `Sts_Active`; Complete = `Sts_Complete`; Disabled = `Sts_Disabled`; Failed = `Sts_Failed`; Filling = `Sts_Filling`; Recovering = `Sts_Recovering`; Selected = `Sts_Selected`; Vacuumed = `Sts_Vacuumed`; Vacuuming = `Sts_Vacuuming`; Venting = `Sts_Venting` |

### Component-level custom properties

None. The components carry no `custom` properties.

### Session, page and message payloads

- **Session:** none. The view reads and writes no `session.custom` value.
- **Page:** none.
- **Messages:** none. The view has no message handlers and sends no messages.
- **View state:** `view.custom.pendingCmd` only (see above).

## Bindings reference

Total: **91 bindings**. 38 are at the view root and 53 are on components. By type: 40 `tag`, 25 `property` and 26 `expr`. Component bindings: 23 `property`, 26 `expr` and 4 `tag` (the setpoint fields).

### View root

The 38 view-root bindings are 36 tag mirrors, the `custom.s` transform and `custom.level`. Each is listed with its source in **View-level custom properties** above.

### root/Header

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Header | `props.style.classes` | expr | `("Container/Panel" + {view.custom.s.hiCls}) + ' Station/Fill/Header'` | Header classes. `hiCls` adds `Util/Highlight` when selected. |
| root/Header/Titles/Name | `props.text` | property | `view.custom.s.name` | Station name, or "Station" when empty. |
| root/Header/Titles/Scale | `props.text` | property | `view.custom.s.scale` | Scale tag name, or empty. |
| root/Header/Chip | `props.text` | property | `view.custom.s.word` | State word. |
| root/Header/Chip | `props.style.classes` | expr | `({view.custom.s.chip}) + ' Station/Fill/Chip'` | State colour class plus `Station/Fill/Chip`. |
| root/Header/Select | `props.text` | property | `view.custom.s.selText` | `SELECTED` or `SELECT`. |
| root/Header/Select | `props.style.classes` | expr | `{view.custom.s.selCls}` | `Button/Toggle/On` or `Button/Toggle/Off`. |
| root/Header/Select | `props.enabled` | expr | `({view.custom.level} < 1) || (!{view.custom.s.dis})` | Enabled unless the station is disabled. Below Operator it stays enabled (locked). |

### root/Body

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Body/Msg | `props.text` | property | `view.custom.s.msg` | Message line: `Sts_Msg`, or the state fallback text. |
| root/Body/NetBlock/NetHead/Target | `props.text` | property | `view.custom.s.target` | Target weight, 3 decimals. |
| root/Body/NetBlock/NetHead/TgtUnits | `props.text` | property | `view.custom.s.units` | Weight units. |
| root/Body/NetBlock/NetRow/Net | `props.text` | property | `view.custom.s.net` | Net weight, 3 decimals. |
| root/Body/NetBlock/NetRow/NetUnits | `props.text` | property | `view.custom.s.units` | Weight units. |
| root/Body/NetBlock/NetRow/Pct | `props.text` | property | `view.custom.s.pct` | Percent of target, `OVER` prefix when over, `-` with no target. |
| root/Body/NetBlock/NetBar/Fill | `position.width` | property | `view.custom.s.fillW` | Bar length: net / (1.08 x target), clamped 0 to 1. |
| root/Body/NetBlock/NetBar/Fill | `props.style.classes` | expr | `{view.custom.s.fillCls}` | `Bar/FillAlarm` when over target + deadband, else `Bar/Fill`. |
| root/Body/NetBlock/NetBar/Deadband | `position.x` | property | `view.custom.s.dbX` | Left edge of the deadband band: (target - deadband) / scale. |
| root/Body/NetBlock/NetBar/Deadband | `position.width` | property | `view.custom.s.dbW` | Width of the deadband band: 2 x deadband / scale, minimum 0.012, or 0 with no target. |
| root/Body/NetBlock/NetBar/Target | `position.x` | property | `view.custom.s.tgtX` | Target marker position. |
| root/Body/NetBlock/NetCap/Rem | `props.text` | property | `view.custom.s.rem` | Remaining: max(0, target - net), 3 decimals. |
| root/Body/NetBlock/NetCap/Gr | `props.text` | property | `view.custom.s.gross` | Gross weight, 3 decimals. |
| root/Body/Boxes/Tare/TareRow/TareVal | `props.text` | property | `view.custom.s.tare` | Tare weight, 3 decimals. |
| root/Body/Boxes/Tare/TareRow/TareU | `props.text` | property | `view.custom.s.units` | Weight units. |
| root/Body/Boxes/Total/TotalRow/TotalVal | `props.text` | property | `view.custom.s.total` | Total weight, 3 decimals. |
| root/Body/Boxes/Total/TotalRow/TotalU | `props.text` | property | `view.custom.s.units` | Weight units. |
| root/Body/Boxes/PT/PTRow/PTVal | `props.text` | property | `view.custom.s.pt` | Vessel pressure, 1 decimal, or `-----` when invalid. |
| root/Body/Boxes/PT/PTRow/PTVal | `props.style.classes` | expr | `{view.custom.s.ptSmallCls}` | Full class string. It adds `Value/BadQuality` when `Inp_PTValid` is false. |
| root/Body/Setpoints/SpRow0/SpTarget/SpTargetRow/SpTargetFld | `props.value` | tag | `{0}/Prm_TargetWt` (indirect, `{0}` = `{view.params.tagPath}`, bidirectional) | Target setpoint. Edits write `Prm_TargetWt`. |
| root/Body/Setpoints/SpRow0/SpTarget/SpTargetRow/SpTargetFld | `props.enabled` | expr | `{view.custom.level} >= 1 && (!{view.custom.s.dis})` | Enabled at Operator or above when the station is not disabled; greyed below Operator. |
| root/Body/Setpoints/SpRow0/SpTarget/SpTargetRow/SpTargetU | `props.text` | property | `view.custom.s.units` | Weight units. |
| root/Body/Setpoints/SpRow0/SpSample/SpSampleRow/SpSampleFld | `props.value` | tag | `{0}/Prm_SampleWt` (indirect, bidirectional) | Sample setpoint. Edits write `Prm_SampleWt`. |
| root/Body/Setpoints/SpRow0/SpSample/SpSampleRow/SpSampleFld | `props.enabled` | expr | `{view.custom.level} >= 1 && (!{view.custom.s.dis})` | Enabled at Operator or above when the station is not disabled; greyed below Operator. |
| root/Body/Setpoints/SpRow0/SpSample/SpSampleRow/SpSampleU | `props.text` | property | `view.custom.s.units` | Weight units. |
| root/Body/Setpoints/SpRow1/SpPmax/SpPmaxRow/SpPmaxFld | `props.value` | tag | `{0}/Prm_MaxPress` (indirect, bidirectional) | Max press setpoint. Edits write `Prm_MaxPress`. |
| root/Body/Setpoints/SpRow1/SpPmax/SpPmaxRow/SpPmaxFld | `props.enabled` | expr | `{view.custom.level} >= 1 && (!{view.custom.s.dis})` | Enabled at Operator or above when the station is not disabled; greyed below Operator. |
| root/Body/Setpoints/SpRow1/SpPrefill/SpPrefillRow/SpPrefillFld | `props.value` | tag | `{0}/Prm_PrefillPress` (indirect, bidirectional) | Prefill press setpoint. Edits write `Prm_PrefillPress`. |
| root/Body/Setpoints/SpRow1/SpPrefill/SpPrefillRow/SpPrefillFld | `props.enabled` | expr | `{view.custom.level} >= 1 && (!{view.custom.s.dis})` | Enabled at Operator or above when the station is not disabled; greyed below Operator. |
| root/Body/Commands/Buttons | `position.display` | expr | `{view.custom.pendingCmd} = ""` | Button row shown when no command is pending. |
| root/Body/Commands/Buttons/Tare | `props.enabled` | expr | `({view.custom.level} < 1) || (!{view.custom.s.tzLocked})` | Tare enabled unless locked (busy or disabled). Below Operator it stays enabled (locked). |
| root/Body/Commands/Buttons/Zero | `props.enabled` | expr | `({view.custom.level} < 1) || (!{view.custom.s.tzLocked})` | Zero enabled unless locked (busy or disabled). Below Operator it stays enabled (locked). |
| root/Body/Commands/Buttons/Reset | `props.enabled` | expr | `({view.custom.level} < 1) || (!{view.custom.s.resetLocked})` | Reset enabled only when Complete or Failed. Below Operator it stays enabled (locked). |
| root/Body/Commands/Confirm | `position.display` | expr | `{view.custom.pendingCmd} != ""` | Confirm strip shown while a command is pending. |
| root/Body/Commands/Confirm/ConfirmTxt | `props.text` | expr | `{view.custom.pendingCmd} + " " + {view.custom.s.scale} + "?"` | Question text, for example `Tare WT101?`. |

## Scripts reference

Total: **6 event scripts** and **1 transform script**. There are no custom methods, message handlers or property-change scripts.

1. **`root/Header/Select`**: `events.component.onActionPerformed`, scope G. Trigger: click on the Select toggle. It pulses `Cmd_Select`. Code:

```python
	# Momentary pulse: set the PLC bit, release it 1 s later (harmless if the PLC clears it first).
	if efc.ui.cmd(self, 'Cmd_Select', True, 1):
		path = self.view.params.tagPath + "/Cmd_Select"
		def _release(p=path):
			import time
			time.sleep(1.0)
			system.tag.writeBlocking([p], [False])
		system.util.invokeAsynchronous(_release)
```

   It writes True to `Cmd_Select` through `efc.ui.cmd` (minimum level Operator) and releases it to False 1 s later on a background thread. Below Operator, `efc.ui.cmd` writes nothing and opens the AccessDenied popup. No confirm step.

2. **`root/Body/Commands/Buttons/Tare`**: `events.component.onActionPerformed`, scope G. Trigger: click on Tare. It only stores the command name for confirmation. Code:

```python
	if efc.ui.userLevel(self) < 1:
		efc.ui.denied(self, 1, 'Tare')
	else:
		self.view.custom.pendingCmd = "Tare"
```

3. **`root/Body/Commands/Buttons/Zero`**: `events.component.onActionPerformed`, scope G. Trigger: click on Zero. Stores `Zero` in `pendingCmd`. Code:

```python
	if efc.ui.userLevel(self) < 1:
		efc.ui.denied(self, 1, 'Zero')
	else:
		self.view.custom.pendingCmd = "Zero"
```

4. **`root/Body/Commands/Buttons/Reset`**: `events.component.onActionPerformed`, scope G. Trigger: click on Reset. Stores `Reset` in `pendingCmd`. Code:

```python
	if efc.ui.userLevel(self) < 1:
		efc.ui.denied(self, 1, 'Reset')
	else:
		self.view.custom.pendingCmd = "Reset"
```

5. **`root/Body/Commands/Confirm/Cancel`**: `events.component.onActionPerformed`, scope G. Trigger: click on Cancel. Clears `pendingCmd`, so the button row returns and nothing is written. Code:

```python
	self.view.custom.pendingCmd = ""
```

6. **`root/Body/Commands/Confirm/ConfirmBtn`**: `events.component.onActionPerformed`, scope G. Trigger: click on Confirm. It clears `pendingCmd`, maps the name to `Cmd_Tare`, `Cmd_Zero` or `Cmd_Reset`, and pulses that member (True, then False after 1 s on a background thread). Code:

```python
	cmd = self.view.custom.pendingCmd
	self.view.custom.pendingCmd = ""
	member = {"Tare": "Cmd_Tare", "Zero": "Cmd_Zero", "Reset": "Cmd_Reset"}.get(cmd)
	if member and efc.ui.cmd(self, member, True, 1):
		path = self.view.params.tagPath + "/" + member
		def _release(p=path):
			import time
			time.sleep(1.0)
			system.tag.writeBlocking([p], [False])
		system.util.invokeAsynchronous(_release)
```

   The write goes through `efc.ui.cmd` (minimum level Operator), so a press below Operator is refused and logged. There is still no enable check on `Sts_Active` or `Sts_Disabled` before the write (see Notes).

7. **`view.custom.s`**: script transform on the property binding from `view.custom.t`. Trigger: runs whenever any of the 36 mirrored values changes. It returns the whole display dict. Code (identical to the transform in `Station_Tile`):

```python
	t = value
	def g(k, d=None):
		try:
			v = t[k]
		except:
			v = None
		return d if v is None else v
	def b(k):
		try:
			return bool(g(k, False))
		except:
			return False
	def f(k):
		try:
			return float(g(k, 0.0))
		except:
			return 0.0
	def cl(x):
		return max(0.0, min(1.0, x))
	f3 = lambda x: "%.3f" % x
	def f1(x):
		return "{:,.1f}".format(x)
	dis, flt, cmp = b("Disabled"), b("Failed"), b("Complete")
	smp = b("SampleCMD")
	if dis:   word, chip, txt = "DISABLED", "State/OutOfService", "Station disabled"
	elif flt: word, chip, txt = "FAULT", "State/Fault", "Station fault"
	elif cmp: word, chip, txt = "COMPLETE", "State/Stopped", "Fill complete"
	elif b("Filling"):    word, chip, txt = "FILLING", "State/Running", "Filling primary vessel"
	elif smp:             word, chip, txt = "SAMPLING", "State/Running", "Routing sample to secondary"
	elif b("Vacuuming"):  word, chip, txt = "VACUUMING", "State/Transition", "Evacuating vessel"
	elif b("Venting"):    word, chip, txt = "VENTING", "State/Transition", "Venting"
	elif b("Recovering"): word, chip, txt = "RECOVERING", "State/Transition", "Recovering"
	elif b("Active"):     word, chip, txt = "ACTIVE", "State/Running", "Station active"
	elif b("ReadyToStart") or b("ReadyToFill"): word, chip, txt = "READY", "State/Stopped", "Ready to start"
	else:                 word, chip, txt = "IDLE", "State/Stopped", "Idle"
	busy = chip in ("State/Running", "State/Transition")
	msg = g("Msg", "")
	try:
		msg = msg.strip() if isinstance(msg, basestring) else ""
	except NameError:
		msg = msg.strip() if isinstance(msg, str) else ""
	if not msg:
		msg = txt
	u = g("Units", "")
	u = ("%s" % u).strip() if u is not None else ""
	if u in ("", "---", "null", "None"):
		u = "kg"
	net, tgt, db = f("NetWeight"), f("TargetWeight"), f("Deadband")
	scale = tgt * 1.08 if tgt > 0 else 1.0
	pct = net / tgt * 100.0 if tgt > 0 else 0.0
	over = tgt > 0 and net > tgt + db
	pt, pmax, pre = f("PT"), f("Press_Max"), f("SamplePress")
	ptok = b("PT_Valid")
	pscale = pmax * 1.1 if pmax > 0 else 100.0
	vac = b("Vacuumed")
	st = [0, 0, 0, 0, 0, 0]
	st[0] = 2 if b("Vessel_Present") else 0
	st[1] = 2 if vac else (1 if b("Vacuuming") else 0)
	st[2] = 2 if b("Press_Balanced") else (1 if (b("Active") and vac and not b("Filling")) else 0)
	st[3] = 2 if (cmp or smp) else (1 if b("Filling") else 0)
	st[4] = 2 if cmp else (1 if smp else 0)
	st[5] = 2 if cmp else 0
	if dis:
		st = [0, 0, 0, 0, 0, 0]
	elif flt:
		for i in range(6):
			if st[i] != 2:
				st[i] = 3
				break
	SC = ["Station/Step/Pending", "Station/Step/Active", "Station/Step/Done", "Station/Step/Fault"]
	TC = ["Text/Caption Text/Mod/Center", "Text/Caption Text/Mod/Center Text/Color/Default Text/Weight/Bold",
	      "Text/Caption Text/Mod/Center Text/Color/Default", "Text/Caption Text/Mod/Center Text/Color/Default Text/Weight/Bold"]
	led = lambda x: "Indicator/LED/On" if x else "Indicator/LED/Off"
	pl = lambda x: "Text/Label Text/Color/Default" if x else "Text/Label"
	sel = b("Selected")
	tz = busy or dis
	rs = not (cmp or flt)
	foot = "Station disabled: commands unavailable" if dis else ("Tare and Zero locked while active" if tz else "")
	name = g("StationName", "")
	scl = g("ScaleName", "")
	return {
		"name": ("%s" % name) if name else "Station", "scale": ("%s" % scl) if scl else "",
		"word": word, "chip": chip, "msg": msg, "units": u,
		"busy": busy, "dis": dis, "sel": sel,
		"selText": "SELECTED" if sel else "SELECT",
		"selCls": "Button/Toggle/On" if sel else "Button/Toggle/Off",
		"hiCls": " Util/Highlight" if sel else "",
		"net": f3(net), "target": f3(tgt), "rem": f3(max(0.0, tgt - net)), "db": f3(db),
		"gross": f3(f("GrossWeight")), "tare": f3(f("TareWeight")), "total": f3(f("TotalWeight")),
		"pct": (("OVER " if over else "") + "%.1f%%" % pct) if tgt > 0 else "-",
		"fillCls": "Bar/FillAlarm" if over else "Bar/Fill",
		"fillW": cl(net / scale), "tgtX": cl(tgt / scale) if tgt > 0 else 0.0,
		"dbX": cl((tgt - db) / scale), "dbW": max(0.012, cl(2 * db / scale)) if tgt > 0 else 0.0,
		"pt": f1(pt) if ptok else "-----", "ptBad": not ptok,
		"ptCls": "Text/ValueLarge" if ptok else "Text/ValueLarge Value/BadQuality",
		"ptSmallCls": "Text/Value Text/Mod/Right" if ptok else "Text/Value Text/Mod/Right Value/BadQuality",
		"ptd": "dP %.1f psi" % f("PT_Diff"),
		"ptW": cl(pt / pscale) if ptok else 0.0,
		"preX": cl(pre / pscale), "maxX": cl(pmax / pscale - 0.008),
		"pre": f1(pre), "pmax": f1(pmax),
		"steps": [SC[x] for x in st], "stepText": [TC[x] for x in st],
		"permLed": [led(b("Vessel_Present")), led(ptok), led(b("Press_Balanced")), led(b("ReadyToStart")), led(b("ReadyToFill"))],
		"permTxt": [pl(b("Vessel_Present")), pl(ptok), pl(b("Press_Balanced")), pl(b("ReadyToStart")), pl(b("ReadyToFill"))],
		"inReq": led(b("InletREQ")), "inCmd": led(b("InletCMD")), "inIlk": b("InletREQ") and not b("InletCMD"),
		"smReq": led(b("SampleREQ")), "smCmd": led(smp), "smIlk": b("SampleREQ") and not smp,
		"vaReq": led(b("VacuumREQ")), "vaCmd": led(b("VacuumCMD")), "vaIlk": b("VacuumREQ") and not b("VacuumCMD"),
		"tzLocked": tz, "resetLocked": rs, "foot": foot
	}
```

   Plain-language summary:
   - Reads each key with `g()`, `b()` and `f()`, which return a default for a missing or `None` value (0 for numbers, false for booleans, empty for text).
   - Sets the state word and chip, and the busy flag (chip is Running or Transition).
   - Builds the weights, the remaining value, the percent, the over-fill flag, and the bar, deadband and target positions. The bar scale is 1.08 x target, or 1.0 when target is 0 or less.
   - Builds the pressure text and classes. `pscale` is 1.1 x `Press_Max`, or 100 when `Press_Max` is 0 or less.
   - Builds the units text, with `kg` as the fallback.
   - Builds the step list, the permissive LEDs, the valve request and command indicators, the interlock flags, and the footer text. None of these is bound (see Notes).
   - Sets `tzLocked` and `resetLocked`, which the command buttons use.

### library calls made from this view

`efc.ui` only. The view calls `efc.ui.level` (the `custom.level` transform), `efc.ui.cmd` (Select and Confirm), `efc.ui.userLevel` and `efc.ui.denied` (Tare, Zero and Reset). It calls no other project library module.

## Tag members used

Relative to `tagPath`. Types and comments are from `types/PCLib_Members.csv`. Writes are the four command pulses and the four bidirectional setpoints.

| Member | Access | Data type | Meaning |
|---|---|---|---|
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Cfg_ScaleName` | read | STRING[20] | Scale tag shown on the HMI, e.g. WT-101 |
| `Cfg_EU` | read | STRING[8] | Weight units text (kg, lb) |
| `Prm_TargetWt` | read/write | REAL | Fill target, net weight (operator setpoint) |
| `Prm_Deadband` | read | REAL | Fill deadband, net weight (operator setpoint) |
| `Prm_SampleWt` | read/write | REAL | Sample draw weight (operator setpoint) |
| `Prm_MaxPress` | read/write | REAL | Maximum vessel pressure during fill (operator setpoint) |
| `Prm_PrefillPress` | read/write | REAL | Prefill pressure (operator setpoint) |
| `Val_Net` | read | REAL | Net weight (Cfg_EU) |
| `Val_Gross` | read | REAL | Gross weight (Cfg_EU) |
| `Val_Tare` | read | REAL | Tare weight (Cfg_EU) |
| `Val_Total` | read | REAL | Total filled this cycle (Cfg_EU) |
| `Val_PT` | read | REAL | Vessel pressure |
| `Val_PTDiff` | read | REAL | Vessel minus header pressure |
| `Inp_PTValid` | read | BOOL | Pressure reading valid |
| `Inp_VesselPresent` | read | BOOL | Vessel detected on the station |
| `Sts_PressBalanced` | read | BOOL | Vessel and header pressures balanced |
| `Sts_Msg` | read | STRING[40] | Status message for the HMI |
| `Sts_ReadyToStart` | read | BOOL | Ready to start (all start permissives) |
| `Sts_ReadyToFill` | read | BOOL | Ready to fill |
| `Sts_InletReq` | read | BOOL | Sequence requests the inlet valve open |
| `Out_InletCmd` | read | BOOL | Inlet valve command |
| `Sts_SampleReq` | read | BOOL | Sequence requests the sample valve open |
| `Out_SampleCmd` | read | BOOL | Sample valve command |
| `Sts_VacuumReq` | read | BOOL | Sequence requests the vacuum valve open |
| `Out_VacuumCmd` | read | BOOL | Vacuum valve command |
| `Sts_Active` | read | BOOL | Station in a fill cycle |
| `Sts_Complete` | read | BOOL | Fill complete |
| `Sts_Disabled` | read | BOOL | Station disabled |
| `Sts_Failed` | read | BOOL | Fill failed - reset required |
| `Sts_Filling` | read | BOOL | Filling |
| `Sts_Recovering` | read | BOOL | Recovering |
| `Sts_Selected` | read | BOOL | Station selected |
| `Sts_Vacuumed` | read | BOOL | Vessel evacuated |
| `Sts_Vacuuming` | read | BOOL | Evacuating the vessel |
| `Sts_Venting` | read | BOOL | Venting |
| `Cmd_Select` | write | BOOL | Select this station (one-shot) |
| `Cmd_Tare` | write | BOOL | Tare the scale (one-shot; blocked while active) |
| `Cmd_Zero` | write | BOOL | Zero the scale (one-shot; blocked while active) |
| `Cmd_Reset` | write | BOOL | Reset a failed / complete station (one-shot) |

## Component tree

```
- `root` (ia.container.flex)
  - `Header` (ia.container.flex)
    - `Titles` (ia.container.flex)
      - `Name` (ia.display.label)
      - `Scale` (ia.display.label)
    - `Chip` (ia.display.label)
    - `Select` (ia.input.button)
  - `Body` (ia.container.flex)
    - `Msg` (ia.display.label)
    - `NetBlock` (ia.container.flex)
      - `NetHead` (ia.container.flex)
        - `NetLbl` (ia.display.label)
        - `TgtLbl` (ia.display.label)
        - `Target` (ia.display.label)
        - `TgtUnits` (ia.display.label)
      - `NetRow` (ia.container.flex)
        - `Net` (ia.display.label)
        - `NetUnits` (ia.display.label)
        - `Spacer` (ia.display.label)
        - `Pct` (ia.display.label)
      - `NetBar` (ia.container.coord)
        - `Fill` (ia.display.label)
        - `Deadband` (ia.display.label)
        - `Target` (ia.display.label)
      - `NetCap` (ia.container.flex)
        - `RemL` (ia.display.label)
        - `Rem` (ia.display.label)
        - `Sp2` (ia.display.label)
        - `GrL` (ia.display.label)
        - `Gr` (ia.display.label)
    - `Boxes` (ia.container.flex)
      - `Tare` (ia.container.flex)
        - `TareLbl` (ia.display.label)
        - `TareRow` (ia.container.flex)
          - `TareVal` (ia.display.label)
          - `TareU` (ia.display.label)
      - `Total` (ia.container.flex)
        - `TotalLbl` (ia.display.label)
        - `TotalRow` (ia.container.flex)
          - `TotalVal` (ia.display.label)
          - `TotalU` (ia.display.label)
      - `PT` (ia.container.flex)
        - `PTLbl` (ia.display.label)
        - `PTRow` (ia.container.flex)
          - `PTVal` (ia.display.label)
          - `PTU` (ia.display.label)
    - `Setpoints` (ia.container.flex)
      - `SpLbl` (ia.display.label)
      - `SpRow0` (ia.container.flex)
        - `SpTarget` (ia.container.flex)
          - `SpTargetLbl` (ia.display.label)
          - `SpTargetRow` (ia.container.flex)
            - `SpTargetFld` (ia.input.numeric-entry-field)
            - `SpTargetU` (ia.display.label)
        - `SpSample` (ia.container.flex)
          - `SpSampleLbl` (ia.display.label)
          - `SpSampleRow` (ia.container.flex)
            - `SpSampleFld` (ia.input.numeric-entry-field)
            - `SpSampleU` (ia.display.label)
      - `SpRow1` (ia.container.flex)
        - `SpPmax` (ia.container.flex)
          - `SpPmaxLbl` (ia.display.label)
          - `SpPmaxRow` (ia.container.flex)
            - `SpPmaxFld` (ia.input.numeric-entry-field)
            - `SpPmaxU` (ia.display.label)
        - `SpPrefill` (ia.container.flex)
          - `SpPrefillLbl` (ia.display.label)
          - `SpPrefillRow` (ia.container.flex)
            - `SpPrefillFld` (ia.input.numeric-entry-field)
            - `SpPrefillU` (ia.display.label)
    - `Commands` (ia.container.flex)
      - `Buttons` (ia.container.flex)
        - `Tare` (ia.input.button)
        - `Zero` (ia.input.button)
        - `Reset` (ia.input.button)
      - `Confirm` (ia.container.flex)
        - `ConfirmTxt` (ia.display.label)
        - `Cancel` (ia.input.button)
        - `ConfirmBtn` (ia.input.button)
```

## Notes and open questions

- **Role lock on the commands (decision 33).** Select, Tare, Zero, Reset and Confirm check the role level through `efc.ui` before they write. Below Operator they show a lock and refuse the press. The writes are not audited here: `efc.ui.cmd` is called without `audit=True`. Enforce access in Perspective security and the PLC, because the HMI check is not security.
- **Setpoint fields write directly.** The four setpoint fields are bidirectional tag bindings, not `efc.ui.cmd`, so an edit is not logged or audited. They are disabled below Operator, as in the Station window.
- **Cancel is not gated.** Cancel only clears `pendingCmd` and writes nothing, so it has no level check. It cannot be reached below Operator because Tare, Zero and Reset open the popup instead of storing a command.
- **Confirm has no guard.** `ConfirmBtn` has no enable expression, and its script does not re-read `Sts_Active` or `Sts_Disabled`. If a cycle starts between the first click (Tare or Zero) and Confirm, the pulse is still written. PCLib says Cmd_Tare and Cmd_Zero are "blocked while active". The view does not re-check that before writing, and whether the PLC enforces it is not in the repo.
- **Tare and Zero are not gated on selection.** `tzLocked` depends only on busy and disabled, not on `Sts_Selected`. The PCLib comments do not say whether Tare or Zero needs the station to be selected. Open question.
- **Reset ignores disabled.** `resetLocked` = not (Complete or Failed). If Sts_Disabled and (Sts_Complete or Sts_Failed) are both true, Reset is enabled. Whether the PLC can reach that state is not in the repo.
- **Setpoints editable during a cycle.** Only the disabled state blocks the four setpoint fields. Editing Prm_TargetWt or Prm_MaxPress while the station is Active is allowed by the view. Whether that is intended is not in the repo.
- **Computed but never shown.** 25 of the 51 keys in `custom.s` are never bound. They include the start-step list (`steps`, `stepText`), the permissive LEDs (`permLed`, `permTxt`), the valve request, command and interlock indicators (`inReq` to `vaIlk`), the footer (`foot`) and the pressure-bar helpers (`ptW`, `preX`, `maxX`, `pre`, `pmax`, `ptBad`, `ptCls`, `ptd`). The view therefore has no step, permissive or interlock indicators, although the transform builds them. Either those elements were removed, or the transform is out of date.
- **Tag subscriptions with no visible effect.** 12 mirrored tags feed only the unbound outputs above, or none: InletREQ, InletCMD, SampleREQ, VacuumREQ, VacuumCMD, Vessel_Present, Press_Balanced, Vacuumed, PT_Diff, Press_Max, SamplePress and SampleWeight. `SampleWeight` is bound but never read. The sample setpoint field binds `Prm_SampleWt` directly.
- **Name mismatch.** `custom.t.SamplePress` mirrors `Prm_PrefillPress`, and the transform's "pre" values come from it. The mapping follows the assumption noted in `docs/station-faceplates.md`. The name is a leftover from the old naming.
- **Fixed units text.** The Max press and Prefill press lines use the fixed unit `psig`.
- **Confirm text.** The confirm strip uses the scale name. When `Cfg_ScaleName` is empty it reads, for example, `Tare ?`.
- **Pulse release.** The one-shot pulses are released to False 1 s later by the view's own background thread. The code comment says this is harmless if the PLC clears the bit first. PCLib describes these members as one-shot.
