# Templates/Dynamic Window/ProcessValues/ProcessValue

Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/Dynamic Window/ProcessValues/ProcessValue/view.json`

Opened from: the process value templates [PV_RangeBar](../../ProcessValues/PV_RangeBar.md) and [PV_StatusStrip](../../ProcessValues/PV_StatusStrip.md) (`tType` `T_AI`), and the analog indicator templates [A_RangeBar](../../AnalogIndicator/A_RangeBar.md), [B_PointerScale](../../AnalogIndicator/B_PointerScale.md), [C_CompactRow](../../AnalogIndicator/C_CompactRow.md) and [D_MiniColumn](../../AnalogIndicator/D_MiniColumn.md) (`tType` `T_KPI`), all through `efc.ui.openDynamic`. `efc.ui.BY_TYPE` maps both `T_AI` and `T_KPI` to dynamic window `dw_ProcessValue`. The `T_KPI` route has a binding problem; see the notes.

## Overview

The operator and maintenance window for an analog process value (T_AI). It shows the value in engineering units, the percent of span, the rate of change and the range, six alarms, a trend, simulation, the alarm limits and the scaling configuration. It has no commands, no mode buttons and no interlock lists. It opens in the page's right dock (`dw_Right`), not as a popup.

- **Default size:** 400 x 860 (`props.defaultSize`). The root is a scrolling column.
- **Parameters:** `tagPath` (the T_AI instance) and `tType` (default `T_AI`).
- **How it is opened:** the template's single click runs `efc.ui.openDynamic(self)`. That function loads `Templates/Dynamic Window/ProcessValues/ProcessValue` into the page's `dw_Right` dock with params `{tagPath: ...}` (`system.perspective.alterDock`) and opens the dock (`system.perspective.openDock`). Before that it runs `efc.ui.sizeDock(self)`, which sets the dock size to 37.04 vh (400 px at 1080p, 800 px at 4K, decision 33). `efc.ui.openDynamic` passes only `tagPath` (and `model` if present). **`tType` is never passed**, so the window always runs with its default `T_AI`. Nothing in this view uses `tType`.
- **Generated view:** this view is written by `generator/docks/build_docks.py` (function `process_value()`). Running that function in memory reproduces the committed `view.json` exactly. Change the generator, not `view.json`, or the next build overwrites the edit.
- **How it closes:** the header `X` runs `efc.ui.closeDynamic(self)`, which puts the page's default view back in the `dw_Right` dock (set by `efc.ui.setDefaultDock` in the screen's onStartup), or closes the dock if the page has no default. That startup script is not in this view.

## How it operates

**Header.** Shows `Cfg_Tag` (large) and `Cfg_Desc`. The `X` button closes the window.

**Banner.** If `Sts_Bad` is true the banner reads `BAD QUALITY` (style `State/Fault`). Otherwise it shows the value with its unit, `numberFormat(Val_PV, '#,##0.0') + ' ' + Cfg_EU`, in style `State/Stopped` whatever the value. Four badges appear when their flag is true: SIM (`Sts_Sim`), SUBST (`Sts_Subst`), OVER (`Sts_ORng`) and UNDER (`Sts_URng`).

**Values** (all levels). Five rows: value (`Val_PV`, `Cfg_EU`, `#,##0.0`), of range (`Val_PVPct`, %, `0` decimals), rate of change (`Val_ROC`, shown with the unit `Cfg_EU + '/s'`), range (`Cfg_EUMin` .. `Cfg_EUMax`, `Cfg_EU`) and diagnostics (`Sts_NE107` text: `NE107 OK`, `NE107 F`, `NE107 C`, `NE107 S`, `NE107 M`, or blank). The rows are not gated by `Sts_Bad`. The rate of change is in EU per second, as PCLib defines `Val_ROC`.

