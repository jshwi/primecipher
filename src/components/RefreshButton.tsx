"use client";
import { useTransition, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { startRefreshJob, getRefreshStatus } from "@/lib/api";

export default function RefreshButton() {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [err, setErr] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [state, setState] = useState<
    "idle" | "queued" | "running" | "done" | "error"
  >("idle");
  const [progress, setProgress] = useState<{
    narrativesDone?: number;
    narrativesTotal?: number;
  }>({});

  // poll when we have a job id
  useEffect(() => {
    if (!jobId) return;
    let stop = false;
    let pollCount = 0;
    const maxPolls = 10; // 10 seconds max

    async function poll() {
      if (stop || pollCount >= maxPolls) {
        if (pollCount >= maxPolls) {
          setErr("Refresh timeout - please check status manually");
        }
        return;
      }

      try {
        const s = await getRefreshStatus(jobId!);
        if (stop) return;

        setState(s.state);
        setProgress({
          narrativesDone: s.narrativesDone,
          narrativesTotal: s.narrativesTotal,
        });

        if (s.state === "done") {
          setTimeout(() => router.refresh(), 100); // re-render page data
        } else if (s.state === "error") {
          setErr(s.error || "Refresh failed");
        } else {
          pollCount++;
          setTimeout(poll, 1000);
        }
      } catch (e: unknown) {
        if (!stop) {
          const error = e instanceof Error ? e : new Error(String(e));
          if (error.message.includes("401")) {
            setErr("Authentication failed - check refresh token");
          } else if (error.message.includes("500")) {
            setErr("Server error - please try again later");
          } else {
            setErr(error.message || "Refresh status failed");
          }
        }
      }
    }
    poll();
    return () => {
      stop = true;
    };
  }, [jobId, router]);

  async function run() {
    setErr(null);
    setState("idle");
    setProgress({});
    try {
      const { jobId } = await startRefreshJob();
      setJobId(jobId);
      setState("queued");
    } catch (e: unknown) {
      const error = e instanceof Error ? e : new Error(String(e));
      if (error.message.includes("401")) {
        setErr("Authentication failed - check refresh token");
      } else if (error.message.includes("500")) {
        setErr("Server error - please try again later");
      } else {
        setErr(error.message || "Failed to start refresh");
      }
    }
  }

  const getStatusText = () => {
    if (
      state === "running" &&
      progress.narrativesDone !== undefined &&
      progress.narrativesTotal !== undefined
    ) {
      return `Updating… (${progress.narrativesDone}/${progress.narrativesTotal})`;
    } else if (state === "done") {
      return "Refresh complete";
    } else if (state === "queued") {
      return "Refresh started (job: " + (jobId || "unknown") + ")";
    }
    return null;
  };

  const statusText = getStatusText();

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "end",
        gap: 6,
      }}
    >
      <button
        onClick={() => startTransition(run)}
        disabled={isPending || state === "running" || state === "queued"}
        style={{
          padding: "8px 12px",
          border: "1px solid #222",
          borderRadius: 6,
          opacity: isPending || state !== "idle" ? 0.7 : 1,
        }}
      >
        {isPending ? "Starting…" : "Refresh"}
      </button>

      {statusText && (
        <div
          style={{
            background: state === "done" ? "#d1edff" : "#fff3cd",
            color: state === "done" ? "#0c5460" : "#856404",
            border:
              state === "done" ? "1px solid #74c0fc" : "1px solid #f6d55c",
            padding: "6px 8px",
            borderRadius: 6,
            fontSize: 13,
            maxWidth: 360,
          }}
        >
          {statusText}
        </div>
      )}

      {err && (
        <div
          style={{
            background: "#fee",
            color: "#900",
            padding: "6px 8px",
            borderRadius: 6,
            fontSize: 13,
            maxWidth: 360,
          }}
        >
          {err}
        </div>
      )}
    </div>
  );
}
