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
            border: "1px solid var(--border)",
            borderRadius: 8,
            padding: 12,
            background: "rgba(255,255,255,0.02)",
          }}
        >
          <div style={{ fontWeight: 600, color: "var(--fg)" }}>
            {item.parent}
          </div>
          <div style={{ fontSize: 13, color: "var(--fg-muted)" }}>
            matches: {item.matches}
            {typeof item.score === "number" ? (
              <span> • score: {item.score}</span>
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
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: 12,
          background: "rgba(255,255,255,0.02)",
        }}
      >
        <pre style={{ margin: 0, fontSize: 13, color: "var(--fg)" }}>
          {JSON.stringify(item, null, 2)}
        </pre>
      </div>
    );
  };

  return (
    <div>
      {error && (
        <div
          role="alert"
          style={{
            background: "var(--error-bg)",
            color: "var(--error-fg)",
            padding: 8,
            borderRadius: 6,
            marginBottom: 8,
            border: "1px solid var(--border)",
            fontSize: 13,
          }}
        >
          {error}
        </div>
      )}

      {items.length === 0 ? (
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
          {items.map((item, index) => renderItem(item, index))}
        </div>
      )}

      {nextCursor && (
        <button
          onClick={loadMore}
          disabled={loading}
          style={{
            padding: "8px 12px",
            border: "1px solid var(--border)",
            borderRadius: 6,
            background: "transparent",
            color: "var(--fg)",
            opacity: loading ? 0.7 : 1,
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Loading…" : "Load more"}
        </button>
      )}
    </div>
  );
}
