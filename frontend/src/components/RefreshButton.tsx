'use client'
import { useTransition, useState } from 'react'
import { useRouter } from 'next/navigation'
import { doRefresh } from '@/lib/api'

export default function RefreshButton() {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()
  const [err, setErr] = useState<string | null>(null)

  async function run() {
    setErr(null)
    await doRefresh('24h')     // calls your POST /refresh
    router.refresh()           // ask Next to re-render the current route
  }

  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'end',gap:6}}>
      <button
        onClick={() => startTransition(run)}
        disabled={isPending}
        style={{padding:'8px 12px',border:'1px solid #222',borderRadius:6,opacity:isPending?0.7:1}}
      >
        {isPending ? 'Refreshing…' : 'Refresh'}
      </button>
      {err && (
        <div style={{background:'#fee', color:'#900', padding:'6px 8px', borderRadius:6, fontSize:13, maxWidth:360}}>
          {err}
        </div>
      )}
    </div>
  )
}
