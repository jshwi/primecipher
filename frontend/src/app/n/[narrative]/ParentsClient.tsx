"use client"

import { useState } from "react"
import type { ParentsResp, ParentItem } from "@/lib/api"
import { getParents } from "@/lib/api"

export default function ParentsClient({ initial }: { initial: ParentsResp }) {
  const [rows, setRows] = useState<ParentItem[]>(initial.items)
  const [cursor, setCursor] = useState<string | null | undefined>(initial.nextCursor)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const narrative = initial.narrative

  async function loadMore() {
    if (!cursor || busy) return
    setBusy(true)
    setErr(null)
    try {
      const next = await getParents(narrative, { limit: 25, cursor })
      setRows((r) => [...r, ...next.items])
      setCursor(next.nextCursor ?? null)
    } catch (e: any) {
      setErr(e?.message || "Failed to load more")
    } finally {
      setBusy(false)
    }
  }

  return (
    <main>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ fontSize: 22, margin: "8px 0 12px" }}>{narrative}</h1>
      </div>

      {err && (
        <div style={{ background: "#fee", color: "#900", padding: "6px 8px", borderRadius: 6, marginBottom: 8 }}>
          {err}
        </div>
      )}

      {rows.length === 0 ? (
        <div style={{ padding: 12, border: "1px dashed #444", borderRadius: 8, color: "#888" }}>
          No parents yet. Try Refresh on the homepage.
        </div>
      ) : (
        <div style={{ display: "grid", gap: 8, marginBottom: 12 }}>
          {rows.map((it, i) => (
            <div key={`${it.parent}-${i}`} style={{ border: "1px solid #222", borderRadius: 8, padding: 12 }}>
              <div style={{ fontWeight: 600 }}>{it.parent}</div>
              <div style={{ fontSize: 13, color: "#888" }}>
                matches: {it.matches}
                {typeof it.score === "number" ? <span> • score: {it.score}</span> : null}
              </div>
            </div>
          ))}
        </div>
      )}

      {cursor ? (
        <button
          onClick={loadMore}
          disabled={busy}
          style={{ padding: "8px 12px", border: "1px solid #222", borderRadius: 6, opacity: busy ? 0.7 : 1 }}
        >
          {busy ? "Loading…" : "Load more"}
        </button>
      ) : (
        <div style={{ color: "#888", fontSize: 13 }}>End of list</div>
      )}
    </main>
  )
}
