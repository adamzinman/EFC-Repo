# XSY tag import (Control Expert V16.2 -> Ignition 8.1)

Imports the variables that have **HMI Variable** ticked in Control Expert into the `[EFC]` tag
provider for one production line. Design and rules: [`docs/xsy-tag-import-strategy.md`](../../docs/xsy-tag-import-strategy.md).

| File | What it is | Tested |
|---|---|---|
| `xsyimport.py` | Pure planner: parse the XSY, decide what to create/extend/update/skip. No `system.*` calls. Runs in Jython 2.7 and CPython. | offline, `test_xsyimport.py` (22 tests) |
| `gateway.py` | Designer prompts, file picker, dry run, confirm, gateway apply and re-read. Jython 2.7. | **not on a gateway yet**. Lines marked `VERIFY` need checking. |
| `test_xsyimport.py` | Tests against `samples/xsy-import/` (the 2026 RGTCR export and its tag export). | run it |

## Run the tests

```
python3 tools/xsyimport/test_xsyimport.py
```

The tests cover: the HMI filter (217 of 496), refusal of an export with no HMI flags, every HMI variable
accounted for exactly once, arrays and I/O card types skipped with a reason, nested UDTs created before their
parents, a second run changing nothing, a tag moved by hand not being duplicated, and blank PLC comments never
blanking Ignition text.

## Install on the dev gateway

1. Gateway scripting project `EFC_Tools` (or change `PROJECT` in `gateway.py`).
2. Project Library: `efc/xsyimport.py` = copy of `xsyimport.py`; `efc/xsyimport_gw.py` = copy of `gateway.py`.
3. Gateway Events > Message handler `xsyImport` that returns `efc.xsyimport_gw.handle(payload)`.
4. Designer Script Console: `from efc import xsyimport_gw` then `xsyimport_gw.designerRun()`.

## Run

1. Enter the production line (three digits, e.g. `058`).
2. Enter the OPC server name for that line.
3. Pick the `.XSY` (the report is saved next to it as `<name>_<line>_<date>_report.txt`).
4. Read the report. Nothing has been written yet.
5. Confirm. The gateway applies the plan and re-reads it. The summary shows anything left.

## Rules the planner follows

- **Only HMI variables** are imported. A DDT variable brings its whole structure.
- **New tags** go to `<line>/imported/`. Moving them by hand is fine: they are found by PLC name next run.
- **New UDTs** go to `_types_/<line>/`. Each line has its own copies. Nested types are created first.
- **Existing UDTs** are extended only: missing members are added. Members that differ, or that are no longer in the
  PLC, are reported, never changed or deleted.
- **Existing tags** are matched by PLC identity (instance `Tag` parameter, or the atomic OPC item name), anywhere
  under `<line>/`. Type or data-type differences are reported as conflicts and not changed.
- **Documentation:** a non-empty PLC comment overwrites the Ignition description. A blank comment never does.
- **Skipped, with a reason:** arrays (not mapped in v1), I/O card types (`T_U_*`, not defined in the export),
  types outside the v1 mapping (BYTE, LREAL, ...), and any UDT that depends on a skipped type.

## Open points (see the strategy doc)

- UDT name is the XSY DDT name. The interface contract says `T_` names. Decision needed.
- OPC item path is `ns=2;s=0:<name>`. The live tags also use `nsu=...;s=0:<name>`. Confirm.
- Arrays of DDTs (`Station`, `Scale`, `Spare_Valve`) are reported, not built.
