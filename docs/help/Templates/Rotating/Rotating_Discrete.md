# Rotating equipment templates (two-state drives)

Covers `Templates/Rotating/Agitator`, `Templates/Rotating/Blower`, `Templates/Rotating/Compressor_Centrifugal`, `Templates/Rotating/Compressor_Diaphragm`, `Templates/Rotating/Motor`, `Templates/Rotating/Pump_Centrifugal`, `Templates/Rotating/Pump_Diaphragm`, `Templates/Rotating/Pump_PD_Rotary`, `Templates/Rotating/Pump_Reciprocating`, `Templates/Rotating/Pump_Vacuum` and `Templates/HeatTransfer/HX_AirCooled`.
Sources: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/Rotating/<name>/view.json` and `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/HeatTransfer/HX_AirCooled/view.json`.
Reference view: `Templates/Rotating/Motor`. Sections below describe Motor. The differences table lists how each other view differs.
Dynamic window they open: `Templates/Dynamic Window/Rotating/Rotating` (see [Rotating](../Dynamic%20Window/Rotating/Rotating.md)).

## Overview

These are single-device symbols for a two-state drive (T_Motor): start/stop with run feedback and a run output. Each shows the run state as a fill colour, an alarm or fault outline, P and I badges, a status line (STOPPED, RUNNING, STARTING, STOPPING or FAULT), an M label, and a Start/Stop button in manual mode. The family shares one set of params, custom properties, bindings, scripts and tag members. The views differ in symbol geometry, default `tagPath`, `custom.lw` values, which SVG elements are bound, and (for two views) the `I` badge position. See the differences table.

- **Default size:** 120 x 116 (`props.defaultSize`) for all 11 views.
- **Bound to:** one T_Motor instance through `params.tagPath`. The default `tagPath` is per view (see the table).
- **Opening the dock:** a single click on the symbol runs `efc.ui.openDynamic(self)`. It maps `tType` (`T_Motor`, via BY_TYPE) to `dw_Rotating`, then loads that window into the page's `dw_Right` dock with `params:{tagPath}` and opens the dock. The `dw_Right` dock then shows `Templates/Dynamic Window/Rotating/Rotating`. Only `tagPath` is passed on; `dwTagPath` overrides it when set.
- **Touch mode:** with `useButton = false` and `dblCmd = true`, a double-tap runs `efc.ui.dblCmd(self)`. See How it operates.
- **Generated view:** `Templates/Dynamic Window/Rotating/Rotating` is written by `generator/docks/build_docks.py` (`rotating()`). The templates in this family are not generated.

### Differences between the views

| View | Default size | Default `tagPath` | `custom.lw` normal / alarm | Symbol `viewBox` | Symbol geometry | `I` badge (x / y) |
|---|---|---|---|---|---|---|
| `Motor` (reference) | 120 x 116 | `[default]PID_Demo/P101` | 3.75 / 7.5 | 0 0 100 100 | Circle r34 with an "M" mark. Inner mark has no fill. | 0.8333 / 0.1897 |
| `Agitator` | 120 x 116 | `[default]PID_Demo/P101` | 3.0 / 6.0 | 0 0 100 100 | Circle r14 at the top with an "M" mark, a vertical shaft and a crossed blade pair below (shaft and blades unbound). | 0.8333 / 0.1897 |
| `Blower` | 120 x 116 | `[default]PID_Demo/B301` | 2.679 / 5.357 | 0 0 100 100 | Volute casing with a three-spoke impeller and a filled hub. | 0.8333 / 0.5345 |
| `Compressor_Centrifugal` | 120 x 116 | `[default]PID_Demo/K202` | 2.344 / 4.688 | 0 0 100 100 | Tapered (funnel) casing, taller at its left edge, with a horizontal centre bar. | 0.8333 / 0.1897 |
| `Compressor_Diaphragm` | 120 x 116 | `[default]PID_Demo/K201` | 2.344 / 4.688 | 0 0 100 100 | Circle r38 with two diagonal strokes. Dark grey pipe stubs left and right (fixed #333333, unbound). | 0.8333 / 0.1897 |
| `Pump_Centrifugal` | 120 x 116 | `[default]PID_Demo/P101` | 2.679 / 5.357 | 0 0 100 100 | Volute casing with discharge nozzle, a base (fixed #EBEBEB) and a filled hub. Pipe stubs (unbound). | 0.8333 / 0.5345 |
| `Pump_Diaphragm` | 120 x 116 | `[default]PID_Demo/P101` | 2.679 / 5.357 | 0 0 100 100 | Circle r28 with a diaphragm arc and an arrow. Rectangular ports left and right. Base (fixed #EBEBEB). | 0.8333 / 0.1897 |
| `Pump_PD_Rotary` | 120 x 116 | `[default]PID_Demo/P102` | 2.679 / 5.357 | 0 0 100 100 | Circle r28 with two circles r9. Rectangular ports left and right. Base (fixed #EBEBEB). | 0.8333 / 0.1897 |
| `Pump_Reciprocating` | 120 x 116 | `[default]PID_Demo/P101` | 3.0 / 6.0 | 0 0 120 100 | Rectangular cylinder 60 x 40 with a plunger rod, a crank-end circle r12 (fixed #EBEBEB) and a base. Shaft line (unbound). | 0.8333 / 0.1897 |
| `Pump_Vacuum` | 120 x 116 | `[default]PID_Demo/PV501` | 2.344 / 4.688 | 0 0 100 100 | Circle r38 with two diagonal strokes and a circle r7 mark. Pipe stubs (unbound). | 0.8333 / 0.1897 |
| `HX_AirCooled` | 120 x 116 | `[default]PID_Demo/P101` | 2.5 / 5.0 | 0 0 140 110 | Rectangular header 120 x 24 (fixed #EBEBEB) with a zig-zag line across it (unbound), above a fan circle r18 with a three-blade mark. Connecting and base lines (unbound). `tType` is `T_Motor`, see Notes. | 0.8333 / 0.1897 |

The SVG element bindings differ by view. Each row below is one element of the view's `root/Symbol`, with what drives its fill, stroke paint and stroke width. A "fixed" value is set in the view and not bound. Element indices are the view's own (they are not the same across views).

| View | Index | Element (type) | Fill paint | Stroke paint | Stroke width |
|---|---|---|---|---|---|
| `Motor` | 0 | `state0` (circle) | `custom.fill` | `custom.line` | `custom.lw` |
| `Motor` | 1 | `cstroke1` (path) | fixed transparent | `custom.con` | fixed 3.75 |
| `Agitator` | 0 | `detail0` (path) | fixed transparent | fixed `#262626` | fixed 2.0 |
| `Agitator` | 1 | `detail1` (path) | fixed transparent | fixed `#262626` | fixed 2.0 |
| `Agitator` | 2 | `state2` (circle) | `custom.fill` | `custom.line` | `custom.lw` |
| `Agitator` | 3 | `cstroke3` (path) | fixed transparent | `custom.con` | fixed 3.0 |
| `Blower` | 0 | `state0` (path) | `custom.fill` | `custom.line` | `custom.lw` |
| `Blower` | 1 | `cstroke1` (path) | fixed transparent | `custom.con` | fixed 2.679 |
| `Blower` | 2 | `cfill2` (circle) | `custom.con` | fixed `transparent` | fixed 0 |
| `Compressor_Centrifugal` | 0 | `state0` (path) | `custom.fill` | `custom.line` | `custom.lw` |
| `Compressor_Centrifugal` | 1 | `cstroke1` (path) | fixed transparent | `custom.con` | fixed 2.344 |
| `Compressor_Diaphragm` | 0 | `pipe0` (path) | fixed transparent | fixed `#333333` | fixed 3.125 |
| `Compressor_Diaphragm` | 1 | `state1` (circle) | `custom.fill` | `custom.line` | `custom.lw` |
| `Compressor_Diaphragm` | 2 | `cstroke2` (path) | fixed transparent | `custom.con` | fixed 1.562 |
| `Pump_Centrifugal` | 0 | `pipe0` (path) | fixed transparent | fixed `#333333` | fixed 3.571 |
| `Pump_Centrifugal` | 1 | `body1` (path) | fixed #EBEBEB | `custom.line` | `custom.lw` |
| `Pump_Centrifugal` | 2 | `state2` (path) | `custom.fill` | `custom.line` | `custom.lw` |
| `Pump_Centrifugal` | 3 | `cfill3` (circle) | `custom.con` | fixed `transparent` | fixed 0 |
| `Pump_Diaphragm` | 0 | `state0` (rect) | `custom.fill` | `custom.line` | `custom.lw` |
| `Pump_Diaphragm` | 1 | `state1` (rect) | `custom.fill` | `custom.line` | `custom.lw` |
| `Pump_Diaphragm` | 2 | `state2` (circle) | `custom.fill` | `custom.line` | `custom.lw` |
| `Pump_Diaphragm` | 3 | `cstroke3` (path) | fixed transparent | `custom.con` | fixed 2.679 |
| `Pump_Diaphragm` | 4 | `cstroke4` (path) | fixed transparent | `custom.con` | fixed 2.679 |
| `Pump_Diaphragm` | 5 | `body5` (path) | fixed #EBEBEB | `custom.line` | `custom.lw` |
| `Pump_PD_Rotary` | 0 | `state0` (rect) | `custom.fill` | `custom.line` | `custom.lw` |
| `Pump_PD_Rotary` | 1 | `state1` (rect) | `custom.fill` | `custom.line` | `custom.lw` |
| `Pump_PD_Rotary` | 2 | `state2` (circle) | `custom.fill` | `custom.line` | `custom.lw` |
| `Pump_PD_Rotary` | 3 | `cstroke3` (circle) | fixed transparent | `custom.con` | fixed 2.679 |
| `Pump_PD_Rotary` | 4 | `cstroke4` (circle) | fixed transparent | `custom.con` | fixed 2.679 |
| `Pump_PD_Rotary` | 5 | `body5` (path) | fixed #EBEBEB | `custom.line` | `custom.lw` |
| `Pump_Reciprocating` | 0 | `detail0` (path) | fixed transparent | fixed `#262626` | fixed 2.0 |
| `Pump_Reciprocating` | 1 | `body1` (circle) | fixed #EBEBEB | `custom.line` | `custom.lw` |
| `Pump_Reciprocating` | 2 | `state2` (rect) | `custom.fill` | `custom.line` | `custom.lw` |
| `Pump_Reciprocating` | 3 | `cfill3` (rect) | `custom.con` | fixed `transparent` | fixed 0 |
| `Pump_Reciprocating` | 4 | `body4` (path) | fixed #EBEBEB | `custom.line` | `custom.lw` |
| `Pump_Vacuum` | 0 | `pipe0` (path) | fixed transparent | fixed `#333333` | fixed 3.125 |
| `Pump_Vacuum` | 1 | `state1` (circle) | `custom.fill` | `custom.line` | `custom.lw` |
| `Pump_Vacuum` | 2 | `cstroke2` (path) | fixed transparent | `custom.con` | fixed 1.562 |
| `Pump_Vacuum` | 3 | `cstroke3` (circle) | fixed transparent | `custom.con` | fixed 2.344 |
| `HX_AirCooled` | 0 | `body0` (rect) | fixed #EBEBEB | `custom.line` | `custom.lw` |
| `HX_AirCooled` | 1 | `detail1` (path) | fixed transparent | fixed `#262626` | fixed 1.667 |
| `HX_AirCooled` | 2 | `detail2` (path) | fixed transparent | fixed `#262626` | fixed 1.667 |
| `HX_AirCooled` | 3 | `state3` (circle) | `custom.fill` | `custom.line` | `custom.lw` |
| `HX_AirCooled` | 4 | `cstroke4` (path) | fixed transparent | `custom.con` | fixed 2.5 |
| `HX_AirCooled` | 5 | `detail5` (path) | fixed transparent | fixed `#262626` | fixed 1.667 |

