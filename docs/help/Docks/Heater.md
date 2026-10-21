# Docks/Heater

Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Docks/Heater/view.json`
Opened from: the electric heater template (`HeatTransfer/Heater_Electric`; see [Electric heater template](../Templates/HeatTransfer/Heater_Electric.md)) through `efc.ui.openDynamic`. Dynamic window id `dw_Heater`.

## Overview

The operator and maintenance dynamic window for an electric heater (T_Heater). It opens in the screen's right-hand region (`Docks/Region`), not as a popup. It shows state, interlock and permissive detail, mode, on/off and power-demand commands, control and power values, alarms, a trend, maintenance counters and configuration. The control type (`Cfg_CtrlType`) decides which rows are shown: 0 on/off, 1 time-proportioned SSR, 2 SCR phase angle.

- **Default size:** 400 x 860 (`props.defaultSize`). The root is a scrolling column.
- **Parameters:** `tagPath` (the T_Heater instance) and `tType` (default `T_Heater`).
- **How it is opened:** the template's single click runs `efc.ui.openDynamic(self)`. The template's `tType` is `T_Heater` and its `dockId` is empty, so `efc.ui.openDynamic` maps it to `dw_Heater` and writes `session.custom.efcDw[pageId] = {path: 'Docks/Heater', params: {tagPath: ...}}`. `Docks/Region` then displays this view. `efc.ui.openDynamic` passes only `tagPath` (and `model` if present). **`tType` is never passed**, so the dock always runs with its default `T_Heater`. Nothing in this view uses `tType`.
- **Generated view:** this view is written by `generator/docks/build_docks.py` (function `heater()`). Change the generator, not `view.json`, or the next build overwrites the edit.
- **How it closes:** the header `X` runs `efc.ui.closeDynamic(self)`, which restores the screen default set by `efc.ui.setDefaultDock` on `Docks/Region` startup. That startup script is not in this view.

## How it operates

**Header.** Shows `Cfg_Tag` (large) and `Cfg_Desc`.

**Banner.** The state label is chosen by priority: `Sts_HiLimit` (HIGH LIMIT), `Sts_Tripped` (TRIPPED), `Sts_Fault` (FAULT), `Sts_Heating` (HEATING), `Sts_On` (ON), `Sts_Off` (OFF), else UNKNOWN. The style class follows the same order (`State/Fault` for the first three, `State/Running` for HEATING and ON, `State/Stopped` for OFF, else `State/Unknown`). Four badges appear when their flag is true: SIM (`Sts_Sim`), LOCAL (`Sts_Local`), INTLK (`Sts_Intlk`), NOT PERM (`Sts_NotPerm`).

**Mode.** The mode text shows the highest of OOS, MAINT, MAN, else AUTO. The four toggle buttons highlight the active mode. AUTO and MAN are visible at level 1 and above, and MAINT and OOS at level 2 and above. None of the four has an `enabled` binding, so they are always clickable when visible. Each writes a one-shot `Mode/Cmd_*`. MAINT and OOS are audited.

**Commands** (level 1 and above). Three buttons and one power-demand entry:

- `ON` (`B0`) writes `Cmd_On`. Enabled only when all of these are true: `Mode/Sts_Man`, `Sts_Avail`, not `Sts_Intlk`, not `Sts_Local`, not `Sts_NotPerm`. It does not check `Sts_On`, `Sts_Tripped`, `Sts_Fault`, `Sts_HiLimit` or `Mode/Sts_OOS`.
- `OFF` (`B1`) writes `Cmd_Off`. It has **no enable condition**.
- `RESET` (`B2`) writes `Cmd_Reset`. It has **no enable condition**, so it is clickable outside MAN.
- **Power demand** (`Cmd_Pwr`, REAL, %) is a bidirectional entry. It is visible at level 1 and above only when `Cfg_CtrlType` is greater than 0 (types 1 and 2). It uses the same enable as ON.

A hint line states "Enabled in MAN, available, permitted, not interlocked, not LOCAL". This is true for ON and the power-demand entry only. See Notes.

**Values** (all levels). Control (`Cfg_CtrlType` as text: `On/off`, `Time-proportioned (SSR)`, `SCR phase angle`, else `?`), Power demand (`Val_PwrDemand`, %, only when `Cfg_CtrlType` > 0), Duty (`Val_Duty`, %, only when `Cfg_CtrlType` > 0), Power (`Val_Power`, kW), Current (`Val_Current`, A), Load (`Val_LoadPct`, %), Diagnostics (NE107 text for `Sts_NE107`: 0 `NE107 OK`, 1 `NE107 F`, 2 `NE107 C`, 3 `NE107 S`, 4 `NE107 M`).

**Permissives and interlocks.** Two embedded `Docks/Parts/IntlkList` views get `tagPath + '/Perm'` and `tagPath + '/Intlk'`, with titles "Permissives" and "Interlocks". Their content is described in [Parts/IntlkList.md](Parts/IntlkList.md).

**Alarms** (all levels). Seven rows: high-limit trip, shorted SSR/SCR, element load failure, fail to energise, fail to de-energise, SCR fault, interlock trip. A row is coloured when its alarm is active, using the alarm's `Cfg_Priority`: 1 `Critical`, 2 `High`, 3 `Medium`, 4 `Low`, anything else `Medium`. The class adds `/Unacked` or `/Fill`. An inactive but unacknowledged alarm uses `Alarm/Status/ClearedUnacked`. An inactive, acknowledged alarm uses `Text/Caption Text/Color/Muted`. "No active alarms" is shown when none is active. **ACK** (level 1 and above) calls `efc.ui.ackAll` with the seven alarm names. It writes `Cmd_Ack` only for those whose `Sts_Unack` is true.

**Trend.** Embeds `Docks/Parts/Trend` with pens `Val_Power`, `Val_PwrDemand` and `Val_Current` over the tagPath. The embedded view's `expanded` param starts `false`. It is declared `inout` in `Docks/Parts/Trend`, so the Trend part toggles it itself and the value flows back to this embed. The `position.basis` binding (`{this.props.params.expanded}`) then grows the trend from 15.741 vh to 70.370 vh. The expansion is local to the trend and does not widen the dock region. See [Parts/Trend.md](Parts/Trend.md).

**Maintenance** (level 2 and above). Shows run hours, starts, starts in the last hour, hours since maintenance and whether maintenance is due. `RESET MAINT` writes `Run/Cmd_ResetMaint` (audited). `SIMULATE` toggles `Sim_En` (audited).

**Configuration** (collapsible; collapsed by default; the header click toggles `open_Configuration`). Below level 4 each value is a read-only row. At level 4 and above each value is an editable entry bound bidirectionally to its tag, with an enable expression of the literal `true`; the row is hidden and the entry shown. The entries are: Cycle time (`Cfg_CycleTime`, s, TIME), Min pulse (`Cfg_MinPulse`, s, TIME), Power min (`Cfg_PwrMin`, %), Power max (`Cfg_PwrMax`, %), Power rate (`Cfg_PwrRate`, %/s), Rated power (`Cfg_RatedKW`, kW), Rated current (`Cfg_RatedAmps`, A), Load fail (`Cfg_LoadFailPct`, %), Leak current (`Cfg_LeakAmps`, A) and Feedback time (`Cfg_FbkTime`, s, TIME). The TIME members are milliseconds on the PLC: their rows show `member / 1000`, their entries read the mirror `/ 1000`, and a `props.value` onChange script (only when `origin == 'Browser'`) writes `int(round(value * 1000))` through `efc.ui.cmd(self, member, ..., 4, audit=True)` (Engineer, audited). The other entries write their tags through the binding. Their only guard is the UI enable expression. `Cfg_CtrlType` is displayed in Values but has no configuration row here.

**Role checks.** All role levels come from the Perspective session (`session.props.auth.user.roles`) and are checked in the client. `efc.ui.cmd` returns without writing when the level is too low. Bindings do not check the level, except that the three TIME entries go through `efc.ui.cmd`. Real access control has to be enforced in Perspective security and the PLC logic.

**Audit.** `efc.ui` writes an audit entry (`system.util.audit`, falling back to the logger) for MAINT, OOS, RESET MAINT, SIMULATE and edits of Cycle time, Min pulse and Feedback time. It does not audit AUTO, MAN, ON, OFF, RESET, power-demand changes, the other configuration edits or ACK.

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `""` | T_Heater instance. Every component binding uses `{view.params.tagPath}`. | Set by `efc.ui.openDynamic` from the template's `dwTagPath` (or `tagPath`). Read by bindings and `efc.ui` commands. |
| `tType` | input | `T_Heater` | Declared type. | Not passed by `efc.ui.openDynamic`; not referenced by any binding or script in this view. Always the default. |

Both have `paramDirection: input` and `persistent: true`. No output parameters.

### View-level custom properties (`custom`)

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.level` | `0` | property + script transform | `session.props.auth.user.roles` → `return efc.ui.level(value)` | Role level 0-5 from `session.props.auth.user.roles` via `efc.ui.level`. Gates buttons and sections (Guest 0, Operator 1, Maintenance 2, Supervisor 3, Engineer 4, Admin 5). |
| `view.custom.open_Configuration` | `false` | none (written by scripts) | none | View-local toggle for the Configuration section. Set by the header click script; not bound to any tag; not persisted. |

