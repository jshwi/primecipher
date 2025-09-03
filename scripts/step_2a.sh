# 1) Start a job
TOKEN="s3cr3t"
AUTH_HEADER=(-H "Authorization: Bearer $TOKEN")
JOBID=$(curl -s -X POST http://127.0.0.1:8000/refresh/async | jq -r '.jobId')
echo "jobId=$JOBID"; test -n "$JOBID"

# 2) Global status shows running OR lastJob
curl -s http://127.0.0.1:8000/refresh/status "${AUTH_HEADER[@]}" | jq .
# Expect:
# { "running": true, "jobId": "...", ... }  (while active)
# OR after finish:
# { "running": false, "lastJob": { "jobId": "...", "state": "done", ... } }

# 3) Job-by-id status mirrors lastJob
curl -s "http://127.0.0.1:8000/refresh/status/$JOBID" "${AUTH_HEADER[@]}" | jq .
# Expect: { id: JOBID, state: "done" | "running", ... }

# 4) Idempotency: repost during run returns same job
RID=$(curl -s -X POST http://127.0.0.1:8000/refresh/async  "${AUTH_HEADER[@]}"| jq -r '.jobId')
test "$RID" = "$JOBID" && echo "same job id (good)"
