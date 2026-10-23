# Step 1 spec: FB_AI (T_AI) and FB_DI (T_DI)

Neither type has `T_Mode`. Their "mode table" is the signal-source table (field / simulated / bad).

## FB_AI

(a) Pins

| Pin | Dir | Type | Purpose |
|---|---|---|---|
| `UDT_Data` | IN_OUT | T_AI | HMI interface |
| `Raw` | IN | INT | raw counts -> `Inp_Raw` |
| `ChFault` | IN | BOOL | channel / module fault -> `Inp_ChFault` |
| `NE107` | IN | INT | smart-device status -> `Inp_NE107` (0 if not used) |
| `PV` | OUT | REAL | = `Val_PV` (convenience for downstream logic) |
| `Bad` | OUT | BOOL | = `Sts_Bad` |

(b) Members (logic = old FB_AI, reviewed; order: dt, config check, % span, NE43, sqrt/cutoff, sim, filter, bad action, quality, ROC, alarms)

| Member | Type | Written by | Logic |
|---|---|---|---|
| `Cfg_Tag`, `Cfg_Desc`, `Cfg_EU` | STRING | HMI | HMI-only / passthrough |
| `Inp_Raw` | INT | Pin | raw counts |
| `Inp_ChFault` | BOOL | Pin | -> field bad |
| `Cfg_RawMin/Max` | INT | HMI | span; equal -> config error -> PV bad, no divide |
| `Cfg_EUMin/Max` | REAL | HMI | span; equal -> config error -> PV bad |
| `Cfg_FiltTC` | REAL | HMI | 1st-order filter (s), <=0 off; re-init on start, recovery, sim change |
| `Cfg_SqrtExtract` | BOOL | HMI | sqrt of % (negative -> 0) |
| `Cfg_LoCutoff` | REAL | HMI | % below -> 0 % |
| `Cfg_BadLoPct/HiPct` | REAL | HMI | NE43 limits -> `Sts_URng`/`Sts_ORng` |
| `Cfg_BadAction` | INT | HMI | PV when bad: 0 hold, 1 subst, 2 EUMin, 3 EUMax (answers the prompt's "PV when bad" question: configurable per instance) |
| `Cfg_SubstPV` | REAL | HMI | substitute PV |
| `Sim_En` | BOOL | HMI | sim replaces field, field faults ignored |
| `Sim_PV` | REAL | HMI | simulated PV |
| `Val_PV` | REAL | PLC | final PV |
| `Val_PVPct` | REAL | PLC | % of EU span (guarded) |
| `Val_ROC` | REAL | PLC | EU/s over 1 s window; re-init on recovery/sim change |
| `Sts_Bad` | BOOL | PLC | field bad (not in sim) |
| `Sts_URng`, `Sts_ORng` | BOOL | PLC | NE43 under/over range |
| `Sts_Sim` | BOOL | PLC | = Sim_En |
| `Sts_Subst` | BOOL | PLC | bad action in use |
| `Sts_Quality` | INT | PLC | 0 good, 1 uncertain (sim, NE107 C/S), 2 bad |
| `Inp_NE107` | INT | Pin | 1 -> bad |
| `Sts_NE107` | INT | PLC | F bad; C sim or device C; S; M |
| `Alm_HH`, `Alm_H` | T_AlmLim | PLC | FB_AlmLim high on final PV; suppressed while bad |
| `Alm_L`, `Alm_LL` | T_AlmLim | PLC | FB_AlmLim low; suppressed while bad |
| `Alm_ROC` | T_AlmLim | PLC | FB_AlmLim high on ABS(Val_ROC); suppressed while bad |
| `Alm_Bad` | T_Alarm | PLC | cond = field bad AND NOT sim |

(c) Signal-source table

| State | PV | Quality | NE107 | Process alarms |
|---|---|---|---|---|
| Field good | scaled, filtered | 0 | 0 / device S, M | evaluated |
| Field bad (range, ChFault, NE107=1, config error) | per `Cfg_BadAction` | 2 | 1 F | suppressed (state G), `Alm_Bad` active |
| Sim | `Sim_PV` | 1 | 2 C | evaluated on Sim_PV, `Alm_Bad` cleared |
| First scan | filter/ROC initialised to current value | as above | as above | cleared |

(d) Alarms

| Alarm | Condition | Limit / deadband | Delays |
|---|---|---|---|
| Alm_HH | PV > Lim, RTN at Lim-DB | `Alm_HH.Cfg_Lim/Cfg_DB` | `Alm_HH.Cfg_OnDly/OffDly` |
| Alm_H | PV > Lim | `Alm_H.*` | `Alm_H.*` |
| Alm_L | PV < Lim, RTN at Lim+DB | `Alm_L.*` | `Alm_L.*` |
| Alm_LL | PV < Lim | `Alm_LL.*` | `Alm_LL.*` |
| Alm_ROC | ABS(ROC) > Lim (EU/s) | `Alm_ROC.*` | `Alm_ROC.*` |
| Alm_Bad | field bad, not sim | - | `Alm_Bad.*` |

Limit alarms ship `Cfg_En = FALSE` (type init); enable after rationalisation.

## FB_DI

(a) Pins: `UDT_Data : T_DI` (IN_OUT); `Raw : BOOL` (IN -> Inp_Raw); `ChFault : BOOL` (IN -> Inp_ChFault); `Val : BOOL` (OUT = `Val`).

(b) Members

| Member | Type | Written by | Logic |
|---|---|---|---|
| `Cfg_Tag`, `Cfg_Desc` | STRING | HMI | passthrough |
| `Inp_Raw` | BOOL | Pin | raw |
| `Inp_ChFault` | BOOL | Pin | -> Sts_Bad |
| `Cfg_Invert` | BOOL | HMI | x := Inp_Raw XOR Cfg_Invert |
| `Cfg_OnDly` | TIME | HMI | TON debounce on x |
| `Cfg_OffDly` | TIME | HMI | TOF debounce: Val := TOF(TON(x)) |
| `Cfg_AlmMode` | INT | HMI | 0 none, 1 alarm Val TRUE, 2 alarm Val FALSE -> `Alm.Inp_Cond` |
| `Cfg_TrueText`, `Cfg_FalseText` | STRING | HMI | passthrough |
| `Sim_En` | BOOL | HMI | Val := Sim_Val (no debounce), ChFault ignored |
| `Sim_Val` | BOOL | HMI | simulated value |
| `Val` | BOOL | PLC | conditioned value. While bad (not sim): **holds last value** (see Q11) |
| `Sts_Bad` | BOOL | PLC | ChFault AND NOT sim |
| `Sts_Sim` | BOOL | PLC | = Sim_En |
| `Sts_NE107` | INT | PLC | 1 bad, 2 sim, else 0 |
| `Val_Transitions` | UDINT | PLC | +1 on Val FALSE->TRUE (prev-state BOOL) |
| `Alm` | T_Alarm | PLC | per Cfg_AlmMode; suppressed while bad |
| `Alm_Bad` | T_Alarm | PLC | cond = Sts_Bad |

(c) Signal-source table: field good -> debounced; field bad -> Val held, `Alm` suppressed, `Alm_Bad`; sim -> Sim_Val; first scan -> Val := x without delay, counter not incremented.
(d) Alarms: `Alm` (state alarm, delays from `Alm.Cfg_OnDly/OffDly` on top of the debounce), `Alm_Bad`.
