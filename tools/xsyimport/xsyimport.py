# -*- coding: utf-8 -*-
"""Control Expert V16.2 .XSY -> Ignition 8.1 tag planner.

Pure logic: no system.* calls, so the same file runs in Jython 2.7 (gateway
scripting project, as efc/xsyimport.py) and in CPython (tests).

    plan(xsy_bytes, line, tag_tree, types_tree, options) -> Plan

Nothing is written here. gateway.py applies a Plan with system.tag.configure.
Rules: docs/xsy-tag-import-strategy.md, shared interface contract v1.0.

Policy:
  * every HMI-flagged variable is imported (all tags shown on the HMI)
  * an existing UDT gets new members added; old members are never deleted, only reported
  * duplicates, tags no longer in the PLC and possible renames are reported, never changed
"""
import re
import xml.etree.ElementTree as ET

try:  # Jython 2.7 uses unicode; CPython 3 uses str
    STRING_TYPES = (basestring,)  # noqa: F821
except NameError:
    STRING_TYPES = (str,)

from library_types import LIBRARY_TYPES

VERSION = "1.1.0"
HMI_ATTR = "IsVariableHMI"
HMI_TRUE = ("-1", "1", "TRUE")
PARAM_PREFIX = "OPC Prefix"
PARAM_SERVER = "OPC Server"
PARAM_TAG = "Tag"
DEFAULT_PREFIX = "ns=2;s=0:"
IMPORTED = "imported"
ITEM_PATH = "{OPC Prefix}{Tag}.{TagName}"

# Control Expert elementary type -> Ignition dataType. The first block is contract v1.0.
# BYTE/SINT/USINT/LREAL/LINT follow tools/ddtsync; BYTE -> Int2 keeps unsigned 8-bit values.
ELEMENTARY = {
    "BOOL": "Boolean", "EBOOL": "Boolean",
    "INT": "Int2", "SINT": "Int1", "BYTE": "Int2", "USINT": "Int2",
    "UINT": "Int4", "WORD": "Int4", "DINT": "Int4", "LINT": "Int8",
    "UDINT": "Int8", "DWORD": "Int8",
    "REAL": "Float4", "LREAL": "Float8",
    "TIME": "Int4", "DT": "DateTime",
}
ARRAY_OF = {  # Ignition array dataType for each element dataType
    "Boolean": "BooleanArray", "Int1": "Int1Array", "Int2": "Int2Array", "Int4": "Int4Array",
    "Int8": "Int8Array", "Float4": "Float4Array", "Float8": "Float8Array", "String": "StringArray",
    "DateTime": "DateTimeArray",
}
LINE_RE = re.compile(r"^\d{3}$")
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
STRING_RE = re.compile(r"^STRING(\[\d+\])?$", re.I)
ARRAY_RE = re.compile(r"^ARRAY\s*\[\s*(-?\d+)\s*\.\.\s*(-?\d+)\s*\]\s*OF\s+(.+)$", re.I)

DEFAULTS = {
    "opcServer": None,          # required: the OPC UA connection name, asked at run time
    "prefix": DEFAULT_PREFIX,   # OPC item prefix for elementary tags and UDT members
    "syncDocumentation": True,  # a non-empty PLC comment overwrites Ignition Documentation; blank never does
    "typesFolder": None,        # UDT folder under _types_; defaults to the line number
    "library": None,            # library layouts; defaults to library_types.LIBRARY_TYPES
    "layouts": None,            # extra layout files (bytes) for types the export does not define
}


class ImportRefused(Exception):
    """Inputs that must not be imported at all (never a per-variable problem)."""


# --------------------------------------------------------------------------- XSY

class _Skip(Exception):
    """A type or variable that cannot be built. Raised, caught, and reported as a skip."""


class Model(object):
    def __init__(self):
        self.ddts = {}      # DDT name -> [(member, typeName, comment)]
        self.fbs = {}       # FB type name -> [(member, typeName, comment)] (inputs, outputs, public)
        self.hmi = []       # [(variable, typeName, comment)] for HMI-flagged top-level variables
        self.total = 0
        self.flagged = 0    # variables that carry the HMI attribute at all, any value
        self.from_layout = set()   # type names defined only by a layout file


def _comment(el):
    c = el.find("comment")
    return (c.text or "").strip() if c is not None and c.text else ""


def _members(el):
    if el is None:
        return []
    return [(v.get("name"), (v.get("typeName") or "").strip(), _comment(v))
            for v in el.findall("variables")]