Where a stroke width is fixed, the mark does not thicken on alarm. Only the outline (`custom.lw`) does. Symbol elements that show a fixed colour are not bound to any state.

Apart from the rows above, the default `tagPath`, the `custom.lw` values and the `I` badge position, the 11 views are identical. Their params, custom properties (including all expressions other than `custom.lw`), view and component bindings (other than `root/Symbol`), scripts and component trees match Motor. The rest of this document applies to all of them.

## How it operates

**Body colour (state).** The state body takes `custom.fill` from `custom.state`:

| State | Derived from | Body colour | Status text | Status class |
|---|---|---|---|---|
| 0 | `Sts_Stopped` (after the checks for 1 and 3) | #9E9E9E | STOPPED | `State/Stopped` |
| 1 | `Sts_Running` | #FFFFFF | RUNNING | `State/Running` |
| 2 | neither | #C4C4C4 | STARTING if `Out_Run` is true, else STOPPING | `State/Transition` |
| 3 | `Sts_Fault` or `Sts_Tripped` (checked first) | #3A3A3A | FAULT | `State/Fault` |

Priority is fault or trip, then running, then stopped, then transition. STARTING or STOPPING is chosen from `Out_Run` (the run command), not from `Sts_Starting` or `Sts_Stopping`. Those two members exist in T_Motor but this template does not read them.

