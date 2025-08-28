import Link from 'next/link'
import { getNarratives, doRefresh } from '@/lib/api'

export default async function Page() {
  const data = await getNarratives('24h')
  const rows: { narrative: string; count?: number }[] = data?.items || []
  return (
    <main>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
        <h1 style={{fontSize:24,margin:'8px 0 16px'}}>Narratives (24h)</h1>
        <form action={async () => { 'use server'; await doRefresh('24h') }}>
          <button style={{padding:'8px 12px',border:'1px solid #222',borderRadius:6}}>Refresh</button>
        </form>
      </div>
      {rows.length === 0 ? (
        <div>No narratives found. Make sure the backend is running and seeds are loaded.</div>
      ) : (
        <div style={{display:'grid',gap:8}}>
          {rows.map((r) => (
            <Link key={r.narrative} href={`/n/${encodeURIComponent(r.narrative)}`} style={{padding:12,border:'1px solid #222',borderRadius:8,textDecoration:'none'}}>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                <span>{r.narrative}</span>
                <span>{r.count ?? ''}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </main>
  )
}
