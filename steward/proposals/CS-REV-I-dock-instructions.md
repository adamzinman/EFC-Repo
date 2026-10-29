# Controls Standard rev I: dynamic windows open in a Perspective dock (dw_Right)

Instructions for an agent working on the EFC Controls Standard (LaTeX, Google Drive folder `Claude/Controls Standard`, **revision I**). Apply exactly these edits, then stop and report. Do not change anything else, do not bump the revision letter, do not regenerate whole files, and do not compile until told.

**Order:** apply after the rev I batch (`steward/standard-edits/rev-I-batch/`, DOC-QUEUE rows 1-3). The Drive copy of `sections/hmi-dynamic-windows.tex` does not exist yet; the anchors below are the batch's applied text. Anchors in the appendix (`appendices/perspective-screen-design.tex`) are the text as it reads after batch Edit G1-8a, which replaced the embedded-view paragraph.

**Why:** decision 31 (`steward/DECISIONS.md`, 2026-10-23) supersedes decision 24. Dynamic windows no longer open in an embedded-view region of the screen shell. They open in a Perspective dock. Every page configuration defines one right-side dock with the common id `dw_Right` (400 x 860 at 1080p). A template click calls `efc.ui.openDynamic`, which sets the dock view with `system.perspective.alterDock('dw_Right', {view, viewParams})` and opens it with `system.perspective.openDock('dw_Right')` (Ignition 8.1.19 or later). Close returns the page's default view. Window ids keep the `dw_` names. Views now live in the EFCLib library under `Templates/Dynamic Window/<category>/`, with shared parts in `Templates/Dynamic Window/Parts/`. The old `Docks/*` paths are retired. The standard text still describes the embedded-view region, the `session.custom.efcDw` value and `Docks/` paths, so it must be corrected.

**Decision 32 (`steward/DECISIONS.md`, 2026-10-24) refines 31 and supersedes decision 25 for the dock:** the dock covers the right-hand section of the shell (a content cover, not a reserved column) and is always displayed; it is not shown on demand. Each page's initial dock view is its trends overview, shown when the page loads. The `dockId` template parameter keeps its name. The text below uses these settings. The 8.1.22 library minimum and the no-default-view close case are still open (see Still open).

**Sizing (decision 33, 2026-10-24):** all design work is for a 1920 x 1080 page that scales up to 4K, so any px size is its vh / vw equivalent. Page Configuration takes the `dw_Right` size in px only, so the library scales it: `efc.ui.sizeDock` sets the dock to 400 x viewport height / 1080 (37.04 vh; 400 px at 1080p, 800 px at 4K) through `alterDock` on every open, close and screen startup, and a screen change script on `page.props.dimensions.viewport.height` (Ignition 8.1.7+) calls it on resize. Edits 8a and 9 state this.

**Source of the content:** `steward/DECISIONS.md` rows 31 and 32 (and rows 24, 25, 2 for context). Library view paths: EFCLib `Templates/Dynamic Window/` tree, decision 31.

---

## Edit 1: `sections/hmi-dynamic-windows.tex`, size bullet (line 36)

Anchor (whole line, verbatim):

```latex
  \item \textbf{Size and position.} The dynamic window fills the full height between the header and the alarm bar, in the right-hand region of the shell: 400 $\times$ 860 at 1920 $\times$ 1080 (37.04\,vh wide, 79.63\,vh tall), and 800 $\times$ 1720 at 3840 $\times$ 2160 (Appendix~\ref{app:screen-design}).
```

Replace with:

```latex
  \item \textbf{Size and position.} The dynamic window is shown in the page's right-hand Perspective dock, \texttt{dw\_Right}. Every page defines this one dock, with the same id on every page. The dock covers the right-hand section of the shell and fills the full height between the header and the alarm bar: 400 $\times$ 860 at 1920 $\times$ 1080 (37.04\,vh wide, 79.63\,vh tall), and 800 $\times$ 1720 at 3840 $\times$ 2160 (Appendix~\ref{app:screen-design}). The dock is always displayed on every page. When the page loads, it shows the page's trends overview.
```

