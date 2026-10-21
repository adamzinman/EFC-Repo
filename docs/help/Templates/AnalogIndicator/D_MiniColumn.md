# Analog indicator: D_MiniColumn

Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/AnalogIndicator/D_MiniColumn/view.json`
Dynamic window it opens: `Docks/ProcessValue` (see [ProcessValue](../../Docks/ProcessValue.md)).

## Overview

A narrow vertical column for a single value. From top to bottom: a header (tag label or short description), the value and units, a vertical bar with the pointer on its right, and the chip at the bottom. The view is display-only.

- **Default size:** 64 x 200 (`props.defaultSize`).
- **Bound to:** one T_KPI instance through `params.tagPath`. The default is `[default]KPI/KPI_101`, which is not in `tags/` (see Notes).
- **Opening the dock:** a single click on the whole view runs `efc.ui.openDynamic(self)`. `tType` defaults to `T_KPI`, and `efc.ui.BY_TYPE` maps `T_KPI` to `dw_ProcessValue`, which `efc.ui.WINDOWS` maps to `Docks/ProcessValue`. The screen's `Docks/Region` shows that dock with `tagPath` (or `dwTagPath` when set).
- **Generated view:** this view is written by `generator/analog_indicators/gen_analog_indicators.py`, which builds `build/analog/EFC_AnalogIndicators.zip`. Change the generator, not `view.json`, or the next build replaces the edit.
- **Siblings:** the other three templates (A to D) share the same view-level custom properties, tag mirrors, and click script. Only the params and the component tree differ (checked by diffing the four `view.json` files).

## How it operates

**Layout.** Top to bottom: header, value box, units, the bar (`root/Bar`), and the chip row. The bar is a row with the track on the left and the pointer column on the right. Both are `column-reverse`, so low values are at the bottom.

**Header.** As in C: `Header` = `Desc` shows `Cfg_ShortDesc`, falling back to `Cfg_Desc`. Otherwise `Cfg_Tag`.

**Value.** `Val_PV` with `Format`, in the medium size class and centred, with units `Cfg_EU` below.

**Quality.** `Sts_Quality` maps to `q`: 0 Good, 1 Uncertain (simulation), 2 Bad. `good` is true unless `q` is 2. When bad, the pointer is hidden (`meta.visible`), the value box takes `Indicator/Analog/ValueBox` plus `Value/BadQuality`, and the chip shows the bad text in `ChipBad` style. When simulated (`q` = 1) and no limit is active, the value box takes `Value/Simulated`.

**Limits and alarms.** The four PCLib limits (`Alm_HH`, `Alm_LL`, `Alm_H`, `Alm_L`) are read from their `Sts_Active`, `Sts_Unack` and `Cfg_Priority` members. The view does not use Ignition alarm pipelines. `lvl` takes the first active level in the order HH, LL, H, L, and only that level is shown. Its `Cfg_Priority` sets the colour: 1 Critical `#D50000`, 2 High `#FF7A00`, 3 Medium `#FFD200`, 4 Low `#00A3E0`. With no limit active the pointer is `#1F1F1F`. The order is by limit level, not by `Cfg_Priority`: an active L alarm with priority 1 is hidden while an H alarm with priority 4 is active. The chip shows `HH`, `HI`, `LL` or `LO`, as in C.

**Zones and pointer.** As in A, but vertical: the segments use the same classes, and the pointer moves up the bar. The pointer is hidden when quality is bad.

**Ideal band, range and clamping.** Same as A.

**Click.** A single click opens `Docks/ProcessValue` through `efc.ui.openDynamic`, which writes the page's `session.custom.efcDw` entry shown by `Docks/Region` (see Scripts). No role level is checked, nothing is audited, and no tag is written.

