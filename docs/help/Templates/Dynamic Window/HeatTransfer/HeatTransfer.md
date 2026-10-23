# Templates/Dynamic Window/HeatTransfer/HeatTransfer

Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/Dynamic Window/HeatTransfer/HeatTransfer/view.json`

Opened from: **no shipped template.** `efc.ui.BY_TYPE` maps the template `tType` `T_HeatEx` to dynamic window `dw_HeatTransfer`, but no template under `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/` sets `tType` to `T_HeatEx`, and none sets `dockId` to `dw_HeatTransfer`. The heat exchanger template `HX_AirCooled` (see [Rotating_Discrete](../../Rotating/Rotating_Discrete.md)) defaults to `tType` `T_Motor` and opens `Templates/Dynamic Window/Rotating/Rotating`. The window is reached only when a template sets `tType` to `T_HeatEx` or `dockId` to `dw_HeatTransfer` in its own params.

## Overview

The monitoring window for a heat exchanger (T_HeatEx). It is read-only: it has no commands, no mode buttons, no interlock or permissive lists and no maintenance section. It shows the four temperatures and two flows, the calculated duty, LMTD, UA, cleanliness, approach and effectiveness, five alarms, a trend and the configuration. It opens in the screen's right-hand region (`Docks/Region`), not as a popup.

- **Default size:** 400 x 860 (`props.defaultSize`). The root is a scrolling column.
- **Parameters:** `tagPath` (the T_HeatEx instance) and `tType` (default `T_HeatEx`).
- **How it is opened:** the template's single click runs `efc.ui.openDynamic(self)`. That function writes `session.custom.efcDw[pageId] = {path: 'Templates/Dynamic Window/HeatTransfer/HeatTransfer', params: {tagPath: ...}}`, and `Docks/Region` displays this view. `efc.ui.openDynamic` passes only `tagPath` (and `model` if present). **`tType` is never passed**, so the window always runs with its default `T_HeatEx`. Nothing in this view uses `tType`.
- **Generated view:** this view is written by `generator/docks/build_docks.py` (function `heat_transfer()`). Running that function in memory reproduces the committed `view.json` exactly. Change the generator, not `view.json`, or the next build overwrites the edit.
- **How it closes:** the header `X` runs `efc.ui.closeDynamic(self)`, which restores the screen default set by `efc.ui.setDefaultDock` on `Docks/Region` startup. That startup script is not in this view.

## How it operates

**Header.** Shows `Cfg_Tag` (large) and `Cfg_Desc`. The `X` button closes the window.

**Banner.** `Sts_CalcValid` selects the state text: `CALC VALID` (style `State/Running`) when true, otherwise `CALC INVALID` (style `State/Unknown`). The banner has no SIM, LOCAL, INTLK or NOT PERM badges.

**Values** (all levels). Twelve read-only rows, all formatted `#,##0.0` (effectiveness is multiplied by 100 first): hot in and hot out (`Inp_HotInT`, `Inp_HotOutT`, unit °C), cold in and cold out (`Inp_ColdInT`, `Inp_ColdOutT`, °C), hot flow and cold flow (`Inp_HotFlow`, `Inp_ColdFlow`, no unit shown), duty (`Val_Duty`, kW), LMTD (`Val_LMTD`, K), UA (`Val_UA`, kW/K), cleanliness (`Val_Clean`, %), approach (`Val_Approach`, K) and effectiveness (`Val_Effect`, a 0-1 fraction shown as a percentage: value x 100, unit %). The values are not gated by `Sts_CalcValid`, so the banner and the values can disagree (see the notes).

**Alarms** (all levels). Five rows: Fouling (`Alm_Fouling`), Hot side dP high (`Alm_HotDP`), Cold side dP high (`Alm_ColdDP`), Heat balance error (`Alm_HeatBal`) and Outlet temperature high (`Alm_HiOutT`). A row is coloured when its alarm is active, using the alarm's `Cfg_Priority`: 1 `Critical`, 2 `High`, 3 `Medium`, 4 `Low`, anything else `Medium`. The class adds `/Unacked` or `/Fill`. An inactive but unacknowledged alarm uses `Alarm/Status/ClearedUnacked`. An inactive, acknowledged alarm uses `Text/Caption Text/Color/Muted`. "No active alarms" is shown when none is active. **ACK** (level 1 and above) calls `efc.ui.ackAll`, which writes `Cmd_Ack` only for the alarms whose `Sts_Unack` is true.