**Inner mark colour.** `custom.con` (the inner mark stroke or fill) is #F2F2F2 when `state` is 3 and #262626 otherwise.

**Alarm and fault outline.** `custom.line` is #D50000 when faulted. Otherwise it follows the highest active alarm class under `<tagPath>/*`: 1 cyan #00A3E0, 2 yellow #FFD200, 3 orange #FF7A00, 4 red #D50000. Default #262626. `custom.lw` is the view's normal width when no alarm is active and not faulted, and the alarm width when one is (see the differences table). Diagnostic (0) alarms do not change the outline.

**Badges.** `P` is shown when `Sts_NotPerm` is true. `I` is shown when `Sts_Intlk` is true, with the tooltip "Interlock active - start blocked" followed by the first-out condition text, if one exists.

**Mode and status line.** With `useButton = true` (default) the `M` label is hidden. With `useButton = false` (touch mode) the `M` label is shown while in MAN, and the status text gets the `Mode/ManualJoined` class.

**Name and tooltip.** The label shows `Cfg_Tag`, or the last segment of tagPath if `Cfg_Tag` is empty. The tooltip shows `Cfg_Desc`, if non-empty.

**Start/Stop button (`PB`).** Visible when `useButton` is true and the drive is in MAN. Enabled when `custom.canCmd` is true: MAN, available, not local, not OOS, and either a stop is pending (`cmd`) or the drive is not permissive-missing and not interlocked. The tooltip is "Stop" when `cmd` (`Out_Run`) is true, otherwise "Start". A click writes `Cmd_Stop` if `Out_Run` is true, otherwise `Cmd_Start`, with `True`.