**Acknowledgement.** The view shows `Sts_Unack` but binds no `Cmd_Ack`, `Cmd_Reset` or `Cmd_Shelve`. It does not write to the tag. An unacknowledged level uses the `/Unacked` alarm class on the chip, and an acknowledged one uses `/Fill`.

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `[default]KPI/KPI_101` | T_KPI instance. Every tag binding reads `{view.params.tagPath}`. Not in `tags/` (see Notes). | Caller. Read by all tag bindings and by `efc.ui.openDynamic`. |
| `Header` | input | `Tag` | `Desc` shows the short description, falling back to the description (see Notes). Any other value shows the tag label. | Caller. Read by the header text binding `root/Header`. |
| `Format` | input | `#,##0.0` | Number format for the value (`numberFormat`). | Caller. Read by `custom.valText` only. |
| `tType` | input | `T_KPI` | Type key for the dock. `efc.ui.openDynamic` uses it, through `BY_TYPE`, to pick the window. | Read by `efc.ui.openDynamic` only. No binding in this view reads it. |
| `dockId` | input | `""` | Overrides the window chosen from `tType`. Must be a key of `efc.ui.WINDOWS`. | Read by `efc.ui.openDynamic` only. |
| `dwTagPath` | input | `""` | Tag path passed to the dock instead of `tagPath`, when non-empty. | Read by `efc.ui.openDynamic` only. |

All params have `paramDirection: input` and `persistent: true`. No output params.

### View-level custom properties (`custom`)

There are 60 view-level custom properties. All default to `null` in the JSON. All 60 have a binding, so no script sets them. 30 are tag mirrors (below). The other 30 are derived expressions, listed here. These 60 are identical in all four templates.

