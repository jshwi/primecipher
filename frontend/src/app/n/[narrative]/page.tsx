// frontend/src/app/n/[narrative]/page.tsx
import Link from 'next/link';
import { fetchJSON } from '@/lib/api';
import ParentsTable from './_components/ParentsTable';

type ParentRow = {
  parent: string;
  narrative: string;
  childrenCount: number;
  childrenNew24h: number;
  survivalRates: { h24: number; d7: number };
  liquidityFunnel: { parentLiquidityUsd: number; childrenLiquidityUsd: number };
  topChild: {
    symbol: string | null;
    liquidityUsd: number;
    volume24hUsd: number;
    ageHours: number | null;
    holders: number | null;
    matched?: { field?: string; term?: string; dexId?: string; pairAddress?: string };
  };
  lastUpdated?: string;
};

export default async function Page({ params }: { params: { narrative: string } }) {
  const { narrative } = params;

  let rows: ParentRow[] = [];
  try {
    rows = await fetchJSON(`/parents/${narrative}?window=24h`);
  } catch {
    rows = [];
  }
  const last = rows?.[0]?.lastUpdated ?? '—';

  return (
    <main style={{ padding: 24, fontFamily: 'ui-sans-serif, system-ui' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
        <h1 style={{ fontSize: 28 }}>Narrative: {narrative}</h1>
        <span style={{ fontSize: 12, opacity: 0.7 }}>Last updated: {last}</span>
        <span style={{ marginLeft: 'auto', fontSize: 12 }}>
          <Link href="/">← Back</Link>
        </span>
      </div>
      <ParentsTable rows={rows} />
    </main>
  );
}
