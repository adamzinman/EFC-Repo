# Docks/ValveAnalog

Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Docks/ValveAnalog/view.json`
Opened from: the analog valve template (`Valve_Control`; see [Analog valve template](../Templates/Valves/Valve_Control.md)) through `efc.ui.openDynamic`. Dynamic window id `dw_ValveAnalog`.

## Overview

The operator and maintenance dynamic window for an analog control valve (T_CValve). It opens in the screen's right-hand region (`Docks/Region`), not as a popup. It shows demand and position, manual position entry and presets, interlock detail, alarms, a trend and configuration. It has no maintenance section.

- **Default size:** 400 x 860 (`props.defaultSize`). The root is a scrolling column.
- **Parameters:** `tagPath` (the T_CValve instance) and `tType` (default `T_CValve`).
- **How it is opened:** the template's single click runs `efc.ui.openDynamic(self)`. The template's `dockId` is empty, so the function uses `BY_TYPE` in `efc/ui/code.py`, which maps `T_CValve` to `dw_ValveAnalog`. It then writes `session.custom.efcDw[pageId] = {path: 'Docks/ValveAnalog', params: {tagPath: ...}}`. `Docks/Region` then displays this view. `efc.ui.openDynamic` passes only `tagPath` (and `model` if present). **`tType` is never passed**, so the dock always runs with its default `T_CValve`. Nothing in this view uses `tType`.
- **Generated view:** this view is written by `generator/docks/build_docks.py` (function `valve_analog()`). Change the generator, not `view.json`, or the next build overwrites the edit.
- **How it closes:** the header `X` runs `efc.ui.closeDynamic(self)`, which restores the screen default set by `efc.ui.setDefaultDock` on `Docks/Region` startup. That startup script is not in this view.

## How it operates

**Header.** Shows `Cfg_Tag` (large) and `Cfg_Desc`.

**Banner.** The state label is chosen by priority: UNKNOWN first, while `Val_Pos` or `Sts_Closed` is null or has bad quality (`isNull(...) || !isGood(...)`, class `State/Unknown`); then `Sts_Fault` (FAULT), `Sts_Intlk` (INTERLOCKED), `Sts_Closed` (CLOSED), else `OPEN nn %`, where nn is `Val_Pos` rounded to whole percent. The style class follows the same order (`State/Unknown`, `State/Fault`, `State/Fault`, `State/Stopped`, `State/Running`). The last condition is the literal `true`, so the trailing `UNKNOWN` fallback is never reached; UNKNOWN comes from the first case. Two chips appear: SIM (`Sts_Sim`) and RATE LIM (`Sts_RateLim`, output is being rate limited).

**Mode.** As on the discrete valve dock, the mode text shows the highest of OOS, MAINT, MAN, else AUTO. The four toggle buttons highlight the active mode. AUTO and MAN are visible at level 1 and above, and MAINT and OOS at level 2 and above. None of the four has an `enabled` binding, so each is clickable whenever it is visible. Each writes a one-shot `Mode/Cmd_*`. MAINT and OOS are audited.

**Commands** (level 1 and above). The section shows these controls:
- `RESET` writes `Cmd_Reset`. It has no enable condition, so it is clickable in any state.
- `Pos` is a manual position entry (%) bound bidirectionally to `Cmd_ManPos`. It is enabled when `Mode/Sts_Man && !Sts_Intlk`.
- Five preset buttons (0, 25, 50, 75 and 100 %) each write `Cmd_ManPos` through `efc.ui.cmd` at level 1. Their enable expression is the same as the entry.
- A hint line reads "Position entry and presets enabled in MAN, not interlocked".

**Values** (all levels). Demand (`Val_Demand`). Position (`Val_Pos`) and Deviation (`Val_Dev`), both shown only when `Cfg_HasFbk` is true. Travel (`Val_Travel`) and Reversals (`Val_Reversals`). A diagnostics row shows the NAMUR NE107 text for `Sts_NE107`: 0 `NE107 OK`, 1 `NE107 F`, 2 `NE107 C`, 3 `NE107 S`, 4 `NE107 M`.

**Interlocks.** One embedded `Docks/Parts/IntlkList` view gets `tagPath + '/Intlk'` with the title "Interlocks". There is no permissive list, because T_CValve has no `Perm` group. The content of the embedded view is not in this file (see [Parts/IntlkList.md](Parts/IntlkList.md)).

**Alarms** (all levels). Three rows: position deviation (`Alm_PosDev`), feedback bad (`Alm_FbkBad`) and interlock trip (`Alm_IntlkTrip`). A row is coloured when its alarm is active, using the alarm's `Cfg_Priority`: 1 `Critical`, 2 `High`, 3 `Medium`, 4 `Low`, anything else `Medium`. The class adds `/Unacked` or `/Fill`. An inactive but unacknowledged alarm uses `Alarm/Status/ClearedUnacked`. An inactive, acknowledged alarm uses `Text/Caption Text/Color/Muted`. "No active alarms" is shown when none is active. **ACK** (level 1 and above) calls `efc.ui.ackAll`, which writes `Cmd_Ack` only for those alarms whose `Sts_Unack` is true.

**Trend.** Embeds `Docks/Parts/Trend` with pens `Val_Demand` and `Val_Pos`. The embedded view's `expanded` param starts `false`. It is declared `inout` in `Docks/Parts/Trend`, so the trend part toggles it and the value flows back to this embed. The `position.basis` binding (`{this.props.params.expanded}`) then grows the trend from 15.741 vh to 70.370 vh. The expansion is local to the trend and does not widen the dock region (see [Parts/Trend.md](Parts/Trend.md)).

**Configuration** (collapsible; the header click toggles `open_Configuration`, collapsed by default). It holds seven values: Output min, Output max, Rate up, Rate down, Deviation limit, Deviation time and Tight shutoff. Below level 4 each shows as a read-only label. At level 4 and above each has a numeric entry bound bidirectionally to its tag. The entries have the literal enable `true`, so the level 4 rule is enforced only by visibility.

**Maintenance.** None. This window has no maintenance section, run-hour counters or SIMULATE button. `Sim_En` is not referenced. Simulation shows only as the SIM chip in the banner.

**Role checks.** All role levels come from the Perspective session (`session.props.auth.user.roles`) and are checked in the client. `efc.ui.cmd` returns without writing when the level is too low. The manual position entry and the Configuration entries are bindings that write tags directly. Their only guards are their visibility and enable expressions. Real access control has to be enforced in Perspective security and the PLC logic.

**Audit.** `efc.ui` writes an audit entry (`system.util.audit`, and the logger as a fallback record) only for calls with `audit=True`, which here means MAINT and OOS. Nothing audits AUTO, MAN, RESET, the presets, ACK, the manual position entry or configuration edits.

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `""` | T_CValve instance. Every component binding uses `{view.params.tagPath}`. | Set by `efc.ui.openDynamic` from the template's `dwTagPath` (or `tagPath`, `cardPath`). Read by bindings and `efc.ui` commands. |
| `tType` | input | `T_CValve` | Declared type. | Not passed by `efc.ui.openDynamic`; not referenced by any binding or script in this view. Always the default. |

Both have `paramDirection: input` and `persistent: true`. No output parameters.

### View-level custom properties (`custom`)

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.level` | `0` | property + script transform | `session.props.auth.user.roles` → `return efc.ui.level(value)` | Role level 0-5 from `session.props.auth.user.roles` via `efc.ui.level`. Gates buttons and sections (Guest 0, Operator 1, Maintenance 2, Supervisor 3, Engineer 4, Admin 5). |
| `view.custom.open_Configuration` | `false` | none (written by scripts) | none | View-local toggle for the Configuration section. Set by the header click script; not bound to any tag; not persisted. |