#### Tag mirrors (`custom.m_*`)

There are 61 tag-mirror properties. Each `custom.m_<member>` (with `/` replaced by `_`) has an indirect, read-only tag binding to `{view.params.tagPath}/<member>` (`bidirectional: false`, fallback delay 2.5 s), and its default is `null`. The display bindings read tag values through these mirrors. The setpoint and configuration entries bind their tags directly (see Bindings reference).

| Group | Members |
|---|---|
| Mode | `Mode/Sts_Man`, `Mode/Sts_OOS`, `Mode/Sts_Maint`, `Mode/Sts_Auto` |
| Status / other | `Sts_Avail`, `Sts_Intlk`, `Sts_Local`, `Sts_NotPerm`, `Sts_HiLimit`, `Sts_Tripped`, `Sts_Fault`, `Sts_Heating`, `Sts_On`, `Sts_Off`, `Sts_Sim`, `Sts_NE107` |
| Values | `Val_PwrDemand`, `Val_Duty`, `Val_Power`, `Val_Current`, `Val_LoadPct` |
| Config | `Cfg_CtrlType`, `Cfg_Tag`, `Cfg_Desc`, `Cfg_CycleTime`, `Cfg_MinPulse`, `Cfg_PwrMin`, `Cfg_PwrMax`, `Cfg_PwrRate`, `Cfg_RatedKW`, `Cfg_RatedAmps`, `Cfg_LoadFailPct`, `Cfg_LeakAmps`, `Cfg_FbkTime` |
| Alarms | `Alm_HiLimit/Sts_Active`, `Alm_HiLimit/Sts_Unack`, `Alm_HiLimit/Cfg_Priority`, `Alm_Shorted/Sts_Active`, `Alm_Shorted/Sts_Unack`, `Alm_Shorted/Cfg_Priority`, `Alm_LoadFail/Sts_Active`, `Alm_LoadFail/Sts_Unack`, `Alm_LoadFail/Cfg_Priority`, `Alm_FailOn/Sts_Active`, `Alm_FailOn/Sts_Unack`, `Alm_FailOn/Cfg_Priority`, `Alm_FailOff/Sts_Active`, `Alm_FailOff/Sts_Unack`, `Alm_FailOff/Cfg_Priority`, `Alm_ScrFault/Sts_Active`, `Alm_ScrFault/Sts_Unack`, `Alm_ScrFault/Cfg_Priority`, `Alm_IntlkTrip/Sts_Active`, `Alm_IntlkTrip/Sts_Unack`, `Alm_IntlkTrip/Cfg_Priority` |
| Runtime | `Run/Val_RunHrs`, `Run/Val_Starts`, `Run/Val_StartsLastHr`, `Run/Val_HrsSinceMaint`, `Run/Sts_MaintDue` |
| Other | `Sim_En` |