**Trend.** Embeds `Templates/Dynamic Window/Parts/Trend` ([Parts/Trend](../Parts/Trend.md)) with pens `Val_Clean` and `Val_UA`, over the window's tag. The embedded view's `expanded` param starts `false`. The Trend part toggles it itself, and the `position.basis` binding grows the trend from 15.741 vh to 70.370 vh. The expansion is local to the trend and does not widen the dock region. Both pens are plotted on one shared scale (see the notes).

**Configuration** (collapsible; the header click toggles `open_Configuration`, collapsed at start). Seven items: design UA (`Cfg_DesignUA`, kW/K), minimum flow (`Cfg_MinFlow`), calculation filter (`Cfg_CalcFilt`, s), fouling limit (`Alm_Fouling/Cfg_Lim`, %), hot side dP limit (`Alm_HotDP/Cfg_Lim`), cold side dP limit (`Alm_ColdDP/Cfg_Lim`) and outlet temperature limit (`Alm_HiOutT/Cfg_Lim`, °C). Below level 4 each is a read-only row. At level 4 and above each is an entry bound bidirectionally to the tag. The entries' enable expression is the literal `true`. Their visibility is what limits them to level 4. Writes are not audited.

**Role checks.** All role levels come from the Perspective session (`session.props.auth.user.roles`), mapped by `efc.ui.level`. Only ACK checks the level in script (inside `efc.ui.ackAll`). The configuration entries are protected by visibility only. Bindings do not check the level. Real access control has to be enforced in Perspective security and the PLC logic.

**Audit.** None. This view makes no `efc.ui.cmd` call with `audit=True`, and `efc.ui.ackAll` does not audit. Configuration writes go straight to the tags and are not audited.

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `""` | T_HeatEx instance. Every component binding uses `{view.params.tagPath}`. | Set by `efc.ui.openDynamic` from the template's `dwTagPath` (or `tagPath`). Read by bindings, by `efc.ui.ackAll` and by the Trend embed. |
| `tType` | input | `T_HeatEx` | Declared type. | Not passed by `efc.ui.openDynamic`; not referenced by any binding or script in this view. Always the default. |

Both have `paramDirection: input` and `persistent: true`. No output parameters.

