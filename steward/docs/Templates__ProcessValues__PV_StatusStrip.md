# Templates/ProcessValues/PV_StatusStrip

<!-- keep:start -->
**Purpose:** Process value card (compact value + status strip) bound to EFCLib v1 T_AI (tagPath).

**Usage notes:** Click opens dw_ProcessValue (trend, limits, simulate).

**Gotchas:** Alarm state from the T_AI alarm members (Alm_HH .. Alm_LL, Alm_Bad); bad quality from Sts_Bad.
<!-- keep:end -->

<!-- auto:start -->
_Auto-generated 2026-10-25 01:51 from EFC_Library:view:Templates/ProcessValues/PV_StatusStrip. Do not edit this section._

| Param | Direction | Default |
|---|---|---|
| census | input | true |
| dockId | input | "" |
| dwTagPath | input | "" |
| tType | input | "T_AI" |
| tagPath | input | "" |

- PCLib types: T_AI
- Dynamic window: none
- Style classes: PV/Body, PV/Card, PV/Chip/Inhibit, PV/Chip/More, PV/ChipRow, PV/HeaderRow, PV/Shell, PV/Strip/Normal, PV/Tag, PV/Units, PV/Value, Text/Mod/Ellipsis, Text/Mod/NoWrap, Util/Pointer (+10 bound)
- Inline style props: 0
- Popups opened: 0
- system.* calls: none
- Last modified: 2026-10-19T00:00:00Z by efc-ignition-library
<!-- auto:end -->