def _definitions(root, model):
    for s in root.findall("DDTSource"):
        model.ddts[s.get("DDTName")] = _members(s.find("structure"))
    for f in root.findall("FBSource"):
        mem = []
        for sec in ("inputParameters", "outputParameters", "publicLocalVariables"):
            mem.extend(_members(f.find(sec)))
        model.fbs[f.get("nameOfFBType")] = mem


def parse(data):
    """Parse the export: type definitions plus the HMI-flagged variables. Refuses an export with no HMI flags."""
    root = ET.fromstring(data)
    if root.tag != "VariablesExchangeFile":
        raise ImportRefused("not a Control Expert variables export (root is %s)" % root.tag)
    m = Model()
    _definitions(root, m)
    db = root.find("dataBlock")
    for v in (db.findall("variables") if db is not None else []):
        m.total += 1
        attrs = [a for a in v.findall("attribute") if a.get("name") == HMI_ATTR]
        if attrs:
            m.flagged += 1
        if any((a.get("value") or "").strip().upper() in HMI_TRUE for a in attrs):
            m.hmi.append((v.get("name"), (v.get("typeName") or "").strip(), _comment(v)))
    if m.total and m.flagged == 0:
        raise ImportRefused("export has no %s attributes; re-export with attributes included. "
                            "Refusing to import every variable." % HMI_ATTR)
    return m


def _add_layouts(model, layouts):
    """Layout files (any Control Expert export or DDT exchange file) supply types the export lacks."""
    for data in layouts or []:
        root = ET.fromstring(data)
        extra = Model()
        _definitions(root, extra)
        for name, mem in list(extra.ddts.items()) + list(extra.fbs.items()):
            if name not in model.ddts and name not in model.fbs:
                (model.ddts if name in extra.ddts else model.fbs)[name] = mem
                model.from_layout.add(name)


def _layout_diff(name, exp, lib):
    """Differences between the export's layout for a type and the EFCLib v1 layout."""
    out = []
    ex = dict((m[0], m[1]) for m in exp)
    lb = dict((m[0], m[1]) for m in lib)
    for m in lib:
        if m[0] not in ex:
            out.append((name, "member %s in EFCLib v1, not in export" % m[0]))
        elif ex[m[0]].replace(" ", "") != m[1].replace(" ", ""):
            out.append((name, "member %s is %s in export, %s in EFCLib v1" % (m[0], ex[m[0]], m[1])))
    for m in exp:
        if m[0] not in lb:
            out.append((name, "member %s in export, not in EFCLib v1" % m[0]))
    return out


def _add_library(model, library):
    """EFCLib v1 layouts win over the export and any layout file. Returns the differences for the report."""
    diffs = []
    for name, entry in (library or {}).items():
        if entry.get("confidence") != "confirmed":
            continue
        lib = [(m[0], m[1], m[2]) for m in entry["members"]]
        exp = model.ddts.get(name) or model.fbs.get(name)
        if exp is not None and name not in model.from_layout:
            diffs.extend(_layout_diff(name, exp, lib))
        model.ddts[name] = lib
        model.fbs.pop(name, None)
        model.from_layout.discard(name)
    return diffs


# --------------------------------------------------------------------- type rules

_ARRAY_RE = re.compile(r"^ARRAY\s*\[(.+?)\]\s*OF\s+(.+)$", re.I)
_RANGE_RE = re.compile(r"^\s*(-?\d+)\s*\.\.\s*(-?\d+)\s*$")


def _elem(t):
    if STRING_RE.match(t):
        return "String"
    return ELEMENTARY.get(t.upper())


def _classify(tn, model):
    """-> ('elem', dataType) | ('array', (lo, hi, element type name)) | ('udt', type name). Raises _Skip.

    Multi-dimensional arrays are read as arrays of arrays: ARRAY[1..2,1..3] OF T -> ARRAY[1..2] OF ARRAY[1..3] OF T.
    """
    m = _ARRAY_RE.match(tn)
    if m:
        dims = [d.strip() for d in m.group(1).split(",")]
        ranges = []
        for d in dims:
            r = _RANGE_RE.match(d)
            if not r:
                raise _Skip("array %s: dimension %r not readable" % (tn, d))
            lo, hi = int(r.group(1)), int(r.group(2))
            if hi < lo:
                raise _Skip("array %s has an empty range" % tn)
            ranges.append((lo, hi))
        elem = m.group(2).strip()
        if len(dims) > 1:
            elem = "ARRAY[%s] OF %s" % (",".join(dims[1:]), elem)
        return "array", (ranges[0][0], ranges[0][1], elem)
    dt = _elem(tn)
    if dt:
        return "elem", dt
    if tn in model.ddts or tn in model.fbs:
        return "udt", tn
    raise _Skip("type %s is not elementary and not defined in the export, a layout file or EFCLib v1" % tn)


