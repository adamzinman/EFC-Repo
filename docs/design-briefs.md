# Design briefs: faceplates and screens

These designs were worked on in other sessions. Their exports aren't in this repo yet. Add each with `python3 tools/import_project_zip.py <zip>` (the latest copies are in Downloads), then record it in [`inventory.md`](inventory.md).

## EFC_IOFaceplates: Modicon x80 I/O card faceplates
- A suite of Perspective 8.1 faceplates (it must survive the 8.3 upgrade) for Modicon x80 I/O cards read through the M580.
- **Decided:**
  - OPC UA.
  - **One UDT and one faceplate per card** (not per channel), tied directly to the cards' native **IODDTs**.
  - Popups open from a **rack/backplane overview**.
  - The card list comes from the Controls Standard hardware table.
- **Latest export:** `EFC_IOFaceplates.zip` (2026-10-07).

## EFC_StationFaceplates: scale/fill station (DDT_Station)
- Redesign of the "Station faceplate", which collects and displays scale data and is backed by the `DDT_Station` UDT. The new design is ISA-101 light gray in EFC_Styles, with new classes only if needed.
- **Three types:**
  1. **Sidebar faceplate** for the overview screen, 300×800 px at 1080p, based on the old Station popup.
  2. **Medium faceplate** for the filling screen: only the fill information needed, plus direct setpoint entry.
  3. **Compact tile** on the overview screen that opens the sidebar when clicked. The sidebar opening is wired up on site.
- **Latest export:** `EFC_StationFaceplates.zip` (2026-10-06; `EFC_StationFaceplates_v1.zip` is the earlier one).

## Diaphragm compressor screen (PDC-style, two-stage)
- A Perspective 8.1 HMI screen for a PDC-style two-stage diaphragm compressor. Several layout options are to be compared, in ISA-101 light gray using EFC_Styles and the PID_Symbols templates (`Templates/Rotating/Compressor_Diaphragm`).
- **Related export:** `PID_Compressor_Diaphragm_PROJECT.zip` (the early compressor symbol project, superseded by PID_Symbols).
- **Status:** in progress.

## Haskel pump (air-driven liquid PD pump)
- A faceplate plus a simple P&ID status symbol.
- **Inputs:** the PLC has discharge, suction and drive-air pressure. There's no existing DDT/UDT yet.
- **Decided:**
  - Use the existing **Rotary PD** symbol (`Templates/Rotating/Pump_PD_Rotary`) on P&ID screens.
  - The drive-air I/P uses the premade PID block (the earlier plan for 3 configurable drive-air control types was dropped).
  - An air-driven depiction is parked for later.
- Clicking a Rotary PD that is set up as a Haskel pump opens the faceplate in the shell's dynamic window (see [`screen-layout-standard.md`](screen-layout-standard.md)).
- **Status:** in progress; not built.
