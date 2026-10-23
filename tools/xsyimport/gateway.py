# -*- coding: utf-8 -*-
"""XSY tag import: Designer and gateway glue (Jython 2.7, Ignition 8.1).

UNTESTED ON A GATEWAY. Every line marked VERIFY is an API or behaviour to confirm
on the dev gateway before the first real import. The planning logic in
xsyimport.py is tested offline (test_xsyimport.py).

Install (gateway scripting project, inheritable library):
  Project Library  efc/xsyimport.py      <- copy of tools/xsyimport/xsyimport.py
  Project Library  efc/library_types.py  <- copy of tools/xsyimport/library_types.py (run build_library.py first)
  Project Library  efc/xsyimport_gw.py   <- this file
  Message handler  name "xsyImport"      -> calls  efc.xsyimport_gw.handle(payload)

Run from the Designer Script Console:
  from efc import xsyimport_gw
  xsyimport_gw.designerRun()

Flow: ask tag provider + OPC server, pick the .XSY, dry run on the gateway, save the report
next to the file, confirm, apply, re-read and report what is left.
"""
import base64
import datetime

from efc import xsyimport as X

PROJECT = "EFC_Tools"        # VERIFY: gateway scripting project that holds this library
HANDLER = "xsyImport"        # VERIFY: message handler name registered in that project
REQUIRED_ROLE = "Engineering"

log = system.util.getLogger("XsyImport")


# ------------------------------------------------------------------- gateway side

def _tree(path):
    """Children of a tag folder, recursive. VERIFY: returns [] for a folder that does not exist."""
    return system.tag.getConfiguration(path, True) or []


def _ensure_folder(parent, name):
    system.tag.configure(parent, [{"name": name, "tagType": "Folder"}], "i")


def _provider(payload):
    """'[name]' for the payload's tag provider. Every tag and type path is built from this."""
    return "[" + payload["provider"] + "]"


def _plan(payload):
    raw = base64.b64decode(payload["data"])
    PROVIDER = _provider(payload)
    opts = {"opcServer": payload["opcServer"],
            "prefix": payload.get("prefix") or X.DEFAULT_PREFIX,
            "syncDocumentation": payload.get("syncDocumentation", True),
            "layouts": [base64.b64decode(x) for x in payload.get("layouts") or []]}
    tags = _tree(PROVIDER)                 # tag provider root, recursive
    types = _tree(PROVIDER + "_types_")    # UDT definitions, flat under _types_
    p = X.plan(raw, tags, types, opts)
    header = ["XSY tag import, provider %s, OPC server %s" % (PROVIDER, opts["opcServer"]),
              "UDTs flat in %s_types_, tags grouped by UDT under the provider root" % PROVIDER,
              "Planner version %s" % X.VERSION, ""]
    return p, X.report_text(p, header)


def _apply(p, PROVIDER):
    """Write a Plan under PROVIDER ('[name]'). Creates are 'i' (never overwrite), extends are 'i', doc updates are 'm'."""
    bad = []
    typesRoot = PROVIDER + "_types_"
    for folder, js in p.udt_create:               # flat at the _types_ root; nested types were ordered first
        for q in system.tag.configure(typesRoot, [js], "i"):
            if not q.isGood():
                bad.append("UDT %s: %s" % (js["name"], q))
    for tname, members in p.udt_extend:
        for q in system.tag.configure(typesRoot + "/" + tname, members, "i"):
            if not q.isGood():
                bad.append("UDT member %s.*: %s" % (tname, q))
    made = set()
    for folder, js in p.tag_create:                # create group folders (and array folders) as needed
        parts = [x for x in folder.split("/") if x]
        for depth in range(1, len(parts) + 1):
            sub = "/".join(parts[:depth])
            if sub not in made:
                _ensure_folder(PROVIDER + "/".join(parts[:depth - 1]), parts[depth - 1])
                made.add(sub)
    for folder, js in p.tag_create:
        for q in system.tag.configure(PROVIDER + folder, [js], "i"):    # "[prov]" + "Valves"
            if not q.isGood():
                bad.append("tag %s: %s" % (js["name"], q))
    for path, props in p.tag_update:
        parent, name = path.rsplit("/", 1)
        props = dict(props)
        props["name"] = name
        for q in system.tag.configure(PROVIDER + parent, [props], "m"):
            if not q.isGood():
                bad.append("doc %s: %s" % (path, q))
    return bad


def _may_apply(user):
    try:
        # VERIFY: system.security.getRolesForUser exists on the target 8.1 build.
        return REQUIRED_ROLE in system.security.getRolesForUser(user)
    except Exception:
        return False


