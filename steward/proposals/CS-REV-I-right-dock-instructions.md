# Controls Standard rev I: dynamic windows in a Perspective right dock (push mode)

Instructions for an agent working on the EFC Controls Standard (LaTeX, Google Drive folder `Claude/Controls Standard`, **revision I**). Apply exactly these edits, then stop and report. Do not change anything else, do not bump the revision letter, and do not regenerate whole files. Edits marked **HOLD** are not to be applied until the reviewer closes the open items listed at the end.

**Ordering:** this file depends on `CS-REV-I-hmi-rules-instructions.md` (DOC-QUEUE row 2) and `CS-REV-I-library-build-instructions.md` (row 3). The quoted old text is the text as it stands after rows 1-3 (working copies in `steward/standard-edits/rev-I-batch/`, which already contain the row 2 and 3 edits). The Drive rev I copies are the pre-batch text and do not contain it. Apply the row 2 and 3 edits first, or merge this file into the batch.

**Why:** decision 31 (`steward/DECISIONS.md`, 2026-10-22) supersedes decision 24. Dynamic windows are no longer an Embedded View in the shell's right region. Every screen page now has a built-in Perspective right (East) docked view in push mode: Dock ID `efcDynamic`, view `Docks/Host`, Content `push`, Display `visible`, width 37.04 vh (400 px at 1920 x 1080, 800 px at 3840 x 2160) set at runtime by `efc.ui.sizeDock`, not resizable by the operator, handle hidden. The dock takes its own column, the process area shrinks, and nothing is covered. `efc.ui.openDynamic` opens the dock with the window's path, tag path and model. `efc.ui.closeDynamic` reopens it with an empty path, so the screen's default view returns (the dock's View Parameters `defaultPath` / `defaultParams`, set per page in Page Configuration). `session.custom.efcDw`, `Docks/Region` and `efc.ui.setDefaultDock` are removed. The within-window trend expand (decision 26) stays. Setup steps for screen owners: `docs/dock-setup.md` (status: not verified in a gateway). Decision 25 (window height 860 px, 37.04 vh) still holds for the content inside the dock.

**Source:** EFC-Repo branch `claude/loving-bohr-e99ok5`, DOC-QUEUE row 4. Anchors are taken from the rev I working copies (rows 1-3 applied) and checked against `revision.tex` in Drive, which reads `\documentrevision{I}`. The three source files were fetched from Drive but not byte-compared; re-check the anchors in the batch compile.

## Edit 1: `appendices/perspective-screen-design.tex`, shell paragraph (first paragraph after `\section{Approach}`)

Replace the two sentences that start `Each screen region (header, menu, main area, trends, alarm bar)` through the end of the paragraph.

Old:

```latex
Each screen region (header, menu, main area, trends, alarm bar) is an Embedded View placed in the shell. Perspective docks are not used for these regions.
```

New:

```latex
Each screen region (header, menu, main area, alarm bar) is an Embedded View placed in the shell. The dynamic window is the one exception: it is a built-in Perspective right dock in push mode (Dock ID \texttt{efcDynamic}), outside the percent-mode root. The process area shrinks to make room for it, and nothing is covered. The dock width is 37.04\,vh, set at runtime from the viewport height, so it scales with the window content (Section~\ref{sec:hmi-dw-open}).
```

## Edit 2: `appendices/perspective-screen-design.tex`, Container Settings table, row `Region views`

Old (one table row):

```latex
Region views (header, menu, trends, alarm bar) & Equal to the region's slot size & Coordinate, mode = percent & Blank \\
```

New:

```latex
Region views (header, menu, alarm bar) & Equal to the region's slot size & Coordinate, mode = percent & Blank \\
```

The root container and aspect ratio of the dock's view (`Docks/Host` and the `Docks/*` windows) are not in this table. See open item E.

## Edit 3: `appendices/perspective-screen-design.tex`, paragraph `\textbf{Trends / dynamic window.}`

Replace the whole paragraph (it is the only paragraph in the Navigation and Dynamic Content section that starts with that label). Old text, verbatim from the rev I working copy:

```latex
\textbf{Trends / dynamic window.} The right-hand region of the shell is one Embedded View, the dynamic window. Its path and params are bound to a per-page session value, \texttt{session.\allowbreak{}custom.\allowbreak{}efcDw[pageId]}, which holds the current view path, the params and the screen's default view. The project-library script \texttt{efc.ui} writes that value. A click on a template symbol calls \texttt{openDynamic} and shows that device's dynamic window for its tag path. The close button calls \texttt{closeDynamic}, which returns the region to the screen's default view. An expanded trend graph fills the dynamic window below its header; the window keeps its size and the right-hand region never changes width. Each screen view names its default view in the \texttt{defaultDock} view parameter, which \texttt{setDefaultDock} reads on startup. The region is sized in viewport height: 37.04\,vh wide and 79.63\,vh tall, the full height between the header and the alarm bar (400 $\times$ 860 at 1920 $\times$ 1080; 800 $\times$ 1720 at 3840 $\times$ 2160). There are no Perspective docks and no per-project page or dock configuration. What the dynamic window shows and how it opens and closes is set in Section~\ref{sec:hmi-dynamic-windows}. \newmark
```