**Touch mode (double-tap).** With `useButton = false` and `dblCmd = true`, a double-click on the symbol calls `efc.ui.dblCmd(self)`. For T_Motor that function acts only when the user is Operator (level 1) or higher, and all of these hold: `Mode/Sts_Man` and `Sts_Avail` are true, and `Sts_Intlk`, `Sts_NotPerm`, `Sts_Local` and `Sts_Fault` are false. It then writes `Cmd_Stop` if `Sts_Running` is true, otherwise `Cmd_Start`.

**Security.** The `PB` script calls `efc.ui.cmd(self, m, True, 1)`, which re-checks that the user is Operator (level 1) or higher before writing, with no audit record. The enable expression is a second guard. The double-tap path checks for Operator or higher but also writes no audit record. Neither path checks `Sts_Tripped` (see Notes).

## Properties reference

### View parameters (`params`)

The same six params on all 11 views. Only the default `tagPath` differs (see the differences table).

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | per view (see differences table) | T_Motor instance. All bindings use it as `{view.params.tagPath}`. | Caller; read by bindings and `efc.ui` |
| `useButton` | input | `true` | `true` shows the `PB` command button; `false` enables touch mode (M label, double-tap). | Caller; read by bindings and `efc.ui.dblCmd` |
| `tType` | input | `T_Motor` | Type key. `efc.ui.openDynamic` uses it (via BY_TYPE) to pick the window. | Read by `efc.ui.openDynamic` and `efc.ui.dblCmd`; not referenced in this view's bindings |
| `dockId` | input | `""` | Overrides the window chosen from `tType`. Must be a key of `efc.ui.WINDOWS`. | Read by `efc.ui.openDynamic` only |
| `dwTagPath` | input | `""` | Tag path passed to the dock instead of `tagPath` (when non-empty). | Read by `efc.ui.openDynamic` only |
| `dblCmd` | input | `true` | Permits the double-tap command (checked in `efc.ui.dblCmd`). | Read by `efc.ui.dblCmd` only |

All six params have `paramDirection: input` and `persistent: true`. No output params.

### View-level custom properties (`custom`)

Motor, applied to all 11 views. Only `custom.lw`'s values differ, through the differences table.

