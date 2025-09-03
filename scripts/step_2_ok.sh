#!/usr/bin/env bash
set -euo pipefail

# If your refresh endpoints need auth, keep TOKEN set; otherwise unset it.
: "${TOKEN:=s3cr3t}"
if [[ -n "${TOKEN:-}" ]]; then AUTH=(-H "Authorization: Bearer $TOKEN"); else AUTH=(); fi

echo "1) Start job via /refresh/async"
JOBID="$(curl -s -X POST "http://127.0.0.1:8000/refresh/async" "${AUTH[@]}" | jq -r '.jobId')"
echo "jobId=$JOBID"
test -n "$JOBID"

echo "2) Job-by-id status (should exist)"
curl -s "http://127.0.0.1:8000/refresh/status/$JOBID" "${AUTH[@]}" | jq .

echo "3) Global status (currently not wired in your repo; expect lastJob=null)"
curl -s "http://127.0.0.1:8000/refresh/status" "${AUTH[@]}" | jq .
