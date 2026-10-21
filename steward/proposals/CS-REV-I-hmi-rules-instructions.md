# Controls Standard rev I: add HMI role, dynamic window, bypass and trend rules

Instructions for an agent working on the EFC Controls Standard (LaTeX, Google Drive folder `Claude/Controls Standard`, **revision I**). Apply exactly these seven edits, then stop and report. Do not change anything else, do not bump the revision letter, and do not regenerate whole files.

**Why:** the EFCLib design review (steward/DECISIONS.md rows 1-16) fixed how users, dynamic windows (docks), touch commands, bypasses and dock trends work on Perspective screens. The standard needs (1) the role hierarchy and a table of minimum roles in Chapter 11 Security and Audit, (2) a new Chapter 11 section on dynamic windows, (3) a pointer from Alarms to the role table and (4) a cross-reference from the Perspective Screen Design appendix.

**Source of the content:** EFC-Repo branch `steward/finish-library` (`steward/DECISIONS.md` rows 1-6, 8, 10, 12-16, 19; row 7 only where it affects the HMI). Electric heater text (row 17) is in `CS-REV-I-heaters-instructions.md` and is not repeated here. Anchors below were taken from the rev I files in Drive (`sections/11-scada-standards.tex`, `appendices/perspective-screen-design.tex`, `appendices/data-types-future.tex`).

---

## Edit 1: new file `sections/hmi-dynamic-windows.tex`

Create it with exactly this content:

```latex
\section[Dynamic Windows]{Dynamic Windows \newmark}\label{sec:hmi-dynamic-windows}
Every equipment template opens a dynamic window: a panel on the right of the screen that shows the device's state, mode, commands, permissives, interlocks, alarms and history. Equipment of the same kind shares one dynamic window (Table~\ref{tab:hmi-docks}), so a valve, motor or loop looks and works the same on every screen.

\begin{small}
\begin{longtable}{@{}P{3.6cm}P{12.6cm}@{}}
\caption{Dynamic Windows}\label{tab:hmi-docks} \\
\toprule
\rowcolor{tblhead}\textbf{Dock id} & \textbf{Used by} \\
\midrule
\endfirsthead
\multicolumn{2}{@{}l}{\small\textit{Table \thetable{} continued}} \\
\toprule
\rowcolor{tblhead}\textbf{Dock id} & \textbf{Used by} \\
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

\subsection[Size, Opening and Closing]{Size, Opening and Closing \newmark}\label{sec:hmi-dw-open}
\begin{itemize}[itemsep=1pt]
  \item \textbf{Size and position.} The dynamic window fills the right-hand slot of the shell: 400 design px wide (37.04\,vh), which is 400\,px at 1920 $\times$ 1080 and 800\,px at 3840 $\times$ 2160, and the full height between the header and the alarm bar (Appendix~\ref{app:screen-design}).
  \item \textbf{Opening.} A single click or tap on the template symbol opens its dynamic window. The click target is the whole symbol bounding box, at least 44 design px in each direction.
  \item \textbf{Closing.} The close button returns the right-hand slot to the screen's default content. Each screen view has a \texttt{defaultDock} parameter that names it (normally the screen's trends).
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
  \item \textbf{Rule.} A bypass made this way from the HMI is the rule, and it is exempt from the second-person and approved MOC requirement for a force or bypass in Section~\ref{sec:online-changes}. PLC forces and logic changes are not exempt.
\end{itemize}
\future{Named permissive and interlock groups are to be embedded in the device types: \texttt{Perm : T\_Intlk} and \texttt{Intlk : T\_Intlk} in \texttt{T\_DValve}, \texttt{T\_Motor} and \texttt{T\_VFD}, \texttt{Intlk : T\_Intlk} in \texttt{T\_CValve} and \texttt{T\_PID}, and \texttt{Prot : T\_Intlk} in equipment modules. The existing \texttt{Inp\_IntlkOK} and \texttt{Inp\_PermOK} are kept and ANDed with the group. \texttt{T\_Intlk} gains \texttt{Sts\_BypLeft : ARRAY[0..15] OF TIME} so the time left can be shown per condition; until then only the time left on the oldest bypass (\texttt{Sts\_BypassLeft}) is available.}

\subsection[Trends]{Trends \newmark}\label{sec:hmi-trends}
Trends in a dynamic window show the last 30~minutes by default. Every graph has an expand button that opens it at about half the screen (960 $\times$ 540 design px, \texttt{Docks/Parts/TrendExpanded}) with range buttons 5~m, 30~m, 1~h, 8~h and 24~h, and pause /\allowbreak{} live.
```

