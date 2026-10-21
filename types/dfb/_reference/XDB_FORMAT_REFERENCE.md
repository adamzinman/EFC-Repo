# XDB format reference (derived from `DFB_Device.XDB`)

Source: `DFB Converter Prompt/DFB_Device.XDB`, 322 lines, exported by Control Expert V16.2. All line numbers (`L<n>`) refer to that file. Anything not in the sample is marked **UNVERIFIED (not in sample)**.

## 0. Byte-level facts (verified with a script)

| Property | Observed |
|---|---|
| Encoding | declared UTF-8; file is pure ASCII; no BOM (starts with `<?xml`) |
| Line endings | **CRLF (`\r\n`) on every line**, 322 of 322. Final line `</FBExchangeFile>` is followed by `\r\n`. |
| Indentation | **TAB characters** (1429 tabs, no leading spaces). One tab per nesting level. |
| Trailing whitespace | none |
| Empty elements | always **explicit close tags** `<x ...></x>`; self-closing `<x/>` never appears |
| Attribute quoting | double quotes only |

## 1. File skeleton

L1 verbatim:
```
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
```
Root: `<FBExchangeFile>` (L2, no attributes) ... `</FBExchangeFile>` (L322).

Element tree in order (R = required in sample, 1 = exactly once, * = repeated):
```
FBExchangeFile
  fileHeader            (1, L3)  attrs only
  contentHeader         (1, L4)  attrs only
  FBSource              (1, L5-279)  one DFB type
    attribute           (3, L6-8)    type-level attributes
    inputParameters     (L9-28)
      variables *       (+ child attribute PositionPin)
    inOutParameters     (L29-33)
      variables *
    publicLocalVariables   (L34-40)
      variables *
    privateLocalVariables  (L41-49)
      variables *
    FBProgram *         (2: L50-74 ST, L75-278 LD)  = "sections"
      STSource | LDSource
  DDTSource *           (2, L280-313, L314-321) one per DDT used by the DFB
    attribute           (1)
    structure
      variables *
```
Order of variable-class blocks in sample: input, inOut, public, private. **No `outputParameters` block exists in this DFB** (see section 4). Order of top-level children: fileHeader, contentHeader, FBSource, DDTSource, DDTSource.

## 2. Elements and attributes

| Element (line) | Attribute | Observed value | Notes |
|---|---|---|---|
| `fileHeader` L3 | `company` | `Schneider Automation` | constant |
| | `product` | `Control Expert V16.2 - 250430` | constant (version + build). `250430` is presumably a build/date tag (UNVERIFIED meaning). |
| | `dateTime` | `date_and_time#2026-10-21-14:6:8` | export time. **Date zero-padded? NO**, see below |
| | `content` | `Function Block source file` | constant |
| | `DTDVersion` | `41` | constant |
| `contentHeader` L4 | `name` | `RGTCR` | project/application name the DFB was exported from (UNVERIFIED meaning; likely the project name) |
| | `version` | `0.0.379` | project version, 3 dot-separated ints |
| | `dateTime` | `date_and_time#2026-2-4-12:11:13` | same non-padded format as fileHeader |
| `FBSource` L5 | `nameOfFBType` | `DFB_Device` | the DFB type name |
| | `version` | `0.28` | **2-part** version, two-digit minor |
| | `dateTime` | `dt#2026-03-12-15:26:01` | **zero-padded** `dt#` format |
| `DDTSource` L280 | `DDTName` | `DDT_Device` | |
| | `version` | `0.09` | 2-part, zero-padded minor |
| | `dateTime` | `dt#2026-02-11-11:08:12` | zero-padded |
| `DDTSource` L314 | `DDTName`,`version`,`dateTime` | `DDT_Mode`, `0.03`, `dt#2025-11-20-11:17:59` | |

### Date/time formats (exact)
| Where | Prefix | Pattern | Examples | Padding |
|---|---|---|---|---|
| `fileHeader@dateTime`, `contentHeader@dateTime` | `date_and_time#` | `YYYY-M-D-H:M:S` | `2026-10-21-14:6:8`, `2026-2-4-12:11:13` | **NOT padded** (month, day, hour, min, sec as plain ints; `6`, `8`, `2`, `4`) |
| `FBSource@dateTime`, `DDTSource@dateTime` | `dt#` | `YYYY-MM-DD-HH:MM:SS` | `2026-03-12-15:26:01`, `2026-02-11-11:08:12` | **zero-padded** |

