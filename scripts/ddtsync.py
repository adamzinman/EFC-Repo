"""ddtsync: pull the DDTs out of a Modicon M580 through its BMENUA0100 (NUA) OPC UA
card and create or extend the matching Ignition UDT definitions.

Store this as a gateway Project Library script (e.g. Project Library -> ddtsync)
and run it from a Gateway Message Handler, a gateway timer, or the Script Console:

    report = ddtsync.run(
        opcServer="M580_NUA",            # OPC UA connection name (Config -> OPC Client Connections)
        provider="EFC",                  # tag provider that holds the UDTs
        rootNode="ns=2;s=",              # node that holds the PLC variables (copy it from the OPC browser)
        typesFolder="PLC",               # where NEW UDTs are created, under [EFC]_types_/
        dryRun=True,                     # True = report only. Set False to write.
    )
    print report["text"]

Rules (what the request asked for):
  - DDT has no UDT yet          -> a new UDT is created with every member, OPC-bound
                                   through the {BasePath} and {OPCServer} parameters.
  - UDT already exists          -> only members missing from the UDT are added.
  - member already in the UDT   -> ignored (never changed, even if its type differs).
  - UDT member no longer in PLC -> ignored (never deleted).

Where DDT names come from. Ignition's OPC browse returns variables, not OPC UA type
definitions, so the layout of each DDT is read from its instances and the type
NAME is resolved, in this order, from:
  1. typeNames      {"AV001": "DDT_Valve", "re:^AV\\d+$": "DDT_Valve", "DDT_Valve.Intlk": "DDT_Intlk"}
  2. variablesExport a Control Expert export on the gateway (.XEF / .ZEF / .XSY); its
                     <variables name=.. typeName=..> and <DDTSource> blocks give every name.
  3. scanInstances  existing UDT instances in the provider whose parameter holds the
                     PLC variable name or node id (so already-mapped DDTs need nothing).
  4. structure      an unnamed instance whose member layout is identical to a named one.
Anything still unnamed is listed in the report (or auto-named with unresolved="auto").

Written for Ignition 8.1 Jython 2.7 (also 8.3). No third-party imports.
"""
import re

LOGGER_NAME = "DDTSync"

try:
    basestring
except NameError:  # lets the offline tests run under Python 3
    basestring = str
try:
    from java.lang import Throwable   # Jython: Java exceptions are not Python Exceptions
    _ERRORS = (Exception, Throwable)
except ImportError:
    _ERRORS = (Exception,)

# Ignition atomic data types, keyed by upper case.
_IGN_TYPES = dict((t.upper(), t) for t in (
    "Int1 Int2 Int4 Int8 Float4 Float8 Boolean String DateTime Text Document ByteArray "
    "Int1Array Int2Array Int4Array Int8Array Float4Array Float8Array BooleanArray "
    "StringArray DateTimeArray").split())
# OPC UA built-in type names and Control Expert elementary types.
_ALIASES = {
    "BOOLEAN": "Boolean", "BOOL": "Boolean", "EBOOL": "Boolean",
    "SBYTE": "Int1", "BYTE": "Int2", "INT16": "Int2", "INT": "Int2", "UINT16": "Int4",
    "UINT": "Int4", "WORD": "Int4", "INT32": "Int4", "DINT": "Int4", "UINT32": "Int8",
    "UDINT": "Int8", "DWORD": "Int8", "INT64": "Int8", "UINT64": "Int8", "LINT": "Int8",
    "FLOAT": "Float4", "REAL": "Float4", "DOUBLE": "Float8", "LREAL": "Float8",
    "STRING": "String", "LOCALIZEDTEXT": "String", "DATETIME": "DateTime",
    "BYTESTRING": "ByteArray", "TIME": "Int4", "DATE": "DateTime", "DT": "DateTime",
    "TOD": "Int4", "STRUCTURE": "Document", "EXTENSIONOBJECT": "Document",
}
_SKIP_ELEMENTS = ("METHOD", "PROPERTY")
_CONTAINER_ELEMENTS = ("FOLDER", "SERVER", "DEVICE", "VIEW")
# Standard OPC UA nodes at the server root that never hold PLC variables.
_ROOT_SKIP = ("Server", "Types", "Views", "Aliases", "Locations")
_INDEX_RE = re.compile(r"\[(-?\d+)\]$")


