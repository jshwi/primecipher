"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import RefreshButton from "./RefreshButton";

export default function Header() {
  const searchParams = useSearchParams();
  const currentView = searchParams.get("view") || "heatmap";

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

      {/* Center: Navigation links */}
      <nav
        style={{
          display: "flex",
          gap: "24px",
        }}
      >
        <Link
          href="/?view=heatmap"
          style={{
            color: currentView === "heatmap" ? "#0066cc" : "#666",
            textDecoration: "none",
            fontWeight: currentView === "heatmap" ? "600" : "400",
            padding: "8px 12px",
            borderRadius: "6px",
            backgroundColor:
              currentView === "heatmap" ? "#f0f8ff" : "transparent",
          }}
        >
          Heatmap
        </Link>
        <Link
          href="/?view=narratives"
          style={{
            color: currentView === "narratives" ? "#0066cc" : "#666",
            textDecoration: "none",
            fontWeight: currentView === "narratives" ? "600" : "400",
            padding: "8px 12px",
            borderRadius: "6px",
            backgroundColor:
              currentView === "narratives" ? "#f0f8ff" : "transparent",
          }}
        >
          Narratives
        </Link>
      </nav>

      {/* Right: Refresh button */}
      <div>
        <RefreshButton />
      </div>
    </header>
  );
}
