// frontend/src/app/page.tsx
import Link from 'next/link';
import LiveToolbar from './_components/LiveToolbar';
import { fetchJSON } from '@/lib/api';

export const dynamic = 'force-dynamic';

type NarrativeRow = {
  narrative: string;
  heatScore: number;
  window: string;
  signals: { onchainVolumeUsd: number; onchainLiquidityUsd: number; ctMentions: number };
  parents: string[];
  lastUpdated?: string;
};

export default async function Page({ searchParams }: { searchParams?: { [key: string]: string | string[] | undefined } }) {
  const source = typeof searchParams?.source === 'string' ? (searchParams!.source as string) : '';
  const isLive = source.toLowerCase() === 'live';
  const query = `/narratives?window=24h${isLive ? '&source=live' : ''}`;

  let data: NarrativeRow[] = [];
  try {
    data = await fetchJSON(query);
  } catch {
    data = [];
  }

  return (
    <main style={{ padding: 24, fontFamily: 'ui-sans-serif, system-ui' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
        <h1 style={{ fontSize: 28, marginBottom: 0 }}>Narratives</h1>
        <span style={{ fontSize: 12, opacity: 0.7 }}>Window: 24h</span>
        <span style={{ marginLeft: 'auto' }}>
          <LiveToolbar windowParam="24h" />
        </span>
      </div>

      <div style={{ marginTop: 16, border: '1px solid #333', borderRadius: 8, overflow: 'hidden' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '160px 100px 220px 1fr',
            padding: '10px 12px',
            background: '#111',
            fontSize: 12,
            opacity: 0.85,
          }}
        >
          <div>Narrative</div>
          <div>Heat</div>
          <div>On-chain (vol / liq)</div>
          <div>Parents</div>
        </div>

        {data.length === 0 && (
          <div style={{ padding: 16, fontSize: 14, opacity: 0.7 }}>No narratives yet. Try “Refresh”.</div>
        )}

        {data.map((n) => (
          <div
            key={n.narrative}
            style={{ display: 'grid', gridTemplateColumns: '160px 100px 220px 1fr', padding: '12px', borderTop: '1px solid #222' }}
          >
            <div>
              <Link href={`/n/${n.narrative}${isLive ? '?source=live' : ''}`} style={{ textDecoration: 'underline' }}>
                {n.narrative}
              </Link>
              {n.lastUpdated && <div style={{ fontSize: 11, opacity: 0.6 }}>updated {n.lastUpdated}</div>}
            </div>
            <div>{n.heatScore.toFixed(1)}</div>
            <div>
              ${Math.round(n.signals.onchainVolumeUsd).toLocaleString()} / $
              {Math.round(n.signals.onchainLiquidityUsd).toLocaleString()}
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