### Component-level custom properties

None.

### Session, page and message payloads

- `session.props.auth.user.roles`: read by `custom.level` (transform `efc.ui.level`).
- `session.props.auth.user.userName`: read by `efc.ui._audit` (not bound in this view).
- `session.custom.efcDw[pageId]`: written by `efc.ui.openDynamic` and `closeDynamic` in the template and header; read by `Docks/Region` (not in this file).
- `page.props.pageId`: read by `efc.ui._state` to key `efcDw`.
- No message handlers. No `customMethods`.

## Bindings reference

Total: **182 bindings**: 62 at view root (all `custom.*`, including 1 `property` binding with a transform) and 120 on components. Types: 112 `expr`, 69 `tag`, 1 `property`. `params.tagPath` and `params.tType` have `paramDirection` only. Embedded-view `params.*` values and `position.basis` are component bindings and counted in the 120.

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
| root/Banner | `props.style.classes` | expr | `if({view.custom.m_Sts_HiLimit}, 'State/Fault', if({view.custom.m_Sts_Tripped}, 'State/Fault', if({view.custom.m_Sts_Fault}, 'State/Fault', if({view.custom.m_Sts_Heating}, 'State/Running', if({view.custom.m_Sts_On}, 'State/Running', if({view.custom.m_Sts_Off}, 'State/Stopped', 'State/Unknown'))))))` | CSS class(es) selected by state |
| root/Banner/State | `props.text` | expr | `if({view.custom.m_Sts_HiLimit}, 'HIGH LIMIT', if({view.custom.m_Sts_Tripped}, 'TRIPPED', if({view.custom.m_Sts_Fault}, 'FAULT', if({view.custom.m_Sts_Heating}, 'HEATING', if({view.custom.m_Sts_On}, 'ON', if({view.custom.m_Sts_Off}, 'OFF', 'UNKNOWN'))))))` | Text content |
| root/Banner/Chip0 | `position.display` | expr | `{view.custom.m_Sts_Sim}` | Shown while expression is true |
| root/Banner/Chip1 | `position.display` | expr | `{view.custom.m_Sts_Local}` | Shown while expression is true |
| root/Banner/Chip2 | `position.display` | expr | `{view.custom.m_Sts_Intlk}` | Shown while expression is true |
| root/Banner/Chip3 | `position.display` | expr | `{view.custom.m_Sts_NotPerm}` | Shown while expression is true |

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
| root/Commands/Body/Buttons/B0 | `props.enabled` | expr | `{view.custom.m_Mode_Sts_Man} && {view.custom.m_Sts_Avail} && !{view.custom.m_Sts_Intlk} && !{view.custom.m_Sts_Local} && !{view.custom.m_Sts_NotPerm}` | Enabled while expression is true |
| root/Commands/Body/Buttons/B1 | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Commands/Body/Buttons/B2 | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Commands/Body/Pwr | `position.display` | expr | `{view.custom.level} >= 1 && ({view.custom.m_Cfg_CtrlType} > 0)` | Shown while expression is true |
| root/Commands/Body/Pwr/Entry | `props.value` | tag (indirect) | tag `{0}/Cmd_Pwr` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Commands/Body/Pwr/Entry | `props.enabled` | expr | `{view.custom.m_Mode_Sts_Man} && {view.custom.m_Sts_Avail} && !{view.custom.m_Sts_Intlk} && !{view.custom.m_Sts_Local} && !{view.custom.m_Sts_NotPerm}` | Enabled while expression is true |

