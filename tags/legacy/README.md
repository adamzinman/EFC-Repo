# Legacy (pre-EFCLib v1) UDT definitions

The UDTs the `claude/legacy-ddt-fork` build binds to. Import the `*_UDT.json` files into **Tag Browser → Data Types**
(`MEM_Interlock_List` before `DDT_Valve`, which embeds it). `tools/check_bindings.py` checks every binding in
`projects/EFC_Library` against these files.

| File | Type | Members | Source |
|---|---|---|---|
| `DDT_Valve_UDT.json` | plant discrete valve (DFB_Valve), incl. memory `Name` / `Description` and `InterlockList : MEM_Interlock_List` | 27 | live RGTCR tag export |
| `DDT_Device_UDT.json` | plant running equipment (DFB_Device v0.28: pumps, compressors) | 31 | live RGTCR tag export |
| `DDT_Process_Value_UDT.json` | plant analog value with `LL` / `L` / `H` / `HH` alarm folders (SP, DB, DLY, Enabled, Alarm, Inhibit) | 49 | live RGTCR tag export |
| `DDT_Station_UDT.json` | weigh-fill station (the Station faceplates' original type) | 41 | live RGTCR tag export |
| `MEM_Interlock_List_UDT.json` | interlock list (20-entry `InterlockName[]`, `Used[]`, `Description[]`, derived `Status[]`) | 4 | live RGTCR tag export |
| `PID_ControlValve_UDT.json` | the library's own analog-valve UDT (the plant has no DDT_ for analog valves) | 9 | `tags/` before commit e710de8 |
| `PID_Loop_UDT.json` | the library's own PID loop UDT (the plant's `PID1` UDT was never bound by the library) | 16 | `tags/PID_Loops/` before commit 8e719f8 |

The five `DDT_*` / `MEM_*` files were extracted unchanged with `tools/extract_legacy_udts.py` from
`samples/xsy-import/RGTCR_ignition_tags.json` at commit `0b91606` (a live-gateway export of the RGTCR provider).
They keep that gateway's conventions: parameters `OPC Server`, `OPC Prefix` (default `ns=2;s=0:`) and `Tag`, OPC item
paths `{OPC Prefix}{Tag}.{TagName}`, and on `DDT_Process_Value.PV` a history configuration pointing at the
`HatfieldDB` history provider (change or remove it on another gateway). The exports carry the Ignition alarms of
that gateway on `DDT_Process_Value` (`x/Alarm`, `Overrange`, `Underrange`) and `DDT_Scale`.

Demo stand-ins with the same member names (memory tags) are generated into `tags/` by the build:
`DDT_Valve_Demo`, `DDT_Device_Demo`, `PID_ControlValve` (`PID_Demo_Instances.json`), `DDT_Process_Value_Demo`
(`PV_Demo_Tags.json`), `PID_Loop` (`PID_Loops/`), and `DDT_Station_Demo` + `Station_Demo_Instances.json` (restored
from the pre-e710de8 tree).
