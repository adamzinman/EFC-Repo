# Templates/Dynamic Window/Rotating/Rotating

Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/Dynamic Window/Rotating/Rotating/view.json`
Opened from: the motor-type rotating templates (`Templates/Rotating/` symbols with `tType` `T_Motor`: `Pump_Centrifugal`, `Pump_PD_Rotary`, `Pump_Diaphragm`, `Pump_Reciprocating`, `Pump_Vacuum`, `Compressor_Centrifugal`, `Compressor_Diaphragm`, `Blower`, `Agitator`, `Motor`; see [Rotating templates](../../Rotating/Rotating_Discrete.md)) through `efc.ui.openDynamic`. The heat exchanger template `Templates/HeatTransfer/HX_AirCooled` also has `tType` `T_Motor` and opens this window (documented in the same family file, [Rotating templates](../../Rotating/Rotating_Discrete.md), because it shares their properties). Dynamic window id `dw_Rotating`.

## Overview

The operator and maintenance dynamic window for a motor-driven equipment item (T_Motor): start/stop control, feedback, permissives and interlocks, alarms, run counters and motor configuration. It opens in the page's right dock (`dw_Right`), not as a popup.

- **Default size:** 400 x 860 (`props.defaultSize`). The root is a scrolling column.
- **Parameters:** `tagPath` (the T_Motor instance) and `tType` (default `T_Motor`).
- **How it is opened:** the template's single click runs `efc.ui.openDynamic(self)`. The template's `dockId` is empty, so the function uses `BY_TYPE` in `efc/ui/code.py`, which maps `T_Motor` to `dw_Rotating`. It then loads `Templates/Dynamic Window/Rotating/Rotating` into the page's `dw_Right` dock with params `{tagPath: ...}` (`system.perspective.alterDock`) and opens the dock. `efc.ui.openDynamic` passes only `tagPath` (and `model` if present). **`tType` is never passed**, so the dock always runs with its default `T_Motor`. Nothing in this view uses `tType`. The VFD symbols (`T_VFD`) open `Templates/Dynamic Window/Rotating/VFD` instead.
- **Generated view:** this view is written by `generator/docks/build_docks.py` (function `rotating()`, which calls `motor_like()`). Change the generator, not `view.json`, or the next build overwrites the edit.
- **How it closes:** the header `X` runs `efc.ui.closeDynamic(self)`, which puts the page's default view back in the `dw_Right` dock (set by `efc.ui.setDefaultDock` in the screen's onStartup), or closes the dock if the page has no default. That startup script is not in this view.

## How it operates

**Header.** Shows `Cfg_Tag` (large) and `Cfg_Desc`.

**Banner.** The state label is chosen by priority: `Sts_Tripped` (TRIPPED), `Sts_Fault` (FAULT), `Sts_Starting` (STARTING), `Sts_Stopping` (STOPPING), `Sts_Running` (RUNNING), `Sts_Stopped` (STOPPED), else UNKNOWN. The style class follows the same order (`State/Fault`, `State/Fault`, `State/Transition`, `State/Transition`, `State/Running`, `State/Stopped`, `State/Unknown`). Four chips appear when their flag is true: SIM (`Sts_Sim`), LOCAL (`Sts_Local`), INTLK (`Sts_Intlk`), NOT PERM (`Sts_NotPerm`).

**Mode.** As on the discrete valve dock, the mode text shows the highest of OOS, MAINT, MAN, else AUTO. The four toggle buttons highlight the active mode. AUTO and MAN are visible at level 1 and above, and MAINT and OOS at level 2 and above. None of the four has an `enabled` binding. Each writes a one-shot `Mode/Cmd_*`. MAINT and OOS are audited.

**Commands** (level 1 and above). The section shows four controls:
- `START` writes `Cmd_Start` at level 1. Enabled when `Mode/Sts_Man && Sts_Avail && !Sts_Intlk && !Sts_Local && !Sts_NotPerm`.
- `STOP` writes `Cmd_Stop` at level 1. It has no enable condition.
- `RESET` writes `Cmd_Reset` at level 1. It has no enable condition.
- `JOG` is hold-to-jog, visible at level 2 and above only. It writes `Cmd_Jog` TRUE on mouse down or touch start and FALSE on mouse up, mouse leave or touch end (`efc.ui.cmd`, level 2, not audited). It is enabled only in MAINT: `Mode/Sts_Maint` and the START terms except `Mode/Sts_Man` (available, not interlocked, not LOCAL, not NOT PERM).
- A hint line reads "Enabled in MAN, available, permitted, not interlocked, not LOCAL. JOG: hold, MAINT mode only".

**Values** (all levels). Current (`Val_Current`, A). Rated (`Cfg_RatedAmps`, A). Load (`Val_LoadPct`, %). A diagnostics row shows the NAMUR NE107 text for `Sts_NE107`: 0 `NE107 OK`, 1 `NE107 F`, 2 `NE107 C`, 3 `NE107 S`, 4 `NE107 M`.

**Permissives and interlocks.** Two embedded `Templates/Dynamic Window/Parts/IntlkList` views get `tagPath + '/Perm'` (title "Permissives") and `tagPath + '/Intlk'` (title "Interlocks"). Their content is not in this file (see [Parts/IntlkList.md](../Parts/IntlkList.md)).

**Alarms** (all levels). Eight rows: fail to start (`Alm_FailStart`), fail to stop (`Alm_FailStop`), uncommanded run/stop (`Alm_Uncmd`), E-stop (`Alm_EStop`), interlock trip (`Alm_IntlkTrip`), excess starts (`Alm_ExcessStarts`), overload (`Alm_OL`) and high current (`Alm_HiCurrent`). A row is coloured when its alarm is active, using the alarm's `Cfg_Priority`: 1 `Critical`, 2 `High`, 3 `Medium`, 4 `Low`, anything else `Medium`. The class adds `/Unacked` or `/Fill`. An inactive but unacknowledged alarm uses `Alarm/Status/ClearedUnacked`. An inactive, acknowledged alarm uses `Text/Caption Text/Color/Muted`. "No active alarms" is shown when none is active. **ACK** (level 1 and above) calls `efc.ui.ackAll` with all eight alarms, which writes `Cmd_Ack` only for those whose `Sts_Unack` is true.

**Trend.** Embeds `Templates/Dynamic Window/Parts/Trend` with pens `Val_Current` and `Sts_Running`. The embedded view's `expanded` param starts `false`. It is declared `inout` in `Templates/Dynamic Window/Parts/Trend`, so the trend part toggles it and the value flows back to this embed. The `position.basis` binding (`{this.props.params.expanded}`) then grows the trend from 15.741 vh to 70.370 vh. The expansion is local to the trend and does not widen the dock (see [Parts/Trend.md](../Parts/Trend.md)).

**Maintenance** (level 2 and above). Shows run hours (`Run/Val_RunHrs`), starts (`Run/Val_Starts`), starts in the last hour (`Run/Val_StartsLastHr`), run hours since maintenance (`Run/Val_HrsSinceMaint`) and whether maintenance is due (`Run/Sts_MaintDue`). `RESET MAINT` writes `Run/Cmd_ResetMaint` (audited). `SIMULATE` toggles `Sim_En` (audited).

**Configuration** (collapsible; the header click toggles `open_Configuration`, collapsed by default). Feedback time, restart delay, rated current, max starts per hour, the auto restart checkbox and the high current alarm limit. Below level 4 the numeric values show as read-only labels. At level 4 and above each numeric value has an entry bound bidirectionally to its tag, except Feedback time (`Cfg_FbkTime`) and Restart delay (`Cfg_RestartDly`), which are PCLib TIME in milliseconds: they are shown as `member / 1000` seconds and written as `int(round(value * 1000))` by a `props.value` onChange script (only when `origin == 'Browser'`) through `efc.ui.cmd(self, member, ..., 4, audit=True)`. Auto restart (`Cfg_AutoRestart`) follows the same pattern: below level 4 a read-only row shows `Yes` or `No`; at level 4 and above the row is hidden and the checkbox is shown. The entries have the literal enable `true`, so the level 4 rule is enforced only by visibility; the checkbox is also hidden below level 4.

**Role checks.** All role levels come from the Perspective session (`session.props.auth.user.roles`) and are checked in the client. `efc.ui.cmd` returns without writing when the level is too low. The Configuration entries (except the two TIME entries, which go through `efc.ui.cmd`) and the auto restart checkbox are bindings that write tags directly. Their only guards are their visibility and enable expressions. Real access control has to be enforced in Perspective security and the PLC logic.

**Audit.** `efc.ui` writes an audit entry (`system.util.audit`, and the logger as a fallback record) only for calls with `audit=True`. In this view that means MAINT, OOS, RESET MAINT, SIMULATE and the Feedback time and Restart delay edits. Nothing audits AUTO, MAN, START, STOP, RESET, JOG, ACK, or the other configuration edits.

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `""` | T_Motor instance. Every component binding uses `{view.params.tagPath}`. | Set by `efc.ui.openDynamic` from the template's `dwTagPath` (or `tagPath`, `cardPath`). Read by bindings and `efc.ui` commands. |
| `tType` | input | `T_Motor` | Declared type. | Not passed by `efc.ui.openDynamic`; not referenced by any binding or script in this view. Always the default. |

Both have `paramDirection: input` and `persistent: true`. No output parameters.

### View-level custom properties (`custom`)

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.level` | `0` | property + script transform | `session.props.auth.user.roles` → `return efc.ui.level(value)` | Role level 0-5 from `session.props.auth.user.roles` via `efc.ui.level`. Gates buttons and sections (Guest 0, Operator 1, Maintenance 2, Supervisor 3, Engineer 4, Admin 5). |
| `view.custom.open_Configuration` | `false` | none (written by scripts) | none | View-local toggle for the Configuration section. Set by the header click script; not bound to any tag; not persisted. |

