# Docks/ProcessValue

Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Docks/ProcessValue/view.json`

Opened from: the process value templates [PV_RangeBar](../Templates/ProcessValues/PV_RangeBar.md) and [PV_StatusStrip](../Templates/ProcessValues/PV_StatusStrip.md) (`tType` `T_AI`), and the analog indicator templates [A_RangeBar](../Templates/AnalogIndicator/A_RangeBar.md), [B_PointerScale](../Templates/AnalogIndicator/B_PointerScale.md), [C_CompactRow](../Templates/AnalogIndicator/C_CompactRow.md) and [D_MiniColumn](../Templates/AnalogIndicator/D_MiniColumn.md) (`tType` `T_KPI`), all through `efc.ui.openDynamic`. `efc.ui.BY_TYPE` maps both `T_AI` and `T_KPI` to dynamic window `dw_ProcessValue`. The `T_KPI` route has a binding problem; see the notes.

## Overview

The operator and maintenance window for an analog process value (T_AI). It shows the value in engineering units, the percent of span, the rate of change and the range, six alarms, a trend, simulation, the alarm limits and the scaling configuration. It has no commands, no mode buttons and no interlock lists. It opens in the screen's right-hand region (`Docks/Region`), not as a popup.

- **Default size:** 400 x 860 (`props.defaultSize`). The root is a scrolling column.
- **Parameters:** `tagPath` (the T_AI instance) and `tType` (default `T_AI`).
- **How it is opened:** the template's single click runs `efc.ui.openDynamic(self)`. That function writes `session.custom.efcDw[pageId] = {path: 'Docks/ProcessValue', params: {tagPath: ...}}`, and `Docks/Region` displays this view. `efc.ui.openDynamic` passes only `tagPath` (and `model` if present). **`tType` is never passed**, so the window always runs with its default `T_AI`. Nothing in this view uses `tType`.
- **Generated view:** this view is written by `generator/docks/build_docks.py` (function `process_value()`). Running that function in memory reproduces the committed `view.json` exactly. Change the generator, not `view.json`, or the next build overwrites the edit.
- **How it closes:** the header `X` runs `efc.ui.closeDynamic(self)`, which restores the screen default set by `efc.ui.setDefaultDock` on `Docks/Region` startup. That startup script is not in this view.

## How it operates

**Header.** Shows `Cfg_Tag` (large) and `Cfg_Desc`. The `X` button closes the window.

**Banner.** If `Sts_Bad` is true the banner reads `BAD QUALITY` (style `State/Fault`). Otherwise it shows the value with its unit, `numberFormat(Val_PV, '#,##0.0') + ' ' + Cfg_EU`, in style `State/Stopped` whatever the value. Four badges appear when their flag is true: SIM (`Sts_Sim`), SUBST (`Sts_Subst`), OVER (`Sts_ORng`) and UNDER (`Sts_URng`).

**Values** (all levels). Five rows: value (`Val_PV`, `Cfg_EU`, `#,##0.0`), of range (`Val_PVPct`, %, `0` decimals), rate of change (`Val_ROC`, shown with the unit `Cfg_EU + '/s'`), range (`Cfg_EUMin` .. `Cfg_EUMax`, `Cfg_EU`) and diagnostics (`Sts_NE107` text: `NE107 OK`, `NE107 F`, `NE107 C`, `NE107 S`, `NE107 M`, or blank). The rows are not gated by `Sts_Bad`. The rate of change is in EU per second, as PCLib defines `Val_ROC`.

**Alarms** (all levels). Six rows: high high (`Alm_HH`), high (`Alm_H`), low (`Alm_L`), low low (`Alm_LL`), rate of change (`Alm_ROC`) and bad quality (`Alm_Bad`). A row is coloured when its alarm is active, using the alarm's `Cfg_Priority`: 1 `Critical`, 2 `High`, 3 `Medium`, 4 `Low`, anything else `Medium`. The class adds `/Unacked` or `/Fill`. An inactive but unacknowledged alarm uses `Alarm/Status/ClearedUnacked`. An inactive, acknowledged alarm uses `Text/Caption Text/Color/Muted`. "No active alarms" is shown when none is active. **ACK** (level 1 and above) calls `efc.ui.ackAll`, which writes `Cmd_Ack` only for the alarms whose `Sts_Unack` is true.

