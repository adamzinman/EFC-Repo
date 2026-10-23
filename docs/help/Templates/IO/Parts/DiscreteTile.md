# Discrete channel tile (DiscreteTile)

Covers `Templates/IO/Parts/DiscreteTile`: one channel of a discrete card (LED, loop tag, description, fault state).
Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/IO/Parts/DiscreteTile/view.json`.
Used by: the `Tiles*` repeaters of the five discrete faceplates, see [Discrete_Cards](../Faceplates/Discrete_Cards.md). Dock: [IOCard](../../Dynamic%20Window/IO/IOCard.md) (the card-level dock; the tile does not open anything).

## Overview

- **Default size:** 96 x 70 (`props.defaultSize`).
- **How it is embedded:** by the body repeaters of the discrete faceplates. Each repeater passes `cardPath`, `ch`, `chFolder` (`CHnn`) and `alt` as the instance dict.
- **Generated view:** no.
- **Params:** `cardPath`, `ch`, `chFolder`, `alt` (all input).

## How it operates

- **LED.** Off, On, Fault (`Indicator/LED/Fault`, when `CH_ERROR`) or Unknown (bad value quality). Blank for spare.
- **Label.** "CH nn" from the channel index, and the loop tag (or "Spare", or "—").
- **Second line.** The description. For a channel in error, "FAULT" and the diagnostic text instead. Blank for spare.
- **Tile outline.** `State/Fault` when in error, dashed (`Util/BorderDashed`) when spare, otherwise the card style.
- **Tooltip.** Channel number, loop tag, description, diagnostics and bad-quality note.
- **Writes.** None. The tile has no events and no commands, so it is read only. This matches the RO caption on the DO faceplates.
- **Alt param.** `alt` is passed in by the repeater for row shading, but no binding in this view reads it (see Notes).

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `cardPath` | input | `""` | Card UDT path. Used to build `chPath`. | Set by: discrete faceplate `Tiles*` repeaters. Read by: `custom.chPath`. |
| `ch` | input | `0` | Channel index. | Set by: repeaters (0 to 63, by faceplate). Read by: `root/Tile/Top/Ch` and the tooltip. |
| `chFolder` | input | `"CH00"` | Channel folder under the card (`CHnn`). | Set by: repeaters. Read by: `custom.chPath`. |
| `alt` | input | `false` | Odd-channel flag from the repeater. | Set by: repeaters (`i % 2 == 1`). Read by: nothing in this view. |

All four params have `paramDirection: input` and `persistent: true`.

### View-level custom properties (`custom`)

Each is a tag mirror of one channel member, except `chPath`. None has a default (the `custom` block is empty). `{0}` in the sources is `chPath`.

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.chPath` | unset | expr | `{view.params.cardPath} + "/" + {view.params.chFolder}` | Channel tag folder: `cardPath` + "/" + `chFolder`. Base for every channel tag read. |
| `view.custom.value` | unset | tag (indirect) | tag `{0}/VALUE`, `{0}` = `{view.custom.chPath}` | Channel value (`VALUE`), a boolean. Drives the LED state. |
| `view.custom.err` | unset | tag (indirect) | tag `{0}/CH_ERROR`, `{0}` = `{view.custom.chPath}` | Channel error (`CH_ERROR`). Drives the `State/Fault` outline, the FAULT text and the LED. |
| `view.custom.loop` | unset | tag (indirect) | tag `{0}/Doc/LoopTag`, `{0}` = `{view.custom.chPath}` | Loop tag (`Doc/LoopTag`). |
| `view.custom.desc` | unset | tag (indirect) | tag `{0}/Doc/Description`, `{0}` = `{view.custom.chPath}` | Description (`Doc/Description`). |
| `view.custom.spare` | unset | tag (indirect) | tag `{0}/Doc/Spare`, `{0}` = `{view.custom.chPath}` | Spare flag (`Doc/Spare`). Dashes the tile and shows "Spare". |
| `view.custom.diag` | unset | tag (indirect) | tag `{0}/HMI/DiagText`, `{0}` = `{view.custom.chPath}` | Channel diagnostic text (`HMI/DiagText`). Shown in the tooltip and on the second line when in error. |

### Component-level custom properties

None.

### Session, page and message payloads

None.

## Bindings reference

Total: **13 bindings** (7 view root: 1 `expr` for `chPath` and 6 `tag`; 6 components, all `expr`).

### View root

The view-root bindings are the seven `custom.*` bindings listed in View-level custom properties above.

