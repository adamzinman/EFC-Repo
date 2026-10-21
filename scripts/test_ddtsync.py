"""Offline test for ddtsync.py against a mock gateway (system.opc / system.tag).

    python3 scripts/test_ddtsync.py

The mock OPC tree mimics a BMENUA0100 address space: string node ids, DDT members as
child nodes ("ns=2;s=AV001.Auto"), arrays as "[n]" children.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ddtsync


class El(object):
    def __init__(self, name, nid, et, dt=None):
        self.n, self.nid, self.et, self.dt = name, nid, et, dt

    def getDisplayName(self): return self.n
    def getNodeId(self): return self.nid
    def getElementType(self): return self.et
    def getDataType(self): return self.dt


def var(name, base, dt=None, kids=()):
    nid = base + name if base.endswith("=") else base + "." + name
    if name.startswith("["):
        nid = base + name
    return (El(name, nid, "datavariable", dt), [(lambda b: k(b)) for k in kids], nid)


OPC = {}


def add(parent, name, dt=None, kids=None):
    """kids: list of (name, dt, kids)."""
    sep = "" if parent.endswith("=") or name.startswith("[") else "."
    nid = parent + sep + name
    OPC.setdefault(parent, []).append(El(name, nid, "datavariable", dt))
    for k in kids or []:
        add(nid, *k)
    return nid


ROOT = "ns=2;s="
OPC[""] = [El("Server", "i=2253", "object"), El("M580", ROOT, "folder")]
intlk = [("Status", "Int16"), ("Used", None, [("[0]", "Boolean"), ("[1]", "Boolean")])]
valve = [("Auto", "Boolean"), ("CMD", "Boolean"), ("Permissive", "Boolean"), ("Intlk", None, intlk)]
add(ROOT, "AV001", None, valve)
add(ROOT, "AV002", None, valve)
add(ROOT, "PT001", None, [("PV", "Float"), ("HiAlm", "Boolean")])
add(ROOT, "Stations", None, [("[1]", None, [("Weight", "Float")]), ("[2]", None, [("Weight", "Float")])])
add(ROOT, "Pump1", None, [("Run", "Boolean"), ("Speed", "Float"), ("Hours", "UInt32")])
add(ROOT, "Temp", "Float")


class Cfg(dict):
    pass


EXISTING = {
    "name": "DDT_Valve", "tagType": "UdtType",
    "parameters": {"InstancePath": {"dataType": "String", "value": ""}},
    "tags": [
        {"name": "Auto", "tagType": "AtomicTag", "valueSource": "opc", "dataType": "Boolean",
         "opcServer": {"bindType": "parameter", "binding": "{OPCServer}"},
         "opcItemPath": {"bindType": "parameter", "binding": "ns=2;s={InstancePath}.Auto"}},
        {"name": "OldMember", "tagType": "AtomicTag", "valueSource": "memory", "dataType": "Int4"},
    ]}
INSTANCE = {"name": "AV001", "tagType": "UdtInstance", "typeId": "Plant/DDT_Valve",
            "parameters": {"InstancePath": {"dataType": "String", "value": "AV001"}}}
WRITES = []


class Opc(object):
    def browseServer(self, server, nodeId):
        assert server == "M580_NUA"
        return OPC.get(nodeId, [])


class Tag(object):
    def browse(self, path, filter=None):
        if filter and filter.get("tagType") == "UdtInstance":
            return [{"fullPath": "[EFC]RGTCR/Valves/AV001"}]
        if path == "[EFC]_types_":
            return [{"name": "Plant", "tagType": "Folder"}]
        if path == "[EFC]_types_/Plant":
            return [{"name": "DDT_Valve", "tagType": "UdtType"}]
        return []

    def getConfiguration(self, path, recursive):
        return {"[EFC]_types_/Plant/DDT_Valve": [EXISTING], "[EFC]RGTCR/Valves/AV001": [INSTANCE]}[path]

    def configure(self, basePath, tags, policy):
        WRITES.append((basePath, tags, policy))
        return ["Good"] * len(tags)


class Log(object):
    def info(self, m): pass
    def warn(self, m): pass


class System(object):
    opc, tag = Opc(), Tag()


ddtsync.system = System()


def find(tags, name):
    return [t for t in tags if t["name"] == name][0]


def main():
    kw = dict(opcServer="M580_NUA", provider="EFC", rootNode="", typesFolder="PLC",
              typeNames={"PT001": "DDT_PV", "re:^Stations$": "DDT_Station",
                         "DDT_Valve.Intlk": "DDT_Intlk"}, logger=Log())
    r = ddtsync.run(dryRun=True, **kw)
    print(r["text"])
    assert WRITES == [], "dry run wrote"
    assert r["instances"] == 6, r["instances"]          # AV001, AV002, PT001, Stations[1..2], Pump1
    assert "Pump1" in r["unresolved"]

    r = ddtsync.run(dryRun=False, **kw)
    print(json.dumps(WRITES, indent=1)[:3000])
    by = {}
    for base, tags, pol in WRITES:
        assert pol == "i"
        for t in tags:
            by[(base, t["name"])] = t
    order = [t["name"] for _, tags, _ in WRITES for t in tags]
    # nested type created before the UDT that uses it
    assert order.index("DDT_Intlk") < order.index("Intlk"), order
    # existing UDT: only CMD, Permissive, Intlk added, with the UDT's own path pattern
    vb = "[EFC]_types_/Plant/DDT_Valve"
    added = sorted(n for (b, n) in by if b == vb)
    assert added == ["CMD", "Intlk", "Permissive"], added
    assert by[(vb, "CMD")]["opcItemPath"]["binding"] == "ns=2;s={InstancePath}.CMD"
    assert by[(vb, "CMD")]["opcServer"]["binding"] == "{OPCServer}"
    il = by[(vb, "Intlk")]
    assert il["tagType"] == "UdtInstance" and il["typeId"] == "PLC/DDT_Intlk", il
    assert il["parameters"]["BasePath"]["value"]["binding"] == "ns=2;s={InstancePath}.Intlk"
    # new UDTs
    di = by[("[EFC]_types_/PLC", "DDT_Intlk")]
    used = find(di["tags"], "Used")
    assert used["tagType"] == "Folder" and [t["name"] for t in used["tags"]] == ["_0", "_1"]
    assert find(used["tags"], "_1")["opcItemPath"]["binding"] == "{BasePath}.Used[1]"
    st = by[("[EFC]_types_/PLC", "DDT_Station")]
    assert find(st["tags"], "Weight")["opcItemPath"]["binding"] == "{BasePath}.Weight"
    assert find(st["tags"], "Weight")["dataType"] == "Float4"
    pv = by[("[EFC]_types_/PLC", "DDT_PV")]
    assert set(pv["parameters"]) == {"BasePath", "OPCServer"}
    assert not any(n == "DDT_Valve" for (_, n) in by), "existing UDT must not be rewritten"
    print("\nOK")


if __name__ == "__main__":
    main()
