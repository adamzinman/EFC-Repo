# Process value status strip (PV_StatusStrip)

Covers `Templates/ProcessValues/PV_StatusStrip` (design A1 in the PV design note).
Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/ProcessValues/PV_StatusStrip/view.json`
Dynamic window it opens: `Templates/Dynamic Window/ProcessValues/ProcessValue` (dock `dw_ProcessValue`, chosen from `tType` `T_AI`; see [ProcessValue](../Dynamic%20Window/ProcessValues/ProcessValue.md)).
Context: [PV display design note](../../../pv-display.md). The sibling template is [PV_RangeBar](PV_RangeBar.md).

## Overview

A process value card for an analog input (`T_AI`). It shows a coloured status strip on the left edge, the tag name, up to two alarm letters with a `+N` overflow chip, and the PV value with its units. The strip and the letters take their colour from the alarm priority. The view is display only: it writes no tags.

- **Default size** (`props.defaultSize`): 104 x 54. The card is 100 x 50 inside the view, so the shell margin keeps the shadow from clipping (per the design note).
- **Bound to:** one T_AI instance through `params.tagPath`. The bindings use the T_AI member names listed under Tag members used.
- **Opening the dock:** a single click runs `efc.ui.openDynamic(self)`. It maps `tType` (`T_AI`) through `BY_TYPE` to `dw_ProcessValue` and writes `session.custom.efcDw[pageId] = {path: 'Templates/Dynamic Window/ProcessValues/ProcessValue', params: {tagPath}}`. `dwTagPath` replaces `tagPath` when set, and `dockId` overrides the window.
- **Generated view:** written by `generator/build_pv.py`, which writes the project to `projects/EFC_ProcessValues/`, not to `projects/EFC_Library/`. Check which copy is current before editing (see Notes).

## How it operates

**Strip (left edge).** The strip colour is chosen in this order: (1) fault, if an FLT alarm is active (`fltActive`), blinking if any alarm is unacknowledged; (2) the highest active priority, blinking if any alarm is unacknowledged; (3) a cleared fault, or a cleared priority, shown with the cleared-but-unacknowledged style; (4) otherwise `PV/Strip/Normal`.

**Alarm letters.** The letters are FLT, HH, H, L, LL, OVR, UNR and INH, in that order. A letter is visible when its code is 0 or more (active, or cleared and unacknowledged). At most two letters show. Each further active letter is counted in a `+N` chip, whose tooltip (`Also:`) names the hidden letters. `+N` blinks if a hidden letter is unacknowledged. INH shows when any limit alarm is suppressed (`inh`).

**Alarm codes.** Each alarm has one code: -1 for none; otherwise `state` x 10 + `priority`, where state 0 is active and acknowledged, 1 is active and unacknowledged, and 2 is cleared and unacknowledged (which adds 20 rather than 10). `priority` is the template's internal rank, 0 to 4, which maps to Diagnostic, Low, Medium, High and Critical in the class names. The PLC `Cfg_Priority` (PCLib: 1 Critical, 2 High, 3 Medium, 4 Low) is converted to that rank where it is read: `case(toInt(coalesce(pri, 3)), 1, 4, 2, 3, 3, 2, 4, 1, 2)`, so a missing or out-of-range value reads as Medium (rank 2). Diagnostic (0) is used only for the range chips. Blink is applied for 10 to 19, and the cleared modifier for 20 and up.

**Value.** The PV shows one decimal, or `---` when PV is null. `badValue` is true when PV is not good, an FLT alarm is active, or `hwFault` (`Sts_Bad`) is true. It adds the `Value/BadQuality` style. It does not change the strip.

**As the repo defines the type,** the FLT, HH, H, L, LL, OVR and UNR codes never leave -1, because their bindings point at members that T_AI does not have (see Notes). In practice the strip stays `PV/Strip/Normal`, and only the INH chip and the bad-value style can appear.

**Click.** A single click opens the process value dock for this tag. The view writes no tag and checks no role.

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

All 40 are bound (no script sets one). Tag bindings use mode `indirect` with a 2.5 s fallback delay. `{0}` resolves to `{view.params.tagPath}`.

Tag mirrors fall into the groups below. The other 14 properties are expressions over them.

| Group | Members | Source | What it holds / drives |
|---|---|---|---|
| Value and names (tag mirrors) | `pv`, `name`, `desc`, `units`, `hwFault` | `{view.params.tagPath}/` + `Val_PV`, `Cfg_Tag`, `Cfg_Desc`, `Cfg_EU`, `Sts_Bad` | PV, instrument tag, description, units and the bad-PV flag (`hwFault`). |
| Inhibit flags (tag mirrors) | `inhHH`, `inhH`, `inhL`, `inhLL` | `{view.params.tagPath}/Alm_HH/Sts_Suppressed`, `Alm_H/...`, `Alm_L/...`, `Alm_LL/...` | Suppressed state of each limit alarm. Feed `inh`. |
| FLT raw alarm (tag mirrors) | `FLTact`, `FLTun`, `FLTpri` | `{view.params.tagPath}/Alm_Bad/Sts_Active`, `Alm_Bad/Sts_Unack`, `Alm_Bad/Cfg_Priority` | Raw state, unacknowledged flag and priority of the bad-PV alarm (`Alm_Bad`, T_Alarm). |
| HH, H, L, LL raw alarms (tag mirrors) | `HHact`/`HHun`/`HHpri`, `Hact`/`Hun`/`Hpri`, `Lact`/`Lun`/`Lpri`, `LLact`/`LLun`/`LLpri` | `{view.params.tagPath}/` + `Alm_HH/Sts_Active`, `Alm_HH/Sts_Unack`, `Alm_HH/Cfg_Priority`, `Alm_H/Sts_Active`, `Alm_H/Sts_Unack`, `Alm_H/Cfg_Priority`, `Alm_L/Sts_Active`, `Alm_L/Sts_Unack`, `Alm_L/Cfg_Priority`, `Alm_LL/Sts_Active`, `Alm_LL/Sts_Unack`, `Alm_LL/Cfg_Priority` | Raw state, unacknowledged flag and priority of each limit alarm (`Alm_HH`, `Alm_H`, `Alm_L`, `Alm_LL`, T_AlmLim). |
| OVR and UNR raw flags (tag mirrors) | `rOVR`, `rUNR` | `{view.params.tagPath}/Sts_ORng`, `{view.params.tagPath}/Sts_URng` | Raw over- and under-range flags (T_AI BOOL). |

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.tick` | `null` | expr | `now(1000)` | Ticks every 1000 ms (`now(1000)`). Not referenced by any binding in this view. See Notes. |
| `view.custom.aFLT` | `-1` | expr | `if(toBoolean(coalesce({view.custom.FLTact}, false)), if(toBoolean(coalesce({view.custom.FLTun}, false)), 10, 0) + case(toInt(coalesce({view.custom.FLTpri}, 3)), 1, 4, 2, 3, 3, 2, 4, 1, 2),   if(toBoolean(coalesce({view.custom.FLTun}, false)), 20 + case(toInt(coalesce({view.custom.FLTpri}, 3)), 1, 4, 2, 3, 3, 2, 4, 1, 2), -1))` | FLT code: -1 none, else state x 10 + priority (state 0 active and acked, 1 active and unacked, 2 cleared and unacked, which adds 20). A missing or out-of-range `Cfg_Priority` reads as Medium (rank 2). |
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

