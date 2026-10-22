# -*- coding: utf-8 -*-
"""Offline tests for xsyimport.py against the sample export and live tag export.

    python3 tools/xsyimport/test_xsyimport.py
"""
import copy
import json
import os
import re
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


def apply_sim(p, tag_tree, types_tree):
    """Mimic gateway.apply: merge a Plan into in-memory trees."""
    types = types_tree
    for tf, js in p.udt_create:
        types.append(copy.deepcopy(js))
    for tname, members in p.udt_extend:
        node = next(n for n in types if n.get("name") == tname)
        node.setdefault("tags", []).extend(copy.deepcopy(members))
    for fold, js in p.tag_create:
        # fold is relative to the provider root ("Motors", "Valves/Spare_Valve"): create each level if needed
        nodes = tag_tree
        for sub in [x for x in fold.split("/") if x]:
            if not any(n["name"] == sub for n in nodes):
                nodes.append({"name": sub, "tagType": "Folder", "tags": []})
            nodes = next(n for n in nodes if n["name"] == sub)["tags"]
        nodes.append(copy.deepcopy(js))
    for path, props in p.tag_update:
        name = path.rsplit("/", 1)[-1]
        node = _find_by_path(tag_tree, path)
        node.update(props)
        node["name"] = name
    return tag_tree, types_tree


def _find_by_path(tree, path):
    """path is relative to the provider root, e.g. 'Motors/P101'."""
    parts = path.split("/")
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
    def test_blank_server_refused(self):
        with self.assertRaises(X.ImportRefused):
            X.plan(load_xsy(), [], [], {"opcServer": "  "})


class FreshLineTests(unittest.TestCase):
    """An empty provider: everything buildable is new."""

    @classmethod
    def setUpClass(cls):
        cls.p = X.plan(load_xsy(), [], [], {"opcServer": SERVER})

    def test_every_hmi_variable_accounted_for_once(self):
        # array-of-DDT variables expand to one tag per element; count them under the array name
        names = set()
        for fold, js in self.p.tag_create:
            names.add(fold.split("/")[-1] if js["name"].startswith("_") and "/" in fold else js["name"])
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

    def test_udts_are_flat_and_typeids_are_plain_names(self):
        names = set(js["name"] for _, js in self.p.udt_create)
        for fold, js in self.p.udt_create:
            self.assertEqual(fold, "")
        for fold, js in self.p.tag_create:
            if js["tagType"] == "UdtInstance":
                self.assertNotIn("/", js["typeId"])
                self.assertIn(js["typeId"], names)
        for _, js in self.p.udt_create:
            for t in js["tags"]:
                if t["tagType"] == "UdtInstance":
                    self.assertNotIn("/", t["typeId"])

    def test_elementary_tags_go_to_other_with_opc_item(self):
        m = X.parse(load_xsy())
        name, tn, _ = next(v for v in m.hmi if X._elem(v[1]))
        fold, js = next((f, j) for f, j in self.p.tag_create if j["name"] == name)
        self.assertEqual(fold, "Other")
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
        p1 = X.plan(load_xsy(), tags, types, {"opcServer": SERVER})
        self.assertFalse(p1.is_noop())
        apply_sim(p1, tags, types)
        p2 = X.plan(load_xsy(), tags, types, {"opcServer": SERVER})
        self.assertEqual(p2.udt_create, [])
        self.assertEqual(p2.udt_extend, [])
        self.assertEqual(p2.tag_create, [])
        self.assertEqual(p2.tag_update, [])
        self.assertEqual(p2.conflicts, [])

    def test_moved_tag_is_found_not_duplicated(self):
        tags, types = [], []
        p1 = X.plan(load_xsy(), tags, types, {"opcServer": SERVER})
        apply_sim(p1, tags, types)
        # operator moves every imported tag into one folder, "Moved"
        moved = {"name": "Moved", "tagType": "Folder", "tags": []}
        for n in list(tags):
            moved["tags"].append(n)
            tags.remove(n)
        tags.append(moved)
        p2 = X.plan(load_xsy(), tags, types, {"opcServer": SERVER})
        self.assertEqual(p2.tag_create, [])
        self.assertTrue(p2.exists)

    def _first_commented(self, p1):
        return next(f + "/" + js["name"] for f, js in p1.tag_create if js.get("documentation"))

    def test_documentation_change_in_plc_is_updated(self):
        tags, types = [], []
        p1 = X.plan(load_xsy(), tags, types, {"opcServer": SERVER})
        apply_sim(p1, tags, types)
        # simulate an Ignition-side documentation edit that differs from the PLC comment
        node = _find_by_path(tags, self._first_commented(p1))
        node["documentation"] = "old text"
        p2 = X.plan(load_xsy(), tags, types, {"opcServer": SERVER})
        self.assertEqual(len(p2.tag_update), 1)
        p3_tags = apply_sim(p2, tags, types)[0]
        self.assertEqual(X.plan(load_xsy(), p3_tags, types, {"opcServer": SERVER}).tag_update, [])

    def test_blank_plc_comment_never_blanks_ignition_text(self):
        tags, types = [], []
        p1 = X.plan(load_xsy(), tags, types, {"opcServer": SERVER})
        apply_sim(p1, tags, types)
        blank = next(f + "/" + js["name"] for f, js in p1.tag_create if not js.get("documentation"))
        _find_by_path(tags, blank)["documentation"] = "written in Ignition"
        p2 = X.plan(load_xsy(), tags, types, {"opcServer": SERVER})
        self.assertEqual([u for u in p2.tag_update if u[0] == blank], [])

    def test_sync_documentation_off_leaves_docs_alone(self):
        tags, types = [], []
        p1 = X.plan(load_xsy(), tags, types, {"opcServer": SERVER})
        apply_sim(p1, tags, types)
        node = _find_by_path(tags, self._first_commented(p1))
        node["documentation"] = "keep me"
        p2 = X.plan(load_xsy(), tags, types,
                    {"opcServer": SERVER, "syncDocumentation": False})
        self.assertEqual(p2.tag_update, [])