## Edit 2: `sections/hmi-dynamic-windows.tex`, opening bullet (line 37)

Anchor (whole line, verbatim):

```latex
  \item \textbf{Opening.} A single click or tap on the template symbol opens its dynamic window. The click target is the whole symbol bounding box, at least 44 design px in each direction.
```

Replace with:

```latex
  \item \textbf{Opening.} A single click or tap on the template symbol opens its dynamic window. The template calls \texttt{efc.ui.openDynamic}, which sets the view and params of \texttt{dw\_Right} (\texttt{system.perspective.alterDock}) and opens the dock (\texttt{system.perspective.openDock}; Ignition 8.1.19 or later). The click target is the whole symbol bounding box, at least 44 design px in each direction.
```

## Edit 3: `sections/hmi-dynamic-windows.tex`, closing bullet (line 38)

Anchor (whole line, verbatim):

```latex
  \item \textbf{Closing.} The close button returns the right-hand region to the screen's default view. Each screen view has a \texttt{defaultDock} view parameter that names it (normally the screen's trends), and \texttt{setDefaultDock} sets it on startup.
```

Replace with:

```latex
  \item \textbf{Closing.} The close button calls \texttt{efc.ui.closeDynamic}, which returns \texttt{dw\_Right} to the page's default view, normally the trends overview. Each screen view has a \texttt{defaultDock} view parameter that names its default view, and \texttt{setDefaultDock} sets it on startup. The behaviour for a page with no default view is \tbd.
```

## Edit 4: `sections/hmi-dynamic-windows.tex`, confirmation bullet (line 68)

Substring replace (unique in the file):

- Old: `\texttt{Docks/Parts/BypassConfirm}`
- New: `\texttt{Templates/Dynamic Window/Parts/BypassConfirm}`

## Edit 5: `sections/hmi-dynamic-windows.tex`, library paths paragraph (new paragraph)

Insert the following paragraph as a new paragraph immediately before the line that begins `A template's \texttt{dockId} parameter overrides` (line 30). Leave that line unchanged. Leave a blank line before and after the new paragraph.

```latex
Dynamic window views are library templates under \texttt{Templates/Dynamic Window/\textit{category}}, in the categories Valves, Rotating, HeatTransfer, ProcessValues, Loops, Station and IO. Parts shared by several windows are in \texttt{Templates/Dynamic Window/Parts} (Trend, IntlkList and BypassConfirm). Window ids keep the \texttt{dw\_} names in Table~\ref{tab:hmi-dw-ids}.
```

## Edit 6: `sections/hmi-dynamic-windows.tex`, trends paragraph (line 76)

Substring replace (unique in the file):

- Old: `the right-hand region never changes width`
- New: `the dock never changes width`

## Edit 7: `sections/11-scada-standards.tex`, script library paragraph

Substring replace (unique in the file):

- Old: `The dynamic-window region calls \texttt{setDefaultDock} at startup to show its screen default view.`
- New: `Each screen view calls \texttt{setDefaultDock} at startup to show its default view in the \texttt{dw\_Right} dock.`

## Edit 8: `appendices/perspective-screen-design.tex`, shell paragraph, table row and percent sentence

Three changes in this appendix. All three anchors are the batch's applied text and were checked against it.

**8a. Shell paragraph (line 6).** Substring replace (unique in the line):

- Old: `Each screen region (header, menu, main area, trends, alarm bar) is an Embedded View placed in the shell. Perspective docks are not used for these regions, because docks are sized in fixed pixels and would not stay aligned with the scaled content.`
- New: `Each screen region (header, menu, main area, alarm bar) is an Embedded View placed in the shell. The dynamic window is not an Embedded View: it is the page's right-hand Perspective dock, \texttt{dw\_Right} (Section~\ref{sec:hmi-dynamic-windows}), which covers the right-hand section of the shell. The dock is set in pixels in Page Configuration and scaled to viewport units by \texttt{efc.ui.sizeDock}, as set out in the Trends / dynamic window paragraph below.`

