"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import RefreshButton from "./RefreshButton";

interface HeaderProps {
  onViewChange?: (view: "heatmap" | "narratives") => void;
  refreshTrigger?: number;
  onRefreshComplete?: () => void;
}

const STORAGE_KEY = "primecipher.home.view";

export default function Header({
  onViewChange,
  refreshTrigger,
  onRefreshComplete,
}: HeaderProps) {
  const searchParams = useSearchParams();
  const [mounted, setMounted] = useState(false);
  const [currentView, setCurrentView] = useState<"heatmap" | "narratives">(
    "heatmap",
  );

  useEffect(() => {
    setMounted(true);

    // Initialize view from URL params
    const urlView = searchParams.get("view") || "heatmap";
    const initialView = urlView === "narratives" ? "narratives" : "heatmap";
    setCurrentView(initialView);

    // Read from localStorage on mount and update if different
    const stored = localStorage.getItem(STORAGE_KEY);
    if (
      stored &&
      (stored === "heatmap" || stored === "narratives") &&
      stored !== initialView
    ) {
      setCurrentView(stored);
      onViewChange?.(stored);
    }
  }, [searchParams, onViewChange]);

  const handleViewChange = (newView: "heatmap" | "narratives") => {
    setCurrentView(newView);
    localStorage.setItem(STORAGE_KEY, newView);
    onViewChange?.(newView);
  };

  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "16px 0",
        borderBottom: "1px solid #e5e5e5",
        marginBottom: "24px",
      }}
    >
      {/* Left: PrimeCipher branding */}
      <div>
        <Link
          href="/"
          style={{
            fontSize: "24px",
            fontWeight: "bold",
            color: "#333",
            textDecoration: "none",
          }}
        >
          PrimeCipher
        </Link>
      </div>

      {/* Center: Navigation buttons */}
      <nav
        style={{
          display: "flex",
          gap: "24px",
        }}
      >
        <button
          onClick={() => handleViewChange("heatmap")}
          style={{
            color: currentView === "heatmap" ? "#0066cc" : "#666",
            textDecoration: "none",
            fontWeight: currentView === "heatmap" ? "600" : "400",
            padding: "8px 12px",
            borderRadius: "6px",
            backgroundColor:
              currentView === "heatmap" ? "#f0f8ff" : "transparent",
            border: "none",
            cursor: "pointer",
            fontSize: "16px",
          }}
        >
          Heatmap
        </button>
        <button
          onClick={() => handleViewChange("narratives")}
          style={{
            color: currentView === "narratives" ? "#0066cc" : "#666",
            textDecoration: "none",
            fontWeight: currentView === "narratives" ? "600" : "400",
            padding: "8px 12px",
            borderRadius: "6px",
            backgroundColor:
              currentView === "narratives" ? "#f0f8ff" : "transparent",
            border: "none",
            cursor: "pointer",
            fontSize: "16px",
          }}
        >
          Narratives
        </button>
      </nav>

      {/* Right: Refresh button */}
      <div>
        <RefreshButton onRefreshComplete={onRefreshComplete} />
      </div>
    </header>
  );
}
