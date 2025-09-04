"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/config";
import type { ParentItem } from "@/lib/api";

interface ParentsListProps {
  narrative: string;
  initial: {
    items: ParentItem[];
    nextCursor?: string | null;
  };
}

export default function ParentsList({ narrative, initial }: ParentsListProps) {
  const [items, setItems] = useState<ParentItem[]>(initial.items);
  const [nextCursor, setNextCursor] = useState<string | null | undefined>(
    initial.nextCursor,
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMore = async () => {
    if (!nextCursor || loading) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/parents/${narrative}?limit=25&cursor=${encodeURIComponent(nextCursor)}`,
      );

      if (!response.ok) {
        if (response.status === 400) {
          throw new Error("Invalid cursor");
        }
        throw new Error(`Failed to load: ${response.status}`);
      }

      const data = await response.json();
      setItems((prev) => [...prev, ...data.items]);
      setNextCursor(data.nextCursor ?? null);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load more";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const renderItem = (item: ParentItem, index: number) => {
    // Check if item has the expected structure
    if (item.parent && typeof item.matches === "number") {
      return (
        <div
          key={`${item.parent}-${index}`}
          style={{
            backgroundColor: "rgba(255, 255, 255, 0.02)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "16px",
            transition: "transform 0.2s ease, box-shadow 0.2s ease",
            cursor: "pointer",
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
            {item.parent}
          </h3>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "4px",
              fontSize: "14px",
              color: "var(--fg-muted)",
            }}
          >
            <div>Matches: {item.matches}</div>
            {typeof item.score === "number" ? (
              <div>Score: {item.score.toFixed(4)}</div>
            ) : null}
          </div>
        </div>
      );
    }

    // Fallback to JSON.stringify for unexpected structure
    return (
      <div
        key={`item-${index}`}
        style={{
          backgroundColor: "rgba(255, 255, 255, 0.02)",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          padding: "16px",
        }}
      >
        <pre style={{ margin: 0, fontSize: "13px", color: "var(--fg)" }}>
          {JSON.stringify(item, null, 2)}
        </pre>
      </div>
    );
  };

  return (
    <div>
      <div
        style={{
          marginBottom: "16px",
          padding: "12px",
          backgroundColor: "rgba(255, 255, 255, 0.02)",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          fontSize: "14px",
          color: "var(--fg-muted)",
        }}
      >
        Total loaded: {items.length} parents
      </div>

      {error && (
        <div
          role="alert"
          style={{
            backgroundColor: "var(--error-bg)",
            color: "var(--error-fg)",
            padding: "16px",
            borderRadius: "8px",
            marginBottom: "20px",
            border: "1px solid var(--error-fg)",
            fontSize: "14px",
          }}
        >
          {error}
        </div>
      )}

      {items.length === 0 ? (
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
          No parents yet. Try Refresh on the homepage.
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "16px",
            marginBottom: "20px",
          }}
        >
          {items.map((item, index) => renderItem(item, index))}
        </div>
      )}

      {nextCursor && (
        <button
          onClick={loadMore}
          disabled={loading}
          style={{
            padding: "12px 24px",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            backgroundColor: "rgba(255, 255, 255, 0.02)",
            color: "var(--fg)",
            opacity: loading ? 0.7 : 1,
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: "14px",
            fontWeight: "500",
            transition: "transform 0.2s ease, box-shadow 0.2s ease",
          }}
        >
          {loading ? "Loading…" : "Load more"}
        </button>
      )}
    </div>
  );
}