#### Tag mirrors (`custom.m_*`)

There are 34 tag-mirror properties. Each `custom.m_<member>` (with `/` replaced by `_`) has an indirect, read-only tag binding to `{view.params.tagPath}/<member>` (`bidirectional: false`, fallback delay 2.5 s), and its default is `null`. The rest of the view reads tag values only through these mirrors. The manual position entry and the Configuration entries are the exceptions: they bind directly to their tags.

| Group | Members |
|---|---|
| Mode | `Mode/Sts_Man`, `Mode/Sts_OOS`, `Mode/Sts_Maint`, `Mode/Sts_Auto` |
| Config | `Cfg_Tag`, `Cfg_Desc`, `Cfg_HasFbk`, `Cfg_OutMin`, `Cfg_OutMax`, `Cfg_RateUp`, `Cfg_RateDn`, `Cfg_DevLim`, `Cfg_DevTime`, `Cfg_TightShut` |
| Values | `Val_Pos`, `Val_Demand`, `Val_Dev`, `Val_Travel`, `Val_Reversals` |
| Alarms | `Alm_PosDev/Sts_Active`, `Alm_PosDev/Sts_Unack`, `Alm_PosDev/Cfg_Priority`, `Alm_FbkBad/Sts_Active`, `Alm_FbkBad/Sts_Unack`, `Alm_FbkBad/Cfg_Priority`, `Alm_IntlkTrip/Sts_Active`, `Alm_IntlkTrip/Sts_Unack`, `Alm_IntlkTrip/Cfg_Priority` |
| Status / other | `Sts_Intlk`, `Sts_Fault`, `Sts_Closed`, `Sts_Sim`, `Sts_RateLim`, `Sts_NE107` |

