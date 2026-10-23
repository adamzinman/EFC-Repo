# Process value range bar (PV_RangeBar)

Covers `Templates/ProcessValues/PV_RangeBar` (design B2 in the PV design note).
Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/ProcessValues/PV_RangeBar/view.json`
Dynamic window it opens: `Templates/Dynamic Window/ProcessValues/ProcessValue` (dock `dw_ProcessValue`, chosen from `tType` `T_AI`; see [ProcessValue](../Dynamic%20Window/ProcessValues/ProcessValue.md)).
Context: [PV display design note](../../../pv-display.md). The sibling template is [PV_StatusStrip](PV_StatusStrip.md).

## Overview

A process value card for an analog input (`T_AI`) with a range track. The track shows the engineering range split into five bands (LL, L, normal, H, HH), coloured alarm overlays for the limits that are active, and a pointer at the PV. The header has the tag name and the same alarm letters as PV_StatusStrip. The value and units sit between the header and the track. The view is display only: it writes no tags.

- **Default size** (`props.defaultSize`): 104 x 54. The card is 100 x 50 inside the view (per the design note).
- **Bound to:** one T_AI instance through `params.tagPath`.
- **Opening the dock:** a single click runs `efc.ui.openDynamic(self)`, which maps `tType` (`T_AI`) to `dw_ProcessValue` and `Templates/Dynamic Window/ProcessValues/ProcessValue`, as described in PV_StatusStrip.
- **Generated view:** written by `generator/build_pv.py` to `projects/EFC_ProcessValues/`, not to `projects/EFC_Library/`. Check which copy is current before editing (see Notes).

## How it operates

**Alarm letters and blink.** The header letters work as in PV_StatusStrip: FLT, HH, H, L, LL, OVR, UNR, INH in order, at most two shown, with a `+N` overflow chip. The codes and blink rules are the same (see PV_StatusStrip, How it operates).

**Track bands.** The track is the range from `engMin` to `engMax`. The fractions `fLL`, `fL`, `fH` and `fHH` place the limits (each clamped to 0 to 1, and 0 when the range is zero or a limit is null). Five static bands are drawn: an extreme band from 0 to `fLL`, a low band to `fL`, a normal band to `fH`, a high band to `fHH`, and an extreme band to 1.

**Alarm overlays.** For each of LL, L, H and HH, an overlay sits over its band and shows while its code is 0 or more. Its colour is the priority class, with blink or the cleared style from the code. These overlays depend on the same alarm bindings as PV_StatusStrip (see Notes).

**Pointer.** The pointer sits at `fPV`, the PV as a fraction of the range, scaled by (1 - 0.09091) so the pointer stays inside the track. It is magenta when `badValue` is true.

**Tooltips.** The track tooltip gives the range (`Range <engMin> to <engMax> <units>`). The header tooltip gives `desc`.

**Value.** Same as PV_StatusStrip: PV to one decimal, or `---` when null, with `Value/BadQuality` when `badValue` is true.

**As the repo defines the type,** FLT, HH, H, L, LL, OVR and UNR never become active, for the same reason as PV_StatusStrip. In practice the track shows only the five static bands and the pointer, plus the INH chip when an inhibit is set.

**Click.** A single click opens the process value dock. The view writes no tag and checks no role.

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `tagPath` | input | `""` | Analog input (T_AI) instance. Every binding reads its members as `{view.params.tagPath}/<member>`. The PV design note calls it a `DDT_Process_Value` instance. | Caller. Read by all bindings and by `efc.ui.openDynamic`. |
| `tType` | input | `T_AI` | Type key. `efc.ui.openDynamic` maps it through `BY_TYPE` to the dock. | Read by `efc.ui.openDynamic` only. |
| `dockId` | input | `""` | Dock id that overrides the window chosen from `tType`. | Read by `efc.ui.openDynamic` only. |
| `dwTagPath` | input | `""` | Tag path passed to the dock instead of `tagPath` when non-empty. | Read by `efc.ui.openDynamic` only. |

All four have `paramDirection: input` and `persistent: true`. There are no output params. `docs/pv-display.md` says the only parameter is `tagPath`. The view also has `tType`, `dockId` and `dwTagPath`, which the click path reads.

### View-level custom properties (`custom`)

All 51 are bound (no script sets one). Tag bindings use mode `indirect` with a 2.5 s fallback delay. `{0}` resolves to `{view.params.tagPath}`. The first 40 match PV_StatusStrip. The last 11 are the range and limit values and the range fractions.

Tag mirrors fall into the groups below. The other 19 properties are expressions over them.

| Group | Members | Source | What it holds / drives |
|---|---|---|---|
| Value and names (tag mirrors) | `pv`, `name`, `desc`, `units`, `hwFault` | `{view.params.tagPath}/` + `Val_PV`, `Cfg_Tag`, `Cfg_Desc`, `Cfg_EU`, `Sts_Bad` | PV, instrument tag, description, units and the bad-PV flag (`hwFault`). |
| Inhibit flags (tag mirrors) | `inhHH`, `inhH`, `inhL`, `inhLL` | `{view.params.tagPath}/Alm_HH/Sts_Suppressed`, `Alm_H/...`, `Alm_L/...`, `Alm_LL/...` | Suppressed state of each limit alarm. Feed `inh`. |
| FLT raw alarm (tag mirrors) | `FLTact`, `FLTun`, `FLTpri` | `{view.params.tagPath}/Alm_Bad/Sts_Active`, `Alm_Bad/Sts_Unack`, `Alm_Bad/Cfg_Priority` | Raw state, unacknowledged flag and priority of the bad-PV alarm (`Alm_Bad`, T_Alarm). |
| HH, H, L, LL raw alarms (tag mirrors) | `HHact`/`HHun`/`HHpri`, `Hact`/`Hun`/`Hpri`, `Lact`/`Lun`/`Lpri`, `LLact`/`LLun`/`LLpri` | `{view.params.tagPath}/` + `Alm_HH/Sts_Active`, `Alm_HH/Sts_Unack`, `Alm_HH/Cfg_Priority`, `Alm_H/Sts_Active`, `Alm_H/Sts_Unack`, `Alm_H/Cfg_Priority`, `Alm_L/Sts_Active`, `Alm_L/Sts_Unack`, `Alm_L/Cfg_Priority`, `Alm_LL/Sts_Active`, `Alm_LL/Sts_Unack`, `Alm_LL/Cfg_Priority` | Raw state, unacknowledged flag and priority of each limit alarm (`Alm_HH`, `Alm_H`, `Alm_L`, `Alm_LL`, T_AlmLim). |
| OVR and UNR raw flags (tag mirrors) | `rOVR`, `rUNR` | `{view.params.tagPath}/Sts_ORng`, `{view.params.tagPath}/Sts_URng` | Raw over- and under-range flags (T_AI BOOL). |
| Limits and range (tag mirrors) | `engMin`, `engMax`, `spLL`, `spL`, `spH`, `spHH` | `Cfg_EUMin`, `Cfg_EUMax`, `Alm_LL/Cfg_Lim`, `Alm_L/Cfg_Lim`, `Alm_H/Cfg_Lim`, `Alm_HH/Cfg_Lim` | Scale minimum and maximum, and the four limits (EU), with defaults 0, 100, 10, 20, 80 and 90. |

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.tick` | `null` | expr | `now(1000)` | Ticks every 1000 ms (`now(1000)`). Not referenced by any binding in this view. See Notes. |
| `view.custom.aFLT` | `-1` | expr | `if(toBoolean(coalesce({view.custom.FLTact}, false)), if(toBoolean(coalesce({view.custom.FLTun}, false)), 10, 0) + case(toInt(coalesce({view.custom.FLTpri}, 3)), 1, 4, 2, 3, 3, 2, 4, 1, 2),   if(toBoolean(coalesce({view.custom.FLTun}, false)), 20 + case(toInt(coalesce({view.custom.FLTpri}, 3)), 1, 4, 2, 3, 3, 2, 4, 1, 2), -1))` | FLT code: -1 none, else state x 10 + priority (state 0 active and acked, 1 active and unacked, 2 cleared and unacked, which adds 20). Priority defaults to 2. |
| `view.custom.aHH` | `-1` | expr | `if(toBoolean(coalesce({view.custom.HHact}, false)), if(toBoolean(coalesce({view.custom.HHun}, false)), 10, 0) + case(toInt(coalesce({view.custom.HHpri}, 3)), 1, 4, 2, 3, 3, 2, 4, 1, 2),   if(toBoolean(coalesce({view.custom.HHun}, false)), 20 + case(toInt(coalesce({view.custom.HHpri}, 3)), 1, 4, 2, 3, 3, 2, 4, 1, 2), -1))` | HH code (same encoding as `aFLT`). |
| `view.custom.aH` | `-1` | expr | `if(toBoolean(coalesce({view.custom.Hact}, false)), if(toBoolean(coalesce({view.custom.Hun}, false)), 10, 0) + case(toInt(coalesce({view.custom.Hpri}, 3)), 1, 4, 2, 3, 3, 2, 4, 1, 2),   if(toBoolean(coalesce({view.custom.Hun}, false)), 20 + case(toInt(coalesce({view.custom.Hpri}, 3)), 1, 4, 2, 3, 3, 2, 4, 1, 2), -1))` | H code (same encoding as `aFLT`). |
| `view.custom.aL` | `-1` | expr | `if(toBoolean(coalesce({view.custom.Lact}, false)), if(toBoolean(coalesce({view.custom.Lun}, false)), 10, 0) + case(toInt(coalesce({view.custom.Lpri}, 3)), 1, 4, 2, 3, 3, 2, 4, 1, 2),   if(toBoolean(coalesce({view.custom.Lun}, false)), 20 + case(toInt(coalesce({view.custom.Lpri}, 3)), 1, 4, 2, 3, 3, 2, 4, 1, 2), -1))` | L code (same encoding as `aFLT`). |
| `view.custom.aLL` | `-1` | expr | `if(toBoolean(coalesce({view.custom.LLact}, false)), if(toBoolean(coalesce({view.custom.LLun}, false)), 10, 0) + case(toInt(coalesce({view.custom.LLpri}, 3)), 1, 4, 2, 3, 3, 2, 4, 1, 2),   if(toBoolean(coalesce({view.custom.LLun}, false)), 20 + case(toInt(coalesce({view.custom.LLpri}, 3)), 1, 4, 2, 3, 3, 2, 4, 1, 2), -1))` | LL code (same encoding as `aFLT`). |
| `view.custom.aOVR` | `-1` | expr | `if(toBoolean(coalesce({view.custom.rOVR}, false)), 0, -1)` | OVR code: 0 when `rOVR` is true, else -1. It has no acknowledge state, so it never blinks. |
| `view.custom.aUNR` | `-1` | expr | `if(toBoolean(coalesce({view.custom.rUNR}, false)), 0, -1)` | UNR code: 0 when `rUNR` is true, else -1. No acknowledge state. |
| `view.custom.fltActive` | `false` | expr | `{view.custom.aFLT} >= 0 && {view.custom.aFLT} < 20` | True when `aFLT` is 0 to 19, so an FLT alarm is active (acked or unacked). Drives the strip fault colour. |
| `view.custom.anyUnacked` | `false` | expr | `({view.custom.aFLT} >= 10 && {view.custom.aFLT} < 20) \|\| ({view.custom.aHH} >= 10 && {view.custom.aHH} < 20) \|\| ({view.custom.aH} >= 10 && {view.custom.aH} < 20) \|\| ({view.custom.aL} >= 10 && {view.custom.aL} < 20) \|\| ({view.custom.aLL} >= 10 && {view.custom.aLL} < 20) \|\| ({view.custom.aOVR} >= 10 && {view.custom.aOVR} < 20) \|\| ({view.custom.aUNR} >= 10 && {view.custom.aUNR} < 20)` | True when any code is 10 to 19 (active and unacknowledged). Drives the blink on the strip. |
| `view.custom.activePri` | `-1` | expr | `max(-1, if({view.custom.aHH} >= 0 && {view.custom.aHH} < 20, {view.custom.aHH} % 10, -1), if({view.custom.aH} >= 0 && {view.custom.aH} < 20, {view.custom.aH} % 10, -1), if({view.custom.aL} >= 0 && {view.custom.aL} < 20, {view.custom.aL} % 10, -1), if({view.custom.aLL} >= 0 && {view.custom.aLL} < 20, {view.custom.aLL} % 10, -1), if({view.custom.aOVR} >= 0 && {view.custom.aOVR} < 20, {view.custom.aOVR} % 10, -1), if({view.custom.aUNR} >= 0 && {view.custom.aUNR} < 20, {view.custom.aUNR} % 10, -1))` | Highest priority (0 to 4) among active codes 0 to 19. -1 when none. |
| `view.custom.clearedPri` | `-1` | expr | `max(-1, if({view.custom.aHH} >= 20, {view.custom.aHH} % 10, -1), if({view.custom.aH} >= 20, {view.custom.aH} % 10, -1), if({view.custom.aL} >= 20, {view.custom.aL} % 10, -1), if({view.custom.aLL} >= 20, {view.custom.aLL} % 10, -1), if({view.custom.aOVR} >= 20, {view.custom.aOVR} % 10, -1), if({view.custom.aUNR} >= 20, {view.custom.aUNR} % 10, -1))` | Highest priority among cleared and unacknowledged codes (20 and up). -1 when none. |
| `view.custom.inh` | `false` | expr | `toBoolean(coalesce({view.custom.inhHH}, false)) \|\| toBoolean(coalesce({view.custom.inhH}, false)) \|\| toBoolean(coalesce({view.custom.inhL}, false)) \|\| toBoolean(coalesce({view.custom.inhLL}, false))` | True when any of the four inhibit flags is true. Drives the INH chip. |
| `view.custom.badValue` | `false` | expr | `!isGood({view.custom.pv}) \|\| {view.custom.fltActive} \|\| toBoolean(coalesce({view.custom.hwFault}, false))` | True when `pv` is not good, `fltActive` is true, or `hwFault` is true. Drives the value style and the pointer colour. |
| `view.custom.fLL` | `0.1` | expr | `if({view.custom.engMax} = {view.custom.engMin} \|\| isNull({view.custom.spLL}), 0, max(0, min(1, ({view.custom.spLL} - {view.custom.engMin}) / ({view.custom.engMax} - {view.custom.engMin}))))` | LL limit as a fraction of the range, 0 to 1. 0 if the range is zero or the limit is null. |
| `view.custom.fL` | `0.2` | expr | `if({view.custom.engMax} = {view.custom.engMin} \|\| isNull({view.custom.spL}), 0, max(0, min(1, ({view.custom.spL} - {view.custom.engMin}) / ({view.custom.engMax} - {view.custom.engMin}))))` | L limit as a fraction of the range, 0 to 1. |
| `view.custom.fH` | `0.8` | expr | `if({view.custom.engMax} = {view.custom.engMin} \|\| isNull({view.custom.spH}), 0, max(0, min(1, ({view.custom.spH} - {view.custom.engMin}) / ({view.custom.engMax} - {view.custom.engMin}))))` | H limit as a fraction of the range, 0 to 1. |
| `view.custom.fHH` | `0.9` | expr | `if({view.custom.engMax} = {view.custom.engMin} \|\| isNull({view.custom.spHH}), 0, max(0, min(1, ({view.custom.spHH} - {view.custom.engMin}) / ({view.custom.engMax} - {view.custom.engMin}))))` | HH limit as a fraction of the range, 0 to 1. |
| `view.custom.fPV` | `0.5` | expr | `if({view.custom.engMax} = {view.custom.engMin} \|\| isNull({view.custom.pv}), 0, max(0, min(1, ({view.custom.pv} - {view.custom.engMin}) / ({view.custom.engMax} - {view.custom.engMin}))))` | PV as a fraction of the range, clamped to 0 to 1. 0 if the range is zero or PV is null. Drives the pointer. |

