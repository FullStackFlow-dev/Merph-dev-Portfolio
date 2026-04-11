#!/usr/bin/env bash
# Tests for the bash validation script embedded in the 'validate' job of
# .github/workflows/ci-cd.yml.
#
# Changes in scope (PR diff):
#   - "notebooks/README.md" replaces "notes/README.md" in required_files
#   - Error message: "❌ Validation failed" (dropped "— missing files" suffix)
#   - Success message: "✅ Structure OK" (was "✅ All structure is valid")
#
# Uses plain bash assertions; no external framework required.

set -uo pipefail

PASS=0
FAIL=0

pass() { echo "PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $1"; FAIL=$((FAIL + 1)); }

# ---------------------------------------------------------------------------
# The exact validation logic extracted from the workflow step
# ---------------------------------------------------------------------------
run_validation() {
  local dir="$1"
  (
    cd "$dir"
    required_files=(
      "README.md"
      "learning-paths/cybersecurity.md"
      "learning-paths/ai-ml.md"
      "learning-paths/devops-cloud.md"
      "learning-paths/web-fullstack.md"
      "learning-paths/git-github.md"
      "certifications/README.md"
      "notebooks/README.md"
      "models/README.md"
      "docs/ROADMAP.md"
    )
    all_ok=true
    for file in "${required_files[@]}"; do
      if [ ! -f "$file" ]; then
        echo "❌ MISSING: $file"
        all_ok=false
      else
        echo "✅ OK: $file"
      fi
    done
    if [ "$all_ok" = false ]; then
      echo "❌ Validation failed"
      exit 1
    fi
    echo "✅ Structure OK"
  )
}

