import Link from 'next/link'
import { getNarratives, doRefresh } from '@/lib/api'

function fmt(ts?: number) {
  if (!ts) return null
  const s = new Date(ts * 1000).toLocaleString()
  return <div style={{color:'#888', marginBottom: 8}}>Last refresh: {s}</div>
}

export default async function Page() {
  const data = await getNarratives('24h')
  const rows: string[] = data?.items || []

  async function refreshAction() {
    'use server'
    await doRefresh('24h')
  }

  return (
    <main>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
        <h1 style={{fontSize:24,margin:'8px 0 16px'}}>Narratives (24h)</h1>
        <form action={refreshAction}>
          <button style={{padding:'8px 12px',border:'1px solid #222',borderRadius:6}}>Refresh</button>
        </form>
      </div>

      {fmt(data?.lastRefresh)}

      {rows.length === 0 ? (
        <div style={{padding:12,border:'1px dashed #444',borderRadius:8,color:'#888'}}>
          No narratives yet. Add one in <code>backend/seeds/narratives.seed.json</code> then hit Refresh.
        </div>
      ) : (
        <div style={{display:'grid',gap:8}}>
          {rows.map((n) => (
            <Link key={n} href={`/n/${encodeURIComponent(n)}`}
              style={{padding:12,border:'1px solid #222',borderRadius:8,textDecoration:'none'}}>
              {n}
            </Link>
          ))}
        </div>
      )}
    </main>
  )
}
