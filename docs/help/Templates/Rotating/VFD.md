# Variable frequency drive template

Covers `Templates/Rotating/VFD`.
Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/Rotating/VFD/view.json`
Dynamic window it opens: `Docks/VFD` (see [VFD](../../Docks/VFD.md)).

## Overview

A single-device symbol for a variable frequency drive (T_VFD). It shows the run state as a fill colour, an alarm or fault outline, P and I badges, a status line that shows the running speed with its engineering units, an M label, and a Start/Stop button in manual mode. It is the drive version of the two-state rotating templates (see [Rotating_Discrete](Rotating_Discrete.md)), with a speed readout in the status line while running, and no touch (double-tap) command.

- **Default size:** 120 x 116 (`props.defaultSize`).
- **Bound to:** one T_VFD instance through `params.tagPath` (default `[default]PID_Demo/M601`).
- **Opening the dock:** a single click on the symbol runs `efc.ui.openDynamic(self)`. It maps `tType` (`T_VFD`, via BY_TYPE) to `dw_VFD`, then writes `session.custom.efcDw[pageId] = {path, params:{tagPath}}`. The screen's `Docks/Region` embedded view shows `Docks/VFD`. Only `tagPath` is passed on; `dwTagPath` overrides it when set.
- **Generated view:** `Docks/VFD` is written by `generator/docks/build_docks.py` (`vfd()`). This template is not generated.
- **Writes:** only the `PB` button. The symbol click opens the dock and writes nothing.

## How it operates

**Body colour and status (state).** The state body (`elements[0]`) takes `custom.fill` from `custom.state`. The status line text follows the same state:

| State | Derived from | Body colour | Status text | Status class |
|---|---|---|---|---|
| 0 | `Sts_Stopped` (after the checks for 1 and 3) | #9E9E9E | STOPPED | `State/Stopped` |
| 1 | `Sts_Running` | #FFFFFF | speed (`Val_Spd`, one decimal) and units (`Cfg_SpdEU`), e.g. `42.0 Hz` | `State/Running` |
| 2 | neither | #C4C4C4 | STARTING if `Out_Run` is true, else STOPPING | `State/Transition` |
| 3 | `Sts_Fault` or `Sts_Tripped` (checked first) | #3A3A3A | FAULT | `State/Fault` |

Priority is fault or trip, then running, then stopped, then transition. The speed readout is shown only in state 1. In states 0, 2 and 3 the speed is not shown. STARTING or STOPPING is chosen from `Out_Run` (the run command), not from `Sts_Starting` or `Sts_Stopping`.

**Mode and status line.** With `useButton = true` (default) the `M` label is hidden. With `useButton = false` the `M` label is shown while in MAN, and the status text gets the `Mode/ManualJoined` class.

**Inner marks.** `custom.con` drives the stroke of both inner marks (`elements[1]` and `elements[2]`). It is #F2F2F2 when `state` is 3 and #262626 otherwise.

**Alarm and fault outline.** `custom.line` is #D50000 when faulted. Otherwise it follows the highest active alarm class under `<tagPath>/*`: 1 cyan #00A3E0, 2 yellow #FFD200, 3 orange #FF7A00, 4 red #D50000. Default #262626. `custom.lw` is 3.75 normally and 7.5 when an alarm is active or the drive is faulted or tripped. Diagnostic (0) alarms do not change the outline.

**Badges.** `P` is shown when `Sts_NotPerm` is true. `I` is shown when `Sts_Intlk` is true. Its tooltip reads "Interlock active - switch-on blocked", followed by the first-out condition text if one exists.

**Name and tooltip.** The label shows `Cfg_Tag`, or the last segment of tagPath if `Cfg_Tag` is empty. The tooltip shows `Cfg_Desc`, if non-empty.

**Start/Stop button (`PB`).** Visible when `useButton` is true and the drive is in MAN. Enabled when `custom.canCmd` is true: MAN, available, not local, not OOS, and either a stop is pending (`cmd`, from `Out_Run`) or the drive is not permissive-missing and not interlocked. The tooltip is "Stop" when `cmd` is true, otherwise "Start". A click writes `Cmd_Stop` if `cmd` is true, otherwise `Cmd_Start`, with `True`.

**No speed command and no touch mode.** This template does not write a speed reference. Speed setpoint and direction are on the dock (`Cmd_Spd`, `Cmd_Rev`). There is no double-tap event and no `dblCmd` parameter, so with `useButton = false` the template has no command path at all.

**Security.** The `PB` script does not call `efc.ui.cmd`, so it does not check the user's role level and does not write an audit record. Its only guard is the enable expression. `canCmd` does not check `Sts_Fault` or `Sts_Tripped` (see Notes).

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `[default]PID_Demo/M601` | T_VFD instance. All bindings use it as `{view.params.tagPath}`. | Caller; read by bindings and `efc.ui.openDynamic` |
| `useButton` | input | `true` | `true` shows the `PB` command button; `false` shows the M label in MAN and hides `PB`. | Caller; read by bindings only |
| `tType` | input | `T_VFD` | Type key. `efc.ui.openDynamic` uses it (via BY_TYPE) to pick the window. | Read by `efc.ui.openDynamic`; not referenced in this view's bindings |
| `dockId` | input | `""` | Overrides the window chosen from `tType`. Must be a key of `efc.ui.WINDOWS`. | Read by `efc.ui.openDynamic` only |
| `dwTagPath` | input | `""` | Tag path passed to the dock instead of `tagPath` (when non-empty). | Read by `efc.ui.openDynamic` only |

All five params have `paramDirection: input` and `persistent: true`. No output params. There is no `dblCmd` param.

### View-level custom properties (`custom`)

Every property below has a binding. The source column gives what drives each one.

**Tag mirrors.** Seventeen properties are plain tag mirrors. Each one is an indirect, read-only tag binding (fallback delay 2.5 s, no `bidirectional` flag) to `{view.params.tagPath}` plus the member below.

| Group | Members |
|---|---|
| Run status | `custom.on` = `Sts_Running` (default `false`); `custom.off` = `Sts_Stopped` (default `true`); `custom.fault` = `Sts_Fault` (default `false`); `custom.trip` = `Sts_Tripped` (default `false`) |
| Run command | `custom.cmd` = `Out_Run` (default `false`). Drives STARTING/STOPPING and the `PB` action. |
| Speed | `custom.spd` = `Val_Spd` (default `0.0`); `custom.spdEU` = `Cfg_SpdEU` (default `""`). Used only by the status text in state 1. |
| Mode | `custom.man` = `Mode/Sts_Man` (default `false`); `custom.oos` = `Mode/Sts_OOS` (default `false`) |
| Availability | `custom.avail` = `Sts_Avail` (default `true`); `custom.local` = `Sts_Local` (default `false`) |
| Interlock / permissive | `custom.intlk` = `Sts_Intlk` (default `false`); `custom.permMissing` = `Sts_NotPerm` (default `false`); `custom.firstOut` = `Intlk/Sts_FirstOut` (default `-1`); `custom.firstDesc` = `Intlk/Cfg_CondDesc/{firstOut}` (default `""`) |
| Config | `custom.name` = `Cfg_Tag` (default `""`); `custom.desc` = `Cfg_Desc` (default `""`) |

**Computed properties.** These are expressions. The table gives the full source.

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.state` | `0` | expr | `if(coalesce({view.custom.fault}, false) \|\| coalesce({view.custom.trip}, false), 3, if(coalesce({view.custom.on}, false), 1, if(coalesce({view.custom.off}, false), 0, 2)))` | 3 if fault or trip, 1 if running, 0 if stopped, else 2 (transition). Drives fill, status and outline width. |
| `view.custom.mode` | `0` | expr | `if(coalesce({view.custom.man}, false), 1, 0)` | 1/0 from `man`. Not referenced by any binding or script in this view. |
| `view.custom.alarm` | `0` | expr | `if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 4, 4, 0, 1, 0), false), false)), 4, if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 3, 3, 0, 1, 0), false), false)), 3, if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 2, 2, 0, 1, 0), false), false)), 2, if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 1, 1, 0, 1, 0), false), false)), 1, 0))))` | Highest active alarm class 0-4 (4 checked first). Drives outline colour and width. |
| `view.custom.fill` | `"#9E9E9E"` | expr | `case({view.custom.state}, 0, "#9E9E9E", 1, "#FFFFFF", 2, "#C4C4C4", 3, "#3A3A3A", "#C4C4C4")` | Body colour from `state`. |
| `view.custom.head` | `"#9E9E9E"` | expr | `if({view.custom.command} < 0, {view.custom.fill}, if({view.custom.command} = 1, "#FFFFFF", "#9E9E9E"))` | Would select a head colour from `command`. `command` is never bound, so this always returns `fill`. Not referenced in this view. |
| `view.custom.line` | `"#262626"` | expr | `if({view.custom.state} = 3, "#D50000", case({view.custom.alarm}, 1, "#00A3E0", 2, "#FFD200", 3, "#FF7A00", 4, "#D50000", "#262626"))` | Outline colour: #D50000 when faulted or tripped; else by alarm class; default #262626. |
| `view.custom.con` | `"#262626"` | expr | `if({view.custom.state} = 3, "#F2F2F2", "#262626")` | Inner mark colour: #F2F2F2 when faulted or tripped, else #262626. |
| `view.custom.lw` | `3.75` | expr | `if({view.custom.alarm} > 0 \|\| {view.custom.state} = 3, 7.5, 3.75)` | Outline width: 7.5 when `alarm` > 0 or faulted or tripped, else 3.75. |
| `view.custom.canCmd` | `false` | expr | `coalesce({view.custom.man}, false) && coalesce({view.custom.avail}, true) && !coalesce({view.custom.local}, false) && !coalesce({view.custom.oos}, false) && (coalesce({view.custom.cmd}, false) \|\| (!coalesce({view.custom.permMissing}, false) && !coalesce({view.custom.intlk}, false)))` | True when man AND avail AND not local AND not oos AND (cmd OR (not permMissing AND not intlk)). Enables `PB`. Does not check `fault` or `trip`. |

### Component-level custom properties

None. The components carry no `custom` properties.

### Session, page and message payloads

None. The view reads no `session.*` or `page.*` values and sends no messages. Its only use of `session` is inside `efc.ui.openDynamic` (see the Scripts section). The `PB` button writes tags only.

## Bindings reference

Total: **44 bindings**: 26 at view root (`custom.*`) and 18 on components. Types: 27 `expr`, 17 `tag`. No transforms. `params.*` entries have `paramDirection` only and are not bindings.

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
| root/Symbol | `props.elements[1].stroke.paint` | expr | `{view.custom.con}` | Inner mark colour (`M` mark) |
| root/Symbol | `props.elements[2].stroke.paint` | expr | `{view.custom.con}` | Inner mark colour (wave mark) |

### `root/P`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/P | `meta.visible` | expr | `coalesce({view.custom.permMissing}, false)` | Shown while expression is true |

### `root/I`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/I | `meta.visible` | expr | `coalesce({view.custom.intlk}, false)` | Shown while expression is true |
| root/I | `meta.tooltip.text` | expr | `"Interlock active - " + "switch-on" + " blocked" + if(coalesce({view.custom.firstOut}, -1) >= 0 && len(coalesce({view.custom.firstDesc}, "")) > 0, ": " + {view.custom.firstDesc}, "")` | Tooltip |

### `root/StatusGroup`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/StatusGroup/M | `meta.visible` | expr | `!{view.params.useButton} && coalesce({view.custom.man}, false)` | Shown while expression is true |
| root/StatusGroup/M | `props.style.classes` | expr | `if(!{view.params.useButton} && coalesce({view.custom.man}, false), "Mode/ManualSplit", "Util/Collapsed")` | CSS class(es) selected by state |
| root/StatusGroup/Status | `props.text` | expr | `case({view.custom.state}, 0, "STOPPED", 1, numberFormat(coalesce({view.custom.spd}, 0.0), "0.0") + " " + coalesce({view.custom.spdEU}, ""), 2, if(coalesce({view.custom.cmd}, false), "STARTING", "STOPPING"), 3, "FAULT", "???")` | Text content: speed in state 1, otherwise a word |
| root/StatusGroup/Status | `props.style.classes` | expr | `case({view.custom.state}, 0, "State/Stopped", 1, "State/Running", 2, "State/Transition", 3, "State/Fault", "State/Unknown") + if(!{view.params.useButton} && coalesce({view.custom.man}, false), " Mode/ManualJoined", "")` | CSS class(es) selected by state |

### `root/PB`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/PB | `meta.visible` | expr | `{view.params.useButton} && coalesce({view.custom.man}, false)` | Shown while expression is true |
| root/PB | `props.enabled` | expr | `{view.custom.canCmd}` | Enabled while expression is true |
| root/PB | `meta.tooltip.text` | expr | `if(coalesce({view.custom.cmd}, false), "Stop", "Start")` | Tooltip |

## Scripts reference

Total: **2 event scripts**, no `customMethods`, no `messageHandlers`, no property-change scripts, no script transforms. `view.scripts` is absent. There is no `dom.onDoubleClick` event.

1. **`root/Symbol`**: `events.dom.onClick` on `root/Symbol`, scope G.
   Opens the dynamic window for this tag. Calls `efc.ui.openDynamic`. No tag writes.

```python
	efc.ui.openDynamic(self)
```

2. **`root/PB`**: `events.component.onActionPerformed` on `root/PB`, scope G.
   Manual Start/Stop button. Writes `True` to `Cmd_Stop` if `cmd` (`Out_Run`) is true, else to `Cmd_Start`, directly via `system.tag.writeBlocking`. No role check, no audit.

```python
	m = 'Cmd_Stop' if self.view.custom.cmd else 'Cmd_Start'
	system.tag.writeBlocking([self.view.params.tagPath + '/' + m], [True])
```

### Library functions called by this view (`efc.ui`, `projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.openDynamic(component)`**: picks the window from `dockId`, or from `BY_TYPE[tType]`. For `T_VFD` that is `dw_VFD`, which maps to `Docks/VFD`. If no window is found, it logs a warning and stops. Otherwise it writes `session.custom.efcDw[pageId] = {path, params:{tagPath: dwTagPath or tagPath}}`. It does not check the user's role and does not write to the tag.
- `efc.ui.dblCmd` is not called by this view, and `T_VFD` is not in its `DBL_CMD` table.

## Tag members used

All paths are relative to `tagPath`. Types come from `types/PCLib_Members.csv` (type T_VFD, MTP `MonAnaDrv`; nested types from T_Mode and T_Intlk).

| Member | Access | Data type | Meaning (PCLib comment) |
|---|---|---|---|
| `Cfg_Tag` | read | STRING[20] | Equipment / instrument tag, e.g. FT-101 |
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Cfg_SpdEU` | read | STRING[8] | Speed units text (%, Hz, rpm) |
| `Out_Run` | read | BOOL | Run command to drive |
| `Val_Spd` | read | REAL | Speed |
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
| `Cmd_Start` | write (PB) | BOOL | Operator start (one-shot) |
| `Cmd_Stop` | write (PB) | BOOL | Operator stop (one-shot) |

The alarm expression reads `<tagPath>/*` through `isAlarmActiveFiltered`, not a member. `Alm_*`, `Sts_Rev`, `Sts_AtSpd`, `Sts_CommFail` and the other T_VFD members are not referenced here.

## Component tree

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

`root/Symbol` has three SVG elements: `state0` (circle r34, bound), `cstroke1` (an "M" mark, stroke bound to `custom.con`) and `cstroke2` (a wave mark, stroke bound to `custom.con`).

## Notes and open questions

- **`PB` can be enabled in fault or trip.** `custom.canCmd` does not check `fault` or `trip`. With no interlock or permissive-missing, `PB` is enabled, and a click writes `Cmd_Start` even when the drive is tripped or faulted. Confirm this matches the drive logic for start after a trip.
- **No role check or audit on `PB`.** It writes directly and is guarded only by its enable expression. `efc.ui.cmd` (role check and optional audit) is not used.
- **`useButton = false` leaves no command path.** `PB` is hidden, there is no double-tap event and no `dblCmd` parameter. Commands are only possible on the dock.
- **Speed readout only in state 1.** The status line shows speed only while `Sts_Running` is true. A drive that is running at zero speed shows `0.0` plus units. A drive whose `Cfg_SpdEU` is empty shows a trailing space after the number.
- **Speed is not clamped or checked.** The readout shows `Val_Spd` as-is. No limit, deviation or at-speed indication (`Sts_AtSpd`, `Alm_SpdDev`) is used on the symbol.
- **Direction is not shown.** `Sts_Rev` and `Out_Rev` are not used, so the symbol does not show forward or reverse.
- **`custom.command` is never bound**, so `custom.head` always equals `custom.fill`. `custom.head` is not referenced. `custom.mode` is also unused.
- **Interlock wording.** The `I` tooltip says "switch-on blocked" where the rotating templates say "start blocked". The text is set in the view, so it is not derived from the drive type.
- **STARTING and STOPPING depend on the run command.** A drive commanded to run but with no feedback yet shows STARTING. The T_VFD `Sts_Starting` and `Sts_Stopping` members are not used.
