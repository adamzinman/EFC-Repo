# EFC Station faceplates (EFC_Library), Ignition Perspective 8.1

Three views for the `T_Station` type in ISA-101 light gray, shipped in `projects/EFC_Library/`. Detailed behavior and member mappings are in [Station_Fill](help/Templates/Station/Station_Fill.md), [Station_Tile](help/Templates/Station/Station_Tile.md) and the [Station dynamic window](help/Templates/Dynamic%20Window/Station/Station.md).

| View | Size @1080p | Use |
|---|---|---|
| `Templates/Dynamic Window/Station/Station` | 400 × 860 | Type 1: full faceplate, dynamic-window id `dw_Station`, opened in the page's `dw_Right` dock |
| `Templates/Station/Station_Fill` | 300 × 400 | Type 2: filling screen, with live fill data and setpoint entry |
| `Templates/Station/Station_Tile` | 220 × 96 | Type 3: overview tile. Clicking it opens the station window in the `dw_Right` dock. |
| `Templates/Station/_Demo` | 1920 × 1080 | All three bound to the demo tags |

Set **`tagPath`** to the `T_Station` instance, e.g. `[default]FillStn/Station_1`. Fill and the Station window take only `tagPath`. Tile also takes `tType` (default `T_Station`), `dockId` (window-id override) and `dwTagPath` (tag-path override for the window).

## Import
Since the October 24, 2026 merge (PR #36, decisions 31–32), dynamic windows use `Templates/Dynamic Window/<category>/*` and one right-side `dw_Right` dock. The imported `Station_Sidebar` name is retained only in the source project.

1. **Gateway → Config → Projects → Import** `EFC_Library_PROJECT.zip` (or `dist/EFC_Library_PROJECT.zip` from `python3 build.py --dist`). It includes the views, style classes and `efc.ui` scripts; no parent project is required.
2. Optional demo:
   - Tag Browser → Data Types → import `tags/T_Station_Demo_UDT.json`.
   - Tags root → import `tags/Station_Demo_Instances.json`.
   - Open `Templates/Station/_Demo`.
3. Dock: in Page Configuration on the overview page, add the library's **right dock** (the same on every page, see [library-reference](library-reference.md#page-setup-the-dw_right-dock)):
   - id `dw_Right`
   - view: the page's trends overview, shown on page load
   - size 400 (`efc.ui.sizeDock` rescales it to 37.04 vh: 400 px at 1080p, 800 px at 4K, decision 33), display "visible", content "cover", handle "hide" (decision 32)

   The tile's onClick calls `efc.ui.openDynamic(self)`, which loads `Templates/Dynamic Window/Station/Station` with `{"tagPath": …}` into `dw_Right` and opens it (Ignition 8.1.19+). The window's ✕ calls `efc.ui.closeDynamic(self)`, which puts the page's default view back (`efc.ui.setDefaultDock` in the screen's onStartup) or closes the dock.

