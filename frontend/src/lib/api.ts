const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000"

export type NarrativesResp = { items: string[]; lastRefresh?: number | null }

export async function getNarratives(): Promise<NarrativesResp> {
  const r = await fetch(`${base}/narratives`, { cache: "no-store" })
  if (!r.ok) throw new Error(`GET /narratives ${r.status}`)
  return r.json()
}

export type ParentItem = { parent: string; matches: number; score?: number }
export type ParentsResp = {
  narrative: string
  window: string
  items: ParentItem[]
  nextCursor?: string | null
}

export async function getParents(
  narrative: string,
  opts?: { limit?: number; cursor?: string | null }
): Promise<ParentsResp> {
  const u = new URL(`${base}/parents/${encodeURIComponent(narrative)}`)
  u.searchParams.set("limit", String(opts?.limit ?? 25))
  if (opts?.cursor) u.searchParams.set("cursor", opts.cursor)
  const r = await fetch(u.toString(), { cache: "no-store" })
  if (!r.ok) throw new Error(`GET /parents/${narrative} ${r.status}`)
  return r.json()
}

const devRefreshToken = process.env.NEXT_PUBLIC_REFRESH_TOKEN
export async function doRefresh(windowParam?: string) {
  const u = new URL(`${base}/refresh`)
  if (windowParam) u.searchParams.set("window", windowParam)
  const r = await fetch(u.toString(), {
    method: "POST",
    headers: devRefreshToken ? { Authorization: `Bearer ${devRefreshToken}` } : undefined,
  })
  if (!r.ok) throw new Error(`POST /refresh ${r.status}`)
  return r.json()
}
