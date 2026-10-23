# Templates/Loops/Loop_B4_Column

<!-- keep:start -->
**Purpose:** PID loop card (narrow column) bound to EFCLib v1 T_PID: PV, SP, output, mode, deviation alarm.

**Usage notes:** Click opens dw_Loop (mode, SP/CV entry, tuning Engineer+). The LoopConfig popup is retired.

**Gotchas:** Deviation marks use Val_SP ± Alm_DevH/DevL Cfg_Lim.
<!-- keep:end -->

<!-- auto:start -->
_Auto-generated 2026-10-23 20:15 from EFC_Library:view:Templates/Loops/Loop_B4_Column. Do not edit this section._

| Param | Direction | Default |
|---|---|---|
| dockId | input | "" |
| dwTagPath | input | "" |
| label | input | "" |
| tType | input | "T_PID" |
| tagPath | input | "[default]PID_Demo/TIC101" |

- PCLib types: T_PID
- Dynamic window: none
- Style classes: Loop/B1/mode, Loop/B1/outLbl, Loop/B1/tag, Loop/B1/title, Loop/B4/bars, Loop/B4/chipRow, Loop/B4/labs, Loop/B4/out, Loop/B4/pv, Loop/B4/root, Loop/B4/sp, Loop/B4/spRow, Loop/B4/units
- Inline style props: 0
- Popups opened: 0
- system.* calls: none
- Last modified: 2026-10-05T12:00:00Z by admin
<!-- auto:end -->
