#!/usr/bin/env bash
set -euo pipefail
: "${TOKEN:=s3cr3t}"
if [[ -n "${TOKEN:-}" ]]; then AUTH=(-H "Authorization: Bearer $TOKEN"); else AUTH=(); fi

JOBID="$(curl -s -X POST "http://127.0.0.1:8000/refresh/async" "${AUTH[@]}" | jq -r '.jobId')"
echo "first jobId=$JOBID"; test -n "$JOBID"

RID="$(curl -s -X POST "http://127.0.0.1:8000/refresh/async" "${AUTH[@]}" | jq -r '.jobId')"
echo "second jobId=$RID"

if [[ "$RID" == "$JOBID" ]]; then
  echo "Idempotent while running/instant-done (good)"
else
  echo "Different job IDs—your server allows multiple concurrent jobs"
fi
