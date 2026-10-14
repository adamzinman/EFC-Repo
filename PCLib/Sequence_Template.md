# Phase sequence template (T_Phase + FB_Phase + T_SeqBar)

Fill in one sheet per phase before writing code. Each section maps to one part of the DFB:

| Sheet section | DFB part |
|---|---|
| A. Pins | pins |
| B. Parameters and reports | `Ph.Prm_` / `Ph.Rpt_` |
| C. Sequence bar | section A (labels) |
| D. Steps | section C (open area) |
| E. Hold, Restart, Stop, Abort | the non-running branches |
| F. Failures | `iFail` codes |

Review the sheet with process and operations, keep it with the Control Narrative, and use it for the FAT checkout rows.

Two filled-in examples follow the blank sheet: **Example 1**, cylinder fill, and **Example 2**, xenon feed.

---

## Blank sheet

**Phase:** `FB_Ph________`  **Phase ID:** ____  **Unit:** ________________  **Owner:** operator / unit logic / batch server
**Purpose (one line):** ______________________________________________
**Cfg_StepTimeout (default watchdog):** T#____

### A. Pins
`PermOK`, `IntlkOK`, `IntlkAbort` and `EStop` are always present.

| Pin | Dir | Type | From / to | Meaning |
|---|---|---|---|---|
| | IN | | | |
| | OUT | BOOL | control module `Prog_` input | request |

**Start permissives (`PermOK`):** ____________________
**Interlocks (`IntlkOK`), hold or abort?** ____________________

### B. Parameters and reports

| Member | Units | Default | Limits | Meaning |
|---|---|---|---|---|
| `Prm_Real[1]` | | | | |
| `Prm_DInt[1]` | | | | |
| `Rpt_Real[1]` | | — | — | |

### C. Sequence bar
**Title:** ________________  (up to 24 characters; segment labels up to 12 characters, 10 segments maximum)

| Segment | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Label | | | | | | | | | | |
| Can be skipped? | | | | | | | | | | |

### D. Running steps (state 1 Running / 3 Pausing)

| Step | Seg | Description (`sMsg`, up to 40 characters) | Outputs ON | Next step when | Watchdog | Failure (code: text) | On entry |
|---|---|---|---|---|---|---|---|
| 10 | 1 | | | → 20 when | default | | |
| 20 | | | | | | | |
| … | | | | | | | |
| 90 | last | write reports | — | `xDone` | | | |

Watchdog column: default (`Cfg_StepTimeout`), a step limit (`tStepMax`) or off (`xWdogOff`). On-entry column: one-time work done on `fbCore.StepEntry`.

### E. Hold, Restart, Stop, Abort (and Paused)

| State | Outputs | Logic (steps from 10) | `xDone` when |
|---|---|---|---|
| 4 Paused | none (default), or the `4:` branch | — | — |
| 5 Holding | | | |
| 7 Restarting | | resumes at `fbCore.RunStep` | |
| 8 Stopping | | | |
| 10 Aborting | | | |

### F. Failure codes

| Code | Text (up to 40 characters) | Step | Cause | Operator action |
|---|---|---|---|---|
| | | | | |

### G. Test (FAT rows)
- [ ] Start blocked without `PermOK`, in Manual, and with E-stop.
- [ ] Each step: transition and watchdog.
- [ ] Each failure code: puts the phase in Holding, shows the Fault segment, and Restart resumes the step.
- [ ] Hold, Restart, Stop and Abort leave the equipment safe in every step.
- [ ] Pause and Semi-automatic: the next step waits with outputs off.
- [ ] Reports are correct at Complete. Reset clears the bar.

---

## Example 1: FB_PhFill, xenon cylinder fill by weight (one per station, six stations)

**Phase:** `FB_PhFill`  **Phase ID:** 101–106  **Unit:** XeFill  **Owner:** operator (or batch server)
**Purpose:** Recover the heel, evacuate and leak-check the cylinder, then fill it with xenon to a target net weight from the compressed fill header.
**Cfg_StepTimeout:** T#10M

### A. Pins

