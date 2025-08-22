// frontend/src/app/n/[narrative]/_components/ParentsTable.tsx
'use client';

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

export default function ParentsTable({ rows }: { rows: ParentRow[] }) {
  return (
    <div style={{ marginTop: 16, border: '1px solid #333', borderRadius: 8, overflow: 'hidden' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '120px 140px 120px 1fr', padding: '10px 12px', background: '#111', fontSize: 12, opacity: 0.85 }}>
        <div>Parent</div>
        <div>Children (new24h)</div>
        <div>Survival h24</div>
        <div>Liquidity funnel / Top child</div>
      </div>
      {rows.length === 0 && (
        <div style={{ padding: 16, fontSize: 14, opacity: 0.7 }}>No data yet for this narrative.</div>
      )}
      {rows.map((r) => (
        <div key={r.parent} style={{ display: 'grid', gridTemplateColumns: '120px 140px 120px 1fr', padding: '12px', borderTop: '1px solid #222' }}>
          <div style={{ fontWeight: 600 }}>{r.parent}</div>
          <div>{r.childrenCount} <span style={{ opacity: 0.7 }}>({r.childrenNew24h})</span></div>
          <div>{(r.survivalRates.h24 * 100).toFixed(1)}%</div>
          <div style={{ fontSize: 13 }}>
            <div style={{ opacity: 0.85 }}>
              parent liq: ${Math.round(r.liquidityFunnel.parentLiquidityUsd).toLocaleString()} · children liq: ${Math.round(r.liquidityFunnel.childrenLiquidityUsd).toLocaleString()}
            </div>
            {r.topChild?.symbol ? (
              <div style={{ marginTop: 6 }}>
                top child: <strong>{r.topChild.symbol}</strong>
                {' · '}liq ${Math.round(r.topChild.liquidityUsd).toLocaleString()}
                {' · '}vol24h ${Math.round(r.topChild.volume24hUsd).toLocaleString()}
                {r.topChild.ageHours != null && <> {' · '}age {r.topChild.ageHours.toFixed(1)}h</>}
                {r.topChild.matched?.pairAddress && (
                  <>
                    {' · '}
                    <a
                      href={`https://dexscreener.com/solana/${r.topChild.matched.pairAddress}`}
                      target="_blank"
                      rel="noreferrer"
                      style={{ textDecoration: 'underline' }}
                    >
                      view pair
                    </a>
                  </>
                )}
                {r.topChild.matched?.term && (
                  <span style={{ marginLeft: 8, opacity: 0.7 }}>
                    (match: {r.topChild.matched.field} “{r.topChild.matched.term}”)
                  </span>
                )}
              </div>
            ) : (
              <div style={{ marginTop: 6, opacity: 0.7 }}>No qualifying children</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
