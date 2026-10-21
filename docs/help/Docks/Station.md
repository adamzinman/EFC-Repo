# Docks/Station

Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Docks/Station/view.json`
Built from: `imported/EFC_StationFaceplates/com.inductiveautomation.perspective/views/Templates/Station/Station_Sidebar/view.json` (see Overview). Opened from: the station overview tile [`Templates/Station/Station_Tile`](../Templates/Station/Station_Tile.md) through `efc.ui.openDynamic`. Dynamic window id `dw_Station`. `efc.ui.BY_TYPE` maps `T_Station` to `dw_Station`.

## Overview

The operator dynamic window for a fill station (T_Station). It is the full station faceplate: header, status chip and step strip, net, gross, tare and total weights with the target bar, vessel pressure, permissives, valve REQ and CMD lamps, setpoints, and the Tare, Zero and Reset commands. It opens in the screen's right-hand region (`Docks/Region`), not as a popup.

- **Default size:** 400 x 860 (`props.defaultSize`). The root column uses `Container/Popup Util/Clip` and has no scroll class, so content taller than the window is clipped, not scrolled (the `Util/Clip` class is defined in EFC_Styles and was not checked).
- **Parameters:** `tagPath` only (the T_Station instance). The view has no `tType` param, and `efc.ui.openDynamic` passes only `tagPath`.
- **How it is opened:** the tile's click runs `efc.ui.openDynamic(self)`. That function writes `session.custom.efcDw[pageId] = {path: 'Docks/Station', params: {tagPath: ...}}`. `Docks/Region` then displays this view.
- **Built view:** this view is not written by `generator/docks/build_docks.py`. `build.py` copies the imported Designer project `imported/EFC_StationFaceplates` into the merged library and relocates `Templates/Station/Station_Sidebar` to `Docks/Station` (its `RELOCATE` table). `steward/tools/fix_station.py` maps the DDT_Station member names to T_Station, adds the dynamic-window params to the tile and sets the window to 400 x 860 (`steward/DECISIONS.md`, decisions 4 and 25). Make changes in the imported source and rebuild. Edits made directly to `Docks/Station/view.json` are replaced on the next build.
- **How it closes:** the header icon (`Util/Pointer`) runs `efc.ui.closeDynamic(self)` on click, which restores the screen default set by `efc.ui.setDefaultDock` on `Docks/Region` startup. That startup script is not in this view.

## How it operates

**Header.** The name is `custom.s.name` (`Cfg_Desc`, or "Station" when blank). The scale is `custom.s.scale` (`Cfg_ScaleName`).

**Status.** The chip (`custom.s.word`, class `custom.s.chip`) shows the status word for the first matching state: DISABLED, FAULT, COMPLETE, FILLING, SAMPLING, VACUUMING, VENTING, RECOVERING, ACTIVE, READY or IDLE. The message line shows `Sts_Msg` when it has text, otherwise the status text for that state. The status block is highlighted (`Util/Highlight`) while the station is selected.

**Select** (level 1 and above, and station not disabled). The button reads SELECT or SELECTED from `Sts_Selected`. It pulses `Cmd_Select`: True now, then False 1 s later on a background thread (`system.util.invokeAsynchronous`).

**Steps.** A strip of six segments: Vessel, Vac, Prefill, Fill, Sample, Done. Each segment is Pending, Active, Done or Fault (see the derived state below). When the station is FAILED, the first unfinished step is drawn as the fault step.

**Weights.** Net weight (`Val_Net`) is shown to three decimals, with the target (`Prm_TargetWt`), remaining, deadband band (`±` deadband), gross, tare and total (`Val_Gross`, `Val_Tare`, `Val_Total`). The bar is scaled to 108 % of the target and clamped, so a net above 108 % of target is drawn at full width. Overfill (net above target + deadband) switches the bar to `Bar/FillAlarm` and the percentage text to `OVER`.

**Pressure.** Vessel pressure (`Val_PT`) is shown as `#,##0.0`, or `-----` with a `BAD QUALITY` label when `Inp_PTValid` is false. The bar shows the prefill pressure (`Prm_PrefillPress`) and the maximum (`Prm_MaxPress`) as markers. The dP line shows `Val_PTDiff`.

**Permissives.** Five LEDs: Vessel present, PT valid, Press balanced, Ready to start, Ready to fill. Each LED is on when its flag is true.

**Valves.** Inlet, Sample and Vacuum each show a REQ LED (`Sts_InletReq`, `Sts_SampleReq`, `Sts_VacuumReq`) and a CMD LED (`Out_InletCmd`, `Out_SampleCmd`, `Out_VacuumCmd`). An `I` marker shows when REQ is on and CMD is off.

**Setpoints** (level 1 and above, and station not disabled). Five numeric entries, each bound two-way to a T_Station setpoint: Target (`Prm_TargetWt`), Sample (`Prm_SampleWt`), Max press (`Prm_MaxPress`), Prefill press (`Prm_PrefillPress`) and Deadband (`Prm_Deadband`). Units come from `custom.s.units`, except the two pressures, which are fixed as `psig`. The entries write through their bindings. No `efc.ui` call, no role check in script, no audit.

**Commands.** Tare and Zero are enabled at level 1 and above when the station is not locked (`tzLocked` is false). Reset is enabled at level 1 and above when `resetLocked` is false, that is, only when the station is Complete or Failed. Each button sets `view.custom.pendingCmd` to `Tare`, `Zero` or `Reset`, which shows the confirm strip: "`<Command> <scale>?`" with Cancel and Confirm. Cancel clears `pendingCmd`. Confirm clears it and writes `Cmd_Tare`, `Cmd_Zero` or `Cmd_Reset` True, then False 1 s later. While a command is pending the button row is hidden. The foot line below the buttons shows the lock reason (see `foot`).

