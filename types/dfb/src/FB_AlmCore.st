(* FB_AlmCore v1.00 - 2026-10-21 - EFC Controls *)
(* ISA-18.2 / IEC 62682 alarm state machine: on/off delays, latching, acknowledge, *)
(* time-limited shelving, suppression by design, out of service. *)
(* Shared by FB_Alarm and FB_AlmLim. Interface: FB_AlmCore.iface.yaml *)

(* ---- First scan after a cold start: alarm cleared ---- *)
IF NOT xInitDone THEN
	xOOS := FALSE;
	xShelved := FALSE;
	xLatch := FALSE;
	xUnack := FALSE;
	xActivePrev := FALSE;
	xInitDone := TRUE;
END_IF;

(* ---- Out of service (state H) ---- *)
IF RemoveSvc THEN
	xOOS := TRUE;
END_IF;
IF ReturnSvc THEN
	xOOS := FALSE;
END_IF;

(* ---- Shelving (state F), always time-limited ---- *)
IF Shelve AND Enabled AND NOT xOOS AND NOT OOSIn THEN
	xShelved := TRUE;
END_IF;
IF Unshelve OR xOOS OR OOSIn OR NOT Enabled THEN
	xShelved := FALSE;
END_IF;
tonShelf(IN := xShelved, PT := MaxShelf);
IF tonShelf.Q THEN
	xShelved := FALSE;
END_IF;
IF xShelved THEN
	ShelfLeft := MaxShelf - tonShelf.ET;
ELSE
	ShelfLeft := T#0S;
END_IF;

xInhibit := xOOS OR OOSIn OR xShelved OR Supp OR NOT Enabled;

(* ---- Chattering control: on-delay, off-delay ---- *)
tonOn(IN := Cond AND NOT xInhibit, PT := OnDly);
tofOff(IN := tonOn.Q, PT := OffDly);
xCond := tofOff.Q AND NOT xInhibit;

(* ---- Latching (state E): reset clears it only after return to normal ---- *)
IF xInhibit OR NOT LatchCfg THEN
	xLatch := FALSE;
ELSIF xCond THEN
	xLatch := TRUE;
ELSIF Rst THEN
	xLatch := FALSE;
END_IF;

xActive := xCond OR xLatch;

(* ---- Annunciation edges (stored previous state) and acknowledge ---- *)
EvtActive := xActive AND NOT xActivePrev;
EvtRTN := xActivePrev AND NOT xActive AND NOT xInhibit;
xActivePrev := xActive;

IF EvtActive AND NOT NoAck THEN
	xUnack := TRUE;
END_IF;
IF Ack OR xInhibit OR NoAck THEN
	xUnack := FALSE;
END_IF;

(* ---- State per the ISA-18.2 state model ---- *)
IF xOOS OR OOSIn OR NOT Enabled THEN
	State := 7;
ELSIF Supp THEN
	State := 6;
ELSIF xShelved THEN
	State := 5;
ELSIF xLatch AND NOT xCond THEN
	State := 4;
ELSIF xActive AND xUnack THEN
	State := 1;
ELSIF xActive THEN
	State := 2;
ELSIF xUnack THEN
	State := 3;
ELSE
	State := 0;
END_IF;

Active := xActive;
Unack := xUnack;
Shelved := xShelved;
Suppressed := Supp AND Enabled AND NOT xOOS AND NOT OOSIn;
OOS := xOOS OR OOSIn;