| Path | Default | Binding | Source (full expression) | What it holds / drives |
|---|---|---|---|---|
| `view.custom.good` | `null` | expr | `{view.custom.q} != 2` | True unless quality is 2 (Bad). Drives pointer visibility (`meta.visible`), the bad-quality chip and the `Value/BadQuality` class. |
| `view.custom.span` | `null` | expr | `max({view.custom.max} - {view.custom.min}, 0.000001)` | Display range `Cfg_EUMax - Cfg_EUMin`, floored at 0.000001 to avoid divide-by-zero. |
| `view.custom.p` | `null` | expr | `min(max(({view.custom.pv} - {view.custom.min}) / {view.custom.span}, 0), 1) * 100` | Pointer position: value as a percent of the display range, clamped 0 to 100. |
| `view.custom.pLL` | `null` | expr | `min(max(({view.custom.ll} - {view.custom.min}) / {view.custom.span}, 0), 1) * 100` | LL limit as a percent of the range, clamped 0 to 100. |
| `view.custom.pL` | `null` | expr | `min(max(({view.custom.l} - {view.custom.min}) / {view.custom.span}, 0), 1) * 100` | L limit as a percent of the range, clamped 0 to 100. |
| `view.custom.pH` | `null` | expr | `min(max(({view.custom.h} - {view.custom.min}) / {view.custom.span}, 0), 1) * 100` | H limit as a percent of the range, clamped 0 to 100. |
| `view.custom.pHH` | `null` | expr | `min(max(({view.custom.hh} - {view.custom.min}) / {view.custom.span}, 0), 1) * 100` | HH limit as a percent of the range, clamped 0 to 100. |
| `view.custom.pIL` | `null` | expr | `if({view.custom.iLo} < {view.custom.iHi}, min(max(({view.custom.iLo} - {view.custom.min}) / {view.custom.span}, 0), 1) * 100, {view.custom.pL})` | Ideal band low as a percent. Equal to `pL` when the ideal band is off (`Cfg_IdealLo >= Cfg_IdealHi`). |
| `view.custom.pIH` | `null` | expr | `if({view.custom.iLo} < {view.custom.iHi}, min(max(({view.custom.iHi} - {view.custom.min}) / {view.custom.span}, 0), 1) * 100, {view.custom.pL})` | Ideal band high as a percent. Equal to `pL` when the ideal band is off. |
| `view.custom.lvl` | `null` | expr | `if({view.custom.hhA}, 'HH', if({view.custom.llA}, 'LL', if({view.custom.hA}, 'H', if({view.custom.lA}, 'L', ''))))` | Active limit level in the order HH, LL, H, L (first active wins), or `""` when none is active. Selects which priority and unack flag are used. |
| `view.custom.almUnack` | `null` | expr | `case({view.custom.lvl}, 'HH', {view.custom.hhU}, 'LL', {view.custom.llU}, 'H', {view.custom.hU}, 'L', {view.custom.lU}, false)` | Unacknowledged flag (`Sts_Unack`) of the level in `lvl`; `false` when none. |
| `view.custom.almPri` | `null` | expr | `case({view.custom.lvl}, 'HH', {view.custom.hhP}, 'LL', {view.custom.llP}, 'H', {view.custom.hP}, 'L', {view.custom.lP}, 3)` | `Cfg_Priority` (1 to 4) of the level in `lvl`; 3 when none. |
| `view.custom.pri` | `null` | expr | `case(toInt({view.custom.almPri}), 1, 'Critical', 2, 'High', 3, 'Medium', 4, 'Low', 'Medium')` | Priority name: 1 `Critical`, 2 `High`, 3 `Medium`, 4 `Low`; anything else `Medium`. |
| `view.custom.almCls` | `null` | expr | `if({view.custom.lvl} = '', '', 'Alarm/' + {view.custom.pri} + if({view.custom.almUnack}, '/Unacked', '/Fill'))` | Alarm class `Alarm/<pri>/Unacked` or `Alarm/<pri>/Fill` for the level in `lvl`; `""` when none. |
| `view.custom.ptrColor` | `null` | expr | `if({view.custom.lvl} = '', '#1F1F1F', case({view.custom.pri}, 'Critical', '#D50000', 'High', '#FF7A00', 'Medium', '#FFD200', 'Low', '#00A3E0', '#6E6E6E'))` | Pointer colour: `#1F1F1F` when no limit is active; otherwise Critical `#D50000`, High `#FF7A00`, Medium `#FFD200`, Low `#00A3E0`. |
| `view.custom.valCls` | `null` | expr | `'Indicator/Analog/ValueBox' + if(!{view.custom.good}, ' Value/BadQuality', if({view.custom.lvl} != '', ' Alarm/' + {view.custom.pri} + '/Outline', if({view.custom.q} = 1, ' Value/Simulated', '')))` | Value box classes: `Indicator/Analog/ValueBox`, plus `Value/BadQuality` when bad, else the `Alarm/<pri>/Outline` class when a limit is active, else `Value/Simulated` when quality is 1. |
| `view.custom.valText` | `null` | expr | `numberFormat({view.custom.pv}, {view.params.Format})` | Value text: `Val_PV` formatted with the `Format` parameter. |
| `view.custom.chipVis` | `null` | expr | `!{view.custom.good} \|\| {view.custom.lvl} != ''` | Chip visible when quality is bad or any limit is active. |
| `view.custom.chipCls` | `null` | expr | `'Indicator/Analog/Chip ' + if(!{view.custom.good}, 'Indicator/Analog/ChipBad', {view.custom.almCls})` | Chip classes: `Indicator/Analog/Chip` plus `ChipBad` when bad, else the active alarm class (`almCls`). |
| `view.custom.zLL` | `null` | expr | `max({view.custom.pLL}, 0) + '%'` | Width of the LL segment (string, percent): `max(pLL, 0)`. |
| `view.custom.zL` | `null` | expr | `max({view.custom.pL} - {view.custom.pLL}, 0) + '%'` | Width of the L segment: `max(pL - pLL, 0)`. |
| `view.custom.zW1` | `null` | expr | `max({view.custom.pIL} - {view.custom.pL}, 0) + '%'` | Width of the gap from L to the ideal low limit: `max(pIL - pL, 0)`. |
| `view.custom.zI` | `null` | expr | `max({view.custom.pIH} - {view.custom.pIL}, 0) + '%'` | Width of the ideal band: `max(pIH - pIL, 0)`. |
| `view.custom.zW2` | `null` | expr | `max({view.custom.pH} - {view.custom.pIH}, 0) + '%'` | Width of the gap from the ideal high limit to H: `max(pH - pIH, 0)`. |
| `view.custom.zH` | `null` | expr | `max({view.custom.pHH} - {view.custom.pH}, 0) + '%'` | Width of the H segment: `max(pHH - pH, 0)`. |
| `view.custom.zHH` | `null` | expr | `max(100 - {view.custom.pHH}, 0) + '%'` | Width of the HH segment: `max(100 - pHH, 0)`. |
| `view.custom.cLL` | `null` | expr | `if({view.custom.lvl} = 'LL', {view.custom.almCls}, if({view.custom.llEn}, 'Indicator/Analog/ZoneLL', if({view.custom.lEn}, 'Indicator/Analog/ZoneL', 'Indicator/Analog/ZoneNormal')))` | Colour class of the LL segment: alarm class if LL is the active level; else `ZoneLL` if LL enabled, `ZoneL` if only L enabled, else `ZoneNormal`. |
| `view.custom.cL` | `null` | expr | `if({view.custom.lvl} = 'L', {view.custom.almCls}, if({view.custom.lEn}, 'Indicator/Analog/ZoneL', 'Indicator/Analog/ZoneNormal'))` | Colour class of the L segment: alarm class if L is active; else `ZoneL` if L enabled, else `ZoneNormal`. |
| `view.custom.cH` | `null` | expr | `if({view.custom.lvl} = 'H', {view.custom.almCls}, if({view.custom.hEn}, 'Indicator/Analog/ZoneL', 'Indicator/Analog/ZoneNormal'))` | Colour class of the H segment: alarm class if H is active; else `ZoneL` if H enabled, else `ZoneNormal`. |
| `view.custom.cHH` | `null` | expr | `if({view.custom.lvl} = 'HH', {view.custom.almCls}, if({view.custom.hhEn}, 'Indicator/Analog/ZoneLL', if({view.custom.hEn}, 'Indicator/Analog/ZoneL', 'Indicator/Analog/ZoneNormal')))` | Colour class of the HH segment: alarm class if HH is active; else `ZoneLL` if HH enabled, `ZoneL` if only H enabled, else `ZoneNormal`. |

