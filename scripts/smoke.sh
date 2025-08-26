#!/usr/bin/env bash
# End-to-end smoke test for Narrative Heatmap backend
# - Verifies debug -> quick backtest -> walk-forward backtest (synthetic backfill)
# Usage:
#   bash scripts/smoke.sh
# Env:
#   API_BASE (optional; if occupied by some other process, we will spawn a private server on 127.0.0.1:8010)
#   NARRATIVE (default dogs)
#   PARENT (default WIF)
#   HOLD (default h6)
#   MIN_LIQ (default 50000)
#   TOL_MIN (default 20)
#   DB_PATH (optional; default: <repo>/primecipher.db)

set -euo pipefail

# -------- configuration --------
NARRATIVE="${NARRATIVE:-dogs}"
PARENT="${PARENT:-WIF}"
HOLD="${HOLD:-h6}"
MIN_LIQ="${MIN_LIQ:-50000}"
TOL_MIN="${TOL_MIN:-20}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="${DB_PATH:-${REPO_ROOT}/primecipher.db}"
export PRIMECIPHER_DB_PATH="${DB_PATH}"

# prefer 8000, but if it's busy we'll spin up our own server on 8010
DEFAULT_HOST="127.0.0.1"
PREF_PORT="${PREF_PORT:-8000}"
ALT_PORT="${ALT_PORT:-8010}"

# If API_BASE is set, we'll still validate it; otherwise we'll decide dynamically.
API_BASE="${API_BASE:-http://${DEFAULT_HOST}:${PREF_PORT}}"

# -------- helpers --------
log()  { printf "\n\033[1;34m[smoke]\033[0m %s\n" "$*"; }
pass() { printf "\033[1;32m✔\033[0m %s\n" "$*"; }
fail() { printf "\033[1;31m✘ %s\033[0m\n" "$*"; exit 1; }
is_up() { curl -fsS "$1/docs" >/dev/null 2>&1; }

need_bin() { command -v "$1" >/dev/null 2>&1 || fail "$1 not found"; }
need_bin curl
need_bin jq

# optional sqlite3 (for debug prints)
if ! command -v sqlite3 >/dev/null 2>&1; then
  log "sqlite3 not found (optional; debug prints will be limited)"
fi

