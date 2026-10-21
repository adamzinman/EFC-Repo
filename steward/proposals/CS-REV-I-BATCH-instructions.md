# Controls Standard rev I: batch instructions (rows 1-3 of DOC-QUEUE)

Instructions for an agent working on the EFC Controls Standard (LaTeX, Google Drive folder `Claude/Controls Standard`, **revision I**). Apply the edits in the order given below, then stop and report. Do not change anything else, do not bump the revision letter, do not regenerate whole files, and do not compile until Adam asks. Each edit names its file and quotes its anchor. Anchors were checked verbatim against rev I (Drive folder `Claude/Controls Standard`, `revision.tex` = I) on 2026-10-21; the result for each is in the Anchor check table below. If an anchor has moved when an edit is applied, stop and report.

Sources: `steward/proposals/CS-REV-I-heaters-instructions.md` (row 1), `CS-REV-I-hmi-rules-instructions.md` (row 2), `CS-REV-I-library-build-instructions.md` (row 3). The text below is copied from those files; where they overlap, the duplicate was removed as noted.

## Decisions needed before applying

1. **Rev I source found (2026-10-21).** In Drive `Claude/Controls Standard`, `revision.tex` = I (`\newcommand{\documentrevision}{I}`). The rev I section files are in the `sections/`, `appendices/` and `references/` subfolders. `sections/heaters.tex` and `sections/hmi-dynamic-windows.tex` are not in Drive; that is expected, because both are new files created by these edits.
2. **Wrong path in row 2 Edit 6 and row 1 Edit 4.** Both point at `Claude outputs/REV-I-CHANGES.md`, a Drive folder path to a different copy of the log (2026-10-16). Use `references/REV-I-CHANGES.md` (Drive `references` folder, 2026-10-14 copy, exists in rev I). Append; do not create. The three REV-I entries (H1, H2, H3 below) go in that one file. That copy stops at item 8; the `Claude outputs` copy has items 9-10 (2026-10-15), so the next number is 11 once the two copies are reconciled (open item).
3. **Dropped:** row 2 Edit 5. It is superseded by Edit 8 (G1). Do not apply it.
4. **Dedupe:** row 2 Edit 1 and row 3 Edit 3 both touch `sections/hmi-dynamic-windows.tex`; row 3 Edit 3 is appended to that file's table block (B2). Row 2 Edit 8 and row 3 Edit 2 both touch the appendix; they are different paragraphs (G1 shell and dynamic window, G2 Templates).
5. **Resolved 2026-10-21 (all style classes -> EFC_Styles, see G2).** Background: Rev I wording, `appendices/perspective-screen-design.tex`, Templates section (checked 2026-10-21): "All template text uses the dp style classes." The Text Scaling Standard in the same appendix defines the `dp` unit (a `--dp` CSS variable) and says "Text sizes are applied through Style Classes", with suggested classes Text/Small to Text/Title. The name `EFC_Styles` does not appear in the rev I files checked (Ch6, Ch7, Ch11, Appendix I, and the screen-design appendix). Adam confirmed: EFC_Styles is the class library name; apply G2a-c.
6. **Policy (decided 2026-10-21):** Edit D: safety-related signals can never be bypassed in software. HMI bypass by Supervisor+ with reason is exempt from the two-person / MOC rule only for conditions engineering configured as bypassable (Cfg_Bypassable, never on safety conditions).
7. **Policy (decision 24 vs 26):** the expanded trend stays inside the 400 x 860 window (decision 26). Decision 24's "about 50 %" is not used anywhere in this batch.

---

## Anchor check (rev I, Drive folder, 2026-10-21)

`revision.tex` = I. Each anchor below was searched verbatim in the rev I file named. Found = keep; moved = replace with rev I text (none needed); missing = flag (none).

| Edit | Rev I file | Anchor | Result |
|---|---|---|---|
| A | sections/heaters.tex | new file | not in Drive; create (expected) |
| B | sections/hmi-dynamic-windows.tex | new file | not in Drive; create (expected) |
| C | sections/06-hardware.tex | `\subsection{Standard Air Prep Unit}\label{sec:air-prep}` | found, keep |
| D | sections/07-software.tex | `\item A force or bypass on an interlock ... (Section~\ref{sec:review-release}).` | found, keep |
| E1 | sections/11-scada-standards.tex | `Perspective screens follow the Perspective Screen Design Standard in Appendix~\ref{app:screen-design}.` | found, keep (`ch:scada` exists, no fallback) |
| E2 | sections/11-scada-standards.tex | `\section{Alarms}` | found, keep |
| E3 | sections/11-scada-standards.tex | `Acknowledging an alarm does not clear the process condition that caused it.` | found, keep |
| E4 | sections/11-scada-standards.tex | `\subsection*{Roles and audit}` and its paragraph | found, keep |
| F-3a | appendices/data-types-future.tex | row `Control module &` containing `\texttt{T\_VFD}, ` | found, keep |
| F-3b | appendices/data-types-future.tex | row `\hyperref[sec:pclib-t-vfd]` | found, keep |
| F-3c | appendices/data-types-future.tex | `\subsection{T\_PID}\label{sec:pclib-t-pid}` | found, keep |
| G1-8a | appendices/perspective-screen-design.tex | `\textbf{Trends / dynamic window.}` paragraph (Old text) | found verbatim, keep |
| G1-8b | appendices/perspective-screen-design.tex | Shell Layout row `Trends / dynamic window & 400 $\times$ 860 & 79.17\% ...` | found verbatim, keep |
| G1-8c | appendices/perspective-screen-design.tex | `The trends/dynamic window is 400 design px wide, ...` | found verbatim, keep |
| G2 | appendices/perspective-screen-design.tex | `All template text uses the dp style classes.` | found verbatim, keep (see Decision 5) |
| H1-H3 | references/REV-I-CHANGES.md | append after the numbered list | file exists in rev I; path fixed (Decision 2) |

Totals: 13 anchors kept, 0 moved, 0 missing. Path fixes: 3 (H1, H2, H3 and the row 1 Edit 4 heading). New files: 2.

---

### A. New file sections/heaters.tex (row 1 Edit 1)

Create it with exactly this content:

```latex
\subsection{Electric Heaters}\label{sec:heaters}\newmark
Electric heaters (band, cartridge, immersion, jacket and duct heaters) are switched in one of three ways. The method is chosen per heater and set in the \texttt{T\_Heater} data type with \texttt{Cfg\_CtrlType} (Appendix~\ref{app:data-types-future}). The PLC logic, alarms and HMI dynamic window are the same for all three, so the method can be changed later without reworking the program or the screens.

\begin{small}
\setlength{\tabcolsep}{4pt}
\begin{longtable}{@{}P{2.6cm}P{4.6cm}P{4.4cm}P{4.6cm}@{}}
\caption{Electric Heater Control Methods}\label{tab:heater-methods} \\
\toprule
\rowcolor{tblhead}\textbf{Method} & \textbf{How power is set} & \textbf{Use when} & \textbf{Notes} \\
\midrule
\endfirsthead
\multicolumn{4}{@{}l}{\small\textit{Table \thetable{} continued}} \\
\toprule
\rowcolor{tblhead}\textbf{Method} & \textbf{How power is set} & \textbf{Use when} & \textbf{Notes} \\
\midrule
\endhead
On/off contactor (\texttt{Cfg\_CtrlType = 0}) & Full power or none. A PLC output drives the heater contactor; temperature is held by on/off control with hysteresis. & Large thermal mass, coarse control: trace heating, freeze protection, tank heaters. & Contactors wear with every operation, so set the hysteresis wide enough to keep switching to a few cycles per hour. \\
Time-proportioned SSR (\texttt{Cfg\_CtrlType = 1}) & Duty cycle. A PLC transistor output drives a zero-cross solid-state relay (SSR). The output is on for the demanded percentage of a fixed cycle time, e.g.\ 62\,\% of a 4~s cycle is 2.5~s on, 1.5~s off. & Most process heaters that need tight temperature control: the PID output sets the duty. & Default cycle time 4~s (range 2--10~s): shorter cycles give smoother temperature but more element thermal cycling. Minimum pulse 100~ms. Use a transistor output, never a relay output. \\
SCR power controller (\texttt{Cfg\_CtrlType = 2}) & The PLC sends a 0--100\,\% power reference (4--20~mA or network) to an SCR (thyristor) controller, which switches the load itself. & Large loads, multiple zones, fast processes, or where the controller's current limit and load-failure detection are wanted. & Use burst / zero-cross firing by default (low electrical noise). Use phase-angle firing only where the load requires it (infrared lamps, low cold-resistance elements, transformer-coupled loads); it creates harmonics and radio-frequency noise. \\
\bottomrule
\end{longtable}
\end{small}

\subsubsection*{Required for every electric heater}
\begin{itemize}[itemsep=2pt]
  \item \textbf{Independent excess-temperature limit.} A separate limit controller with its own sensor, hardwired so that it opens the heater contactor coil circuit directly, latching, and reset only at the device. The PLC monitors its status (\texttt{Inp\_HiLimitOK}) but is never part of the limit circuit, and the control loop sensor is never used as the limit sensor. Where NFPA~86 applies (ovens, furnaces, process heaters in its scope) the limit controller must be listed for the purpose; confirm the adopted edition and its requirements with the authority having jurisdiction.
  \item \textbf{Series isolating contactor upstream of every SSR or SCR.} Solid-state switches normally fail shorted, so the heater would stay on regardless of the PLC output. The contactor is opened by the excess-temperature limit, the E-stop, an interlock trip, and by the PLC when it sees heater current with the output off (\texttt{Sts\_Shorted}).
  \item \textbf{Current monitoring.} A current transformer per heater, or current feedback from the SCR controller, for heaters above \tbd~kW. The PLC compares the current with what is expected at the present duty and raises a partial load failure (a lost element, fuse or phase) when it falls below \texttt{Cfg\_LoadFailPct} (default 80\,\%).
  \item \textbf{Semiconductor protection and heat.} Protect SSRs and SCR controllers with semiconductor (high-speed) fuses sized to the device's I\textsuperscript{2}t rating, and coordinate them with the panel SCCR (Section~\ref{sec:sccr}). Size SSRs from the manufacturer's derating curve at the panel's maximum internal temperature, mount them on the specified heat sink, and include their dissipation (roughly 1--1.5~W per ampere of load) in the panel heat calculation (Section~\ref{sec:heat}).
\end{itemize}

\subsubsection*{Control}
\begin{itemize}[itemsep=2pt]
  \item A temperature loop (\texttt{T\_PID}) writes its output to the heater's \texttt{Prog\_Pwr}; \texttt{Cfg\_PwrMin}, \texttt{Cfg\_PwrMax} and \texttt{Cfg\_PwrRate} limit it. Do not run a PID loop through an on/off contactor: use an SSR or SCR when proportional control is needed.
  \item Use \texttt{Cfg\_PwrRate} as a soft start for elements that absorb moisture when idle (mineral-insulated, cartridge, immersion), following the heater manufacturer's start-up instructions.
  \item On the HMI, the heater's dynamic window shows demand and applied power, the on/off cycle for SSR heaters, current and load percentage, and the limit, shorted and load-failure alarms.
\end{itemize}
\note{Open: set the heater size above which current monitoring is required (TBD above). NFPA~86 clause references to be confirmed against the edition adopted at each site.}
```
### B. New file sections/hmi-dynamic-windows.tex (row 2 Edit 1; row 3 Edit 3 appended to its table block)

Create it with exactly this content:

```latex
\section[Dynamic Windows]{Dynamic Windows \newmark}\label{sec:hmi-dynamic-windows}
Every equipment template opens a dynamic window: a panel on the right of the screen that shows the device's state, mode, commands, permissives, interlocks, alarms and history. Equipment of the same kind shares one dynamic window (Table~\ref{tab:hmi-dw-ids}), so a valve, motor or loop looks and works the same on every screen.

\begin{small}
\begin{longtable}{@{}P{3.6cm}P{12.6cm}@{}}
\caption{Dynamic Windows}\label{tab:hmi-dw-ids} \\
\toprule
\rowcolor{tblhead}\textbf{Window id} & \textbf{Used by} \\
\midrule
\endfirsthead
\multicolumn{2}{@{}l}{\small\textit{Table \thetable{} continued}} \\
\toprule
\rowcolor{tblhead}\textbf{Window id} & \textbf{Used by} \\
\midrule
\endhead
\texttt{dw\_ValveDiscrete} & On/off valves (\texttt{T\_DValve}) \\
\texttt{dw\_ValveAnalog} & Control valves (\texttt{T\_CValve}) \\
\texttt{dw\_Rotating} & Fixed-speed motors, pumps, fans, agitators and compressors (\texttt{T\_Motor}) \\
\texttt{dw\_VFD} & Variable-speed drives (\texttt{T\_VFD}) \\
\texttt{dw\_Heater} & Electric heaters (\texttt{T\_Heater}) \\
\texttt{dw\_HeatTransfer} & Heat exchangers (\texttt{T\_HeatEx}) \\
\texttt{dw\_ProcessValue} & Analog process values and indicators (\texttt{T\_AI}) \\
\texttt{dw\_Loop} & PID loops (\texttt{T\_PID}), including tuning \\
\texttt{dw\_Station} & Fill stations \\
\texttt{dw\_IOCard} & PLC I/O cards and racks (diagnostics) \\
\bottomrule
\end{longtable}
\end{small}

I/O card, rack and power-supply faceplates bind directly to the Modicon x80 device DDTs from Control Expert, which are imported into Ignition as-is; there is no PCLib type for them (\texttt{T\_IOCard} and \texttt{T\_IORack} are removed), and the window id \texttt{dw\_IOCard} is kept.

\subsection[Size, Opening and Closing]{Size, Opening and Closing \newmark}\label{sec:hmi-dw-open}
\begin{itemize}[itemsep=1pt]
  \item \textbf{Size and position.} The dynamic window fills the full height between the header and the alarm bar, in the right-hand region of the shell: 400 $\times$ 860 at 1920 $\times$ 1080 (37.04\,vh wide, 79.63\,vh tall), and 800 $\times$ 1720 at 3840 $\times$ 2160 (Appendix~\ref{app:screen-design}).
  \item \textbf{Opening.} A single click or tap on the template symbol opens its dynamic window. The click target is the whole symbol bounding box, at least 44 design px in each direction.
  \item \textbf{Closing.} The close button returns the right-hand region to the screen's default view. Each screen view has a \texttt{defaultDock} view parameter that names it (normally the screen's trends), and \texttt{setDefaultDock} sets it on startup.
\end{itemize}

\subsection[Layout and Buttons]{Layout and Buttons \newmark}\label{sec:hmi-dw-layout}
Sections appear in this order; a section that does not apply to the device is left out:
\begin{enumerate}[itemsep=1pt]
  \item Header: tag, description and close button.
  \item State.
  \item Mode.
  \item Commands.
  \item Permissives.
  \item Interlocks.
  \item Alarms: active alarms are listed; inactive alarms are folded.
  \item History: an 8~h state strip and the most recent events.
  \item Maintenance and Configuration: collapsed by default and shown only to the roles in Table~\ref{tab:hmi-roles}. Loop tuning is done here, in \texttt{dw\_Loop}; there is no separate tuning popup.
\end{enumerate}
Buttons come in two sizes so that every dynamic window looks the same:
\begin{itemize}[itemsep=1pt]
  \item \textbf{Command tier} (mode AUTO /\allowbreak{} MAN /\allowbreak{} MAINT /\allowbreak{} OOS, OPEN /\allowbreak{} CLOSE, START /\allowbreak{} STOP, RESET, JOG, FWD /\allowbreak{} REV): one size, 72 $\times$ 30 design px, style \texttt{Button/Default}. The button for the current state is highlighted with \texttt{Button/Toggle/On}.
  \item \textbf{Secondary tier} (BYPASS, UNBYP, ACK, RESET LATCHED, RESET MAINT, SIMULATE, analog valve presets 0 /\allowbreak{} 25 /\allowbreak{} 50 /\allowbreak{} 75 /\allowbreak{} 100\,\%): one smaller size, style \texttt{Button/Small}.
  \item \texttt{Button/Danger} is used only for the confirm action in the bypass confirmation (Section~\ref{sec:hmi-bypass}).
\end{itemize}

\subsection[Touch Operation]{Touch Operation \newmark}\label{sec:hmi-touch}
In touch mode (template parameter \texttt{useButton = false}) a double tap on the symbol of a two-state device (\texttt{T\_DValve}, \texttt{T\_Motor}) sends the toggle command (open /\allowbreak{} close, start /\allowbreak{} stop). It is sent only when the device is in Manual and available, and is not interlocked, in local or faulted; otherwise the double tap does nothing. Each template has a \texttt{dblCmd} parameter (default on) to turn this off. Analog devices (control valves, drives, loops) take commands from the dynamic window only.

\subsection[Permissives, Interlocks and Bypass]{Permissives, Interlocks and Bypass \newmark}\label{sec:hmi-bypass}
The Permissives and Interlocks sections list each condition by name (\texttt{Cfg\_CondDesc} in \texttt{T\_Intlk}, Section~\ref{sec:pclib-t-intlk}) with its state, and mark the first-out, latched and bypassed conditions.
\begin{itemize}[itemsep=1pt]
  \item \textbf{Who.} Bypass and unbypass need the Supervisor role or higher. The BYPASS button is shown only for conditions configured as bypassable (\texttt{Cfg\_Bypassable}) and works only while the bypass authorisation \texttt{Inp\_BypassPerm} is on.
  \item \textbf{Confirmation.} BYPASS opens a confirmation (\texttt{Docks/Parts/BypassConfirm}). The user picks a duration from the presets 1~h, 2~h, 4~h and 8~h, limited to the group's maximum (\texttt{Cfg\_BypassMax}), and must enter a reason. The bypass is not applied without a reason.
  \item \textbf{Indication.} Each bypassed condition shows its own time left and an audit line: who bypassed it, their role, when, and the reason.
  \item \textbf{Logging.} Bypass and unbypass are written to the Ignition audit log (Section~\ref{sec:ignition-roles}).
  \item \textbf{Rule.} A bypass made this way from the HMI, on a condition configured as bypassable, is exempt from the second-person and approved MOC requirement in Section~\ref{sec:online-changes}. Safety-related signals are never configured as bypassable and cannot be bypassed in software. PLC forces and logic changes are not exempt.
\end{itemize}
\future{Named permissive and interlock groups are to be embedded in the device types: \texttt{Perm : T\_Intlk} and \texttt{Intlk : T\_Intlk} in \texttt{T\_DValve}, \texttt{T\_Motor} and \texttt{T\_VFD}, \texttt{Intlk : T\_Intlk} in \texttt{T\_CValve} and \texttt{T\_PID}, and \texttt{Prot : T\_Intlk} in equipment modules. The existing \texttt{Inp\_IntlkOK} and \texttt{Inp\_PermOK} are kept and ANDed with the group. \texttt{T\_Intlk} gains \texttt{Sts\_BypLeft : ARRAY[0..15] OF TIME} so the time left can be shown per condition; until then only the time left on the oldest bypass (\texttt{Sts\_BypassLeft}) is available.}

\subsection[Trends]{Trends \newmark}\label{sec:hmi-trends}
Trends in a dynamic window show the last 30~minutes by default. Every graph has an expand button. Expanding a graph keeps the dynamic window at 400 $\times$ 860 design px and the right-hand region never changes width: the graph fills the window below its header (about 400 $\times$ 760 design px) with range buttons 5~m, 30~m, 1~h, 8~h and 24~h, pause /\allowbreak{} live and a collapse button. The other sections of the window are hidden until the graph is collapsed.
```
### B2. sections/hmi-dynamic-windows.tex, addition after the window table (row 3 Edit 3)