#### Tag mirrors (`custom.*`)

The other 30 custom properties are plain tag mirrors. Each is a `tag` binding in `indirect` mode on `{1}/<member>` with reference `1` = `{view.params.tagPath}` and `fallbackDelay` 2.5. None is bidirectional, and none has a default (`null`). The table below lists them by group.

| Group | Custom properties (`view.custom.*`) | Tag member (`{1}/`) |
|---|---|---|
| Scalars | `pv`, `eu`, `desc`, `sdesc`, `tag`, `min`, `max`, `iLo`, `iHi`, `q` | `Val_PV`, `Cfg_EU`, `Cfg_Desc`, `Cfg_ShortDesc`, `Cfg_Tag`, `Cfg_EUMin`, `Cfg_EUMax`, `Cfg_IdealLo`, `Cfg_IdealHi`, `Sts_Quality` |
| LL limit | `ll`, `llEn`, `llA`, `llU`, `llP` | `Alm_LL/Cfg_Lim`, `Alm_LL/Cfg_En`, `Alm_LL/Sts_Active`, `Alm_LL/Sts_Unack`, `Alm_LL/Cfg_Priority` |
| L limit | `l`, `lEn`, `lA`, `lU`, `lP` | `Alm_L/Cfg_Lim`, `Alm_L/Cfg_En`, `Alm_L/Sts_Active`, `Alm_L/Sts_Unack`, `Alm_L/Cfg_Priority` |
| H limit | `h`, `hEn`, `hA`, `hU`, `hP` | `Alm_H/Cfg_Lim`, `Alm_H/Cfg_En`, `Alm_H/Sts_Active`, `Alm_H/Sts_Unack`, `Alm_H/Cfg_Priority` |
| HH limit | `hh`, `hhEn`, `hhA`, `hhU`, `hhP` | `Alm_HH/Cfg_Lim`, `Alm_HH/Cfg_En`, `Alm_HH/Sts_Active`, `Alm_HH/Sts_Unack`, `Alm_HH/Cfg_Priority` |