# ---------------------------------------------------------------------------
# Helper: run validation and capture exit code without triggering set -e
# ---------------------------------------------------------------------------
capture_exit() {
  # Usage: capture_exit <dir>
  # Sets global RUN_OUTPUT and RUN_EXIT
  set +e
  RUN_OUTPUT=$(run_validation "$1" 2>&1)
  RUN_EXIT=$?
  set -e
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
make_full_project() {
  local dir="$1"
  mkdir -p "$dir/learning-paths" \
           "$dir/certifications" \
           "$dir/notebooks" \
           "$dir/models" \
           "$dir/docs"
  touch "$dir/README.md"
  touch "$dir/learning-paths/cybersecurity.md"
  touch "$dir/learning-paths/ai-ml.md"
  touch "$dir/learning-paths/devops-cloud.md"
  touch "$dir/learning-paths/web-fullstack.md"
  touch "$dir/learning-paths/git-github.md"
  touch "$dir/certifications/README.md"
  touch "$dir/notebooks/README.md"
  touch "$dir/models/README.md"
  touch "$dir/docs/ROADMAP.md"
}

# ---------------------------------------------------------------------------
# TEST 1: All required files present → exits 0 and prints success message
# ---------------------------------------------------------------------------
tmp=$(mktemp -d)
make_full_project "$tmp"
capture_exit "$tmp"
rm -rf "$tmp"

if [[ $RUN_EXIT -eq 0 ]]; then
  pass "all files present: exits 0"
else
  fail "all files present: expected exit 0, got $RUN_EXIT"
fi

if echo "$RUN_OUTPUT" | grep -q "✅ Structure OK"; then
  pass "all files present: prints '✅ Structure OK'"
else
  fail "all files present: success message not found in output"
fi

# ---------------------------------------------------------------------------
# TEST 2: notebooks/README.md required (not notes/README.md)
# ---------------------------------------------------------------------------
tmp=$(mktemp -d)
make_full_project "$tmp"
# Remove notebooks/README.md — validation must FAIL
rm "$tmp/notebooks/README.md"
capture_exit "$tmp"
rm -rf "$tmp"

if [[ $RUN_EXIT -ne 0 ]]; then
  pass "missing notebooks/README.md: exits non-zero"
else
  fail "missing notebooks/README.md: expected non-zero exit"
fi

# ---------------------------------------------------------------------------
# TEST 3: notes/README.md is NOT in the required list (it's notebooks now)
# ---------------------------------------------------------------------------
tmp=$(mktemp -d)
make_full_project "$tmp"
# Remove notebooks/README.md but add notes/README.md — must still FAIL
rm "$tmp/notebooks/README.md"
mkdir -p "$tmp/notes"
touch "$tmp/notes/README.md"
capture_exit "$tmp"
rm -rf "$tmp"

if [[ $RUN_EXIT -ne 0 ]]; then
  pass "notes/README.md does not satisfy notebooks/README.md requirement"
else
  fail "notes/README.md should NOT satisfy notebooks/README.md requirement"
fi

# ---------------------------------------------------------------------------
# TEST 4: Error message is "❌ Validation failed" (no "— missing files" suffix)
# ---------------------------------------------------------------------------
tmp=$(mktemp -d)
# Empty project — everything is missing
capture_exit "$tmp"
rm -rf "$tmp"

if echo "$RUN_OUTPUT" | grep -q "❌ Validation failed"; then
  pass "error message contains '❌ Validation failed'"
else
  fail "error message '❌ Validation failed' not found"
fi

if echo "$RUN_OUTPUT" | grep -qF "— missing files"; then
  fail "error message must NOT contain '— missing files' suffix (old message)"
else
  pass "error message does not contain old suffix '— missing files'"
fi

# ---------------------------------------------------------------------------
# TEST 5: Missing any single required file → exit non-zero
# ---------------------------------------------------------------------------
required_files=(
  "README.md"
  "learning-paths/cybersecurity.md"
  "learning-paths/ai-ml.md"
  "learning-paths/devops-cloud.md"
  "learning-paths/web-fullstack.md"
  "learning-paths/git-github.md"
  "certifications/README.md"
  "notebooks/README.md"
  "models/README.md"
  "docs/ROADMAP.md"
)

for missing_file in "${required_files[@]}"; do
  tmp=$(mktemp -d)
  make_full_project "$tmp"
  rm "$tmp/$missing_file"
  capture_exit "$tmp"
  rm -rf "$tmp"
  if [[ $RUN_EXIT -ne 0 ]]; then
    pass "missing $missing_file: exits non-zero"
  else
    fail "missing $missing_file: expected non-zero exit, got 0"
  fi
done

# ---------------------------------------------------------------------------
# TEST 6: Missing file is reported with ❌ MISSING prefix
# ---------------------------------------------------------------------------
tmp=$(mktemp -d)
make_full_project "$tmp"
rm "$tmp/notebooks/README.md"
capture_exit "$tmp"
rm -rf "$tmp"

if echo "$RUN_OUTPUT" | grep -q "❌ MISSING: notebooks/README.md"; then
  pass "missing file reported with '❌ MISSING: notebooks/README.md'"
else
  fail "expected '❌ MISSING: notebooks/README.md' in output"
fi

# ---------------------------------------------------------------------------
# TEST 7: Success message is "✅ Structure OK" (not old "All structure is valid")
# ---------------------------------------------------------------------------
tmp=$(mktemp -d)
make_full_project "$tmp"
capture_exit "$tmp"
rm -rf "$tmp"

if echo "$RUN_OUTPUT" | grep -q "✅ Structure OK"; then
  pass "success message is '✅ Structure OK'"
else
  fail "success message '✅ Structure OK' not found"
fi

if echo "$RUN_OUTPUT" | grep -qF "All structure is valid"; then
  fail "old success message 'All structure is valid' must not appear"
else
  pass "old success message 'All structure is valid' is absent"
fi

# ---------------------------------------------------------------------------
# TEST 8: Regression — all_ok=false accumulates multiple missing files
# ---------------------------------------------------------------------------
tmp=$(mktemp -d)
make_full_project "$tmp"
rm "$tmp/notebooks/README.md"
rm "$tmp/models/README.md"
capture_exit "$tmp"
rm -rf "$tmp"

missing_count=$(echo "$RUN_OUTPUT" | grep -c "❌ MISSING:" || true)
if [[ $missing_count -eq 2 ]]; then
  pass "two missing files both reported as MISSING"
else
  fail "expected 2 MISSING lines, got $missing_count"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "Results: $PASS passed, $FAIL failed"
if [[ $FAIL -gt 0 ]]; then
  exit 1
fi