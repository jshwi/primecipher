import Link from 'next/link';
import { fetchJSON } from '@/lib/api';

export default async function Page() {
  const narratives = await fetchJSON('/narratives?window=24h');
  return (
    <main style={{ padding: 24, fontFamily: 'ui-sans-serif, system-ui' }}>
      <h1 style={{ fontSize: 28, marginBottom: 16 }}>Narrative Heatmap (stub)</h1>
      <ul style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 12 }}>
        {narratives.map((n: any) => (
          <li key={n.narrative} style={{ border: '1px solid #333', borderRadius: 8, padding: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <strong>{n.narrative}</strong>
              <span>{Math.round(n.heatScore)}</span>
            </div>
            <div style={{ fontSize: 12, opacity: 0.8, marginTop: 8 }}>
              vol {n.signals.onchainVolumeUsd.toLocaleString()} · liq {n.signals.onchainLiquidityUsd.toLocaleString()} · ct {n.signals.ctMentions.toLocaleString()}
            </div>
            <div style={{ marginTop: 8 }}>
              <Link href={`/n/${n.narrative}`}>View parents →</Link>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