**Tag mirrors.** Fifteen properties are plain tag mirrors. Each one is an indirect, read-only tag binding (no `bidirectional` flag, fallback delay 2.5 s) to `{view.params.tagPath}` plus the member below. The rest of the view reads drive state only through these mirrors.

| Group | Members |
|---|---|
| Run status | `custom.on` = `Sts_Running` (default `false`); `custom.off` = `Sts_Stopped` (default `true`); `custom.fault` = `Sts_Fault` (default `false`); `custom.trip` = `Sts_Tripped` (default `false`) |
| Run command | `custom.cmd` = `Out_Run` (default `false`). Read as the run command, so it drives STARTING/STOPPING and the `PB` action. |
| Mode | `custom.man` = `Mode/Sts_Man` (default `false`); `custom.oos` = `Mode/Sts_OOS` (default `false`) |
| Availability | `custom.avail` = `Sts_Avail` (default `true`); `custom.local` = `Sts_Local` (default `false`) |
| Interlock / permissive | `custom.intlk` = `Sts_Intlk` (default `false`); `custom.permMissing` = `Sts_NotPerm` (default `false`); `custom.firstOut` = `Intlk/Sts_FirstOut` (default `-1`); `custom.firstDesc` = `Intlk/Cfg_CondDesc/{firstOut}` (default `""`) |
| Config | `custom.name` = `Cfg_Tag` (default `""`); `custom.desc` = `Cfg_Desc` (default `""`) |

