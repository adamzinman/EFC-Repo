# Trends overview for dw_Right: what the repo already has (read-only research)

Branch `claude/dynamic-window-opendock`. Paths are relative to `/home/user/EFC-Repo`.

## Headline findings
- **No trends overview exists yet.** Decision 32 makes it the dock's initial view (`steward/DECISIONS.md:38`). `docs/improvements.md:13` (P1 item 3) asks for a new `Templates/Dynamic Window/TrendsOverview` and a demo page shell. No screen calls `setDefaultDock` yet (`docs/improvements.md:12`).
- **Nothing in PCLib states the variable type.** There is no VarType, Kind, MeasType or ISA-letter member on T_AI, T_PID, T_KPI or T_Station. The only per-type enums are `T_Analyzer.Cfg_AnType` (`types/gen_pclib.py:906`) and `T_Heater.Cfg_CtrlType` (`:502`). Grouping today has to come from `tType`, the EU text, or the first letter of `Cfg_Tag` (ISA-5.1).
- **History is enabled nowhere.** `gen_pclib.py`, the export JSON and all `tags/*.json` have no `historyEnabled`, `historyProvider` or `sampleMode`. HatfieldDB is not mentioned anywhere. The existing trend part needs history (`docs/help/Templates/Dynamic Window/Parts/Trend.md:150`: "Tag history must be enabled for each pen, or the graph stays blank").
- **No generated template root has a `system` event** (`onStartup` / `onShutdown`). Every root has only `dom.onClick`. The only `onStartup` was the retired LoopConfig popup (`generator/pid_loops/generate_loops.py:543`). A registration call is therefore a new event at known emit points (section 3).

## 1. Templates with analog values, and where the value and metadata live

All templates take `tagPath` (a T_ instance) plus `tType`, `dockId` and `dwTagPath`. HDR = `Cfg_Tag` STRING[20] (ISA-5.1 tag) and `Cfg_Desc` STRING[40] (`gen_pclib.py:36-39`), shared by every type below except T_KPI.

| Template (generator) | tType | Value member(s) to chart | EU member | Range members | Name/desc | Variable-type member |
|---|---|---|---|---|---|---|
| `ProcessValues/PV_StatusStrip`, `PV_RangeBar` (`generator/build_pv.py`; binds `custom.pv/name/desc/units` at `:130-133`; RangeBar adds `Cfg_EUMin/Max` at `:286`; tType default `T_AI` at `:253`) | T_AI | `Val_PV` (`gen_pclib.py:297`, CSV:132). Also `Val_PVPct`, `Val_ROC` | `Cfg_EU` STRING[12] (`:281`) | `Cfg_EUMin`, `Cfg_EUMax` (`:286-287`); alarm limits `Alm_HH/H/L/LL/Cfg_Lim` | HDR | none |
| `AnalogIndicator/A_RangeBar`, `B_PointerScale`, `C_CompactRow`, `D_MiniColumn` (`generator/analog_indicators/gen_analog_indicators.py:42-46` TAGM; tType forced to `T_KPI` at `:128`) | T_KPI | `Val_PV` (`types/T_KPI/gen_pclib_T_KPI_block.py:17`) | `Cfg_EU` (`:7`) | `Cfg_EUMin/Max` (`:10-11`), ideal band `Cfg_IdealLo/Hi` (`:12-13`), limits under `Alm_*` | `Cfg_Tag`, `Cfg_Desc`, `Cfg_ShortDesc` STRING[12] | none. **T_KPI is not in `gen_pclib.py` or the PCLib export yet** (the export has 28 types and none is T_KPI; it is a proposal in `types/T_KPI/README.md:1`) |
| `Loops/Loop_B1..B4` (`generator/pid_loops/generate_loops.py:116-130`; tType `T_PID` at `:238`) | T_PID | `Val_PV` (`gen_pclib.py:593`), `Val_SP` (`:591`), `Out_CV` (`:590`, %) | `Cfg_PVEU` STRING[12] (`:558`). CV is always % | `Cfg_PVMin/Max` (`:577-578`), `Cfg_SPMin/Max`, `Cfg_CVMin/Max` (CSV:480-485) | HDR | none |
| `Valves/Valve_Control` (`generator/build_pid.py:222`, `dw_params(..., "T_CValve")` at `:236`) | T_CValve | `Val_Pos` (`gen_pclib.py:407`), `Val_Demand` (CSV:239), `Out_CV` (`:403`) | none: % is implied | `Cfg_OutMin/Max` (CSV:223-224) | HDR | none (type = valve position) |
| Motors: `Rotating/*` (`build_pid.py:249-286`; `ttype_for` at `:247`) | T_Motor | `Val_Current` (`gen_pclib.py:432`), `Val_LoadPct` (`:433`). **The template binds neither**: it shows state only | none: A and % are implied | `Cfg_RatedAmps` (`:113`) | HDR | none |
| `Rotating/VFD` (template binds `Val_Spd` and `Cfg_SpdEU`, `build_pid.py:263`) | T_VFD | `Val_Spd` (`:476`), `Val_Current` (`:477`), `Val_SpdRef`, `Val_Torque`, `Val_Power` (CSV:375-379) | `Cfg_SpdEU` STRING[8] "%, Hz, rpm" (`:456`). Current is in A | `Cfg_SpdMin/Max` (CSV:337-338) | HDR | none |
| `HeatTransfer/Heater_Electric` (T_Heater via `ttype_for`) | T_Heater | `Val_Current` (`:543`), `Val_Power` kW, `Val_Duty` %, `Val_PwrDemand` (CSV:444-447). The template binds none of them | none: A, kW and % are implied | `Cfg_RatedAmps` (`:510`), `Cfg_PwrMin/Max` | HDR | `Cfg_CtrlType` is the control type, not a measured-variable type |
| `Station/Station_Tile` (tType `T_Station`), `Station_Fill` (tagPath only, no tType). Both imported from the Designer (`imported/EFC_StationFaceplates/`) | T_Station | `Val_Net`, `Val_Gross`, `Val_Tare`, `Val_Total` (weight), `Val_PT`, `Val_PTDiff` (pressure) (`gen_pclib.py:1052-1058`, CSV:930-937) | `Cfg_EU` STRING[8] covers **weight only** (`:1011`). **No EU member for `Val_PT`** | `Prm_TargetWt`, `Prm_MaxPress`, `Prm_PrefillPress` | HDR | none |

