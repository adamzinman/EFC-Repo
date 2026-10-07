# PID loop templates (PID_Loops)

**Status:** designed and built 2026-10-05; the `xMidYMid` fix followed 2026-10-07. **The project and its generator (`generate_loops.py`) aren't in this repo yet.** The export `PID_Loops_PROJECT.zip` / `PID_Loop_Templates_Perspective81.zip` is in Downloads. Add it with `python3 tools/import_project_zip.py PID_Loops_PROJECT.zip`, and use the copy that has `preserveAspectRatio` = `xMidYMid` (the 2026-10-05 zips still have `xMidYMid meet`, which 8.1 rejects). It has not been test-imported on a gateway.

The chosen design is Option B (a bar-graph card) plus three variations, in a modern flat ISA-101 style: grays, a blue SP, and color only for alarms.

| View | Size @1080p | Notes |
|---|---|---|
| `PID/Templates/Loop_B1_Bar` | 150×156 | Vertical PV bar, SP pointer and alarm ticks. SP and OUT values enlarged to 16 px. |
| `PID/Templates/Loop_B2_Horizontal` | 260×92 | Horizontal bar with a normal-range band between AlmLo and AlmHi |
| `PID/Templates/Loop_B3_Sparkline` | 172×184 | B1 plus a 1-minute PV/SP sparkline (queryTagHistory) and a deviation chip (orange past AlmDev) |
| `PID/Templates/Loop_B4_Column` | 104×196 | Twin vertical bars: PV and OUT |
| `PID/Popups/LoopConfig` | 440×480 | Tabs: Operate / Tuning / Limits & Alarms |
| `PID/_Demo_Loops` | — | All four templates × 3 demo loops |

- **Template parameters:** `tagPath` (a `PID_Loop` UDT instance) and `label` (optional). The whole card is the click target and calls `openPopup("loopcfg_<tagPath>", "PID/Popups/LoopConfig")`.
- **Graphics:** Drawing components with bound element geometry. Fonts and padding are in vh.
- **UDT `PID_Loop`:**
  - PV (EngUnit/EngLow/EngHigh drive the units and scaling; the PV_High/PV_Low alarms are bound to AlmHi/AlmLo), SP, OUT.
  - Mode (0 MAN / 1 AUTO / 2 CAS), Kp, Ti, Td, Action (0 Rev / 1 Dir).
  - SP_Lo/Hi, OUT_Lo/Hi, AlmHi, AlmLo, AlmDev, Description.
  - They're memory tags in the export; map them to the M580 PID block.
- **Popup:**
  - The mode buttons and SP/OUT write immediately. OUT is writable only in MAN, and SP is locked in CAS.
  - Tuning and limits are read when the popup opens and written on Apply. They're editable only with the role in `view.custom.engineerRole` (default `Engineer`).
- **History:** must be enabled on PV/SP/OUT for the B3 sparkline and the popup trend.

## Open items
- The card's alarm state is PV ≥ AlmHi or ≤ AlmLo, not the real alarm priority yet.
- It uses inline styles, not EFC_Styles classes, so it doesn't follow the style-library standard yet.
- The cards label the output "OUT"; relabel it to CV if wanted.
