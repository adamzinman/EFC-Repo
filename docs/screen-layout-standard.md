# Perspective screen design standard

This is the layout standard every EFC Perspective screen and template follows. It is also an appendix to the EFC Controls Standard; `Perspective_Screen_Design_Standard.pdf` is the published copy.

## Frame (16:9)
Screens scale at 16:9 from **1920×1080 to 3840×2160**. Text inside templates must stay usable across that whole range, which is why every EFC_Styles size is in vh: 1080p is 1×, 1440p is 1.33× and 2160p is 2×.

| Region | Size at 1920×1080 (design) | Size at 3840×2160 | Notes |
|---|---|---|---|
| Header | 1920 × 80 | 3840 × 160 | Title, navigation, status |
| Left menu | 120 × 860 | 240 × 1720 | Screen navigation |
| Main process area | 1400 × 860 | 2800 × 1720 | P&ID templates (PID_Symbols, PV, loops) |
| Trends / dynamic window | 400 × 860 (dock Size 400 px; content 37.04 vh × 79.63 vh) | 800 × 1720 (dock Size 800 px) | Perspective right dock in push mode, Dock ID `efcDynamic`, view `Docks/Host` (decision 31). It takes its own column; the process area shrinks, nothing is covered. Shows the screen's default view (trends) or the dynamic window opened by `efc.ui`. An expanded graph grows inside the window (about 400 × 760); the dock never changes width. Setup: [`dock-setup.md`](dock-setup.md). |
| Alarm bar | 1920 × 140 | 3840 × 280 | Most-recent alarms (about four rows plus a header row) |

Sizes match the Controls Standard screen design appendix (Perspective Screen Design Standard). All regions scale down proportionally on smaller displays, except the right dock: a Perspective dock Size is in px, not vh, so the screen owner sets 400 px for 1920 × 1080 and 800 px for 3840 × 2160 (see [`dock-setup.md`](dock-setup.md)). The appendix still describes the right region as an Embedded View; that text change is queued (`steward/DOC-QUEUE.md` row 4).

## Graphics conventions
- **ISA-101 high-performance grayscale:**
  - Background `#D9D9D9`.
  - Color only for abnormal states.
  - Color always backed by text or shape.
  - Flashing only for unacknowledged alarms.
- **Equipment state:** running/open is white, stopped/closed is gray, transition is `#C4C4C4`, and fault is dark gray `#3A3A3A` with a red border.
- **Automated valves:** the actuator head shows the command; the body shows actual feedback when separate feedback exists.
- **Device templates:**
  - Tag above, status below, both centered on the symbol's centerline.
  - Orange P when a permissive blocks the device; red I when an interlock blocks it.
  - A small blank-square command button appears in Manual.
  - The only parameter is `tagPath`, plus `useButton`.
- **Static symbols:** plain SVGs in `symbols/`, imported as needed.
- **Styles:** use EFC_Styles classes (`props.style.classes`), never inline styles. See [`style-library.md`](style-library.md).
