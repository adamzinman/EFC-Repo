# Templates/Loops/Loop_B1_Bar

<!-- keep:start -->
**Purpose:** PID loop card (vertical PV/SP bar) bound to EFCLib v1 T_PID: PV, SP, output, mode, deviation alarm.

**Usage notes:** Click opens dw_Loop (mode, SP/CV entry, tuning Engineer+). The LoopConfig popup is retired.

**Gotchas:** Deviation marks use Val_SP ± Alm_DevH/DevL Cfg_Lim.
<!-- keep:end -->

<!-- auto:start -->
_Auto-generated 2026-10-21 03:56 from EFC_Library:view:Templates/Loops/Loop_B1_Bar. Do not edit this section._

| Param | Direction | Default |
|---|---|---|
| dockId | input | "" |
| dwTagPath | input | "" |
| label | input | "" |
| tType | input | "T_PID" |
| tagPath | input | "[default]PID_Demo/TIC101" |

- PCLib types: T_PID
- Dynamic window: none
- Style classes: Loop/B1/body, Loop/B1/header, Loop/B1/mode, Loop/B1/out, Loop/B1/outBarRow, Loop/B1/outLbl, Loop/B1/outRow, Loop/B1/pctU, Loop/B1/pv, Loop/B1/root, Loop/B1/sp, Loop/B1/spLbl, Loop/B1/tag, Loop/B1/title, Loop/B1/units, Loop/B1/vals
- Inline style props: 0
- Popups opened: 0
- system.* calls: none
- Last modified: 2026-10-05T12:00:00Z by admin
<!-- auto:end -->
