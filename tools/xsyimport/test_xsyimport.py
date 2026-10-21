# -*- coding: utf-8 -*-
"""Offline tests for xsyimport.py against the sample export and live tag export.

    python3 tools/xsyimport/test_xsyimport.py
"""
import copy
import json
import os
import unittest

import xsyimport as X

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "..", "..", "samples", "xsy-import")
XSY = os.path.join(SAMPLES, "RGTCR_variables.XSY")
TAGS = os.path.join(SAMPLES, "RGTCR_ignition_tags.json")
SERVER = "M580_L058"


def load_xsy():
    with open(XSY, "rb") as f:
        return f.read()


def load_tags():
    with open(TAGS, encoding="utf-8") as f:
        return json.load(f)


def folder(tree, *path):
    """Children of the folder at `path` in a getConfiguration-shaped tree."""
    nodes = tree
    for name in path:
        nodes = next(n for n in nodes if n["name"] == name).get("tags", [])
    return nodes


def apply_sim(p, tag_tree, types_tree, line):
    """Mimic gateway.apply: merge a Plan into in-memory trees."""
    types = types_tree
    for tf, js in p.udt_create:
        types.append(copy.deepcopy(js))
    for tname, members in p.udt_extend:
        node = next(n for n in types if n.get("name") == tname)
        node.setdefault("tags", []).extend(copy.deepcopy(members))
    for fold, js in p.tag_create:
        # fold is "<line>/imported": create the folder under the line if needed
        sub = fold.split("/", 1)[1]
        if not any(n["name"] == sub for n in tag_tree):
            tag_tree.append({"name": sub, "tagType": "Folder", "tags": []})
        nodes = next(n for n in tag_tree if n["name"] == sub)["tags"]
        nodes.append(copy.deepcopy(js))
    for path, props in p.tag_update:
        name = path.rsplit("/", 1)[-1]
        node = _find_by_path(tag_tree, path)
        node.update(props)
        node["name"] = name
    return tag_tree, types_tree


def _find_by_path(tree, path):
    """path is 'line/…/name'; the line segment is the root of tag_tree."""
    parts = path.split("/")[1:]
    nodes = tree
    for i, name in enumerate(parts):
        node = next(n for n in nodes if n["name"] == name)
        if i == len(parts) - 1:
            return node
        nodes = node.get("tags", [])


class ParseTests(unittest.TestCase):
    def test_hmi_filter_counts(self):
        m = X.parse(load_xsy())
        self.assertEqual(m.total, 496)
        self.assertEqual(len(m.hmi), 217)
        self.assertGreater(len(m.ddts), 40)
        self.assertEqual(len(m.fbs), 14)

    def test_fb_members_are_read_from_export(self):
        m = X.parse(load_xsy())
        names = [v[0] for v in m.fbs["DFB_TMR"]]
        self.assertIn("IN", names)
        self.assertIn("Q", names)

    def test_refuses_export_without_hmi_flags(self):
        raw = load_xsy().replace(b"IsVariableHMI", b"IsVariableXXX")
        with self.assertRaises(X.ImportRefused):
            X.parse(raw)

    def test_refuses_non_xsy(self):
        with self.assertRaises(X.ImportRefused):
            X.parse(b"<root/>")


class PlanInputTests(unittest.TestCase):
    def test_bad_line_refused(self):
        with self.assertRaises(X.ImportRefused):
            X.plan(load_xsy(), "58", [], [], {"opcServer": SERVER})

    def test_blank_server_refused(self):
        with self.assertRaises(X.ImportRefused):
            X.plan(load_xsy(), "058", [], [], {"opcServer": "  "})


