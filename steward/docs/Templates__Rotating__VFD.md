# Templates/Rotating/VFD

<!-- keep:start -->
**Purpose:** P&ID motor-on-VFD template bound to EFCLib v1 T_VFD through tagPath: state fill, alarm outline, P/I badges, mode and status line. Running status shows Val_Spd + Cfg_SpdEU.

**Usage notes:** Params: tagPath, useButton (in-template command button), tType, dockId / dwTagPath overrides. Click the symbol opens the dynamic window (dw_VFD) in the page's right dock (efcDynamic, decision 31).

**Gotchas:** No double-tap command (only T_DValve / T_Motor take one). Speed is set from the window (Operator+, MAN).
<!-- keep:end -->

<!-- auto:start -->
_Auto-generated 2026-10-21 03:53 from EFC_Library:view:Templates/Rotating/VFD. Do not edit this section._

| Param | Direction | Default |
|---|---|---|
| dockId | input | "" |
| dwTagPath | input | "" |
| tType | input | "T_VFD" |
| tagPath | input | "[default]PID_Demo/M601" |
| useButton | input | true |

- PCLib types: T_VFD
- Dynamic window: none
- Style classes: Button/Command, Indicator/InterlockBadge, Indicator/PermissiveBadge, State/Stopped, Text/Mod/Center, Text/Mod/NoWrap, Text/TagName, Util/Collapsed, Util/Pointer (+2 bound)
- Inline style props: 0
- Popups opened: 0
- system.* calls: system.tag.writeBlocking
- Last modified: 2026-10-19T00:00:00Z by efc-ignition-library
<!-- auto:end -->
