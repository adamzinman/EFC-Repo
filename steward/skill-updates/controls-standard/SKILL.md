---
name: controls-standard
description: Workflow for the EFC Controls Engineering Standard written in LaTeX with lettered revisions. Use whenever the user works on the Controls Standard, including drafting or expanding chapters, syncing with PCLib, UDTs, the Ignition library or the hardware list, open items, reviewer comments, proofreading, or releasing a revision, even if they only say the standard or name a chapter.
---

# Controls Standard workflow

Token efficiency is the priority: everything read stays in context and
is re-sent every turn.

## Rules
- Never read the PDF, .docx, zip, whole `main.tex`, or the scripts.
  `python3 scripts/std.py --help` lists every command.
- Start each session with `std.py brief <chapter>`. Navigate with
  `std.py outline <chapter>` and `std.py show <label>`; read a whole
  chapter only if the user asks.
- Edit with str_replace on exact lines (omit the `NNNN| ` prefix that
  `show` prints). Report changes as a short diff or one-line summary;
  never echo whole sections.
- Script output is capped. Don't add `--all` unless fixing every item in
  one file.
- Keep replies short. Suggest a new chat when the task changes.
- Never put credentials or live plant IPs in the standard. Never invent
  a policy decision: log it as `\openitem{OI-NNN}{...}` plus a row in
  `open-items.csv`.
- When a chapter changes, update its `INDEX.md` summary in the same
  commit.

## Source
Git repo (clone `--depth 1`) or Drive `Claude/Controls Standard`
(latest revision: the unzipped source in that folder, or the newest
`Controls-Standard-rev-*.zip`; check `revision.tex` for the letter). If `scripts/std.py`, `INDEX.md`
or `chapters/` is missing, follow `references/repo-setup.md` first.

## Router (load a reference only when its task comes up)
| Task | Do |
|---|---|
| Draft / expand | read `references/drafting.md`; then lint, sync if tables/parts changed, update INDEX, commit |
| Close open item | grep its row in `open-items.csv`, edit text, set status + decision |
| Proofread / review / reviewer comments | read `references/review-passes.md` |
| Sync with PCLib / UDTs / hardware | `std.py types`, `std.py hw`; fix listed lines |
| Where are we | `std.py status` |
| Send for review | `std.py redline`; ask before uploading |
| Contractor checklist | `std.py req` |
| Release a revision | read `references/release-checklist.md` |
| Change requested from another project (library, types, hardware) | doc subagent: read `references/change-queue.md`; queue an instruction file, never edit the standard |
| Compile queued changes | read `references/change-queue.md` (Compile) |