**8b. Shell Layout table row (line 28).** Keep the row's label and design size. Replace the four percent cells with one spanning cell. Substring replace (unique in the file):

- Old: `Trends / dynamic window (37.04\,vh wide, 79.63\,vh tall) & 400 $\times$ 860 & 79.17\% & 7.41\% & 20.83\% & 79.63\% \\`
- New: `Trends / dynamic window (37.04\,vh wide, 79.63\,vh tall) & 400 $\times$ 860 & \multicolumn{4}{c}{Perspective dock \texttt{dw\_Right}, covers this section} \\`

**8c. Percent sentence (line 33).** Replace the whole line. Anchor (whole line, verbatim):

```latex
Percent values are the position properties to enter on each Embedded View in the shell's percent-mode root. The trends/dynamic window fills the full height between the header and the alarm bar: 400 $\times$ 860 design px at 1920 $\times$ 1080 (37.04\,vh wide, 79.63\,vh tall), which renders at 800 $\times$ 1720\,px on a 3840 $\times$ 2160 display (its largest size) and scales down proportionally on smaller displays. When a trend graph is expanded, the graph fills the window below its header and the window keeps its size; the region never changes width (Section~\ref{sec:hmi-trends}). If a collapsible-trends variant of the shell is added later, its main area becomes 1800 $\times$ 860 and should use layouts designed for that size.
```

Replace with:

```latex
Percent values are the position properties to enter on each Embedded View in the shell's percent-mode root. The trends/dynamic window takes no percent position: it is the \texttt{dw\_Right} dock, which covers the right-hand section of the shell and fills the full height between the header and the alarm bar: 400 $\times$ 860 design px at 1920 $\times$ 1080 (37.04\,vh wide, 79.63\,vh tall), which renders at 800 $\times$ 1720\,px on a 3840 $\times$ 2160 display (its largest size) and scales down proportionally on smaller displays. When a trend graph is expanded, the graph fills the window below its header and the window keeps its size; the dock never changes width (Section~\ref{sec:hmi-trends}). If a collapsible-trends variant of the shell is added later, its main area becomes 1800 $\times$ 860 and should use layouts designed for that size. \tbd (see Still open item 3.)
```

## Edit 9: `appendices/perspective-screen-design.tex`, Trends / dynamic window paragraph (line 54)