**Computed properties.** These are expressions. The table gives the full source.

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.state` | `0` | expr | `if(coalesce({view.custom.fault}, false) \|\| coalesce({view.custom.trip}, false), 3, if(coalesce({view.custom.on}, false), 1, if(coalesce({view.custom.off}, false), 0, 2)))` | 3 if fault or trip, 1 if running, 0 if stopped, else 2 (transition). Drives fill, status and outline width. |
| `view.custom.mode` | `0` | expr | `if(coalesce({view.custom.man}, false), 1, 0)` | 1/0 from `man`. Not referenced by any binding or script in any of the 11 views. |
| `view.custom.alarm` | `0` | expr | `if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 4, 4, 0, 1, 0), false), false)), 4, if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 3, 3, 0, 1, 0), false), false)), 3, if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 2, 2, 0, 1, 0), false), false)), 2, if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 1, 1, 0, 1, 0), false), false)), 1, 0))))` | Highest active alarm class 0-4 (4 checked first). Drives outline colour and width. |
| `view.custom.fill` | `"#9E9E9E"` | expr | `case({view.custom.state}, 0, "#9E9E9E", 1, "#FFFFFF", 2, "#C4C4C4", 3, "#3A3A3A", "#C4C4C4")` | Body colour from `state`. Bound to the state element of each view. |
| `view.custom.head` | `"#9E9E9E"` | expr | `if({view.custom.command} < 0, {view.custom.fill}, if({view.custom.command} = 1, "#FFFFFF", "#9E9E9E"))` | Would select a head colour from `command`. `command` is never bound (see Notes), so this always returns `fill`. Not referenced in any view. |
| `view.custom.line` | `"#262626"` | expr | `if({view.custom.state} = 3, "#D50000", case({view.custom.alarm}, 1, "#00A3E0", 2, "#FFD200", 3, "#FF7A00", 4, "#D50000", "#262626"))` | Outline colour: #D50000 when faulted or tripped; else by alarm class; default #262626. |
| `view.custom.con` | `"#262626"` | expr | `if({view.custom.state} = 3, "#F2F2F2", "#262626")` | Inner mark colour: #F2F2F2 when faulted or tripped, else #262626. |
| `view.custom.lw` | per view (see table) | expr | `if({view.custom.alarm} > 0 \|\| {view.custom.state} = 3, <alarm width>, <normal width>)` | Outline width. Motor: `7.5` and `3.75`. Other views use their own values (see the differences table). |
| `view.custom.canCmd` | `false` | expr | `coalesce({view.custom.man}, false) && coalesce({view.custom.avail}, true) && !coalesce({view.custom.local}, false) && !coalesce({view.custom.oos}, false) && (coalesce({view.custom.cmd}, false) \|\| (!coalesce({view.custom.permMissing}, false) && !coalesce({view.custom.intlk}, false)))` | True when man AND avail AND not local AND not oos AND (cmd OR (not permMissing AND not intlk)). Enables `PB`. Does not check `fault` or `trip`. |

The `lw` expression is the same in every view. Its constants come from the table above.

### Component-level custom properties

None. The components carry no `custom` properties.

### Session, page and message payloads

None. The views read no `session.*` or `page.*` values and send no messages. `efc.ui.openDynamic` changes the page's `dw_Right` dock (see the Scripts section). The PB and the double-tap path write tags only.

## Bindings reference

Motor (reference) total: **41 bindings**: 24 at view root (`custom.*`) and 17 on components. Types: 26 `expr`, 15 `tag`. No transforms. `params.*` entries have `paramDirection` only and are not bindings.

Totals for all 11 views (view root plus components):

| View | Bindings | Components | Scripts |
|---|---|---|---|
| `Motor` | 41 | 17 | 3 |
| `Agitator` | 41 | 17 | 3 |
| `Blower` | 42 | 18 | 3 |
| `Compressor_Centrifugal` | 41 | 17 | 3 |
| `Compressor_Diaphragm` | 41 | 17 | 3 |
| `Pump_Centrifugal` | 43 | 19 | 3 |
| `Pump_Diaphragm` | 50 | 26 | 3 |
| `Pump_PD_Rotary` | 50 | 26 | 3 |
| `Pump_Reciprocating` | 45 | 21 | 3 |
| `Pump_Vacuum` | 42 | 18 | 3 |
| `HX_AirCooled` | 43 | 19 | 3 |

The extra component bindings are all in `root/Symbol` (per-view element bindings) and, for Blower and Pump_Centrifugal, the `root/I` position (which is not a binding). The Symbol element rows are listed in the differences table. Each view's view-root bindings are the 24 listed for Motor.

### View root

The view-root bindings drive the custom properties. Each one is listed with its full source in **View-level custom properties** above.

### `root/Tag`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Tag | `props.text` | expr | `if(len(coalesce({view.custom.name}, "")) > 0, {view.custom.name}, substring({view.params.tagPath}, lastIndexOf({view.params.tagPath}, "/") + 1))` | Text content |
| root/Tag | `meta.tooltip.text` | expr | `coalesce({view.custom.desc}, "")` | Tooltip |
| root/Tag | `meta.tooltip.enabled` | expr | `len(coalesce({view.custom.desc}, "")) > 0` | Tooltip |

### `root/Symbol`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Symbol | `props.elements[0].fill.paint` | expr | `{view.custom.fill}` | State body fill colour |
| root/Symbol | `props.elements[0].stroke.paint` | expr | `{view.custom.line}` | State body outline colour |
| root/Symbol | `props.elements[0].stroke.width` | expr | `{view.custom.lw}` | State body outline width |
| root/Symbol | `props.elements[1].stroke.paint` | expr | `{view.custom.con}` | Inner mark colour |

Motor's Symbol has these four bindings. Other views bind different element indices (see the differences table).

### `root/P`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/P | `meta.visible` | expr | `coalesce({view.custom.permMissing}, false)` | Shown while expression is true |

### `root/I`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/I | `meta.visible` | expr | `coalesce({view.custom.intlk}, false)` | Shown while expression is true |
| root/I | `meta.tooltip.text` | expr | `"Interlock active - " + "start" + " blocked" + if(coalesce({view.custom.firstOut}, -1) >= 0 && len(coalesce({view.custom.firstDesc}, "")) > 0, ": " + {view.custom.firstDesc}, "")` | Tooltip |

### `root/StatusGroup`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/StatusGroup/M | `meta.visible` | expr | `!{view.params.useButton} && coalesce({view.custom.man}, false)` | Shown while expression is true |
| root/StatusGroup/M | `props.style.classes` | expr | `if(!{view.params.useButton} && coalesce({view.custom.man}, false), "Mode/ManualSplit", "Util/Collapsed")` | CSS class(es) selected by state |
| root/StatusGroup/Status | `props.text` | expr | `case({view.custom.state}, 0, "STOPPED", 1, "RUNNING", 2, if(coalesce({view.custom.cmd}, false), "STARTING", "STOPPING"), 3, "FAULT", "???")` | Text content |
| root/StatusGroup/Status | `props.style.classes` | expr | `case({view.custom.state}, 0, "State/Stopped", 1, "State/Running", 2, "State/Transition", 3, "State/Fault", "State/Unknown") + if(!{view.params.useButton} && coalesce({view.custom.man}, false), " Mode/ManualJoined", "")` | CSS class(es) selected by state |

### `root/PB`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/PB | `meta.visible` | expr | `{view.params.useButton} && coalesce({view.custom.man}, false)` | Shown while expression is true |
| root/PB | `props.enabled` | expr | `{view.custom.canCmd}` | Enabled while expression is true |
| root/PB | `meta.tooltip.text` | expr | `if(coalesce({view.custom.cmd}, false), "Stop", "Start")` | Tooltip |

## Scripts reference

Total: **3 event scripts** on every view (identical in all 11), no `customMethods`, no `messageHandlers`, no property-change scripts, no script transforms. `view.scripts` is absent.

1. **`root/Symbol`**: `events.dom.onClick` on `root/Symbol`, scope G.
   Opens the dynamic window for this tag. Calls `efc.ui.openDynamic`. No tag writes.

```python
	efc.ui.openDynamic(self)
