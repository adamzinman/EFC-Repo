# EFC Repo

## PCLib: ISA-88 phases and sequence bar
`PCLib/` holds the phase DFBs for Control Expert Classic V16.2 and their Ignition 8.1 sequence bar. See [`PCLib/README_FB_Phase.md`](PCLib/README_FB_Phase.md).
- `FB_PhaseCore`: the state machine.
- `FB_Phase`: the template.
- `FB_PhXeFill`: one xenon fill sequence for any number of stations (example).
- `T_SeqBar`: the sequence-bar DDT.

Design a new phase with [`PCLib/Sequence_Template.md`](PCLib/Sequence_Template.md).
