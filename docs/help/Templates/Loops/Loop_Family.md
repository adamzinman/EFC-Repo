# PID loop templates (B1 to B4)

Covers `Templates/Loops/Loop_B1_Bar`, `Templates/Loops/Loop_B2_Horizontal`, `Templates/Loops/Loop_B3_Sparkline` and `Templates/Loops/Loop_B4_Column`.
Sources: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/Loops/<name>/view.json`
Dynamic window they open: `Docks/Loop` (dock `dw_Loop`, chosen from `tType` `T_PID`; see [Loop](../../Docks/Loop.md)).

## Overview

These four views are single-loop symbols for a PID controller (`T_PID`). Each shows the PV on a scale with the setpoint, the high and low deviation alarm lines, the output, the mode, and a deviation alarm outline. The views are display only. They write no tags and have no command buttons. A single click opens the loop dock.

- **Default sizes** (`props.defaultSize`): B1 150 x 156, B2 260 x 92, B3 172 x 184, B4 104 x 196.
- **Bound to:** one T_PID instance through `params.tagPath`.
- **Opening the dock:** a single click runs `efc.ui.openDynamic(self)`. It maps `tType` (`T_PID`) through `BY_TYPE` to `dw_Loop`, then writes `session.custom.efcDw[pageId] = {path: 'Docks/Loop', params: {tagPath}}`. The screen's `Docks/Region` shows that path. `dwTagPath` replaces `tagPath` when it is set, and `dockId` overrides the window.
- **Generated view:** these views are written by `generator/pid_loops/generate_loops.py`. That script writes `PID/Templates/Loop_B1_Bar` to `Loop_B4_Column` under `projects/PID_Loops/`, not `Templates/Loops/` in EFC_Library. Check which copy is current before editing either (see Open questions).

### Differences between the views

| View | Default size | Layout (root is a column) | Components (incl. root) | Bindings: view root / components / total | Scripts |
|---|---|---|---|---|---|
| `Loop_B1_Bar` | 150 x 156 | Header row. Body row: vertical PV bar beside a value column (PV, units, SP). Output row (label and value). Full-width output bar row. | 22 | 21 / 16 / 37 | 1 event |
| `Loop_B2_Horizontal` | 260 x 92 | Header row. Middle row: value column (PV, units, SP) beside a horizontal PV bar. Output row: label, horizontal output bar, value, `%`. | 22 | 21 / 17 / 38 | 1 event |
| `Loop_B3_Sparkline` | 172 x 184 | Header row. Body row: vertical PV bar beside a value column (PV, units, SP, deviation). One-minute sparkline. Output row (label and value). Output bar row. | 25 | 23 / 21 / 44 | 1 event, 1 transform |
| `Loop_B4_Column` | 104 x 196 | Narrow column: title, mode chip, PV, units, SP. Row of PV and output bars side by side. PV and OUT labels below. | 20 | 21 / 17 / 38 | 1 event |

The four views share the same params, the same view-level custom property definitions (B3 adds two), the same click script and the same header. Everything else differs (layout, SVG element indexes and component bindings), so the bindings and component tree are given per view below. The params, custom properties, click script, tag members and operating rules apply to all four views.

## How it operates

**Title.** The title is `custom.name`: the `label` parameter if set, otherwise the last segment of `tagPath`.

**Alarm outline and icon.** `custom.alarm` is true when either deviation alarm is active (`Alm_DevH/Sts_Active` or `Alm_DevL/Sts_Active`). The card border then becomes 2 px orange (`#FF7A00`) and the orange alarm icon shows. No other alarm changes these views. In particular `Alm_PVBad` is not read.

**Mode chip.** The chip shows `MAN`, `AUTO` or `CAS` from `Sts_Mode` (0, 1, 2). MAN has a dark chip with white text. CAS has a light chip with blue text. AUTO and any other code have a light grey chip. Track (3) and Intlk (4) show `---`.

**PV bar and markers.** `pvPct` is (PV - `Cfg_PVMin`) / (`Cfg_PVMax` - `Cfg_PVMin`) x 100, clamped to 0 to 100. A zero span uses a divisor of 0.000001, so the bar goes to 0 or 100. The high marker sits at `almHi` (SP + `devH`) and the low marker at `almLo` (SP - `devL`), both as percent of scale and clamped. The setpoint triangle sits at SP. If a deviation limit is 0, its marker sits on SP.

