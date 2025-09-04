"use client";

import { useEffect, useState } from "react";

interface StaleBannerProps {
  stale: boolean;
  lastUpdated?: number | null;
}

function formatRelativeTime(timestamp: number): string {
  const now = Date.now();
  const diffMs = now - timestamp;
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return "just now";
  } else if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else {
    return `${diffDays}d ago`;
  }
}

export default function StaleBanner({ stale, lastUpdated }: StaleBannerProps) {
  const [relativeTime, setRelativeTime] = useState<string>("");

  useEffect(() => {
    if (!lastUpdated) {
      setRelativeTime("");
      return;
    }

    // Convert Unix timestamp to milliseconds
    const timestamp = lastUpdated * 1000;
    setRelativeTime(formatRelativeTime(timestamp));

    // Update every minute
    const interval = setInterval(() => {
      setRelativeTime(formatRelativeTime(timestamp));
    }, 60000);

    return () => clearInterval(interval);
  }, [lastUpdated]);

  if (stale) {
    return (
      <div
        style={{
          background: "#fef3cd",
          border: "1px solid #f6d55c",
          borderRadius: "6px",
          padding: "12px",
          marginBottom: "16px",
          color: "#856404",
        }}
      >
        ⚠️ Data may be stale. Last updated {relativeTime || "unknown"}
      </div>
    );
  }

  return (
    <div
      style={{
        background: "#d1edff",
        border: "1px solid #74c0fc",
        borderRadius: "6px",
        padding: "8px 12px",
        marginBottom: "16px",
        color: "#0c5460",
        fontSize: "14px",
      }}
    >
      ✓ Fresh as of {relativeTime || "unknown"}
    </div>
  );
}