### Component-level custom properties

None. No component in this view carries a `custom` property.

### Session, page and message payloads

- **Writes:** `session.custom.efcDw[<pageId>]` = `{path, params}` through `efc.ui.openDynamic`, on click only. The `path` is `Docks/ProcessValue` and `params` holds `tagPath`.
- **Reads:** none. The template reads no `session.*` or `page.*` value.
- **Messages:** none sent or handled.

## Bindings reference

Total: **81 bindings** (60 at view root in `custom.*`, 21 on components). Types: 51 `expr`, 30 `tag`. No transforms. `params.*` entries have `paramDirection` only and are not bindings.

### View root

The view-root bindings drive the custom properties. Each one is listed with its full source in **View-level custom properties** above.

### `root/Header`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Header` | `props.text` | expr | `if({view.params.Header} = 'Desc', coalesce({view.custom.sdesc}, {view.custom.desc}), {view.custom.tag})` | Header text. When `Header` is `Desc`: `Cfg_ShortDesc`, or `Cfg_Desc` when ShortDesc is null (see Notes). Otherwise `Cfg_Tag`. |

### `root/Value`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Value` | `props.text` | expr | `{view.custom.valText}` | Value text (`valText`): `Val_PV` formatted with the `Format` parameter. |
| `root/Value` | `props.style.classes` | expr | `{view.custom.valCls} + ' Text/Size/M Text/Mod/Center'` | Value box classes (`valCls`), with the size or position classes from the expression. Adds `Text/Size/M Text/Mod/Center`. |

### `root/Units`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Units` | `props.text` | expr | `{view.custom.eu}` | Engineering units `Cfg_EU`. |

### `root/Bar`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Bar/Track/ZoneLL` | `position.basis` | expr | `{view.custom.zLL}` | Width of the LL segment: 0 to `pLL`. |
| `root/Bar/Track/ZoneLL` | `props.style.classes` | expr | `{view.custom.cLL}` | Colour of the LL segment (`cLL`). Alarm class when LL is the active level; otherwise `ZoneLL` if LL is enabled, `ZoneL` if only L is enabled, else `ZoneNormal`. |
| `root/Bar/Track/ZoneL` | `position.basis` | expr | `{view.custom.zL}` | Width of the L segment: `pLL` to `pL`. |
| `root/Bar/Track/ZoneL` | `props.style.classes` | expr | `{view.custom.cL}` | Colour of the L segment (`cL`). Alarm class when L is active; otherwise `ZoneL` if L is enabled, else `ZoneNormal`. |
| `root/Bar/Track/ZoneW1` | `position.basis` | expr | `{view.custom.zW1}` | Width of the gap from L to the ideal low limit. Zero when the ideal band is off or starts at or below L. Static class `ZoneNormal`. |
| `root/Bar/Track/ZoneI` | `position.basis` | expr | `{view.custom.zI}` | Width of the ideal band, `pIL` to `pIH`. Zero when the ideal band is off. Static class `ZoneIdeal`. |
| `root/Bar/Track/ZoneW2` | `position.basis` | expr | `{view.custom.zW2}` | Width of the gap from the ideal high limit to H. Static class `ZoneNormal`. |
| `root/Bar/Track/ZoneH` | `position.basis` | expr | `{view.custom.zH}` | Width of the H segment: `pH` to `pHH`. |
| `root/Bar/Track/ZoneH` | `props.style.classes` | expr | `{view.custom.cH}` | Colour of the H segment (`cH`). Alarm class when H is active; otherwise `ZoneL` if H is enabled, else `ZoneNormal`. |
| `root/Bar/Track/ZoneHH` | `position.basis` | expr | `{view.custom.zHH}` | Width of the HH segment: `pHH` to 100. |
| `root/Bar/Track/ZoneHH` | `props.style.classes` | expr | `{view.custom.cHH}` | Colour of the HH segment (`cHH`). Alarm class when HH is active; otherwise `ZoneLL` if HH is enabled, `ZoneL` if only H is enabled, else `ZoneNormal`. |
| `root/Bar/PtrCol/PtrOffset` | `position.basis` | expr | `{view.custom.p} + '%'` | Moves the pointer to the value: `p` percent along the scale. |
| `root/Bar/PtrCol/Pointer` | `props.elements[0].fill.paint` | expr | `{view.custom.ptrColor}` | Pointer colour (`ptrColor`): `#1F1F1F` when no limit is active; otherwise the priority colour of the active level. |
| `root/Bar/PtrCol/Pointer` | `meta.visible` | expr | `{view.custom.good}` | Pointer shown only while quality is good (`good`). |

