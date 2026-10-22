# Discrete valve templates

Covers `Templates/Valves/Valve_Solenoid`, `Templates/Valves/Valve_MOV` and `Templates/Valves/Valve_OnOff_Pneumatic`.
Sources: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/Valves/<name>/view.json`
Dynamic window they open: `Docks/ValveDiscrete` (see [ValveDiscrete](../../Docks/ValveDiscrete.md)).

## Overview

These are single-device P&ID symbols for a two-state valve (T_DValve). Each shows the valve state as a fill colour, an alarm or fault outline, interlock (I) and permissive (P) badges, a mode/status line, and an optional in-place command button.

- **Default size:** 120 x 100 (`props.defaultSize`).
- **Bound to:** one T_DValve instance through `params.tagPath`.
- **Opening the dock:** a single click on the symbol runs `efc.ui.openDynamic(self)`. It maps `tType` (or `dockId`) to a window, then writes `session.custom.efcDw[pageId] = {path, params:{tagPath}}`. The screen's `Docks/Region` embedded view shows that path. Only `tagPath` is passed on; `dwTagPath` overrides it when set.

### Differences between the three views

All three have the same params, custom properties, bindings (expressions and sources), scripts and component tree. This document applies to all three. Only the following differ:

| View | Symbol head (`elements[1]`) | Body element bound to `custom.fill` | Default `tagPath` | P/I badge position (x / y) |
|---|---|---|---|---|
| `Valve_Solenoid` | rect 28x22 with an "S" mark | `elements[3]` | `[default]PID_Demo/XV102` | P 0.307 / 0.211, I 0.577 / 0.211 |
| `Valve_MOV` | circle r14 with an "M" mark | `elements[3]` | `[default]PID_Demo/XV103` | P 0.307 / 0.207, I 0.577 / 0.207 |
| `Valve_OnOff_Pneumatic` | flat rect 40x16, no mark (3 elements, not 4) | `elements[2]` | `[default]PID_Demo/XV101` | P 0.285 / 0.216, I 0.598 / 0.216 |

In every view, the head is `elements[1]`. Where this document says `elements[3]` for the body, read `elements[2]` for `Valve_OnOff_Pneumatic`.

## How it operates

**Body colour (state).** The body (`elements[3]`, state path) takes `custom.fill` from `custom.state`:

| State | Derived from | Body colour | Status text |
|---|---|---|---|
| 0 | `Sts_Closed` | #9E9E9E | CLOSED |
| 1 | `Sts_Opened` | #FFFFFF | OPEN |
| 2 | neither | #C4C4C4 | OPENING if `Out_Open`, else CLOSING |
| 3 | `Sts_Fault` (checked first) | #3A3A3A | FAULT (outline and frame turn red) |

Priority is fault, then opened, then closed, then transition.

**Head colour (command).** The actuator head (`elements[1]`) is white (#FFFFFF) while `Out_Open` is commanded, grey (#9E9E9E) otherwise. If neither limit switch is configured, the head uses the body colour.

**Alarm and fault outline.** The outline (`custom.line`) is red when faulted. Otherwise it follows the highest active alarm class under `<tagPath>/*`: 1 Low cyan #00A3E0, 2 Medium yellow #FFD200, 3 High orange #FF7A00, 4 Critical red #D50000. These are Ignition alarm priorities (0 Diagnostic to 4 Critical). Diagnostic (0) alarms do not change the outline. The outline is 8.333 wide when any alarm or fault is active and 4.167 otherwise.

**Badges.** `P` is shown when `Sts_NotPerm` is true. `I` is shown when `Sts_Intlk` is true; its tooltip reads "Interlock active - open blocked" followed by the first-out condition text, if one exists.

**Mode and status line.** With `useButton = true` (default) the `M` label is hidden. With `useButton = false` (touch mode) the `M` label is shown while in MAN, and the status text gets the `Mode/ManualJoined` class. The `M` label uses `Mode/ManualSplit`.

**Name and tooltip.** The label shows `Cfg_Tag`, or the last segment of tagPath if `Cfg_Tag` is empty. The tooltip shows `Cfg_Desc`, if non-empty.

**Command button (`PB`).** Visible only when `useButton` is true and the valve is in MAN. Enabled when `custom.canCmd` is true: MAN, available, not LOCAL, not OOS, and either a close is pending (`cmd`) or the valve is not permissive-missing and not interlocked. Clicking writes `Cmd_Close` if `Out_Open` is true, otherwise `Cmd_Open`, with `True`. Tooltip: "Local control", "Manual mode required", "Close" or "Open".

**Touch mode (double-tap).** With `useButton = false` and `dblCmd = true`, the `Symbol` double-click calls `efc.ui.dblCmd(self)`. Details are in the Scripts section below.

**Security.** The PB button script calls `efc.ui.cmd(self, m, True, 1)`, which re-checks the Operator level (1) and writes no audit record. The enable expression is a second guard. The double-tap path also checks the role (Operator or higher).

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | per view (see table above) | T_DValve instance. All bindings use it as `{view.params.tagPath}`. | Caller; read by bindings and `efc.ui` |
| `useButton` | input | `true` | `true` shows the PB command button; `false` enables touch mode (M label, double-tap). | Caller; read by bindings and `efc.ui.dblCmd` |
| `tType` | input | `T_DValve` | Type key. `efc.ui.openDynamic` uses it (via BY_TYPE) to pick the window. | Read by `efc.ui.openDynamic` and `efc.ui.dblCmd`; not referenced in this view's bindings |
| `dockId` | input | `""` | Overrides the window chosen from `tType`. Must be a key of `efc.ui.WINDOWS`. | Read by `efc.ui.openDynamic` only |
| `dwTagPath` | input | `""` | Tag path passed to the dock instead of `tagPath` (when non-empty). | Read by `efc.ui.openDynamic` only |
| `dblCmd` | input | `true` | Permits the double-tap command (checked in `efc.ui.dblCmd`). | Read by `efc.ui.dblCmd` only |

All six params have `paramDirection: input` and `persistent: true`. No output params.

### View-level custom properties (`custom`)

Every property below has a binding (none is set by a script), so the source column gives what drives it.

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.cmd` | `false` | tag | tag `{0}/Out_Open` | Mirror of `Out_Open` (open command output). Drives PB action, status text OPENING/CLOSING and head colour. |
| `view.custom.opened` | `false` | tag | tag `{0}/Sts_Opened` | Mirror of `Sts_Opened`. |
| `view.custom.closed` | `true` | tag | tag `{0}/Sts_Closed` | Mirror of `Sts_Closed`. |
| `view.custom.fault` | `false` | tag | tag `{0}/Sts_Fault` | Mirror of `Sts_Fault`. |
| `view.custom.hasZso` | `true` | tag | tag `{0}/Cfg_HasZSO` | Mirror of `Cfg_HasZSO` (open limit fitted). |
| `view.custom.hasZsc` | `true` | tag | tag `{0}/Cfg_HasZSC` | Mirror of `Cfg_HasZSC` (closed limit fitted). |
| `view.custom.state` | `0` | expr | `if(coalesce({view.custom.fault}, false), 3, if(coalesce({view.custom.opened}, false), 1, if(coalesce({view.custom.closed}, false), 0, 2)))` | Derived: 3 if fault, 1 if opened, 0 if closed, else 2 (transition). Note: numbering differs from the PCLib `Sts_State` member. |
| `view.custom.command` | `0` | expr | `if(coalesce({view.custom.hasZso}, false) \|\| coalesce({view.custom.hasZsc}, false), if(coalesce({view.custom.cmd}, false), 1, 0), -1)` | Derived: -1 if neither limit switch is configured, 1 if `cmd` true, else 0. Selects head colour. |
| `view.custom.name` | `""` | tag | tag `{0}/Cfg_Tag` | Mirror of `Cfg_Tag`; falls back to last segment of tagPath (tag label). |
| `view.custom.desc` | `""` | tag | tag `{0}/Cfg_Desc` | Mirror of `Cfg_Desc`; used as tooltip. |
| `view.custom.man` | `false` | tag | tag `{0}/Mode/Sts_Man` | Mirror of `Mode/Sts_Man`. |
| `view.custom.oos` | `false` | tag | tag `{0}/Mode/Sts_OOS` | Mirror of `Mode/Sts_OOS`. |
| `view.custom.avail` | `true` | tag | tag `{0}/Sts_Avail` | Mirror of `Sts_Avail` (defaults true in expression). |
| `view.custom.local` | `false` | tag | tag `{0}/Sts_Local` | Mirror of `Sts_Local`. |
| `view.custom.intlk` | `false` | tag | tag `{0}/Sts_Intlk` | Mirror of `Sts_Intlk`. |
| `view.custom.permMissing` | `false` | tag | tag `{0}/Sts_NotPerm` | Mirror of `Sts_NotPerm` (permissive missing). |
| `view.custom.firstOut` | `-1` | tag | tag `{0}/Intlk/Sts_FirstOut` | Mirror of `Intlk/Sts_FirstOut` (-1 = none). |
| `view.custom.firstDesc` | `""` | tag | tag `{0}/Intlk/Cfg_CondDesc/{1}` | Mirror of `Intlk/Cfg_CondDesc[firstOut]` (text of first-out condition). |
| `view.custom.mode` | `0` | expr | `if(coalesce({view.custom.man}, false), 1, 0)` | Derived 1/0 from `man`. Set but not referenced by any binding or script in this view. |
| `view.custom.alarm` | `0` | expr | `if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 4, 4, 0, 1, 0), false), false)), 4, if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 3, 3, 0, 1, 0), false), false)), 3, if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 2, 2, 0, 1, 0), false), false)), 2, if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 1, 1, 0, 1, 0), false), false)), 1, 0))))` | Highest active alarm class 0-4 from isAlarmActiveFiltered on `tagPath/*` (4 checked first). Drives outline colour and width. |
| `view.custom.fill` | `"#9E9E9E"` | expr | `case({view.custom.state}, 0, "#9E9E9E", 1, "#FFFFFF", 2, "#C4C4C4", 3, "#3A3A3A", "#C4C4C4")` | Body colour from `state` (0 #9E9E9E, 1 #FFFFFF, 2 #C4C4C4, 3 #3A3A3A). |
| `view.custom.head` | `"#9E9E9E"` | expr | `if({view.custom.command} < 0, {view.custom.fill}, if({view.custom.command} = 1, "#FFFFFF", "#9E9E9E"))` | Actuator head colour: `fill` if `command` < 0, #FFFFFF if `command` = 1, else #9E9E9E. |
| `view.custom.line` | `"#262626"` | expr | `if({view.custom.state} = 3, "#D50000", case({view.custom.alarm}, 1, "#00A3E0", 2, "#FFD200", 3, "#FF7A00", 4, "#D50000", "#262626"))` | Outline colour: #D50000 when faulted; else alarm 1 #00A3E0, 2 #FFD200, 3 #FF7A00, 4 #D50000; default #262626. |
| `view.custom.lw` | `4.167` | expr | `if({view.custom.alarm} > 0 \|\| {view.custom.state} = 3, 8.333, 4.167)` | Outline width: 8.333 when `alarm` > 0 or faulted, else 4.167. |
| `view.custom.con` | `"#262626"` | expr | `if({view.custom.state} = 3, "#F2F2F2", "#262626")` | Not referenced anywhere in the view (defined and bound, unused). |
| `view.custom.canCmd` | `false` | expr | `coalesce({view.custom.man}, false) && coalesce({view.custom.avail}, true) && !coalesce({view.custom.local}, false) && !coalesce({view.custom.oos}, false) && (coalesce({view.custom.cmd}, false) \|\| (!coalesce({view.custom.permMissing}, false) && !coalesce({view.custom.intlk}, false)))` | True when man AND avail AND not local AND not oos AND (cmd OR (not permMissing AND not intlk)). Enables PB. |

### Component-level custom properties

None. The components carry no `custom` properties.

### Session, page and message payloads

None. The template reads no `session.*` or `page.*` values and sends no messages. Its writes are the PB button script (through `efc.ui.cmd`) and the double-tap path (`efc.ui.dblCmd`).

## Bindings reference

Total: **45 bindings** (26 at view root in `custom.*`, 19 on components). Types: 29 `expr`, 16 `tag`. No transforms. `params.*` entries have `paramDirection` only and are not bindings.

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
| root/Symbol | `props.elements[1].fill.paint` | expr | `{view.custom.head}` | SVG element colour or stroke width |
| root/Symbol | `props.elements[1].stroke.paint` | expr | `{view.custom.line}` | SVG element colour or stroke width |
| root/Symbol | `props.elements[1].stroke.width` | expr | `{view.custom.lw}` | SVG element colour or stroke width |
| root/Symbol | `props.elements[3].fill.paint` | expr | `{view.custom.fill}` | SVG element colour or stroke width |
| root/Symbol | `props.elements[3].stroke.paint` | expr | `{view.custom.line}` | SVG element colour or stroke width |
| root/Symbol | `props.elements[3].stroke.width` | expr | `{view.custom.lw}` | SVG element colour or stroke width |

### `root/P`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/P | `meta.visible` | expr | `coalesce({view.custom.permMissing}, false)` | Shown while expression is true |

### `root/I`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/I | `meta.visible` | expr | `coalesce({view.custom.intlk}, false)` | Shown while expression is true |
| root/I | `meta.tooltip.text` | expr | `"Interlock active - " + "open" + " blocked" + if(coalesce({view.custom.firstOut}, -1) >= 0 && len(coalesce({view.custom.firstDesc}, "")) > 0, ": " + {view.custom.firstDesc}, "")` | Tooltip |

### `root/StatusGroup`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/StatusGroup/M | `meta.visible` | expr | `!{view.params.useButton} && coalesce({view.custom.man}, false)` | Shown while expression is true |
| root/StatusGroup/M | `props.style.classes` | expr | `if(!{view.params.useButton} && coalesce({view.custom.man}, false), "Mode/ManualSplit", "Util/Collapsed")` | CSS class(es) selected by state |
| root/StatusGroup/Status | `props.text` | expr | `case({view.custom.state}, 0, "CLOSED", 1, "OPEN", 2, if(coalesce({view.custom.cmd}, false), "OPENING", "CLOSING"), 3, "FAULT", "???")` | Text content |
| root/StatusGroup/Status | `props.style.classes` | expr | `case({view.custom.state}, 0, "State/Stopped", 1, "State/Running", 2, "State/Transition", 3, "State/Fault", "State/Unknown") + if(!{view.params.useButton} && coalesce({view.custom.man}, false), " Mode/ManualJoined", "")` | CSS class(es) selected by state |

### `root/PB`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/PB | `meta.visible` | expr | `{view.params.useButton} && coalesce({view.custom.man}, false)` | Shown while expression is true |
| root/PB | `props.enabled` | expr | `{view.custom.canCmd}` | Enabled while expression is true |
| root/PB | `meta.tooltip.text` | expr | `if(coalesce({view.custom.local}, false), "Local control", if(!coalesce({view.custom.man}, false), "Manual mode required", if(coalesce({view.custom.cmd}, false), "Close", "Open")))` | Tooltip |

## Scripts reference

Total: **3 event scripts**, no `customMethods`, no `messageHandlers`, no property-change scripts, no script transforms. `view.scripts` is absent.

1. **`root/Symbol`**: `events.dom.onClick` on `root/Symbol`, scope G.
   Opens the dynamic window for this tag. Calls `efc.ui.openDynamic`, which writes `session.custom.efcDw` (see below). No tag writes.

```python
	efc.ui.openDynamic(self)
```

2. **`root/Symbol`**: `events.dom.onDoubleClick` on `root/Symbol`, scope G.
   Touch-mode double-tap. Calls `efc.ui.dblCmd`, which toggles Open/Close only when ready (see below). Writes one tag, only when the guards pass.

```python
	efc.ui.dblCmd(self)
```

3. **`root/PB`**: `events.component.onActionPerformed` on `root/PB`, scope G.
   Manual command button. Writes `True` to `Cmd_Close` if `Out_Open` is true, else to `Cmd_Open`, through `efc.ui.cmd(self, m, True, 1)`, which re-checks the Operator level (1) and writes the tag `<tagPath>/<m>`. No audit.

```python
	m = 'Cmd_Close' if self.view.custom.cmd else 'Cmd_Open'
	efc.ui.cmd(self, m, True, 1)
```

### Library functions called by this view (`efc.ui`, `projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.openDynamic(component)`**: picks the window from `dockId`, or from `BY_TYPE[tType]`. For `T_DValve` that is `dw_ValveDiscrete`, which maps to `Docks/ValveDiscrete`. If no window is found, logs a warning and stops. Otherwise it writes `session.custom.efcDw[pageId] = {path, params:{tagPath: dwTagPath or tagPath}}`. It does not check the user's role and does not write to the tag. The `Docks/Region` view shows this path.
- **`efc.ui.cmd(component, member, value, minLevel, audit)`**: returns unless the user's level is at least `minLevel`; otherwise writes `value` to `<tagPath>/<member>` and, with `audit=True`, writes an audit record. The PB button calls it with the chosen `Cmd_*` member, `True` and level 1, no audit.
- **`efc.ui.dblCmd(component)`**: returns immediately unless all of these hold: `useButton` false, `dblCmd` true, `tType` in `DBL_CMD` (only `T_DValve` and `T_Motor`), and the user's level is 1 (Operator) or higher. It then reads `Sts_Opened`, `Mode/Sts_Man`, `Sts_Avail`, `Sts_Intlk`, `Sts_NotPerm`, `Sts_Local` and `Sts_Fault`. It writes nothing unless `Mode/Sts_Man` and `Sts_Avail` are true and `Sts_Intlk`, `Sts_NotPerm`, `Sts_Local` and `Sts_Fault` are all false. When it does write, it sends `Cmd_Close` if `Sts_Opened` is true, else `Cmd_Open`, with `True`. It does not check `Mode/Sts_OOS`. The steward note omits the fault check, which the code does have.
- **Role levels** (`efc.ui.level`): the highest index in `['Guest','Operator','Maintenance','Supervisor','Engineer','Admin']` gives 0 to 5. Operator is 1. Used by the dock; `dblCmd` uses `userLevel >= 1`.
- **`efc.ui.closeDynamic`** is not called from this view. The dock's close button calls it.

## Tag members used

All paths are relative to `tagPath`. Types come from `types/PCLib_Members.csv`.

| Member | Access | Data type | Meaning (PCLib comment) |
|---|---|---|---|
| `Cfg_Tag` | read | STRING[20] | Equipment / instrument tag, e.g. FT-101 |
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Cfg_HasZSO` | read | BOOL | Open limit switch fitted |
| `Cfg_HasZSC` | read | BOOL | Closed limit switch fitted |
| `Out_Open` | read | BOOL | Solenoid output: open (energise) |
| `Sts_Opened` | read | BOOL | Confirmed open |
| `Sts_Closed` | read | BOOL | Confirmed closed |
| `Sts_Fault` | read | BOOL | Any fault present |
| `Sts_Avail` | read | BOOL | Available to Auto/program control |
| `Sts_Local` | read | BOOL | In local control |
| `Sts_Intlk` | read | BOOL | Interlock not healthy |
| `Sts_NotPerm` | read | BOOL | Permissive not healthy |
| `Mode/Sts_Man` | read | BOOL | In Manual (commanded by operator) - MTP Operator |
| `Mode/Sts_OOS` | read | BOOL | Out of service - MTP Offline |
| `Intlk/Sts_FirstOut` | read | INT | First condition to fail (-1 = none) |
| `Intlk/Cfg_CondDesc` | read (indexed by Sts_FirstOut) | ARRAY[0..15] OF STRING[32] | HMI text for condition n |
| `Cmd_Open` | write (PB, double-tap) | BOOL | Operator open (one-shot) |
| `Cmd_Close` | write (PB, double-tap) | BOOL | Operator close (one-shot) |

The alarm expression reads `<tagPath>/*` through `isAlarmActiveFiltered`, not a member. The alarm members `Alm_*` are not referenced here.

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

## Notes and open questions

- The steward note mentions "limit-switch LEDs". This view has no limit-switch indicators. The limit-switch rows are in the dock (`Feedback`).
- `custom.mode` and `custom.con` are defined and bound but never referenced.
- The I tooltip always says "open blocked", whatever the interlock actually drives (`Cfg_IntlkOpen` is not read here).
- The alarm expression checks one Ignition priority at a time (`minPriority = maxPriority = N`, 4 first) for every alarm under `tagPath/*`. It reads Ignition alarms configured on the tags, not the PLC `Alm_*` members the dock shows. The two only agree if the UDT carries matching Ignition alarm definitions.
- A double-tap also opens the dock. Browsers fire two `click` events before `dblclick`, so `onClick` (open the dock) runs as well as `onDoubleClick` (command). This is harmless: the dock opens for the same valve.
- The PB command writes `True` to a one-shot member and never clears it. This relies on the PLC resetting one-shot commands (the PCLib comment says "one-shot").
- The template state (`0` closed, `1` open, `2` transition, `3` fault) is not the PCLib `Sts_State` numbering (`0` transit, `1` closed, `2` open, `3` opening, `4` closing, `5` fault).