## Edit 2: `sections/11-scada-standards.tex`, include the new section

Insert one line, followed by a blank line, immediately **before** this existing line (after the Perspective Design section):

```latex
\section{Alarms}
```

Line to insert:

```latex
\input{sections/hmi-dynamic-windows}
```

## Edit 3: `sections/11-scada-standards.tex`, Alarms

In the first paragraph under `\section{Alarms}`, immediately after the sentence

```latex
Acknowledging an alarm does not clear the process condition that caused it.
```

insert (same paragraph, one space before it):

```latex
Alarm shelving needs the Supervisor role and alarm-limit changes the Engineer role, and both are audit-logged (Table~\ref{tab:hmi-roles}). \newmark
```

## Edit 4: `sections/11-scada-standards.tex`, Roles and audit

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

## Edit 5: `appendices/perspective-screen-design.tex` (Appendix: Perspective Screen Design Standard)

Under `\section{Navigation and Dynamic Content}`, at the end of the paragraph that starts `\textbf{Trends / dynamic window.}` (it ends `is an acceptable alternative.`), append (same paragraph, one space before it):

```latex
What the dynamic window shows and how it opens and closes is set in Section~\ref{sec:hmi-dynamic-windows}. \newmark
```

Then insert this line on its own, immediately after that paragraph and before the blank line that precedes `\textbf{Menu.}`:

```latex
\note{Open: EFCLib opens dynamic windows as a Perspective right dock with its width in vh (37.04\,vh), closed with \texttt{efc.ui.closeDynamic}, while Section ``Approach'' says docks are not used for the shell regions and this paragraph describes an Embedded View bound to session properties. Which one is the standard is \tbd; the losing text is to be amended.}
```

## Edit 6: `Claude outputs/REV-I-CHANGES.md`

Append this item to the numbered list of applied changes (use the next free number in place of N):

```
N. Ch11 SCADA: Roles and audit rewritten (label sec:ignition-roles): role hierarchy Guest < Operator < Maintenance < Supervisor < Engineer < Admin, one session level at login, controls hidden below the required level, Table tab:hmi-roles (MAINT/OOS, JOG, simulation, maintenance resets = Maintenance; bypass and shelving = Supervisor; alarm limits, configuration and tuning = Engineer), audit-log content. New section Dynamic Windows (sections/hmi-dynamic-windows.tex, \input before Alarms): dock ids (Table tab:hmi-docks), size, open/close and defaultDock, section order, button tiers, touch double-tap (dblCmd), named permissives/interlocks and bypass (BypassConfirm, presets 1/2/4/8 h up to Cfg_BypassMax, mandatory reason, time left and audit line per condition; T_Intlk embedding as \future), trends (30 min default, expand 960 x 540, ranges 5 m to 24 h). Alarms: shelving/limit roles sentence. Appendix Perspective Screen Design: cross-reference from Trends / dynamic window and open note on dock vs embedded view. Section Online Changes and Forces (sec:online-changes): HMI bypass by one Supervisor-or-higher user with a mandatory reason, up to the configured maximum, audit-logged, is exempt from the second-person and MOC requirement; PLC forces and logic changes keep it (Edit 7, cross-ref sec:hmi-bypass).
```

Add to its "Still open (need Adam)" list:

```
- Minimum role for alarm acknowledge, setpoint changes and reset of latched interlocks (tab:hmi-roles).
- Which actions are Admin-only, e.g. user and role administration (tab:hmi-roles).
- Dynamic window as a Perspective right dock (EFCLib) vs the appendix's embedded view and "docks are not used" (app:screen-design, Navigation and Dynamic Content).
```

## Edit 7: `sections/07-software.tex`, Online Changes and Forces

