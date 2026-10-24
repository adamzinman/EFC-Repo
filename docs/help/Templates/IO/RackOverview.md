# I/O rack overview (RackOverview)

Covers `Templates/IO/RackOverview`: one rack, shown as a row of card tiles (SlotTile), one per card found in the rack.
Source: `projects/EFC_Library/com.inductiveautomation.perspective/views/Templates/IO/RackOverview/view.json`.
Tiles: [SlotTile](Parts/SlotTile.md). Dock opened by a tile: [IOCard](../Dynamic%20Window/IO/IOCard.md). Faceplates: [Discrete_Cards](Faceplates/Discrete_Cards.md), [Analog_Cards](Faceplates/Analog_Cards.md).

## Overview

- **Default size:** 1200 x 220 (`props.defaultSize`).
- **How it is embedded:** by the `_Demo` view, as an `ia.display.view` with `path` = `Templates/IO/RackOverview` and `params` = `{"rackPath": "[default]IO_Demo/Rack0"}`. No other view in the library uses it.
- **Generated view:** no.
- **Params:** `rackPath` (input). Default `[default]IO_Demo/Rack0`.

## How it operates

- **Title.** "I/O Rack" plus the rack name, from the last segment of `rackPath`.
- **Hint.** Static text: "Click a card to open its window".
- **Cards.** The `custom.cards` transform browses the rack for UDT instances and reads each card model and slot. Cards without a model are left out. The result is sorted by slot, and a missing slot counts as 99.
- **Slots.** The `Slots` repeater builds one SlotTile per card. Each tile is set up with `cardPath`, `model` and `slot`.
- **Clicks.** Clicking a tile opens the IOCard dock for that card (see SlotTile). The faceplate itself opens from the dock.
- **Writes.** None. Tag reads only (`browse`, `readBlocking`).

## Properties reference

### View parameters (`params`)

| Name | Direction | Default | Meaning | Set / read by |
|---|---|---|---|---|
| `rackPath` | input | `[default]IO_Demo/Rack0` | Rack folder to browse for cards. | Set by: the `_Demo` view embed (`{"rackPath": "[default]IO_Demo/Rack0"}`). Read by: `root/Head/Title` and `custom.cards`. |

`paramDirection: input`, `persistent: true`. No output params.

### View-level custom properties (`custom`)

| Path | Default | Binding | Source | What it holds / drives |
|---|---|---|---|---|
| `view.custom.cards` | `[]` | expr | `{view.params.rackPath}` | Card list for the `Slots` repeater. Expression `{view.params.rackPath}` run through a script transform (see Scripts) that browses the rack and returns one dict per card: `cardPath`, `model`, `slot`. |

The default `[]` is the custom default in the view JSON, used until the binding first returns.

### Component-level custom properties

None.

### Session, page and message payloads

None.

## Bindings reference

Total: **3 bindings** (1 view root `expr` with a script transform; 2 components: 1 `expr` and 1 `property`).

### View root

The view-root binding is `custom.cards`, listed in View-level custom properties above.

#### root/Head

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Head/Title` | `props.text` | expr | `"I/O Rack  " + substring({view.params.rackPath}, lastIndexOf({view.params.rackPath}, "/") + 1)` | "I/O Rack " plus the last segment of `rackPath` (for example `Rack0`). |

#### root/Slots

| Component | Property | Type | Source | Effect |
|---|---|---|---|---|
| `root/Slots` | `props.instances` | property | property `view.custom.cards` | Feeds `view.custom.cards` to the `Slots` repeater. The repeater builds one SlotTile per card, with `cardPath`, `model` and `slot` as its params. |

## Scripts reference

One transform script, on the view-level `custom.cards` binding. There are no event scripts.

```python
	log = system.util.getLogger("EFC_IO")
	out = []
	if not value:
		return out
	try:
		res = system.tag.browse(str(value), {"tagType": "UdtInstance"}).getResults()
	except Exception as e:
		log.warn("Rack browse failed for %s: %s" % (value, e))
		return out
	paths = [str(r["fullPath"]) for r in res]
	if not paths:
		return out
	qv = system.tag.readBlocking([p + "/CardModel" for p in paths] + [p + "/Slot" for p in paths])
	n = len(paths)
	for i, p in enumerate(paths):
		model = qv[i].value
		if not model:
			continue
		slot = qv[n + i].value
		out.append({"cardPath": p, "model": str(model), "slot": slot if slot is not None else 99})
	return sorted(out, key=lambda c: c["slot"])
```

Explanation, line by line in plain terms:

- Returns an empty list when `value` (the rack path) is blank.
- Browses the rack for `UdtInstance` children with `system.tag.browse`. If the browse fails it logs a warning to the `EFC_IO` logger and returns an empty list.
- Reads `CardModel` and `Slot` for every child with one `system.tag.readBlocking` call.
- Keeps only children with a non-empty model. The slot defaults to 99 when null.
- Returns the list sorted by slot. Each entry is `{cardPath, model, slot}`.

This is the only place in the IO views that calls `system.tag` for the rack. It is read only.

## Tag members used

| Member | Access | Data type | Meaning |
|---|---|---|---|
| `CardModel` (per card) | read | STRING (inferred) | Model name. Empty means no card. |
| `Slot` (per card) | read | INT (inferred) | Slot number. Null is treated as 99. |
| Child UDT instances of `rackPath` | browse | UdtInstance | Each card. |

No PCLib entry exists for these members (see the discrete faceplate doc). `CardModel` is also read by the fixture in `generator/render_views.py`.

## Component tree

- `root` (ia.container.flex)
  - `Head` (ia.container.flex)
    - `Title` (ia.display.label)
    - `Hint` (ia.display.label)
  - `Slots` (ia.display.flex-repeater, embeds `Templates/IO/Parts/SlotTile`)

## Notes and open questions

- **Refresh.** The transform depends on `rackPath` only. The rack is browsed when the binding runs, so cards added later may not appear until the view is reloaded. Not tested at runtime. Open question.
- **Silent empty list.** A failed browse or an empty rack returns an empty list. The only trace is a warning in the `EFC_IO` log.
- **Spare slots are hidden.** A card with no `CardModel` is not shown, so an empty slot leaves no tile.
- **Slot 99.** A card with a null slot is sorted last and shows "Slot 99".