**Alarms** (all levels). Six rows: high high (`Alm_HH`), high (`Alm_H`), low (`Alm_L`), low low (`Alm_LL`), rate of change (`Alm_ROC`) and bad quality (`Alm_Bad`). A row is coloured when its alarm is active, using the alarm's `Cfg_Priority`: 1 `Critical`, 2 `High`, 3 `Medium`, 4 `Low`, anything else `Medium`. The class adds `/Unacked` or `/Fill`. An inactive but unacknowledged alarm uses `Alarm/Status/ClearedUnacked`. An inactive, acknowledged alarm uses `Text/Caption Text/Color/Muted`. "No active alarms" is shown when none is active. **ACK** (always visible; lock icon below level 1) calls `efc.ui.ackAll`, which writes `Cmd_Ack` only for the alarms whose `Sts_Unack` is true. Below Operator `efc.ui.ackAll` writes nothing, logs a warning and opens the AccessDenied popup.

**Trend.** Embeds `Templates/Dynamic Window/Parts/Trend` ([Parts/Trend](../Parts/Trend.md)) with pen `Val_PV`, over the window's tag. The embedded view's `expanded` param starts `false`. The Trend part toggles it itself, and the `position.basis` binding grows the trend from 15.741 vh to 70.370 vh. The expansion is local to the trend and does not widen the dock.

**Maintenance** (level 2 and above). Two controls. **Simulate** is a checkbox that reads `Sim_En` one way, enabled at level 2. **Simulated value** is an entry that reads `Sim_PV` one way, shown only while `Sim_En` is true. Both commit an edit through `efc.ui.setValue(self, member, value, 2)` (level 2 re-checked, audited old -> new, binding refreshed if refused or failed).

**Limits** (level 1 and above, hidden below Operator; collapsible, collapsed at start; the header click toggles `open_Limits`). Five alarm limits: high high, high, low, low low and rate of change (`Alm_HH/Cfg_Lim`, `Alm_H/Cfg_Lim`, `Alm_L/Cfg_Lim`, `Alm_LL/Cfg_Lim`, `Alm_ROC/Cfg_Lim`). Below level 4 each is a read-only row. At level 4 and above each is an entry that reads the tag one way and commits an edit through `efc.ui.setValue(self, member, value, 4)` (level 4 re-checked, audited). The units shown are blank for the four PV limits and `/min` for the rate-of-change limit.

**Configuration** (level 1 and above, hidden below Operator; collapsible, collapsed at start; the header click toggles `open_Configuration`). Seven items: EU min (`Cfg_EUMin`), EU max (`Cfg_EUMax`), raw min (`Cfg_RawMin`), raw max (`Cfg_RawMax`), filter time constant (`Cfg_FiltTC`, s), low cutoff (`Cfg_LoCutoff`) and square root extraction (`Cfg_SqrtExtract`, checkbox). Below level 4 they are read-only rows (square root extraction shows `Yes` or `No`). At level 4 and above they are entries or a checkbox that read the tag one way and commit through `efc.ui.setValue` (level 4, audited), and the rows are hidden.

**Role checks.** `view.custom.level` comes from the Perspective session (`session.props.auth.securityLevels`), mapped by `efc.ui.level` (case-insensitive, site names through `efc.ui.ROLE_ALIASES`). ACK checks the level in script (inside `efc.ui.ackAll`): its button stays visible with a lock below Operator, and a press below it logs a warning and opens the `Parts/AccessDenied` popup (decision 36; see [AccessDenied](../Parts/AccessDenied.md)). The maintenance controls (level 2), the limits and the configuration (level 4) are re-checked by `efc.ui.setValue`, which refuses with the same popup. Real access control has to be enforced in Perspective security and the PLC logic.

**Audit.** Simulation, limit and configuration changes are audited by `efc.ui.setValue` (`EFC set`, old -> new). This view makes no `efc.ui.cmd` call and `efc.ui.ackAll` does not audit.

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
| `view.custom.level` | `0` | property + script transform | `session.props.auth.securityLevels` → `return efc.ui.level(value)` | Role level 0-5 from `session.props.auth.securityLevels` via `efc.ui.level`. Gates the ACK button, the maintenance section (level 2), the Limits and Configuration sections (hidden below 1) and their editors (level 4). |
| `view.custom.open_Limits` | `false` | none (written by script) | none | View-local toggle for the Limits section. Set by the header click script; not bound to any tag; not persisted. |
| `view.custom.open_Configuration` | `false` | none (written by script) | none | View-local toggle for the Configuration section. Set by the header click script; not bound to any tag; not persisted. |