**Trend.** Embeds `Docks/Parts/Trend` ([Parts/Trend](Parts/Trend.md)) with pen `Val_PV`, over the window's tag. The embedded view's `expanded` param starts `false`. The Trend part toggles it itself, and the `position.basis` binding grows the trend from 15.741 vh to 70.370 vh. The expansion is local to the trend and does not widen the dock region.

**Maintenance** (level 2 and above). Two controls. **Simulate** is a checkbox bound bidirectionally to `Sim_En`, enabled at level 2. **Simulated value** is an entry bound bidirectionally to `Sim_PV`, shown only while `Sim_En` is true. Neither goes through `efc.ui.cmd`, so neither is audited.

**Limits** (collapsible, collapsed at start; the header click toggles `open_Limits`). Five alarm limits: high high, high, low, low low and rate of change (`Alm_HH/Cfg_Lim`, `Alm_H/Cfg_Lim`, `Alm_L/Cfg_Lim`, `Alm_LL/Cfg_Lim`, `Alm_ROC/Cfg_Lim`). Below level 4 each is a read-only row. At level 4 and above each is an entry bound bidirectionally to the tag. The units shown are blank for the four PV limits and `/min` for the rate-of-change limit. Writes are not audited.

**Configuration** (collapsible, collapsed at start; the header click toggles `open_Configuration`). Seven items: EU min (`Cfg_EUMin`), EU max (`Cfg_EUMax`), raw min (`Cfg_RawMin`), raw max (`Cfg_RawMax`), filter time constant (`Cfg_FiltTC`, s), low cutoff (`Cfg_LoCutoff`) and square root extraction (`Cfg_SqrtExtract`, checkbox). Below level 4 they are read-only rows (square root extraction shows `Yes` or `No`). At level 4 and above they are entries or a checkbox bound bidirectionally to the tag, and the rows are hidden. Writes are not audited.

**Role checks.** Role levels come from the Perspective session (`session.props.auth.user.roles`), mapped by `efc.ui.level`. Only ACK checks the level in script (inside `efc.ui.ackAll`). The maintenance controls, the limits and the configuration are protected by visibility and enable bindings only. Bindings do not check the level. Real access control has to be enforced in Perspective security and the PLC logic.

**Audit.** None. This view makes no `efc.ui.cmd` call and `efc.ui.ackAll` does not audit. Simulation, limit and configuration changes go straight to the tags and are not audited.

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `""` | T_AI instance. Every component binding uses `{view.params.tagPath}`. | Set by `efc.ui.openDynamic` from the template's `dwTagPath` (or `tagPath`). Read by bindings, by `efc.ui.ackAll` and by the Trend embed. |
| `tType` | input | `T_AI` | Declared type. | Not passed by `efc.ui.openDynamic`; not referenced by any binding or script in this view. Always the default. |

Both have `paramDirection: input` and `persistent: true`. No output parameters.