Not a separate edit. When row 2 Edit 1 inserts the dynamic-window table, add this paragraph directly after the table caption paragraph (the one that follows `tab:hmi-dw-ids`):

```latex
A template's \texttt{dockId} parameter overrides the default window chosen from its \texttt{tType} parameter, and \texttt{dwTagPath} overrides the bound tag. The \texttt{native} type opens the I/O card window; I/O card, rack and power-supply faceplates bind to the Modicon x80 device DDTs (decision 23).
```

---
### C. sections/06-hardware.tex (row 1 Edit 2)

Insert one line, followed by a blank line, immediately **before** this existing line (under `\section{Other Hardware}`, after the Solenoids subsection):

```latex
\subsection{Standard Air Prep Unit}\label{sec:air-prep}
```

Line to insert:

```latex
\input{sections/heaters}
```
### D. sections/07-software.tex, Online Changes and Forces (row 2 Edit 7)

Anchor (from `sections/07-software.tex`, section at `\label{sec:online-changes}`; the bullet is the third item of the `itemize`). Checked verbatim against rev I on 2026-10-21; the text below is the rev I line.

```latex
  \item A force or bypass on an interlock or safety-related signal needs a second person to check it and an approved MOC (Section~\ref{sec:review-release}).
```

Replace that line with exactly these two lines (Adam, 2026-10-21: safety signals cannot be bypassed through software):

```latex
  \item Safety-related signals (safety PLC and SIS functions, emergency stops, safety interlocks) are never forced or bypassed in software, from the HMI or in the PLC. They are defeated only through the hardware and procedures of the safety system.
  \item A force or bypass on a process interlock or permissive needs a second person to check it and an approved MOC (Section~\ref{sec:review-release}), except an HMI bypass of a condition that engineering has configured as bypassable (\texttt{Cfg\_Bypassable}). Such an HMI bypass is set by one user with the Supervisor role or higher from the dynamic window through the bypass confirmation, with a mandatory reason, a duration up to the configured maximum (\texttt{Cfg\_BypassMax}), and an entry in the audit log (Section~\ref{sec:hmi-bypass}); it needs no second person and no MOC. \texttt{Cfg\_Bypassable} is set during design and changed only under MOC, and is never set on a safety-related condition. PLC forces and logic changes keep the second-person and MOC requirement.
```

Checks for this edit: `sec:online-changes` and `sec:review-release` exist in rev I (grep `sections/`); `sec:hmi-bypass` is created by Edit 1 of this file, so Edit 1 must be applied first. Leave the existing `\note` at the top of the section (it says the policy is not yet enforced) unchanged; that is a separate decision.

Background: the anchor was checked against rev I (`sections/07-software.tex`, Drive, 2026-10-21) and matches verbatim. The section is in `07-software.tex`, not `10-plc-standards.tex`.

---
### E1. sections/11-scada-standards.tex, Perspective Design (row 3 Edit 1)

**Anchor** (`\section{Perspective Design}`, first paragraph; checked verbatim against rev I on 2026-10-21): the paragraph whose first sentence is
`Perspective screens follow the Perspective Screen Design Standard in Appendix~\ref{app:screen-design}.`

**Action:** insert the following as a new paragraph immediately after that paragraph. Do not change the anchor paragraph.

```latex
\paragraph{Script library.} Perspective screens call the project script library \texttt{efc.ui} (Ignition 8.1 and 8.3) for dynamic-window and command actions, so that every template behaves the same way. Template symbols call \texttt{openDynamic} on click and \texttt{dblCmd} on double-click in touch mode. Window close buttons call \texttt{closeDynamic}. The dynamic-window region calls \texttt{setDefaultDock} at startup to show its screen default view. \texttt{cmd} performs every command write after a role check. \texttt{bypass} and \texttt{unbypass} require Supervisor or higher and a reason, and write an audit entry. \texttt{ackAll}, \texttt{trend} and \texttt{level} provide alarm acknowledgement, trend display and the user's role level. Role levels and bypass rules follow Chapter~\ref{ch:scada} (\texttt{sec:ignition-roles}, \texttt{sec:hmi-bypass}).
```

**Check:** the label `ch:scada` may not exist. Grep `sections/` for `\label{ch:scada}`; if absent, delete the final sentence and use `Role levels and bypass rules follow Section~\ref{sec:ignition-roles} and Section~\ref{sec:hmi-bypass}.` instead (both labels are created by row 2 Edits 1 and 4).

---
### E2. sections/11-scada-standards.tex, include new section before Alarms (row 2 Edit 2)

Insert one line, followed by a blank line, immediately **before** this existing line (after the Perspective Design section):

```latex
\section{Alarms}
```

Line to insert:

```latex
\input{sections/hmi-dynamic-windows}
```
### E3. sections/11-scada-standards.tex, Alarms (row 2 Edit 3)

In the first paragraph under `\section{Alarms}`, immediately after the sentence

```latex
Acknowledging an alarm does not clear the process condition that caused it.
```

insert (same paragraph, one space before it):

```latex
Alarm shelving needs the Supervisor role and alarm-limit changes the Engineer role, and both are audit-logged (Table~\ref{tab:hmi-roles}). \newmark
```
### E4. sections/11-scada-standards.tex, Roles and audit (row 2 Edit 4)

Replace these two existing lines (under `\section{Security and Audit}`):

```latex
\subsection*{Roles and audit}
Use the approved identity provider when practical and assign access by role. Typical roles include operator, maintenance, engineering, supervisor, and administrator. Audit important actions such as setpoint changes, alarm shelving, recipe changes, and security administration.
```

with exactly this:

