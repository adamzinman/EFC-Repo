# -*- coding: utf-8 -*-
"""Control Expert V16.2 .XSY -> Ignition 8.1 tag planner.

Pure logic: no system.* calls, so the same file runs in Jython 2.7 (gateway
scripting project, as efc/xsyimport.py) and in CPython (tools/xsyimport tests).

    plan(xsy_bytes, line, tag_tree, types_tree, options) -> Plan

Nothing is written here. The gateway glue (gateway.py) applies a Plan with
system.tag.configure. Rules follow docs/xsy-tag-import-strategy.md and the
shared PLC <-> Ignition interface contract (v1.0).
"""
import base64
import re
import xml.etree.ElementTree as ET

try:  # Jython 2.7 uses unicode; CPython 3 uses str
    STRING_TYPES = (basestring,)  # noqa: F821
except NameError:
    STRING_TYPES = (str,)

VERSION = "1.0.0"
HMI_ATTR = "IsVariableHMI"
HMI_TRUE = ("-1", "1", "TRUE")
PARAM_PREFIX = "OPC Prefix"
PARAM_SERVER = "OPC Server"
PARAM_TAG = "Tag"
DEFAULT_PREFIX = "ns=2;s=0:"
IMPORTED = "imported"
ITEM_PATH = "{OPC Prefix}{Tag}.{TagName}"

# Control Expert elementary type -> Ignition dataType (contract v1.0 table).
ELEMENTARY = {
    "BOOL": "Boolean", "EBOOL": "Boolean",
    "INT": "Int2",
    "UINT": "Int4", "WORD": "Int4", "DINT": "Int4",
    "UDINT": "Int8", "DWORD": "Int8",
    "REAL": "Float4",
    "STRING": "String",
    "TIME": "Int4",
}
LINE_RE = re.compile(r"^\d{3}$")
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
STRING_RE = re.compile(r"^STRING(\[\d+\])?$")

DEFAULTS = {
    "opcServer": None,          # required: the OPC UA connection name, asked at run time
    "prefix": DEFAULT_PREFIX,   # OPC item prefix for elementary tags and UDT members
    "syncDocumentation": True,  # a non-empty PLC comment overwrites Ignition Documentation; blank never does
    "typesFolder": None,        # UDT folder under _types_; defaults to the line number
}


class ImportRefused(Exception):
    """Raised for inputs that must not be imported at all (never a per-variable problem)."""


# --------------------------------------------------------------------------- XSY

class Model(object):
    def __init__(self):
        self.ddts = {}   # DDT name -> [(member, typeName, comment)]
        self.fbs = {}    # FB type name -> [(member, typeName, comment)] (inputs, outputs, public)
        self.hmi = []    # [(variable, typeName, comment)] for HMI-flagged top-level variables
        self.total = 0   # top-level variables in the export
        self.flagged = 0 # variables that carry the HMI attribute at all, any value


def _comment(el):
    c = el.find("comment")
    return (c.text or "").strip() if c is not None and c.text else ""


def _members(el):
    if el is None:
        return []
    return [(v.get("name"), (v.get("typeName") or "").strip(), _comment(v))
            for v in el.findall("variables")]


def parse(data):
    """Parse XSY bytes (utf-8 or str). Refuses an export that has no HMI flags at all."""
    root = ET.fromstring(data)
    if root.tag != "VariablesExchangeFile":
        raise ImportRefused("not a Control Expert variables export (root is %s)" % root.tag)
    m = Model()
    for s in root.findall("DDTSource"):
        m.ddts[s.get("DDTName")] = _members(s.find("structure"))
    for f in root.findall("FBSource"):
        mem = []
        for sec in ("inputParameters", "outputParameters", "publicLocalVariables"):
            mem.extend(_members(f.find(sec)))
        m.fbs[f.get("nameOfFBType")] = mem
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


# --------------------------------------------------------------------- type rules

def _elem(t):
    u = t.upper()
    if STRING_RE.match(u):
        return "String"
    return ELEMENTARY.get(u)


