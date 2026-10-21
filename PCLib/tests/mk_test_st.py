"""Write one IEC 61131-3 file with the PCLib phase DDTs, DFBs and the example unit program
for MatIEC: python mk_test_st.py <PCLib folder> <out.st>

MatIEC differences from Control Expert handled here:
  - STRING[n] in a structure is not accepted, so strings become plain STRING.
  - T_Alarm and FB_Alarm come from PCLib_DFB_AI_CE_V16.2.xdb in Control Expert; a stub
    with the members the phase core uses stands in for them.
"""
import re
import sys

sys.path.insert(0, sys.argv[1])
import gen_phase as g  # noqa: E402

out = ["TYPE",
       "  T_Alarm : STRUCT",
       "    Inp_Cond : BOOL; Inp_Suppress : BOOL; Cfg_En : BOOL; Sts_Active : BOOL; Sts_State : INT;",
       "  END_STRUCT;"]
for d in g.DDTS:
    out.append(f"  {d['name']} : STRUCT")
    out += [f"    {n} : {t}{' := ' + i if i else ''};" for n, t, c, i in d["members"]]
    out.append("  END_STRUCT;")
out.append("END_TYPE\n")
out.append("""FUNCTION_BLOCK FB_Alarm
VAR_INPUT SuppressIn : BOOL; END_VAR
VAR_IN_OUT Alm : T_Alarm; END_VAR
Alm.Sts_Active := Alm.Inp_Cond AND NOT SuppressIn;
END_FUNCTION_BLOCK
""")
out += [g.st_text(fb) for fb in g.DFBS]
out.append(g.unit_program())
open(sys.argv[2], "w").write(re.sub(r"STRING\[\d+\]", "STRING", "\n".join(out)))
