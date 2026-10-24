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

**Mode** (level 1 and above). The MAN, AUTO and CAS toggle buttons are highlighted (`Button/Toggle/On`) when `Sts_Man`, `Sts_Auto` or `Sts_Cas` is true. Each runs `efc.ui.cmd(self, 'Cmd_<mode>', True, 1)`, a one-shot write with no audit. None of the three buttons has an `enabled` binding, so each is clickable in any state, including INTERLOCKED and TRACKING. The PLC decides whether the request is honoured.

**Values** (all levels). PV (`Val_PV`), SP (`Val_SP`), Output (`Out_CV`, unit `%`) and Error (`Val_Err`) are shown with `#,##0.0`. The EU text for PV, SP and Error comes from `Cfg_PVEU`.

- **Setpoint entry** (level 1 and above): a numeric entry bound two-way to `Cmd_SP`. It is enabled only when `Sts_Cas` is false. The entry writes through its binding. The only guard is the UI enable and visibility. No `efc.ui` call, no role check in script, no audit.
- **Output entry** (level 1 and above): a numeric entry bound two-way to `Cmd_CV`. It is enabled only when `Sts_Man` is true. Same write path as the setpoint entry.

**Interlocks** (all levels). An embedded `Templates/Dynamic Window/Parts/IntlkList` (see [Parts/IntlkList](../Parts/IntlkList.md)) gets `tagPath + '/Intlk'` and the title "Interlocks". Its content is not in this file.

**Alarms** (all levels). Three rows: Deviation high (`Alm_DevH`), Deviation low (`Alm_DevL`) and PV bad (`Alm_PVBad`). An active row takes `Alarm/<priority>/Unacked` or `Alarm/<priority>/Fill`. The priority comes from `Cfg_Priority`: 1 `Critical`, 2 `High`, 3 `Medium`, 4 `Low`, anything else `Medium`. An inactive, unacknowledged row uses `Alarm/Status/ClearedUnacked`. An inactive, acknowledged row uses `Text/Caption Text/Color/Muted`. "No active alarms" shows when none is active. **ACK** (level 1 and above) calls `efc.ui.ackAll`, which writes `Cmd_Ack` only for the alarms whose `Sts_Unack` is true.

**Trend.** Embeds `Templates/Dynamic Window/Parts/Trend` (see [Parts/Trend](../Parts/Trend.md)) with the static pens `["Val_PV", "Val_SP", "Out_CV"]` and `expanded` = `false`. The Trend part declares `expanded` as `inout` and toggles it itself, and the value flows back to this embed. The `position.basis` binding (`{this.props.params.expanded}`) then grows the trend from 15.741 vh to 70.370 vh. The expansion is local to the trend and does not widen the dock. The trend reads tag history through `efc.ui.trend` (`queryTagHistory`), with a range selector inside the Trend part (5 min, 30 min, 1 h, 8 h, 24 h; default 30 min).

**Tuning** (all levels for the read-only rows; collapsible). The header click toggles `open_Tuning`. Rows: Gain (Kp), Integral (Ti, s), Derivative (Td, s), Deadband, SP rate (/s), CV rate (%/s) and a "Direct acting" checkbox (`Cfg_DirectAct`). Below level 4 each row shows its value read-only (Direct acting shows `Yes` or `No`). At level 4 and above the value rows are replaced by numeric entries bound two-way to `Cfg_Kp`, `Cfg_DB`, `Cfg_SPRate`, `Cfg_CVRate`, and by entries for `Cfg_Ti` and `Cfg_Td` (PCLib TIME, milliseconds on the PLC) that show `member / 1000` seconds and write `int(round(value * 1000))` from a `props.value` onChange script (only when `origin == 'Browser'`) through `efc.ui.cmd(self, member, ..., 4, audit=True)`, and the checkbox is shown (level 4 and above; hidden below). The entries have `enabled` = `true`. Their only guard is visibility.

**Configuration** (all levels for the read-only rows; collapsible). The header click toggles `open_Configuration`. Rows: Dev high limit (`Alm_DevH/Cfg_Lim`), Dev low limit (`Alm_DevL/Cfg_Lim`), SP min, SP max, CV min (%), CV max (%), PV min and PV max. Editing works as for Tuning: read-only below level 4, bidirectional entries at level 4 and above, `enabled` = `true`.

