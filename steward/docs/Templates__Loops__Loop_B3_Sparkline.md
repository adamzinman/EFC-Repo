# Templates/Loops/Loop_B3_Sparkline

<!-- keep:start -->
**Purpose:** PID loop card (bar + 1 min PV/SP sparkline) bound to EFCLib v1 T_PID: PV, SP, output, mode, deviation alarm.

**Usage notes:** Click opens dw_Loop (mode, SP/CV entry, tuning Engineer+). The LoopConfig popup is retired.

**Gotchas:** Sparkline/trend needs tag history on Val_PV / Val_SP.
<!-- keep:end -->

<!-- auto:start -->
_Auto-generated 2026-10-21 03:56 from EFC_Library:view:Templates/Loops/Loop_B3_Sparkline. Do not edit this section._

| Param | Direction | Default |
|---|---|---|
| dockId | input | "" |
| dwTagPath | input | "" |
| label | input | "" |
| tType | input | "T_PID" |
| tagPath | input | "[default]PID_Demo/TIC101" |

- PCLib types: T_PID
- Dynamic window: none
- Style classes: Loop/B1/header, Loop/B1/mode, Loop/B1/outLbl, Loop/B1/pv, Loop/B1/root, Loop/B1/spLbl, Loop/B1/tag, Loop/B1/title, Loop/B2/ob, Loop/B2/sp, Loop/B2/units, Loop/B3/body, Loop/B3/dev, Loop/B3/out, Loop/B3/outRow, Loop/B3/sparkWrap, Loop/B3/vals
- Inline style props: 0
- Popups opened: 0
- system.* calls: system.tag.queryTagHistory
- Last modified: 2026-10-05T12:00:00Z by admin
<!-- auto:end -->
