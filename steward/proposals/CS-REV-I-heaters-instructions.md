# Controls Standard rev I: add electric heater content

Instructions for an agent working on the EFC Controls Standard (LaTeX, Google Drive folder `Claude/Controls Standard`, **revision I**). Apply exactly these four edits, then stop and report. Do not change anything else, do not bump the revision letter, and do not regenerate whole files.

**Why:** EFCLib/PCLib gained a new data type, `T_Heater` (electric heater: on/off contactor, time-proportioned SSR, or SCR power controller). The standard needs (1) a hardware and control-methodology subsection in Chapter 6 and (2) the type in Appendix I (PLC Data Type Reference, Future).

**Source of the content:** EFC-Repo branch `steward/finish-library` (`types/gen_pclib.py` defines T_Heater). The Appendix I block below was produced with the standard's own `tools/gen_future_appendix.py` from the regenerated `types/README.md`.

---

## Edit 1: new file `sections/heaters.tex`

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

## Edit 2: `sections/06-hardware.tex`

Insert one line, followed by a blank line, immediately **before** this existing line (under `\section{Other Hardware}`, after the Solenoids subsection):

```latex
\subsection{Standard Air Prep Unit}\label{sec:air-prep}
```

Line to insert:

```latex
\input{sections/heaters}
```

## Edit 3: `appendices/data-types-future.tex` (Appendix I)

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

## Edit 4: `references/REV-I-CHANGES.md`

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

## Checks before reporting back

1. Labels referenced by the new text already exist: `app:data-types-future`, `sec:sccr`, `sec:heat`. New labels: `sec:heaters`, `tab:heater-methods`, `sec:pclib-t-heater`, `tab:pclib-t-heater`; confirm none is already defined.
2. Macros used: `\newmark`, `\tbd`, `\note`, column type `P{}`, colour `tblhead`, `enumitem` list options; all are defined in `preamble.tex`.
3. Build only if Adam asks (rev I convention: do not compile until told). If asked, run `pdflatex` on the main document three times and confirm there are no undefined references.
4. Report the four files touched with a one-line summary each. Do not echo whole sections.

## Background (for the reviewer; do not paste into the standard)

- Time proportioning: an SSR is on/off, so the PLC switches it on for the demanded fraction of a fixed cycle; 2-10 s cycles are typical for heaters.
- SCR controllers switch the load themselves from an analog reference: burst / zero-cross firing (low noise, the default) or phase-angle firing (needed for some loads, creates harmonics).
- SSRs usually fail shorted, hence the series contactor and the "current with output off" check.
- Excess-temperature limit: separate controller and sensor, hardwired, latching, manual reset (NFPA 86 practice where it applies).
- Primary standard texts (IEC 60947-4-3, NFPA 86) were not available while drafting, so clause numbers are deliberately not quoted.