### Component-level custom properties

None.

### Session, page and message payloads

None read. The click writes `session.custom.efcDw[<pageId>]` through `efc.ui.openDynamic`. See Scripts.

## Bindings reference

Total: **65 bindings** (40 at view root, 25 on components). View root: 26 tag, 14 expr. Components: 25 expr. No transforms.

### View root

The view-root bindings drive the custom properties. Each one is listed with its full source in View-level custom properties above.

### `root/Card`

Every component binding is in the table below, in tree order. The `Source` column gives the full expression or tag path.

#### `root/Card`

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Card/Strip` | `props.style.classes` | expr | `if({view.custom.fltActive}, "PV/Strip/Fault" + if({view.custom.anyUnacked}, " Alarm/Mod/Blink", ""),  if({view.custom.activePri} >= 0, "PV/Strip/" + case({view.custom.activePri}, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.anyUnacked}, " Alarm/Mod/Blink", ""),   if({view.custom.aFLT} >= 20, "PV/Strip/Fault Alarm/Mod/ClearedUnacked",    if({view.custom.clearedPri} >= 0, "PV/Strip/" + case({view.custom.clearedPri}, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + " Alarm/Mod/ClearedUnacked",     "PV/Strip/Normal"))))` | Strip colour: fault when `fltActive` (blink if `anyUnacked`); else highest active priority (blink if `anyUnacked`); else the cleared fault or cleared priority with `Alarm/Mod/ClearedUnacked`; else `PV/Strip/Normal`. |
| `root/Card/Body/HeaderRow/Tag` | `props.text` | expr | `if(isNull({view.custom.name}) \|\| len(toStr({view.custom.name})) = 0 \|\| toStr({view.custom.name}) = "null",   substring({view.params.tagPath}, max(lastIndexOf({view.params.tagPath}, "/"), lastIndexOf({view.params.tagPath}, "]")) + 1),   toStr({view.custom.name}))` | Header text: `name`, or the last segment of `tagPath` when `name` is blank or `null`. |
| `root/Card/Body/HeaderRow/Tag` | `meta.tooltip.text` | expr | `if(isNull({view.custom.desc}) \|\| toStr({view.custom.desc}) = "null", "", toStr({view.custom.desc}))` | Tooltip: `desc`, blank when null. |
| `root/Card/Body/HeaderRow/Chips/Chip_FLT` | `position.display` | expr | `({view.custom.aFLT} >= 0) && 0 < 2` | Visible while `aFLT` is 0 or more (active, or cleared and unacknowledged). FLT is the first letter, so no earlier letter counts. |
| `root/Card/Body/HeaderRow/Chips/Chip_FLT` | `props.style.classes` | expr | `if({view.custom.aFLT} < 0, "PV/Chip/Fault", "PV/Chip/Fault" + if({view.custom.aFLT} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aFLT} >= 10, " Alarm/Mod/Blink", "")))` | `PV/Chip/Fault`, with `Alarm/Mod/Blink` when unacknowledged (10 to 19) or `Alarm/Mod/ClearedUnacked` (20 and up). |
| `root/Card/Body/HeaderRow/Chips/Chip_HH` | `position.display` | expr | `({view.custom.aHH} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0)) < 2` | Visible while `aHH` is 0 or more (active, or cleared and unacknowledged) and fewer than two of the letters before it (FLT) are active. |
| `root/Card/Body/HeaderRow/Chips/Chip_HH` | `props.style.classes` | expr | `if({view.custom.aHH} < 0, "", "PV/Chip/" + case({view.custom.aHH} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aHH} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aHH} >= 10, " Alarm/Mod/Blink", "")))` | Priority class from the code (`code % 10`: Critical, High, Medium, Low, Diagnostic). Adds `Alarm/Mod/Blink` for 10 to 19 and `Alarm/Mod/ClearedUnacked` for 20 and up. |
| `root/Card/Body/HeaderRow/Chips/Chip_H` | `position.display` | expr | `({view.custom.aH} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0)) < 2` | Visible while `aH` is 0 or more (active, or cleared and unacknowledged) and fewer than two of the letters before it (FLT, HH) are active. |
| `root/Card/Body/HeaderRow/Chips/Chip_H` | `props.style.classes` | expr | `if({view.custom.aH} < 0, "", "PV/Chip/" + case({view.custom.aH} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aH} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aH} >= 10, " Alarm/Mod/Blink", "")))` | Priority class from the code (`code % 10`: Critical, High, Medium, Low, Diagnostic). Adds `Alarm/Mod/Blink` for 10 to 19 and `Alarm/Mod/ClearedUnacked` for 20 and up. |
| `root/Card/Body/HeaderRow/Chips/Chip_L` | `position.display` | expr | `({view.custom.aL} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0)) < 2` | Visible while `aL` is 0 or more (active, or cleared and unacknowledged) and fewer than two of the letters before it (FLT, HH, H) are active. |
| `root/Card/Body/HeaderRow/Chips/Chip_L` | `props.style.classes` | expr | `if({view.custom.aL} < 0, "", "PV/Chip/" + case({view.custom.aL} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aL} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aL} >= 10, " Alarm/Mod/Blink", "")))` | Priority class from the code (`code % 10`: Critical, High, Medium, Low, Diagnostic). Adds `Alarm/Mod/Blink` for 10 to 19 and `Alarm/Mod/ClearedUnacked` for 20 and up. |
| `root/Card/Body/HeaderRow/Chips/Chip_LL` | `position.display` | expr | `({view.custom.aLL} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0)) < 2` | Visible while `aLL` is 0 or more (active, or cleared and unacknowledged) and fewer than two of the letters before it (FLT, HH, H, L) are active. |
| `root/Card/Body/HeaderRow/Chips/Chip_LL` | `props.style.classes` | expr | `if({view.custom.aLL} < 0, "", "PV/Chip/" + case({view.custom.aLL} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aLL} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aLL} >= 10, " Alarm/Mod/Blink", "")))` | Priority class from the code (`code % 10`: Critical, High, Medium, Low, Diagnostic). Adds `Alarm/Mod/Blink` for 10 to 19 and `Alarm/Mod/ClearedUnacked` for 20 and up. |
| `root/Card/Body/HeaderRow/Chips/Chip_OVR` | `position.display` | expr | `({view.custom.aOVR} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0)) < 2` | Visible while `aOVR` is 0 or more (active, or cleared and unacknowledged) and fewer than two of the letters before it (FLT, HH, H, L, LL) are active. |
| `root/Card/Body/HeaderRow/Chips/Chip_OVR` | `props.style.classes` | expr | `if({view.custom.aOVR} < 0, "", "PV/Chip/" + case({view.custom.aOVR} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aOVR} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aOVR} >= 10, " Alarm/Mod/Blink", "")))` | `PV/Chip/Diagnostic` when active (code 0). No blink or cleared modifier, because the code has no acknowledge state. |
| `root/Card/Body/HeaderRow/Chips/Chip_UNR` | `position.display` | expr | `({view.custom.aUNR} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0) + if({view.custom.aOVR} >= 0, 1, 0)) < 2` | Visible while `aUNR` is 0 or more (active, or cleared and unacknowledged) and fewer than two of the letters before it (FLT, HH, H, L, LL, OVR) are active. |
| `root/Card/Body/HeaderRow/Chips/Chip_UNR` | `props.style.classes` | expr | `if({view.custom.aUNR} < 0, "", "PV/Chip/" + case({view.custom.aUNR} % 10, 4, "Critical", 3, "High", 2, "Medium", 1, "Low", "Diagnostic") + if({view.custom.aUNR} >= 20, " Alarm/Mod/ClearedUnacked", if({view.custom.aUNR} >= 10, " Alarm/Mod/Blink", "")))` | `PV/Chip/Diagnostic` when active (code 0). No blink or cleared modifier, because the code has no acknowledge state. |
| `root/Card/Body/HeaderRow/Chips/Chip_INH` | `position.display` | expr | `({view.custom.inh}) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0) + if({view.custom.aOVR} >= 0, 1, 0) + if({view.custom.aUNR} >= 0, 1, 0)) < 2` | Visible while `inh` is true and fewer than two of the letters before it (FLT, HH, H, L, LL, OVR, UNR) are active. |
| `root/Card/Body/HeaderRow/Chips/Chip_More` | `position.display` | expr | `(if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0) + if({view.custom.aOVR} >= 0, 1, 0) + if({view.custom.aUNR} >= 0, 1, 0) + if({view.custom.inh}, 1, 0)) > 2` | Visible when more than two letters are active (INH counts). |
| `root/Card/Body/HeaderRow/Chips/Chip_More` | `props.text` | expr | `"+" + toStr((if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0) + if({view.custom.aOVR} >= 0, 1, 0) + if({view.custom.aUNR} >= 0, 1, 0) + if({view.custom.inh}, 1, 0)) - 2)` | `+N`, where N is the number of active letters minus 2. |
| `root/Card/Body/HeaderRow/Chips/Chip_More` | `props.style.classes` | expr | `"PV/Chip/More" + if(((({view.custom.aFLT} >= 0) && 0 >= 2) && {view.custom.aFLT} >= 10 && {view.custom.aFLT} < 20) \|\| ((({view.custom.aHH} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0)) >= 2) && {view.custom.aHH} >= 10 && {view.custom.aHH} < 20) \|\| ((({view.custom.aH} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0)) >= 2) && {view.custom.aH} >= 10 && {view.custom.aH} < 20) \|\| ((({view.custom.aL} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0)) >= 2) && {view.custom.aL} >= 10 && {view.custom.aL} < 20) \|\| ((({view.custom.aLL} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0)) >= 2) && {view.custom.aLL} >= 10 && {view.custom.aLL} < 20) \|\| ((({view.custom.aOVR} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0)) >= 2) && {view.custom.aOVR} >= 10 && {view.custom.aOVR} < 20) \|\| ((({view.custom.aUNR} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0) + if({view.custom.aOVR} >= 0, 1, 0)) >= 2) && {view.custom.aUNR} >= 10 && {view.custom.aUNR} < 20), " Alarm/Mod/Blink", "")` | `PV/Chip/More`, plus `Alarm/Mod/Blink` when a hidden letter (third or later) is unacknowledged. |
| `root/Card/Body/HeaderRow/Chips/Chip_More` | `meta.tooltip.text` | expr | `"Also: " + if((({view.custom.aFLT} >= 0) && 0 >= 2), "FLT ", "") + if((({view.custom.aHH} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0)) >= 2), "HH ", "") + if((({view.custom.aH} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0)) >= 2), "H ", "") + if((({view.custom.aL} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0)) >= 2), "L ", "") + if((({view.custom.aLL} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0)) >= 2), "LL ", "") + if((({view.custom.aOVR} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0)) >= 2), "OVR ", "") + if((({view.custom.aUNR} >= 0) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0) + if({view.custom.aOVR} >= 0, 1, 0)) >= 2), "UNR ", "") + if((({view.custom.inh}) && (if({view.custom.aFLT} >= 0, 1, 0) + if({view.custom.aHH} >= 0, 1, 0) + if({view.custom.aH} >= 0, 1, 0) + if({view.custom.aL} >= 0, 1, 0) + if({view.custom.aLL} >= 0, 1, 0) + if({view.custom.aOVR} >= 0, 1, 0) + if({view.custom.aUNR} >= 0, 1, 0)) >= 2), "INH ", "")` | Tooltip `Also:` followed by the hidden letters, in order (FLT, HH, H, L, LL, OVR, UNR, INH). |
| `root/Card/Body/ValueRow/Value` | `props.text` | expr | `if(isNull({view.custom.pv}), "---", numberFormat({view.custom.pv}, "#,##0.0"))` | PV, one decimal, or `---` when PV is null. |
| `root/Card/Body/ValueRow/Value` | `props.style.classes` | expr | `"PV/Value Text/Mod/NoWrap" + if({view.custom.badValue}, " Value/BadQuality", "")` | Value style. Adds `Value/BadQuality` when `badValue` is true. |
| `root/Card/Body/ValueRow/Units` | `props.text` | expr | `if(isNull({view.custom.units}) \|\| toStr({view.custom.units}) = "null", "", toStr({view.custom.units}))` | Units text, blank when null or `null`. |


## Scripts reference

Total: **1 event script**. No transforms, custom methods, message handlers or onChange scripts.

### Click script (`root`, `events.dom.onClick`, scope G)

Trigger: a single click on the view.

```python
	efc.ui.openDynamic(self)
