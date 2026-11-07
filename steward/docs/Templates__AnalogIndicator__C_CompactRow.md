# Templates/AnalogIndicator/C_CompactRow

<!-- keep:start -->
**Purpose:** Analog indicator card bound to EFCLib v1 T_KPI (tagPath). One-line row (header, chip, value) over a thin zone bar for dense lists. Param: Header = Tag | Desc.

**Usage notes:** Use on overview / process screens; ideal band from Cfg_IdealLo/Hi. Click opens dw_ProcessValue.

**Gotchas:** Alarm colors come from the PLC alarm members (Sts_Active / Sts_Unack / Cfg_Priority), not Ignition alarm queries.
<!-- keep:end -->

<!-- auto:start -->
_Auto-generated 2026-10-25 01:51 from EFC_Library:view:Templates/AnalogIndicator/C_CompactRow. Do not edit this section._

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
- Style classes: Indicator/Analog/A/ValueRow, Indicator/Analog/A/root, Indicator/Analog/C/Pointer, Indicator/Analog/C/root, Indicator/Analog/CardCompact, Indicator/Analog/Chip, Indicator/Analog/Track, Indicator/Analog/ValueBox, Indicator/Analog/ZoneIdeal, Indicator/Analog/ZoneNormal, Text/TagName, Text/Units (+6 bound)
- Inline style props: 0
- Popups opened: 0
- system.* calls: none
- Last modified: 2026-10-13T00:00:00Z by efc-ignition-library
<!-- auto:end -->