Other types with an EU text (none has a template yet): `T_Tank.Cfg_LvlEU` and `Cfg_VolEU` (CSV:643-644), `T_Totalizer.Cfg_RateEU` and `Cfg_TotEU` (CSV:683-684), `T_GasDet.Cfg_EU` (CSV:816).

The EU text is not carried into Ignition tag metadata. `_ign_atomic` sets `engUnit` only for TIME members (`"ms"`, `gen_pclib.py:1495-1496`). There is no engLow/engHigh. An overview has to read `Cfg_EU`, `Cfg_PVEU` or `Cfg_SpdEU` as tags.

### Proposed member (none exists today)
Following the PCLib conventions (`types/UDT Standards.md:132-152`: `Cfg_` = configuration written by the Engineer; integer enums with the values listed in the comment) and the `Cfg_AnType` precedent:

- **`Cfg_MeasType : INT`, init `0`.** Comment: "Measured variable (ISA-5.1 first letter) for HMI grouping and trends: 0=Unset (derive from Cfg_Tag / EU) 1=Pressure (P) 2=Temperature (T) 3=Flow (F) 4=Level (L) 5=Weight (W) 6=Speed (S) 7=Current (I) 8=Power (J) 9=Position (Z) 10=Analysis (A) 11=Density (D) 12=Other".
  - 13 characters, so it passes `validate()` (32-character limit and reserved words, `gen_pclib.py:1153-1174`).
  - It is writable in Ignition because `Cfg` is in `IGN_WRITABLE` (`:1461`).
- **Where to add it:**
  - `T("AI", ...)` after `Cfg_EU` (`gen_pclib.py:281`).
  - `T("PID", ...)` after `Cfg_PVEU` (`:558`). There it describes the PV; SP follows the PV and CV is %.
  - `types/T_KPI/gen_pclib_T_KPI_block.py` after `Cfg_EU` (line 7).
  - T_Analyzer embeds `@AI` (`:905`), so `AI.Cfg_MeasType` = 10 works there with no further change.
  - The device types (T_CValve, T_Motor, T_VFD, T_Heater, T_Station) do not need it: their variables are fixed by type. Map them in the HMI by `tType` + member.
  - T_Station also needs `Cfg_PTEU STRING[8]` if its pressure is to be grouped and labelled correctly.