Python: `f"date_and_time#{t.year}-{t.month}-{t.day}-{t.hour}:{t.minute}:{t.second}"` and `t.strftime("dt#%Y-%m-%d-%H:%M:%S")`. 24-hour clock (14, 15 seen). Whether hour 0 prints `0` is UNVERIFIED (not in sample).

## 3. Checksums (RISK)

| Location | Attribute | Value | Meaning |
|---|---|---|---|
| FBSource L6 | `TypeCodeCheckSumString` | `088A` | 4 hex chars, uppercase. Presumably a checksum of the DFB code. |
| FBSource L7 | `TypeSignatureCheckSumString` | `FB2C` | 4 hex chars. Presumably checksum of the DFB interface/signature. |
| FBSource L8 | `UseNewTplSignAlgo` | `TRUE` | flag: which signature algorithm; keep `TRUE`. |
| DDTSource L281 | `TypeSignatureCheckSumString` | `40A7` | DDT signature (DDT has no CodeCheckSum) |
| DDTSource L315 | `TypeSignatureCheckSumString` | `08B5` | |

The algorithm is **not in the sample and cannot be inferred from one data point per type**. A generator cannot compute them.

**RISK / unknown:** Control Expert may (a) recompute and ignore them, (b) reject/warn on mismatch, or (c) accept an import with the attributes absent. None of these is verified. Recommendation (UNVERIFIED, to be tested on the pilot import, in this order): 1) emit a file with the attributes **omitted**; 2) if refused, emit copies of the sample values (`088A`/`FB2C`/`40A7`) as placeholders; 3) if Control Expert reports mismatch, export the imported DFB from Control Expert and read back the values it assigns. Make this a generator option (`--checksums omit|copy|value`). A DDT that is only referenced and already present in the target project probably needs no `DDTSource` at all (unverified; see section 11).

## 4. Variable classes

Common shape: `<variables name="X" typeName="T">` with optional child `<attribute>`; always explicit close. Attribute order: `name` then `typeName`. Interface variables are children of the class block, tab-indented one level deeper.

| Class | In sample? | Variable children | Notes |
|---|---|---|---|
| `inputParameters` | yes L9-28 | `attribute name="PositionPin" value="N"` | |
| `inOutParameters` | yes L29-33 | same | |
| `publicLocalVariables` | yes L34-40 | none (empty element body) | |
| `privateLocalVariables` | yes L41-49 | none | |
| `outputParameters` | **NO** | | UNVERIFIED (not in sample): element name inferred by analogy only |

Verbatim snippets:
```xml
			<inputParameters>
				<variables name="Interlock" typeName="BOOL">
					<attribute name="PositionPin" value="3"></attribute>
				</variables>
```
(L9-12)
```xml
			<inOutParameters>
				<variables name="DEV" typeName="DDT_Device">
					<attribute name="PositionPin" value="1"></attribute>
				</variables>
			</inOutParameters>
```
(L29-33)
```xml
			<publicLocalVariables>
				<variables name="HMI_CMD" typeName="BOOL"></variables>
```
(L34-35)
```xml
			<privateLocalVariables>
				<variables name="Stall_TMR" typeName="TON"></variables>
```
(L41, L45)

### PositionPin (pin order)
Pin position is an `<attribute name="PositionPin" value="N">` child, 1-based, shared across input/in-out/(output) pins as one sequence on the block face. Observed:

| Pin | Class | Name | Type |
|---|---|---|---|
| 1 | inOut | DEV | DDT_Device |
| 2 | **absent** | (no variable has 2; an output pin presumably used it and was deleted, or gap) | UNVERIFIED |
| 3 | in | Interlock | BOOL |
| 4 | in | Estop | BOOL |
| 5 | in | FB_Enb | BOOL |
| 6 | in | Sys_Auto | BOOL |
| 7 | in | Sys_Man | BOOL |
| 8 | in | Sys_Off | BOOL |

Document order of inputs matches ascending PositionPin; the in-out (pin 1) is listed in its own block. Whether gaps are allowed and how outputs are numbered are not shown.

**Not present in the sample on any variable:** `topologicalAddress`, comments (`<comment>` or similar), initial values, `posParam`, alias/`%MW` addresses, arrays, EBOOL. Do not invent syntax for them. Local (public/private) variables carry no attributes at all in this sample.

## 5. Type references