### Component-level custom properties

None.

### Session, page and message payloads

- `session.props.auth.user.roles`: read by `custom.level` (transform `efc.ui.level`).
- `session.props.auth.user.userName`: read by `efc.ui._audit` (not bound in this view).
- `session.custom.efcDw[pageId]`: written by `efc.ui.openDynamic` and `closeDynamic` in the template and header; read by `Docks/Region` (not in this file).
- `page.props.pageId`: read by `efc.ui._state` to key `efcDw`.
- No message handlers. No `customMethods`.

## Bindings reference

Total: **124 bindings**: 35 at view root (1 `property` binding with a transform, plus 34 tag mirrors) and 89 on components. Types: 81 `expr`, 42 `tag`, 1 `property`. `params.tagPath` and `params.tType` have `paramDirection` only. Embedded-view `params.*` values and `position.basis` are component bindings and are counted in the 89.

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
| root/Banner | `props.style.classes` | expr | `if(isNull({view.custom.m_Val_Pos}) || !isGood({view.custom.m_Val_Pos}) || isNull({view.custom.m_Sts_Closed}) || !isGood({view.custom.m_Sts_Closed}), 'State/Unknown', if({view.custom.m_Sts_Fault}, 'State/Fault', if({view.custom.m_Sts_Intlk}, 'State/Fault', if({view.custom.m_Sts_Closed}, 'State/Stopped', if(true, 'State/Running', 'State/Unknown')))))` | CSS class(es) selected by state |
| root/Banner/State | `props.text` | expr | `if(isNull({view.custom.m_Val_Pos}) || !isGood({view.custom.m_Val_Pos}) || isNull({view.custom.m_Sts_Closed}) || !isGood({view.custom.m_Sts_Closed}), 'UNKNOWN', if({view.custom.m_Sts_Fault}, 'FAULT', if({view.custom.m_Sts_Intlk}, 'INTERLOCKED', if({view.custom.m_Sts_Closed}, 'CLOSED', if(true, 'OPEN ' + numberFormat({view.custom.m_Val_Pos}, '0') + ' %', 'UNKNOWN')))))` | Text content |
| root/Banner/Chip0 | `position.display` | expr | `{view.custom.m_Sts_Sim}` | Shown while expression is true |
| root/Banner/Chip1 | `position.display` | expr | `{view.custom.m_Sts_RateLim}` | Shown while expression is true |

