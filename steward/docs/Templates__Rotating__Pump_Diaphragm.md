# Templates/Rotating/Pump_Diaphragm

<!-- keep:start -->
**Purpose:** P&ID diaphragm pump template bound to EFCLib v1 T_Motor through tagPath: state fill, alarm outline, P/I badges, mode and status line.

**Usage notes:** Params: tagPath, useButton (in-template command button), tType, dockId / dwTagPath overrides. Click the symbol opens the dynamic window (dw_Rotating) in the page's dw_Right dock.

**Gotchas:** Touch mode (useButton = false, dblCmd = true): double-tap toggles the device, Operator+, only in MAN, available, permitted, not interlocked, not LOCAL.
<!-- keep:end -->

<!-- auto:start -->
_Auto-generated 2026-10-23 20:15 from EFC_Library:view:Templates/Rotating/Pump_Diaphragm. Do not edit this section._

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
