// frontend/src/app/n/[narrative]/_components/ParentsTable.tsx
'use client';

import { useCallback, useMemo, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';

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
    matched?: { field?: string; term?: string; terms?: string[]; dexId?: string; pairAddress?: string };
  };
  lastUpdated?: string;
};

type DebugChild = {
  symbol: string | null;
  name?: string | null;
  liquidityUsd: number;
  volume24hUsd: number;
  ageHours: number | null;
  matched?: { field?: string; term?: string; terms?: string[]; dexId?: string; pairAddress?: string };
};

type DebugResp = {
  children: DebugChild[];
  counts?: { total?: number; returned?: number };
  resolved?: {
    terms?: string[];
    allowNameMatch?: boolean;
    discovery?: { dexIds?: string[]; volMinUsd?: number; liqMinUsd?: number; maxAgeHours?: number };
  };
};

function fmtUsd(n?: number) {
  const v = typeof n === 'number' ? n : 0;
  return `$${Math.round(v).toLocaleString()}`;
}

function ParentRowItem({ r }: { r: ParentRow }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resp, setResp] = useState<DebugResp | null>(null);
  const [error, setError] = useState<string | null>(null);

  const debugHref = useMemo(() => {
    return `${API_BASE}/debug/children/${encodeURIComponent(r.parent)}?narrative=${encodeURIComponent(
      r.narrative
    )}&limit=100&applyBlocklist=true`;
  }, [r.parent, r.narrative]);

  const onToggle = useCallback(async () => {
    const next = !open;
    setOpen(next);
    if (next && !resp && !loading) {
      try {
        setLoading(true);
        setError(null);
        const res = await fetch(debugHref);
        const json: DebugResp = await res.json();
        setResp(json);
      } catch (e: any) {
        setError('Failed to load children');
      } finally {
        setLoading(false);
      }
    }
  }, [open, resp, loading, debugHref]);

  const children = resp?.children ?? [];

  return (
    <>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '120px 140px 120px 1fr',
          padding: '12px',
          borderTop: '1px solid #222',
        }}
      >
        <div style={{ fontWeight: 600 }}>
          {r.parent}
          <span style={{ marginLeft: 8, fontSize: 11 }}>
            <a href={debugHref} target="_blank" rel="noreferrer" style={{ textDecoration: 'underline', opacity: 0.8 }}>
              debug
            </a>
          </span>
        </div>

        <div>
          {r.childrenCount} <span style={{ opacity: 0.7 }}>({r.childrenNew24h})</span>
        </div>

        <div>{(r.survivalRates.h24 * 100).toFixed(1)}%</div>

        <div style={{ fontSize: 13 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <div style={{ opacity: 0.85 }}>
              parent liq: {fmtUsd(r.liquidityFunnel.parentLiquidityUsd)} · children liq: {fmtUsd(r.liquidityFunnel.childrenLiquidityUsd)}
            </div>
            <button
              type="button"
              onClick={onToggle}
              disabled={loading}
              style={{
                padding: '4px 8px',
                borderRadius: 6,
                border: '1px solid #333',
                background: '#181818',
                color: '#ddd',
                cursor: 'pointer',
                fontSize: 12,
              }}
            >
              {open ? 'Hide children' : 'Show children'}
            </button>
          </div>

          {r.topChild?.symbol ? (
            <div style={{ marginTop: 6 }}>
              top child: <strong>{r.topChild.symbol}</strong>
              {' · '}liq {fmtUsd(r.topChild.liquidityUsd)}
              {' · '}vol24h {fmtUsd(r.topChild.volume24hUsd)}
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
              {r.topChild.matched?.terms && r.topChild.matched.terms.length > 0 && (
                <span style={{ marginLeft: 8, opacity: 0.7 }}>(match: {r.topChild.matched.terms.join(' & ')})</span>
              )}
            </div>
          ) : (
            <div style={{ marginTop: 6, opacity: 0.7 }}>No qualifying children</div>
          )}
        </div>
      </div>

      {open && (
        <div style={{ borderTop: '1px dashed #222', background: '#0c0c0c', padding: '10px 12px' }}>
          {loading && <div style={{ fontSize: 13, opacity: 0.8 }}>Loading children…</div>}
          {error && <div style={{ fontSize: 13, color: '#f66' }}>{error}</div>}

          {!loading && !error && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, opacity: 0.8, marginBottom: 8 }}>
                <div>returned: {resp?.counts?.returned ?? children.length}</div>
                {resp?.resolved?.terms?.length ? <div>terms: {resp?.resolved?.terms?.join(' + ')}</div> : null}
                {resp?.resolved?.discovery?.dexIds?.length ? <div>DEX: {resp?.resolved?.discovery?.dexIds?.join(', ')}</div> : null}
                {resp?.resolved?.discovery?.volMinUsd != null ? <div>vol≥{resp?.resolved?.discovery?.volMinUsd}</div> : null}
                {resp?.resolved?.discovery?.liqMinUsd != null ? <div>liq≥{resp?.resolved?.discovery?.liqMinUsd}</div> : null}
              </div>

              <div style={{ border: '1px solid #222', borderRadius: 6, overflow: 'hidden' }}>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '140px 120px 120px 100px 1fr',
                    padding: '8px 10px',
                    background: '#111',
                    fontSize: 12,
                    opacity: 0.85,
                  }}
                >
                  <div>Symbol</div>
                  <div>Liq</div>
                  <div>Vol24h</div>
                  <div>Age</div>
                  <div>Match</div>
                </div>
                {children.length === 0 && <div style={{ padding: 10, fontSize: 13, opacity: 0.7 }}>No matches.</div>}
                {children.map((c, i) => {
                  const link = c.matched?.pairAddress ? `https://dexscreener.com/solana/${c.matched.pairAddress}` : undefined;
                  const age = c.ageHours != null ? `${c.ageHours.toFixed(1)}h` : '—';
                  const matchTerms = c.matched?.terms?.length ? c.matched.terms.join(' & ') : c.matched?.term || '—';
                  const matchWhere = c.matched?.field || '—';
                  return (
                    <div
                      key={`${c.symbol || 'SYM'}-${i}`}
                      style={{
                        display: 'grid',
                        gridTemplateColumns: '140px 120px 120px 100px 1fr',
                        padding: '8px 10px',
                        borderTop: '1px solid #1a1a1a',
                        fontSize: 13,
                      }}
                    >
                      <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {link ? (
                          <a href={link} target="_blank" rel="noreferrer" style={{ textDecoration: 'underline' }}>
                            {c.symbol || '—'}
                          </a>
                        ) : (
                          c.symbol || '—'
                        )}
                      </div>
                      <div>{fmtUsd(c.liquidityUsd)}</div>
                      <div>{fmtUsd(c.volume24hUsd)}</div>
                      <div>{age}</div>
                      <div style={{ opacity: 0.85 }}>
                        {matchTerms} <span style={{ opacity: 0.7 }}>({matchWhere})</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}

export default function ParentsTable({ rows }: { rows: ParentRow[] }) {
  return (
    <div style={{ marginTop: 16, border: '1px solid #333', borderRadius: 8, overflow: 'hidden' }}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '120px 140px 120px 1fr',
          padding: '10px 12px',
          background: '#111',
          fontSize: 12,
          opacity: 0.85,
        }}
      >
        <div>Parent</div>
        <div>Children (new24h)</div>
        <div>Survival h24</div>
        <div>Liquidity funnel / Top child</div>
      </div>

      {rows.length === 0 && <div style={{ padding: 16, fontSize: 14, opacity: 0.7 }}>No data yet for this narrative.</div>}

      {rows.map((r) => (
        <ParentRowItem key={r.parent} r={r} />
      ))}
    </div>
  );
}

