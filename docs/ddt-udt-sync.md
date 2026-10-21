# DDT → UDT sync (M580 through a BMENUA0100 OPC UA card)

[`scripts/ddtsync.py`](../scripts/ddtsync.py) is a gateway script. It browses an M580 through its NUA (BMENUA0100) OPC UA connection, works out every DDT, and then:

| Case | What happens |
| --- | --- |
| No UDT with the DDT's name yet | A new UDT is created in `[provider]_types_/<typesFolder>` with every member. Members are OPC tags bound to `{BasePath}` + member path, with server `{OPCServer}`. |
| UDT already exists | Only the members that are missing are added. They follow the UDT's own OPC path pattern, which is learned from one of its existing OPC members. |
| Member already in the UDT | Ignored. It is never changed, even if its data type differs. |
| UDT member no longer in the PLC | Ignored. It is never deleted. |

Writes use `system.tag.configure(..., "i")` (collision policy *ignore*), so no existing member can be overwritten. Instances are not created or changed.

## Install
1. In the Designer, open **Project Library**. Create a script named `ddtsync` in the gateway scripting project (Config → Gateway Settings → Gateway Scripting Project) and paste in `scripts/ddtsync.py`.
2. Find the node that holds the PLC variables. In the Designer OPC browser, open the NUA connection and copy the node id of the folder above the variables. That is `rootNode`.

## Run
Run it once as a dry run. In the Script Console, the browse goes through the Designer, which works the same way:

```python
r = ddtsync.run(opcServer="M580_NUA", provider="EFC", rootNode="ns=2;s=", typesFolder="PLC",
                typeNames={"re:^AV\\d+$": "DDT_Valve"}, dryRun=True)
print r["text"]
```

The report lists `NEW`, `EXTENDED` (with the members to be added), `UP TO DATE`, `SKIPPED` (with the reason), `NO NAME` and warnings. When the report looks right, run it again with `dryRun=False`. For a large PLC, run it on the gateway from a Gateway Message Handler with `ddtsync.runAsync(...)`. The report then goes to the gateway log under `DDTSync`.

## DDT names
Ignition's OPC browse returns variables but not OPC UA type definitions. The script therefore reads each DDT's layout (its members and data types) from the PLC instances, and gets the DDT's name from these sources, in order:

1. **`typeNames`**: an exact variable name (`"PT001": "DDT_PV"`), a regex (`"re:^AV\\d+$": "DDT_Valve"`), or a nested member (`"DDT_Valve.Intlk": "DDT_Intlk"`).
2. **`variablesExport`**: a path on the gateway to a Control Expert export (`.XEF`, `.ZEF` or `.XSY`). Its `typeName` attributes and `<DDTSource>` blocks name every variable and nested DDT, so `typeNames` is rarely needed.
3. **Existing UDT instances** (`scanInstances=True`): an instance whose parameter holds the PLC variable name or node id gives its UDT type. DDTs already mapped in Ignition need nothing.
4. **Same layout**: an unnamed instance with exactly the same members as a named one gets that name.

Any layout that is still unnamed shows up under `NO NAME` with the variables that use it. To fix it, add one of those variables to `typeNames`, or pass `unresolved="auto"` to name it `DDT_<variable>`.

## Options
| Option | Default | Meaning |
| --- | --- | --- |
| `include` / `exclude` | none | Regex on top-level variable names. Use `exclude` for DFB instances, which also appear as structures. |
| `nestedAsUdt` | `True` | A named nested DDT becomes a UDT instance member, with its `BasePath` bound to the parent path. When `False`, or when the nested DDT has no name, it becomes a folder. |
| `pathParam` / `serverParam` | `BasePath` / `OPCServer` | Parameter names used on new UDTs. |
| `elementName` | `_{index}` | Tag name for each element of an array that is exposed element by element (`Used[3]` becomes `Used/_3`). |
| `fallbackDataType` | `Int4` | Data type used when the browse reports none. Each use is listed as a warning. |
| `maxDepth` / `maxStructDepth` | 6 / 12 | How deep to recurse into folders and into nested structures. |

## Limits
- Member OPC paths have to extend the instance node id, as BMENUA string ids do (`ns=2;s=AV001` → `ns=2;s=AV001.Auto`). Numeric node ids can't be parameterized, so those types are reported as `SKIPPED`.
- An existing UDT is extended only if the script can tell how it builds OPC paths: either an atomic member with a parameter-bound `opcItemPath` that matches its PLC member, or a `{BasePath}` parameter. Otherwise it is reported as `SKIPPED`.
- Arrays that the server exposes as a single array value become a single array tag, for example `BooleanArray`.
- Tested offline against a mock gateway (`python3 scripts/test_ddtsync.py`). It has not yet been run against a live BMENUA0100, so do a dry run first.