```latex
\subsection*{Roles and audit}\label{sec:ignition-roles}
Use the approved identity provider when practical and assign access by role. EFC uses six roles in a fixed order: Guest $<$ Operator $<$ Maintenance $<$ Supervisor $<$ Engineer $<$ Admin. Each role can do everything the roles below it can. The user's highest role is read once at login and held as a single session level, so a change to a user's roles takes effect at the next login. Screens compare that level with the level each action needs (Table~\ref{tab:hmi-roles}); controls that need a higher level than the user has are hidden. \newmark

\begin{small}
\begin{longtable}{@{}P{8.6cm}P{2.8cm}P{4.8cm}@{}}
\caption{Minimum Role for HMI Actions}\label{tab:hmi-roles} \\
\toprule
\rowcolor{tblhead}\textbf{Action} & \textbf{Minimum role} & \textbf{Audit log} \\
\midrule
\endfirsthead
\multicolumn{3}{@{}l}{\small\textit{Table \thetable{} continued}} \\
\toprule
\rowcolor{tblhead}\textbf{Action} & \textbf{Minimum role} & \textbf{Audit log} \\
\midrule
\endhead
View screens, trends and alarms & Guest & No \\
Mode AUTO /\allowbreak{} MAN, device commands in Manual, fault reset (Section~\ref{sec:pclib-modes}) & Operator & No \\
Alarm acknowledge, setpoint changes, reset of latched interlocks & \tbd & \tbd \\
Mode MAINT and OOS, JOG, simulation, maintenance resets (run time and counters) & Maintenance & No \\
Bypass and unbypass of permissives and interlocks (Section~\ref{sec:hmi-bypass}) & Supervisor & Yes, with reason \\
Alarm shelving & Supervisor & Yes \\
Alarm-limit changes & Engineer & Yes, old $\rightarrow$ new \\
Configuration and tuning (\texttt{Cfg\_} members, PID tuning) & Engineer & Yes, old $\rightarrow$ new \\
User and role administration & \tbd & Yes \\
\bottomrule
\end{longtable}
\end{small}

Bypass, unbypass, shelving, alarm-limit, configuration and tuning changes are written to the Ignition audit log with the old and new value, the user and role, the time, and the reason where one is entered. Also audit setpoint changes, recipe changes, and security administration.
\note{Open: minimum role for alarm acknowledge, setpoint changes and reset of latched interlocks, and which actions are reserved for Admin (TBD above).}
```
### F. appendices/data-types-future.tex, Appendix I (row 1 Edit 3)

This file has hand edits in rev I (for example T_DiaComp), so **splice; do not regenerate it**.

**3a. Control-module group list.** In the table row that starts with `Control module &` and lists `\texttt{T\_AI}, \texttt{T\_DI}, ...`, insert `\texttt{T\_Heater}, ` immediately after `\texttt{T\_VFD}, `.

**3b. Type index row.** In the type index table, insert this row immediately after the row that starts with `\hyperref[sec:pclib-t-vfd]`:

```latex
\hyperref[sec:pclib-t-heater]{\texttt{T\_Heater}} & Control module & MonBinDrv (on/\allowbreak{}off) /\allowbreak{} MonAnaDrv (SSR, SCR) & 64 & T\_Alarm, T\_Mode, T\_RunTime \\
```

**3c. Type section.** Insert this block immediately **before** the line `\subsection{T\_PID}\label{sec:pclib-t-pid}`:

