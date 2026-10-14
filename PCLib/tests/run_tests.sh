#!/usr/bin/env bash
# Compile the PCLib phase DFBs and the example unit program with MatIEC (an open-source
# IEC 61131-3 compiler), then run sim.c: a scan-by-scan process simulation of the xenon
# feed and one fill station that checks the ISA-88 behaviour (56 checks).
# Needs git, gcc, make, autoconf, automake, flex and bison. Not a substitute for
# Analyze Project and simulator tests in Control Expert.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
PCLIB=$(dirname "$HERE")
WORK=${WORK:-$HERE/.build}
mkdir -p "$WORK"
if [ ! -x "$WORK/matiec/iec2c" ]; then
  git clone -q --depth 1 https://github.com/beremiz/matiec.git "$WORK/matiec"
  (cd "$WORK/matiec" && autoreconf -i >/dev/null 2>&1 && ./configure >/dev/null && make -j4 >/dev/null)
fi
# Control Expert converts DINT <-> TIME in milliseconds, MatIEC in seconds: patch a copy of its runtime.
rm -rf "$WORK/lib" && cp -r "$WORK/matiec/lib/C" "$WORK/lib"
sed -i 's|return (TIME){IN, 0};}|return (TIME){IN / 1000, (IN % 1000) * 1000000};}|; s|{return IN.tv_sec;}|{return IN.tv_sec * 1000 + IN.tv_nsec / 1000000;}|' "$WORK/lib/iec_std_lib.h"
grep -q "IN / 1000, (IN % 1000)" "$WORK/lib/iec_std_lib.h" || { echo "TIME patch did not apply"; exit 1; }

python3 "$PCLIB/gen_phase.py" >/dev/null
python3 "$HERE/mk_test_st.py" "$PCLIB" "$WORK/all.st"
(cd "$WORK" && "$WORK/matiec/iec2c" -I "$WORK/matiec/lib" -T "$WORK" all.st >/dev/null)
echo "MatIEC: DFBs and unit program compile"
gcc -O0 -w -I "$WORK" -I "$WORK/lib" "$HERE/sim.c" -o "$WORK/sim" -lm
"$WORK/sim" "$@"
