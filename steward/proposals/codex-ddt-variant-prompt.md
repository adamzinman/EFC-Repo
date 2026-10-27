# Codex prompt: DDT-style variant of the EFC Library templates and dynamic windows

You are working in the EFC-Repo (Ignition 8.1 Perspective library for Schneider M580 / Control Expert V16.2). Read `README.md`, `build.py`, `steward/type_map.json`, `steward/DECISIONS.md` (decisions 23-24) and `docs/ddt-udt-sync.md` first.

## Goal
Build an alternate version of the templates (`Templates/*`) and dynamic windows (`Docks/*`, the `dw_*` windows) that binds to **DDT-style data types** (flat PLC-style Derived Data Types, named `DDT_*`) instead of the current EFCLib v1 `T_*` types. The existing T_* project must keep building and must not change.

## Background (verified in git history)
- The library originally used DDT-style UDTs. Commits `e710de8` (devices, station) and `8e719f8` (PV, loops) moved the templates to the `T_*` types. The last state with DDT bindings is parent commit `b198bfb`.
- Only two DDT families ever had real member lists in the repo: `DDT_Station` (`tags/DDT_Station_Demo_UDT.json`, about 40 flat members) and `DDT_Process_Value_Demo` (`tags/PV_Demo_Tags.json`: PV, Name, Description, Units, Eng_Min, Eng_Max, HW_Fault, Overrange, Underrange, plus HH/H/L/LL folders each with SP, Inhibit, Enabled, DLY, Alarm). Recover them with `git show b198bfb:<path>`.
- `DDT_Valve`, `DDT_Intlk`, `DDT_PV` and `DDT_Device` appear only as names in docs and `scripts/ddtsync.py` / `scripts/test_ddtsync.py` examples. Before the conversion, valves and motors used `PID_*_UDT` types.
- The `Docks/*` dynamic windows were built after the conversion, so no DDT version of them has ever existed.
- Commit `f46fab2` removed `types/xdd/T_IOCard.xdd` and `T_IORack.xdd` in favour of the PLC's native Modicon x80 device DDTs (decision 23). Recover them with `git show f46fab2^:types/xdd/T_IOCard.xdd` if useful.

## Decisions already made by the owner
1. **Member shapes come from the owner's real DDT exports**, placed in `samples/ddt/` (Control Expert `.XDD`, `.XSY`/`.XEF`, or Ignition UDT JSON). Do not invent members for any family that has no export.
2. **Structure:** a parallel project `projects/EFC_Library_DDT`, produced by the same generators with a **type-profile switch** (`T_*` vs `DDT_*`), so the two stay in sync when a template changes. Do not make a hand-edited copy of the views.

## Step 0: check the inputs
List `samples/ddt/`. If it is missing or empty, **stop and report that** and do nothing else. If only some families are present, build only those and list the rest as pending in the final report.

## Work
1. Parse the exports (reuse the parser in `scripts/ddtsync.py` where possible) and write one machine-readable map per DDT: member name, data type, nesting.
2. Add a `DDT` column to `steward/type_map.json`: for each template/dock, the DDT name and a member mapping from what the view reads or writes today (T_* member) to the DDT member. Where the DDT lacks a member the view needs, record it in `steward/GAPS.md` and make the view degrade gracefully (hide or disable that element). Do not fabricate a binding.
3. Refactor the generators (`generator/*.py`, `generator/docks/`, `generator/pid_loops/`, `generator/analog_indicators/`) so that every tag path and `T_*` reference goes through one profile lookup. There are about 34 hard-coded `T_*` references. Default behaviour must stay byte-identical for the T_* profile.
4. `imported/EFC_StationFaceplates` is imported, not generated, and was originally written for `DDT_Station`. Handle Station through the same map (rewrite bindings at build time), not by forking it by hand.
5. Add an `EFC_Library_DDT` target to `build.py` (output `projects/EFC_Library_DDT`, gateway folder layout like `projects/EFC_Library`), and make `--check` cover it.
6. Generate demo UDT and instance JSON for the DDT profile under `tags/` (prefix `DDT_`, from the real exports) so the demos work.
7. Render previews for the DDT variant with the existing preview tooling and write a short `docs/ddt-variant.md`: what is covered, the member mapping, the gaps, and how to import it into a gateway.

## Constraints
- `python3 build.py --check` must pass for both projects, and regenerating the T_* project must produce no diff in `projects/EFC_Library`.
- Follow the existing style: EFC_Styles classes only, no new inline styles beyond what the T_* views use, 8.1-compatible JSON (`generator/check_81.py`).
- Do not edit `types/xdd/*` or the Controls Standard. If the standard needs a change, add an instruction file under `steward/standard-edits/` as the repo already does.
- Add an entry to `CHANGELOG.md` and `steward/DECISIONS.md` for the profile switch.
- Do not commit or push unless asked. Leave the work in the working tree.

## Done means
- `samples/ddt` inputs were found (or you stopped at Step 0 and said so).
- Both projects build and pass `--check`; the T_* output is unchanged.
- Every template and dock is either bound to a real DDT member or listed in `steward/GAPS.md` with the missing member.
- Final report lists: families covered, families pending, gaps, files changed, and the commands you ran.
