# Templates/Dynamic Window/Loops/Loop

Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/Dynamic Window/Loops/Loop/view.json`
Opened from: the PID loop templates `Templates/Loops/Loop_B1_Bar`, `Loop_B2_Horizontal`, `Loop_B3_Sparkline` and `Loop_B4_Column` (see [PID loop templates](../../Loops/Loop_Family.md)) through `efc.ui.openDynamic`. Dynamic window id `dw_Loop`. `efc.ui.BY_TYPE` maps `T_PID` to `dw_Loop`.

## Overview

The operator, tuning and configuration dynamic window for a PID loop (T_PID). It opens in the page's right dock (`dw_Right`), not as a popup. It shows the mode, PV, SP, output and error, the setpoint and output entries, interlocks, alarms, a trend, tuning values and alarm and range configuration.

- **Default size:** 400 x 860 (`props.defaultSize`). The root is a scrolling column (`Container/Scroll`).
- **Parameters:** `tagPath` (the T_PID instance) and `tType` (default `T_PID`).
- **How it is opened:** the template's click runs `efc.ui.openDynamic(self)`. That function loads `Templates/Dynamic Window/Loops/Loop` into the page's `dw_Right` dock with params `{tagPath: ...}` (`system.perspective.alterDock`) and opens the dock (`system.perspective.openDock`). Before that it runs `efc.ui.sizeDock(self)`, which sets the dock size to 37.04 vh (400 px at 1080p, 800 px at 4K, decision 33). `efc.ui.openDynamic` passes only `tagPath` (and `model` if present). **`tType` is never passed**, so the dock always runs with its default `T_PID`. No binding in this view reads `view.params.tType`.
- **Generated view:** this view is written by `generator/docks/build_docks.py` (function `loop()`, listed in `VIEWS`). Change the generator, not `view.json`, or the next build overwrites the edit.
- **How it closes:** the header `X` runs `efc.ui.closeDynamic(self)`, which puts the page's default view back in the `dw_Right` dock (set by `efc.ui.setDefaultDock` in the screen's onStartup), or closes the dock if the page has no default. That startup script is not in this view.

## How it operates

**Header.** Shows `Cfg_Tag` (large) and `Cfg_Desc`. The `X` button closes the window (see Overview).

**Banner.** The state label is the first true flag in this order: `Sts_Intlk` (INTERLOCKED, `State/Fault`), `Sts_Track` (TRACKING, `State/Transition`), `Sts_Cas` (CASCADE, `State/Running`), `Sts_Auto` (AUTO, `State/Running`), `Sts_Man` (MANUAL, `State/Stopped`). If none is true, the label is UNKNOWN (`State/Unknown`). Three chips appear when their flag is true: WINDUP HI (`Sts_WindupHi`), WINDUP LO (`Sts_WindupLo`) and RAMPING (`Sts_SPRamping`). Unlike the valve docks, the banner has no SIM, LOCAL or INTLK chips.

**Mode** (all levels). The MAN, AUTO and CAS toggle buttons are highlighted (`Button/Toggle/On`) when `Sts_Man`, `Sts_Auto` or `Sts_Cas` is true. Each runs `efc.ui.cmd(self, 'Cmd_<mode>', True, 1)`, a one-shot write with no audit. None of the three buttons has an `enabled` binding, so each is clickable in any state, including INTERLOCKED and TRACKING. Below level 1 each shows a lock icon and the tooltip "Requires Operator access"; a press is refused by `efc.ui.cmd`, which logs a warning and opens the AccessDenied popup (see [AccessDenied](../Parts/AccessDenied.md)). The PLC decides whether the request is honoured.

**Values** (all levels). PV (`Val_PV`), SP (`Val_SP`), Output (`Out_CV`, unit `%`) and Error (`Val_Err`) are shown with `#,##0.0`. The EU text for PV, SP and Error comes from `Cfg_PVEU`.

- **Setpoint entry** (level 1 and above): a numeric entry that reads `Cmd_SP` one way. It is enabled only when `Sts_Cas` is false. An edit (only when `origin == 'Browser'`) commits through `efc.ui.setValue(self, 'Cmd_SP', value, 1)`, which re-checks level 1, writes and audits old -> new; a refused or failed write refreshes the binding.
- **Output entry** (level 1 and above): a numeric entry that reads `Cmd_CV` one way. It is enabled only when `Sts_Man` is true. Same write path as the setpoint entry (`efc.ui.setValue`, level 1).

**Interlocks** (all levels). An embedded `Templates/Dynamic Window/Parts/IntlkList` (see [Parts/IntlkList](../Parts/IntlkList.md)) gets `tagPath + '/Intlk'` and the title "Interlocks". Its content is not in this file.

**Alarms** (all levels). Three rows: Deviation high (`Alm_DevH`), Deviation low (`Alm_DevL`) and PV bad (`Alm_PVBad`). An active row takes `Alarm/<priority>/Unacked` or `Alarm/<priority>/Fill`. The priority comes from `Cfg_Priority`: 1 `Critical`, 2 `High`, 3 `Medium`, 4 `Low`, anything else `Medium`. An inactive, unacknowledged row uses `Alarm/Status/ClearedUnacked`. An inactive, acknowledged row uses `Text/Caption Text/Color/Muted`. "No active alarms" shows when none is active. **ACK** (always visible; lock icon below level 1) calls `efc.ui.ackAll`, which writes `Cmd_Ack` only for the alarms whose `Sts_Unack` is true. Below Operator `efc.ui.ackAll` writes nothing, logs a warning and opens the AccessDenied popup.