Replace the whole paragraph that begins `\textbf{Trends / dynamic window.} The right-hand region of the shell is one Embedded View` (it is one line, the batch's applied text) with:

```latex
\textbf{Trends / dynamic window.} The dynamic window is the page's right-hand Perspective dock, \texttt{dw\_Right}. Every page configuration defines this one dock, with the common id \texttt{dw\_Right}. The dock covers the right-hand section of the shell and is always displayed on every page. It is set in pixels in Page Configuration and scaled in script by \texttt{efc.ui.sizeDock} so that it stays sized in viewport height: 37.04\,vh wide and 79.63\,vh tall, the full height between the header and the alarm bar (400 $\times$ 860 at 1920 $\times$ 1080; 800 $\times$ 1720 at 3840 $\times$ 2160). When the page loads, the dock shows the page's trends overview. A click on a template symbol calls \texttt{efc.ui.openDynamic}, which sets the view and params of the dock to that device's dynamic window for its tag path, then opens the dock (\texttt{system.perspective.alterDock} with \texttt{dw\_Right}, then \texttt{system.perspective.openDock}; Ignition 8.1.19 or later). The close button calls \texttt{efc.ui.closeDynamic}, which returns the dock to the page's default view. The behaviour for a page with no default view is \tbd. Each screen view names its default view in the \texttt{defaultDock} view parameter, which \texttt{setDefaultDock} reads on startup. An expanded trend graph fills the dynamic window below its header; the window keeps its size. What the dynamic window shows and how it opens and closes is set in Section~\ref{sec:hmi-dynamic-windows}. \newmark
```

## Edit 10: `references/REV-I-CHANGES.md`, new numbered item

Add item 14 after item 13 (the library build item) and before `## Queued`:

```
14. Dynamic windows open in the page's right-hand Perspective dock `dw_Right` (decisions 31-32, supersede decision 24's embedded-view region). The dock covers the right-hand section of the shell and is always displayed; its initial view is the trends overview. Template click calls efc.ui.openDynamic, which alters and opens the dock (Ignition 8.1.19 or later); close returns the page default view (no-default case TBD). Views are in the library under Templates/Dynamic Window/<category>, shared parts in Templates/Dynamic Window/Parts; Docks/ paths retired. Edits: hmi-dynamic-windows (size, opening, closing, BypassConfirm path, library paths paragraph, trends width), 11-scada (script library), perspective-screen-design (shell paragraph, shell table row, percent sentence, trends paragraph).
```

---

## Still open (need Adam)

1. **Close with no default view. DEFERRED.** Adam will evaluate options. Standard text says close returns the page's default view and marks the no-default case `\tbd` (Edits 3 and 9). Decide what happens on a page with no default view.
2. **Ignition library minimum.** Adam is not sure. Recommendation: state the library minimum as Ignition 8.1.22. The library requires it anyway; 8.1.19 is only the version where `alterDock` appeared. Edits 2 and 9 currently state the 8.1.19 API floor. If 8.1.22 is adopted, change both to 8.1.22.
3. **Collapsible-trends sentence (appendix line 33, last sentence).** It assumes the main area can widen when the window is hidden. The dock is now always displayed, so the sentence may be obsolete. Edit 8c keeps it and marks it `\tbd`. Remove it or keep it.

Resolved by decision 32 (no longer open): the shell layout (the dock covers the right-hand section; the table row keeps its size and loses its percent cells; the percent-placement sentence is rewritten); display (always displayed, not on demand); the `dockId` parameter name (kept).

## Checks

- Anchors: each substring or line above occurs exactly once in the batch-applied file. Anchor text is taken from the batch file (`steward/standard-edits/rev-I-batch/`), not from an older revision. Re-checked 2026-10-24 for Edits 1-3, 5-6, 8a-8c, 9.
- Labels referenced exist: `sec:hmi-dynamic-windows`, `tab:hmi-dw-ids`, `app:screen-design`, `sec:hmi-trends`. No new labels are introduced.
- Macros used exist: `\newmark` (already used in both files), `\tbd` (used in the batch), `\texttt`, `\textit`, `\textbf`, `\multicolumn`, `\item`. The `<category>` placeholder is written as `\textit{category}`, so no raw `<` or `>` appear.
- Underscores in text are escaped as `\_` (for example `dw\_Right`, `Cfg\_BypassMax`).
- Braces and environments balance in each changed file. Do not compile until told.

## Background for the reviewer (not pasted into the standard)

- Decision 31 changes the region from an Embedded View to a dock. Decision 24 had settled the embedded-view approach (CS-REV-I-hmi-rules Edit 8). This file replaces that wording for the dynamic window. It does not rewrite the already-written batch files in the repo copy; it is a new topic queued after the batch.
- Decision 32 overrides decision 25 ("display onDemand") for `dw_Right`. The new text says the dock is always displayed and never uses "on demand" or "the dock closes" for the page-with-no-default case.
- The library build (`steward/proposals/efc_ui_code.py`) still uses the `Docks/*` paths and `session.custom.efcDw` from decision 24. That code is in EFCLib, not the standard, and is outside this file.
- Decision 31 retires the `Docks/Region` and `efcDw` paths. Those names are in the batch text only in the line-68 `Docks/Parts/BypassConfirm` path (Edit 4) and the appendix trends paragraph (Edit 9).