```latex
\subsection{T\_Heater}\label{sec:pclib-t-heater}

Electric heater: on/\allowbreak{}off contactor, time-proportioned SSR, or SCR power controller.

\par\smallskip{\small \textbf{ISA-88 role:} Control module \quad \textbf{MTP:} MonBinDrv (on/\allowbreak{}off) /\allowbreak{} MonAnaDrv (SSR, SCR) \quad \textbf{Standards:} ISA-88 /\allowbreak{} IEC 61512-1, ISA-5.1, ISA-18.2 /\allowbreak{} IEC 62682, ISA-101.01, NAMUR NE107, VDI/\allowbreak{}VDE/\allowbreak{}NAMUR 2658-4 (MTP), IEC 60947-4-3 (semiconductor controllers, non-motor loads), NFPA 86 (excess-temperature limit)}\par

\begin{small}
\begin{longtable}{@{}P{3.70cm}P{2.20cm}P{1.70cm}P{8.91cm}@{}}
\caption{T\_Heater Members}\label{tab:pclib-t-heater} \\
\toprule
\rowcolor{tblhead}\textbf{Member} & \textbf{Type} & \textbf{Init} & \textbf{Description} \\
\midrule
\endfirsthead
\multicolumn{4}{@{}l}{\small\textit{Table \thetable{} continued}} \\
\toprule
\rowcolor{tblhead}\textbf{Member} & \textbf{Type} & \textbf{Init} & \textbf{Description} \\
\midrule
\endhead
\texttt{Cfg\_Tag} & \texttt{STRING[20]} &  & Equipment /\allowbreak{} instrument tag, e.g. FT-101 \\
\texttt{Cfg\_Desc} & \texttt{STRING[40]} &  & Description shown on HMI faceplate \\
\texttt{Mode} & \texttt{T\_Mode} &  & Mode block \\
\texttt{Inp\_ContactorFbk} & \texttt{BOOL} &  & Main /\allowbreak{} isolating contactor closed (aux contact) \\
\texttt{Inp\_Remote} & \texttt{BOOL} &  & Local/\allowbreak{}Remote switch in REMOTE \\
\texttt{Inp\_AvailOK} & \texttt{BOOL} &  & Supply available: breaker closed, control power OK \\
\texttt{Inp\_HiLimitOK} & \texttt{BOOL} &  & Independent excess-temperature limit healthy (hardwired, latching; PLC monitors only) \\
\texttt{Inp\_IntlkOK} & \texttt{BOOL} &  & Interlocks healthy (TRUE = may heat; FALSE trips) \\
\texttt{Inp\_PermOK} & \texttt{BOOL} &  & Permissives healthy (TRUE = may switch on) \\
\texttt{Inp\_IOFault} & \texttt{BOOL} &  & I/\allowbreak{}O channel or comms fault \\
\texttt{Inp\_Current} & \texttt{REAL} &  & Heater current from CT or SCR controller (A), optional \\
\texttt{Inp\_ScrAlarm} & \texttt{BOOL} &  & SCR controller alarm relay (fuse /\allowbreak{} partial load failure /\allowbreak{} overtemp) \\
\texttt{Cfg\_CtrlType} & \texttt{INT} & 0 & 0 = on/\allowbreak{}off (contactor), 1 = time-proportioned SSR on a PLC output, 2 = SCR power controller (analog reference) \\
\texttt{Cfg\_CycleTime} & \texttt{TIME} & T\#4S & Time-proportioning cycle (type 1): output is ON for Val\_Duty \% of each cycle \\
\texttt{Cfg\_MinPulse} & \texttt{TIME} & T\#100MS & Shortest ON or OFF pulse (type 1); shorter pulses are skipped \\
\texttt{Cfg\_ScrFiring} & \texttt{INT} & 0 & SCR firing mode set in the controller (type 2, documentation): 0 = burst /\allowbreak{} zero-cross, 1 = single-cycle, 2 = phase angle \\
\texttt{Cfg\_PwrMin} & \texttt{REAL} & 0.0 & Minimum power demand when on (\%) \\
\texttt{Cfg\_PwrMax} & \texttt{REAL} & 100.0 & Maximum power demand (\%) \\
\texttt{Cfg\_PwrRate} & \texttt{REAL} & 0.0 & Power ramp limit (\%/\allowbreak{}s), 0 = none (soft start for cold elements) \\
\texttt{Cfg\_RatedKW} & \texttt{REAL} & 0.0 & Heater rated power at 100 \% (kW) \\
\texttt{Cfg\_RatedAmps} & \texttt{REAL} & 0.0 & Heater current at 100 \% (A); 0 = no current monitoring \\
\texttt{Cfg\_LoadFailPct} & \texttt{REAL} & 80.0 & Partial load failure: current below this \% of expected while heating \\
\texttt{Cfg\_LeakAmps} & \texttt{REAL} & 1.0 & Current above this while the output is off = SSR /\allowbreak{} SCR shorted (A) \\
\texttt{Cfg\_FbkTime} & \texttt{TIME} & T\#3S & Time allowed for contactor feedback and current to settle \\
\texttt{Cmd\_On} & \texttt{BOOL} &  & Operator on (one-shot) \\
\texttt{Cmd\_Off} & \texttt{BOOL} &  & Operator off (one-shot) \\
\texttt{Cmd\_Reset} & \texttt{BOOL} &  & Fault /\allowbreak{} trip reset (one-shot) \\
\texttt{Cmd\_Pwr} & \texttt{REAL} &  & Operator power demand (\%), Manual mode, types 1 and 2 \\
\texttt{Prog\_On} & \texttt{BOOL} &  & Program /\allowbreak{} sequence on request (Auto mode) \\
\texttt{Prog\_Off} & \texttt{BOOL} &  & Program /\allowbreak{} sequence off request (Auto mode) \\
\texttt{Prog\_Pwr} & \texttt{REAL} &  & Program power demand (\%), Auto mode, e.g. a T\_PID Out\_CV \\
\texttt{Out\_Contactor} & \texttt{BOOL} &  & Main /\allowbreak{} isolating contactor (opened on trip, high limit or shorted SSR) \\
\texttt{Out\_SSR} & \texttt{BOOL} &  & Time-proportioned output to the SSR (type 1) \\
\texttt{Out\_PwrRef} & \texttt{REAL} &  & Power reference to the SCR controller, 0-100 \% (type 2) \\
\texttt{Sim\_En} & \texttt{BOOL} &  & Simulation: ignore field I/\allowbreak{}O, logic generates feedback \\
\texttt{Sts\_On} & \texttt{BOOL} &  & On: contactor closed and enabled to heat \\
\texttt{Sts\_Off} & \texttt{BOOL} &  & Off \\
\texttt{Sts\_Heating} & \texttt{BOOL} &  & Output conducting now (on/\allowbreak{}off: on; SSR: inside the ON part of the cycle; SCR: reference \textgreater{} 0) \\
\texttt{Sts\_Avail} & \texttt{BOOL} &  & Available to Auto/\allowbreak{}program control \\
\texttt{Sts\_Intlk} & \texttt{BOOL} &  & Interlock not healthy \\
\texttt{Sts\_NotPerm} & \texttt{BOOL} &  & Permissive not healthy \\
\texttt{Sts\_Local} & \texttt{BOOL} &  & In local control \\
\texttt{Sts\_HiLimit} & \texttt{BOOL} &  & Excess-temperature limit tripped (reset at the limit device) \\
\texttt{Sts\_LoadFail} & \texttt{BOOL} &  & Partial load failure (element, fuse or phase lost) \\
\texttt{Sts\_Shorted} & \texttt{BOOL} &  & Current while output off: SSR /\allowbreak{} SCR failed shorted, contactor opened \\
\texttt{Sts\_Tripped} & \texttt{BOOL} &  & Tripped --- reset required \\
\texttt{Sts\_Fault} & \texttt{BOOL} &  & Any fault present \\
\texttt{Sts\_Sim} & \texttt{BOOL} &  & Simulation active \\
\texttt{Sts\_State} & \texttt{INT} &  & 0=Off 1=Switching on 2=On 3=Switching off 4=Tripped 5=Not available \\
\texttt{Sts\_NE107} & \texttt{INT} &  & NAMUR NE107 status: 0=Good 1=Failure (F) 2=Function check (C) 3=Out of specification (S) 4=Maintenance required (M) \\
\texttt{Val\_PwrDemand} & \texttt{REAL} &  & Power demand after limits and ramp (\%) \\
\texttt{Val\_Duty} & \texttt{REAL} &  & Applied duty /\allowbreak{} power (\%): on/\allowbreak{}off 0 or 100, SSR ON-time fraction, SCR reference \\
\texttt{Val\_Power} & \texttt{REAL} &  & Estimated power (kW) = Val\_Duty x Cfg\_RatedKW, or from current \\
\texttt{Val\_Current} & \texttt{REAL} &  & Heater current (A) \\
\texttt{Val\_LoadPct} & \texttt{REAL} &  & Measured current as \% of expected at the present duty \\
\texttt{Val\_Energy} & \texttt{LREAL} &  & Energy total (kWh) \\
\texttt{Alm\_HiLimit} & \texttt{T\_Alarm} &  & Excess-temperature limit tripped \\
\texttt{Alm\_Shorted} & \texttt{T\_Alarm} &  & SSR /\allowbreak{} SCR shorted --- current with output off \\
\texttt{Alm\_LoadFail} & \texttt{T\_Alarm} &  & Partial load failure \\
\texttt{Alm\_FailOn} & \texttt{T\_Alarm} &  & No contactor feedback /\allowbreak{} current within Cfg\_FbkTime \\
\texttt{Alm\_FailOff} & \texttt{T\_Alarm} &  & Contactor feedback still present after off \\
\texttt{Alm\_ScrFault} & \texttt{T\_Alarm} &  & SCR controller alarm \\
\texttt{Alm\_IntlkTrip} & \texttt{T\_Alarm} &  & Tripped by interlock \\
\texttt{Run} & \texttt{T\_RunTime} &  & On hours /\allowbreak{} switch-on count \\
\bottomrule
\end{longtable}
\end{small}
```

