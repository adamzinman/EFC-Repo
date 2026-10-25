# Templates/Valves/Valve_Control

<!-- keep:start -->
**Purpose:** P&ID control valve template bound to EFCLib v1 T_CValve through tagPath: state fill, alarm outline, P/I badges, mode and status line. Position bar shows Val_Pos (Val_Demand when Cfg_HasFbk is false).

**Usage notes:** Params: tagPath, useButton (in-template command button), tType, dockId / dwTagPath overrides. Click the symbol opens the dynamic window (dw_ValveAnalog) in the page's dw_Right dock.

**Gotchas:** No Perm member on T_CValve; the P badge stays hidden. No double-tap command (only T_DValve / T_Motor take one).
<!-- keep:end -->

<!-- auto:start -->
_Auto-generated 2026-10-25 01:45 from EFC_Library:view:Templates/Valves/Valve_Control. Do not edit this section._

| Param | Direction | Default |
|---|---|---|
| dockId | input | "" |
| dwTagPath | input | "" |
| tType | input | "T_CValve" |
| tagPath | input | "[default]PID_Demo/FV101" |

- PCLib types: T_CValve
- Dynamic window: none
- Style classes: Indicator/InterlockBadge, Indicator/PermissiveBadge, State/Stopped, Text/Mod/Center, Text/Mod/NoWrap, Text/TagName, Util/Collapsed, Util/Pointer (+2 bound)
- Inline style props: 0
- Popups opened: 0
- system.* calls: none
- Last modified: 2026-10-19T00:00:00Z by efc-ignition-library
<!-- auto:end -->