| Pin | Dir | Type | From / to | Meaning |
|---|---|---|---|---|
| `VesselOK` | IN | BOOL | cylinder clamp / valve switch | cylinder connected, valve open |
| `NetWt` | IN | REAL | WT-1n1 (`T_AI.Val_PV`) | scale net weight, kg |
| `WtStable` | IN | BOOL | scale motion bit | motion-free |
| `PT` | IN | REAL | PT-1n1 | station pressure, bar g |
| `VacPT` | IN | REAL | PT-1n2 | vacuum, mbar abs |
| `FeedReady` | IN | BOOL | `fbFeed.FeedReady` | header at pressure |
| `Out_Inlet` | OUT | BOOL | XV-1n1 | fill inlet |
| `Out_Recover` | OUT | BOOL | XV-1n2 | heel to recovery header |
| `Out_Vac` | OUT | BOOL | XV-1n3 | vacuum |
| `Out_Sample` | OUT | BOOL | XV-1n4 | sample |
| `Out_Tare` | OUT | BOOL | WT-1n1 | tare (pulse) |
| `FeedReq` | OUT | BOOL | unit logic | needs feed |

**Permissives:** station enabled, scale healthy, no station alarm.
**Interlocks (hold):** PT-1n1 HH, scale fault, recovery header high pressure.

### B. Parameters and reports

| Member | Units | Default | Meaning |
|---|---|---|---|
| `Prm_Real[1]` | kg | 20.0 | target net weight |
| `Prm_Real[2]` / `[3]` | kg | 0.2 / 0.1 | tolerance + / − |
| `Prm_Real[4]` | kg | 1.0 | fast → slow change-over before target |
| `Prm_Real[5]` | kg | 0.12 | preact (in-flight) |
| `Prm_Real[6]` | bar g | 0.2 | heel recovered down to |
| `Prm_Real[7]` | mbar abs | 1.0 | evacuation target |
| `Prm_Real[8]` | mbar | 0.5 | leak check maximum rise |
| `Prm_Real[9]` | bar g | 60 | maximum cylinder fill pressure |
| `Prm_DInt[1]` | 0/1 | 0 | sample required |
| `Prm_DInt[2]` | — | 3 | maximum top-ups |
| `Prm_DInt[3]` / `[4]` | s | 10 / 2 | leak check time / settle time |
| `Prm_DInt[5]` / `[6]` | ms | 200 / 800 | slow fill pulse on / off |
| `Prm_DInt[7]` | s | 5 | sample fill time |
| `Rpt_Real[1..4]` | kg, bar g, s, mbar | — | final net weight, final pressure, run time, leak rise |
| `Rpt_DInt[1]` | — | — | top-ups used |

### C. Sequence bar
**Title:** `Station n fill` (set by the unit program)

| Segment | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Label | Vessel | Vac | Prefill | Fill | Sample | Done |
| Can be skipped? | | | | | yes (`Prm_DInt[1]` = 0) | |

### D. Running steps

| Step | Seg | Description | Outputs ON | Next step when | Watchdog | Failure |
|---|---|---|---|---|---|---|
| 10 | 1 | Checking cylinder and recipe | — | `VesselOK` and stable 3 s → 20 | default | 100: Invalid recipe parameters |
| 20 | 2 | Recovering heel | Recover | `PT` ≤ Prm[6] → 30 | default | |
| 30 | 2 | Evacuating cylinder | Vac | `VacPT` ≤ Prm[7] → 40 | default | |
| 40 | 2 | Vacuum hold - leak check | — | after Prm_DInt[3] s → 50 | Prm_DInt[3] s + 60 s | 101: Leak check failed |
| 50 | 3 | Taring scale | Tare (1 s) | stable 2 s → 60 | default | |
| 60 | 3 | Waiting for feed pressure | FeedReq | `FeedReady` → 70 | off | |
| 70 | 4 | Fast fill | FeedReq, Inlet (while `FeedReady`) | net ≥ target − Prm[4] → 80 | default | 102: Cylinder above max fill pressure |
| 80 | 4 | Slow fill | FeedReq, Inlet pulsed | net ≥ target − Prm[5] → 90 | default | 102 |
| 90 | 4 | Settling - checking weight | FeedReq | in tolerance → 100; under → 80; over → fail | default | 103: Overfill - above tolerance; 104: Under weight after max top-ups |
| 100 | 5 | Filling sample cylinder / No sample required | Sample | Prm_DInt[7] s → 110 (skip at once if no sample) | default | |
| 110 | 6 | Fill complete | — | reports, `xDone` | default | |

On entry: step 40 captures the vacuum reference. Step 80 counts a top-up when it is entered from step 90.

### E. Hold, Restart, Stop, Abort