#### Tag mirrors (`custom.m_*`)

There are 56 tag-mirror properties. Each `custom.m_<member>` (with `/` replaced by `_`) has an indirect, read-only tag binding to `{view.params.tagPath}/<member>` (`bidirectional: false`, fallback delay 2.5 s), and its default is `null`. The rest of the view reads tag values only through these mirrors. The Configuration entries and the auto restart checkbox are the exceptions: they also bind directly to their tags.

| Group | Members |
|---|---|
| Mode | `Mode/Sts_Man`, `Mode/Sts_OOS`, `Mode/Sts_Maint`, `Mode/Sts_Auto` |
| Config | `Cfg_RatedAmps`, `Cfg_Tag`, `Cfg_Desc`, `Cfg_FbkTime`, `Cfg_RestartDly`, `Cfg_MaxStartsHr`, `Cfg_AutoRestart` |
| Values | `Val_Current`, `Val_LoadPct` |
| Alarms | `Alm_FailStart/Sts_Active`, `Alm_FailStart/Sts_Unack`, `Alm_FailStart/Cfg_Priority`, `Alm_FailStop/Sts_Active`, `Alm_FailStop/Sts_Unack`, `Alm_FailStop/Cfg_Priority`, `Alm_Uncmd/Sts_Active`, `Alm_Uncmd/Sts_Unack`, `Alm_Uncmd/Cfg_Priority`, `Alm_EStop/Sts_Active`, `Alm_EStop/Sts_Unack`, `Alm_EStop/Cfg_Priority`, `Alm_IntlkTrip/Sts_Active`, `Alm_IntlkTrip/Sts_Unack`, `Alm_IntlkTrip/Cfg_Priority`, `Alm_ExcessStarts/Sts_Active`, `Alm_ExcessStarts/Sts_Unack`, `Alm_ExcessStarts/Cfg_Priority`, `Alm_OL/Sts_Active`, `Alm_OL/Sts_Unack`, `Alm_OL/Cfg_Priority`, `Alm_HiCurrent/Sts_Active`, `Alm_HiCurrent/Sts_Unack`, `Alm_HiCurrent/Cfg_Priority`, `Alm_HiCurrent/Cfg_Lim` |
| Runtime | `Run/Val_RunHrs`, `Run/Val_Starts`, `Run/Val_StartsLastHr`, `Run/Val_HrsSinceMaint`, `Run/Sts_MaintDue` |
| Status / other | `Sts_Avail`, `Sts_Intlk`, `Sts_Local`, `Sts_NotPerm`, `Sts_NE107`, `Sts_Tripped`, `Sts_Fault`, `Sts_Starting`, `Sts_Stopping`, `Sts_Running`, `Sts_Stopped`, `Sts_Sim`, `Sim_En` |