Anchor (quoted from the rev H copy of `sections/07-software.tex`, section at `\label{sec:online-changes}`; the bullet is the third item of the `itemize`). Re-check it verbatim against rev I before applying; see Background.

```latex
  \item A force or bypass on an interlock or safety-related signal needs a second person to check it and an approved MOC (Section~\ref{sec:review-release}).
```

Replace that line with exactly this:

```latex
  \item A force or bypass on an interlock or safety-related signal needs a second person to check it and an approved MOC (Section~\ref{sec:review-release}), except an HMI bypass of a permissive or interlock condition. An HMI bypass is the rule when one user with the Supervisor role or higher sets it from the dynamic window through the bypass confirmation, with a mandatory reason, a duration up to the configured maximum (\texttt{Cfg\_BypassMax}), and an entry in the audit log (Section~\ref{sec:hmi-bypass}). It needs no second person and no MOC. PLC forces and logic changes on an interlock or safety-related signal keep the second-person and MOC requirement.
```

Checks for this edit: `sec:online-changes` and `sec:review-release` exist in rev I (grep `sections/`); `sec:hmi-bypass` is created by Edit 1 of this file, so Edit 1 must be applied first. Leave the existing `\note` at the top of the section (it says the policy is not yet enforced) unchanged; that is a separate decision.

Background: the rev H copy is the only copy available to the documentation subagent (`revision.tex` = H, file dated 2026-10-08). The Google Drive rev I copy could not be read from this session, so the anchor and the line number are unverified against rev I. The section is in `07-software.tex`, not `10-plc-standards.tex`.

---

## Checks before reporting back

1. Labels referenced by the new text already exist in rev I: `app:screen-design`, `sec:pclib-t-intlk`, `sec:pclib-modes`. New labels: `sec:hmi-dynamic-windows`, `tab:hmi-docks`, `sec:hmi-dw-open`, `sec:hmi-dw-layout`, `sec:hmi-touch`, `sec:hmi-bypass`, `sec:hmi-trends`, `sec:ignition-roles`, `tab:hmi-roles`; confirm none is already defined (`grep -rn` over `sections/` and `appendices/`).
2. Macros used: `\newmark`, `\tbd`, `\note`, `\future`, column type `P{}`, colour `tblhead`, `enumitem` list options; all are defined in `preamble.tex`.
3. Build only if Adam asks (rev I convention: do not compile until told). If asked, run `pdflatex` on the main document three times and confirm there are no undefined references.
4. Report the four files touched (plus the new file) with a one-line summary each. Do not echo whole sections.

## Background (for the reviewer; do not paste into the standard)

- Rows used: 1 (click/double-tap, dblCmd, 44 px target), 2 (defaultDock, close), 3 (right dock 800 px at 4K, 37.04 vh), 4 (dw_Station), 5 (roles, MAINT/OOS, bypass), 6 (8 h history), 7 (Perm/Intlk embedding, Sts_BypLeft: \future only), 8 (dw_ValveDiscrete layout), 10 (BypassConfirm, Inp_BypassPerm, per-condition time left and audit line), 12 (presets, JOG Maintenance+), 13 (button tiers), 14 (limits, shelving, configuration roles and audit), 15 (LoopConfig retired: tuning in dw_Loop), 16 (trend expand and ranges), 19 (HMI bypass exemption from the Online Changes and Forces rule, Edit 7). Rows 9 and 11 are library-only; 17 is in the heaters file; 18 is process.
- Chapter 10 mode transitions (sec:pclib-modes) already name the Operator role for Auto/Manual and the Maintenance role for MAINT/OOS, so Table tab:hmi-roles is consistent with it; Chapter 10 is not edited.
- `T_Intlk` in rev I Appendix I has `Cfg_Bypassable`, `Cfg_BypassMax` (default T#8H), `Inp_BypassPerm` and `Sts_BypassLeft` (oldest bypass only); `Sts_BypLeft[n]` is planned, hence the \future.
- Sizes are in design px (1080p pixels), as in the Perspective Screen Design appendix: 400 dp = 37.04 vh = 800 px at 4K; the dock height between header (80 dp) and alarm bar (140 dp) is 860 dp.
```
