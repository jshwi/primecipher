#!/usr/bin/env bash
set -euo pipefail
API_BASE="${API_BASE:-http://localhost:8000}"

curl -sf "$API_BASE/healthz" | jq . >/dev/null || { echo "healthz failed"; exit 1; }
curl -sf "$API_BASE/narratives?window=24h" | jq '.[0].narrative' >/dev/null || { echo "narratives failed"; exit 1; }
curl -sf "$API_BASE/parents/dogs?window=24h" | jq '.[0].parent' >/dev/null || { echo "parents failed"; exit 1; }
echo "smoke: ok"
