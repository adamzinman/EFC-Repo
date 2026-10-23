# Analog channel row (AnalogRow_AI, AnalogRow_AO, AnalogRow_TEMP)

Covers `Templates/IO/Parts/AnalogRow_AI`, `AnalogRow_AO` and `AnalogRow_TEMP`. Each is one channel row of an analog card faceplate. The three differ in which cells they show and how the value is formatted.
Sources: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/IO/Parts/AnalogRow_<AI|AO|TEMP>/view.json`.
Used by: [Analog_Cards](../Faceplates/Analog_Cards.md) (`Rows` repeater). Dock: [IOCard](../../Dynamic%20Window/IO/IOCard.md) (the card-level dock; the row itself does not open anything).

## Overview

- **Default size:** 1000 x 34 (`props.defaultSize`), all three.
- **How it is embedded:** by the `Rows` flex repeater of an analog faceplate. The repeater passes `cardPath`, `ch`, `chFolder` and `alt` as the instance dict. The views are not used on their own (no `ia.display.view` points at them).
- **Generated view:** no.
- **Params:** `cardPath`, `ch`, `chFolder`, `alt` (all input).

### Differences between the variants

| Variant | Value text format (`Value`) | Bar cell (`BarCell`, "Range" header) | Flags cell (`Flags`, "Limit" header) | Lower/upper limit custom props | Bindings (view root + components) | Used by faceplate |
|---|---|---|---|---|---|---|
| `AnalogRow_AI` | span-based: no decimals at 1000 or more, else up to one decimal | yes | yes | yes (`lo`, `hi`) | 27 (13 + 14) | `BMXAMI0810` |
| `AnalogRow_AO` | fixed one decimal | yes | no | no | 24 (11 + 13) | `BMXAMO0802` |
| `AnalogRow_TEMP` | fixed one decimal | no | yes | yes (`lo`, `hi`) | 25 (13 + 12) | `BMXART0814` |

The rest of this document applies to all three. The row container, channel, loop, description, raw, units and health cells are the same in all three. Only the value text, the bar, the flags and the two limit custom props differ. The differences follow the column headers: the AO row has no Limit cell, and the TEMP row has no Range cell.

## How it operates

- **Shading.** Odd channels (`alt` true) use the `Table/RowAlt` style.
- **Channel and loop.** `Ch` shows the channel number. `Loop` shows the loop tag, "—" for a spare channel.
- **Description and raw.** `Desc` shows the description, or "Spare". `Raw` shows the raw counts from `VALUE`, blank for spare or when null.
- **Value.** Shows the scaled value (see the variant table). "FAULT" when `CH_ERROR`. The value gets the `Value/BadQuality` class when the raw quality is bad.
- **Units.** `Doc/Units`.
- **Bar (AI and AO only).** A horizontal track with a fill. The fill is the scaled value between `EngMin` and `EngMax`, clamped to 0 to 100%. The bar is hidden for spare and error channels.
- **Limit flags (AI and TEMP only).** "UNDER" when `LOWER_LIMIT` is true, "OVER" when `UPPER_LIMIT` is true. Blank otherwise.
- **Health.** "SPARE", "COMMS?" (raw quality bad), "FAULT" (`CH_ERROR`), or "OK". The tooltip shows the channel diagnostic text.
- **Writes.** None. The row only reads.

## Properties reference

### View parameters (`params`)

Same four params in all three variants, all `paramDirection: input`, `persistent: true`.

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `cardPath` | input | `""` | Card UDT path. Used to build `chPath`. | Set by: analog faceplate `Rows` repeater. Read by: `custom.chPath`. |
| `ch` | input | `0` | Channel index. | Set by: `Rows` repeater (0 to 7). Read by: `root/Ch` text. |
| `chFolder` | input | `"CH00"` | Channel folder name under the card (`CHnn`). | Set by: `Rows` repeater. Read by: `custom.chPath`. |
| `alt` | input | `false` | Odd-row shading flag. | Set by: `Rows` repeater (`ch % 2 == 1`). Read by: row style class. |

### View-level custom properties (`custom`)

Each is a tag mirror of one channel member, except `chPath` (an expression). No defaults (the `custom` block is empty). `lo` and `hi` exist in AI and TEMP only. The source is the same for every variant (`{0}` is `chPath`).

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.chPath` | unset | expr | `{view.params.cardPath} + "/" + {view.params.chFolder}` | Channel tag folder: `cardPath` + "/" + `chFolder`. Base for every channel tag read. |
| `view.custom.raw` | unset | tag (indirect) | tag `{0}/VALUE`, `{0}` = `{view.custom.chPath}` | Raw counts (`VALUE`). Used for the Raw cell and the quality test. |
| `view.custom.err` | unset | tag (indirect) | tag `{0}/CH_ERROR`, `{0}` = `{view.custom.chPath}` | Channel error (`CH_ERROR`). Drives FAULT text, the `Text/Color/Fault` class and hides the bar. |
| `view.custom.val` | unset | tag (indirect) | tag `{0}/HMI/Scaled`, `{0}` = `{view.custom.chPath}` | Scaled value (`HMI/Scaled`). Drives the Value cell and the bar fill. |
| `view.custom.loop` | unset | tag (indirect) | tag `{0}/Doc/LoopTag`, `{0}` = `{view.custom.chPath}` | Loop tag (`Doc/LoopTag`). |
| `view.custom.desc` | unset | tag (indirect) | tag `{0}/Doc/Description`, `{0}` = `{view.custom.chPath}` | Description (`Doc/Description`). |
| `view.custom.spare` | unset | tag (indirect) | tag `{0}/Doc/Spare`, `{0}` = `{view.custom.chPath}` | Spare flag (`Doc/Spare`). Blanks the row and shows "Spare". |
| `view.custom.units` | unset | tag (indirect) | tag `{0}/Doc/Units`, `{0}` = `{view.custom.chPath}` | Units (`Doc/Units`). |
| `view.custom.emin` | unset | tag (indirect) | tag `{0}/Doc/EngMin`, `{0}` = `{view.custom.chPath}` | Engineering minimum (`Doc/EngMin`). The 0% point of the bar. |
| `view.custom.emax` | unset | tag (indirect) | tag `{0}/Doc/EngMax`, `{0}` = `{view.custom.chPath}` | Engineering maximum (`Doc/EngMax`). The 100% point of the bar. |
| `view.custom.diag` | unset | tag (indirect) | tag `{0}/HMI/DiagText`, `{0}` = `{view.custom.chPath}` | Channel diagnostic text (`HMI/DiagText`). Shown in the Health tooltip. |
| `view.custom.lo` | unset | tag (indirect) | tag `{0}/LOWER_LIMIT`, `{0}` = `{view.custom.chPath}` | Lower limit flag (`LOWER_LIMIT`). Shows UNDER in the Limit cell. AI and TEMP only. |
| `view.custom.hi` | unset | tag (indirect) | tag `{0}/UPPER_LIMIT`, `{0}` = `{view.custom.chPath}` | Upper limit flag (`UPPER_LIMIT`). Shows OVER in the Limit cell. AI and TEMP only. |

