# Templates/AnalogIndicator/A_RangeBar

<!-- keep:start -->
**Purpose:** Analog indicator card bound to EFCLib v1 T_KPI (tagPath). Full card: tag/description, boxed value, pointer over the zoned bar, min/max and alarm chip. Params: LabelMode, ShowMinMax.

**Usage notes:** Use on overview / process screens; ideal band from Cfg_IdealLo/Hi. Click opens dw_ProcessValue.

**Gotchas:** Alarm colors come from the PLC alarm members (Sts_Active / Sts_Unack / Cfg_Priority), not Ignition alarm queries.
<!-- keep:end -->

<!-- auto:start -->
_Auto-generated 2026-10-25 01:51 from EFC_Library:view:Templates/AnalogIndicator/A_RangeBar. Do not edit this section._

| Param | Direction | Default |
|---|---|---|
| Format | input | "#,##0.0" |
| LabelMode | input | "Both" |
| ShowMinMax | input | true |
| census | input | true |
| dockId | input | "" |
| dwTagPath | input | "" |
| tType | input | "T_KPI" |
| tagPath | input | "[default]KPI/KPI_101" |

- PCLib types: T_KPI
- Dynamic window: none
- Style classes: Indicator/Analog/A/Pointer, Indicator/Analog/A/ValueRow, Indicator/Analog/A/root, Indicator/Analog/Card, Indicator/Analog/Chip, Indicator/Analog/Desc, Indicator/Analog/Scale, Indicator/Analog/Track, Indicator/Analog/ValueBox, Indicator/Analog/ZoneIdeal, Indicator/Analog/ZoneNormal, Text/Mod/Right, Text/TagName, Text/Units (+7 bound)
- Inline style props: 0
- Popups opened: 0
- system.* calls: none
- Last modified: 2026-10-13T00:00:00Z by efc-ignition-library
<!-- auto:end -->