class LiveExportTests(unittest.TestCase):
    """The live export holds line 056 (tags) with a DDT_Valve/Valve type; its folders stand in for a provider."""

    @classmethod
    def setUpClass(cls):
        tree = load_tags()["tags"]
        cls.tags_056 = folder(tree, "056")
        cls.types_056 = folder(tree, "_types_", "056")
        cls.p = X.plan(load_xsy(), cls.tags_056, cls.types_056, {"opcServer": "OPC_OSML"})

    def test_existing_type_is_extended_not_recreated(self):
        self.assertNotIn("Valve", [js["name"] for _, js in self.p.udt_create])

    def test_plan_is_consistent_with_counts(self):
        c = self.p.counts()
        self.assertEqual(c["tag_create"], len(self.p.tag_create))
        self.assertGreater(c["tag_create"] + c["exists"] + c["skipped"], 0)

    def test_unrelated_branches_are_not_touched(self):
        # new tags go to group folders; nothing is created in the folders that already exist
        groups = set(f for _, f in X.GROUPS) | {X.DEFAULT_GROUP}
        for fold, _ in self.p.tag_create:
            self.assertIn(fold.split("/")[0], groups)


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
        p = X.plan(MINI_XSY, [], [], {"opcServer": SERVER})
        udt = next(js for _, js in p.udt_create if js["name"] == "T_Motor")
        names = [t["name"] for t in udt["tags"]]
        self.assertIn("Mode", names)
        self.assertNotIn("Old_Member", names)
        diffs = " ".join(msg for _, msg in p.library)
        self.assertIn("Old_Member", diffs)

    def test_dt_maps_to_datetime(self):
        self.assertEqual(X._elem("DT"), "DateTime")


