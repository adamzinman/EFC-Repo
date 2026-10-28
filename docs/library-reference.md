# Library reference: PID_Symbols + EFC_Styles (v5.1, Ignition Perspective 8.1)

A library of templates for actively controlled devices, in a modern ISA-inspired style. It is built from the design notes in [`design-notes.md`](design-notes.md). Shapes come from the reference library; colors and text come from EFC_Styles, revised to match ISA-101, ISA-18.2, NFPA 79 and ANSI Z535.

## Contents
Since v7.0 everything ships as one project, **EFC_Library** (`dist/EFC_Library_PROJECT.zip`, built with `python3 build.py --dist`; unzipped in the repo at `projects/EFC_Library/`). The rows below describe the parts that are merged into it.

| Item | What it is |
|---|---|
| PID_Symbols part | 16 templates (one per controlled-device symbol) + `Templates/_Demo`, inside EFC_Library |
| EFC_Styles part | Style library (166 classes, ISA-101 audit fixes applied), inside EFC_Library |
| `tags/` (repo root) | UDTs `PID_Motor`, `PID_ControlValve`, the demo stand-in `Valve_Discrete_Demo` (same members as the plant discrete-valve UDT) and 13 demo instances (`PID_Demo` folder) |
| `symbols/` (repo root) | 214 plain SVGs to import as needed: all 198 static symbols from v2, recolored to the standards palette, plus the 16 active symbols in `symbols/Active/` |
| `docs/previews/` | Rendered previews of the demo templates (`python3 build.py --preview`) |
| `generator/` | `active.py` (geometry + palette), `build_pid.py` (templates), `pid_common.py` (shared helpers, static SVG export), `build_styles.py` (EFC_Styles), `preview.py` / `preview_pid.py`, `check_81.py` (8.1 import check), `make_project_zip.py`, `v2/` (static symbol source). Run everything from the repo root with `python3 build.py`. |

## Templates (one per symbol, only parameter = `tagPath`)
The project imports straight into **Views → Templates** (`Templates/<Category>/<Symbol>`, demo at `Templates/_Demo`), with no `PID` folder.
Every template takes **`tagPath`** (the UDT instance). Valve and running-equipment templates also take **`useButton`** (default `true`; see v4.4). Everything else comes from the UDT:
- the tag text comes from `Name`, with `Description` as its tooltip
- feedback mode comes from `Feedback_Enabled`
- the mode letter and P/I badges come from the mode, permissive and interlock members
- the alarm outline is the **highest active alarm priority on any member of the instance** (`isAlarmActiveFiltered` on `tagPath/*`, priorities 1–4; shelved alarms ignored)

