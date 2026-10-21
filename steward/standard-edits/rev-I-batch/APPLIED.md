# Controls Standard rev I batch: applied edits

Source: `steward/proposals/CS-REV-I-BATCH-instructions.md` (DOC-QUEUE rows 1-3). Working copies were made from the rev I files in `W/src` (byte-exact copies of Drive `Claude/Controls Standard`, revision.tex = I). Edits were made in `W/out` only, by exact-string replace (each anchor required exactly one occurrence). Batch text was taken from the instruction file as-is, not retyped. Nothing compiled. Nothing uploaded to Drive (upload pending).

## Edits

| Edit | File | Result | Note |
|---|---|---|---|
| A | sections/heaters.tex | applied (new file) | Electric Heaters subsection |
| B | sections/hmi-dynamic-windows.tex | applied (new file) | Dynamic Windows section |
| B2 | sections/hmi-dynamic-windows.tex | applied | Placed after the dynamic-window table block, before the I/O card paragraph. The batch's "table caption paragraph" does not exist as a separate paragraph in B, so this is the nearest equivalent position. |
| C | sections/06-hardware.tex | applied | `\input{sections/heaters}` before `\subsection{Standard Air Prep Unit}` |
| D | sections/07-software.tex | applied | Safety signals never bypassed in software; HMI bypass of configured-bypassable conditions exempt (decision D, approved) |
| E1 | sections/11-scada-standards.tex | applied | `\paragraph{Script library.}` after the Perspective Design paragraph. `ch:scada` exists, so the fallback sentence was not used. |
| E2 | sections/11-scada-standards.tex | applied | `\input{sections/hmi-dynamic-windows}` before `\section{Alarms}` |
| E3 | sections/11-scada-standards.tex | applied | Shelving and alarm-limit roles sentence |
| E4 | sections/11-scada-standards.tex | applied | Roles and audit rewritten; labels sec:ignition-roles, tab:hmi-roles |
| F-3a | appendices/data-types-future.tex | applied | `\texttt{T\_Heater}` added to control module list |
| F-3b | appendices/data-types-future.tex | applied | Type index row after T_VFD |
| F-3c | appendices/data-types-future.tex | applied | T_Heater type section before T_PID. The appendix states no total type count, so no count was changed. |
| G1-8a | appendices/perspective-screen-design.tex | applied | Trends / dynamic window paragraph replaced (embedded-view design) |
| G1-8b | appendices/perspective-screen-design.tex | applied | Shell layout row, first column |
| G1-8c | appendices/perspective-screen-design.tex | applied | Sentence on 400 x 860 sizing |
| G2a | appendices/perspective-screen-design.tex | applied | Templates sentence now uses EFC_Styles classes (decision 5, approved) |
| G2b | appendices/perspective-screen-design.tex | applied | Sentence uses EFC_Styles classes; the size table now lists the EFC_Styles type scale Text/Size/XXS..XXXL (10, 11, 12, 14, 16, 20, 24, 32 px at 1080p, from generator/build_styles.py TYPE_SCALE). |
| G2c | all .tex | checked | No other occurrence of "style class" in any .tex file. Only perspective-screen-design.tex lines 65, 69 and 99 matched, and 99 is G2a. |
| Row 2 Edit 5 | - | not applied | Dropped by the batch (superseded by G1) |
| H1 | references/REV-I-CHANGES.md | applied as item 11 | Roles, dynamic windows, bypass, trends. Still-open lines merged. |
| H2 | references/REV-I-CHANGES.md | applied as item 12 | Electric heaters. Still-open lines merged. |
| H3 | references/REV-I-CHANGES.md | applied as item 13 | Library build. Path is references/ (the batch's "Claude outputs" path was not used). |
| H-merge | references/REV-I-CHANGES.md | applied | Built from the outputs/ copy (items 1-10 and Queued kept). New heading "## Added 2026-10-21 (Ignition library build)" placed before "## Queued". Four still-open lines merged into "## Still open (need Adam)". |
| H-cleanup | outputs/REV-I-CHANGES.md | removed from W/out | Per step 3; its content now lives in references/ |

Not changed: revision letter, any other content, any file not listed above.

## Sanity checks (Python, W/out)

- Braces: balanced in every changed and new .tex file (unescaped `{` count equals `}` count; 0 in each file, same as src).
- Environments: `\begin` and `\end` match in every file. The changed files gained one `small` and one `longtable` pair each (11-scada, data-types) and both counts stay matched.
- Labels: no duplicate labels in W/out.
- References added by these edits: 16 unique. All resolve to a label in W/out except:
  - `sec:pclib-modes`: exists in rev I per the batch; not checked locally (defined in sections/10-plc-standards.tex, not in W/src).
  - All others resolve, including sec:review-release, sec:online-changes, sec:pclib-t-intlk, app:screen-design, app:data-types-future, sec:sccr, sec:heat, sec:pclib-t-vfd, sec:pclib-t-pid, ch:scada.
- New labels: sec:heaters, tab:heater-methods, sec:pclib-t-heater, tab:pclib-t-heater, sec:hmi-dynamic-windows, tab:hmi-dw-ids, sec:hmi-dw-open, sec:hmi-dw-layout, sec:hmi-touch, sec:hmi-bypass, sec:hmi-trends, sec:ignition-roles, tab:hmi-roles. None was already defined.

## Files in this folder

- sections/heaters.tex (new)
- sections/hmi-dynamic-windows.tex (new)
- sections/06-hardware.tex
- sections/07-software.tex
- sections/11-scada-standards.tex
- appendices/data-types-future.tex
- appendices/perspective-screen-design.tex
- references/REV-I-CHANGES.md
- batch.diff (diff -ru of W/src vs W/out)

## Open items

- Minimum roles for ack, setpoint and latch reset; Admin-only actions (tab:hmi-roles, from H1).
- kW threshold for heater current monitoring; NFPA 86 clause references (from H2).
- Reconcile the two REV-I-CHANGES.md copies (references 2026-10-14 vs Claude outputs 2026-10-16). The batch's item 9-10 content is now in the single file.
- Drive upload: changed/new files are in this folder on GitHub (EFC-Repo main); not uploaded to Drive.
- Not compiled.