# --------------------------------------------------------------------------- entry points

def run(opcServer, provider="default", rootNode="", typesFolder="PLC",
        pathParam="BasePath", serverParam="OPCServer", typeNames=None,
        variablesExport=None, scanInstances=True, instanceFolder="",
        include=None, exclude=None, maxDepth=6, maxStructDepth=12,
        nestedAsUdt=True, unresolved="report", autoPrefix="DDT_",
        elementName="_{index}", fallbackDataType="Int4", dryRun=True, logger=None):
    """Browse the PLC, work out its DDTs and create/extend the UDTs. Returns a report dict
    with "created", "extended", "unchanged", "skipped", "unresolved", "warnings" and "text"."""
    s = _Sync(locals())
    try:
        s.go()
    except _ERRORS as e:  # report instead of dying silently in a gateway thread
        s.warn("Aborted: %s" % e)
        raise
    finally:
        s.finish()
    return s.report


def runAsync(**kwargs):
    """Same as run() on a background thread; the report goes to the gateway log (DDTSync)."""
    from functools import partial
    system.util.invokeAsynchronous(partial(run, **kwargs))


# --------------------------------------------------------------------------- PLC model

class Node(object):
    """One PLC variable or member. kind: atomic | struct | array."""
    __slots__ = ("name", "nodeId", "kind", "dataType", "children", "template", "elements")

    def __init__(self, name, nodeId):
        self.name, self.nodeId = name, nodeId
        self.kind, self.dataType = "atomic", None
        self.children, self.template, self.elements = [], None, []

    def sig(self):
        """Layout signature (member names and types, not the variable's own name)."""
        if self.kind == "atomic":
            return ("A", self.dataType)
        if self.kind == "array":
            return ("R", len(self.elements), self.template.sig())
        return ("S", tuple(sorted((c.name.lower(), c.sig()) for c in self.children)))


def _call(el, *names):
    for n in names:
        f = getattr(el, n, None)
        if f is not None:
            try:
                return f()
            except _ERRORS:
                pass
    return None


def _node_id(el):
    v = _call(el, "getNodeId")
    if v is None:
        sid = _call(el, "getServerNodeId")
        v = _call(sid, "getNodeId") if sid is not None else None
        if v is None:
            v = sid
    return "" if v is None else str(v)


def _etype(el):
    return str(_call(el, "getElementType") or "").upper()


def _map_dt(raw):
    if raw is None:
        return None
    t = str(raw).strip()
    t = t.rsplit(".", 1)[-1].split(":")[-1].upper()
    if t.endswith("[]"):
        base = _ALIASES.get(t[:-2]) or _IGN_TYPES.get(t[:-2])
        return _IGN_TYPES.get((base or "").upper() + "ARRAY")
    return _IGN_TYPES.get(t) or _ALIASES.get(t)


# --------------------------------------------------------------------------- sync

