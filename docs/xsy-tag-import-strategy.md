# XSY → Ignition tag import (Control Expert Classic V16.2 → Ignition 8.1)

**Status (v2, 2026-10-21):** planner and gateway glue built in `tools/xsyimport/`. The planner is tested offline
against the sample export (47 tests). The gateway glue has **not run on a gateway** yet; its `VERIFY` lines
need checking on the dev gateway. Samples are in `samples/xsy-import/`.

Code: [`tools/xsyimport/`](../tools/xsyimport/README.md) (`xsyimport.py`, `gateway.py`, `test_xsyimport.py`).

Related: [`scripts/ddtsync.py`](../scripts/ddtsync.py) is merged on `main`. It adds missing members to existing UDTs from the live PLC. See §11.

## 1. Requirements

| # | Requirement | Met by |
|---|---|---|
| R1 | Script lives on the gateway and runs from the Designer | `gateway.py` (`designerRun`, gateway `handle`) |
| R2 | Prompts for the tag provider (one provider per project; no line folder) | §4 step 1 |
| R3 | Lists the new UDTs and new tags before writing anything | dry run and report, §4 |
| R4 | New UDTs go flat in the provider's `_types_` folder | §6 |
| R5 | Opens a file browser; a required location is the fallback | §4 step 3 |
| R6 | New tags go in group folders by UDT type under the provider root | §6 |
| R7 | Only variables with **HMI Variable** set in the PLC | §5 |
| R8 | Re-runnable; updates existing tags and UDTs safely | §7 |
| R9 | **OPC server name is asked for at run time** | §4 step 2 |

## 2. What the run does

```
Designer                                   Gateway (xsyimport_gw.handle)
────────                                   ─────────────────────────────
tag provider (R2)
OPC server name (R9)
pick .XSY (R5)
sendRequest(dryRun) ──────────────────────▶ read [prov] and [prov]_types_
                                            parse XSY, plan (pure, tested)
report saved next to .XSY  ◀──────────────  report + counts (nothing written)
confirm
sendRequest(apply) ───────────────────────▶ create / extend / update (i, i, m)
                                            re-read, return what is left
summary  ◀─────────────────────────────────
```

Ignition is the state. There is no state file. Running twice in a row changes nothing the second time.

## 3. Reading the XSY (verified against the 2026 RGTCR export)

- **HMI flag:** `<attribute name="IsVariableHMI" value="-1"/>` on a top-level `dataBlock` variable. `-1` is TRUE.
  The export has 496 top-level variables, 217 flagged. A flagged DDT exposes its whole structure.
- **Export refusal:** if the file has no `IsVariableHMI` attribute at all, the run stops. It never imports everything.
- **DDT definitions:** `DDTSource/@DDTName` with `structure/variables` (name, `typeName`, `comment`). 51 in the sample.
- **FB definitions:** `FBSource/@nameOfFBType` with `inputParameters`, `outputParameters` and
  `publicLocalVariables`. **The export does contain FB member layouts** (correction to v1 of this doc).
  14 in the sample, e.g. `DFB_TMR` with `IN`, `PT`, `ET`, `Q`.
- **Types the sample uses that are not in the export:** the Modicon I/O card types (`T_U_ANA_STD_IN_8`,
  `T_U_DIS_STD_IN_16`, `T_U_DIS_STD_OUT_16`). They come from the library, so they are skipped with a reason.

## 4. Run flow

1. **Tag provider** (R2): each project has its own provider. The Designer reads `system.tag.getProviders()` and
   asks with `system.gui.inputBox`, listing the available names. A name not in the list is refused. Every path in
   the run is built from `[provider]`. (VERIFY: return type of `getProviders()` on 8.1.)
2. **OPC server** (R9): the OPC UA connection name, typed each run. Written into every new tag and every UDT
   instance's `OPC Server` parameter. Never guessed.
3. **File** (R5): `system.file.openFile` in the Designer. The bytes are sent base64 in the payload. A fallback
   gateway folder for runs without a Designer is still to be built (open point).
