# -*- coding: utf-8 -*-
"""Generate the XSY import Perspective project (projects/XSYImport) for Ignition 8.1.

    python3 tools/xsyimport/build_view.py

The view calls efc.xsyimport_gw.handle(payload) on the gateway. The planner and apply code
live in the gateway scripting project (see tools/xsyimport/README.md); this project only holds the view.

UNTESTED ON A GATEWAY. Component type names and event keys follow the 8.1 Perspective JSON
shape, but each one is marked VERIFY below and must be checked against an export from a dev gateway.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "projects", "XSYImport")
VIEW_DIR = os.path.join(ROOT, "com.inductiveautomation.perspective", "views", "XSYImport", "Import")

# ---- event scripts (run on the gateway, per session) -------------------------------------

STARTUP = '''from efc import xsyimport_gw as g
rows = g._provider_names(system.tag.getProviders())   # VERIFY: return type on 8.1
self.view.custom.providers = [{"label": n, "value": n} for n in rows]
self.view.custom.report = "Pick a provider, the OPC server name and a .XSY file, then Dry run."
self.view.custom.canApply = False
'''

DRY_RUN = '''from efc import xsyimport_gw as g
c = self.view.custom
if not c.provider or not c.opcServer or not c.fileB64:
    c.report = "Provider, OPC server name and an XSY file are all required."
    c.canApply = False
else:
    payload = {"provider": c.provider, "opcServer": c.opcServer, "data": c.fileB64,
               "dryRun": True, "user": session.props.auth.user.userName,   # VERIFY: userName property
               "layouts": []}
    res = g.handle(payload)
    if "error" in res:
        c.report = res["error"]
        c.canApply = False
    else:
        c.report = res["report"]
        c.counts = "%d UDT, %d tags, %d conflicts, %d skipped" % (
            res["counts"]["udt_create"], res["counts"]["tag_create"],
            res["counts"]["conflicts"], res["counts"]["skipped"])
        c.payload = payload
        c.canApply = True
'''

APPLY = '''from efc import xsyimport_gw as g
c = self.view.custom
if not c.canApply or not c.payload:
    c.report = "Run a dry run first."
else:
    payload = dict(c.payload)
    payload["dryRun"] = False
    res = g.handle(payload)
    if "error" in res:
        c.report = res["error"]
    else:
        errs = res.get("errors", [])
        c.report = res["report"] + "\\n\\nApplied. Errors: %d. Left after re-read: %s" % (len(errs), res.get("remaining"))
        if errs:
            c.report += "\\n" + "\\n".join(errs[:50])
    c.canApply = False
    c.payload = None
'''

ON_FILE = '''# VERIFY: name of the FileUpload event and where the uploaded bytes arrive on 8.1
import base64
self.view.custom.fileB64 = base64.b64encode(event.file.read()) if hasattr(event, "file") else None
'''


def _script_event(code):
    return {"type": "script", "config": {"script": code}}


def _label(name, text_expr, x, y, w, h, style=None):
    comp = {"type": "ia.display.label", "version": 0, "meta": {"name": name},
            "position": {"x": x, "y": y, "width": w, "height": h},
            "props": {"text": "", "style": style or {}}}
    if text_expr:
        comp["propConfig"] = {"props.text": {"binding": {"type": "property", "config": {"path": text_expr}}}}
    return comp


def _button(name, text, enabled_expr, script, x, y, w, h):
    comp = {"type": "ia.input.button", "version": 0, "meta": {"name": name},
            "position": {"x": x, "y": y, "width": w, "height": h},
            "props": {"text": text},
            "events": {"component": {"onActionPerformed": _script_event(script)}}}
    if enabled_expr:
        comp["propConfig"] = {"props.enabled": {"binding": {"type": "property", "config": {"path": enabled_expr}}}}
    return comp


def build():
    view = {
        "custom": {"providers": [], "provider": None, "opcServer": "", "fileB64": None,
                   "report": "", "counts": "", "canApply": False, "payload": None},
        "params": {},
        "props": {"defaultSize": {"width": 900, "height": 700}, "style": {"padding": "16px"}},
        "root": {
            "type": "ia.container.flex",
            "version": 0,
            "meta": {"name": "root"},
            "props": {"direction": "column", "gap": "10px"},
            "events": {"component": {"onStartup": _script_event(STARTUP)}},
            "children": [
                _label("Title", None, 0, 0, 0, 0, {"fontSize": "20px", "fontWeight": "bold"}),
                {"type": "ia.input.dropdown", "version": 0, "meta": {"name": "Provider"},
                 "props": {"placeholder": "Tag provider"},
                 "propConfig": {"props.options": {"binding": {"type": "property",
                                                              "config": {"path": "view.custom.providers"}}},
                                "props.value": {"binding": {"type": "property",
                                                            "config": {"path": "view.custom.provider"}}}}},
                {"type": "ia.input.text-field", "version": 0, "meta": {"name": "OPC"},
                 "props": {"placeholder": "OPC server name for this project"},
                 "propConfig": {"props.value": {"binding": {"type": "property",
                                                            "config": {"path": "view.custom.opcServer"}}}}},
                {"type": "ia.input.file-upload", "version": 0, "meta": {"name": "XsyFile"},   # VERIFY type name
                 "props": {"accept": ".xsy,.XSY"},
                 "events": {"component": {"onFileUploaded": _script_event(ON_FILE)}}},          # VERIFY event name
                {"type": "ia.container.flex", "version": 0, "meta": {"name": "Actions"},
                 "props": {"direction": "row", "gap": "10px"},
                 "children": [
                     _button("DryRun", "Dry run", None, DRY_RUN, 0, 0, 0, 0),
                     _button("Apply", "Apply", "view.custom.canApply", APPLY, 0, 0, 0, 0)]},
                {"type": "ia.display.label", "version": 0, "meta": {"name": "Counts"},
                 "propConfig": {"props.text": {"binding": {"type": "property",
                                                           "config": {"path": "view.custom.counts"}}}},
                 "props": {"text": ""}},
                {"type": "ia.input.text-area", "version": 0, "meta": {"name": "Report"},
                 "props": {"readOnly": True, "style": {"fontFamily": "monospace"}},
                 "propConfig": {"props.text": {"binding": {"type": "property",
                                                           "config": {"path": "view.custom.report"}}}}},
            ],
        },
    }
    # the title text is set in the view so it renders without a binding
    view["root"]["children"][0]["props"]["text"] = "XSY tag import"
    return view


def write():
    os.makedirs(VIEW_DIR, exist_ok=True)
    with open(os.path.join(VIEW_DIR, "view.json"), "w", encoding="utf-8") as f:
        json.dump(build(), f, indent=2)
        f.write("\n")
    with open(os.path.join(VIEW_DIR, "resource.json"), "w", encoding="utf-8") as f:
        json.dump({"scope": "G", "version": 1, "restricted": False, "overridable": True,
                   "files": ["view.json"],
                   "attributes": {"lastModification": {"actor": "efc-ignition-library",
                                                       "timestamp": "2026-10-22T00:00:00Z"}}}, f, indent=2)
        f.write("\n")
    with open(os.path.join(ROOT, "project.json"), "w", encoding="utf-8") as f:
        json.dump({"title": "XSYImport",
                   "description": "Import Control Expert XSY HMI variables into the project's tag provider. "
                                  "Needs the EFC_Tools gateway scripts (see tools/xsyimport/README.md).",
                   "parent": "", "enabled": True, "inheritable": False}, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    write()
    print("wrote", os.path.relpath(VIEW_DIR, os.path.join(HERE, "..", "..")))
