import Link from "next/link";
import RefreshButton from "@/components/RefreshButton";
import StaleBanner from "@/components/StaleBanner";
import { getNarratives } from "@/lib/api";

export default async function Page() {
  let data;
  let error = null;

  try {
    data = await getNarratives();
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to fetch data";
    data = { items: [], stale: true, lastUpdated: null };
  }

  // Defensive: handle either ['dogs','ai'] or [{narrative:'dogs',count:2}, ...]
  const rows = Array.isArray(data?.items)
    ? data.items
        .map((x: string | { narrative: string; count?: number }) =>
          typeof x === "string" ? x : x?.narrative,
        )
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

      <StaleBanner
        stale={data?.stale ?? true}
        lastUpdated={data?.lastUpdated ?? null}
      />

      {error && (
        <div
          style={{
            background: "#fee",
            color: "#900",
            padding: "12px",
            borderRadius: 8,
            marginBottom: "16px",
            border: "1px solid #f5c6cb",
          }}
        >
          Backend unavailable: {error}
        </div>
      )}

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
