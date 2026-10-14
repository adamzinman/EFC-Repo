/* Scan-by-scan simulation of FB_PhFill (one station) and FB_PhFeed on the C code MatIEC generates
   from the phase DFBs (built and run by run_tests.sh). 100 ms scans; simple process model:
   cylinder pressure from xenon mass, heel recovery, vacuum and leak, scale with tare and valve
   in-flight, compressor and fill header. Each CHECK is one ISA-88 behaviour. */
#include <stdio.h>
#include <math.h>
#include <string.h>
#include "iec_std_lib.h"
#include "accessor.h"
TIME __CURRENT_TIME;
double iec_lib_fmod(double a, double b) { return fmod(a, b); }
BOOL __DEBUG;
#include "POUS.h"
#define _____time_add(a, b) __time_add(a, b)
#define _____time_sub(a, b) __time_sub(a, b)
#include "POUS.c"

#define P(fb,X) ((fb).PH.value.X.value)
#define B(fb,X) ((fb).BAR.value.X.value)
static const double DTS = 0.1;
static double now_s = 0;
static int fails = 0;
#define CHECK(c, msg) do { if (c) printf("   PASS  %s\n", msg); else { printf("   FAIL  %s\n", msg); fails++; } } while (0)

typedef struct { double m, cyl, tare, leak, offt, lastflow; BOOL inlet_act; } Stn;
typedef struct { double hdr, suct, src, runT; BOOL run; } Feed;

static FB_PHFILL_data__ st;
static FB_PHFEED_data__ fd;
static FB_PHASE_data__ tp;
static Stn s; static Feed f;
static BOOL unit_auto = 1;
static const char *SN[] = {"Idle","Running","Complete","Pausing","Paused","Holding","Held","Restarting","Stopping","Stopped","Aborting","Aborted"};

static void str(char *o, IEC_STRING *x) { int n = x->len; memcpy(o, x->body, n); o[n] = 0; }

static void setup(void) {
  memset(&st, 0, sizeof st); memset(&fd, 0, sizeof fd);
  FB_PHFILL_init__(&st, 0); FB_PHFEED_init__(&fd, 0);
  s.m = 5.0; s.cyl = 50.0; s.tare = 50.0; s.leak = 0.001; s.offt = 99; s.lastflow = -99; s.inlet_act = 0;
  f.hdr = 0; f.suct = 0; f.src = 800; f.runT = 0; f.run = 0;
  double pr[16] = {20.0, 0.2, 0.1, 1.0, 0.12, 0.2, 1.0, 0.5, 60.0};
  long long pd[8] = {0, 3, 10, 2, 200, 800, 5};
  for (int i = 0; i < 16; i++) st.PH.value.PRM_REAL.table[i].value = pr[i];
  for (int i = 0; i < 8; i++) st.PH.value.PRM_DINT.table[i].value = pd[i];
  double fr[16] = {30.0, 3.0, 40.0, 2.0, 5.0};
  long long fdi[8] = {20, 5};
  for (int i = 0; i < 16; i++) fd.PH.value.PRM_REAL.table[i].value = fr[i];
  for (int i = 0; i < 8; i++) fd.PH.value.PRM_DINT.table[i].value = fdi[i];
  P(st, CFG_STEPTIMEOUT).tv_sec = 600; P(fd, CFG_STEPTIMEOUT).tv_sec = 600;
  st.PERMOK.value = 1; st.INTLKOK.value = 1; fd.PERMOK.value = 1; fd.INTLKOK.value = 1;
  now_s = 0;
}

