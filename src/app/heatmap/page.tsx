import { getHeatmap } from "@/lib/api";
import { API_BASE } from "@/lib/config";
import HeatmapCard from "@/components/HeatmapCard";
import StaleBanner from "@/components/StaleBanner";

export default async function HeatmapPage() {
  let heatmapData;
  let error: string | null = null;

  try {
    heatmapData = await getHeatmap();
  } catch (err) {
    error = err instanceof Error ? err.message : "Failed to fetch heatmap data";
  }

  if (error) {
    return (
      <div style={{ padding: "20px" }}>
        <h1 style={{ marginBottom: "20px", color: "var(--error-fg)" }}>
          Heatmap
        </h1>
        <div
          style={{
            backgroundColor: "var(--error-bg)",
            color: "var(--error-fg)",
            padding: "16px",
            borderRadius: "8px",
            border: "1px solid var(--error-fg)",
          }}
        >
          Error: {error}
        </div>
      </div>
    );
  }

  if (!heatmapData) {
    return (
      <div style={{ padding: "20px" }}>
        <h1 style={{ marginBottom: "20px" }}>Heatmap</h1>
        <div>Loading...</div>
      </div>
    );
  }

  return (
    <div style={{ padding: "20px" }}>
      <h1 style={{ marginBottom: "20px" }}>Heatmap</h1>

      <StaleBanner
        stale={heatmapData.stale}
        lastUpdated={heatmapData.lastUpdated}
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "16px",
          marginTop: "20px",
        }}
      >
        {heatmapData.items.map((item) => (
          <HeatmapCard
            key={item.name}
            name={item.name}
            score={item.score}
            count={item.count}
            lastUpdated={item.lastUpdated}
            stale={item.stale}
          />
        ))}
      </div>

      {heatmapData.items.length === 0 && (
        <div
          style={{
            textAlign: "center",
            color: "var(--fg-muted)",
            padding: "40px",
            fontSize: "16px",
          }}
        >
          No narratives found
        </div>
      )}
    </div>
  );
}
