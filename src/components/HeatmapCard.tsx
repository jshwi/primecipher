"use client";

interface HeatmapCardProps {
  name: string;
  score: number;
  count: number;
  lastUpdated?: number | null;
  stale: boolean;
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
