import { getParents } from '@/lib/api'

export default async function NarrativePage({ params }: { params: Promise<{ narrative: string }> }) {
  const { narrative } = await params
  const data = await getParents(narrative, '24h')
  const parents: { parent: string; matches?: number }[] = data?.items || []

  return (
    <main>
      <h1 style={{fontSize:24,margin:'8px 0 16px'}}>{narrative}</h1>
      {parents.length === 0 ? (
        <div>No data yet for this narrative.</div>
      ) : (
        <div style={{border:'1px solid #222',borderRadius:8,overflow:'hidden'}}>
          <div style={{display:'grid',gridTemplateColumns:'2fr 1fr',fontWeight:600,padding:'8px 12px',background:'#111'}}>
            <div>Parent</div><div style={{textAlign:'right'}}>Matches</div>
          </div>
          {parents.map((p, i) => (
            <div key={i} style={{display:'grid',gridTemplateColumns:'2fr 1fr',padding:'10px 12px',borderTop:'1px solid #222'}}>
              <div>{p.parent}</div><div style={{textAlign:'right'}}>{p.matches ?? ''}</div>
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