### Component-level custom properties

None.

### Session, page and message payloads

None.

## Bindings reference

Totals: **AnalogRow_AI 27** (13 view root, 14 components), **AnalogRow_AO 24** (11 view root, 13 components), **AnalogRow_TEMP 25** (13 view root, 12 components). View-root bindings are tag mirrors (12 `tag` and 1 `expr` for `chPath`, in AI). Component bindings are `expr` except the bar `position` bindings (`position.display` and `position.basis`, also `expr`).

Each variant has its own tables below.

### AnalogRow_AI

#### View root

The view-root bindings are the 13 `custom.*` mirrors listed in View-level custom properties above (all of them).

#### root (row container)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root` | `props.style.classes` | expr | `if({view.params.alt}, "Table/Row Table/RowAlt", "Table/Row")` | Row shading: `Table/Row Table/RowAlt` on odd channels (`alt`), otherwise `Table/Row`. |

#### root/Ch

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Ch` | `props.text` | expr | `toStr({view.params.ch})` | Channel number (`ch`). |

#### root/Loop

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Loop` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "—", if(isNull({view.custom.loop}), "", toStr({view.custom.loop})))` | Loop tag from `Doc/LoopTag`. Shows "—" for a spare channel and blank when the tag is null. |

#### root/Desc

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Desc` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "Spare", if(isNull({view.custom.desc}), "", toStr({view.custom.desc})))` | `Doc/Description`, or "Spare" for a spare channel. |

#### root/Raw

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Raw` | `props.text` | expr | `if(coalesce({view.custom.spare}, false) \|\| isNull({view.custom.raw}), "", toStr({view.custom.raw}))` | Raw counts from `VALUE`. Blank for a spare channel or when `VALUE` is null. |