#### Tag mirrors (`custom.m_*`)

There are 43 tag-mirror properties. Each `custom.m_<member>` (with `/` replaced by `_`) has an indirect, read-only tag binding to `{view.params.tagPath}/<member>` (`bidirectional: false`, fallback delay 2.5 s), and its default is `null`. The read-only display rows read tag values through these mirrors. The entries and checkboxes (one-way tag bindings) and the ACK script read the tags directly (the square root checkbox's read-only row uses a mirror).

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

- `session.props.auth.securityLevels`: read by `custom.level` (transform `efc.ui.level`).
- `session.props.auth.user.userName`: read by `efc.ui._audit` (not bound in this view).
- `session.custom.efcDw['<pageId>|<page path>']`: holds only the page's default dock view (`{'default': {'path', 'params'}}`), written by `efc.ui.setDefaultDock` in the screen's onStartup (not in this file) and read by `efc.ui.closeDynamic` in the header. `openDynamic` writes no session value; it calls `system.perspective.alterDock` and `openDock` on `dw_Right`.
- `page.props.pageId` and `page.props.path`: read by `efc.ui._state` to key `efcDw` (the pageId survives `navigate()`, so the path keeps one screen's default from leaking into the next).
- `page.props.dimensions`: `efc.ui.sizeDock` (run by `openDynamic`, `closeDynamic` and `setDefaultDock`) reads `viewport.height`, turns `dimensions.enabled` on if needed, and sets the `dw_Right` dock size to 400 x height / 1080 px (37.04 vh, decision 33). Needs Ignition 8.1.7+ for page dimensions and 8.1.19+ for `alterDock`.
- No message handlers. No `customMethods`.

## Bindings reference

Total: **155 bindings**: 44 at view root (all `custom.*`, including 1 `property` binding with a transform) and 111 on components (97 `expr`, 14 `tag`). Types overall: 97 `expr`, 57 `tag`, 1 `property`. `params.tagPath` and `params.tType` have `paramDirection` only, so they are not counted.

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
| root/Alarms/Body/Ack | `props.image.icon.path` | expr | `if({view.custom.level} < 1, 'material/lock', '')` | Shows a lock icon on the button while the user is below Operator |
| root/Alarms/Body/Ack | `meta.tooltip.enabled` | expr | `{view.custom.level} < 1` | Tooltip "Requires Operator access" shown while expression is true |

### `root/Trend`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Trend | `props.params.tagPath` | expr | `{view.params.tagPath}` | Embedded view tagPath param |
| root/Trend | `position.basis` | expr | `if({this.props.params.expanded}, '70.370vh', '15.741vh')` | Row height |

### `root/Maintenance`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Maintenance | `position.display` | expr | `{view.custom.level} >= 2` | Shown while expression is true |
| root/Maintenance/Body/Sim | `props.selected` | tag (indirect) | tag `{0}/Sim_En`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (checkbox) |
| root/Maintenance/Body/Sim | `props.selected` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Sim_En', bool(currentValue.value), 2): self.refreshBinding('props.selected')` | Edit committed through `efc.ui.setValue`, level 2, audited; a refused or failed write refreshes the binding |
| root/Maintenance/Body/Sim | `props.enabled` | expr | `{view.custom.level} >= 2` | Enabled while expression is true |
| root/Maintenance/Body/SimPV | `position.display` | expr | `{view.custom.level} >= 2 && ({view.custom.m_Sim_En})` | Shown while expression is true |
| root/Maintenance/Body/SimPV/Entry | `props.value` | tag (indirect) | tag `{0}/Sim_PV`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Maintenance/Body/SimPV/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Sim_PV', currentValue.value, 2): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 2, audited; a refused or failed write refreshes the binding |
| root/Maintenance/Body/SimPV/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |

### `root/Limits`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Limits | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true (hidden below Operator) |
| root/Limits/Header/Chevron | `props.text` | expr | `if({view.custom.open_Limits}, '▾', '▸')` | Text content |
| root/Limits/Body | `position.display` | expr | `{view.custom.open_Limits}` | Shown while expression is true |
| root/Limits/Body/R0 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Limits/Body/R0/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_HH_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Limits/Body/R0/EU | `props.text` | expr | `''` | Text content |
| root/Limits/Body/E0 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Limits/Body/E0/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_HH/Cfg_Lim`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Limits/Body/E0/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Alm_HH/Cfg_Lim', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Limits/Body/E0/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Limits/Body/R1 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Limits/Body/R1/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_H_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Limits/Body/R1/EU | `props.text` | expr | `''` | Text content |
| root/Limits/Body/E1 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Limits/Body/E1/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_H/Cfg_Lim`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Limits/Body/E1/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Alm_H/Cfg_Lim', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Limits/Body/E1/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Limits/Body/R2 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Limits/Body/R2/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_L_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Limits/Body/R2/EU | `props.text` | expr | `''` | Text content |
| root/Limits/Body/E2 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Limits/Body/E2/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_L/Cfg_Lim`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Limits/Body/E2/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Alm_L/Cfg_Lim', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Limits/Body/E2/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Limits/Body/R3 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Limits/Body/R3/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_LL_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Limits/Body/R3/EU | `props.text` | expr | `''` | Text content |
| root/Limits/Body/E3 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Limits/Body/E3/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_LL/Cfg_Lim`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Limits/Body/E3/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Alm_LL/Cfg_Lim', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Limits/Body/E3/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Limits/Body/R4 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Limits/Body/R4/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_ROC_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Limits/Body/R4/EU | `props.text` | expr | `'/s'` | Text content |
| root/Limits/Body/E4 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Limits/Body/E4/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_ROC/Cfg_Lim`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Limits/Body/E4/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Alm_ROC/Cfg_Lim', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Limits/Body/E4/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |

### `root/Configuration`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true (hidden below Operator) |
| root/Configuration/Header/Chevron | `props.text` | expr | `if({view.custom.open_Configuration}, '▾', '▸')` | Text content |
| root/Configuration/Body | `position.display` | expr | `{view.custom.open_Configuration}` | Shown while expression is true |
| root/Configuration/Body/R0 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R0/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_EUMin}, '#,##0.###')` | Text content |
| root/Configuration/Body/R0/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E0 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E0/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_EUMin`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Configuration/Body/E0/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_EUMin', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E0/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R1 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R1/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_EUMax}, '#,##0.###')` | Text content |
| root/Configuration/Body/R1/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E1 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E1/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_EUMax`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Configuration/Body/E1/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_EUMax', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E1/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R2 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R2/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_RawMin}, '#,##0.###')` | Text content |
| root/Configuration/Body/R2/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E2 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E2/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_RawMin`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Configuration/Body/E2/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_RawMin', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E2/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R3 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R3/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_RawMax}, '#,##0.###')` | Text content |
| root/Configuration/Body/R3/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E3 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E3/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_RawMax`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Configuration/Body/E3/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_RawMax', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E3/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R4 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R4/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_FiltTC}, '#,##0.###')` | Text content |
| root/Configuration/Body/R4/EU | `props.text` | expr | `'s'` | Text content |
| root/Configuration/Body/E4 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E4/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_FiltTC`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Configuration/Body/E4/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_FiltTC', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E4/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R5 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R5/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_LoCutoff}, '#,##0.###')` | Text content |
| root/Configuration/Body/R5/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E5 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E5/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_LoCutoff`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Configuration/Body/E5/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_LoCutoff', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E5/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R6 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R6/Val | `props.text` | expr | `if({view.custom.m_Cfg_SqrtExtract}, 'Yes', 'No')` | Text content |
| root/Configuration/Body/C6 | `props.selected` | tag (indirect) | tag `{0}/Cfg_SqrtExtract`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (checkbox) |
| root/Configuration/Body/C6 | `props.selected` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_SqrtExtract', bool(currentValue.value), 4): self.refreshBinding('props.selected')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/C6 | `props.enabled` | expr | `{view.custom.level} >= 4` | Enabled while expression is true |
| root/Configuration/Body/C6 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |

## Scripts reference

Total: **19 scripts**: 4 event scripts (2 `component.onActionPerformed`, 2 `dom.onClick`) and 1 transform script (`custom.level`). 14 property-change `onChange` scripts (`props.value` of the entries and `props.selected` of the checkboxes, see the end of the list). No `customMethods`, no `messageHandlers`.

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

5. **transform on `(view root)` `custom.level`**: `custom.level` binding, `property` source `session.props.auth.securityLevels`.

```python
	return efc.ui.level(value)
```

6. **`root/Maintenance/Body/Sim`**: `propConfig` `props.selected` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Sim_En', bool(currentValue.value), 2):
			self.refreshBinding('props.selected')
```

7. **`root/Maintenance/Body/SimPV/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Sim_PV', currentValue.value, 2):
			self.refreshBinding('props.value')
```

8. **`root/Limits/Body/E0/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Alm_HH/Cfg_Lim', currentValue.value, 4):
			self.refreshBinding('props.value')
```

9. **`root/Limits/Body/E1/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Alm_H/Cfg_Lim', currentValue.value, 4):
			self.refreshBinding('props.value')
```

10. **`root/Limits/Body/E2/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Alm_L/Cfg_Lim', currentValue.value, 4):
			self.refreshBinding('props.value')
```

11. **`root/Limits/Body/E3/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Alm_LL/Cfg_Lim', currentValue.value, 4):
			self.refreshBinding('props.value')
```

12. **`root/Limits/Body/E4/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Alm_ROC/Cfg_Lim', currentValue.value, 4):
			self.refreshBinding('props.value')
```

13. **`root/Configuration/Body/E0/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_EUMin', currentValue.value, 4):
			self.refreshBinding('props.value')
```

14. **`root/Configuration/Body/E1/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_EUMax', currentValue.value, 4):
			self.refreshBinding('props.value')
```

15. **`root/Configuration/Body/E2/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_RawMin', currentValue.value, 4):
			self.refreshBinding('props.value')
```

16. **`root/Configuration/Body/E3/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_RawMax', currentValue.value, 4):
			self.refreshBinding('props.value')
```

17. **`root/Configuration/Body/E4/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_FiltTC', currentValue.value, 4):
			self.refreshBinding('props.value')
```

18. **`root/Configuration/Body/E5/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_LoCutoff', currentValue.value, 4):
			self.refreshBinding('props.value')
```

19. **`root/Configuration/Body/C6`**: `propConfig` `props.selected` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_SqrtExtract', bool(currentValue.value), 4):
			self.refreshBinding('props.selected')
```

### Explanation of each handler

| Handler | Action | Writes | Role check | Audit |
|---|---|---|---|---|
| `Header/Close` | `efc.ui.closeDynamic` restores the default dock view or closes the dock | none | none | no |
| `Alarms/Ack` | `efc.ui.ackAll` on the six alarms | `Alm_*/Cmd_Ack`, only where `Sts_Unack` is true | level 1 (in `efc.ui.ackAll`) | no |
| `Limits/Header` (dom click) | toggles `open_Limits` | none | none | no |
| `Configuration/Header` (dom click) | toggles `open_Configuration` | none | none | no |
| `Maintenance/Body/Sim` (`Sim_En` checkbox, onChange) | `efc.ui.setValue(... 'Sim_En', bool(value), 2)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Sim_En` | level 2 (`setValue`) | yes |
| `Maintenance/Body/SimPV` (`Sim_PV` entry, onChange) | `efc.ui.setValue(... 'Sim_PV', value, 2)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Sim_PV` | level 2 (`setValue`) | yes |
| `Limits/Body/E0` (`Alm_HH/Cfg_Lim` entry, onChange) | `efc.ui.setValue(... 'Alm_HH/Cfg_Lim', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Alm_HH/Cfg_Lim` | level 4 (`setValue`) | yes |
| `Limits/Body/E1` (`Alm_H/Cfg_Lim` entry, onChange) | `efc.ui.setValue(... 'Alm_H/Cfg_Lim', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Alm_H/Cfg_Lim` | level 4 (`setValue`) | yes |
| `Limits/Body/E2` (`Alm_L/Cfg_Lim` entry, onChange) | `efc.ui.setValue(... 'Alm_L/Cfg_Lim', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Alm_L/Cfg_Lim` | level 4 (`setValue`) | yes |
| `Limits/Body/E3` (`Alm_LL/Cfg_Lim` entry, onChange) | `efc.ui.setValue(... 'Alm_LL/Cfg_Lim', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Alm_LL/Cfg_Lim` | level 4 (`setValue`) | yes |
| `Limits/Body/E4` (`Alm_ROC/Cfg_Lim` entry, onChange) | `efc.ui.setValue(... 'Alm_ROC/Cfg_Lim', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Alm_ROC/Cfg_Lim` | level 4 (`setValue`) | yes |
| `Configuration/Body/E0` (`Cfg_EUMin` entry, onChange) | `efc.ui.setValue(... 'Cfg_EUMin', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_EUMin` | level 4 (`setValue`) | yes |
| `Configuration/Body/E1` (`Cfg_EUMax` entry, onChange) | `efc.ui.setValue(... 'Cfg_EUMax', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_EUMax` | level 4 (`setValue`) | yes |
| `Configuration/Body/E2` (`Cfg_RawMin` entry, onChange) | `efc.ui.setValue(... 'Cfg_RawMin', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_RawMin` | level 4 (`setValue`) | yes |
| `Configuration/Body/E3` (`Cfg_RawMax` entry, onChange) | `efc.ui.setValue(... 'Cfg_RawMax', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_RawMax` | level 4 (`setValue`) | yes |
| `Configuration/Body/E4` (`Cfg_FiltTC` entry, onChange) | `efc.ui.setValue(... 'Cfg_FiltTC', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_FiltTC` | level 4 (`setValue`) | yes |
| `Configuration/Body/E5` (`Cfg_LoCutoff` entry, onChange) | `efc.ui.setValue(... 'Cfg_LoCutoff', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_LoCutoff` | level 4 (`setValue`) | yes |
| `Configuration/Body/C6` (`Cfg_SqrtExtract` checkbox, onChange) | `efc.ui.setValue(... 'Cfg_SqrtExtract', bool(value), 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_SqrtExtract` | level 4 (`setValue`) | yes |

This view has no `efc.ui.cmd` calls. The simulate checkbox and simulated value entry (level 2), the limit entries and the configuration entries and checkbox (level 4) read their tags one way and write through `efc.ui.setValue`, which re-checks the level and audits.

### Library functions used (`projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.level(levels)`**: walks `session.props.auth.securityLevels` (nested `name`/`children`, a path string, or a plain role list) and returns the highest index, 0 to 5, of the names that match `['Guest','Operator','Maintenance','Supervisor','Engineer','Admin']` case-insensitively (site names map through `efc.ui.ROLE_ALIASES`; no match gives 0). Bound to `custom.level`. `efc.ui.userLevel` (used by the checks in `cmd`, `setValue`, `ackAll`, `bypass`, `unbypass` and `dblCmd`) takes the larger of this and the level from `session.props.auth.user.roles`.
- **`efc.ui.closeDynamic(component)`**: sizes the dock (`efc.ui.sizeDock`), then loads the page's stored `default` view and params (`session.custom.efcDw['<pageId>|<page path>']`) back into the `dw_Right` dock, or closes the dock if there is no default. Writes no tags.
- **`efc.ui.ackAll(component, alarms)`**: below level 1 it writes nothing and calls `efc.ui.denied` (WARN log and AccessDenied popup). Otherwise it reads `<alarm>/Sts_Unack` for the listed alarms, then writes `<alarm>/Cmd_Ack` = True for those that are true. No audit.
- **`efc.ui.setValue(component, member, value, minLevel=4, scale=1)`**: the commit behind every entry field and checkbox (decisions 14, 27). It returns False on an empty `tagPath` or a None value. Below `minLevel` it calls `efc.ui.denied` (WARN log and AccessDenied popup) and returns False. With `scale` other than 1 it writes `int(round(value * scale))` (the TIME entries pass 1000). It reads the old value and returns True without writing when the value is unchanged; otherwise it writes through `_writeTags` and, on a good write, audits `EFC set` with target `<tagPath>/<member>` and value `'<old> -> <new>'`. It returns whether the write was good; on False the onChange script calls `self.refreshBinding(...)`, so the field shows the tag value again.
- **`efc.ui.cmd`, `bypass`, `unbypass`, `dblCmd`**: not called from this view. `efc.ui.trend` is called by the Trend part, not here.

## Tag members used

All paths are relative to `tagPath`. Types and meanings are taken verbatim from `types/PCLib_Members.csv` (type `T_AI`; alarm members from `T_AlmLim`, and `Alm_Bad` from `T_Alarm`). The trend pen is read through tag history by the Trend part.

| Member | Access (read/write) | Data type | Meaning |
|---|---|---|---|
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Cfg_EU` | read | STRING[12] | Engineering units text |
| `Cfg_EUMax` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | PV at 100% (EU) |
| `Cfg_EUMin` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | PV at 0% (EU) |
| `Cfg_FiltTC` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | 1st-order filter time constant (s), 0 = off |
| `Cfg_LoCutoff` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Low cutoff (% span): PV forced to EUMin below this, 0 = off |
| `Cfg_RawMax` | read; write via `efc.ui.setValue` (level 4, audited) | INT | Raw counts at 100% (M340/M580 4-20mA default 10000) |
| `Cfg_RawMin` | read; write via `efc.ui.setValue` (level 4, audited) | INT | Raw counts at 0% (M340/M580 4-20mA default 0) |
| `Cfg_SqrtExtract` | read; write via `efc.ui.setValue` (level 4, audited) | BOOL | Square-root extraction (DP flow) |
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
| `Sim_En` | read; write via `efc.ui.setValue` (level 2, audited) | BOOL | Simulation enabled |
| `Sim_PV` | read; write via `efc.ui.setValue` (level 2, audited) | REAL | Simulated PV (EU) |
| `Alm_Bad/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_Bad/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_Bad/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_Bad/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_H/Cfg_Lim` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Alm_H/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_H/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_H/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_H/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_HH/Cfg_Lim` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Alm_HH/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_HH/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_HH/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_HH/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_L/Cfg_Lim` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Alm_L/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_L/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_L/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_L/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_LL/Cfg_Lim` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Alm_LL/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_LL/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_LL/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_LL/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_ROC/Cfg_Lim` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
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
- **Units not shown on several rows.** The four PV limit rows (`Alm_HH`, `Alm_H`, `Alm_L`, `Alm_LL`) and the EU min and EU max rows show no unit, although the values are in `Cfg_EU`. The low cutoff (`Cfg_LoCutoff`) is documented in PCLib as % of span, but it is shown with no unit.
- **Banner colour for a good value.** A good reading uses the style `State/Stopped` (the stopped style) whatever its value. Confirm that this is intended.
- **Bad-quality handling is not configurable here.** The banner switches to BAD QUALITY, but the value rows still show `Val_PV`. The alarms still apply. The bad-quality settings (`Cfg_BadAction`, `Cfg_SubstPV`, `Cfg_BadLoPct`, `Cfg_BadHiPct`) and `Sts_Quality` and `Inp_NE107` are not shown in this view. Only the SUBST badge (`Sts_Subst`) is visible. Confirm the intended behaviour.
- **Trend hides bad quality.** `efc.ui.trend` queries history with `ignoreBadQuality=True`, so periods of bad quality are left out of the plot without any marker. The trend shows `Val_PV` only.