4. **Dry run:** the report goes to the Designer console and is saved as
   `<name>_<provider>_<date>_report.txt` next to the file. Counts are shown in the confirm box.
5. **Apply** (only after confirm, and only for users with the `Engineering` role): `system.tag.configure` with
   `"i"` (never overwrite) for creates and extends, `"m"` for documentation. The gateway re-reads and reports
   what is left.

## 5. Mapping

| XSY | Ignition | Where |
|---|---|---|
| DDT `X` (used by an HMI variable) | UDT `X`: members from `structure`; atomic members; nested DDTs as nested UDT instances | `[prov]_types_/X` (flat) |
| FB `F` (used by an HMI variable) | UDT `F` from input, output and public variables | `[prov]_types_/F` (flat) |
| HMI variable of DDT/FB type | UDT instance, `typeId` `X` (plain name), parameters `OPC Server` and `Tag` only | `<group(X)>/` |
| HMI variable of elementary type | atomic OPC tag, `opcItemPath` = `ns=2;s=0:<name>`, `opcServer` = the prompt | `Other/` |
| Comment | Documentation | same object |

Elementary types (contract v1.0): BOOL/EBOOL → Boolean, INT → Int2, UINT/WORD/DINT → Int4,
UDINT/DWORD → Int8, REAL → Float4, STRING[n] → String, TIME → Int4.

**Arrays (v2):** an array of an elementary type becomes one array tag (`Int2Array` etc.); a `BYTE` maps to
`Int2` (unsigned 8-bit values stay intact, as in `ddtsync`), and `SINT`, `USINT`, `LINT` and `LREAL` map
similarly. An array of a DDT (`Station`, `Scale`, `Spare_Valve`) becomes a folder of instances, one per index:
`Stations/Station/_1` … `_6`, with `Tag` = `Station[1]`. Arrays inside a UDT member that are not elementary
(an array of structures) are still skipped and reported.

**I/O card types (v2):** the `T_U_*` device types are not in the export. The web lookup did not confirm a
member layout (see `tools/xsyimport/library_types.py`), so they stay skipped with a reason until a confirmed
layout is entered from the Control Expert project. Anything not confirmed is never used.

**Member bindings** follow the live convention:
- `OPC Prefix` = `ns=2;s=0:` (default), `OPC Server` = blank, `Tag` = blank on each UDT
- atomic member item path: `{OPC Prefix}{Tag}.{TagName}`, server `{OPC Server}`
- nested instance: `OPC Prefix` = `{OPC Prefix}`, `OPC Server` = `{OPC Server}`, `Tag` = `{Tag}.<member>`

**EFCLib v1 is the type source (v3).** The data types in the sample export are examples. Where a PLC type is
an EFCLib v1 `T_*` type, the UDT layout comes from `types/xdd/T_*.xdd` (generated into
`tools/xsyimport/library_types.py` by `build_library.py`). The export's layout is used only for types EFCLib does
not define. Any member that differs between the export and EFCLib is listed under *EFCLib v1 DIFFERS FROM
EXPORT*, and the EFCLib layout is used.

Two conflicts still to decide:
- **Parameter names.** The generated Ignition JSON in `types/export/` uses `OPCServer`, `PathPrefix`, `BaseTag`.
  The interface contract v1.0 says `OPC Server`, `OPC Prefix`, `Tag`. The planner uses the contract names.
- **Type names.** The export's `DDT_*` names do not match EFCLib's `T_*` names, except by stem (`Mode`, `Station`).
  A mapping from PLC type to EFCLib type is needed for the PLC program to move onto EFCLib.

**Any UDT, any tag (v3.1).** The planner applies one rule at every level:
- a DDT or FB becomes a UDT, with each member built by the same rule (nested DDTs become nested UDT instances);
- an elementary type becomes an atomic tag; a one-dimensional array of an elementary type becomes one array tag
  (`Int2Array` etc.; `BYTE` maps to `Int2`);
- an array of anything else becomes a folder with one child per index (`_1`, `_2`, ...). Multi-dimensional arrays
  become nested folders, one level per dimension (a 2-D array of INT becomes a folder of `Int2Array` row tags);
