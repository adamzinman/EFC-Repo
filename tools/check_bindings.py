#!/usr/bin/env python3
"""Check every tag binding in projects/EFC_Library against the UDT definitions the build targets.

    python3 tools/check_bindings.py              # legacy-ddt build: members must exist in tags/legacy/*.json (+ demo UDTs)
    python3 tools/check_bindings.py --t          # EFCLib v1 build: members must exist in types/export/PCLib_Ignition81.json
    python3 tools/check_bindings.py -v           # also list every member each view binds

For each view.json it collects
  - indirect tag bindings whose path is {0}/Member... or {1}/Member... (references {view.params.tagPath}),
  - tag paths built in scripts and expressions as tagPath + '/Member' (efc.ui.cmd / pulse members, writeBlocking paths,
    queryTagHistory pens),
works out which type the view binds (its params.tType, or the type of the window / part that embeds it) and asserts
every member path exists in that type (folders, nested UDT instances and `.engUnit`-style tag properties included).
In the legacy build it also fails on any member name that exists only in the T_ types (Sts_Avail, Cmd_Bypass,
Mode/Sts_Man, Cfg_Tag, Val_PV ...). Exit code 1 when anything is unknown.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = os.path.join(ROOT, "projects", "EFC_Library", "com.inductiveautomation.perspective", "views")
UI = os.path.join(ROOT, "projects", "EFC_Library", "ignition", "script-python", "efc", "ui", "code.py")

# T_-only member names: must not appear in any legacy binding
T_ONLY = ["Sts_Avail", "Cmd_Bypass", "Cmd_Unbypass", "Mode/Sts_Man", "Mode/Sts_Auto", "Mode/Sts_OOS", "Mode/Sts_Maint", "Cfg_Tag", "Cfg_Desc",
          "Val_PV", "Sts_NotPerm", "Sts_Intlk", "Sts_Local", "Sts_Fault", "Out_Open", "Sts_Opened", "Sts_Closed", "Cmd_Open", "Cmd_Close",
          "Cmd_Start", "Cmd_Stop", "Out_Run", "Sts_Running", "Sts_Stopped", "Val_Demand", "Val_Pos", "Cfg_HasFbk", "Cfg_EU", "Cfg_EUMin",
          "Cfg_EUMax", "Alm_HH", "Alm_H", "Alm_L", "Alm_LL", "Alm_Bad", "Sts_ORng", "Sts_URng", "Sts_Bad", "Val_SP", "Out_CV", "Sts_Mode",
          "Alm_DevH", "Alm_DevL", "Cfg_PVEU", "Cfg_PVMin", "Cfg_PVMax", "Sts_Active", "Sts_Unack", "Cfg_Priority", "Cfg_Lim", "Sts_Suppressed",
          "Run/Val_RunHrs", "Sim_En", "Cfg_CondDesc", "Sts_FirstOut", "Sts_Bypassed", "Val_Net", "Prm_TargetWt", "Cmd_Select"]

# Type names by tType param; windows / parts that take their type from the embedding view
PART_TYPES = {"Templates/Dynamic Window/Parts/IntlkList": "MEM_Interlock_List",            # legacy: {tagPath}/InterlockList
              "Templates/Dynamic Window/Parts/Trend": None}                                 # pens come from the window (checked there)
T_PART_TYPES = {"Templates/Dynamic Window/Parts/IntlkList": "T_Intlk", "Templates/Dynamic Window/Parts/Trend": None,
                "Templates/Dynamic Window/Parts/BypassConfirm": "T_Intlk"}
EXEMPT_PREFIX = ("Templates/IO/", "Styles/", "Templates/Dynamic Window/IO/")               # native x80 DDTs / no tags
NO_TYPE = {"none", "native", ""}


# ----------------------------------------------------------------- UDT definitions
def load_type(node, out, prefix="", nested=None):
    """Member paths of a UDT definition (folders and nested instances flattened to a/b/c). Nested UdtInstance members
    without inline tags are recorded in `nested` {path: typeId} and expanded by expand_nested() once every type is known."""
    for t in node.get("tags", []):
        p = prefix + t["name"]
        out.add(p)
        if t.get("tags"):
            load_type(t, out, p + "/", nested)
        elif t.get("tagType") == "UdtInstance" and t.get("typeId") and nested is not None:
            nested[p] = t["typeId"].split("/")[-1]


def expand_nested(types, nested_by_type, depth=4):
    """Add <instance path>/<member> for every nested instance whose type is known (T_Mode, T_RunTime, T_AlmLim, T_Intlk ...)."""
    for _ in range(depth):
        for tname, nested in nested_by_type.items():
            for p, sub in nested.items():
                if sub in types:
                    types[tname] |= {p + "/" + m for m in types[sub]}


def find_types(node, path=""):
    if node.get("tagType") == "UdtType":
        yield node
    for c in node.get("tags", []):
        yield from find_types(c)


def legacy_types():
    types, nested = {}, {}
    for d in (os.path.join(ROOT, "tags", "legacy"), os.path.join(ROOT, "tags"), os.path.join(ROOT, "tags", "PID_Loops")):
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if not f.endswith(".json"):
                continue
            data = json.load(open(os.path.join(d, f), encoding="utf-8"))
            for t in find_types(data):
                s, n = set(), {}; load_type(t, s, "", n)
                types.setdefault(t["name"], set()).update(s); nested.setdefault(t["name"], {}).update(n)
    expand_nested(types, nested)                       # e.g. DDT_Valve.InterlockList is a MEM_Interlock_List instance
    for demo, real in (("DDT_Valve_Demo", "DDT_Valve"), ("DDT_Device_Demo", "DDT_Device"), ("DDT_Process_Value_Demo", "DDT_Process_Value"),
                       ("DDT_Station_Demo", "DDT_Station")):
        if demo in types and real in types:            # the memory stand-ins may not carry every member; the real type rules
            types[demo] = types[real]
    return types


def t_types():
    types, nested = {}, {}
    for f in (os.path.join(ROOT, "types", "export", "PCLib_Ignition81.json"), os.path.join(ROOT, "types", "T_KPI", "T_KPI_Ignition81.json")):
        for t in find_types(json.load(open(f, encoding="utf-8"))):
            s, n = set(), {}; load_type(t, s, "", n); types[t["name"]] = s; nested[t["name"]] = n
    expand_nested(types, nested)                       # embedded groups (Mode: T_Mode, Run: T_RunTime, Alm_x: T_AlmLim, Intlk: T_Intlk)
    return types


# ----------------------------------------------------------------- bindings in a view
def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)


SCRIPT_MEMBER = re.compile(r"""(?:tagPath|base|p|tp)\s*\+\s*['"]/([A-Za-z_][\w/\.]*)['"]""")
UI_MEMBER = re.compile(r"""efc\.ui\.(?:cmd|pulse)\(self,\s*['"]([\w/\.]+)['"]""")


