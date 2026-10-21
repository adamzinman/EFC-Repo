# FB_AlmCore - ISA-18.2 alarm state machine (Control Expert Classic V16.2)

Version 1.00. EFCLib v1 helper DFB. Shared by `FB_Alarm` (`T_Alarm`) and `FB_AlmLim` (`T_AlmLim`), which
every core device DFB calls once per nested alarm. It has no data type of its own: everything goes through pins.

Status: **pilot stage 2a, not yet imported into 16.2.** Its job is to prove the generator
(`tools/st2xdb.py`) and the unverified `outputParameters` block before any DFB that needs nested DDTs or DFB instances.

## Files

| File | Use |
|---|---|
| `FB_AlmCore.XDB` | **Import this.** Generated; never edit by hand |
| `src/FB_AlmCore.iface.yaml` | Pins and private variables (generator input) |
| `src/FB_AlmCore.st` | ST body (generator input, readable on its own) |
| `tests/FB_AlmCore_tests.md` | Simulator test sheet |
| `_work/pilot/B_copy-checksums/FB_AlmCore.XDB` | Fallback if the import asks for checksums (see below) |

Regenerate: `python3 tools/st2xdb.py FB_AlmCore`.

## Import prerequisites and steps

- No DDTs needed (no `DDTSource` in the file). No other DFBs needed.
1. Project Browser > **Derived FB Types** > right-click > **Import...** > `types/dfb/FB_AlmCore.XDB`.
2. **Build > Analyze Project**, then **Rebuild All**.
3. If step 1 fails, try `_work/pilot/B_copy-checksums/FB_AlmCore.XDB` (same content, with the sample's checksum values).
4. Report back: the import / analyze messages verbatim, or OK. **If OK, please export the imported DFB**
   (right-click `FB_AlmCore` > Export) and send the `.XDB`: it shows how 16.2 writes outputs, TIME pins,
   ST comments and the checksums it assigned.

## Pins

| Pin | Dir | Type | Purpose |
|---|---|---|---|
| 1 `Cond` | IN | BOOL | Raw alarm condition |
| 2 `Supp` | IN | BOOL | Suppressed by design (state G) |
| 3 `OOSIn` | IN | BOOL | Owner device Out of Service (state H) |
| 4 `Enabled` | IN | BOOL | Alarm enabled; FALSE = state H |
| 5 `LatchCfg` | IN | BOOL | Latching alarm (state E) |
| 6 `NoAck` | IN | BOOL | No acknowledge required |
| 7 `OnDly` | IN | TIME | On-delay |
| 8 `OffDly` | IN | TIME | Off-delay |
| 9 `MaxShelf` | IN | TIME | Maximum shelve time |
| 10 `Ack` | IN | BOOL | Acknowledge (caller clears its one-shot) |
| 11 `Rst` | IN | BOOL | Reset latched alarm |
| 12 `Shelve` | IN | BOOL | Shelve |
| 13 `Unshelve` | IN | BOOL | Unshelve |
| 14 `RemoveSvc` | IN | BOOL | Remove from service |
| 15 `ReturnSvc` | IN | BOOL | Return to service |
| 16 `Active` | OUT | BOOL | Active after delays and latch |
| 17 `Unack` | OUT | BOOL | Unacknowledged |
| 18 `Shelved` | OUT | BOOL | Shelved |
| 19 `Suppressed` | OUT | BOOL | Suppressed by design |
| 20 `OOS` | OUT | BOOL | Out of service (`RemoveSvc` memory or `OOSIn`) |
| 21 `State` | OUT | INT | 0 A Normal, 1 B Unack, 2 C Acked, 3 D RTN-Unack, 4 E Latched, 5 F Shelved, 6 G Suppressed, 7 H OOS / disabled |
| 22 `ShelfLeft` | OUT | TIME | Shelve time remaining |
| 23 `EvtActive` | OUT | BOOL | One-scan pulse: became active |
| 24 `EvtRTN` | OUT | BOOL | One-scan pulse: returned to normal (not on inhibit) |

All BOOL inputs default FALSE. Commands are levels for one scan; the caller (FB_Alarm) clears its `Cmd_` members.

## Behaviour

- **Acknowledge** (`Ack`) clears Unack only. **Reset** (`Rst`) clears a latch only after the condition has gone.
- **Inhibit** = OOS (either source), shelved, suppressed or disabled. While inhibited the alarm is not active,
  not unacked, and the delay timers restart; a latch is dropped.
- **Shelving** ends on `Unshelve`, on `MaxShelf` expiry, on OOS or on disable. If the condition is still there it
  re-annunciates (after `OnDly`).
- **State priority:** H > G > F > E > B > C > D > A.
- **First scan after a cold start:** all memories cleared, state 0. A warm start keeps them (no system bits used).
- Timing: TON/TOF only. No located variables, no globals, no system bits.

## Format items this pilot tests (unverified in the reference export)

| Item | In this file | If the import rejects it |
|---|---|---|
| `outputParameters` block, after `inputParameters`, pins 16-24 continue the input numbering | yes | send the error; I change the generator |
| Checksums omitted | yes | try the B fallback |
| `TIME` pins and typed literal `T#0S` | yes | send the error |
| ST comments `(* *)` | yes | send the error |

## Open items

- Real 16.2 export of `DFB_FmtTest` (question 3) is needed before stage 2b (`FB_Alarm`, `FB_AlmLim`, `FB_AI`).
- `XDB_FORMAT_REFERENCE.md` section 8 says variables sit at 4 tabs and pin attributes at 5; the raw export has
  3 and 4. The generator follows the raw export.
