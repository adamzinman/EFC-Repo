# EFC Controls Standard

LaTeX source for the EFC Gases & Advanced Materials Controls Standard.

**This folder is the source of truth.** Edit the standard here and commit; the Google Drive "Controls Standard" folder is a read-only copy as of rev I (copied 2026-10-29). Old `*-revE/F/G-backup.tex` files were not carried over; released PDFs are in `pdf/` and earlier history is in git.

## Build

On Windows with MiKTeX, double-click `build-all.bat`. It reads the revision letter from `revision.tex` and produces:

- `Controls Standard rev-<X>.pdf`, the full document
- `Appendix PDFs/Controls Standard rev-<X> - Appendix <L> - <Title>.pdf`, one PDF per appendix

Released PDFs are kept in `pdf/` (rev-H, rev-I). Build output (the compiled PDF, `Appendix PDFs/`, `*.aux` and the like) is gitignored; rebuild it from the source. On Linux, run `pdflatex "Controls Standard.tex"` three times.

## Layout

| Path | Contents |
|---|---|
| `Controls Standard.tex` | Master document |
| `preamble.tex` | Shared packages and macros (`\note`, `\future`, `\tbd`, `\newmark`, ...) |
| `revision.tex` | Current revision letter |
| `sections/` | Chapters 0–12 |
| `appendices/` | Appendices A–M |
| `standalone/` | Wrappers that build each appendix as its own PDF |
| `assets/` | Logo and images |
| `tools/` | `gen_future_appendix.py`: rebuilds `appendices/data-types-future.tex` from the PCLib `UDT Standards.md` |
| `references/` | Source material: PCLib `UDT Standards.md`, DDT/DFB extracts, rev H/I change logs, screen design standard. The hardware pricing archive stays in Drive: this repo is public |

## Revisions

Each released revision is tagged (`rev-G`, `rev-H`, ...). Bump the letter in `revision.tex` and add a row to the revision history in `sections/00-frontmatter.tex` for each release.

## Regenerating Appendix I (PCLib)

When the PCLib library changes, copy its latest `UDT Standards.md` into `references/` and run:

    python tools/gen_future_appendix.py "references/PCLib UDT Standards.md" appendices/data-types-future.tex

Don't hand-edit the type tables in that appendix.

> **Warning (2026-10-29):** the committed `appendices/data-types-future.tex` has edits the generator doesn't reproduce: the `T_DiaComp` type, and the alarm-priority paragraph rewritten for Ignition's numbering. Running the command now would delete them. Update `references/PCLib UDT Standards.md` with those changes first, then regenerate and check the diff.

## Not in the build

These files are kept but `Controls Standard.tex` doesn't include them: `sections/06-hardware-ADD-hmi-mounting-height.tex` (pending section for rev J), `appendices/pclib-data-types.tex`, `appendices/perspective-screen-scaling.tex` and `appendices/Perspective-Screen-Scaling-Procedure.tex` (replaced by the screen design appendix in rev H).

## Editing notes

- A comment starting with `%claude-` is an instruction for Claude. It is carried out on the next edit pass and then removed.
- Use `\textgreater{}` instead of a literal `>` in text (OT1 font encoding).