- **Regenerate:** re-running `gen_pclib.py` rewrites the xdd files, `export/PCLib_Ignition81.json`, `PCLib_Members.csv` and the README (`main`, `:1586-1616`). `gen_tex.py` then rewrites the appendix tables (`steward/standard-edits/rev-I-batch/appendices/data-types-future.tex`, T_AI at `:458`).
- **Controls Standard path** (decision 18, `steward/DECISIONS.md:24`): the standard text is never edited directly.
  1. A background Haiku doc-steward writes `steward/proposals/CS-REV-I-<topic>-instructions.md`, with the exact edits against the latest revision. The edits here are: add `Cfg_MeasType` to the T_AI, T_PID and T_KPI tables in Appendix `data-types-future`, plus one sentence in `hmi-dynamic-windows.tex` saying that the trends overview groups by it.
  2. It adds a row to `steward/DOC-QUEUE.md` (columns at `steward/skill-updates/controls-standard/references/change-queue.md:38-44`) with status `queued`.
  3. The row is compiled with the other queued rev-I rows into one batch at the end. Status runs `queued` -> `compiled` -> `applied`.
  4. Row 4 (dock) is still `queued` (`steward/DOC-QUEUE.md:10`), so the overview topic could also be folded into `CS-REV-I-dock-instructions.md`, with a date note in that row.
- **Fallback with no PLC change:** take the ISA-5.1 first letter of `Cfg_Tag` (P/T/F/L/W...). This works for T_AI, T_PID and T_KPI. It does **not** work for devices: FV-101 is a flow valve whose value is a position. For devices, use the tType mapping. Use the EU text as the last fallback.

## 2. Tag history

- **The UDT export and the generator do not enable history.** `gen_pclib.py` `_ign_atomic` (`:1480-1500`) emits only name, tagType, valueSource, opcServer, opcItemPath, documentation, tooltip, dataType, engUnit (TIME only) and readOnly. Its UDT parameters are only `OPCServer`, `PathPrefix` and `BaseTag` (`:1463-1467`). A repo-wide search for `historyEnabled|historyProvider|HatfieldDB|sampleMode` outside `archive/` and `build/` finds nothing. The demo UDTs (`tags/*`) are memory or expression tags with no history either.
- **The docs assume history.** `docs/pid-loop-templates.md:34`: "History: must be enabled on PV/SP/OUT for the B3 sparkline and the window's trend". `Trend.md:150` says the same for every pen. `docs/xsy-tag-import-strategy.md:40,168` treats history as a site-owned setting that the DDT-sync tool never touches.
- **To build it into the library:** add a `HIST` set in `gen_pclib.py`, for example `{T_AI: Val_PV; T_PID: Val_PV, Val_SP, Out_CV; T_CValve: Val_Pos, Val_Demand; T_Motor and T_VFD: Val_Current, Val_Spd; T_Heater: Val_Current, Val_Power; T_Station: Val_Net, Val_PT}`. `_ign_atomic` would then emit `historyEnabled: true`, `historyProvider` bound to a new UDT parameter `{HistProvider}` (added to `IGN_PARAMS`), and a sample mode or deadband. The exact property names belong to the Ignition API research.
- **`efc.ui.trend(base, pens, minutes, w, h)`** (`generator/docks/efc_ui.py:238-263`):
  1. It builds one `system.tag.queryTagHistory(paths=[base+'/'+m for m in pens], rangeMinutes, returnSize=200, aggregationMode='Average', returnFormat='Wide', ignoreBadQuality=True)` call.
  2. It finds one shared min/max over all pens, padded 10 % (at least 0.5).
  3. It returns `{'d': [svg path per pen], 'lo', 'hi'}`.
  4. On an exception it returns empty paths and logs a warning (`:247-249`).
  It sets no `historyProvider` or `tagProvider` argument.
