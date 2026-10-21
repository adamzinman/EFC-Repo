# One-time setup / restructure (load only when files are missing)

## Target layout
```
main.tex               preamble + \include list only
chapters/NN-slug.tex   one file per chapter / appendix (A1-, A2-...)
INDEX.md               per chapter: header line + 2-3 line summary
glossary.txt           preferred | avoid: ... | definition
open-items.csv         id,status,owner,target_rev,chapter,question,decision
review-comments.csv    created by `std.py comments`
config.json            paths to type exports and hardware sheet
CHANGELOG.md           one entry per revision
scripts/               copy of this skill's scripts/ (entry point std.py)
```
`chapter` in open-items.csv uses the INDEX chapter number (4, A1) so
`std.py brief` can find the rows.

## Split a single large .tex into chapters
1. `grep -n '\\chapter' <file>.tex` to find boundaries (no full read).
2. Use `sed -n 'a,bp'` to write each range to
   `chapters/NN-slug.tex` (NN = order, appendices `A1-`, `A2-`...).
3. Replace the body of `main.tex` with `\include{chapters/NN-slug}`
   lines. Keep the preamble.
4. Build once to confirm the page count matches the old PDF.

## Create INDEX.md
One block per chapter, built from the `\chapter` titles:
```
## 01-overview.tex | Ch 1 | Overview | Drafted
- <2-3 lines: key rules, decisions, open OIs>
```
The header format is parsed by `std.py status` and `brief`; keep the `|` separators and
the status last. Ask the user for statuses; default to `Drafted`, or
`Skeleton` if the file is under ~40 lines (`wc -l`). Write summaries one
chapter at a time, reading in chunks; this is the one-time cost that
makes every later session cheap.

## Create glossary.txt
One term per line: `Preferred term | avoid: alt1, alt2 | short definition`.
Seed it from the Terminology chapter. Lines starting with # are comments.

## Create open-items.csv
Header: `id,status,owner,target_rev,chapter,question,decision`
Status is `open`, `closed` or `deferred`. Convert existing bracketed
notes to `\openitem{OI-NNN}{...}` and add one row each.
Add to the preamble if missing:
```latex
\newcommand{\openitem}[2]{\textcolor{orange}{\textit{[#1: #2]}}}
\newcommand{\newtag}[1]{#1\marginpar{\footnotesize NEW}}
\newcommand{\pn}[1]{\texttt{#1}}
```

## Mark parts and type tables for the sync scripts
- Wrap every part number in `\pn{...}` (grep for likely patterns first).
- Put `% sync-type: <TypeName>` on the line before each type table
  (Appendix I). Column 1 = member name, column 2 = type.

## Create config.json
```json
{
  "types_plc": "../pclib/exports/**/*.xdd",
  "types_ignition": "../efc-ignition-library/udts/**/*.json",
  "hardware_sheet": "hardware/Standard-Hardware.xlsx",
  "hardware_column": "Part Number"
}
```
Paths are globs relative to the repo root; ask the user where the
exports and sheet live. Clone sibling repos with `--depth 1`.
`redline.sh` needs `latexdiff` (`apt-get install -y latexdiff`).

## Copy the scripts
`cp -r <skill>/scripts .` so they run from the repo root.

## Allowlisting
Append `% lint-ok` to a line to suppress all checks on it (e.g. an
example IP that is not a real address).