If the appendix states a total number of types anywhere, add one to it.
### G1. appendices/perspective-screen-design.tex, shell layout and dynamic window (row 2 Edit 8; supersedes row 2 Edit 5, which is dropped)

This replaces the cross-reference that Edit 5 would have added. The sentence in 8a is part of the new paragraph: do not add it a second time. Anchors are quoted from rev I.

**8a.** Under `\section{Navigation and Dynamic Content}`, replace the whole paragraph that starts `\textbf{Trends / dynamic window.}` (quoted verbatim below) with the new paragraph. The message-handler alternative in the old text is removed; `efc.ui` does not use it.

Old:

```latex
\textbf{Trends / dynamic window.} The right-hand Embedded View's path and params are bound to session custom properties (for example \texttt{session.\allowbreak{}custom.\allowbreak{}trend.\allowbreak{}view} and \texttt{session.\allowbreak{}custom.\allowbreak{}trend.\allowbreak{}params}). Clicking equipment on a process screen writes to these properties to change the panel's content. A message handler on the shell (\texttt{system.\allowbreak{}perspective.\allowbreak{}sendMessage}) is an acceptable alternative.
```

New:

```latex
\textbf{Trends / dynamic window.} The right-hand region of the shell is one Embedded View, the dynamic window. Its path and params are bound to a per-page session value, \texttt{session.\allowbreak{}custom.\allowbreak{}efcDw[pageId]}, which holds the current view path, the params and the screen's default view. The project-library script \texttt{efc.ui} writes that value. A click on a template symbol calls \texttt{openDynamic} and shows that device's dynamic window for its tag path. The close button calls \texttt{closeDynamic}, which returns the region to the screen's default view. An expanded trend graph fills the dynamic window below its header; the window keeps its size and the right-hand region never changes width. Each screen view names its default view in the \texttt{defaultDock} view parameter, which \texttt{setDefaultDock} reads on startup. The region is sized in viewport height: 37.04\,vh wide and 79.63\,vh tall, the full height between the header and the alarm bar (400 $\times$ 860 at 1920 $\times$ 1080; 800 $\times$ 1720 at 3840 $\times$ 2160). There are no Perspective docks and no per-project page or dock configuration. What the dynamic window shows and how it opens and closes is set in Section~\ref{sec:hmi-dynamic-windows}. \newmark
```

**8b.** In the Shell Layout table, replace this row (first column only; the 4K table row `Trends / dynamic window & 400 $\times$ 860 & 800 $\times$ 1720` is unchanged, so 800 px at 4K stays):

Old:

```latex
Trends / dynamic window & 400 $\times$ 860 & 79.17\% & 7.41\% & 20.83\% & 79.63\% \\
```

New:

```latex
Trends / dynamic window (37.04\,vh wide, 79.63\,vh tall) & 400 $\times$ 860 & 79.17\% & 7.41\% & 20.83\% & 79.63\% \\
```

**8c.** In the paragraph after that table, replace this sentence:

Old:

```latex
The trends/dynamic window is 400 design px wide, which renders at 800\,px on a 3840 $\times$ 2160 display (its largest size) and scales down proportionally on smaller displays.
```

New:

```latex
The trends/dynamic window fills the full height between the header and the alarm bar: 400 $\times$ 860 design px at 1920 $\times$ 1080 (37.04\,vh wide, 79.63\,vh tall), which renders at 800 $\times$ 1720\,px on a 3840 $\times$ 2160 display (its largest size) and scales down proportionally on smaller displays. When a trend graph is expanded, the graph fills the window below its header and the window keeps its size; the region never changes width (Section~\ref{sec:hmi-trends}).
```

---
### G2. appendices/perspective-screen-design.tex, style classes -> EFC_Styles (row 3 Edit 2; Adam, 2026-10-21: change all style classes to EFC_Styles)

**G2a. Anchor** (`\section{Templates}`, second paragraph; checked verbatim against rev I on 2026-10-21): the sentence
`All template text uses the dp style classes.`

Replace that sentence (only that sentence) with:

```latex
All template text and styling uses the \texttt{EFC\_Styles} classes; templates carry no static inline styles. Generators move static inline styles into generated classes (for example \texttt{Loop/*}, \texttt{Indicator/Analog/*} and \texttt{Station/*}). Spacing uses the \texttt{Util/Gap} classes \texttt{XS}, \texttt{S}, \texttt{M} and \texttt{L}.
```

**G2b. Text Scaling Standard** (same appendix): the sentence that says text sizes are applied through Style Classes, and its list of suggested classes (Text/Small to Text/Title). Change "Style Classes" to "\texttt{EFC\_Styles} classes" and replace the suggested class names with the EFC_Styles text classes: \texttt{Text/Size/XXS}, \texttt{XS}, \texttt{S}, \texttt{M}, \texttt{L}, \texttt{XL}, \texttt{XXL}, \texttt{XXXL}, plus the role classes \texttt{Text/Label}, \texttt{Text/Value}, \texttt{Text/Title}. Keep the \texttt{dp} unit and the \texttt{--dp} CSS variable text unchanged: dp is the unit, EFC_Styles is the class library.

**G2c. Everywhere else:** search every `.tex` file for "style class" / "style classes" (any case). Where it names the class library, use "\texttt{EFC\_Styles} classes". Leave generic mentions of Perspective's Style Classes feature as they are. List each change in the report.

---
### H1. references/REV-I-CHANGES.md, row 2 entry (row 2 Edit 6)

Append this item to the numbered list of applied changes (use the next free number in place of N):