- **The part** `Templates/Dynamic Window/Parts/Trend` (`generator/docks/build_docks.py:551-580`):
  - One SVG with a 360x100 viewBox and **3 fixed path elements**: `#1F1F1F`, `#1F4E99`, `#7F7F7F` (`:560-561`). The `custom.hist` default has 3 slots (`:556`).
  - It is re-run by `{view.custom.range} + toMillis(now(10000))*0`, so **every 10 s per instance** (`:557`).
  - Ranges are 24h/8h/1h/30m/5m, default 30 min (`:550`).
  - Params are `tagPath`, `pens` and `expanded` (inout). Hosts embed it with `trend(pens)` (`:200-206`), and the host's basis grows from 170 to 760 when expanded (decision 26).
- **Limits for reuse in a multi-pen overview** (from `Trend.md:166-172` and the code):
  - All pens hang off **one base** (`base + '/' + pen`) and share **one y-scale**. That is acceptable for one variable-type group with the same EU, but wrong for mixed units.
  - The part draws at most **3 pens**, has no legend and shows no units.
  - `returnSize=200` gives about one point every 7 min over 24 h.
  - The fixed 10 s poll is a load per instance.
  - Bad quality is dropped silently.
  - Pause/live (decision 26) and the legend in the TrendExpanded mockup (`steward/previews/Templates_DynamicWindow_Parts_TrendExpanded.html`) are not implemented.
- **Reuse path:** the function core is sound. Add a sibling `efc.ui.trendPaths(paths, minutes, w, h, lo=None, hi=None)` that takes **full tag paths** (devices sit under different parents and providers). One query per group, with N pens and an optional fixed scale from `Cfg_EUMin/Max`. For example, the Loop B4 inline script already uses `Cfg_PVMin/Max` as the scale (`generate_loops.py:400-410`). Then build a `Parts/TrendGroup` with N path elements, or one `queryTagHistory` for all groups in a single view-level binding, to cut the per-instance 10 s load.

## 3. Per-page state, and where a PV registry would hook in

- **Existing state:** `session.custom.efcDw` is a dict keyed `'%s|%s' % (page.props.pageId, page.props.path)` (`efc_ui.py:73-81`). The value is `{'default': {'path', 'params'}}`.
  - `_write` copies the dict, updates it and re-assigns it whole (`:84-89`).
  - `setDefaultDock(component, viewPath, params)` writes the default and calls `showDock` (`:162-169`). `closeDynamic` reads it back (`:172-179`).
  - `page.props.dimensions` is used only for dock sizing (`:101-123`).
  - Entries are never pruned.
  - `docs/improvements.md:12` (item 12) flags that values read back are property-tree wrappers and need conversion to plain Python.
- **Fit for a registry:**
  - Use a **separate `session.custom.efcPv`** with the same key function, rather than the `efcDw` dict. The reason: `_write` is a whole-dict read-modify-write, so 20-50 templates starting at the same time would race and lose entries. Keeping PVs out of `efcDw` also keeps the dock default from being clobbered.
  - Better still, make the value per key a dict keyed by `tagPath` (`{tagPath: {'tType':..., 'view': component.view.id}}`), so registration is idempotent.
  - The dock view runs on the same page and can compute the same `pageId|path` key, so the overview can bind to `session.custom.efcPv[key]`.
  - The race still exists with a separate property. Alternatives:
    - a page-scoped message: each template sends `system.perspective.sendMessage('efcPvReg', {...}, scope='page')` and the overview's message handler accumulates the entries in its own `view.custom`;
    - have the overview read the screen's template list once, after a short delay.
    Which of these works is for the Ignition API research.
- **What each template root would run:**
  - `onStartup`: `efc.ui.pvRegister(self)` reads `view.params.tagPath` and `tType`, and the key from `self.page.props`.
  - `onShutdown`: `efc.ui.pvUnregister(self)`.
  - Both go next to `openDynamic` in `efc_ui.py`, using `_p` (`:47-55`) and the BY_TYPE-style tType tables (`:25-29`).