**Role checks.** Role levels come from the Perspective session and are mapped by `efc.ui.level` to `view.custom.level`. The Select button, the setpoints, the command buttons and Confirm are gated by `view.custom.level >= 1` in their enable expressions. No script in this view checks the level, and no script calls `efc.ui.cmd`. Real access control has to be enforced in Perspective security and the PLC logic.

**Audit.** None. The commands and setpoints do not call `efc.ui`, so nothing is audit-logged.

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `""` | T_Station instance. Every component binding uses `{view.params.tagPath}`. | Set by `efc.ui.openDynamic` from the tile's `dwTagPath` (or `tagPath`). Read by the tag bindings and the command scripts. |

`tagPath` has `paramDirection: input` and `persistent: true`. No output parameters.

### View-level custom properties (`custom`)

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.s` | sample values from the design preview (for example `"name": "Station 1"`, `"net": "9.814"`) | property with script transform | `view.custom.t` → `custom.s` transform (below) | Derived display state for the whole faceplate: header text, status chip and message, step strip, weight and pressure bars, permissive and valve LEDs, enable flags and the foot line. Every component that shows state reads `view.custom.s.*`. The default is replaced when the binding evaluates. |
| `view.custom.t` | dictionary of nulls | 36 tag mirrors (see below) | `custom.t.<Name>` | Raw tag values, one key per member. Only the transform reads it. |
| `view.custom.level` | `0` | property + script transform | `session.props.auth.user.roles` → `return efc.ui.level(value)` | Role level 0-5 via `efc.ui.level` (Guest 0, Operator 1, Maintenance 2, Supervisor 3, Engineer 4, Admin 5). Gates the Select button, the setpoints, Tare, Zero, Reset and the Confirm and Cancel buttons. |
| `view.custom.pendingCmd` | `""` | none (written by scripts) | none | The command waiting for confirmation: `Tare`, `Zero`, `Reset` or empty. Set by the command buttons and cleared by Cancel and Confirm. Not persisted. |

#### Derived state (`custom.s`)

`custom.s` is one property binding on `view.custom.t` with a script transform. Every time the transform runs it returns a single dictionary of the keys below. Components bind to individual keys (for example `view.custom.s.word`, `view.custom.s.steps[0]`). The transform is explained in the Scripts reference.

Keys: `name`, `scale`, `word`, `chip`, `msg`, `units`, `busy`, `dis`, `sel`, `selText`, `selCls`, `hiCls`, `net`, `target`, `rem`, `db`, `gross`, `tare`, `total`, `pct`, `fillCls`, `fillW`, `tgtX`, `dbX`, `dbW`, `pt`, `ptBad`, `ptCls`, `ptSmallCls`, `ptd`, `ptW`, `preX`, `maxX`, `pre`, `pmax`, `steps`, `stepText`, `permLed`, `permTxt`, `inReq`, `inCmd`, `inIlk`, `smReq`, `smCmd`, `smIlk`, `vaReq`, `vaCmd`, `vaIlk`, `tzLocked`, `resetLocked`, `foot`.

#### Tag mirrors (`custom.t.*`)

There are 36 tag-mirror properties. Each `custom.t.<Name>` has an indirect, read-only tag binding to `{view.params.tagPath}/<member>` (`bidirectional: false`, fallback delay 2.5 s), and its default is `null`. The transform reads them through `custom.t` (the `value` of `custom.s`). `custom.t.Deadband` and `custom.t.Press_Max` and the other setpoint mirrors read the same members as the setpoint entries, so the faceplate shows the value the setpoint entries write.

| Group | Members (custom.t key: member) |
|---|---|
| State flags | `Active`: `Sts_Active`, `Complete`: `Sts_Complete`, `Disabled`: `Sts_Disabled`, `Failed`: `Sts_Failed`, `Filling`: `Sts_Filling`, `Recovering`: `Sts_Recovering`, `Selected`: `Sts_Selected`, `Vacuuming`: `Sts_Vacuuming`, `Vacuumed`: `Sts_Vacuumed`, `Venting`: `Sts_Venting` |
| Valve requests and commands | `InletREQ`: `Sts_InletReq`, `InletCMD`: `Out_InletCmd`, `SampleREQ`: `Sts_SampleReq`, `SampleCMD`: `Out_SampleCmd`, `VacuumREQ`: `Sts_VacuumReq`, `VacuumCMD`: `Out_VacuumCmd` |
| Permissives | `Vessel_Present`: `Inp_VesselPresent`, `PT_Valid`: `Inp_PTValid`, `Press_Balanced`: `Sts_PressBalanced`, `ReadyToStart`: `Sts_ReadyToStart`, `ReadyToFill`: `Sts_ReadyToFill` |
| Weights | `NetWeight`: `Val_Net`, `GrossWeight`: `Val_Gross`, `TareWeight`: `Val_Tare`, `TotalWeight`: `Val_Total` |
| Setpoints (operator, bidirectional entries) | `TargetWeight`: `Prm_TargetWt`, `SampleWeight`: `Prm_SampleWt`, `Press_Max`: `Prm_MaxPress`, `SamplePress`: `Prm_PrefillPress`, `Deadband`: `Prm_Deadband` |
| Pressure | `PT`: `Val_PT`, `PT_Diff`: `Val_PTDiff` |
| Text and configuration | `Msg`: `Sts_Msg`, `StationName`: `Cfg_Desc`, `ScaleName`: `Cfg_ScaleName`, `Units`: `Cfg_EU` |

### Component-level custom properties

None.

### Session, page and message payloads

- `session.props.auth.user.roles`: read by `custom.level` (transform `efc.ui.level`).
- `session.custom.efcDw[pageId]`: written by `efc.ui.openDynamic` (tile) and `efc.ui.closeDynamic` (header icon). Read by `Docks/Region` (not in this file).
- `page.props.pageId`: read by `efc.ui._state` to key `efcDw`. Reached through the header icon.
- `session.props.auth.user.userName`: not used in this view.
- No message handlers. No `customMethods`.

## Bindings reference

Total: **124 bindings**: 38 at view root (`custom.s`, 36 `custom.t.*` mirrors and `custom.level`) and 86 on components. Types: 47 `expr`, 41 `tag`, 36 `property`. `params.tagPath` has `paramDirection` only. The setpoint entries are component tag bindings, and the setpoint values are shared with the `custom.t` mirrors.

### View root

The view-root bindings drive the custom properties. Each one is listed with its full source in **View-level custom properties** above.

### `root/Header`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Header/Titles/Name | `props.text` | property | `view.custom.s.name` | Text content |
| root/Header/Titles/Scale | `props.text` | property | `view.custom.s.scale` | Text content |

### `root/Body/Status`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Body/Status | `props.style.classes` | expr | `("Container/Faceplate" + {view.custom.s.hiCls}) + ' Station/Sidebar/Status'` | CSS class(es) selected by state |
| root/Body/Status/ChipRow/Chip | `props.text` | property | `view.custom.s.word` | Text content |
| root/Body/Status/ChipRow/Chip | `props.style.classes` | expr | `({view.custom.s.chip}) + ' Station/Fill/Chip'` | CSS class(es) selected by state |
| root/Body/Status/ChipRow/Select | `props.text` | property | `view.custom.s.selText` | Text content |
| root/Body/Status/ChipRow/Select | `props.style.classes` | expr | `{view.custom.s.selCls}` | CSS class(es) selected by state |
| root/Body/Status/ChipRow/Select | `props.enabled` | expr | `{view.custom.level} >= 1 && (!{view.custom.s.dis})` | Enabled while expression is true |
| root/Body/Status/Msg | `props.text` | property | `view.custom.s.msg` | Text content |
| root/Body/Status/Steps/Step0/Seg | `props.style.classes` | expr | `{view.custom.s.steps[0]}` | CSS class(es) selected by state |
| root/Body/Status/Steps/Step0/Txt | `props.style.classes` | expr | `{view.custom.s.stepText[0]}` | CSS class(es) selected by state |
| root/Body/Status/Steps/Step1/Seg | `props.style.classes` | expr | `{view.custom.s.steps[1]}` | CSS class(es) selected by state |
| root/Body/Status/Steps/Step1/Txt | `props.style.classes` | expr | `{view.custom.s.stepText[1]}` | CSS class(es) selected by state |
| root/Body/Status/Steps/Step2/Seg | `props.style.classes` | expr | `{view.custom.s.steps[2]}` | CSS class(es) selected by state |
| root/Body/Status/Steps/Step2/Txt | `props.style.classes` | expr | `{view.custom.s.stepText[2]}` | CSS class(es) selected by state |
| root/Body/Status/Steps/Step3/Seg | `props.style.classes` | expr | `{view.custom.s.steps[3]}` | CSS class(es) selected by state |
| root/Body/Status/Steps/Step3/Txt | `props.style.classes` | expr | `{view.custom.s.stepText[3]}` | CSS class(es) selected by state |
| root/Body/Status/Steps/Step4/Seg | `props.style.classes` | expr | `{view.custom.s.steps[4]}` | CSS class(es) selected by state |
| root/Body/Status/Steps/Step4/Txt | `props.style.classes` | expr | `{view.custom.s.stepText[4]}` | CSS class(es) selected by state |
| root/Body/Status/Steps/Step5/Seg | `props.style.classes` | expr | `{view.custom.s.steps[5]}` | CSS class(es) selected by state |
| root/Body/Status/Steps/Step5/Txt | `props.style.classes` | expr | `{view.custom.s.stepText[5]}` | CSS class(es) selected by state |

### `root/Body/Weight`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Body/Weight/NetHead/Target | `props.text` | property | `view.custom.s.target` | Text content |
| root/Body/Weight/NetHead/TgtUnits | `props.text` | property | `view.custom.s.units` | Text content |
| root/Body/Weight/NetRow/Net | `props.text` | property | `view.custom.s.net` | Text content |
| root/Body/Weight/NetRow/NetUnits | `props.text` | property | `view.custom.s.units` | Text content |
| root/Body/Weight/NetRow/Pct | `props.text` | property | `view.custom.s.pct` | Text content |
| root/Body/Weight/NetBar/Fill | `position.width` | property | `view.custom.s.fillW` | Bar fill width |
| root/Body/Weight/NetBar/Fill | `props.style.classes` | expr | `{view.custom.s.fillCls}` | CSS class(es) selected by state |
| root/Body/Weight/NetBar/Deadband | `position.x` | property | `view.custom.s.dbX` | Marker position (x) |
| root/Body/Weight/NetBar/Deadband | `position.width` | property | `view.custom.s.dbW` | Band width |
| root/Body/Weight/NetBar/Target | `position.x` | property | `view.custom.s.tgtX` | Marker position (x) |
| root/Body/Weight/NetCap/Rem | `props.text` | property | `view.custom.s.rem` | Text content |
| root/Body/Weight/NetCap/Db | `props.text` | property | `view.custom.s.db` | Text content |
| root/Body/Weight/Boxes/Gross/GrossRow/GrossVal | `props.text` | property | `view.custom.s.gross` | Text content |
| root/Body/Weight/Boxes/Tare/TareRow/TareVal | `props.text` | property | `view.custom.s.tare` | Text content |
| root/Body/Weight/Boxes/Total/TotalRow/TotalVal | `props.text` | property | `view.custom.s.total` | Text content |

### `root/Body/Pressure`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Body/Pressure/PHead/Ptd | `props.text` | property | `view.custom.s.ptd` | Text content |
| root/Body/Pressure/PRow/Pt | `props.text` | property | `view.custom.s.pt` | Text content |
| root/Body/Pressure/PRow/Pt | `props.style.classes` | expr | `{view.custom.s.ptCls}` | CSS class(es) selected by state |
| root/Body/Pressure/PRow/PtBad | `position.display` | property | `view.custom.s.ptBad` | Shown while value is true |
| root/Body/Pressure/PtBar/Fill | `position.width` | property | `view.custom.s.ptW` | Bar fill width |
| root/Body/Pressure/PtBar/Prefill | `position.x` | property | `view.custom.s.preX` | Marker position (x) |
| root/Body/Pressure/PtBar/Max | `position.x` | property | `view.custom.s.maxX` | Marker position (x) |
| root/Body/Pressure/PCap/Pre | `props.text` | property | `view.custom.s.pre` | Text content |
| root/Body/Pressure/PCap/Max | `props.text` | property | `view.custom.s.pmax` | Text content |

### `root/Body/PermIO`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Body/PermIO/Perms/Perm0/Led | `props.style.classes` | expr | `({view.custom.s.permLed[0]}) + ' Station/Sidebar/Led'` | CSS class(es) selected by state |
| root/Body/PermIO/Perms/Perm0/Txt | `props.style.classes` | expr | `{view.custom.s.permTxt[0]}` | CSS class(es) selected by state |
| root/Body/PermIO/Perms/Perm1/Led | `props.style.classes` | expr | `({view.custom.s.permLed[1]}) + ' Station/Sidebar/Led'` | CSS class(es) selected by state |
| root/Body/PermIO/Perms/Perm1/Txt | `props.style.classes` | expr | `{view.custom.s.permTxt[1]}` | CSS class(es) selected by state |
| root/Body/PermIO/Perms/Perm2/Led | `props.style.classes` | expr | `({view.custom.s.permLed[2]}) + ' Station/Sidebar/Led'` | CSS class(es) selected by state |
| root/Body/PermIO/Perms/Perm2/Txt | `props.style.classes` | expr | `{view.custom.s.permTxt[2]}` | CSS class(es) selected by state |
| root/Body/PermIO/Perms/Perm3/Led | `props.style.classes` | expr | `({view.custom.s.permLed[3]}) + ' Station/Sidebar/Led'` | CSS class(es) selected by state |
| root/Body/PermIO/Perms/Perm3/Txt | `props.style.classes` | expr | `{view.custom.s.permTxt[3]}` | CSS class(es) selected by state |
| root/Body/PermIO/Perms/Perm4/Led | `props.style.classes` | expr | `({view.custom.s.permLed[4]}) + ' Station/Sidebar/Led'` | CSS class(es) selected by state |
| root/Body/PermIO/Perms/Perm4/Txt | `props.style.classes` | expr | `{view.custom.s.permTxt[4]}` | CSS class(es) selected by state |
| root/Body/PermIO/Valves/V_Inlet/Name/Ilk | `position.display` | property | `view.custom.s.inIlk` | Shown while value is true |
| root/Body/PermIO/Valves/V_Inlet/Req/Led | `props.style.classes` | expr | `({view.custom.s.inReq}) + ' Station/Sidebar/Led'` | CSS class(es) selected by state |
| root/Body/PermIO/Valves/V_Inlet/Cmd/Led | `props.style.classes` | expr | `({view.custom.s.inCmd}) + ' Station/Sidebar/Led'` | CSS class(es) selected by state |
| root/Body/PermIO/Valves/V_Sample/Name/Ilk | `position.display` | property | `view.custom.s.smIlk` | Shown while value is true |
| root/Body/PermIO/Valves/V_Sample/Req/Led | `props.style.classes` | expr | `({view.custom.s.smReq}) + ' Station/Sidebar/Led'` | CSS class(es) selected by state |
| root/Body/PermIO/Valves/V_Sample/Cmd/Led | `props.style.classes` | expr | `({view.custom.s.smCmd}) + ' Station/Sidebar/Led'` | CSS class(es) selected by state |
| root/Body/PermIO/Valves/V_Vacuum/Name/Ilk | `position.display` | property | `view.custom.s.vaIlk` | Shown while value is true |
| root/Body/PermIO/Valves/V_Vacuum/Req/Led | `props.style.classes` | expr | `({view.custom.s.vaReq}) + ' Station/Sidebar/Led'` | CSS class(es) selected by state |
| root/Body/PermIO/Valves/V_Vacuum/Cmd/Led | `props.style.classes` | expr | `({view.custom.s.vaCmd}) + ' Station/Sidebar/Led'` | CSS class(es) selected by state |

### `root/Body/Setpoints`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Body/Setpoints/SpRow0/SpTarget/SpTargetRow/SpTargetFld | `props.value` | tag (indirect) | tag `{0}/Prm_TargetWt` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Body/Setpoints/SpRow0/SpTarget/SpTargetRow/SpTargetFld | `props.enabled` | expr | `{view.custom.level} >= 1 && (!{view.custom.s.dis})` | Enabled while expression is true |
| root/Body/Setpoints/SpRow0/SpTarget/SpTargetRow/SpTargetU | `props.text` | property | `view.custom.s.units` | Text content |
| root/Body/Setpoints/SpRow0/SpSample/SpSampleRow/SpSampleFld | `props.value` | tag (indirect) | tag `{0}/Prm_SampleWt` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Body/Setpoints/SpRow0/SpSample/SpSampleRow/SpSampleFld | `props.enabled` | expr | `{view.custom.level} >= 1 && (!{view.custom.s.dis})` | Enabled while expression is true |
| root/Body/Setpoints/SpRow0/SpSample/SpSampleRow/SpSampleU | `props.text` | property | `view.custom.s.units` | Text content |
| root/Body/Setpoints/SpRow1/SpPmax/SpPmaxRow/SpPmaxFld | `props.value` | tag (indirect) | tag `{0}/Prm_MaxPress` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Body/Setpoints/SpRow1/SpPmax/SpPmaxRow/SpPmaxFld | `props.enabled` | expr | `{view.custom.level} >= 1 && (!{view.custom.s.dis})` | Enabled while expression is true |
| root/Body/Setpoints/SpRow1/SpPrefill/SpPrefillRow/SpPrefillFld | `props.value` | tag (indirect) | tag `{0}/Prm_PrefillPress` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Body/Setpoints/SpRow1/SpPrefill/SpPrefillRow/SpPrefillFld | `props.enabled` | expr | `{view.custom.level} >= 1 && (!{view.custom.s.dis})` | Enabled while expression is true |
| root/Body/Setpoints/SpRow2/SpDb/SpDbRow/SpDbFld | `props.value` | tag (indirect) | tag `{0}/Prm_Deadband` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Body/Setpoints/SpRow2/SpDb/SpDbRow/SpDbFld | `props.enabled` | expr | `{view.custom.level} >= 1 && (!{view.custom.s.dis})` | Enabled while expression is true |
| root/Body/Setpoints/SpRow2/SpDb/SpDbRow/SpDbU | `props.text` | property | `view.custom.s.units` | Text content |

### `root/Body/Commands`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Body/Commands/Buttons | `position.display` | expr | `{view.custom.pendingCmd} = ""` | Shown while expression is true |
| root/Body/Commands/Buttons/Tare | `props.enabled` | expr | `{view.custom.level} >= 1 && (!{view.custom.s.tzLocked})` | Enabled while expression is true |
| root/Body/Commands/Buttons/Zero | `props.enabled` | expr | `{view.custom.level} >= 1 && (!{view.custom.s.tzLocked})` | Enabled while expression is true |
| root/Body/Commands/Buttons/Reset | `props.enabled` | expr | `{view.custom.level} >= 1 && (!{view.custom.s.resetLocked})` | Enabled while expression is true |
| root/Body/Commands/Confirm | `position.display` | expr | `{view.custom.pendingCmd} != ""` | Shown while expression is true |
| root/Body/Commands/Confirm/ConfirmTxt | `props.text` | expr | `{view.custom.pendingCmd} + " " + {view.custom.s.scale} + "?"` | Text content |
| root/Body/Commands/Confirm/Cancel | `props.enabled` | expr | `{view.custom.level} >= 1` | Enabled while expression is true |
| root/Body/Commands/Confirm/ConfirmBtn | `props.enabled` | expr | `{view.custom.level} >= 1` | Enabled while expression is true |
| root/Body/Commands/Foot | `props.text` | property | `view.custom.s.foot` | Text content |

## Scripts reference

Total: **9 scripts**: 7 event scripts (6 `component.onActionPerformed`, 1 `dom.onClick`) and 2 transform scripts (`custom.s` and `custom.level`). No `customMethods`, no `messageHandlers`, no property-change `onChange` scripts.

The button handlers below call no `efc.ui` command functions. The Tare, Zero, Reset and Select writes are made directly with `system.tag.writeBlocking`. The derived state transform is explained after the list.

1. **`root/Header/Close`**: `events.dom.onClick`, scope G.

```python
	efc.ui.closeDynamic(self)