class FreshLineTests(unittest.TestCase):
    """Line 058 does not exist yet: everything buildable is new."""

    @classmethod
    def setUpClass(cls):
        cls.p = X.plan(load_xsy(), "058", [], [], {"opcServer": SERVER})

    def test_every_hmi_variable_accounted_for_once(self):
        # array-of-DDT variables expand to one tag per element; count them under the array name
        names = set()
        for fold, js in self.p.tag_create:
            names.add(fold.split("/")[-1] if js["name"].startswith("_") and "/" in fold and fold.split("/")[-1] != "imported" else js["name"])
        names |= set(v for v, _ in self.p.exists if "[" not in v) | set(v for v, _ in self.p.conflicts if "[" not in v)
        names |= set(v for v, _ in self.p.skipped)
        self.assertEqual(len(names), 217)

    def test_arrays_and_io_card_types_are_skipped_with_reason(self):
        reasons = dict(self.p.skipped)
        self.assertNotIn("Spare_Valve", reasons)   # array of DDT: imported as indexed instances
        self.assertIn("Spare_Valve", [f.split("/")[-1] for f, _ in self.p.tag_create])
        self.assertIn("PLC0_d0_r0_s5_DDO1602", reasons)
        self.assertIn("T_U_DIS_STD_OUT_16", reasons["PLC0_d0_r0_s5_DDO1602"])
        self.assertNotIn("PLC0_d0_r0_s5_DDO1602", [j["name"] for _, j in self.p.tag_create])

    def test_dfb_instances_become_udts(self):
        names = [js["name"] for _, js in self.p.tag_create]
        self.assertIn("Fill_Press", names)
        udt_names = [js["name"] for _, js in self.p.udt_create]
        self.assertIn("DFB_TMR", udt_names)

    def test_nested_udts_come_before_their_parent(self):
        order = [js["name"] for _, js in self.p.udt_create]
        for parent in ("DDT_Process_Value", "T_Scales", "DDT_CompModes"):
            if parent in order and "DDT_AI_Alarm" in order:
                self.assertLess(order.index("DDT_AI_Alarm"), order.index(parent))

    def test_udts_are_in_line_folder_and_typeids_qualified(self):
        for fold, js in self.p.udt_create:
            self.assertEqual(fold, "058")
        for fold, js in self.p.tag_create:
            if js["tagType"] == "UdtInstance":
                self.assertEqual(js["typeId"].split("/")[0], "058")

    def test_elementary_tags_go_to_imported_with_opc_item(self):
        m = X.parse(load_xsy())
        name, tn, _ = next(v for v in m.hmi if X._elem(v[1]))
        fold, js = next((f, j) for f, j in self.p.tag_create if j["name"] == name)
        self.assertEqual(fold, "058/imported")
        self.assertEqual(js["tagType"], "AtomicTag")
        self.assertEqual(js["opcItemPath"], "ns=2;s=0:" + name)
        self.assertEqual(js["opcServer"], SERVER)
        self.assertEqual(js["dataType"], X._elem(tn))

    def test_instances_carry_only_server_and_tag(self):
        for fold, js in self.p.tag_create:
            if js["tagType"] == "UdtInstance":
                self.assertEqual(set(js["parameters"]), {"OPC Server", "Tag"})
                tag = js["parameters"]["Tag"]["value"]
                self.assertTrue(tag == js["name"] or tag.endswith("[" + js["name"][1:] + "]"), tag)

    def test_udt_member_bindings_follow_contract(self):
        for _, js in self.p.udt_create:
            for t in js["tags"]:
                if t["tagType"] == "AtomicTag":
                    self.assertEqual(t["opcItemPath"]["binding"], "{OPC Prefix}{Tag}.{TagName}")
                    self.assertEqual(t["opcServer"]["binding"], "{OPC Server}")
            self.assertEqual(set(js["parameters"]), {"OPC Prefix", "OPC Server", "Tag"})