def _atomic(name, dt, comment, suffix):
    """Atomic member/tag binding. suffix is the path below the owning Tag (the member name for a plain member)."""
    binding = ITEM_PATH if suffix == name else "{OPC Prefix}{Tag}.%s" % suffix
    return {"name": name, "tagType": "AtomicTag", "valueSource": "opc", "dataType": dt,
            "opcServer": {"bindType": "parameter", "binding": "{OPC Server}"},
            "opcItemPath": {"bindType": "parameter", "binding": binding},
            "documentation": comment}


def _nested(name, type_id, comment, suffix):
    return {"name": name, "tagType": "UdtInstance", "typeId": type_id,
            "parameters": {
                PARAM_PREFIX: {"dataType": "String", "value": {"bindType": "parameter", "binding": "{OPC Prefix}"}},
                PARAM_SERVER: {"dataType": "String", "value": {"bindType": "parameter", "binding": "{OPC Server}"}},
                PARAM_TAG: {"dataType": "String", "value": {"bindType": "parameter", "binding": "{Tag}.%s" % suffix}}},
            "documentation": comment}


class _Types(object):
    """UDT definitions for every DDT/FB the import can reach. Built once per type, nested types first."""

    def __init__(self, model, folder, prefix):
        self.model = model
        self.folder = folder        # the _types_ folder, e.g. "058"
        self.prefix = prefix
        self.done = {}              # type name -> (udt json or None, reason or None)
        self.order = []             # successfully built names, nested types first

    def udt(self, name, stack=()):
        if name in self.done:
            return self.done[name]
        if name in stack:
            return None, "recursive type %s" % name
        members = self.model.ddts[name] if name in self.model.ddts else self.model.fbs[name]
        tags, problem = [], None
        for mname, tn, comment in members:
            if not NAME_RE.match(mname or ""):
                problem = "member %s has a name Ignition does not allow" % mname
                break
            try:
                tags.append(self.member(mname, tn, comment, mname, stack + (name,)))
            except _Skip as e:
                problem = "member %s: %s" % (mname, e)
                break
        if problem:
            res = (None, problem)
        else:
            res = ({"name": name, "tagType": "UdtType",
                    "parameters": {
                        PARAM_PREFIX: {"dataType": "String", "value": self.prefix},
                        PARAM_SERVER: {"dataType": "String", "value": ""},
                        PARAM_TAG: {"dataType": "String", "value": ""}},
                    "tags": tags}, None)
        self.done[name] = res
        if res[0] is not None and name not in self.order:
            self.order.append(name)
        return res

    def buildable(self, tn, stack=()):
        """(True, None) when a tag or member of this type can be built; otherwise (False, reason)."""
        try:
            kind, val = _classify(tn, self.model)
        except _Skip as e:
            return False, str(e)
        if kind == "elem":
            return True, None
        if kind == "array":
            lo, hi, et = val
            ek, ev = _classify(et, self.model) if not _ARRAY_RE.match(et) else ("array", None)
            if ek == "elem" and ev not in ARRAY_OF:
                return False, "array of %s is not mapped" % ev
            return self.buildable(et, stack)
        js, why = self.udt(val, stack)
        return js is not None, why

    def member(self, name, tn, comment, suffix, stack):
        """One UDT member (or one element of an array member). suffix is its path below the owning Tag."""
        kind, val = _classify(tn, self.model)
        if kind == "elem":
            return _atomic(name, val, comment, suffix)
        if kind == "array":
            lo, hi, et = val
            ek, ev = _classify(et, self.model) if not _ARRAY_RE.match(et) else ("array", None)
            if ek == "elem":
                if ev not in ARRAY_OF:
                    raise _Skip("array of %s is not mapped" % ev)
                return _atomic(name, ARRAY_OF[ev], comment, suffix)
            children = [self.member("_%d" % i, et, comment, "%s[%d]" % (suffix, i), stack)
                        for i in range(lo, hi + 1)]
            return {"name": name, "tagType": "Folder", "tags": children}
        sub, why = self.udt(val, stack)
        if sub is None:
            raise _Skip(why)
        return _nested(name, "%s/%s" % (self.folder, val), comment, suffix)