### `root/Values`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Values/Body/Type/Val | `props.text` | expr | `case(toInt({view.custom.m_Cfg_CtrlType}), 0, 'On/off', 1, 'Time-proportioned (SSR)', 2, 'SCR phase angle', '?')` | Text content |
| root/Values/Body/Dem | `position.display` | expr | `{view.custom.m_Cfg_CtrlType} > 0` | Shown while expression is true |
| root/Values/Body/Dem/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_PwrDemand}, '#,##0.0')` | Text content |
| root/Values/Body/Dem/EU | `props.text` | expr | `'%'` | Text content |
| root/Values/Body/Duty | `position.display` | expr | `{view.custom.m_Cfg_CtrlType} > 0` | Shown while expression is true |
| root/Values/Body/Duty/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Duty}, '#,##0.0')` | Text content |
| root/Values/Body/Duty/EU | `props.text` | expr | `'%'` | Text content |
| root/Values/Body/Pwr/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Power}, '#,##0.0')` | Text content |
| root/Values/Body/Pwr/EU | `props.text` | expr | `'kW'` | Text content |
| root/Values/Body/Cur/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Current}, '#,##0.0')` | Text content |
| root/Values/Body/Cur/EU | `props.text` | expr | `'A'` | Text content |
| root/Values/Body/Load/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_LoadPct}, '0')` | Text content |
| root/Values/Body/Load/EU | `props.text` | expr | `'%'` | Text content |
| root/Values/Body/NE107/Val | `props.text` | expr | `case(toInt({view.custom.m_Sts_NE107}), 0, 'NE107 OK', 1, 'NE107 F', 2, 'NE107 C', 3, 'NE107 S', 4, 'NE107 M', '')` | Text content |

### `root/Perm`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Perm | `props.params.tagPath` | expr | `{view.params.tagPath} + '/Perm'` | Embedded view tagPath param |

### `root/Intlk`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Intlk | `props.params.tagPath` | expr | `{view.params.tagPath} + '/Intlk'` | Embedded view tagPath param |

### `root/Alarms`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Alarms/Body/None | `position.display` | expr | `!({view.custom.m_Alm_HiLimit_Sts_Active} \|\| {view.custom.m_Alm_Shorted_Sts_Active} \|\| {view.custom.m_Alm_LoadFail_Sts_Active} \|\| {view.custom.m_Alm_FailOn_Sts_Active} \|\| {view.custom.m_Alm_FailOff_Sts_Active} \|\| {view.custom.m_Alm_ScrFault_Sts_Active} \|\| {view.custom.m_Alm_IntlkTrip_Sts_Active})` | Shown while expression is true |
| root/Alarms/Body/List/A0 | `props.style.classes` | expr | `if({view.custom.m_Alm_HiLimit_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_HiLimit_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_HiLimit_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_HiLimit_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A1 | `props.style.classes` | expr | `if({view.custom.m_Alm_Shorted_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_Shorted_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_Shorted_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_Shorted_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A2 | `props.style.classes` | expr | `if({view.custom.m_Alm_LoadFail_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_LoadFail_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_LoadFail_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_LoadFail_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A3 | `props.style.classes` | expr | `if({view.custom.m_Alm_FailOn_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_FailOn_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_FailOn_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_FailOn_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A4 | `props.style.classes` | expr | `if({view.custom.m_Alm_FailOff_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_FailOff_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_FailOff_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_FailOff_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A5 | `props.style.classes` | expr | `if({view.custom.m_Alm_ScrFault_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_ScrFault_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_ScrFault_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_ScrFault_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A6 | `props.style.classes` | expr | `if({view.custom.m_Alm_IntlkTrip_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_IntlkTrip_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_IntlkTrip_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_IntlkTrip_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
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
| root/Maintenance/Body/Hrs/Val | `props.text` | expr | `numberFormat({view.custom.m_Run_Val_RunHrs}, '#,##0')` | Text content |
| root/Maintenance/Body/Starts/Val | `props.text` | expr | `numberFormat({view.custom.m_Run_Val_Starts}, '#,##0')` | Text content |
| root/Maintenance/Body/StartsHr/Val | `props.text` | expr | `numberFormat({view.custom.m_Run_Val_StartsLastHr}, '#,##0')` | Text content |
| root/Maintenance/Body/SinceMaint/Val | `props.text` | expr | `numberFormat({view.custom.m_Run_Val_HrsSinceMaint}, '#,##0')` | Text content |
| root/Maintenance/Body/Due/Val | `props.text` | expr | `if({view.custom.m_Run_Sts_MaintDue}, 'YES', 'no')` | Text content |

### `root/Configuration`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration/Header/Chevron | `props.text` | expr | `if({view.custom.open_Configuration}, '▾', '▸')` | Text content |
| root/Configuration/Body | `position.display` | expr | `{view.custom.open_Configuration}` | Shown while expression is true |
| root/Configuration/Body/R0 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R0/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_CycleTime} / 1000, '#,##0.###')` | Text content |
| root/Configuration/Body/R0/EU | `props.text` | expr | `'s'` | Text content |
| root/Configuration/Body/E0 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E0/Entry | `props.value` | expr | `{view.custom.m_Cfg_CycleTime} / 1000` | Value in seconds (the PLC TIME is in milliseconds) |
| root/Configuration/Body/E0/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: efc.ui.cmd(self, 'Cfg_CycleTime', int(round(currentValue.value * 1000)), 4, audit=True)` | Edit written as milliseconds, Engineer, audited |
| root/Configuration/Body/E0/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R1 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R1/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_MinPulse} / 1000, '#,##0.###')` | Text content |
| root/Configuration/Body/R1/EU | `props.text` | expr | `'s'` | Text content |
| root/Configuration/Body/E1 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E1/Entry | `props.value` | expr | `{view.custom.m_Cfg_MinPulse} / 1000` | Value in seconds (the PLC TIME is in milliseconds) |
| root/Configuration/Body/E1/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: efc.ui.cmd(self, 'Cfg_MinPulse', int(round(currentValue.value * 1000)), 4, audit=True)` | Edit written as milliseconds, Engineer, audited |
| root/Configuration/Body/E1/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R2 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R2/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_PwrMin}, '#,##0.###')` | Text content |
| root/Configuration/Body/R2/EU | `props.text` | expr | `'%'` | Text content |
| root/Configuration/Body/E2 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E2/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_PwrMin` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E2/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R3 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R3/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_PwrMax}, '#,##0.###')` | Text content |
| root/Configuration/Body/R3/EU | `props.text` | expr | `'%'` | Text content |
| root/Configuration/Body/E3 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E3/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_PwrMax` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E3/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R4 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R4/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_PwrRate}, '#,##0.###')` | Text content |
| root/Configuration/Body/R4/EU | `props.text` | expr | `'%/s'` | Text content |
| root/Configuration/Body/E4 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E4/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_PwrRate` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E4/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R5 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R5/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_RatedKW}, '#,##0.###')` | Text content |
| root/Configuration/Body/R5/EU | `props.text` | expr | `'kW'` | Text content |
| root/Configuration/Body/E5 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E5/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_RatedKW` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E5/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R6 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R6/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_RatedAmps}, '#,##0.###')` | Text content |
| root/Configuration/Body/R6/EU | `props.text` | expr | `'A'` | Text content |
| root/Configuration/Body/E6 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E6/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_RatedAmps` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E6/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R7 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R7/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_LoadFailPct}, '#,##0.###')` | Text content |
| root/Configuration/Body/R7/EU | `props.text` | expr | `'%'` | Text content |
| root/Configuration/Body/E7 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E7/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_LoadFailPct` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E7/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R8 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R8/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_LeakAmps}, '#,##0.###')` | Text content |
| root/Configuration/Body/R8/EU | `props.text` | expr | `'A'` | Text content |
| root/Configuration/Body/E8 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E8/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_LeakAmps` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E8/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R9 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R9/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_FbkTime} / 1000, '#,##0.###')` | Text content |
| root/Configuration/Body/R9/EU | `props.text` | expr | `'s'` | Text content |
| root/Configuration/Body/E9 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E9/Entry | `props.value` | expr | `{view.custom.m_Cfg_FbkTime} / 1000` | Value in seconds (the PLC TIME is in milliseconds) |
| root/Configuration/Body/E9/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: efc.ui.cmd(self, 'Cfg_FbkTime', int(round(currentValue.value * 1000)), 4, audit=True)` | Edit written as milliseconds, Engineer, audited |
| root/Configuration/Body/E9/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |


## Scripts reference

Total: **16 scripts**: 12 event scripts (11 `component.onActionPerformed`, 1 `dom.onClick`) and 1 transform script (`custom.level`). 3 property-change `onChange` scripts (`props.value` of the TIME entries, see the end of the list). No `customMethods`, no `messageHandlers`.

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
	efc.ui.cmd(self, 'Cmd_On', True, 1)
```

7. **`root/Commands/Body/Buttons/B1`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_Off', True, 1)
```

8. **`root/Commands/Body/Buttons/B2`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_Reset', True, 1)
```

9. **`root/Alarms/Body/Ack`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.ackAll(self, ['Alm_HiLimit', 'Alm_Shorted', 'Alm_LoadFail', 'Alm_FailOn', 'Alm_FailOff', 'Alm_ScrFault', 'Alm_IntlkTrip'])
```

10. **`root/Maintenance/Body/Buttons/ResetMaint`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Run/Cmd_ResetMaint', True, 2, audit=True)
```

11. **`root/Maintenance/Body/Buttons/Sim`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Sim_En', not self.view.custom.m_Sim_En, 2, audit=True)
```

12. **`root/Configuration/Header`**: `events.dom.onClick`, scope G.

```python
	self.view.custom.open_Configuration = not self.view.custom.open_Configuration
```

13. **transform on `(view root)` `custom.level`**: `custom.level` binding, `property` source `session.props.auth.user.roles`.

```python
	return efc.ui.level(value)
```


14. **`root/Configuration/Body/E0/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		efc.ui.cmd(self, 'Cfg_CycleTime', int(round(currentValue.value * 1000)), 4, audit=True)
```

