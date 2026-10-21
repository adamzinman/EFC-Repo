# Electric heater template

Covers `Templates/HeatTransfer/Heater_Electric`.
Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/HeatTransfer/Heater_Electric/view.json`
Dynamic window it opens: `Docks/Heater` (see [Heater](../../Docks/Heater.md)).

## Overview

A single-device symbol for an electric heater (T_Heater). It shows the on or off state as a fill colour, an alarm, fault or high-limit outline, P and I badges, a status line (OFF, ON, SWITCHING ON, SWITCHING OFF or FAULT), an M label, and an On/Off button in manual mode. It uses only the on/off members of the type (`Out_Contactor`, `Sts_On`, `Sts_Off`). The power, duty, current and SSR or SCR fields in T_Heater are not shown on this symbol. They are on the dock.

- **Default size:** 120 x 116 (`props.defaultSize`).
- **Bound to:** one T_Heater instance through `params.tagPath` (default `[default]PID_Demo/E401`).
- **Opening the dock:** a single click on the symbol runs `efc.ui.openDynamic(self)`. It maps `tType` (`T_Heater`, via BY_TYPE) to `dw_Heater`, then writes `session.custom.efcDw[pageId] = {path, params:{tagPath}}`. The screen's `Docks/Region` embedded view shows `Docks/Heater`. Only `tagPath` is passed on; `dwTagPath` overrides it when set.
- **Generated view:** `Docks/Heater` is written by `generator/docks/build_docks.py` (`heater()`). This template is not generated.
- **Writes:** only the `PB` button. The symbol click opens the dock and writes nothing.

## How it operates

**Body colour and status (state).** The state head (`elements[3]`) takes `custom.fill` from `custom.state`. The status line text follows the same state:

| State | Derived from | Body colour | Status text | Status class |
|---|---|---|---|---|
| 0 | `Sts_Off`, when not 1 or 3 | #9E9E9E | OFF | `State/Stopped` |
| 1 | `Sts_On` | #FFFFFF | ON | `State/Running` |
| 2 | neither | #C4C4C4 | SWITCHING ON if `Out_Contactor` is true, else SWITCHING OFF | `State/Transition` |
| 3 | `Sts_Fault` or `Sts_Tripped` (checked first) | #3A3A3A | FAULT | `State/Fault` |

Priority is fault or trip, then on, then off, then transition. SWITCHING ON or OFF is chosen from `Out_Contactor` (the contactor command), not from any feedback member. The `Sts_HiLimit` (high-limit tripped) state is not separately shown: a high-limit trip is handled only if it also sets `Sts_Tripped` or `Sts_Fault`.

**Mode and status line.** With `useButton = true` (default) the `M` label is hidden. With `useButton = false` the `M` label is shown while in MAN, and the status text gets the `Mode/ManualJoined` class.

**Alarm and fault outline.** `custom.line` is #D50000 when faulted or tripped. Otherwise it follows the highest active alarm class under `<tagPath>/*`: 1 cyan #00A3E0, 2 yellow #FFD200, 3 orange #FF7A00, 4 red #D50000. Default #262626. `custom.lw` is 2.5 normally and 5.0 when an alarm is active or the heater is faulted or tripped. Diagnostic (0) alarms do not change the outline.

**Badges.** `P` is shown when `Sts_NotPerm` is true. `I` is shown when `Sts_Intlk` is true. Its tooltip reads "Interlock active - switch-on blocked", followed by the first-out condition text if one exists.

**Name and tooltip.** The label shows `Cfg_Tag`, or the last segment of tagPath if `Cfg_Tag` is empty. The tooltip shows `Cfg_Desc`, if non-empty.

**On/Off button (`PB`).** Visible when `useButton` is true and the heater is in MAN. Enabled when `custom.canCmd` is true: MAN, available, not local, not OOS, and either a switch-off is pending (`cmd`, from `Out_Contactor`) or the heater is not permissive-missing and not interlocked. The tooltip is "Switch off" when `cmd` is true, otherwise "Switch on". A click writes `Cmd_Off` if `cmd` is true, otherwise `Cmd_On`, with `True`.

**Security.** The `PB` script does not call `efc.ui.cmd`, so it does not check the user's role level and does not write an audit record. Its only guard is the enable expression. `canCmd` does not check `Sts_Fault` or `Sts_Tripped` (see Notes).

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `[default]PID_Demo/E401` | T_Heater instance. All bindings use it as `{view.params.tagPath}`. | Caller; read by bindings and `efc.ui.openDynamic` |
| `useButton` | input | `true` | `true` shows the `PB` command button; `false` shows the M label in MAN and hides `PB`. | Caller; read by bindings only |
| `tType` | input | `T_Heater` | Type key. `efc.ui.openDynamic` uses it (via BY_TYPE) to pick the window. | Read by `efc.ui.openDynamic`; not referenced in this view's bindings |
| `dockId` | input | `""` | Overrides the window chosen from `tType`. Must be a key of `efc.ui.WINDOWS`. | Read by `efc.ui.openDynamic` only |
| `dwTagPath` | input | `""` | Tag path passed to the dock instead of `tagPath` (when non-empty). | Read by `efc.ui.openDynamic` only |

All five params have `paramDirection: input` and `persistent: true`. No output params. There is no `dblCmd` param.

### View-level custom properties (`custom`)

Every property below has a binding. The source column gives what drives each one.

**Tag mirrors.** Fifteen properties are plain tag mirrors. Each one is an indirect, read-only tag binding (fallback delay 2.5 s, no `bidirectional` flag) to `{view.params.tagPath}` plus the member below.

| Group | Members |
|---|---|
| Run status | `custom.on` = `Sts_On` (default `false`); `custom.off` = `Sts_Off` (default `true`); `custom.fault` = `Sts_Fault` (default `false`); `custom.trip` = `Sts_Tripped` (default `false`) |
| Contactor command | `custom.cmd` = `Out_Contactor` (default `false`). Drives SWITCHING ON/OFF and the `PB` action. |
| Mode | `custom.man` = `Mode/Sts_Man` (default `false`); `custom.oos` = `Mode/Sts_OOS` (default `false`) |
| Availability | `custom.avail` = `Sts_Avail` (default `true`); `custom.local` = `Sts_Local` (default `false`) |
| Interlock / permissive | `custom.intlk` = `Sts_Intlk` (default `false`); `custom.permMissing` = `Sts_NotPerm` (default `false`); `custom.firstOut` = `Intlk/Sts_FirstOut` (default `-1`); `custom.firstDesc` = `Intlk/Cfg_CondDesc/{firstOut}` (default `""`) |
| Config | `custom.name` = `Cfg_Tag` (default `""`); `custom.desc` = `Cfg_Desc` (default `""`) |

**Computed properties.** These are expressions. The table gives the full source.

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.state` | `0` | expr | `if(coalesce({view.custom.fault}, false) \|\| coalesce({view.custom.trip}, false), 3, if(coalesce({view.custom.on}, false), 1, if(coalesce({view.custom.off}, false), 0, 2)))` | 3 if fault or trip, 1 if on, 0 if off, else 2 (transition). Drives fill, status and outline width. |
| `view.custom.mode` | `0` | expr | `if(coalesce({view.custom.man}, false), 1, 0)` | 1/0 from `man`. Not referenced by any binding or script in this view. |
| `view.custom.alarm` | `0` | expr | `if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 4, 4, 0, 1, 0), false), false)), 4, if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 3, 3, 0, 1, 0), false), false)), 3, if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 2, 2, 0, 1, 0), false), false)), 2, if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 1, 1, 0, 1, 0), false), false)), 1, 0))))` | Highest active alarm class 0-4 (4 checked first). Drives outline colour and width. |
| `view.custom.fill` | `"#9E9E9E"` | expr | `case({view.custom.state}, 0, "#9E9E9E", 1, "#FFFFFF", 2, "#C4C4C4", 3, "#3A3A3A", "#C4C4C4")` | Body colour from `state`. |
| `view.custom.head` | `"#9E9E9E"` | expr | `if({view.custom.command} < 0, {view.custom.fill}, if({view.custom.command} = 1, "#FFFFFF", "#9E9E9E"))` | Would select a head colour from `command`. `command` is never bound, so this always returns `fill`. Not referenced in this view. |
| `view.custom.line` | `"#262626"` | expr | `if({view.custom.state} = 3, "#D50000", case({view.custom.alarm}, 1, "#00A3E0", 2, "#FFD200", 3, "#FF7A00", 4, "#D50000", "#262626"))` | Outline colour: #D50000 when faulted or tripped; else by alarm class; default #262626. |
| `view.custom.con` | `"#262626"` | expr | `if({view.custom.state} = 3, "#F2F2F2", "#262626")` | Not referenced anywhere in the view (defined and bound, unused). |
| `view.custom.lw` | `2.5` | expr | `if({view.custom.alarm} > 0 \|\| {view.custom.state} = 3, 5.0, 2.5)` | Outline width: 5.0 when `alarm` > 0 or faulted or tripped, else 2.5. |
| `view.custom.canCmd` | `false` | expr | `coalesce({view.custom.man}, false) && coalesce({view.custom.avail}, true) && !coalesce({view.custom.local}, false) && !coalesce({view.custom.oos}, false) && (coalesce({view.custom.cmd}, false) \|\| (!coalesce({view.custom.permMissing}, false) && !coalesce({view.custom.intlk}, false)))` | True when man AND avail AND not local AND not oos AND (cmd OR (not permMissing AND not intlk)). Enables `PB`. Does not check `fault` or `trip`. |

### Component-level custom properties

None. The components carry no `custom` properties.

### Session, page and message payloads

None. The view reads no `session.*` or `page.*` values and sends no messages. Its only use of `session` is inside `efc.ui.openDynamic` (see the Scripts section). The `PB` button writes tags only.

## Bindings reference

Total: **42 bindings**: 24 at view root (`custom.*`) and 18 on components. Types: 27 `expr`, 15 `tag`. No transforms. `params.*` entries have `paramDirection` only and are not bindings.

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
| root/Symbol | `props.elements[0].stroke.paint` | expr | `{view.custom.line}` | Body outline colour |
| root/Symbol | `props.elements[0].stroke.width` | expr | `{view.custom.lw}` | Body outline width |
| root/Symbol | `props.elements[3].fill.paint` | expr | `{view.custom.fill}` | State head fill colour |
| root/Symbol | `props.elements[3].stroke.paint` | expr | `{view.custom.line}` | State head outline colour |
| root/Symbol | `props.elements[3].stroke.width` | expr | `{view.custom.lw}` | State head outline width |

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
| root/StatusGroup/Status | `props.text` | expr | `case({view.custom.state}, 0, "OFF", 1, "ON", 2, if(coalesce({view.custom.cmd}, false), "SWITCHING ON", "SWITCHING OFF"), 3, "FAULT", "???")` | Text content |
| root/StatusGroup/Status | `props.style.classes` | expr | `case({view.custom.state}, 0, "State/Stopped", 1, "State/Running", 2, "State/Transition", 3, "State/Fault", "State/Unknown") + if(!{view.params.useButton} && coalesce({view.custom.man}, false), " Mode/ManualJoined", "")` | CSS class(es) selected by state |

### `root/PB`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/PB | `meta.visible` | expr | `{view.params.useButton} && coalesce({view.custom.man}, false)` | Shown while expression is true |
| root/PB | `props.enabled` | expr | `{view.custom.canCmd}` | Enabled while expression is true |
| root/PB | `meta.tooltip.text` | expr | `if(coalesce({view.custom.cmd}, false), "Switch off", "Switch on")` | Tooltip |

## Scripts reference

Total: **2 event scripts**, no `customMethods`, no `messageHandlers`, no property-change scripts, no script transforms. `view.scripts` is absent. There is no `dom.onDoubleClick` event.

1. **`root/Symbol`**: `events.dom.onClick` on `root/Symbol`, scope G.
   Opens the dynamic window for this tag. Calls `efc.ui.openDynamic`. No tag writes.

```python
	efc.ui.openDynamic(self)
```

2. **`root/PB`**: `events.component.onActionPerformed` on `root/PB`, scope G.
   Manual On/Off button. Writes `True` to `Cmd_Off` if `cmd` (`Out_Contactor`) is true, else to `Cmd_On`, directly via `system.tag.writeBlocking`. No role check, no audit.

```python
	m = 'Cmd_Off' if self.view.custom.cmd else 'Cmd_On'
	system.tag.writeBlocking([self.view.params.tagPath + '/' + m], [True])
```

### Library functions called by this view (`efc.ui`, `projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.openDynamic(component)`**: picks the window from `dockId`, or from `BY_TYPE[tType]`. For `T_Heater` that is `dw_Heater`, which maps to `Docks/Heater`. If no window is found, it logs a warning and stops. Otherwise it writes `session.custom.efcDw[pageId] = {path, params:{tagPath: dwTagPath or tagPath}}`. It does not check the user's role and does not write to the tag.
- `efc.ui.dblCmd` is not called by this view, and `T_Heater` is not in its `DBL_CMD` table.

## Tag members used

All paths are relative to `tagPath`. Types come from `types/PCLib_Members.csv` (type T_Heater, MTP `MonBinDrv (on/off) / MonAnaDrv (SSR, SCR)`; nested types from T_Mode and T_Intlk).

| Member | Access | Data type | Meaning (PCLib comment) |
|---|---|---|---|
| `Cfg_Tag` | read | STRING[20] | Equipment / instrument tag, e.g. FT-101 |
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Out_Contactor` | read | BOOL | Main / isolating contactor (opened on trip, high limit or shorted SSR) |
| `Sts_On` | read | BOOL | On: contactor closed and enabled to heat |
| `Sts_Off` | read | BOOL | Off |
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
| `Cmd_On` | write (PB) | BOOL | Operator on (one-shot) |
| `Cmd_Off` | write (PB) | BOOL | Operator off (one-shot) |

The alarm expression reads `<tagPath>/*` through `isAlarmActiveFiltered`, not a member. `Sts_HiLimit`, `Sts_Heating`, `Sts_LoadFail`, `Sts_Shorted`, `Val_*` and `Alm_*` members are not referenced here.

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

`root/Symbol` (viewBox 0 0 120 90) has four SVG elements: `body0` (rect, fill fixed #EBEBEB, outline bound), `detail1` (zig-zag element, unbound), `detail2` (short stem, unbound) and `state3` (rect head, fill, outline bound).

## Notes and open questions

- **`PB` can be enabled in fault or trip.** `custom.canCmd` does not check `fault` or `trip`. With no interlock or permissive-missing, `PB` is enabled, and a click writes `Cmd_On` even when the heater is tripped or faulted. Confirm this matches the PLC logic for switch-on after a trip. Note also that `Sts_HiLimit` (hardwired high-limit trip) is not checked here.
- **`custom.con` is unused.** It is defined and bound (`if(state = 3, "#F2F2F2", "#262626")`), but no element in `root/Symbol` uses it. Either bind it to a mark or remove it.
- **`custom.mode` and `custom.head` are unused.** `custom.command` is never bound, so `head` always equals `fill`.
- **Power and current are not shown on the symbol.** The symbol shows only on, off, switching and fault. `Val_Power`, `Val_Duty`, `Val_Current` and the SSR or SCR fields are on the dock.
- **High-limit trip is not shown separately.** The dock banner has a HIGH LIMIT state (`Sts_HiLimit`). This symbol does not read it. A high-limit trip shows as FAULT only if it also sets `Sts_Fault` or `Sts_Tripped`.
- **No command path with `useButton = false`.** `PB` is hidden, there is no double-tap event and no `dblCmd` parameter, so commands are only possible on the dock.
- **Interlock wording.** The `I` tooltip says "switch-on blocked", as on the VFD template, while the rotating templates say "start blocked".
- **STARTING and STOPPING equivalents depend on the contactor command.** SWITCHING ON or OFF is shown from `Out_Contactor`, not from `Sts_State` (which has its own switching states in T_Heater).