#### root/Value

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Value` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "", if(coalesce({view.custom.err}, false), "FAULT", if(isNull({view.custom.val}), "---", numberFormat({view.custom.val}, if(abs(coalesce({view.custom.emax}, 100) - coalesce({view.custom.emin}, 0)) >= 1000, "#,##0", "#,##0.0#")))))` | Scaled value from `HMI/Scaled`. Blank for spare, "FAULT" when `CH_ERROR`, "---" when null. Otherwise formatted with no decimals when the span (EngMax minus EngMin) is 1000 or more, else with up to one decimal (`#,##0.0#`). |
| `root/Value` | `props.style.classes` | expr | `"Table/CellNumeric Text/Weight/Bold Text/Size/M" + if(!coalesce({view.custom.spare}, false) && !isGood({view.custom.raw}), " Value/BadQuality", if(coalesce({view.custom.err}, false), " Text/Color/Fault", ""))` | Bold value text. Adds `Value/BadQuality` when the raw quality is bad (not for spare), or `Text/Color/Fault` when `CH_ERROR` is true. |

#### root/Units

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Units` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "", if(isNull({view.custom.units}), "", toStr({view.custom.units})))` | `Doc/Units`, blank for a spare channel. |

#### root/BarCell

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/BarCell/Track` | `position.display` | expr | `!coalesce({view.custom.spare}, false) && !coalesce({view.custom.err}, false)` | Shows the bar track unless the channel is spare or in error. |
| `root/BarCell/Track/Fill` | `position.basis` | expr | `toStr(max(0, min(100, (coalesce({view.custom.val}, 0) - coalesce({view.custom.emin}, 0)) * 100.0 / if(coalesce({view.custom.emax}, 1) = coalesce({view.custom.emin}, 0), 1, coalesce({view.custom.emax}, 1) - coalesce({view.custom.emin}, 0))))) + "%"` | Fill width in percent: `HMI/Scaled` mapped from `Doc/EngMin` (0%) to `Doc/EngMax` (100%) and clamped to 0 to 100. If the two limits are equal the divisor is 1. |

#### root/Flags

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Flags` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "", if(coalesce({view.custom.lo}, false), "UNDER", if(coalesce({view.custom.hi}, false), "OVER", "")))` | "UNDER" when `LOWER_LIMIT` is true, else "OVER" when `UPPER_LIMIT` is true, else blank. Blank for spare. |

#### root/HealthCell

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/HealthCell/Health` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "SPARE", if(!isGood({view.custom.raw}), "COMMS?", if(coalesce({view.custom.err}, false), "FAULT", "OK")))` | "SPARE" for a spare channel, "COMMS?" when the raw quality is bad, "FAULT" when `CH_ERROR`, otherwise "OK". |
| `root/HealthCell/Health` | `props.style.classes` | expr | `if(coalesce({view.custom.spare}, false), "State/OutOfService", if(!isGood({view.custom.raw}), "State/Unknown", if(coalesce({view.custom.err}, false), "State/Fault", "State/Running")))` | Colour class for the health word: State/OutOfService, State/Unknown, State/Fault or State/Running. |
| `root/HealthCell/Health` | `meta.tooltip.text` | expr | `if(len(if(isNull({view.custom.diag}), "", toStr({view.custom.diag}))) > 0, "Diagnostics: " + {view.custom.diag}, "No channel diagnostics active")` | "Diagnostics: " plus `HMI/DiagText`, or "No channel diagnostics active". |

### AnalogRow_AO

#### View root

The view-root bindings are the 11 `custom.*` mirrors listed in View-level custom properties above (all except `lo` and `hi`, which AO does not have).

#### root (row container)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root` | `props.style.classes` | expr | `if({view.params.alt}, "Table/Row Table/RowAlt", "Table/Row")` | Row shading: `Table/Row Table/RowAlt` on odd channels (`alt`), otherwise `Table/Row`. |