### View-level custom properties (`custom`)

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.level` | `0` | property + script transform | `session.props.auth.user.roles` → `return efc.ui.level(value)` | Role level 0-5 from `session.props.auth.user.roles` via `efc.ui.level`. Gates the ACK button and the configuration entries (level 4). |
| `view.custom.open_Configuration` | `false` | none (written by script) | none | View-local toggle for the Configuration section. Set by the header click script; not bound to any tag; not persisted. |

#### Tag mirrors (`custom.m_*`)

There are 37 tag-mirror properties. Each `custom.m_<member>` (with `/` replaced by `_`) has an indirect, read-only tag binding to `{view.params.tagPath}/<member>` (`bidirectional: false`, fallback delay 2.5 s), and its default is `null`. The read-only display rows read tag values through these mirrors. The configuration entries and the ACK script read the tags directly.

| Group | Members |
|---|---|
| Identity | `Cfg_Tag`, `Cfg_Desc` |
| Status | `Sts_CalcValid` |
| Inputs | `Inp_HotInT`, `Inp_HotOutT`, `Inp_ColdInT`, `Inp_ColdOutT`, `Inp_HotFlow`, `Inp_ColdFlow` |
| Calculated values | `Val_Duty`, `Val_LMTD`, `Val_UA`, `Val_Clean`, `Val_Approach`, `Val_Effect` |
| Config | `Cfg_DesignUA`, `Cfg_MinFlow`, `Cfg_CalcFilt`, `Alm_Fouling/Cfg_Lim`, `Alm_HotDP/Cfg_Lim`, `Alm_ColdDP/Cfg_Lim`, `Alm_HiOutT/Cfg_Lim` |
| Alarms | `Alm_Fouling`, `Alm_HotDP`, `Alm_ColdDP`, `Alm_HeatBal`, `Alm_HiOutT`: each with `/Sts_Active`, `/Sts_Unack` and `/Cfg_Priority` (`Alm_HeatBal` has no `Cfg_Lim` mirror) |

### Component-level custom properties

None.

### Session, page and message payloads

- `session.props.auth.user.roles`: read by `custom.level` (transform `efc.ui.level`).
- `session.props.auth.user.userName`: read by `efc.ui._audit` (not bound in this view).
- `session.custom.efcDw[pageId]`: written by `efc.ui.openDynamic` and `closeDynamic` in the template and header; read by `Docks/Region` (not in this file).
- `page.props.pageId`: read by `efc.ui._state` to key `efcDw`.
- No message handlers. No `customMethods`.

## Bindings reference

Total: **119 bindings**: 38 at view root (all `custom.*`, including 1 `property` binding with a transform) and 81 on components (74 `expr`, 7 `tag`). Types overall: 74 `expr`, 44 `tag`, 1 `property`. `params.tagPath` and `params.tType` have `paramDirection` only, so they are not counted.

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
| root/Banner | `props.style.classes` | expr | `if({view.custom.m_Sts_CalcValid}, 'State/Running', if(true, 'State/Unknown', 'State/Unknown'))` | CSS class(es) selected by state |
| root/Banner/State | `props.text` | expr | `if({view.custom.m_Sts_CalcValid}, 'CALC VALID', if(true, 'CALC INVALID', 'UNKNOWN'))` | Text content |

### `root/Values`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Values/Body/HI/Val | `props.text` | expr | `numberFormat({view.custom.m_Inp_HotInT}, '#,##0.0')` | Text content |
| root/Values/Body/HI/EU | `props.text` | expr | `'°C'` | Text content |
| root/Values/Body/HO/Val | `props.text` | expr | `numberFormat({view.custom.m_Inp_HotOutT}, '#,##0.0')` | Text content |
| root/Values/Body/HO/EU | `props.text` | expr | `'°C'` | Text content |
| root/Values/Body/CI/Val | `props.text` | expr | `numberFormat({view.custom.m_Inp_ColdInT}, '#,##0.0')` | Text content |
| root/Values/Body/CI/EU | `props.text` | expr | `'°C'` | Text content |
| root/Values/Body/CO/Val | `props.text` | expr | `numberFormat({view.custom.m_Inp_ColdOutT}, '#,##0.0')` | Text content |
| root/Values/Body/CO/EU | `props.text` | expr | `'°C'` | Text content |
| root/Values/Body/HF/Val | `props.text` | expr | `numberFormat({view.custom.m_Inp_HotFlow}, '#,##0.0')` | Text content |
| root/Values/Body/HF/EU | `props.text` | expr | `''` | Text content |
| root/Values/Body/CF/Val | `props.text` | expr | `numberFormat({view.custom.m_Inp_ColdFlow}, '#,##0.0')` | Text content |
| root/Values/Body/CF/EU | `props.text` | expr | `''` | Text content |
| root/Values/Body/Duty/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Duty}, '#,##0.0')` | Text content |
| root/Values/Body/Duty/EU | `props.text` | expr | `'kW'` | Text content |
| root/Values/Body/LMTD/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_LMTD}, '#,##0.0')` | Text content |
| root/Values/Body/LMTD/EU | `props.text` | expr | `'K'` | Text content |
| root/Values/Body/UA/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_UA}, '#,##0.0')` | Text content |
| root/Values/Body/UA/EU | `props.text` | expr | `'kW/K'` | Text content |
| root/Values/Body/Clean/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Clean}, '#,##0.0')` | Text content |
| root/Values/Body/Clean/EU | `props.text` | expr | `'%'` | Text content |
| root/Values/Body/App/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Approach}, '#,##0.0')` | Text content |
| root/Values/Body/App/EU | `props.text` | expr | `'K'` | Text content |
| root/Values/Body/Eff/Val | `props.text` | expr | `numberFormat({view.custom.m_Val_Effect} * 100, '#,##0.0')` | Text content |
| root/Values/Body/Eff/EU | `props.text` | expr | `'%'` | Text content |

