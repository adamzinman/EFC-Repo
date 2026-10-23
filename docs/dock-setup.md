# Right dock setup for EFC screens (decision 31)

> **Status: screens live outside this repo; steps not verified in a gateway.** The EFC_Library side (`Docks/Host`, the `Docks/*` windows and `efc.ui`) is generated and built here. The page configuration below is done by the screen owner in the HMI project and has not been tested on an 8.1 or 8.3 gateway yet.

Dynamic windows open in a built-in Perspective **right dock in push mode**. The dock takes its own column on the right; the primary view (the process area) shrinks to make room, and nothing is covered. Decision 31 in `steward/DECISIONS.md` supersedes the embedded-view region (decision 24).

## How it works
- Every screen page has one right (East) docked view: **Dock ID `efcDynamic`**, view **`Docks/Host`**.
- A click on a template symbol calls `efc.ui.openDynamic(self)`, which runs
  `system.perspective.openDock("efcDynamic", params={"path": <window view>, "tagPath": <tag>, "model": <model or "">})`.
  `Docks/Host` embeds that window (`Docks/ValveDiscrete`, `Docks/Loop`, …).
- The window's close button calls `efc.ui.closeDynamic(self)`. It reopens the dock with an empty `path`, and `Docks/Host` shows the screen's **default view** again. If the page has no default view, `Docks/Host` closes the dock (`system.perspective.closeDock("efcDynamic")`), and the process area takes the full width.
- The default view is stored per page as the dock's **View Parameters** in Page Configuration (`defaultPath`, `defaultParams`). `Docks/Host` keeps a copy in `view.custom.default` when it starts, so later `openDock` calls don't need to repeat it.
- The trend expand (decision 26) stays inside the window: the graph grows to about 400 × 760 px, and the dock never changes width.

## Steps for each screen page
1. Import or inherit **EFC_Library**. The project must contain `Docks/Host`, the `Docks/*` windows and the `efc.ui` script library.
2. In Designer, open **Perspective → Page Configuration** and select the screen page (for example `/screen/:name`).
3. On the **right** edge, click **Add** and pick the view **`Docks/Host`**. Use a page-specific dock rather than Shared Settings when pages need different default views. Perspective allows only one docked view per edge.
4. In **Configure Docked View**, set:

   | Property | Value |
   |---|---|
   | Dock ID | `efcDynamic` (exactly this, because `efc.ui.DOCK_ID` uses it) |
   | Display | `visible` |
   | Content | `push` |
   | Size | `400` (starting value; `efc.ui.sizeDock` resizes it to 37.04 % of the viewport height, see [Width](#width)) |
   | Resizable? | off |
   | Handle | `Hide` |
   | View Parameters | `defaultPath` = the screen's trend view, for example `Screens/<Area>/Trends`; `defaultParams` = that view's params as an object (or `{}`); leave `path`, `tagPath` and `model` empty |

5. **Trend dock:** there's no separate trend dock. The screen's trends are the default view of `efcDynamic` (`defaultPath`), so the right column shows the trends until an operator opens a dynamic window, and goes back to them on close.
6. **Shell:** the dynamic window sits **between the header and the alarm bar**. So the header is a full-width **top** dock (80 px tall at 1080p), the alarm bar is a full-width **bottom** dock (140 px tall), and the primary view is the left menu and main process area (1400 × 860). The right dock `efcDynamic` fills the height between them, 860 px at 1080p. Take the old right-hand trends / dynamic-window region out of the shell. If the shell's percent-mode root has its aspect ratio locked to 16:9, adjust it, because the dock now uses 37.04 vh of the page width. This layout relies on Perspective's top, bottom and East dock placement, which hasn't been verified on a gateway.
7. **Remove the old wiring** from earlier builds: any `Docks/Region` embedded view, the `session.custom.efcDw` session property, and any screen `onStartup` call to `efc.ui.setDefaultDock`. Templates need no change, because they still call `efc.ui.openDynamic(self)`, `efc.ui.closeDynamic(self)` and `efc.ui.dblCmd(self)`.

## Width
The dock is sized from the screen height, so it matches the windows at every display size. `Docks/Host` binds `view.custom.viewportH` to `{page.props.dimensions.viewport.height}`. Its change script, `efc.ui.sizeDock`, calls `system.perspective.alterDock('efcDynamic', {'size': …})` with 37.04 % of that height. That gives 400 px at 1920 × 1080 and 800 px at 3840 × 2160. The windows are 37.04 vh wide, so they match.

- `alterDock` needs **8.1.19 or later**. On older versions the dock keeps the Size set in Page Configuration (set it to 400 for 1080p).
- The viewport binding and `page.props.dimensions.viewport` are **not verified in a gateway**. They come from Inductiveautomation forum posts, not the docs. Test the dock at 1080p and 2160p before relying on it.
- The Page Configuration Size is only the starting value, so set it to 400 and the runtime sizing takes over.

## Check in a gateway (8.1 and 8.3)
- [ ] The page opens with the trends in the right column, and the process area is not covered.
- [ ] The header is a full-width top dock and the alarm bar a full-width bottom dock. The dynamic window fills the height between them, at 1080p and at 2160p.
- [ ] Clicking a valve, motor or PV symbol shows its window in the dock, and a second click on another symbol replaces it.
- [ ] ✕ returns the dock to the trends. On a page with no `defaultPath`, ✕ closes the dock and the process area grows back.
- [ ] The trend expand grows the graph inside the window, and the dock width does not change.
- [ ] `openDock` with new params on a dock that's already open updates `Docks/Host` (param change scripts run) and keeps `view.custom.default`.
- [ ] The gateway log (`efc.ui`) shows no `openDock efcDynamic failed` warning.
