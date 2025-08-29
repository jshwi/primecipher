// frontend/src/lib/api.ts

const BASE =
  process.env.NEXT_PUBLIC_API_BASE?.trim() || "http://127.0.0.1:8000";

export type ParentItem = {
  parent: string;
  matches: number;
  score?: number;
};

export type ParentsResp = {
  narrative: string;
  window: string;
  items: ParentItem[];
  nextCursor?: string | null;
};

export type NarrativesResp = {
  items: string[];
  lastRefresh?: number | null;
};

/** GET /narratives */
export async function getNarratives(): Promise<NarrativesResp> {
  const r = await fetch(`${BASE}/narratives`, { cache: "no-store" });
  if (!r.ok) throw new Error(`GET /narratives ${r.status}`);
  return r.json();
}

/** GET /parents/:narrative?limit&cursor */
export async function getParents(
  narrative: string,
  opts?: { limit?: number; cursor?: string | null }
): Promise<ParentsResp> {
  const u = new URL(`${BASE}/parents/${encodeURIComponent(narrative)}`);
  u.searchParams.set("limit", String(opts?.limit ?? 25));
  if (opts?.cursor) u.searchParams.set("cursor", opts.cursor);
  const r = await fetch(u.toString(), { cache: "no-store" });
  if (!r.ok) throw new Error(`GET /parents/${narrative} ${r.status}`);
  return r.json();
}

/* ---------- Optional: async refresh endpoints (only if you wired them) ---------- */

const DEV_REFRESH_TOKEN = process.env.NEXT_PUBLIC_REFRESH_TOKEN || "";

function authHeaders() {
  return DEV_REFRESH_TOKEN
    ? { Authorization: `Bearer ${DEV_REFRESH_TOKEN}` }
    : undefined;
}

/** POST /refresh (sync path) */
export async function doRefresh(windowParam?: string) {
  const u = new URL(`${BASE}/refresh`);
  if (windowParam) u.searchParams.set("window", windowParam);
  const r = await fetch(u.toString(), {
    method: "POST",
    headers: authHeaders(),
  });
  if (!r.ok) throw new Error(`POST /refresh ${r.status}`);
  return r.json();
}

/** POST /refresh/async → { jobId } */
export async function startRefreshJob(): Promise<{ jobId: string }> {
  const r = await fetch(`${BASE}/refresh/async`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!r.ok) throw new Error(`POST /refresh/async ${r.status}`);
  return r.json();
}

export type RefreshJob = {
  id: string;
  state: "queued" | "running" | "done" | "error";
  ts: number;
  error?: string | null;
};

/** GET /refresh/status/:jobId */
export async function getRefreshStatus(jobId: string): Promise<RefreshJob> {
  const r = await fetch(`${BASE}/refresh/status/${jobId}`, {
    headers: authHeaders(),
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`GET /refresh/status ${r.status}`);
  return r.json();
}
