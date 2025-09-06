"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/config";
import type { ParentItem } from "@/lib/api";

interface ParentsListProps {
  narrative: string;
  initial: {
    items: ParentItem[];
    nextCursor?: string | null;
  };
  debug?: boolean;
}

export default function ParentsList({
  narrative,
  initial,
  debug = false,
}: ParentsListProps) {
  const [items, setItems] = useState<ParentItem[]>(initial.items);
  const [nextCursor, setNextCursor] = useState<string | null | undefined>(
    initial.nextCursor,
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMore = async () => {
    if (!nextCursor || loading) return;

    setLoading(true);
    setError(null);

    try {
      const url = new URL(`${API_BASE}/parents/${narrative}`);
      url.searchParams.set("limit", "25");
      url.searchParams.set("cursor", nextCursor);
      if (debug) {
        url.searchParams.set("debug", "true");
      }

      const response = await fetch(url.toString());

      if (!response.ok) {
        if (response.status === 400) {
          throw new Error("Invalid cursor");
        }
        throw new Error(`Failed to load: ${response.status}`);
      }

      const data = await response.json();
      setItems((prev) => [...prev, ...data.items]);
      setNextCursor(data.nextCursor ?? null);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load more";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number): string => {
    if (price >= 1) {
      return `$${price.toFixed(2)}`;
    } else if (price >= 0.01) {
      return `$${price.toFixed(4)}`;
    } else {
      return `$${price.toExponential(2)}`;
    }
  };

  const formatMarketCap = (marketCap: number): string => {
    if (marketCap >= 1e12) {
      return `$${(marketCap / 1e12).toFixed(1)}T`;
    } else if (marketCap >= 1e9) {
      return `$${(marketCap / 1e9).toFixed(1)}B`;
    } else if (marketCap >= 1e6) {
      return `$${(marketCap / 1e6).toFixed(1)}M`;
    } else if (marketCap >= 1e3) {
      return `$${(marketCap / 1e3).toFixed(1)}K`;
    } else {
      return `$${marketCap.toFixed(0)}`;
    }
  };

  const renderSources = (sources?: string[]): string => {
    if (!sources || sources.length === 0) return "";

    const hasCoingecko = sources.includes("coingecko");
    const hasDexscreener = sources.includes("dexscreener");

    if (hasCoingecko && hasDexscreener) {
      return "C+D";
    } else if (hasCoingecko) {
      return "C";
    } else if (hasDexscreener) {
      return "D";
    } else {
      return "";
    }
  };

  const renderItem = (item: ParentItem, index: number) => {
    // Check if item has the expected structure
    if (item.parent && typeof item.matches === "number") {
      const nameElement = item.url ? (
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            color: "var(--fg)",
            textDecoration: "none",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.textDecoration = "underline";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.textDecoration = "none";
          }}
        >
          {item.parent}
          <span style={{ fontSize: "12px", opacity: 0.7 }}>↗</span>
        </a>
      ) : (
        item.parent
      );

      return (
        <div
          key={`${item.parent}-${index}`}
          style={{
            backgroundColor: "rgba(255, 255, 255, 0.02)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "16px",
            transition: "transform 0.2s ease, box-shadow 0.2s ease",
            cursor: "pointer",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "8px",
            }}
          >
            <h3
              style={{
                margin: "0",
                fontSize: "16px",
                fontWeight: "600",
                color: "var(--fg)",
                lineHeight: "1.4",
              }}
            >
              {nameElement}
            </h3>
            {item.symbol && (
              <span
                style={{
                  backgroundColor: "rgba(255, 255, 255, 0.1)",
                  color: "var(--fg-muted)",
                  padding: "2px 8px",
                  borderRadius: "4px",
                  fontSize: "12px",
                  fontWeight: "500",
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                }}
              >
                {item.symbol}
              </span>
            )}
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "4px",
              fontSize: "14px",
              color: "var(--fg-muted)",
            }}
          >
            <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
              <span>Matches: {item.matches}</span>
              {debug && (
                <span
                  style={{
                    backgroundColor: renderSources(item.sources)
                      ? "rgba(59, 130, 246, 0.1)"
                      : "transparent",
                    color: renderSources(item.sources)
                      ? "var(--fg)"
                      : "var(--fg-muted)",
                    padding: renderSources(item.sources) ? "2px 6px" : "0",
                    borderRadius: "4px",
                    fontSize: "12px",
                    fontWeight: "500",
                    minWidth: "24px",
                    textAlign: "center",
                  }}
                >
                  {renderSources(item.sources) || "—"}
                </span>
              )}
            </div>
            {typeof item.score === "number" ? (
              <div>Score: {item.score.toFixed(4)}</div>
            ) : null}
            {(item.price !== undefined && item.price !== null) ||
            (item.marketCap !== undefined && item.marketCap !== null) ? (
              <div
                style={{
                  display: "flex",
                  gap: "12px",
                  marginTop: "4px",
                  paddingTop: "4px",
                  borderTop: "1px solid rgba(255, 255, 255, 0.1)",
                }}
              >
                {item.price !== undefined && item.price !== null && (
                  <div style={{ color: "var(--fg)", fontWeight: "500" }}>
                    {formatPrice(item.price)}
                  </div>
                )}
                {item.marketCap !== undefined && item.marketCap !== null && (
                  <div style={{ color: "var(--fg)", fontWeight: "500" }}>
                    {formatMarketCap(item.marketCap)}
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      );
    }

    // Fallback to JSON.stringify for unexpected structure
    return (
      <div
        key={`item-${index}`}
        style={{
          backgroundColor: "rgba(255, 255, 255, 0.02)",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          padding: "16px",
        }}
      >
        <pre style={{ margin: 0, fontSize: "13px", color: "var(--fg)" }}>
          {JSON.stringify(item, null, 2)}
        </pre>
      </div>
    );
  };

  return (
    <div>
      <div
        style={{
          marginBottom: "16px",
          padding: "12px",
          backgroundColor: "rgba(255, 255, 255, 0.02)",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          fontSize: "14px",
          color: "var(--fg-muted)",
        }}
      >
        Total loaded: {items.length} parents
      </div>

      {error && (
        <div
          role="alert"
          style={{
            backgroundColor: "var(--error-bg)",
            color: "var(--error-fg)",
            padding: "16px",
            borderRadius: "8px",
            marginBottom: "20px",
            border: "1px solid var(--error-fg)",
            fontSize: "14px",
          }}
        >
          {error}
        </div>
      )}

      {items.length === 0 ? (
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
          No parents yet. Try Refresh on the homepage.
        </div>
      ) : debug ? (
        <div
          style={{
            border: "1px solid var(--border)",
            borderRadius: "8px",
            overflow: "hidden",
            marginBottom: "20px",
          }}
        >
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              fontSize: "14px",
            }}
          >
            <thead>
              <tr
                style={{
                  backgroundColor: "rgba(255, 255, 255, 0.05)",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <th
                  style={{
                    padding: "12px 16px",
                    textAlign: "left",
                    fontWeight: "600",
                    color: "var(--fg)",
                    borderRight: "1px solid var(--border)",
                  }}
                >
                  Parent
                </th>
                <th
                  style={{
                    padding: "12px 16px",
                    textAlign: "left",
                    fontWeight: "600",
                    color: "var(--fg)",
                    borderRight: "1px solid var(--border)",
                  }}
                >
                  Matches
                </th>
                <th
                  style={{
                    padding: "12px 16px",
                    textAlign: "center",
                    fontWeight: "600",
                    color: "var(--fg)",
                    borderRight: "1px solid var(--border)",
                    minWidth: "60px",
                  }}
                >
                  Src
                </th>
                <th
                  style={{
                    padding: "12px 16px",
                    textAlign: "left",
                    fontWeight: "600",
                    color: "var(--fg)",
                  }}
                >
                  Details
                </th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => {
                if (item.parent && typeof item.matches === "number") {
                  const nameElement = item.url ? (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        color: "var(--fg)",
                        textDecoration: "none",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.textDecoration = "underline";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.textDecoration = "none";
                      }}
                    >
                      {item.parent}
                      <span style={{ fontSize: "12px", opacity: 0.7 }}>↗</span>
                    </a>
                  ) : (
                    item.parent
                  );

                  const sourceText = renderSources(item.sources);
                  const details = [];

                  if (typeof item.score === "number") {
                    details.push(`Score: ${item.score.toFixed(4)}`);
                  }

                  if (item.symbol) {
                    details.push(`Symbol: ${item.symbol}`);
                  }

                  if (item.price !== undefined && item.price !== null) {
                    details.push(formatPrice(item.price));
                  }

                  if (item.marketCap !== undefined && item.marketCap !== null) {
                    details.push(formatMarketCap(item.marketCap));
                  }

                  return (
                    <tr
                      key={`${item.parent}-${index}`}
                      style={{
                        borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
                        transition: "background-color 0.2s ease",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor =
                          "rgba(255, 255, 255, 0.02)";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = "transparent";
                      }}
                    >
                      <td
                        style={{
                          padding: "12px 16px",
                          borderRight: "1px solid var(--border)",
                          fontWeight: "500",
                          color: "var(--fg)",
                        }}
                      >
                        {nameElement}
                      </td>
                      <td
                        style={{
                          padding: "12px 16px",
                          borderRight: "1px solid var(--border)",
                          color: "var(--fg-muted)",
                        }}
                      >
                        {item.matches}
                      </td>
                      <td
                        style={{
                          padding: "12px 16px",
                          borderRight: "1px solid var(--border)",
                          textAlign: "center",
                        }}
                      >
                        <span
                          style={{
                            backgroundColor: sourceText
                              ? "rgba(59, 130, 246, 0.1)"
                              : "transparent",
                            color: sourceText ? "var(--fg)" : "var(--fg-muted)",
                            padding: sourceText ? "2px 6px" : "0",
                            borderRadius: "4px",
                            fontSize: "12px",
                            fontWeight: "500",
                            minWidth: "24px",
                            display: "inline-block",
                          }}
                        >
                          {sourceText || "—"}
                        </span>
                      </td>
                      <td
                        style={{
                          padding: "12px 16px",
                          color: "var(--fg-muted)",
                          fontSize: "13px",
                        }}
                      >
                        {details.join(" • ")}
                      </td>
                    </tr>
                  );
                }

                // Fallback for unexpected structure
                return (
                  <tr
                    key={`item-${index}`}
                    style={{
                      borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
                    }}
                  >
                    <td
                      colSpan={4}
                      style={{
                        padding: "12px 16px",
                        color: "var(--fg-muted)",
                        fontFamily: "monospace",
                        fontSize: "12px",
                      }}
                    >
                      <pre style={{ margin: 0 }}>
                        {JSON.stringify(item, null, 2)}
                      </pre>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "16px",
            marginBottom: "20px",
          }}
        >
          {items.map((item, index) => renderItem(item, index))}
        </div>
      )}

      {nextCursor && (
        <button
          onClick={loadMore}
          disabled={loading}
          style={{
            padding: "12px 24px",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            backgroundColor: "rgba(255, 255, 255, 0.02)",
            color: "var(--fg)",
            opacity: loading ? 0.7 : 1,
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: "14px",
            fontWeight: "500",
            transition: "transform 0.2s ease, box-shadow 0.2s ease",
          }}
        >
          {loading ? "Loading…" : "Load more"}
        </button>
      )}
    </div>
  );
}