def members_of(view, text):
    """(member path, where) for every binding / script reference in this view."""
    out = []
    for o in walk(view):
        b = o.get("binding") if isinstance(o, dict) else None
        if b and b.get("type") == "tag":
            cfg = b.get("config", {})
            tp = cfg.get("tagPath", "")
            refs = cfg.get("references", {}) or {}
            m = re.match(r"\{(\d)\}/(.+)$", tp)
            if m and "tagPath" in str(refs.get(m.group(1), "")):
                out.append((m.group(2), "tag binding"))
            elif cfg.get("mode") == "direct" and tp.startswith("[default]"):
                pass                                                   # demo views: direct paths to demo instances
            elif m:
                out.append((m.group(2), "tag binding (ref %s)" % refs.get(m.group(1))))
        if isinstance(o, dict) and o.get("type") == "ia.display.view":
            pens = (o.get("props", {}).get("params", {}) or {}).get("pens")
            if pens:
                out.extend((p, "trend pen") for p in pens)
    for mm in SCRIPT_MEMBER.finditer(text):
        out.append((mm.group(1), "script path"))
    for mm in UI_MEMBER.finditer(text):
        out.append((mm.group(1), "efc.ui command"))
    return out


def view_type(path, view, legacy):
    parts = PART_TYPES if legacy else T_PART_TYPES
    if path in parts:
        return parts[path]
    tt = (view.get("params") or {}).get("tType")
    if tt is None and "/Station/" in path:            # Designer-built Station views: only the tile carries tType
        tt = "DDT_Station" if legacy else "T_Station"
    if tt in NO_TYPE:
        return None
    return tt


