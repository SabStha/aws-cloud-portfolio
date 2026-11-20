#!/usr/bin/env bash
# check.sh - one command that runs every test and prints a single PASS/FAIL board.
#
#   ./check.sh          local checks only (fast, free: no AWS, no model calls)
#   ./check.sh --aws    also run the live evidence pipeline (51 model calls)
#
# Exit 0 if every HARD check passed, 1 if any failed. Soft checks only report.
set -u
cd "$(dirname "$0")"
[ -f .venv/bin/activate ] && source .venv/bin/activate

PY=python
FAIL=0
ROWS=()

row() { ROWS+=("$1|$2|$3"); }           # name | PASS/FAIL/SKIP/INFO | detail

# --- run a tool, capture output, or mark SKIP if the tool is missing ---------
run() { [ -f "$1" ] && $PY "$@" 2>/dev/null; }

# 1. TRIAGE CASES (hard: must be 30/30) ---------------------------------------
if [ -f score_triage.py ]; then
  OUT=$(run score_triage.py triage)
  SC=$(echo "$OUT" | grep -oE 'SCORE: [0-9]+/[0-9]+' | head -1 | grep -oE '[0-9]+/[0-9]+')
  if [ "${SC%%/*}" = "${SC##*/}" ] && [ -n "$SC" ]; then row "triage cases" PASS "$SC"
  else row "triage cases" FAIL "${SC:-no score}"; FAIL=1; fi
  QP=$(echo "$OUT" | grep -oE '\([0-9.]+ per inquiry\)' | grep -oE '[0-9.]+' | head -1)
  [ -n "$QP" ] && row "  questions/inquiry" INFO "$QP"
else row "triage cases" SKIP "score_triage.py missing"; fi

# 2. BASELINE (soft: report the contrast) -------------------------------------
if [ -f score_triage.py ] && [ -f baseline.py ]; then
  OUT=$(run score_triage.py baseline)
  SC=$(echo "$OUT" | grep -oE 'SCORE: [0-9]+/[0-9]+' | head -1 | grep -oE '[0-9]+/[0-9]+')
  row "  vs fixed checklist" INFO "${SC:-n/a}"
fi

# 3. INQUIRY-BOOK COVERAGE (soft: report %, warn under 85) --------------------
if [ -f build_inquiry_book.py ] && [ -f test_book.py ]; then
  run build_inquiry_book.py >/dev/null
  OUT=$(run test_book.py)
  PCT=$(echo "$OUT" | grep -oE 'recognised.*\([0-9]+%\)' | grep -oE '[0-9]+%' | head -1)
  N=$(echo "$OUT" | grep -oE 'inquiry book: [0-9]+' | grep -oE '[0-9]+' | head -1)
  if [ -n "$PCT" ]; then
    [ "${PCT%\%}" -ge 85 ] && row "coverage" PASS "$PCT of ${N:-?} qs" || row "coverage" INFO "$PCT of ${N:-?} qs (<85)"
  else row "coverage" SKIP "no result"; fi
else row "coverage" SKIP "book tools missing"; fi

# 4. KNOWLEDGE BASE (soft: report counts) -------------------------------------
if [ -f extract_kb.py ] && [ -f lsc_build/chunks.json ]; then
  run extract_kb.py >/dev/null
  REL=$($PY -c "import json;print(len(json.load(open('lsc_build/version_timeline.json'))['versions']))" 2>/dev/null)
  PAR=$($PY -c "import json;print(json.load(open('lsc_build/parser_catalog.json'))['count'])" 2>/dev/null)
  row "knowledge base" INFO "${REL:-?} releases, ${PAR:-?} parsers"
else row "knowledge base" SKIP "no local KB"; fi

# 5. EVIDENCE PIPELINE (hard, only with --aws) --------------------------------
if [ "${1:-}" = "--aws" ]; then
  if [ -f pipeline.py ]; then
    OUT=$(run pipeline.py)
    SC=$(echo "$OUT" | grep -oE 'Score: [0-9]+ / [0-9]+' | grep -oE '[0-9]+ / [0-9]+' | head -1)
    A=$(echo "$SC" | grep -oE '^[0-9]+'); B=$(echo "$SC" | grep -oE '[0-9]+$')
    if [ -n "$A" ] && [ "$A" = "$B" ]; then row "evidence pipeline (AWS)" PASS "$A/$B"
    else row "evidence pipeline (AWS)" FAIL "${SC:-no score}"; FAIL=1; fi
  else row "evidence pipeline (AWS)" SKIP "pipeline.py missing"; fi
else
  row "evidence pipeline (AWS)" SKIP "run with --aws to include"
fi

# --- print the board ---------------------------------------------------------
echo
echo "  EvidenceDesk self-check           $(date '+%Y-%m-%d %H:%M')"
echo "  ---------------------------------------------------------"
for r in "${ROWS[@]}"; do
  IFS='|' read -r name stat det <<< "$r"
  case "$stat" in
    PASS) mark="  OK  ";; FAIL) mark=" FAIL ";; SKIP) mark=" skip ";; INFO) mark="      ";;
  esac
  printf "  %s %-28s %s\n" "$mark" "$name" "$det"
done
echo "  ---------------------------------------------------------"
if [ "$FAIL" = 0 ]; then echo "  RESULT: all hard checks passed"; else echo "  RESULT: SOMETHING FAILED (see FAIL above)"; fi
echo
exit $FAIL