**Values.** PV, SP and output show one decimal. The units text (`Cfg_PVEU`) follows the PV value (B4 shows it on its own row, and B4's SP text has an `SP ` prefix). Output is shown as a value and as a bar clamped to 0 to 100 %.

**Per view:**

- **B1:** vertical PV bar (88 SVG units tall) with markers and setpoint triangle, a value column, and an output bar along the bottom.
- **B2:** horizontal PV bar. The band between the two alarm lines (`loPct` to `hiPct`) is drawn behind the PV fill, with markers and a setpoint triangle on the bar.
- **B3:** as B1, plus a deviation text line `Δ` = PV - SP. The text is highlighted when |PV - SP| is greater than `devAlm`. A one-minute sparkline shows PV (solid) and SP (dashed).
- **B4:** narrow column. The PV fill and the output fill are two bars side by side (82 units tall). Labels PV and OUT sit below them.

**Sparkline (B3 only).** Every 5 s the `now(5000)` expression re-runs the transform (see Scripts). It reads up to 40 samples of `Val_PV` and `Val_SP` from the last minute of tag history, scales both traces to one range with 15 % padding (at least 0.5 EU), and returns two SVG path strings. If the history query fails or returns fewer than two complete samples, both paths are empty and the sparkline is blank.

**Commands and writes.** None. The only script is the click handler. No `Cmd_*` member is written and no role check applies, because nothing can be commanded from these views.

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `[default]PID_Demo/TIC101` | T_PID instance. Every tag binding uses it as `{view.params.tagPath}`. | Caller. Read by all bindings and by `efc.ui.openDynamic`. |
| `label` | input | `""` | Title override. Empty means the last segment of `tagPath`. | Caller. Read by `custom.name`. Not passed by `openDynamic`. |
| `tType` | input | `T_PID` | Type key used to pick the dock. | Caller. Read by `efc.ui.openDynamic` (through `BY_TYPE`). Not referenced by any binding in these views. |
| `dockId` | input | `""` | Dock id that overrides the window picked from `tType`. Must be a key of `efc.ui.WINDOWS`. | Read by `efc.ui.openDynamic` only. |
| `dwTagPath` | input | `""` | Tag path passed to the dock instead of `tagPath` when non-empty. | Read by `efc.ui.openDynamic` only. |

All five have `paramDirection: input` and `persistent: true`. There are no output params.

### View-level custom properties (`custom`)

No view-level custom property is set by a script. Each is bound. Tag bindings use mode `indirect` with a 2.5 s fallback delay, and `{1}` resolves to `{view.params.tagPath}`. The table is generated from `Loop_B3_Sparkline`, the superset, and every row except the two B3-only rows is identical in B1, B2 and B4 (checked by comparing the JSON).

In B1, B2 and B4, the eleven rows `pv`, `sp`, `out`, `mode`, `devH`, `devL`, `devHAct`, `devLAct`, `pvLo`, `pvHi` and `units` are plain tag mirrors, and the other ten are expressions over them. B3 adds `devAlm` (a tag mirror of `Alm_DevH/Cfg_Lim`) and `spark` (an expression with a transform).

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.pv` | `0` | tag | `{view.params.tagPath}/Val_PV` | PV (EU) from `Val_PV`. Drives the PV value text and `pvPct`. |
| `view.custom.sp` | `0` | tag | `{view.params.tagPath}/Val_SP` | Active setpoint (EU) from `Val_SP`. Drives the SP text and `spPct`, and the base of `almHi` and `almLo`. |
| `view.custom.out` | `0` | tag | `{view.params.tagPath}/Out_CV` | Controller output (%) from `Out_CV`. Drives the output text and `outPct`. |
| `view.custom.mode` | `0` | tag | `{view.params.tagPath}/Sts_Mode` | Mode code from `Sts_Mode` (0 Man, 1 Auto, 2 Cas, 3 Track, 4 Intlk). Drives `modeText` and the mode chip colours. |
| `view.custom.devH` | `0` | tag | `{view.params.tagPath}/Alm_DevH/Cfg_Lim` | High deviation limit (EU) from `Alm_DevH/Cfg_Lim`. Used for `almHi`. Its value is not shown. |
| `view.custom.devL` | `0` | tag | `{view.params.tagPath}/Alm_DevL/Cfg_Lim` | Low deviation limit (EU) from `Alm_DevL/Cfg_Lim`. Used for `almLo`. |
| `view.custom.devHAct` | `false` | tag | `{view.params.tagPath}/Alm_DevH/Sts_Active` | High deviation alarm state from `Alm_DevH/Sts_Active`. One input to `alarm`. |
| `view.custom.devLAct` | `false` | tag | `{view.params.tagPath}/Alm_DevL/Sts_Active` | Low deviation alarm state from `Alm_DevL/Sts_Active`. One input to `alarm`. |
| `view.custom.almHi` | `0` | expr | `{view.custom.sp} + {view.custom.devH}` | Upper alarm line (EU): `sp` + `devH`. Drives `hiPct`. |
| `view.custom.almLo` | `0` | expr | `{view.custom.sp} - {view.custom.devL}` | Lower alarm line (EU): `sp` - `devL`. Drives `loPct`. |
| `view.custom.pvLo` | `0` | tag | `{view.params.tagPath}/Cfg_PVMin` | Scale minimum (EU) from `Cfg_PVMin`. Base of every percent calculation. |
| `view.custom.pvHi` | `0` | tag | `{view.params.tagPath}/Cfg_PVMax` | Scale maximum (EU) from `Cfg_PVMax`. |
| `view.custom.units` | `""` | tag | `{view.params.tagPath}/Cfg_PVEU` | Engineering units text from `Cfg_PVEU`. Shown next to the PV value. |
| `view.custom.pvPct` | `0` | expr | `min(100, max(0, ({view.custom.pv} - {view.custom.pvLo}) / max(0.000001, {view.custom.pvHi} - {view.custom.pvLo}) * 100))` | PV as percent of scale, clamped to 0 to 100. Drives the PV fill. |
| `view.custom.spPct` | `0` | expr | `min(100, max(0, ({view.custom.sp} - {view.custom.pvLo}) / max(0.000001, {view.custom.pvHi} - {view.custom.pvLo}) * 100))` | SP as percent of scale, clamped to 0 to 100. Drives the setpoint marker. |
| `view.custom.hiPct` | `0` | expr | `min(100, max(0, ({view.custom.almHi} - {view.custom.pvLo}) / max(0.000001, {view.custom.pvHi} - {view.custom.pvLo}) * 100))` | High alarm line as percent of scale, clamped to 0 to 100. Drives the high marker. |
| `view.custom.loPct` | `0` | expr | `min(100, max(0, ({view.custom.almLo} - {view.custom.pvLo}) / max(0.000001, {view.custom.pvHi} - {view.custom.pvLo}) * 100))` | Low alarm line as percent of scale, clamped to 0 to 100. Drives the low marker. |
| `view.custom.outPct` | `0` | expr | `min(100, max(0, {view.custom.out}))` | Output clamped to 0 to 100. Drives the output bar. |
| `view.custom.alarm` | `false` | expr | `{view.custom.devHAct} \|\| {view.custom.devLAct}` | True when `devHAct` or `devLAct` is true. Drives the card border and the alarm icon. |
| `view.custom.modeText` | `""` | expr | `case({view.custom.mode}, 0, "MAN", 1, "AUTO", 2, "CAS", "---")` | `MAN`, `AUTO` or `CAS`; `---` for any other code (Track, Intlk). |
| `view.custom.name` | `""` | expr | `if(len({view.params.label}) > 0, {view.params.label}, substring({view.params.tagPath}, lastIndexOf({view.params.tagPath}, "/") + 1))` | Label parameter if set, else the last segment of `tagPath`. Shown as the title. |
| `view.custom.devAlm` (B3 only) | `10` | tag | `{view.params.tagPath}/Alm_DevH/Cfg_Lim` | B3 only. High deviation limit from `Alm_DevH/Cfg_Lim`, used as the threshold for the deviation highlight (default 10). Same tag as `devH`. |
| `view.custom.spark` (B3 only) | `{"pv": "", "sp": ""}` | expr | `now(5000)` | B3 only. `{pv, sp}` path strings for the sparkline. Recomputed every 5 s by the `now(5000)` trigger and the transform (see Scripts). |

### Component-level custom properties

None. No component in these views has a `custom` property.

### Session, page and message payloads

The views read no session, page or message values. The click writes `session.custom.efcDw[<pageId>]` through `efc.ui.openDynamic`. See Scripts.

## Bindings reference

Totals: **B1 37** (21 view root, 16 components), **B2 38** (21 / 17), **B3 44** (23 / 21), **B4 38** (21 / 17). The types are:

- `Loop_B1_Bar`: view root 21 (10 expr, 11 tag); components 16 (12 expr, 4 property).
- `Loop_B2_Horizontal`: view root 21 (10 expr, 11 tag); components 17 (13 expr, 4 property).
- `Loop_B3_Sparkline`: view root 23 (11 expr, 12 tag); components 21 (15 expr, 6 property).
- `Loop_B4_Column`: view root 21 (10 expr, 11 tag); components 17 (13 expr, 4 property).

### Loop_B1_Bar (37 bindings: 21 view root, 16 components)

#### View root

The view-root bindings drive the custom properties. Each one is listed with its full source in [View-level custom properties](#view-level-custom-properties-custom) above.

#### `root` (container)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root` | `props.style.border` | expr | `if({view.custom.alarm}, "2px solid #FF7A00", "1px solid #A6A6A6")` | Card border: 2 px orange (`#FF7A00`) when `alarm` is true, else 1 px grey (`#A6A6A6`). |

#### `root/header`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/header/title/tag` | `props.text` | property | `view.custom.name` (property binding) | Loop name (`custom.name`). |
| `root/header/title/alarmIcon` | `position.display` | property | `view.custom.alarm` (property binding) | Alarm icon shown while `alarm` is true. |
| `root/header/mode` | `props.text` | property | `view.custom.modeText` (property binding) | Mode text from `modeText`: MAN, AUTO or CAS; `---` for other codes (Track, Intlk). |
| `root/header/mode` | `props.style.backgroundColor` | expr | `case({view.custom.mode}, 0, "#3A3A3A", 2, "#E6E6E6", "#EDEDED")` | Mode chip fill: `#3A3A3A` for MAN, `#E6E6E6` for CAS, `#EDEDED` otherwise. |
| `root/header/mode` | `props.style.color` | expr | `case({view.custom.mode}, 0, "#FFFFFF", 2, "#1F4E99", "#4D4D4D")` | Mode chip text: `#FFFFFF` for MAN, `#1F4E99` for CAS, `#4D4D4D` otherwise. |

#### `root/body`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/body/pvBar` | `props.elements[1].height` | expr | `88 * {view.custom.pvPct} / 100` | PV fill height: 88 SVG units x `pvPct` / 100 (fill element is index 1). |
| `root/body/pvBar` | `props.elements[1].y` | expr | `88 - 88 * {view.custom.pvPct} / 100` | PV fill top edge, so the fill grows up from the bottom. |
| `root/body/pvBar` | `props.elements[2].y` | expr | `88 - 88 * {view.custom.hiPct} / 100 - 1` | High alarm marker (`hi`, index 2) at `hiPct`. |
| `root/body/pvBar` | `props.elements[3].y` | expr | `88 - 88 * {view.custom.loPct} / 100 - 1` | Low alarm marker (`lo`, index 3) at `loPct`. |
| `root/body/pvBar` | `props.elements[4].d` | expr | `"M1," + (88 - 88*{view.custom.spPct}/100 - 5) + " L8," + (88 - 88*{view.custom.spPct}/100) + " L1," + (88 - 88*{view.custom.spPct}/100 + 5) + " Z"` | Setpoint marker (`sp`, index 4): triangle path centred on `spPct`. |
| `root/body/vals/pv` | `props.text` | expr | `numberFormat({view.custom.pv}, "#,##0.0")` | PV value, one decimal. |
| `root/body/vals/units` | `props.text` | property | `view.custom.units` (property binding) | Engineering units (`custom.units`). |
| `root/body/vals/spRow/sp` | `props.text` | expr | `numberFormat({view.custom.sp}, "#,##0.0")` | SP value, one decimal. |

#### `root/outRow`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/outRow/outVal/out` | `props.text` | expr | `numberFormat({view.custom.out}, "#,##0.0")` | Output value, one decimal. |

#### `root/outBarRow`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/outBarRow/outBar` | `props.elements[1].width` | expr | `2 * {view.custom.outPct}` | Output bar fill width: 2 SVG units per percent of `outPct` (bar is 200 units wide). |

### Loop_B2_Horizontal (38 bindings: 21 view root, 17 components)

#### View root

The view-root bindings drive the custom properties. Each one is listed with its full source in [View-level custom properties](#view-level-custom-properties-custom) above.

#### `root` (container)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root` | `props.style.border` | expr | `if({view.custom.alarm}, "2px solid #FF7A00", "1px solid #A6A6A6")` | Card border: 2 px orange (`#FF7A00`) when `alarm` is true, else 1 px grey (`#A6A6A6`). |

#### `root/header`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/header/title/tag` | `props.text` | property | `view.custom.name` (property binding) | Loop name (`custom.name`). |
| `root/header/title/alarmIcon` | `position.display` | property | `view.custom.alarm` (property binding) | Alarm icon shown while `alarm` is true. |
| `root/header/mode` | `props.text` | property | `view.custom.modeText` (property binding) | Mode text from `modeText`: MAN, AUTO or CAS; `---` for other codes (Track, Intlk). |
| `root/header/mode` | `props.style.backgroundColor` | expr | `case({view.custom.mode}, 0, "#3A3A3A", 2, "#E6E6E6", "#EDEDED")` | Mode chip fill: `#3A3A3A` for MAN, `#E6E6E6` for CAS, `#EDEDED` otherwise. |
| `root/header/mode` | `props.style.color` | expr | `case({view.custom.mode}, 0, "#FFFFFF", 2, "#1F4E99", "#4D4D4D")` | Mode chip text: `#FFFFFF` for MAN, `#1F4E99` for CAS, `#4D4D4D` otherwise. |

#### `root/mid`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/mid/vals/pvRow/pv` | `props.text` | expr | `numberFormat({view.custom.pv}, "#,##0.0")` | PV value, one decimal. |
| `root/mid/vals/pvRow/units` | `props.text` | property | `view.custom.units` (property binding) | Engineering units (`custom.units`). |
| `root/mid/vals/spRow/sp` | `props.text` | expr | `numberFormat({view.custom.sp}, "#,##0.0")` | SP value, one decimal. |
| `root/mid/barWrap/pvBar` | `props.elements[1].x` | expr | `2 * {view.custom.loPct}` | Alarm band (`band`, index 1) start: 2 units x `loPct`. |
| `root/mid/barWrap/pvBar` | `props.elements[1].width` | expr | `2 * max(0, {view.custom.hiPct} - {view.custom.loPct})` | Alarm band width: 2 units x (`hiPct` - `loPct`), never negative. |
| `root/mid/barWrap/pvBar` | `props.elements[2].width` | expr | `2 * {view.custom.pvPct}` | PV fill width (`fill`, index 2): 2 units x `pvPct`. |
| `root/mid/barWrap/pvBar` | `props.elements[3].x` | expr | `2 * {view.custom.loPct} - 1` | Low alarm marker (`lo`, index 3) position: 2 x `loPct` - 1. |
| `root/mid/barWrap/pvBar` | `props.elements[4].x` | expr | `2 * {view.custom.hiPct} - 1` | High alarm marker (`hi`, index 4) position: 2 x `hiPct` - 1. |
| `root/mid/barWrap/pvBar` | `props.elements[5].d` | expr | `"M" + (2*{view.custom.spPct} - 5) + ",0 L" + (2*{view.custom.spPct} + 5) + ",0 L" + (2*{view.custom.spPct}) + ",7 Z"` | Setpoint marker (`sp`, index 5): triangle centred on `spPct`. |

#### `root/outRow`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/outRow/ob/outBar` | `props.elements[1].width` | expr | `2 * {view.custom.outPct}` | Output bar fill width: 2 units per percent of `outPct`. |
| `root/outRow/out` | `props.text` | expr | `numberFormat({view.custom.out}, "#,##0.0")` | Output value, one decimal. |

### Loop_B3_Sparkline (44 bindings: 23 view root, 21 components)

#### View root

The view-root bindings drive the custom properties. Each one is listed with its full source in [View-level custom properties](#view-level-custom-properties-custom) above.

#### `root` (container)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root` | `props.style.border` | expr | `if({view.custom.alarm}, "2px solid #FF7A00", "1px solid #A6A6A6")` | Card border: 2 px orange (`#FF7A00`) when `alarm` is true, else 1 px grey (`#A6A6A6`). |

#### `root/header`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/header/title/tag` | `props.text` | property | `view.custom.name` (property binding) | Loop name (`custom.name`). |
| `root/header/title/alarmIcon` | `position.display` | property | `view.custom.alarm` (property binding) | Alarm icon shown while `alarm` is true. |
| `root/header/mode` | `props.text` | property | `view.custom.modeText` (property binding) | Mode text from `modeText`: MAN, AUTO or CAS; `---` for other codes (Track, Intlk). |
| `root/header/mode` | `props.style.backgroundColor` | expr | `case({view.custom.mode}, 0, "#3A3A3A", 2, "#E6E6E6", "#EDEDED")` | Mode chip fill: `#3A3A3A` for MAN, `#E6E6E6` for CAS, `#EDEDED` otherwise. |
| `root/header/mode` | `props.style.color` | expr | `case({view.custom.mode}, 0, "#FFFFFF", 2, "#1F4E99", "#4D4D4D")` | Mode chip text: `#FFFFFF` for MAN, `#1F4E99` for CAS, `#4D4D4D` otherwise. |

#### `root/body`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/body/pvBar` | `props.elements[1].height` | expr | `62 * {view.custom.pvPct} / 100` | PV fill height: 62 SVG units x `pvPct` / 100. |
| `root/body/pvBar` | `props.elements[1].y` | expr | `62 - 62 * {view.custom.pvPct} / 100` | PV fill top edge. |
| `root/body/pvBar` | `props.elements[2].y` | expr | `62 - 62 * {view.custom.hiPct} / 100 - 1` | High alarm marker (`hi`) at `hiPct`. |
| `root/body/pvBar` | `props.elements[3].y` | expr | `62 - 62 * {view.custom.loPct} / 100 - 1` | Low alarm marker (`lo`) at `loPct`. |
| `root/body/pvBar` | `props.elements[4].d` | expr | `"M1," + (62 - 62*{view.custom.spPct}/100 - 5) + " L8," + (62 - 62*{view.custom.spPct}/100) + " L1," + (62 - 62*{view.custom.spPct}/100 + 5) + " Z"` | Setpoint marker (`sp`) triangle at `spPct`. |
| `root/body/vals/pvRow/pv` | `props.text` | expr | `numberFormat({view.custom.pv}, "#,##0.0")` | PV value, one decimal. |
| `root/body/vals/pvRow/units` | `props.text` | property | `view.custom.units` (property binding) | Engineering units (`custom.units`). |
| `root/body/vals/spRow/sp` | `props.text` | expr | `numberFormat({view.custom.sp}, "#,##0.0")` | SP value, one decimal. |
| `root/body/vals/dev` | `props.text` | expr | `"Δ " + if({view.custom.pv} - {view.custom.sp} >= 0, "+", "−") + numberFormat(abs({view.custom.pv} - {view.custom.sp}), "#,##0.0")` | Deviation text: `Δ `, then `+` or `−`, then abs(PV - SP) to one decimal. |
| `root/body/vals/dev` | `props.style.backgroundColor` | expr | `if(abs({view.custom.pv} - {view.custom.sp}) > {view.custom.devAlm}, "#FFFFFF", "#EDEDED")` | Highlight fill `#FFFFFF` when abs(PV - SP) is greater than `devAlm`; otherwise `#EDEDED`. |
| `root/body/vals/dev` | `props.style.color` | expr | `if(abs({view.custom.pv} - {view.custom.sp}) > {view.custom.devAlm}, "#8F4500", "#4D4D4D")` | Text `#8F4500` when abs(PV - SP) is greater than `devAlm`; otherwise `#4D4D4D`. |

#### `root/sparkWrap`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/sparkWrap/spark` | `props.elements[1].d` | property | `view.custom.spark.sp` (property binding) | SP trace (dashed, `#1F4E99`, index 1) path string from `custom.spark.sp`. |
| `root/sparkWrap/spark` | `props.elements[2].d` | property | `view.custom.spark.pv` (property binding) | PV trace (solid, `#1F1F1F`, index 2) path string from `custom.spark.pv`. |

#### `root/outRow`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/outRow/outVal/out` | `props.text` | expr | `numberFormat({view.custom.out}, "#,##0.0")` | Output value, one decimal. |

#### `root/outBarRow`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/outBarRow/outBar` | `props.elements[1].width` | expr | `2 * {view.custom.outPct}` | Output bar fill width: 2 units per percent of `outPct`. |

### Loop_B4_Column (38 bindings: 21 view root, 17 components)

#### View root

The view-root bindings drive the custom properties. Each one is listed with its full source in [View-level custom properties](#view-level-custom-properties-custom) above.

#### `root` (container)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root` | `props.style.border` | expr | `if({view.custom.alarm}, "2px solid #FF7A00", "1px solid #A6A6A6")` | Card border: 2 px orange (`#FF7A00`) when `alarm` is true, else 1 px grey (`#A6A6A6`). |

#### `root/title`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/title/tag` | `props.text` | property | `view.custom.name` (property binding) | Loop name (`custom.name`). |
| `root/title/alarmIcon` | `position.display` | property | `view.custom.alarm` (property binding) | Alarm icon shown while `alarm` is true. |

#### `root/chipRow`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/chipRow/mode` | `props.text` | property | `view.custom.modeText` (property binding) | Mode text from `modeText`: MAN, AUTO or CAS; `---` for other codes (Track, Intlk). |
| `root/chipRow/mode` | `props.style.backgroundColor` | expr | `case({view.custom.mode}, 0, "#3A3A3A", 2, "#E6E6E6", "#EDEDED")` | Mode chip fill: `#3A3A3A` for MAN, `#E6E6E6` for CAS, `#EDEDED` otherwise. |
| `root/chipRow/mode` | `props.style.color` | expr | `case({view.custom.mode}, 0, "#FFFFFF", 2, "#1F4E99", "#4D4D4D")` | Mode chip text: `#FFFFFF` for MAN, `#1F4E99` for CAS, `#4D4D4D` otherwise. |

#### `root/pvRow`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/pvRow/pv` | `props.text` | expr | `numberFormat({view.custom.pv}, "#,##0.0")` | PV value, one decimal. |

#### `root/uRow`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/uRow/units` | `props.text` | property | `view.custom.units` (property binding) | Engineering units (`custom.units`). |

#### `root/spRow`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/spRow/sp` | `props.text` | expr | `"SP " + numberFormat({view.custom.sp}, "#,##0.0")` | SP value with `SP ` prefix, one decimal. |

#### `root/bars`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/bars/bars` | `props.elements[1].height` | expr | `82 * {view.custom.pvPct} / 100` | PV fill height: 82 SVG units x `pvPct` / 100 (fill is index 1). |
| `root/bars/bars` | `props.elements[1].y` | expr | `82 - 82 * {view.custom.pvPct} / 100` | PV fill top edge. |
| `root/bars/bars` | `props.elements[2].y` | expr | `82 - 82 * {view.custom.hiPct} / 100 - 1` | High alarm marker (`hi`, index 2) at `hiPct`. |
| `root/bars/bars` | `props.elements[3].y` | expr | `82 - 82 * {view.custom.loPct} / 100 - 1` | Low alarm marker (`lo`, index 3) at `loPct`. |
| `root/bars/bars` | `props.elements[4].d` | expr | `"M1," + (82 - 82*{view.custom.spPct}/100 - 5) + " L8," + (82 - 82*{view.custom.spPct}/100) + " L1," + (82 - 82*{view.custom.spPct}/100 + 5) + " Z"` | Setpoint marker (`sp`, index 4): triangle centred on `spPct`. |
| `root/bars/bars` | `props.elements[6].y` | expr | `82 - 82 * {view.custom.outPct} / 100` | Output fill top edge (`outFill`, index 6): 82 - 82 x `outPct` / 100. |
| `root/bars/bars` | `props.elements[6].height` | expr | `82 * {view.custom.outPct} / 100` | Output fill height (`outFill`, index 6): 82 x `outPct` / 100. |

#### `root/labs`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/labs/outL/out` | `props.text` | expr | `numberFormat({view.custom.out}, "#,##0.0") + "%"` | Output value with `%` appended, one decimal. |

## Scripts reference

Totals: **B1 1, B2 1, B4 1** event scripts. **B3 2**: one event script and one transform script. None has custom methods, message handlers or onChange scripts.

### Click script (all four views)

- **Location:** `root` (the container), `events.dom.onClick`, scope G.
- **Trigger:** a single click on the view.

```python
	efc.ui.openDynamic(self)
```

It opens the loop dock for this tag. The view passes itself (`self`). `openDynamic` reads the view's `dockId`, `tType`, `dwTagPath` and `tagPath`, writes the dock state for this page, and writes nothing to the PLC. See the library function below.

### Transform script on `custom.spark` (B3 only)

- **Location:** `view.custom.spark`, transform of type `script`, on an expression binding `now(5000)`.
- **Trigger:** the expression re-evaluates every 5 s, which re-runs the transform.
- **Returns:** `{pv, sp}`, two SVG path strings for the sparkline (`viewBox` 150 x 34).

```python
	base = self.view.params.tagPath
	W, H = 150.0, 34.0
	empty = {"pv": "", "sp": ""}
	if not base:
		return empty
	try:
		ds = system.tag.queryTagHistory(paths=[base + "/Val_PV", base + "/Val_SP"], rangeMinutes=1, returnSize=40,
			aggregationMode="Average", returnFormat="Wide", ignoreBadQuality=True)
	except:
		return empty
	rows = []
	for r in range(ds.getRowCount()):
		a, b = ds.getValueAt(r, 1), ds.getValueAt(r, 2)
		if a is not None and b is not None:
			rows.append((float(a), float(b)))
	if len(rows) < 2:
		return empty
	lo = min(min(p) for p in rows)
	hi = max(max(p) for p in rows)
	pad = max((hi - lo) * 0.15, 0.5)
	lo, hi = lo - pad, hi + pad
	def y(val):
		return H - 3 - (val - lo) / (hi - lo) * (H - 6)
	step = W / (len(rows) - 1)
	def mk(i):
		return " ".join(("M" if n == 0 else "L") + "%.1f,%.1f" % (n * step, y(p[i])) for n, p in enumerate(rows))
	return {"pv": mk(0), "sp": mk(1)}
```

Step by step: (1) take the tag path from `self.view.params.tagPath`; if it is empty, return blank paths. (2) Query `Val_PV` and `Val_SP` with `system.tag.queryTagHistory`, last 1 minute, up to 40 samples, averaged, Wide format, bad-quality samples ignored. An exception from the query returns blank paths. (3) Keep only rows where both values exist; fewer than two rows returns blank. (4) Compute one min and max over both series, widen by 15 % (at least 0.5), and map each value to a Y coordinate in the 34-unit height. X is spread evenly over 150 units. (5) Build `M`/`L` path strings for the PV series (`pv`) and the SP series (`sp`). The script returns no error details: any failure looks like an empty trace.

### Library function called (`efc.ui`, `projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.openDynamic(component)`**: reads `dockId`, else `BY_TYPE[tType]`. `BY_TYPE` maps `T_PID` to `dw_Loop`, and `WINDOWS` maps `dw_Loop` to `Docks/Loop`. If the chosen id is not in `WINDOWS` it logs a warning and stops. Otherwise it sets the path to the window and the params to `{tagPath: dwTagPath or tagPath}` (plus `model`, if set) in `session.custom.efcDw` for this page id. It does not check the user's role, does not write a tag and does not write an audit record.

## Tag members used

All paths are relative to `tagPath`. Types and comments come from `types/PCLib_Members.csv`. The first seven rows are T_PID members. The `Alm_Dev*` rows are members of T_AlmLim, the type of `Alm_DevH` and `Alm_DevL`. No member is written.

| Member | Access | Data type | Meaning |
|---|---|---|---|
| `Val_PV` | read | REAL | Process value (EU) |
| `Val_SP` | read | REAL | Active setpoint after ramp and limits (EU) |
| `Out_CV` | read | REAL | Controller output (%) |
| `Sts_Mode` | read | INT | Mode: 0=Man 1=Auto 2=Cas 3=Track 4=Intlk |
| `Cfg_PVMin` | read | REAL | PV range low (EU) |
| `Cfg_PVMax` | read | REAL | PV range high (EU) |
| `Cfg_PVEU` | read | STRING[12] | PV engineering units text |
| `Alm_DevH/Cfg_Lim` | read | REAL | Alarm limit (EU) for high deviation (PV - SP) |
| `Alm_DevH/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_DevL/Cfg_Lim` | read | REAL | Alarm limit (EU), low deviation (SP - PV) |
| `Alm_DevL/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |

The sparkline (B3) also reads `Val_PV` and `Val_SP` from tag history.

## Component tree

### Loop_B1_Bar

Indentation shows parent and child. Each entry is `name` (component type).

- `root` (`ia.container.flex`)
  - `header` (`ia.container.flex`)
    - `title` (`ia.container.flex`)
      - `tag` (`ia.display.label`)
      - `alarmIcon` (`ia.shapes.svg`)
    - `mode` (`ia.display.label`)
  - `body` (`ia.container.flex`)
    - `pvBar` (`ia.shapes.svg`)
    - `vals` (`ia.container.flex`)
      - `pv` (`ia.display.label`)
      - `units` (`ia.display.label`)
      - `spacer` (`ia.container.flex`)
      - `spRow` (`ia.container.flex`)
        - `spLbl` (`ia.display.label`)
        - `sp` (`ia.display.label`)
  - `outRow` (`ia.container.flex`)
    - `outLbl` (`ia.display.label`)
    - `outVal` (`ia.container.flex`)
      - `out` (`ia.display.label`)
      - `pctU` (`ia.display.label`)
  - `outBarRow` (`ia.container.flex`)
    - `outBar` (`ia.shapes.svg`)

### Loop_B2_Horizontal

Indentation shows parent and child. Each entry is `name` (component type).

- `root` (`ia.container.flex`)
  - `header` (`ia.container.flex`)
    - `title` (`ia.container.flex`)
      - `tag` (`ia.display.label`)
      - `alarmIcon` (`ia.shapes.svg`)
    - `mode` (`ia.display.label`)
  - `mid` (`ia.container.flex`)
    - `vals` (`ia.container.flex`)
      - `pvRow` (`ia.container.flex`)
        - `pv` (`ia.display.label`)
        - `units` (`ia.display.label`)
      - `spRow` (`ia.container.flex`)
        - `spLbl` (`ia.display.label`)
        - `sp` (`ia.display.label`)
    - `barWrap` (`ia.container.flex`)
      - `pvBar` (`ia.shapes.svg`)
  - `outRow` (`ia.container.flex`)
    - `outLbl` (`ia.display.label`)
    - `ob` (`ia.container.flex`)
      - `outBar` (`ia.shapes.svg`)
    - `out` (`ia.display.label`)
    - `pctU` (`ia.display.label`)

### Loop_B3_Sparkline

Indentation shows parent and child. Each entry is `name` (component type).

- `root` (`ia.container.flex`)
  - `header` (`ia.container.flex`)
    - `title` (`ia.container.flex`)
      - `tag` (`ia.display.label`)
      - `alarmIcon` (`ia.shapes.svg`)
    - `mode` (`ia.display.label`)
  - `body` (`ia.container.flex`)
    - `pvBar` (`ia.shapes.svg`)
    - `vals` (`ia.container.flex`)
      - `pvRow` (`ia.container.flex`)
        - `pv` (`ia.display.label`)
        - `units` (`ia.display.label`)
      - `spRow` (`ia.container.flex`)
        - `spLbl` (`ia.display.label`)
        - `sp` (`ia.display.label`)
      - `dev` (`ia.display.label`)
  - `sparkWrap` (`ia.container.flex`)
    - `spark` (`ia.shapes.svg`)
  - `outRow` (`ia.container.flex`)
    - `outLbl` (`ia.display.label`)
    - `outVal` (`ia.container.flex`)
      - `out` (`ia.display.label`)
      - `pctU` (`ia.display.label`)
  - `outBarRow` (`ia.container.flex`)
    - `outBar` (`ia.shapes.svg`)

### Loop_B4_Column

Indentation shows parent and child. Each entry is `name` (component type).

- `root` (`ia.container.flex`)
  - `title` (`ia.container.flex`)
    - `tag` (`ia.display.label`)
    - `alarmIcon` (`ia.shapes.svg`)
  - `chipRow` (`ia.container.flex`)
    - `mode` (`ia.display.label`)
  - `pvRow` (`ia.container.flex`)
    - `pv` (`ia.display.label`)
  - `uRow` (`ia.container.flex`)
    - `units` (`ia.display.label`)
  - `spRow` (`ia.container.flex`)
    - `sp` (`ia.display.label`)
  - `bars` (`ia.container.flex`)
    - `bars` (`ia.shapes.svg`)
  - `labs` (`ia.container.flex`)
    - `pvL` (`ia.container.flex`)
      - `l` (`ia.display.label`)
    - `outL` (`ia.container.flex`)
      - `l` (`ia.display.label`)
      - `out` (`ia.display.label`)

## Notes and open questions

**Behaviour to review**

1. **Alarm outline covers deviation alarms only.** `Alm_PVBad` (T_PID, "PV bad") and the PV limits are not read by any of the four views, so a bad PV or a process alarm is not shown here. Confirm that is intended for a loop symbol.
2. **Track and Intlk show `---`.** Modes 3 and 4 get the default grey chip with `---`. Intlk is the state where the controller forces its output, and these views give no cue. The dock shows an INTERLOCKED banner.
3. **B3 deviation highlight ignores direction.** It compares |PV - SP| with `devAlm`, which is the high limit (`Alm_DevH/Cfg_Lim`). A low deviation of the same size highlights too, and `Alm_DevL/Cfg_Lim` is not used by B3.
4. **B3 sparkline failures are silent.** The transform swallows exceptions and returns blank traces. It assumes column 1 is `Val_PV` and column 2 is `Val_SP` in the Wide result. It also uses `self.view.params.tagPath`, which is not verified in a transform context on the gateway.
5. **Demo alarms cannot be shown.** In `tags/PID_Loops/T_PID_Demo_UDT.json`, `Alm_DevH/Sts_Active` and `Alm_DevL/Sts_Active` are plain memory values (False) with no expression, so the outline cannot change on the demo tags unless the flags are forced.
6. **Two copies of the views.** `generate_loops.py` writes `PID/Templates/Loop_B*` under `projects/PID_Loops/`. The EFC_Library copies are under `Templates/Loops/`. Running the generator does not update the EFC_Library views as the script is written.

**Open questions**

- Which copy is authoritative: the generator output or the EFC_Library `Templates/Loops` views?
- Should PV and process alarms drive the outline, or is the deviation-only rule intentional?
- Should B3's highlight use the low limit when the deviation is negative?
- Does `self` in a transform script resolve to the view on this gateway (Ignition 8.1)? Not verified here.

