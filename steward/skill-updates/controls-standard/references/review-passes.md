# Review passes (load for proofreading / review)

Run passes **one at a time, one chapter at a time**. Report each pass
as a short list of `file:line  issue  fix`. Fix only after the user
agrees, unless they asked for fixes up front.

## Pass 1: mechanical (script only, no reading)
`python3 scripts/std.py lint chapters/<file>.tex` (or no args for all).
Covers: undefined/duplicate labels, normative language, avoided terms,
possible credentials/IPs, open-item IDs vs register, TODO markers,
chktex if installed. Fix the failures; do not re-read the chapter.

## Pass 2: technical accuracy
Run `std.py types` and `std.py hw` first; fix what they list.
For anything the scripts can't check (ranges, defaults, behaviour),
grep the name in the doc and the source repo and read only the
matching lines.

## Pass 3: completeness
Check against the template in `drafting.md`: purpose, scope, verifiable
requirements, rationale. Flag vague requirements ("appropriate",
"as needed", "adequate") that can't be checked.

## Pass 4: consistency across chapters
Start from the INDEX.md summaries to spot overlapping topics. Then, only
for terms or rules that appear in more than one chapter:
`grep -rn "<term>" chapters/` and compare those lines. Flag rules
that contradict each other.

## Pass 5: copyedit
Last, and only on chapters that passed 1-4. Read in chunks of about
150 lines. Grammar, clarity and sentence length only.

## Reviewer comments (Scott, Sigmund, George, others)
1. `python3 scripts/std.py comments <markup.docx|pdf> [name]`
   appends to `review-comments.csv`. Never read the marked-up file itself.
2. Work through `open` rows by chapter: grep the anchor text in
   `chapters/` to find the line, edit, then set status `done` (or
   `rejected` / `needs-decision`) and a one-line response.
3. Comments that raise a policy question become an `\openitem` and an
   `open-items.csv` row; reference the OI id in the response.