class RerunTests(unittest.TestCase):
    """Running again after applying must change nothing."""

    def test_second_run_is_noop(self):
        tags, types = [], []
        p1 = X.plan(load_xsy(), "058", tags, types, {"opcServer": SERVER})
        self.assertFalse(p1.is_noop())
        apply_sim(p1, tags, types, "058")
        p2 = X.plan(load_xsy(), "058", tags, types, {"opcServer": SERVER})
        self.assertEqual(p2.udt_create, [])
        self.assertEqual(p2.udt_extend, [])
        self.assertEqual(p2.tag_create, [])
        self.assertEqual(p2.tag_update, [])
        self.assertEqual(p2.conflicts, [])

    def test_moved_tag_is_found_not_duplicated(self):
        tags, types = [], []
        p1 = X.plan(load_xsy(), "058", tags, types, {"opcServer": SERVER})
        apply_sim(p1, tags, types, "058")
        # operator moves every imported tag into a Stations folder
        imported = next(n for n in tags if n["name"] == "imported")
        moved = {"name": "Stations", "tagType": "Folder", "tags": imported.pop("tags")}
        tags.append(moved)
        imported["tags"] = []
        tags.remove(imported)
        p2 = X.plan(load_xsy(), "058", tags, types, {"opcServer": SERVER})
        self.assertEqual(p2.tag_create, [])
        self.assertTrue(p2.exists)

    def _first_commented(self, p1):
        return next(js["name"] for _, js in p1.tag_create if js.get("documentation"))

    def test_documentation_change_in_plc_is_updated(self):
        tags, types = [], []
        p1 = X.plan(load_xsy(), "058", tags, types, {"opcServer": SERVER})
        apply_sim(p1, tags, types, "058")
        # simulate an Ignition-side documentation edit that differs from the PLC comment
        node = _find_by_path(tags, "058/imported/" + self._first_commented(p1))
        node["documentation"] = "old text"
        p2 = X.plan(load_xsy(), "058", tags, types, {"opcServer": SERVER})
        self.assertEqual(len(p2.tag_update), 1)
        p3_tags = apply_sim(p2, tags, types, "058")[0]
        self.assertEqual(X.plan(load_xsy(), "058", p3_tags, types, {"opcServer": SERVER}).tag_update, [])

    def test_blank_plc_comment_never_blanks_ignition_text(self):
        tags, types = [], []
        p1 = X.plan(load_xsy(), "058", tags, types, {"opcServer": SERVER})
        apply_sim(p1, tags, types, "058")
        blank = next(js["name"] for _, js in p1.tag_create if not js.get("documentation"))
        _find_by_path(tags, "058/imported/" + blank)["documentation"] = "written in Ignition"
        p2 = X.plan(load_xsy(), "058", tags, types, {"opcServer": SERVER})
        self.assertEqual([u for u in p2.tag_update if u[0].endswith("/" + blank)], [])

    def test_sync_documentation_off_leaves_docs_alone(self):
        tags, types = [], []
        p1 = X.plan(load_xsy(), "058", tags, types, {"opcServer": SERVER})
        apply_sim(p1, tags, types, "058")
        node = _find_by_path(tags, "058/imported/" + self._first_commented(p1))
        node["documentation"] = "keep me"
        p2 = X.plan(load_xsy(), "058", tags, types,
                    {"opcServer": SERVER, "syncDocumentation": False})
        self.assertEqual(p2.tag_update, [])


class LiveExportTests(unittest.TestCase):
    """The live provider already has line 056 with a DDT_Valve/Valve type. Plan against it."""

    @classmethod
    def setUpClass(cls):
        tree = load_tags()["tags"]
        cls.tags_056 = folder(tree, "056")
        cls.types_056 = folder(tree, "_types_", "056")
        cls.p = X.plan(load_xsy(), "056", cls.tags_056, cls.types_056, {"opcServer": "OPC_OSML"})

    def test_existing_type_is_extended_not_recreated(self):
        self.assertNotIn("Valve", [js["name"] for _, js in self.p.udt_create])

    def test_plan_is_consistent_with_counts(self):
        c = self.p.counts()
        self.assertEqual(c["tag_create"], len(self.p.tag_create))
        self.assertGreater(c["tag_create"] + c["exists"] + c["skipped"], 0)

    def test_unrelated_branches_are_not_touched(self):
        # plan only reads the line folder: nothing references RGTCR/OMSL/C2F6 paths
        for fold, _ in self.p.tag_create:
            self.assertTrue(fold.startswith("056"))


MINI_XSY = b"""<?xml version="1.0"?>
<VariablesExchangeFile>
  <DDTSource DDTName="T_Motor">
    <structure>
      <variables name="Cfg_Tag" typeName="STRING[20]"/>
      <variables name="Old_Member" typeName="BOOL"/>
    </structure>
  </DDTSource>
  <dataBlock>
    <variables name="P101" typeName="T_Motor">
      <attribute name="IsVariableHMI" value="-1"/>
    </variables>
  </dataBlock>
</VariablesExchangeFile>"""


class EFCLibTests(unittest.TestCase):
    """EFCLib v1 layouts override the export; differences are reported, not hidden."""

    def test_efclib_layout_is_used_and_difference_reported(self):
        p = X.plan(MINI_XSY, "058", [], [], {"opcServer": SERVER})
        udt = next(js for _, js in p.udt_create if js["name"] == "T_Motor")
        names = [t["name"] for t in udt["tags"]]
        self.assertIn("Mode", names)
        self.assertNotIn("Old_Member", names)
        diffs = " ".join(msg for _, msg in p.library)
        self.assertIn("Old_Member", diffs)

    def test_dt_maps_to_datetime(self):
        self.assertEqual(X._elem("DT"), "DateTime")


if __name__ == "__main__":
    unittest.main()