```
N. Ch11 SCADA: Roles and audit rewritten (label sec:ignition-roles): role hierarchy Guest < Operator < Maintenance < Supervisor < Engineer < Admin, one session level at login, controls hidden below the required level, Table tab:hmi-roles (MAINT/OOS, JOG, simulation, maintenance resets = Maintenance; bypass and shelving = Supervisor; alarm limits, configuration and tuning = Engineer), audit-log content. New section Dynamic Windows (sections/hmi-dynamic-windows.tex, \input before Alarms): window ids (Table tab:hmi-dw-ids), size, open/close and defaultDock, section order, button tiers, touch double-tap (dblCmd), named permissives/interlocks and bypass (BypassConfirm, presets 1/2/4/8 h up to Cfg_BypassMax, mandatory reason, time left and audit line per condition; T_Intlk embedding as \future), trends (30 min default; expand keeps the window at 400 x 860 and fills it below the header, about 400 x 760, with ranges 5 m to 24 h, pause/live and collapse; the region never changes width; decision 26). I/O card, rack and power-supply faceplates bind directly to the Modicon x80 device DDTs from Control Expert (no PCLib type; decision 23). Alarms: shelving/limit roles sentence. Appendix Perspective Screen Design: Trends / dynamic window paragraph and shell table rewritten as the embedded-view dynamic window (efc.ui session value, openDynamic/closeDynamic, defaultDock, sizes in vh; Edit 8), which settles the former dock-vs-embedded-view question. Section Online Changes and Forces (sec:online-changes): HMI bypass by one Supervisor-or-higher user with a mandatory reason, up to the configured maximum, audit-logged, is exempt from the second-person and MOC requirement; PLC forces and logic changes keep it (Edit 7, cross-ref sec:hmi-bypass).
```

Add to its "Still open (need Adam)" list:

```
- Minimum role for alarm acknowledge, setpoint changes and reset of latched interlocks (tab:hmi-roles).
- Which actions are Admin-only, e.g. user and role administration (tab:hmi-roles).
```
### H2. references/REV-I-CHANGES.md, row 1 entry (row 1 Edit 4)

Append this item to the numbered list of applied changes (use the next free number in place of N):

```
N. Ch6 Other Hardware: new subsection Electric Heaters (sections/heaters.tex, \input before Standard Air Prep Unit): on/off contactor, time-proportioned SSR (duty cycle) and SCR power controller methods (Table tab:heater-methods); required independent excess-temperature limit, series isolating contactor, current monitoring, semiconductor fuses and SSR heat. Appendix I: added T_Heater (64 members) after T_VFD; index row and Control module list updated. Open: kW threshold for current monitoring (\tbd); NFPA 86 clause references to confirm against the adopted edition.
```

Add to its "Still open (need Adam)" list:

```
- Heater size (kW) above which current monitoring is required (sec:heaters).
- NFPA 86 clause references for the excess-temperature limit (confirm the adopted edition with the AHJ).
```

---
### H3. references/REV-I-CHANGES.md, row 3 entry (row 3 Edit 4)

**Path correction:** the file is `references/REV-I-CHANGES.md` (Drive `references` folder). It already exists in rev I, so append to it; do not create it. The row 2 file names `Claude outputs/REV-I-CHANGES.md`, a different and newer copy of the log (2026-10-16) in a Drive folder, which is not a path in the standard. Add the item below to the same list as rows 1 and 2 (their Edit 4 and Edit 6 entries). Do not add a second file.

Add this numbered item:

> N. Perspective (library build): script library `efc.ui` described in the Perspective Design section (openDynamic, closeDynamic, setDefaultDock, dblCmd, cmd, bypass/unbypass, ackAll, trend, level). Perspective Screen Design: template text and styling use EFC_Styles classes, generated classes for static inline styles, Util/Gap spacing classes; dockId and dwTagPath overrides described under the dynamic-window table. No change to type definitions.

---

---

## Open items (all rows)

From row 1 (heaters):
- kW threshold for current monitoring (`\tbd`).
- NFPA 86 clause references to confirm against the adopted edition (`\note`).

From row 2 (HMI rules):
- Ack, setpoint and latch-reset roles (Operator / Maintenance / Supervisor) to confirm.
- Admin-only actions to list (none named yet).
- Edit D (07-software.tex) anchor checked verbatim against rev I on 2026-10-21 (resolved).

From row 3 (library build):
- Whether template and class names (`Templates/Rotating/VFD`, `Templates/AnalogIndicator`, `EFC_Styles`, `Util/Gap`) belong in a generic standard.
- (Resolved 2026-10-21: all style-class references use EFC_Styles; G2a-c.)
- LoopConfig retirement (decision 15) and the VFD and AnalogIndicator template changes are library-only; no standard text proposed.

Batch-level:
- Anchors checked against rev I on 2026-10-21: 13 found verbatim, none moved, 2 new files absent as expected (Decision 1).
- Reconcile the two REV-I-CHANGES.md copies (references 2026-10-14 vs Claude outputs 2026-10-16) before H1-H3 are applied; then use the next free number (11 if items 9-10 are merged).
- Confirm label `sec:pclib-modes` is defined in rev I (a full-text hit exists in `sections/10-plc-standards.tex`; the definition itself was not confirmed).

## Checks before reporting back

1. Labels referenced exist in rev I (grep `sections/` and `appendices/`): `app:screen-design`, `sec:pclib-t-intlk`, `sec:pclib-modes`, `sec:online-changes`, `sec:review-release`, `sec:pclib-t-vfd`, `sec:pclib-t-pid`, `sec:sccr`, `sec:heat`, `app:data-types-future`. New labels (from rows 1 and 2): `sec:heaters`, `tab:heater-methods`, `sec:hmi-dynamic-windows`, `tab:hmi-dw-ids`, `sec:hmi-dw-open`, `sec:hmi-dw-layout`, `sec:hmi-touch`, `sec:hmi-bypass`, `sec:hmi-trends`, `sec:ignition-roles`, `tab:hmi-roles`. Confirm none is already defined.
2. `ch:scada` is optional (row 3 Edit 1); if absent, use the fallback sentence given in that edit.
3. Macros: `\newmark`, `\tbd`, `\note`, `\future`, `\paragraph`, `\texttt`, column type `P{}`, colour `tblhead`, `enumitem` options. All are defined in `preamble.tex`.
4. Braces and environments balance in every inserted block.
5. Report the files touched with a one-line summary each (expected: `sections/heaters.tex`, `sections/hmi-dynamic-windows.tex` (new), `sections/06-hardware.tex`, `sections/07-software.tex`, `sections/11-scada-standards.tex`, `appendices/data-types-future.tex`, `appendices/perspective-screen-design.tex`, `references/REV-I-CHANGES.md`). Do not echo whole sections.

## Background (for the reviewer; not pasted into the standard)

Row 1 covers electric heaters (decision 17). Row 2 covers roles, dynamic windows, touch, bypass and trends (decisions 1-16, 19, 23-26). Row 3 covers the efc.ui script library, the style rule and the VFD and analog-indicator template names (decisions 15, 24, 26; `generator/docks/efc_ui.py`). Edits from rows 1 and 2 are copied from their files unchanged except for the dropped and merged items above.
