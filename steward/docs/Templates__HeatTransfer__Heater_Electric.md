# Templates/HeatTransfer/Heater_Electric

<!-- keep:start -->
**Purpose:** P&ID electric heater template bound to EFCLib v1 T_Heater through tagPath: state fill, alarm outline, P/I badges, mode and status line. Works for on/off and power-controlled (SSR/SCR) heaters (Cfg_CtrlType).

**Usage notes:** Params: tagPath, useButton (in-template command button), tType, dockId / dwTagPath overrides. Click the symbol opens the dynamic window (dw_Heater) in the screen's Docks/Region.

**Gotchas:** No double-tap command (only T_DValve / T_Motor take one). Power demand is set in the window.
<!-- keep:end -->

<!-- auto:start -->
_Auto-generated 2026-10-23 20:15 from EFC_Library:view:Templates/HeatTransfer/Heater_Electric. Do not edit this section._

| Param | Direction | Default |
|---|---|---|
| dockId | input | "" |
| dwTagPath | input | "" |
| tType | input | "T_Heater" |
| tagPath | input | "[default]PID_Demo/E401" |
| useButton | input | true |

- PCLib types: T_Heater
- Dynamic window: none
- Style classes: Button/Command, Indicator/InterlockBadge, Indicator/PermissiveBadge, State/Stopped, Text/Mod/Center, Text/Mod/NoWrap, Text/TagName, Util/Collapsed, Util/Pointer (+2 bound)
- Inline style props: 0
- Popups opened: 0
- system.* calls: none
- Last modified: 2026-10-19T00:00:00Z by efc-ignition-library
<!-- auto:end -->