```

It opens the dock for this tag. See the library function below.

### Library function called (`efc.ui`, `projects/EFC_Library/ignition/script-python/efc/ui/code.py`)

- **`efc.ui.openDynamic(component)`**: uses `dockId`, or else `BY_TYPE['T_AI']`, which is `dw_ProcessValue`. `WINDOWS` maps that to `Templates/Dynamic Window/ProcessValues/ProcessValue`. If the id is not in `WINDOWS` it logs a warning and stops. Otherwise it writes the path and `{tagPath: dwTagPath or tagPath}` to `session.custom.efcDw` for this page. It does not check the role, does not write a tag and does not write an audit record.

## Tag members used

Paths are relative to `tagPath`. Types and comments come from `types/PCLib_Members.csv` (T_AI, and T_AlmLim for the `Alm_*` limits). No member is written.

| Member | Access | Data type | Meaning |
|---|---|---|---|
| `Val_PV` | read | REAL | Process value (EU), use this in logic |
| `Cfg_Tag` | read | STRING[20] | Equipment / instrument tag, e.g. FT-101 |
| `Cfg_Desc` | read | STRING[40] | Description shown on HMI faceplate |
| `Cfg_EU` | read | STRING[12] | Engineering units text |
| `Sts_Bad` | read | BOOL | PV bad (out of range or channel fault) |
| `Alm_HH/Sts_Suppressed`, `Alm_H/Sts_Suppressed`, `Alm_L/Sts_Suppressed`, `Alm_LL/Sts_Suppressed` | read | BOOL | Suppressed by design (ISA-18.2 state G) |
| `Alm_Bad/Sts_Active`, `Alm_Bad/Sts_Unack`, `Alm_Bad/Cfg_Priority` | read | BOOL / BOOL / INT | Bad-PV alarm (`Alm_Bad`, T_Alarm): active, unacknowledged, priority. |
| `Alm_HH/Sts_Active`, `Alm_HH/Sts_Unack`, `Alm_HH/Cfg_Priority`, `Alm_H/Sts_Active`, `Alm_H/Sts_Unack`, `Alm_H/Cfg_Priority`, `Alm_L/Sts_Active`, `Alm_L/Sts_Unack`, `Alm_L/Cfg_Priority`, `Alm_LL/Sts_Active`, `Alm_LL/Sts_Unack`, `Alm_LL/Cfg_Priority` | read | BOOL / BOOL / INT | Limit alarms (T_AlmLim): active, unacknowledged, priority. |
| `Sts_ORng`, `Sts_URng` | read | BOOL | Over range, under range. |

Priority (`Cfg_Priority`): PCLib order, `1=Critical 2=High 3=Medium 4=Low`. The view converts it to its internal rank (1 to 4, 2 to 3, 3 to 2, 4 to 1; anything else Medium) in the `a*` code bindings, and the range chips use rank 0 (Diagnostic).

## Component tree

Indentation shows parent and child. Each entry is `name` (component type).

- `root` (`ia.container.flex`)
  - `Card` (`ia.container.flex`)
    - `Strip` (`ia.display.label`)
    - `Body` (`ia.container.flex`)
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

## Notes and open questions

**Behaviour to review**

1. **`hwFault` does not drive the strip.** `hwFault` (`Sts_Bad`) only feeds `badValue`, so a PV bad flag changes the value style. The strip enters the fault state from the bad-PV alarm (`Alm_Bad/Sts_Active`).
2. **OVR and UNR never blink.** `aOVR` is 0 when `rOVR` is true, with no acknowledge state. The chip class is therefore always the Diagnostic class when active, and `anyUnacked` never includes it.
3. **`tick` drives nothing.** `docs/pv-display.md` says the alarm state is evaluated on `view.custom.tick` by a script transform that calls `system.alarm.queryStatus`. This view has no such transform, and no binding reads `view.custom.tick`. The design note is out of date for these views, or the transform was lost.
4. **Empty `tagPath` still opens the dock.** `tagPath` defaults to empty. A click then writes an empty `tagPath` to the dock, because `openDynamic` does not check it.

**Open questions**

- Should `hwFault` also make the strip show the fault colour?
- Which copy is current: the `EFC_ProcessValues` project from `generator/build_pv.py`, or the EFC_Library `Templates/ProcessValues` views?