def exists(types, tname, member):
    member = re.sub(r"/\{\d\}$", "", member)          # {0}/Intlk/Cfg_CondDesc/{1}: a second reference indexes the folder
    base = member.split(".")[0]                       # PV.engUnit -> PV (tag property)
    if "." in member and member.split(".")[1] not in ("engUnit", "engLow", "engHigh", "formatString", "documentation", "tooltip"):
        return False
    s = types.get(tname)
    if s is None:
        return False
    if base in s:
        return True
    if "/" in base:                                   # Alm_HH/Cfg_Lim with Alm_HH an embedded instance listed with its members
        return base in s
    return False


def main():
    legacy = "--t" not in sys.argv
    verbose = "-v" in sys.argv
    types = legacy_types() if legacy else t_types()
    bad, n_members, n_views = [], 0, 0
    views = sorted(os.path.relpath(d, VIEWS).replace(os.sep, "/") for d, _, fs in os.walk(VIEWS) if "view.json" in fs)
    for vp in views:
        if vp.startswith(EXEMPT_PREFIX) or vp.endswith("/_Demo") or vp.endswith("/_Examples") or vp == "Templates/_Demo":
            continue
        text = open(os.path.join(VIEWS, vp, "view.json"), encoding="utf-8").read()
        view = json.loads(text)
        tname = view_type(vp, view, legacy)
        mems = members_of(view, text)
        if tname is None:
            if mems and not vp.endswith("Parts/Trend"):
                bad.append(f"{vp}: binds {sorted(set(m for m, _ in mems))} but has no type")
            continue
        n_views += 1
        seen = sorted(set(mems))
        if verbose:
            print(f"{vp}  [{tname}]")
            for m, w in seen:
                print(f"    {m}  ({w})")
        for m, where in seen:
            n_members += 1
            if not exists(types, tname, m):
                bad.append(f"{vp}: {tname} has no member {m}  ({where})")
            if legacy and any(m == t or m.startswith(t + "/") or m.endswith("/" + t) for t in T_ONLY):
                bad.append(f"{vp}: T_-only member name {m}  ({where})")
    if legacy and os.path.isfile(UI):                  # efc.ui tables in the legacy build
        code = open(UI).read()
        if "\nLEGACY = True\n" not in code:
            bad.append("efc.ui: LEGACY flag not set")
        rows = re.findall(r"'(DDT_\w+)':\s*\('(\w+)', '(\w+)', (\[[^\]]*\]), (\[[^\]]*\]), (\[[^\]]*\])\)", code)
        if not rows:
            bad.append("efc.ui: LEGACY_DBL table not found")
        for t, state, cmd, ready, blk_all, blk_on in rows:
            lists = [json.loads(x.replace("'", '"')) for x in (ready, blk_all, blk_on)]
            for m in [state, cmd] + lists[0] + lists[1] + lists[2]:
                if not exists(types, t, m):
                    bad.append(f"efc.ui LEGACY_DBL: {t} has no member {m}")
    print(f"{n_views} typed views, {n_members} member references checked against {len(types)} types "
          f"({'legacy DDT_' if legacy else 'EFCLib v1 T_'})")
    if bad:
        print("UNKNOWN:\n  " + "\n  ".join(sorted(set(bad))))
        sys.exit(1)
    print("OK: every bound member exists" + (" and no T_-only member name remains" if legacy else ""))


if __name__ == "__main__":
    main()
