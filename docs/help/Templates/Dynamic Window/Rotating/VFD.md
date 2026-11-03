# Templates/Dynamic Window/Rotating/VFD

Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/Dynamic Window/Rotating/VFD/view.json`
Opened from: the VFD template (`Rotating/VFD`; see [Rotating VFD template](../../Rotating/VFD.md)) through `efc.ui.openDynamic`. Dynamic window id `dw_VFD`.

## Overview

The operator and maintenance dynamic window for a variable frequency drive (T_VFD). It opens in the page's right dock (`dw_Right`), not as a popup. It shows state, interlock and permissive detail, mode, start/stop/jog and direction commands, a speed reference, drive values, alarms, a trend, maintenance counters and configuration.

- **Default size:** 400 x 860 (`props.defaultSize`). The root is a scrolling column.
- **Parameters:** `tagPath` (the T_VFD instance) and `tType` (default `T_VFD`).
- **How it is opened:** the template's single click runs `efc.ui.openDynamic(self)`. The template's `tType` is `T_VFD` and its `dockId` is empty, so `efc.ui.openDynamic` maps it to `dw_VFD` and loads `Templates/Dynamic Window/Rotating/VFD` into the page's `dw_Right` dock with params `{tagPath: ...}` (`system.perspective.alterDock`) and opens the dock (`system.perspective.openDock`). Before that it runs `efc.ui.sizeDock(self)`, which sets the dock size to 37.04 vh (400 px at 1080p, 800 px at 4K, decision 33). `efc.ui.openDynamic` passes only `tagPath` (and `model` if present). **`tType` is never passed**, so the dock always runs with its default `T_VFD`. Nothing in this view uses `tType`.
- **Generated view:** this view is written by `generator/docks/build_docks.py` (function `vfd()`, which uses the shared `motor_like()` layout). Change the generator, not `view.json`, or the next build overwrites the edit.
- **How it closes:** the header `X` runs `efc.ui.closeDynamic(self)`, which puts the page's default view back in the `dw_Right` dock (set by `efc.ui.setDefaultDock` in the screen's onStartup), or closes the dock if the page has no default. That startup script is not in this view.

## How it operates

**Header.** Shows `Cfg_Tag` (large) and `Cfg_Desc`.

**Banner.** The state label is chosen by priority: `Sts_Tripped` (TRIPPED), `Sts_Fault` (FAULT), `Sts_Starting` (STARTING), `Sts_Stopping` (STOPPING), `Sts_Running` (RUNNING), `Sts_Stopped` (STOPPED), else UNKNOWN. The style class follows the same order (`State/Fault`, `State/Fault`, `State/Transition`, `State/Transition`, `State/Running`, `State/Stopped`, `State/Unknown`). Four badges appear when their flag is true: SIM (`Sts_Sim`), LOCAL (`Sts_Local`), INTLK (`Sts_Intlk`), NOT PERM (`Sts_NotPerm`).

**Mode.** The mode text shows the highest of OOS, MAINT, MAN, else AUTO. The four toggle buttons highlight the active mode. All four are always visible. AUTO and MAN show a lock icon and the tooltip "Requires Operator access" below level 1; MAINT and OOS show a lock and "Requires Maintenance access" below level 2. None of the four has an `enabled` binding, so each is always clickable. A press below a button's level is refused by `efc.ui.cmd`, which logs a warning and opens the AccessDenied popup (see [AccessDenied](../Parts/AccessDenied.md)); nothing is written. Each writes a one-shot `Mode/Cmd_*`. MAINT and OOS are audited.

**Commands** (all levels; the buttons are locked below the level they need). Four buttons:

- `START` (`B0`) writes `Cmd_Start`. Enabled when the user is below Operator (so a press can be refused with the popup) or when all of these are true: `Mode/Sts_Man`, `Sts_Avail`, not `Sts_Intlk`, not `Sts_Local`, not `Sts_NotPerm`. Lock and tooltip "Requires Operator access" below level 1. It does not check `Sts_Running`, `Sts_Stopped`, `Sts_Tripped`, `Sts_Fault` or `Mode/Sts_OOS`.
- `STOP` (`B1`) writes `Cmd_Stop`. It has **no enable condition**. Lock below level 1.
- `RESET` (`B2`) writes `Cmd_Reset`. It has **no enable condition**, so it is clickable outside MAN. Lock below level 1.
- `JOG` (`B3`) is hold-to-jog. Below level 2 it shows a lock and the tooltip "Requires Maintenance access". It writes `Cmd_Jog` TRUE on mouse down or touch start and FALSE on mouse up, mouse leave or touch end (`efc.ui.cmd`, level 2, not audited). The release events pass `notify=False`, so a release below Maintenance is refused without a popup; only the press opens it. It is enabled when the user is below Maintenance or in MAINT: `Mode/Sts_Maint` and the START terms except `Mode/Sts_Man` (available, not interlocked, not LOCAL, not NOT PERM).

A hint line states "Enabled in MAN, available, permitted, not interlocked, not LOCAL. JOG: hold, MAINT mode only". The first part is true for START only; STOP and RESET have no enable.

**Speed and direction.** Both are in the Commands section. The speed entry is shown at level 1 and above only. The direction buttons are always shown when `Cfg_Reversible` is true, and are locked (lock icon, tooltip "Requires Operator access") below level 1.

- The speed entry reads `Cmd_Spd` (REAL) one way; an edit commits through `efc.ui.setValue(self, 'Cmd_Spd', value, 1)` (level re-checked, audited, binding refreshed if refused or failed). It is enabled when `Mode/Sts_Man` and `Sts_Avail` are true. It has no interlock, LOCAL or permissive term. Its unit label is blank.
- The direction row (`Dir`) is shown only when `Cfg_Reversible` is true. `FWD` writes `Cmd_Rev` = False and `REV` writes `Cmd_Rev` = True. Both are enabled when the user is below Operator or when `Mode/Sts_Man` and `Sts_Avail` are true. Neither button shows the current direction (`Sts_Rev` is not bound).

**Values** (all levels). Current (`Val_Current`, A), Rated (`Cfg_RatedAmps`, A), Load (`Val_LoadPct`, %), Diagnostics (NE107 text for `Sts_NE107`: 0 `NE107 OK`, 1 `NE107 F`, 2 `NE107 C`, 3 `NE107 S`, 4 `NE107 M`), Speed ref (`Val_SpdRef`, `Cfg_SpdEU`), Speed (`Val_Spd`, `Cfg_SpdEU`), Torque (`Val_Torque`, %), Power (`Val_Power`, kW). The row `Drive fault code` (`Inp_FaultCode`) is shown only when `Sts_Fault` is true.

**Permissives and interlocks.** Two embedded `Templates/Dynamic Window/Parts/IntlkList` views get `tagPath + '/Perm'` and `tagPath + '/Intlk'`, with titles "Permissives" and "Interlocks". Their content is described in [Parts/IntlkList.md](../Parts/IntlkList.md).

**Alarms** (all levels). Ten rows: fail to start, fail to stop, uncommanded run/stop, E-stop, interlock trip, excess starts, drive fault, drive warning, drive comm fail, speed deviation. A row is coloured when its alarm is active, using the alarm's `Cfg_Priority`: 1 `Critical`, 2 `High`, 3 `Medium`, 4 `Low`, anything else `Medium`. The class adds `/Unacked` or `/Fill`. An inactive but unacknowledged alarm uses `Alarm/Status/ClearedUnacked`. An inactive, acknowledged alarm uses `Text/Caption Text/Color/Muted`. "No active alarms" is shown when none is active. **ACK** (always visible; lock icon below level 1) calls `efc.ui.ackAll` with all ten alarm names. It writes `Cmd_Ack` only for those whose `Sts_Unack` is true. Below Operator `efc.ui.ackAll` writes nothing, logs a warning and opens the AccessDenied popup.

**Trend.** Embeds `Templates/Dynamic Window/Parts/Trend` with pens `Val_Spd`, `Val_SpdRef` and `Val_Current` over the tagPath. The embedded view's `expanded` param starts `false`. It is declared `inout` in `Templates/Dynamic Window/Parts/Trend`, so the Trend part toggles it itself and the value flows back to this embed. The `position.basis` binding (`{this.props.params.expanded}`) then grows the trend from 15.741 vh to 70.370 vh. The expansion is local to the trend and does not widen the dock. See [Parts/Trend.md](../Parts/Trend.md).

**Maintenance** (level 2 and above). Shows run hours, starts, starts in the last hour, hours since maintenance and whether maintenance is due. `RESET MAINT` writes `Run/Cmd_ResetMaint` (audited). `SIMULATE` toggles `Sim_En` (audited).

**Configuration** (level 1 and above, hidden below Operator; collapsible; collapsed by default; the header click toggles `open_Configuration`). Below level 4 each value is a read-only row. At level 4 and above each value is an editable entry that reads its tag one way, with an enable expression of the literal `true`; the row is hidden and the entry shown. The entries are: Feedback time (`Cfg_FbkTime`, s, TIME), Restart delay (`Cfg_RestartDly`, s, TIME), Rated current (`Cfg_RatedAmps`, A), Max starts / hr (`Cfg_MaxStartsHr`), Speed min (`Cfg_SpdMin`), Speed max (`Cfg_SpdMax`), Speed dev limit (`Cfg_SpdDevLim`) and Speed dev time (`Cfg_SpdDevTime`, s, TIME). The TIME members are milliseconds on the PLC: their rows show `member / 1000`, their entries read the mirror `/ 1000`, and `efc.ui.setValue` is called with scale 1000, so `int(round(value * 1000))` is written. "Auto restart" (`Cfg_AutoRestart`) follows the same pattern: below level 4 a read-only row shows `Yes` or `No`; at level 4 and above the row is hidden and a checkbox is shown (enabled at level 4 and above). Every entry and the checkbox commit an edit from a `props.value` (checkbox: `props.selected`) onChange script (only when `origin == 'Browser'`) through `efc.ui.setValue(self, member, value, 4)`, which re-checks level 4, writes and audits old -> new; a refused or failed write refreshes the binding.

**Role checks.** `view.custom.level` comes from the Perspective session (`session.props.auth.securityLevels`) through `efc.ui.level`, which matches the security-level names case-insensitively (site names through `efc.ui.ROLE_ALIASES`). It decides which controls are locked or hidden in the client. `efc.ui.cmd`, `efc.ui.setValue` and `efc.ui.ackAll` re-check the level (`efc.ui.userLevel`, the larger of the security levels and `session.props.auth.user.roles`). Below it they do not write: they log a warning and open the `Parts/AccessDenied` popup (decision 36; see [AccessDenied](../Parts/AccessDenied.md)). Failed writes are logged too. No binding writes a tag: the speed entry and the Configuration entries and checkbox go through `efc.ui.setValue`. Real access control has to be enforced in Perspective security and the PLC logic.

**Audit.** `efc.ui` writes an audit entry (`system.util.audit`, falling back to the logger) for MAINT, OOS, RESET MAINT, SIMULATE, speed changes and every Configuration edit (`EFC set`, old -> new, from `efc.ui.setValue`). It does not audit AUTO, MAN, START, STOP, RESET, JOG, FWD, REV or ACK.

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `""` | T_VFD instance. Every component binding uses `{view.params.tagPath}`. | Set by `efc.ui.openDynamic` from the template's `dwTagPath` (or `tagPath`). Read by bindings and `efc.ui` commands. |
| `tType` | input | `T_VFD` | Declared type. | Not passed by `efc.ui.openDynamic`; not referenced by any binding or script in this view. Always the default. |

Both have `paramDirection: input` and `persistent: true`. No output parameters.

### View-level custom properties (`custom`)

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.level` | `0` | property + script transform | `session.props.auth.securityLevels` → `return efc.ui.level(value)` | Role level 0-5 from `session.props.auth.securityLevels` via `efc.ui.level`. Locks command buttons below the level they need and hides the sections and entries above the user's level (Guest 0, Operator 1, Maintenance 2, Supervisor 3, Engineer 4, Admin 5). |
| `view.custom.open_Configuration` | `false` | none (written by scripts) | none | View-local toggle for the Configuration section. Set by the header click script; not bound to any tag; not persisted. |