def handle(payload):
    """Message handler entry point. Returns a dict the Designer shows."""
    dry = payload.get("dryRun", True)
    if not dry and not _may_apply(payload.get("user", "")):
        return {"error": "applying needs role %s" % REQUIRED_ROLE}
    try:
        p, text = _plan(payload)
    except X.ImportRefused as e:
        return {"error": str(e)}
    if dry:
        return {"report": text, "counts": p.counts()}
    bad = _apply(p, _provider(payload))
    p2, _ = _plan(payload)
    log.info("XSY import provider %s by %s: %s; errors %d"
             % (payload["provider"], payload.get("user", "?"), p.counts(), len(bad)))
    return {"report": text, "counts": p.counts(), "errors": bad, "remaining": p2.counts()}


# ------------------------------------------------------------------- Designer side

def _provider_names(ds):
    """Provider names from system.tag.getProviders(). VERIFY: return type and column name on 8.1.

    Handles a Dataset (a 'Name' column, else the first column), a list of strings, or a list of dicts.
    """
    names = []
    try:
        if hasattr(ds, "getRowCount"):
            col = 0
            for i in range(ds.getColumnCount()):
                if str(ds.getColumnName(i)).lower() == "name":
                    col = i
            names = [ds.getValueAt(r, col) for r in range(ds.getRowCount())]
        else:
            for item in ds or []:
                names.append(item.get("name") if isinstance(item, dict) else item)
    except Exception:
        log.warn("could not read tag providers from %r" % (ds,))
    return [unicode(n) for n in names if n]    # noqa: F821 (Jython 2.7 only; this file never runs in CPython)


def designerRun():
    # VERIFY: on 8.1 system.tag.getProviders() returns a dataset-like object (not a list of strings);
    # confirm the return type and the column holding the provider name on the dev gateway.
    ds = system.tag.getProviders()
    names = _provider_names(ds)
    if not names:
        system.gui.messageBox("No tag providers found.")
        return
    provider = (system.gui.inputBox("Tag provider for this project. Available: %s" % ", ".join(names), "")
                or "").strip().strip("[]")
    if not provider:
        return
    if provider not in names:
        system.gui.messageBox("'%s' is not a tag provider. Available: %s" % (provider, ", ".join(names)))
        return
    opc = (system.gui.inputBox("OPC server name for this project, as used by the UDT OPC Server parameter:", "")
           or "").strip()
    if not opc:
        return
    path = system.file.openFile("xsy")   # VERIFY: extension filter syntax in the 8.1 Designer
    if not path:
        return
    raw = system.file.readFileAsBytes(path)
    data = "".join([chr(b & 0xFF) for b in raw])     # Java byte[] -> raw bytes in Jython
    layouts = []
    while system.gui.confirm("Add a layout file for types the export does not define?\n"
                             "(EFCLib v1 types are built in and never need one.)"):
        lp = system.file.openFile("")   # VERIFY: no filter = any file type
        if not lp:
            break
        layouts.append(base64.b64encode("".join([chr(b & 0xFF) for b in system.file.readFileAsBytes(lp)])))
    payload = {"provider": provider, "opcServer": opc, "data": base64.b64encode(data), "dryRun": True,
               "layouts": layouts}

    res = system.util.sendRequest(PROJECT, HANDLER, payload)   # VERIFY: 8.1 sendRequest signature
    if "error" in res:
        system.gui.messageBox(res["error"])
        return
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    reportPath = "%s_%s_%s_report.txt" % (path.rsplit(".", 1)[0], provider, stamp)
    system.file.writeFile(reportPath, res["report"])
    print(res["report"])
    print("Report saved to %s" % reportPath)
    c = res["counts"]
    summary = ("Create %d UDT, extend %d UDT, create %d tags, update %d docs.\n"
               "Conflicts (not changed): %d. Skipped: %d tags, %d UDTs.\n\nApply now?") % (
        c["udt_create"], c["udt_extend"], c["tag_create"], c["tag_update"],
        c["conflicts"], c["skipped"], c["udt_skipped"])
    if not system.gui.confirm(summary):
        return

    payload["dryRun"] = False
    res = system.util.sendRequest(PROJECT, HANDLER, payload)
    if "error" in res:
        system.gui.messageBox(res["error"])
        return
    errs = res.get("errors", [])
    msg = "Applied. Errors: %d. Still to create after re-read: %s" % (len(errs), res.get("remaining"))
    if errs:
        msg += "\n" + "\n".join(errs[:20])
    system.gui.messageBox(msg)
