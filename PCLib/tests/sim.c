/* Scan-by-scan simulation of FB_PhXeFill (one sequence, six stations) on the C code MatIEC generates
   from the phase DFBs (built and run by run_tests.sh). 100 ms scans; simple process model:
   per station cylinder pressure from xenon mass, heel recovery, vacuum and leak, scale with tare and
   valve in-flight; shared source cylinder, compressor and fill header. Each CHECK is one behaviour. */
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

#define NS 6
#define P(X) (px.PH.value.X.value)
#define B(X) (px.BAR.value.X.value)
#define U(X) (px.U.value.X.value)
#define S(i, X) (px.U.value.STN.table[i].X.value)
#define PRM(i) (px.PH.value.PRM_REAL.table[(i) - 1].value)
#define PRD(i) (px.PH.value.PRM_DINT.table[(i) - 1].value)
#define RPT(i) (px.PH.value.RPT_REAL.table[(i) - 1].value)
#define RPD(i) (px.PH.value.RPT_DINT.table[(i) - 1].value)
#define SEG(i) (px.BAR.value.STS_SEG.table[(i) - 1].value)

static const double DTS = 0.1;
static double now_s = 0;
static int fails = 0, verbose = 1;
#define CHECK(c, msg) do { if (c) printf("   PASS  %s\n", msg); else { printf("   FAIL  %s\n", msg); fails++; } } while (0)

typedef struct { double m, cyl, tare, leak, offt, lastflow, t_done, t_last_inlet; int ever_open; } Stn;
static Stn st[NS];
static double hdr, src, runT;
static int comp_run, intlk_override[NS];
static FB_PHXEFILL_data__ px;
static FB_PHASE_data__ tp;
static const char *SN[] = {"Idle","Running","Complete","Pausing","Paused","Holding","Held","Restarting","Stopping","Stopped","Aborting","Aborted"};

static void str(char *o, IEC_STRING *x) { int n = x->len; memcpy(o, x->body, n); o[n] = 0; }
static void tick(void) { __CURRENT_TIME.tv_nsec += 100000000; if (__CURRENT_TIME.tv_nsec >= 1000000000) { __CURRENT_TIME.tv_sec++; __CURRENT_TIME.tv_nsec -= 1000000000; } }

static void setup(const double *targets) {
  memset(&px, 0, sizeof px);
  FB_PHXEFILL_init__(&px, 0);
  for (int i = 0; i < NS; i++) {
    memset(&st[i], 0, sizeof st[i]);
    st[i].m = 2.0 + i; st[i].cyl = 50.0; st[i].tare = 50.0; st[i].leak = 0.001; st[i].offt = 99; st[i].lastflow = -99;
    st[i].t_done = -1; st[i].t_last_inlet = -1; intlk_override[i] = 0;
    PRM(i + 1) = targets[i];
  }
  double pr[10] = {0.2, 0.1, 1.0, 0.12, 0.2, 1.0, 0.5, 60.0, 30.0, 3.0};   /* Prm_Real[7..16] */
  for (int k = 0; k < 10; k++) PRM(NS + 1 + k) = pr[k];
  long long pd[6] = {3, 10, 2, 200, 800, 5};
  for (int k = 0; k < 6; k++) PRD(k + 1) = pd[k];
  P(CFG_STEPTIMEOUT).tv_sec = 900;
  px.PERMOK.value = 1; px.INTLKOK.value = 1;
  hdr = 0; src = 800; runT = 0; comp_run = 0; now_s = 0;
}