- **Emit points today.** Every root has only `dom.onClick`; add `"system": {"onStartup": ..., "onShutdown": ...}` alongside it:
  - PV_StatusStrip: `build_pv.py:264`; PV_RangeBar: `build_pv.py:333`. Both are `root["events"] = {"dom": {"onClick": ...}}`.
  - AnalogIndicator A-D: `gen_analog_indicators.py:130` in `make_view`. One edit covers all four.
  - Loops B1-B4: `generate_loops.py:149` in `card_root(..., events={"dom": {"onClick": ev(OPEN_POPUP)}})`, using the `ev()` helper (`:57-58`).
  - Device templates (Valve_Control, motors, VFD, Heater): the root is a bare coord with **no events** (`build_pid.py:137-143`, `view()`), and the click sits on the symbol image (`:180`). Add the events in `view()` on the root, or in `dw_params` (`:172-174`), which every T_ template passes through.
  - Dock windows (`build_docks.py`): `comp(..., events=)` (`:21-26`), `on_click` and `on_action` (`:33-34`). They do not need to register.
  - Station_Tile and Station_Fill are Designer-built (`imported/`). They need an edit in the Designer and a re-import (`tools/import_project_zip.py`), or a post-import patch like `steward/tools/fix_station_styles.py` (decision 28).

## 4. ISA-101 style constraints