**Trend.** Embeds `Templates/Dynamic Window/Parts/Trend` (see [Parts/Trend](../Parts/Trend.md)) with the static pens `["Val_PV", "Val_SP", "Out_CV"]` and `expanded` = `false`. The Trend part declares `expanded` as `inout` and toggles it itself, and the value flows back to this embed. The `position.basis` binding (`{this.props.params.expanded}`) then grows the trend from 15.741 vh to 70.370 vh. The expansion is local to the trend and does not widen the dock. The trend reads tag history through `efc.ui.trend` (`queryTagHistory`), with a range selector inside the Trend part (5 min, 30 min, 1 h, 8 h, 24 h; default 30 min).

**Tuning** (level 1 and above; hidden below Operator; collapsible). The header click toggles `open_Tuning`. Rows: Gain (Kp), Integral (Ti, s), Derivative (Td, s), Deadband, SP rate (/s), CV rate (%/s) and a "Direct acting" checkbox (`Cfg_DirectAct`). Below level 4 each row shows its value read-only (Direct acting shows `Yes` or `No`). At level 4 and above the value rows are replaced by numeric entries that read `Cfg_Kp`, `Cfg_DB`, `Cfg_SPRate`, `Cfg_CVRate` one way, and by entries for `Cfg_Ti` and `Cfg_Td` (PCLib TIME, milliseconds on the PLC) that show `member / 1000` seconds, and the checkbox is shown (level 4 and above; hidden below). Every entry and the checkbox commit an edit from a `props.value` (checkbox: `props.selected`) onChange script (only when `origin == 'Browser'`) through `efc.ui.setValue(self, member, value, 4)`; the Ti and Td entries pass scale 1000, so `int(round(value * 1000))` is written. A refused or failed write refreshes the binding. The entries have `enabled` = `true`.

**Configuration** (level 1 and above; hidden below Operator; collapsible). The header click toggles `open_Configuration`. Rows: Dev high limit (`Alm_DevH/Cfg_Lim`), Dev low limit (`Alm_DevL/Cfg_Lim`), SP min, SP max, CV min (%), CV max (%), PV min and PV max. Editing works as for Tuning: read-only below level 4, entries committed through `efc.ui.setValue` (level 4, audited) at level 4 and above, `enabled` = `true`.

**Role checks.** `view.custom.level` comes from the Perspective session (`session.props.auth.securityLevels`) and is mapped by `efc.ui.level` (case-insensitive, site names through `efc.ui.ROLE_ALIASES`). The Mode buttons and ACK call a role-checked script function (`efc.ui.cmd` and `efc.ui.ackAll`, both minimum level 1). Their buttons stay visible with a lock below Operator; a press below it is refused, logged and answered with the `Parts/AccessDenied` popup (decision 36; see [AccessDenied](../Parts/AccessDenied.md)). The setpoint and output entries (level 1) and the Tuning and Configuration entries and checkbox (level 4) are re-checked by `efc.ui.setValue`, which refuses below the level with the same popup. Real access control has to be enforced in Perspective security and the PLC logic.

**Audit.** Every button call in this view omits the audit flag. Every entry and checkbox edit (setpoint, output, Tuning, Configuration) is audited by `efc.ui.setValue` as `EFC set`, old -> new.

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `""` | T_PID instance. Every component binding uses `{view.params.tagPath}`. | Set by `efc.ui.openDynamic` from the template's `dwTagPath` (or `tagPath`). Read by bindings and `efc.ui` commands. |
| `tType` | input | `T_PID` | Declared type. | Not passed by `efc.ui.openDynamic`; not referenced by any binding or script in this view. Always the default. |

Both have `paramDirection: input` and `persistent: true`. No output parameters.