static int pst = -1, pstep = -1;
static void scan(void) {
  /* ---- process model, using last scan's outputs ---- */
  double used = 0;
  for (int i = 0; i < NS; i++) {
    Stn *c = &st[i];
    if (S(i, OUT_INLET)) { c->offt = 0; c->ever_open = 1; c->t_last_inlet = now_s; } else c->offt += DTS;
    int inlet_act = c->offt < 0.1;                          /* 0.1 s valve closing delay */
    double pabs = c->m * 1000.0, pt = pabs / 1000.0 - 1.013;
    if (S(i, OUT_RECOVER) && pabs > 1100) c->m -= 0.5 * DTS;
    if (S(i, OUT_VAC)) { c->m *= exp(-DTS / 3.0); if (c->m < 0.0003) c->m = 0.0003; }
    if (pabs < 1013) c->m += c->leak / 1000.0 * DTS;
    if (inlet_act && hdr > pt + 1.0) { c->m += 0.5 * DTS; used += 0.5 * DTS; c->lastflow = now_s; }
    if (S(i, OUT_TARE)) c->tare = c->cyl + c->m;
  }
  if (U(OUT_COMPRUN)) runT += DTS; else runT = 0;
  comp_run = U(OUT_COMPRUN) && runT >= 1.0;
  double suct = U(OUT_SRCVLV) ? 10.0 : 0.0;
  if (comp_run && U(OUT_COMPLOAD) && suct > 1) hdr += 3.0 * DTS;
  hdr -= used * 1.2; if (hdr < 0) hdr = 0;
  src -= used;
  /* ---- inputs ---- */
  for (int i = 0; i < NS; i++) {
    Stn *c = &st[i];
    S(i, INP_VESSELOK) = 1; S(i, INP_INTLKOK) = !intlk_override[i];
    S(i, INP_NETWT) = c->cyl + c->m - c->tare; S(i, INP_WTSTABLE) = (now_s - c->lastflow) > 1.0;
    S(i, INP_PT) = c->m - 1.013; S(i, INP_VACPT) = c->m * 1000.0;
  }
  U(INP_SRCWT) = src; U(INP_SUCTPT) = suct; U(INP_HDRPT) = hdr; U(INP_COMPRDY) = 1; U(INP_COMPRUN) = comp_run;
  /* ---- PLC scan ---- */
  tick();
  FB_PHXEFILL_body__(&px);
  now_s += DTS;
  for (int i = 0; i < NS; i++) if (S(i, STS_STATE) == 9 && st[i].t_done < 0) st[i].t_done = now_s;
  if (verbose && (P(STS_STATE) != pst || P(STS_STEP) != pstep)) {
    char m[64]; str(m, &B(VAL_MSG));
    printf("  %7.1fs %-10s step %3d seg %d hdr %5.1f | stn", now_s, SN[P(STS_STATE)], P(STS_STEP), B(STS_ACTSEG), hdr);
    for (int i = 0; i < NS; i++) printf(" %2d", S(i, STS_STATE));
    printf(" | %s\n", m);
    pst = P(STS_STATE); pstep = P(STS_STEP);
  }
}
static int run_until(int (*cond)(void), double maxs) { double t0 = now_s; while (now_s - t0 < maxs) { scan(); if (cond()) return 1; } return 0; }
static void run_for(double secs) { double t0 = now_s; while (now_s - t0 < secs) scan(); }
static int c_done(void) { return P(STS_STATE) == 2; }
static int c_held(void) { return P(STS_STATE) == 6; }
static int c_fill(void) { return P(STS_STATE) == 1 && P(STS_STEP) == 80; }
static int c_first_stn_done(void) { for (int i = 0; i < NS; i++) if (S(i, STS_STATE) == 9) return 1; return 0; }
static int c_paused(void) { return P(STS_STATE) == 4; }
static int c_aborted(void) { return P(STS_STATE) == 11; }
static int bar_is(const int *e) { for (int i = 1; i <= 6; i++) if (SEG(i) != e[i - 1]) return 0; return 1; }
static void show_bar(void) { printf("   bar:"); for (int i = 1; i <= 6; i++) printf(" %d", SEG(i)); printf("\n"); }
static int any_valve(int i) { return S(i, OUT_INLET) || S(i, OUT_RECOVER) || S(i, OUT_VAC) || S(i, OUT_TARE); }
static int all_off(void) { for (int i = 0; i < NS; i++) if (any_valve(i)) return 0; return !U(OUT_SRCVLV) && !U(OUT_COMPLOAD); }
static int in_tol(int i) { double w = S(i, VAL_FINALWT), t = PRM(i + 1); return w >= t - 0.1 && w <= t + 0.2; }
static void results(void) {
  printf("   station: state fail final(kg) target topups leak(mbar) done(s)\n");
  for (int i = 0; i < NS; i++)
    printf("     %d      %2d    %3d  %7.3f  %5.1f   %d     %6.3f   %6.1f\n", i + 1, S(i, STS_STATE), S(i, STS_FAILCODE),
           S(i, VAL_FINALWT), PRM(i + 1), S(i, STS_TOPUPS), S(i, VAL_LEAKRISE), st[i].t_done);
}

