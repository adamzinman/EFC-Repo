# Review decisions

Approved items from the design review. Phase 3 builds from this list.

| # | Date | Decision |
|---|---|---|
| 1 | 2026-10-21 | Interaction: click on the symbol opens the dynamic window; in touch mode (useButton = false) double-click/tap sends the manual command for two-state devices only (T_DValve, T_Motor), when in Manual, available, not interlocked/local/faulted; per-template `dblCmd` param (default true). Click target = symbol bounding box, min 44 px. |
| 2 | 2026-10-21 | Each screen view has a `defaultDock` param; dock close button reopens it (`efc.ui.closeDynamic`). |
| 3 | 2026-10-21 | Docks follow screen-layout-standard: right, 800 px wide at 4K (400 px / 37.04 vh at 1080p). Height pending header size. |
| 4 | 2026-10-21 | Station dock id `dw_Station`; view moves to `Docks/Station`, resized to 400 px wide. CHANGELOG upgrade note for the id and path. |
| 5 | 2026-10-21 | Role hierarchy Guest < Operator < Maintenance < Supervisor < Engineer < Admin, stored as one session level at login. MAINT / OOS mode buttons: Maintenance+. Bypass: Supervisor+. |
| 6 | 2026-10-21 | Docks show a small history (8 h state strip + last events). |
| 7 | 2026-10-21 | Named permissives / interlocks: embed `Perm : T_Intlk` / `Intlk : T_Intlk` in T_DValve, T_Motor, T_VFD (both) and T_CValve, T_PID (Intlk); equipment modules get `Prot : T_Intlk`. Existing Inp_IntlkOK / Inp_PermOK kept and ANDed. Shared `Parts/IntlkList` view. Add `Sts_BypLeft : ARRAY[0..15] OF TIME` to T_Intlk; bypass audit trail logged in Ignition (user, time, condition). |
| 8 | 2026-10-21 | dw_ValveDiscrete rev 2 approved. |
| 9 | 2026-10-21 | Fix 7: `alignItems: stretch` on AnalogIndicator flex containers (zone bars collapse otherwise). |
| 10 | 2026-10-21 | Bypass UI: each bypassed condition shows its own time left (`Sts_BypLeft[n]`) and an audit line (user, role, time, reason). Bypass button (Supervisor+) opens `Docks/Parts/BypassConfirm`: duration presets up to `Cfg_BypassMax`, reason required, logged to the Ignition audit log; BYPASS also needs `Inp_BypassPerm`. |
| 11 | 2026-10-21 | Agitator and compressor templates bind to T_Motor or T_VFD depending on how the drive is controlled (template param `tType`); dock follows: dw_Rotating or dw_VFD. T_Agitator / T_Compressor not used until a use case appears. |
| 12 | 2026-10-21 | Analog valve manual presets 0 / 25 / 50 / 75 / 100 % approved. JOG is Maintenance+. |
| 13 | 2026-10-21 | Uniform dock buttons. Command tier (mode AUTO/MAN/MAINT/OOS, OPEN/CLOSE, START/STOP, RESET, JOG, FWD/REV): one size (72 x 30 px at 1080p), `Button/Default`, the current state highlighted with `Button/Toggle/On`. Secondary tier (BYPASS, UNBYP, ACK, RESET LATCHED, RESET MAINT, SIMULATE, presets): one smaller size, `Button/Small`. `Button/Danger` only for the confirm action in BypassConfirm. |
| 14 | 2026-10-21 | Alarm-limit changes: Engineer+. Shelving: Supervisor+. Both written to the audit log. Configuration / tuning edits: Engineer+, audit-logged (old -> new, user, time); sections collapsed by default. |
| 15 | 2026-10-21 | Retire `Templates/Loops/Popups/LoopConfig`; tuning lives in dw_Loop. |
| 16 | 2026-10-21 | Every dock graph has an expand button: `Docks/Parts/TrendExpanded`, about half the screen (960 x 540 at 1080p), range buttons 5 m / 30 m / 1 h / 8 h / 24 h, pause / live. Default range 30 min everywhere. |
| 17 | 2026-10-21 | New type `T_Heater` (types/gen_pclib.py): `Cfg_CtrlType` 0 = on/off contactor, 1 = time-proportioned SSR on a PLC output (duty % of `Cfg_CycleTime`, `Cfg_MinPulse`), 2 = SCR power controller via analog reference (burst / single-cycle / phase angle set in the controller). Series isolating contactor always present; independent hardwired excess-temperature limit is monitored only (`Inp_HiLimitOK`); current monitoring for partial load failure and shorted SSR/SCR. `Heater_Electric` binds to T_Heater; new dock `dw_Heater`. |
| 18 | 2026-10-21 | Controls Standard text is never edited directly. When a decision needs standard text, a background subagent (model: Haiku) writes a Cowork instruction file `steward/proposals/CS-REV-<rev>-<topic>-instructions.md` (exact edits against the latest revision in Drive `Claude/Controls Standard`) and a row in `steward/DOC-QUEUE.md`; the main session continues the library work. Agent definition: `.claude/agents/doc-steward.md`; process: `controls-standard` skill, `references/change-queue.md`. At the end of the library work the queue is compiled into one batch instruction file. |
