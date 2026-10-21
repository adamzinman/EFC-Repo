#!/usr/bin/env python3
"""st2xdb - build a Control Expert Classic V16.2 DFB exchange file (.XDB) from
an interface definition (types/dfb/src/<DFB>.iface.yaml) and an ST body
(types/dfb/src/<DFB>.st).

Format source: types/dfb/_reference/XDB_FORMAT_REFERENCE.md (binding) and the
raw export types/dfb/_reference/DFB_Device.XDB. Items the reference marks as
not demonstrated are behind switches and reported on every run.

Usage:
    python3 tools/st2xdb.py FB_AlmCore            # build types/dfb/FB_AlmCore.XDB
    python3 tools/st2xdb.py --all                 # build every src/*.iface.yaml
    python3 tools/st2xdb.py FB_AlmCore --check    # lint + checks only, no write

Exit code 1 if any lint or file check fails (nothing is written).
"""
import argparse
import datetime
import os
import re
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DFB_DIR = os.path.join(ROOT, "types", "dfb")
SRC_DIR = os.path.join(DFB_DIR, "src")
XDD_DIR = os.path.join(ROOT, "types", "xdd")
REF_XDB = os.path.join(DFB_DIR, "_reference", "DFB_Device.XDB")

CRLF = "\r\n"
TAB = "\t"

# Constants copied from the reference export (XDB_FORMAT_REFERENCE.md sections 2 and 9).
FILE_HEADER = ('<fileHeader company="Schneider Automation" product="Control Expert V16.2 - 250430" '
               'dateTime="date_and_time#{dt}" content="Function Block source file" DTDVersion="41"></fileHeader>')
# Sample checksum values, used only with --checksums copy.
SAMPLE_CODE_CS = "088A"
SAMPLE_SIG_CS = "FB2C"
SAMPLE_DDT_SIG_CS = "40A7"

ELEMENTARY = {"BOOL", "INT", "DINT", "UINT", "UDINT", "WORD", "DWORD", "BYTE", "REAL", "LREAL",
              "TIME", "DT", "DATE", "TOD", "STRING"}
STD_FBS = {"TON", "TOF", "TP", "R_TRIG", "F_TRIG", "CTU", "CTD", "CTUD", "SR", "RS"}
# Element types the reference export demonstrates; anything else is reported as unverified.
VERIFIED_TYPES = {"BOOL", "INT", "REAL", "TON", "TOF"}

ST_KEYWORDS = {"IF", "THEN", "ELSIF", "ELSE", "END_IF", "CASE", "OF", "END_CASE", "FOR", "TO", "BY",
               "DO", "END_FOR", "WHILE", "END_WHILE", "REPEAT", "UNTIL", "END_REPEAT", "EXIT",
               "RETURN", "AND", "OR", "XOR", "NOT", "MOD", "TRUE", "FALSE"}
# Standard / Control Expert functions the ST may call. Flagged ones need a 16.2 library check.
ST_FUNCTIONS = {"ABS", "SQRT", "MIN", "MAX", "LIMIT", "SEL", "SHL", "SHR", "TRUNC",
                "INT_TO_REAL", "DINT_TO_REAL", "UDINT_TO_REAL", "REAL_TO_INT", "REAL_TO_DINT",
                "REAL_TO_LREAL", "LREAL_TO_REAL", "INT_TO_DINT", "DINT_TO_INT", "INT_TO_WORD",
                "TIME_TO_DINT", "DINT_TO_TIME"}
ST_FUNCTIONS_FLAG = {"TIME_TO_DINT", "DINT_TO_TIME", "RRTC_DT"}
ST_FUNCTIONS |= ST_FUNCTIONS_FLAG
BLOCKS = [("IF", "END_IF"), ("CASE", "END_CASE"), ("FOR", "END_FOR"),
          ("WHILE", "END_WHILE"), ("REPEAT", "END_REPEAT")]
MAX_ID = 32


# ---------------------------------------------------------------- interface