### View-level custom properties (`custom`)

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.level` | `0` | property + script transform | `session.props.auth.securityLevels` → `return efc.ui.level(value)` | Role level 0-5 from `session.props.auth.securityLevels` via `efc.ui.level`. Gates the Mode, ACK, the Tuning and Configuration sections (hidden below 1) and their read/write rows (Guest 0, Operator 1, Maintenance 2, Supervisor 3, Engineer 4, Admin 5). |
| `view.custom.open_Tuning` | `false` | none (written by script) | none | View-local toggle for the Tuning section. Set by the Tuning header click script; not bound to any tag; not persisted. |
| `view.custom.open_Configuration` | `false` | none (written by script) | none | View-local toggle for the Configuration section. Set by the Configuration header click script; not bound to any tag; not persisted. |

#### Tag mirrors (`custom.m_*`)

There are 39 tag-mirror properties. Each `custom.m_<member>` (with `/` replaced by `_`) has an indirect, read-only tag binding to `{view.params.tagPath}/<member>` (`bidirectional: false`, fallback delay 2.5 s), and its default is `null`. The rest of the view reads tag values only through these mirrors.

| Group | Members |
|---|---|
| Mode and status | `Sts_Man`, `Sts_Auto`, `Sts_Cas`, `Sts_Track`, `Sts_Intlk`, `Sts_WindupHi`, `Sts_WindupLo`, `Sts_SPRamping` |
| Values | `Val_PV`, `Val_SP`, `Out_CV`, `Val_Err` |
| Config | `Cfg_PVEU`, `Cfg_Tag`, `Cfg_Desc`, `Cfg_Kp`, `Cfg_Ti`, `Cfg_Td`, `Cfg_DB`, `Cfg_SPRate`, `Cfg_CVRate`, `Cfg_SPMin`, `Cfg_SPMax`, `Cfg_CVMin`, `Cfg_CVMax`, `Cfg_PVMin`, `Cfg_PVMax`, `Cfg_DirectAct` |
| Alarms (per alarm: Sts_Active, Sts_Unack, Cfg_Priority; limits) | `Alm_DevH/Sts_Active`, `Alm_DevH/Sts_Unack`, `Alm_DevH/Cfg_Priority`, `Alm_DevH/Cfg_Lim`, `Alm_DevL/Sts_Active`, `Alm_DevL/Sts_Unack`, `Alm_DevL/Cfg_Priority`, `Alm_DevL/Cfg_Lim`, `Alm_PVBad/Sts_Active`, `Alm_PVBad/Sts_Unack`, `Alm_PVBad/Cfg_Priority` |

### Component-level custom properties

None.

### Session, page and message payloads

- `session.props.auth.securityLevels`: read by `custom.level` (transform `efc.ui.level`).
- `session.props.auth.user.userName`: not bound in this view. `efc.ui._audit` reads it; the entry and checkbox onChange scripts reach it through `efc.ui.setValue`.
- `session.custom.efcDw['<pageId>|<page path>']`: holds only the page's default dock view (`{'default': {'path', 'params'}}`), written by `efc.ui.setDefaultDock` in the screen's onStartup (not in this file) and read by `efc.ui.closeDynamic` in the header. `openDynamic` writes no session value; it calls `system.perspective.alterDock` and `openDock` on `dw_Right`.
- `page.props.pageId` and `page.props.path`: read by `efc.ui._state` to key `efcDw` (the pageId survives `navigate()`, so the path keeps one screen's default from leaking into the next).
- `page.props.dimensions`: `efc.ui.sizeDock` (run by `openDynamic`, `closeDynamic` and `setDefaultDock`) reads `viewport.height`, turns `dimensions.enabled` on if needed, and sets the `dw_Right` dock size to 400 x height / 1080 px (37.04 vh, decision 33). Needs Ignition 8.1.7+ for page dimensions and 8.1.19+ for `alterDock`. Reached through the header close.
- No message handlers. No `customMethods`.

## Bindings reference

Total: **174 bindings**: 40 at view root (all `custom.*`, including 1 `property` binding with a transform) and 134 on components. Types: 119 `expr`, 54 `tag`, 1 `property`. `params.tagPath` and `params.tType` have `paramDirection` only. Embedded-view `params.*` values and `position.basis` are component bindings and are counted in the 134.

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
| root/Banner | `props.style.classes` | expr | `if({view.custom.m_Sts_Intlk}, 'State/Fault', if({view.custom.m_Sts_Track}, 'State/Transition', if({view.custom.m_Sts_Cas}, 'State/Running', if({view.custom.m_Sts_Auto}, 'State/Running', if({view.custom.m_Sts_Man}, 'State/Stopped', 'State/Unknown')))))` | CSS class(es) selected by state |
| root/Banner/State | `props.text` | expr | `if({view.custom.m_Sts_Intlk}, 'INTERLOCKED', if({view.custom.m_Sts_Track}, 'TRACKING', if({view.custom.m_Sts_Cas}, 'CASCADE', if({view.custom.m_Sts_Auto}, 'AUTO', if({view.custom.m_Sts_Man}, 'MANUAL', 'UNKNOWN')))))` | Text content |
| root/Banner/Chip0 | `position.display` | expr | `{view.custom.m_Sts_WindupHi}` | Shown while expression is true |
| root/Banner/Chip1 | `position.display` | expr | `{view.custom.m_Sts_WindupLo}` | Shown while expression is true |
| root/Banner/Chip2 | `position.display` | expr | `{view.custom.m_Sts_SPRamping}` | Shown while expression is true |

### `root/Mode`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Mode/Body/Buttons/Man | `props.image.icon.path` | expr | `if({view.custom.level} < 1, 'material/lock', '')` | Shows a lock icon on the button while the user is below Operator |
| root/Mode/Body/Buttons/Man | `meta.tooltip.enabled` | expr | `{view.custom.level} < 1` | Tooltip "Requires Operator access" shown while expression is true |
| root/Mode/Body/Buttons/Man | `props.style.classes` | expr | `if({view.custom.m_Sts_Man}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |
| root/Mode/Body/Buttons/Auto | `props.image.icon.path` | expr | `if({view.custom.level} < 1, 'material/lock', '')` | Shows a lock icon on the button while the user is below Operator |
| root/Mode/Body/Buttons/Auto | `meta.tooltip.enabled` | expr | `{view.custom.level} < 1` | Tooltip "Requires Operator access" shown while expression is true |
| root/Mode/Body/Buttons/Auto | `props.style.classes` | expr | `if({view.custom.m_Sts_Auto}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |
| root/Mode/Body/Buttons/Cas | `props.image.icon.path` | expr | `if({view.custom.level} < 1, 'material/lock', '')` | Shows a lock icon on the button while the user is below Operator |
| root/Mode/Body/Buttons/Cas | `meta.tooltip.enabled` | expr | `{view.custom.level} < 1` | Tooltip "Requires Operator access" shown while expression is true |
| root/Mode/Body/Buttons/Cas | `props.style.classes` | expr | `if({view.custom.m_Sts_Cas}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |

### `root/Values`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Values/Body/PV/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_PV}, '#,##0.0')` | Text content |
| root/Values/Body/PV/EU | `props.text` | expr | `{view.custom.m_Cfg_PVEU}` | Text content |
| root/Values/Body/SP/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_SP}, '#,##0.0')` | Text content |
| root/Values/Body/SP/EU | `props.text` | expr | `{view.custom.m_Cfg_PVEU}` | Text content |
| root/Values/Body/CV/Val | `props.text` | expr | `numberFormat({view.custom.m_Out_CV}, '#,##0.0')` | Text content |
| root/Values/Body/CV/EU | `props.text` | expr | `'%'` | Text content |
| root/Values/Body/Err/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Err}, '#,##0.0')` | Text content |
| root/Values/Body/Err/EU | `props.text` | expr | `{view.custom.m_Cfg_PVEU}` | Text content |
| root/Values/Body/SPe | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Values/Body/SPe/Entry | `props.value` | tag (indirect) | tag `{0}/Cmd_SP`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (numeric entry) |
| root/Values/Body/SPe/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cmd_SP', currentValue.value, 1): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 1, audited; a refused or failed write refreshes the binding |
| root/Values/Body/SPe/Entry | `props.enabled` | expr | `!{view.custom.m_Sts_Cas}` | Enabled while expression is true |
| root/Values/Body/CVe | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Values/Body/CVe/Entry | `props.value` | tag (indirect) | tag `{0}/Cmd_CV`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (numeric entry) |
| root/Values/Body/CVe/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cmd_CV', currentValue.value, 1): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 1, audited; a refused or failed write refreshes the binding |
| root/Values/Body/CVe/Entry | `props.enabled` | expr | `{view.custom.m_Sts_Man}` | Enabled while expression is true |