class _Sync(object):

    def __init__(self, cfg):
        self.c = cfg
        self.log = cfg["logger"] or system.util.getLogger(LOGGER_NAME)
        self.prefix = "[%s]" % cfg["provider"]
        self.report = dict(created=[], extended={}, unchanged=[], skipped={},
                           unresolved={}, instances=0, warnings=[], dryRun=cfg["dryRun"])
        self.inc = re.compile(cfg["include"]) if cfg["include"] else None
        self.exc = re.compile(cfg["exclude"]) if cfg["exclude"] else None
        names = cfg["typeNames"] or {}
        self.exactNames = dict((k.lower(), v) for k, v in names.items() if not k.startswith("re:"))
        self.reNames = [(re.compile(k[3:]), v) for k, v in sorted(names.items()) if k.startswith("re:")]
        self.varTypes, self.ddtMembers = {}, {}
        self.types = {}         # lower name -> {"name", "nodes": [Node], "sig"}
        self.nested = {}        # (lower type, member path) -> nested type name or None
        self.existing = {}      # lower name -> path under _types_
        self.bindings = {}      # lower name -> binding info

    def warn(self, msg):
        self.report["warnings"].append(msg)
        self.log.warn(msg)

    # ---- 1. browse ------------------------------------------------------------------

    def browse(self, nodeId):
        try:
            return list(system.opc.browseServer(self.c["opcServer"], nodeId) or [])
        except _ERRORS as e:
            self.warn("Browse failed at '%s': %s" % (nodeId, e))
            return []

    def instances(self):
        found = []

        def walk(nodeId, depth):
            for el in self.browse(nodeId):
                et, name = _etype(el), str(_call(el, "getDisplayName") or "")
                if et in _SKIP_ELEMENTS or (depth == 0 and not self.c["rootNode"] and name in _ROOT_SKIP):
                    continue
                if et in _CONTAINER_ELEMENTS:
                    if depth < self.c["maxDepth"]:
                        walk(_node_id(el), depth + 1)
                    continue
                if (self.inc and not self.inc.search(name)) or (self.exc and self.exc.search(name)):
                    continue
                node = self.read(el, 0)
                if node.kind == "struct":
                    found.append(node)
                elif node.kind == "array" and node.template.kind == "struct":
                    # ARRAY[..] OF DDT at the top: each element is an instance of the DDT.
                    for idx, nid in node.elements:
                        e = _rebase(node.template, node.template.nodeId, nid)
                        e.name = "%s[%s]" % (node.name, idx)
                        e.template = node      # remembers the array for name lookups
                        found.append(e)
        walk(self.c["rootNode"], 0)
        return found

    def read(self, el, depth):
        node = Node(str(_call(el, "getDisplayName") or ""), _node_id(el))
        et = _etype(el)
        dt = _map_dt(_call(el, "getDataType", "getDatatype"))
        kids = []
        if (et in ("OBJECT",) + _CONTAINER_ELEMENTS or dt in (None, "Document")) \
                and depth < self.c["maxStructDepth"]:
            kids = [k for k in self.browse(node.nodeId) if _etype(k) not in _SKIP_ELEMENTS]
        if not kids:
            node.dataType = dt or self.c["fallbackDataType"]
            if dt is None:
                self.warn("No data type for %s; using %s" % (node.nodeId, node.dataType))
            return node
        idx = [_INDEX_RE.search(str(_call(k, "getDisplayName") or "")) for k in kids]
        if all(idx):
            # Array exposed element by element. Elements share a layout, so read one.
            node.kind = "array"
            node.template = self.read(kids[0], depth + 1)
            node.elements = [(m.group(1), _node_id(k)) for m, k in zip(idx, kids)]
            return node
        node.kind = "struct"
        node.children = [self.read(k, depth + 1) for k in kids]
        return node

    # ---- 2. names ---------------------------------------------------------------------

    def load_export(self):
        path = self.c["variablesExport"]
        if not path:
            return
        text = _read_export(path)
        blocks = re.compile(r"<(DDTSource|FBSource)\b([^>]*)>(.*?)</\1>", re.S)
        for m in blocks.finditer(text):
            if m.group(1) != "DDTSource":
                continue
            owner = _attrs(m.group(2)).get("DDTName", "")
            for v in re.finditer(r"<variables\b([^>]*)>", m.group(3)):
                a = _attrs(v.group(1))
                if "name" in a and "typeName" in a:
                    self.ddtMembers[(owner.lower(), a["name"].lower())] = _elem_type(a["typeName"])
        for v in re.finditer(r"<variables\b([^>]*)>", blocks.sub("", text)):
            a = _attrs(v.group(1))
            if "name" in a and "typeName" in a:
                self.varTypes[a["name"].lower()] = _elem_type(a["typeName"])
        self.log.info("Export %s: %d variables, %d DDT members" % (path, len(self.varTypes), len(self.ddtMembers)))

    def instance_params(self):
        """Map PLC variable name/node id -> UDT name from the provider's existing instances."""
        out = {}
        if not self.c["scanInstances"]:
            return out
        base = self.prefix + self.c["instanceFolder"]
        try:
            res = system.tag.browse(base, {"tagType": "UdtInstance", "recursive": True})
            rows = res.getResults() if hasattr(res, "getResults") else res
        except _ERRORS as e:
            self.warn("Instance scan of %s failed: %s" % (base, e))
            return out
        for r in rows:
            path = str(_get(r, "fullPath"))
            if "_types_" in path:
                continue
            try:
                cfg = system.tag.getConfiguration(path, False)[0]
            except _ERRORS:
                continue
            typeId = str(_get(cfg, "typeId") or "")
            params = _get(cfg, "parameters") or {}
            for k in list(params.keys()):
                v = _param_value(params[k])
                if isinstance(v, basestring) and v.strip() and typeId:
                    out.setdefault(v.strip().lower(), typeId.split("/")[-1])
        return out

    def name_for(self, node, byParam):
        keys = [node.name]
        if node.template is not None:          # element of a top-level array of DDTs
            keys.append(node.template.name)
        for k in keys:
            if k.lower() in self.exactNames:
                return self.exactNames[k.lower()]
        for k in keys:
            for rx, v in self.reNames:
                if rx.search(k):
                    return v
        for k in keys:
            if k.lower() in self.varTypes:
                return self.varTypes[k.lower()]
        for k in [node.nodeId, node.nodeId.split(";s=")[-1]] + keys:
            if k.lower() in byParam:
                return byParam[k.lower()]
        return None

    def add_type(self, name, node):
        t = self.types.setdefault(name.lower(), {"name": name, "nodes": [], "sig": node.sig()})
        if t["sig"] != node.sig() and not any(n.sig() == node.sig() for n in t["nodes"]):
            self.warn("%s has a different layout from other %s instances; members are merged"
                      % (node.name, name))
        t["nodes"].append(node)

    def resolve(self, found):
        byParam = self.instance_params()
        pending = []
        for n in found:
            name = self.name_for(n, byParam)
            if name:
                self.add_type(name, n)
            else:
                pending.append(n)
        sigs = {}
        for t in self.types.values():
            for n in t["nodes"]:
                sigs.setdefault(n.sig(), set()).add(t["name"])
        groups = {}
        for n in pending:
            match = sigs.get(n.sig(), set())
            if len(match) == 1:
                self.add_type(list(match)[0], n)
            else:
                groups.setdefault(n.sig(), []).append(n)
        for nodes in groups.values():
            label = nodes[0].name
            if self.c["unresolved"] == "auto":
                name = self.c["autoPrefix"] + re.sub(r"\W", "_", label)
                self.warn("No DDT name for %s (+%d same layout); auto-named %s"
                          % (label, len(nodes) - 1, name))
                for n in nodes:
                    self.add_type(name, n)
            else:
                self.report["unresolved"][label] = [n.name for n in nodes]
        # Nested DDTs: walk every type's layout and name its struct members.
        queue = list(self.types.keys())
        while queue:
            key = queue.pop(0)
            t = self.types[key]
            for node in t["nodes"][:1]:
                self._nested(t["name"], node.children, "", sigs, queue)

    def _nested(self, owner, children, path, sigs, queue):
        for c in children:
            rel = (path + "." if path else "") + c.name
            target = c.template if c.kind == "array" else c
            if target is None or target.kind != "struct":
                continue
            name = self.exactNames.get((owner + "." + rel).lower())
            if not name and "." not in rel:
                name = self.ddtMembers.get((owner.lower(), c.name.lower()))
            if not name:
                match = sigs.get(target.sig(), set())
                name = list(match)[0] if len(match) == 1 else None
            if name and name.lower() not in self.types:
                elem = Node(target.name, target.nodeId)
                elem.kind, elem.children = "struct", target.children
                self.add_type(name, elem)
                sigs.setdefault(target.sig(), set()).add(name)
                queue.append(name.lower())
            self.nested[(owner.lower(), rel.lower())] = name if self.c["nestedAsUdt"] else None
            if not name or not self.c["nestedAsUdt"]:
                self._nested(owner, target.children, rel, sigs, queue)

    # ---- 3. existing UDTs -------------------------------------------------------------

    def load_existing(self):
        root = self.prefix + "_types_"

        def walk(path, rel):
            try:
                res = system.tag.browse(path)
                rows = res.getResults() if hasattr(res, "getResults") else res
            except _ERRORS as e:
                self.warn("Browse of %s failed: %s" % (path, e))
                return
            for r in rows:
                name, tt = str(_get(r, "name")), str(_get(r, "tagType"))
                sub = (rel + "/" if rel else "") + name
                if tt == "UdtType":
                    self.existing.setdefault(name.lower(), sub)
                elif tt == "Folder":
                    walk(path + "/" + name, sub)
        walk(root, "")

    def binding_new(self):
        return {"prefix": "{%s}" % self.c["pathParam"], "param": self.c["pathParam"],
                "server": _bind("{%s}" % self.c["serverParam"]), "serverParam": self.c["serverParam"]}

    def binding_existing(self, key, cfg, rep):
        """Learn how an existing UDT builds its OPC paths from one of its OPC members."""
        suffixes = {}
        _suffix_map(rep, rep.nodeId, "", suffixes)
        found = {}

        def walk(tags, rel):
            for m in tags or []:
                name, tt = str(_get(m, "name")), str(_get(m, "tagType"))
                sub = (rel + "/" if rel else "") + name
                if tt == "Folder":
                    walk(_get(m, "tags"), sub)
                elif tt == "AtomicTag" and "prefix" not in found:
                    path = _binding_text(_get(m, "opcItemPath"))
                    suf = suffixes.get(sub.lower())
                    if path and suf and path.endswith(suf) and "{" in path[:len(path) - len(suf)]:
                        found["prefix"] = path[:len(path) - len(suf)]
                        found["server"] = _server_value(_get(m, "opcServer"))
        walk(_get(cfg, "tags"), "")
        params = _get(cfg, "parameters") or {}
        if "prefix" not in found:
            if self.c["pathParam"] in list(params.keys()):
                found["prefix"] = "{%s}" % self.c["pathParam"]
            else:
                return None
        if found.get("server") is None:
            found["server"] = (_bind("{%s}" % self.c["serverParam"])
                               if self.c["serverParam"] in list(params.keys()) else self.c["opcServer"])
        m = re.match(r"^\{(\w+)\}$", found["prefix"])
        found["param"] = m.group(1) if m else None
        sb = _binding_text(found["server"]) or ""
        m = re.match(r"^\{(\w+)\}$", sb) if isinstance(found["server"], dict) else None
        found["serverParam"] = m.group(1) if m else None
        return found

    # ---- 4. build members -------------------------------------------------------------

    def members(self, owner, children, nodeBase, relBase, b, path=""):
        out = []
        for c in children:
            rel = (path + "." if path else "") + c.name
            if not c.nodeId.startswith(nodeBase):
                raise ValueError("node id %s does not start with %s, so it can't be made "
                                 "relative to the instance" % (c.nodeId, nodeBase))
            suffix = relBase + c.nodeId[len(nodeBase):]
            if c.kind == "atomic":
                out.append(self.atomic(c.name, c.dataType, suffix, b))
            elif c.kind == "struct":
                out.append(self.structure(owner, rel, c.name, c, suffix, b))
            else:
                elems = []
                for idx, nid in c.elements:
                    if not nid.startswith(nodeBase):
                        raise ValueError("node id %s does not start with %s" % (nid, nodeBase))
                    esuf = relBase + nid[len(nodeBase):]
                    ename = self.c["elementName"].format(index=idx, name=c.name)
                    if c.template.kind == "atomic":
                        elems.append(self.atomic(ename, c.template.dataType, esuf, b))
                    else:
                        elems.append(self.structure(owner, rel, ename, c.template, esuf, b))
                out.append({"name": c.name, "tagType": "Folder", "tags": elems})
        return out

    def atomic(self, name, dataType, suffix, b):
        return {"name": name, "tagType": "AtomicTag", "valueSource": "opc", "dataType": dataType,
                "opcServer": b["server"], "opcItemPath": _bind(b["prefix"] + suffix)}

    def structure(self, owner, rel, name, node, suffix, b):
        nested = self.nested.get((owner.lower(), rel.lower()))
        nb = self.bindings.get(nested.lower()) if nested else None
        if nb and nb.get("param"):
            params = {nb["param"]: {"dataType": "String", "value": _bind(b["prefix"] + suffix)}}
            if nb.get("serverParam"):
                params[nb["serverParam"]] = {"dataType": "String", "value": b["server"]}
            return {"name": name, "tagType": "UdtInstance", "typeId": self.type_id(nested),
                    "parameters": params}
        return {"name": name, "tagType": "Folder",
                "tags": self.members(owner, node.children, node.nodeId, suffix, b, rel)}

    def type_id(self, name):
        return self.existing.get(name.lower()) or "/".join(
            p for p in (self.c["typesFolder"].strip("/"), name) if p)

    # ---- 5. write ---------------------------------------------------------------------

    def configure(self, basePath, tags):
        if self.c["dryRun"]:
            return True
        res = system.tag.configure(basePath, tags, "i")    # i = ignore existing, never overwrite
        bad = [str(q) for q in res or [] if not _good(q)]
        if bad:
            self.warn("configure %s returned %s" % (basePath, ", ".join(bad)))
        return not bad

    def go(self):
        self.load_export()
        found = self.instances()
        self.report["instances"] = len(found)
        self.log.info("Found %d DDT instances under '%s'" % (len(found), self.c["rootNode"]))
        self.resolve(found)
        self.load_existing()
        for key, t in self.types.items():
            if key in self.existing:
                cfg = system.tag.getConfiguration(self.prefix + "_types_/" + self.existing[key], True)[0]
                t["cfg"] = cfg
                b = self.binding_existing(key, cfg, self.merged(t))
                if b is None:
                    self.report["skipped"][t["name"]] = ("can't tell how the existing UDT builds OPC "
                                                         "paths (no parameter-bound OPC member and no "
                                                         "{%s} parameter)" % self.c["pathParam"])
                    continue
                self.bindings[key] = b
            else:
                self.bindings[key] = self.binding_new()
        for key in self.order():
            if key in self.bindings:
                self.sync(self.types[key])

    def merged(self, t):
        """Representative node: first instance plus any members only other instances have."""
        rep = t["nodes"][0]
        if len(t["nodes"]) == 1:
            return rep
        out = Node(rep.name, rep.nodeId)
        out.kind, out.children = "struct", list(rep.children)
        have = set(c.name.lower() for c in rep.children)
        for n in t["nodes"][1:]:
            for c in n.children:
                if c.name.lower() not in have and c.nodeId.startswith(n.nodeId):
                    cc = _rebase(c, n.nodeId, rep.nodeId)
                    out.children.append(cc)
                    have.add(c.name.lower())
        return out

    def order(self):
        """Nested types first, so a parent's UdtInstance member never points at a missing type."""
        done, out = set(), []

        def visit(key, stack):
            if key in done or key in stack:
                return
            for (owner, _), child in self.nested.items():
                if owner == key and child and child.lower() in self.types:
                    visit(child.lower(), stack | set([key]))
            done.add(key)
            out.append(key)
        for key in sorted(self.types):
            visit(key, set())
        return out

    def sync(self, t):
        key, name = t["name"].lower(), t["name"]
        rep, b = self.merged(t), self.bindings[key]
        try:
            members = self.members(name, rep.children, rep.nodeId, "", b)
        except ValueError as e:
            self.report["skipped"][name] = str(e)
            del self.bindings[key]
            return
        if "cfg" not in t:
            udt = {"name": name, "tagType": "UdtType", "tags": members, "parameters": {
                self.c["pathParam"]: {"dataType": "String", "value": ""},
                self.c["serverParam"]: {"dataType": "String", "value": self.c["opcServer"]}}}
            base = self.prefix + "_types_" + ("/" + self.c["typesFolder"].strip("/")
                                              if self.c["typesFolder"].strip("/") else "")
            if self.configure(base, [udt]):
                self.existing[key] = self.type_id(name)
                self.report["created"].append("%s (%d members)" % (name, _count(members)))
            return
        adds = []
        _diff(members, _get(t["cfg"], "tags"), "", adds)
        if not adds:
            self.report["unchanged"].append(name)
            return
        root = self.prefix + "_types_/" + self.existing[key]
        groups = {}
        for parent, m in adds:
            groups.setdefault(parent, []).append(m)
        added = []
        for parent in sorted(groups):
            if self.configure(root + ("/" + parent if parent else ""), groups[parent]):
                added += [(parent + "/" if parent else "") + m["name"] for m in groups[parent]]
        if added:
            self.report["extended"][name] = added

    def finish(self):
        r = self.report
        lines = ["DDT -> UDT sync %s (%s, provider %s)" % (
            "DRY RUN, nothing written" if r["dryRun"] else "applied", self.c["opcServer"],
            self.c["provider"]), "DDT instances found: %d" % r["instances"]]
        for name in r["created"]:
            lines.append("  NEW       %s" % name)
        for name in sorted(r["extended"]):
            lines.append("  EXTENDED  %s: + %s" % (name, ", ".join(r["extended"][name])))
        for name in sorted(r["unchanged"]):
            lines.append("  UP TO DATE %s" % name)
        for name in sorted(r["skipped"]):
            lines.append("  SKIPPED   %s: %s" % (name, r["skipped"][name]))
        for label in sorted(r["unresolved"]):
            lines.append("  NO NAME   layout of %s, used by: %s  -> add it to typeNames"
                         % (label, ", ".join(r["unresolved"][label][:10])))
        for w in r["warnings"]:
            lines.append("  WARNING   %s" % w)
        r["text"] = "\n".join(lines)
        self.log.info(r["text"])


