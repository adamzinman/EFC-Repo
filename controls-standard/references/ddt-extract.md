# DDTs extracted from user screenshots (Control Expert Data Editor), 2026-10-02

AI_Sensors (no DDT_ prefix): PV REAL; Raw REAL; Rate REAL; Fraction REAL; LL_Alarm BOOL; LL_Alarm_Acked BOOL; Lo_Alarm BOOL; Lo_Alarm_Acked BOOL; Hi_Alarm BOOL; Hi_Alarm_Acked BOOL; HH_Alarm BOOL; HH_Alarm_Acked BOOL

DDT_AI_Alarm: SP REAL; DB REAL; Enabled BOOL; Alarm BOOL; DLY REAL; Inhibit BOOL

DDT_Device: REQ, Auto_Perm, Man_Perm, HMI_Auto, HMI_Manual, HMI_Off, HMI_Lockout, CMD, YI, YIF, HMI_CMD, Interlock, FB_Enb, Alarm, Warning, Auto, Manual, Off, LockedOut BOOL; Run_Sec, Run_Min, Run_Hour, Runtime REAL; Reset_Runtime BOOL; Enable_Stalling BOOL; Comp_Ratio REAL; Curr_Comp_Ratio REAL; Stall_Time INT; Stalled BOOL

DDT_Discrete: Override_Enb BOOL; Override_Sig BOOL; Fault BOOL

DDT_Motor_VFD (comments truncated in screenshot): REQ BOOL "START REQU..."; INTERLOCK BOOL "RUN INTERL..."; AUTO_PERM BOOL (no comment); AUTO BOOL "MOTOR IN A..."; MANUAL BOOL "MOTOR IN M..."; OFF BOOL "MOTOR IN OFF"; LOCKOUT BOOL "MOTOR IN S..."; HMI_AUTO/HMI_MANUAL/HMI_OFF/HMI_LOCKOUT BOOL "HMI COMMAN..."; CMD BOOL "MOTOR COM..."; YI BOOL "MOTOR RUN..."; WARNING BOOL "MOTOR WAR..."; ALARM BOOL "MOTOR ALAR..."; SPD_AUTO REAL "SPEED COM..."; SPD_MANUAL REAL "SPEED COM..."; SPD_CMD REAL "OUTPUT SPE..."; RUNTIME REAL "RUNTIME OF ..."; HMI_RESET_RUNTIME BOOL "RESET RUNT..."

DDT_Scale: GrossWeight REAL; TareWeight REAL; NetWeight REAL; TareCmd BOOL; ZeroCmd BOOL; ResetScale BOOL; Stable BOOL; Warning BOOL; Alarm BOOL; Fault BOOL; Msg STRING

DDT_Seq (cut off): Disabled BOOL; Ready BOOL; ...

Collapsed / not shown: DDT_ColorEnum, DDT_CompControl, DDT_CompModes, DDT_CompOpMode, DDT_CompVars, DDT_Minebea, DDT_MinebeaReadCmd, DDT_MinebeaWriteCmd, DDT_Mode, DDT_OpModeEnum, DDT_Process_Value, DDT_SCT2200, DDT_SCT2200_CMDs

## Batch 2

DDT_Seq (complete): Disabled BOOL; Ready BOOL; Running BOOL; Msg string[255]; Start BOOL; Abort BOOL; ShowCont BOOL; Pop_Msg string[255]; State DINT; Continue BOOL; Alarm DINT; Complete BOOL; Percent_Complete REAL; HMI_Auto BOOL; HMI_Manual BOOL; HMI_Off BOOL; Auto BOOL; Manual BOOL; Off BOOL; Ack BOOL; HMI_Pause BOOL; Paused BOOL; HMI_Topfill BOOL

DDT_Setpoint: SP REAL; Default REAL

DDT_Station (comments partly visible): TargetWeight REAL "Target Fill Wei..."; ReadyToStart BOOL "Station is Rea..."; ReadyToFill BOOL "Station is Rea..."; Active BOOL "Station is Filling"; Complete BOOL "Station has Su..."; Deadband REAL; HMI_Select BOOL; HMI_Reset BOOL; Selected BOOL; Venting BOOL; Vacuuming BOOL; Recovering BOOL; Vacuumed BOOL; Press_Balanced BOOL; Disabled BOOL; Failed BOOL; PT_Valid BOOL; PT_Diff REAL; InletREQ BOOL; InletCMD BOOL; SampleREQ BOOL; SampleCMD BOOL; VacuumREQ BOOL; VacuumCMD BOOL; PT REAL; Press_Max REAL; TareCMD BOOL; ZeroCMD BOOL; GrossWeight REAL; TareWeight REAL; NetWeight REAL; StatusEnum INT; Msg string[255]; ScaleLoaded BOOL; ScaleTared BOOL; Fill_Rate REAL; HMI_SP_Max_Vac_Press REAL; TotalWeight REAL; SampleWeight REAL; SamplePress REAL; Pressurizing BOOL "Station is buildi..."; Sampling BOOL; HighPressWarningReq BOOL "Station Max pr..."; PressurizeReqd BOOL; SampleReqd BOOL; Filling BOOL; Disconnecting BOOL; HMI_Disc BOOL; Purged BOOL; Light BOOL

DDT_Valve: REQ, Auto_Perm, Man_Perm, HMI_Auto, HMI_Manual, HMI_Off, HMI_Lockout, CMD, ZSO, ZSC, HMI_CMD, Interlock BOOL; Cycle_Count DINT; Reset_Count BOOL; Feedback_Enabled BOOL; Auto, Manual, Off, LockedOut BOOL

Still collapsed: DDT_Station_Data, DDT_StationEnum; non-prefixed: DevCtrl, DI_Sensors, HS, ModeBools, ReadVar, Seq, Sub..., plus earlier collapsed list (ColorEnum, Comp*, Minebea*, Mode, OpModeEnum, Process_Value, SCT2200*)
