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
    name?: string | null;
    liq?: number | null;
    vol24h?: number | null;
    ageHours?: number | null;
    pairAddress?: string | null;
    matchedTerms?: string[] | null;
  } | null;
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
  counts?: { total?: number; returned?: number; offset?: number; limit?: number };
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
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
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
        <div style={{ fontWeight: 600 }}>{r.parent}</div>

        <div style={{ fontSize: 13, opacity: 0.9 }}>
          <div>{r.childrenCount} ({r.childrenNew24h})</div>
          <a
            href={`${API_BASE}/debug/children/${encodeURIComponent(r.parent)}?narrative=${encodeURIComponent(
              r.narrative
            )}&limit=100&applyBlocklist=true`}
            target="_blank"
            rel="noreferrer"
            style={{ fontSize: 12, opacity: 0.9, color: '#68a0ff' }}
          >
            debug
          </a>
        </div>

        <div style={{ fontSize: 13 }}>
          {Number.isFinite(r.survivalRates.h24) ? `${r.survivalRates.h24.toFixed(1)}%` : '—'}
        </div>

        <div style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ opacity: 0.85 }}>
            parent liq: {fmtUsd(r.liquidityFunnel.parentLiquidityUsd)} · children liq: {fmtUsd(r.liquidityFunnel.childrenLiquidityUsd)}
          </div>
          {r.topChild && (
            <>
              <div style={{ opacity: 0.5 }}>·</div>
              <div>
                top child:{' '}
                <strong>{r.topChild.symbol || '—'}</strong>{' '}
                {typeof r.topChild.liq === 'number' && <>· liq {fmtUsd(r.topChild.liq)}</>}
                {typeof r.topChild.vol24h === 'number' && <> · vol24h {fmtUsd(r.topChild.vol24h)}</>}
                {typeof r.topChild.ageHours === 'number' && <> · age {r.topChild.ageHours.toFixed(1)}h</>}
                {r.topChild.pairAddress && (
                  <>
                    {' '}
                    ·{' '}
                    <a
                      href={`https://dexscreener.com/solana/${r.topChild.pairAddress}`}
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: '#68a0ff' }}
                    >
                      view pair
                    </a>
                  </>
                )}
                {r.topChild.matchedTerms?.length ? (
                  <span style={{ opacity: 0.6 }}> (match: {r.topChild.matchedTerms.join(' & ')})</span>
                ) : null}
              </div>
            </>
          )}
          <button
            onClick={onToggle}
            style={{
              marginLeft: 10,
              padding: '3px 8px',
              border: '1px solid #333',
              borderRadius: 6,
              background: '#0f0f0f',
              cursor: 'pointer',
              fontSize: 12,
            }}
          >
            {open ? 'Hide children' : 'Show children'}
          </button>
        </div>
      </div>

      {open && (
        <div style={{ borderTop: '1px dashed #222', background: '#0c0c0c', padding: '10px 12px' }}>
          {loading && <div style={{ fontSize: 13, opacity: 0.8 }}>Loading children…</div>}
          {error && <div style={{ fontSize: 13, color: '#f66' }}>{error}</div>}

          {!loading && !error && (
            <>
              {/* Counts + filters summary */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, opacity: 0.8, marginBottom: 8 }}>
                <div>returned: {resp?.counts?.returned ?? children.length}</div>
                {resp?.counts?.total != null ? <div>total: {resp.counts.total}</div> : null}
                {resp?.counts?.offset != null ? <div>offset: {resp.counts.offset}</div> : null}
                {resp?.counts?.limit != null ? <div>limit: {resp.counts.limit}</div> : null}
                {resp?.resolved?.terms?.length ? <div>terms: {resp?.resolved?.terms?.join(' + ')}</div> : null}
                {resp?.resolved?.discovery?.dexIds?.length ? <div>DEX: {resp?.resolved?.discovery?.dexIds?.join(', ')}</div> : null}
                {resp?.resolved?.discovery?.volMinUsd != null ? <div>vol≥{resp?.resolved?.discovery?.volMinUsd}</div> : null}
                {resp?.resolved?.discovery?.liqMinUsd != null ? <div>liq≥{resp?.resolved?.discovery?.liqMinUsd}</div> : null}
              </div>

              {/* Neutral empty state (not an error) */}
              {children.length === 0 && <div style={{ padding: 10, fontSize: 13, opacity: 0.7 }}>No matches.</div>}

              {children.length > 0 && (
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
                  {children.map((c, i) => {
                    const link = c.matched?.pairAddress ? `https://dexscreener.com/solana/${c.matched.pairAddress}` : undefined;
                    const age = c.ageHours != null ? `${c.ageHours.toFixed(1)}h` : '—';
                    const matchTerms = c.matched?.terms?.length ? c.matched.terms.join(' & ') : c.matched?.term || '—';
                    return (
                      <div
                        key={`${c.symbol || '—'}-${i}`}
                        style={{
                          display: 'grid',
                          gridTemplateColumns: '140px 120px 120px 100px 1fr',
                          padding: '8px 10px',
                          borderTop: '1px solid #191919',
                          fontSize: 13,
                        }}
                      >
                        <div style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace' }}>
                          {c.symbol || '—'}
                        </div>
                        <div>{fmtUsd(c.liquidityUsd)}</div>
                        <div>{fmtUsd(c.volume24hUsd)}</div>
                        <div>{age}</div>
                        <div>
                          {link ? (
                            <a href={link} target="_blank" rel="noreferrer" style={{ color: '#68a0ff' }}>
                              {matchTerms}
                            </a>
                          ) : (
                            matchTerms
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </>
  );
}

export default function ParentsTable({ rows }: { rows: ParentRow[] }) {
  return (
    <div style={{ border: '1px solid #222', borderRadius: 8, overflow: 'hidden', marginTop: 14 }}>
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