### `root/ChipRow`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/ChipRow/Chip` | `props.text` | expr | `if(!{view.custom.good}, 'BAD', case({view.custom.lvl}, 'HH', 'HH', 'H', 'HI', 'L', 'LO', 'LL', 'LL', ''))` | Alarm text. `BAD` when quality is bad; otherwise `HH`, `HI`, `LL` or `LO` for the active level; blank when none. |
| `root/ChipRow/Chip` | `props.style.classes` | expr | `{view.custom.chipCls}` | Chip classes (`chipCls`): `Indicator/Analog/Chip`, plus `ChipBad` when quality is bad, else the active alarm class (`Alarm/<Pri>/Unacked` or `/Fill`). |
| `root/ChipRow/Chip` | `position.display` | expr | `{view.custom.chipVis}` | Chip shown when quality is bad or any limit is active (`chipVis`). |

## Scripts reference

Total: **1 event script**, no `customMethods`, no `messageHandlers`, no property-change scripts, no script transforms. `view.scripts` is absent.

1. **`root`**: `events.dom.onClick` on `root`, scope G.
   Opens the dynamic window for this tag. Calls `efc.ui.openDynamic`, which writes `session.custom.efcDw` (see below). No tag writes, no role check, no audit.

```python
	efc.ui.openDynamic(self)
```

### Library functions called by this view (`efc.ui`, `projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.openDynamic(component)`**: uses `dockId` if set, else `BY_TYPE[tType]`. With the default `tType` `T_KPI` that is `dw_ProcessValue`, which maps to `Docks/ProcessValue`. If no window is found, it logs a warning and returns. Otherwise it takes the tag path from `dwTagPath`, then `tagPath`, then `cardPath`, and calls `_write`. `_write` updates `session.custom.efcDw[pageId]` with `path` and `params:{tagPath}`. `openDynamic` adds `model` to `params` only when that param is set. The existing `default` entry for the page is kept. It does not read the user's role, does not write a tag, and does not audit.
- **`efc.ui.level` / `userLevel`**: not called by this view.
- **`efc.ui.closeDynamic`**: not called by this view. The dock's close button calls it.

## Tag members used

All paths are relative to `tagPath`. Every member is read. There are no writes and no bidirectional bindings. Types and comments for the `Cfg_`, `Val_` and `Sts_` members come from `types/T_KPI/T_KPI_Ignition81.json` (T_KPI is not in `types/PCLib_Members.csv`). The `Alm_*` members are `T_AlmLim`, taken from `types/PCLib_Members.csv`.