# ----------------------------------------------------------------- existing state

def _binding_text(v):
    return v if isinstance(v, STRING_TYPES) else None


def _pval(v):
    if isinstance(v, dict):
        v = v.get("value")
    return v if isinstance(v, STRING_TYPES) else None


def _plc_key(item):
    """Last segment of an OPC item path: 'nsu=...;s=0:PT101' and 'ns=2;s=0:PT101' -> 'PT101'."""
    m = re.search(r"([^:;=]+)$", item or "")
    return m.group(1) if m else None


def records(nodes, base):
    """Flatten a getConfiguration() tree under `base`. 'top' is False for anything inside a UDT instance."""
    out = []

    def walk(items, parent, in_udt):
        for n in items or []:
            name = n.get("name")
            if not name:
                continue
            path = parent + "/" + name
            tt = n.get("tagType")
            out.append({"path": path, "name": name, "tagType": tt, "typeId": n.get("typeId"),
                        "dataType": n.get("dataType"),
                        "opcItemPath": _binding_text(n.get("opcItemPath")),
                        "documentation": n.get("documentation") or "",
                        "params": n.get("parameters") or {}, "top": not in_udt})
            if tt in ("Folder", "UdtInstance"):
                walk(n.get("tags"), path, in_udt or tt == "UdtInstance")

    walk(nodes, base, False)
    return out


def types_index(nodes):
    """{UDT name: {member: {tagType, dataType, typeId}}} for the children of _types_/<folder>."""
    out = {}
    for n in nodes or []:
        if n.get("tagType") != "UdtType":
            continue
        out[n["name"]] = dict((m["name"], {"tagType": m.get("tagType"), "dataType": m.get("dataType"),
                                           "typeId": m.get("typeId")})
                              for m in (n.get("tags") or []) if m.get("name"))
    return out


def _last(path):
    return (path or "").rsplit("/", 1)[-1]


# ------------------------------------------------------------------------- plan

class Plan(object):
    def __init__(self):
        self.udt_create = []    # (types folder, udt json), nested types first
        self.udt_extend = []    # (type name, [member json]) new members added to an existing UDT
        self.udt_stale = []     # (type name, member) in Ignition, not in the PLC: kept and reported
        self.udt_diff = []      # (type name, member, message): reported, not changed
        self.udt_skipped = []   # (type name, reason)
        self.tag_create = []    # (folder, tag json)
        self.tag_update = []    # (full path, {property: value}) documentation only
        self.exists = []        # (variable or element, path): already in Ignition, nothing to do
        self.conflicts = []     # (variable, message): reported, not changed
        self.duplicates = []    # (PLC identity, [paths]): reported, not changed
        self.not_in_plc = []    # (PLC identity, path): kept, reported
        self.renames = []       # (old path, new name): possible rename, reported
        self.skipped = []       # (variable, reason)
        self.library = []       # (type, message): export layout differs from EFCLib v1; EFCLib used

    def counts(self):
        return {"udt_create": len(self.udt_create), "udt_extend": len(self.udt_extend),
                "udt_stale": len(self.udt_stale), "udt_diff": len(self.udt_diff),
                "udt_skipped": len(self.udt_skipped), "tag_create": len(self.tag_create),
                "tag_update": len(self.tag_update), "exists": len(self.exists),
                "conflicts": len(self.conflicts), "duplicates": len(self.duplicates),
                "not_in_plc": len(self.not_in_plc), "renames": len(self.renames),
                "library_diffs": len(self.library), "skipped": len(self.skipped)}

    def is_noop(self):
        return not (self.udt_create or self.udt_extend or self.tag_create or self.tag_update)


