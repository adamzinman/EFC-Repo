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

A filled-in example follows the blank sheet: **FB_PhXeFill**, one sequence that fills any number of xenon stations.

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

### D2. Parallel items (optional: stations, lines, trains)
Use this when one step works on several items at once, each finishing on its own. Every item has its own state inside the step. Its outputs follow its own state, so its valves close as it finishes. An item with a fault is dropped while the rest carry on.

| Item state | Meaning | Outputs ON | Next item state when | Item fault (code: text) |
|---|---|---|---|---|
| | | | | |

**How items are selected:** ____________________  **The step ends when:** every item is done or faulted.  **No item left:** fail ____.

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

## Example: FB_PhXeFill, one xenon fill sequence for any number of stations

**Phase:** `FB_PhXeFill`  **Phase ID:** 100  **Unit:** XeFill  **Owner:** operator (or batch server)
**Purpose:** Fill the selected cylinders with xenon to their own target weights from the large source cylinder, through the diaphragm compressor and the fill header. Each station's inlet (direction valve) closes as that station finishes.
**Cfg_StepTimeout:** T#15M

### A. Pins
`PermOK`, `IntlkOK`, `IntlkAbort` and `EStop`, plus `U : T_XeFill` (in/out), which holds all the equipment I/O.

| `T_XeFill` member | Dir | From / to | Meaning |
|---|---|---|---|
| `Inp_SrcWt` | IN | WT-100 | source cylinder net weight, kg |
| `Inp_SuctPT` / `Inp_HdrPT` | IN | PT-101 / PT-110 | suction / fill header, bar g |
| `Inp_CompRdy` / `Inp_CompRun` | IN | K-100 | compressor ready / running |
| `Out_SrcVlv`, `Out_Recycle` | OUT | XV-100, XV-105 | source valve, recycle |
| `Out_CompRun`, `Out_CompLoad` | OUT | K-100 | compressor run, load |
| `Stn[n].Inp_VesselOK`, `Inp_IntlkOK` | IN | station n | cylinder connected; station interlocks healthy |
| `Stn[n].Inp_NetWt`, `Inp_WtStable` | IN | WT-1n1 | net weight kg, motion-free |
| `Stn[n].Inp_PT`, `Inp_VacPT` | IN | PT-1n1, PT-1n2 | bar g, mbar abs |
| `Stn[n].Out_Inlet` | OUT | XV-1n1 | **direction valve, header → station n** |
| `Stn[n].Out_Recover`, `Out_Vac`, `Out_Tare` | OUT | XV-1n2, XV-1n3, WT-1n1 | heel to recovery, vacuum, tare |

**Unit interlocks (`IntlkOK`, hold):** header PT-110 HH, compressor trips (discharge temperature, diaphragm leak, oil).
**Station interlocks (`Stn[n].Inp_IntlkOK`, drop that station only):** PT-1n1 HH, scale fault.

### B. Parameters and reports

| Member | Units | Default | Meaning |
|---|---|---|---|
| `Prm_Real[1..6]` | kg | e.g. 20, 10, 0, 15, 0, 25 | target per station; **0 = station not filled** |
| `Prm_Real[7]` / `[8]` | kg | 0.2 / 0.1 | tolerance + / − |
| `Prm_Real[9]` / `[10]` | kg | 1.0 / 0.12 | fast → slow change-over / preact |
| `Prm_Real[11]` / `[12]` | bar g / mbar abs | 0.2 / 1.0 | heel recovered to / evacuation target |
| `Prm_Real[13]` / `[14]` | mbar / bar g | 0.5 / 60 | leak check max rise / max cylinder pressure |
| `Prm_Real[15]` / `[16]` | bar g / bar | 30 / 3 | header setpoint / band |
| `Prm_DInt[1..6]` | — | 3, 10, 2, 200, 800, 5 | max top-ups, leak time s, settle s, pulse on ms, pulse off ms, cool-down s |
| `Cfg_HdrMax`, `Cfg_SuctMin`, `Cfg_SrcHeel` | bar g, bar g, kg | 40, 2, 5 | equipment limits in `T_XeFill` |
| `Rpt_Real[1..6]` | kg | — | final net weight per station |
| `Rpt_Real[7..10]` | kg, kg, kg, s | — | total filled, source start, source end, run time |
| `Rpt_DInt[1]` / `[2]` | — | — | stations filled / faulted |