GENERIC_XSY = b"""<?xml version="1.0"?>
<VariablesExchangeFile>
  <DDTSource DDTName="T_Cell"><structure>
    <variables name="Open" typeName="BOOL"/>
    <variables name="Level" typeName="REAL"/>
  </structure></DDTSource>
  <DDTSource DDTName="T_Rack"><structure>
    <variables name="Cells" typeName="ARRAY[1..2] OF T_Cell"/>
    <variables name="Flags" typeName="ARRAY[1..3] OF BOOL"/>
    <variables name="Grid" typeName="ARRAY[1..2,1..2] OF INT"/>
    <variables name="Pairs" typeName="ARRAY[1..2,1..2] OF T_Cell"/>
  </structure></DDTSource>
  <DDTSource DDTName="T_Bad"><structure>
    <variables name="Timer" typeName="TON"/>
  </structure></DDTSource>
  <FBSource nameOfFBType="FB_Timer">
    <inputParameters><variables name="IN" typeName="BOOL"/></inputParameters>
    <outputParameters><variables name="Q" typeName="BOOL"/></outputParameters>
  </FBSource>
  <dataBlock>
    <variables name="Rack1" typeName="T_Rack"><attribute name="IsVariableHMI" value="-1"/></variables>
    <variables name="Cell_Arr" typeName="ARRAY[1..2] OF T_Cell"><attribute name="IsVariableHMI" value="-1"/></variables>
    <variables name="Matrix" typeName="ARRAY[1..2,1..3] OF REAL"><attribute name="IsVariableHMI" value="-1"/></variables>
    <variables name="Pairs" typeName="ARRAY[1..2,1..2] OF T_Cell"><attribute name="IsVariableHMI" value="-1"/></variables>
    <variables name="Timer1" typeName="FB_Timer"><attribute name="IsVariableHMI" value="-1"/></variables>
    <variables name="Bad1" typeName="T_Bad"><attribute name="IsVariableHMI" value="-1"/></variables>
  </dataBlock>
</VariablesExchangeFile>"""


GROUP_XSY = b"""<?xml version="1.0"?>
<VariablesExchangeFile>
  <DDTSource DDTName="T_Unknown"><structure><variables name="A" typeName="BOOL"/></structure></DDTSource>
  <DDTSource DDTName="DDT_Valve"><structure><variables name="Open" typeName="BOOL"/></structure></DDTSource>
  <dataBlock>
    <variables name="P101" typeName="T_Motor"><attribute name="IsVariableHMI" value="-1"/></variables>
    <variables name="XV1" typeName="DDT_Valve"><attribute name="IsVariableHMI" value="-1"/></variables>
    <variables name="Odd1" typeName="T_Unknown"><attribute name="IsVariableHMI" value="-1"/></variables>
    <variables name="Flag1" typeName="BOOL"><attribute name="IsVariableHMI" value="-1"/></variables>
    <variables name="Words" typeName="ARRAY[1..4] OF INT"><attribute name="IsVariableHMI" value="-1"/></variables>
    <variables name="XVs" typeName="ARRAY[1..2] OF DDT_Valve"><attribute name="IsVariableHMI" value="-1"/></variables>
  </dataBlock>
</VariablesExchangeFile>"""


def _udt(p, name):
    return next(js for _, js in p.udt_create if js["name"] == name)


def _tag(p, folder, name):
    return next(js for f, js in p.tag_create if f == folder and js["name"] == name)