The symbol is **embedded in the template as a Perspective Drawing** (`ia.shapes.svg`): every SVG shape lives in the view JSON, and each shape's fill, outline color and outline weight is bound to the state, command and alarm properties, so the fills change in place as the state changes. There's no image link or data URI. There are no nested symbol views. Clicking the symbol opens the device's dynamic window in the page's `dw_Right` dock (see [Page setup: the dw_Right dock](#page-setup-the-dw_right-dock)).

| Template | Size @1080p | UDT | Button |
|---|---|---|---|
| `Templates/Valves/Valve_OnOff_Pneumatic` · `Valve_Solenoid` · `Valve_MOV` | 120×100 | `T_DValve` | Operator+ writes `Cmd_Close` when `Out_Open` is true, otherwise `Cmd_Open` (one-shot), Manual only |
| `Templates/Valves/Valve_Control` | 120×100 | `T_CValve` | none (operated from the dynamic window) |
| `Templates/Rotating/` `Pump_Centrifugal` · `Pump_Vacuum` · `Pump_PD_Rotary` · `Pump_Diaphragm` · `Pump_Reciprocating` · `Compressor_Centrifugal` · `Compressor_Diaphragm` · `Blower` · `Agitator` · `Motor` | 120×116 | `PID_Motor` | Momentary start/stop (PB) |
| `Templates/HeatTransfer/` `HX_AirCooled` · `Heater_Electric` | 120×116 | `PID_Motor` | Momentary start/stop (PB) |

To use one, drag the template for the right symbol onto a screen and set `tagPath`. `PID_Motor` and `PID_ControlValve` gained `Name`, `Description` and `Feedback_Enabled` members, and `PID_Motor.Fault` now carries a demo High alarm.

### Layout (the same on every template)
- **Tag name:** above the symbol, centered on the symbol's centerline. Uses `Text/TagName`.
- **Status:** below the symbol, centered on the same centerline. It stays centered whether or not the button is there.
- **P badge** (`Indicator/PermissiveBadge`): on the left. Shown when `PermOK` = 0.
- **I badge** (`Indicator/InterlockBadge`): on the right. Shown when `Intlk` = 1.
- **Badges and the process line:** the badges are never on the process line.
  - Valves: they sit at actuator height.
  - Pumps and compressors: they sit above the y = 50 ports.
  - Centrifugal pump and blower: I drops to lower right, clear of the top-right discharge (set automatically from `symbol`).
- **Momentary button** (`Button/Momentary`, blank square): bottom left, **visible only in Manual** (valves: `Manual` = 1; motors: `Mode` = 1). It's hidden in Auto, Off and Locked Out.
  - Open/close on valves, start/stop on running equipment.
  - **Motor:** writes PB 1 on press and 0 on release. Disabled only when stopped **and** P or I is showing.
  - **AutoValve:** one click writes `Cmd_Close` when `Out_Open` is true, otherwise `Cmd_Open`, through `efc.ui.cmd` (Operator+; see the AutoValve section).
  - Valve closing bypasses the permissive/interlock opening restriction, but still requires MAN, available, not LOCAL and not OOS. Tooltip reads Open/Close or Start/Stop.
- **No mode letters** (note 27). Manual is shown by the button, which only appears in Manual.
  - Other options (white M, orange M, inverted tag, chip) are documented in the notes. To switch, change `MANUAL_M` in `build_styles.py`.

### Status logic
| Template | Status values | State derivation |
|---|---|---|
| AutoValve | CLOSED · OPEN · OPENING / CLOSING · FAULT | `Sts_Fault` first, then `Sts_Opened`, then `Sts_Closed`, otherwise travel; direction from `Out_Open`. |
| ControlValve | `NN %` (Pos, or Out without feedback) · FAULT | Body = position (> 1 % = open); actuator head = command (Out > 1 %) |
| Motor | STOPPED · RUNNING · STARTING / STOPPING · FAULT | Run and Cmd agree → that state; they disagree → transition; Fault → fault. Without feedback the symbol follows Cmd. |

### AutoValve: current T_DValve mapping
The three discrete templates bind to a `T_DValve` instance through `tagPath`. See [discrete-valve help](help/Templates/Valves/Valve_Discrete.md) for the full bindings and scripts.

| Member | Used for |
|---|---|
| `Out_Open` | Actuator head color and OPENING/CLOSING direction; command button chooses Close when true, Open otherwise |
| `Sts_Opened` / `Sts_Closed` | Body state (opened takes priority over closed) |
| `Sts_Fault` | Fault state, checked before opened/closed; also blocks the double-tap command |
| `Cfg_HasZSO` / `Cfg_HasZSC` | Whether limit switches are fitted; with neither fitted the head follows the body color. Limit-switch LEDs are in the dynamic window's Feedback section, not the template. |
| `Sts_NotPerm` / `Sts_Intlk` | P/I badges; block opening from the button |
| `Intlk/Sts_FirstOut` / `Intlk/Cfg_CondDesc` | First-out text in the I tooltip |
| `Mode/Sts_Man` / `Mode/Sts_OOS` | Manual and out-of-service flags used by the button |
| `Sts_Avail` / `Sts_Local` | Availability and local-control guards |
| `Cfg_Tag` / `Cfg_Desc` | Tag text (last tag-path segment is the fallback) and tooltip |
| `Cmd_Open` / `Cmd_Close` | One-shot operator commands; scripts write True, with no timed reset in the HMI |

**Button rules:** with `useButton = true`, the button is visible only in MAN. It is enabled in MAN, available, not LOCAL, not OOS, and either `Out_Open` is true (closing) or neither permissive-missing nor interlocked. The script calls `efc.ui.cmd(self, member, True, 1)`, which checks Operator+ before writing. The button's enable expression does not separately check `Sts_Fault`.

**Touch mode:** with `useButton = false` and `dblCmd = true`, double-tap calls `efc.ui.dblCmd`. It requires Operator+, `Mode/Sts_Man` and `Sts_Avail` true, and `Sts_Intlk`, `Sts_NotPerm`, `Sts_Local` and `Sts_Fault` false. It writes `Cmd_Close` if `Sts_Opened` is true, otherwise `Cmd_Open`. This path does not separately check `Mode/Sts_OOS` and does not bypass permissive/interlock guards for closing. With touch mode, M is shown while manual; the default button mode hides that letter.

A single click opens `Templates/Dynamic Window/Valves/ValveDiscrete` in `dw_Right`. The PLC must enforce command acceptance and clear one-shot commands.

### UDTs for the other templates (memory tags in the export; point them at the M580 addresses)
| UDT | Members |
|---|---|
| `PID_Motor` | Cmd, Run, PB, PermOK, Intlk, Fault, Mode |
| `PID_ControlValve` | Out (%), Pos (%), PermOK, Intlk, Fault, Mode |

**PLC side (Motor template):**
- Toggle Cmd on the **rising edge** of PB, and ignore open/start requests when not permitted.
- The PLC must enforce permissives and interlocks itself; the HMI badges are information only.
- A very fast click can produce a short pulse. If your scan could miss it, have the PLC reset PB and delete the release events on the button.

## Page setup: the dw_Right dock
Dynamic windows (`Templates/Dynamic Window/<category>/`) open in one right-side Perspective dock per page, id `dw_Right` (decision 31). A template click runs `efc.ui.openDynamic(self)`, which loads the window into that dock with `system.perspective.alterDock` and opens it with `system.perspective.openDock`. This needs **Ignition 8.1.19 or later** (the library minimum is 8.1.22).

In each page's **Page Configuration**, add a **right dock**:
- id `dw_Right`
- view: the page's trends overview as the initial view (shown when the page loads; a click replaces it with the device's window)
- size 400 px at 1080p (37.04 vh equivalent; the window is 400 x 860, decision 25)
- display "visible": the dock is always present (decision 32)
- content "cover": the dock covers the right-hand section of the shell
- handle "hide"

To make the trends overview the view a window's close button returns to, call `efc.ui.setDefaultDock(self, viewPath, params)` in the screen's root `onStartup`. A window's close button then puts that view back. Without a default, the close button closes the dock.

Scripts can also open the dock directly: `efc.ui.openWindow(dw, tagPath, model=None)` opens a window by its id (`dw_ValveDiscrete`, `dw_Loop`, ...), and `efc.ui.showDock(path, params)` loads any view.

## Access levels: the lock and the AccessDenied popup
The user's level comes from the Perspective session's security levels, `session.props.auth.securityLevels` (decision 33). `efc.ui.level` takes the highest of `Guest` 0, `Operator` 1, `Maintenance` 2, `Supervisor` 3, `Engineer` 4 and `Admin` 5 found anywhere in that tree, so both `Authenticated/Roles/Operator` and a custom security level named `Operator` count. Names are matched without regard to case. If your gateway uses other names, map them in `efc.ui.ROLE_ALIASES` (for example `'administrator': 'Admin'`); a user whose roles match nothing is Guest.

- **Command buttons below the user's level stay visible with a lock.** This covers the template Manual button and, in the dynamic windows, the mode, command, preset, FWD/REV, ACK and interlock RESET buttons. The tooltip says which role is needed.
- **A press anyway is refused.** `efc.ui.cmd` writes nothing, logs a warning to the `efc.ui` logger and opens `Templates/Dynamic Window/Parts/AccessDenied`: "Invalid access level", what was pressed, the role it needs, and who is signed in. Double-tap commands and ACK behave the same.
- **Failed writes are logged too.** When a write comes back bad (missing member, read-only tag, bad quality), `efc.ui` logs the tag path and the quality.
- Sections and controls that are Supervisor+ or Engineer+ (bypass, alarm limits, configuration, tuning, the Maintenance section) stay hidden below their level, as before (decision 27).
- The HMI check is a convenience, not security: enforce access in Perspective security and the PLC.

## Placing templates in a flex container
Template text is sized in vh, so it grows with the screen. The box a template sits in has to grow the same way, or the text outgrows it and clips. When you drop a template into a flex container, the Designer sets the child's `position.basis` to a pixel size. That pins the box: at 1080p it fits, but on a taller screen the vh text gets bigger while the box doesn't, and the bottom row is cut off with a scrollbar.

Set `position.basis` in vh instead, with `grow` and `shrink` at 0:
- Basis is the size along the parent's direction: width in a row, height in a column.
- Convert the template's default size at 1080p: px / 10.8 = vh. For example, `PV_StatusStrip` (104 × 54) is `9.63vh` in a row and `5vh` in a column.
- `basis: auto` also works if the box should size itself from its content.

`Templates/ProcessValues/_Demo` shows the pattern: each strip sits in a row with `basis: 9.63vh`, grow 0, shrink 0. In a coordinate container, use percent mode for the same reason: fixed mode pins the box in pixels.

## Symbols & colors
| State | Fill | Notes |
|---|---|---|
| 0 stopped / closed | gray `#9E9E9E` | |
| 1 running / open | white `#FFFFFF` | |
| 2 transition | light gray `#C4C4C4` | Darker than the `#D9D9D9` screen so it stays visible |
| 3 fault | dark gray `#3A3A3A` | Inner details flip to light gray so they stay readable. Red is reserved for Critical alarms. |

- **Alarm outline:** 3 px in the priority color. Low `#00A3E0`, Medium `#FFD200`, High `#FF7A00`, Critical `#D50000`.
- **Actuator head:** shows the command; the valve body shows position feedback.
- **On/off valve:** rectangular actuator, the stem runs to the body center, and there's no ball circle in the body.
- **Diaphragm compressor:** geometry taken from the user's base image (converging lines, bold curved diaphragm). Its geometry is in the notes doc.

## EFC_Styles changes in this release
**v5 (ISA-101 audit, see `claude/isa101-audit.md`):**
- **`Button/Danger`:** hover and pressed are now neutral (`#F5F5F5` / `#BFBFBF`); the last red is gone.
- **`State/OutOfService`:** text darkened to `#5E5E5E` (5.5:1), border `#7F7F7F`.
- **`Indicator/Permissive`** (text form): `#8F4500` (4.9:1).
- **`Alarm/Diagnostic`:** fill `#6E6E6E` (5.1:1 with white text); the text form on dark is `#9A9A9A`.
- **`Alarm/Status/ClearedUnacked`:** steady and faded (opacity 0.45) instead of blinking. Flashing now means an active, unacknowledged alarm only.
- **`Text/Micro` and `Text/Size/XXS`:** 9 px → 10 px.
- **New class `Util/Collapsed`:** takes an element out of the layout with zero width.

**Earlier (v3/v4):**
- **Fault color:** `#D50000` → `#3A3A3A`. This affects `State/Fault`, `Text/Color/Fault` and `Indicator/LED/Fault`.
- **Diagnostic alarm:** purple → gray (`#7A7A7A`, now `#6E6E6E`).
- **Simulated / forced:** purple → teal.
- **`Button/Danger`:** now neutral with a heavy border.
- **`Util/Highlight`:** now blue-gray.
- **`Util/Blink`:** removed. Flashing now means an unacknowledged alarm only.
- **New classes:** `Indicator/PermissiveBadge`, `Indicator/InterlockBadge`, `Mode/ManualSplit`, `Mode/ManualSplitStatus`.

## Ignition 8.1 compatibility
Both projects target **Ignition 8.1** and pass `generator/check_81.py`, a static import check:
- **Project zips:** `project.json` sits at the zip root (title, parent, enabled, inheritable). Every resource uses the 8.1 layout: `com.inductiveautomation.perspective/<type>/<path>/` plus `resource.json` (scope `G`, version 1).
- **Style classes:** in the 8.1 `style.json` form (`base.style` plus `variants` with `pseudo`).
- **Coordinate containers:** percent mode, with every child position a 0–1 fraction (the 8.1 format).
- **Expression functions:** only 8.1 functions are used: `case`, `if`, `indexOf`, `lastIndexOf`, `len`, `numberFormat`, `substring`, `coalesce`, `toStr`, `try`, `forceQuality`, `isAlarmActiveFiltered`. The earlier `endsWith()` call doesn't exist in 8.1 and was replaced with `indexOf()`.
- **Symbol rendering (v5.1):** each template contains one **Drawing** component (`ia.shapes.svg`, `preserveAspectRatio` = `xMidYMid`, a valid 8.1 enum value). Its `elements` hold the symbol's paths, rects and circles. The bindings `props.elements[n].fill.paint`, `.stroke.paint` and `.stroke.width` point at the custom props `fill`, `head`, `line`, `con` and `lw` (plain `#RRGGBB`). The control-valve position bar is a Drawing too: its fill rect's `y`/`height` are bound to Pos and its pointer path `d` to Out. Nothing lives in Image Management, and there are no external files or data URIs.
- **Alarm lookup:** `isAlarmActiveFiltered(tagPath + "/*", "*", "*", p, p, 0, 1, 0)`, an 8.1 alarming expression function. Each call is wrapped as `forceQuality(coalesce(try(…, false), false))`. The function returns Bad_NotFound quality when no member of the instance has an alarm configured (seen on DDT_Valve). The wrapper turns that into 0, so the bad quality can't spread to the outline bindings (`line`, `lw`).
- **Bindings and events:** indirect tag bindings on `{view.params.tagPath}`. Gateway-scoped DOM event scripts call `system.tag.writeBlocking` and `system.perspective.openPopup`.
- **Tags:** 8.1 tag JSON (`UdtType` / `UdtInstance`) with data types `Boolean`, `Int2`, `Float4`.
- **Version-dependent:** the EFC_Styles **Advanced Stylesheet** (`stylesheet/stylesheet.css`, holding only the unacknowledged-alarm blink keyframes) needs **8.1.22 or later**. On older 8.1 builds, everything else works and `Alarm/*/Unacked` shows solid instead of blinking.
- **Not testable offline:** the import itself and live rendering. Open `Templates/_Demo` after import.

## Single-file import (EFC_PID_Library_PROJECT.zip)
`EFC_PID_Library_PROJECT.zip` holds everything in one project, with no parent required:
- all EFC_Styles classes and the stylesheet
- the 16 templates
- `Templates/_Demo` and `Styles/_Catalog`

Import it on its own, or set it as your HMI project's parent. The two separate zips (`EFC_Styles_PROJECT.zip` then `PID_Symbols_PROJECT.zip`) are still included if you prefer the inheritance chain. Don't import both the single file and the separate pair into the same inheritance chain.

## Import order
1. Gateway: import `EFC_Styles_PROJECT.zip` (overwrite the existing project).
2. Tag Browser → Data Types → import `PID_Motor_UDT.json`, `PID_ControlValve_UDT.json`, and `Valve_Discrete_Demo_UDT.json` (demo only; real valves use your existing discrete-valve UDT).
3. Tags root → import `PID_Demo_Instances.json` (optional demo).
4. Gateway: import `PID_Symbols_PROJECT.zip` (overwrite the earlier version). Check that its parent is `EFC_Styles` and your HMI project's parent is `PID_Symbols`.
5. Open `Templates/_Demo`.