### Component-level custom properties

None.

### Session, page and message payloads

- `session.props.auth.user.roles`: read by `custom.level` (transform `efc.ui.level`).
- `session.props.auth.user.userName`: read by `efc.ui._audit` (not bound in this view).
- `session.custom.efcDw[pageId]`: holds only the page's default dock view, written by `efc.ui.setDefaultDock` in the screen's onStartup (not in this file) and read by `efc.ui.closeDynamic` in the header. `openDynamic` writes no session value; it calls `system.perspective.alterDock` and `openDock` on `dw_Right`.
- `page.props.pageId`: read by `efc.ui._state` to key `efcDw`.
- No message handlers. No `customMethods`.

## Bindings reference

Total: **144 bindings**: 57 at view root (1 `property` binding with a transform, plus 56 tag mirrors) and 88 on components. Types: 84 `expr`, 60 `tag`, 1 `property`. `params.tagPath` and `params.tType` have `paramDirection` only. Embedded-view `params.*` values and `position.basis` are component bindings and are counted in the 88.

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
| root/Banner | `props.style.classes` | expr | `if({view.custom.m_Sts_Tripped}, 'State/Fault', if({view.custom.m_Sts_Fault}, 'State/Fault', if({view.custom.m_Sts_Starting}, 'State/Transition', if({view.custom.m_Sts_Stopping}, 'State/Transition', if({view.custom.m_Sts_Running}, 'State/Running', if({view.custom.m_Sts_Stopped}, 'State/Stopped', 'State/Unknown'))))))` | CSS class(es) selected by state |
| root/Banner/State | `props.text` | expr | `if({view.custom.m_Sts_Tripped}, 'TRIPPED', if({view.custom.m_Sts_Fault}, 'FAULT', if({view.custom.m_Sts_Starting}, 'STARTING', if({view.custom.m_Sts_Stopping}, 'STOPPING', if({view.custom.m_Sts_Running}, 'RUNNING', if({view.custom.m_Sts_Stopped}, 'STOPPED', 'UNKNOWN'))))))` | Text content |
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
| root/Commands/Body/Buttons/B3 | `position.display` | expr | `{view.custom.level} >= 2` | Shown while expression is true |
| root/Commands/Body/Buttons/B3 | `props.enabled` | expr | `{view.custom.m_Mode_Sts_Maint} && {view.custom.m_Sts_Avail} && !{view.custom.m_Sts_Intlk} && !{view.custom.m_Sts_Local} && !{view.custom.m_Sts_NotPerm}` | Enabled while expression is true |