15. **`root/Configuration/Body/E1/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		efc.ui.cmd(self, 'Cfg_MinPulse', int(round(currentValue.value * 1000)), 4, audit=True)
```

16. **`root/Configuration/Body/E9/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		efc.ui.cmd(self, 'Cfg_FbkTime', int(round(currentValue.value * 1000)), 4, audit=True)
```

### Explanation of each handler

| Handler | Action | Writes | Role check | Audit |
|---|---|---|---|---|
| `Header/Close` | `efc.ui.closeDynamic` restores default region view | none | none | no |
| `Mode/Auto` | `efc.ui.cmd(... 'Mode/Cmd_Auto', True, 1)` | `Mode/Cmd_Auto` | level 1 | no |
| `Mode/Man` | `efc.ui.cmd(... 'Mode/Cmd_Man', True, 1)` | `Mode/Cmd_Man` | level 1 | no |
| `Mode/Maint` | `efc.ui.cmd(... 'Mode/Cmd_Maint', True, 2)` | `Mode/Cmd_Maint` | level 2 | yes |
| `Mode/OOS` | `efc.ui.cmd(... 'Mode/Cmd_OOS', True, 2)` | `Mode/Cmd_OOS` | level 2 | yes |
| `Commands/B0` (ON) | `efc.ui.cmd(... 'Cmd_On', True, 1)` | `Cmd_On` | level 1 | no |
| `Commands/B1` (OFF) | `efc.ui.cmd(... 'Cmd_Off', True, 1)` | `Cmd_Off` | level 1 | no |
| `Commands/B2` (RESET) | `efc.ui.cmd(... 'Cmd_Reset', True, 1)` | `Cmd_Reset` | level 1 | no |
| `Alarms/Ack` | `efc.ui.ackAll` on the seven alarms | `Alm_*/Cmd_Ack` where unacked | level 1 | no |
| `Maintenance/ResetMaint` | `efc.ui.cmd(... 'Run/Cmd_ResetMaint', True, 2)` | `Run/Cmd_ResetMaint` | level 2 | yes |
| `Maintenance/Sim` | `efc.ui.cmd(... 'Sim_En', not m_Sim_En, 2)` | `Sim_En` (toggle) | level 2 | yes |
| `Configuration/Header` (dom click) | toggles `open_Configuration` | none | none | no |
| `Configuration/Body/E0` (`Cfg_CycleTime` entry, onChange) | `efc.ui.cmd(... 'Cfg_CycleTime', int(round(value * 1000)), 4)`, only when `origin == 'Browser'` | `Cfg_CycleTime` (milliseconds) | level 4 | yes
| `Configuration/Body/E1` (`Cfg_MinPulse` entry, onChange) | `efc.ui.cmd(... 'Cfg_MinPulse', int(round(value * 1000)), 4)`, only when `origin == 'Browser'` | `Cfg_MinPulse` (milliseconds) | level 4 | yes
| `Configuration/Body/E9` (`Cfg_FbkTime` entry, onChange) | `efc.ui.cmd(... 'Cfg_FbkTime', int(round(value * 1000)), 4)`, only when `origin == 'Browser'` | `Cfg_FbkTime` (milliseconds) | level 4 | yes

`efc.ui.cmd` writes `view.params.tagPath + '/' + member` with `system.tag.writeBlocking` only when `userLevel >= minLevel`. The Mode, Commands, Ack and Maintenance buttons therefore use the level check. The three TIME entries (Cycle time, Min pulse, Feedback time) use the level check (level 4). The power-demand entry and the other Configuration entries are bound directly and do not use `efc.ui.cmd`.

### Library functions used (`projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.level(roles)`**: highest index of the role in `['Guest','Operator','Maintenance','Supervisor','Engineer','Admin']`, or 0. Bound to `custom.level`.
- **`efc.ui.closeDynamic(component)`**: writes `efcDw[pageId]` back to the stored `default` path and params. Writes no tags.
- **`efc.ui.cmd(component, member, value, minLevel, audit)`**: the role-checked write described above. Audits when `audit=True`.
- **`efc.ui.ackAll(component, alarms)`**: reads `<alarm>/Sts_Unack` for the listed alarms, then writes `<alarm>/Cmd_Ack` = True for those that are true, only at level 1 and above.
- **`efc.ui.bypass` / `unbypass`**: not called from this view. They are called from the embedded `IntlkList` views and the `BypassConfirm` popup.

## Tag members used

All paths are relative to `tagPath`. Types come from `types/PCLib_Members.csv` (nested types: `Mode` = T_Mode, `Alm_*` = T_Alarm, `Run` = T_RunTime, `Perm` and `Intlk` = T_Intlk). Access is taken from the bindings and handler scripts in this view.

