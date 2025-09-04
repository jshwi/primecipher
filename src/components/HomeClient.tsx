"use client";

import { useState, useEffect } from "react";
import Header from "./Header";
import HeatmapGrid from "./HeatmapGrid";
import NarrativesList from "./NarrativesList";

interface HomeClientProps {
  initialView: "heatmap" | "narratives";
  heatmapError?: string | null;
  narrativesError?: string | null;
}

interface RefreshableComponentProps {
  error?: string | null;
  refreshTrigger?: number;
}

export default function HomeClient({
  initialView,
  heatmapError,
  narrativesError,
}: HomeClientProps) {
  const [view, setView] = useState<"heatmap" | "narratives">(initialView);
  const [mounted, setMounted] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleViewChange = (newView: "heatmap" | "narratives") => {
    setView(newView);
  };

  const handleRefreshComplete = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  // Prevent hydration mismatch by showing loading state until mounted
  if (!mounted) {
    return (
      <div>
        <Header
          onViewChange={handleViewChange}
          onRefreshComplete={handleRefreshComplete}
        />
        <div style={{ padding: "20px" }}>
          <div
            style={{
              padding: "40px",
              textAlign: "center",
              color: "var(--fg-muted)",
              fontSize: "16px",
            }}
          >
            Loading dashboard...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Header
        onViewChange={handleViewChange}
        onRefreshComplete={handleRefreshComplete}
      />
      <div style={{ padding: "20px" }}>
        {view === "heatmap" ? (
          <HeatmapGrid error={heatmapError} refreshTrigger={refreshTrigger} />
        ) : (
          <NarrativesList
            error={narrativesError}
            refreshTrigger={refreshTrigger}
          />
        )}
      </div>
    </div>
  );
}
