# Controls Standard rev I: process values historized (HistProvider)

Instructions for an agent working on the EFC Controls Standard (LaTeX, Google Drive folder `Claude/Controls Standard`, **revision I**). Apply exactly these edits, then stop and report. Do not change anything else, do not bump the revision letter, and do not regenerate whole files. Rows 1 to 4 of `steward/DOC-QUEUE.md` are separate topics. Edit 5 depends on row 4 (dock) and row 2 (HMI rules), so compile it after them.

**Why:** decision 34 (`steward/DECISIONS.md`, 2026-10-25). The PCLib Ignition UDTs get a `HistProvider` parameter (tag history provider / historian database name; empty = no history). It is passed to nested instances. `Val_PV` on `T_AI`, `T_KPI` and `T_Analyzer`, and `Val_PV`, `Val_SP` and `Out_CV` on `T_PID`, have tag history enabled when it is set (analog deadband, sample on change, provider defaults for everything else). This is the prerequisite for the dynamic-window trends (decisions 16 and 26) and the dock's trends overview (decision 32). Source: EFC-Repo `types/gen_pclib.py` (`IGN_PARAMS`, `IGN_HISTORY`, `IGN_HISTORY_PROPS`), `types/README.md` (parameter table, regenerated), `generator/build_pv.py` and `generator/pid_loops/generate_loops.py` (demo UDTs `T_AI_Demo`, `T_PID_Demo`). The parameter table here must match `types/README.md`. The demo UDTs are not in the standard and get no edit.

**Anchor check:** Edits 1 to 4 and the Historian section anchor were checked verbatim against the rev I source in Drive (`revision.tex` = I, 2026-10-25). Edit 5 anchors only exist in the rev I batch copy (`steward/standard-edits/rev-I-batch/sections/hmi-dynamic-windows.tex`, created by row 2); re-check them after rows 2 and 4 are applied.

---

## Edit 1: `appendices/data-types-future.tex`, PCLib Ignition UDT Parameters table

**Anchor** (`tab:pclib-ign-params`, last data row before `\bottomrule`; checked verbatim against rev I):
`\texttt{BaseTag} & PLC instance name & \texttt{P101} \\`

**Action:** insert the following line immediately after the anchor line (before `\bottomrule`). Do not change the anchor line.

```latex
\texttt{HistProvider} & Tag history provider (historian database) for the process values; empty = no history & \texttt{PlantHistorian} \\
```

---

## Edit 2: `appendices/data-types-future.tex`, paragraph after the parameter table

**Anchor** (checked verbatim against rev I): the paragraph whose first words are
`Each tag's OPC path is \texttt{\{PathPrefix\}\{BaseTag\}.`

**Action:** insert the following as a new paragraph immediately after that paragraph (before `\begin{longtable}` of the T_AI members table, which follows it).

```latex
Every instance that holds a process value must name a tag history provider in \texttt{HistProvider}. Nested instances receive the parameter from their parent, so set it once on the top-level instance (or multi-edit a folder of instances). When it is set, the historized process values below use analog deadband, sample on change, and the provider's defaults for everything else. An empty \texttt{HistProvider} turns history off. The historized members are \texttt{Val\_PV} of \texttt{T\_AI} and \texttt{T\_Analyzer}, and \texttt{Val\_PV}, \texttt{Val\_SP} and \texttt{Out\_CV} of \texttt{T\_PID}; their member tables say so (Edit 4).
```

**Note:** `T_KPI` is deliberately not named. It has no section in rev I (see Still open, item 1).

---

## Edit 3: `sections/11-scada-standards.tex`, Historian and Data section

**Anchor** (`\section{Historian and Data}`, first paragraph; checked verbatim against rev I, no label on the section): the paragraph whose first sentence is
`Historize data that has a defined operating, quality, maintenance, regulatory, or analysis purpose.`

**Action:** insert the following as a new paragraph immediately after that paragraph. Do not change the anchor paragraph.

```latex
Every process value of a PCLib instance is historized. Every instance that holds one names a tag history provider in \texttt{HistProvider} (Table~\ref{tab:pclib-ign-params} in Appendix~\ref{app:data-types-future}); the historized process values use analog deadband, sampled on change. The deadband value and the retention period are \tbd. Instances without a provider have no history.
\note{Decision 34 fixes the sample mode and the deadband style. The deadband value and retention are not decided; the Ignition implementation currently leaves them to the provider defaults. See Still open, item 3.}
```

---

## Edit 4: `appendices/data-types-future.tex`, member tables (historized rows)

Each replacement keeps the row's four cells and changes only the description cell. Replace the anchor line with the replacement line. Each anchor occurs once in the file (check with `grep -c` before replacing).

**4a. T_AI, `Val_PV`.** Anchor:
`\texttt{Val\_PV} & \texttt{REAL} &  & Process value (EU) --- use this in logic \\`
Replace with:
```latex
\texttt{Val\_PV} & \texttt{REAL} &  & Process value (EU) --- use this in logic; historized when \texttt{HistProvider} is set \\
```

**4b. T_PID, `Val_PV`.** Anchor:
`\texttt{Val\_PV} & \texttt{REAL} &  & Process value (EU) \\`
Replace with:
```latex
\texttt{Val\_PV} & \texttt{REAL} &  & Process value (EU); historized when \texttt{HistProvider} is set \\
```

**4c. T_PID, `Val_SP`.** Anchor:
`\texttt{Val\_SP} & \texttt{REAL} &  & Active setpoint after ramp and limits (EU) \\`
Replace with:
```latex
\texttt{Val\_SP} & \texttt{REAL} &  & Active setpoint after ramp and limits (EU); historized when \texttt{HistProvider} is set \\
```

