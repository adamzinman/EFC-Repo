# EFC Controls Standard

This directory in EFC-Repo is the primary location for the EFC Gases & Advanced Materials Controls Standard: LaTeX sources, supporting assets and references, and released PDFs. Make future edits here and commit the sources and corresponding PDFs together. Google Drive is a legacy copy, not the editing location.

## Build

On Windows with MiKTeX, double-click `build-all.bat`. It reads the revision letter from `revision.tex` and produces:

- `pdf/Controls Standard rev-<X>.pdf`, the full document
- `Appendix PDFs/Controls Standard rev-<X> - Appendix <L> - <Title>.pdf`, one PDF per appendix

Released PDFs are tracked alongside their source. Temporary LaTeX build files are ignored. Run the build from this directory and commit the updated full PDF and appendix PDFs with the source changes.

## Layout

| Path | Contents |
|---|---|
| `Controls Standard.tex` | Master document (`master.tex` is a stub that inputs it) |
| `preamble.tex` | Shared packages and macros (`\note`, `\future`, `\tbd`, `\newmark`, ...) |
| `revision.tex` | Current revision letter |
| `sections/` | Chapters 0–12 |
| `appendices/` | Appendices A–N |
| `standalone/` | Wrappers that build each appendix as its own PDF |
| `assets/` | Logo and images |
| `tools/` | `gen_future_appendix.py`: rebuilds `appendices/data-types-future.tex` from the PCLib `UDT Standards.md` |
| `references/` | Source material: PCLib `UDT Standards.md`, DDT/DFB extracts, rev H/I change logs, screen design standard. The hardware pricing archive is kept out of this public repo (it stays in Drive) |

## Revisions

Each released revision is tagged (`rev-G`, `rev-H`, ...). Bump the letter in `revision.tex` and add a row to the revision history in `sections/00-frontmatter.tex` for each release.

## Regenerating Appendix I (PCLib)

When the PCLib library changes, copy its latest `UDT Standards.md` into `references/` and run:

    python tools/gen_future_appendix.py "references/PCLib UDT Standards.md" appendices/data-types-future.tex

Don't hand-edit the type tables in that appendix.

> **Warning (2026-11-03):** the committed `appendices/data-types-future.tex` has edits the generator doesn't reproduce: the `T_DiaComp` type, and the alarm-priority paragraph rewritten for Ignition's numbering. Running the command now would delete them. Update `references/PCLib UDT Standards.md` with those changes first, then regenerate and check the diff.

## Not in the build

These files are kept but `Controls Standard.tex` doesn't include them: `sections/06-hardware-ADD-hmi-mounting-height.tex` (pending section for rev J), `appendices/pclib-data-types.tex`, `appendices/perspective-screen-scaling.tex` and `appendices/Perspective-Screen-Scaling-Procedure.tex` (replaced by the screen design appendix in rev H). The `*-rev?-backup.tex` files and `master-revG-backup.tex` are historical copies.

## Editing notes

- A comment starting with `%claude-` is an instruction for Claude. It is carried out on the next edit pass and then removed.
- Use `\textgreater{}` instead of a literal `>` in text (OT1 font encoding).

## Migration from Google Drive

Imported from `G:\My Drive\Claude\Controls Standard` on 2026-11-03. All 133 source, PDF, asset, reference, and helper files were copied and SHA-256 verified. The hardware pricing archive was removed afterwards (public repo), and `references/REV-I-CHANGES.md` was replaced with the complete change log from `steward/standard-edits/rev-I-batch/` (the Drive copy was a 21-line excerpt). Temporary LaTeX files were excluded. `drive-import-manifest.json` records the original paths, destination paths, and original hashes; README and build instructions were then updated for repository ownership. The existing master source and rev-I full PDF matched the Drive copies.

The current release is rev-I: [full PDF](pdf/Controls%20Standard%20rev-I.pdf) and [appendix PDFs](Appendix%20PDFs/). Rev-H PDFs, backup sources, `master.pdf`, and `Claude outputs/` are retained as historical/reference material; they are not the current release. `references/` contains supporting material.