### View-level custom properties (`custom`)

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.level` | `0` | property + script transform | `session.props.auth.user.roles` → `return efc.ui.level(value)` | Role level 0-5 from `session.props.auth.user.roles` via `efc.ui.level`. Gates the ACK button, the maintenance section (level 2) and the limit and configuration editors (level 4). |
| `view.custom.open_Limits` | `false` | none (written by script) | none | View-local toggle for the Limits section. Set by the header click script; not bound to any tag; not persisted. |
| `view.custom.open_Configuration` | `false` | none (written by script) | none | View-local toggle for the Configuration section. Set by the header click script; not bound to any tag; not persisted. |

#### Tag mirrors (`custom.m_*`)

There are 43 tag-mirror properties. Each `custom.m_<member>` (with `/` replaced by `_`) has an indirect, read-only tag binding to `{view.params.tagPath}/<member>` (`bidirectional: false`, fallback delay 2.5 s), and its default is `null`. The read-only display rows read tag values through these mirrors. The entries, checkboxes and the ACK script read the tags directly (the square root checkbox's read-only row uses a mirror).

| Group | Members |
|---|---|
| Identity | `Cfg_Tag`, `Cfg_Desc`, `Cfg_EU` |
| Scaling | `Cfg_EUMin`, `Cfg_EUMax`, `Cfg_RawMin`, `Cfg_RawMax`, `Cfg_FiltTC`, `Cfg_LoCutoff`, `Cfg_SqrtExtract` |
| Status | `Sts_Bad`, `Sts_Sim`, `Sts_Subst`, `Sts_ORng`, `Sts_URng`, `Sts_NE107` |
| Values | `Val_PV`, `Val_PVPct`, `Val_ROC` |
| Simulation | `Sim_En` |
| Alarms | `Alm_HH`, `Alm_H`, `Alm_L`, `Alm_LL`, `Alm_ROC`, `Alm_Bad`: each with `/Sts_Active`, `/Sts_Unack` and `/Cfg_Priority`. `Alm_HH`, `Alm_H`, `Alm_L`, `Alm_LL` and `Alm_ROC` also have `/Cfg_Lim` (`Alm_Bad` is a `T_Alarm`, with no limit) |

### Component-level custom properties

None.

### Session, page and message payloads

- `session.props.auth.user.roles`: read by `custom.level` (transform `efc.ui.level`).
- `session.props.auth.user.userName`: read by `efc.ui._audit` (not bound in this view).
- `session.custom.efcDw[pageId]`: written by `efc.ui.openDynamic` and `closeDynamic` in the template and header; read by `Docks/Region` (not in this file).
- `page.props.pageId`: read by `efc.ui._state` to key `efcDw`.
- No message handlers. No `customMethods`.

## Bindings reference

Total: **154 bindings**: 44 at view root (all `custom.*`, including 1 `property` binding with a transform) and 108 on components (94 `expr`, 14 `tag`). Types overall: 94 `expr`, 57 `tag`, 1 `property`. `params.tagPath` and `params.tType` have `paramDirection` only, so they are not counted.

### View root

The view-root bindings drive the custom properties. Each one is listed with its full source in **View-level custom properties** above.

### `root/Header`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Header/Names/Tag | `props.text` | expr | `{view.custom.m_Cfg_Tag}` | Text content |
| root/Header/Names/Desc | `props.text` | expr | `{view.custom.m_Cfg_Desc}` | Text content |

### `root/Banner`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Banner | `props.style.classes` | expr | `if({view.custom.m_Sts_Bad}, 'State/Fault', if(true, 'State/Stopped', 'State/Unknown'))` | CSS class(es) selected by state |
| root/Banner/State | `props.text` | expr | `if({view.custom.m_Sts_Bad}, 'BAD QUALITY', if(true, numberFormat({view.custom.m_Val_PV}, '#,##0.0') + ' ' + {view.custom.m_Cfg_EU}, 'UNKNOWN'))` | Text content |
| root/Banner/Chip0 | `position.display` | expr | `{view.custom.m_Sts_Sim}` | Shown while expression is true |
| root/Banner/Chip1 | `position.display` | expr | `{view.custom.m_Sts_Subst}` | Shown while expression is true |
| root/Banner/Chip2 | `position.display` | expr | `{view.custom.m_Sts_ORng}` | Shown while expression is true |
| root/Banner/Chip3 | `position.display` | expr | `{view.custom.m_Sts_URng}` | Shown while expression is true |

### `root/Values`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Values/Body/PV/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_PV}, '#,##0.0')` | Text content |
| root/Values/Body/PV/EU | `props.text` | expr | `{view.custom.m_Cfg_EU}` | Text content |
| root/Values/Body/Pct/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_PVPct}, '0')` | Text content |
| root/Values/Body/Pct/EU | `props.text` | expr | `'%'` | Text content |
| root/Values/Body/ROC/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_ROC}, '#,##0.###')` | Text content |
| root/Values/Body/ROC/EU | `props.text` | expr | `{view.custom.m_Cfg_EU} + '/s'` | Text content |
| root/Values/Body/Rng/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_EUMin}, '#,##0.##') + ' .. ' + numberFormat({view.custom.m_Cfg_EUMax}, '#,##0.##')` | Text content |
| root/Values/Body/Rng/EU | `props.text` | expr | `{view.custom.m_Cfg_EU}` | Text content |
| root/Values/Body/NE107/Val | `props.text` | expr | `case(toInt({view.custom.m_Sts_NE107}), 0, 'NE107 OK', 1, 'NE107 F', 2, 'NE107 C', 3, 'NE107 S', 4, 'NE107 M', '')` | Text content |

### `root/Alarms`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Alarms/Body/None | `position.display` | expr | `!({view.custom.m_Alm_HH_Sts_Active} \|\| {view.custom.m_Alm_H_Sts_Active} \|\| {view.custom.m_Alm_L_Sts_Active} \|\| {view.custom.m_Alm_LL_Sts_Active} \|\| {view.custom.m_Alm_ROC_Sts_Active} \|\| {view.custom.m_Alm_Bad_Sts_Active})` | Shown while expression is true |
| root/Alarms/Body/List/A0 | `props.style.classes` | expr | `if({view.custom.m_Alm_HH_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_HH_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_HH_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_HH_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A1 | `props.style.classes` | expr | `if({view.custom.m_Alm_H_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_H_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_H_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_H_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A2 | `props.style.classes` | expr | `if({view.custom.m_Alm_L_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_L_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_L_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_L_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A3 | `props.style.classes` | expr | `if({view.custom.m_Alm_LL_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_LL_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_LL_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_LL_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A4 | `props.style.classes` | expr | `if({view.custom.m_Alm_ROC_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_ROC_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_ROC_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_ROC_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A5 | `props.style.classes` | expr | `if({view.custom.m_Alm_Bad_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_Bad_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_Bad_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_Bad_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/Ack | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |

### `root/Trend`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Trend | `props.params.tagPath` | expr | `{view.params.tagPath}` | Embedded view tagPath param |
| root/Trend | `position.basis` | expr | `if({this.props.params.expanded}, '70.370vh', '15.741vh')` | Row height |

### `root/Maintenance`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Maintenance | `position.display` | expr | `{view.custom.level} >= 2` | Shown while expression is true |
| root/Maintenance/Body/Sim | `props.selected` | tag (indirect) | tag `{0}/Sim_En` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (checkbox) |
| root/Maintenance/Body/Sim | `props.enabled` | expr | `{view.custom.level} >= 2` | Enabled while expression is true |
| root/Maintenance/Body/SimPV | `position.display` | expr | `{view.custom.level} >= 2 && ({view.custom.m_Sim_En})` | Shown while expression is true |
| root/Maintenance/Body/SimPV/Entry | `props.value` | tag (indirect) | tag `{0}/Sim_PV` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Maintenance/Body/SimPV/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |

### `root/Limits`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Limits/Header/Chevron | `props.text` | expr | `if({view.custom.open_Limits}, '▾', '▸')` | Text content |
| root/Limits/Body | `position.display` | expr | `{view.custom.open_Limits}` | Shown while expression is true |
| root/Limits/Body/R0 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Limits/Body/R0/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_HH_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Limits/Body/R0/EU | `props.text` | expr | `''` | Text content |
| root/Limits/Body/E0 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Limits/Body/E0/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_HH/Cfg_Lim` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Limits/Body/E0/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Limits/Body/R1 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Limits/Body/R1/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_H_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Limits/Body/R1/EU | `props.text` | expr | `''` | Text content |
| root/Limits/Body/E1 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Limits/Body/E1/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_H/Cfg_Lim` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Limits/Body/E1/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Limits/Body/R2 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Limits/Body/R2/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_L_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Limits/Body/R2/EU | `props.text` | expr | `''` | Text content |
| root/Limits/Body/E2 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Limits/Body/E2/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_L/Cfg_Lim` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Limits/Body/E2/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Limits/Body/R3 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Limits/Body/R3/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_LL_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Limits/Body/R3/EU | `props.text` | expr | `''` | Text content |
| root/Limits/Body/E3 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Limits/Body/E3/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_LL/Cfg_Lim` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Limits/Body/E3/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Limits/Body/R4 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Limits/Body/R4/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_ROC_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Limits/Body/R4/EU | `props.text` | expr | `'/s'` | Text content |
| root/Limits/Body/E4 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Limits/Body/E4/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_ROC/Cfg_Lim` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Limits/Body/E4/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |

### `root/Configuration`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration/Header/Chevron | `props.text` | expr | `if({view.custom.open_Configuration}, '▾', '▸')` | Text content |
| root/Configuration/Body | `position.display` | expr | `{view.custom.open_Configuration}` | Shown while expression is true |
| root/Configuration/Body/R0 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R0/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_EUMin}, '#,##0.###')` | Text content |
| root/Configuration/Body/R0/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E0 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E0/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_EUMin` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E0/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R1 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R1/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_EUMax}, '#,##0.###')` | Text content |
| root/Configuration/Body/R1/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E1 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E1/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_EUMax` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E1/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R2 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R2/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_RawMin}, '#,##0.###')` | Text content |
| root/Configuration/Body/R2/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E2 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E2/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_RawMin` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E2/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R3 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R3/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_RawMax}, '#,##0.###')` | Text content |
| root/Configuration/Body/R3/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E3 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E3/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_RawMax` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E3/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R4 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R4/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_FiltTC}, '#,##0.###')` | Text content |
| root/Configuration/Body/R4/EU | `props.text` | expr | `'s'` | Text content |
| root/Configuration/Body/E4 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E4/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_FiltTC` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E4/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R5 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R5/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_LoCutoff}, '#,##0.###')` | Text content |
| root/Configuration/Body/R5/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E5 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E5/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_LoCutoff` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E5/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R6 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R6/Val | `props.text` | expr | `if({view.custom.m_Cfg_SqrtExtract}, 'Yes', 'No')` | Text content |
| root/Configuration/Body/C6 | `props.selected` | tag (indirect) | tag `{0}/Cfg_SqrtExtract` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (checkbox) |
| root/Configuration/Body/C6 | `props.enabled` | expr | `{view.custom.level} >= 4` | Enabled while expression is true |
| root/Configuration/Body/C6 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |

## Scripts reference

Total: **5 scripts**: 4 event scripts (2 `component.onActionPerformed`, 2 `dom.onClick`) and 1 transform script (`custom.level`). No `customMethods`, no `messageHandlers`, no property-change `onChange` scripts.

The button handlers call `efc.ui` functions, which are summarised after the list.

1. **`root/Header/Close`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.closeDynamic(self)
```

2. **`root/Alarms/Body/Ack`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.ackAll(self, ['Alm_HH', 'Alm_H', 'Alm_L', 'Alm_LL', 'Alm_ROC', 'Alm_Bad'])
```

3. **`root/Limits/Header`**: `events.dom.onClick`, scope G.

```python
	self.view.custom.open_Limits = not self.view.custom.open_Limits
```

4. **`root/Configuration/Header`**: `events.dom.onClick`, scope G.

```python
	self.view.custom.open_Configuration = not self.view.custom.open_Configuration
```

5. **transform on `(view root)` `custom.level`**: `custom.level` binding, `property` source `session.props.auth.user.roles`.

```python
	return efc.ui.level(value)
```

### Explanation of each handler

| Handler | Action | Writes | Role check | Audit |
|---|---|---|---|---|
| `Header/Close` | `efc.ui.closeDynamic` restores the default region view | none | none | no |
| `Alarms/Ack` | `efc.ui.ackAll` on the six alarms | `Alm_*/Cmd_Ack`, only where `Sts_Unack` is true | level 1 (in `efc.ui.ackAll`) | no |
| `Limits/Header` (dom click) | toggles `open_Limits` | none | none | no |
| `Configuration/Header` (dom click) | toggles `open_Configuration` | none | none | no |

