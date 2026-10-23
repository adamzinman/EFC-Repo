# Controls Standard rev I: dynamic windows open in a Perspective dock (dw_Right)

Instructions for an agent working on the EFC Controls Standard (LaTeX, Google Drive folder `Claude/Controls Standard`, **revision I**). Apply exactly these edits, then stop and report. Do not change anything else, do not bump the revision letter, do not regenerate whole files, and do not compile until told.

**Order:** apply after the rev I batch (`steward/standard-edits/rev-I-batch/`, DOC-QUEUE rows 1-3). The Drive copy of `sections/hmi-dynamic-windows.tex` does not exist yet; the anchors below are the batch's applied text. Anchors in the appendix (`appendices/perspective-screen-design.tex`) are the text as it reads after batch Edit G1-8a, which replaced the embedded-view paragraph.

**Why:** decision 31 (`steward/DECISIONS.md`, 2026-10-23) supersedes decision 24. Dynamic windows no longer open in an embedded-view region of the screen shell. They open in a Perspective dock. Every page configuration defines one right-side dock with the common id `dw_Right` (400 x 860 at 1080p, display on demand, decision 25). A template click calls `efc.ui.openDynamic`, which sets the dock view with `system.perspective.alterDock('dw_Right', {view, viewParams})` and opens it with `system.perspective.openDock('dw_Right')` (Ignition 8.1.19 or later). Closing returns the page's default view or closes the dock. Window ids keep the `dw_` names. Views now live in the EFCLib library under `Templates/Dynamic Window/<category>/`, with shared parts in `Templates/Dynamic Window/Parts/`. The old `Docks/*` paths are retired. The standard text still describes the embedded-view region, the `session.custom.efcDw` value and `Docks/` paths, so it must be corrected.

**Source of the content:** `steward/DECISIONS.md` row 31 (and rows 24, 25, 2 for context). Library view paths: EFCLib `Templates/Dynamic Window/` tree, decision 31.

---

## Edit 1: `sections/hmi-dynamic-windows.tex`, size bullet (line 36)

Anchor (whole line, verbatim):

```latex
  \item \textbf{Size and position.} The dynamic window fills the full height between the header and the alarm bar, in the right-hand region of the shell: 400 $\times$ 860 at 1920 $\times$ 1080 (37.04\,vh wide, 79.63\,vh tall), and 800 $\times$ 1720 at 3840 $\times$ 2160 (Appendix~\ref{app:screen-design}).
```

Replace with:

```latex
  \item \textbf{Size and position.} The dynamic window is shown in the page's right-hand Perspective dock, \texttt{dw\_Right}. Every page defines this one dock, with the same id on every page. The dock fills the full height between the header and the alarm bar: 400 $\times$ 860 at 1920 $\times$ 1080 (37.04\,vh wide, 79.63\,vh tall), and 800 $\times$ 1720 at 3840 $\times$ 2160 (Appendix~\ref{app:screen-design}). The dock is set to display on demand.
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
  \item \textbf{Closing.} The close button calls \texttt{efc.ui.closeDynamic}, which returns \texttt{dw\_Right} to the page's default view, or closes the dock where the page has none. Each screen view has a \texttt{defaultDock} view parameter that names its default view (normally the screen's trends), and \texttt{setDefaultDock} sets it on startup.
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

## Edit 8: `appendices/perspective-screen-design.tex`, shell paragraph (line 6)

Substring replace (unique in the file):

- Old: `Each screen region (header, menu, main area, trends, alarm bar) is an Embedded View placed in the shell. Perspective docks are not used for these regions, because docks are sized in fixed pixels and would not stay aligned with the scaled content.`
- New: `Each screen region (header, menu, main area, alarm bar) is an Embedded View placed in the shell. The dynamic window is not an Embedded View: it is shown in the page's right-hand Perspective dock, \texttt{dw\_Right} (Section~\ref{sec:hmi-dynamic-windows}). The dock is sized in viewport units, as set out in the Trends / dynamic window paragraph below.`

**HELD, see Still open item 1:** do not apply the shell table row or the percent-placement sentence in this appendix (`Trends / dynamic window (37.04\,vh wide ...`, and the sentence beginning `Percent values are the position properties`) until Adam decides. Leave them as they are.

## Edit 9: `appendices/perspective-screen-design.tex`, Trends / dynamic window paragraph (line 54)

