# FB_AlmCore simulator tests

Setup (all tests): in a test project with `FB_AlmCore` imported, declare `fbT : FB_AlmCore;` and the test
variables below in the Data Editor, and add an ST section to MAST:

```
fbT(Cond := tCond, Supp := tSupp, OOSIn := tOOSIn, Enabled := tEn, LatchCfg := tLatch, NoAck := tNoAck,
    OnDly := tOnDly, OffDly := tOffDly, MaxShelf := tMaxShelf, Ack := tAck, Rst := tRst,
    Shelve := tShelve, Unshelve := tUnshelve, RemoveSvc := tRemove, ReturnSvc := tReturn);
tAck := FALSE; tRst := FALSE; tShelve := FALSE; tUnshelve := FALSE; tRemove := FALSE; tReturn := FALSE;
IF fbT.EvtActive THEN nEvtActive := nEvtActive + 1; END_IF;
IF fbT.EvtRTN THEN nEvtRTN := nEvtRTN + 1; END_IF;
```

`tCond, tSupp, tOOSIn, tEn, tLatch, tNoAck, tAck, tRst, tShelve, tUnshelve, tRemove, tReturn : BOOL;
tOnDly, tOffDly, tMaxShelf : TIME; nEvtActive, nEvtRTN : INT;`

Default before each test (unless stated): `tEn` TRUE, all other BOOLs FALSE, all TIMEs `T#0S`, counters 0,
state 0. The command bits (`tAck` ... `tReturn`) are one-scan: set them from an animation table.

| # | Setup | Action | Expected |
|---|---|---|---|
| 1 | Cold start: Build, download, **Init** (cold start) with `tCond` TRUE already | Run | Memories start cleared, so the standing condition annunciates as a new alarm on the first scan: `Active` TRUE, `Unack` TRUE, `State` 1, `nEvtActive` 1, `nEvtRTN` 0 |
| 2 | Default | `tCond` TRUE | `Active`, `Unack`, `State` 1, `nEvtActive` 1 |
| 3 | After #2 (active, unacked) | `tAck` | **Ack while active:** `Unack` FALSE, `Active` TRUE, `State` 2 |
| 4 | After #3 | `tCond` FALSE | `Active` FALSE, `State` 0, `nEvtRTN` 1 |
| 5 | Default | `tCond` TRUE, then FALSE (no ack) | `State` 1 -> 3 (RTN unack), `nEvtRTN` 1 |
| 6 | After #5 | `tAck` | **Ack after clear:** `State` 0, `Unack` FALSE |
| 7 | `tOnDly` T#5S | `tCond` TRUE for 3 s, then FALSE | never active, `nEvtActive` 0 |
| 8 | `tOnDly` T#5S | `tCond` TRUE and hold | active after 5 s (+/- one scan) |
| 9 | `tOffDly` T#5S, active | `tCond` FALSE | stays active 5 s, then `State` 3 |
| 10 | `tLatch` TRUE | `tCond` TRUE, `tAck`, `tCond` FALSE | `State` 4 (latched), `Active` TRUE |
| 11 | After #10 | `tCond` TRUE again, then `tRst` | **Reset while condition present:** still active, `State` 2 |
| 12 | After #11 | `tCond` FALSE, then `tRst` | latch cleared, `Active` FALSE, `State` 0 |
| 13 | `tLatch` TRUE, active and unacked | `tCond` FALSE, then `tRst` | latch cleared, `State` 3 (still unacked), then `tAck` -> 0 |
| 14 | `tNoAck` TRUE | `tCond` TRUE | `Active` TRUE, `Unack` FALSE, `State` 2 |
| 15 | `tMaxShelf` T#10S, active | `tShelve` | `Shelved`, `State` 5, `Active` FALSE, `ShelfLeft` counts down from 10 s |
| 16 | After #15, `tCond` still TRUE | wait 10 s | shelf expires: `Shelved` FALSE, re-annunciates: `State` 1, `nEvtActive` +1 |
| 17 | Shelved (as #15) | `tUnshelve` | `Shelved` FALSE, `ShelfLeft` T#0S, `State` 1 if `tCond` |
| 18 | `tEn` FALSE | `tShelve` | not shelved; `State` 7 |
| 19 | Active | `tSupp` TRUE | `Suppressed`, `State` 6, `Active` FALSE, `Unack` FALSE, `nEvtRTN` unchanged |
| 20 | After #19 | `tSupp` FALSE (cond still TRUE) | re-annunciates, `State` 1 |
| 21 | Active | `tRemove` | `OOS`, `State` 7, `Active` FALSE |
| 22 | After #21 | `tShelve` | not shelved (OOS) |
| 23 | After #21 | `tReturn` | `OOS` FALSE, `State` 1 if `tCond` |
| 24 | Active | `tOOSIn` TRUE | `OOS` TRUE, `State` 7, `Active` FALSE |
| 25 | After #24 | `tOOSIn` FALSE | `OOS` FALSE (no `RemoveSvc` memory), alarm returns per `tCond` |
| 26 | Shelved | `tOOSIn` TRUE | shelve dropped (`Shelved` FALSE) |
| 27 | Active, `tEn` TRUE | `tEn` FALSE | `State` 7, `Active` FALSE, `Suppressed` FALSE |
| 28 | `tSupp` TRUE and `tRemove` | - | `State` 7 (H wins over G) |
| 29 | Active and latched (#10), warm start (stop/run without Init) | Run | latch kept (`State` 4) - documents warm-start behaviour |
| 30 | Cold start (Init) after #29 | Run | `State` 0 if `tCond` FALSE |