This view has no `efc.ui.cmd` calls. The simulate checkbox, the simulated value entry, the limit entries and the configuration entries are direct bidirectional bindings, with no script between the control and the tag.

### Library functions used (`projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.level(roles)`**: highest index of the role in `['Guest','Operator','Maintenance','Supervisor','Engineer','Admin']`, or 0. Bound to `custom.level`.
- **`efc.ui.closeDynamic(component)`**: writes `efcDw[pageId]` back to the stored `default` path and params. Writes no tags.
- **`efc.ui.ackAll(component, alarms)`**: returns unless the user is at level 1 or above. Reads `<alarm>/Sts_Unack` for the listed alarms, then writes `<alarm>/Cmd_Ack` = True for those that are true. No audit.
- **`efc.ui.cmd`, `bypass`, `unbypass`, `dblCmd`**: not called from this view. `efc.ui.trend` is called by the Trend part, not here.

## Tag members used

All paths are relative to `tagPath`. Types and meanings are taken verbatim from `types/PCLib_Members.csv` (type `T_AI`; alarm members from `T_AlmLim`, and `Alm_Bad` from `T_Alarm`). The trend pen is read through tag history by the Trend part.

| Member | Access (read/write) | Data type | Meaning |
|---|---|---|---|
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Cfg_EU` | read | STRING[12] | Engineering units text |
| `Cfg_EUMax` | read/write (bidirectional) | REAL | PV at 100% (EU) |
| `Cfg_EUMin` | read/write (bidirectional) | REAL | PV at 0% (EU) |
| `Cfg_FiltTC` | read/write (bidirectional) | REAL | 1st-order filter time constant (s), 0 = off |
| `Cfg_LoCutoff` | read/write (bidirectional) | REAL | Low cutoff (% span): PV forced to EUMin below this, 0 = off |
| `Cfg_RawMax` | read/write (bidirectional) | INT | Raw counts at 100% (M340/M580 4-20mA default 10000) |
| `Cfg_RawMin` | read/write (bidirectional) | INT | Raw counts at 0% (M340/M580 4-20mA default 0) |
| `Cfg_SqrtExtract` | read/write (bidirectional) | BOOL | Square-root extraction (DP flow) |
| `Cfg_Tag` | read | STRING[20] | Equipment / instrument tag, e.g. FT-101 |
| `Sts_Bad` | read | BOOL | PV bad (out of range or channel fault) |
| `Sts_NE107` | read | INT | NAMUR NE107 status: 0=Good 1=Failure (F) 2=Function check (C) 3=Out of specification (S) 4=Maintenance required (M) |
| `Sts_ORng` | read | BOOL | Over range |
| `Sts_Sim` | read | BOOL | Simulation active |
| `Sts_Subst` | read | BOOL | Substitute / held value in use |
| `Sts_URng` | read | BOOL | Under range |
| `Val_PV` | read; also read by trend pens | REAL | Process value (EU) - use this in logic |
| `Val_PVPct` | read | REAL | Process value (% of span) |
| `Val_ROC` | read | REAL | Rate of change (EU/s, 1 s window) - input to Alm_ROC |
| `Sim_En` | read/write (bidirectional) | BOOL | Simulation enabled |
| `Sim_PV` | read/write (bidirectional) | REAL | Simulated PV (EU) |
| `Alm_Bad/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_Bad/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_Bad/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_Bad/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_H/Cfg_Lim` | read/write (bidirectional) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Alm_H/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_H/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_H/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_H/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_HH/Cfg_Lim` | read/write (bidirectional) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Alm_HH/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_HH/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_HH/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_HH/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_L/Cfg_Lim` | read/write (bidirectional) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Alm_L/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_L/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_L/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_L/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_LL/Cfg_Lim` | read/write (bidirectional) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Alm_LL/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_LL/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_LL/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_LL/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_ROC/Cfg_Lim` | read/write (bidirectional) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Alm_ROC/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_ROC/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_ROC/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_ROC/Sts_Unack` | read | BOOL | Alarm unacknowledged |

