# Trends overview: can a script build the screen's chart automatically?

Evaluation, 2026-10-24. Question: when a screen loads, can an Ignition script find every process value shown on it and build a chart of them, grouped by variable type, to be the default view of the `dw_Right` dock (decision 32)? Scope agreed: process-value templates only (`PV_StatusStrip`, `PV_RangeBar`, `AnalogIndicator/*`, and the legacy `DDT_Process_Value` templates on the fork); variable type inferred from the engineering unit; no setup on the screen; one small chart per type, stacked.

Sources: Ignition docs and forum research (`page-scan-research` report), and a read of this library (`trends-overview-repo` report). Nothing has been run on a gateway.

## Verdict

**Feasible, but not as a scan.** Perspective gives a script no supported way to list the template instances on a page: component traversal "is limited to a single view". A screen script sees its embedded-view components but nothing inside them; a template cannot see its parent; the dock view sees only `page.props`. The only true page scan uses internal SDK classes, which is unsupported and may break in 8.3.

**What works instead: the templates announce themselves.** Each process-value template registers its tag with the page when it starts and removes it when it stops. The overview reads that registry. This works through nested views and flex repeaters, and the screen builder does nothing beyond adding the `dw_Right` dock. Estimated effort: about a week to a working prototype, plus a gateway test pass.

## Recommended design

1. **Registration.** The PV template roots get `onStartup` / `onShutdown` events and a change script on `params.tagPath`, all calling `efc.pv.register(self)` / `unregister(self)`. The generators have the hook points (`generator/build_pv.py` lines 264 and 333, `gen_analog_indicators.py` `make_view`). Each entry carries `tagPath`, `tType`, `Cfg_EU`, `Cfg_Tag`, the page path and the mount path.
   - The change script matters: Perspective reuses a view when only its params change, so `onStartup` does not fire again.
   - Templates inside dock windows and popups must be excluded, or a valve window's own PV would join the chart. A `census` view param (default on; the windows set it off) is the simplest switch.
2. **Registry.** Not `session.custom`: template scripts run in parallel and a read-modify-write of a session list drops entries (the same pattern `efc.ui._write` uses, at lower load). Use a Java `ConcurrentHashMap` in `system.util.getGlobals()`, keyed `sessionId|pageId`, with the page path stored on each entry (pageId survives `navigate()`). Purge in the Session Shutdown event and prune page ids no longer in `getSessionInfo()`, because closing a browser tab does not shut views down until the session times out.
3. **Overview view** `Templates/Dynamic Window/TrendsOverview`, set by each screen's `efc.ui.setDefaultDock`. It reads the registry on its own startup, on an `efc.pvChanged` page message (a hint, not the state) and on a slow poll, and rebuilds its charts only when the set of tags changed, so a zoomed chart is not reset every few seconds.
4. **Chart.** One Perspective Power Chart written from script: one plot per variable type (own axis, pens with that type's EU), tag browser and pen table hidden, plots stacked. At 400 × 860 that is 5 or 6 plots of up to about 8 pens. Pens, axes and plots are written by script, not bound. Fallback for denser screens: the existing `efc.ui.trend` SVG approach, one row per value.
5. **Grouping.** Normalised EU → type table (first match wins; unknown → "Other"):

   | Type | Units |
   |---|---|
   | Pressure | psi, psig, psia, bar, barg, mbar, kPa, MPa, Pa, inHg, mmHg, torr, atm |
   | Differential pressure | psid, inH2O / inWC, mmH2O, kPad, mbard |
   | Temperature | °F, °C, F, C, K |
   | Flow | gpm, gph, l/min, lpm, l/s, l/h, m3/h, cfm, scfm, acfm, Nm3/h, kg/h, t/h, lb/h |
   | Analysis | pH, µS/cm, mS/cm, NTU, ppm, ppb, mg/l, %O2, %LEL, mV |
   | Speed | rpm, Hz |
   | Electrical | A, mA, V, kW, MW, hp, kVA |
   | Weight | kg, t, lb |
   | Volume | m3, l, gal, bbl (no time unit) |
   | Vibration | mm/s, in/s, g, mils |

   Ambiguous units: `%` (level, position, output, concentration), `m`/`ft`/`in` (level or distance), `inH2O` (level or DP), `bar`/`kPa` without a g/a/d suffix, and an empty EU. `Cfg_EU` is a 12-character string, so truncation happens. Recommended tie-break order: a per-instance override (a custom tag property `varType` on `Val_PV` in the Ignition UDT, no PLC change), then the ISA first letter of `Cfg_Tag` (P, T, F, L, A, W; watch PD, FQ), then the EU table.

## Prerequisites and risks

| | Finding | Consequence |
|---|---|---|
| **Tag history is enabled nowhere.** | `gen_pclib.py` and the UDT export set no `historyEnabled`, provider or deadband on `Val_PV`; the demo tags have none. | Every chart stays blank until history is configured. Decide where it is turned on (UDT vs instance), which historian, and the deadband. The Power Chart also needs a Tag Historian licence. |
| **Startup/shutdown reliability** | `onShutdown` on a removed repeater instance, and startup order between the main view and the dock, are not documented. | Verify on 8.1.22; the design tolerates both because the registry is the state and the dock polls. |
| **Dock persistence across `navigate()`** | Unknown whether `dw_Right` keeps its altered view after navigation. | Same open item as P1-1 in `docs/improvements.md`; the overview refreshes on `page.props.path` either way. |
| **`T_KPI` is not in the PCLib export** | The AnalogIndicator templates bind a type that exists only as a proposal. | Needs the `T_KPI` merge (improvements item 10) before KPI values can register. |
| **Legacy templates** | On the `DDT_` fork the value is `DDT_Process_Value.PV` and the EU member differs. | `efc.pv.register` takes the member names from a per-type table, so the fork adds one row. |
| **8.3** | Power Chart pen source paths use the 8.1 `drv:` form, which 8.3 still accepts; `getGlobals` and page messages are unchanged. | Low risk; include in the 8.3 trial pass. |

## Verify on a gateway before building the full thing

1. `onStartup` / `onShutdown` fire for a template inside a nested embedded view and inside a flex repeater, including when the instance is removed.
2. A Power Chart accepts pens, axes and plots written from a script, with plain tag paths converted to history paths.
3. Two templates registering at the same instant both appear (the `ConcurrentHashMap` path).
4. The overview does not reset zoom when the registry is re-read with no change.

## Decisions needed

1. Who enables history, where, and with what deadband; which historian; confirm the Tag Historian licence.
2. Confirm "Other" as the bucket for unknown or ambiguous units, and the tie-break order above.
3. Maximum plots and pens per chart, and whether operators can pin or drop pens.
4. Default range (decision 16 says 30 min) and whether the chart is live only.
5. Whether a screen may also pass an area tag path so an empty registry falls back to browsing that area's `T_AI` instances.

## Not recommended

- **Static walk of `view.json` on the gateway.** Possible for literal params, but 18 of the library's 71 embedded views have bound params and 14 are repeaters, so the pen list would be wrong on exactly the screens that matter. Useful only as a build-time lint.
- **Message census alone.** Page-scope `sendMessage` is asynchronous and unacknowledged; templates that mount late miss it. Kept only as a "re-announce" request.
- **Internal SDK page scan.** Works today, unsupported, likely to break on upgrade.
