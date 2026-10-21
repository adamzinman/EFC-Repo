# Change queue: standard updates requested from other projects

Use when work outside the standard (EFCLib templates, PCLib types, hardware,
design reviews) produces decisions the standard must reflect. The standard
is never edited from that session. A documentation subagent queues the
change as a Cowork instruction file; the queue is compiled into one batch
at the end of the work and applied by an agent in Cowork.

## The documentation subagent
- Model: Haiku. Spawn it in the background so the main work continues.
- Inputs: the decision text (one or more rows of the project's decision
  log) and the latest revision of the standard (see Source in SKILL.md).
- Reads only what it needs: `grep -n` for `\section`, `\subsection`,
  `\label`, then `sed -n` ranges. Never whole files.
- Output: one instruction file per topic plus a ledger row (below).
  Commit both in the requesting project's repo; upload nothing.

## Instruction file (one per topic)
`CS-REV-<rev>-<topic>-instructions.md`, sections in this order:
1. Header: target revision, "apply exactly these edits, then stop and
   report; do not bump the revision; do not regenerate whole files".
2. Why: one paragraph, plus where the content came from (repo, branch,
   generator).
3. Numbered edits. Each names the file, quotes the anchor line verbatim
   (taken from the target revision, not an older one), and gives the
   complete LaTeX block to insert or replace. Generated content (type
   tables) is produced with the standard's own `tools/` generator and
   spliced, never by regenerating a hand-edited file.
4. REV-<rev>-CHANGES.md entry (numbered item) and "Still open (need
   Adam)" items. Undecided policy is written as `\tbd` + `\note` and
   listed here. Never invent policy.
5. Checks: labels referenced exist; new labels are unused; macros exist
   in `preamble.tex`; braces and environments balance; do not compile
   until told.
6. Background for the reviewer (not pasted into the standard).

## Ledger
`DOC-QUEUE.md` in the requesting repo, one row per instruction file:
`| # | date | topic | instruction file | target rev | files touched | open items | status |`
Status: `queued` -> `compiled` -> `applied` (set by the user after Cowork
reports back) or `dropped`. When a later decision changes a queued topic,
edit that topic's instruction file and note the date in the row; do not
add a second file for the same topic.

## Compile (end of the work, when the user asks)
1. Take every `queued` row for the same target revision.
2. Re-check each anchor against the current target revision (it may have
   moved). Fix the instruction text, do not guess.
3. Merge into `CS-REV-<rev>-batch-<date>-instructions.md`: edits grouped
   by file in document order; edits to the same anchor combined; one
   combined REV-CHANGES entry per topic; one merged Still-open list; one
   checks section.
4. Flag conflicts with existing text (for example a rule the new text
   contradicts) at the top under "Decisions needed before applying".
5. Set the rows to `compiled`, commit, and give the user the file.