#### root/Ch

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Ch` | `props.text` | expr | `toStr({view.params.ch})` | Channel number (`ch`). |

#### root/Loop

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Loop` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "—", if(isNull({view.custom.loop}), "", toStr({view.custom.loop})))` | Loop tag from `Doc/LoopTag`. Shows "—" for a spare channel and blank when the tag is null. |

#### root/Desc

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Desc` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "Spare", if(isNull({view.custom.desc}), "", toStr({view.custom.desc})))` | `Doc/Description`, or "Spare" for a spare channel. |

#### root/Raw

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Raw` | `props.text` | expr | `if(coalesce({view.custom.spare}, false) \|\| isNull({view.custom.raw}), "", toStr({view.custom.raw}))` | Raw counts from `VALUE`. Blank for a spare channel or when `VALUE` is null. |

#### root/Value

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Value` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "", if(coalesce({view.custom.err}, false), "FAULT", if(isNull({view.custom.val}), "---", numberFormat({view.custom.val}, "#,##0.0"))))` | Scaled value from `HMI/Scaled`. Blank for spare, "FAULT" when `CH_ERROR`, "---" when null. Otherwise always one decimal (`#,##0.0`), whatever the span. |
| `root/Value` | `props.style.classes` | expr | `"Table/CellNumeric Text/Weight/Bold Text/Size/M" + if(!coalesce({view.custom.spare}, false) && !isGood({view.custom.raw}), " Value/BadQuality", if(coalesce({view.custom.err}, false), " Text/Color/Fault", ""))` | Bold value text. Adds `Value/BadQuality` when the raw quality is bad (not for spare), or `Text/Color/Fault` when `CH_ERROR` is true. |

#### root/Units

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Units` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "", if(isNull({view.custom.units}), "", toStr({view.custom.units})))` | `Doc/Units`, blank for a spare channel. |