| Item | Shown? | How |
|---|---|---|
| Elementary types | yes | `typeName="BOOL"`, `"INT"`, `"REAL"` |
| DDT as in-out | yes (L30) | `typeName="DDT_Device"`, name only; the DDT definition is **also embedded** as sibling `DDTSource` (L280) |
| DDT as private local | yes (L46) | `name="ModeEnum" typeName="DDT_Mode"`; DDT embedded at L314 |
| Nested FB instances | yes | `typeName="TON"` (L45, L47), `typeName="TOF"` (L48), in `privateLocalVariables`. No dedicated element; just a variable whose type is the FB name. Names `Stall_TMR`, `TON_0`, `TOF_0`. (None are called in the code; see section 8.) |
| DDT as input / output | **NO** | |
| EBOOL | **NO** | |
| Arrays | **NO** | no syntax shown |
| R_TRIG / F_TRIG | **NO** (only TON, TOF) | |
| Another user DFB as instance | **NO** | |
| DDT containing sub-DDT/array | **NO** (structures hold only BOOL/REAL/INT) | |

### DDTSource structure (L280-313)
```xml
		<DDTSource DDTName="DDT_Mode" version="0.03" dateTime="dt#2025-11-20-11:17:59">
			<attribute name="TypeSignatureCheckSumString" value="08B5"></attribute>
			<structure>
				<variables name="Off" typeName="INT"></variables>
```
(L314-317). Members are plain `variables` under `structure`. Field `name` case in DDT (`REQ` L283) differs from usage (`Dev.Req` L164, `DEV.CMD`), so identifiers are case-insensitive in code. The sample DDTs contain 28 and 3 fields. DDT_Device fields used by the DFB but **not defined** in the DDT: none verified (all `Dev.*` references exist except see section 8 notes).

## 6. Code sections

Each section is `<FBProgram name="...">` (a direct child of `FBSource`, after all variable blocks) containing exactly one language element. `FBProgram` has only the `name` attribute here (no `comment`, `task`, `type`...).

| Section | Lines | Child |
|---|---|---|
| `Runtime_Tracking` | L50-74 | `<STSource>` |
| `Commands` | L75-278 | `<LDSource nbColumns="11">` |

Section order = execution order is assumed (UNVERIFIED). Multiple sections ARE demonstrated (two, mixed ST + LD). FBD/IL/SFC not shown.

### ST body embedding (L51-73)
- **No CDATA.** Plain text, XML-escaped, as the element's text content.
- `<STSource>` ends with a newline (CRLF); the body starts at **column 0** on the next line (no added indentation); the closing tag `</STSource>` is at **column 0** on its own line (L73), after the final body line's CRLF.
- ST's own indentation uses **TABs** (one per level, from column 0).
- Blank lines in the body are completely empty (L57, L66, L68), no tab.
- Body text lines use CRLF like the rest of the file.
- Escapes seen: `<` -> `&lt;` (L53, L58). `&gt;`, `&amp;`, `&quot;`, `&apos;` do not occur in the sample (UNVERIFIED but standard XML: escape `&` first, then `<`, `>`). `>=`, `<=`, `<>` would need `&gt;`/`&lt;` (not shown). ST string literals/quotes not shown.
- Comments `(* *)` not shown. `%S6` system bit used in code (L52). REAL literals written `59.0`, `1.0`, `0.0`.

Start verbatim (L50-54):
```
		<FBProgram name="Runtime_Tracking">
			<STSource>
IF %S6 AND DEV.YI THEN
	IF DEV.Run_Sec &lt; 59.0 THEN
		DEV.Run_Sec := DEV.Run_Sec + 1.0;
```
End verbatim (L70-74):
```
		DEV.Runtime := 0.0;
		DEV.Reset_Runtime:=FALSE;
	END_IF;
</STSource>
		</FBProgram>
```
(L72 `END_IF;`, L73 `</STSource>` at col 0; body does not end with an extra blank line.)

### LD section (L76-277), structure only
`LDSource nbColumns="11"` > `networkLD` > repeated `typeLine`, then `textBox`es. Cell vocabulary seen: `emptyLine nbRows="N"`, `emptyCell nbCells="N"`, `contact typeContact="closedContact|openContact|PContact" contactVariableName="..."`, `coil typeCoil="coil|setCoil|resetCoil" coilVariableName="..."`, `HLink nbCells="N"`, `VLink` (empty), `shortCircuit` (wraps `VLink` + one `HLink`/`contact`). Each `typeLine` is one rung row of 11 cells; widths must sum to 11 (hand-check; e.g. L82-89: 1+1+1(shortCircuit)+3+1... sum rule UNVERIFIED). Text boxes (L270-275): `<textBox width="8" height="1">TEXT<objPosition posX=".." posY=".."></objPosition>` newline-tab `</textBox>`; text is inline, `objPosition` follows it directly, the close tag is on the next line. **Recommendation: a generator should emit ST sections only; LD is complex and its grid rules are not fully inferable. Copy LD verbatim if needed.**