### Component-level custom properties

None.

### Session, page and message payloads

None read. The click loads the window into the `dw_Right` dock through `efc.ui.openDynamic`. See Scripts.

## Bindings reference

Total: **102 bindings** (51 at view root, 51 on components). View root: 32 tag, 19 expr. Components: 51 expr. No transforms.

### View root

The view-root bindings drive the custom properties. Each one is listed with its full source in View-level custom properties above.

### `root/Card`

Every component binding is in the table below, in tree order. The `Source` column gives the full expression.

#### `root/Card`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Card/HeaderRow/Tag` | `props.text` | expr | `if(isNull({view.custom.name}) \|\| len(toStr({view.custom.name})) = 0 \|\| toStr({view.custom.name}) = "null",   substring({view.params.tagPath}, max(lastIndexOf({view.params.tagPath}, "/"), lastIndexOf({view.params.tagPath}, "]")) + 1),   toStr({view.custom.name}))` | Header text: `name`, or the last segment of `tagPath` when `name` is blank or `null`. |
| `root/Card/HeaderRow/Tag` | `meta.tooltip.text` | expr | `if(isNull({view.custom.desc}) \|\| toStr({view.custom.desc}) = "null", "", toStr({view.custom.desc}))` | Tooltip: `desc`, blank when null. |
| `root/Card/HeaderRow/Chips/Chip_FLT` | `position.display` | expr | `({view.custom.aFLT} >= 0) && 0 < 2` | Visible while `aFLT` is 0 or more (active, or cleared and unacknowledged). FLT is the first letter, so no earlier letter counts. |
| `root/Card/HeaderRow/Chips/Chip_FLT` | `props.style.classes` | expr | `if({view.custom.aFLT} < 0, "PV/Chip/Fault", "PV/Chip/Fault" + if({view.custom.aFLT} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aFLT} >= 10, " Alarm/Mod/Blink", "")))` | `PV/Chip/Fault`, with `Alarm/Mod/Blink` when unacknowledged (10 to 19) or `Alarm/Mod/ClearedUnacked` (20 and up). |
| `root/Card/HeaderRow/Chips/Chip_HH` | `position.display` | expr | `({view.custom.aHH} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0)) < 2` | Visible while `aHH` is 0 or more (active, or cleared and unacknowledged) and fewer than two of the letters before it (FLT) are active. |
| `root/Card/HeaderRow/Chips/Chip_HH` | `props.style.classes` | expr | `if({view.custom.aHH} < 0, "", "PV/Chip/" + case({view.custom.aHH} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aHH} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aHH} >= 10, " Alarm/Mod/Blink", "")))` | Priority class from the code (`code % 10`: Critical, High, Medium, Low, Diagnostic). Adds `Alarm/Mod/Blink` for 10 to 19 and `Alarm/Mod/ClearedUnacked` for 20 and up. |
| `root/Card/HeaderRow/Chips/Chip_H` | `position.display` | expr | `({view.custom.aH} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0)) < 2` | Visible while `aH` is 0 or more (active, or cleared and unacknowledged) and fewer than two of the letters before it (FLT, HH) are active. |
| `root/Card/HeaderRow/Chips/Chip_H` | `props.style.classes` | expr | `if({view.custom.aH} < 0, "", "PV/Chip/" + case({view.custom.aH} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aH} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aH} >= 10, " Alarm/Mod/Blink", "")))` | Priority class from the code (`code % 10`: Critical, High, Medium, Low, Diagnostic). Adds `Alarm/Mod/Blink` for 10 to 19 and `Alarm/Mod/ClearedUnacked` for 20 and up. |
| `root/Card/HeaderRow/Chips/Chip_L` | `position.display` | expr | `({view.custom.aL} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0)) < 2` | Visible while `aL` is 0 or more (active, or cleared and unacknowledged) and fewer than two of the letters before it (FLT, HH, H) are active. |
| `root/Card/HeaderRow/Chips/Chip_L` | `props.style.classes` | expr | `if({view.custom.aL} < 0, "", "PV/Chip/" + case({view.custom.aL} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aL} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aL} >= 10, " Alarm/Mod/Blink", "")))` | Priority class from the code (`code % 10`: Critical, High, Medium, Low, Diagnostic). Adds `Alarm/Mod/Blink` for 10 to 19 and `Alarm/Mod/ClearedUnacked` for 20 and up. |
| `root/Card/HeaderRow/Chips/Chip_LL` | `position.display` | expr | `({view.custom.aLL} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0)) < 2` | Visible while `aLL` is 0 or more (active, or cleared and unacknowledged) and fewer than two of the letters before it (FLT, HH, H, L) are active. |
| `root/Card/HeaderRow/Chips/Chip_LL` | `props.style.classes` | expr | `if({view.custom.aLL} < 0, "", "PV/Chip/" + case({view.custom.aLL} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aLL} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aLL} >= 10, " Alarm/Mod/Blink", "")))` | Priority class from the code (`code % 10`: Critical, High, Medium, Low, Diagnostic). Adds `Alarm/Mod/Blink` for 10 to 19 and `Alarm/Mod/ClearedUnacked` for 20 and up. |
| `root/Card/HeaderRow/Chips/Chip_OVR` | `position.display` | expr | `({view.custom.aOVR} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0)) < 2` | Visible while `aOVR` is 0 or more (active, or cleared and unacknowledged) and fewer than two of the letters before it (FLT, HH, H, L, LL) are active. |
| `root/Card/HeaderRow/Chips/Chip_OVR` | `props.style.classes` | expr | `if({view.custom.aOVR} < 0, "", "PV/Chip/" + case({view.custom.aOVR} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aOVR} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aOVR} >= 10, " Alarm/Mod/Blink", "")))` | `PV/Chip/Diagnostic` when active (code 0). No blink or cleared modifier, because the code has no acknowledge state. |
| `root/Card/HeaderRow/Chips/Chip_UNR` | `position.display` | expr | `({view.custom.aUNR} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0) + if({view.custom.aOVR} >= 0, 1, 0)) < 2` | Visible while `aUNR` is 0 or more (active, or cleared and unacknowledged) and fewer than two of the letters before it (FLT, HH, H, L, LL, OVR) are active. |
| `root/Card/HeaderRow/Chips/Chip_UNR` | `props.style.classes` | expr | `if({view.custom.aUNR} < 0, "", "PV/Chip/" + case({view.custom.aUNR} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aUNR} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aUNR} >= 10, " Alarm/Mod/Blink", "")))` | `PV/Chip/Diagnostic` when active (code 0). No blink or cleared modifier, because the code has no acknowledge state. |
| `root/Card/HeaderRow/Chips/Chip_INH` | `position.display` | expr | `({view.custom.inh}) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0) + if({view.custom.aOVR} >= 0, 1, 0) + if({view.custom.aUNR} >= 0, 1, 0)) < 2` | Visible while `inh` is true and fewer than two of the letters before it (FLT, HH, H, L, LL, OVR, UNR) are active. |
| `root/Card/HeaderRow/Chips/Chip_More` | `position.display` | expr | `(if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0) + if({view.custom.aOVR} >= 0, 1, 0) + if({view.custom.aUNR} >= 0, 1, 0) + if({view.custom.inh}, 1, 0)) > 2` | Visible when more than two letters are active (INH counts). |
| `root/Card/HeaderRow/Chips/Chip_More` | `props.text` | expr | `"+" + toStr((if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0) + if({view.custom.aOVR} >= 0, 1, 0) + if({view.custom.aUNR} >= 0, 1, 0) + if({view.custom.inh}, 1, 0)) - 2)` | `+N`, where N is the number of active letters minus 2. |
| `root/Card/HeaderRow/Chips/Chip_More` | `props.style.classes` | expr | `"PV/Chip/More" + if(((({view.custom.aFLT} >= 0) && 0 >= 2) && {view.custom.aFLT} >= 10 && {view.custom.aFLT} < 20) \|\| ((({view.custom.aHH} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0)) >= 2) && {view.custom.aHH} >= 10 && {view.custom.aHH} < 20) \|\| ((({view.custom.aH} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0)) >= 2) && {view.custom.aH} >= 10 && {view.custom.aH} < 20) \|\| ((({view.custom.aL} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0)) >= 2) && {view.custom.aL} >= 10 && {view.custom.aL} < 20) \|\| ((({view.custom.aLL} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0)) >= 2) && {view.custom.aLL} >= 10 && {view.custom.aLL} < 20) \|\| ((({view.custom.aOVR} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0)) >= 2) && {view.custom.aOVR} >= 10 && {view.custom.aOVR} < 20) \|\| ((({view.custom.aUNR} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0) + if({view.custom.aOVR} >= 0, 1, 0)) >= 2) && {view.custom.aUNR} >= 10 && {view.custom.aUNR} < 20), " Alarm/Mod/Blink", "")` | `PV/Chip/More`, plus `Alarm/Mod/Blink` when a hidden letter (third or later) is unacknowledged. |
| `root/Card/HeaderRow/Chips/Chip_More` | `meta.tooltip.text` | expr | `"Also: " + if((({view.custom.aFLT} >= 0) && 0 >= 2), "FLT ", "") + if((({view.custom.aHH} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0)) >= 2), "HH ", "") + if((({view.custom.aH} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0)) >= 2), "H ", "") + if((({view.custom.aL} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0)) >= 2), "L ", "") + if((({view.custom.aLL} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0)) >= 2), "LL ", "") + if((({view.custom.aOVR} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0)) >= 2), "OVR ", "") + if((({view.custom.aUNR} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0) + if({view.custom.aOVR} >= 0, 1, 0)) >= 2), "UNR ", "") + if((({view.custom.inh}) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0) + if({view.custom.aOVR} >= 0, 1, 0) + if({view.custom.aUNR} >= 0, 1, 0)) >= 2), "INH ", "")` | Tooltip `Also:` followed by the hidden letters, in order (FLT, HH, H, L, LL, OVR, UNR, INH). |
| `root/Card/ValueRow/Value` | `props.text` | expr | `if(isNull({view.custom.pv}), "---", numberFormat({view.custom.pv}, "#,##0.0"))` | PV, one decimal, or `---` when PV is null. |
| `root/Card/ValueRow/Value` | `props.style.classes` | expr | `"PV/ValueSmall Text/Mod/NoWrap" + if({view.custom.badValue}, " Value/BadQuality", "")` | Value style. Adds `Value/BadQuality` when `badValue` is true. |
| `root/Card/ValueRow/Units` | `props.text` | expr | `if(isNull({view.custom.units}) \|\| toStr({view.custom.units}) = "null", "", toStr({view.custom.units}))` | Units text, blank when null or `null`. |
| `root/Card/Track` | `meta.tooltip.text` | expr | `"Range " + numberFormat({view.custom.engMin}, "#,##0.##") + " to " + numberFormat({view.custom.engMax}, "#,##0.##") + " " + if(isNull({view.custom.units}) \|\| toStr({view.custom.units}) = "null", "", toStr({view.custom.units}))` | Tooltip: `Range <engMin> to <engMax> <units>`. |
| `root/Card/Track/Band_LL` | `position.width` | expr | `max(0, {view.custom.fLL} - 0)` | Extreme band from 0 to `fLL` (static class `Bar/Band/Extreme`). |
| `root/Card/Track/Band_L` | `position.x` | expr | `{view.custom.fLL}` | Start of the low band, at `fLL`. |
| `root/Card/Track/Band_L` | `position.width` | expr | `max(0, {view.custom.fL} - {view.custom.fLL})` | Width of the low band, from `fLL` to `fL`. |
| `root/Card/Track/Band_N` | `position.x` | expr | `{view.custom.fL}` | Start of the normal band, at `fL`. |
| `root/Card/Track/Band_N` | `position.width` | expr | `max(0, {view.custom.fH} - {view.custom.fL})` | Width of the normal band, from `fL` to `fH`. |
| `root/Card/Track/Band_H` | `position.x` | expr | `{view.custom.fH}` | Start of the high band, at `fH`. |
| `root/Card/Track/Band_H` | `position.width` | expr | `max(0, {view.custom.fHH} - {view.custom.fH})` | Width of the high band, from `fH` to `fHH`. |
| `root/Card/Track/Band_HH` | `position.x` | expr | `{view.custom.fHH}` | Start of the extreme band, at `fHH`. |
| `root/Card/Track/Band_HH` | `position.width` | expr | `max(0, 1 - {view.custom.fHH})` | Width of the extreme band, from `fHH` to 1. |
| `root/Card/Track/Alarm_LL` | `position.display` | expr | `{view.custom.aLL} >= 0` | Overlay visible while `aLL` is 0 or more. |
| `root/Card/Track/Alarm_LL` | `position.width` | expr | `max(0, {view.custom.fLL} - 0)` | Overlay from 0 to `fLL`. |
| `root/Card/Track/Alarm_LL` | `props.style.classes` | expr | `if({view.custom.aLL} < 0, "", "Bar/Band/" + case({view.custom.aLL} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aLL} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aLL} >= 10, " Alarm/Mod/Blink", "")))` | Priority class of the LL overlay, with blink or the cleared modifier. |
| `root/Card/Track/Alarm_L` | `position.display` | expr | `{view.custom.aL} >= 0` | Overlay visible while `aL` is 0 or more. |
| `root/Card/Track/Alarm_L` | `position.width` | expr | `max(0, {view.custom.fL} - {view.custom.fLL})` | Overlay width, from `fLL` to `fL`. |
| `root/Card/Track/Alarm_L` | `props.style.classes` | expr | `if({view.custom.aL} < 0, "", "Bar/Band/" + case({view.custom.aL} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aL} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aL} >= 10, " Alarm/Mod/Blink", "")))` | Priority class of the L overlay, with blink or the cleared modifier. |
| `root/Card/Track/Alarm_L` | `position.x` | expr | `{view.custom.fLL}` | Overlay start, at `fLL`. |
| `root/Card/Track/Alarm_H` | `position.display` | expr | `{view.custom.aH} >= 0` | Overlay visible while `aH` is 0 or more. |
| `root/Card/Track/Alarm_H` | `position.width` | expr | `max(0, {view.custom.fHH} - {view.custom.fH})` | Overlay width, from `fH` to `fHH`. |
| `root/Card/Track/Alarm_H` | `props.style.classes` | expr | `if({view.custom.aH} < 0, "", "Bar/Band/" + case({view.custom.aH} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aH} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aH} >= 10, " Alarm/Mod/Blink", "")))` | Priority class of the H overlay, with blink or the cleared modifier. |
| `root/Card/Track/Alarm_H` | `position.x` | expr | `{view.custom.fH}` | Overlay start, at `fH`. |
| `root/Card/Track/Alarm_HH` | `position.display` | expr | `{view.custom.aHH} >= 0` | Overlay visible while `aHH` is 0 or more. |
| `root/Card/Track/Alarm_HH` | `position.width` | expr | `max(0, 1 - {view.custom.fHH})` | Overlay width, from `fHH` to 1. |
| `root/Card/Track/Alarm_HH` | `props.style.classes` | expr | `if({view.custom.aHH} < 0, "", "Bar/Band/" + case({view.custom.aHH} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aHH} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aHH} >= 10, " Alarm/Mod/Blink", "")))` | Priority class of the HH overlay, with blink or the cleared modifier. |
| `root/Card/Track/Alarm_HH` | `position.x` | expr | `{view.custom.fHH}` | Overlay start, at `fHH`. |
| `root/Card/Track/Pointer` | `position.x` | expr | `{view.custom.fPV} * (1 - 0.09091)` | Pointer left edge: `fPV` x (1 - 0.09091). Keeps the pointer inside the track. |
| `root/Card/Track/Pointer` | `props.source` | expr | `if({view.custom.badValue}, "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 12' preserveAspectRatio='none'><polygon points='0,0 8,0 4,5' fill='%23B000B0'/></svg>", "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 12' preserveAspectRatio='none'><polygon points='0,0 8,0 4,5' fill='%231F1F1F'/><rect x='2' y='5' width='4' height='7' fill='%23FFFFFF'/><rect x='3' y='5' width='2' height='7' fill='%231F1F1F'/></svg>")` | Pointer image (inline SVG data URI): magenta triangle when `badValue`, otherwise a dark triangle with a white-edged stem. |


