# Rev I change log (draft, 2026-10-14)

Requested: sync Appendix I with PCLib, flesh out thin chapters, close open items.

1. Appendix I: added T_DiaComp (from PCLib gen_pclib.py output pclib-data-types.tex, 2026-10-14) after T_Conveyor; type index row (89 members); mapping row (PDC compressor package -> T_DiaComp, \tbd). Ch10 PDC Compressor gets \label{sec:pdc-compressor} + paragraph and \future note pointing to T_DiaComp.
2. Alarm priority: per Adam's decision, Ignition numbering (0 Diagnostic, 1 Low, 2 Medium, 3 High, 4 Critical). New Table tab:alarm-priority in Ch11. Appendix I text updated; orange note that member tables still show v1.00 numbering until gen_pclib.py is changed. PCLib TODO: change Cfg_Priority enum + default in gen_pclib.py.
3. Alarm ack: Ignition annunciates; ack in Ignition writes through to PLC Cmd_Ack (Ch11 Alarms).
4. Ch4: new sections Contractor Roles (table), Information EFC Provides, Submittal Review (+note: turnaround not defined), Packaged Equipment, PLC and SCADA Software by Contractors, Testing and Acceptance, Site Work, Contractor Cybersecurity (IEC 62443-2-4:2023 footnote), Turnover and Closeout (+note: warranty terms not set).
5. Ch11: Version and Upgrades (8.1; \future 8.3), PLC Connections section.
6. Ch12: EFC Internal References (+note: EFC Repo location undecided), Manufacturer Documentation, Further Reading (free ISA papers, ISA TRs), Training. Standards table: IEC 62443-2-4:2023, ISA-TR18.2.7-2017.
7. Added chapter labels ch:accounts, ch:software, ch:scada, ch:process-definition.
8. Frontmatter: H row date fixed to October 13, 2026; I row added. revision.tex -> I.

## Still open (need Adam)
- ICONICS version(s) in use.
- SMC air prep unit part number.
- IND780 vs IND700 (confirm with Mettler Toledo).
- DFB_Device inputs [check]; \tbd markers in Appendix H.
- Vendor phone numbers (Jeff DiTrolio/MDCI, Art McEvoy/ADI, MDCI main, Airline Hydraulics Bensalem) and "what we use them for" column.
- Review turnaround, warranty terms, EFC Repo location.
- T_UnitCtl not yet designed (state numbering must not collide).
- Minimum role for alarm acknowledge, setpoint changes and reset of latched interlocks (tab:hmi-roles).
- Which actions are Admin-only, e.g. user and role administration (tab:hmi-roles).
- Heater size (kW) above which current monitoring is required (sec:heaters).
- NFPA 86 clause references for the excess-temperature limit (confirm the adopted edition with the AHJ).

## Added 2026-10-15
9. Table 6.3 (Terminal Blocks): Analog Inputs primary -> WAGO 2202-3201 (triple-deck L/L/L, push-button, 2.5 mm2, grey, 22 A / 500 V, $6.71 Powermatic Oct 2026). 280-560 moved to Analog Inputs (Alternate); 2020-5311 stays as the second alternate.
10. Table 6.4 (Accessories): added 2002-1492 (0.8 mm orange end plate, 2002-14xx), 2002-2296 (2.0 mm orange, 2002-22xx), 2002-3292 (0.8 mm orange, 2002-32xx). "202-191" confirmed as 209-191, already in the table.

## Added 2026-10-21 (Ignition library build)

11. Ch11 SCADA: Roles and audit rewritten (label sec:ignition-roles): role hierarchy Guest < Operator < Maintenance < Supervisor < Engineer < Admin, one session level at login, controls hidden below the required level, Table tab:hmi-roles (MAINT/OOS, JOG, simulation, maintenance resets = Maintenance; bypass and shelving = Supervisor; alarm limits, configuration and tuning = Engineer), audit-log content. New section Dynamic Windows (sections/hmi-dynamic-windows.tex, \input before Alarms): window ids (Table tab:hmi-dw-ids), size, open/close and defaultDock, section order, button tiers, touch double-tap (dblCmd), named permissives/interlocks and bypass (BypassConfirm, presets 1/2/4/8 h up to Cfg_BypassMax, mandatory reason, time left and audit line per condition; T_Intlk embedding as \future), trends (30 min default; expand keeps the window at 400 x 860 and fills it below the header, about 400 x 760, with ranges 5 m to 24 h, pause/live and collapse; the region never changes width; decision 26). I/O card, rack and power-supply faceplates bind directly to the Modicon x80 device DDTs from Control Expert (no PCLib type; decision 23). Alarms: shelving/limit roles sentence. Appendix Perspective Screen Design: Trends / dynamic window paragraph and shell table rewritten as the embedded-view dynamic window (efc.ui session value, openDynamic/closeDynamic, defaultDock, sizes in vh; Edit 8), which settles the former dock-vs-embedded-view question. Section Online Changes and Forces (sec:online-changes): HMI bypass by one Supervisor-or-higher user with a mandatory reason, up to the configured maximum, audit-logged, is exempt from the second-person and MOC requirement; PLC forces and logic changes keep it (Edit 7, cross-ref sec:hmi-bypass).