int main(void) {
  static const int ALLDONE[6] = {2, 2, 2, 2, 2, 2};
  double sel4[NS] = {20, 10, 0, 15, 0, 25};

  printf("== 1. One sequence fills stations 1, 2, 4, 6 (3 and 5 not selected) ==\n");
  setup(sel4); scan();
  CHECK(B(CFG_NUMSEG) == 6, "one sequence bar, 6 segments");
  P(CMD_START) = 1;
  int inlet_after_first = 0, inlet_after_done = 0;
  verbose = 1;
  while (now_s < 3000 && P(STS_STATE) != 2) {
    scan();
    for (int i = 0; i < NS; i++) if (S(i, STS_STATE) == 9 && S(i, OUT_INLET)) inlet_after_done = 1;
    if (c_first_stn_done()) for (int i = 0; i < NS; i++) if (S(i, STS_STATE) != 9 && S(i, OUT_INLET)) inlet_after_first = 1;
  }
  results();
  CHECK(P(STS_STATE) == 2, "sequence Complete");
  CHECK(in_tol(0) && in_tol(1) && in_tol(3) && in_tol(5), "every selected station inside +0.2 / -0.1 kg of its own target");
  CHECK(!st[2].ever_open && !st[4].ever_open && S(2, STS_STATE) == 0 && S(4, STS_STATE) == 0, "stations 3 and 5 untouched");
  CHECK(st[1].t_done < st[3].t_done && st[3].t_done < st[0].t_done && st[0].t_done < st[5].t_done,
        "stations finish one by one (10, 15, 20, 25 kg)");
  CHECK(!inlet_after_done, "a filled station's inlet never opens again");
  CHECK(inlet_after_first, "other stations keep filling after the first one closes");
  show_bar(); CHECK(bar_is(ALLDONE), "bar: all segments Done");
  printf("   reports: total %.2f kg, source %.1f -> %.1f kg, filled %lld, faulted %lld\n", RPT(7), RPT(8), RPT(9),
         (long long)RPD(1), (long long)RPD(2));
  CHECK(RPD(1) == 4 && RPD(2) == 0 && fabs(RPT(7) - (RPT(1) + RPT(2) + RPT(4) + RPT(6))) < 0.001, "reports: 4 filled, total");
  CHECK(all_off() && !comp_run, "everything closed and compressor stopped");

  printf("\n== 2. Station 4 fails its leak check: dropped, the others fill ==\n");
  setup(sel4); st[3].leak = 0.2; scan(); P(CMD_START) = 1; verbose = 0;
  CHECK(run_until(c_done, 3000), "sequence Complete");
  results();
  CHECK(S(3, STS_STATE) == 10 && S(3, STS_FAILCODE) == 101 && !st[3].ever_open, "station 4: fault 101, inlet never opened");
  CHECK(in_tol(0) && in_tol(1) && in_tol(5) && RPD(1) == 3 && RPD(2) == 1, "stations 1, 2, 6 filled; report 3 filled / 1 faulted");

  printf("\n== 3. Every selected station leaks: nothing left to fill ==\n");
  double sel2[NS] = {20, 10, 0, 0, 0, 0};
  setup(sel2); st[0].leak = 0.2; st[1].leak = 0.2; scan(); P(CMD_START) = 1; verbose = 1;
  CHECK(run_until(c_held, 600) && P(STS_FAILCODE) == 301, "fail 301, sequence Held");
  { static const int e[6] = {2, 2, 3, 0, 0, 0}; show_bar(); CHECK(bar_is(e), "bar: Leak check segment = Fault"); }
  CHECK(all_off(), "everything closed");

  printf("\n== 4. Station 1 interlock trips mid-fill: station 1 dropped, the others carry on ==\n");
  setup(sel4); scan(); P(CMD_START) = 1; verbose = 0;
  CHECK(run_until(c_fill, 900), "filling");
  run_for(8); intlk_override[0] = 1; scan(); scan();
  CHECK(S(0, STS_STATE) == 10 && S(0, STS_FAILCODE) == 105 && !S(0, OUT_INLET), "station 1: fault 105, inlet closed");
  CHECK(P(STS_STATE) == 1, "sequence still running");
  CHECK(run_until(c_done, 3000) && in_tol(1) && in_tol(3) && in_tol(5), "stations 2, 4, 6 complete");

  printf("\n== 5. Operator Hold mid-fill, then Restart ==\n");
  setup(sel4); scan(); P(CMD_START) = 1; verbose = 1;
  CHECK(run_until(c_fill, 900), "filling");
  run_for(10); P(CMD_HOLD) = 1;
  CHECK(run_until(c_held, 30), "Held");
  CHECK(all_off() && !comp_run, "Held: every inlet closed, source closed, compressor stopped");
  double w[NS]; for (int i = 0; i < NS; i++) w[i] = S(i, INP_NETWT);
  run_for(10); int same = 1; for (int i = 0; i < NS; i++) if (fabs(S(i, INP_NETWT) - w[i]) > 0.01) same = 0;
  CHECK(same, "no weight change while held");
  P(CMD_RESTART) = 1;
  CHECK(run_until(c_fill, 60), "Restarting starts the compressor and resumes the fill step");
  CHECK(run_until(c_done, 3000) && in_tol(0) && in_tol(1) && in_tol(3) && in_tol(5), "Complete, all in tolerance");

  printf("\n== 6. Pause during fill: the fill step finishes, then Paused before shutdown ==\n");
  setup(sel4); scan(); P(CMD_START) = 1; verbose = 0;
  CHECK(run_until(c_fill, 900), "filling");
  run_for(5); P(CMD_PAUSE) = 1; scan();
  CHECK(P(STS_STATE) == 3, "Pausing: stations keep filling");
  CHECK(run_until(c_paused, 3000), "Paused when the last station finished");
  run_for(2);
  CHECK(P(STS_STEP) == 90 && comp_run && U(OUT_RECYCLE) && !U(OUT_COMPLOAD), "paused before shutdown: compressor unloaded");
  P(CMD_RESUME) = 1;
  CHECK(run_until(c_done, 60), "Resume: shutdown and Complete");

  printf("\n== 7. Semi-automatic: each step waits for Advance with everything closed ==\n");
  setup(sel4); scan(); P(CMD_SEMIAUTO) = 1; scan(); P(CMD_START) = 1;
  int adv = 0, closed = 1;
  while (now_s < 4000 && P(STS_STATE) != 2) {
    scan();
    if (P(STS_WAITADVANCE)) {
      scan();
      for (int i = 0; i < NS; i++) if (any_valve(i)) closed = 0;
      if (U(OUT_COMPLOAD)) closed = 0;
      run_for(2); P(CMD_ADVANCE) = 1; adv++;
    }
  }
  printf("   advances: %d\n", adv);
  CHECK(P(STS_STATE) == 2 && adv == 8, "Complete after 8 Advances (one per transition)");
  CHECK(closed, "station valves closed and compressor unloaded while waiting");

  printf("\n== 8. No station selected ==\n");
  double none[NS] = {0};
  setup(none); scan(); P(CMD_START) = 1;
  CHECK(run_until(c_held, 5) && P(STS_FAILCODE) == 300, "fail 300 No station selected");

  printf("\n== 9. E-stop mid-fill -> Aborted, everything off ==\n");
  setup(sel4); scan(); P(CMD_START) = 1;
  CHECK(run_until(c_fill, 900), "filling");
  run_for(5); px.ESTOP.value = 1;
  CHECK(run_until(c_aborted, 5) && all_off(), "Aborted, all valves closed");
  P(CMD_RESET) = 1; scan(); CHECK(P(STS_STATE) == 0, "Reset -> Idle");

  printf("\n== 10. Recipe ownership ==\n");
  setup(sel4); scan(); P(PROG_ACQUIRE) = 1; scan(); P(CMD_START) = 1; scan();
  CHECK(P(STS_STATE) == 0 && P(STS_CMDREJECTED), "operator Start rejected while a recipe owns the phase");
  P(PROG_CMD) = 1; scan(); scan();
  CHECK(P(STS_STATE) == 1, "Prog_Cmd 1 starts");

  printf("\n== 11. FB_Phase template: placeholder step completes after 5 s ==\n");
  memset(&tp, 0, sizeof tp); FB_PHASE_init__(&tp, 0); tp.PERMOK.value = 1; tp.INTLKOK.value = 1;
  tick(); FB_PHASE_body__(&tp);
  tp.PH.value.CMD_START.value = 1; int n = 0;
  while (tp.PH.value.STS_STATE.value != 2 && n < 200) { tick(); FB_PHASE_body__(&tp); n++; }
  CHECK(tp.PH.value.STS_STATE.value == 2 && n >= 50 && n <= 53, "Complete about 5 s after Start");

  printf("\n%s: %d failure(s)\n", fails ? "FAILED" : "ALL PASSED", fails);
  return fails != 0;
}