```

2. **`root/Body/Status/ChipRow/Select`**: `events.component.onActionPerformed`, scope G.

```python
	# Momentary pulse: set the PLC bit, release it 1 s later (harmless if the PLC clears it first).
	path = self.view.params.tagPath + "/Cmd_Select"
	system.tag.writeBlocking([path], [True])
	def _release(p=path):
		import time
		time.sleep(1.0)
		system.tag.writeBlocking([p], [False])
	system.util.invokeAsynchronous(_release)
```

3. **`root/Body/Commands/Buttons/Tare`**: `events.component.onActionPerformed`, scope G.

```python
	self.view.custom.pendingCmd = "Tare"
```

4. **`root/Body/Commands/Buttons/Zero`**: `events.component.onActionPerformed`, scope G.

```python
	self.view.custom.pendingCmd = "Zero"
```

5. **`root/Body/Commands/Buttons/Reset`**: `events.component.onActionPerformed`, scope G.

```python
	self.view.custom.pendingCmd = "Reset"
```

6. **`root/Body/Commands/Confirm/Cancel`**: `events.component.onActionPerformed`, scope G.

```python
	self.view.custom.pendingCmd = ""
```

7. **`root/Body/Commands/Confirm/ConfirmBtn`**: `events.component.onActionPerformed`, scope G.

```python
	cmd = self.view.custom.pendingCmd
	self.view.custom.pendingCmd = ""
	member = {"Tare": "Cmd_Tare", "Zero": "Cmd_Zero", "Reset": "Cmd_Reset"}.get(cmd)
	if member:
		path = self.view.params.tagPath + "/" + member
		system.tag.writeBlocking([path], [True])
		def _release(p=path):
			import time
			time.sleep(1.0)
			system.tag.writeBlocking([p], [False])
		system.util.invokeAsynchronous(_release)
