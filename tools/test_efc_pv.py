#!/usr/bin/env python3
"""CPython test of generator/docks/efc_pv.py (efc.pv) with a fake `system`: unit -> type grouping, the registry
(register / unregister / rebind / purge, parallel registration), chart config shape. Run by build.py.

    python3 tools/test_efc_pv.py
"""
import os, sys, threading, types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "generator", "docks", "efc_pv.py")

# ----------------------------------------------------------------- fake Ignition
TAGS = {}
MESSAGES = []
GLOBALS = {}


class Q:
    def __init__(self, v): self.value = v


class _Tag:
    @staticmethod
    def readBlocking(paths): return [Q(TAGS.get(p)) for p in paths]


class _Util:
    @staticmethod
    def getGlobals(): return GLOBALS

    @staticmethod
    def getLogger(name):
        class L:
            def debug(self, m): pass
            def info(self, m): pass
            def warn(self, m): pass
        return L()


class _Persp:
    @staticmethod
    def sendMessage(t, payload=None, scope=None, sessionId=None, pageId=None): MESSAGES.append((t, scope, pageId))


system = types.SimpleNamespace(tag=_Tag, util=_Util, perspective=_Persp)


class NS(dict):
    def __getattr__(self, k):
        try: return self[k]
        except KeyError: raise AttributeError(k)
    def __setattr__(self, k, v): self[k] = v


def component(session="s1", page="p1", path="/overview", **params):
    c = NS(session=NS(props=NS(id=session)), page=NS(props=NS(pageId=page, path=path)),
           view=NS(params=NS(**params), custom=NS()))
    chart = NS(props=NS())
    c.getChild = lambda name: chart
    c._chart = chart
    return c


def load():
    ns = {"system": system}
    exec(compile(open(SRC).read(), SRC, "exec"), ns)
    return ns


def check(cond, msg):
    if not cond:
        print("FAIL:", msg); sys.exit(1)


def main():
    pv = load()
    # unit -> type
    for eu, tag, want in [("PSIG", "PT-101", "pressure"), ("°F", "TT-5", "temperature"), ("Deg C", "", "temperature"),
                          ("SCFM", "FT-1", "flow"), ("kg/h", "", "flow"), ("%", "LT-7", "level"), ("%", "", "percent"),
                          ("", "FIC-3", "flow"), ("", "", "other"), ("pH", "AT-2", "analysis"), ("Hz", "", "speed"),
                          ("kg", "WT-1", "weight"), ("in H2O", "", "dp"), ("ft", "LT-9", "level"), ("rpm", "ST-1", "speed")]:
        got = pv["var_type"](eu, tag)
        check(got == want, "var_type(%r, %r) = %r, want %r" % (eu, tag, got, want))
    # registry
    TAGS.update({"[default]PV_Demo/PT001/Cfg_EU": "PSIG", "[default]PV_Demo/PT001/Cfg_Tag": "PT-001", "[default]PV_Demo/PT001/Cfg_Desc": "Header",
                 "[default]PID_Demo/TIC101/Cfg_PVEU": "°F", "[default]PID_Demo/TIC101/Cfg_Tag": "TIC-101", "[default]PID_Demo/TIC101/Cfg_Desc": "Jacket"})
    a = component(tagPath="[default]PV_Demo/PT001", tType="T_AI")
    b = component(tagPath="[default]PID_Demo/TIC101", tType="T_PID")
    hidden = component(tagPath="[default]PV_Demo/PT002", tType="T_AI", census=False)
    pv["register"](a); pv["register"](b); pv["register"](hidden)
    ov = component()
    ents = pv["entries"](ov)
    check([e["tagPath"] for e in ents] == ["[default]PV_Demo/PT001", "[default]PID_Demo/TIC101"], "entries sorted by tag: %r" % [e["tagPath"] for e in ents])
    check(ents[0]["type"] == "pressure" and ents[1]["type"] == "temperature", "types")
    check(len(ents[1]["pens"]) == 2 and ents[1]["pens"][1]["kind"] == "sp", "PID gets PV + SP pens")
    check(MESSAGES and MESSAGES[-1][0] == "efc.pvChanged", "notify sent")
    # other screen in the same tab is not listed
    check(pv["entries"](component(path="/other")) == [], "page path filter")
    # groups and chart
    gs = pv["groups"](ents)
    check([g["type"] for g in gs] == ["pressure", "temperature"], "group order follows VAR_TYPES: %r" % [g["type"] for g in gs])
    cfg = pv["chart"](gs, 30)
    check(len(cfg["plots"]) == 2 and len(cfg["axes"]) == 2 and len(cfg["pens"]) == 3, "chart shape")
    check(cfg["pens"][0]["plot"] == 0 and cfg["pens"][1]["plot"] == 1 and cfg["pens"][2]["axis"] == "temperature_1", "pen -> plot/axis")
    check(cfg["pens"][0]["data"]["source"] == "[default]PV_Demo/PT001/Val_PV", "pen source path")
    check(cfg["axes"][0]["label"]["text"] == "PSIG" and cfg["axes"][0]["range"]["auto"] is True, "axis schema")
    check(set(cfg["pens"][0]["display"]["styles"]) == {"normal", "highlighted", "selected", "muted"}, "pen style states")
    check(cfg["unitOfTime"] == 30 and cfg["measureOfTime"] == "minutes", "range keys")
    # refresh writes the chart once per change
    check(pv["refresh"](ov) is True and pv["refresh"](ov) is False, "refresh only on change")
    check(len(ov._chart.props.pens) == 3 and ov.view.custom.count == 2, "chart props written")
    # rebind, unregister
    class QV:
        def __init__(self, v): self.value = v
    view_a = NS(rootContainer=a, params=a.view.params)          # on a view-param change script, self is the view
    pv["rebind"](view_a, QV("[default]PV_Demo/PT001"), QV("[default]PV_Demo/PT003"))
    paths = [e["tagPath"] for e in pv["entries"](ov)]
    check("[default]PV_Demo/PT003" in paths and "[default]PV_Demo/PT001" not in paths, "rebind swaps the entry: %r" % paths)
    pv["unregister"](b)
    check(len(pv["entries"](ov)) == 1, "unregister")
    # parallel registration keeps every entry
    comps = [component(tagPath="[default]X/PT%03d" % i, tType="T_AI") for i in range(200)]
    ts = [threading.Thread(target=pv["register"], args=(c,)) for c in comps]
    [t.start() for t in ts]; [t.join() for t in ts]
    check(len(pv["entries"](ov)) == 201, "parallel registration: %d" % len(pv["entries"](ov)))
    # purge on session shutdown
    pv["purgeSession"]("s1")
    check(pv["entries"](ov) == [], "purgeSession")
    # cap on plots and pens
    many = [{"tagPath": "t%d" % i, "type": t, "eu": "x", "tag": "", "desc": "", "pens": [{"name": "p", "path": "t%d/Val_PV" % i, "kind": "pv"}]}
            for i, t in enumerate(["pressure"] * 10 + ["flow", "level", "speed", "weight", "volume", "other", "analysis"])]
    gs = pv["groups"](many)
    check(len(gs) == 6 and len(gs[0]["pens"]) == 8 and gs[0]["dropped"] == 2, "caps: %d plots, %d pens" % (len(gs), len(gs[0]["pens"])))
    print("efc.pv tests OK")


if __name__ == "__main__":
    main()
