# Analog valve template

Covers `Templates/Valves/Valve_Control`.
Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/Valves/Valve_Control/view.json`
Dynamic window it opens: `Docks/ValveAnalog` (see [ValveAnalog](../../Docks/ValveAnalog.md)).

## Overview

A single-device P&ID symbol for a modulating (analog) control valve (T_CValve). It shows the valve position or demand as a fill colour, an alarm or fault outline, a vertical position bar with a command marker, an interlock (I) badge, a mode line and a status line. It has no command button and no touch command. All control is in the dynamic window.

- **Default size:** 120 x 100 (`props.defaultSize`).
- **Bound to:** one T_CValve instance through `params.tagPath` (default `[default]PID_Demo/FV101`).
- **Opening the dock:** a single click on the symbol runs `efc.ui.openDynamic(self)`. It maps `tType` (or `dockId`) to a window (`T_CValve` gives `dw_ValveAnalog`), then writes `session.custom.efcDw[pageId] = {path, params:{tagPath}}`. The screen's `Docks/Region` embedded view shows that path. Only `tagPath` is passed on; `dwTagPath` overrides it when set.
- **Writes:** none. This template writes no tag and checks no role. The dock does the writes.
- **Generated view:** the dock `Docks/ValveAnalog` is written by `generator/docks/build_docks.py`. This template is not generated.

## How it operates

**Body colour (state).** The body (`elements[2]`, state path) takes `custom.fill` from `custom.state`. Only states 0, 1 and 3 are produced:

| State | Derived from | Body colour | Status text | Status class |
|---|---|---|---|---|
| 0 | value (position if feedback fitted, else demand) at or below 1 % | #9E9E9E | percentage | `State/Stopped` |
| 1 | value above 1 % | #FFFFFF | percentage | `State/Running` |
| 3 | `Sts_Fault` true (checked first) | #3A3A3A | FAULT | `State/Fault` |

State 2 (transition) is never produced by this template, so the `2` branch of `custom.fill` (#C4C4C4) is unreachable. The state is a position threshold, not a limit-switch read. The status text shows the value as a whole-number percentage (`numberFormat(..., "0") + " %"`), taken from `custom.pos` when `custom.fb` is true and from `custom.out` otherwise. Text is `FAULT` in state 3. When `custom.man` is true the status also gets the `Mode/ManualJoined` class.

**Head colour (command).** The actuator head (`elements[1]`) takes `custom.head`. When there is no feedback (`custom.command` = -1) the head uses the body colour. When the demand is above 1 % (`command` = 1) it is white (#FFFFFF). Otherwise it is grey (#9E9E9E).

**Alarm and fault outline.** The outline (`custom.line`) is red (#D50000) when faulted. Otherwise it follows the highest active alarm class under `<tagPath>/*`: 1 cyan #00A3E0, 2 yellow #FFD200, 3 orange #FF7A00, 4 red #D50000. Default #262626. The outline is 8.333 wide when any alarm or fault is active and 4.167 otherwise. The alarm check is the same as in the discrete templates: it reads Ignition alarms on the tag, not the PLC `Alm_*` members.

**Position bar.** A separate SVG (`root/PositionBar`) beside the symbol. It has a white track and two markers:
- A dark grey fill (#4D4D4D) rises from the bottom in proportion to `custom.posC`, which is the position clamped to 0 to 100 %. The fill height is `0.96 * posC` in the 96-unit track.
- A blue triangle (#1F4E99) on the left edge sits at the height of `custom.outC`, the demand clamped to 0 to 100 %.
- The tooltip reads `Position <posC> % / Command <outC> %`.

The bar uses the clamped values, so it does not show a value above 100 % or below 0 %. The status text does not clamp.

**Badges.** `P` is never shown. Its `meta.visible` is the literal expression `false`, and `custom.permMissing` has no binding (see Notes). `I` is shown when `Sts_Intlk` is true. Its tooltip reads "Interlock active - control blocked", followed by the first-out condition text if one exists.

**Mode line.** The `M` label is shown while `custom.man` is true, with class `Mode/ManualSplit`. Unlike the discrete template, there is no `useButton` parameter and no touch-mode switch.

**Name and tooltip.** The label shows `Cfg_Tag`, or the last segment of tagPath if `Cfg_Tag` is empty. The tooltip shows `Cfg_Desc`, if non-empty.

**Security.** Nothing on this template writes to the tag or checks the user's role. Every command is on the dock. This template only opens it.

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `[default]PID_Demo/FV101` | T_CValve instance. All bindings use it as `{view.params.tagPath}`. | Caller; read by bindings and `efc.ui.openDynamic` |
| `tType` | input | `T_CValve` | Type key. `efc.ui.openDynamic` uses it (via BY_TYPE) to pick the window. | Read by `efc.ui.openDynamic`; not referenced in this view's bindings |
| `dockId` | input | `""` | Overrides the window chosen from `tType`. Must be a key of `efc.ui.WINDOWS`. | Read by `efc.ui.openDynamic` only |
| `dwTagPath` | input | `""` | Tag path passed to the dock instead of `tagPath` (when non-empty). | Read by `efc.ui.openDynamic` only |

All four params have `paramDirection: input` and `persistent: true`. No output params.

### View-level custom properties (`custom`)

**Tag mirrors.** Thirteen properties are plain tag mirrors. Each one is an indirect, read-only tag binding (fallback delay 2.5 s, no `bidirectional` flag) to `{view.params.tagPath}` plus the member below. Their defaults are `out` 0.0, `pos` 0.0, `fb` true, `fault` false, `name` and `desc` empty, `man`, `oos`, `local`, `intlk` false, `avail` true, `firstOut` -1 and `firstDesc` empty.

| Group | Members |
|---|---|
| Demand and position | `custom.out` = `Val_Demand` (demand before rate limit, %); `custom.pos` = `Val_Pos` (position, %; feedback, or demand if no feedback); `custom.fb` = `Cfg_HasFbk` |
| Status | `custom.fault` = `Sts_Fault`; `custom.intlk` = `Sts_Intlk` (drives the `I` badge) |
| Mode | `custom.man` = `Mode/Sts_Man` (drives the `M` label); `custom.oos` = `Mode/Sts_OOS` (not referenced) |
| Availability | `custom.avail` = `Sts_Avail` (not referenced); `custom.local` = `Sts_Local` (not referenced). Neither member is in the PCLib T_CValve type. See Notes. |
| Interlock first-out | `custom.firstOut` = `Intlk/Sts_FirstOut` (-1 = none); `custom.firstDesc` = `Intlk/Cfg_CondDesc/{firstOut}` (used by the `I` tooltip) |
| Config | `custom.name` = `Cfg_Tag` (falls back to the last segment of tagPath); `custom.desc` = `Cfg_Desc` (tooltip) |

**Computed properties.** These are expressions. The table gives the full source.

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.state` | `0` | expr | `if(coalesce({view.custom.fault}, false), 3, if((if(coalesce({view.custom.fb}, true), coalesce({view.custom.pos}, 0), coalesce({view.custom.out}, 0))) > 1, 1, 0))` | 3 if fault, 1 if the selected value is above 1 %, else 0. Drives fill, status and outline width. |
| `view.custom.command` | `0` | expr | `if(coalesce({view.custom.fb}, true), if(coalesce({view.custom.out}, 0) > 1, 1, 0), -1)` | -1 if no feedback, 1 if demand is above 1 %, else 0. Selects head colour. |
| `view.custom.mode` | `0` | expr | `if(coalesce({view.custom.man}, false), 1, 0)` | 1/0 from `man`. Not referenced by any binding or script in this view. |
| `view.custom.alarm` | `0` | expr | `if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 4, 4, 0, 1, 0), false), false)), 4, if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 3, 3, 0, 1, 0), false), false)), 3, if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 2, 2, 0, 1, 0), false), false)), 2, if(forceQuality(coalesce(try(isAlarmActiveFiltered({view.params.tagPath} + "/*", "*", "*", 1, 1, 0, 1, 0), false), false)), 1, 0))))` | Highest active alarm class 0-4 (4 checked first). Drives outline colour and width. |
| `view.custom.fill` | `"#9E9E9E"` | expr | `case({view.custom.state}, 0, "#9E9E9E", 1, "#FFFFFF", 2, "#C4C4C4", 3, "#3A3A3A", "#C4C4C4")` | Body colour from `state`. |
| `view.custom.head` | `"#9E9E9E"` | expr | `if({view.custom.command} < 0, {view.custom.fill}, if({view.custom.command} = 1, "#FFFFFF", "#9E9E9E"))` | Head colour: `fill` if `command` < 0, #FFFFFF if `command` = 1, else #9E9E9E. |
| `view.custom.line` | `"#262626"` | expr | `if({view.custom.state} = 3, "#D50000", case({view.custom.alarm}, 1, "#00A3E0", 2, "#FFD200", 3, "#FF7A00", 4, "#D50000", "#262626"))` | Outline colour: #D50000 when faulted; else by alarm class; default #262626. |
| `view.custom.lw` | `4.167` | expr | `if({view.custom.alarm} > 0 \|\| {view.custom.state} = 3, 8.333, 4.167)` | Outline width: 8.333 when `alarm` > 0 or faulted, else 4.167. |
| `view.custom.con` | `"#262626"` | expr | `if({view.custom.state} = 3, "#F2F2F2", "#262626")` | Not referenced anywhere in the view (defined and bound, unused). |
| `view.custom.posC` | `0.0` | expr | `max(0, min(100, coalesce(coalesce({view.custom.pos}, 0), 0)))` | `pos` clamped to 0-100. Drives the position fill. |
| `view.custom.outC` | `0.0` | expr | `max(0, min(100, coalesce(coalesce({view.custom.out}, 0), 0)))` | `out` clamped to 0-100. Drives the command marker. |

`view.custom.permMissing` (default `false`) has no binding in this view. Nothing drives it, and `root/P` is hard-off (see Notes).

### Component-level custom properties

None. The components carry no `custom` properties.

### Session, page and message payloads

None. The template reads no `session.*` or `page.*` values and sends no messages. Its only use of `session` is inside `efc.ui.openDynamic`, which writes `session.custom.efcDw` (see the Scripts section).

## Bindings reference

Total: **44 bindings**: 24 at view root (`custom.*`) and 20 on components. Types: 31 `expr`, 13 `tag`. No transforms. `params.*` entries have `paramDirection` only and are not bindings.

- View root: 13 `tag` (`custom.out`, `pos`, `fb`, `fault`, `name`, `desc`, `man`, `oos`, `avail`, `local`, `intlk`, `firstOut`, `firstDesc`) and 11 `expr` (`custom.state`, `command`, `mode`, `alarm`, `fill`, `head`, `line`, `con`, `lw`, `posC`, `outC`).
- Components: all 20 are `expr`.

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
| root/Symbol | `props.elements[1].fill.paint` | expr | `{view.custom.head}` | Head fill colour |
| root/Symbol | `props.elements[1].stroke.paint` | expr | `{view.custom.line}` | Head outline colour |
| root/Symbol | `props.elements[1].stroke.width` | expr | `{view.custom.lw}` | Head outline width |
| root/Symbol | `props.elements[2].fill.paint` | expr | `{view.custom.fill}` | Body fill colour |
| root/Symbol | `props.elements[2].stroke.paint` | expr | `{view.custom.line}` | Body outline colour |
| root/Symbol | `props.elements[2].stroke.width` | expr | `{view.custom.lw}` | Body outline width |

### `root/P`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/P | `meta.visible` | expr | `false` | Shown while expression is true (always false) |

### `root/I`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/I | `meta.visible` | expr | `coalesce({view.custom.intlk}, false)` | Shown while expression is true |
| root/I | `meta.tooltip.text` | expr | `"Interlock active - " + "control" + " blocked" + if(coalesce({view.custom.firstOut}, -1) >= 0 && len(coalesce({view.custom.firstDesc}, "")) > 0, ": " + {view.custom.firstDesc}, "")` | Tooltip |

### `root/StatusGroup`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/StatusGroup/M | `meta.visible` | expr | `coalesce({view.custom.man}, false)` | Shown while expression is true |
| root/StatusGroup/M | `props.style.classes` | expr | `if(coalesce({view.custom.man}, false), "Mode/ManualSplit", "Util/Collapsed")` | CSS class(es) selected by state |
| root/StatusGroup/Status | `props.text` | expr | `if({view.custom.state} = 3, "FAULT", numberFormat(if(coalesce({view.custom.fb}, true), coalesce({view.custom.pos}, 0), coalesce({view.custom.out}, 0)), "0") + " %")` | Text content |
| root/StatusGroup/Status | `props.style.classes` | expr | `case({view.custom.state}, 0, "State/Stopped", 1, "State/Running", 2, "State/Transition", 3, "State/Fault", "State/Unknown") + " Text/Mod/Tabular" + if(coalesce({view.custom.man}, false), " Mode/ManualJoined", "")` | CSS class(es) selected by state |

### `root/PositionBar`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/PositionBar | `props.elements[1].y` | expr | `98 - 0.96 * {view.custom.posC}` | Position fill top edge |
| root/PositionBar | `props.elements[1].height` | expr | `0.96 * {view.custom.posC}` | Position fill height |
| root/PositionBar | `props.elements[2].d` | expr | `"M0 " + toStr(91 - 0.96 * {view.custom.outC}) + " L7 " + toStr(98 - 0.96 * {view.custom.outC}) + " L0 " + toStr(105 - 0.96 * {view.custom.outC}) + " Z"` | Command marker path |
| root/PositionBar | `meta.tooltip.text` | expr | `"Position " + numberFormat({view.custom.posC}, "0") + " % / Command " + numberFormat({view.custom.outC}, "0") + " %"` | Tooltip |

`root/P` has 1 binding, `root/I` 2, `root/Tag` 3, `root/Symbol` 6, `root/StatusGroup/M` 2, `root/StatusGroup/Status` 2 and `root/PositionBar` 4. That is 20 on components.

## Scripts reference

Total: **1 event script**, no `customMethods`, no `messageHandlers`, no property-change scripts, no script transforms. `view.scripts` is absent.

1. **`root/Symbol`**: `events.dom.onClick` on `root/Symbol`, scope G.
   Opens the dynamic window for this tag. Calls `efc.ui.openDynamic`, which writes `session.custom.efcDw` (see below). No tag writes.

```python
	efc.ui.openDynamic(self)
```

### Library functions called by this view (`efc.ui`, `projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.openDynamic(component)`**: picks the window from `dockId`, or from `BY_TYPE[tType]`. For `T_CValve` that is `dw_ValveAnalog`, which maps to `Docks/ValveAnalog`. If no window is found, it logs a warning and stops. Otherwise it writes `session.custom.efcDw[pageId] = {path, params:{tagPath: dwTagPath or tagPath}}`. It does not check the user's role and does not write to the tag.

## Tag members used

All paths are relative to `tagPath`. Types come from `types/PCLib_Members.csv`, except where marked.

| Member | Access | Data type | Meaning (PCLib comment) |
|---|---|---|---|
| `Cfg_Tag` | read | STRING[20] | Equipment / instrument tag, e.g. FT-101 |
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Cfg_HasFbk` | read | BOOL | Position feedback fitted |
| `Val_Demand` | read | REAL | Active demand before rate limit (%) |
| `Val_Pos` | read | REAL | Position (%) - feedback, or demand if no feedback |
| `Sts_Fault` | read | BOOL | Any fault present |
| `Sts_Intlk` | read | BOOL | Interlock active |
| `Mode/Sts_Man` | read | BOOL | In Manual (commanded by operator) - MTP Operator |
| `Mode/Sts_OOS` | read | BOOL | Out of service - MTP Offline (bound, not used) |
| `Sts_Avail` | read | BOOL | **Not in `PCLib_Members.csv` for T_CValve.** Defined in `tags/T_CValve_Demo_UDT.json` only. Bound, not used. |
| `Sts_Local` | read | BOOL | **Not in `PCLib_Members.csv` for T_CValve.** Defined in `tags/T_CValve_Demo_UDT.json` only. Bound, not used. |
| `Intlk/Sts_FirstOut` | read | INT | First condition to fail (-1 = none) |
| `Intlk/Cfg_CondDesc` | read (indexed by Sts_FirstOut) | ARRAY[0..15] OF STRING[32] | HMI text for condition n |

The alarm expression reads `<tagPath>/*` through `isAlarmActiveFiltered`, not a member. The PLC alarms `Alm_PosDev`, `Alm_FbkBad` and `Alm_IntlkTrip` are not referenced here.

The template writes no members.

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
  - `PositionBar` (ia.shapes.svg)
```

## Notes and open questions

- **Members not in PCLib.** `Sts_Avail` and `Sts_Local` are bound (`custom.avail`, `custom.local`) but are not defined for T_CValve in `types/PCLib_Members.csv`. They exist only in the demo UDT `tags/T_CValve_Demo_UDT.json`. Neither value is used by any component, so there is no visible effect, but the bindings would read members the PCLib type does not define. Either add them to the type or remove the bindings.
- **Unused custom properties.** `custom.oos`, `custom.avail`, `custom.local`, `custom.mode` and `custom.con` are bound or defined and never referenced. `custom.permMissing` is defined and unbound.
- **P badge never shows.** `root/P` `meta.visible` is the literal `false`. Compare the discrete template, which drives its `P` badge from `Sts_NotPerm`. This type has no permissive-missing member, so the badge is disabled rather than wired. Confirm that this is intended.
- **Dead state branch.** No path produces state 2, so `custom.fill`'s `2` branch (#C4C4C4) and the `State/Transition` class in the status are unreachable. There is also no opening or closing text, unlike the discrete template.
- **Threshold, not feedback.** The state (open or closed) comes from a 1 % threshold on `pos` or `out`. It does not read a limit switch. With feedback fitted, a valve can show state 0 while the command is above 1 % if feedback lags.
- **Position bar clamping.** The bar uses clamped values (`posC`, `outC`). The status text does not clamp, so a value above 100 % is shown as-is in the text but not in the bar.
- **Alarm source.** As in the discrete templates, the outline reads Ignition alarms on the tag. It does not read `Alm_PosDev`, `Alm_FbkBad` or `Alm_IntlkTrip`. The two only agree if the UDT carries matching Ignition alarm definitions.
- **Interlock tooltip.** The I tooltip says "control blocked" whatever the interlock actually drives. This template does not read `Cfg_IntlkPos` or `Sts_Mode`.
- **No command path on this template.** Because there is no button and no double-tap, all commands go through the dock. The dock uses `efc.ui.cmd`, which checks the role and writes the tag. Nothing on this template bypasses it.