# --------------------------------------------------------------------------- helpers

def _diff(new, existing, parent, adds):
    """Collect (parentPath, member) for members missing from the existing UDT. Existing
    members are never touched; folders that exist on both sides are compared inside."""
    have = {}
    for m in existing or []:
        have[str(_get(m, "name")).lower()] = m
    for m in new:
        cur = have.get(m["name"].lower())
        if cur is None:
            adds.append((parent, m))
        elif m["tagType"] == "Folder" and str(_get(cur, "tagType")) == "Folder":
            _diff(m["tags"], _get(cur, "tags"), (parent + "/" if parent else "") + str(_get(cur, "name")), adds)


def _suffix_map(node, base, rel, out):
    for c in node.children:
        sub = (rel + "/" if rel else "") + c.name
        if c.kind == "atomic" and c.nodeId.startswith(base):
            out[sub.lower()] = c.nodeId[len(base):]
        elif c.kind == "struct":
            _suffix_map(c, base, sub, out)


def _rebase(node, old, new):
    n = Node(node.name, new + node.nodeId[len(old):])
    n.kind, n.dataType = node.kind, node.dataType
    n.children = [_rebase(c, old, new) for c in node.children if c.nodeId.startswith(old)]
    if node.template is not None:
        n.template = _rebase(node.template, old, new) if node.template.nodeId.startswith(old) else node.template
    n.elements = [(i, new + e[len(old):] if e.startswith(old) else e) for i, e in node.elements]
    return n