**Role checks.** Role levels come from the Perspective session (`session.props.auth.user.roles`) and are mapped by `efc.ui.level`. Only the Mode buttons and ACK call a role-checked script function (`efc.ui.cmd` and `efc.ui.ackAll`, both minimum level 1). Setpoint, output, the other Tuning entries and Configuration writes are gated by visibility and enable bindings only; the Ti and Td entries also call `efc.ui.cmd` (level 4). Real access control has to be enforced in Perspective security and the PLC logic.

**Audit.** Every button call in this view omits the audit flag. Only the Ti and Td entries call `efc.ui.cmd` with `audit=True`. Setpoint, output, the other Tuning entries and Configuration writes are not audited.

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
| `view.custom.level` | `0` | property + script transform | `session.props.auth.user.roles` → `return efc.ui.level(value)` | Role level 0-5 from `session.props.auth.user.roles` via `efc.ui.level`. Gates the Mode, ACK, read/write visibility of Tuning and Configuration (Guest 0, Operator 1, Maintenance 2, Supervisor 3, Engineer 4, Admin 5). |
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

- `session.props.auth.user.roles`: read by `custom.level` (transform `efc.ui.level`).
- `session.props.auth.user.userName`: not bound in this view. `efc.ui._audit` reads it; only the Ti and Td entry onChange scripts reach it.
- `session.custom.efcDw['<pageId>|<page path>']`: holds only the page's default dock view (`{'default': {'path', 'params'}}`), written by `efc.ui.setDefaultDock` in the screen's onStartup (not in this file) and read by `efc.ui.closeDynamic` in the header. `openDynamic` writes no session value; it calls `system.perspective.alterDock` and `openDock` on `dw_Right`.
- `page.props.pageId` and `page.props.path`: read by `efc.ui._state` to key `efcDw` (the pageId survives `navigate()`, so the path keeps one screen's default from leaking into the next).
- `page.props.dimensions`: `efc.ui.sizeDock` (run by `openDynamic`, `closeDynamic` and `setDefaultDock`) reads `viewport.height`, turns `dimensions.enabled` on if needed, and sets the `dw_Right` dock size to 400 x height / 1080 px (37.04 vh, decision 33). Needs Ignition 8.1.7+ for page dimensions and 8.1.19+ for `alterDock`. Reached through the header close.
- No message handlers. No `customMethods`.

## Bindings reference

Total: **169 bindings**: 40 at view root (all `custom.*`, including 1 `property` binding with a transform) and 129 on components. Types: 114 `expr`, 54 `tag`, 1 `property`. `params.tagPath` and `params.tType` have `paramDirection` only. Embedded-view `params.*` values and `position.basis` are component bindings and are counted in the 129.

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
| root/Mode | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Mode/Body/Buttons/Man | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Mode/Body/Buttons/Man | `props.style.classes` | expr | `if({view.custom.m_Sts_Man}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |
| root/Mode/Body/Buttons/Auto | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Mode/Body/Buttons/Auto | `props.style.classes` | expr | `if({view.custom.m_Sts_Auto}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |
| root/Mode/Body/Buttons/Cas | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
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
| root/Values/Body/SPe/Entry | `props.value` | tag (indirect) | tag `{0}/Cmd_SP` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Values/Body/SPe/Entry | `props.enabled` | expr | `!{view.custom.m_Sts_Cas}` | Enabled while expression is true |
| root/Values/Body/CVe | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Values/Body/CVe/Entry | `props.value` | tag (indirect) | tag `{0}/Cmd_CV` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
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
| root/Alarms/Body/Ack | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |

### `root/Trend`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Trend | `props.params.tagPath` | expr | `{view.params.tagPath}` | Embedded view tagPath param |
| root/Trend | `position.basis` | expr | `if({this.props.params.expanded}, '70.370vh', '15.741vh')` | Row height |

### `root/Tuning`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Tuning/Header/Chevron | `props.text` | expr | `if({view.custom.open_Tuning}, '▾', '▸')` | Text content |
| root/Tuning/Body | `position.display` | expr | `{view.custom.open_Tuning}` | Shown while expression is true |
| root/Tuning/Body/R0 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Tuning/Body/R0/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_Kp}, '#,##0.###')` | Text content |
| root/Tuning/Body/R0/EU | `props.text` | expr | `''` | Text content |
| root/Tuning/Body/E0 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Tuning/Body/E0/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_Kp` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Tuning/Body/E0/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Tuning/Body/R1 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Tuning/Body/R1/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_Ti} / 1000, '#,##0.###')` | Text content |
| root/Tuning/Body/R1/EU | `props.text` | expr | `'s'` | Text content |
| root/Tuning/Body/E1 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Tuning/Body/E1/Entry | `props.value` | expr | `{view.custom.m_Cfg_Ti} / 1000` | Value in seconds (the PLC TIME is in milliseconds) |
| root/Tuning/Body/E1/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: efc.ui.cmd(self, 'Cfg_Ti', int(round(currentValue.value * 1000)), 4, audit=True)` | Edit written as milliseconds, Engineer, audited |
| root/Tuning/Body/E1/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Tuning/Body/R2 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Tuning/Body/R2/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_Td} / 1000, '#,##0.###')` | Text content |
| root/Tuning/Body/R2/EU | `props.text` | expr | `'s'` | Text content |
| root/Tuning/Body/E2 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Tuning/Body/E2/Entry | `props.value` | expr | `{view.custom.m_Cfg_Td} / 1000` | Value in seconds (the PLC TIME is in milliseconds) |
| root/Tuning/Body/E2/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: efc.ui.cmd(self, 'Cfg_Td', int(round(currentValue.value * 1000)), 4, audit=True)` | Edit written as milliseconds, Engineer, audited |
| root/Tuning/Body/E2/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Tuning/Body/R3 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Tuning/Body/R3/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_DB}, '#,##0.###')` | Text content |
| root/Tuning/Body/R3/EU | `props.text` | expr | `''` | Text content |
| root/Tuning/Body/E3 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Tuning/Body/E3/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_DB` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Tuning/Body/E3/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Tuning/Body/R4 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Tuning/Body/R4/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_SPRate}, '#,##0.###')` | Text content |
| root/Tuning/Body/R4/EU | `props.text` | expr | `'/s'` | Text content |
| root/Tuning/Body/E4 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Tuning/Body/E4/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_SPRate` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Tuning/Body/E4/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Tuning/Body/R5 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Tuning/Body/R5/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_CVRate}, '#,##0.###')` | Text content |
| root/Tuning/Body/R5/EU | `props.text` | expr | `'%/s'` | Text content |
| root/Tuning/Body/E5 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Tuning/Body/E5/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_CVRate` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Tuning/Body/E5/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Tuning/Body/R6 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Tuning/Body/R6/Val | `props.text` | expr | `if({view.custom.m_Cfg_DirectAct}, 'Yes', 'No')` | Text content |
| root/Tuning/Body/C6 | `props.selected` | tag (indirect) | tag `{0}/Cfg_DirectAct` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write checkbox value |
| root/Tuning/Body/C6 | `props.enabled` | expr | `{view.custom.level} >= 4` | Enabled while expression is true |
| root/Tuning/Body/C6 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |

### `root/Configuration`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration/Header/Chevron | `props.text` | expr | `if({view.custom.open_Configuration}, '▾', '▸')` | Text content |
| root/Configuration/Body | `position.display` | expr | `{view.custom.open_Configuration}` | Shown while expression is true |
| root/Configuration/Body/R0 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R0/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_DevH_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Configuration/Body/R0/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E0 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E0/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_DevH/Cfg_Lim` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Configuration/Body/E0/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R1 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R1/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_DevL_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Configuration/Body/R1/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E1 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E1/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_DevL/Cfg_Lim` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Configuration/Body/E1/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R2 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R2/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_SPMin}, '#,##0.###')` | Text content |
| root/Configuration/Body/R2/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E2 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E2/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_SPMin` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Configuration/Body/E2/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R3 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R3/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_SPMax}, '#,##0.###')` | Text content |
| root/Configuration/Body/R3/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E3 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E3/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_SPMax` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Configuration/Body/E3/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R4 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R4/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_CVMin}, '#,##0.###')` | Text content |
| root/Configuration/Body/R4/EU | `props.text` | expr | `'%'` | Text content |
| root/Configuration/Body/E4 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E4/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_CVMin` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Configuration/Body/E4/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R5 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R5/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_CVMax}, '#,##0.###')` | Text content |
| root/Configuration/Body/R5/EU | `props.text` | expr | `'%'` | Text content |
| root/Configuration/Body/E5 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E5/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_CVMax` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Configuration/Body/E5/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R6 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R6/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_PVMin}, '#,##0.###')` | Text content |
| root/Configuration/Body/R6/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E6 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E6/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_PVMin` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Configuration/Body/E6/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R7 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R7/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_PVMax}, '#,##0.###')` | Text content |
| root/Configuration/Body/R7/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E7 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E7/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_PVMax` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value (numeric entry) |
| root/Configuration/Body/E7/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |

## Scripts reference

Total: **10 scripts**: 7 event scripts (5 `component.onActionPerformed`, 2 `dom.onClick`) and 1 transform script (`custom.level`). 2 property-change `onChange` scripts (`props.value` of the TIME entries, see the end of the list). No `customMethods`, no `messageHandlers`.

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

8. **transform on `(view root)` `custom.level`**: `custom.level` binding, `property` source `session.props.auth.user.roles`.

```python
	return efc.ui.level(value)
```

9. **`root/Tuning/Body/E1/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		efc.ui.cmd(self, 'Cfg_Ti', int(round(currentValue.value * 1000)), 4, audit=True)
```

10. **`root/Tuning/Body/E2/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		efc.ui.cmd(self, 'Cfg_Td', int(round(currentValue.value * 1000)), 4, audit=True)
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
| `Tuning/Body/E1` (`Cfg_Ti` entry, onChange) | `efc.ui.cmd(... 'Cfg_Ti', int(round(value * 1000)), 4)`, only when `origin == 'Browser'` | `Cfg_Ti` (milliseconds) | level 4 | yes
| `Tuning/Body/E2` (`Cfg_Td` entry, onChange) | `efc.ui.cmd(... 'Cfg_Td', int(round(value * 1000)), 4)`, only when `origin == 'Browser'` | `Cfg_Td` (milliseconds) | level 4 | yes

`efc.ui.cmd` writes `view.params.tagPath + '/' + member` with `system.tag.writeBlocking` only when `userLevel >= minLevel`. The Mode and ACK buttons therefore use the level check. The Ti and Td entries call it from their onChange scripts (level 4, audited). The Setpoint, Output, the other Tuning and the Configuration entries do not call `efc.ui`, so they have no script-side level check.

### Library functions used (`projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.level(roles)`**: highest index of the role in `['Guest','Operator','Maintenance','Supervisor','Engineer','Admin']`, or 0. Bound to `custom.level`.
- **`efc.ui.closeDynamic(component)`**: sizes the dock (`efc.ui.sizeDock`), then loads the page's stored `default` view and params (`session.custom.efcDw['<pageId>|<page path>']`) back into the `dw_Right` dock, or closes the dock if there is no default. Writes no tags.
- **`efc.ui.cmd(component, member, value, minLevel, audit)`**: the role-checked write described above. It is called with `minLevel` 1 and no audit by the Mode buttons, and with `minLevel` 4 and `audit=True` by the Ti and Td entries. It writes one tag member with `system.tag.writeBlocking`.
- **`efc.ui.ackAll(component, alarms)`**: reads `<alarm>/Sts_Unack` for the listed alarms with `system.tag.readBlocking`, then writes `<alarm>/Cmd_Ack` = True for those that are true. Only runs at level 1 and above.
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
| `Cfg_Kp` | read/write (bidirectional) | REAL | Proportional gain |
| `Cfg_Ti` | read (shown as value / 1000); write value * 1000 via `efc.ui.cmd` | TIME | Integral time, T#0S = no integral. Shown with unit `s`. See Notes. |
| `Cfg_Td` | read (shown as value / 1000); write value * 1000 via `efc.ui.cmd` | TIME | Derivative time. Shown with unit `s`. See Notes. |
| `Cfg_DB` | read/write (bidirectional) | REAL | Error deadband (EU) |
| `Cfg_SPRate` | read/write (bidirectional) | REAL | Setpoint ramp rate (EU/s), 0 = step |
| `Cfg_CVRate` | read/write (bidirectional) | REAL | Output rate limit (%/s), 0 = none |
| `Alm_DevH/Cfg_Lim` | read/write (bidirectional) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Alm_DevL/Cfg_Lim` | read/write (bidirectional) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Cfg_SPMin` | read/write (bidirectional) | REAL | Setpoint low limit (EU) |
| `Cfg_SPMax` | read/write (bidirectional) | REAL | Setpoint high limit (EU) |
| `Cfg_CVMin` | read/write (bidirectional) | REAL | Output low limit (%) |
| `Cfg_CVMax` | read/write (bidirectional) | REAL | Output high limit (%) |
| `Cfg_PVMin` | read/write (bidirectional) | REAL | PV range low (EU) |
| `Cfg_PVMax` | read/write (bidirectional) | REAL | PV range high (EU) |
| `Cmd_SP` | read/write (bidirectional) | REAL | Operator setpoint (EU) |
| `Cmd_CV` | read/write (bidirectional) | REAL | Operator manual output (%) |
| `Cfg_DirectAct` | read/write (bidirectional) | BOOL | TRUE = direct acting (CV rises with PV); FALSE = reverse |
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

- **Mode buttons have no enable or state gate.** MAN, AUTO and CAS are clickable at level 1 and above in any state, including INTERLOCKED and TRACKING. Only the PLC checks the request. Compare the valve docks, where OPEN and CLOSE check `Sts_Man` and availability.
- **Setpoint, output, Tuning (except Ti and Td) and Configuration writes bypass `efc.ui`.** They are direct two-way bindings. Their only guard is visibility and the enable expression. `efc.ui.cmd` is not called, so there is no server-side level re-check and no audit. `steward/DECISIONS.md` decision 27 says writes go through `efc.ui.cmd`, and decision 14 says Tuning and Configuration edits and alarm-limit changes are Engineer+ and audit-logged (old value, new value, user, time). This view meets the level rule only through visibility, and it has no audit, apart from the Ti and Td entries, which now go through `efc.ui.cmd` (level 4, audited). This needs a decision: either move these writes into a role-checked, audited `efc.ui` function, or record the exception in DECISIONS.
- **Setpoint enable rule.** The setpoint entry is enabled only when `Sts_Cas` is false. It stays enabled in INTERLOCKED and TRACKING, and in MAN. The PLC decides what the setpoint does in those states.
- **Read-only Tuning and Configuration are shown to every level.** A Guest (level 0) sees the Tuning and Configuration values, because the read-only rows have no level floor. The sections are collapsed by default (`open_Tuning` and `open_Configuration` are `false`). Confirm that read-only visibility at Guest is intended.
- **EU labels in Configuration.** The SP min, SP max, PV min, PV max and deviation-limit rows have a blank unit. The Values rows use `Cfg_PVEU`, and the Setpoint entry has a blank unit too. Deviation limits are in EU (the T_AlmLim comment says so). Decide whether these rows should show `Cfg_PVEU`.
- **Banner ignores `Sts_Mode`.** `Sts_Mode` (INT, 0=Man 1=Auto 2=Cas 3=Track 4=Intlk) is not bound. The banner uses the separate booleans, so a loop with none of `Sts_Man`, `Sts_Auto`, `Sts_Cas`, `Sts_Track` or `Sts_Intlk` set shows UNKNOWN.
- **Trend history.** The Trend part reads `Val_PV`, `Val_SP` and `Out_CV` through `efc.ui.trend` (`queryTagHistory`, average aggregation). History must be enabled on these members on the gateway, or the trend stays empty. This is not checked from the repo.
- **T_PID members this view does not use.** Inputs: `Inp_PV`, `Inp_PVBad`, `Inp_CasSP`, `Inp_FF`, `Inp_TrackEn`, `Inp_TrackVal`, `Inp_IntlkOK`. Program and config: `Prog_SP`, `Cfg_ProgSP`, `Cfg_FFGain`, `Cfg_PVTrack`, `Cfg_IntlkCV`, `Cfg_BadPVAction`. Status: `Val_SPTarget`, `Sts_Mode`. This is expected for an operator dock, but `Cfg_PVTrack`, `Cfg_BadPVAction` and `Cfg_IntlkCV` change how the loop behaves on a bad PV or interlock, so the operator cannot see them here.
- **Every custom mirror is used.** All 38 `custom.m_*` properties are read by at least one binding. None is unused.
- **`docs/pid-loop-templates.md`** now says the cards open this window with `efc.ui.openDynamic` (decision 15 retired the LoopConfig popup) and bind `T_PID`. The cards still read `Sts_Mode` (0 MAN / 1 AUTO / 2 CAS) for their mode chip; this window uses the boolean `Sts_Man`, `Sts_Auto` and `Sts_Cas`.