### `root/Alarms`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| root/Alarms/Body/None | `position.display` | expr | `!({view.custom.m_Alm_Fouling_Sts_Active} \|\| {view.custom.m_Alm_HotDP_Sts_Active} \|\| {view.custom.m_Alm_ColdDP_Sts_Active} \|\| {view.custom.m_Alm_HeatBal_Sts_Active} \|\| {view.custom.m_Alm_HiOutT_Sts_Active})` | Shown while expression is true |
| root/Alarms/Body/List/A0 | `props.style.classes` | expr | `if({view.custom.m_Alm_Fouling_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_Fouling_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_Fouling_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_Fouling_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A1 | `props.style.classes` | expr | `if({view.custom.m_Alm_HotDP_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_HotDP_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_HotDP_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_HotDP_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A2 | `props.style.classes` | expr | `if({view.custom.m_Alm_ColdDP_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_ColdDP_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_ColdDP_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_ColdDP_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A3 | `props.style.classes` | expr | `if({view.custom.m_Alm_HeatBal_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_HeatBal_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_HeatBal_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_HeatBal_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
| root/Alarms/Body/List/A4 | `props.style.classes` | expr | `if({view.custom.m_Alm_HiOutT_Sts_Active}, 'Alarm/' + case(toInt({view.custom.m_Alm_HiOutT_Cfg_Priority}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium') + if({view.custom.m_Alm_HiOutT_Sts_Unack}, '/Unacked', '/Fill'), if({view.custom.m_Alm_HiOutT_Sts_Unack}, 'Alarm/Status/ClearedUnacked', 'Text/Caption Text/Color/Muted'))` | CSS class(es) selected by state |
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
| root/Configuration/Body/R0/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_DesignUA}, '#,##0.###')` | Text content |
| root/Configuration/Body/R0/EU | `props.text` | expr | `'kW/K'` | Text content |
| root/Configuration/Body/E0 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E0/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_DesignUA` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E0/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R1 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R1/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_MinFlow}, '#,##0.###')` | Text content |
| root/Configuration/Body/R1/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E1 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E1/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_MinFlow` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E1/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R2 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R2/Val | `props.text` | expr | `numberFormat({view.custom.m_Cfg_CalcFilt}, '#,##0.###')` | Text content |
| root/Configuration/Body/R2/EU | `props.text` | expr | `'s'` | Text content |
| root/Configuration/Body/E2 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E2/Entry | `props.value` | tag (indirect) | tag `{0}/Cfg_CalcFilt` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E2/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R3 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R3/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_Fouling_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Configuration/Body/R3/EU | `props.text` | expr | `'%'` | Text content |
| root/Configuration/Body/E3 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E3/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_Fouling/Cfg_Lim` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E3/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R4 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R4/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_HotDP_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Configuration/Body/R4/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E4 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E4/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_HotDP/Cfg_Lim` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E4/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R5 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R5/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_ColdDP_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Configuration/Body/R5/EU | `props.text` | expr | `''` | Text content |
| root/Configuration/Body/E5 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E5/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_ColdDP/Cfg_Lim` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E5/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |
| root/Configuration/Body/R6 | `position.display` | expr | `!({view.custom.level} >= 4)` | Shown while expression is true |
| root/Configuration/Body/R6/Val | `props.text` | expr | `numberFormat({view.custom.m_Alm_HiOutT_Cfg_Lim}, '#,##0.###')` | Text content |
| root/Configuration/Body/R6/EU | `props.text` | expr | `'°C'` | Text content |
| root/Configuration/Body/E6 | `position.display` | expr | `{view.custom.level} >= 4` | Shown while expression is true |
| root/Configuration/Body/E6/Entry | `props.value` | tag (indirect) | tag `{0}/Alm_HiOutT/Cfg_Lim` (bidirectional); refs {"0": "{view.params.tagPath}"} | Read/write tag value |
| root/Configuration/Body/E6/Entry | `props.enabled` | expr | `true` | Enabled while expression is true |

## Scripts reference

Total: **4 scripts**: 3 event scripts (2 `component.onActionPerformed`, 1 `dom.onClick`) and 1 transform script (`custom.level`). No `customMethods`, no `messageHandlers`, no property-change `onChange` scripts.

The button handlers call `efc.ui` functions, which are summarised after the list.

1. **`root/Header/Close`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.closeDynamic(self)
```

