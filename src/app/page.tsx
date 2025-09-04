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
    <div style={{ padding: "20px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        <h1 style={{ fontSize: 24, margin: 0 }}>Narratives (24h)</h1>
        <RefreshButton />
      </div>

      <StaleBanner
        stale={data?.stale ?? true}
        lastUpdated={data?.lastUpdated ?? null}
      />

      {error && (
        <div
          style={{
            backgroundColor: "var(--error-bg)",
            color: "var(--error-fg)",
            padding: "16px",
            borderRadius: "8px",
            marginBottom: "20px",
            border: "1px solid var(--error-fg)",
          }}
        >
          Backend unavailable: {error}
        </div>
      )}

      {rows.length === 0 ? (
        <div
          style={{
            padding: "40px",
            textAlign: "center",
            color: "var(--fg-muted)",
            fontSize: "16px",
            border: "1px dashed var(--border)",
            borderRadius: "8px",
            backgroundColor: "rgba(255, 255, 255, 0.02)",
          }}
        >
          No narratives yet. Add one in{" "}
          <code
            style={{
              backgroundColor: "rgba(255, 255, 255, 0.1)",
              padding: "2px 6px",
              borderRadius: "4px",
              fontSize: "14px",
            }}
          >
            backend/seeds/narratives.seed.json
          </code>{" "}
          then hit Refresh.
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "16px",
            marginTop: "20px",
          }}
        >
          {rows.map((n: string) => (
            <Link
              key={n}
              href={`/n/${encodeURIComponent(n)}`}
              style={{
                backgroundColor: "rgba(255, 255, 255, 0.02)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                padding: "16px",
                textDecoration: "none",
                color: "var(--fg)",
                transition: "transform 0.2s ease, box-shadow 0.2s ease",
                display: "block",
              }}
            >
              <h3
                style={{
                  margin: "0 0 8px 0",
                  fontSize: "16px",
                  fontWeight: "600",
                  color: "var(--fg)",
                  lineHeight: "1.4",
                }}
              >
                {n}
              </h3>
              <div
                style={{
                  fontSize: "14px",
                  color: "var(--fg-muted)",
                }}
              >
                View narrative details →
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