def plan(data, line, tag_tree, types_tree, options=None):
    """Plan an import of `data` (XSY bytes) into production line `line`.

    tag_tree    children of the provider folder <line> (getConfiguration(..., True))
    types_tree  children of _types_/<typesFolder> (defaults to the line)
    options     opcServer (required), prefix, syncDocumentation, typesFolder, library,
                layouts (list of bytes: extra Control Expert exports / DDT files that define types)
    """
    opts = dict(DEFAULTS)
    opts.update(options or {})
    if not LINE_RE.match(line or ""):
        raise ImportRefused("production line must be three digits, e.g. 058 (got %r)" % (line,))
    if not (opts["opcServer"] or "").strip():
        raise ImportRefused("OPC server name is required")
    tf = opts["typesFolder"] or line
    prefix = opts["prefix"]
    server = opts["opcServer"].strip()
    sync_doc = bool(opts["syncDocumentation"])

    model = parse(data)
    _add_layouts(model, opts["layouts"])
    lib_diffs = _add_library(model, LIBRARY_TYPES if opts["library"] is None else opts["library"])
    types = _Types(model, tf, prefix)
    existing_types = types_index(types_tree)
    recs = records(tag_tree, line)
    imported = "%s/%s" % (line, IMPORTED)
    inst, atoms, used = {}, {}, {}     # used: name directly under imported/ -> tagType
    by_identity = {}
    for r in recs:
        if not r["top"]:
            continue
        if r["path"] == "%s/%s" % (imported, r["name"]):
            used[r["name"]] = r["tagType"]
        if r["tagType"] == "UdtInstance":
            ident = _pval(r["params"].get(PARAM_TAG))
            if ident:
                inst.setdefault(ident, r)
                by_identity.setdefault(ident, []).append(r["path"])
        elif r["tagType"] == "AtomicTag" and r["opcItemPath"]:
            ident = _plc_key(r["opcItemPath"])
            if ident:
                atoms.setdefault(ident, r)
                by_identity.setdefault(ident, []).append(r["path"])

    p = Plan()
    p.library = lib_diffs
    wanted = set()             # PLC identities the export still exposes
    new_docs = []              # (name, tagType, type, documentation) of tags this run creates

    def atomic_here(name, expr, dt, comment, folder):
        wanted.add(expr)
        rec = atoms.get(expr)
        if rec is None and expr in inst:
            p.conflicts.append((expr, "UDT instance %s in Ignition, %s in PLC; not changed"
                                % (inst[expr]["typeId"], dt)))
            return
        if rec:
            p.exists.append((expr, rec["path"]))
            if rec["dataType"] and rec["dataType"] != dt:
                p.conflicts.append((expr, "dataType %s in Ignition, %s in PLC; not changed"
                                    % (rec["dataType"], dt)))
            if sync_doc and comment and rec["documentation"] != comment:
                p.tag_update.append((rec["path"], {"tagType": "AtomicTag", "documentation": comment}))
            return
        p.tag_create.append((folder, {
            "name": name, "tagType": "AtomicTag", "valueSource": "opc", "dataType": dt,
            "opcServer": server, "opcItemPath": prefix + expr, "documentation": comment}))
        new_docs.append((name, "AtomicTag", dt, comment))

    def instance_here(name, expr, type_name, comment, folder):
        wanted.add(expr)
        rec = inst.get(expr)
        if rec:
            p.exists.append((expr, rec["path"]))
            if _last(rec["typeId"]) != type_name:
                p.conflicts.append((expr, "type %s in Ignition, %s in PLC; not changed"
                                    % (rec["typeId"], type_name)))
            if sync_doc and comment and rec["documentation"] != comment:
                p.tag_update.append((rec["path"], {"tagType": "UdtInstance", "documentation": comment}))
            return
        p.tag_create.append((folder, {
            "name": name, "tagType": "UdtInstance", "typeId": "%s/%s" % (tf, type_name),
            "parameters": {PARAM_SERVER: {"dataType": "String", "value": server},
                           PARAM_TAG: {"dataType": "String", "value": expr}},
            "documentation": comment}))
        new_docs.append((name, "UdtInstance", type_name, comment))

    def place(name, tn, comment, expr, folder):
        """Place one variable (any type, any nesting) under folder. expr is its PLC path, e.g. Station[1][2]."""
        kind, val = _classify(tn, model)
        if kind == "elem":
            atomic_here(name, expr, val, comment, folder)
        elif kind == "array":
            lo, hi, et = val
            ek, ev = _classify(et, model) if not _ARRAY_RE.match(et) else ("array", None)
            if ek == "elem":
                atomic_here(name, expr, ARRAY_OF[ev], comment, folder)
            else:
                for i in range(lo, hi + 1):
                    place("_%d" % i, et, comment, "%s[%d]" % (expr, i), "%s/%s" % (folder, name))
        else:
            instance_here(name, expr, val, comment, folder)

    for vname, tn, comment in model.hmi:
        wanted.add(vname)            # still exposed by the PLC, even when skipped below
        if not NAME_RE.match(vname or ""):
            p.skipped.append((vname, "name is not allowed in Ignition"))
            continue
        ok, why = types.buildable(tn)
        if not ok:
            p.skipped.append((vname, why))
            continue
        matched = vname in atoms or vname in inst
        if not matched and vname in used and used[vname] != "Folder":
            p.skipped.append((vname, "name already used by another tag under %s" % line))
            continue
        place(vname, tn, comment, vname, imported)

    # UDT definitions: create missing types, add missing members, report the rest.
    for tname in types.order:
        js = types.done[tname][0]
        if tname not in existing_types:
            p.udt_create.append((tf, js))
            continue
        cur = existing_types[tname]
        missing = []
        for t in js["tags"]:
            have = cur.get(t["name"])
            if have is None:
                missing.append(t)
                continue
            if t["tagType"] == "AtomicTag" and have["dataType"] != t["dataType"]:
                p.udt_diff.append((tname, t["name"], "dataType %s in Ignition, %s in PLC; not changed"
                                   % (have["dataType"], t["dataType"])))
            if t["tagType"] == "UdtInstance" and _last(have["typeId"]) != _last(t["typeId"]):
                p.udt_diff.append((tname, t["name"], "type %s in Ignition, %s in PLC; not changed"
                                   % (_last(have["typeId"]), _last(t["typeId"]))))
        if missing:
            p.udt_extend.append((tname, missing))
        mine = set(t["name"] for t in js["tags"])
        for m in cur:
            if m not in mine:
                p.udt_stale.append((tname, m))

    for tname, (js, why) in types.done.items():
        if js is None:
            p.udt_skipped.append((tname, why))

    p.udt_create.sort(key=lambda item: types.order.index(item[1]["name"]))

    # Reports only: duplicates, tags the export no longer exposes, possible renames.
    for ident, paths in sorted(by_identity.items()):
        if len(paths) > 1:
            p.duplicates.append((ident, paths))
    for ident, rec in sorted(list(inst.items()) + list(atoms.items())):
        if ident not in wanted:
            p.not_in_plc.append((ident, rec["path"]))
    for ident, path in list(p.not_in_plc):
        rec = inst.get(ident) or atoms.get(ident)
        for name, ttype, dt, doc in new_docs:
            if doc and rec["documentation"] == doc and rec["tagType"] == ttype:
                p.renames.append((path, name))
                break
    return p


