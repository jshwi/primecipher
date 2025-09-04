"use client";

import { useState, useEffect } from "react";
import { getHeatmap } from "@/lib/api";
import { HeatmapItem, HeatmapResp } from "@/lib/api";
import StaleBanner from "@/components/StaleBanner";

interface HeatmapGridProps {
  error?: string | null;
}

function getScoreColor(score: number): string {
  // Normalize score to 0-1 range for color calculation
  // Assuming scores range from -1 to 1, with 0 being neutral
  const normalizedScore = Math.max(-1, Math.min(1, score));

  if (normalizedScore > 0.1) {
    // High positive score - green
    const intensity = Math.min(1, normalizedScore);
    const alpha = 0.1 + intensity * 0.2; // 0.1 to 0.3 alpha
    return `rgba(34, 197, 94, ${alpha})`; // green-500 with varying alpha
  } else if (normalizedScore < -0.1) {
    // Low negative score - red
    const intensity = Math.min(1, Math.abs(normalizedScore));
    const alpha = 0.1 + intensity * 0.2; // 0.1 to 0.3 alpha
    return `rgba(239, 68, 68, ${alpha})`; // red-500 with varying alpha
  } else {
    // Neutral score - gray
    return `rgba(107, 114, 128, 0.1)`; // gray-500 with low alpha
  }
}

function HeatmapCard({ item }: { item: HeatmapItem }) {
  const backgroundColor = getScoreColor(item.score);

  return (
    <div
      style={{
        backgroundColor,
        border: "1px solid var(--border)",
        borderRadius: "8px",
        padding: "16px",
        position: "relative",
        transition: "transform 0.2s ease, box-shadow 0.2s ease",
      }}
    >
      {item.stale && (
        <div
          style={{
            position: "absolute",
            top: "8px",
            right: "8px",
            backgroundColor: "#f59e0b",
            color: "#000",
            fontSize: "10px",
            fontWeight: "bold",
            padding: "2px 6px",
            borderRadius: "4px",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
          }}
        >
          STALE
        </div>
      )}

      <h3
        style={{
          margin: "0 0 8px 0",
          fontSize: "16px",
          fontWeight: "600",
          color: "var(--fg)",
          lineHeight: "1.4",
        }}
      >
        {item.name}
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
        <div>Score: {item.score.toFixed(3)}</div>
        <div>Count: {item.count}</div>
      </div>
    </div>
  );
}

export default function HeatmapGrid({ error }: HeatmapGridProps) {
  const [heatmapData, setHeatmapData] = useState<HeatmapResp | null>(null);
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
        const data = await getHeatmap();
        setHeatmapData(data);
        setFetchError(null);
      } catch (err) {
        setFetchError(
          err instanceof Error ? err.message : "Failed to fetch heatmap data",
        );
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [error]);

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
        Loading heatmap data...
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

  if (!heatmapData) {
    return (
      <div
        style={{
          padding: "40px",
          textAlign: "center",
          color: "var(--fg-muted)",
          fontSize: "16px",
        }}
      >
        No heatmap data available
      </div>
    );
  }

  // Sort items by score descending
  const sortedItems = [...heatmapData.items].sort((a, b) => b.score - a.score);

  return (
    <div>
      <StaleBanner
        stale={heatmapData.stale}
        lastUpdated={heatmapData.lastUpdated}
      />

      {sortedItems.length === 0 ? (
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
          No heatmap data available
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
          {sortedItems.map((item) => (
            <HeatmapCard key={item.name} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