### `root/Mode`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Mode/Body/Current/Val | `props.text` | expr | `if({view.custom.m_Mode_Sts_OOS}, 'OOS', if({view.custom.m_Mode_Sts_Maint}, 'MAINT', if({view.custom.m_Mode_Sts_Man}, 'MAN', 'AUTO')))` | Text content |
| root/Mode/Body/Buttons/Auto | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Mode/Body/Buttons/Auto | `props.style.classes` | expr | `if({view.custom.m_Mode_Sts_Auto}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |
| root/Mode/Body/Buttons/Man | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Mode/Body/Buttons/Man | `props.style.classes` | expr | `if({view.custom.m_Mode_Sts_Man}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |
| root/Mode/Body/Buttons/Maint | `position.display` | expr | `{view.custom.level} >= 2` | Shown while expression is true |
| root/Mode/Body/Buttons/Maint | `props.style.classes` | expr | `if({view.custom.m_Mode_Sts_Maint}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |
| root/Mode/Body/Buttons/OOS | `position.display` | expr | `{view.custom.level} >= 2` | Shown while expression is true |
| root/Mode/Body/Buttons/OOS | `props.style.classes` | expr | `if({view.custom.m_Mode_Sts_OOS}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |

### `root/Commands`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Commands | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Commands/Body/Buttons/B0 | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Commands/Body/Pos | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Commands/Body/Pos/Entry | `props.value` | tag (indirect) | tag `{0}/Cmd_ManPos` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Commands/Body/Pos/Entry | `props.enabled` | expr | `{view.custom.m_Mode_Sts_Man} && !{view.custom.m_Sts_Intlk}` | Enabled while expression is true |
| root/Commands/Body/Presets/P0 | `props.enabled` | expr | `{view.custom.m_Mode_Sts_Man} && !{view.custom.m_Sts_Intlk}` | Enabled while expression is true |
| root/Commands/Body/Presets/P25 | `props.enabled` | expr | `{view.custom.m_Mode_Sts_Man} && !{view.custom.m_Sts_Intlk}` | Enabled while expression is true |
| root/Commands/Body/Presets/P50 | `props.enabled` | expr | `{view.custom.m_Mode_Sts_Man} && !{view.custom.m_Sts_Intlk}` | Enabled while expression is true |
| root/Commands/Body/Presets/P75 | `props.enabled` | expr | `{view.custom.m_Mode_Sts_Man} && !{view.custom.m_Sts_Intlk}` | Enabled while expression is true |
| root/Commands/Body/Presets/P100 | `props.enabled` | expr | `{view.custom.m_Mode_Sts_Man} && !{view.custom.m_Sts_Intlk}` | Enabled while expression is true |

### `root/Values`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Values/Body/Dem/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Demand}, '#,##0.0')` | Text content |
| root/Values/Body/Dem/EU | `props.text` | expr | `'%'` | Text content |
| root/Values/Body/Pos | `position.display` | expr | `{view.custom.m_Cfg_HasFbk}` | Shown while expression is true |
| root/Values/Body/Pos/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Pos}, '#,##0.0')` | Text content |
| root/Values/Body/Pos/EU | `props.text` | expr | `'%'` | Text content |
| root/Values/Body/Dev | `position.display` | expr | `{view.custom.m_Cfg_HasFbk}` | Shown while expression is true |
| root/Values/Body/Dev/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Dev}, '#,##0.0')` | Text content |
| root/Values/Body/Dev/EU | `props.text` | expr | `'%'` | Text content |
| root/Values/Body/Trv/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Travel}, '#,##0')` | Text content |
| root/Values/Body/Trv/EU | `props.text` | expr | `'%'` | Text content |
| root/Values/Body/Rev/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Reversals}, '#,##0')` | Text content |
| root/Values/Body/NE107/Val | `props.text` | expr | `case(toInt({view.custom.m_Sts_NE107}), 0, 'NE107 OK', 1, 'NE107 F', 2, 'NE107 C', 3, 'NE107 S', 4, 'NE107 M', '')` | Text content |

### `root/Intlk`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Intlk | `props.params.tagPath` | expr | `{view.params.tagPath} + '/Intlk'` | Embedded view tagPath param |