| Member | Access | Data type | Meaning |
|---|---|---|---|
| `Mode/Sts_Man` | read | BOOL | In Manual (commanded by operator) - MTP Operator |
| `Sts_Avail` | read | BOOL | Available to Auto/program control |
| `Sts_Intlk` | read | BOOL | Interlock not healthy |
| `Sts_Local` | read | BOOL | In local control |
| `Sts_NotPerm` | read | BOOL | Permissive not healthy |
| `Cfg_CtrlType` | read | INT | 0 = on/off (contactor), 1 = time-proportioned SSR on a PLC output, 2 = SCR power controller (analog reference) |
| `Cfg_Tag` | read | STRING[20] | Equipment / instrument tag, e.g. FT-101 |
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Sts_HiLimit` | read | BOOL | Excess-temperature limit tripped (reset at the limit device) |
| `Sts_Tripped` | read | BOOL | Tripped - reset required |
| `Sts_Fault` | read | BOOL | Any fault present |
| `Sts_Heating` | read | BOOL | Output conducting now (on/off: on; SSR: inside the ON part of the cycle; SCR: reference > 0) |
| `Sts_On` | read | BOOL | On: contactor closed and enabled to heat |
| `Sts_Off` | read | BOOL | Off |
| `Sts_Sim` | read | BOOL | Simulation active |
| `Mode/Sts_OOS` | read | BOOL | Out of service - MTP Offline |
| `Mode/Sts_Maint` | read | BOOL | In Maintenance |
| `Mode/Sts_Auto` | read | BOOL | In Automatic (commanded by owner) - MTP Automatic |
| `Val_PwrDemand` | read | REAL | Power demand after limits and ramp (%) |
| `Val_Duty` | read | REAL | Applied duty / power (%): on/off 0 or 100, SSR ON-time fraction, SCR reference |
| `Val_Power` | read | REAL | Estimated power (kW) = Val_Duty x Cfg_RatedKW, or from current |
| `Val_Current` | read | REAL | Heater current (A) |
| `Val_LoadPct` | read | REAL | Measured current as % of expected at the present duty |
| `Sts_NE107` | read | INT | NAMUR NE107 status: 0=Good 1=Failure (F) 2=Function check (C) 3=Out of specification (S) 4=Maintenance required (M) |
| `Alm_HiLimit/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_HiLimit/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_HiLimit/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_Shorted/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_Shorted/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_Shorted/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_LoadFail/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_LoadFail/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_LoadFail/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_FailOn/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_FailOn/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_FailOn/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_FailOff/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_FailOff/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_FailOff/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_ScrFault/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_ScrFault/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_ScrFault/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_IntlkTrip/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_IntlkTrip/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_IntlkTrip/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Run/Val_RunHrs` | read | REAL | Total run hours (display) |
| `Run/Val_Starts` | read | UDINT | Total starts / cycles |
| `Run/Val_StartsLastHr` | read | INT | Starts in the last 60 min (rolling) |
| `Run/Val_HrsSinceMaint` | read | REAL | Run hours since last maintenance reset |
| `Run/Sts_MaintDue` | read | BOOL | Maintenance due |
| `Cmd_Pwr` | read/write (bidirectional) | REAL | Operator power demand (%), Manual mode, types 1 and 2 |
| `Cfg_CycleTime` | read (shown as value / 1000); write value * 1000 via `efc.ui.cmd` | TIME | Time-proportioning cycle (type 1): output is ON for Val_Duty % of each cycle |
| `Cfg_MinPulse` | read (shown as value / 1000); write value * 1000 via `efc.ui.cmd` | TIME | Shortest ON or OFF pulse (type 1); shorter pulses are skipped |
| `Cfg_PwrMin` | read/write (bidirectional) | REAL | Minimum power demand when on (%) |
| `Cfg_PwrMax` | read/write (bidirectional) | REAL | Maximum power demand (%) |
| `Cfg_PwrRate` | read/write (bidirectional) | REAL | Power ramp limit (%/s), 0 = none (soft start for cold elements) |
| `Cfg_RatedKW` | read/write (bidirectional) | REAL | Heater rated power at 100 % (kW) |
| `Cfg_RatedAmps` | read/write (bidirectional) | REAL | Heater current at 100 % (A); 0 = no current monitoring |
| `Cfg_LoadFailPct` | read/write (bidirectional) | REAL | Partial load failure: current below this % of expected while heating |
| `Cfg_LeakAmps` | read/write (bidirectional) | REAL | Current above this while the output is off = SSR / SCR shorted (A) |
| `Cfg_FbkTime` | read (shown as value / 1000); write value * 1000 via `efc.ui.cmd` | TIME | Time allowed for contactor feedback and current to settle |
| `Perm` | read (passed as tagPath) | T_Intlk | Permissive group: named conditions, first-out, bypass; Out_OK ANDed with Inp_PermOK |
| `Intlk` | read (passed as tagPath) | T_Intlk | Interlock group: named conditions, first-out, latch, bypass; Out_OK ANDed with Inp_IntlkOK |
| `Mode/Cmd_Auto` | write (one-shot) | BOOL | Operator request Automatic (one-shot) |
| `Mode/Cmd_Man` | write (one-shot) | BOOL | Operator request Manual (one-shot) |
| `Mode/Cmd_Maint` | write (one-shot) | BOOL | Request Maintenance (one-shot) |
| `Mode/Cmd_OOS` | write (one-shot) | BOOL | Request Out-of-Service (one-shot) |
| `Cmd_On` | write (one-shot) | BOOL | Operator on (one-shot) |
| `Cmd_Off` | write (one-shot) | BOOL | Operator off (one-shot) |
| `Cmd_Reset` | write (one-shot) | BOOL | Fault / trip reset (one-shot) |
| `Alm_HiLimit/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_Shorted/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_LoadFail/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_FailOn/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_FailOff/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_ScrFault/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_IntlkTrip/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Run/Cmd_ResetMaint` | write (one-shot) | BOOL | Reset hours-since-maintenance (one-shot) |
| `Sim_En` | read / write (toggle) | BOOL | Simulation: ignore field I/O, logic generates feedback |


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
        - `B1` (ia.input.button)
        - `B2` (ia.input.button)
      - `Pwr` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `Hint` (ia.display.label)
  - `Values` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
    - `Body` (ia.container.flex)
      - `Type` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
      - `Dem` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Duty` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Pwr` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Cur` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Load` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `NE107` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
  - `Perm` (ia.display.view)
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
        - `A3` (ia.display.label)
        - `A4` (ia.display.label)
        - `A5` (ia.display.label)
        - `A6` (ia.display.label)
      - `Ack` (ia.input.button)
  - `Trend` (ia.display.view)
  - `Maintenance` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
    - `Body` (ia.container.flex)
      - `Hrs` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
      - `Starts` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
      - `StartsHr` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
      - `SinceMaint` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
      - `Due` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
      - `Buttons` (ia.container.flex)
        - `ResetMaint` (ia.input.button)
        - `Sim` (ia.input.button)
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
      - `R7` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `E7` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `R8` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `E8` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `R9` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `E9` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
```

