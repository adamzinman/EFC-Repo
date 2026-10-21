#!/usr/bin/env bash
# Redline PDF of changes since a release tag (default: latest rev-* tag).
# Usage: bash scripts/redline.sh [rev-H]   -> redline-<tag>-to-HEAD.pdf
# Needs latexdiff and latexmk. Prints only the output path or the error.
set -euo pipefail
TAG="${1:-$(git tag --list 'rev-*' --sort=-creatordate | head -1)}"
[ -z "$TAG" ] && { echo "no rev-* tag found"; exit 2; }
command -v latexdiff-vc >/dev/null || { echo "latexdiff not installed (apt-get install latexdiff)"; exit 2; }
latexdiff-vc --git --flatten --force -r "$TAG" main.tex >/dev/null 2>&1
DIFF="main-diff${TAG}.tex"
latexmk -pdf -interaction=nonstopmode -quiet "$DIFF" >/dev/null 2>&1 || { echo "build failed: check ${DIFF%.tex}.log"; exit 1; }
OUT="redline-${TAG}-to-HEAD.pdf"
mv "${DIFF%.tex}.pdf" "$OUT"
latexmk -C -quiet "$DIFF" >/dev/null 2>&1 || true
rm -f "$DIFF"
echo "$OUT"
