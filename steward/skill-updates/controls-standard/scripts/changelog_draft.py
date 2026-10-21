#!/usr/bin/env python3
"""Draft a CHANGELOG entry from git history since the last rev-* tag.
Usage: python3 scripts/changelog_draft.py <new-rev-letter>
Prints a short markdown block to review and paste into CHANGELOG.md.
"""
import csv, io, re, subprocess, sys, datetime

def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True).stdout

def items(text):
    try:
        return {r["id"]: r for r in csv.DictReader(io.StringIO(text))}
    except Exception:
        return {}

def main():
    rev = sys.argv[1] if len(sys.argv) > 1 else "?"
    tags = git("tag", "--list", "rev-*", "--sort=-creatordate").split()
    base = tags[0] if tags else git("rev-list", "--max-parents=0", "HEAD").strip()
    print(f"## Rev {rev} ({datetime.date.today()}) - changes since {base}\n")
    print("### Chapters changed")
    for l in git("diff", "--numstat", f"{base}..HEAD", "--", "chapters").splitlines():
        a, d, f = l.split("\t")
        print(f"- {f.split('/')[-1]} (+{a}/-{d})")
    old = items(git("show", f"{base}:open-items.csv"))
    new = items(open("open-items.csv", encoding="utf-8").read())
    closed = [r for k, r in new.items() if r.get("status") == "closed"
              and old.get(k, {}).get("status") != "closed"]
    deferred = [r for r in new.values() if r.get("status") == "deferred"]
    added = [r for k, r in new.items() if k not in old]
    if closed:
        print("\n### Decisions")
        for r in closed: print(f"- {r['id']}: {r.get('decision','').strip() or '(decision missing)'}")
    if added:
        print("\n### New open items")
        for r in added: print(f"- {r['id']}: {r.get('question','').strip()}")
    if deferred:
        print("\n### Deferred")
        for r in deferred: print(f"- {r['id']} -> Rev {r.get('target_rev','?')}")
    subj = [s for s in git("log", "--format=%s", f"{base}..HEAD").splitlines() if s]
    if subj:
        print(f"\n<!-- {len(subj)} commit(s); edit the bullets above, this comment is not part of the entry -->")

if __name__ == "__main__":
    main()
