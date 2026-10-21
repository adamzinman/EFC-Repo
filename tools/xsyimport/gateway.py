# -*- coding: utf-8 -*-
"""XSY tag import: Designer and gateway glue (Jython 2.7, Ignition 8.1).

UNTESTED ON A GATEWAY. Every line marked VERIFY is an API or behaviour to confirm
on the dev gateway before the first real import. The planning logic in
xsyimport.py is tested offline (test_xsyimport.py).

Install (gateway scripting project, inheritable library):
  Project Library  efc/xsyimport.py      <- copy of tools/xsyimport/xsyimport.py
  Project Library  efc/xsyimport_gw.py   <- this file
  Message handler  name "xsyImport"      -> calls  efc.xsyimport_gw.handle(payload)

Run from the Designer Script Console:
  from efc import xsyimport_gw
  xsyimport_gw.designerRun()

Flow: ask line + OPC server, pick the .XSY, dry run on the gateway, save the report
next to the file, confirm, apply, re-read and report what is left.
"""
import base64
import datetime

from efc import xsyimport as X

PROVIDER = "[EFC]"
PROJECT = "EFC_Tools"        # VERIFY: gateway scripting project that holds this library
HANDLER = "xsyImport"        # VERIFY: message handler name registered in that project
REQUIRED_ROLE = "Engineering"
IMPORTED = X.IMPORTED

log = system.util.getLogger("XsyImport")


# ------------------------------------------------------------------- gateway side

def _tree(path):
    """Children of a tag folder, recursive. VERIFY: returns [] for a folder that does not exist."""
    return system.tag.getConfiguration(path, True) or []


def _ensure_folder(parent, name):
    system.tag.configure(parent, [{"name": name, "tagType": "Folder"}], "i")


def _plan(payload):
    raw = base64.b64decode(payload["data"])
    line = payload["line"]
    opts = {"opcServer": payload["opcServer"],
            "prefix": payload.get("prefix") or X.DEFAULT_PREFIX,
            "syncDocumentation": payload.get("syncDocumentation", True),
            "typesFolder": None}
    tags = _tree(PROVIDER + line)
    types = _tree(PROVIDER + "_types_/" + line)
    p = X.plan(raw, line, tags, types, opts)
    header = ["XSY tag import, line %s, OPC server %s" % (line, opts["opcServer"]),
              "Provider %s, UDT folder _types_/%s, tag folder %s/%s" % (PROVIDER, line, line, IMPORTED),
              "Planner version %s" % X.VERSION, ""]
    return p, X.report_text(p, header)


def _apply(p, line):
    """Write a Plan. Creates are 'i' (never overwrite), extends are 'i', doc updates are 'm'."""
    bad = []
    typesRoot = PROVIDER + "_types_"
    if p.udt_create or p.udt_extend:
        _ensure_folder(typesRoot, line)
    for folder, js in p.udt_create:               # nested types were ordered first by the planner
        for q in system.tag.configure(typesRoot + "/" + folder, [js], "i"):
            if not q.isGood():
                bad.append("UDT %s: %s" % (js["name"], q))
    for tname, members in p.udt_extend:
        for q in system.tag.configure(typesRoot + "/" + line + "/" + tname, members, "i"):
            if not q.isGood():
                bad.append("UDT member %s.*: %s" % (tname, q))
    if p.tag_create:
        _ensure_folder(PROVIDER + line, IMPORTED)
    for folder, js in p.tag_create:
        for q in system.tag.configure(PROVIDER + folder, [js], "i"):
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
    bad = _apply(p, payload["line"])
    p2, _ = _plan(payload)
    log.info("XSY import line %s by %s: %s; errors %d"
             % (payload["line"], payload.get("user", "?"), p.counts(), len(bad)))
    return {"report": text, "counts": p.counts(), "errors": bad, "remaining": p2.counts()}


# ------------------------------------------------------------------- Designer side

def designerRun():
    line = (system.gui.inputBox("Production line number (three digits, e.g. 058):", "") or "").strip()
    if not line:
        return
    opc = (system.gui.inputBox("OPC server name for this line, as used by the UDT OPC Server parameter:", "")
           or "").strip()
    if not opc:
        return
    path = system.file.openFile("xsy")   # VERIFY: extension filter syntax in the 8.1 Designer
    if not path:
        return
    raw = system.file.readFileAsBytes(path)
    data = "".join([chr(b & 0xFF) for b in raw])     # Java byte[] -> raw bytes in Jython
    payload = {"line": line, "opcServer": opc, "data": base64.b64encode(data), "dryRun": True}

    res = system.util.sendRequest(PROJECT, HANDLER, payload)   # VERIFY: 8.1 sendRequest signature
    if "error" in res:
        system.gui.messageBox(res["error"])
        return
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    reportPath = "%s_%s_%s_report.txt" % (path.rsplit(".", 1)[0], line, stamp)
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