class GenericTests(unittest.TestCase):
    """Any nesting of DDTs, FBs and arrays is handled by one rule."""

    @classmethod
    def setUpClass(cls):
        cls.p = X.plan(GENERIC_XSY, [], [], {"opcServer": SERVER})

    def test_array_of_udt_member_becomes_folder_of_instances(self):
        cells = next(t for t in _udt(self.p, "T_Rack")["tags"] if t["name"] == "Cells")
        self.assertEqual(cells["tagType"], "Folder")
        self.assertEqual([c["name"] for c in cells["tags"]], ["_1", "_2"])
        self.assertEqual(cells["tags"][0]["parameters"]["Tag"]["value"]["binding"], "{Tag}.Cells[1]")

    def test_elementary_array_member_is_one_array_tag(self):
        flags = next(t for t in _udt(self.p, "T_Rack")["tags"] if t["name"] == "Flags")
        self.assertEqual(flags["dataType"], "BooleanArray")
        self.assertEqual(flags["opcItemPath"]["binding"], "{OPC Prefix}{Tag}.{TagName}")

    def test_multidimensional_member_becomes_nested_folders(self):
        pairs = next(t for t in _udt(self.p, "T_Rack")["tags"] if t["name"] == "Pairs")
        inner = pairs["tags"][0]
        self.assertEqual(inner["tagType"], "Folder")
        self.assertEqual(inner["tags"][1]["parameters"]["Tag"]["value"]["binding"], "{Tag}.Pairs[1][2]")

    def test_multidimensional_elementary_array_is_folder_of_row_arrays(self):
        grid = next(t for t in _udt(self.p, "T_Rack")["tags"] if t["name"] == "Grid")
        self.assertEqual(grid["tagType"], "Folder")
        self.assertEqual([r["dataType"] for r in grid["tags"]], ["Int2Array", "Int2Array"])

    def test_fb_instance_becomes_udt_with_its_public_members(self):
        fb = _udt(self.p, "FB_Timer")
        self.assertEqual(sorted(t["name"] for t in fb["tags"]), ["IN", "Q"])

    def test_array_of_udt_top_level_is_folder_of_instances(self):
        self.assertEqual(_tag(self.p, "Other/Cell_Arr", "_2")["parameters"]["Tag"]["value"], "Cell_Arr[2]")

    def test_top_level_multidimensional_elementary_array(self):
        row = _tag(self.p, "Other/Matrix", "_2")
        self.assertEqual(row["dataType"], "Float4Array")
        self.assertEqual(row["opcItemPath"], "ns=2;s=0:Matrix[2]")

    def test_top_level_multidimensional_udt_array(self):
        self.assertEqual(_tag(self.p, "Other/Pairs/_2", "_2")["parameters"]["Tag"]["value"], "Pairs[2][2]")

    def test_udt_with_unbuildable_member_is_skipped_with_reason(self):
        self.assertIn("TON", " ".join(r for _, r in self.p.udt_skipped))
        self.assertIn("Bad1", [v for v, _ in self.p.skipped])
        self.assertNotIn("Bad1", [j["name"] for _, j in self.p.tag_create])

    def test_generic_rerun_changes_nothing(self):
        tags, types = [], []
        p1 = X.plan(GENERIC_XSY, tags, types, {"opcServer": SERVER})
        apply_sim(p1, tags, types)
        p2 = X.plan(GENERIC_XSY, tags, types, {"opcServer": SERVER})
        self.assertEqual(p2.udt_create, [])
        self.assertEqual(p2.udt_extend, [])
        self.assertEqual(p2.tag_create, [])
        self.assertTrue(p2.exists)

    def test_layout_file_supplies_type_missing_from_export(self):
        layout = b"""<?xml version="1.0"?><DDTExchangeFile>
          <DDTSource DDTName="T_Dev"><structure><variables name="CH1" typeName="BOOL"/></structure></DDTSource>
          </DDTExchangeFile>"""
        xsy = GENERIC_XSY.replace(b"</dataBlock>", b'<variables name="Dev1" typeName="T_Dev"><attribute name="IsVariableHMI" value="-1"/></variables></dataBlock>')
        p = X.plan(xsy, [], [], {"opcServer": SERVER, "layouts": [layout]})
        self.assertEqual([m["name"] for m in _udt(p, "T_Dev")["tags"]], ["CH1"])
        self.assertIn("Dev1", [j["name"] for _, j in p.tag_create])

    def test_layout_file_cannot_override_efclib(self):
        layout = b"""<?xml version="1.0"?><DDTExchangeFile>
          <DDTSource DDTName="T_Motor"><structure><variables name="Other" typeName="BOOL"/></structure></DDTSource>
          </DDTExchangeFile>"""
        p = X.plan(MINI_XSY, [], [], {"opcServer": SERVER, "layouts": [layout]})
        names = [t["name"] for t in _udt(p, "T_Motor")["tags"]]
        self.assertIn("Mode", names)