## Component tree

```

- `root` (ia.container.flex)
  - `Header` (ia.container.flex)
    - `Names` (ia.container.flex)
      - `Tag` (ia.display.label)
      - `Desc` (ia.display.label)
    - `Close` (ia.input.button)
  - `Banner` (ia.container.flex)
    - `State` (ia.display.label)
    - `Chip0` (ia.display.label)
    - `Chip1` (ia.display.label)
    - `Chip2` (ia.display.label)
    - `Chip3` (ia.display.label)
  - `Values` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
    - `Body` (ia.container.flex)
      - `PV` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Pct` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `ROC` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Rng` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `NE107` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
  - `Alarms` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
    - `Body` (ia.container.flex)
      - `None` (ia.display.label)
      - `List` (ia.container.flex)
        - `A0` (ia.display.label)
        - `A1` (ia.display.label)
        - `A2` (ia.display.label)
        - `A3` (ia.display.label)
        - `A4` (ia.display.label)
        - `A5` (ia.display.label)
      - `Ack` (ia.input.button)
  - `Trend` (ia.display.view)
  - `Maintenance` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
    - `Body` (ia.container.flex)
      - `Sim` (ia.input.checkbox)
      - `SimPV` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
  - `Limits` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
      - `Chevron` (ia.display.label)
    - `Body` (ia.container.flex)
      - `R0` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `E0` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `R1` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `E1` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `R2` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `E2` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `R3` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `E3` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `R4` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `E4` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
  - `Configuration` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
      - `Chevron` (ia.display.label)
    - `Body` (ia.container.flex)
      - `R0` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `E0` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `R1` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `E1` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `R2` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `E2` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `R3` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `E3` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `R4` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `E4` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `R5` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `E5` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `R6` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
      - `C6` (ia.input.checkbox)

```
## Notes and open questions