def _count(members):
    return sum(_count(m["tags"]) if m["tagType"] == "Folder" else 1 for m in members)


def _bind(text):
    return {"bindType": "parameter", "binding": text}


def _get(obj, key):
    if obj is None:
        return None
    try:
        return obj[key]
    except _ERRORS:
        try:
            return obj.get(key)
        except _ERRORS:
            return None


def _binding_text(v):
    if v is None:
        return None
    if hasattr(v, "getBinding"):
        return str(v.getBinding())
    b = _get(v, "binding") if not isinstance(v, basestring) else None
    return str(b) if b is not None else str(v)


def _server_value(v):
    if v is None:
        return None
    if isinstance(v, basestring):
        return v
    text = _binding_text(v)
    return _bind(text) if "{" in text else text


def _param_value(v):
    if v is None or isinstance(v, basestring):
        return v
    inner = _get(v, "value")
    if inner is not None:
        return _param_value(inner)
    val = _call(v, "getValue")
    return val if val is not None and val is not v else str(v)


def _good(q):
    for f in ("isGood", "isGoodOrUncertain"):
        g = getattr(q, f, None)
        if g is not None:
            return bool(g())
    return "good" in str(q).lower()


def _attrs(text):
    return dict(re.findall(r'(\w+)="([^"]*)"', text))


def _elem_type(typeName):
    m = re.match(r"(?i)^\s*ARRAY\s*\[.*?\]\s*OF\s+(\S+)", typeName)
    return m.group(1) if m else typeName.strip()


def _read_export(path):
    lower = path.lower()
    if lower.endswith(".zef") or lower.endswith(".zip"):
        import zipfile
        z = zipfile.ZipFile(path)
        try:
            for n in z.namelist():
                if n.lower().endswith((".xef", ".xml", ".xsy")):
                    return z.read(n).decode("utf-8", "replace")
        finally:
            z.close()
        raise ValueError("no .xef/.xml inside %s" % path)
    f = open(path, "rb")
    try:
        return f.read().decode("utf-8", "replace")
    finally:
        f.close()