# ----------------------------------------------------------------------- report

def report_text(p, header):
    lines = list(header)

    def section(title, items, fmt):
        lines.append("")
        lines.append("%s (%d)" % (title, len(items)))
        for it in items:
            lines.append("  " + fmt(it))

    section("NEW UDT", p.udt_create,
            lambda it: "%s/%s  (%d members)" % (it[0], it[1]["name"], len(it[1]["tags"])))
    section("EXTENDED UDT (new members added)", p.udt_extend,
            lambda it: "%s: + %s" % (it[0], ", ".join(t["name"] for t in it[1])))
    section("NEW TAG", p.tag_create, lambda it: "%s/%s  (%s)" % (it[0], it[1]["name"], it[1]["tagType"]))
    section("DOCUMENTATION UPDATE", p.tag_update, lambda it: "%s" % it[0])
    section("UP TO DATE", p.exists, lambda it: "%s -> %s" % (it[0], it[1]))
    section("DUPLICATE (reported, not changed)", p.duplicates, lambda it: "%s: %s" % (it[0], ", ".join(it[1])))
    section("NOT IN PLC (kept, not deleted)", p.not_in_plc, lambda it: "%s -> %s" % it)
    section("POSSIBLE RENAME (not changed)", p.renames, lambda it: "%s -> %s" % it)
    section("EFCLib v1 DIFFERS FROM EXPORT (EFCLib layout used)", p.library, lambda it: "%s: %s" % it)
    section("CONFLICT (reported, not changed)", p.conflicts, lambda it: "%s: %s" % it)
    section("UDT MEMBER NOT IN PLC (kept, not deleted)", p.udt_stale, lambda it: "%s.%s" % it)
    section("UDT MEMBER DIFFERENCE (reported, not changed)", p.udt_diff, lambda it: "%s.%s: %s" % it)
    section("SKIPPED TAG", p.skipped, lambda it: "%s: %s" % it)
    section("SKIPPED UDT", p.udt_skipped, lambda it: "%s: %s" % it)
    return "\n".join(lines)