```

2. **`root/Symbol`**: `events.dom.onDoubleClick` on `root/Symbol`, scope G.
   Touch-mode double-tap. Calls `efc.ui.dblCmd`. Writes one tag, only when the guards pass.

```python
	efc.ui.dblCmd(self)
```

3. **`root/PB`**: `events.component.onActionPerformed` on `root/PB`, scope G.
   Manual Start/Stop button. Writes `True` to `Cmd_Stop` if `Out_Run` is true, else to `Cmd_Start`, through `efc.ui.cmd(self, m, True, 1)`, which re-checks the Operator level (1) and writes the tag `<tagPath>/<m>`. No audit.

```python
	m = 'Cmd_Stop' if self.view.custom.cmd else 'Cmd_Start'
	efc.ui.cmd(self, m, True, 1)
```

### Library functions called by this family (`efc.ui`, `projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.openDynamic(component)`**: picks the window from `dockId`, or from `BY_TYPE[tType]`. For `T_Motor` that is `dw_Rotating`, which maps to `Templates/Dynamic Window/Rotating/Rotating`. If no window is found, it logs a warning and stops. Otherwise it loads it into the page's `dw_Right` dock with `params:{tagPath: dwTagPath or tagPath}` and opens the dock (`efc.ui.showDock`). It does not check the user's role and does not write to the tag.
- **`efc.ui.cmd(component, member, value, minLevel, audit)`**: returns unless the user's level is at least `minLevel`; otherwise writes `value` to `<tagPath>/<member>` and, with `audit=True`, writes an audit record. The PB button calls it with the chosen `Cmd_*` member, `True` and level 1, no audit.
- **`efc.ui.dblCmd(component)`**: returns immediately unless all of these hold: `useButton` false, `dblCmd` true, `tType` in `DBL_CMD` (`T_DValve` or `T_Motor`), and the user's level is 1 (Operator) or higher. It then reads `Sts_Running`, `Mode/Sts_Man`, `Sts_Avail`, `Sts_Intlk`, `Sts_NotPerm`, `Sts_Local` and `Sts_Fault`. It writes nothing unless `Mode/Sts_Man` and `Sts_Avail` are true and `Sts_Intlk`, `Sts_NotPerm`, `Sts_Local` and `Sts_Fault` are all false. When it does write, it sends `Cmd_Stop` if `Sts_Running` is true, else `Cmd_Start`, with `True`. It does not check `Mode/Sts_OOS` or `Sts_Tripped`, and it writes no audit record.
- **`efc.ui.level`**: the highest index in `['Guest','Operator','Maintenance','Supervisor','Engineer','Admin']` gives 0 to 5. Used by `dblCmd` (`userLevel >= 1`).
- **`efc.ui.closeDynamic`** is not called from these views. The dock's close button calls it.

## Tag members used

All paths are relative to `tagPath`. Types come from `types/PCLib_Members.csv` (type T_Motor, MTP `MonBinDrv`; nested types from T_Mode and T_Intlk).

| Member | Access | Data type | Meaning (PCLib comment) |
|---|---|---|---|
| `Cfg_Tag` | read | STRING[20] | Equipment / instrument tag, e.g. FT-101 |
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Out_Run` | read | BOOL | Run output to contactor / starter |
| `Sts_Running` | read | BOOL | Running (feedback confirmed) |
| `Sts_Stopped` | read | BOOL | Stopped (feedback confirmed) |
| `Sts_Fault` | read | BOOL | Any fault present |
| `Sts_Tripped` | read | BOOL | Tripped - reset required |
| `Sts_Avail` | read | BOOL | Available to Auto/program control |
| `Sts_Local` | read | BOOL | In local control |
| `Sts_Intlk` | read | BOOL | Interlock not healthy |
| `Sts_NotPerm` | read | BOOL | Permissive not healthy |
| `Mode/Sts_Man` | read | BOOL | In Manual (commanded by operator) - MTP Operator |
| `Mode/Sts_OOS` | read | BOOL | Out of service - MTP Offline |
| `Intlk/Sts_FirstOut` | read | INT | First condition to fail (-1 = none) |
| `Intlk/Cfg_CondDesc` | read (indexed by Sts_FirstOut) | ARRAY[0..15] OF STRING[32] | HMI text for condition n |
| `Cmd_Start` | write (PB, double-tap) | BOOL | Operator start (one-shot) |
| `Cmd_Stop` | write (PB, double-tap) | BOOL | Operator stop (one-shot) |