#### Tag mirrors (`custom.m_*`)

There are 72 tag-mirror properties. Each `custom.m_<member>` (with `/` replaced by `_`) has an indirect, read-only tag binding to `{view.params.tagPath}/<member>` (`bidirectional: false`, fallback delay 2.5 s), and its default is `null`. The display bindings read tag values through these mirrors. The speed and configuration entries bind their tags directly, one way (see Bindings reference).

| Group | Members |
|---|---|
| Mode | `Mode/Sts_Man`, `Mode/Sts_OOS`, `Mode/Sts_Maint`, `Mode/Sts_Auto` |
| Status / other | `Sts_Avail`, `Sts_Intlk`, `Sts_Local`, `Sts_NotPerm`, `Sts_NE107`, `Sts_Tripped`, `Sts_Fault`, `Sts_Starting`, `Sts_Stopping`, `Sts_Running`, `Sts_Stopped`, `Sts_Sim` |
| Values | `Val_Current`, `Val_LoadPct`, `Val_SpdRef`, `Val_Spd`, `Val_Torque`, `Val_Power` |
| Config | `Cfg_RatedAmps`, `Cfg_Tag`, `Cfg_Desc`, `Cfg_Reversible`, `Cfg_SpdEU`, `Cfg_FbkTime`, `Cfg_RestartDly`, `Cfg_MaxStartsHr`, `Cfg_SpdMin`, `Cfg_SpdMax`, `Cfg_SpdDevLim`, `Cfg_SpdDevTime`, `Cfg_AutoRestart` |
| Inputs | `Inp_FaultCode` |
| Alarms | `Alm_FailStart/Sts_Active`, `Alm_FailStart/Sts_Unack`, `Alm_FailStart/Cfg_Priority`, `Alm_FailStop/Sts_Active`, `Alm_FailStop/Sts_Unack`, `Alm_FailStop/Cfg_Priority`, `Alm_Uncmd/Sts_Active`, `Alm_Uncmd/Sts_Unack`, `Alm_Uncmd/Cfg_Priority`, `Alm_EStop/Sts_Active`, `Alm_EStop/Sts_Unack`, `Alm_EStop/Cfg_Priority`, `Alm_IntlkTrip/Sts_Active`, `Alm_IntlkTrip/Sts_Unack`, `Alm_IntlkTrip/Cfg_Priority`, `Alm_ExcessStarts/Sts_Active`, `Alm_ExcessStarts/Sts_Unack`, `Alm_ExcessStarts/Cfg_Priority`, `Alm_DrvFault/Sts_Active`, `Alm_DrvFault/Sts_Unack`, `Alm_DrvFault/Cfg_Priority`, `Alm_DrvWarn/Sts_Active`, `Alm_DrvWarn/Sts_Unack`, `Alm_DrvWarn/Cfg_Priority`, `Alm_CommFail/Sts_Active`, `Alm_CommFail/Sts_Unack`, `Alm_CommFail/Cfg_Priority`, `Alm_SpdDev/Sts_Active`, `Alm_SpdDev/Sts_Unack`, `Alm_SpdDev/Cfg_Priority` |
| Runtime | `Run/Val_RunHrs`, `Run/Val_Starts`, `Run/Val_StartsLastHr`, `Run/Val_HrsSinceMaint`, `Run/Sts_MaintDue` |
| Other | `Sim_En` |


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

