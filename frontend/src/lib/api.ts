
const base = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'
export async function getNarratives(windowParam?: string) {
  const u = new URL(base + '/narratives')
  if (windowParam) u.searchParams.set('window', windowParam)
  const r = await fetch(u.toString(), { cache: 'no-store' })
  if (!r.ok) throw new Error('failed')
  return r.json()
}
export async function getParents(narrative: string, windowParam?: string) {
  const u = new URL(base + `/parents/${encodeURIComponent(narrative)}`)
  if (windowParam) u.searchParams.set('window', windowParam)
  const r = await fetch(u.toString(), { cache: 'no-store' })
  if (!r.ok) throw new Error('failed')
  return r.json()
}
export async function doRefresh(windowParam?: string) {
  const u = new URL(base + '/refresh')
  if (windowParam) u.searchParams.set('window', windowParam)
  const r = await fetch(u.toString(), { method: 'POST' })
  if (!r.ok) throw new Error('failed')
  return r.json()
}