def _kind(tn, model):
    """-> (kind, value, reason). kind is 'elem' (value = dataType), 'udt' (value = type name) or 'skip'."""
    if tn.upper().startswith("ARRAY"):
        return "skip", None, "array %s is not mapped in v1" % tn
    dt = _elem(tn)
    if dt:
        return "elem", dt, None
    if tn in model.ddts or tn in model.fbs:
        return "udt", tn, None
    return "skip", None, "type %s is not elementary and not defined in the export" % tn


def _atomic_member(name, dt, comment):
    return {"name": name, "tagType": "AtomicTag", "valueSource": "opc", "dataType": dt,
            "opcServer": {"bindType": "parameter", "binding": "{OPC Server}"},
            "opcItemPath": {"bindType": "parameter", "binding": ITEM_PATH},
            "documentation": comment}


def _nested_member(name, type_id, comment):
    return {"name": name, "tagType": "UdtInstance", "typeId": type_id,
            "parameters": {
                PARAM_PREFIX: {"dataType": "String", "value": {"bindType": "parameter", "binding": "{OPC Prefix}"}},
                PARAM_SERVER: {"dataType": "String", "value": {"bindType": "parameter", "binding": "{OPC Server}"}},
                PARAM_TAG: {"dataType": "String", "value": {"bindType": "parameter", "binding": "{Tag}.%s" % name}}},
            "documentation": comment}


class _Builder(object):
    """Builds UDT definitions for every DDT/FB reached from the HMI variables."""

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
            return None, "recursive type"
        members = self.model.ddts[name] if name in self.model.ddts else self.model.fbs[name]
        tags, problem = [], None
        for mname, tn, comment in members:
            if not NAME_RE.match(mname or ""):
                problem = "member %s has a name Ignition does not allow" % mname
                break
            kind, val, why = _kind(tn, self.model)
            if kind == "elem":
                tags.append(_atomic_member(mname, val, comment))
            elif kind == "udt":
                sub, why2 = self.udt(val, stack + (name,))
                if sub is None:
                    problem = "member %s: %s" % (mname, why2)
                    break
                tags.append(_nested_member(mname, "%s/%s" % (self.folder, val), comment))
            else:
                problem = "member %s: %s" % (mname, why)
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
        self.udt_extend = []    # (type name, [member json]) missing members added
        self.udt_stale = []     # (type name, member) in Ignition but no longer in the PLC; reported only
        self.udt_diff = []      # (type name, member, message); reported only
        self.udt_skipped = []   # (type name, reason)
        self.tag_create = []    # (folder, tag json)
        self.tag_update = []    # (full path, {property: value}) documentation only
        self.exists = []        # (variable, path): already in Ignition, nothing to do
        self.conflicts = []     # (variable, message): different type/dataType, reported only
        self.skipped = []       # (variable, reason)

    def counts(self):
        return {"udt_create": len(self.udt_create), "udt_extend": len(self.udt_extend),
                "udt_stale": len(self.udt_stale), "udt_diff": len(self.udt_diff),
                "udt_skipped": len(self.udt_skipped), "tag_create": len(self.tag_create),
                "tag_update": len(self.tag_update), "exists": len(self.exists),
                "conflicts": len(self.conflicts), "skipped": len(self.skipped)}

    def is_noop(self):
        return not (self.udt_create or self.udt_extend or self.tag_create or self.tag_update)