#### root/Tile

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Tile` | `props.style.classes` | expr | `if(coalesce({view.custom.spare}, false), "Container/Inset Util/BorderDashed", if(coalesce({view.custom.err}, false), "State/Fault", "Container/Card")) + " Util/Pad/S"` | Tile style: dashed inset for a spare channel, `State/Fault` outline when `CH_ERROR`, otherwise `Container/Card`. Always adds `Util/Pad/S`. |
| `root/Tile` | `meta.tooltip.text` | expr | `"CH " + numberFormat({view.params.ch}, "00") + "  " + if(isNull({view.custom.loop}), "", toStr({view.custom.loop})) + "\n" + if(isNull({view.custom.desc}), "", toStr({view.custom.desc})) + if(len(if(isNull({view.custom.diag}), "", toStr({view.custom.diag}))) > 0, "\nDiagnostics: " + {view.custom.diag}, "") + if(!isGood({view.custom.value}), "\nBad OPC quality", "")` | Tooltip: "CH nn", loop tag, description, a "Diagnostics:" line when there is diagnostic text, and "Bad OPC quality" when the value quality is bad. |
| `root/Tile/Top/Ch` | `props.text` | expr | `"CH " + numberFormat({view.params.ch}, "00")` | Channel label "CH nn" from `ch` (two digits). |
| `root/Tile/Top/Led` | `props.style.classes` | expr | `if(coalesce({view.custom.spare}, false), "", if(!isGood({view.custom.value}), "Indicator/LED/Unknown", if(coalesce({view.custom.err}, false), "Indicator/LED/Fault", if({view.custom.value}, "Indicator/LED/On", "Indicator/LED/Off"))))` | LED state: blank for a spare channel, `Indicator/LED/Unknown` when the value quality is bad, `Indicator/LED/Fault` when `CH_ERROR`, `Indicator/LED/On` when `VALUE` is true, otherwise `Indicator/LED/Off`. |
| `root/Tile/Loop` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "Spare", if(len(if(isNull({view.custom.loop}), "", toStr({view.custom.loop}))) > 0, {view.custom.loop}, "—"))` | Loop tag, or "Spare" for a spare channel, or "—" when there is no tag. |
| `root/Tile/Sub` | `props.text` | expr | `if(coalesce({view.custom.spare}, false), "", if(coalesce({view.custom.err}, false), "FAULT " + if(isNull({view.custom.diag}), "", toStr({view.custom.diag})), if(isNull({view.custom.desc}), "", toStr({view.custom.desc}))))` | Second line: blank for a spare channel; "FAULT" plus the diagnostic text when `CH_ERROR`; otherwise the description. |

## Scripts reference

None. No event scripts, transforms, custom methods, message handlers or onChange scripts.

## Tag members used

There is no PCLib definition for these members (see the AnalogRow doc for the same note). Types are inferred from use.

| Member | Access | Data type | Meaning |
|---|---|---|---|
| `VALUE` | read | BOOL (inferred) | Channel state. Drives the LED On/Off. Quality drives Unknown. |
| `CH_ERROR` | read | BOOL (inferred) | Channel error. `State/Fault` outline, FAULT text, fault LED. |
| `Doc/LoopTag` | read | STRING (inferred) | Loop tag. |
| `Doc/Description` | read | STRING (inferred) | Description. |
| `Doc/Spare` | read | BOOL (inferred) | Spare channel flag. |
| `HMI/DiagText` | read | STRING (inferred) | Channel diagnostic text. |

All read only, relative to `chPath`.

## Component tree

- `root` (ia.container.flex)
  - `Tile` (ia.container.flex)
    - `Top` (ia.container.flex)
      - `Ch` (ia.display.label)
      - `Led` (ia.display.label)
    - `Loop` (ia.display.label)
    - `Sub` (ia.display.label)

## Notes and open questions

- **Unused param.** `alt` is declared and set by the repeaters, but no binding in this view reads `view.params.alt`. The row shading is therefore not applied to the tiles. Harmless, but either remove it or use it.
- **Bad quality on VALUE.** The LED shows Unknown when the `VALUE` quality is bad, which is checked before the fault test. So a faulted channel with bad quality shows Unknown, not Fault.
- **Tooltip wording.** The tooltip says "Bad OPC quality". The tile tests `isGood` on `VALUE` only. Other members are not checked.
- **No commands.** The tile has no buttons or events. The DO faceplates say "Read-only" for this reason. Open question if output commands are wanted here.
