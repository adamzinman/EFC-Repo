# EFC Station faceplates (EFC_StationFaceplates), Ignition Perspective 8.1

Three faceplates for the `DDT_Station` UDT in ISA-101 light gray. They use EFC_Styles classes only, plus 5 new classes that ship in this project.

| View | Size @1080p | Use |
|---|---|---|
| `Templates/Station/Station_Sidebar` | 400 × 860 | Type 1: full faceplate. In EFC_Library it is the `dw_Station` dynamic window `Templates/Dynamic Window/Station/Station`, opened in the page's `dw_Right` dock (resized from 300 × 800, decisions 4 and 25) |
| `Templates/Station/Station_Fill` | 300 × 400 | Type 2: filling screen, with live fill data and setpoint entry |
| `Templates/Station/Station_Tile` | 220 × 96 | Type 3: overview tile. Clicking it opens the station window in the `dw_Right` dock. |
| `Templates/Station/_Demo` | 1920 × 1080 | All three bound to the demo tags |

The only parameter on each view is **`tagPath`**: the DDT_Station instance, e.g. `[default]FillStn/Station_1`.

## Import
1. **Gateway → Config → Projects → Import** `EFC_StationFaceplates.zip`. Its parent is `EFC_Styles`; import that first if it isn't already on the gateway. Then do one of:
   - set it as a parent in your chain (`EFC_Styles → EFC_StationFaceplates → …→ HMI`), or
   - in Designer, copy the `Templates/Station` views and the `Station/*` and `Bar/Band/Deadband` style classes into your HMI project.
2. Optional demo:
   - Tag Browser → Data Types → import `tags/DDT_Station_Demo_UDT.json`.
   - Tags root → import `tags/Station_Demo_Instances.json`.
   - Open `Templates/Station/_Demo`.
3. Dock: in Page Configuration on the overview page, add the library's **right dock** (the same on every page, see [library-reference](library-reference.md#page-setup-the-dw_right-dock)):
   - id `dw_Right`
   - view: the page's trends overview as the initial view (decision 32)
   - size 400 (`efc.ui.sizeDock` rescales it to 37.04 vh: 400 px at 1080p, 800 px at 4K, decision 33), display "visible", content "cover", handle "hide" (decision 32)

   In the screen's root onStartup call `efc.ui.setDefaultDock(self, viewPath, params)` with that overview, and call `efc.ui.sizeDock(self)` from a change script on a custom property bound to `page.props.dimensions.viewport.height`.

   The tile's onClick calls `efc.ui.openDynamic(self)`, which loads `Templates/Dynamic Window/Station/Station` with `{"tagPath": …}` into `dw_Right` and opens it (Ignition 8.1.19+). The window's ✕ calls `efc.ui.closeDynamic(self)`, which puts the page's default view back (`efc.ui.setDefaultDock` in the screen's onStartup) or closes the dock.

## Member mapping
The names below are the `DDT_Station` members of the original export. In EFC_Library the built window binds the T_Station equivalents, renamed by `steward/tools/fix_station.py` (`NetWeight` → `Val_Net`, `TargetWeight` → `Prm_TargetWt`, `Filling` → `Sts_Filling`, `Vessel_Present` → `Inp_VesselPresent`, `PT` → `Val_PT`, `HMI_Select` → `Cmd_Select`, ...); the demo UDT is `tags/T_Station_Demo_UDT.json`.

**Displays**
- **Status chip:** derived from the bools, in this order:
  - `Disabled`, then `Failed`, then `Complete`, then `Filling`, then `SampleCMD`, then `Vacuuming`, `Venting`, `Recovering`, then `Active`, then `ReadyToStart`/`ReadyToFill`.
- **Message line:** `Msg` when it's a non-empty string, otherwise text derived from the status.
- **Sequence:**
  - Vessel: `Vessel_Present`
  - Vac: `Vacuuming`/`Vacuumed`
  - Prefill: `Press_Balanced`
  - Fill: `Filling`
  - Sample: `SampleCMD`
  - Done: `Complete`
  - On `Failed`, the first unfinished step is drawn as the fault step.
- **Weights:** `NetWeight`, `TargetWeight`, `Deadband`, `GrossWeight`, `TareWeight`, `TotalWeight`.
  - The fill bar scale is 108 % of target.
  - Overfill (net > target + deadband) switches the bar to `Bar/FillAlarm`.
- **Pressure:** `PT` against `Press_Max`, with the prefill marker at `SamplePress`. `PT_Diff` is shown as dP.
  - When `PT_Valid` is false, the value shows `-----` with `Value/BadQuality`.
- **Permissives:** `Vessel_Present`, `PT_Valid`, `Press_Balanced`, `ReadyToStart`, `ReadyToFill`.
- **Valve lamps:** Inlet, Sample and Vacuum REQ/CMD. The red I appears when REQ = 1 and CMD = 0.
- **Units:** `Units`. Blank or `---` falls back to `kg`.

**Setpoints** (numeric entry, bidirectional; disabled while the station is disabled)
- Target → `TargetWeight`
- Sample → `SampleWeight`
- Max press → `Press_Max`
- Prefill press → `SamplePress`
- Deadband → `Deadband` (sidebar only)

**Commands**
- **Select** pulses `Cmd_Select` (was `HMI_Select`); the button label shows `Selected`.
- **Tare**, **Zero** and **Reset** ask for confirmation, then pulse `Cmd_Tare`, `Cmd_Zero` and `Cmd_Reset` (were `TareCMD`, `ZeroCMD`, `HMI_Reset`; T_Station names, `steward/tools/fix_station.py`).
  - A pulse writes 1, then writes 0 after 1 s.
  - Tare and Zero are locked while the station is active or disabled.
  - Reset is enabled only after Complete or Failed.

## Check on the live gateway
- **SamplePress mapping:** `SamplePress` is assumed to be the old "Prefill Press" setpoint, and `SampleWeight` the sample setpoint. If not, change the two setpoint fields in the views (the generator `build_station.py` isn't in this repo).
- **Command pulse:** if the PLC treats `Cmd_Tare`, `Cmd_Zero`, `Cmd_Reset` or `Cmd_Select` as a level rather than a rising edge, adjust the 1 s pulse.
- **Derived-state recalculation:** all derived values come from one script transform: the property binding `view.custom.t` → `custom.s`. Confirm it recalculates when a single tag changes. If it doesn't, change that binding to an expression binding on `now(1000)` with the same transform.
- **Old 8.1 builds:** before 8.1.22 the stylesheet keyframes aren't loaded, which only affects blinking alarm classes; nothing here blinks.

## New style classes (in this project; fold into EFC_Styles later)
`Station/Step/Done`, `Station/Step/Active`, `Station/Step/Pending`, `Station/Step/Fault`, `Bar/Band/Deadband`

## In this repo
- **Project:** source in `imported/EFC_StationFaceplates/` (imported from the 2026-10-06 export, v6.2); ships inside `projects/EFC_Library/` at `Templates/Station/`. Edit it in the Designer and re-import; its generator (`build_station.py`) is not in the repo.
- **Demo tags:** `tags/DDT_Station_Demo_UDT.json`, `tags/Station_Demo_Instances.json`.
- **Checks:** passes the 8.1 import check. It uses 44 EFC_Styles classes, all present, and its own 5 classes don't clash with EFC_Styles, EFC_ProcessValues or EFC_IOFaceplates.
- **Inline styles:** mostly layout spacing (`gap`, `height`, `padding`, margins). A few typography values (`fontSize`, `lineHeight`) are inline too; move those to classes when the station classes are folded into EFC_Styles.