```

8. **transform on `(view root)` `custom.s`**: property `view.custom.t`, script transform (the derived state map, explained below).

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

9. **transform on `(view root)` `custom.level`**: `custom.level` binding, `property` source `session.props.auth.user.roles`.

```python
	return efc.ui.level(value)
```

### Explanation of each handler

| Handler | Action | Writes | Role check | Audit |
|---|---|---|---|---|
| `Header/Close` (dom click) | `efc.ui.closeDynamic` restores the default region view | none | none | no |
| `Status/ChipRow/Select` | pulses `Cmd_Select`: True now, False after 1 s, on a background thread | `Cmd_Select` | enable only: level 1 and not `Disabled` | no |
| `Commands/Buttons/Tare` | sets `pendingCmd` = `Tare`, which shows the confirm strip | none (confirm writes) | enable only: level 1 and not `tzLocked` | no |
| `Commands/Buttons/Zero` | sets `pendingCmd` = `Zero` | none (confirm writes) | enable only: level 1 and not `tzLocked` | no |
| `Commands/Buttons/Reset` | sets `pendingCmd` = `Reset` | none (confirm writes) | enable only: level 1 and not `resetLocked` | no |
| `Commands/Confirm/Cancel` | clears `pendingCmd` | none | enable only: level 1 | no |
| `Commands/Confirm/ConfirmBtn` | clears `pendingCmd`, writes the matching command True, then False after 1 s | `Cmd_Tare`, `Cmd_Zero` or `Cmd_Reset` | enable only: level 1 | no |
| `custom.s` transform | derives the state map from `custom.t` (below) | `view.custom.s` | none | no |
| `custom.level` transform | `efc.ui.level(value)` | `view.custom.level` | none | no |

### Derived state transform (`custom.s`)

- Input: `value` is the `custom.t` dictionary. A missing or null key falls back to a default: `g` returns the given default, `b` returns false and `f` returns 0.0.
- Status word and chip, first match wins: Disabled (`DISABLED`, `State/OutOfService`), Failed (`FAULT`, `State/Fault`), Complete (`COMPLETE`, `State/Stopped`), Filling (`FILLING`), SampleCMD (`SAMPLING`), Vacuuming (`VACUUMING`, `State/Transition`), Venting (`VENTING`, `State/Transition`), Recovering (`RECOVERING`, `State/Transition`), Active (`ACTIVE`), ReadyToStart or ReadyToFill (`READY`, `State/Stopped`), else `IDLE`.
- `busy` is true only for the chips `State/Running` and `State/Transition`. It drives the Tare and Zero lock.
- `msg` is `Msg` when it has text, otherwise the status text for that chip (for example "Filling primary vessel"). `units` is `Units`, or `kg` when it is blank, `---`, `null` or `None`.
- Weights: `scale` = target x 1.08 (the bar is drawn to 108 % of target). `pct` is net / target as a percentage, prefixed `OVER` when net > target + deadband. `fillCls` is `Bar/FillAlarm` when over, else `Bar/Fill`. `fillW` = net / scale, clamped to 0..1. `tgtX` marks the target and `dbX`/`dbW` draw the deadband band at (target - deadband) / scale with width 2 x deadband / scale (minimum 0.012 when a target is set). `rem` = max(0, target - net).
- Pressure: `pt` is shown as `#,##0.0`, or `-----` with the class `Value/BadQuality` when `PT_Valid` is false. `pscale` = Press_Max x 1.1. `ptW` = PT / pscale. `preX` marks the prefill pressure and `maxX` the maximum. `ptd` = "dP x psi" from `PT_Diff`.
- Step strip (six steps: Vessel, Vac, Prefill, Fill, Sample, Done). Each step is 0 Pending, 1 Active, 2 Done. Vessel is Done when `Vessel_Present`. Vac is Done when `Vacuumed`, Active when `Vacuuming`. Prefill is Done when `Press_Balanced`, Active when Active and Vacuumed and not Filling. Fill is Done when Complete or SampleCMD, Active when Filling. Sample is Done when Complete, Active when SampleCMD. Done is Done when Complete. When Disabled every step is 0. When Failed, the first step that is not Done is set to 3 (Fault, `Station/Step/Fault`).
- Permissive LEDs (Vessel present, PT valid, Press balanced, Ready to start, Ready to fill) are on or off from their flags. Valve LEDs: REQ and CMD for Inlet, Sample and Vacuum. The `I` marker (`inIlk`, `smIlk`, `vaIlk`) shows when REQ is on and CMD is off.
- `tzLocked` = `busy` or `Disabled`. Tare and Zero are locked by it. `resetLocked` = not (Complete or Failed). Reset is enabled only in those two states. `foot` = "Station disabled: commands unavailable", else "Tare and Zero locked while active" when `tzLocked`, else empty.