2. **`root/Alarms/Body/Ack`**: `events.component.onActionPerformed`, scope G.

```python
	efc.ui.ackAll(self, ['Alm_Fouling', 'Alm_HotDP', 'Alm_ColdDP', 'Alm_HeatBal', 'Alm_HiOutT'])
```

3. **`root/Configuration/Header`**: `events.dom.onClick`, scope G.

```python
	self.view.custom.open_Configuration = not self.view.custom.open_Configuration
```

4. **transform on `(view root)` `custom.level`**: `custom.level` binding, `property` source `session.props.auth.user.roles`.

```python
	return efc.ui.level(value)
```

### Explanation of each handler

| Handler | Action | Writes | Role check | Audit |
|---|---|---|---|---|
| `Header/Close` | `efc.ui.closeDynamic` restores the default region view | none | none | no |
| `Alarms/Ack` | `efc.ui.ackAll` on the five alarms | `Alm_*/Cmd_Ack`, only where `Sts_Unack` is true | level 1 (in `efc.ui.ackAll`) | no |
| `Configuration/Header` (dom click) | toggles `open_Configuration` | none | none | no |

This view has no `efc.ui.cmd` calls. The configuration entries and checkboxes are direct bidirectional bindings, with no script between the control and the tag.

### Library functions used (`projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.level(roles)`**: highest index of the role in `['Guest','Operator','Maintenance','Supervisor','Engineer','Admin']`, or 0. Bound to `custom.level`.
- **`efc.ui.closeDynamic(component)`**: writes `efcDw[pageId]` back to the stored `default` path and params. Writes no tags.
- **`efc.ui.ackAll(component, alarms)`**: returns unless the user is at level 1 or above. Reads `<alarm>/Sts_Unack` for the listed alarms, then writes `<alarm>/Cmd_Ack` = True for those that are true. No audit.
- **`efc.ui.cmd`, `bypass`, `unbypass`, `dblCmd`**: not called from this view. `efc.ui.trend` is called by the Trend part, not here.

## Tag members used

All paths are relative to `tagPath`. Types and meanings are taken verbatim from `types/PCLib_Members.csv` (type `T_HeatEx`; alarm members from `T_AlmLim`). Trend pens are read through tag history by the Trend part.