# activate backend venv if present
if [[ -d "${REPO_ROOT}/backend/.venv" && -f "${REPO_ROOT}/backend/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/backend/.venv/bin/activate"
fi

# ensure package marker exists (some environments need this)
if [[ ! -f "${REPO_ROOT}/backend/app/tools/__init__.py" ]]; then
  mkdir -p "${REPO_ROOT}/backend/app/tools"
  echo "# package marker" > "${REPO_ROOT}/backend/app/tools/__init__.py"
fi

# -------- decide server to use --------
STARTED=0
PID=""

pick_and_start_server() {
  local host="$1" pref_port="$2" alt_port="$3"

  # If API_BASE was provided explicitly and is up, we still avoid using it
  # because it likely doesn't inherit PRIMECIPHER_DB_PATH. We'll prefer a private instance.
  if is_up "${API_BASE}"; then
    log "Detected existing service at ${API_BASE}; launching private server on ${host}:${alt_port} to ensure DB/env consistency"
    API_BASE="http://${host}:${alt_port}"
  fi

  # If chosen API_BASE is up (either user-provided or adjusted above), don't reuse it; still launch our own.
  if is_up "${API_BASE}"; then
    # bump to alt port
    API_BASE="http://${host}:${alt_port}"
  fi

  # Start our own uvicorn at API_BASE
  local url="${API_BASE}"
  local port="${url##*:}"; port="${port%/*}"

  log "Starting local uvicorn at ${url}"
  pushd "${REPO_ROOT}/backend" >/dev/null
  export PYTHONPATH=.
  mkdir -p "$(dirname "${PRIMECIPHER_DB_PATH}")"
  python -m uvicorn app.main:app --host "${host}" --port "${port}" > ../uvicorn.smoke.log 2>&1 &
  PID=$!
  STARTED=1
  popd >/dev/null

  # wait up to ~10s
  for _ in {1..20}; do
    is_up "${url}" && return 0
    sleep 0.5
  done
  fail "API did not become ready at ${url}"
}

# Always launch a private server to guarantee it inherits our env
pick_and_start_server "${DEFAULT_HOST}" "${PREF_PORT}" "${ALT_PORT}"
trap '[[ "$STARTED" -eq 1 && -n "$PID" ]] && kill "$PID" >/dev/null 2>&1 || true' EXIT

# -------- run checks --------
log "Probing API: ${API_BASE}/docs"
curl -fsS "${API_BASE}/docs" >/dev/null || fail "API not reachable at ${API_BASE}"

log "Using sqlite db: ${PRIMECIPHER_DB_PATH}"

# 1) DEBUG CHILDREN
log "1) /debug/children (${PARENT}, narrative=${NARRATIVE})"
DBG_JSON="$(curl -fsS "${API_BASE}/debug/children/${PARENT}?narrative=${NARRATIVE}&applyBlocklist=true&limit=5")" \
  || fail "debug/children fetch failed"

echo "$DBG_JSON" | jq -e '.counts.total' >/dev/null || fail "debug/children missing .counts.total"
TOTAL="$(echo "$DBG_JSON" | jq '.counts.total')"
RET="$(echo "$DBG_JSON" | jq '.counts.returned')"
pass "debug/children OK (total=${TOTAL}, returned=${RET})"

# 2) QUICK BACKTEST
log "2) /backtest (parent=${PARENT}, hold=h24, liq>=${MIN_LIQ})"
BT_JSON="$(curl -fsS "${API_BASE}/backtest?narrative=${NARRATIVE}&parent=${PARENT}&hold=h24&liqMinUsd=${MIN_LIQ}")" \
  || fail "backtest fetch failed"

BT_TRADES="$(echo "$BT_JSON" | jq -r '.summary.n_trades // .summary.count // 0')"
[[ "$BT_TRADES" =~ ^[0-9]+$ ]] || fail "backtest summary not numeric"
[[ "$BT_TRADES" -ge 1 ]] || { echo "$BT_JSON" | jq . >/dev/null || true; fail "backtest returned no trades"; }
pass "backtest OK (n_trades=${BT_TRADES})"

# 3) SYNTHETIC BACKFILL -> WALK-FORWARD
log "3) Synthetic backfill (${HOLD}) to seed entry snapshots, then /backtest/walk"

PYTHONPATH="${REPO_ROOT}/backend" python -m app.tools.synthetic_backfill \
  --window "${HOLD}" --narrative "${NARRATIVE}" --parent "${PARENT}" --limit 8

WALK_JSON="$(curl -fsS "${API_BASE}/backtest/walk?narrative=${NARRATIVE}&parent=${PARENT}&hold=${HOLD}&minLiqUsd=${MIN_LIQ}&toleranceMin=${TOL_MIN}")" \
  || fail "backtest/walk fetch failed"

WALK_TRADES="$(echo "$WALK_JSON" | jq -r '.summary.n_trades // .summary.count // 0')"
[[ "$WALK_TRADES" =~ ^[0-9]+$ ]] || fail "walk summary not numeric"

# emit summary / diagnostics for troubleshooting
echo "$WALK_JSON" | jq '.summary, .diagnostics // empty' >/dev/null || true

if [[ "$WALK_TRADES" -lt 1 ]]; then
  if command -v sqlite3 >/dev/null 2>&1; then
    printf "\n[smoke] debug: showing recent rows from snapshots (if any):\n"
    sqlite3 "${PRIMECIPHER_DB_PATH}" 'SELECT pair_address, ts, price_usd, liquidity_usd FROM snapshots ORDER BY ts DESC LIMIT 10;' 2>/dev/null || true
    printf "\n[smoke] debug: showing recent rows from pair_snapshots (if any):\n"
    sqlite3 "${PRIMECIPHER_DB_PATH}" 'SELECT pair_address, ts, price_usd, liquidity_usd FROM pair_snapshots ORDER BY ts DESC LIMIT 10;' 2>/dev/null || true
    printf "\n[smoke] debug: tracked pairs (if any):\n"
    sqlite3 "${PRIMECIPHER_DB_PATH}" 'SELECT pair_address, parent, narrative, first_seen, last_seen FROM tracked_pairs ORDER BY last_seen DESC LIMIT 10;' 2>/dev/null || true
  fi
  fail "walk-forward produced 0 trades (summary printed above). If this persists, try HOLD=m5 with real snapshots."
fi
pass "walk-forward OK (n_trades=${WALK_TRADES})"

log "All smoke checks passed ✅"
