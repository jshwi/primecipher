// @ts-nocheck
import Link from "next/link";
import RefreshButton from "@/components/RefreshButton";
import { getNarratives } from "@/lib/api";

function fmt(ts?: number) {
  if (!ts) return null;
  const s = new Date(ts * 1000).toLocaleString();
  return (
    <div style={{ color: "#888", marginBottom: 8 }}>Last refresh: {s}</div>
  );
}

export default async function Page() {
  const data = await getNarratives();

  // Defensive: handle either ['dogs','ai'] or [{narrative:'dogs',count:2}, ...]
  const rows = Array.isArray(data?.items)
    ? data.items
        .map((x: any) => (typeof x === "string" ? x : x?.narrative))
        .filter(Boolean)
    : [];

  return (
    <main>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h1 style={{ fontSize: 24, margin: "8px 0 16px" }}>Narratives (24h)</h1>
        <RefreshButton />
      </div>

      {fmt(data?.lastRefresh)}

      {rows.length === 0 ? (
        <div
          style={{
            padding: 12,
            border: "1px dashed #444",
            borderRadius: 8,
            color: "#888",
          }}
        >
          No narratives yet. Add one in{" "}
          <code>backend/seeds/narratives.seed.json</code> then hit Refresh.
        </div>
      ) : (
        <div style={{ display: "grid", gap: 8 }}>
          {rows.map((n: string) => (
            <Link
              key={n}
              href={`/n/${encodeURIComponent(n)}`}
              style={{
                padding: 12,
                border: "1px solid #222",
                borderRadius: 8,
                textDecoration: "none",
              }}
            >
              {n}
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
