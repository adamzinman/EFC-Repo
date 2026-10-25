# Templates/AnalogIndicator/D_MiniColumn

<!-- keep:start -->
**Purpose:** Analog indicator card bound to EFCLib v1 T_KPI (tagPath). Narrow column bar for side-by-side groups. Param: Header = Tag | Desc.

**Usage notes:** Use on overview / process screens; ideal band from Cfg_IdealLo/Hi. Click opens dw_ProcessValue.

**Gotchas:** Alarm colors come from the PLC alarm members (Sts_Active / Sts_Unack / Cfg_Priority), not Ignition alarm queries.
<!-- keep:end -->

<!-- auto:start -->
_Auto-generated 2026-10-25 01:45 from EFC_Library:view:Templates/AnalogIndicator/D_MiniColumn. Do not edit this section._

| Param | Direction | Default |
|---|---|---|
| Format | input | "#,##0.0" |
| Header | input | "Tag" |
| census | input | true |
| dockId | input | "" |
| dwTagPath | input | "" |
| tType | input | "T_KPI" |
| tagPath | input | "[default]KPI/KPI_101" |

- PCLib types: T_KPI
- Dynamic window: none
- Style classes: Indicator/Analog/Card, Indicator/Analog/Chip, Indicator/Analog/D/Bar, Indicator/Analog/D/Pointer, Indicator/Analog/D/root, Indicator/Analog/Header, Indicator/Analog/Track, Indicator/Analog/ValueBox, Indicator/Analog/ZoneIdeal, Indicator/Analog/ZoneNormal, Text/Mod/Center, Text/Size/M, Text/Units (+6 bound)
- Inline style props: 0
- Popups opened: 0
- system.* calls: none
- Last modified: 2026-10-13T00:00:00Z by efc-ignition-library
<!-- auto:end -->
