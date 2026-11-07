# Templates/HeatTransfer/HX_AirCooled

<!-- keep:start -->
**Purpose:** Air-cooled exchanger (fan) template, bound as T_Motor for the fan.

**Usage notes:** Click opens dw_Rotating. For exchanger performance set dockId = dw_HeatTransfer and dwTagPath to the T_HeatEx instance.

**Gotchas:** Open item: decide whether air coolers default to the fan or the T_HeatEx window.
<!-- keep:end -->

<!-- auto:start -->
_Auto-generated 2026-10-25 01:45 from EFC_Library:view:Templates/HeatTransfer/HX_AirCooled. Do not edit this section._

| Param | Direction | Default |
|---|---|---|
| dblCmd | input | true |
| dockId | input | "" |
| dwTagPath | input | "" |
| tType | input | "T_Motor" |
| tagPath | input | "[default]PID_Demo/P101" |
| useButton | input | true |

- PCLib types: T_Motor
- Dynamic window: none
- Style classes: Button/Command, Indicator/InterlockBadge, Indicator/PermissiveBadge, State/Stopped, Text/Mod/Center, Text/Mod/NoWrap, Text/TagName, Util/Collapsed, Util/Pointer (+2 bound)
- Inline style props: 0
- Popups opened: 0
- system.* calls: none
- Last modified: 2026-10-19T00:00:00Z by efc-ignition-library
<!-- auto:end -->
