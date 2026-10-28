# Controls Standard rev I: access-level indication (decision 33) instructions

**Target revision:** I. Apply exactly these edits, then stop and report. Do not bump the revision, do not regenerate whole files, do not compile until Adam asks.

**Drive source checked:** `Claude/Controls Standard`, unzipped source folder (`controls-standard-efc-repo-459ca0`, 2026-10-22). `revision.tex` = `\newcommand{\documentrevision}{I}`. Rev I Drive copies of `sections/11-scada-standards.tex` and `appendices/perspective-screen-design.tex` checked 2026-10-28.

**Important: sequencing.** The rev I Drive copy still has the original `\subsection*{Roles and audit}` text (no role-visibility rule). Edits 1 to 3 apply to text that row 2 (`CS-REV-I-hmi-rules-instructions.md`, and batch `CS-REV-I-BATCH-instructions.md`) adds. Apply them only after row 2's edit E4 (and its REV-I-CHANGES entry) has been applied, or merge them into that text at batch compile. If the quoted text is not found, stop and report.

## Why

Decision 33 (2026-10-28, refines decision 27 of 2026-10-21) changes how role-gated HMI controls look. Decision 27 said controls below the user's role level are hidden, not greyed. Decision 33 keeps command buttons that the user's level does not allow on screen, marked with a lock and a tooltip ("Requires <role> access"). Pressing one writes nothing, is logged, and shows a message that names the role needed and the signed-in user. Supervisor+ and Engineer+ controls (bypass, alarm limits, configuration, tuning) and maintenance sections stay hidden below their level. Failed command writes are logged.

Source: `steward/DECISIONS.md` rows 27 and 33; `docs/library-reference.md`, section "Access levels: the lock and the AccessDenied popup" (repo EFC-Repo, branch `claude/great-cray-lcvyr6`). The standard text is generic: library names (`efc.ui`, template paths, the popup part name) are kept out of it.

**Where the rule lives in the standard today.** The rev I Drive copy has no hidden-versus-greyed sentence (`perspective-screen-design.tex` has no role text; `11-scada-standards.tex` has only the role list). The "controls ... are hidden" sentence exists only in the pending row 2 text (batch E4 and REV-I-CHANGES entry N). This file changes that sentence.

## Edits

### 1. sections/11-scada-standards.tex, Roles and audit (batch E4 paragraph)

Anchor (from batch E4, pending row 2; the rev I Drive copy does not yet have it). Find this exact sentence in the paragraph under `\subsection*{Roles and audit}\label{sec:ignition-roles}`:

```
Screens compare that level with the level each action needs (Table~\ref{tab:hmi-roles}); controls that need a higher level than the user has are hidden. \newmark
```

Replace with exactly:

```
Screens compare that level with the level each action needs (Table~\ref{tab:hmi-roles}). A command button that the user's level does not allow stays visible, marked with a lock and a tooltip that names the role needed. Pressing it writes nothing, is logged, and shows a message naming the role needed and the signed-in user. Failed command writes are logged. Controls that need Supervisor or higher, or Engineer or higher, and maintenance sections stay hidden below their level. \newmark
```

### 2. sections/hmi-dynamic-windows.tex, Command tier item (row 2 new file)

Anchor (from batch line for `\item \textbf{Command tier}`, the new file is not yet in Drive). The item ends with this sentence:

```
The button for the current state is highlighted with \texttt{Button/Toggle/On}.
```

Replace with exactly (same sentence, then the new one added after it):

```
The button for the current state is highlighted with \texttt{Button/Toggle/On}. A button that the user's level does not allow is not hidden: it stays visible with a lock and a tooltip naming the role needed (Section~\ref{sec:ignition-roles}). Maintenance and Configuration sections remain hidden below their level, as stated under Maintenance and Configuration.
```

### 3. references/REV-I-CHANGES.md, entry N (Ch11 SCADA, row 2 Edit 6)

Anchor: the phrase `controls hidden below the required level` in entry N. It appears in `CS-REV-I-BATCH-instructions.md` (the entry text under "Append this item") and in `CS-REV-I-hmi-rules-instructions.md` (its entry N). In the REV-I-CHANGES file, change that phrase only:

Old: `controls hidden below the required level`

New: `command buttons below the user's level stay visible with a lock and a tooltip (a press is refused, logged and shown as a message); Supervisor and Engineer controls and maintenance sections stay hidden below their level`

Use the number N that row 2 assigns. Do not add a second entry.

### 4. Still open (need Adam)

Add to the "Still open (need Adam)" list of the REV-I entry:

- Confirm that the standard should describe the lock and the refused-press message (decision 33). The text in Edit 1 is generic on purpose; confirm the wording.

## Checks

1. Labels referenced exist in rev I plus the pending batch: `sec:ignition-roles` and `tab:hmi-roles` (both from batch E4). Grep `sections/` for each before applying.
2. No new labels are introduced by these edits.
3. The quoted anchor sentences in Edits 1 to 3 must match verbatim. If one does not, stop and report; do not guess.
4. Braces and environments balance. The only new command is `\newmark`, which is already used in the batch text.
5. Do not change the Maintenance and Configuration bullet, the bypass "Who" item, or Table tab:hmi-roles; they stay true under decision 33.
6. Do not compile until told.

## Background for the reviewer (not pasted into the standard)

- Decision 27 (hidden, not greyed) is kept for Supervisor+/Engineer+ controls and maintenance sections. Decision 33 narrows it: command buttons at Operator and Maintenance level stay visible with a lock.
- The server-side check is in the library and the PLC. The standard must say that the HMI check is a convenience and that access is enforced by Perspective security and the PLC. This is already in the library reference; if Adam wants it in the standard, add it as a sentence to Edit 1 (open item for review).
- Failed command writes are logged; the standard's audit wording (batch E4 "Audit log" column) covers audited actions, not every failed write. Edit 1 states it in the paragraph.
