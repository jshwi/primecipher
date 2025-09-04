"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { getNarratives, NarrativesResp } from "@/lib/api";
import StaleBanner from "@/components/StaleBanner";

interface NarrativesListProps {
  error?: string | null;
  refreshTrigger?: number;
}

export default function NarrativesList({
  error,
  refreshTrigger,
}: NarrativesListProps) {
  const [data, setData] = useState<NarrativesResp | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      if (error) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const result = await getNarratives();
        setData(result);
        setFetchError(null);
      } catch (err) {
        setFetchError(
          err instanceof Error ? err.message : "Failed to fetch narratives",
        );
        setData({ items: [], stale: true, lastUpdated: null });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [error, refreshTrigger]);

  if (error) {
    return (
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
    );
  }

  if (loading) {
    return (
      <div
        style={{
          padding: "40px",
          textAlign: "center",
          color: "var(--fg-muted)",
          fontSize: "16px",
        }}
      >
        Loading narratives...
      </div>
    );
  }

  if (fetchError) {
    return (
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
        Error: {fetchError}
      </div>
    );
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
    <div>
      <StaleBanner
        stale={data?.stale ?? true}
        lastUpdated={data?.lastUpdated ?? null}
      />

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