### C. Sequence bar
**Title:** `Xenon fill`

| Segment | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Label | Lineup | Evacuate | Leak check | Pressurise | Fill | Done |

### D. Running steps

| Step | Seg | Description | Outputs ON | Next step when | Watchdog | Failure |
|---|---|---|---|---|---|---|
| 10 | 1 | Checking line-up | — | selected stations ready, compressor ready, 3 s → 20 | default | 300: No station selected; 200: Invalid recipe parameters; 201: Source cylinder at minimum heel |
| 20 | 2 | Recovering heels and evacuating | per station (D2) | every station evacuated → 30 | default | |
| 30 | 3 | Vacuum hold - leak check | — | after `Prm_DInt[2]` s → 40 | leak time + 60 s | 301: No station left to fill |
| 40 | 4 | Taring scales | Tare (1 s) on ready stations | stable 2 s → 50 | default | |
| 50 | 4 | Opening source cylinder | SrcVlv | suction ≥ `Cfg_SuctMin` 2 s → 60 | default | |
| 60 | 4 | Starting compressor | SrcVlv, CompRun, Recycle | running 5 s → 70 | default | |
| 70 | 4 | Pressurising fill header | SrcVlv, CompRun, CompLoad | header ≥ setpoint → 80 | default | 202: Compressor stopped |
| 80 | 5 | Filling stations | SrcVlv, CompRun, Load or Recycle (hysteresis); per station (D2) | every station filled or faulted → 90 | off | 202; 201; 301 |
| 90 | 6 | Compressor cool-down | CompRun, Recycle for `Prm_DInt[6]` s | stopped → reports, `xDone` | default | |

### D2. Parallel items: the stations

| Station state | Meaning | Outputs ON | Next station state when | Station fault |
|---|---|---|---|---|
| 0 | not selected (target 0) | — | — | — |
| 1 | waiting (step 10) | — | step 20 starts → 2 | |
| 2 | recovering heel | Recover | PT ≤ `Prm_Real[11]` → 3 | 105: station interlock (states 2–8) |
| 3 | evacuating | Vac | vacuum ≤ `Prm_Real[12]` → 4 | |
| 4 | evacuated | — | leak check passes → 5 | 101: leak check |
| 5 | ready to fill | Tare (step 40) | step 80 starts → 6 | |
| 6 | fast fill | Inlet (while header OK) | net ≥ target − `Prm_Real[9]` → 7 | 102: over pressure |
| 7 | slow fill | Inlet pulsed | net ≥ target − `Prm_Real[10]` → 8 | 102 |
| 8 | settling | — (**inlet closed**) | stable after settle time: in tolerance → 9, under → 7 (top-up) | 103: overfill; 104: under weight after max top-ups |
| 9 | filled | — (inlet stays closed) | — | — |
| 10 | fault | — (all closed) | — | code in `Sts_FailCode` |

**How stations are selected:** `Prm_Real[n]` > 0.  **Step ends:** every station filled or faulted.  **No station left:** fail 301.

### E. Hold, Restart, Stop, Abort

| State | Outputs | Logic | `xDone` when |
|---|---|---|---|
| Paused / waiting for Advance | stations isolated; SrcVlv, CompRun, Recycle if the compressor runs | keep the compressor unloaded | — |
| Holding | none: every station and the source closed, compressor stopped | — | compressor stopped |
| Restarting | step 10: SrcVlv; step 20: SrcVlv, CompRun, Recycle (only if it had reached step 60) | stations keep their own states; settling stations settle again | compressor running 5 s (or at once) |
| Stopping / Aborting | none | — | compressor stopped / at once |

Xenon is never vented to atmosphere: heels go to the recovery header, and every stop isolates the cylinders.
