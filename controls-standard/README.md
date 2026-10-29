# EFC Controls Standard

LaTeX source for the EFC Gases & Advanced Materials Controls Standard.

## Build

On Windows with MiKTeX, double-click `build-all.bat`. It reads the revision letter from `revision.tex` and produces:

- `Controls Standard rev-<X>.pdf`, the full document
- `Appendix PDFs/Controls Standard rev-<X> - Appendix <L> - <Title>.pdf`, one PDF per appendix

PDFs and LaTeX build files are not tracked. Rebuild them from the source.

## Layout

| Path | Contents |
|---|---|
| `Controls Standard.tex` | Master document (`master.tex` is a stub that inputs it) |
| `preamble.tex` | Shared packages and macros (`\note`, `\future`, `\tbd`, `\newmark`, ...) |
| `revision.tex` | Current revision letter |
| `sections/` | Chapters 0–12 |
| `appendices/` | Appendices A–M |
| `standalone/` | Wrappers that build each appendix as its own PDF |
| `assets/` | Logo and images |
| `tools/` | `gen_future_appendix.py`: rebuilds `appendices/data-types-future.tex` from the PCLib `UDT Standards.md` |
| `references/` | Source material: DDT/DFB extracts, change log, screen design standard, pricing archive |

## Revisions

Each released revision is tagged (`rev-G`, `rev-H`, ...). Bump the letter in `revision.tex` and add a row to the revision history in `sections/00-frontmatter.tex` for each release.

## Regenerating Appendix I (PCLib)

When the PCLib library changes, copy its latest `UDT Standards.md` into `references/` and run:

    python tools/gen_future_appendix.py "references/PCLib UDT Standards.md" appendices/data-types-future.tex

Don't hand-edit the type tables in that appendix.

## Editing notes

- A comment starting with `%claude-` is an instruction for Claude. It is carried out on the next edit pass and then removed.
- Use `\textgreater{}` instead of a literal `>` in text (OT1 font encoding).