### `root/Values`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Values/Body/Cur/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Current}, '#,##0.0')` | Text content |
| root/Values/Body/Cur/EU | `props.text` | expr | `'A'` | Text content |
| root/Values/Body/Rated/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_RatedAmps}, '#,##0')` | Text content |
| root/Values/Body/Rated/EU | `props.text` | expr | `'A'` | Text content |
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
| root/Alarms/Body/None | `position.display` | expr | `!({view.custom.m_Alm_FailStart_Sts_Active} \|\| {view.custom.m_Alm_FailStop_Sts_Active} \|\| {view.custom.m_Alm_Uncmd_Sts_Active} \|\| {view.custom.m_Alm_EStop_Sts_Active} \|\| {view.custom.m_Alm_IntlkTrip_Sts_Active} \|\| {view.custom.m_Alm_ExcessStarts_Sts_Active} \|\| {view.custom.m_Alm_OL_Sts_Active} \|\| {view.custom.m_Alm_HiCurrent_Sts_Active})` | Shown while expression is true |
| root/Alarms/Body/List/A0 | `props.style.classes` | expr | `if({view.custom.m_Alm_FailStart_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_FailStart_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_FailStart_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_FailStart_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A1 | `props.style.classes` | expr | `if({view.custom.m_Alm_FailStop_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_FailStop_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_FailStop_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_FailStop_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A2 | `props.style.classes` | expr | `if({view.custom.m_Alm_Uncmd_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_Uncmd_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_Uncmd_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_Uncmd_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A3 | `props.style.classes` | expr | `if({view.custom.m_Alm_EStop_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_EStop_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_EStop_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_EStop_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A4 | `props.style.classes` | expr | `if({view.custom.m_Alm_IntlkTrip_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_IntlkTrip_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_IntlkTrip_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_IntlkTrip_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A5 | `props.style.classes` | expr | `if({view.custom.m_Alm_ExcessStarts_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_ExcessStarts_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_ExcessStarts_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_ExcessStarts_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A6 | `props.style.classes` | expr | `if({view.custom.m_Alm_OL_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_OL_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_OL_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_OL_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A7 | `props.style.classes` | expr | `if({view.custom.m_Alm_HiCurrent_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_HiCurrent_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_HiCurrent_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_HiCurrent_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
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
| root/Configuration/Body/R0/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_FbkTime} / 1000, '#,##0.###')` | Text content |
| root/Configuration/Body/R0/EU | `props.text` | expr | `'s'` | Text content |
| root/Configuration/Body/E0 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E0/Entry | `props.value` | expr | `{view.custom.m_Cfg_FbkTime} / 1000` | Value in seconds (the PLC TIME is in milliseconds) |
| root/Configuration/Body/E0/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: efc.ui.cmd(self, 'Cfg_FbkTime', int(round(currentValue.value * 1000)), 4, audit=True)` | Edit written as milliseconds, Engineer, audited |
| root/Configuration/Body/E0/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R1 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R1/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_RestartDly} / 1000, '#,##0.###')` | Text content |
| root/Configuration/Body/R1/EU | `props.text` | expr | `'s'` | Text content |
| root/Configuration/Body/E1 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E1/Entry | `props.value` | expr | `{view.custom.m_Cfg_RestartDly} / 1000` | Value in seconds (the PLC TIME is in milliseconds) |
| root/Configuration/Body/E1/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: efc.ui.cmd(self, 'Cfg_RestartDly', int(round(currentValue.value * 1000)), 4, audit=True)` | Edit written as milliseconds, Engineer, audited |
| root/Configuration/Body/E1/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R2 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R2/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_RatedAmps}, '#,##0.###')` | Text content |
| root/Configuration/Body/R2/EU | `props.text` | expr | `'A'` | Text content |
| root/Configuration/Body/E2 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E2/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_RatedAmps` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E2/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R3 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R3/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_MaxStartsHr}, '#,##0.###')` | Text content |
| root/Configuration/Body/R3/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E3 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E3/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_MaxStartsHr` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E3/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R4 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R4/Val | `props.text` | expr | `if({view.custom.m_Cfg_AutoRestart}, 'Yes', 'No')` | Text content |
| root/Configuration/Body/C4 | `props.selected` | tag (indirect) | tag `{0}/Cfg_AutoRestart` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/C4 | `props.enabled` | expr | `{view.custom.level} >= 4` | Enabled while expression is true |
| root/Configuration/Body/C4 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/R5 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R5/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_HiCurrent_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Configuration/Body/R5/EU | `props.text` | expr | `'A'` | Text content |
| root/Configuration/Body/E5 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E5/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_HiCurrent/Cfg_Lim` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E5/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |

## Scripts reference

Total: **20 scripts**: 17 event scripts (11 `component.onActionPerformed`, 6 `dom` events: 1 `onClick` and the 5 JOG events) and 1 transform script (`custom.level`). 2 property-change `onChange` scripts (`props.value` of the TIME entries, see the end of the list). No `customMethods`, no `messageHandlers`.

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
	efc.ui.cmd(self, 'Cmd_Start', True, 1)
```

7. **`root/Commands/Body/Buttons/B1`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_Stop', True, 1)
```

8. **`root/Commands/Body/Buttons/B2`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_Reset', True, 1)
```

9. **`root/Commands/Body/Buttons/B3`** (JOG): five `events.dom` scripts, scope G. Press writes TRUE (`onMouseDown`, `onTouchStart`), only while the button is enabled, because DOM events can still fire on a disabled button; release always writes FALSE (`onMouseUp`, `onMouseLeave`, `onTouchEnd`).

```python
	# onMouseDown, onTouchStart
	if self.props.enabled:
		efc.ui.cmd(self, 'Cmd_Jog', True, 2)
```

```python
	# onMouseUp, onMouseLeave, onTouchEnd
	efc.ui.cmd(self, 'Cmd_Jog', False, 2)
```

10. **`root/Alarms/Body/Ack`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.ackAll(self, ['Alm_FailStart', 'Alm_FailStop', 'Alm_Uncmd', 'Alm_EStop', 'Alm_IntlkTrip', 'Alm_ExcessStarts', 'Alm_OL', 'Alm_HiCurrent'])
```

11. **`root/Maintenance/Body/Buttons/ResetMaint`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Run/Cmd_ResetMaint', True, 2, audit=True)
```

12. **`root/Maintenance/Body/Buttons/Sim`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Sim_En', not self.view.custom.m_Sim_En, 2, audit=True)
```

13. **`root/Configuration/Header`**: `events.dom.onClick`, scope G.

```python
	self.view.custom.open_Configuration = not self.view.custom.open_Configuration
```

14. **transform on `(view root)` `custom.level`**: `custom.level` binding, `property` source `session.props.auth.user.roles`.

```python
	return efc.ui.level(value)
```

15. **`root/Configuration/Body/E0/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		efc.ui.cmd(self, 'Cfg_FbkTime', int(round(currentValue.value * 1000)), 4, audit=True)
```

16. **`root/Configuration/Body/E1/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		efc.ui.cmd(self, 'Cfg_RestartDly', int(round(currentValue.value * 1000)), 4, audit=True)
```

### Explanation of each handler

| Handler | Action | Writes | Role check | Audit |
|---|---|---|---|---|
| `Header/Close` | `efc.ui.closeDynamic` restores the default dock view or closes the dock | none | none | no |
| `Mode/Auto` | `efc.ui.cmd(... 'Mode/Cmd_Auto', True, 1)` | `Mode/Cmd_Auto` | level 1 | no |
| `Mode/Man` | `efc.ui.cmd(... 'Mode/Cmd_Man', True, 1)` | `Mode/Cmd_Man` | level 1 | no |
| `Mode/Maint` | `efc.ui.cmd(... 'Mode/Cmd_Maint', True, 2)` | `Mode/Cmd_Maint` | level 2 | yes |
| `Mode/OOS` | `efc.ui.cmd(... 'Mode/Cmd_OOS', True, 2)` | `Mode/Cmd_OOS` | level 2 | yes |
| `Commands/B0` (START) | `efc.ui.cmd(... 'Cmd_Start', True, 1)` | `Cmd_Start` | level 1 | no |
| `Commands/B1` (STOP) | `efc.ui.cmd(... 'Cmd_Stop', True, 1)` | `Cmd_Stop` | level 1 | no |
| `Commands/B2` (RESET) | `efc.ui.cmd(... 'Cmd_Reset', True, 1)` | `Cmd_Reset` | level 1 | no |
| `Commands/B3` (JOG) | `efc.ui.cmd(... 'Cmd_Jog', True, 2)` on mouse down / touch start; `efc.ui.cmd(... 'Cmd_Jog', False, 2)` on mouse up / mouse leave / touch end | `Cmd_Jog` (held) | level 2 | no |
| `Alarms/Ack` | `efc.ui.ackAll` on the eight alarms | `Alm_*/Cmd_Ack` where unacked | level 1 | no |
| `Maintenance/ResetMaint` | `efc.ui.cmd(... 'Run/Cmd_ResetMaint', True, 2)` | `Run/Cmd_ResetMaint` | level 2 | yes |
| `Maintenance/Sim` (SIMULATE) | `efc.ui.cmd(... 'Sim_En', not m_Sim_En, 2)` | `Sim_En` (toggle) | level 2 | yes |
| `Configuration/Header` (dom click) | toggles `open_Configuration` | none | none | no |
| `Configuration/Body/E0` (`Cfg_FbkTime` entry, onChange) | `efc.ui.cmd(... 'Cfg_FbkTime', int(round(value * 1000)), 4)`, only when `origin == 'Browser'` | `Cfg_FbkTime` (milliseconds) | level 4 | yes
| `Configuration/Body/E1` (`Cfg_RestartDly` entry, onChange) | `efc.ui.cmd(... 'Cfg_RestartDly', int(round(value * 1000)), 4)`, only when `origin == 'Browser'` | `Cfg_RestartDly` (milliseconds) | level 4 | yes

`efc.ui.cmd` writes `view.params.tagPath + '/' + member` with `system.tag.writeBlocking` only when `userLevel >= minLevel`. The Mode buttons, the command buttons, ACK and the maintenance buttons therefore use the level check. The two TIME entries use the level check (level 4); the other Configuration entries and the auto restart checkbox do not, because they are bindings.

### Library functions used (`projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.level(roles)`**: highest index of the role in `['Guest','Operator','Maintenance','Supervisor','Engineer','Admin']`, or 0. Bound to `custom.level`.
- **`efc.ui.closeDynamic(component)`**: loads the page's stored `default` view and params (`session.custom.efcDw[pageId]`) back into the `dw_Right` dock, or closes the dock if there is no default. Writes no tags.
- **`efc.ui.cmd(component, member, value, minLevel, audit)`**: the role-checked write described above. It writes the value once with `writeBlocking` and does not write it back. One-shot members depend on the PLC behaviour; `Cmd_Jog` is written TRUE on press and FALSE on release. Audits when `audit=True`.
- **`efc.ui.ackAll(component, alarms)`**: reads `<alarm>/Sts_Unack` for the listed alarms, then writes `<alarm>/Cmd_Ack` = True for those that are true, at level 1 and above.
- **`efc.ui.openDynamic`** (called from the template, not from this view): maps the template's type to a window and loads it into the `dw_Right` dock.
- **`efc.ui.bypass` / `unbypass`**: exist in the module but are not called from this view. Interlock bypass is handled in the embedded `IntlkList` views, which are not in this file.

## Tag members used

All paths are relative to `tagPath`. Types come from `types/PCLib_Members.csv` (nested types: `Mode` = T_Mode, `Run` = T_RunTime, `Alm_*` = T_Alarm, except `Alm_HiCurrent` which is T_AlmLim, `Perm` and `Intlk` = T_Intlk). Trend pens are read by the embedded trend part.

| Member | Access | Data type | Meaning |
|---|---|---|---|
| `Mode/Sts_Man` | read | BOOL | In Manual (commanded by operator) - MTP Operator. |
| `Sts_Avail` | read | BOOL | Available to Auto/program control. |
| `Sts_Intlk` | read | BOOL | Interlock not healthy. |
| `Sts_Local` | read | BOOL | In local control. |
| `Sts_NotPerm` | read | BOOL | Permissive not healthy. |
| `Val_Current` | read | REAL | Motor current (A). Also read by a trend pen. |
| `Cfg_RatedAmps` | read/write | REAL | Motor nameplate full-load current (A). |
| `Val_LoadPct` | read | REAL | Load (% of Cfg_RatedAmps). |
| `Sts_NE107` | read | INT | NAMUR NE107 status: 0=Good 1=Failure (F) 2=Function check (C) 3=Out of specification (S) 4=Maintenance required (M). |
| `Cfg_Tag` | read | STRING[20] | Equipment / instrument tag, e.g. FT-101. |
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate. |
| `Sts_Tripped` | read | BOOL | Tripped - reset required. |
| `Sts_Fault` | read | BOOL | Any fault present. |
| `Sts_Starting` | read | BOOL | Start commanded, waiting for feedback. |
| `Sts_Stopping` | read | BOOL | Stop commanded, waiting for feedback. |
| `Sts_Running` | read | BOOL | Running (feedback confirmed). Also read by a trend pen. |
| `Sts_Stopped` | read | BOOL | Stopped (feedback confirmed). |
| `Sts_Sim` | read | BOOL | Simulation active. |
| `Mode/Sts_OOS` | read | BOOL | Out of service - MTP Offline. |
| `Mode/Sts_Maint` | read | BOOL | In Maintenance. |
| `Mode/Sts_Auto` | read | BOOL | In Automatic (commanded by owner) - MTP Automatic. |
| `Alm_FailStart/Sts_Active` | read | BOOL | Alarm active (after delays and latch). |
| `Alm_FailStart/Sts_Unack` | read | BOOL | Alarm unacknowledged. |
| `Alm_FailStart/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low. |
| `Alm_FailStop/Sts_Active` | read | BOOL | Alarm active (after delays and latch). |
| `Alm_FailStop/Sts_Unack` | read | BOOL | Alarm unacknowledged. |
| `Alm_FailStop/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low. |
| `Alm_Uncmd/Sts_Active` | read | BOOL | Alarm active (after delays and latch). |
| `Alm_Uncmd/Sts_Unack` | read | BOOL | Alarm unacknowledged. |
| `Alm_Uncmd/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low. |
| `Alm_EStop/Sts_Active` | read | BOOL | Alarm active (after delays and latch). |
| `Alm_EStop/Sts_Unack` | read | BOOL | Alarm unacknowledged. |
| `Alm_EStop/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low. |
| `Alm_IntlkTrip/Sts_Active` | read | BOOL | Alarm active (after delays and latch). |
| `Alm_IntlkTrip/Sts_Unack` | read | BOOL | Alarm unacknowledged. |
| `Alm_IntlkTrip/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low. |
| `Alm_ExcessStarts/Sts_Active` | read | BOOL | Alarm active (after delays and latch). |
| `Alm_ExcessStarts/Sts_Unack` | read | BOOL | Alarm unacknowledged. |
| `Alm_ExcessStarts/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low. |
| `Alm_OL/Sts_Active` | read | BOOL | Alarm active (after delays and latch). |
| `Alm_OL/Sts_Unack` | read | BOOL | Alarm unacknowledged. |
| `Alm_OL/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low. |
| `Alm_HiCurrent/Sts_Active` | read | BOOL | Alarm active (after delays and latch). |
| `Alm_HiCurrent/Sts_Unack` | read | BOOL | Alarm unacknowledged. |
| `Alm_HiCurrent/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low. |
| `Run/Val_RunHrs` | read | REAL | Total run hours (display). |
| `Run/Val_Starts` | read | UDINT | Total starts / cycles. |
| `Run/Val_StartsLastHr` | read | INT | Starts in the last 60 min (rolling). |
| `Run/Val_HrsSinceMaint` | read | REAL | Run hours since last maintenance reset. |
| `Run/Sts_MaintDue` | read | BOOL | Maintenance due. |
| `Sim_En` | read / write (toggle) | BOOL | Simulation: ignore field I/O, logic generates feedback. |
| `Cfg_FbkTime` | read (shown as value / 1000); write value * 1000 via `efc.ui.cmd` | TIME | Time allowed for run feedback after start/stop. |
| `Cfg_RestartDly` | read (shown as value / 1000); write value * 1000 via `efc.ui.cmd` | TIME | Minimum stopped time before restart. |
| `Cfg_MaxStartsHr` | read/write | INT | Maximum starts per hour, 0 = no limit. |
| `Alm_HiCurrent/Cfg_Lim` | read/write | REAL | Alarm limit (EU) - from rationalisation / master alarm database. |
| `Cfg_AutoRestart` | read/write | BOOL | Auto mode restarts after power loss / interlock clears. |
| `Perm` | read | T_Intlk | Passed as tagPath to the embedded `Templates/Dynamic Window/Parts/IntlkList` view |
| `Intlk` | read | T_Intlk | Passed as tagPath to the embedded `Templates/Dynamic Window/Parts/IntlkList` view |
| `Mode/Cmd_Auto` | write | BOOL | Operator request Automatic (one-shot). |
| `Mode/Cmd_Man` | write | BOOL | Operator request Manual (one-shot). |
| `Mode/Cmd_Maint` | write | BOOL | Request Maintenance (one-shot). |
| `Mode/Cmd_OOS` | write | BOOL | Request Out-of-Service (one-shot). |
| `Cmd_Start` | write | BOOL | Operator start (one-shot). |
| `Cmd_Stop` | write | BOOL | Operator stop (one-shot). |
| `Cmd_Reset` | write | BOOL | Fault / trip reset (one-shot). |
| `Cmd_Jog` | write | BOOL | Maintenance jog (maintained, Maint mode only). |
| `Alm_FailStart/Cmd_Ack` | write | BOOL | Operator acknowledge (one-shot). Written by ackAll only when the alarm is unacknowledged. |
| `Alm_FailStop/Cmd_Ack` | write | BOOL | Operator acknowledge (one-shot). Written by ackAll only when the alarm is unacknowledged. |
| `Alm_Uncmd/Cmd_Ack` | write | BOOL | Operator acknowledge (one-shot). Written by ackAll only when the alarm is unacknowledged. |
| `Alm_EStop/Cmd_Ack` | write | BOOL | Operator acknowledge (one-shot). Written by ackAll only when the alarm is unacknowledged. |
| `Alm_IntlkTrip/Cmd_Ack` | write | BOOL | Operator acknowledge (one-shot). Written by ackAll only when the alarm is unacknowledged. |
| `Alm_ExcessStarts/Cmd_Ack` | write | BOOL | Operator acknowledge (one-shot). Written by ackAll only when the alarm is unacknowledged. |
| `Alm_OL/Cmd_Ack` | write | BOOL | Operator acknowledge (one-shot). Written by ackAll only when the alarm is unacknowledged. |
| `Alm_HiCurrent/Cmd_Ack` | write | BOOL | Operator acknowledge (one-shot). Written by ackAll only when the alarm is unacknowledged. |
| `Run/Cmd_ResetMaint` | write | BOOL | Reset hours-since-maintenance (one-shot). |

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
        - `B3` (ia.input.button)
      - `Hint` (ia.display.label)
  - `Values` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
    - `Body` (ia.container.flex)
      - `Cur` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Rated` (ia.container.flex)
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
        - `A7` (ia.display.label)
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
      - `C4` (ia.input.checkbox)
      - `R5` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `E5` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
```

## Notes and open questions

- **START is not blocked by a trip or fault.** START's enable does not include `Sts_Tripped` or `Sts_Fault`. The same is true of the discrete dock's OPEN and CLOSE.
- **STOP and RESET have no enable.** They are clickable at level 1 and above in any mode and state.
- **Restart countdown and readiness are not shown.** `Sts_RestartLeft`, `Sts_Ready` and `Sts_State` are not used. `Cfg_NoFbk` is not shown or editable here.
- **Zero means no limit, and the dock does not say so.** `Cfg_MaxStartsHr` is 0 for no limit (PCLib comment). The Configuration row shows the raw number with no unit and no label for 0.
- **High current limit is an alarm setpoint.** `Alm_HiCurrent/Cfg_Lim` is edited at level 4 in the Configuration section. It has no audit and no script check.