- a top-level array's children are instances whose `Tag` is the PLC index path, e.g. `Pairs[2][2]`.

Type sources, in order: EFCLib v1 (always wins), the export itself, then any layout files the user adds. A type
that is none of these, or a type that needs one of them and cannot be built (for example a standard FB such as
`TON` inside a DDT), is skipped with the reason. Nothing is written for a partly built variable.

Parameters follow the interface contract: `OPC Prefix`, `OPC Server`, `Tag`.

## 6. Folders and naming

Each project has its own tag provider, so there is no line folder. Paths are relative to the provider root.

```
[Proj]_types_/                   UDT definitions, flat (typeId is the plain name)
  T_Motor
  DDT_Valve
  DFB_TMR
[Proj]                           provider root
  Motors/                        group folders, created if missing
    P101                           UdtInstance, typeId T_Motor, Tag = P101
  Valves/
    XV1                            UdtInstance, typeId DDT_Valve
    Spare_Valve/                   array of DDT_Valve: folder named for the variable
      _1  _2  ...
  Stations/
    Station/_1 ... _6
  Other/                         atomic tags, arrays of elementary types, UDT types no group matches
    PT101                          AtomicTag, opcItemPath ns=2;s=0:PT101
```

**Grouping.** The `groups` option is an ordered list of `(regex, folder)` pairs. Each regex is matched
(`re.match`, case-sensitive) against the UDT type name; the first match wins. Default list:

| Folder | UDT type names (regex, `re.match`, case-sensitive, first match wins) |
|---|---|
| Process Values | `^(T_AI\|DDT_Process_Value\|AI_Sensors\|PV_.*)$` |
| Motors | `^(T_Motor\|T_VFD)$` |
| Valves | `^(T_DValve\|T_CValve\|DDT_Valve\|Valve)$` |
| Digital Inputs | `^(T_DI\|DI_Sensors\|DDT_Discrete)$` |
| Pumps | `^(T_PumpDS\|T_PumpProt\|T_DosePump\|Vacuum)$` |
| Stations | `^(T_Station\|DDT_Station\|FillStn)$` |
| Scales | `^(T_Scale\|DDT_Scale\|Scale)$` |
| Tanks | `^T_Tank$` |
| Heaters | `^(T_Heater\|T_HeatEx)$` |
| Compressors | `^T_Compressor$` |
| Devices | `^(DDT_Device\|DevCtrl)$` |
| Sequences | `^(DDT_Seq\|T_Phase)$` |
| Setpoints | `^Setpoint$` |
| Units | `^(Unit\|T_Unit)$` |
| Variables | `^Variables` |
| Other | everything else: unmatched UDT types, atomic tags, arrays of elementary types |

- A UDT instance of type X goes to `<group(X)>/<name>`.
- An array of UDT goes to `<group(element type)>/<name>/_i`.
- Atomic tags and arrays of elementary types go to `Other/<name>`.
- Elementary arrays and nested UDTs inside UDT definitions are unchanged.
- The gateway glue creates the group folder (and any nested folder) if it does not exist.

**Rules**
- Nested UDTs are created before their parents.
- An existing `_types_/X` is extended, never recreated.
- **Name clash:** a tag with the same name directly in the same group folder that is not the same PLC variable.
  The variable is skipped and reported, never duplicated. Used names are tracked per folder (for example
  `Valves` -> {`DDT_V1`: `UdtInstance`}), not per provider. A folder of that name is not a clash for an array.
- Duplicate and not-in-PLC detection covers the whole provider.

## 7. Updates (R8)