#### root/BarCell

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/BarCell/Track` | `position.display` | expr | `!coalesce({view.custom.spare}, false) && !coalesce({view.custom.err}, false)` | Shows the bar track unless the channel is spare or in error. |
| `root/BarCell/Track/Fill` | `position.basis` | expr | `toStr(max(0, min(100, (coalesce({view.custom.val}, 0) - coalesce({view.custom.emin}, 0)) * 100.0 / if(coalesce({view.custom.emax}, 1) = coalesce({view.custom.emin}, 0), 1, coalesce({view.custom.emax}, 1) - coalesce({view.custom.emin}, 0))))) + "%"` | Fill width in percent: `HMI/Scaled` mapped from `Doc/EngMin` (0%) to `Doc/EngMax` (100%) and clamped to 0 to 100. If the two limits are equal the divisor is 1. |

#### root/HealthCell

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/HealthCell/Health` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "SPARE", if(!isGood({view.custom.raw}), "COMMS?", if(coalesce({view.custom.err}, false), "FAULT", "OK")))` | "SPARE" for a spare channel, "COMMS?" when the raw quality is bad, "FAULT" when `CH_ERROR`, otherwise "OK". |
| `root/HealthCell/Health` | `props.style.classes` | expr | `if(coalesce({view.custom.spare}, false), "State/OutOfService", if(!isGood({view.custom.raw}), "State/Unknown", if(coalesce({view.custom.err}, false), "State/Fault", "State/Running")))` | Colour class for the health word: State/OutOfService, State/Unknown, State/Fault or State/Running. |
| `root/HealthCell/Health` | `meta.tooltip.text` | expr | `if(len(if(isNull({view.custom.diag}), "", toStr({view.custom.diag}))) > 0, "Diagnostics: " + {view.custom.diag}, "No channel diagnostics active")` | "Diagnostics: " plus `HMI/DiagText`, or "No channel diagnostics active". |

### AnalogRow_TEMP

#### View root

The view-root bindings are the 13 `custom.*` mirrors listed in View-level custom properties above (all of them).

#### root (row container)

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root` | `props.style.classes` | expr | `if({view.params.alt}, "Table/Row Table/RowAlt", "Table/Row")` | Row shading: `Table/Row Table/RowAlt` on odd channels (`alt`), otherwise `Table/Row`. |

#### root/Ch

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Ch` | `props.text` | expr | `toStr({view.params.ch})` | Channel number (`ch`). |

#### root/Loop

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Loop` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "—", if(isNull({view.custom.loop}), "", toStr({view.custom.loop})))` | Loop tag from `Doc/LoopTag`. Shows "—" for a spare channel and blank when the tag is null. |

#### root/Desc

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Desc` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "Spare", if(isNull({view.custom.desc}), "", toStr({view.custom.desc})))` | `Doc/Description`, or "Spare" for a spare channel. |

#### root/Raw

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Raw` | `props.text` | expr | `if(coalesce({view.custom.spare}, false) \|\| isNull({view.custom.raw}), "", toStr({view.custom.raw}))` | Raw counts from `VALUE`. Blank for a spare channel or when `VALUE` is null. |

#### root/Value

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Value` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "", if(coalesce({view.custom.err}, false), "FAULT", if(isNull({view.custom.val}), "---", numberFormat({view.custom.val}, "#,##0.0"))))` | Scaled value from `HMI/Scaled`. Blank for spare, "FAULT" when `CH_ERROR`, "---" when null. Otherwise always one decimal (`#,##0.0`), whatever the span. |
| `root/Value` | `props.style.classes` | expr | `"Table/CellNumeric Text/Weight/Bold Text/Size/M" + if(!coalesce({view.custom.spare}, false) && !isGood({view.custom.raw}), " Value/BadQuality", if(coalesce({view.custom.err}, false), " Text/Color/Fault", ""))` | Bold value text. Adds `Value/BadQuality` when the raw quality is bad (not for spare), or `Text/Color/Fault` when `CH_ERROR` is true. |

#### root/Units

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Units` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "", if(isNull({view.custom.units}), "", toStr({view.custom.units})))` | `Doc/Units`, blank for a spare channel. |

#### root/Flags

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Flags` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "", if(coalesce({view.custom.lo}, false), "UNDER", if(coalesce({view.custom.hi}, false), "OVER", "")))` | "UNDER" when `LOWER_LIMIT` is true, else "OVER" when `UPPER_LIMIT` is true, else blank. Blank for spare. |