| State | Outputs | Logic | `xDone` when |
|---|---|---|---|
| Paused | none: cylinder isolated | — | — |
| Holding | none: cylinder isolated, feed released | — | at once |
| Restarting | FeedReq if `RunStep` is 60–90 | wait for `FeedReady` | `FeedReady` (or at once) |
| Stopping / Aborting | none: cylinder isolated | — | at once |

Xenon is never vented to atmosphere: the heel goes to recovery, and every stop isolates the cylinder.

---

## Example 2: FB_PhFeed, xenon feed (source cylinder → diaphragm compressor → fill header)

**Phase:** `FB_PhFeed`  **Phase ID:** 100  **Unit:** XeFill  **Owner:** unit logic (`Prog_Acquire`), started on station demand
**Purpose:** Pressurise the fill header from the large source cylinder and hold it at setpoint while any station asks for feed.
**Cfg_StepTimeout:** T#5M

### A. Pins

| Pin | Dir | Type | From / to | Meaning |
|---|---|---|---|---|
| `SrcWt` | IN | REAL | WT-100 | source cylinder net weight, kg |
| `SuctPT` | IN | REAL | PT-101 | suction, bar g |
| `HdrPT` | IN | REAL | PT-110 | fill header, bar g |
| `CompRdy` / `CompRun` | IN | BOOL | K-100 (`T_DiaComp` / `T_Motor`) | ready / running |
| `FeedReqs` | IN | INT | unit logic | stations asking for feed |
| `Out_SrcVlv` | OUT | BOOL | XV-100 | source cylinder valve |
| `Out_CompRun` / `Out_CompLoad` | OUT | BOOL | K-100 | run / load |
| `Out_Recycle` | OUT | BOOL | XV-105 | recycle / bypass |
| `FeedReady` | OUT | BOOL | stations | header at pressure |

**Interlocks (hold):** header PT-110 HH, discharge temperature high, diaphragm leak, hydraulic oil low (from `T_DiaComp`).

### B. Parameters and reports

| Member | Units | Default | Meaning |
|---|---|---|---|
| `Prm_Real[1]` | bar g | 30 | header pressure setpoint |
| `Prm_Real[2]` | bar | 3 | load band below setpoint |
| `Prm_Real[3]` | bar g | 40 | header maximum (unload above) |
| `Prm_Real[4]` | bar g | 2 | minimum suction |
| `Prm_Real[5]` | kg | 5 | source cylinder minimum heel |
| `Prm_DInt[1]` / `[2]` | s | 20 / 5 | idle time before shutdown / unloaded cool-down |
| `Rpt_Real[1..4]` | kg, kg, kg, s | — | source weight at start, source weight at end, xenon delivered, run time |

### C. Sequence bar
**Title:** `Xenon feed`

| Segment | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Label | Lineup | Source | Start | Pressurise | Supply | Done |

### D. Running steps

| Step | Seg | Description | Outputs ON | Next step when | Watchdog | Failure |
|---|---|---|---|---|---|---|
| 10 | 1 | Checking line-up | — | `CompRdy` → 20 | default | 200: Invalid recipe parameters; 201: Source cylinder at minimum heel |
| 20 | 2 | Opening source cylinder | SrcVlv | suction ≥ Prm[4] for 2 s → 30 | default | |
| 30 | 3 | Starting compressor | SrcVlv, CompRun, Recycle | running 5 s → 40 | default | |
| 40 | 4 | Pressurising fill header | SrcVlv, CompRun, CompLoad | header ≥ Prm[1] → 50 | default | 202: Compressor stopped |
| 50 | 5 | Supplying stations / Supply - no requests | SrcVlv, CompRun, Load or Recycle (hysteresis), FeedReady | no request for Prm_DInt[1] s → 60 | off | 201, 202 |
| 60 | 6 | Compressor cool-down | CompRun and Recycle for Prm_DInt[2] s | stopped → reports, `xDone` | default | |

### E. Hold, Restart, Stop, Abort

| State | Outputs | Logic | `xDone` when |
|---|---|---|---|
| Paused | SrcVlv, CompRun, Recycle (if running): unloaded, FeedReady off | `4:` branch | — |
| Holding | none: compressor stopped, source closed | — | compressor stopped |
| Restarting | step 10: SrcVlv; step 20: SrcVlv, CompRun, Recycle | open the source, start unloaded | compressor running 5 s |
| Stopping | none | — | compressor stopped |
| Aborting | none | — | at once |