### Library functions used (`projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.level(roles)`**: highest index of the role in `['Guest','Operator','Maintenance','Supervisor','Engineer','Admin']`, or 0. Bound to `custom.level`.
- **`efc.ui.closeDynamic(component)`**: writes `efcDw[pageId]` back to the stored `default` path and params. Writes no tags.
- Not used by this view: `efc.ui.cmd` and `efc.ui.ackAll`. The command and setpoint writes are direct tag writes (see the notes).
- Ignition built-ins used directly: `system.tag.writeBlocking`, `system.util.invokeAsynchronous`, and Python `time.sleep` on the release thread.

## Tag members used

All paths are relative to `tagPath`. Types and comments come from `types/PCLib_Members.csv` (type `T_Station`, Equipment module). Members the faceplate reads through `custom.t` are read-only; the setpoints are bidirectional; the four commands are pulses.

| Member | Access (read/write) | Data type | Meaning (PCLib comment) |
|---|---|---|---|
| `Sts_Active` | read | BOOL | Station in a fill cycle |
| `Sts_Complete` | read | BOOL | Fill complete |
| `Prm_Deadband` | read/write (bidirectional) | REAL | Fill deadband, net weight (operator setpoint) |
| `Sts_Disabled` | read | BOOL | Station disabled |
| `Sts_Failed` | read | BOOL | Fill failed - reset required |
| `Sts_Filling` | read | BOOL | Filling |
| `Val_Gross` | read | REAL | Gross weight (Cfg_EU) |
| `Out_InletCmd` | read | BOOL | Inlet valve command |
| `Sts_InletReq` | read | BOOL | Sequence requests the inlet valve open |
| `Sts_Msg` | read | STRING[40] | Status message for the HMI |
| `Val_Net` | read | REAL | Net weight (Cfg_EU) |
| `Sts_PressBalanced` | read | BOOL | Vessel and header pressures balanced |
| `Prm_MaxPress` | read/write (bidirectional) | REAL | Maximum vessel pressure during fill (operator setpoint) |
| `Val_PT` | read | REAL | Vessel pressure |
| `Val_PTDiff` | read | REAL | Vessel minus header pressure |
| `Inp_PTValid` | read | BOOL | Pressure reading valid |
| `Sts_ReadyToFill` | read | BOOL | Ready to fill |
| `Sts_ReadyToStart` | read | BOOL | Ready to start (all start permissives) |
| `Sts_Recovering` | read | BOOL | Recovering |
| `Out_SampleCmd` | read | BOOL | Sample valve command |
| `Prm_PrefillPress` | read/write (bidirectional) | REAL | Prefill pressure (operator setpoint). Mapped from `custom.t.SamplePress`. |
| `Sts_SampleReq` | read | BOOL | Sequence requests the sample valve open |
| `Prm_SampleWt` | read/write (bidirectional) | REAL | Sample draw weight (operator setpoint) |
| `Cfg_ScaleName` | read | STRING[20] | Scale tag shown on the HMI, e.g. WT-101 |
| `Sts_Selected` | read | BOOL | Station selected |
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Val_Tare` | read | REAL | Tare weight (Cfg_EU) |
| `Prm_TargetWt` | read/write (bidirectional) | REAL | Fill target, net weight (operator setpoint) |
| `Val_Total` | read | REAL | Total filled this cycle (Cfg_EU) |
| `Cfg_EU` | read | STRING[8] | Weight units text (kg, lb) |
| `Out_VacuumCmd` | read | BOOL | Vacuum valve command |
| `Sts_Vacuumed` | read | BOOL | Vessel evacuated |
| `Sts_Vacuuming` | read | BOOL | Evacuating the vessel |
| `Sts_VacuumReq` | read | BOOL | Sequence requests the vacuum valve open |
| `Sts_Venting` | read | BOOL | Venting |
| `Inp_VesselPresent` | read | BOOL | Vessel detected on the station |
| `Cmd_Select` | write (1 s pulse) | BOOL | Select this station (one-shot) |
| `Cmd_Tare` | write (1 s pulse) | BOOL | Tare the scale (one-shot; blocked while active) |
| `Cmd_Zero` | write (1 s pulse) | BOOL | Zero the scale (one-shot; blocked while active) |
| `Cmd_Reset` | write (1 s pulse) | BOOL | Reset a failed / complete station (one-shot) |

## Component tree

```
- `root` (ia.container.flex)
  - `Header` (ia.container.flex)
    - `Titles` (ia.container.flex)
      - `Name` (ia.display.label)
      - `Scale` (ia.display.label)
    - `Close` (ia.display.icon)
  - `Body` (ia.container.flex)
    - `Status` (ia.container.flex)
      - `ChipRow` (ia.container.flex)
        - `Chip` (ia.display.label)
        - `Sp` (ia.display.label)
        - `Select` (ia.input.button)
      - `Msg` (ia.display.label)
      - `Steps` (ia.container.flex)
        - `Step0` (ia.container.flex)
          - `Seg` (ia.display.label)
          - `Txt` (ia.display.label)
        - `Step1` (ia.container.flex)
          - `Seg` (ia.display.label)
          - `Txt` (ia.display.label)
        - `Step2` (ia.container.flex)
          - `Seg` (ia.display.label)
          - `Txt` (ia.display.label)
        - `Step3` (ia.container.flex)
          - `Seg` (ia.display.label)
          - `Txt` (ia.display.label)
        - `Step4` (ia.container.flex)
          - `Seg` (ia.display.label)
          - `Txt` (ia.display.label)
        - `Step5` (ia.container.flex)
          - `Seg` (ia.display.label)
          - `Txt` (ia.display.label)
    - `Weight` (ia.container.flex)
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
        - `DbL` (ia.display.label)
        - `Db` (ia.display.label)
      - `Boxes` (ia.container.flex)
        - `Gross` (ia.container.flex)
          - `GrossLbl` (ia.display.label)
          - `GrossRow` (ia.container.flex)
            - `GrossVal` (ia.display.label)
        - `Tare` (ia.container.flex)
          - `TareLbl` (ia.display.label)
          - `TareRow` (ia.container.flex)
            - `TareVal` (ia.display.label)
        - `Total` (ia.container.flex)
          - `TotalLbl` (ia.display.label)
          - `TotalRow` (ia.container.flex)
            - `TotalVal` (ia.display.label)
    - `Pressure` (ia.container.flex)
      - `PHead` (ia.container.flex)
        - `PLbl` (ia.display.label)
        - `Ptd` (ia.display.label)
      - `PRow` (ia.container.flex)
        - `Pt` (ia.display.label)
        - `PtU` (ia.display.label)
        - `Sp3` (ia.display.label)
        - `PtBad` (ia.display.label)
      - `PtBar` (ia.container.coord)
        - `Fill` (ia.display.label)
        - `Prefill` (ia.display.label)
        - `Max` (ia.display.label)
      - `PCap` (ia.container.flex)
        - `PreL` (ia.display.label)
        - `Pre` (ia.display.label)
        - `Sp4` (ia.display.label)
        - `MaxL` (ia.display.label)
        - `Max` (ia.display.label)
    - `PermIO` (ia.container.flex)
      - `Perms` (ia.container.flex)
        - `PermLbl` (ia.display.label)
        - `Perm0` (ia.container.flex)
          - `Led` (ia.display.label)
          - `Txt` (ia.display.label)
        - `Perm1` (ia.container.flex)
          - `Led` (ia.display.label)
          - `Txt` (ia.display.label)
        - `Perm2` (ia.container.flex)
          - `Led` (ia.display.label)
          - `Txt` (ia.display.label)
        - `Perm3` (ia.container.flex)
          - `Led` (ia.display.label)
          - `Txt` (ia.display.label)
        - `Perm4` (ia.container.flex)
          - `Led` (ia.display.label)
          - `Txt` (ia.display.label)
      - `Valves` (ia.container.flex)
        - `ValveLbl` (ia.display.label)
        - `VHead` (ia.container.flex)
          - `B` (ia.display.label)
          - `Req` (ia.display.label)
          - `Cmd` (ia.display.label)
        - `V_Inlet` (ia.container.flex)
          - `Name` (ia.container.flex)
            - `Txt` (ia.display.label)
            - `Ilk` (ia.display.label)
          - `Req` (ia.container.flex)
            - `Led` (ia.display.label)
          - `Cmd` (ia.container.flex)
            - `Led` (ia.display.label)
        - `V_Sample` (ia.container.flex)
          - `Name` (ia.container.flex)
            - `Txt` (ia.display.label)
            - `Ilk` (ia.display.label)
          - `Req` (ia.container.flex)
            - `Led` (ia.display.label)
          - `Cmd` (ia.container.flex)
            - `Led` (ia.display.label)
        - `V_Vacuum` (ia.container.flex)
          - `Name` (ia.container.flex)
            - `Txt` (ia.display.label)
            - `Ilk` (ia.display.label)
          - `Req` (ia.container.flex)
            - `Led` (ia.display.label)
          - `Cmd` (ia.container.flex)
            - `Led` (ia.display.label)
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
      - `SpRow2` (ia.container.flex)
        - `SpDb` (ia.container.flex)
          - `SpDbLbl` (ia.display.label)
          - `SpDbRow` (ia.container.flex)
            - `SpDbFld` (ia.input.numeric-entry-field)
            - `SpDbU` (ia.display.label)
        - `SpBlank4` (ia.display.label)
    - `Commands` (ia.container.flex)
      - `Buttons` (ia.container.flex)
        - `Tare` (ia.input.button)
        - `Zero` (ia.input.button)
        - `Reset` (ia.input.button)
      - `Confirm` (ia.container.flex)
        - `ConfirmTxt` (ia.display.label)
        - `Cancel` (ia.input.button)
        - `ConfirmBtn` (ia.input.button)
      - `Foot` (ia.display.label)
