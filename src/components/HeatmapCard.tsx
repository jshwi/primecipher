"use client";

interface HeatmapCardProps {
  name: string;
  score: number;
  count: number;
  lastUpdated?: number | null;
  stale: boolean;
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

export default function HeatmapCard({
  name,
  score,
  count,
  lastUpdated,
  stale,
}: HeatmapCardProps) {
  const backgroundColor = getScoreColor(score);

  return (
    <div
      style={{
        backgroundColor,
        border: "1px solid var(--border)",
        borderRadius: "8px",
        padding: "16px",
        position: "relative",
        transition: "transform 0.2s ease, box-shadow 0.2s ease",
        cursor: "pointer",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-2px)";
        e.currentTarget.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.3)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      {stale && (
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
        {name}
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
        <div>Score: {score.toFixed(4)}</div>
        <div>Count: {count}</div>
      </div>
    </div>
  );
}
