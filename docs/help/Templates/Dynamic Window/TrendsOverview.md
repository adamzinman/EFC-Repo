# Templates/Dynamic Window/TrendsOverview

**Purpose.** The default view of the `dw_Right` dock (decisions 32, 35): a chart of every process value shown on the current screen, grouped by variable type, so an operator sees the screen's pressures, temperatures and flows without picking pens.

## What it shows
- Header: `TRENDS`, a count line (`3 values on screen, 30 min`) and range buttons 24 h / 8 h / 1 h / 30 m / 5 m (`efc.pv.setRange`).
- One Power Chart (`Chart`), realtime, tag browser and pen table hidden. `efc.pv.refresh` writes its `plots`, `axes` and `pens`: one plot per variable type in `efc.pv.VAR_TYPES` order, each with a left axis labelled with the group's unit; up to 6 plots and 8 pens per plot (extra pens are counted in `view.custom.groups[].dropped`).
- Pens: the value (`Val_PV`) of every registered template, plus the setpoint (`Val_SP`, dashed blue) for loops. Colours follow `efc.pv.PEN_STYLES` (ISA-101 greys first, the setpoint blue, then dashes).
- With nothing registered the chart is hidden and the caption reads `No process values on this screen`.

## How it knows what is on the screen
Perspective cannot list a page's templates from one place, so the process-value templates register themselves (`efc.pv`): `PV_StatusStrip`, `PV_RangeBar` and `AnalogIndicator/A..D` call `efc.pv.register(self)` in their root `onStartup`, `efc.pv.unregister(self)` in `onShutdown` and `efc.pv.rebind(self, previousValue, currentValue)` from a change script on `params.tagPath` (a reused view gets new params without restarting). A template with `params.census` = false (inside a dynamic window or popup) does not register.

The registry is a gateway-memory map (`system.util.getGlobals()['efc.pv.registry']`), one `ConcurrentHashMap` per `<sessionId>|<pageId>`; each entry stores the tag path, type, unit, tag name, description and the screen path, so a window open in another screen of the same tab is not listed. After every change the template sends the page message `efc.pvChanged`; the overview also re-reads on its own startup and every 5 s (`custom.tick`) and rebuilds the chart only when the set of values changed (`custom.sig`).

## Variable type
`efc.pv.var_type(eu, tag)`: the engineering unit, normalised (`°F` → `degf`, spaces removed), is looked up in `VAR_TYPES` (pressure, differential pressure, temperature, flow, level, analysis, speed, electrical, weight, volume, vibration, percent, length, other). For `%`, lengths and a missing unit the ISA letter of `Cfg_Tag` decides (P, T, F, L, A, S, I/E/J, W, V, Z); anything else is `Other`.

## Project setup
- Each screen's root `onStartup`: `efc.ui.setDefaultDock(self, 'Templates/Dynamic Window/TrendsOverview')`.
- Gateway Events > Perspective > Session Shutdown: `efc.pv.purgeSession(session.props.id)` (a closed tab does not shut its views down until the session ends).
- Tag history on the values (decision 34, `HistProvider`) and a Tag Historian licence.

## Session and page values
- `view.custom.sig`, `count`, `groups`, `range`; root `custom.tick` (poll), root `custom.vh` (bound to `page.props.dimensions.viewport.height`, change script `efc.ui.sizeDock(self)`).
- No session values; the registry is gateway memory.

## Verify on a gateway
Power Chart accepts pens / axes / plots written from script with plain tag paths; `onShutdown` fires for a template removed from a flex repeater; two templates starting at the same instant both appear; the chart keeps its zoom when the registry is re-read without change.
