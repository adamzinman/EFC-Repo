# Templates/Valves/Valve_OnOff_Pneumatic

<!-- keep:start -->
**Purpose:** P&ID pneumatic on/off valve template bound to EFCLib v1 T_DValve through tagPath: state fill, alarm outline, P/I badges, mode and status line.

**Usage notes:** Params: tagPath, useButton (in-template command button), tType, dockId / dwTagPath overrides. Click the symbol opens the dynamic window (dw_ValveDiscrete) in the page's dw_Right dock.

**Gotchas:** Touch mode (useButton = false, dblCmd = true): double-tap toggles the device, Operator+, only in MAN, available, permitted, not interlocked, not LOCAL. Limit-switch LEDs follow Cfg_HasZSO / Cfg_HasZSC.
<!-- keep:end -->

<!-- auto:start -->
_Auto-generated 2026-10-25 01:45 from EFC_Library:view:Templates/Valves/Valve_OnOff_Pneumatic. Do not edit this section._

| Param | Direction | Default |
|---|---|---|
| dblCmd | input | true |
| dockId | input | "" |
| dwTagPath | input | "" |
| tType | input | "T_DValve" |
| tagPath | input | "[default]PID_Demo/XV101" |
| useButton | input | true |

- PCLib types: T_DValve
- Dynamic window: none
- Style classes: Button/Command, Indicator/InterlockBadge, Indicator/PermissiveBadge, State/Stopped, Text/Mod/Center, Text/Mod/NoWrap, Text/TagName, Util/Collapsed, Util/Pointer (+2 bound)
- Inline style props: 0
- Popups opened: 0
- system.* calls: none
- Last modified: 2026-10-19T00:00:00Z by efc-ignition-library
<!-- auto:end -->