New:

```latex
\textbf{Trends / dynamic window.} The right-hand dock of each screen page is a built-in Perspective view on the East edge, Dock ID \texttt{efcDynamic}, view \texttt{Docks/Host}, in push mode. It shows the screen's default view (normally the trends) or the open dynamic window. A click on a template symbol calls \texttt{openDynamic}, which opens the dock with that window's path, tag path and model. The close button calls \texttt{closeDynamic}, which reopens the dock with an empty path, so the default view returns. Each screen page sets its default view in the dock's View Parameters in Page Configuration (\texttt{defaultPath}, \texttt{defaultParams}). If the page has no default view, the dock is closed and the process area takes the full width. An expanded trend graph fills the dynamic window below its header; the window keeps its size and the dock never changes width. The dock width is set at runtime to 37.04\,vh (Section~\ref{sec:hmi-dw-open}). The window content inside the dock is sized in viewport height, 37.04\,vh wide and 79.63\,vh tall at 1920 $\times$ 1080. What the dynamic window shows and how it opens and closes is set in Section~\ref{sec:hmi-dynamic-windows}. \newmark
```

## Edit 4: `sections/hmi-dynamic-windows.tex`, `Size and position` and `Closing` items

Two items in the `\subsection[Size, Opening and Closing]` list. Replace each whole `\item` line.

Old, Size and position (line 36 of the working copy):

```latex
  \item \textbf{Size and position.} The dynamic window fills the full height between the header and the alarm bar, in the right-hand region of the shell: 400 $\times$ 860 at 1920 $\times$ 1080 (37.04\,vh wide, 79.63\,vh tall), and 800 $\times$ 1720 at 3840 $\times$ 2160 (Appendix~\ref{app:screen-design}).
```

New:

```latex
  \item \textbf{Size and position.} The dynamic window is the right dock \texttt{efcDynamic} in push mode: its own column on the right edge, with the process area beside it. The dock width is 37.04\,vh, which is 400 px at 1920 $	imes$ 1080 and 800 px at 3840 $	imes$ 2160 (Appendix~
ef{app:screen-design}), set at runtime by 	exttt{efc.ui.sizeDock}. The window content inside the dock is sized in viewport height: 37.04\,vh wide and 79.63\,vh tall at 1920 $\times$ 1080. The runtime sizing is open item A and is not verified in a gateway. Whether the dock runs the full height or sits between the header and the alarm bar is open item B.
```

Old, Closing (line 38 of the working copy):

```latex
  \item \textbf{Closing.} The close button returns the right-hand region to the screen's default view. Each screen view has a \texttt{defaultDock} view parameter that names it (normally the screen's trends), and \texttt{setDefaultDock} sets it on startup.
```

New:

```latex
  \item \textbf{Closing.} The close button calls \texttt{closeDynamic}, which reopens the right dock \texttt{efcDynamic} with an empty path. The dock then shows the screen's default view (normally the trends), set per page in the dock's View Parameters \texttt{defaultPath} and \texttt{defaultParams} in Page Configuration. If the page has no default view, the dock is closed and the process area takes the full width.
```

Opening (line 37) needs no change: it still names the template click and the dynamic window. The `dockId` / `dwTagPath` paragraph (after the table) is also unchanged; `dockId` there is a template parameter, not the Perspective Dock ID.

## Edit 5: `sections/hmi-dynamic-windows.tex`, trend expand sentence (last paragraph of the Trends section, `\label{sec:hmi-trends}`)

Substring replacement in the one sentence that begins `Trends in a dynamic window show the last 30~minutes`.

Old (substring):

```latex
Expanding a graph keeps the dynamic window at 400 $\times$ 860 design px and the right-hand region never changes width:
```

New (substring):

```latex
Expanding a graph keeps the dynamic window at its size and the right dock never changes width:
```

The rest of the sentence (range buttons, pause / live, collapse, about 400 x 760 design px) is unchanged. Decision 26 stands.

## Edit 6: `sections/11-scada-standards.tex`, `\paragraph{Script library.}`

Substring replacement in the paragraph starting `\paragraph{Script library.}`.

Old (substring):

```latex
The dynamic-window region calls \texttt{setDefaultDock} at startup to show its screen default view.
```

New (substring):

```latex
The right dock \texttt{efcDynamic} shows the screen's default view: \texttt{Docks/Host} reads the dock's View Parameters \texttt{defaultPath} and \texttt{defaultParams}, and \texttt{closeDynamic} reopens the dock with an empty path so that the default view returns.
```

## Edit 7: `references/REV-I-CHANGES.md`, items 11 and 13 (no new item; this change belongs to items 11 and 13)

Item 11, substring:

Old: `window ids (Table tab:hmi-dw-ids), size, open/close and defaultDock, section order,`

New: `window ids (Table tab:hmi-dw-ids), size, open/close and the right-dock default view (decision 31), section order,`

