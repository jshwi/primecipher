#!/usr/bin/env bash
set -euo pipefail
: "${TOKEN:=s3cr3t}"
if [[ -n "${TOKEN:-}" ]]; then AUTH=(-H "Authorization: Bearer $TOKEN"); else AUTH=(); fi

echo "Expect global status to show running/lastJob (it doesn't yet):"
curl -s "http://127.0.0.1:8000/refresh/status" "${AUTH[@]}" | jq .