def load_iface(name):
    path = os.path.join(SRC_DIR, name + ".iface.yaml")
    with open(path, encoding="utf-8") as f:
        d = yaml.safe_load(f)
    for key in ("inputs", "outputs", "inouts", "public", "private"):
        d[key] = d.get(key) or []
        for v in d[key]:
            v["type"] = str(v["type"]).strip()
    d.setdefault("version", "1.00")
    d.setdefault("sections", [{"name": "Main", "file": name + ".st"}])
    return d


def assign_pins(d):
    """PositionPin: one 1-based sequence, in-outs first, then inputs, then outputs.
    An explicit `pin:` in the yaml wins."""
    n = 0
    for key in ("inouts", "inputs", "outputs"):
        for v in d[key]:
            n += 1
            v.setdefault("pin", n)
    pins = [v["pin"] for k in ("inouts", "inputs", "outputs") for v in d[k]]
    if len(pins) != len(set(pins)):
        raise SystemExit("duplicate PositionPin in " + d["name"])


# ---------------------------------------------------------------- DDTs

def read_xdd(type_name):
    """Members (name, typeName), version and dateTime of a T_ type from types/xdd/."""
    path = os.path.join(XDD_DIR, type_name + ".xdd")
    root = ET.parse(path).getroot()
    src = root.find("DDTSource")
    members = [(v.get("name"), v.get("typeName")) for v in src.find("structure").findall("variables")]
    return {"name": type_name, "version": src.get("version"), "dateTime": src.get("dateTime"),
            "members": members}


def base_type(t):
    m = re.match(r"ARRAY\s*\[.*\]\s*OF\s+(.+)$", t, re.I)
    t = m.group(1) if m else t
    return re.sub(r"\[.*\]$", "", t).strip()  # STRING[20] -> STRING


def is_ddt(t):
    return os.path.exists(os.path.join(XDD_DIR, base_type(t) + ".xdd"))


def ddts_used(d):
    """Every DDT used by the DFB's variables, nested ones included, inner types first."""
    order, seen = [], set()

    def visit(t):
        t = base_type(t)
        if t in seen or not is_ddt(t):
            return
        seen.add(t)
        info = read_xdd(t)
        for _, mt in info["members"]:
            visit(mt)
        order.append(info)

    for key in ("inouts", "inputs", "outputs", "public", "private"):
        for v in d[key]:
            visit(v["type"])
    return order


# ---------------------------------------------------------------- ST lint

def strip_comments(st):
    return re.sub(r"\(\*.*?\*\)", " ", st, flags=re.S)