#### root/HealthCell

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/HealthCell/Health` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "SPARE", if(!isGood({view.custom.raw}), "COMMS?", if(coalesce({view.custom.err}, false), "FAULT", "OK")))` | "SPARE" for a spare channel, "COMMS?" when the raw quality is bad, "FAULT" when `CH_ERROR`, otherwise "OK". |
| `root/HealthCell/Health` | `props.style.classes` | expr | `if(coalesce({view.custom.spare}, false), "State/OutOfService", if(!isGood({view.custom.raw}), "State/Unknown", if(coalesce({view.custom.err}, false), "State/Fault", "State/Running")))` | Colour class for the health word: State/OutOfService, State/Unknown, State/Fault or State/Running. |
| `root/HealthCell/Health` | `meta.tooltip.text` | expr | `if(len(if(isNull({view.custom.diag}), "", toStr({view.custom.diag}))) > 0, "Diagnostics: " + {view.custom.diag}, "No channel diagnostics active")` | "Diagnostics: " plus `HMI/DiagText`, or "No channel diagnostics active". |

## Scripts reference

None. The three views have no event scripts, transforms, custom methods, message handlers or onChange scripts.

## Tag members used

There is no PCLib definition for these channel members. `types/PCLib_Members.csv` has no `VALUE`, `HMI/Scaled`, `Doc/*`, `LOWER_LIMIT` or `UPPER_LIMIT` entries. The `T_AI` type there has `Inp_Raw` and `Cfg_EUMin`/`Cfg_EUMax`, which are different names. Types below are inferred from use. The fixture in `generator/render_views.py` (`io_fixture`) creates these members with integer raw counts, float scaled values and boolean flags.

| Member | Access | Data type | Meaning |
|---|---|---|---|
| `VALUE` | read | INT (inferred) | Raw counts. Used for the Raw cell and quality (`isGood`). |
| `CH_ERROR` | read | BOOL (inferred) | Channel error. FAULT text, fault text colour class, hidden bar. |
| `HMI/Scaled` | read | REAL (inferred) | Scaled engineering value. |
| `HMI/DiagText` | read | STRING (inferred) | Channel diagnostic text (tooltip). |
| `Doc/LoopTag` | read | STRING (inferred) | Loop tag. |
| `Doc/Description` | read | STRING (inferred) | Description. |
| `Doc/Spare` | read | BOOL (inferred) | Spare channel flag. |
| `Doc/Units` | read | STRING (inferred) | Units text. |
| `Doc/EngMin` | read | REAL (inferred) | Engineering minimum (bar 0%). |
| `Doc/EngMax` | read | REAL (inferred) | Engineering maximum (bar 100%). |
| `LOWER_LIMIT` | read | BOOL (inferred) | Low limit tripped. AI and TEMP only. |
| `UPPER_LIMIT` | read | BOOL (inferred) | High limit tripped. AI and TEMP only. |

All members are read only, relative to `chPath` (`cardPath` + "/" + `CHnn`).

## Component tree

Tree of `AnalogRow_AI`. AO has no `Flags` and TEMP has no `BarCell`.

- `root` (ia.container.flex)
  - `Ch` (ia.display.label)
  - `Loop` (ia.display.label)
  - `Desc` (ia.display.label)
  - `Raw` (ia.display.label)
  - `Value` (ia.display.label)
  - `Units` (ia.display.label)
  - `BarCell` (ia.container.flex)
    - `Track` (ia.container.flex)
      - `Fill` (ia.display.label)
  - `Flags` (ia.display.label)
  - `HealthCell` (ia.container.flex)
    - `Health` (ia.display.label)

## Notes and open questions

- **Value formatting differs.** AI chooses the number format from the span. AO and TEMP always show one decimal. Open question: is this intended?
- **Null limit defaults differ.** The Value text uses `EngMax` default 100 (AI only), while the bar fill uses `EngMax` default 1 and `EngMin` default 0. A missing `EngMax` therefore gives a different number format and a different bar scale. Open question.
- **Empty card path.** `chPath` is built without a guard. With a blank `cardPath` it becomes "/CHnn" and the tags would be unresolved. Not run. Expected to show bad quality (COMMS?).
- **Missing cells are intentional.** The AO row has no Limit cell and the TEMP row has no Range cell, which matches the headers in the faceplates. Not a defect.