### `root/Alarms`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Alarms/Body/None | `position.display` | expr | `!({view.custom.m_Alm_PosDev_Sts_Active} \|\| {view.custom.m_Alm_FbkBad_Sts_Active} \|\| {view.custom.m_Alm_IntlkTrip_Sts_Active})` | Shown while expression is true |
| root/Alarms/Body/List/A0 | `props.style.classes` | expr | `if({view.custom.m_Alm_PosDev_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_PosDev_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_PosDev_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_PosDev_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A1 | `props.style.classes` | expr | `if({view.custom.m_Alm_FbkBad_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_FbkBad_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_FbkBad_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_FbkBad_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A2 | `props.style.classes` | expr | `if({view.custom.m_Alm_IntlkTrip_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_IntlkTrip_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_IntlkTrip_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_IntlkTrip_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/Ack | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |

### `root/Trend`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Trend | `props.params.tagPath` | expr | `{view.params.tagPath}` | Embedded view tagPath param |
| root/Trend | `position.basis` | expr | `if({this.props.params.expanded}, '70.370vh', '15.741vh')` | Row height |

### `root/Configuration`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration/Header/Chevron | `props.text` | expr | `if({view.custom.open_Configuration}, '▾', '▸')` | Text content |
| root/Configuration/Body | `position.display` | expr | `{view.custom.open_Configuration}` | Shown while expression is true |
| root/Configuration/Body/R0 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R0/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_OutMin}, '#,##0.###')` | Text content |
| root/Configuration/Body/R0/EU | `props.text` | expr | `'%'` | Text content |
| root/Configuration/Body/E0 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E0/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_OutMin` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E0/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R1 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R1/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_OutMax}, '#,##0.###')` | Text content |
| root/Configuration/Body/R1/EU | `props.text` | expr | `'%'` | Text content |
| root/Configuration/Body/E1 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E1/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_OutMax` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E1/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R2 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R2/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_RateUp}, '#,##0.###')` | Text content |
| root/Configuration/Body/R2/EU | `props.text` | expr | `'%/s'` | Text content |
| root/Configuration/Body/E2 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E2/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_RateUp` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E2/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R3 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R3/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_RateDn}, '#,##0.###')` | Text content |
| root/Configuration/Body/R3/EU | `props.text` | expr | `'%/s'` | Text content |
| root/Configuration/Body/E3 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E3/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_RateDn` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E3/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R4 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R4/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_DevLim}, '#,##0.###')` | Text content |
| root/Configuration/Body/R4/EU | `props.text` | expr | `'%'` | Text content |
| root/Configuration/Body/E4 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E4/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_DevLim` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E4/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R5 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R5/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_DevTime}, '#,##0.###')` | Text content |
| root/Configuration/Body/R5/EU | `props.text` | expr | `'s'` | Text content |
| root/Configuration/Body/E5 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E5/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_DevTime` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E5/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R6 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R6/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_TightShut}, '#,##0.###')` | Text content |
| root/Configuration/Body/R6/EU | `props.text` | expr | `'%'` | Text content |
| root/Configuration/Body/E6 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E6/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_TightShut` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E6/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |

## Scripts reference

Total: **14 scripts**: 13 event scripts (12 `component.onActionPerformed`, 1 `dom.onClick`) and 1 transform script (`custom.level`). No `customMethods`, no `messageHandlers`, no property-change `onChange` scripts.

The button handlers below call `efc.ui` functions. Those functions are summarised after the list.

1. **`root/Header/Close`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.closeDynamic(self)
```

2. **`root/Mode/Body/Buttons/Auto`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Mode/Cmd_Auto', True, 1, audit=False)
```

3. **`root/Mode/Body/Buttons/Man`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Mode/Cmd_Man', True, 1, audit=False)
```

4. **`root/Mode/Body/Buttons/Maint`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Mode/Cmd_Maint', True, 2, audit=True)
```

5. **`root/Mode/Body/Buttons/OOS`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Mode/Cmd_OOS', True, 2, audit=True)
```

6. **`root/Commands/Body/Buttons/B0`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_Reset', True, 1)
```

7. **`root/Commands/Body/Presets/P0`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_ManPos', 0.0, 1)
```

8. **`root/Commands/Body/Presets/P25`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_ManPos', 25.0, 1)
```

9. **`root/Commands/Body/Presets/P50`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_ManPos', 50.0, 1)
```

10. **`root/Commands/Body/Presets/P75`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_ManPos', 75.0, 1)
```

11. **`root/Commands/Body/Presets/P100`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_ManPos', 100.0, 1)
```

12. **`root/Alarms/Body/Ack`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.ackAll(self, ['Alm_PosDev', 'Alm_FbkBad', 'Alm_IntlkTrip'])
```

13. **`root/Configuration/Header`**: `events.dom.onClick`, scope G.

```python
	self.view.custom.open_Configuration = not self.view.custom.open_Configuration
```

14. **transform on `(view root)` `custom.level`**: `custom.level` binding, `property` source `session.props.auth.user.roles`.

```python
	return efc.ui.level(value)
```

### Explanation of each handler

| Handler | Action | Writes | Role check | Audit |
|---|---|---|---|---|
| `Header/Close` | `efc.ui.closeDynamic` restores default region view | none | none | no |
| `Mode/Auto` | `efc.ui.cmd(... 'Mode/Cmd_Auto', True, 1)` | `Mode/Cmd_Auto` | level 1 | no |
| `Mode/Man` | `efc.ui.cmd(... 'Mode/Cmd_Man', True, 1)` | `Mode/Cmd_Man` | level 1 | no |
| `Mode/Maint` | `efc.ui.cmd(... 'Mode/Cmd_Maint', True, 2)` | `Mode/Cmd_Maint` | level 2 | yes |
| `Mode/OOS` | `efc.ui.cmd(... 'Mode/Cmd_OOS', True, 2)` | `Mode/Cmd_OOS` | level 2 | yes |
| `Commands/B0` (RESET) | `efc.ui.cmd(... 'Cmd_Reset', True, 1)` | `Cmd_Reset` | level 1 | no |
| `Commands/Presets/P0` (0 %) | `efc.ui.cmd(... 'Cmd_ManPos', 0.0, 1)` | `Cmd_ManPos` | level 1 | no |
| `Commands/Presets/P25` (25 %) | `efc.ui.cmd(... 'Cmd_ManPos', 25.0, 1)` | `Cmd_ManPos` | level 1 | no |
| `Commands/Presets/P50` (50 %) | `efc.ui.cmd(... 'Cmd_ManPos', 50.0, 1)` | `Cmd_ManPos` | level 1 | no |
| `Commands/Presets/P75` (75 %) | `efc.ui.cmd(... 'Cmd_ManPos', 75.0, 1)` | `Cmd_ManPos` | level 1 | no |
| `Commands/Presets/P100` (100 %) | `efc.ui.cmd(... 'Cmd_ManPos', 100.0, 1)` | `Cmd_ManPos` | level 1 | no |
| `Alarms/Ack` | `efc.ui.ackAll` on the three alarms | `Alm_*/Cmd_Ack` where unacked | level 1 | no |
| `Configuration/Header` (dom click) | toggles `open_Configuration` | none | none | no |

`efc.ui.cmd` writes `view.params.tagPath + '/' + member` with `system.tag.writeBlocking` only when `userLevel >= minLevel`. The Mode buttons, RESET, the presets and ACK therefore use the level check. The manual position entry and the Configuration entries do not, because they are bindings.

### Library functions used (`projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.level(roles)`**: highest index of the role in `['Guest','Operator','Maintenance','Supervisor','Engineer','Admin']`, or 0. Bound to `custom.level`.
- **`efc.ui.closeDynamic(component)`**: writes `efcDw[pageId]` back to the stored `default` path and params. Writes no tags.
- **`efc.ui.cmd(component, member, value, minLevel, audit)`**: the role-checked write described above. It writes the value once with `writeBlocking` and does not write it back. One-shot members therefore depend on the PLC clearing them. Audits when `audit=True`.
- **`efc.ui.ackAll(component, alarms)`**: reads `<alarm>/Sts_Unack` for the listed alarms, then writes `<alarm>/Cmd_Ack` = True for those that are true, at level 1 and above.
- **`efc.ui.openDynamic`** (called from the template, not from this view): maps the template's type to a window and writes the region state.
- **`efc.ui.bypass` / `unbypass`**: exist in the module but are not called from this view. Interlock bypass is handled in the embedded `IntlkList` views, which are not in this file.

## Tag members used

All paths are relative to `tagPath`. Types come from `types/PCLib_Members.csv` (nested types: `Mode` = T_Mode, `Alm_*` = T_Alarm, `Intlk` = T_Intlk). Trend pens are read by the embedded trend part.

| Member | Access | Data type | Meaning |
|---|---|---|---|
| `Mode/Sts_Man` | read | BOOL | In Manual (commanded by operator) - MTP Operator. |
| `Sts_Intlk` | read | BOOL | Interlock active. |
| `Cfg_Tag` | read | STRING[20] | Equipment / instrument tag, e.g. FT-101. |
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate. |
| `Sts_Fault` | read | BOOL | Any fault present. |
| `Sts_Closed` | read | BOOL | Valve closed. |
| `Val_Pos` | read | REAL | Position (%) - feedback, or demand if no feedback. Also read by a trend pen. |
| `Sts_Sim` | read | BOOL | Simulation active. |
| `Sts_RateLim` | read | BOOL | Output is being rate limited. |
| `Mode/Sts_OOS` | read | BOOL | Out of service - MTP Offline. |
| `Mode/Sts_Maint` | read | BOOL | In Maintenance. |
| `Mode/Sts_Auto` | read | BOOL | In Automatic (commanded by owner) - MTP Automatic. |
| `Val_Demand` | read | REAL | Active demand before rate limit (%). Also read by a trend pen. |
| `Cfg_HasFbk` | read | BOOL | Position feedback fitted. |
| `Val_Dev` | read | REAL | Demand minus position (%). |
| `Val_Travel` | read | REAL | Accumulated travel (% of full stroke, summed) for diagnostics. |
| `Val_Reversals` | read | UDINT | Direction reversal count. |
| `Sts_NE107` | read | INT | NAMUR NE107 status: 0=Good 1=Failure (F) 2=Function check (C) 3=Out of specification (S) 4=Maintenance required (M). |
| `Alm_PosDev/Sts_Active` | read | BOOL | Alarm active (after delays and latch). |
| `Alm_PosDev/Sts_Unack` | read | BOOL | Alarm unacknowledged. |
| `Alm_PosDev/Cfg_Priority` | read | INT | Rationalised priority: 1=Emergency 2=High 3=Medium 4=Low. |
| `Alm_FbkBad/Sts_Active` | read | BOOL | Alarm active (after delays and latch). |
| `Alm_FbkBad/Sts_Unack` | read | BOOL | Alarm unacknowledged. |
| `Alm_FbkBad/Cfg_Priority` | read | INT | Rationalised priority: 1=Emergency 2=High 3=Medium 4=Low. |
| `Alm_IntlkTrip/Sts_Active` | read | BOOL | Alarm active (after delays and latch). |
| `Alm_IntlkTrip/Sts_Unack` | read | BOOL | Alarm unacknowledged. |
| `Alm_IntlkTrip/Cfg_Priority` | read | INT | Rationalised priority: 1=Emergency 2=High 3=Medium 4=Low. |
| `Cfg_OutMin` | read/write | REAL | Minimum output (%). |
| `Cfg_OutMax` | read/write | REAL | Maximum output (%). |
| `Cfg_RateUp` | read/write | REAL | Opening rate limit (%/s), 0 = none. |
| `Cfg_RateDn` | read/write | REAL | Closing rate limit (%/s), 0 = none. |
| `Cfg_DevLim` | read/write | REAL | Position deviation alarm limit (%). |
| `Cfg_DevTime` | read/write | TIME | Deviation must persist this long. |
| `Cfg_TightShut` | read/write | REAL | Demand below this (%) forces 0 for tight shut-off. |
| `Cmd_ManPos` | read/write | REAL | Operator manual demand (%). |
| `Intlk` | read | T_Intlk | Passed as tagPath to the embedded `Docks/Parts/IntlkList` view |
| `Mode/Cmd_Auto` | write | BOOL | Operator request Automatic (one-shot). |
| `Mode/Cmd_Man` | write | BOOL | Operator request Manual (one-shot). |
| `Mode/Cmd_Maint` | write | BOOL | Request Maintenance (one-shot). |
| `Mode/Cmd_OOS` | write | BOOL | Request Out-of-Service (one-shot). |
| `Cmd_Reset` | write | BOOL | Fault reset (one-shot). |
| `Alm_PosDev/Cmd_Ack` | write | BOOL | Operator acknowledge (one-shot). Written by ackAll only when the alarm is unacknowledged. |
| `Alm_FbkBad/Cmd_Ack` | write | BOOL | Operator acknowledge (one-shot). Written by ackAll only when the alarm is unacknowledged. |
| `Alm_IntlkTrip/Cmd_Ack` | write | BOOL | Operator acknowledge (one-shot). Written by ackAll only when the alarm is unacknowledged. |

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
  - `Mode` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
    - `Body` (ia.container.flex)
      - `Current` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
      - `Buttons` (ia.container.flex)
        - `Auto` (ia.input.button)
        - `Man` (ia.input.button)
        - `Maint` (ia.input.button)
        - `OOS` (ia.input.button)
  - `Commands` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
    - `Body` (ia.container.flex)
      - `Buttons` (ia.container.flex)
        - `B0` (ia.input.button)
      - `Pos` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `Presets` (ia.container.flex)
        - `P0` (ia.input.button)
        - `P25` (ia.input.button)
        - `P50` (ia.input.button)
        - `P75` (ia.input.button)
        - `P100` (ia.input.button)
      - `Hint` (ia.display.label)
  - `Values` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
    - `Body` (ia.container.flex)
      - `Dem` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Pos` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Dev` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Trv` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Rev` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
      - `NE107` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
  - `Intlk` (ia.display.view)
  - `Alarms` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
    - `Body` (ia.container.flex)
      - `None` (ia.display.label)
      - `List` (ia.container.flex)
        - `A0` (ia.display.label)
        - `A1` (ia.display.label)
        - `A2` (ia.display.label)
      - `Ack` (ia.input.button)
  - `Trend` (ia.display.view)
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
        - `EU` (ia.display.label)
      - `E6` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
```

## Notes and open questions

- **Banner fallback shows OPEN.** The last banner case is `true`, so any state that is not FAULT, INTERLOCKED or CLOSED is shown as `OPEN nn %`, including mid-travel and idle states. T_CValve has no opening or closing member, so travel direction is not shown.
- **Position shown without feedback.** The banner's `OPEN nn %` always uses `Val_Pos`, and the PCLib comment says `Val_Pos` is the demand when there is no feedback. The Position row, however, is hidden when `Cfg_HasFbk` is false. Confirm whether the banner percentage should be shown in that case.
- **Manual position does not check faults.** The entry and presets are enabled by `Mode/Sts_Man && !Sts_Intlk` only. They do not check `Sts_Fault`. The double-tap rule in `efc/ui/code.py` (`READY_FALSE`, which applies to T_DValve and T_Motor only) does check `Sts_Fault`. The discrete dock's OPEN and CLOSE rule does not. T_CValve has no `Sts_Avail`, `Sts_Local` or `Sts_NotPerm`, so none of those are checked here.
- **The manual position entry bypasses `efc.ui.cmd`.** It is a bidirectional tag binding to `Cmd_ManPos`. Its only role control is visibility (level 1), and it is not audited. The presets use `efc.ui.cmd` (checked, not audited). Both are level 1, so the result is the same in practice, but the two paths differ.
- **Configuration is not role-checked in script or audited.** The entries write tags directly through bindings, and the view does not validate values (for example Output min against Output max). The enable expression is the literal `true`, so level 4 is enforced only by visibility.
- **`Cfg_HasFbk` cannot be changed here.** It controls the Position and Deviation rows, but it is not in the Configuration section and is not written by this view.
- **Units of TIME members.** `Cfg_DevTime` is a TIME member. The dock shows the raw value with unit `s`. Confirm whether the tag delivers seconds or milliseconds before commissioning.
- **RESET is always enabled, and the mode buttons have no enable.** RESET has no enable expression, so it is clickable at level 1 and above in any state. The four mode buttons also have no enable expression. The position entry and presets are the only manual controls with an enable, and it is `Mode/Sts_Man && !Sts_Intlk`.