### `root/Intlk`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Intlk | `props.params.tagPath` | expr | `{view.params.tagPath} + '/Intlk'` | Embedded view tagPath param |

### `root/Alarms`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Alarms/Body/None | `position.display` | expr | `!({view.custom.m_Alm_DevH_Sts_Active} \|\| {view.custom.m_Alm_DevL_Sts_Active} \|\| {view.custom.m_Alm_PVBad_Sts_Active})` | Shown while expression is true |
| root/Alarms/Body/List/A0 | `props.style.classes` | expr | `if({view.custom.m_Alm_DevH_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_DevH_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_DevH_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_DevH_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A1 | `props.style.classes` | expr | `if({view.custom.m_Alm_DevL_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_DevL_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_DevL_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_DevL_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A2 | `props.style.classes` | expr | `if({view.custom.m_Alm_PVBad_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_PVBad_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_PVBad_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_PVBad_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/Ack | `props.image.icon.path` | expr | `if({view.custom.level} < 1, 'material/lock', '')` | Shows a lock icon on the button while the user is below Operator |
| root/Alarms/Body/Ack | `meta.tooltip.enabled` | expr | `{view.custom.level} < 1` | Tooltip "Requires Operator access" shown while expression is true |

### `root/Trend`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Trend | `props.params.tagPath` | expr | `{view.params.tagPath}` | Embedded view tagPath param |
| root/Trend | `position.basis` | expr | `if({this.props.params.expanded}, '70.370vh', '15.741vh')` | Row height |

### `root/Tuning`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Tuning | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true (hidden below Operator) |
| root/Tuning/Header/Chevron | `props.text` | expr | `if({view.custom.open_Tuning}, '▾', '▸')` | Text content |
| root/Tuning/Body | `position.display` | expr | `{view.custom.open_Tuning}` | Shown while expression is true |
| root/Tuning/Body/R0 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Tuning/Body/R0/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_Kp}, '#,##0.###')` | Text content |
| root/Tuning/Body/R0/EU | `props.text` | expr | `''` | Text content |
| root/Tuning/Body/E0 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Tuning/Body/E0/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_Kp`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (numeric entry) |
| root/Tuning/Body/E0/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_Kp', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Tuning/Body/E0/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Tuning/Body/R1 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Tuning/Body/R1/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_Ti} / 1000, '#,##0.###')` | Text content |
| root/Tuning/Body/R1/EU | `props.text` | expr | `'s'` | Text content |
| root/Tuning/Body/E1 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Tuning/Body/E1/Entry | `props.value` | expr | `{view.custom.m_Cfg_Ti} / 1000` | Value in seconds (the PLC TIME is in milliseconds) |
| root/Tuning/Body/E1/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_Ti', currentValue.value, 4, 1000): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue` as value * 1000 (milliseconds), level 4, audited; a refused or failed write refreshes the binding |
| root/Tuning/Body/E1/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Tuning/Body/R2 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Tuning/Body/R2/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_Td} / 1000, '#,##0.###')` | Text content |
| root/Tuning/Body/R2/EU | `props.text` | expr | `'s'` | Text content |
| root/Tuning/Body/E2 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Tuning/Body/E2/Entry | `props.value` | expr | `{view.custom.m_Cfg_Td} / 1000` | Value in seconds (the PLC TIME is in milliseconds) |
| root/Tuning/Body/E2/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_Td', currentValue.value, 4, 1000): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue` as value * 1000 (milliseconds), level 4, audited; a refused or failed write refreshes the binding |
| root/Tuning/Body/E2/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Tuning/Body/R3 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Tuning/Body/R3/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_DB}, '#,##0.###')` | Text content |
| root/Tuning/Body/R3/EU | `props.text` | expr | `''` | Text content |
| root/Tuning/Body/E3 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Tuning/Body/E3/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_DB`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (numeric entry) |
| root/Tuning/Body/E3/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_DB', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Tuning/Body/E3/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Tuning/Body/R4 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Tuning/Body/R4/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_SPRate}, '#,##0.###')` | Text content |
| root/Tuning/Body/R4/EU | `props.text` | expr | `'/s'` | Text content |
| root/Tuning/Body/E4 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Tuning/Body/E4/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_SPRate`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (numeric entry) |
| root/Tuning/Body/E4/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_SPRate', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Tuning/Body/E4/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Tuning/Body/R5 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Tuning/Body/R5/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_CVRate}, '#,##0.###')` | Text content |
| root/Tuning/Body/R5/EU | `props.text` | expr | `'%/s'` | Text content |
| root/Tuning/Body/E5 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Tuning/Body/E5/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_CVRate`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (numeric entry) |
| root/Tuning/Body/E5/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_CVRate', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Tuning/Body/E5/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Tuning/Body/R6 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Tuning/Body/R6/Val | `props.text` | expr | `if({view.custom.m_Cfg_DirectAct}, 'Yes', 'No')` | Text content |
| root/Tuning/Body/C6 | `props.selected` | tag (indirect) | tag `{0}/Cfg_DirectAct`; refs {"0": "{view.params.tagPath}"} | Checkbox value, read one way |
| root/Tuning/Body/C6 | `props.selected` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_DirectAct', bool(currentValue.value), 4): self.refreshBinding('props.selected')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Tuning/Body/C6 | `props.enabled` | expr | `{view.custom.level} >= 4` | Enabled while expression is true |
| root/Tuning/Body/C6 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |

### `root/Configuration`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true (hidden below Operator) |
| root/Configuration/Header/Chevron | `props.text` | expr | `if({view.custom.open_Configuration}, '▾', '▸')` | Text content |
| root/Configuration/Body | `position.display` | expr | `{view.custom.open_Configuration}` | Shown while expression is true |
| root/Configuration/Body/R0 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R0/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_DevH_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Configuration/Body/R0/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E0 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E0/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_DevH/Cfg_Lim`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (numeric entry) |
| root/Configuration/Body/E0/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Alm_DevH/Cfg_Lim', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E0/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R1 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R1/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_DevL_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Configuration/Body/R1/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E1 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E1/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_DevL/Cfg_Lim`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (numeric entry) |
| root/Configuration/Body/E1/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Alm_DevL/Cfg_Lim', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E1/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R2 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R2/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_SPMin}, '#,##0.###')` | Text content |
| root/Configuration/Body/R2/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E2 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E2/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_SPMin`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (numeric entry) |
| root/Configuration/Body/E2/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_SPMin', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E2/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R3 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R3/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_SPMax}, '#,##0.###')` | Text content |
| root/Configuration/Body/R3/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E3 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E3/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_SPMax`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (numeric entry) |
| root/Configuration/Body/E3/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_SPMax', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E3/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R4 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R4/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_CVMin}, '#,##0.###')` | Text content |
| root/Configuration/Body/R4/EU | `props.text` | expr | `'%'` | Text content |
| root/Configuration/Body/E4 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E4/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_CVMin`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (numeric entry) |
| root/Configuration/Body/E4/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_CVMin', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E4/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R5 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R5/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_CVMax}, '#,##0.###')` | Text content |
| root/Configuration/Body/R5/EU | `props.text` | expr | `'%'` | Text content |
| root/Configuration/Body/E5 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E5/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_CVMax`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (numeric entry) |
| root/Configuration/Body/E5/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_CVMax', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E5/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R6 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R6/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_PVMin}, '#,##0.###')` | Text content |
| root/Configuration/Body/R6/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E6 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E6/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_PVMin`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (numeric entry) |
| root/Configuration/Body/E6/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_PVMin', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E6/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R7 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R7/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_PVMax}, '#,##0.###')` | Text content |
| root/Configuration/Body/R7/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E7 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E7/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_PVMax`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way (numeric entry) |
| root/Configuration/Body/E7/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_PVMax', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E7/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |

## Scripts reference

Total: **25 scripts**: 7 event scripts (5 `component.onActionPerformed`, 2 `dom.onClick`) and 1 transform script (`custom.level`). 17 property-change `onChange` scripts (`props.value` of every entry and `props.selected` of the Direct acting checkbox, see the end of the list). No `customMethods`, no `messageHandlers`.

The button handlers below call `efc.ui` functions. Those functions are summarised after the list.

1. **`root/Header/Close`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.closeDynamic(self)
```