Replace the whole paragraph that begins `\textbf{Trends / dynamic window.} The right-hand region of the shell is one Embedded View` (it is one line, the batch's applied text) with:

```latex
\textbf{Trends / dynamic window.} The dynamic window is the page's right-hand Perspective dock, \texttt{dw\_Right}. Every page configuration defines this one dock, on the right side of the screen, with the common id \texttt{dw\_Right}. The dock is set to display on demand and sized in viewport height: 37.04\,vh wide and 79.63\,vh tall, the full height between the header and the alarm bar (400 $\times$ 860 at 1920 $\times$ 1080; 800 $\times$ 1720 at 3840 $\times$ 2160). A click on a template symbol calls \texttt{efc.ui.openDynamic}, which sets the view and params of the dock to that device's dynamic window for its tag path, then opens the dock (\texttt{system.perspective.alterDock} with \texttt{dw\_Right}, then \texttt{system.perspective.openDock}; Ignition 8.1.19 or later). The close button calls \texttt{efc.ui.closeDynamic}, which returns the dock to the page's default view. Each screen view names its default view in the \texttt{defaultDock} view parameter, which \texttt{setDefaultDock} reads on startup. An expanded trend graph fills the dynamic window below its header; the window keeps its size. What the dynamic window shows and how it opens and closes is set in Section~\ref{sec:hmi-dynamic-windows}. \newmark
```

## Edit 10: `references/REV-I-CHANGES.md`, new numbered item

Add item 14 after item 13 (the library build item) and before `## Queued`:

```
14. Dynamic windows open in the page's right-hand Perspective dock `dw_Right` (decision 31, supersedes decision 24's embedded-view region). Template click calls efc.ui.openDynamic, which alters and opens the dock (Ignition 8.1.19 or later); close returns the page default view. Views are in the library under Templates/Dynamic Window/<category>, shared parts in Templates/Dynamic Window/Parts; Docks/ paths retired. Edits: hmi-dynamic-windows (size, opening, closing, BypassConfirm path, library paths paragraph, trends width), 11-scada (script library), perspective-screen-design (shell paragraph, trends paragraph).
```

---

## Still open (need Adam)

1. **Shell layout.** Decision 31 does not say whether the shell keeps a reserved right-hand column. Shell Layout table row `Trends / dynamic window (37.04\,vh wide ...` and the sentence `Percent values are the position properties ...` still place the dynamic window as a percent-mode Embedded View. Edit 8 table and percent parts are held. Decide: (a) the dock overlays the shell (remove the row and the percent sentence), or (b) the shell keeps a right column of that size and the dock sits in it.
2. **Close with no default view.** Decision 31 says close returns the page default view "or closes the dock". The standard text in Edits 3 and 9 says the dock closes where the page has none. Confirm which pages have no default view, if any.
3. **Display on demand.** Decision 25 sets display onDemand. Edit 1 and Edit 9 state it. Confirm that the default view (normally trends) is shown when the dock is opened, not kept visible on load.
4. **Library minimum version.** Decision 31 gives 8.1.19 for the alterDock/openDock API and a library minimum of 8.1.22. Edits 2 and 9 state only 8.1.19. Confirm whether the standard should state the 8.1.22 library minimum.
5. **`dockId` parameter name.** The template parameter `dockId` (batch line 30) is kept under the decision text. Confirm it is not renamed to `dwId` or similar in the library.

## Checks

- Anchors: each substring or line above occurs exactly once in the batch-applied file. Anchor text is taken from the batch file (`steward/standard-edits/rev-I-batch/`), not from an older revision.
- Labels referenced exist: `sec:hmi-dynamic-windows`, `tab:hmi-dw-ids`, `app:screen-design`, `sec:hmi-trends`. No new labels are introduced.
- Macros used exist: `\newmark` (already used in both files), `\texttt`, `\textit`, `\textbf`, `\item`. The `<category>` placeholder is written as `\textit{category}`, so no raw `<` or `>` appear.
- Underscores in text are escaped as `\_` (for example `dw\_Right`, `Cfg\_BypassMax`).
- Braces and environments balance in each changed file. Do not compile until told.

## Background for the reviewer (not pasted into the standard)

- Decision 31 changes the region from an Embedded View to a dock. Decision 24 had settled the embedded-view approach (CS-REV-I-hmi-rules Edit 8). This file replaces that wording for the dynamic window. It does not rewrite the already-written batch files in the repo copy; it is a new topic queued after the batch.
- The library build (`steward/proposals/efc_ui_code.py`) still uses the `Docks/*` paths and `session.custom.efcDw` from decision 24. That code is in EFCLib, not the standard, and is outside this file.
- Decision 31 retires the `Docks/Region` and `efcDw` paths. Those names are in the batch text only in the line-68 `Docks/Parts/BypassConfirm` path (Edit 4) and the appendix trends paragraph (Edit 9).
