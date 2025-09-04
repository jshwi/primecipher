"use client";

import { useEffect, useState } from "react";

interface HomeToggleProps {
  view: "heatmap" | "narratives";
  onChange: (view: "heatmap" | "narratives") => void;
}

const STORAGE_KEY = "primecipher.home.view";

export default function HomeToggle({ view, onChange }: HomeToggleProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);

    // Read from localStorage on mount and update if different
    const stored = localStorage.getItem(STORAGE_KEY);
    if (
      stored &&
      (stored === "heatmap" || stored === "narratives") &&
      stored !== view
    ) {
      onChange(stored);
    }
  }, [view, onChange]);

  const handleToggle = (newView: "heatmap" | "narratives") => {
    onChange(newView);
    localStorage.setItem(STORAGE_KEY, newView);
  };

  // Prevent hydration mismatch by not rendering until mounted
  if (!mounted) {
    return (
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
    );
  }

  return (
    <div
      style={{
        display: "flex",
        backgroundColor: "rgba(255, 255, 255, 0.02)",
        borderRadius: "8px",
        padding: "4px",
        width: "fit-content",
        border: "1px solid var(--border)",
      }}
    >
      <button
        onClick={() => handleToggle("heatmap")}
        style={{
          padding: "8px 16px",
          fontSize: "14px",
          fontWeight: "500",
          borderRadius: "6px",
          border: "none",
          cursor: "pointer",
          transition: "all 0.2s ease",
          backgroundColor: view === "heatmap" ? "var(--fg)" : "transparent",
          color: view === "heatmap" ? "var(--bg)" : "var(--fg-muted)",
        }}
        onMouseEnter={(e) => {
          if (view !== "heatmap") {
            e.currentTarget.style.color = "var(--fg)";
          }
        }}
        onMouseLeave={(e) => {
          if (view !== "heatmap") {
            e.currentTarget.style.color = "var(--fg-muted)";
          }
        }}
      >
        Heatmap
      </button>
      <button
        onClick={() => handleToggle("narratives")}
        style={{
          padding: "8px 16px",
          fontSize: "14px",
          fontWeight: "500",
          borderRadius: "6px",
          border: "none",
          cursor: "pointer",
          transition: "all 0.2s ease",
          backgroundColor: view === "narratives" ? "var(--fg)" : "transparent",
          color: view === "narratives" ? "var(--bg)" : "var(--fg-muted)",
        }}
        onMouseEnter={(e) => {
          if (view !== "narratives") {
            e.currentTarget.style.color = "var(--fg)";
          }
        }}
        onMouseLeave={(e) => {
          if (view !== "narratives") {
            e.currentTarget.style.color = "var(--fg-muted)";
          }
        }}
      >
        Narratives
      </button>
    </div>
  );
}
