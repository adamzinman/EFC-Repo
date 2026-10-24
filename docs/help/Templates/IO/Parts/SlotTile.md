# I/O slot tile (SlotTile)

Covers `Templates/IO/Parts/SlotTile`: one card tile in a rack overview. It shows the slot, model, description and module health, and opens the card dock on click.
Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/IO/Parts/SlotTile/view.json`.
Used by: [RackOverview](../RackOverview.md) (the `Slots` repeater). Dock opened: [IOCard](../../Dynamic%20Window/IO/IOCard.md) (via `efc.ui.openDynamic`, window `dw_IOCard`).

## Overview

- **Default size:** 132 x 150 (`props.defaultSize`).
- **How it is embedded:** by the `Slots` flex repeater of [RackOverview](../RackOverview.md). The repeater passes `cardPath`, `model` and `slot` as the instance dict, from the rack browse. `tType` and `dockId` are not passed, so they keep their defaults (`native`, `dw_IOCard`).
- **Generated view:** no.
- **Opening:** a single click runs `efc.ui.openDynamic(self)` when `model` is set. That shows `Templates/Dynamic Window/IO/IOCard` for this card in the page's `dw_Right` dock. The faceplate itself opens from the dock (see below).

## How it operates

- **Layout.** "Slot n" at the top, the model name, the card description, the instance name (last part of `cardPath`), and the health word at the bottom.
- **Health.** "COMMS?" when the MOD_ERROR quality is bad, "FAULT" when it is true (`State/Fault` outline too), otherwise "HEALTHY".
- **Click.** When `model` is set, the click loads `Templates/Dynamic Window/IO/IOCard` into the page's `dw_Right` dock with `tagPath` = the card path and `model`. This writes no tag and no session value, and checks no role.
- **Empty model.** With no model the click does nothing, and the tile shows no model name.
- **Writes.** None.

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `cardPath` | input | `""` | Card UDT path. | Set by: RackOverview `Slots` (from the rack browse). Read by: `root/Tile/Inst`, `custom` tag references, `openDynamic` (as the tag path). |
| `model` | input | `""` | Card model, for example `BMXDDI1602`. | Set by: RackOverview (from `CardModel`). Read by: `root/Tile/Model`, the click guard, `openDynamic` (passed to the dock as `model`). |
| `slot` | input | `0` | Slot number. | Set by: RackOverview (from `Slot`, or 99 when missing). Read by: `root/Tile/Slot`. |
| `tType` | input | `"native"` | Type key for `openDynamic`. | Read by: `openDynamic`, only when `dockId` is empty. Here `dockId` is set, so it is not used. |
| `dockId` | input | `"dw_IOCard"` | Window id. Takes precedence over `tType`. | Read by: `openDynamic`. |
| `dwTagPath` | input | `""` | Tag path for the dock instead of `cardPath`. | Read by: `openDynamic`. Empty here. |

All six params have `paramDirection: input` and `persistent: true`.

### View-level custom properties (`custom`)

None have a default (the `custom` block is empty). `{0}` in the sources is `cardPath`.

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.modErr` | unset | tag (indirect) | tag `{0}/Module/MOD_ERROR`, `{0}` = `{view.params.cardPath}` | Module error (`Module/MOD_ERROR`). Drives the card outline and the health word. |
| `view.custom.desc` | unset | tag (indirect) | tag `{0}/CardDesc`, `{0}` = `{view.params.cardPath}` | Card description (`CardDesc`). Shown on the Desc line. |
| `view.custom.diag` | unset | tag (indirect) | tag `{0}/Module/HMI/DiagText`, `{0}` = `{view.params.cardPath}` | Module diagnostic text (`Module/HMI/DiagText`). Shown in the tooltip. |

### Component-level custom properties

None.

### Session, page and message payloads

- **Writes:** no tag or session value. `efc.ui.openDynamic` changes the page's `dw_Right` dock (view and params).
- **Reads:** none directly. The library function reads `view.params` and the page id.
- **Messages:** none.

## Bindings reference

Total: **11 bindings** (3 view root `tag`; 8 components: 6 `expr`, 1 `property`, plus the `Tile` style and tooltip).

### View root

The view-root bindings are the three `custom.*` tag mirrors listed in View-level custom properties above.

