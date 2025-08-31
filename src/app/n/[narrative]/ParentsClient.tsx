"use client";

import { useState } from "react";
import type { ParentsResp, ParentItem } from "@/lib/api";
import { getParents } from "@/lib/api";

export default function ParentsClient({ initial }: { initial: ParentsResp }) {
  const [rows, setRows] = useState<ParentItem[]>(initial.items);
  const [cursor, setCursor] = useState<string | null | undefined>(
    initial.nextCursor,
  );
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const narrative = initial.narrative;

  async function loadMore() {
    if (!cursor || busy) return;
    setBusy(true);
    setErr(null);
    try {
      const next = await getParents(narrative, { limit: 25, cursor });
      setRows((r) => [...r, ...next.items]);
      setCursor(next.nextCursor ?? null);
    } catch (e: any) {
      setErr(e?.message || "Failed to load more");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h1 style={{ fontSize: 22, margin: "8px 0 12px" }}>{narrative}</h1>
      </div>

      {err && (
        <div
          role="alert"
          style={{
            background: "var(--error-bg)",
            color: "var(--error-fg)",
            padding: 8,
            borderRadius: 6,
            marginBottom: 8,
            border: "1px solid var(--border)",
          }}
        >
          {err}
        </div>
      )}

      {rows.length === 0 ? (
        <div
          style={{
            padding: 12,
            border: "1px dashed var(--border)",
            borderRadius: 8,
            color: "var(--fg-muted)",
            background: "transparent",
          }}
        >
          No parents yet. Try Refresh on the homepage.
        </div>
      ) : (
        <div style={{ display: "grid", gap: 8, marginBottom: 12 }}>
          {rows.map((it, i) => (
            <div
              key={`${it.parent}-${i}`}
              style={{
                border: "1px solid var(--border)",
                borderRadius: 8,
                padding: 12,
                background: "rgba(255,255,255,0.02)",
              }}
            >
              <div style={{ fontWeight: 600, color: "var(--fg)" }}>
                {it.parent}
              </div>
              <div style={{ fontSize: 13, color: "var(--fg-muted)" }}>
                matches: {it.matches}
                {typeof it.score === "number" ? (
                  <span> • score: {it.score}</span>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      )}

      {cursor ? (
        <button
          onClick={loadMore}
          disabled={busy}
          style={{
            padding: "8px 12px",
            border: "1px solid var(--border)",
            borderRadius: 6,
            background: "transparent",
            color: "var(--fg)",
            opacity: busy ? 0.7 : 1,
          }}
        >
          {busy ? "Loading…" : "Load more"}
        </button>
      ) : (
        <div style={{ color: "var(--fg-muted)", fontSize: 13 }}>
          End of list
        </div>
      )}
    </main>
  );
}