Total: **210 bindings**: 73 at view root (all `custom.*`, including 1 `property` binding with a transform) and 137 on components. Types: 130 `expr`, 79 `tag`, 1 `property`. `params.tagPath` and `params.tType` have `paramDirection` only. Embedded-view `params.*` values and `position.basis` are component bindings and counted in the 137.

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
| root/Mode/Body/Buttons/Auto | `props.image.icon.path` | expr | `if({view.custom.level} < 1, 'material/lock', '')` | Shows a lock icon on the button while the user is below Operator |
| root/Mode/Body/Buttons/Auto | `meta.tooltip.enabled` | expr | `{view.custom.level} < 1` | Tooltip "Requires Operator access" shown while expression is true |
| root/Mode/Body/Buttons/Auto | `props.style.classes` | expr | `if({view.custom.m_Mode_Sts_Auto}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |
| root/Mode/Body/Buttons/Man | `props.image.icon.path` | expr | `if({view.custom.level} < 1, 'material/lock', '')` | Shows a lock icon on the button while the user is below Operator |
| root/Mode/Body/Buttons/Man | `meta.tooltip.enabled` | expr | `{view.custom.level} < 1` | Tooltip "Requires Operator access" shown while expression is true |
| root/Mode/Body/Buttons/Man | `props.style.classes` | expr | `if({view.custom.m_Mode_Sts_Man}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |
| root/Mode/Body/Buttons/Maint | `props.image.icon.path` | expr | `if({view.custom.level} < 2, 'material/lock', '')` | Shows a lock icon on the button while the user is below Maintenance |
| root/Mode/Body/Buttons/Maint | `meta.tooltip.enabled` | expr | `{view.custom.level} < 2` | Tooltip "Requires Maintenance access" shown while expression is true |
| root/Mode/Body/Buttons/Maint | `props.style.classes` | expr | `if({view.custom.m_Mode_Sts_Maint}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |
| root/Mode/Body/Buttons/OOS | `props.image.icon.path` | expr | `if({view.custom.level} < 2, 'material/lock', '')` | Shows a lock icon on the button while the user is below Maintenance |
| root/Mode/Body/Buttons/OOS | `meta.tooltip.enabled` | expr | `{view.custom.level} < 2` | Tooltip "Requires Maintenance access" shown while expression is true |
| root/Mode/Body/Buttons/OOS | `props.style.classes` | expr | `if({view.custom.m_Mode_Sts_OOS}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |

### `root/Commands`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Commands/Body/Buttons/B0 | `props.image.icon.path` | expr | `if({view.custom.level} < 1, 'material/lock', '')` | Shows a lock icon on the button while the user is below Operator |
| root/Commands/Body/Buttons/B0 | `meta.tooltip.enabled` | expr | `{view.custom.level} < 1` | Tooltip "Requires Operator access" shown while expression is true |
| root/Commands/Body/Buttons/B0 | `props.enabled` | expr | `({view.custom.level} < 1) || ({view.custom.m_Mode_Sts_Man} && {view.custom.m_Sts_Avail} && !{view.custom.m_Sts_Intlk} && !{view.custom.m_Sts_Local} && !{view.custom.m_Sts_NotPerm})` | Enabled while expression is true. Below the needed level the button is enabled so the press reaches `efc.ui` (decision 36). |
| root/Commands/Body/Buttons/B1 | `props.image.icon.path` | expr | `if({view.custom.level} < 1, 'material/lock', '')` | Shows a lock icon on the button while the user is below Operator |
| root/Commands/Body/Buttons/B1 | `meta.tooltip.enabled` | expr | `{view.custom.level} < 1` | Tooltip "Requires Operator access" shown while expression is true |
| root/Commands/Body/Buttons/B2 | `props.image.icon.path` | expr | `if({view.custom.level} < 1, 'material/lock', '')` | Shows a lock icon on the button while the user is below Operator |
| root/Commands/Body/Buttons/B2 | `meta.tooltip.enabled` | expr | `{view.custom.level} < 1` | Tooltip "Requires Operator access" shown while expression is true |
| root/Commands/Body/Buttons/B3 | `props.image.icon.path` | expr | `if({view.custom.level} < 2, 'material/lock', '')` | Shows a lock icon on the button while the user is below Maintenance |
| root/Commands/Body/Buttons/B3 | `meta.tooltip.enabled` | expr | `{view.custom.level} < 2` | Tooltip "Requires Maintenance access" shown while expression is true |
| root/Commands/Body/Buttons/B3 | `props.enabled` | expr | `({view.custom.level} < 2) || ({view.custom.m_Mode_Sts_Maint} && {view.custom.m_Sts_Avail} && !{view.custom.m_Sts_Intlk} && !{view.custom.m_Sts_Local} && !{view.custom.m_Sts_NotPerm})` | Enabled while expression is true. Below the needed level the button is enabled so the press reaches `efc.ui` (decision 36). |
| root/Commands/Body/Spd | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Commands/Body/Spd/Entry | `props.value` | tag (indirect) | tag `{0}/Cmd_Spd`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Commands/Body/Spd/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cmd_Spd', currentValue.value, 1): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 1, audited; a refused or failed write refreshes the binding |
| root/Commands/Body/Spd/Entry | `props.enabled` | expr | `{view.custom.m_Mode_Sts_Man} && {view.custom.m_Sts_Avail}` | Enabled while expression is true |
| root/Commands/Body/Dir | `position.display` | expr | `{view.custom.m_Cfg_Reversible}` | Shown while expression is true |
| root/Commands/Body/Dir/Fwd | `props.enabled` | expr | `({view.custom.level} < 1) || ({view.custom.m_Mode_Sts_Man} && {view.custom.m_Sts_Avail})` | Enabled while expression is true. Below the needed level the button is enabled so the press reaches `efc.ui` (decision 36). |
| root/Commands/Body/Dir/Fwd | `props.image.icon.path` | expr | `if({view.custom.level} < 1, 'material/lock', '')` | Shows a lock icon on the button while the user is below Operator |
| root/Commands/Body/Dir/Fwd | `meta.tooltip.enabled` | expr | `{view.custom.level} < 1` | Tooltip "Requires Operator access" shown while expression is true |
| root/Commands/Body/Dir/Rev | `props.enabled` | expr | `({view.custom.level} < 1) || ({view.custom.m_Mode_Sts_Man} && {view.custom.m_Sts_Avail})` | Enabled while expression is true. Below the needed level the button is enabled so the press reaches `efc.ui` (decision 36). |
| root/Commands/Body/Dir/Rev | `props.image.icon.path` | expr | `if({view.custom.level} < 1, 'material/lock', '')` | Shows a lock icon on the button while the user is below Operator |
| root/Commands/Body/Dir/Rev | `meta.tooltip.enabled` | expr | `{view.custom.level} < 1` | Tooltip "Requires Operator access" shown while expression is true |

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
| root/Values/Body/Ref/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_SpdRef}, '#,##0.0')` | Text content |
| root/Values/Body/Ref/EU | `props.text` | expr | `{view.custom.m_Cfg_SpdEU}` | Text content |
| root/Values/Body/Spd/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Spd}, '#,##0.0')` | Text content |
| root/Values/Body/Spd/EU | `props.text` | expr | `{view.custom.m_Cfg_SpdEU}` | Text content |
| root/Values/Body/Trq/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Torque}, '#,##0.0')` | Text content |
| root/Values/Body/Trq/EU | `props.text` | expr | `'%'` | Text content |
| root/Values/Body/Pwr/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Power}, '#,##0.0')` | Text content |
| root/Values/Body/Pwr/EU | `props.text` | expr | `'kW'` | Text content |
| root/Values/Body/Code | `position.display` | expr | `{view.custom.m_Sts_Fault}` | Shown while expression is true |
| root/Values/Body/Code/Val | `props.text` | expr | `numberFormat({view.custom.m_Inp_FaultCode}, '0')` | Text content |

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
| root/Alarms/Body/None | `position.display` | expr | `!({view.custom.m_Alm_FailStart_Sts_Active} \|\| {view.custom.m_Alm_FailStop_Sts_Active} \|\| {view.custom.m_Alm_Uncmd_Sts_Active} \|\| {view.custom.m_Alm_EStop_Sts_Active} \|\| {view.custom.m_Alm_IntlkTrip_Sts_Active} \|\| {view.custom.m_Alm_ExcessStarts_Sts_Active} \|\| {view.custom.m_Alm_DrvFault_Sts_Active} \|\| {view.custom.m_Alm_DrvWarn_Sts_Active} \|\| {view.custom.m_Alm_CommFail_Sts_Active} \|\| {view.custom.m_Alm_SpdDev_Sts_Active})` | Shown while expression is true |
| root/Alarms/Body/List/A0 | `props.style.classes` | expr | `if({view.custom.m_Alm_FailStart_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_FailStart_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_FailStart_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_FailStart_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A1 | `props.style.classes` | expr | `if({view.custom.m_Alm_FailStop_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_FailStop_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_FailStop_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_FailStop_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A2 | `props.style.classes` | expr | `if({view.custom.m_Alm_Uncmd_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_Uncmd_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_Uncmd_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_Uncmd_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A3 | `props.style.classes` | expr | `if({view.custom.m_Alm_EStop_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_EStop_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_EStop_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_EStop_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A4 | `props.style.classes` | expr | `if({view.custom.m_Alm_IntlkTrip_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_IntlkTrip_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_IntlkTrip_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_IntlkTrip_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A5 | `props.style.classes` | expr | `if({view.custom.m_Alm_ExcessStarts_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_ExcessStarts_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_ExcessStarts_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_ExcessStarts_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A6 | `props.style.classes` | expr | `if({view.custom.m_Alm_DrvFault_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_DrvFault_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_DrvFault_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_DrvFault_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A7 | `props.style.classes` | expr | `if({view.custom.m_Alm_DrvWarn_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_DrvWarn_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_DrvWarn_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_DrvWarn_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A8 | `props.style.classes` | expr | `if({view.custom.m_Alm_CommFail_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_CommFail_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_CommFail_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_CommFail_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A9 | `props.style.classes` | expr | `if({view.custom.m_Alm_SpdDev_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_SpdDev_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_SpdDev_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_SpdDev_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
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
| root/Maintenance/Body/Hrs/Val | `props.text` | expr | `numberFormat({view.custom.m_Run_Val_RunHrs}, '#,##0')` | Text content |
| root/Maintenance/Body/Starts/Val | `props.text` | expr | `numberFormat({view.custom.m_Run_Val_Starts}, '#,##0')` | Text content |
| root/Maintenance/Body/StartsHr/Val | `props.text` | expr | `numberFormat({view.custom.m_Run_Val_StartsLastHr}, '#,##0')` | Text content |
| root/Maintenance/Body/SinceMaint/Val | `props.text` | expr | `numberFormat({view.custom.m_Run_Val_HrsSinceMaint}, '#,##0')` | Text content |
| root/Maintenance/Body/Due/Val | `props.text` | expr | `if({view.custom.m_Run_Sts_MaintDue}, 'YES', 'no')` | Text content |

### `root/Configuration`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true (hidden below Operator) |
| root/Configuration/Header/Chevron | `props.text` | expr | `if({view.custom.open_Configuration}, '▾', '▸')` | Text content |
| root/Configuration/Body | `position.display` | expr | `{view.custom.open_Configuration}` | Shown while expression is true |
| root/Configuration/Body/R0 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R0/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_FbkTime} / 1000, '#,##0.###')` | Text content |
| root/Configuration/Body/R0/EU | `props.text` | expr | `'s'` | Text content |
| root/Configuration/Body/E0 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E0/Entry | `props.value` | expr | `{view.custom.m_Cfg_FbkTime} / 1000` | Value in seconds (the PLC TIME is in milliseconds) |
| root/Configuration/Body/E0/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_FbkTime', currentValue.value, 4, 1000): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue` as value * 1000 (milliseconds), level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E0/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R1 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R1/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_RestartDly} / 1000, '#,##0.###')` | Text content |
| root/Configuration/Body/R1/EU | `props.text` | expr | `'s'` | Text content |
| root/Configuration/Body/E1 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E1/Entry | `props.value` | expr | `{view.custom.m_Cfg_RestartDly} / 1000` | Value in seconds (the PLC TIME is in milliseconds) |
| root/Configuration/Body/E1/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_RestartDly', currentValue.value, 4, 1000): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue` as value * 1000 (milliseconds), level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E1/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R2 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R2/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_RatedAmps}, '#,##0.###')` | Text content |
| root/Configuration/Body/R2/EU | `props.text` | expr | `'A'` | Text content |
| root/Configuration/Body/E2 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E2/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_RatedAmps`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Configuration/Body/E2/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_RatedAmps', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E2/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R3 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R3/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_MaxStartsHr}, '#,##0.###')` | Text content |
| root/Configuration/Body/R3/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E3 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E3/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_MaxStartsHr`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Configuration/Body/E3/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_MaxStartsHr', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E3/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R4 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R4/Val | `props.text` | expr | `if({view.custom.m_Cfg_AutoRestart}, 'Yes', 'No')` | Text content |
| root/Configuration/Body/C4 | `props.selected` | tag (indirect) | tag `{0}/Cfg_AutoRestart`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Configuration/Body/C4 | `props.selected` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_AutoRestart', bool(currentValue.value), 4): self.refreshBinding('props.selected')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/C4 | `props.enabled` | expr | `{view.custom.level} >= 4` | Enabled while expression is true |
| root/Configuration/Body/C4 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/R5 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R5/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_SpdMin}, '#,##0.###')` | Text content |
| root/Configuration/Body/R5/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E5 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E5/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_SpdMin`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Configuration/Body/E5/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_SpdMin', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E5/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R6 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R6/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_SpdMax}, '#,##0.###')` | Text content |
| root/Configuration/Body/R6/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E6 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E6/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_SpdMax`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Configuration/Body/E6/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_SpdMax', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E6/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R7 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R7/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_SpdDevLim}, '#,##0.###')` | Text content |
| root/Configuration/Body/R7/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E7 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E7/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_SpdDevLim`; refs {"0": "{view.params.tagPath}"} | Tag value, read one way |
| root/Configuration/Body/E7/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_SpdDevLim', currentValue.value, 4): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue`, level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E7/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R8 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R8/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_SpdDevTime} / 1000, '#,##0.###')` | Text content |
| root/Configuration/Body/R8/EU | `props.text` | expr | `'s'` | Text content |
| root/Configuration/Body/E8 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E8/Entry | `props.value` | expr | `{view.custom.m_Cfg_SpdDevTime} / 1000` | Value in seconds (the PLC TIME is in milliseconds) |
| root/Configuration/Body/E8/Entry | `props.value` onChange | script | `if origin == 'Browser' and currentValue.value is not None: if not efc.ui.setValue(self, 'Cfg_SpdDevTime', currentValue.value, 4, 1000): self.refreshBinding('props.value')` | Edit committed through `efc.ui.setValue` as value * 1000 (milliseconds), level 4, audited; a refused or failed write refreshes the binding |
| root/Configuration/Body/E8/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |


## Scripts reference

Total: **30 scripts**: 19 event scripts (13 `component.onActionPerformed`, 6 `dom` events: 1 `onClick` and the 5 JOG events) and 1 transform script (`custom.level`). 10 property-change `onChange` scripts (`props.value` of the speed and Configuration entries, `props.selected` of the Auto restart checkbox, see the end of the list). No `customMethods`, no `messageHandlers`.

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

9. **`root/Commands/Body/Buttons/B3`** (JOG): five `events.dom` scripts, scope G. Press writes TRUE (`onMouseDown`, `onTouchStart`), only while the button is enabled, because DOM events can still fire on a disabled button; release always tries to write FALSE (`onMouseUp`, `onMouseLeave`, `onTouchEnd`), with `notify=False` so a refusal below Maintenance opens no popup.

```python
	# onMouseDown, onTouchStart
	if self.props.enabled:
		efc.ui.cmd(self, 'Cmd_Jog', True, 2)
```

```python
	# onMouseUp, onMouseLeave, onTouchEnd
	efc.ui.cmd(self, 'Cmd_Jog', False, 2, notify=False)
```

10. **`root/Commands/Body/Dir/Fwd`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_Rev', False, 1)
```

11. **`root/Commands/Body/Dir/Rev`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_Rev', True, 1)
```

12. **`root/Alarms/Body/Ack`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.ackAll(self, ['Alm_FailStart', 'Alm_FailStop', 'Alm_Uncmd', 'Alm_EStop', 'Alm_IntlkTrip', 'Alm_ExcessStarts', 'Alm_DrvFault', 'Alm_DrvWarn', 'Alm_CommFail', 'Alm_SpdDev'])
```

13. **`root/Maintenance/Body/Buttons/ResetMaint`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Run/Cmd_ResetMaint', True, 2, audit=True)
```

14. **`root/Maintenance/Body/Buttons/Sim`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Sim_En', not self.view.custom.m_Sim_En, 2, audit=True)
```

15. **`root/Configuration/Header`**: `events.dom.onClick`, scope G.

```python
	self.view.custom.open_Configuration = not self.view.custom.open_Configuration
```

16. **transform on `(view root)` `custom.level`**: `custom.level` binding, `property` source `session.props.auth.securityLevels`.

```python
	return efc.ui.level(value)
```

17. **`root/Commands/Body/Spd/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cmd_Spd', currentValue.value, 1):
			self.refreshBinding('props.value')
```

18. **`root/Configuration/Body/E0/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_FbkTime', currentValue.value, 4, 1000):
			self.refreshBinding('props.value')
```

19. **`root/Configuration/Body/E1/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_RestartDly', currentValue.value, 4, 1000):
			self.refreshBinding('props.value')
```

20. **`root/Configuration/Body/E2/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_RatedAmps', currentValue.value, 4):
			self.refreshBinding('props.value')
```

21. **`root/Configuration/Body/E3/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_MaxStartsHr', currentValue.value, 4):
			self.refreshBinding('props.value')
```

22. **`root/Configuration/Body/C4`**: `propConfig` `props.selected` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_AutoRestart', bool(currentValue.value), 4):
			self.refreshBinding('props.selected')
```

23. **`root/Configuration/Body/E5/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_SpdMin', currentValue.value, 4):
			self.refreshBinding('props.value')
```

24. **`root/Configuration/Body/E6/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_SpdMax', currentValue.value, 4):
			self.refreshBinding('props.value')
```

25. **`root/Configuration/Body/E7/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_SpdDevLim', currentValue.value, 4):
			self.refreshBinding('props.value')
```

26. **`root/Configuration/Body/E8/Entry`**: `propConfig` `props.value` `onChange` (written only when `origin == 'Browser'`).

```python
	if origin == 'Browser' and currentValue.value is not None:
		if not efc.ui.setValue(self, 'Cfg_SpdDevTime', currentValue.value, 4, 1000):
			self.refreshBinding('props.value')
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
| `Commands/B3` (JOG) | `efc.ui.cmd(... 'Cmd_Jog', True, 2)` on mouse down / touch start; `efc.ui.cmd(... 'Cmd_Jog', False, 2, notify=False)` on mouse up / mouse leave / touch end | `Cmd_Jog` (held) | level 2 | no |
| `Commands/Dir/Fwd` | `efc.ui.cmd(... 'Cmd_Rev', False, 1)` | `Cmd_Rev` = FALSE | level 1 | no |
| `Commands/Dir/Rev` | `efc.ui.cmd(... 'Cmd_Rev', True, 1)` | `Cmd_Rev` = TRUE | level 1 | no |
| `Alarms/Ack` | `efc.ui.ackAll` on the ten alarms | `Alm_*/Cmd_Ack` where unacked | level 1 | no |
| `Maintenance/ResetMaint` | `efc.ui.cmd(... 'Run/Cmd_ResetMaint', True, 2)` | `Run/Cmd_ResetMaint` | level 2 | yes |
| `Maintenance/Sim` | `efc.ui.cmd(... 'Sim_En', not m_Sim_En, 2)` | `Sim_En` (toggle) | level 2 | yes |
| `Configuration/Header` (dom click) | toggles `open_Configuration` | none | none | no |
| `Commands/Body/Spd` (`Cmd_Spd` entry, onChange) | `efc.ui.setValue(... 'Cmd_Spd', value, 1)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cmd_Spd` | level 1 (`setValue`) | yes |
| `Configuration/Body/E0` (`Cfg_FbkTime` entry, onChange) | `efc.ui.setValue(... 'Cfg_FbkTime', value, 4, 1000)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_FbkTime` (milliseconds) | level 4 (`setValue`) | yes |
| `Configuration/Body/E1` (`Cfg_RestartDly` entry, onChange) | `efc.ui.setValue(... 'Cfg_RestartDly', value, 4, 1000)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_RestartDly` (milliseconds) | level 4 (`setValue`) | yes |
| `Configuration/Body/E2` (`Cfg_RatedAmps` entry, onChange) | `efc.ui.setValue(... 'Cfg_RatedAmps', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_RatedAmps` | level 4 (`setValue`) | yes |
| `Configuration/Body/E3` (`Cfg_MaxStartsHr` entry, onChange) | `efc.ui.setValue(... 'Cfg_MaxStartsHr', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_MaxStartsHr` | level 4 (`setValue`) | yes |
| `Configuration/Body/C4` (`Cfg_AutoRestart` checkbox, onChange) | `efc.ui.setValue(... 'Cfg_AutoRestart', bool(value), 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_AutoRestart` | level 4 (`setValue`) | yes |
| `Configuration/Body/E5` (`Cfg_SpdMin` entry, onChange) | `efc.ui.setValue(... 'Cfg_SpdMin', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_SpdMin` | level 4 (`setValue`) | yes |
| `Configuration/Body/E6` (`Cfg_SpdMax` entry, onChange) | `efc.ui.setValue(... 'Cfg_SpdMax', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_SpdMax` | level 4 (`setValue`) | yes |
| `Configuration/Body/E7` (`Cfg_SpdDevLim` entry, onChange) | `efc.ui.setValue(... 'Cfg_SpdDevLim', value, 4)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_SpdDevLim` | level 4 (`setValue`) | yes |
| `Configuration/Body/E8` (`Cfg_SpdDevTime` entry, onChange) | `efc.ui.setValue(... 'Cfg_SpdDevTime', value, 4, 1000)`, only when `origin == 'Browser'`; `refreshBinding` on False | `Cfg_SpdDevTime` (milliseconds) | level 4 (`setValue`) | yes |

`efc.ui.cmd` writes `view.params.tagPath + '/' + member` with `system.tag.writeBlocking` only when `userLevel >= minLevel`; below it, `cmd` returns False after logging and opening the AccessDenied popup (unless `notify=False`). The Mode, Commands, Ack and Maintenance buttons therefore use the level check. The speed entry (level 1) and the Configuration entries and checkbox (level 4) use `efc.ui.setValue`, which applies the same check and audits.

### Library functions used (`projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.level(levels)`**: walks `session.props.auth.securityLevels` (nested `name`/`children`, a path string, or a plain role list) and returns the highest index, 0 to 5, of the names that match `['Guest','Operator','Maintenance','Supervisor','Engineer','Admin']` case-insensitively (site names map through `efc.ui.ROLE_ALIASES`; no match gives 0). Bound to `custom.level`. `efc.ui.userLevel` (used by the checks in `cmd`, `setValue`, `ackAll`, `bypass`, `unbypass` and `dblCmd`) takes the larger of this and the level from `session.props.auth.user.roles`.
- **`efc.ui.closeDynamic(component)`**: sizes the dock (`efc.ui.sizeDock`), then loads the page's stored `default` view and params (`session.custom.efcDw['<pageId>|<page path>']`) back into the `dw_Right` dock, or closes the dock if there is no default. Writes no tags.
- **`efc.ui.cmd(component, member, value=True, minLevel=1, audit=False, notify=True)`**: the role-checked write described above. Below `minLevel` it does not write: with `notify` true it calls `efc.ui.denied` (a WARN log line and the `efcAccessDenied` popup, see [AccessDenied](../Parts/AccessDenied.md)), and it returns False either way. The JOG release events pass `notify=False`. Otherwise it writes through `_writeTags`, which logs any write that does not come back good, and returns True when the write was good. Audits when `audit=True`.
- **`efc.ui.setValue(component, member, value, minLevel=4, scale=1)`**: the commit behind every entry field and checkbox (decisions 14, 27). It returns False on an empty `tagPath` or a None value. Below `minLevel` it calls `efc.ui.denied` (WARN log and AccessDenied popup) and returns False. With `scale` other than 1 it writes `int(round(value * scale))` (the TIME entries pass 1000). It reads the old value and returns True without writing when the value is unchanged; otherwise it writes through `_writeTags` and, on a good write, audits `EFC set` with target `<tagPath>/<member>` and value `'<old> -> <new>'`. It returns whether the write was good; on False the onChange script calls `self.refreshBinding(...)`, so the field shows the tag value again.
- **`efc.ui.denied(component, minLevel, action='')`**: logs `Refused <action> for <user> (<have>): needs <need>` at WARN level and opens the popup `efcAccessDenied` (`Templates/Dynamic Window/Parts/AccessDenied`, modal) with params `action`, `need`, `have` and `user`. Called by `cmd`, `setValue`, `ackAll`, `bypass`, `unbypass` and `dblCmd`. See [AccessDenied](../Parts/AccessDenied.md).
- **`efc.ui.ackAll(component, alarms)`**: reads `<alarm>/Sts_Unack` for the listed alarms, then writes `<alarm>/Cmd_Ack` = True for those that are true. Below level 1 it writes nothing and calls `efc.ui.denied` (WARN log and AccessDenied popup).
- **`efc.ui.bypass` / `unbypass`**: not called from this view. They are called from the `BypassConfirm` popup, which the embedded `IntlkList` views open for both BYPASS and UNBYP.

## Tag members used

All paths are relative to `tagPath`. Types come from `types/PCLib_Members.csv` (nested types: `Mode` = T_Mode, `Alm_*` = T_Alarm, `Run` = T_RunTime, `Perm` and `Intlk` = T_Intlk). Access is taken from the bindings and handler scripts in this view.

| Member | Access | Data type | Meaning |
|---|---|---|---|
| `Mode/Sts_Man` | read | BOOL | In Manual (commanded by operator) - MTP Operator |
| `Sts_Avail` | read | BOOL | Available to Auto/program control |
| `Sts_Intlk` | read | BOOL | Interlock not healthy |
| `Sts_Local` | read | BOOL | In local control |
| `Sts_NotPerm` | read | BOOL | Permissive not healthy |
| `Val_Current` | read | REAL | Motor current (A) |
| `Val_LoadPct` | read | not defined in T_VFD | Load (% of Cfg_RatedAmps). Defined on T_Motor (REAL), not on T_VFD. See Notes. |
| `Sts_NE107` | read | INT | NAMUR NE107 status: 0=Good 1=Failure (F) 2=Function check (C) 3=Out of specification (S) 4=Maintenance required (M) |
| `Cfg_Tag` | read | STRING[20] | Equipment / instrument tag, e.g. FT-101 |
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Sts_Tripped` | read | BOOL | Tripped - reset required |
| `Sts_Fault` | read | BOOL | Any fault present |
| `Sts_Starting` | read | BOOL | Start commanded, waiting for feedback |
| `Sts_Stopping` | read | BOOL | Stop commanded, waiting for feedback |
| `Sts_Running` | read | BOOL | Running (feedback confirmed) |
| `Sts_Stopped` | read | BOOL | Stopped (feedback confirmed) |
| `Sts_Sim` | read | BOOL | Simulation active |
| `Mode/Sts_OOS` | read | BOOL | Out of service - MTP Offline |
| `Mode/Sts_Maint` | read | BOOL | In Maintenance |
| `Mode/Sts_Auto` | read | BOOL | In Automatic (commanded by owner) - MTP Automatic |
| `Cfg_Reversible` | read | BOOL | Reverse direction allowed |
| `Cfg_SpdEU` | read | STRING[8] | Speed units text (%, Hz, rpm) |
| `Val_SpdRef` | read | REAL | Active speed reference |
| `Val_Spd` | read | REAL | Speed |
| `Val_Torque` | read | REAL | Torque (%) |
| `Val_Power` | read | REAL | Power (kW) |
| `Inp_FaultCode` | read | UINT | Drive fault code |
| `Alm_FailStart/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_FailStart/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_FailStart/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_FailStop/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_FailStop/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_FailStop/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_Uncmd/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_Uncmd/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_Uncmd/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_EStop/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_EStop/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_EStop/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_IntlkTrip/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_IntlkTrip/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_IntlkTrip/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_ExcessStarts/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_ExcessStarts/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_ExcessStarts/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_DrvFault/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_DrvFault/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_DrvFault/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_DrvWarn/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_DrvWarn/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_DrvWarn/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_CommFail/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_CommFail/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_CommFail/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_SpdDev/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_SpdDev/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_SpdDev/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Run/Val_RunHrs` | read | REAL | Total run hours (display) |
| `Run/Val_Starts` | read | UDINT | Total starts / cycles |
| `Run/Val_StartsLastHr` | read | INT | Starts in the last 60 min (rolling) |
| `Run/Val_HrsSinceMaint` | read | REAL | Run hours since last maintenance reset |
| `Run/Sts_MaintDue` | read | BOOL | Maintenance due |
| `Cmd_Spd` | read; write via `efc.ui.setValue` (level 1, audited) | REAL | Operator manual speed reference |
| `Cfg_FbkTime` | read (shown as value / 1000); write value * 1000 via `efc.ui.setValue` (level 4, audited) | TIME | Time allowed for run feedback after start/stop |
| `Cfg_RestartDly` | read (shown as value / 1000); write value * 1000 via `efc.ui.setValue` (level 4, audited) | TIME | Minimum stopped time before restart |
| `Cfg_RatedAmps` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Motor nameplate full-load current (A) |
| `Cfg_MaxStartsHr` | read; write via `efc.ui.setValue` (level 4, audited) | INT | Maximum starts per hour, 0 = no limit |
| `Cfg_AutoRestart` | read; write via `efc.ui.setValue` (level 4, audited) | BOOL | Auto mode restarts after power loss / interlock clears |
| `Cfg_SpdMin` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Minimum speed reference |
| `Cfg_SpdMax` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Maximum speed reference |
| `Cfg_SpdDevLim` | read; write via `efc.ui.setValue` (level 4, audited) | REAL | Speed deviation alarm limit |
| `Cfg_SpdDevTime` | read (shown as value / 1000); write value * 1000 via `efc.ui.setValue` (level 4, audited) | TIME | Speed deviation delay |
| `Perm` | read (passed as tagPath) | T_Intlk | Permissive group: named conditions, first-out, bypass; Out_OK ANDed with Inp_PermOK |
| `Intlk` | read (passed as tagPath) | T_Intlk | Interlock group: named conditions, first-out, latch, bypass; Out_OK ANDed with Inp_IntlkOK |
| `Mode/Cmd_Auto` | write (one-shot) | BOOL | Operator request Automatic (one-shot) |
| `Mode/Cmd_Man` | write (one-shot) | BOOL | Operator request Manual (one-shot) |
| `Mode/Cmd_Maint` | write (one-shot) | BOOL | Request Maintenance (one-shot) |
| `Mode/Cmd_OOS` | write (one-shot) | BOOL | Request Out-of-Service (one-shot) |
| `Cmd_Start` | write (one-shot) | BOOL | Operator start (one-shot) |
| `Cmd_Stop` | write (one-shot) | BOOL | Operator stop (one-shot) |
| `Cmd_Reset` | write (one-shot) | BOOL | Fault / trip reset (one-shot) |
| `Cmd_Jog` | write | BOOL | Maintenance jog (maintained, Maint mode only) |
| `Cmd_Rev` | write | BOOL | Operator direction: TRUE = reverse |
| `Alm_FailStart/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_FailStop/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_Uncmd/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_EStop/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_IntlkTrip/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_ExcessStarts/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_DrvFault/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_DrvWarn/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_CommFail/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_SpdDev/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
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
        - `B3` (ia.input.button)
      - `Spd` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Entry` (ia.input.numeric-entry-field)
        - `EU` (ia.display.label)
      - `Dir` (ia.container.flex)
        - `Fwd` (ia.input.button)
        - `Rev` (ia.input.button)
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
      - `Ref` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Spd` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Trq` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Pwr` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Code` (ia.container.flex)
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
        - `A8` (ia.display.label)
        - `A9` (ia.display.label)
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
```

## Notes and open questions

- **`Val_LoadPct` is not defined on T_VFD.** The Load row (`root/Values/Body/Load/Val`, and the mirror `custom.m_Val_LoadPct`) reads `{0}/Val_LoadPct`. `types/PCLib_Members.csv` defines `Val_LoadPct` on T_Motor and T_Heater, but not on T_VFD. The generator's shared `motor_like()` layout adds this row to every motor-type window. Confirm the T_VFD UDT in the tag provider has this member. If it does not, the row will show bad quality or be empty.
- **Speed and direction are enabled by a looser rule than START.** The speed entry and FWD/REV require only `Mode/Sts_Man` and `Sts_Avail`. START also requires `!Sts_Intlk`, `!Sts_Local` and `!Sts_NotPerm`. The generator (`vfd()`, `cmd()`) builds both rules this way, so the difference is intentional in the source. Confirm it is intended. The operator can change the speed reference and direction while interlocked, in LOCAL, or not permitted. Whether the PLC ignores those writes is not in this file.
- **START does not check the drive state.** START is enabled while the drive is running, tripped or faulted, so it can write `Cmd_Start` in those states. STOP and RESET have no enable at all, so RESET is clickable outside MAN.
- **The hint line is not accurate.** It says the commands are "Enabled in MAN, available, permitted, not interlocked, not LOCAL". That is true only for START (JOG is MAINT-only and says so in the hint). STOP and RESET have no enable, and the speed entry and direction buttons use the looser rule above.
- **Direction is not shown.** `Sts_Rev` (running in reverse) is not bound. The FWD and REV buttons have no state highlight, so neither the commanded nor the running direction is visible.
- **Speed unit label is blank.** The unit beside the speed entry is an empty static label with no binding. The Values rows show the unit from `Cfg_SpdEU`.
- **Trend pens share one scale and have no legend.** `efc.ui.trend` scales every pen to one minimum and maximum. Speed reference, speed (in `Cfg_SpdEU` units) and current (A) therefore share one axis. The part draws the pens in fixed colours by position (dark, blue, grey) and the view does not label them. See [Parts/Trend.md](../Parts/Trend.md).
- **Unused PCLib members.** `Sts_State`, `Sts_Ready`, `Sts_AtSpd`, `Sts_Rev`, `Sts_CommFail` and `Sts_RestartLeft` are not read by this view. The banner computes its own state from the feedback flags. Communication failure appears only through `Alm_CommFail`.
- **Simulate toggle depends on the mirror.** `SIMULATE` writes `not self.view.custom.m_Sim_En`. If the mirror has not yet been read (`None`), `not None` is TRUE, so the first click writes TRUE.
- **Mode buttons have no enable binding.** MAN and AUTO can be clicked in any state, and so can MAINT and OOS. Below level 1 (MAN, AUTO) or level 2 (MAINT, OOS) the button shows a lock and a click opens the AccessDenied popup. The same applies in `Templates/Dynamic Window/Valves/ValveDiscrete`.
- **Outside this view, the template has its own enable rules.** The `PB` button on `Templates/Rotating/VFD` writes `Cmd_Start` or `Cmd_Stop` through `efc.ui.cmd(self, m, True, 1)`, so it has the same Operator check (and AccessDenied popup) as this dock. Its enable is the template's `canCmd` (MAN, available, not local, not OOS, and not interlocked or permissive-missing unless a stop is pending), which is not the same as the dock's START enable. Operators using the template symbol therefore follow the template's enable rules, not this dock's.
- **Drive fault code depends on `Sts_Fault`.** The fault code row is shown only when `Sts_Fault` is true. PCLib defines `Sts_Fault` as "any fault present" and `Sts_Tripped` as "tripped - reset required", but does not say whether a trip also sets `Sts_Fault`. If it does not, the code row is hidden while the banner shows TRIPPED. Open question.
- **Parameter and style class names** (`Alarm/Critical/Unacked` and similar, `Button/Toggle/On`, `Button/Momentary`, etc.) are style classes defined elsewhere. Their appearance was not checked.
- **Level thresholds** come from the constants in `efc.ui` (`OPERATOR=1`, `MAINT=2`, `SUPERVISOR=3`, `ENGINEER=4`). The dock uses 4 for Configuration editing, which matches `ENGINEER`.
