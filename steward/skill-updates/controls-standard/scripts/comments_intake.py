#!/usr/bin/env python3
"""Extract reviewer comments from a marked-up .docx or .pdf into review-comments.csv.
Appends to the CSV (keeps existing rows). Prints only a summary line.

Usage: python3 scripts/comments_intake.py <file.docx|file.pdf> [reviewer-name]
Columns: id, source, location, author, anchor, comment, status, response
docx: location = nearest heading, anchor = commented text.
pdf:  location = page number, anchor = highlighted text when available.
"""
import csv, os, re, sys, zipfile, xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
OUT = "review-comments.csv"

def docx(path):
    z = zipfile.ZipFile(path)
    if "word/comments.xml" not in z.namelist():
        return []
    com = {}
    for c in ET.fromstring(z.read("word/comments.xml")).iter(W + "comment"):
        com[c.get(W + "id")] = (c.get(W + "author", ""),
                                " ".join(t.text or "" for t in c.iter(W + "t")).strip())
    body = ET.fromstring(z.read("word/document.xml"))
    anchors, heading, loc, open_ = {}, "", {}, set()
    for p in body.iter(W + "p"):
        sty = p.find(f"{W}pPr/{W}pStyle")
        ptxt = "".join(t.text or "" for t in p.iter(W + "t")).strip()
        if sty is not None and "heading" in (sty.get(W + "val") or "").lower() and ptxt:
            heading = ptxt[:60]
        for el in p.iter():
            tag = el.tag
            if tag == W + "commentRangeStart":
                i = el.get(W + "id"); open_.add(i); anchors[i] = ""; loc[i] = heading
            elif tag == W + "commentRangeEnd":
                open_.discard(el.get(W + "id"))
            elif tag == W + "t" and el.text:
                for i in open_: anchors[i] += el.text
            elif tag == W + "commentReference":
                loc.setdefault(el.get(W + "id"), heading)
    return [(loc.get(i, ""), a, (anchors.get(i, "") or "")[:200], t) for i, (a, t) in com.items()]

def pdf(path):
    from pypdf import PdfReader
    rows = []
    for n, page in enumerate(PdfReader(path).pages, 1):
        for ref in page.get("/Annots") or []:
            a = ref.get_object()
            txt = a.get("/Contents")
            if a.get("/Subtype") in ("/Link", "/Popup") or not txt:
                continue
            rows.append((f"p.{n}", str(a.get("/T", "")), "", str(txt).strip()))
    return rows

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    who = sys.argv[2] if len(sys.argv) > 2 else ""
    rows = docx(path) if path.lower().endswith(".docx") else pdf(path)
    exists = os.path.exists(OUT)
    start = 0
    if exists:
        with open(OUT, encoding="utf-8") as h:
            start = sum(1 for _ in h) - 1
    with open(OUT, "a", newline="", encoding="utf-8") as h:
        w = csv.writer(h)
        if not exists:
            w.writerow(["id", "source", "location", "author", "anchor", "comment", "status", "response"])
        for k, (loc, author, anchor, text) in enumerate(rows, start + 1):
            w.writerow([f"RC-{k:03d}", os.path.basename(path), loc, author or who,
                        re.sub(r"\s+", " ", anchor), re.sub(r"\s+", " ", text), "open", ""])
    print(f"{len(rows)} comment(s) from {os.path.basename(path)} -> {OUT}")

if __name__ == "__main__":
    main()