## 7. Other blocks / attributes

| Block | Lines | What it appears to do |
|---|---|---|
| `fileHeader` | L3 | tool/product identification, DTD version 41 (import compatibility) |
| `contentHeader` | L4 | source project name/version/time |
| `attribute TypeCodeCheckSumString` / `TypeSignatureCheckSumString` / `UseNewTplSignAlgo` | L6-8 | integrity/versioning of the DFB type (section 3) |
| `attribute PositionPin` | L11 etc. | pin ordering on graphical block |

**Not present anywhere:** dataBlock, protection/password, DFB description/comment, ownership, diagnostic flag, per-variable comments, ST sections' comments, "EF/ENO" pin settings, `userDefinedAttribute`. Do not emit them.

## 8. Whitespace/formatting conventions

- Indent: 1 tab per depth. `FBExchangeFile` children at 1 tab, `FBSource` children at 2, `variables` at 4, pin `attribute` at 5.
- Leaf and empty elements: one line, `<attribute name=".." value=".."></attribute>`.
- Elements with children: open tag, newline, children, close tag on its own line at the parent's indent.
- Attribute order: as listed in section 2 (`name`, `typeName`; `attribute name` before `value`).
- Text-only: `STSource` (above) and `textBox` (LD).
- CRLF everywhere.

## 9. Generator checklist

1. Open files in binary/`newline=""` mode; write `\r\n` after every line, including the last.
2. Write the declaration exactly: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`, no BOM, ASCII-safe output (escape non-ASCII or test).
3. Indent with tabs only (depth as in the tree in section 1).
4. Always write `<x ...></x>` for empty elements; never `<x/>`.
5. Attribute order: copy the order in section 2; double quotes; XML-escape attribute values (`&`, `<`, `"`).
6. `fileHeader` constants: `company="Schneider Automation" product="Control Expert V16.2 - 250430" content="Function Block source file" DTDVersion="41"`.
7. `fileHeader`/`contentHeader` `dateTime`: `date_and_time#Y-M-D-H:M:S`, **no zero padding**. `FBSource`/`DDTSource` `dateTime`: `dt#YYYY-MM-DD-HH:MM:SS`, zero padded.
8. Version strings `MAJOR.MINOR` for types (`0.28`, `0.09`: minor two digits in sample); `contentHeader@version` three-part.
9. Emit the three FBSource `attribute` lines first (L6-8) per checksum policy (section 3); expose it as a switch.
10. Emit variable blocks in this order: inputParameters, inOutParameters, publicLocalVariables, privateLocalVariables. Omit a block when empty (outputParameters is absent in the sample; whether an empty block is tolerated is UNVERIFIED). Output-block placement is UNVERIFIED.
11. Each input/in-out variable: child `PositionPin` attribute with unique, ascending 1-based numbers. Locals: no children.
12. For every DDT type used by the DFB (in any variable), also emit a `DDTSource` after `FBSource` (the sample does this for both DDTs); members under `structure`.
13. ST sections: `<FBProgram name="..."><STSource>`, CRLF, body at column 0 (tabs inside the body for structure), `</STSource>` at column 0, then `</FBProgram>`.
14. Escape the ST body with `&` -> `&amp;`, `<` -> `&lt;`, `>` -> `&gt;` (in that order; `&lt;` is the only escape verified in the sample). No CDATA. Use `xml.sax.saxutils.escape`.
15. Normalise ST newlines to CRLF; blank lines contain no whitespace; no trailing spaces.
16. Use REAL literals with a decimal point (`59.0`) as the sample does; keep identifier spelling consistent with declarations.
17. Keep the file to the verified element vocabulary; never introduce unverified elements without a pilot test.

