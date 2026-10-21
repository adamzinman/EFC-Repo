# Docks/ValveDiscrete

Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Docks/ValveDiscrete/view.json`
Opened from: the `Valve_Solenoid` template (and its MOV and Pneumatic siblings) through `efc.ui.openDynamic`. Dynamic window id `dw_ValveDiscrete`.

## Overview

The operator and maintenance dynamic window for a two-state valve (T_DValve). It opens in the screen's right-hand region (`Docks/Region`), not as a popup. It shows state, interlock and permissive detail, mode, commands, feedback, alarms, a trend, maintenance counters and configuration.

- **Default size:** 400 x 860 (`props.defaultSize`). The root is a scrolling column.
- **Parameters:** `tagPath` (the T_DValve instance) and `tType` (default `T_DValve`).
- **How it is opened:** the template's single click runs `efc.ui.openDynamic(self)`. That function writes `session.custom.efcDw[pageId] = {path: 'Docks/ValveDiscrete', params: {tagPath: ...}}`. `Docks/Region` then displays this view. `efc.ui.openDynamic` passes only `tagPath` (and `model` if present). **`tType` is never passed**, so the dock always runs with its default `T_DValve`. Nothing in this view uses `tType`.
- **Generated view:** this view is written by `generator/docks/build_docks.py`. Change the generator, not `view.json`, or the next build overwrites the edit.
- **How it closes:** the header `X` runs `efc.ui.closeDynamic(self)`, which restores the screen default set by `efc.ui.setDefaultDock` on `Docks/Region` startup. That startup script is not in this view.

## How it operates

**Header.** Shows `Cfg_Tag` (large) and `Cfg_Desc`.

**Banner.** The state label is chosen by priority: `Sts_Fault` (FAULT), `Sts_Opening` (OPENING), `Sts_Closing` (CLOSING), `Sts_Opened` (OPEN), `Sts_Closed` (CLOSED), else UNKNOWN. The style class follows the same order (`State/Fault`, `State/Transition`, `State/Running`, `State/Stopped`, `State/Unknown`). Four badges appear when their flag is true: SIM (`Sts_Sim`), LOCAL (`Sts_Local`), INTLK (`Sts_Intlk`), NOT PERM (`Sts_NotPerm`).

**Mode.** The mode text shows the highest of OOS, MAINT, MAN, else AUTO. The four toggle buttons highlight the active mode. AUTO and MAN are visible at level 1 and above, and MAINT and OOS at level 2 and above. None of the four has an `enabled` binding, so they are always clickable when visible. Each writes a one-shot `Mode/Cmd_*`. MAINT and OOS are audited.

**Commands** (level 1 and above). `OPEN` and `CLOSE` are enabled only when all of these are true: `Mode/Sts_Man`, `Sts_Avail`, not `Sts_Intlk`, not `Sts_Local`, not `Sts_NotPerm`. They write `Cmd_Open` and `Cmd_Close`. Note: they do not check `Sts_Opened`, `Sts_Closed`, `Sts_Fault` or `Mode/Sts_OOS`. `RESET` writes `Cmd_Reset` and is visible at level 1 and above, but has **no enable condition**, so it is clickable outside MAN. A hint line states the enable rule.

**Feedback.** Two rows show the limit switches, each visible only when that limit is configured (`Cfg_HasZSO` / `Cfg_HasZSC`). Each shows ON or off from `Inp_ZSO` / `Inp_ZSC`. A diagnostics row shows the NAMUR NE107 text for `Sts_NE107`: 0 `NE107 OK`, 1 `NE107 F`, 2 `NE107 C`, 3 `NE107 S`, 4 `NE107 M`.

**Permissives and interlocks.** Two embedded `Docks/Parts/IntlkList` views get `tagPath + '/Perm'` and `tagPath + '/Intlk'`, with titles "Permissives" and "Interlocks". Their content is not in this file.

**Alarms** (all levels). Five rows (fail to open, fail to close, position conflict, uncommanded move, interlock trip). A row is coloured when its alarm is active, using the alarm's `Cfg_Priority`: 1 `Critical`, 2 `High`, 3 `Medium`, 4 `Low`, anything else `Medium`. The class adds `/Unacked` or `/Fill`. An inactive but unacknowledged alarm uses `Alarm/Status/ClearedUnacked`. An inactive, acknowledged alarm uses `Text/Caption Text/Color/Muted`. "No active alarms" is shown when none is active. **ACK** (level 1 and above) calls `efc.ui.ackAll`, which writes `Cmd_Ack` only for those alarms whose `Sts_Unack` is true.

**Trend.** Embeds `Docks/Parts/Trend` with pens `Out_Open` and `Sts_Opened` over the tagPath. The embedded view's `expanded` param starts `false`. It is declared `inout` in `Docks/Parts/Trend`, so the Trend part toggles it itself and the value flows back to this embed. The `position.basis` binding (`{this.props.params.expanded}`) then grows the trend from 15.741 vh to 70.370 vh. The expansion is local to the trend and does not widen the dock region.

**Maintenance** (level 2 and above). Shows run hours, starts, starts in the last hour, hours since maintenance and whether maintenance is due. `RESET MAINT` writes `Run/Cmd_ResetMaint` (audited). `SIMULATE` toggles `Sim_En` (audited).

**Configuration** (collapsible; the header click toggles `open_Configuration`). Travel time is read-only below level 4 and editable at level 4 and above (bidirectional `Cfg_TravelTime`, unit s). The "Has open limit" and "Has closed limit" checkboxes are bidirectional to `Cfg_HasZSO` and `Cfg_HasZSC`, enabled only at level 4 and above. The entry and checkboxes write the tag directly through the binding. The only guard is the UI enable expression. The entry's enable expression is the literal `true`; its visibility is what limits it to level 4.

**Role checks.** All role levels come from the Perspective session (`session.props.auth.user.roles`) and are checked in the client. `efc.ui.cmd` returns without writing when the level is too low. Bindings do not check the level. Real access control has to be enforced in Perspective security and the PLC logic.

**Audit.** `efc.ui` writes an audit entry (`system.util.audit`, falling back to the logger) for MAINT, OOS, RESET MAINT and SIMULATE. It does not audit AUTO, MAN, OPEN, CLOSE, RESET or ACK.

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `""` | T_DValve instance. Every component binding uses `{view.params.tagPath}`. | Set by `efc.ui.openDynamic` from the template's `dwTagPath` (or `tagPath`). Read by bindings and `efc.ui` commands. |
| `tType` | input | `T_DValve` | Declared type. | Not passed by `efc.ui.openDynamic`; not referenced by any binding or script in this view. Always the default. |

Both have `paramDirection: input` and `persistent: true`. No output parameters.

### View-level custom properties (`custom`)


| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.level` | `0` | property + script transform | `session.props.auth.user.roles` → `return efc.ui.level(value)` | Role level 0-5 from `session.props.auth.user.roles` via `efc.ui.level`. Gates buttons and sections (Guest 0, Operator 1, Maintenance 2, Supervisor 3, Engineer 4, Admin 5). |
| `view.custom.m_Mode_Sts_Man` | `null` | tag | tag `{0}/Mode/Sts_Man` | Mirror of tag `<tagPath>/Mode/Sts_Man`. |
| `view.custom.m_Sts_Avail` | `null` | tag | tag `{0}/Sts_Avail` | Mirror of tag `<tagPath>/Sts_Avail`. |
| `view.custom.m_Sts_Intlk` | `null` | tag | tag `{0}/Sts_Intlk` | Mirror of tag `<tagPath>/Sts_Intlk`. |
| `view.custom.m_Sts_Local` | `null` | tag | tag `{0}/Sts_Local` | Mirror of tag `<tagPath>/Sts_Local`. |
| `view.custom.m_Sts_NotPerm` | `null` | tag | tag `{0}/Sts_NotPerm` | Mirror of tag `<tagPath>/Sts_NotPerm`. |
| `view.custom.m_Cfg_Tag` | `null` | tag | tag `{0}/Cfg_Tag` | Mirror of tag `<tagPath>/Cfg_Tag`. |
| `view.custom.m_Cfg_Desc` | `null` | tag | tag `{0}/Cfg_Desc` | Mirror of tag `<tagPath>/Cfg_Desc`. |
| `view.custom.m_Sts_Fault` | `null` | tag | tag `{0}/Sts_Fault` | Mirror of tag `<tagPath>/Sts_Fault`. |
| `view.custom.m_Sts_Opening` | `null` | tag | tag `{0}/Sts_Opening` | Mirror of tag `<tagPath>/Sts_Opening`. |
| `view.custom.m_Sts_Closing` | `null` | tag | tag `{0}/Sts_Closing` | Mirror of tag `<tagPath>/Sts_Closing`. |
| `view.custom.m_Sts_Opened` | `null` | tag | tag `{0}/Sts_Opened` | Mirror of tag `<tagPath>/Sts_Opened`. |
| `view.custom.m_Sts_Closed` | `null` | tag | tag `{0}/Sts_Closed` | Mirror of tag `<tagPath>/Sts_Closed`. |
| `view.custom.m_Sts_Sim` | `null` | tag | tag `{0}/Sts_Sim` | Mirror of tag `<tagPath>/Sts_Sim`. |
| `view.custom.m_Mode_Sts_OOS` | `null` | tag | tag `{0}/Mode/Sts_OOS` | Mirror of tag `<tagPath>/Mode/Sts_OOS`. |
| `view.custom.m_Mode_Sts_Maint` | `null` | tag | tag `{0}/Mode/Sts_Maint` | Mirror of tag `<tagPath>/Mode/Sts_Maint`. |
| `view.custom.m_Mode_Sts_Auto` | `null` | tag | tag `{0}/Mode/Sts_Auto` | Mirror of tag `<tagPath>/Mode/Sts_Auto`. |
| `view.custom.m_Inp_ZSO` | `null` | tag | tag `{0}/Inp_ZSO` | Mirror of tag `<tagPath>/Inp_ZSO`. |
| `view.custom.m_Cfg_HasZSO` | `null` | tag | tag `{0}/Cfg_HasZSO` | Mirror of tag `<tagPath>/Cfg_HasZSO`. |
| `view.custom.m_Inp_ZSC` | `null` | tag | tag `{0}/Inp_ZSC` | Mirror of tag `<tagPath>/Inp_ZSC`. |
| `view.custom.m_Cfg_HasZSC` | `null` | tag | tag `{0}/Cfg_HasZSC` | Mirror of tag `<tagPath>/Cfg_HasZSC`. |
| `view.custom.m_Sts_NE107` | `null` | tag | tag `{0}/Sts_NE107` | Mirror of tag `<tagPath>/Sts_NE107`. |
| `view.custom.m_Alm_FailOpen_Sts_Active` | `null` | tag | tag `{0}/Alm_FailOpen/Sts_Active` | Mirror of tag `<tagPath>/Alm_FailOpen/Sts_Active`. |
| `view.custom.m_Alm_FailOpen_Sts_Unack` | `null` | tag | tag `{0}/Alm_FailOpen/Sts_Unack` | Mirror of tag `<tagPath>/Alm_FailOpen/Sts_Unack`. |
| `view.custom.m_Alm_FailOpen_Cfg_Priority` | `null` | tag | tag `{0}/Alm_FailOpen/Cfg_Priority` | Mirror of tag `<tagPath>/Alm_FailOpen/Cfg_Priority`. |
| `view.custom.m_Alm_FailClose_Sts_Active` | `null` | tag | tag `{0}/Alm_FailClose/Sts_Active` | Mirror of tag `<tagPath>/Alm_FailClose/Sts_Active`. |
| `view.custom.m_Alm_FailClose_Sts_Unack` | `null` | tag | tag `{0}/Alm_FailClose/Sts_Unack` | Mirror of tag `<tagPath>/Alm_FailClose/Sts_Unack`. |
| `view.custom.m_Alm_FailClose_Cfg_Priority` | `null` | tag | tag `{0}/Alm_FailClose/Cfg_Priority` | Mirror of tag `<tagPath>/Alm_FailClose/Cfg_Priority`. |
| `view.custom.m_Alm_PosConflict_Sts_Active` | `null` | tag | tag `{0}/Alm_PosConflict/Sts_Active` | Mirror of tag `<tagPath>/Alm_PosConflict/Sts_Active`. |
| `view.custom.m_Alm_PosConflict_Sts_Unack` | `null` | tag | tag `{0}/Alm_PosConflict/Sts_Unack` | Mirror of tag `<tagPath>/Alm_PosConflict/Sts_Unack`. |
| `view.custom.m_Alm_PosConflict_Cfg_Priority` | `null` | tag | tag `{0}/Alm_PosConflict/Cfg_Priority` | Mirror of tag `<tagPath>/Alm_PosConflict/Cfg_Priority`. |
| `view.custom.m_Alm_Uncmd_Sts_Active` | `null` | tag | tag `{0}/Alm_Uncmd/Sts_Active` | Mirror of tag `<tagPath>/Alm_Uncmd/Sts_Active`. |
| `view.custom.m_Alm_Uncmd_Sts_Unack` | `null` | tag | tag `{0}/Alm_Uncmd/Sts_Unack` | Mirror of tag `<tagPath>/Alm_Uncmd/Sts_Unack`. |
| `view.custom.m_Alm_Uncmd_Cfg_Priority` | `null` | tag | tag `{0}/Alm_Uncmd/Cfg_Priority` | Mirror of tag `<tagPath>/Alm_Uncmd/Cfg_Priority`. |
| `view.custom.m_Alm_IntlkTrip_Sts_Active` | `null` | tag | tag `{0}/Alm_IntlkTrip/Sts_Active` | Mirror of tag `<tagPath>/Alm_IntlkTrip/Sts_Active`. |
| `view.custom.m_Alm_IntlkTrip_Sts_Unack` | `null` | tag | tag `{0}/Alm_IntlkTrip/Sts_Unack` | Mirror of tag `<tagPath>/Alm_IntlkTrip/Sts_Unack`. |
| `view.custom.m_Alm_IntlkTrip_Cfg_Priority` | `null` | tag | tag `{0}/Alm_IntlkTrip/Cfg_Priority` | Mirror of tag `<tagPath>/Alm_IntlkTrip/Cfg_Priority`. |
| `view.custom.m_Run_Val_RunHrs` | `null` | tag | tag `{0}/Run/Val_RunHrs` | Mirror of tag `<tagPath>/Run/Val_RunHrs`. |
| `view.custom.m_Run_Val_Starts` | `null` | tag | tag `{0}/Run/Val_Starts` | Mirror of tag `<tagPath>/Run/Val_Starts`. |
| `view.custom.m_Run_Val_StartsLastHr` | `null` | tag | tag `{0}/Run/Val_StartsLastHr` | Mirror of tag `<tagPath>/Run/Val_StartsLastHr`. |
| `view.custom.m_Run_Val_HrsSinceMaint` | `null` | tag | tag `{0}/Run/Val_HrsSinceMaint` | Mirror of tag `<tagPath>/Run/Val_HrsSinceMaint`. |
| `view.custom.m_Run_Sts_MaintDue` | `null` | tag | tag `{0}/Run/Sts_MaintDue` | Mirror of tag `<tagPath>/Run/Sts_MaintDue`. |
| `view.custom.m_Sim_En` | `null` | tag | tag `{0}/Sim_En` | Mirror of tag `<tagPath>/Sim_En`. |
| `view.custom.m_Cfg_TravelTime` | `null` | tag | tag `{0}/Cfg_TravelTime` | Mirror of tag `<tagPath>/Cfg_TravelTime`. |
| `view.custom.open_Configuration` | `false` | none (written by scripts) | none | View-local toggle for the Configuration section. Set by the header click script; not bound to any tag; not persisted. |

