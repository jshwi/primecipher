TOKEN="s3cr3t"
AUTH_HEADER=(-H "Authorization: Bearer $TOKEN")


JOBID=$(curl -s -X POST http://127.0.0.1:8000/refresh/async "${AUTH_HEADER[@]}" | jq -r '.jobId')
while true; do
  S=$(curl -s "http://127.0.0.1:8000/refresh/status/$JOBID" "${AUTH_HEADER[@]}")
  echo "$S" | jq '{id, state, narrativesDone, narrativesTotal, errors}'
  [[ "$(echo "$S" | jq -r '.state')" == "done" ]] && break
  sleep 2
done