2. **`root/Mode/Body/Buttons/Man`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_Man', True, 1)
```

3. **`root/Mode/Body/Buttons/Auto`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_Auto', True, 1)
```

4. **`root/Mode/Body/Buttons/Cas`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_Cas', True, 1)
```

5. **`root/Alarms/Body/Ack`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.ackAll(self, ['Alm_DevH', 'Alm_DevL', 'Alm_PVBad'])
```

6. **`root/Tuning/Header`**: `events.dom.onClick`, scope G.

```python
	self.view.custom.open_Tuning = not self.view.custom.open_Tuning
```

7. **`root/Configuration/Header`**: `events.dom.onClick`, scope G.

```python
	self.view.custom.open_Configuration = not self.view.custom.open_Configuration
```

8. **transform on `(view root)` `custom.level`**: `custom.level` binding, `property` source `session.props.auth.securityLevels`.

```python
	return efc.ui.level(value)
```

9. **`root/Values/Body/SPe/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cmd_SP', currentValue.value, 1):
			self.refreshBinding('props.value')
```

10. **`root/Values/Body/CVe/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cmd_CV', currentValue.value, 1):
			self.refreshBinding('props.value')
```

11. **`root/Tuning/Body/E0/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_Kp', currentValue.value, 4):
			self.refreshBinding('props.value')
```

12. **`root/Tuning/Body/E1/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_Ti', currentValue.value, 4, 1000):
			self.refreshBinding('props.value')
```

13. **`root/Tuning/Body/E2/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_Td', currentValue.value, 4, 1000):
			self.refreshBinding('props.value')
```

14. **`root/Tuning/Body/E3/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_DB', currentValue.value, 4):
			self.refreshBinding('props.value')
```

15. **`root/Tuning/Body/E4/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_SPRate', currentValue.value, 4):
			self.refreshBinding('props.value')
```

