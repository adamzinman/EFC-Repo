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
