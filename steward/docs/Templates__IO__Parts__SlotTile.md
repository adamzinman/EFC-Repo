# Templates/IO/Parts/SlotTile

<!-- keep:start -->
**Purpose:** Rack slot tile: model, rack/slot, module error, from the native x80 device DDT.

**Usage notes:** Click opens dw_IOCard (params tagPath = cardPath, model).

**Gotchas:** Empty model = empty slot; the click does nothing.
<!-- keep:end -->

<!-- auto:start -->
_Auto-generated 2026-10-23 20:15 from EFC_Library:view:Templates/IO/Parts/SlotTile. Do not edit this section._

| Param | Direction | Default |
|---|---|---|
| cardPath | input | "" |
| dockId | input | "dw_IOCard" |
| dwTagPath | input | "" |
| model | input | "" |
| slot | input | 0 |
| tType | input | "native" |

- PCLib types: none
- Dynamic window: none
- Style classes: Container/Card, State/Running, Text/Mod/Ellipsis, Text/Mod/Wrap, Text/Size/S, Text/Size/XS, Text/Size/XXS, Text/Weight/Bold, Util/Pad/S, Util/Pointer, Util/Transparent (+2 bound)
- Inline style props: 0
- Popups opened: 0
- system.* calls: none
- Last modified: 2026-10-06T22:29:13Z by build_io.py
<!-- auto:end -->