16. **`root/Tuning/Body/E5/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_CVRate', currentValue.value, 4):
			self.refreshBinding('props.value')
```

17. **`root/Tuning/Body/C6`**: `propConfig` `props.selected` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_DirectAct', bool(currentValue.value), 4):
			self.refreshBinding('props.selected')
```

18. **`root/Configuration/Body/E0/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Alm_DevH/Cfg_Lim', currentValue.value, 4):
			self.refreshBinding('props.value')
```

19. **`root/Configuration/Body/E1/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Alm_DevL/Cfg_Lim', currentValue.value, 4):
			self.refreshBinding('props.value')
```

20. **`root/Configuration/Body/E2/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_SPMin', currentValue.value, 4):
			self.refreshBinding('props.value')
```

21. **`root/Configuration/Body/E3/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_SPMax', currentValue.value, 4):
			self.refreshBinding('props.value')
```

22. **`root/Configuration/Body/E4/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_CVMin', currentValue.value, 4):
			self.refreshBinding('props.value')
```

23. **`root/Configuration/Body/E5/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_CVMax', currentValue.value, 4):
			self.refreshBinding('props.value')
```

24. **`root/Configuration/Body/E6/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_PVMin', currentValue.value, 4):
			self.refreshBinding('props.value')
```

25. **`root/Configuration/Body/E7/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_PVMax', currentValue.value, 4):
			self.refreshBinding('props.value')