def lint_st(d, body):
    """Returns (errors, warnings)."""
    errs, warns = [], []
    code = strip_comments(body)
    code = re.sub(r"'[^']*'", " ", code)                      # string literals
    code_nolit = re.sub(r"\b\w+#[\w.#:]+", " 0 ", code)         # T#5S, 16#FF, WORD#16#1
    up = code_nolit.upper()

    if "%" in code:
        errs.append("located / system address ('%') in ST")
    if "(*" in strip_comments(body) or "*)" in strip_comments(body):
        errs.append("unbalanced comment")
    for open_kw, close_kw in BLOCKS:
        n_open = len(re.findall(r"(?<![\w])" + open_kw + r"(?![\w])", up))
        n_close = len(re.findall(r"(?<![\w])" + close_kw + r"(?![\w])", up))
        if n_open != n_close:
            errs.append("unbalanced %s/%s: %d vs %d" % (open_kw, close_kw, n_open, n_close))
        for m in re.finditer(r"(?<![\w])" + close_kw + r"(?![\w])\s*(.)", up):
            if m.group(1) != ";":
                errs.append(close_kw + " not followed by ';'")
                break
    if "?" in code_nolit:
        errs.append("'?' found (no inline conditionals)")

    declared = {}
    for key in ("inputs", "outputs", "inouts", "public", "private"):
        for v in d[key]:
            declared[v["name"].upper()] = v
            if len(v["name"]) > MAX_ID:
                errs.append("identifier > 32 chars: " + v["name"])
    if len(d["name"]) > MAX_ID:
        errs.append("DFB name > 32 chars")

    used = set()
    tokens = list(re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", code_nolit))
    depth_at = []
    depth = 0
    for i, ch in enumerate(code_nolit):
        depth_at.append(depth)
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
    for m in tokens:
        tok = m.group(0)
        tu = tok.upper()
        before = code_nolit[:m.start()].rstrip()
        after = code_nolit[m.end():].lstrip()
        if before.endswith("."):
            continue                                            # member access
        if tu in ST_KEYWORDS:
            continue
        if depth_at[m.start()] > 0 and (after.startswith(":=") or after.startswith("=>")):
            continue                                            # formal parameter name in a call
        if after.startswith("("):
            if tu in declared:
                used.add(tu)                                    # FB instance call
            elif tu in ST_FUNCTIONS:
                if tu in ST_FUNCTIONS_FLAG:
                    warns.append("function %s: confirm it exists in the 16.2 library" % tu)
            else:
                errs.append("unknown function or undeclared FB instance: " + tok)
            continue
        if tu in declared:
            used.add(tu)
        else:
            errs.append("undeclared identifier: " + tok)
    for name, v in declared.items():
        if name not in used:
            errs.append("declared but not used: " + v["name"])
    return sorted(set(errs)), sorted(set(warns))


# ---------------------------------------------------------------- XML writer

def attr(s):
    return escape(str(s), {'"': "&quot;"})


def fmt_header_dt(t):
    return "%d-%d-%d-%d:%d:%d" % (t.year, t.month, t.day, t.hour, t.minute, t.second)


def fmt_source_dt(t):
    return t.strftime("dt#%Y-%m-%d-%H:%M:%S")


def var_lines(v, indent, with_pin, opts):
    o = indent + '<variables name="%s" typeName="%s">' % (attr(v["name"]), attr(v["type"]))
    children = []
    if with_pin:
        children.append(indent + TAB + '<attribute name="PositionPin" value="%d"></attribute>' % v["pin"])
    if opts.var_comments and v.get("comment"):                        # UNVERIFIED element
        children.append(indent + TAB + "<comment>%s</comment>" % escape(v["comment"]))
    if not children:
        return [o + "</variables>"]
    return [o] + children + [indent + "</variables>"]


def build_xdb(d, bodies, ddts, opts, now):
    L = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', "<FBExchangeFile>"]
    L.append(TAB + FILE_HEADER.format(dt=fmt_header_dt(now)))
    L.append(TAB + '<contentHeader name="%s" version="%s" dateTime="date_and_time#%s"></contentHeader>'
             % (attr(opts.project_name), attr(opts.project_version), fmt_header_dt(now)))
    L.append(TAB + '<FBSource nameOfFBType="%s" version="%s" dateTime="%s">'
             % (attr(d["name"]), attr(d["version"]), fmt_source_dt(now)))
    if opts.checksums != "omit":
        code_cs, sig_cs = (SAMPLE_CODE_CS, SAMPLE_SIG_CS) if opts.checksums == "copy" else \
            (d.get("code_checksum", ""), d.get("sig_checksum", ""))
        L.append(TAB * 2 + '<attribute name="TypeCodeCheckSumString" value="%s"></attribute>' % code_cs)
        L.append(TAB * 2 + '<attribute name="TypeSignatureCheckSumString" value="%s"></attribute>' % sig_cs)
    L.append(TAB * 2 + '<attribute name="UseNewTplSignAlgo" value="TRUE"></attribute>')

    def block(tag, items, with_pin):
        if not items:
            return
        L.append(TAB * 2 + "<%s>" % tag)
        for v in items:
            L.extend(var_lines(v, TAB * 3, with_pin, opts))
        L.append(TAB * 2 + "</%s>" % tag)

    block("inputParameters", d["inputs"], True)
    if opts.outputs_pos == "after-inputs":
        block("outputParameters", d["outputs"], True)                  # UNVERIFIED element
    block("inOutParameters", d["inouts"], True)
    if opts.outputs_pos == "after-inout":
        block("outputParameters", d["outputs"], True)
    block("publicLocalVariables", d["public"], False)
    block("privateLocalVariables", d["private"], False)

    for sec, body in bodies:
        L.append(TAB * 2 + '<FBProgram name="%s">' % attr(sec))
        L.append(TAB * 3 + "<STSource>")
        L.extend(escape(line) for line in body)
        L.append("</STSource>")
        L.append(TAB * 2 + "</FBProgram>")
    L.append(TAB + "</FBSource>")

    for t in ddts:
        L.append(TAB + '<DDTSource DDTName="%s" version="%s" dateTime="%s">'
                 % (attr(t["name"]), attr(t["version"]), attr(t["dateTime"])))
        if opts.checksums == "copy":
            L.append(TAB * 2 + '<attribute name="TypeSignatureCheckSumString" value="%s"></attribute>'
                     % SAMPLE_DDT_SIG_CS)
        L.append(TAB * 2 + "<structure>")
        for n, ty in t["members"]:
            L.append(TAB * 3 + '<variables name="%s" typeName="%s"></variables>' % (attr(n), attr(ty)))
        L.append(TAB * 2 + "</structure>")
        L.append(TAB + "</DDTSource>")
    L.append("</FBExchangeFile>")
    return CRLF.join(L) + CRLF


def read_body(path):
    with open(path, encoding="ascii") as f:          # non-ASCII is an error (reference: ASCII file)
        text = f.read()
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    for ln in lines:
        if re.match(r" +\S", ln):
            raise SystemExit("%s: indent with tabs, not spaces: %r" % (path, ln))
    return lines


# ---------------------------------------------------------------- checks

def file_checks(data):
    errs = []
    try:
        data.decode("ascii")
    except UnicodeDecodeError:
        errs.append("non-ASCII byte")
    if data.startswith(b"\xef\xbb\xbf"):
        errs.append("BOM")
    if not data.endswith(b"\r\n"):
        errs.append("last line not CRLF-terminated")
    if re.search(rb"(?<!\r)\n", data):
        errs.append("bare LF line ending")
    if re.search(rb"/>", data):
        errs.append("self-closing tag")
    if re.search(rb"<!\[CDATA\[", data):
        errs.append("CDATA")
    for ln in data.split(b"\r\n"):
        if re.match(rb"\t* +", ln) and not ln.strip() == b"":
            errs.append("space indentation")
            break
        if ln != ln.rstrip():
            errs.append("trailing whitespace")
            break
    try:
        ET.fromstring(data)
    except ET.ParseError as e:
        errs.append("XML parse error: %s" % e)
    return errs


def signature(root):
    """Set of (element path, sorted attribute names) - the structure, not the values."""
    sig = set()

    def walk(e, path):
        p = path + "/" + e.tag
        sig.add((p, tuple(sorted(e.attrib))))
        for c in e:
            walk(c, p)
    walk(root, "")
    return sig


def structural_diff(data):
    ref = signature(ET.parse(REF_XDB).getroot())
    gen = signature(ET.fromstring(data))
    ld = {s for s in ref if "LDSource" in s[0]}                   # LD sections are never generated
    missing = sorted(ref - gen - ld)
    extra = sorted(gen - ref)
    return missing, extra


def unverified_items(d, ddts, opts, body=""):
    items = []
    if "(*" in body:
        items.append("ST comments (* *)")
    if re.search(r"\b\w+#", strip_comments(body)):
        items.append("typed literals (T#..., 16#...)")
    for ch, name in (("<", "'<' (&lt;)"), (">", "'>' (&gt;)"), ("&", "'&' (&amp;)")):
        if ch in strip_comments(body) and ch != "<":
            items.append("ST contains " + name)
    if d["outputs"]:
        items.append("outputParameters block (position: %s)" % opts.outputs_pos)
    if opts.checksums == "omit":
        items.append("checksum attributes omitted")
    if opts.var_comments:
        items.append("<comment> on variables")
    types = {base_type(v["type"]) for k in ("inputs", "outputs", "inouts", "public", "private") for v in d[k]}
    for t in ddts:
        types |= {base_type(mt) for _, mt in t["members"]}
        if any(is_ddt(mt) for _, mt in t["members"]):
            items.append("DDT nested in DDT (%s)" % t["name"])
        if any("ARRAY" in mt.upper() for _, mt in t["members"]):
            items.append("ARRAY member (%s)" % t["name"])
    for t in sorted(types - VERIFIED_TYPES):
        if not is_ddt(t):
            items.append("type not in the sample: " + t)
    user_fbs = [v["name"] for v in d["private"] + d["public"]
                if base_type(v["type"]) not in ELEMENTARY | STD_FBS and not is_ddt(v["type"])]
    if user_fbs:
        items.append("user DFB instances: " + ", ".join(user_fbs))
    return items


# ---------------------------------------------------------------- main

def build(name, opts):
    d = load_iface(name)
    assign_pins(d)
    bodies, ok = [], True
    for sec in d["sections"]:
        body = read_body(os.path.join(SRC_DIR, sec["file"]))
        bodies.append((sec["name"], body))
    errs, warns = lint_st(d, "\n".join(ln for _, b in bodies for ln in b))
    ddts = [] if opts.no_ddt else ddts_used(d)
    now = opts.now or datetime.datetime.now().replace(microsecond=0)
    data = build_xdb(d, [(n, b) for n, b in bodies], ddts, opts, now).encode("ascii")
    ferrs = file_checks(data)
    missing, extra = structural_diff(data) if not ferrs else ([], [])

    print("== %s" % name)
    for e in errs:
        print("  LINT ERROR  " + e)
    for w in warns:
        print("  LINT WARN   " + w)
    for e in ferrs:
        print("  FILE ERROR  " + e)
    for p, a in missing:
        print("  STRUCT      not used (vs reference): %s %s" % (p, list(a)))
    for p, a in extra:
        print("  STRUCT      new (vs reference):      %s %s" % (p, list(a)))
    for u in unverified_items(d, ddts, opts, "\n".join(ln for _, b in bodies for ln in b)):
        print("  UNVERIFIED  " + u)
    if errs or ferrs:
        print("  FAILED - nothing written")
        return False
    if not opts.check:
        out = os.path.join(opts.out_dir or DFB_DIR, name + ".XDB")
        with open(out, "wb") as f:
            f.write(data)
        print("  wrote %s (%d bytes, %d DDTs embedded)" % (os.path.relpath(out, ROOT), len(data), len(ddts)))
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="DFB names (types/dfb/src/<name>.iface.yaml)")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--check", action="store_true", help="lint and check only, do not write")
    ap.add_argument("--checksums", choices=["omit", "copy", "value"], default="omit",
                    help="omit (default, try first) | copy sample values | value from iface code_checksum/sig_checksum")
    ap.add_argument("--outputs-pos", choices=["after-inputs", "after-inout"], default="after-inputs",
                    help="position of the unverified outputParameters block")
    ap.add_argument("--no-ddt", action="store_true", help="do not embed DDTSource blocks")
    ap.add_argument("--var-comments", action="store_true", help="emit <comment> on variables (unverified)")
    ap.add_argument("--out-dir", help="write here instead of types/dfb/ (pilot variants)")
    ap.add_argument("--project-name", default="EFCLib")
    ap.add_argument("--project-version", default="1.0.0")
    ap.add_argument("--now", type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S"),
                    help="fixed timestamp YYYY-MM-DDTHH:MM:SS (reproducible output)")
    opts = ap.parse_args()
    names = opts.names
    if opts.all:
        names = sorted(f[:-len(".iface.yaml")] for f in os.listdir(SRC_DIR) if f.endswith(".iface.yaml"))
    if not names:
        ap.error("give DFB names or --all")
    ok = all([build(n, opts) for n in names])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