## 10. Annotated template (ST-only DFB)

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<FBExchangeFile>
	<fileHeader company="Schneider Automation" product="Control Expert V16.2 - 250430" dateTime="date_and_time#{NOW_UNPADDED}" content="Function Block source file" DTDVersion="41"></fileHeader>
	<contentHeader name="{PROJECT_NAME}" version="{PROJECT_VER_X.Y.Z}" dateTime="date_and_time#{NOW_UNPADDED}"></contentHeader>
	<FBSource nameOfFBType="{DFB_NAME}" version="{X.YY}" dateTime="dt#{NOW_PADDED}">
		<!-- CHECKSUM RISK: omit / copy / value per pilot test; remove these 3 lines for "omit" -->
		<attribute name="TypeCodeCheckSumString" value="{CODE_CS}"></attribute>
		<attribute name="TypeSignatureCheckSumString" value="{SIG_CS}"></attribute>
		<attribute name="UseNewTplSignAlgo" value="TRUE"></attribute>
		<inputParameters>
			<!-- repeat -->
			<variables name="{IN_NAME}" typeName="{TYPE}">
				<attribute name="PositionPin" value="{PIN}"></attribute>
			</variables>
		</inputParameters>
		<inOutParameters>
			<variables name="{IO_NAME}" typeName="{TYPE_OR_DDT}">
				<attribute name="PositionPin" value="{PIN}"></attribute>
			</variables>
		</inOutParameters>
		<publicLocalVariables>
			<variables name="{NAME}" typeName="{TYPE}"></variables>
		</publicLocalVariables>
		<privateLocalVariables>
			<variables name="{NAME}" typeName="{TYPE_OR_FB}"></variables>
		</privateLocalVariables>
		<FBProgram name="{SECTION_NAME}">
			<STSource>
{ST_BODY_ESCAPED_TABS_CRLF}
</STSource>
		</FBProgram>
	</FBSource>
	<!-- repeat per DDT used -->
	<DDTSource DDTName="{DDT_NAME}" version="{X.YY}" dateTime="dt#{NOW_PADDED}">
		<attribute name="TypeSignatureCheckSumString" value="{DDT_SIG_CS}"></attribute>
		<structure>
			<variables name="{FIELD}" typeName="{TYPE}"></variables>
		</structure>
	</DDTSource>
</FBExchangeFile>
```
(The `<!-- -->` lines are annotations only; do not emit. `{ST_BODY...}` must end with CRLF and be followed directly by `</STSource>`. No XML comments appear in the sample.)

## 11. Not demonstrated / open questions (do NOT assume; test on pilot)

- **Checksums**: algorithm unknown; accept/recompute/reject behaviour unknown (section 3).
- **outputParameters**: absent; element name, order relative to others, and pin numbering unverified. Gap at PositionPin 2.
- **EBOOL** pins/vars, **arrays**, DDT as input or output, IN_OUT of elementary type, `R_TRIG`/`F_TRIG`/other FB instances (only TON/TOF declared), instances of user DFBs.
- Variable comments, initial values, `topologicalAddress`, aliases, attributes on locals.
- **DDT dependency**: sample embeds full `DDTSource` for each DDT used. Unknown whether import tolerates a missing `DDTSource` when the DDT already exists in the project, or whether a differing existing DDT is overwritten/conflicts. Test with both.
- Re-import over an existing DFB of the same name and version; what version/date gates apply.
- Empty variable blocks or empty DFB with no sections.
- `contentHeader@name` significance (project name match?).
- Special characters (`>`, `&`, quotes, `'`) in ST, comments `(* *)`, strings; non-ASCII.
- Multiple ST sections (only 1 ST + 1 LD shown), section ordering semantics, other languages.
- Hour 0 formatting in `date_and_time#`.
- Is `Dev.Auto_Perm`-style case mismatch (`DEV` vs `Dev`) in LD accepted: yes in sample (exported by tool).

## Appendix A: observed style (NOT requirements)

### DFB_Device interface (observed style)
| Pin | Class | Name | Type |
|---|---|---|---|
| 1 | InOut | DEV | DDT_Device |
| 3 | In | Interlock | BOOL |
| 4 | In | Estop | BOOL |
| 5 | In | FB_Enb | BOOL |
| 6 | In | Sys_Auto | BOOL |
| 7 | In | Sys_Man | BOOL |
| 8 | In | Sys_Off | BOOL |
| - | Public | HMI_CMD BOOL, Mode INT, Runtime REAL, Reset_Runtime BOOL, Motor_Stalled BOOL | |
| - | Private | Run_Hour, Run_Min, Run_Sec REAL; Stall_TMR TON; ModeEnum DDT_Mode; TON_0 TON; TOF_0 TOF | |