## Notes and open questions

- **RESET does not say that a high limit resets at the device.** `Sts_HiLimit` is defined in PCLib as "excess-temperature limit tripped (reset at the limit device)". The banner shows HIGH LIMIT, and RESET (`Cmd_Reset`, level 1 and above, no enable) is always clickable. The view gives no indication that the limit device must be reset first. Whether the PLC's `Cmd_Reset` clears `Sts_HiLimit` is not in this file. Open question.
- **The hardwired limit's health is not displayed.** `Inp_HiLimitOK` ("independent excess-temperature limit healthy, hardwired, latching") is not bound. The dock shows the limit only after it has tripped (`Sts_HiLimit`).
- **Current and Load rows are always shown.** PCLib defines `Cfg_RatedAmps` = 0 as "no current monitoring". The Current row, the Load row and the element-load and shorted alarms are still shown for such a heater, with values that cannot be measured. Consider hiding them when `Cfg_RatedAmps` is 0. Open question.
- **The hint line is not accurate.** It says the commands are "Enabled in MAN, available, permitted, not interlocked, not LOCAL". That is true for ON and the power-demand entry only. OFF and RESET have no enable.
- **ON does not check the heater state.** ON is enabled while the heater is on, tripped, faulted or at high limit, so it can write `Cmd_On` in those states. OFF and RESET are clickable at all times at level 1 and above.
- **Control-type rows.** The power-demand entry, Power demand row and Duty row are shown only when `Cfg_CtrlType` > 0. For an on/off heater (type 0) the dock shows ON, OFF and RESET only. The entry's writes are hidden, not blocked, for type 0.
- **Trend pens share one scale and have no legend.** `efc.ui.trend` scales every pen to one minimum and maximum. Power (kW), power demand (%) and current (A) therefore share one axis. The part draws the pens in fixed colours by position (dark, blue, grey) and the view does not label them. See [Parts/Trend.md](Parts/Trend.md).
- **Unused PCLib members.** `Sts_State`, `Sts_Shorted`, `Sts_LoadFail`, `Sts_Ready`, `Inp_ContactorFbk`, `Inp_Current` and `Val_Energy` are not read by this view. The banner computes its own state from the feedback flags. Shorted and element load failure appear only through their alarms.
- **Simulate toggle depends on the mirror.** `SIMULATE` writes `not self.view.custom.m_Sim_En`. If the mirror has not yet been read (`None`), `not None` is TRUE, so the first click writes TRUE.
- **Configuration writes are not role-checked in script.** Their only guard is the UI enable expression. This is a binding-level write, not an `efc.ui` call. Real access control has to be in Perspective security and the PLC.
- **Mode buttons have no enable binding.** MAN and AUTO can be clicked at level 1 and above in any state. MAINT and OOS can be clicked at level 2 and above in any state. The same applies in `Docks/ValveDiscrete`.
- **Outside this view, the template bypasses the rules.** The `PB` button on `Templates/HeatTransfer/Heater_Electric` writes `Cmd_On` or `Cmd_Off` directly with `system.tag.writeBlocking`. It has no `efc.ui.cmd` role check and no enable check. Operators using the template symbol can switch the heater on without the level or enable rules in this dock.
- **Parameter and style class names** (`Alarm/Critical/Unacked` and similar, `Button/Toggle/On`, `Button/Momentary`, etc.) are style classes defined elsewhere. Their appearance was not checked.
- **Level thresholds** come from the constants in `efc.ui` (`OPERATOR=1`, `MAINT=2`, `SUPERVISOR=3`, `ENGINEER=4`). The dock uses 4 for Configuration editing, which matches `ENGINEER`.
