TOKEN="s3cr3t"
AUTH_HEADER=(-H "Authorization: Bearer $TOKEN")
# Prove the global status isn’t wired (current behavior)
curl -s http://127.0.0.1:8000/refresh/status "${AUTH_HEADER[@]}" | jq '.'

# Prove job-by-id is fine
JOBID=$(curl -s -X POST http://127.0.0.1:8000/refresh/async "${AUTH_HEADER[@]}" | jq -r '.jobId')
curl -s "http://127.0.0.1:8000/refresh/status/$JOBID" "${AUTH_HEADER[@]}" | jq '.'