- **The AnalogIndicator templates open a window that binds members their type does not define (probable defect).** Templates A to D default to `tType` `T_KPI` and open this window. `T_KPI` is a proposed UDT (`types/T_KPI/README.md`) and is not in `types/PCLib_Members.csv`. This window binds twelve member names that the proposed `T_KPI` does not define: `Val_ROC`, `Alm_ROC`, `Alm_Bad`, `Sts_NE107`, `Sts_URng`, `Sts_ORng`, `Sts_Subst`, `Cfg_RawMin`, `Cfg_RawMax`, `Cfg_LoCutoff`, `Cfg_SqrtExtract` and `Sim_PV`. The proposal names the simulated value `Sim_Value`, not `Sim_PV`. The README omits the raw-channel members, NE107 and ROC on purpose, but says nothing about the window. When an AnalogIndicator opens this window those rows will be blank or unbound. Decide whether `T_KPI` should carry these members, or whether the KPI templates need their own window.
- **Simulation is not audited.** The Simulate checkbox (`Sim_En`) and the simulated value entry (`Sim_PV`) are direct bindings with no `efc.ui` call, so a simulation can be switched on or its value changed at level 2 with no audit entry. ValveDiscrete audits its simulate control through `efc.ui.cmd(..., audit=True)`. This is inconsistent.
- **Limit and configuration changes are not audited and not role-checked in script.** The only guards are the level 4 visibility and enable bindings. Confirm whether these changes must be audited.
- **Units not shown on several rows.** The four PV limit rows (`Alm_HH`, `Alm_H`, `Alm_L`, `Alm_LL`) and the EU min and EU max rows show no unit, although the values are in `Cfg_EU`. The low cutoff (`Cfg_LoCutoff`) is documented in PCLib as % of span, but it is shown with no unit.
- **Banner colour for a good value.** A good reading uses the style `State/Stopped` (the stopped style) whatever its value. Confirm that this is intended.
- **Bad-quality handling is not configurable here.** The banner switches to BAD QUALITY, but the value rows still show `Val_PV`. The alarms still apply. The bad-quality settings (`Cfg_BadAction`, `Cfg_SubstPV`, `Cfg_BadLoPct`, `Cfg_BadHiPct`) and `Sts_Quality` and `Inp_NE107` are not shown in this view. Only the SUBST badge (`Sts_Subst`) is visible. Confirm the intended behaviour.
- **Trend hides bad quality.** `efc.ui.trend` queries history with `ignoreBadQuality=True`, so periods of bad quality are left out of the plot without any marker. The trend shows `Val_PV` only.