12. Ch6 Other Hardware: new subsection Electric Heaters (sections/heaters.tex, \input before Standard Air Prep Unit): on/off contactor, time-proportioned SSR (duty cycle) and SCR power controller methods (Table tab:heater-methods); required independent excess-temperature limit, series isolating contactor, current monitoring, semiconductor fuses and SSR heat. Appendix I: added T_Heater (64 members) after T_VFD; index row and Control module list updated. Open: kW threshold for current monitoring (\tbd); NFPA 86 clause references to confirm against the adopted edition.

13. Perspective (library build): script library `efc.ui` described in the Perspective Design section (openDynamic, closeDynamic, setDefaultDock, dblCmd, cmd, bypass/unbypass, ackAll, trend, level). Perspective Screen Design: template text and styling use EFC_Styles classes, generated classes for static inline styles, Util/Gap spacing classes; dockId and dwTagPath overrides described under the dynamic-window table. No change to type definitions.

## Queued (confirmed with Adam 2026-10-16; DO NOT apply until told)
Q1. Ch6 Servers, Computers, and Operator Stations: add an "Alternate IPCs" table under Table tab:operator-workstation-hardware (CL260 stays primary). Requirements for any IPC: DIN-rail mountable, powered from panel 24 VDC, meets Ignition 8.3 / Edge Panel minimum (dual-core, 4 GB RAM, 10 GB free disk; Windows 10/11 or Linux). Proposed EFC baseline above IA minimum: 4 cores, 8 GB RAM, 128 GB SSD (ask Adam to confirm before adding as a rule).
  - Cincoze DA-1200-N97-R10: Intel N97 4C; 1x DDR5 SODIMM up to 16 GB (order 8 GB) + industrial SSD >=128 GB; DP 4K60; 2x 2.5GbE; 9-48 VDC terminal block; DIN mount; -40 to 70 C; Win10/11 (license extra); $999.95 barebone (MITXPC, Oct 2026), est. $1,150-1,300 configured. Install Ignition Edge on site. Closest match to CL260.
  - Beckhoff C6015-0040: Atom x7433RE 4C; 8-16 GB LPDDR5; 2x 2.5GbE; 1x DP; 24 VDC; DIN adapter C9900-M602; Win11 IoT Enterprise LTSC 2024. Price: quote. Install Ignition Edge on site.
  - Siemens SIMATIC IPC BX-21A 6AG4021-0BC00-1AB1: Atom x6413E 4C, 8 GB, 128 GB SSD; 3x GbE; DP up to 4096x2160; 24 VDC; DIN (bracket separate); Win10 IoT Enterprise LTSC 2021 (deviation from Win11 IoT LTSC 2024); $1,373.43 (WIAutomation, Oct 2026, backorder). Slower than N250 - bench-test Edge Panel.
  - Advantech IGNE-UNO2271GV2-1 (Ignition Edge pre-installed, trial; license from IA): only acceptable with Pentium N6415 4C / 8 GB / 64 GB option (+$640, ~$1,980); base N6210 2C/4 GB/32 GB eMMC is at IA minimum and too weak for Edge Panel. HDMI; 10-30 VDC; DIN kit $9. Advantech is an IA Alliance Partner.
  - Moxa DRP-C100-C1-T-Win10: Celeron 6305E 2C, 8 GB, 64 GB CFast; HDMI 2.0b + VGA; 2x GbE; 12/24 VDC; DIN; -30 to 60 C; Class I Div 2 / ATEX / IECEx certified; Win10 IoT LTSC 2021 (Win11 IoT LTSC 2024 option); $2,114.10 (RSP Supply, Oct 2026) - over budget; option for C1D2 locations. Moxa is an IA Alliance Partner but this model is not on its Ignition pre-load list.
  - Excluded (note in text if useful): Lenovo ThinkEdge SE10-I (discontinued); ThinkEdge SE30n Gen2 (12 V DC jack only - would need 24->12 V ~90 W converter; DIN kit 4XH1W58380); Uticor i-edge-boxxed / DIN-Railer (12 VDC); Advantech UNO-127 (EOL Aug 2026, 1080p), UNO-137 V2 ($2,045), IGNE-UNO137-1 ($2,270), IGNE-UNO410-1 ($1,910, C1D2, no video listed); ASRock iBOX-N97 (19 V adapter); Moxa MC-1220 ($3,700-5,800, 2017 CPU), MC-1122 (Atom E3845, VGA).
  - Add note: Ignition Edge Onboard program ended 2023-08-31; no IA hardware certification; Alliance Partners (Advantech, Moxa, OnLogic, Uticor) ship Ignition pre-installed, license bought separately.
Q2. Table tab:monitors-industrial (Industrial Monitors): add Hope Industrial HIS-UM23.8-BPVB as the HMI monitor of choice, $1,630 (Adam, Oct 2026). Hope 23.8" line: 1920x1080 16:9, resistive standard / PCAP optional, DP + DVI-I (VGA via adapter), AC + 10.8-26.4 VDC, NEMA 4/4X / IP65/66, Class I/II/III Div 2; "UM" appears to be universal mount (stainless or carbon steel; fits 23" yoke, pedestal, YW wall yoke). Confirm suffix (BPVB) meaning / touch type with Hope before publishing. Keep HIS-ML23.8-FPVB (panel mount, $1,420) as the panel-mount option.
Q3. Table tab:keyboards (Industrial Keyboards): add Hope Industrial KB-R3-EXT-BLK-4-USB, $920 (Adam, Oct 2026), as the keyboard to pair with the HIS-UM23.8. Confirm EXT vs WMT variant difference, touchpad, and HazLoc rating with Hope (spec page did not load).
