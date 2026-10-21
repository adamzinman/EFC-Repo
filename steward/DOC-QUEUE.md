# Controls Standard change queue

Pending changes to the EFC Controls Standard from this project. Process: `controls-standard` skill, `references/change-queue.md`. Instruction files live in `steward/proposals/`. Compile all `queued` rows into one batch at the end of the library work.

| # | date | topic | instruction file | target rev | files touched | open items | status |
|---|---|---|---|---|---|---|---|
| 1 | 2026-10-21 | Electric heaters (T_Heater): Ch6 subsection + Appendix I type | CS-REV-I-heaters-instructions.md | I | new sections/heaters.tex; 06-hardware.tex; data-types-future.tex; REV-I-CHANGES.md | kW threshold for current monitoring; NFPA 86 clauses | queued |
| 2 | 2026-10-21 | HMI rules: roles, dynamic windows, touch double-tap, bypass, trends (updated for decisions 23-24, 2026-10-21: embedded-view shell, x80 device DDT faceplates, layout appendix Edit 8; graph expand inside the window (decision 26)) | CS-REV-I-hmi-rules-instructions.md | I | new sections/hmi-dynamic-windows.tex; 11-scada-standards.tex; perspective-screen-design.tex (Shell Layout table and paragraph, Trends / dynamic window); sections/07-software.tex (Online Changes and Forces, not 10-plc-standards.tex); REV-I-CHANGES.md | ack / setpoint / latch-reset roles; Admin-only actions; Edit 7 anchor still from rev H, not re-checked (Drive not reachable this session); anchors checked against local copies, not Drive rev I | queued (all anchors checked against rev I, 2026-10-21; sizes corrected to rev I shell (decision 25)) |
