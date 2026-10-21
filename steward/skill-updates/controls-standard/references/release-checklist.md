# Release checklist (load when cutting a revision)

1. `std.py status` for the overview. `std.py lint`, `std.py types` and
   `std.py hw` report 0 failures, or each remaining one is
   accepted by the user and noted. No `open` rows targeted at this
   revision in `review-comments.csv`.
2. Every chapter in `INDEX.md` is `Proofed` or deliberately left at
   its current status (listed in the changelog as not updated).
3. `open-items.csv`: every row targeted at this revision is `closed` or
   moved to the next revision. Closed items have no `\openitem` left.
4. Remove `\newtag{}` wrappers from the previous revision's content.
5. Bump the revision letter and date on the title page and in the
   revision history table.
6. `python3 scripts/std.py changelog <X>`; tidy the draft to under
   20 lines and add it to `CHANGELOG.md`.
7. Build: `latexmk -pdf main.tex`. Check the log for problems only:
   `grep -iE "warning|undefined" main.log`.
8. Before tagging, `python3 scripts/std.py redline` for a final redline
   against the previous release (reviewer copy).
   Then commit, `git tag rev-<X>`, push.
9. Zip the source as `Controls-Standard-rev-<X>.zip` and upload it with
   the PDF to Drive `Claude/Controls Standard` (ask before uploading).
10. `python3 scripts/std.py req` and keep the CSV with the release
    as the contractor compliance checklist (spot-check numbering vs PDF).
11. Only if the user asks for Word: `pandoc main.tex -o
    Controls-Standard-rev-<X>.docx`, then check tables manually.