static int pst = -1, pstep = -1, fpst = -1, fpstep = -1, verbose = 1;
static void scan(void) {
  /* ---- process model, using last scan's outputs ---- */
  if (st.OUT_INLET.value) s.offt = 0; else s.offt += DTS;
  s.inlet_act = s.offt < 0.1;                               /* 0.1 s valve closing delay */
  double pabs = s.m * 1000.0, pt = pabs / 1000.0 - 1.013;
  double flow = 0;
  if (st.OUT_RECOVER.value && pabs > 1100) s.m -= 0.5 * DTS;
  if (st.OUT_VAC.value) { s.m *= exp(-DTS / 3.0); if (s.m < 0.0003) s.m = 0.0003; }
  if (pabs < 1013) s.m += s.leak / 1000.0 * DTS;
  if (s.inlet_act && f.hdr > pt + 1.0) { flow = 0.5; s.m += flow * DTS; s.lastflow = now_s; }
  double gross = s.cyl + s.m;
  if (st.OUT_TARE.value) s.tare = gross;
  /* feed */
  if (fd.OUT_COMPRUN.value) f.runT += DTS; else f.runT = 0;
  f.run = fd.OUT_COMPRUN.value && f.runT >= 1.0;
  f.suct = fd.OUT_SRCVLV.value ? 10.0 : 0.0;
  if (f.run && fd.OUT_COMPLOAD.value && f.suct > 1) f.hdr += 2.0 * DTS;
  f.hdr -= flow * 1.2 * DTS; if (f.hdr < 0) f.hdr = 0;
  f.src -= flow * DTS;
  /* ---- inputs ---- */
  pabs = s.m * 1000.0; pt = pabs / 1000.0 - 1.013;
  st.VESSELOK.value = 1; st.NETWT.value = (gross - s.tare); st.WTSTABLE.value = (now_s - s.lastflow) > 1.0;
  st.PT.value = pt; st.VACPT.value = pabs; st.FEEDREADY.value = fd.FEEDREADY.value;
  fd.SRCWT.value = f.src; fd.SUCTPT.value = f.suct; fd.HDRPT.value = f.hdr; fd.COMPRDY.value = 1; fd.COMPRUN.value = f.run;
  fd.FEEDREQS.value = st.FEEDREQ.value ? 1 : 0;
  /* ---- unit logic: feed is owned by the unit and started on demand ---- */
  if (unit_auto && P(fd, STS_OWNER) == 0) P(fd, PROG_ACQUIRE) = 1;
  if (P(fd, STS_OWNER) == 1) {
    if (P(fd, STS_STATE) == 0 && fd.FEEDREQS.value > 0) P(fd, PROG_CMD) = 1;
    else if (P(fd, STS_STATE) == 2) P(fd, PROG_CMD) = 6;
  }
  /* ---- PLC scan ---- */
  __CURRENT_TIME.tv_nsec += 100000000; if (__CURRENT_TIME.tv_nsec >= 1000000000) { __CURRENT_TIME.tv_sec++; __CURRENT_TIME.tv_nsec -= 1000000000; }
  FB_PHFEED_body__(&fd);
  FB_PHFILL_body__(&st);
  now_s += DTS;
  char m[64];
  if (verbose && (P(st, STS_STATE) != pst || P(st, STS_STEP) != pstep)) {
    str(m, &B(st, VAL_MSG));
    printf("  %7.1fs STN  %-10s step %3d  seg %d  net %7.3f kg  PT %6.2f barg  vac %9.3f mbar  | %s\n", now_s, SN[P(st, STS_STATE)],
           P(st, STS_STEP), B(st, STS_ACTSEG), st.NETWT.value, st.PT.value, st.VACPT.value, m);
    pst = P(st, STS_STATE); pstep = P(st, STS_STEP);
  }
  if (verbose && (P(fd, STS_STATE) != fpst || P(fd, STS_STEP) != fpstep)) {
    str(m, &B(fd, VAL_MSG));
    printf("  %7.1fs FEED %-10s step %3d  seg %d  hdr %6.2f barg  run %d          | %s\n", now_s, SN[P(fd, STS_STATE)], P(fd, STS_STEP),
           B(fd, STS_ACTSEG), f.hdr, f.run, m);
    fpst = P(fd, STS_STATE); fpstep = P(fd, STS_STEP);
  }
}
static int run_until(int (*cond)(void), double maxs) { double t0 = now_s; while (now_s - t0 < maxs) { scan(); if (cond()) return 1; } return 0; }
static void run_for(double secs) { double t0 = now_s; while (now_s - t0 < secs) scan(); }
static int c_stn_done(void) { return P(st, STS_STATE) == 2; }
static int c_stn_held(void) { return P(st, STS_STATE) == 6; }
static int c_stn_s70(void) { return P(st, STS_STATE) == 1 && P(st, STS_STEP) == 70; }
static int c_stn_s80(void) { return P(st, STS_STEP) == 80; }
static int c_stn_paused(void) { return P(st, STS_STATE) == 4; }
static int c_stn_wait(void) { return P(st, STS_WAITADVANCE); }
static int c_stn_aborted(void) { return P(st, STS_STATE) == 11; }
static int c_feed_supply(void) { return P(fd, STS_STATE) == 1 && P(fd, STS_STEP) == 50; }
static int c_feed_paused(void) { return P(fd, STS_STATE) == 4; }
static int c_feed_s40(void) { return P(fd, STS_STATE) == 1 && P(fd, STS_STEP) == 40; }
static int c_feed_held(void) { return P(fd, STS_STATE) == 6; }
static int c_feed_idle(void) { return P(fd, STS_STATE) == 0 && P(fd, STS_PREVSTATE) == 2; }
static void segs(const char *who, FB_PHFILL_data__ *x) { printf("   bar %s:", who); for (int i = 0; i < 6; i++) printf(" %d", x->BAR.value.STS_SEG.table[i].value); printf("\n"); }
static int seg_is(int a0,int a1,int a2,int a3,int a4,int a5){int e[6]={a0,a1,a2,a3,a4,a5};for(int i=0;i<6;i++)if(st.BAR.value.STS_SEG.table[i].value!=e[i])return 0;return 1;}

