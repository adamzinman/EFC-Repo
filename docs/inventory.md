# Design inventory

This lists every design in the "Ignition SCADA Management" project and where it lives. Status as of v6.0 (2026-10-07).

## In this repo (generated, checked by `check_81.py`)
| Design | Version | Project / files | Generator | Docs |
|---|---|---|---|---|
| EFC_Styles: ISA-101 style classes | 166 classes (v5.1) | `projects/EFC_Styles/` | `generator/build_styles.py` | [style-library](style-library.md), [style-class-index](style-class-index.md), [isa101-audit](isa101-audit.md) |
| PID_Symbols: controlled-device templates | v5.1 (gateway-verified on a DDT_Valve instance) | `projects/PID_Symbols/` (16 templates + `_Demo`) | `generator/build_pid.py`, `pid_common.py`, `active.py` | [library-reference](library-reference.md), [design-notes](design-notes.md) |
| EFC_PID_Library: Styles + PID merged | v5.1 | `projects/EFC_PID_Library/` | `build.py` (merge) | README |
| EFC_ProcessValues: PV_StatusStrip / PV_RangeBar | PV 1.3.0 (not re-tested on a gateway) | `projects/EFC_ProcessValues/`, `tags/PV_Demo_Tags.json` | `generator/build_pv.py`, `common.py` | [pv-display](pv-display.md), [pv-style-index](pv-style-index.md) |
| Static P&ID symbols | v5.1 | `symbols/<Category>/` (198) + `symbols/Active/` (16) | `generator/v2/`, `pid_common.py` | [library-reference](library-reference.md) |
| PID tags (UDTs + demo) | v5.1 | `tags/PID_*_UDT.json`, `Valve_Discrete_Demo_UDT.json`, `PID_Demo_Instances.json` | `build_pid.py` | [library-reference](library-reference.md) |
| Screen design standard | — | docs only | — | [screen-layout-standard](screen-layout-standard.md) |

## Designs not in this repo yet (exports exist; add with `tools/import_project_zip.py`)
| Design | Latest export | Docs here |
|---|---|---|
| PID_Loops: loop cards B1–B4 + LoopConfig popup | `PID_Loops_PROJECT.zip` (needs the `xMidYMid` version) | [pid-loop-templates](pid-loop-templates.md) |
| EFC_IOFaceplates: Modicon x80 card faceplates | `EFC_IOFaceplates.zip` (2026-10-07) | [design-briefs](design-briefs.md) |
| EFC_StationFaceplates: DDT_Station sidebar / filling / tile | `EFC_StationFaceplates.zip` (2026-10-06) | [design-briefs](design-briefs.md) |
| Diaphragm compressor screen | in progress | [design-briefs](design-briefs.md) |
| Haskel pump faceplate | in progress, not built | [design-briefs](design-briefs.md) |

## Retired
- PID_Symbols v2 static views and wrapper templates. They were replaced in v3/v4; their artwork lives on as `symbols/` SVGs.
- `PID_Compressor_Diaphragm_PROJECT.zip`: the early single-symbol project, superseded by `Templates/Rotating/Compressor_Diaphragm`.

## Cross-cutting to-dos
- **PID_Symbols:** move the alarm outline from `isAlarmActiveFiltered` to the `queryStatus` pattern used by EFC_ProcessValues. Perspective doesn't re-run `isAlarmActiveFiltered` when alarms change. Preview first, per the workflow rule.
- **EFC_Styles:** fold in the PV classes and align PV Diagnostic `#7A7A7A` with `#6E6E6E`.
- **PID_Loops:** move to EFC_Styles classes; decide whether to relabel OUT as CV.
- **PID layout open items:** valve alarm outline 2 px vs 3 px; OPENING/CLOSING width; centering when the M is shown.