## Scripts reference

Total: **1 event script**. No transforms, custom methods, message handlers or onChange scripts.

### Click script (`root`, `events.dom.onClick`, scope G)

Trigger: a single click on the view.

```python
	efc.ui.openDynamic(self)
```

It opens the dock for this tag. The library function is the same as PV_StatusStrip (`efc.ui.openDynamic`, see that document).

## Tag members used

Paths are relative to `tagPath`. Types and comments come from `types/PCLib_Members.csv`. No member is written.

| Member | Access | Data type | Meaning |
|---|---|---|---|
| `Val_PV` | read | REAL | Process value (EU), use this in logic |
| `Cfg_Tag` | read | STRING[20] | Equipment / instrument tag, e.g. FT-101 |
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Cfg_EU` | read | STRING[12] | Engineering units text |
| `Cfg_EUMin` | read | REAL | PV at 0% (EU) |
| `Cfg_EUMax` | read | REAL | PV at 100% (EU) |
| `Sts_Bad` | read | BOOL | PV bad (out of range or channel fault) |
| `Alm_LL/Cfg_Lim`, `Alm_L/Cfg_Lim`, `Alm_H/Cfg_Lim`, `Alm_HH/Cfg_Lim` | read | REAL | Alarm limit (EU) |
| `Alm_HH/Sts_Suppressed`, `Alm_H/Sts_Suppressed`, `Alm_L/Sts_Suppressed`, `Alm_LL/Sts_Suppressed` | read | BOOL | Suppressed by design (ISA-18.2 state G) |
| `Alm_Bad/Sts_Active`, `Alm_Bad/Sts_Unack`, `Alm_Bad/Cfg_Priority` | read | BOOL / BOOL / INT | Bad-PV alarm (`Alm_Bad`, T_Alarm): active, unacknowledged, priority. |
| `Alm_HH/Sts_Active`, `Alm_HH/Sts_Unack`, `Alm_HH/Cfg_Priority`, `Alm_H/Sts_Active`, `Alm_H/Sts_Unack`, `Alm_H/Cfg_Priority`, `Alm_L/Sts_Active`, `Alm_L/Sts_Unack`, `Alm_L/Cfg_Priority`, `Alm_LL/Sts_Active`, `Alm_LL/Sts_Unack`, `Alm_LL/Cfg_Priority` | read | BOOL / BOOL / INT | Limit alarms (T_AlmLim): active, unacknowledged, priority. |
| `Sts_ORng`, `Sts_URng` | read | BOOL | Over range, under range. |

Priority (`Cfg_Priority`): PCLib order, `1=Critical 2=High 3=Medium 4=Low`, converted to the internal rank in the `a*` code bindings; see PV_StatusStrip, Tag members used.

## Component tree

Indentation shows parent and child. Each entry is `name` (component type).

- `root` (`ia.container.flex`)
  - `Card` (`ia.container.flex`)
    - `HeaderRow` (`ia.container.flex`)
      - `Tag` (`ia.display.label`)
      - `Chips` (`ia.container.flex`)
        - `Chip_FLT` (`ia.display.label`)
        - `Chip_HH` (`ia.display.label`)
        - `Chip_H` (`ia.display.label`)
        - `Chip_L` (`ia.display.label`)
        - `Chip_LL` (`ia.display.label`)
        - `Chip_OVR` (`ia.display.label`)
        - `Chip_UNR` (`ia.display.label`)
        - `Chip_INH` (`ia.display.label`)
        - `Chip_More` (`ia.display.label`)
    - `ValueRow` (`ia.container.flex`)
      - `Value` (`ia.display.label`)
      - `Units` (`ia.display.label`)
    - `Track` (`ia.container.coord`)
      - `Band_LL` (`ia.display.label`)
      - `Band_L` (`ia.display.label`)
      - `Band_N` (`ia.display.label`)
      - `Band_H` (`ia.display.label`)
      - `Band_HH` (`ia.display.label`)
      - `Alarm_LL` (`ia.display.label`)
      - `Alarm_L` (`ia.display.label`)
      - `Alarm_H` (`ia.display.label`)
      - `Alarm_HH` (`ia.display.label`)
      - `Frame` (`ia.display.label`)
      - `Pointer` (`ia.display.image`)

## Notes and open questions

**Behaviour to review**

1. **Pointer is not exactly on the PV.** The pointer's left edge is `fPV x (1 - 0.09091)`, and its width is 0.09091 of the track. Its centre is `fPV x (1 - 0.09091) + 0.04545`, which equals `fPV` only at 0.5. The two ends of the track are offset by a few per cent.
2. **`tick` drives nothing.** Same as PV_StatusStrip: `docs/pv-display.md` describes a transform on `tick` that is not in this view.
3. **OVR and UNR never blink.** Same as PV_StatusStrip.
4. **Empty `tagPath` still opens the dock.** Same as PV_StatusStrip.

**Open questions**

- Should the pointer sit exactly on `fPV`, or is keeping it inside the track intended?
- Which copy is current: the `EFC_ProcessValues` project from `generator/build_pv.py`, or the EFC_Library `Templates/ProcessValues` views?