int main(void) {
  printf("== 1. Normal fill, Automatic: feed started on demand by the unit ==\n");
  setup(); scan();
  CHECK(P(st, STS_MODE) == 3 && P(st, STS_STATE) == 0, "first scan: Idle, Automatic");
  CHECK(((int)(P(st, STS_CMDMASK))) == 2, "Idle command mask = Start only");
  CHECK(B(st, CFG_NUMSEG) == 6, "sequence-bar labels loaded (6 segments)");
  P(st, CMD_START) = 1;
  CHECK(run_until(c_stn_done, 2000), "station reaches Complete");
  double net = st.PH.value.RPT_REAL.table[0].value;
  printf("   report: net %.3f kg, P %.2f barg, run %.0f s, leak rise %.3f mbar, top-ups %lld\n", net,
         st.PH.value.RPT_REAL.table[1].value, st.PH.value.RPT_REAL.table[2].value, st.PH.value.RPT_REAL.table[3].value,
         (long long)st.PH.value.RPT_DINT.table[0].value);
  CHECK(net >= 19.9 && net <= 20.2, "final net weight inside 20.0 +0.2/-0.1 kg");
  segs("stn", &st); CHECK(seg_is(2,2,2,2,5,2), "bar at Complete: Done x4, Sample skipped, Done");
  CHECK(!st.OUT_INLET.value && !st.FEEDREQ.value, "outputs off at Complete");
  CHECK(run_until(c_feed_idle, 200), "feed idles, cools down, completes and is reset by the unit");
  printf("   feed report: start %.1f kg, end %.1f kg, delivered %.2f kg\n", fd.PH.value.RPT_REAL.table[0].value,
         fd.PH.value.RPT_REAL.table[1].value, fd.PH.value.RPT_REAL.table[2].value);
  P(st, CMD_RESET) = 1; scan(); CHECK(P(st, STS_STATE) == 0 && seg_is(0,0,0,0,0,0), "Reset -> Idle, bar cleared");

  printf("\n== 2. Leak check failure -> Held with fault segment; Restart after repair ==\n");
  setup(); s.leak = 0.2; scan(); P(st, CMD_START) = 1;
  CHECK(run_until(c_stn_held, 600), "station Held");
  char m[64]; str(m, &B(st, VAL_MSG)); printf("   fail %d: %s\n", P(st, STS_FAILCODE), m);
  CHECK(P(st, STS_FAILCODE) == 101, "fail code 101 leak check");
  segs("stn", &st); CHECK(seg_is(2,3,0,0,0,0), "bar: Vessel done, Vac = fault");
  CHECK(st.PH.value.ALM_FAIL.INP_COND.value, "Alm_Fail condition set");
  CHECK(!st.OUT_VAC.value && !st.OUT_RECOVER.value, "valves closed while held");
  s.leak = 0.001; P(st, CMD_RESTART) = 1;
  scan(); scan(); CHECK(P(st, STS_STATE) == 1 && P(st, STS_STEP) == 40 && P(st, STS_FAILCODE) == 0, "Restart resumes at step 40, failure cleared");
  CHECK(run_until(c_stn_done, 2000), "station completes after repair");

  printf("\n== 3. Semi-automatic: each step waits for Advance with outputs off ==\n");
  setup(); scan(); P(st, CMD_SEMIAUTO) = 1; scan(); CHECK(P(st, STS_MODE) == 2, "mode Semi-automatic");
  P(st, CMD_START) = 1; verbose = 0;
  int adv = 0, outs_off = 1;
  while (now_s < 3000 && P(st, STS_STATE) != 2) {
    scan();
    if (P(st, STS_WAITADVANCE)) {
      int o1 = st.OUT_INLET.value || st.OUT_VAC.value || st.OUT_RECOVER.value || st.FEEDREQ.value;
      scan();
      int o2 = st.OUT_INLET.value || st.OUT_VAC.value || st.OUT_RECOVER.value || st.FEEDREQ.value;
      int sg = st.BAR.value.STS_SEG.table[B(st, STS_ACTSEG) - 1].value;
      if (o2 || sg != 4) { outs_off = 0; printf("   step %d: outputs first scan %d, next scan %d, seg %d\n", P(st, STS_STEP), o1, o2, sg); }
      run_for(2); P(st, CMD_ADVANCE) = 1; adv++;
    }
  }
  verbose = 1;
  printf("   advances given: %d\n", adv);
  CHECK(P(st, STS_STATE) == 2 && adv >= 8, "completes in Semi-automatic after an Advance per transition");
  CHECK(outs_off, "while waiting: no station outputs, active segment shown as waiting (4)");

  printf("\n== 4. Pause in fast fill: pauses at the next transition with the inlet closed ==\n");
  setup(); scan(); P(st, CMD_START) = 1;
  CHECK(run_until(c_stn_s70, 600), "reached fast fill (step 70)");
  run_for(3); P(st, CMD_PAUSE) = 1; scan();
  CHECK(P(st, STS_STATE) == 3 && st.OUT_INLET.value, "Pausing: fast fill continues");
  CHECK(run_until(c_stn_paused, 300), "Paused at the transition");
  run_for(1);
  CHECK(P(st, STS_STEP) == 80 && !st.OUT_INLET.value, "paused before step 80, inlet closed");
  double w0 = st.NETWT.value; run_for(10); CHECK(fabs(st.NETWT.value - w0) < 0.01, "no weight change while paused");
  P(st, CMD_RESUME) = 1; scan(); scan(); CHECK(P(st, STS_STATE) == 1 && P(st, STS_STEP) == 80, "Resume runs step 80");
  CHECK(run_until(c_stn_done, 2000), "completes after Resume");

  printf("\n== 5. Interlock trip in fill -> Holding/Held; Restart re-requests feed first ==\n");
  setup(); scan(); P(st, CMD_START) = 1;
  CHECK(run_until(c_stn_s70, 600), "reached fast fill");
  run_for(5); st.INTLKOK.value = 0;
  CHECK(run_until(c_stn_held, 50), "interlock -> Held");
  CHECK(!st.OUT_INLET.value && !st.FEEDREQ.value, "inlet closed and feed released");
  CHECK(((int)(P(st, STS_CMDMASK))) == (4 | 32), "Held, interlock active: Stop and Abort only (Restart masked)");
  st.INTLKOK.value = 1; run_for(1);
  CHECK(((int)(P(st, STS_CMDMASK))) == (4 | 16 | 32), "interlock healthy: Restart allowed");
  P(st, CMD_RESTART) = 1; scan(); scan();
  CHECK((P(st, STS_STATE) == 7 && st.FEEDREQ.value) || (P(st, STS_STATE) == 1 && P(st, STS_STEP) == 70), "Restarting waits for feed (here already ready) and resumes at step 70");
  CHECK(run_until(c_stn_done, 2000), "completes after Restart");

  printf("\n== 6. Ownership: recipe owns the phase ==\n");
  setup(); scan(); P(st, PROG_ACQUIRE) = 1; scan();
  CHECK(P(st, STS_OWNER) == 1, "Prog_Acquire -> owner Recipe");
  P(st, CMD_START) = 1; scan();
  CHECK(P(st, STS_STATE) == 0 && P(st, STS_CMDREJECTED), "operator Start rejected while recipe owns");
  P(st, PROG_CMD) = 1; scan(); scan();
  CHECK(P(st, STS_STATE) == 1 && !P(st, STS_CMDREJECTED) && P(st, PROG_CMD) == 0, "Prog_Cmd 1 starts, Prog_Cmd cleared");
  P(st, CMD_HOLD) = 1; run_for(1);
  CHECK(P(st, STS_STATE) == 6, "operator Hold always accepted");
  P(st, CMD_TAKEOWN) = 1; scan(); P(st, CMD_RESTART) = 1; scan(); scan();
  CHECK(P(st, STS_OWNER) == 0 && P(st, STS_STATE) >= 1, "TakeOwn then operator Restart accepted");

  printf("\n== 7. E-stop -> Aborting -> Aborted; Reset -> Idle ==\n");
  setup(); scan(); P(st, CMD_START) = 1; run_for(30); st.ESTOP.value = 1;
  CHECK(run_until(c_stn_aborted, 10), "E-stop -> Aborted");
  segs("stn", &st);
  P(st, CMD_RESET) = 1; scan(); CHECK(P(st, STS_STATE) == 0, "Reset -> Idle");
  P(st, CMD_START) = 1; scan(); CHECK(P(st, STS_STATE) == 0 && P(st, STS_CMDREJECTED), "Start rejected while E-stop active");

  printf("\n== 8. Manual mode, permissives, recipe validation, step watchdog ==\n");
  setup(); scan(); P(st, CMD_MAN) = 1; scan(); P(st, CMD_START) = 1; scan();
  CHECK(P(st, STS_STATE) == 0 && P(st, STS_CMDREJECTED), "Start rejected in Manual");
  P(st, CMD_AUTO) = 1; scan(); st.PERMOK.value = 0; scan(); P(st, CMD_START) = 1; scan();
  CHECK(P(st, STS_STATE) == 0 && ((int)(P(st, STS_CMDMASK))) == 0, "no permissive: Start masked and rejected");
  st.PERMOK.value = 1; st.PH.value.PRM_REAL.table[0].value = 0; P(st, CMD_START) = 1;
  CHECK(run_until(c_stn_held, 10) && P(st, STS_FAILCODE) == 100, "target 0 kg -> fail 100 invalid recipe");
  setup(); scan(); P(st, CFG_STEPTIMEOUT).tv_sec = 5; s.m = 50; st.PH.value.PRM_REAL.table[5].value = -5; P(st, CMD_START) = 1;
  run_for(20); CHECK(P(st, STS_STEP) == 20 && st.PH.value.ALM_STEPTIMEOUT.INP_COND.value, "recovery stuck > 5 s -> step timeout alarm");


  printf("\n== 9. FB_Phase template: placeholder step completes after 5 s ==\n");
  memset(&tp, 0, sizeof tp); FB_PHASE_init__(&tp, 0); tp.PERMOK.value = 1; tp.INTLKOK.value = 1;
  for (int k = 0; k < 2; k++) { __CURRENT_TIME.tv_nsec += 100000000; if (__CURRENT_TIME.tv_nsec >= 1000000000) { __CURRENT_TIME.tv_sec++; __CURRENT_TIME.tv_nsec -= 1000000000; } FB_PHASE_body__(&tp); }
  CHECK(tp.BAR.value.CFG_NUMSEG.value == 3, "template loads 3 bar labels");
  tp.PH.value.CMD_START.value = 1; int n = 0;
  while (tp.PH.value.STS_STATE.value != 2 && n < 200) { __CURRENT_TIME.tv_nsec += 100000000; if (__CURRENT_TIME.tv_nsec >= 1000000000) { __CURRENT_TIME.tv_sec++; __CURRENT_TIME.tv_nsec -= 1000000000; } FB_PHASE_body__(&tp); n++; }
  printf("   completed after %.1f s, bar %d %d %d\n", n * 0.1, tp.BAR.value.STS_SEG.table[0].value, tp.BAR.value.STS_SEG.table[1].value, tp.BAR.value.STS_SEG.table[2].value);
  CHECK(tp.PH.value.STS_STATE.value == 2 && n >= 50 && n <= 53, "Complete about 5 s after Start, bar all Done");

  printf("\n== 10. Pause the feed while pressurising: paused before Supply, compressor kept running unloaded ==\n");
  setup(); scan(); P(st, CMD_START) = 1;
  CHECK(run_until(c_feed_s40, 600), "feed pressurising (step 40)");
  P(fd, CMD_PAUSE) = 1; scan(); CHECK(P(fd, STS_CMDREJECTED) && P(fd, STS_STATE) == 1, "operator Pause rejected: the unit owns the feed");
  P(fd, PROG_CMD) = 7;
  CHECK(run_until(c_feed_paused, 60), "feed Paused at the 40 -> 50 transition");
  run_for(3);
  CHECK(P(fd, STS_STEP) == 50 && f.run && fd.OUT_RECYCLE.value && !fd.OUT_COMPLOAD.value && !fd.FEEDREADY.value,
        "paused: compressor running unloaded on recycle, FeedReady off");
  CHECK(P(st, STS_STATE) == 1 && !st.OUT_INLET.value, "station waits with its inlet closed");
  P(fd, PROG_CMD) = 8; run_for(1);
  CHECK(P(fd, STS_STATE) == 1 && fd.FEEDREADY.value, "Resume: supply, FeedReady on");
  CHECK(run_until(c_stn_done, 2000), "station completes");
  P(fd, CMD_HOLD) = 1;
  CHECK(run_until(c_feed_held, 30) && !f.run && !fd.OUT_SRCVLV.value, "Hold in supply: compressor stopped, source closed");
  printf("\n%s: %d failure(s)\n", fails ? "FAILED" : "ALL PASSED", fails);
  return fails != 0;
}