## Member mapping
The display names below are keys in `view.custom.t`, retained from the imported faceplates. They are not PLC member names. Indirect bindings map them to `T_Station` as follows; the complete mapping is in [Station_Fill help](help/Templates/Station/Station_Fill.md#t-raw-tag-values).

| Display key(s) | T_Station member(s) |
|---|---|
| `Disabled`, `Failed`, `Complete`, `Filling`, `Active` | `Sts_Disabled`, `Sts_Failed`, `Sts_Complete`, `Sts_Filling`, `Sts_Active` |
| `Vacuuming`, `Vacuumed`, `Venting`, `Recovering` | `Sts_Vacuuming`, `Sts_Vacuumed`, `Sts_Venting`, `Sts_Recovering` |
| `ReadyToStart`, `ReadyToFill`, `Press_Balanced` | `Sts_ReadyToStart`, `Sts_ReadyToFill`, `Sts_PressBalanced` |
| `Selected`, `Msg` | `Sts_Selected`, `Sts_Msg` |
| `NetWeight`, `GrossWeight`, `TareWeight`, `TotalWeight` | `Val_Net`, `Val_Gross`, `Val_Tare`, `Val_Total` |
| `TargetWeight`, `SampleWeight`, `Deadband` | `Prm_TargetWt`, `Prm_SampleWt`, `Prm_Deadband` |
| `PT`, `PT_Diff`, `PT_Valid`, `Vessel_Present` | `Val_PT`, `Val_PTDiff`, `Inp_PTValid`, `Inp_VesselPresent` |
| `Press_Max`, `SamplePress` | `Prm_MaxPress`, `Prm_PrefillPress` |
| `InletREQ`, `SampleREQ`, `VacuumREQ` | `Sts_InletReq`, `Sts_SampleReq`, `Sts_VacuumReq` |
| `InletCMD`, `SampleCMD`, `VacuumCMD` | `Out_InletCmd`, `Out_SampleCmd`, `Out_VacuumCmd` |
| `StationName`, `ScaleName`, `Units` | `Cfg_Desc`, `Cfg_ScaleName`, `Cfg_EU` |

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

**Setpoints** (numeric entry, bidirectional; disabled while the station is disabled). In the Station dynamic window these controls also require Operator+; the embedded Fill view has no role check.
- Target → `Prm_TargetWt`
- Sample → `Prm_SampleWt`
- Max press → `Prm_MaxPress`
- Prefill press → `Prm_PrefillPress`
- Deadband → `Prm_Deadband` (Station dynamic window only)

**Commands**
- **Select** pulses `Cmd_Select`; the button label shows `Selected`.
- **Tare**, **Zero** and **Reset** ask for confirmation, then pulse `Cmd_Tare`, `Cmd_Zero` and `Cmd_Reset`.
  - A pulse writes 1, then writes 0 after 1 s.
  - Tare and Zero are locked while the station is active or disabled.
  - Reset is enabled only after Complete or Failed.
  - The Station dynamic window also gates these controls at Operator+. Fill uses the same pulse and confirm scripts without a role check; enforce command access in Perspective security and PLC logic.

## Check on the live gateway
- **Setpoint mapping:** verify `Prm_PrefillPress` and `Prm_SampleWt` against the PLC configuration. The views bind these members directly.
- **Command pulse:** if the PLC treats `Cmd_Tare`, `Cmd_Zero`, `Cmd_Reset` or `Cmd_Select` as a level rather than a rising edge, adjust the 1 s pulse.
- **Derived-state recalculation:** all derived values come from one script transform: the property binding `view.custom.t` → `custom.s`. Confirm it recalculates when a single tag changes. If it doesn't, change that binding to an expression binding on `now(1000)` with the same transform.
- **Old 8.1 builds:** before 8.1.22 the stylesheet keyframes aren't loaded, which only affects blinking alarm classes; nothing here blinks.

## Station style classes (included in EFC_Library)
`Station/Step/Done`, `Station/Step/Active`, `Station/Step/Pending`, `Station/Step/Fault`, `Bar/Band/Deadband`

## In this repo
- **Project:** source in `imported/EFC_StationFaceplates/` (imported from the 2026-10-06 export, v6.2); ships inside `projects/EFC_Library/` at `Templates/Station/`, with `Station_Sidebar` remapped and resized to `Templates/Dynamic Window/Station/Station` (400 × 860). Edit it in the Designer and re-import; its generator (`build_station.py`) is not in the repo.
- **Demo tags:** `tags/T_Station_Demo_UDT.json`, `tags/Station_Demo_Instances.json`.
- **Build checks:** `python3 build.py` runs the 8.1 static import check; live import and rendering still need a gateway check.
- **Inline styles:** mostly layout spacing (`gap`, `height`, `padding`, margins). A few typography values (`fontSize`, `lineHeight`) are inline too; move those to classes when the station classes are folded into EFC_Styles.