The `Sts_Starting`, `Sts_Stopping` and `Sts_Ready` members exist in T_Motor but are not referenced by these views. The alarm expression reads `<tagPath>/*` through `isAlarmActiveFiltered`, not a member. `Alm_*` members are not referenced.

## Component tree

Motor (identical in all 11 views, apart from the `root/Symbol` element count and the `root/I` position):

```
- `root` (ia.container.coord)
  - `Tag` (ia.display.label)
  - `Symbol` (ia.shapes.svg)
  - `P` (ia.display.label)
  - `I` (ia.display.label)
  - `StatusGroup` (ia.container.flex)
    - `M` (ia.display.label)
    - `Status` (ia.display.label)
  - `PB` (ia.input.button)
```

## Notes and open questions

- **HX_AirCooled uses a motor type.** Its `tType` default is `T_Motor`, so `efc.ui.openDynamic` picks `dw_Rotating` and opens `Templates/Dynamic Window/Rotating/Rotating`. Its bindings are the T_Motor members (`Sts_Running`, `Out_Run`, `Cmd_Start`, `Cmd_Stop`). `efc.ui.BY_TYPE` maps `T_HeatEx` to `dw_HeatTransfer` (`Templates/Dynamic Window/HeatTransfer/HeatTransfer`), which is the dock for a heat exchanger. Confirm whether this view is meant to be a fan drive (motor type, in which case the name is misleading) or a heat exchanger (in which case `tType` and the bindings are wrong).
- **`custom.command` is never bound.** In all 11 views `custom.command` keeps its default `-1`, so `custom.head` always equals `custom.fill`. `custom.head` is not referenced anywhere. Either bind `command` or remove `head`.
- **`custom.mode` is unused** in all 11 views.
- **`PB` can be enabled in fault or trip.** `custom.canCmd` does not check `fault` or `trip`. With no interlock or permissive-missing, `PB` is enabled, and a click writes `Cmd_Start` even when the drive is tripped or faulted. The double-tap path checks `Sts_Fault` but not `Sts_Tripped`. Confirm this matches the PLC behaviour for start after a trip.
- **No audit on `PB` or double-tap.** `PB` goes through `efc.ui.cmd` (Operator level check) and the double-tap path checks the same level, but neither passes `audit=True`.
- **Double-tap also opens the dock.** Browsers fire two `click` events before `dblclick`, so `onClick` (open the dock) runs as well as `onDoubleClick` (command). The dock opens for the same drive.
- **STARTING and STOPPING depend on the run command.** A drive that has been commanded to run but has no run feedback yet shows STARTING. The T_Motor `Sts_Starting` and `Sts_Stopping` members are not used.
- **`I` badge position.** Blower and Pump_Centrifugal place the `I` badge at y 0.5345. The other nine views use y 0.1897. Confirm that this is intended for the taller or wider symbols.
- **`viewBox` changes.** Pump_Reciprocating uses a 120 x 100 viewBox and HX_AirCooled uses 140 x 110. The other views use 100 x 100. The symbol box (`root/Symbol` position) is the same in every view, so these drawings scale differently inside it.
- **Unbound and fixed elements.** Pipe stubs and detail lines have fixed colours and are not bound to any state. Base or body elements have a fixed #EBEBEB fill and a bound outline. Confirm this is intended.
