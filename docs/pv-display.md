# Process Value display templates (EFC_ProcessValues)

PV design **1.3.0**. Generator: `generator/build_pv.py`. Ships inside `projects/EFC_Library/` (`Templates/ProcessValues/`). Demo tags: `tags/PV_Demo_Tags.json`. Class list: [`pv-style-index.md`](pv-style-index.md).

**History:**
- v1.0 was imported on the gateway.
- v1.1 fixed the alarm bindings.
- v1.2 restyled the card.
- v1.3 resized it to 100×50.

**Status:** v1.1–v1.3 have not been re-tested on the gateway yet.

## Requirements and decisions
- Ignition Perspective 8.1, ready for the 8.3 upgrade. Uses EFC_Styles. Templates live in **Views/Templates/ProcessValues**. Set `tagPath` to a `T_AI` instance. The views also accept `tType` (default `T_AI`), `dockId` and `dwTagPath` for dynamic-window selection. A click runs `efc.ui.openDynamic(self)` and opens `dw_ProcessValue` (`Templates/Dynamic Window/ProcessValues/ProcessValue`) in the page's `dw_Right` dock.
- **Two templates**, both 100×50 white rounded cards with a shadow:
  - **A1 `PV_StatusStrip`** (primary).
  - **B2 `PV_RangeBar`**, styled like A1.
  - The views are 104×54 so the `PV/Shell` margin keeps the shadow from being clipped.
- **Letters** appear in a fixed order: FLT · HH · H · L · LL · OVR · UNR · INH. At most 2 are visible; the rest collapse into **+N**, which has an "Also: …" tooltip and blinks if a hidden letter is unacked. Letter colors come from the configured alarm priority.
- **Blinking:** a letter blinks while unacked and goes solid once acked. Cleared-but-unacked shows faded (opacity 0.25).
- **Bad PV:** `Sts_Bad` (mirrored as `custom.hwFault`) adds `Value/BadQuality` to the value. The strip's fault state comes from `Alm_Bad/Sts_Active`, not directly from `Sts_Bad`.

## Implementation
- **Tag reads:** indirect bindings read `Val_PV`, `Cfg_Tag`, `Cfg_Desc`, `Cfg_EU`, `Sts_Bad` and `Alm_HH/H/L/LL` suppressed flags. B2 also reads `Cfg_EUMin`, `Cfg_EUMax` and each limit alarm's `Cfg_Lim`.
- **Alarm state:** expressions use direct PLC tag mirrors: `Alm_Bad` and `Alm_HH/H/L/LL` supply `Sts_Active`, `Sts_Unack` and `Cfg_Priority`. Codes are -1 for none, otherwise state × 10 + internal priority (active acknowledged = 0, active unacknowledged = 1, cleared unacknowledged = 2). PLC priorities 1 Critical / 2 High / 3 Medium / 4 Low map to internal ranks 4 / 3 / 2 / 1. `Sts_ORng` and `Sts_URng` produce Diagnostic range chips without an acknowledgement state. `custom.tick` still binds to `now(1000)`, but nothing reads it; these views have no `queryStatus` transform.
- **A1 strip:** fault first, then the highest active priority (blinking if any item is unacked), then the faded cleared color, otherwise Normal.
- **B2 track:** a percent-mode coordinate container holding the base bands, the priority overlays, a frame and the SVG pointer. The range is in the Track tooltip.
- **Scaling:** all sizes are in vh.
- **Dynamic window:** a single click calls `efc.ui.openDynamic(self)`. `T_AI` selects `dw_ProcessValue`, now `Templates/Dynamic Window/ProcessValues/ProcessValue` in the right-side `dw_Right` Perspective dock (PR #36, October 24, 2026; decisions 31–32). See [page setup](library-reference.md#page-setup-the-dw_right-dock) and detailed help for [PV_StatusStrip](help/Templates/ProcessValues/PV_StatusStrip.md) and [PV_RangeBar](help/Templates/ProcessValues/PV_RangeBar.md).

## Open items
- Raise the faded level (cleared-unacked and the blink OFF phase) from 0.25 to about 0.4 on white?
- Fold the PV classes (`PV/*`, `Alarm/Mod/*`, `Bar/Band/*`, `Bar/Frame`) into EFC_Styles.
- `PV/Chip/Diagnostic` and `PV/Strip/Diagnostic` still use `#7A7A7A`. EFC_Styles moved Diagnostic to `#6E6E6E` in the ISA-101 audit.
- Verify that the deployed `T_AI` exposes the nested alarm members and range flags used by the bindings; missing values are coalesced to inactive states.
- **Tight spots:** the A1 tag truncates with 3+ letters; large values with 4-letter units only just fit; text at 1080p is 9–11 px.
- **To verify on a gateway:** active/acknowledged/cleared PLC alarm states, priority conversion, bad-value styling and dock navigation.