class GroupingTests(unittest.TestCase):
    """New tags are grouped into folders by UDT type name."""

    @classmethod
    def setUpClass(cls):
        cls.p = X.plan(GROUP_XSY, [], [], {"opcServer": SERVER})

    def test_motor_instance_lands_in_motors(self):
        self.assertEqual(_tag(self.p, "Motors", "P101")["typeId"], "T_Motor")

    def test_valve_instance_lands_in_valves(self):
        self.assertEqual(_tag(self.p, "Valves", "XV1")["typeId"], "DDT_Valve")

    def test_unknown_udt_lands_in_other(self):
        self.assertEqual(_tag(self.p, "Other", "Odd1")["typeId"], "T_Unknown")

    def test_atomic_tag_lands_in_other(self):
        self.assertEqual(_tag(self.p, "Other", "Flag1")["tagType"], "AtomicTag")

    def test_elementary_array_lands_in_other(self):
        self.assertEqual(_tag(self.p, "Other", "Words")["dataType"], "Int2Array")

    def test_array_of_udt_lands_in_group_name_i(self):
        self.assertEqual(_tag(self.p, "Valves/XVs", "_2")["parameters"]["Tag"]["value"], "XVs[2]")
        self.assertEqual(_tag(self.p, "Valves/XVs", "_1")["typeId"], "DDT_Valve")

    def test_default_groups_match_from_the_start_and_are_case_sensitive(self):
        g = [(re.compile(rx), f) for rx, f in X.GROUPS]

        def grp(n):
            return next((f for rx, f in g if rx.match(n)), X.DEFAULT_GROUP)
        self.assertEqual(grp("t_motor"), "Other")
        self.assertEqual(grp("XT_Motor"), "Other")
        self.assertEqual(grp("PV_Anything"), "Process Values")
        self.assertEqual(grp("Variables_Foo"), "Variables")

    def test_custom_groups_option_first_match_wins(self):
        groups = [(r"^T_Motor$", "First"), (r"^T_.*$", "Second")]
        p = X.plan(GROUP_XSY, [], [], {"opcServer": SERVER, "groups": groups})
        self.assertEqual(_tag(p, "First", "P101")["typeId"], "T_Motor")
        self.assertEqual(_tag(p, "Second", "Odd1")["typeId"], "T_Unknown")

    def test_rerun_places_nothing_twice(self):
        tags, types = [], []
        apply_sim(self.p, tags, types)
        p2 = X.plan(GROUP_XSY, tags, types, {"opcServer": SERVER})
        self.assertTrue(p2.is_noop())
        self.assertEqual(p2.skipped, [])
        self.assertEqual(p2.duplicates, [])

    def test_tag_moved_by_hand_is_still_found(self):
        tags, types = [], []
        apply_sim(self.p, tags, types)
        motors = next(n for n in tags if n["name"] == "Motors")
        node = motors["tags"].pop(0)
        tags.append({"name": "ByHand", "tagType": "Folder", "tags": [node]})
        p2 = X.plan(GROUP_XSY, tags, types, {"opcServer": SERVER})
        self.assertEqual([j["name"] for _, j in p2.tag_create], [])
        self.assertIn("P101", [e for e, _ in p2.exists])
        self.assertEqual(p2.duplicates, [])

    def test_name_clash_is_per_group_folder(self):
        # an unrelated atomic tag named XV1 in Valves blocks the instance; the same name elsewhere does not
        tags = [{"name": "Valves", "tagType": "Folder", "tags": [
                    {"name": "XV1", "tagType": "AtomicTag", "opcItemPath": "ns=2;s=0:Other", "dataType": "Boolean"}]},
                {"name": "Motors", "tagType": "Folder", "tags": [
                    {"name": "Odd1", "tagType": "AtomicTag", "opcItemPath": "ns=2;s=0:Other2", "dataType": "Boolean"}]}]
        p = X.plan(GROUP_XSY, tags, [], {"opcServer": SERVER})
        self.assertIn("XV1", [v for v, _ in p.skipped])
        self.assertIn("Odd1", [j["name"] for _, j in p.tag_create])

    def test_existing_folder_with_array_name_is_not_a_clash(self):
        tags = [{"name": "Valves", "tagType": "Folder", "tags": [{"name": "XVs", "tagType": "Folder", "tags": []}]}]
        p = X.plan(GROUP_XSY, tags, [], {"opcServer": SERVER})
        self.assertNotIn("XVs", [v for v, _ in p.skipped])


if __name__ == "__main__":
    unittest.main()
