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
   | Size | `400` on 1920 × 1080 clients; `800` on 3840 × 2160 clients (see [Width](#width)) |
   | Resizable? | off |
   | Handle | `Hide` |
   | View Parameters | `defaultPath` = the screen's trend view, for example `Screens/<Area>/Trends`; `defaultParams` = that view's params as an object (or `{}`); leave `path`, `tagPath` and `model` empty |

5. **Trend dock:** there's no separate trend dock. The screen's trends are the default view of `efcDynamic` (`defaultPath`), so the right column shows the trends until an operator opens a dynamic window, and goes back to them on close.
6. **Shell:** take the right-hand trends / dynamic-window region out of the screen shell. The primary view becomes the header, left menu, main process area (1400 × 860) and alarm bar. If the shell's percent-mode root has its aspect ratio locked to 16:9, adjust it, because the dock now uses 400 px of the page width. Check whether the right dock runs the full page height or sits between the header and the alarm bar. The Ignition docs don't say this for East docks. If the header and alarm bar must span the full width, try moving them to top and bottom docks. This hasn't been verified.
7. **Remove the old wiring** from earlier builds: any `Docks/Region` embedded view, the `session.custom.efcDw` session property, and any screen `onStartup` call to `efc.ui.setDefaultDock`. Templates need no change, because they still call `efc.ui.openDynamic(self)`, `efc.ui.closeDynamic(self)` and `efc.ui.dblCmd(self)`.

## Width
A Perspective dock **Size is in pixels**, not vh. The windows inside are sized in vh (37.04 vh = 400 px at 1080p, 800 px at 2160p), so the dock Size has to match the display class:
- 1920 × 1080: Size 400
- 3840 × 2160: Size 800

This repo doesn't solve the case of one page serving both display classes. The options are separate pages or page configurations per display class, or a script that sets the size at runtime with `system.perspective.alterDock("efcDynamic", {"size": …})`, which needs 8.1.19 or later. The screen owner needs to decide between them and test the result.

## Check in a gateway (8.1 and 8.3)
- [ ] The page opens with the trends in the right column, and the process area is not covered.
- [ ] Clicking a valve, motor or PV symbol shows its window in the dock, and a second click on another symbol replaces it.
- [ ] ✕ returns the dock to the trends. On a page with no `defaultPath`, ✕ closes the dock and the process area grows back.
- [ ] The trend expand grows the graph inside the window, and the dock width does not change.
- [ ] `openDock` with new params on a dock that's already open updates `Docks/Host` (param change scripts run) and keeps `view.custom.default`.
- [ ] The gateway log (`efc.ui`) shows no `openDock efcDynamic failed` warning.