| Member | Access | Data type | Meaning |
|---|---|---|---|
| `Val_PV` | read | Float4 | KPI value (EU) after filter / simulation - use this in logic and HMI (`types/T_KPI/T_KPI_Ignition81.json`) |
| `Cfg_EU` | read | String | Engineering units text (`types/T_KPI/T_KPI_Ignition81.json`) |
| `Cfg_Desc` | read | String | Description shown on HMI faceplate (`types/T_KPI/T_KPI_Ignition81.json`) |
| `Cfg_ShortDesc` | read | String | Short description for compact HMI headers (max 11 chars) (`types/T_KPI/T_KPI_Ignition81.json`) |
| `Cfg_Tag` | read | String | Equipment / instrument tag, e.g. FT-101 (`types/T_KPI/T_KPI_Ignition81.json`) |
| `Cfg_EUMin` | read | Float4 | Display range low (EU) (`types/T_KPI/T_KPI_Ignition81.json`) |
| `Cfg_EUMax` | read | Float4 | Display range high (EU) (`types/T_KPI/T_KPI_Ignition81.json`) |
| `Cfg_IdealLo` | read | Float4 | Ideal band low (EU), blue zone on HMI. Band off if Cfg_IdealLo >= Cfg_IdealHi (`types/T_KPI/T_KPI_Ignition81.json`) |
| `Cfg_IdealHi` | read | Float4 | Ideal band high (EU) (`types/T_KPI/T_KPI_Ignition81.json`) |
| `Sts_Quality` | read | Int2 | 0=Good 1=Uncertain (simulation) 2=Bad (`types/T_KPI/T_KPI_Ignition81.json`) |
| `Alm_LL/Cfg_Lim` | read | REAL | Alarm limit (EU), from rationalisation / master alarm database (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_LL/Cfg_En` | read | BOOL | Alarm enabled, set TRUE once Cfg_Lim is rationalised (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_LL/Sts_Active` | read | BOOL | Alarm active (after delays and latch) (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_LL/Sts_Unack` | read | BOOL | Alarm unacknowledged (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_LL/Cfg_Priority` | read | INT | Rationalised priority: 1=Emergency 2=High 3=Medium 4=Low (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_L/Cfg_Lim` | read | REAL | Alarm limit (EU), from rationalisation / master alarm database (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_L/Cfg_En` | read | BOOL | Alarm enabled, set TRUE once Cfg_Lim is rationalised (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_L/Sts_Active` | read | BOOL | Alarm active (after delays and latch) (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_L/Sts_Unack` | read | BOOL | Alarm unacknowledged (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_L/Cfg_Priority` | read | INT | Rationalised priority: 1=Emergency 2=High 3=Medium 4=Low (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_H/Cfg_Lim` | read | REAL | Alarm limit (EU), from rationalisation / master alarm database (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_H/Cfg_En` | read | BOOL | Alarm enabled, set TRUE once Cfg_Lim is rationalised (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_H/Sts_Active` | read | BOOL | Alarm active (after delays and latch) (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_H/Sts_Unack` | read | BOOL | Alarm unacknowledged (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_H/Cfg_Priority` | read | INT | Rationalised priority: 1=Emergency 2=High 3=Medium 4=Low (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_HH/Cfg_Lim` | read | REAL | Alarm limit (EU), from rationalisation / master alarm database (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_HH/Cfg_En` | read | BOOL | Alarm enabled, set TRUE once Cfg_Lim is rationalised (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_HH/Sts_Active` | read | BOOL | Alarm active (after delays and latch) (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_HH/Sts_Unack` | read | BOOL | Alarm unacknowledged (`T_AlmLim`, `types/PCLib_Members.csv`) |
| `Alm_HH/Cfg_Priority` | read | INT | Rationalised priority: 1=Emergency 2=High 3=Medium 4=Low (`T_AlmLim`, `types/PCLib_Members.csv`) |

## Component tree

- `root` (ia.container.flex) [event: dom.onClick]
  - `Header` (ia.display.label)
  - `Value` (ia.display.label)
  - `Units` (ia.display.label)
  - `Bar` (ia.container.flex)
    - `Track` (ia.container.flex)
      - `ZoneLL` (ia.container.flex)
      - `ZoneL` (ia.container.flex)
      - `ZoneW1` (ia.container.flex)
      - `ZoneI` (ia.container.flex)
      - `ZoneW2` (ia.container.flex)
      - `ZoneH` (ia.container.flex)
      - `ZoneHH` (ia.container.flex)
    - `PtrCol` (ia.container.flex)
      - `PtrOffset` (ia.container.flex)
      - `Pointer` (ia.shapes.svg)
  - `ChipRow` (ia.container.flex)
    - `Chip` (ia.display.label)

## Notes and open questions

1. **Short-description fallback.** The same `coalesce(Cfg_ShortDesc, Cfg_Desc)` issue as C.
2. **Chip text differs from A and B.** This view shows `BAD`, `HH`, `HI`, `LO` and `LL`, as in C.
3. **Narrow width.** The column is 64 px wide and the value is in the medium size class. Whether a long value fits was not checked.
4. **Dock mismatch (likely defect).** `Docks/ProcessValue`, which this view opens, binds `Cfg_RawMin`, `Cfg_RawMax` and `Val_ROC` (read), and `Sim_PV`, `Cfg_RawMin` and `Cfg_RawMax` as bidirectional entries (write). `types/T_KPI/T_KPI_Ignition81.json` defines none of `Cfg_RawMin`, `Cfg_RawMax`, `Val_ROC` or `Sim_PV`. It has `Sim_Value` and no raw-channel members. For a KPI tag those dock bindings have no member to read, and the entries cannot write. This was checked from the dock JSON only. The dock's own help page (`docs/help/Docks/ProcessValue.md`) records the same problem in its Notes.
5. **Default tag path.** `[default]KPI/KPI_101` is a placeholder. Nothing under `tags/` defines a KPI instance.
6. **T_KPI is preliminary.** `types/T_KPI/README.md` calls it proposed, and the JSON is marked preliminary. It is not in `types/PCLib_Members.csv`. Its FB (`FB_KPI`), which would write `Val_PV`, `Sts_Quality` and the alarm flags, is still to be written. `Cfg_ShortDesc` is documented as max 11 characters in the JSON and as `STRING[12]` in the README.
7. **Zone widths are not checked.** Nothing checks that LL <= L <= H <= HH, or that the ideal band lies between L and H. If the ideal low limit (`Cfg_IdealLo`) is below the L limit, the zone widths sum to more than 100%, by `pL - pIL`. If the ideal high limit (`Cfg_IdealHi`) is above the H limit, they sum to more, by `pIH - pH`. How the browser renders this overflow was not checked.
8. **Disabled limits still move zone edges.** `pLL`, `pL`, `pH` and `pHH` use the limit value whether or not its enable flag is set. A disabled limit is not coloured, but its position still sets the width of the segments beside it.
9. **Alarm state is shown without the shelve, suppress or out-of-service flags.** The view reads `Sts_Active` and `Sts_Unack` only. It does not read `Sts_Shelved`, `Sts_Suppressed` or `Sts_OOS`. Whether those alarms disappear depends on whether the PLC logic clears `Sts_Active`. Not verified.
10. **Null handling is not verified.** All 60 custom properties default to `null`. `good` (`q != 2`) and `valText` (`numberFormat(pv, Format)`) have no `coalesce`. Their behaviour before the first read, or when a member is missing, was not tested in Designer.
11. **Alarm class definitions are not in this repo.** The `Alarm/<Pri>/Fill`, `/Unacked` and `/Outline` classes are used by the chip and the value box. `generator/analog_indicators/gen_analog_indicators.py` defines the `Indicator/Analog/*` classes but not these. `views/Styles/_Catalog/view.json` uses them as samples. Their colours were not checked.
12. **Priority naming.** `pri` labels priority 1 as `Critical`. The PCLib comment for `Cfg_Priority` calls 1 `Emergency`. The order is consistent, only the label differs.
13. **No tag label fallback.** The tag label has no fallback to the last segment of `tagPath`, unlike the valve templates. A blank `Cfg_Tag` gives a blank label.
14. **No acknowledgement or commands.** The view is display-only. Acknowledgement is not available here.
15. **No role check.** The click does not read the user's role level. Whether `Docks/ProcessValue` enforces roles for its own write entries was not checked here.
16. **Documentation drift.** `CHANGES-analog-indicators.md` (dated 2026-10-20) says there is no dynamic window yet, and places the views in `projects/EFC_AnalogIndicators/`. The copies checked here are under `projects/EFC_Library/`, and the click does open a window.
