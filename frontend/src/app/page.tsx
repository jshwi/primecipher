// frontend/src/app/page.tsx
import Link from 'next/link';
import { fetchJSON } from '@/lib/api';

type NarrativeRow = {
  narrative: string;
  heatScore: number;
  window: string;
  signals: { onchainVolumeUsd: number; onchainLiquidityUsd: number; ctMentions: number };
  parents: string[];
  lastUpdated?: string;
};

export default async function Page() {
  let data: NarrativeRow[] = [];
  try {
    data = await fetchJSON('/narratives?window=24h');
  } catch {
    data = [];
  }

  return (
    <main style={{ padding: 24, fontFamily: 'ui-sans-serif, system-ui' }}>
      <h1 style={{ fontSize: 28, marginBottom: 12 }}>Narratives</h1>
      <div style={{ fontSize: 12, opacity: 0.75, marginBottom: 16 }}>Window: 24h</div>

      <div style={{ border: '1px solid #333', borderRadius: 8, overflow: 'hidden' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '160px 100px 200px 1fr', padding: '10px 12px', background: '#111', fontSize: 12, opacity: 0.85 }}>
          <div>Narrative</div>
          <div>Heat</div>
          <div>On-chain (vol / liq)</div>
          <div>Parents</div>
        </div>

        {data.length === 0 && (
          <div style={{ padding: 16, fontSize: 14, opacity: 0.7 }}>No narratives yet. Try running the backend refresh.</div>
        )}

        {data.map((n) => (
          <div key={n.narrative} style={{ display: 'grid', gridTemplateColumns: '160px 100px 200px 1fr', padding: '12px', borderTop: '1px solid #222' }}>
            <div>
              <Link href={`/n/${n.narrative}`} style={{ textDecoration: 'underline' }}>{n.narrative}</Link>
              {n.lastUpdated && <div style={{ fontSize: 11, opacity: 0.6 }}>updated {n.lastUpdated}</div>}
            </div>
            <div>{n.heatScore.toFixed(1)}</div>
            <div>
              ${Math.round(n.signals.onchainVolumeUsd).toLocaleString()} / ${Math.round(n.signals.onchainLiquidityUsd).toLocaleString()}
            </div>
            <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {n.parents?.join(', ') || '—'}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