```

## Notes and open questions

- **Reset can be enabled while the station is disabled.** `resetLocked` is `not (Complete or Failed)` and does not test `Disabled`. Select, the setpoints, Tare and Zero do check `Disabled`. If `Sts_Failed` and `Sts_Disabled` are both true, Reset is enabled and the chip shows DISABLED.
- **Tare and Zero stay enabled during a fault and at idle.** `tzLocked` is `busy` or `Disabled`, and `busy` only counts the Running and Transition chips. Tare and Zero are therefore enabled in FAULT, COMPLETE, READY and IDLE. The foot line says "Tare and Zero locked while active", which matches only the active states. Confirm that enabling them during a fault is intended.
- **Commands and setpoints write tags directly.** Select, Tare, Zero, Reset and the five setpoints do not call `efc.ui.cmd`. Their only guard is the enable expression. There is no server-side level check and no audit. This conflicts with `steward/DECISIONS.md` decision 27 (writes go through `efc.ui.cmd`) and decision 20 (station setpoints are Operator+ and audit-logged). Decide as for `Docks/Loop`: route these writes through a role-checked, audited `efc.ui` function, or record the exception.
- **Setpoints can change during a fill.** The setpoint entries are enabled whenever the station is not disabled and the level is 1 or higher. Changing `Prm_TargetWt` during a fill moves the target marker, the deadband band, the remaining value and the percentage at once. Confirm that the PLC accepts a target change mid-fill.
- **Fill step is Done as soon as sampling starts.** Step 4 (Fill) is Done when `Sts_Complete` or `Out_SampleCmd` is true. If the sample valve opens before the fill is marked complete, the Fill segment shows Done early. Confirm this matches the sequence.
- **Pressure units are mixed.** The pressure value line, the prefill and max setpoint units and the marker labels are fixed text `psig`. The dP line says `psi` (`ptd` = "dP x psi"). Pick one unit, or take the unit from configuration (`Cfg_EU` is the weight unit, and no pressure unit member exists in T_Station).
- **Command pulses.** Select, Tare, Zero and Reset write True and then write False 1 s later. A PLC that reads these as a level, not a one-shot, will see a 1 s pulse. The PCLib comments call them one-shot (for example "Tare the scale (one-shot; blocked while active)").
- **Members the faceplate does not show.** No alarm rows (`Alm_Failed`, `Alm_OverFill`, `Alm_PressHi`, `Alm_ScaleFault`), no scale health (`Inp_ScaleOK`), no NE107 diagnostic (`Sts_NE107`), no SIM chip (`Sts_Sim`) and no simulation toggle (`Sim_En`). `Sts_State` (the PCLib state enumeration) is not read; the status comes from the flags. `Mode` and `Perm` are not used. Confirm the faceplate does not have to show these.
- **Derived state refresh.** All derived values come from one property binding on `custom.t`. `docs/station-faceplates.md` lists as an open item whether the binding recalculates when one member changes. The view file cannot show this. Confirm on the gateway.
- **Stale faceplate doc.** `docs/station-faceplates.md` describes a 300 x 800 sidebar opened with `system.perspective.openDock("StationSidebar")`, command pulses named `TareCMD`, `ZeroCMD`, `HMI_Reset` and `HMI_Select`, and a `DDT_Station` type. The built dock is 400 x 860, opened by `efc.ui.openDynamic` as `dw_Station`, and writes the T_Station members `Cmd_Tare`, `Cmd_Zero`, `Cmd_Reset` and `Cmd_Select`. Update that document.
- **Prefill setpoint naming.** The view binds `custom.t.SamplePress` to `Prm_PrefillPress`, and the Prefill setpoint writes that member. The PCLib comment says `Prm_PrefillPress` is the prefill pressure, which matches the label. The `SamplePress` name in `station-faceplates.md` is a leftover; the open item there is resolved by the PCLib comment, but the gateway tag mapping still needs checking.
- **No scroll on the root.** The root has `Util/Clip` and no `Container/Scroll`. At 860 px, any content taller than that is clipped. Check the layout on the gateway at 1080p.
- **Built from the imported project.** Edits belong in `imported/EFC_StationFaceplates`, followed by `steward/tools/fix_station.py` and a `build.py` run. The `build_station.py` generator named in `station-faceplates.md` is not in the repo.
- **Related help pages.** The Overview links `Templates/Station/Station_Tile.md`, which exists in `docs/help`. `Station_Fill.md` is not linked from this file.