#### root/Tile

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Tile` | `props.style.classes` | expr | `if(isGood({view.custom.modErr}) && {view.custom.modErr}, "State/Fault", "Container/Card") + " Util/Pad/S Util/Pointer"` | Card outline: `State/Fault` when the module error is true with good quality, otherwise `Container/Card`. Adds `Util/Pad/S` and `Util/Pointer`. |
| `root/Tile` | `meta.tooltip.text` | expr | `"Open card window" + if(len(if(isNull({view.custom.diag}), "", toStr({view.custom.diag}))) > 0, "\nModule: " + {view.custom.diag}, "")` | "Open card window", plus a "Module:" line with the diagnostic text when there is any. |
| `root/Tile/Slot` | `props.text` | expr | `"Slot " + toStr({view.params.slot})` | "Slot " plus the slot number (`slot` param). |
| `root/Tile/Model` | `props.text` | property | property `view.params.model` | Card model from the `model` param (a property binding, no fallback). Blank until RackOverview sets it. |
| `root/Tile/Desc` | `props.text` | expr | `if(isNull({view.custom.desc}), "", toStr({view.custom.desc}))` | `CardDesc`, or blank when null. |
| `root/Tile/Inst` | `props.text` | expr | `substring({view.params.cardPath}, lastIndexOf({view.params.cardPath}, "/") + 1)` | Last segment of `cardPath`, for example `R0S2`. |
| `root/Tile/Health` | `props.text` | expr | `if(!isGood({view.custom.modErr}), "COMMS?", if({view.custom.modErr}, "FAULT", "HEALTHY"))` | "COMMS?" when the MOD_ERROR quality is bad, "FAULT" when true, otherwise "HEALTHY". |
| `root/Tile/Health` | `props.style.classes` | expr | `if(!isGood({view.custom.modErr}), "State/Unknown", if({view.custom.modErr}, "State/Fault", "State/Running"))` | Colour class for the health word: State/Unknown, State/Fault or State/Running. |

## Scripts reference

One event script: the click on the tile (`root/Tile`, `events.dom.onClick`).

```python
	if self.view.params.model:
		efc.ui.openDynamic(self)
```

Explanation: if `model` is not blank, call `efc.ui.openDynamic(self)`. Otherwise do nothing.

Library call, `efc.ui.openDynamic(component)` (`projects/EFC_Library/ignition/script-python/efc/ui/code.py`), for this view:

- Chooses the window: `dockId` ("dw_IOCard") first, else `BY_TYPE[tType]`. `dw_IOCard` maps to `Templates/Dynamic Window/IO/IOCard`. If the window is unknown it logs a warning and stops.
- Picks the tag path: `dwTagPath`, else `tagPath`, else `cardPath`. This view has no `tagPath`, so the card path is used.
- Builds the dock params: `tagPath` (the card path), plus `model` when it is set. `slot` is not passed.
- Loads `Templates/Dynamic Window/IO/IOCard` into the page's `dw_Right` dock with `params: {...}` (`efc.ui.showDock`) and opens the dock. It writes no session value.
- It does not check the user role, does not write a tag and does not write an audit record.

## Tag members used

| Member | Access | Data type | Meaning |
|---|---|---|---|
| `Module/MOD_ERROR` | read | BOOL (inferred) | Module error. Drives the outline and the health word. |
| `CardDesc` | read | STRING (inferred) | Card description. |
| `Module/HMI/DiagText` | read | STRING (inferred) | Module diagnostic text (tooltip). |

Read only, relative to `cardPath`. The model and slot come from RackOverview (`CardModel`, `Slot`). No PCLib entry exists for these members (see the discrete faceplate doc).

## Component tree

- `root` (ia.container.flex)
  - `Tile` (ia.container.flex)
    - `Slot` (ia.display.label)
    - `Model` (ia.display.label)
    - `Desc` (ia.display.label)
    - `Inst` (ia.display.label)
    - `Health` (ia.display.label)

## Notes and open questions

- **Model with no faceplate.** The dock opens `Templates/IO/Faceplates/<model>`. Models other than the eight faceplate views would fail to open (not checked at runtime).
- **Outline and health differ.** When `MOD_ERROR` quality is bad, the health word shows COMMS? (unknown), but the outline stays `Container/Card` (only a true value gives the `State/Fault` outline). Consistent with the rule, but worth knowing.
- **Model binding has no fallback.** `root/Tile/Model` is a property binding to `view.params.model` with no default. Blank model shows blank text. Intentional? Open question.
- **Unused params.** `tType` and `dwTagPath` exist for the library default path only. They are not set by RackOverview.
