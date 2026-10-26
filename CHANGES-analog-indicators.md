# Drop-in: analog indicator templates + T_KPI (2026-10-20)

## Current library (updated October 26, 2026)

The indicators now ship in `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/AnalogIndicator/`: `A_RangeBar`, `B_PointerScale`, `C_CompactRow`, `D_MiniColumn` and `_Examples`. Import `EFC_Library_PROJECT.zip`; no parent project is required. Their input is `tagPath` (lowercase), with `tType` defaulting to `T_KPI`.

A single click calls `efc.ui.openDynamic(self)`; `T_KPI` maps to `dw_ProcessValue`. Following PR #36 (October 24, decisions 31–32), the window is `Templates/Dynamic Window/ProcessValues/ProcessValue` in the right-side `dw_Right` Perspective dock. `dockId` overrides the window id and `dwTagPath` overrides its tag path. See [page setup](docs/library-reference.md#page-setup-the-dw_right-dock) and [indicator help](docs/help/Templates/AnalogIndicator/A_RangeBar.md). The indicators are display-only; the ProcessValue window binds to T_AI members by default, so check T_KPI compatibility or provide a suitable window/tag override (see its detailed help).

Source: `generator/analog_indicators/gen_analog_indicators.py`, merged by `build.py`. The initial drop-in notes below record the October 20 package layout and its then-open gap.

## Original drop-in notes (October 20, historical)

Unzip at the efc-ignition-library repo root. Adds:
- projects/EFC_AnalogIndicators/  Ignition 8.1 project (parent EFC_Styles): EFC/AnalogIndicator/A_RangeBar,
  B_PointerScale, C_CompactRow, D_MiniColumn, _Examples; Indicator/Analog/* style classes;
  gen_analog_indicators.py (source of truth). Views bind to PCLib T_KPI via the TagPath param.
- types/T_KPI/  proposed EFCLib v1 type (generator block, preliminary Ignition UDT, appendix table).
- mockups/analog-indicator-options.md, steward/docs/<view>.md.

Replaces the earlier draft types/T_AnalogIn (delete it if you unzipped the first drop-in).
Known gap: no dynamic window (long-press openDock) yet; needs the dock id.