`DDT_Device` (L282-312): REQ, Auto_Perm, Man_Perm, HMI_Auto/Manual/Off/Lockout, CMD, YI, YIF, HMI_CMD, Interlock, FB_Enb, Alarm, Warning, Auto, Manual, Off, LockedOut (BOOL); Run_Sec/Min/Hour, Runtime (REAL); Reset_Runtime, Enable_Stalling (BOOL); Comp_Ratio, Curr_Comp_Ratio (REAL); Stall_Time (INT); Stalled (BOOL). `DDT_Mode`: Off, Auto, Manual (all INT).

### What the code does (observed style)
Section `Runtime_Tracking` (ST): once per `%S6` pulse while `DEV.YI` (running feedback) is true, it increments `DEV.Run_Sec` to 59, rolls into `DEV.Run_Min`, then `DEV.Run_Hour`; computes `DEV.Runtime = Run_Hour + Run_Min/60.0` and clears it when `DEV.Reset_Runtime` is set (which it then resets). Note the bug-like use of unqualified `Run_Min`/`Run_Hour` (the DFB's private variables, L59, L62) in `DEV.Run_Min := Run_Min + 1.0`, mixing local and DDT members. Section `Commands` (LD, text boxes: "Permissive Control", "Mode control for the Device", command rung): permissives `Dev.Auto_Perm`/`Dev.Man_Perm` from `Estop`/`Interlock` (NC contacts); mode set/reset latches (`Dev.Auto`/`Manual`/`Off`/`LockedOut`) driven by rising-edge `PContact`s on HMI bits (`Dev.HMI_Auto` etc.) and system bits (`Sys_Auto`, `Sys_Man`, `Sys_Off`), lockout resets the other modes; `Dev.CMD` coil from `Dev.Req` with auto/permissive or HMI_CMD/manual/permissive paths, with HMI_CMD reset on Interlock/Estop. Style notes: DDT-centred device struct passed IN_OUT as pin 1 named `DEV`; `Sys_*` mode inputs; `HMI_*` command bits inside the DDT; Mixed-case names with underscores; edge detection via LD `PContact` rather than R_TRIG instances; TON/TOF/`Stall_TMR` declared but unused in sample code; Mode as INT + DDT_Mode enum-style struct.

## 12. Addendum: second sample `FB_AlmCore_reexport_16.2.XDB` (2026-10-21)

Source: `types/dfb/FB_AlmCore.XDB` written by `tools/st2xdb.py` (checksums omitted), imported into Control Expert V16.2 - 250430, then exported again. 198 lines, CRLF on every line, tabs only, no BOM, no self-closing tags. A line diff against the generated file shows only the three header differences below. Every other line (pins, blocks, locals, ST body) is byte-identical.

Now **verified** (were "not demonstrated"):

| Item | Observed (re-export line) |
|---|---|
| `outputParameters` | Element name `outputParameters`, placed **after `inputParameters`** and before `privateLocalVariables` (L56-84). Variables carry `PositionPin` like inputs. |
| Output pin numbering | Continues the input sequence: inputs 1-15, outputs 16-24 (L58-82). |
| Elementary types | `TIME` on inputs and outputs (L28, L75); `INT` output (L72). |
| Checksums | Import accepts a file with **no** `TypeCodeCheckSumString` / `TypeSignatureCheckSumString`. Control Expert computes them and writes them on export (`09AF` / `2A99`, L6-7). `--checksums omit` is the generator default. |
| ST comments | `(* ... *)` lines kept verbatim (L101-106). |
| Typed literal | `T#0S` kept verbatim (L138). |
| ST `-` operator on TIME | `MaxShelf - tonShelf.ET` (L136) accepted. |
| Multiple sections name | Section name `Main` kept (L99). |
| `FBSource@dateTime` | Kept from the imported file (`dt#2026-10-21-19:00:00`), not replaced by the import time. |

Header differences (not errors):

| Line | Generated | Re-export | Meaning |
|---|---|---|---|
| L3 `fileHeader@dateTime` | generator time | export time | written at export |
| L4 `contentHeader` | `name="EFCLib" version="1.0.0" dateTime="date_and_time#..."` | `name="Project" version="0.0.000"` **with no `dateTime`** | project the type was exported from. `dateTime` is optional; the import ignores the generator's values |
| L6-7 | absent | checksum attributes | see above |

Still not demonstrated: IN_OUT of a DDT in a generated file, DDT nested in DDT, arrays, `DT`/`UDINT`/`DINT`/`WORD`/`STRING`/`LREAL`, EBOOL, R_TRIG/F_TRIG, user DFB instances, `<comment>`/`variableInit`, `>`/`&` in ST, DDTSource omission.