```

### Explanation of each handler

| Handler | Action | Writes | Role check | Audit |
|---|---|---|---|---|
| `Header/Close` | `efc.ui.closeDynamic` restores the default dock view or closes the dock | none | none | no |
| `Mode/Man` | `efc.ui.cmd(self, 'Cmd_Man', True, 1)` | `Cmd_Man` | level 1 | no |
| `Mode/Auto` | `efc.ui.cmd(self, 'Cmd_Auto', True, 1)` | `Cmd_Auto` | level 1 | no |
| `Mode/Cas` | `efc.ui.cmd(self, 'Cmd_Cas', True, 1)` | `Cmd_Cas` | level 1 | no |
| `Alarms/Ack` | `efc.ui.ackAll(self, ['Alm_DevH', 'Alm_DevL', 'Alm_PVBad'])` | `Alm_*/Cmd_Ack` for unacknowledged alarms only | level 1 | no |
| `Tuning/Header` (dom click) | toggles `open_Tuning` | none | none | no |
| `Configuration/Header` (dom click) | toggles `open_Configuration` | none | none | no |
| `custom.level` transform | `efc.ui.level(value)` | `view.custom.level` | none | no |
| `Values/Body/SPe` (`Cmd_SP` entry, onChange) | `efc.ui.setValue(... 'Cmd_SP', value, 1)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cmd_SP` | level 1 (`setValue`) | yes |
| `Values/Body/CVe` (`Cmd_CV` entry, onChange) | `efc.ui.setValue(... 'Cmd_CV', value, 1)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cmd_CV` | level 1 (`setValue`) | yes |
| `Tuning/Body/E0` (`Cfg_Kp` entry, onChange) | `efc.ui.setValue(... 'Cfg_Kp', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_Kp` | level 4 (`setValue`) | yes |
| `Tuning/Body/E1` (`Cfg_Ti` entry, onChange) | `efc.ui.setValue(... 'Cfg_Ti', value, 4, 1000)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_Ti` (milliseconds) | level 4 (`setValue`) | yes |
| `Tuning/Body/E2` (`Cfg_Td` entry, onChange) | `efc.ui.setValue(... 'Cfg_Td', value, 4, 1000)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_Td` (milliseconds) | level 4 (`setValue`) | yes |
| `Tuning/Body/E3` (`Cfg_DB` entry, onChange) | `efc.ui.setValue(... 'Cfg_DB', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_DB` | level 4 (`setValue`) | yes |
| `Tuning/Body/E4` (`Cfg_SPRate` entry, onChange) | `efc.ui.setValue(... 'Cfg_SPRate', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_SPRate` | level 4 (`setValue`) | yes |
| `Tuning/Body/E5` (`Cfg_CVRate` entry, onChange) | `efc.ui.setValue(... 'Cfg_CVRate', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_CVRate` | level 4 (`setValue`) | yes |
| `Tuning/Body/C6` (`Cfg_DirectAct` checkbox, onChange) | `efc.ui.setValue(... 'Cfg_DirectAct', bool(value), 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_DirectAct` | level 4 (`setValue`) | yes |
| `Configuration/Body/E0` (`Alm_DevH/Cfg_Lim` entry, onChange) | `efc.ui.setValue(... 'Alm_DevH/Cfg_Lim', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Alm_DevH/Cfg_Lim` | level 4 (`setValue`) | yes |
| `Configuration/Body/E1` (`Alm_DevL/Cfg_Lim` entry, onChange) | `efc.ui.setValue(... 'Alm_DevL/Cfg_Lim', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Alm_DevL/Cfg_Lim` | level 4 (`setValue`) | yes |
| `Configuration/Body/E2` (`Cfg_SPMin` entry, onChange) | `efc.ui.setValue(... 'Cfg_SPMin', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_SPMin` | level 4 (`setValue`) | yes |
| `Configuration/Body/E3` (`Cfg_SPMax` entry, onChange) | `efc.ui.setValue(... 'Cfg_SPMax', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_SPMax` | level 4 (`setValue`) | yes |
| `Configuration/Body/E4` (`Cfg_CVMin` entry, onChange) | `efc.ui.setValue(... 'Cfg_CVMin', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_CVMin` | level 4 (`setValue`) | yes |
| `Configuration/Body/E5` (`Cfg_CVMax` entry, onChange) | `efc.ui.setValue(... 'Cfg_CVMax', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_CVMax` | level 4 (`setValue`) | yes |
| `Configuration/Body/E6` (`Cfg_PVMin` entry, onChange) | `efc.ui.setValue(... 'Cfg_PVMin', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_PVMin` | level 4 (`setValue`) | yes |
| `Configuration/Body/E7` (`Cfg_PVMax` entry, onChange) | `efc.ui.setValue(... 'Cfg_PVMax', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_PVMax` | level 4 (`setValue`) | yes |

`efc.ui.cmd` writes `view.params.tagPath + '/' + member` with `system.tag.writeBlocking` only when `userLevel >= minLevel`; below it, `cmd` returns False after logging and opening the AccessDenied popup (unless `notify=False`). The Mode and ACK buttons therefore use the level check. The entries and the checkbox call `efc.ui.setValue` from their onChange scripts instead (setpoint and output level 1, Tuning and Configuration level 4, all audited).

### Library functions used (`projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.level(levels)`**: walks `session.props.auth.securityLevels` (nested `name`/`children`, a path string, or a plain role list) and returns the highest index, 0 to 5, of the names that match `['Guest','Operator','Maintenance','Supervisor','Engineer','Admin']` case-insensitively (site names map through `efc.ui.ROLE_ALIASES`; no match gives 0). Bound to `custom.level`. `efc.ui.userLevel` (used by the checks in `cmd`, `setValue`, `ackAll`, `bypass`, `unbypass` and `dblCmd`) takes the larger of this and the level from `session.props.auth.user.roles`.
- **`efc.ui.closeDynamic(component)`**: sizes the dock (`efc.ui.sizeDock`), then loads the page's stored `default` view and params (`session.custom.efcDw['<pageId>|<page path>']`) back into the `dw_Right` dock, or closes the dock if there is no default. Writes no tags.
- **`efc.ui.cmd(component, member, value=True, minLevel=1, audit=False, notify=True)`**: the role-checked write described above. Below `minLevel` it does not write: with `notify` true it calls `efc.ui.denied` (a WARN log line and the `efcAccessDenied` popup, see [AccessDenied](../Parts/AccessDenied.md)), and it returns False either way. The JOG release events pass `notify=False`. Otherwise it writes through `_writeTags`, which logs any write that does not come back good, and returns True when the write was good. It is called with `minLevel` 1 and no audit by the Mode buttons. It writes one tag member with `system.tag.writeBlocking`.
- **`efc.ui.setValue(component, member, value, minLevel=4, scale=1)`**: the commit behind every entry field and checkbox (decisions 14, 27). It returns False on an empty `tagPath` or a None value. Below `minLevel` it calls `efc.ui.denied` (WARN log and AccessDenied popup) and returns False. With `scale` other than 1 it writes `int(round(value * scale))` (the TIME entries pass 1000). It reads the old value and returns True without writing when the value is unchanged; otherwise it writes through `_writeTags` and, on a good write, audits `EFC set` with target `<tagPath>/<member>` and value `'<old> -> <new>'`. It returns whether the write was good; on False the onChange script calls `self.refreshBinding(...)`, so the field shows the tag value again.
- **`efc.ui.denied(component, minLevel, action='')`**: logs `Refused <action> for <user> (<have>): needs <need>` at WARN level and opens the popup `efcAccessDenied` (`Templates/Dynamic Window/Parts/AccessDenied`, modal) with params `action`, `need`, `have` and `user`. Called by `cmd`, `setValue`, `ackAll`, `bypass`, `unbypass` and `dblCmd`. See [AccessDenied](../Parts/AccessDenied.md).
- **`efc.ui.ackAll(component, alarms)`**: reads `<alarm>/Sts_Unack` for the listed alarms with `system.tag.readBlocking`, then writes `<alarm>/Cmd_Ack` = True for those that are true.. Below level 1 it writes nothing and calls `efc.ui.denied` (WARN log and AccessDenied popup).
- **`efc.ui.openDynamic`**, **`efc.ui.trend`**: used by the templates and by `Templates/Dynamic Window/Parts/Trend`, not by this view.

## Tag members used

All paths are relative to `tagPath`. Types and comments come from `types/PCLib_Members.csv` (type `T_PID`; nested types: `Alm_DevH` and `Alm_DevL` are `T_AlmLim`, `Alm_PVBad` is `T_Alarm`, `Intlk` is `T_Intlk`).

| Member | Access (read/write) | Data type | Meaning |
|---|---|---|---|
| `Cfg_PVEU` | read | STRING[12] | PV engineering units text |
| `Sts_Man` | read | BOOL | In Manual |
| `Sts_Auto` | read | BOOL | In Auto |
| `Sts_Cas` | read | BOOL | In Cascade |
| `Cfg_Tag` | read | STRING[20] | Equipment / instrument tag, e.g. FT-101 |
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Sts_Intlk` | read | BOOL | Interlock active |
| `Sts_Track` | read | BOOL | Output tracking |
| `Sts_WindupHi` | read | BOOL | Output at high limit |
| `Sts_WindupLo` | read | BOOL | Output at low limit |
| `Sts_SPRamping` | read | BOOL | Setpoint ramping |
| `Val_PV` | read | REAL | Process value (EU). Also read by the trend pens. |
| `Val_SP` | read | REAL | Active setpoint after ramp and limits (EU). Also read by the trend pens. |
| `Out_CV` | read | REAL | Controller output (%). Also read by the trend pens. |
| `Val_Err` | read | REAL | Error SP - PV (EU) |
| `Alm_DevH/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_DevH/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_DevH/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_DevL/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_DevL/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_DevL/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_PVBad/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_PVBad/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_PVBad/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Cfg_Kp` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Proportional gain |
| `Cfg_Ti` | read (shown as value / 1000); write value * 1000 via `efc.ui.setValue` (level 4, audited) | TIME | Integral time, T#0S = no integral. Shown with unit `s`. See Notes. |
| `Cfg_Td` | read (shown as value / 1000); write value * 1000 via `efc.ui.setValue` (level 4, audited) | TIME | Derivative time. Shown with unit `s`. See Notes. |
| `Cfg_DB` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Error deadband (EU) |
| `Cfg_SPRate` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Setpoint ramp rate (EU/s), 0 = step |
| `Cfg_CVRate` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Output rate limit (%/s), 0 = none |
| `Alm_DevH/Cfg_Lim` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Alm_DevL/Cfg_Lim` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Cfg_SPMin` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Setpoint low limit (EU) |
| `Cfg_SPMax` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Setpoint high limit (EU) |
| `Cfg_CVMin` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Output low limit (%) |
| `Cfg_CVMax` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Output high limit (%) |
| `Cfg_PVMin` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | PV range low (EU) |
| `Cfg_PVMax` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | PV range high (EU) |
| `Cmd_SP` | read; write via `efc.ui.setValue` (level 1, audited) | REAL | Operator setpoint (EU) |
| `Cmd_CV` | read; write via `efc.ui.setValue` (level 1, audited) | REAL | Operator manual output (%) |
| `Cfg_DirectAct` | read; write via `efc.ui.setValue` (level 4, audited) | BOOL | TRUE = direct acting (CV rises with PV); FALSE = reverse |
| `Cmd_Man` | write (one-shot) | BOOL | Operator request Manual (one-shot) |
| `Cmd_Auto` | write (one-shot) | BOOL | Operator request Auto (one-shot) |
| `Cmd_Cas` | write (one-shot) | BOOL | Operator request Cascade (one-shot) |
| `Alm_DevH/Cmd_Ack` | write (ackAll, only unacknowledged) | BOOL | Operator acknowledge (one-shot) |
| `Alm_DevL/Cmd_Ack` | write (ackAll, only unacknowledged) | BOOL | Operator acknowledge (one-shot) |
| `Alm_PVBad/Cmd_Ack` | write (ackAll, only unacknowledged) | BOOL | Operator acknowledge (one-shot) |
| `Intlk` | read | T_Intlk | Passed as tagPath to the embedded IntlkList view (interlock group). |

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
  - `Mode` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
    - `Body` (ia.container.flex)
      - `Buttons` (ia.container.flex)
        - `Man` (ia.input.button)
        - `Auto` (ia.input.button)
        - `Cas` (ia.input.button)
  - `Values` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
    - `Body` (ia.container.flex)
      - `PV` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `SP` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `CV` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Err` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `SPe` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `CVe` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
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
  - `Tuning` (ia.container.flex)
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
```

## Notes and open questions

- **Mode buttons have no enable or state gate.** MAN, AUTO and CAS are clickable in any state (below level 1 each shows a lock and the press is refused with the AccessDenied popup), including INTERLOCKED and TRACKING. Only the PLC checks the request. Compare the valve docks, where OPEN and CLOSE check `Sts_Man` and availability.
- **Setpoint enable rule.** The setpoint entry is enabled only when `Sts_Cas` is false. It stays enabled in INTERLOCKED and TRACKING, and in MAN. The PLC decides what the setpoint does in those states.
- **EU labels in Configuration.** The SP min, SP max, PV min, PV max and deviation-limit rows have a blank unit. The Values rows use `Cfg_PVEU`, and the Setpoint entry has a blank unit too. Deviation limits are in EU (the T_AlmLim comment says so). Decide whether these rows should show `Cfg_PVEU`.
- **Banner ignores `Sts_Mode`.** `Sts_Mode` (INT, 0=Man 1=Auto 2=Cas 3=Track 4=Intlk) is not bound. The banner uses the separate booleans, so a loop with none of `Sts_Man`, `Sts_Auto`, `Sts_Cas`, `Sts_Track` or `Sts_Intlk` set shows UNKNOWN.
- **Trend history.** The Trend part reads `Val_PV`, `Val_SP` and `Out_CV` through `efc.ui.trend` (`queryTagHistory`, average aggregation). History must be enabled on these members on the gateway, or the trend stays empty. This is not checked from the repo.
- **T_PID members this view does not use.** Inputs: `Inp_PV`, `Inp_PVBad`, `Inp_CasSP`, `Inp_FF`, `Inp_TrackEn`, `Inp_TrackVal`, `Inp_IntlkOK`. Program and config: `Prog_SP`, `Cfg_ProgSP`, `Cfg_FFGain`, `Cfg_PVTrack`, `Cfg_IntlkCV`, `Cfg_BadPVAction`. Status: `Val_SPTarget`, `Sts_Mode`. This is expected for an operator dock, but `Cfg_PVTrack`, `Cfg_BadPVAction` and `Cfg_IntlkCV` change how the loop behaves on a bad PV or interlock, so the operator cannot see them here.
- **Every custom mirror is used.** All 38 `custom.m_*` properties are read by at least one binding. None is unused.
- **`docs/pid-loop-templates.md`** now says the cards open this window with `efc.ui.openDynamic` (decision 15 retired the LoopConfig popup) and bind `T_PID`. The cards still read `Sts_Mode` (0 MAN / 1 AUTO / 2 CAS) for their mode chip; this window uses the boolean `Sts_Man`, `Sts_Auto` and `Sts_Cas`.
