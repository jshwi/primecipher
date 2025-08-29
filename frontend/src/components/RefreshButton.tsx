"use client"
import { useTransition, useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { startRefreshJob, getRefreshStatus } from "@/lib/api"

export default function RefreshButton() {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()
  const [err, setErr] = useState<string | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [state, setState] = useState<"idle" | "queued" | "running" | "done" | "error">("idle")

  // poll when we have a job id
  useEffect(() => {
    if (!jobId) return
    let stop = false
    async function poll() {
      try {
        const s = await getRefreshStatus(jobId)
        if (stop) return
        setState(s.state)
        if (s.state === "done") {
          setTimeout(() => router.refresh(), 100) // re-render page data
        } else if (s.state === "error") {
          setErr(s.error || "Refresh failed")
        } else {
          setTimeout(poll, 1000)
        }
      } catch (e: any) {
        if (!stop) setErr(e?.message || "Refresh status failed")
      }
    }
    poll()
    return () => { stop = true }
  }, [jobId, router])

  async function run() {
    setErr(null)
    setState("idle")
    const { jobId } = await startRefreshJob()
    setJobId(jobId)
    setState("queued")
  }

  const label =
    state === "running" ? "Refreshing…" :
    state === "queued"  ? "Queued…" :
    isPending           ? "Starting…" :
                          "Refresh"

  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'end',gap:6}}>
      <button
        onClick={() => startTransition(run)}
        disabled={isPending || state === "running" || state === "queued"}
        style={{padding:'8px 12px',border:'1px solid #222',borderRadius:6,opacity:(isPending || state!=="idle")?0.7:1}}
      >
        {label}
      </button>
      {err && (
        <div style={{background:'#fee', color:'#900', padding:'6px 8px', borderRadius:6, fontSize:13, maxWidth:360}}>
          {err}
        </div>
      )}
    </div>
  )
}
