# Page census of process-value templates: chart in `dw_Right` grouped by variable type

Target: Perspective 8.1.22+ (Jython 2.7), 8.3-compatible. Read-only research; repo facts were taken from `/home/user/EFC-Repo` at commit 21008a6.

## TL;DR

- **No supported API lets one script list the template instances on a page.** Component traversal stops at the view boundary. The docs say ["Object Traversal is limited to a single view … message handling should be utilized instead"](https://docs.inductiveautomation.com/docs/8.1/ignition-modules/perspective/scripting-in-perspective/perspective-component-methods).
- **Recommended: self-registration (C) into a gateway-memory registry, with a message used only to say "something changed".** Each PV template registers itself on startup, re-registers when its `tagPath` changes, and unregisters on shutdown. The dock reads the registry, resolves EU and ISA tag in one `readBlocking`, and builds a Power Chart. The chart has one plot per (variable type, EU), a shared time axis, and its tag browser and pen table hidden.
- **Use the tag-side approach (E) as the fallback or cross-check, not as the source.** It shows what is in an area folder, not what is on the screen.
- **Static view.json walking (B) is not viable as the source.** In the library views, 18 of 71 embedded views have bound params, and there are 14 flex repeaters (repo count). Neither can be resolved without running the bindings.

## Repo facts that shape the design

- The templates already expose `params.tagPath` and `params.tType` (PV_StatusStrip: `tType` defaults to `T_AI`; A_RangeBar: `T_KPI`). PV_StatusStrip already binds `custom.units` to `{tagPath}/Cfg_EU` (indirect tag binding).
- None of the library views has a message handler today. Root events are `dom` only.
- `T_AI` has `Cfg_Tag` ("Equipment / instrument tag, e.g. FT-101") and `Cfg_EU` (STRING[12]). It has **no variable-type member**: see `types/PCLib_Members.csv`.
- In `types/export/PCLib_Ignition81.json`, **`Val_PV` has no `historyEnabled`**. Trending in the dock therefore depends on history being turned on in the UDT or on the instances. See the open questions.
- Existing building blocks:
  - `efc.ui.setDefaultDock(component, viewPath, params)` stores the default under `session.custom.efcDw['<pageId>|<page path>']`. It already notes that `pageId` survives `navigate()`.
  - `efc.ui.trend()` draws SVG paths from `system.tag.queryTagHistory`. Both are in `projects/EFC_Library/ignition/script-python/efc/ui/code.py`.

---

## A. Runtime component-tree walk: works with limits (one view only)

**What the API offers.** `getChildren()`, `getChild(name|'a/b')`, `getSibling()`, `.parent`, `.view`, `.page`, `.session`, `view.rootContainer` and `view.id` have been available since Perspective 8.0 and are documented for 8.1 and 8.3 ([8.1](https://docs.inductiveautomation.com/docs/8.1/ignition-modules/perspective/scripting-in-perspective/perspective-component-methods), [8.3](https://docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/scripting-in-perspective/perspective-component-methods)). "Root containers will return the view, and views/sessions will return None" for `.parent`.

**What crosses a view boundary and what does not:**

| From | Can reach | Cannot reach |
|---|---|---|
| Script in the screen (primary view) | The `ia.display.view` and flex-repeater **components** in its own tree. That includes their `props.path`, `props.params` (runtime values, bindings already evaluated) and `props.instances`. This gives a **one-level** census. | Any component **inside** an embedded view or repeater instance. In the forum, Cody Mallonee says "Embedding components only render Views - they don't actually contain ANY components" and Paul Griffith (IA) says to use page/session messages instead ([thread 38138](https://forum.inductiveautomation.com/t/how-to-access-to-components-within-an-embedded-view-from-script/38138)). |
| Script inside a template | Its own view (`self.view.params`, `self.view.id`) | Its embedding parent: `.parent` of the root is the view, and the view's parent is `None`. A view only sees the params it is given ([forum](https://forum.inductiveautomation.com/t/component-method-scripting/74053)). |
| Script in the dock view | `self.page.props`: `pageId`, `path` (URL), **`primaryView`** (path of the main view), `dimensions` (8.1.6) ([Pages in Perspective](https://docs.inductiveautomation.com/docs/8.1/ignition-modules/perspective/pages-in-perspective)) | Any component of the main view. `page.props` carries no view tree. |
| `system.perspective.getSessionInfo()` | Per session: `pageIds`, `activePages`, user, project ([doc](https://docs.inductiveautomation.com/docs/8.1/appendix/scripting-functions/system-perspective/system-perspective-getSessionInfo)) | Page paths, views and components |

**Unsupported escape hatch (SDK).**
- The SDK interface `Page` has `List<ViewModel> getViews()` ([8.1.24 javadoc](https://sdk.inductiveautomation.com/javadoc/ignition81/8.1.24/com/inductiveautomation/perspective/gateway/api/Page.html)). That list holds **every** view instance on the page: nested embedded views, repeater instances, docks and popups.
- `ViewModel.getId()` returns a `ViewInstanceId` with `resourcePath` (the view path) and `mountPath` (where it sits in the DOM) ([javadoc](https://sdk.inductiveautomation.com/javadoc/ignition81/8.1.26/com/inductiveautomation/perspective/gateway/api/ViewInstanceId.html)). `getPropertyTreeOf(PropertyType)` gives the params ([ViewModel](https://sdk.inductiveautomation.com/javadoc/ignition81/8.1.26/com/inductiveautomation/perspective/gateway/model/ViewModel.html)).
- Reaching it takes `IgnitionGateway` → module manager `resolveClass('…perspective.gateway.api.PerspectiveContext')` → `getSessionMonitor()` → sessions → `getPages()` → `getViews()` ([forum 74585](https://forum.inductiveautomation.com/t/get-perspective-session-page-info-from-pageids/74585); one poster hit an import error on 8.1.22).
- This is the only true "scan". It is internal API, unsupported, and may change in 8.3 (new SDK). **Not recommended** for a library standard. It is fine as a diagnostic or test oracle.

**Failure modes of a tree walk:**
- Only one level deep.
- Breaks when the layout is restructured.
- Scripting does not document a component-type attribute, so you must detect embedded views by duck-typing `props.path`.

## B. Design-time / resource introspection: works with limits; not a reliable source

**Available functions:**
- `system.perspective.getProjectInfo()` was **new in 8.1.4** and runs in Perspective Session scope. It returns `views` (path only) and `pageConfigs` (`url`, `primaryView`), with **no view content** ([doc](https://docs.inductiveautomation.com/docs/8.1/appendix/scripting-functions/system-perspective/system-perspective-getProjectInfo)). It is not needed to find the main view, because `page.props.primaryView` already gives it.
- `system.util.getProjectName()` and `system.project.getProjectNames()` return names only. No documented `system.*` function returns resource content.

**Reading view.json, two routes:**
1. **File system:** `<install>/data/projects/<project>/com.inductiveautomation.perspective/views/<path>/view.json`, next to `resource.json` ([8.3 resource.json](https://docs.inductiveautomation.com/docs/8.3/appendix/reference-pages/resource-json-file); 8.3 layout per [forum 110717](https://forum.inductiveautomation.com/t/ignition-internal-folder-structure/110717), not stated in an official doc).
   - A child project folder holds only its own and overridden resources. Inherited views live in the parent's folder. Walk `project.json` → `parent` and take the first folder that has the view (an override replaces the whole resource; there is no merge).
   - The disk copy is the saved state, and reading it costs disk I/O. Paul Griffith (IA): "at least avoid the insane performance hit of calling into the local filesystem each time."
2. **In-memory project:** `getProject().getResource(ResourcePath(ResourceType('com.inductiveautomation.perspective','views'), path)).get().getData('view.json')` ([forum 84882](https://forum.inductiveautomation.com/t/access-a-views-child-components-using-viewpath/84882)). This is an internal API. Its 8.3 resource API differs ([8.3 SDK resource collections](https://www.sdk-docs.inductiveautomation.com/docs/8.3/programming-for-the-gateway/storing-data-using-resource-collections/)).

**Static walk limits:**
- You can resolve literal `params.tagPath` values and pure `{view.params.x}` property bindings, by substitution down the chain from the primary view.
- The primary view's own params come from the URL (`page.props.path` and the page-config pattern), which you would also have to parse.
- You **cannot** resolve:
  - expression, tag, query or script-transform bindings (an evaluator would be needed);
  - `props.path` bound on embedded views;
  - repeater `instances` built by bindings or scripts (typical: a tag browse or a named query);
  - `visible` conditions;
  - tab containers whose tabs load only when activated (`runWhileHidden`, 8.1.5, [Tab Container](https://docs.inductiveautomation.com/docs/8.1/appendix/components/perspective-components/perspective-container-palette/perspective-tab-container)).
- In the EFC library itself, 18 of 71 embedded views have bound params and there are 14 repeaters.

**Verdict:** good for lint and design-time inventory (which screens can show which template types), but **not** for the runtime pen list.

## C. Self-registration: works (recommended) once the concurrency and lifecycle details are handled

**Events.**
- `onStartup` "occur[s] when the View or component is loaded into the Session". `onShutdown` occurs "when the View or component is removed from the Session. Typically … navigate away … or if the Session times out" ([8.3 Component Events](https://docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/working-with-perspective-components/component-events-and-actions)).
- They map to React mount/unmount ([8.1 Event Types Reference](https://docs.inductiveautomation.com/docs/8.1/appendix/reference-pages/perspective-event-types-reference)). Embedded views and repeater instances are views in their own right, so their root events fire when that instance mounts or unmounts.
- A repeater instance that is removed unmounts, so `onShutdown` fires. Verify this on the target build.

**Pitfalls:**
1. **Params change without a restart.** An embedded view or repeater instance that gets new params is reused, so `onStartup` does **not** fire again. pturmel calls this "Expected behavior of the onStartup event" and recommends a change script on the param ([forum 75649](https://forum.inductiveautomation.com/t/embedded-view-onstartup-script-does-consistently-run-on-page-open/75649)). The same reuse applies to repeaters ([forum 115337](https://forum.inductiveautomation.com/t/flex-repeater-instance-parameter-refresh-issues/115337)). **Re-register from a change script on `view.params.tagPath`.**
2. **Closing a tab does not shut views down promptly.** "Closing the browser tab with the Session will not immediately close the Session; the Session must first time out" ([session events](https://docs.inductiveautomation.com/docs/8.1/ignition-modules/perspective/scripting-in-perspective/perspective-session-events-scripts.md)). Key entries by `sessionId|pageId`, purge a session in the Session **Shutdown** event, and prune `pageId`s that are no longer in `getSessionInfo()['pageIds']`.
3. **`pageId` survives `navigate()`.** `efc_ui.py` already relies on this. Old templates unregister on shutdown, but store `page.props.path` in each entry and filter on it anyway.
   - If the dock view persists across navigation (same dock id), its `onStartup` does not fire again. Drive the dock's refresh from `page.props.path` as well as from the change signal.
4. **Templates hosted in the dock or in popups belong to the same page** and would register too.
   - Exclude them with a `census` view param (default `True`; the dynamic windows and popups pass `False`).
   - Or exclude by `mountPath`: `self.view.id` is `resourcePath@mountPath` ([IGN-6563 thread](https://forum.inductiveautomation.com/t/ign-6563-how-to-get-view-name-inside-the-view-itself/63819)). The prefix that identifies dock views has to be confirmed on a running gateway.
5. **Concurrency.**
   - Component scripts run on the Perspective worker pool, which "will create threads as needed" ([forum 43708](https://forum.inductiveautomation.com/t/perspective-trying-to-reduce-thread-count-per-session/43708)). Fifty to a hundred `onStartup` scripts run in parallel.
   - The pattern `l = list(session.custom.pvOnPage[pid]); l.append(x); session.custom.pvOnPage[pid] = l` is a read-modify-write and **will lose entries**. The same risk exists in today's `efc.ui._write`, at lower contention.
   - Session custom props are also synchronized to the browser, so every write costs bandwidth.
   - **Use a gateway-memory registry instead**: a Java `ConcurrentHashMap` kept in `system.util.getGlobals()`. That function is new in 8.1.0 and "persists across the lifetime of the JVM" ([doc](https://docs.inductiveautomation.com/docs/8.1/appendix/scripting-functions/system-util/system-util-getGlobals)). Unlike a module-level variable in a project library, it survives project-script reloads on designer save.
   - Store only Java maps and plain str/dict values, never Python classes defined in a library script (they would pin old classloaders).
6. **Startup order between the main view and the dock is undefined**, and so are the `loading.order` interactions (8.1.5, [Embedded View](https://docs.inductiveautomation.com/docs/8.3/appendix/components/perspective-components/perspective-embedding-palette/perspective-embedded-view), [Flex Repeater](https://docs.inductiveautomation.com/docs/8.1/appendix/components/perspective-components/perspective-embedding-palette/perspective-flex-repeater)).
   - A message sent before the dock's handler exists is lost: the view must be loaded to hear it ([forum 38138](https://forum.inductiveautomation.com/t/how-to-access-to-components-within-an-embedded-view-from-script/38138)).
   - Because the registry is durable state and the message is only a hint, ordering does not matter. The dock reads on its own startup, on each `efc.pvChanged`, and on a slow safety poll (`now(5000)`).
7. **Cost with 100 templates:** 100 in-memory `put`s plus 100 page-scope messages. Each message only bumps `view.custom.rev` on the dock, and the dock's rebuild is debounced. That is negligible next to the templates' own tag bindings (PV_StatusStrip has 40 custom properties).

## D. Message census: works with limits; it collapses into C

- `sendMessage(type, payload, scope='page')` reaches handlers in all views on the page, including embedded views, repeater instances and docks. Handlers "execute asynchronously to the calling script". There is no return value, no queue and no acknowledgement ([doc](https://docs.inductiveautomation.com/docs/8.1/appendix/scripting-functions/system-perspective/system-perspective-sendMessage)).
- A census only reaches templates that are mounted when it is sent. Late templates (repeater re-population, `after-parent` loading, tabs that load on activation, an instance added later) are missed unless they announce themselves, and announcing is pattern C.
- The replies are N concurrent messages into the dock, so the dock handler has the same read-modify-write problem.
- It would still need a "done" condition, which does not exist.
- **Use it only as a "re-announce" request** (dock to templates: "send your entry again"), for example after the registry was flushed by a gateway restart while sessions reconnected.

## E. Tag-side derivation: works; answers a different question

- `system.tag.browse(areaPath, {'tagType':'UdtInstance','typeId':'T_AI','recursive':True})`. `recursive` is new in 8.1.2 ([doc](https://docs.inductiveautomation.com/docs/8.1/appendix/scripting-functions/system-tag/system-tag-browse)). Repeat per `typeId` (T_AI, T_KPI, loop and device types).
- **It needs a screen-to-folder mapping.** The dock cannot read the main view's params, so the mapping has to come from one of:
  - `page.props.primaryView` or `page.props.path` mapped to a folder by convention (for example `Screens/Area1/Overview` → `[default]Area1`);
  - a lookup dict;
  - the area passed to `setDefaultDock(..., params={'area': ...})` (the simplest).
- Pros: deterministic, independent of UI lifecycle, and available before the main view has finished loading.
- Cons:
  - Shows tags that are not on the screen and misses tags shown from other areas.
  - Recursive browses of large folders on every page load are costly; cache by folder.
  - The folder structure becomes a contract.
- Best use: a fallback when the registry is empty, or an "area trends" mode.

## F. Charting in a 400 × 860 column

| Component | Fit | Notes |
|---|---|---|
| **Power Chart** (new in 8.1.0) | **Best** | Covered in detail below. |
| Time Series Chart | OK | `series[].data` takes a dataset with the time column first. `plots[]`, `axes` and `trends[].columns[].key` must all be built in step with the series ([doc](https://docs.inductiveautomation.com/docs/8.1/appendix/components/perspective-components/perspective-chart-palette/perspective-time-series-chart)). It needs more structure to build dynamically. **Plot `relativeWeight` is new in 8.1.23**, above the 8.1.22 floor. |
| Sparkline / existing `Parts/Trend` SVG | Good for a list | One small trend per tag inside a repeater: dense and cheap with one `queryTagHistory` per group (`efc.ui.trend`). No axes or interaction. |
| XY Chart | Poor | Its data is a dataset or array. It has no history source of its own, and it is heavy in a narrow column. |

**Power Chart details:**
- `pens[]` have `axis` (an axis name) and `plot` (a numeric index). `axes[]` have `position` left/right, `range.auto` and a label. `plots[]` are rows with `relativeWeight` and markers ([8.1 doc](https://docs.inductiveautomation.com/docs/8.1/appendix/components/perspective-components/perspective-chart-palette/perspective-power-chart), [8.3 doc](https://docs.inductiveautomation.com/docs/8.3/appendix/components/perspective-components/perspective-chart-palette/perspective-power-chart)).
- 8.1.x additions: 8.1.14 converts non-historical tag paths to historical format; 8.1.16 adds Y auto-range constrained to the pens; 8.1.22 auto-scales the X axis when `tickCount = 0`.
- `config.visibility` hides the tag browser, date range selector and pen table, which a 400 px column needs.
- It requires a Tag Historian license.

**Recommended layout:**
- **One Power Chart with one plot per (type, EU) and a single left axis per plot.** It reads as stacked small multiples that share one time cursor (`xTrace`).
- In 400 px, each Y axis costs roughly 40 to 60 px, so do not put several axes on one plot. If one type has several EUs (psi and inH2O), give each its own plot.
- In 860 px, plan on at most 5 or 6 plots. Above about 8 pens per plot, show the top N (alarm priority first, then order of appearance) with a pen-picker.

**Dynamic pens:**
- `props.pens`, `axes` and `plots` are ordinary properties, so a script can write them.
- **Write them from script (the dock's rebuild), not through a binding.** The chart writes back to `pens` (visibility toggles, the 8.1.14 path conversion "write[s] the converted path back"), which would fight a binding.
- Start each pen, axis and plot from a dict copied out of a designer-made chart, then override `name`, `axis`, `plot` and `data.source`. Do not hand-type the full schema.

**Source path:**
- Build `histprov:<Historian>:/drv:<gateway>:<provider>:/tag:<path>`. 8.3 docs: "any `drv` syntax used in Ignition 8.1 will still work in 8.3". The new 8.3 form is `histprov:X:/sys:gw:/prov:P:/tag:...`.
- Do not rely on plain-path conversion for pens written by script; test it.

**Tag History binding with a dynamic path list:**
- This is supported. Expression mode points at a custom array property of `{path, alias, aggregate?}` objects ([Tag History bindings](https://docs.inductiveautomation.com/docs/8.1/ignition-modules/perspective/working-with-perspective-components/bindings-in-perspective/tag-history-bindings-in-perspective)). It offers "Cache & Share" (8.1.12).
- That is the right pattern for the Time Series Chart.
- For sparklines, a script transform with `system.tag.queryTagHistory(paths=[...], returnSize=~200, aggregationMode='MinMax')` gives full control. Use one call per group, not one per pen.

**8.3 notes:**
- Power Chart: the historian path syntax note above, numeric locale formatting in X-trace and the pen table, and no deprecations listed.
- The 8.3 historian is reworked. Keep the historian name and provider in one config constant.

## G. Variable-type grouping

Use this precedence and stop at the first hit:

1. **Explicit override.** Add a custom tag property such as `varType` on `Val_PV` in the Ignition UDT definition. Ignition supports custom tag properties, so the PLC DDT does not change. Alternatively add a `Cfg_VarType` UDT member, a PLC change that must be synced to PCLib, the DDT and the Standard.
2. **ISA first letter of `Cfg_Tag`,** with the modifier taken into account: `PD*` or `PDI*` = differential pressure, `FQ*` = totalizer, `TD*` = differential temperature. The letter map:

   | Letter | Type |
   |---|---|
   | P | pressure |
   | T | temperature |
   | F | flow |
   | L | level |
   | A | analysis (subtype from EU) |
   | D | density |
   | S | speed |
   | W | weight |
   | J | power |
   | I | current |
   | E | voltage |
   | Z | position |
   | V | vibration |
   | M | moisture / humidity |
   | K | time |
   | C, G, N, O, X | user-defined: map per site |

   Failure modes: tags not in ISA form (`TK-101` is a tank, not a temperature), `U` (multivariable) and `Y`/`H` (not analog).
3. **EU inference**, after normalizing (`lower()`, strip spaces and dots, `°`/`deg` → `deg`, `³` → `3`, `²` → `2`):

| Type | EU tokens |
|---|---|
| pressure | psi, psig, psia, bar, barg, bara, mbar, kpa, mpa, pa, kg/cm2, inhg, mmhg, torr, atm |
| diff. pressure | psid, inh2o / inwc / "wc, mmh2o / mmwc, kpad, mbard |
| temperature | degf, degc, f, c, k |
| flow (vol.) | gpm, gph, mgd, l/s, l/min, lpm, l/h, m3/h, m3/s, m3/d, cfm, scfm, acfm, nm3/h, sm3/h, ft3/min, bbl/d |
| flow (mass) | kg/h, kg/s, t/h, lb/h, lb/min, pph |
| level | (none unique: see ambiguous) |
| analysis | ph, ms/cm, us/cm, µs/cm, ntu, ppm, ppb, mg/l, %o2, %lel, orp/mv |
| speed | rpm, hz |
| current / power / voltage | a, ma, kw, mw, hp, kva, v, kv |
| weight | kg, t, lb, ton |
| volume | m3, l, gal, bbl, ft3 (no time unit: a totalizer or tank volume) |
| vibration | mm/s, in/s, ips, g, mils |
| position | %open, deg (on a valve or damper) |

**Ambiguous EUs.** Fall back to the ISA letter for these, and show them under "Other" if that also fails:

- `%`: level, valve position, speed, humidity, concentration, controller output.
- `m`, `ft`, `in`, `mm`, `cm`: level, distance or position.
- `inH2O` / `mmH2O`: pressure, differential pressure, hydrostatic level or DP flow (with `Cfg_SqrtExtract` = DP flow).
- `bar`, `kPa`, `mbar`: gauge, absolute, differential or vacuum.
- `F` / `C` single letters: Farad and Coulomb are unlikely in practice, but `C` collides with conductivity in user-letter plants.
- `K`: kelvin or thousand.
- `Hz`: speed or frequency.
- `deg`: temperature or angle.
- `t`: tonne or time.
- `m3`: volume, or a mis-typed flow `m3/h`.
- `ppm`: analysis of different species.
- `mA`: a raw signal, not a process variable.
- An empty or `---` EU.
- `Cfg_EU` is STRING[12]. Expect truncation and free text such as `"PSI G"` or `"GPM*1000"`.

---

## Recommended architecture

1. **Templates.** In PV_StatusStrip, PV_RangeBar, AnalogIndicator/*, the Loop cards and the device templates that carry an analog value:
   - root `onStartup` → `efc.pvreg.register(self, members)`;
   - root `onShutdown` → `efc.pvreg.unregister(self)`;
   - a change script on `view.params.tagPath` → `register` again.

   `members` lists the historized analog members per `tType`, for example T_AI → `Val_PV`, loop → `PV`/`SP`/`CV` with SP/CV opt-in, VFD → speed and current. Add a `census` view param (default `True`) so that dock and popup copies opt out.
2. **Registry.** `efc.pvreg` holds a `ConcurrentHashMap` in `system.util.getGlobals()`, keyed `sessionId|pageId` → `{view.id: entry}`. Each change also sends `efc.pvChanged` (page scope) and bumps a per-page revision.
3. **Dock view** (`setDefaultDock(self, 'EFC/Docks/PVTrends', {'area': …})` from the screen's onStartup):
   - message handler `efc.pvChanged` → `self.view.custom.rev = now`;
   - `custom.census` binding on (`rev`, `page.props.path`, `now(5000)`) → `efc.pvreg.census(self)`;
   - a change script on `custom.census` writes the Power Chart's `pens`, `axes` and `plots`, only when the set of tag paths actually changed (compare a hash), so the user's zoom and toggles are not reset every 5 s.
4. **Fallback.** If the census is empty after the first 5 s poll and an `area` param exists, use the tag browse (E).
5. **Lifecycle.** The Session Shutdown event calls `efc.pvreg.purgeSession(session.props.id)`. `census()` drops `pageId`s that are not in `getSessionInfo()`, at most once a minute.

```python
# project library: efc/pvreg  (Jython 2.7, gateway scope)
from java.util.concurrent import ConcurrentHashMap
from java.lang import System

_KEY = 'efc.pvreg.v1'
HIST = {'histprov': 'Historian', 'drv': 'Ignition-GW:default'}   # one place to change for 8.3

def _root():
    g = system.util.getGlobals()
    r = g.get(_KEY)
    if r is None:
        g.setdefault(_KEY, ConcurrentHashMap())   # verify setdefault is atomic on Jython's dict; else guard with a java lock
        r = g.get(_KEY)
    return r

def _pageKey(c):
    return '%s|%s' % (c.session.props.id, c.page.props.pageId)

def _page(c):
    r = _root(); k = _pageKey(c)
    r.putIfAbsent(k, ConcurrentHashMap())
    return r.get(k)

def _ping():
    try:
        system.perspective.sendMessage('efc.pvChanged', {}, scope='page')
    except Exception:
        pass                                    # page may be closing during onShutdown

def register(c, members=('Val_PV',)):
    p = c.view.params
    tp = getattr(p, 'tagPath', None)
    if not tp or getattr(p, 'census', True) is False:
        return unregister(c)
    vid = str(c.view.id)                        # 'Templates/ProcessValues/PV_StatusStrip@<mountPath>'
    _page(c).put(vid, {'viewPath': vid.split('@')[0], 'mount': vid.partition('@')[2],
                       'tType': str(getattr(p, 'tType', '')), 'tagPath': str(tp),
                       'members': list(members), 'pagePath': str(c.page.props.path),
                       't': System.currentTimeMillis()})
    _ping()

def unregister(c):
    m = _root().get(_pageKey(c))
    if m is not None and m.remove(str(c.view.id)) is not None:
        _ping()

def census(c):
    """Dock: unique (tagPath/member) entries on this page, with EU, ISA tag and type resolved."""
    m = _root().get(_pageKey(c)) or {}
    path = str(c.page.props.path)
    seen, rows = set(), []
    for e in list(m.values()):
        if e['pagePath'] != path:
            continue
        for mem in e['members']:
            full = '%s/%s' % (e['tagPath'], mem)
            if full not in seen:
                seen.add(full); rows.append({'tagPath': e['tagPath'], 'path': full, 'order': e['t']})
    if not rows:
        return []
    qv = system.tag.readBlocking([r['tagPath'] + s for r in rows for s in ('/Cfg_EU', '/Cfg_Tag')])
    for i, r in enumerate(rows):
        r['eu'] = (qv[2*i].value or '').strip()
        r['name'] = (qv[2*i+1].value or r['tagPath'].split('/')[-1]).strip()
        r['type'] = varType(r['name'], r['eu'])
    return sorted(rows, key=lambda r: (r['type'], r['eu'], r['order']))

def powerChart(rows, penTpl, axisTpl, plotTpl, maxPens=8):
    """Plot per (type, EU), one left axis per plot. *Tpl = dicts copied from a designer-made chart."""
    import copy
    groups, pens, axes, plots = [], [], [], []
    for r in rows:
        g = (r['type'], r['eu'])
        if g not in groups:
            groups.append(g)
            a = copy.deepcopy(axisTpl); a.update({'name': '%s|%s' % g, 'position': 'left'})
            a.setdefault('label', {})['text'] = '%s (%s)' % g
            axes.append(a); plots.append(copy.deepcopy(plotTpl))
        i = groups.index(g)
        if sum(1 for p in pens if p['plot'] == i) >= maxPens:
            continue
        p = copy.deepcopy(penTpl)
        p.update({'name': r['name'], 'axis': '%s|%s' % g, 'plot': i, 'visible': True})
        p.setdefault('data', {})['source'] = 'histprov:%s:/drv:%s:/tag:%s' % (
            HIST['histprov'], HIST['drv'], r['path'].split(']', 1)[-1])
        pens.append(p)
    return pens, axes, plots
```

`varType(isaTag, eu)` applies section G: the override first (read the tag property `[...]Val_PV.varType` in the same `readBlocking` if one is adopted), then the ISA prefix, then the EU table. Unknown values go to `'other'`.

## Open questions for the designer

1. **History.** `Val_PV` is not historized in `PCLib_Ignition81.json`. Who enables history (UDT or instance), on which historian, and with what deadband and sample mode? Without it, neither the Power Chart nor `queryTagHistory` shows anything.
2. **Which members count as a process value?** For the loops: PV only, or PV+SP+CV? For each device type (VFD speed, motor amps, valve position, heater temperature), list the exact members.
3. **Source of the variable type:** an Ignition-only custom tag property on the UDT (no PLC impact), a `Cfg_VarType` DDT member (PLC, PCLib, Standard), or inference only? Also the site mapping for the user-defined ISA letters (C, G, N, O, X).
4. **Exclusion rule** for templates inside `dw_Right` dynamic windows and popups: a `census` param, or a `mountPath` prefix (confirm the dock and popup mount-path format on a running 8.1.22 and 8.3 gateway).
5. **Screen-to-area mapping** for the tag-side fallback: a `setDefaultDock` param, a URL pattern or a lookup.
6. **Density policy:** maximum plots and pens per plot in 400 × 860, ordering (alarm priority, screen order, alphabetical), and whether operators can pin or unpin pens. Pinning implies keeping user state per `pageId|path`, in the same way as `efcDw`.
7. **Time range and mode:** a realtime window (for example 1 h at `refreshRate` around 5 s) or historical with a range selector. Power Chart `pointCount` should stay around the pixel width (400), not -1.
8. **Dock refresh trigger:** does `dw_Right` keep its view instance across `navigate()` in your page configs? If so, the `page.props.path` dependency is mandatory.
9. **Verification on the target builds** (8.1.22 and 8.3.x):
   - `onShutdown` fires when a repeater instance is removed;
   - `setdefault` is atomic on Jython's dict;
   - script-written pens with a non-historical path are converted, or the explicit `histprov` path is required;
   - the 8.3 historian path form for your provider.