**4d. T_PID, `Out_CV`.** Anchor:
`\texttt{Out\_CV} & \texttt{REAL} &  & Controller output (\%) \\`
Replace with:
```latex
\texttt{Out\_CV} & \texttt{REAL} &  & Controller output (\%); historized when \texttt{HistProvider} is set \\
```
Do not change `Out_CV` in T_CValve ("Output demand"); it is not historized.

**4e. T_Analyzer, `Val_PV`.** Anchor:
`\texttt{Val\_PV} & \texttt{REAL} &  & Value for control --- held value while in hold \\`
Replace with:
```latex
\texttt{Val\_PV} & \texttt{REAL} &  & Value for control --- held value while in hold; historized when \texttt{HistProvider} is set \\
```

---

## Edit 5: `sections/hmi-dynamic-windows.tex`, Trends subsection (depends on rows 2 and 4)

**Anchor** (`\subsection[Trends]{Trends \newmark}\label{sec:hmi-trends}`; the paragraph that ends `...until the graph is collapsed.`). This text exists only in the rev I batch copy, not in the Drive rev I source. Check that the anchor sentence is present after rows 2 and 4 are compiled; if the wording has moved, match on the sentence `The other sections of the window are hidden until the graph is collapsed.` and do not guess.

**Action:** insert the following as a new paragraph immediately after that paragraph.

```latex
A trend reads the history of its process value. A process value whose instance has no \texttt{HistProvider} (Table~\ref{tab:pclib-ign-params}) has no history to trend.
```

---

## REV-I-CHANGES.md entry

Add one numbered item at the end of the numbered list (after the last existing item; the batch copy ends at item 13, so use the next free number), under a new heading `## Added 2026-10-25 (process value history)` placed before `## Still open (need Adam)` or before `## Queued`, whichever is the later section:

> N. Process values historized (decision 34): `HistProvider` added to the PCLib Ignition UDT parameter table (Table `tab:pclib-ign-params`) with a rule that every process-value instance names a provider; historized members marked in the T_AI, T_PID and T_Analyzer member tables (`Val_PV`; T_PID `Val_SP`, `Out_CV`); Historian and Data section sentence (analog deadband, on change); trend sentence in Trends. Demo UDTs not in the standard. Still-open lines merged.

Merge the "Still open" lines below into the existing `## Still open (need Adam)` list.

---

## Still open (need Adam)

1. `T_KPI` has no section in rev I (not in the Type Index), so Edit 2 does not name it and Edit 4 has no row for it. Decision 34 lists `T_KPI.Val_PV`. Either add the T_KPI member table in a later edit (then add `T_KPI` to Edit 2 and Edit 3) or confirm it stays out of the standard for rev I.
2. Empty `HistProvider`. Decision 34 says every process value is historized, but the parameter table and the implementation treat empty as "no history". Edit 2 and Edit 3 say every process-value instance must name a provider and that empty turns history off. Confirm whether an empty value is allowed at all (for example, a site without a historian), and who checks it. Log the answer as `\openitem{OI-NNN}` plus a row in `open-items.csv` if it becomes policy.
3. Deadband value and retention period. The Historian section already says to choose the deadband and retention to match the purpose, while the implementation sets only the deadband style (analog) and sample mode (on change) and leaves the value and retention to the provider defaults. Edit 3 writes `\tbd` plus `\note`. Decide the value, or confirm defaults are acceptable for rev I.
4. Anchors for Edit 5 exist only in the rev I batch copy. Re-check them against the compiled batch after rows 2 and 4.
5. The new `\tbd` and `\note` macros are used elsewhere in the standard (for example `10-plc-standards.tex`), but confirm they are defined in `preamble.tex` before compiling.

---

## Checks

- Labels referenced exist: `tab:pclib-ign-params`, `app:data-types-future`, `sec:hmi-trends` (batch copy; created by row 2). New labels: none.
- Macros: `\texttt`, `\tbd`, `\note` (confirm in `preamble.tex`); `\newmark` already used in the Trends heading.
- Escapes: underscores in member names as `\_`; `\%` in `Controller output (\%)`; `---` kept as written; no unescaped `&` or `%` in new text.
- Table rows: the parameter-table row has 3 cells, the member-table rows have 4 cells (`&  &` for the empty Init cell), each ends with ` \\`.
- Braces and environments balance in the edited files (the parameter table is a `longtable`; do not add or remove `\begin` or `\end`).
- Do not compile until told.

---

## Background for the reviewer (not pasted into the standard)

- The parameter table wording follows `types/README.md` (regenerated from `types/gen_pclib.py`, `IGN_PARAMS`). Change the wording there first if it moves, then copy it here.
- Mechanics (from `IGN_HISTORY_PROPS`): `historyEnabled` = expression `len("{HistProvider}") > 0`; `historyProvider` bound to `{HistProvider}`; `historicalDeadbandStyle` = Analog; `sampleMode` = OnChange. Those are the Ignition tag properties; the standard text does not name them.
- Uncommitted at the time of writing (EFC-Repo working tree): `steward/DECISIONS.md`, `types/gen_pclib.py`, `types/README.md`, `types/export/PCLib_Ignition81.json`, `types/T_KPI/T_KPI_Ignition81.json`, `generator/build_pv.py`, `generator/pid_loops/generate_loops.py`, `tags/...` demo files. The `CHANGELOG.md` and `docs/library-reference.md` entries for decision 34 exist in the repo; they are not standard text.