Item 13, substring:

Old: `(openDynamic, closeDynamic, setDefaultDock, dblCmd, cmd, bypass/unbypass, ackAll, trend, level)`

New: `(openDynamic, closeDynamic, dblCmd, cmd, bypass/unbypass, ackAll, trend, level)`

Add to item 13, at the end of the item, one sentence: `Right dock efcDynamic (decision 31, 2026-10-22) replaces the embedded-view dynamic-window region (decision 24); see items 11 and the Trends / dynamic window paragraph.`

## HOLD edits (do not apply until open items A-C are closed)

**H1. Shell Layout figure and table, `appendices/perspective-screen-design.tex`.** The TikZ rectangle `Trends /\\Dynamic\\400 $\times$ 860` (drawn at x 1520 to 1920) and the table row `Trends / dynamic window (37.04\,vh wide, 79.63\,vh tall) & 400 $\times$ 860 & 79.17\% ...` describe a region inside the percent-mode root. With a push dock, the process area width (today 1400 px, 72.92 %) and the header and alarm bar widths change. Do not set new values until open items A-C are closed. The table caption and percent note under it also depend on the outcome.

**H2. Shell Layout percent note**, the sentence `The trends/dynamic window fills the full height between the header and the alarm bar` and `When a trend graph is expanded ... the region never changes width`, changes the same way as H1.

**H3. Summary of the shell sizes in `sections/hmi-dynamic-windows.tex`** (if any other sentence there still says `right-hand region`). Check with grep before editing; replace `right-hand region` with `right dock` only where it describes the dynamic window.

## Still open (need Adam; not resolved by this file)

- **A. Dock width from the viewport.** The dock width is set at runtime to 37.04 % of the viewport height, so it scales with the window content (400 px at 1080p, 800 px at 2160p). `efc.ui.sizeDock` calls `alterDock` (8.1.19+). The viewport binding (`page.props.dimensions.viewport.height`) is not verified in a gateway. Confirm on 1080p and 2160p before this text is applied.
- **B. Resolved: between header and alarm bar.** The window sits between the header and the alarm bar (decision 25). The header becomes a full-width top dock and the alarm bar a full-width bottom dock, and the East dock `efcDynamic` fills the height between them. Not yet verified on a gateway.
- **C. Shell aspect lock.** The shell root is locked to 16:9 (Container Settings table). With the dock outside the primary view, the locked shell does not include the 400 px (or 800 px at 4K) column. Whether the lock stays, moves, or is removed is open.
- **D. Gateway verification.** None of the dock steps have been tested on an 8.1 or 8.3 gateway. The checklist is in `docs/dock-setup.md`. Until it passes, the text should not be called verified.
- **E. Dock view container settings.** The Container Settings table does not list `Docks/Host` or the `Docks/*` windows. Their root container, mode and aspect ratio are not defined here. Add a row only after A is closed.
- **F. Batch order.** Edits 1-7 quote text that exists only after rows 2 and 3 are applied. If row 4 is compiled into a batch, re-check all anchors against Drive rev I at that time.

## Checks before reporting back

1. Labels referenced by the new text exist in the rev I working copies: `app:screen-design`, `sec:hmi-dw-open`, `sec:hmi-dynamic-windows`, `sec:hmi-trends`, `ch:scada`, `sec:ignition-roles`, `sec:hmi-bypass`. Confirm with `grep -n '\\label{'` on the target files. No new labels are added.
2. Macros used: `\newmark`, `\texttt`, `\allowbreak`. All exist in `preamble.tex`.
3. Braces and environments balance in each replaced block (each `\item` ends with a period and the list still closes with `\end{itemize}`).
4. After the edits, `grep -n 'setDefaultDock\|efcDw\|defaultDock\|Docks/Region\|Perspective docks are not used'` over the `.tex` files and `REV-I-CHANGES.md` returns no lines, except the sentence in Edit 4 that says `defaultPath`.
5. Do not compile until told.
6. Report the files touched with a one-line summary each. Do not echo whole sections.

## Background (for the reviewer; do not paste into the standard)

- Source of the decision: decision 31 (2026-10-22), superseding 24. Decisions 2 and 25 are kept as stated: the decision 2 mechanism (`defaultDock`) is replaced by the dock's View Parameters, and the decision 25 sizes are kept as px for the dock and vh for the content.
- Decision 26 (expand stays in the window) is unchanged, so Edit 5 changes only the wording about the region.
- `dockId` / `dwTagPath` in the template parameters (dock section, after the table) are template parameter names. They are not renamed, and they are not the Perspective Dock ID `efcDynamic`.
- Window ids (`dw_*`) and template scripts that call `openDynamic`, `closeDynamic` and `dblCmd` are unchanged.
- The Drive copy of `perspective-screen-design.tex` has the pre-batch text (the `defaultDock` / `setDefaultDock` wording, and the `Trends / dynamic window (37.04 vh...)` label is not present). This is consistent with rows 2 and 3 not yet applied in Drive.
