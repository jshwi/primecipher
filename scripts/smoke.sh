#!/usr/bin/env bash
# End-to-end smoke test for Narrative Heatmap backend
# - Verifies debug -> quick backtest -> walk-forward backtest (synthetic backfill)
# Usage:
#   bash scripts/smoke.sh
# Env:
#   API_BASE (default http://localhost:8000)
#   NARRATIVE (default dogs)
#   PARENT (default WIF)
#   HOLD (default h6)   # for synthetic backfill + walk-forward
#   MIN_LIQ (default 50000)
#   TOL_MIN (default 20)

set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"
NARRATIVE="${NARRATIVE:-dogs}"
PARENT="${PARENT:-WIF}"
HOLD="${HOLD:-h6}"
MIN_LIQ="${MIN_LIQ:-50000}"
TOL_MIN="${TOL_MIN:-20}"

# Pretty logging
log() { printf "\n\033[1;34m[smoke]\033[0m %s\n" "$*"; }
pass() { printf "\033[1;32m✔\033[0m %s\n" "$*"; }
fail() { printf "\033[1;31m✘ %s\033[0m\n" "$*"; exit 1; }

# Tool checks
command -v curl >/dev/null || fail "curl not found"
command -v jq >/dev/null || fail "jq not found"
command -v sqlite3 >/dev/null || log "sqlite3 not found (optional)"

# Activate backend venv if present
if [[ -d "backend/.venv" && -f "backend/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source backend/.venv/bin/activate
fi

# If API isn't up, start a local uvicorn just for this smoke run
is_up() { curl -fsS "${API_BASE}/docs" >/dev/null 2>&1; }
STARTED=0
PID=""
if ! is_up; then
  log "API not reachable, starting local uvicorn at ${API_BASE}"
  pushd backend >/dev/null
  export PYTHONPATH=.
  mkdir -p data
  : "${DATABASE_URL:=sqlite:///./data/smoke_local.db}"
  export DATABASE_URL
  # Use python -m uvicorn to avoid PATH issues; bind to 127.0.0.1:8000
  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > ../uvicorn.smoke.log 2>&1 &
  PID=$!
  STARTED=1
  popd >/dev/null
  # Wait up to ~10s for readiness
  for _ in {1..20}; do
    is_up && break
    sleep 0.5
  done
fi
# Ensure cleanup on exit if we started the server
trap '[[ "$STARTED" -eq 1 && -n "$PID" ]] && kill "$PID" >/dev/null 2>&1 || true' EXIT

# Quick probe: API up?
log "Probing API: ${API_BASE}/docs"
curl -fsS "${API_BASE}/docs" >/dev/null || fail "API not reachable at ${API_BASE}. Is it running?"

# 1) DEBUG CHILDREN
log "1) /debug/children (${PARENT}, narrative=${NARRATIVE})"
DBG_JSON="$(curl -fsS "${API_BASE}/debug/children/${PARENT}?narrative=${NARRATIVE}&applyBlocklist=true&limit=5")" || fail "debug/children fetch failed"
echo "$DBG_JSON" | jq -e '.counts.total' >/dev/null || fail "debug/children missing .counts.total"
TOTAL="$(echo "$DBG_JSON" | jq '.counts.total')"
RET="$(echo "$DBG_JSON" | jq '.counts.returned')"
pass "debug/children OK (total=${TOTAL}, returned=${RET})"

# 2) QUICK BACKTEST
log "2) /backtest (parent=${PARENT}, hold=h24, liq>=${MIN_LIQ})"
BT_JSON="$(curl -fsS "${API_BASE}/backtest?narrative=${NARRATIVE}&parent=${PARENT}&hold=h24&liqMinUsd=${MIN_LIQ}")" || fail "backtest fetch failed"
echo "$BT_JSON" | jq -e '.summary.n_trades' >/dev/null || fail "backtest missing .summary.n_trades"
BT_TRADES="$(echo "$BT_JSON" | jq '.summary.n_trades')"
pass "backtest OK (n_trades=${BT_TRADES})"

# 3) SYNTHETIC BACKFILL -> WALK-FORWARD
log "3) Synthetic backfill (${HOLD}) to seed entry snapshots, then /backtest/walk"
# Ensure package markers before running the tool
if [[ ! -f backend/app/tools/__init__.py ]]; then
  mkdir -p backend/app/tools
  echo "# package marker" > backend/app/tools/__init__.py
fi

PYTHONPATH=backend python -m app.tools.synthetic_backfill --window "${HOLD}" --narrative "${NARRATIVE}" --parent "${PARENT}"

WALK_JSON="$(curl -fsS "${API_BASE}/backtest/walk?narrative=${NARRATIVE}&parent=${PARENT}&hold=${HOLD}&minLiqUsd=${MIN_LIQ}&toleranceMin=${TOL_MIN}")" || fail "backtest/walk fetch failed"
echo "$WALK_JSON" | jq -e '.summary.n_trades' >/dev/null || fail "backtest/walk missing .summary.n_trades"
WALK_TRADES="$(echo "$WALK_JSON" | jq '.summary.n_trades')"
echo "$WALK_JSON" | jq '.summary, .diagnostics' >/dev/null

if [[ "$WALK_TRADES" -lt 1 ]]; then
  fail "walk-forward produced 0 trades (summary printed above). If this persists, try HOLD=m5 with real snapshots."
fi
pass "walk-forward OK (n_trades=${WALK_TRADES})"

log "All smoke checks passed ✅"