| Member | Access (read/write) | Data type | Meaning |
|---|---|---|---|
| `Cfg_CalcFilt` | read/write (bidirectional) | REAL | Filter time constant for calculated values (s) |
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Cfg_DesignUA` | read/write (bidirectional) | REAL | Clean design UA (kW/K) |
| `Cfg_MinFlow` | read/write (bidirectional) | REAL | Below this flow the calculations are frozen (kg/s) |
| `Cfg_Tag` | read | STRING[20] | Equipment / instrument tag, e.g. FT-101 |
| `Sts_CalcValid` | read | BOOL | Inputs valid, calculations live |
| `Inp_ColdFlow` | read | REAL | Cold side mass flow (kg/s) |
| `Inp_ColdInT` | read | REAL | Cold side inlet temperature (degC) |
| `Inp_ColdOutT` | read | REAL | Cold side outlet temperature (degC) |
| `Inp_HotFlow` | read | REAL | Hot side mass flow (kg/s) |
| `Inp_HotInT` | read | REAL | Hot side inlet temperature (degC) |
| `Inp_HotOutT` | read | REAL | Hot side outlet temperature (degC) |
| `Val_Approach` | read | REAL | Approach temperature (K) |
| `Val_Clean` | read; also read by trend pens | REAL | Cleanliness: UA as % of design |
| `Val_Duty` | read | REAL | Average duty (kW) |
| `Val_Effect` | read | REAL | Thermal effectiveness (0-1); displayed x 100 as % |
| `Val_LMTD` | read | REAL | Log mean temperature difference (K) |
| `Val_UA` | read; also read by trend pens | REAL | Actual UA (kW/K) |
| `Alm_ColdDP/Cfg_Lim` | read/write (bidirectional) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Alm_ColdDP/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_ColdDP/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_ColdDP/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_ColdDP/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_Fouling/Cfg_Lim` | read/write (bidirectional) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Alm_Fouling/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_Fouling/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_Fouling/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_Fouling/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_HeatBal/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_HeatBal/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_HeatBal/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_HeatBal/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_HiOutT/Cfg_Lim` | read/write (bidirectional) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Alm_HiOutT/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_HiOutT/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_HiOutT/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_HiOutT/Sts_Unack` | read | BOOL | Alarm unacknowledged |
| `Alm_HotDP/Cfg_Lim` | read/write (bidirectional) | REAL | Alarm limit (EU) - from rationalisation / master alarm database |
| `Alm_HotDP/Cfg_Priority` | read | INT | Rationalised priority: 1=Critical 2=High 3=Medium 4=Low |
| `Alm_HotDP/Cmd_Ack` | write (ackAll, only unacked) | BOOL | Operator acknowledge (one-shot) |
| `Alm_HotDP/Sts_Active` | read | BOOL | Alarm active (after delays and latch) |
| `Alm_HotDP/Sts_Unack` | read | BOOL | Alarm unacknowledged |

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
  - `Values` (ia.container.flex)
    - `Header` (ia.container.flex)
      - `Title` (ia.display.label)
    - `Body` (ia.container.flex)
      - `HI` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `HO` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `CI` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `CO` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `HF` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `CF` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Duty` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `LMTD` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `UA` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Clean` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `App` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
      - `Eff` (ia.container.flex)
        - `Lbl` (ia.display.label)
        - `Val` (ia.display.label)
        - `EU` (ia.display.label)
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

- **Not reachable from the shipped templates.** The window is generated and bound to `T_HeatEx`, but no template in the library sets `tType` to `T_HeatEx`, and no template sets `dockId` to `dw_HeatTransfer`. The only heat exchanger template, `HX_AirCooled`, has `tType` `T_Motor` and opens `Templates/Dynamic Window/Rotating/Rotating`. Confirm whether `HX_AirCooled` should be switched to `T_HeatEx`, or whether a separate heat exchanger template is planned.
- **Shared trend scale.** `efc.ui.trend` computes one low and one high limit over all pens. `Val_Clean` (%) and `Val_UA` (kW/K) therefore share one axis, and the axis labels apply to both. The two pens have different units and may differ greatly in magnitude, so one can look flat. Consider one trend per pen, or confirm that the magnitudes are comparable.
- **Flow units.** `Inp_HotFlow` and `Inp_ColdFlow` are documented as kg/s in PCLib, but they are shown with no unit. `Cfg_MinFlow` is also shown with no unit, although PCLib gives it as kg/s.
- **Values are not gated by CALC VALID.** When `Sts_CalcValid` is false the banner reads CALC INVALID, but the calculated rows still show their values. This view does not show whether the PLC holds the last valid results. Confirm the intended behaviour.
- **Members not shown.** `Inp_HotDP`, `Inp_ColdDP`, `Val_DutyHot`, `Val_DutyCold`, `Val_HeatBal`, `Cfg_HotCp`, `Cfg_ColdCp` and `Cfg_CounterFlow` are defined in `T_HeatEx` but not displayed. The dP alarms (`Alm_HotDP`, `Alm_ColdDP`) act on dP values that this view never shows. The heat balance alarm (`Alm_HeatBal`) has no value row and no `Cfg_Lim` row, so its limit cannot be seen or changed from the dock.
- **Configuration writes are not role-checked in script and not audited.** The only guard is the level 4 visibility of the entries. Design UA and the four alarm limits can be changed with no audit entry. ValveDiscrete audits its maintenance and simulate actions, so this is inconsistent. Confirm whether limit changes must be audited.
- **Dp limit units.** The hot and cold dP limit rows show no unit. The PLC comment for `Inp_HotDP` gives kPa, but the limit members themselves are documented only as "Alarm limit (EU)". Confirm the units of `Alm_HotDP/Cfg_Lim` and `Alm_ColdDP/Cfg_Lim`.
