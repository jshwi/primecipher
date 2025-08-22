// frontend/src/app/n/page.tsx
import Link from 'next/link';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

type Narr = { key: string; parents: string[]; num_parents: number };
type Resp = { narratives: Narr[] };

export const revalidate = 0; // always fresh

export default async function NarrativesIndex() {
  let data: Resp = { narratives: [] };
  try {
    const res = await fetch(`${API_BASE}/narratives`, { cache: 'no-store' });
    if (res.ok) data = await res.json();
  } catch {
    // best-effort; leave empty
  }

  const items = data.narratives || [];

  return (
    <div style={{ maxWidth: 960, margin: '24px auto', padding: '0 16px' }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Narratives</h1>
      <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 16 }}>
        Pick a narrative to open its heatmap and backtests.
      </div>

      {items.length === 0 && (
        <div style={{ border: '1px solid #222', borderRadius: 8, padding: 16, background: '#0f0f0f' }}>
          No narratives found. Make sure the backend seeds are loaded and the API is running.
        </div>
      )}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
          gap: 12,
        }}
      >
        {items.map((n) => (
          <Link
            key={n.key}
            href={`/n/${encodeURIComponent(n.key)}`}
            style={{
              border: '1px solid #222',
              borderRadius: 10,
              background: '#0f0f0f',
              padding: 14,
              textDecoration: 'none',
              color: 'white',
              display: 'flex',
              flexDirection: 'column',
              gap: 6,
            }}
          >
            <div style={{ fontWeight: 700, fontSize: 16, textTransform: 'lowercase' }}>{n.key}</div>
            <div style={{ fontSize: 13, opacity: 0.8 }}>{n.num_parents} parent{n.num_parents === 1 ? '' : 's'}</div>
            {n.parents.length > 0 && (
              <div style={{ fontSize: 12, opacity: 0.7, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {n.parents.join(' · ')}
              </div>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}