def plan(data, line, tag_tree, types_tree, options=None):
    """Plan an import of `data` (XSY bytes) into production line `line`.

    tag_tree   children of the provider folder <line> (getConfiguration(..., True))
    types_tree children of _types_/<typesFolder> (defaults to the line)
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
    builder = _Builder(model, tf, prefix)
    existing_types = types_index(types_tree)
    recs = records(tag_tree, line)
    inst, atoms, used_names = {}, {}, set()
    for r in recs:
        if not r["top"]:
            continue
        used_names.add(r["name"])
        if r["tagType"] == "UdtInstance":
            tag = _pval(r["params"].get(PARAM_TAG))
            if tag:
                inst.setdefault(tag, r)
        elif r["tagType"] == "AtomicTag" and r["opcItemPath"]:
            key = _plc_key(r["opcItemPath"])
            if key:
                atoms.setdefault(key, r)

    p = Plan()
    imported = "%s/%s" % (line, IMPORTED)

    for vname, tn, comment in model.hmi:
        if not NAME_RE.match(vname or ""):
            p.skipped.append((vname, "name is not allowed in Ignition"))
            continue
        kind, val, why = _kind(tn, model)

        if kind == "elem":
            rec = atoms.get(vname)
            if rec is None and vname in inst:
                p.conflicts.append((vname, "UDT instance %s in Ignition, %s in PLC; not changed"
                                    % (inst[vname]["typeId"], val)))
                continue
            if rec:
                p.exists.append((vname, rec["path"]))
                if rec["dataType"] and rec["dataType"] != val:
                    p.conflicts.append((vname, "dataType %s in Ignition, %s in PLC; not changed"
                                        % (rec["dataType"], val)))
                if sync_doc and comment and rec["documentation"] != comment:
                    p.tag_update.append((rec["path"], {"tagType": "AtomicTag", "documentation": comment}))
                continue
            if vname in used_names:
                p.skipped.append((vname, "name already used by another tag under %s" % line))
                continue
            p.tag_create.append((imported, {
                "name": vname, "tagType": "AtomicTag", "valueSource": "opc", "dataType": val,
                "opcServer": server, "opcItemPath": prefix + vname, "documentation": comment}))
            continue

        if kind != "udt":
            p.skipped.append((vname, why))
            continue
        js, why = builder.udt(val)
        if js is None:
            p.skipped.append((vname, "type %s: %s" % (val, why)))
            continue
        rec = inst.get(vname)
        if rec:
            if _last(rec["typeId"]) != val:
                p.conflicts.append((vname, "type %s in Ignition, %s in PLC; not changed"
                                    % (rec["typeId"], val)))
            p.exists.append((vname, rec["path"]))
            if sync_doc and comment and rec["documentation"] != comment:
                p.tag_update.append((rec["path"], {"tagType": "UdtInstance", "documentation": comment}))
            continue
        if vname in used_names:
            p.skipped.append((vname, "name already used by another tag under %s" % line))
            continue
        p.tag_create.append((imported, {
            "name": vname, "tagType": "UdtInstance", "typeId": "%s/%s" % (tf, val),
            "parameters": {PARAM_SERVER: {"dataType": "String", "value": server},
                           PARAM_TAG: {"dataType": "String", "value": vname}},
            "documentation": comment}))

    # UDT definitions: create missing types, add missing members, report the rest.
    for tname in builder.order:
        js = builder.done[tname][0]
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

    for tname, (js, why) in builder.done.items():
        if js is None:
            p.udt_skipped.append((tname, why))

    p.udt_create.sort(key=lambda item: builder.order.index(item[1]["name"]))
    return p


# ----------------------------------------------------------------------- report

def report_text(p, header):
    lines = list(header)

    def section(title, items, fmt):
        lines.append("")
        lines.append("%s (%d)" % (title, len(items)))
        for it in items:
            lines.append("  " + fmt(it))

    section("NEW UDT", p.udt_create, lambda it: "%s/%s  (%d members)" % (it[0], it[1]["name"], len(it[1]["tags"])))
    section("EXTENDED UDT (members added)", p.udt_extend,
            lambda it: "%s: + %s" % (it[0], ", ".join(t["name"] for t in it[1])))
    section("NEW TAG", p.tag_create, lambda it: "%s/%s  (%s)" % (it[0], it[1]["name"], it[1]["tagType"]))
    section("UPDATED DOCUMENTATION", p.tag_update, lambda it: "%s" % it[0])
    section("UP TO DATE", p.exists, lambda it: "%s -> %s" % (it[0], it[1]))
    section("CONFLICT (reported, not changed)", p.conflicts, lambda it: "%s: %s" % it)
    section("UDT DIFFERENCE (reported, not changed)", p.udt_diff, lambda it: "%s.%s: %s" % it)
    section("STALE UDT MEMBER (in Ignition, not in PLC; kept)", p.udt_stale, lambda it: "%s.%s" % it)
    section("SKIPPED TAG", p.skipped, lambda it: "%s: %s" % it)
    section("SKIPPED UDT", p.udt_skipped, lambda it: "%s: %s" % it)
    return "\n".join(lines)


def encode(text):
    """Payload helper shared by the Designer and the gateway (base64 of the raw XSY bytes)."""
    return base64.b64encode(text)
