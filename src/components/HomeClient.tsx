"use client";

import { useState, useEffect } from "react";
import HomeToggle from "./HomeToggle";
import HeatmapGrid from "./HeatmapGrid";
import NarrativesList from "./NarrativesList";
import RefreshButton from "./RefreshButton";

interface HomeClientProps {
  initialView: "heatmap" | "narratives";
  heatmapError?: string | null;
  narrativesError?: string | null;
}

export default function HomeClient({
  initialView,
  heatmapError,
  narrativesError,
}: HomeClientProps) {
  const [view, setView] = useState<"heatmap" | "narratives">(initialView);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleViewChange = (newView: "heatmap" | "narratives") => {
    setView(newView);
  };

  // Prevent hydration mismatch by showing loading state until mounted
  if (!mounted) {
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
          <h1 style={{ fontSize: 24, margin: 0 }}>PrimeCipher Dashboard</h1>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "16px",
            }}
          >
            <div
              style={{
                display: "flex",
                backgroundColor: "rgba(255, 255, 255, 0.02)",
                borderRadius: "8px",
                padding: "4px",
                width: "fit-content",
              }}
            >
              <div
                style={{
                  padding: "8px 16px",
                  fontSize: "14px",
                  fontWeight: "500",
                  color: "var(--fg-muted)",
                }}
              >
                Loading...
              </div>
            </div>
            <RefreshButton />
          </div>
        </div>
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
    );
  }

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
        <h1 style={{ fontSize: 24, margin: 0 }}>PrimeCipher Dashboard</h1>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "16px",
          }}
        >
          <HomeToggle view={view} onChange={handleViewChange} />
          <RefreshButton />
        </div>
      </div>

      {view === "heatmap" ? (
        <HeatmapGrid error={heatmapError} />
      ) : (
        <NarrativesList error={narrativesError} />
      )}
    </div>
  );
}
