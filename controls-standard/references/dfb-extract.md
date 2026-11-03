# DFBs extracted from user screenshots, 2026-10-02

DFB_Analog_Input
- Inputs: Input (T_U_ANA... X80 analog channel device DDT, name truncated) #1: FCT_TYPE WORD "Function type"; CH_HEALTH BOOL "Channel health"; CH_WARNING BOOL "Channel warning"; ANA (T_U_ANA...): VALUE INT "Analog input value", FORCED_VALUE INT "Forced value", FORCE_CMD BOOL "Force command", FORCED_STATE BOOL "Forced state", TRUE_VALUE INT "Physical value"; MEASURE_STS INT "Measurement status"; CH_ALIGNED BOOL "Aligned channel"; LOWER_LIMIT BOOL "Measurement within lower..."; UPPER_LIMIT BOOL "Measurement within upper..."; INT_OFFSET_ERROR BOOL "Internal offset..."; INT_REF_ERROR BOOL "Internal reference..."; POWER_SUP_ERROR BOOL "Power supply..."; SPI_COM_ERROR BOOL "SPI communication..."
- Outputs: Raw_Value INT #1; Eng_Value REAL #2
- In/out: PV DDT_Process_Value #3
- Public: Overrange BOOL; Underrange BOOL
- Private: (cut off)

DFB_Device (confirmed by user; inputs cut off in screenshot)
- Inputs: not visible; Outputs: none shown
- In/out: DEV DDT_Device #1
- Public: HMI_CMD BOOL; Mode INT; Runtime REAL; Reset_Runtime BOOL; Motor_Stalled BOOL
- Private: Run_Hour, Run_Min, Run_Sec REAL; Stall_TMR TON; ModeEnum DDT_Mode (Off, Auto, Manual INT); TON_0 TON; TOF_0 TOF
- Sections: Runtime_Tracking (ST), Commands... (cut)

DFB_Process_Value (confirmed by user; analog alarm processing)
- Inputs: #1 cut off; Reset BOOL #2
- Outputs: none
- In/out: PV DDT_Process_Value #1
- Private: LL_TMR, L_TMR, H_TMR, HH_TMR (TON); LL/L/H/HH_TMR_IN BOOL; LL/L/H/HH_TMR_PT TIME

DFB_Station
- Inputs: Estop BOOL #8; Upstream_PT DDT_Process_Value #9
- Outputs: none
- In/out: Station DDT_Station #1; Scale DDT_Scale #2; Seq DDT_Seq #3; PT DDT_Process_Value #4; #5-#7 not visible

## Batch 2
DFB_Station (now complete): In/out #5 InletValve DDT_Valve; #6 SampleValve DDT_Valve; #7 VacuumValve DDT_Valve.
- Public: StatusEnum (DDT_StationEnum, truncated "DDT_Stati...") constants Disabled=0, ReadyToStart=10, ReadyToFill=20, Filling=30, Complete=40, Failed=50, Venting=60, Vacuuming=70; ONS_Auto BOOL; ONS_Manual BOOL
- Private: O_DLY TON (PT t#1s), C_DLY TON, TON_0, RS_0, AutoChangeTrig/ManChangeTrig/SeqOffTrig R_TRIG
- Sections: DataMapping (ST), Monitoring (ST)

DFB_Valve
- In/out: Valve DDT_Valve #1
- Outputs: Valve_Output BOOL #2
- Inputs: Interlock #3, Estop #4, Sys_Auto #5, Sys_Manual #6, Sys_Off #7 (BOOL)
- Public: none; Private: TOF_1, TON_1, TON_2, SR_0
- Sections: Commands (LD)

Pin numbering is global across inputs/outputs/in-outs -> unnamed DFB B (PV #1, Reset #2) is NOT missing an input.
Other DFBs seen collapsed (ignored): DeviceCtrl, DI_Ctrl, Unit_Mode_Ctrl, Valve_NoFB, DFB_TMR