| Situation | Action |
|---|---|
| Tag or instance found by PLC identity, nothing changed | counted as up to date |
| Found, PLC comment non-empty and different | documentation updated (`"m"`) |
| Found, PLC comment blank | **nothing**: Ignition text is never blanked |
| Found, `typeId` or `dataType` differs | **reported as a conflict, not changed** |
| Same PLC identity found more than once | **duplicate**, all paths listed, nothing changed |
| Existing tag whose PLC identity is no longer exposed | **not in PLC**, kept and listed, never deleted |
| Not-in-PLC tag and a new tag with the same documentation and type | **possible rename**, listed for you to act on |
| UDT exists, members missing in it | missing members added (`"i"`) |
| UDT exists, member differs or is no longer in the PLC | reported; never changed or deleted |
| Tag moved or renamed by hand | still found by PLC identity (instance `Tag`, or the atomic's OPC item name) |

Found means: anywhere in the provider. A tag moved into any folder, group or not, counts as found.

**Policy (agreed):** when a UDT already exists and the PLC adds members, the new members are added. Members that
the PLC no longer has are never deleted; they are listed. Duplicates, not-in-PLC tags and possible renames are
listed and never changed. A rename is never applied automatically; a deletion is never applied automatically.

**Not done:** changing a UDT member's data type on an existing UDT, changing an instance's type, updating OPC
bindings on existing atomic tags, and re-routing tags that were moved out of their group folder. All are reported only.

## 8. Current results (dry run against the sample export, 47 offline tests)

| Provider state | UDTs to create | Tags to create | Found | Documentation updates | Conflicts | Skipped tags / UDTs |
|---|---|---|---|---|---|---|
| empty provider | 22 | 228 | 0 | 0 | 0 | 7 / 0 |
| RGTCR tags as the provider's tags | 22 | 115 | 94 | 0 | 19 (`Setpoint` UDT instance vs REAL) | 7 / 0 (1 duplicate, 21 not in PLC) |

Group folders for the 228 new tags on an empty provider: Other 117, Valves 40, Process Values 32, Scales 12,
Digital Inputs 11, Stations 6, Sequences 6, Devices 4. The 19 conflicts are the `HMI_SP_*` setpoints. They are
reported and not changed, as agreed. The earlier per-line numbers (v2) no longer apply: there is no line folder,
and not-in-PLC and duplicate detection now cover the whole provider.

## 9. Open points

1. **UDT naming.** The XSY uses `DDT_*` and `Valve` names. The interface contract says `T_` names and
   retires `DDT_`. The import currently uses the XSY name. Decide: use the XSY name, or rename on both sides.
2. **UDT folder.** The contract says `_types_/EFCLib v1/`. The user decided one provider per project with UDTs flat
   at the `_types_` root. The planner follows the user. The contract wording needs updating.
3. **OPC item path.** `ns=2;s=0:<name>` (contract) versus the live `nsu=http://www.unifiedautomation.com/CustomServer/;s=0:<name>`
   on some tags. Confirm which the M580 publishes for each line. The `prefix` option changes it.
4. **DFB instances as UDTs.** The planner does this (`DFB_TMR`). Confirm, and confirm that the FB's
   internal members should be exposed.
5. **Arrays of DDTs.** Built as a folder of instances, `<group>/<name>/_i`.
6. **Fallback folder** for runs without the Designer (`<Ignition install>/data/efc/xsy-import/<provider>/`). Not built.
7. **Role check.** The gateway trusts the `user` field from the Designer. Confirm how the sendRequest user is
   taken on the target gateway before relying on the `Engineering` role check.
8. **Performance.** Creates and updates are one `configure` call per tag, about 300 calls for a full line.
   Fine for a dev gateway; batch if it is slow on the real one.

## 10. Build status

| Step | State |
|---|---|
| 0 Samples under `samples/xsy-import/` | done |
| 1 Pure planner, parse, rules, grouping, report | done, 47 offline tests |
| 2 Gateway and Designer glue | written, **not yet run on a gateway** (`VERIFY` lines) |
| 3 Dev gateway test: first import, move a tag, change the export, re-run | next |
| 4 User guide | `tools/xsyimport/README.md` (short); needs the gateway results |
| 5 Later: fallback folder, arrays, shared module with `ddtsync` | not started |

## 11. Relation to `ddtsync`

`ddtsync` (`scripts/ddtsync.py`, merged to `main`) browses the live PLC over OPC UA and adds
missing UDT members. This import works offline from the export and also creates instances. Both use the
same parameters (`OPC Prefix`, `OPC Server`, `Tag`), so the shared type mapping and JSON shapes can move to
one module later.
