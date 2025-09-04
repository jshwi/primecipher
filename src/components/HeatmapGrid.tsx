"use client";

import { useState, useEffect } from "react";
import { getHeatmap } from "@/lib/api";
import { HeatmapItem, HeatmapResp } from "@/lib/api";
import StaleBanner from "@/components/StaleBanner";

interface HeatmapGridProps {
  error?: string | null;
  refreshTrigger?: number;
}

function getScoreColor(score: number): string {
  // Clamp score to 0-1 range for simple color intensity mapping
  const clampedScore = Math.max(0, Math.min(1, score));

  // Use a blue-to-green gradient based on score intensity
  // Higher scores get more intense colors with higher alpha
  const alpha = 0.1 + clampedScore * 0.4; // 0.1 to 0.5 alpha

  if (clampedScore < 0.5) {
    // Low scores - blue gradient
    const intensity = clampedScore * 2; // 0 to 1
    const red = Math.floor(59 + intensity * 40); // 59 to 99
    const green = Math.floor(130 + intensity * 125); // 130 to 255
    const blue = Math.floor(246 + intensity * 9); // 246 to 255
    return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
  } else {
    // High scores - green gradient
    const intensity = (clampedScore - 0.5) * 2; // 0 to 1
    const red = Math.floor(99 + intensity * 155); // 99 to 254
    const green = Math.floor(255 - intensity * 58); // 255 to 197
    const blue = Math.floor(255 - intensity * 161); // 255 to 94
    return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
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

export default function HeatmapGrid({
  error,
  refreshTrigger,
}: HeatmapGridProps) {
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

      {/* Compact Legend */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "8px",
          marginTop: "16px",
          marginBottom: "8px",
          fontSize: "12px",
          color: "var(--fg-muted)",
        }}
      >
        <span>Low</span>
        <div
          style={{
            width: "60px",
            height: "12px",
            background:
              "linear-gradient(to right, rgba(59, 130, 246, 0.1), rgba(34, 197, 94, 0.5))",
            borderRadius: "6px",
            border: "1px solid var(--border)",
          }}
        />
        <span>High</span>
      </div>

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