- **No chart, pen, sparkline or series classes exist** in EFC_Styles (`generator/build_styles.py`). The relevant ones are:
  - `Container/TrendPanel` (background `trend` #E0E0E0, dark left border, `:153`)
  - `Container/Inset` (#CFCFCF, used as the graph background, `:158`)
  - `Bar/Track` and `Bar/Fill` (#8C8C8C, `:282-283`)
  - `Button/Tab`, `Button/TabActive`, `Button/Small`, `Button/Icon` for the range buttons
  - `Text/Micro`, `Text/Subheader`, `Text/Units`, `Text/Caption`
  The palette keys are in `build_styles.py:16-45`. Decision 28 enforces classes only in generators, so pen strokes would go in SVG element props (as today) or need new `Trend/Pen/*` classes.
- **Palette rules** (`isa101-color-palette.md:11-16`):
  - Alarm colours are for alarms only; normal states are grayscale.
  - The saturated colours are the alarm priorities: #D50000, #FF7A00, #FFD200, #00A3E0, plus Diagnostic #7A7A7A.
  - The only non-gray, non-alarm colour is `editable`/`link` **#1F4E99**, used for setpoints.
- **There are effectively 3 series colours,** used the same way in two places:
  - The Trend part: pen 1 #1F1F1F `text`, pen 2 #1F4E99 `editable`, pen 3 #7F7F7F `borderDark` (`build_docks.py:561`).
  - Loop B3: PV #1F1F1F solid 1.5, SP #1F4E99 dashed "4 3" (`generate_loops.py`, B3 spark paths).
  - Implied convention: dark gray = measured value, blue = setpoint/operator value, mid gray = output.
- **No written "grey-first" rule** exists in the repo; a search for `grey-first`, `pen colour` and `series colour` finds nothing. An N-pen group chart has to tell pens apart within grays: #1F1F1F, #4D4D4D, #7F7F7F and #9E9E9E, plus dash patterns and direct labels, with blue kept for SP. That rule would be new and should be logged as a decision.
- **Controls Standard text:**
  - `hmi-dynamic-windows.tex:75-76`: trends show the last 30 min by default; every graph has an expand button; expanding keeps 400x860, the graph is about 400x760, ranges 5m/30m/1h/8h/24h, pause/live, collapse.
  - `:38`: close returns to "the screen's default view ... (normally the screen's trends)".
  - The dock instructions (`steward/proposals/CS-REV-I-dock-instructions.md:28,56,119`): "When the page loads, it shows the page's trends overview".
  - **Nothing in the standard or the proposals says what the overview contains.** That is still to be specified, so the grouping by variable type is new standard text.
  - Sizes: decision 25 gives 400x860 at 1080p, 37.04vh x 79.63vh (`DECISIONS.md:31`). Decision 26 gives the expanded graph about 400x760 inside the window (`:32`).
  - The `\tbd` collapsible-trends sentence is in the appendix at `perspective-screen-design.tex:33`: "If a collapsible-trends variant of the shell is added later, its main area becomes 1800 x 860". The dock proposal keeps it and marks it `\tbd` as probably obsolete now that the dock is always displayed (`CS-REV-I-dock-instructions.md:136`). The batch appendix `:6` and `:54` still describe the retired embedded-view and `efcDw[pageId]` region; queue row 4 replaces that text.
  - Conflict: `hmi-dynamic-windows.tex:51` and decision 6 still say "History: an 8 h state strip and the most recent events", while the code and decision 16 use a 30-minute pen trend.

## 5. Demo instances (known set for a prototype)

| Demo view | Instances | tType | EU / values | Expected group |
|---|---|---|---|---|
| `Templates/ProcessValues/_Demo` (`build_pv.py:337`, embeds both PV templates per row) | `[default]PV_Demo/PT001..PT005` (UDT `T_AI_Demo`, `tags/PV_Demo_Tags.json`) | T_AI | all `Cfg_EU = "PSIG"`, range 0-50 (`build_pv.py:396-397`); PV 28.2 / 37.6 / 44.1 / 3.2 / 28.2; PT005 has `Sts_Bad` | Pressure (5 pens: more than the 3-pen part) |
| `Templates/Loops/_Demo` (`generate_loops.py:556-570`, B1-B4 x 3 loops) | `[default]PID_Demo/TIC101, PIC205, FIC310` (`tags/PID_Loops/T_PID_Demo_Instances.json`, `generate_loops.py:624-627`) | T_PID | °F 0-200, PSIG 0-300, SCFM 0-500 | Temperature, Pressure, Flow (+ CV % group) |
| `Templates/_Demo` (`build_pid.py:318-336`, `:355-368`) | `[default]PID_Demo/` XV101-105 (T_DValve, discrete, ignore), **FV101, FV102** (T_CValve, Val_Demand/Val_Pos %), **P101, P102, K201, K202, B301, PV501** (T_Motor, no Val_Current in demo UDT), **M601** (T_VFD, `Cfg_SpdEU = "Hz"`, Val_Spd 45), **E401** (T_Heater, no analog in demo UDT) | mixed | `tags/T_*_Demo_UDT.json` hold memory stand-ins with only the members the templates bind | Position %, Speed Hz |
| `Templates/AnalogIndicator/_Examples` (`gen_analog_indicators.py:225-232`) | `[default]KPI/KPI_101` only, used 7 times | T_KPI | **no KPI demo tags exist in `tags/`** | none |
| `Templates/Station/_Demo` (imported) | `[default]Station_Demo/Station_1..4` | T_Station | `Cfg_EU = "kg"` (`tags/T_Station_Demo_UDT.json`); `Val_PT` has no EU | Weight, Pressure (EU unknown) |

**EU to variable-type test table** from the demos: PSIG -> Pressure; °F -> Temperature; SCFM -> Flow; Hz -> Speed; kg -> Weight; % -> Position/Output (T_CValve, PID CV). `Cfg_Tag` first letters also agree for T_AI and T_PID: PT001 -> P, TIC101 -> T, PIC205 -> P, FIC310 -> F. PV_Demo `Cfg_Tag` is `"{InstanceName}"` (`build_pv.py:394`). The device tags (FV-101, M-601) show why tType mapping is needed for devices.

**Demo caveats:**
- None of the demo tags has history, so a prototype stays blank on a gateway until history is turned on. The preview renderer also draws blank trends (`docs/template-review.md:8`).
- The device demo and the loop demo both use the `[default]PID_Demo` folder: `tags/PID_Demo_Instances.json` and `tags/PID_Loops/T_PID_Demo_Instances.json`.

## 6. Prior notes on a trends overview
- `steward/IDEAS.md`: the backlog is empty (header only).
- `docs/design-briefs.md` and `docs/template-review.md`: nothing about a trends overview or auto-built charts. The design briefs use "overview" only for the I/O rack and the Station screen.
- DECISIONS: decision 2 (each screen has a `defaultDock`; close reopens it), decision 6 (small history in docks), decision 16 (default range 30 min everywhere), decision 26 (expand inside the window), decision 32 (initial dock view = trends overview; the close-with-no-default case is open). No decision defines the overview's content.
- `docs/improvements.md:12-13` (P1 items 2-3): ship `Templates/Dynamic Window/TrendsOverview` plus a demo child project (a page config with `dw_Right`, `setDefaultDock` and the resize script). The overview is suggested as the library default for Close.
- `docs/improvements.md` item 4: put the `sizeDock` change script on the window and trends-overview views themselves.
- `docs/library-reference.md:99,107`, `CHANGELOG.md:7` and `docs/screen-layout-standard.md:13` all name "the page's trends overview" as the initial dock view and the `setDefaultDock` target, without saying what it contains.