### Component-level custom properties

None.

### Session, page and message payloads

- `session.props.auth.user.roles`: read by `custom.level` (transform `efc.ui.level`).
- `session.props.auth.user.userName`: read by `efc.ui._audit` (not bound in this view).
- `session.custom.efcDw[pageId]`: written by `efc.ui.openDynamic` and `closeDynamic` in the template and header; read by `Docks/Region` (not in this file).
- `page.props.pageId`: read by `efc.ui._state` to key `efcDw`.
- No message handlers. No `customMethods`.

## Bindings reference

Total: **101 bindings**: 44 at view root (all `custom.*`, including 1 `property` binding with a transform) and 57 on components. Types: 54 `expr`, 46 `tag`, 1 `property`. `params.tagPath` and `params.tType` have `paramDirection` only. Embedded-view `params.*` values and `position.basis` are component bindings and counted in the 57.

### View root (44 bindings)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| (view root) | `custom.level` | property + transform | `session.props.auth.user.roles` | Reads session property; transform: script |
| (view root) | `custom.m_Mode_Sts_Man` | tag (indirect) | tag `{0}/Mode/Sts_Man`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Sts_Avail` | tag (indirect) | tag `{0}/Sts_Avail`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Sts_Intlk` | tag (indirect) | tag `{0}/Sts_Intlk`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Sts_Local` | tag (indirect) | tag `{0}/Sts_Local`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Sts_NotPerm` | tag (indirect) | tag `{0}/Sts_NotPerm`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Cfg_Tag` | tag (indirect) | tag `{0}/Cfg_Tag`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Cfg_Desc` | tag (indirect) | tag `{0}/Cfg_Desc`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Sts_Fault` | tag (indirect) | tag `{0}/Sts_Fault`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Sts_Opening` | tag (indirect) | tag `{0}/Sts_Opening`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Sts_Closing` | tag (indirect) | tag `{0}/Sts_Closing`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Sts_Opened` | tag (indirect) | tag `{0}/Sts_Opened`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Sts_Closed` | tag (indirect) | tag `{0}/Sts_Closed`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Sts_Sim` | tag (indirect) | tag `{0}/Sts_Sim`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Mode_Sts_OOS` | tag (indirect) | tag `{0}/Mode/Sts_OOS`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Mode_Sts_Maint` | tag (indirect) | tag `{0}/Mode/Sts_Maint`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Mode_Sts_Auto` | tag (indirect) | tag `{0}/Mode/Sts_Auto`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Inp_ZSO` | tag (indirect) | tag `{0}/Inp_ZSO`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Cfg_HasZSO` | tag (indirect) | tag `{0}/Cfg_HasZSO`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Inp_ZSC` | tag (indirect) | tag `{0}/Inp_ZSC`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Cfg_HasZSC` | tag (indirect) | tag `{0}/Cfg_HasZSC`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Sts_NE107` | tag (indirect) | tag `{0}/Sts_NE107`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Alm_FailOpen_Sts_Active` | tag (indirect) | tag `{0}/Alm_FailOpen/Sts_Active`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Alm_FailOpen_Sts_Unack` | tag (indirect) | tag `{0}/Alm_FailOpen/Sts_Unack`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Alm_FailOpen_Cfg_Priority` | tag (indirect) | tag `{0}/Alm_FailOpen/Cfg_Priority`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Alm_FailClose_Sts_Active` | tag (indirect) | tag `{0}/Alm_FailClose/Sts_Active`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Alm_FailClose_Sts_Unack` | tag (indirect) | tag `{0}/Alm_FailClose/Sts_Unack`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Alm_FailClose_Cfg_Priority` | tag (indirect) | tag `{0}/Alm_FailClose/Cfg_Priority`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Alm_PosConflict_Sts_Active` | tag (indirect) | tag `{0}/Alm_PosConflict/Sts_Active`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Alm_PosConflict_Sts_Unack` | tag (indirect) | tag `{0}/Alm_PosConflict/Sts_Unack`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Alm_PosConflict_Cfg_Priority` | tag (indirect) | tag `{0}/Alm_PosConflict/Cfg_Priority`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Alm_Uncmd_Sts_Active` | tag (indirect) | tag `{0}/Alm_Uncmd/Sts_Active`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Alm_Uncmd_Sts_Unack` | tag (indirect) | tag `{0}/Alm_Uncmd/Sts_Unack`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Alm_Uncmd_Cfg_Priority` | tag (indirect) | tag `{0}/Alm_Uncmd/Cfg_Priority`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Alm_IntlkTrip_Sts_Active` | tag (indirect) | tag `{0}/Alm_IntlkTrip/Sts_Active`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Alm_IntlkTrip_Sts_Unack` | tag (indirect) | tag `{0}/Alm_IntlkTrip/Sts_Unack`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Alm_IntlkTrip_Cfg_Priority` | tag (indirect) | tag `{0}/Alm_IntlkTrip/Cfg_Priority`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Run_Val_RunHrs` | tag (indirect) | tag `{0}/Run/Val_RunHrs`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Run_Val_Starts` | tag (indirect) | tag `{0}/Run/Val_Starts`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Run_Val_StartsLastHr` | tag (indirect) | tag `{0}/Run/Val_StartsLastHr`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Run_Val_HrsSinceMaint` | tag (indirect) | tag `{0}/Run/Val_HrsSinceMaint`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Run_Sts_MaintDue` | tag (indirect) | tag `{0}/Run/Sts_MaintDue`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Sim_En` | tag (indirect) | tag `{0}/Sim_En`; refs {"0": "{view.params.tagPath}"} | Reads tag value |
| (view root) | `custom.m_Cfg_TravelTime` | tag (indirect) | tag `{0}/Cfg_TravelTime`; refs {"0": "{view.params.tagPath}"} | Reads tag value |

### `root/Header/Names/Tag` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Header/Names/Tag | `props.text` | expr | `{view.custom.m_Cfg_Tag}` | Text content |

### `root/Header/Names/Desc` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Header/Names/Desc | `props.text` | expr | `{view.custom.m_Cfg_Desc}` | Text content |

### `root/Banner` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Banner | `props.style.classes` | expr | `if({view.custom.m_Sts_Fault}, 'State/Fault', if({view.custom.m_Sts_Opening}, 'State/Transition', if({view.custom.m_Sts_Closing}, 'State/Transition', if({view.custom.m_Sts_Opened}, 'State/Running', if({view.custom.m_Sts_Closed}, 'State/Stopped', 'State/Unknown')))))` | CSS class(es) selected by state |

### `root/Banner/State` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Banner/State | `props.text` | expr | `if({view.custom.m_Sts_Fault}, 'FAULT', if({view.custom.m_Sts_Opening}, 'OPENING', if({view.custom.m_Sts_Closing}, 'CLOSING', if({view.custom.m_Sts_Opened}, 'OPEN', if({view.custom.m_Sts_Closed}, 'CLOSED', 'UNKNOWN')))))` | Text content |

### `root/Banner/Chip0` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Banner/Chip0 | `position.display` | expr | `{view.custom.m_Sts_Sim}` | Shown while expression is true |

### `root/Banner/Chip1` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Banner/Chip1 | `position.display` | expr | `{view.custom.m_Sts_Local}` | Shown while expression is true |

### `root/Banner/Chip2` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Banner/Chip2 | `position.display` | expr | `{view.custom.m_Sts_Intlk}` | Shown while expression is true |

### `root/Banner/Chip3` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Banner/Chip3 | `position.display` | expr | `{view.custom.m_Sts_NotPerm}` | Shown while expression is true |

### `root/Mode/Body/Current/Val` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Mode/Body/Current/Val | `props.text` | expr | `if({view.custom.m_Mode_Sts_OOS}, 'OOS', if({view.custom.m_Mode_Sts_Maint}, 'MAINT', if({view.custom.m_Mode_Sts_Man}, 'MAN', 'AUTO')))` | Text content |

### `root/Mode/Body/Buttons/Auto` (2)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Mode/Body/Buttons/Auto | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Mode/Body/Buttons/Auto | `props.style.classes` | expr | `if({view.custom.m_Mode_Sts_Auto}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |

### `root/Mode/Body/Buttons/Man` (2)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Mode/Body/Buttons/Man | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Mode/Body/Buttons/Man | `props.style.classes` | expr | `if({view.custom.m_Mode_Sts_Man}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |

### `root/Mode/Body/Buttons/Maint` (2)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Mode/Body/Buttons/Maint | `position.display` | expr | `{view.custom.level} >= 2` | Shown while expression is true |
| root/Mode/Body/Buttons/Maint | `props.style.classes` | expr | `if({view.custom.m_Mode_Sts_Maint}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |

### `root/Mode/Body/Buttons/OOS` (2)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Mode/Body/Buttons/OOS | `position.display` | expr | `{view.custom.level} >= 2` | Shown while expression is true |
| root/Mode/Body/Buttons/OOS | `props.style.classes` | expr | `if({view.custom.m_Mode_Sts_OOS}, 'Button/Toggle/On', 'Button/Toggle/Off')` | CSS class(es) selected by state |

### `root/Commands` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Commands | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |

### `root/Commands/Body/Buttons/B0` (2)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Commands/Body/Buttons/B0 | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Commands/Body/Buttons/B0 | `props.enabled` | expr | `{view.custom.m_Mode_Sts_Man} && {view.custom.m_Sts_Avail} && !{view.custom.m_Sts_Intlk} && !{view.custom.m_Sts_Local} && !{view.custom.m_Sts_NotPerm}` | Enabled while expression is true |

### `root/Commands/Body/Buttons/B1` (2)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Commands/Body/Buttons/B1 | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |
| root/Commands/Body/Buttons/B1 | `props.enabled` | expr | `{view.custom.m_Mode_Sts_Man} && {view.custom.m_Sts_Avail} && !{view.custom.m_Sts_Intlk} && !{view.custom.m_Sts_Local} && !{view.custom.m_Sts_NotPerm}` | Enabled while expression is true |

### `root/Commands/Body/Buttons/B2` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Commands/Body/Buttons/B2 | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |

### `root/Feedback/Body/ZSO` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Feedback/Body/ZSO | `position.display` | expr | `{view.custom.m_Cfg_HasZSO}` | Shown while expression is true |

### `root/Feedback/Body/ZSO/Val` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Feedback/Body/ZSO/Val | `props.text` | expr | `if({view.custom.m_Inp_ZSO}, 'ON', 'off')` | Text content |

### `root/Feedback/Body/ZSC` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Feedback/Body/ZSC | `position.display` | expr | `{view.custom.m_Cfg_HasZSC}` | Shown while expression is true |

### `root/Feedback/Body/ZSC/Val` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Feedback/Body/ZSC/Val | `props.text` | expr | `if({view.custom.m_Inp_ZSC}, 'ON', 'off')` | Text content |

### `root/Feedback/Body/NE107/Val` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Feedback/Body/NE107/Val | `props.text` | expr | `case(toInt({view.custom.m_Sts_NE107}), 0, 'NE107 OK', 1, 'NE107 F', 2, 'NE107 C', 3, 'NE107 S', 4, 'NE107 M', '')` | Text content |

### `root/Perm` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Perm | `props.params.tagPath` | expr | `{view.params.tagPath} + '/Perm'` | Embedded view tagPath param |

### `root/Intlk` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Intlk | `props.params.tagPath` | expr | `{view.params.tagPath} + '/Intlk'` | Embedded view tagPath param |

### `root/Alarms/Body/None` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Alarms/Body/None | `position.display` | expr | `!({view.custom.m_Alm_FailOpen_Sts_Active} \|\| {view.custom.m_Alm_FailClose_Sts_Active} \|\| {view.custom.m_Alm_PosConflict_Sts_Active} \|\| {view.custom.m_Alm_Uncmd_Sts_Active} \|\| {view.custom.m_Alm_IntlkTrip_Sts_Active})` | Shown while expression is true |

### `root/Alarms/Body/List/A0` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Alarms/Body/List/A0 | `props.style.classes` | expr | `if({view.custom.m_Alm_FailOpen_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_FailOpen_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_FailOpen_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_FailOpen_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |

### `root/Alarms/Body/List/A1` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Alarms/Body/List/A1 | `props.style.classes` | expr | `if({view.custom.m_Alm_FailClose_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_FailClose_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_FailClose_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_FailClose_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |

### `root/Alarms/Body/List/A2` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Alarms/Body/List/A2 | `props.style.classes` | expr | `if({view.custom.m_Alm_PosConflict_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_PosConflict_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_PosConflict_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_PosConflict_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |

### `root/Alarms/Body/List/A3` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Alarms/Body/List/A3 | `props.style.classes` | expr | `if({view.custom.m_Alm_Uncmd_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_Uncmd_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_Uncmd_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_Uncmd_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |

### `root/Alarms/Body/List/A4` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Alarms/Body/List/A4 | `props.style.classes` | expr | `if({view.custom.m_Alm_IntlkTrip_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_IntlkTrip_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_IntlkTrip_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_IntlkTrip_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |

### `root/Alarms/Body/Ack` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Alarms/Body/Ack | `position.display` | expr | `{view.custom.level} >= 1` | Shown while expression is true |

### `root/Trend` (2)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Trend | `props.params.tagPath` | expr | `{view.params.tagPath}` | Embedded view tagPath param |
| root/Trend | `position.basis` | expr | `if({this.props.params.expanded}, '70.370vh', '15.741vh')` | Row height |

### `root/Maintenance` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Maintenance | `position.display` | expr | `{view.custom.level} >= 2` | Shown while expression is true |

### `root/Maintenance/Body/Hrs/Val` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Maintenance/Body/Hrs/Val | `props.text` | expr | `numberFormat({view.custom.m_Run_Val_RunHrs}, '#,##0')` | Text content |

### `root/Maintenance/Body/Starts/Val` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Maintenance/Body/Starts/Val | `props.text` | expr | `numberFormat({view.custom.m_Run_Val_Starts}, '#,##0')` | Text content |

### `root/Maintenance/Body/StartsHr/Val` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Maintenance/Body/StartsHr/Val | `props.text` | expr | `numberFormat({view.custom.m_Run_Val_StartsLastHr}, '#,##0')` | Text content |

### `root/Maintenance/Body/SinceMaint/Val` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Maintenance/Body/SinceMaint/Val | `props.text` | expr | `numberFormat({view.custom.m_Run_Val_HrsSinceMaint}, '#,##0')` | Text content |

### `root/Maintenance/Body/Due/Val` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Maintenance/Body/Due/Val | `props.text` | expr | `if({view.custom.m_Run_Sts_MaintDue}, 'YES', 'no')` | Text content |

### `root/Configuration/Header/Chevron` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration/Header/Chevron | `props.text` | expr | `if({view.custom.open_Configuration}, '▾', '▸')` | Text content |

### `root/Configuration/Body` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration/Body | `position.display` | expr | `{view.custom.open_Configuration}` | Shown while expression is true |

### `root/Configuration/Body/R0` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration/Body/R0 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |

### `root/Configuration/Body/R0/Val` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration/Body/R0/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_TravelTime}, '#,##0.###')` | Text content |

### `root/Configuration/Body/R0/EU` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration/Body/R0/EU | `props.text` | expr | `'s'` | Text content |

### `root/Configuration/Body/E0` (1)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration/Body/E0 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |

### `root/Configuration/Body/E0/Entry` (2)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration/Body/E0/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_TravelTime` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E0/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |

### `root/Configuration/Body/C1` (2)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration/Body/C1 | `props.selected` | tag (indirect) | tag `{0}/Cfg_HasZSO` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/C1 | `props.enabled` | expr | `{view.custom.level} >= 4` | Enabled while expression is true |

### `root/Configuration/Body/C2` (2)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Configuration/Body/C2 | `props.selected` | tag (indirect) | tag `{0}/Cfg_HasZSC` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/C2 | `props.enabled` | expr | `{view.custom.level} >= 4` | Enabled while expression is true |

## Scripts reference

Total: **13 scripts**: 12 event scripts (11 `component.onActionPerformed`, 1 `dom.onClick`) and 1 transform script (`custom.level`). No `customMethods`, no `messageHandlers`, no property-change `onChange` scripts.

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
	efc.ui.cmd(self, 'Cmd_Open', True, 1)
```


7. **`root/Commands/Body/Buttons/B1`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_Close', True, 1)
```


8. **`root/Commands/Body/Buttons/B2`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.cmd(self, 'Cmd_Reset', True, 1)
```


9. **`root/Alarms/Body/Ack`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.ackAll(self, ['Alm_FailOpen', 'Alm_FailClose', 'Alm_PosConflict', 'Alm_Uncmd', 'Alm_IntlkTrip'])
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


### Explanation of each handler

| Handler | Action | Writes | Role check | Audit |
|---|---|---|---|---|
| `Header/Close` | `efc.ui.closeDynamic` restores default region view | none | none | no |
| `Mode/Auto` | `efc.ui.cmd(... 'Mode/Cmd_Auto', True, 1)` | `Mode/Cmd_Auto` | level 1 | no |
| `Mode/Man` | `efc.ui.cmd(... 'Mode/Cmd_Man', True, 1)` | `Mode/Cmd_Man` | level 1 | no |
| `Mode/Maint` | `efc.ui.cmd(... 'Mode/Cmd_Maint', True, 2)` | `Mode/Cmd_Maint` | level 2 | yes |
| `Mode/OOS` | `efc.ui.cmd(... 'Mode/Cmd_OOS', True, 2)` | `Mode/Cmd_OOS` | level 2 | yes |
| `Commands/B0` (OPEN) | `efc.ui.cmd(... 'Cmd_Open', True, 1)` | `Cmd_Open` | level 1 | no |
| `Commands/B1` (CLOSE) | `efc.ui.cmd(... 'Cmd_Close', True, 1)` | `Cmd_Close` | level 1 | no |
| `Commands/B2` (RESET) | `efc.ui.cmd(... 'Cmd_Reset', True, 1)` | `Cmd_Reset` | level 1 | no |
| `Alarms/Ack` | `efc.ui.ackAll` on the five alarms | `Alm_*/Cmd_Ack` where unacked | level 1 | no |
| `Maintenance/ResetMaint` | `efc.ui.cmd(... 'Run/Cmd_ResetMaint', True, 2)` | `Run/Cmd_ResetMaint` | level 2 | yes |
| `Maintenance/Sim` | `efc.ui.cmd(... 'Sim_En', not m_Sim_En, 2)` | `Sim_En` (toggle) | level 2 | yes |
| `Configuration/Header` (dom click) | toggles `open_Configuration` | none | none | no |

`efc.ui.cmd` writes `view.params.tagPath + '/' + member` with `system.tag.writeBlocking` only when `userLevel >= minLevel`. The Mode, Commands, Ack and Maintenance buttons therefore use the level check; the Configuration bindings do not.

### Library functions used (`projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.level(roles)`**: highest index of the role in `['Guest','Operator','Maintenance','Supervisor','Engineer','Admin']`, or 0. Bound to `custom.level`.
- **`efc.ui.closeDynamic(component)`**: writes `efcDw[pageId]` back to the stored `default` path and params. Writes no tags.
- **`efc.ui.cmd(component, member, value, minLevel, audit)`**: the role-checked write described above. Audits when `audit=True`.
- **`efc.ui.ackAll(component, alarms)`**: reads `<alarm>/Sts_Unack` for the listed alarms, then writes `<alarm>/Cmd_Ack` = True for those that are true, only at level 1 and above.
- **`efc.ui.bypass` / `unbypass`**: exist in the module but are not called from this view. Interlock bypass is handled in the embedded `IntlkList` views, which are not in this file.


## Tag members used

All paths are relative to `tagPath`. Types come from `types/PCLib_Members.csv` (nested types: `Mode` = T_Mode, `Alm_*` = T_Alarm, `Run` = T_RunTime, `Perm` and `Intlk` = T_Intlk).

| Member | Access | Data type | Meaning (PCLib comment) |
|---|---|---|---|
| `Cfg_Tag` | read | STRING[20] | Equipment / instrument tag, e.g. FT-101 |
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Sts_Opened` | read; also read by trend pens | BOOL | Confirmed open |
| `Sts_Closed` | read | BOOL | Confirmed closed |
| `Sts_Opening` | read | BOOL | Travelling open |
| `Sts_Closing` | read | BOOL | Travelling closed |
| `Sts_Fault` | read | BOOL | Any fault present |
| `Sts_Avail` | read | BOOL | Available to Auto/program control |
| `Sts_Local` | read | BOOL | In local control |
| `Sts_Intlk` | read | BOOL | Interlock not healthy |
| `Sts_NotPerm` | read | BOOL | Permissive not healthy |
| `Sts_Sim` | read | BOOL | Simulation active |
| `Mode/Sts_Auto` | read | BOOL | In Automatic (commanded by owner) - MTP Automatic |
| `Mode/Sts_Man` | read | BOOL | In Manual (commanded by operator) - MTP Operator |
| `Mode/Sts_Maint` | read | BOOL | In Maintenance |
| `Mode/Sts_OOS` | read | BOOL | Out of service - MTP Offline |
| `Inp_ZSO` | read | BOOL | Open limit switch |
| `Inp_ZSC` | read | BOOL | Closed limit switch |
| `Cfg_HasZSO` | read/write (bidirectional) | BOOL | Open limit switch fitted |
| `Cfg_HasZSC` | read/write (bidirectional) | BOOL | Closed limit switch fitted |
| `Sts_NE107` | read | INT | NAMUR NE107 status: 0=Good 1=Failure (F) 2=Function check (C) 3=Out of specification (S) 4=Maintenance required (M) |
| `Alm_FailOpen/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_FailOpen/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_FailOpen/Cfg_Priority` | read | INT | Rationalised priority: 1=Emergency 2=High 3=Medium 4=Low |
| `Alm_FailClose/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_FailClose/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_FailClose/Cfg_Priority` | read | INT | Rationalised priority: 1=Emergency 2=High 3=Medium 4=Low |
| `Alm_PosConflict/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_PosConflict/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_PosConflict/Cfg_Priority` | read | INT | Rationalised priority: 1=Emergency 2=High 3=Medium 4=Low |
| `Alm_Uncmd/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_Uncmd/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_Uncmd/Cfg_Priority` | read | INT | Rationalised priority: 1=Emergency 2=High 3=Medium 4=Low |
| `Alm_IntlkTrip/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_IntlkTrip/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_IntlkTrip/Cfg_Priority` | read | INT | Rationalised priority: 1=Emergency 2=High 3=Medium 4=Low |
| `Run/Val_RunHrs` | read | REAL | Total run hours (display) |
| `Run/Val_Starts` | read | UDINT | Total starts / cycles |
| `Run/Val_StartsLastHr` | read | INT | Starts in the last 60 min (rolling) |
| `Run/Val_HrsSinceMaint` | read | REAL | Run hours since last maintenance reset |
| `Run/Sts_MaintDue` | read | BOOL | Maintenance due |
| `Sim_En` | read / write (toggle) | BOOL | Simulation: ignore field I/O, logic generates feedback |
| `Cfg_TravelTime` | read/write (bidirectional) | TIME | Maximum travel time before failure alarm |
| `Perm` | read | T_Intlk | Passed as tagPath to embedded IntlkList view |
| `Intlk` | read | T_Intlk | Passed as tagPath to embedded IntlkList view |
| `Mode/Cmd_Auto` | write | BOOL | Operator request Automatic (one-shot) |
| `Mode/Cmd_Man` | write | BOOL | Operator request Manual (one-shot) |
| `Mode/Cmd_Maint` | write | BOOL | Request Maintenance (one-shot) |
| `Mode/Cmd_OOS` | write | BOOL | Request Out-of-Service (one-shot) |
| `Cmd_Open` | write | BOOL | Operator open (one-shot) |
| `Cmd_Close` | write | BOOL | Operator close (one-shot) |
| `Cmd_Reset` | write | BOOL | Fault reset (one-shot) |
| `Run/Cmd_ResetMaint` | write | BOOL | Reset hours-since-maintenance (one-shot) |
| `Alm_FailOpen/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_FailClose/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_PosConflict/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_Uncmd/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_IntlkTrip/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |



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
      - `Hint` (ia.display.label)
  - `Feedback` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
    - `Body` (ia.container.flex)
      - `ZSO` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
      - `ZSC` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
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
      - `C1` (ia.input.checkbox)
      - `C2` (ia.input.checkbox)
```


## Notes and open questions

- **`tType` is never passed.** `efc.ui.openDynamic` sends only `tagPath`, so the dock's `tType` is always its default. Nothing here depends on it.
- **Commands do not check the device state.** OPEN and CLOSE are not disabled by `Sts_Opened`, `Sts_Closed`, `Sts_Fault` or `Mode/Sts_OOS`. The template's enable (`custom.canCmd`) checks OOS but not fault. The double-tap (`efc.ui.dblCmd`) checks fault but not OOS. The three rules differ.
- **RESET is always enabled at level 1 and above**, including outside MAN.
- **Mode buttons have no enable binding.** Clicking MAN or AUTO is always possible at level 1 and above, whatever the current state.
- **Configuration writes are not role-checked in script.** Their only guard is the UI enable expression. This is a binding-level write, not an `efc.ui` call.
- **Priority names differ from PCLib.** The dock maps `Cfg_Priority` 1 to `Critical`. The PCLib `T_Alarm` comment says 1 = Emergency. Both use the same style-class name pattern, so the displayed name may be wrong if the comment is the intent.
- **Trend expand is owned by the Trend part.** `expanded` is an `inout` param of `Docks/Parts/Trend`. This view only seeds it with `false` and resizes the embed from it.
- **`Cfg_TravelTime` units.** The PCLib member is `TIME`, which is held in milliseconds on the PLC. The dock labels the value `s` and reads and writes the raw tag value. Whether the tag delivers seconds or milliseconds depends on the OPC/tag configuration. Confirm this before commissioning.
- **Alarm rows** map `Cfg_Priority` through a `case()` with a default of `Medium`. Each row reads `Sts_Active` and `Sts_Unack` directly from its alarm member. The `Perm` and `Intlk` structures are shown by the embedded `IntlkList` views, which are not in this file.
- **Sts_State is not used.** The PCLib member `Sts_State` is not read by this view. The banner computes its own state from the feedback flags.
- **Parameter and style class names** (`Alarm/Critical/Unacked` and similar, `Button/Toggle/On`, etc.) are style classes defined elsewhere; their appearance was not checked.
- **Level thresholds** come from the constants in `efc.ui` (`OPERATOR=1`, `MAINT=2`, `SUPERVISOR=3`, `ENGINEER=4`). The dock uses 4 for Configuration editing, which matches `ENGINEER`.
