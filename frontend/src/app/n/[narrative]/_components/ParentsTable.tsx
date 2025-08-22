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

type BacktestTrade = {
  parent: string;
  symbol: string;
  pairAddress?: string | null;
  liq?: number | null;
  vol24h?: number | null;
  ageHours?: number | null;
  return?: number | null; // decimal (0.05 => +5%)
};

type BacktestSummary = {
  hold: 'm5' | 'h1' | 'h6' | 'h24';
  n_trades: number;
  n_with_return: number;
  winrate_gt0: number | null;
  mean_return: number | null;
  median_return: number | null;
  min_return: number | null;
  max_return: number | null;
};

type BacktestResp = {
  params: Record<string, any>;
  summary: BacktestSummary;
  trades: BacktestTrade[];
};

type WalkTrade = {
  pairAddress: string;
  parent: string;
  narrative: string;
  entryTs: number;
  exitTs: number;
  entryPrice: number;
  exitPrice: number;
  exitLiq: number | null;
  return: number; // decimal
};

type WalkSummary = {
  hold: 'm5' | 'h1' | 'h6' | 'h24';
  n_trades: number;
  n_with_return: number;
  winrate_gt0: number | null;
  mean_return: number | null;
  median_return: number | null;
  min_return: number | null;
  max_return: number | null;
  tolerance_min: number;
  note?: string | null;
};

type WalkDiagnostics = {
  pairs_considered: number;
  entry_target_ts: number;
  exit_target_ts: number;
  tolerance_sec: number;
  entry_found_any: number;
  exit_found_any: number;
  entry_within_tolerance: number;
  exit_within_tolerance: number;
  priced_pairs: number;
  liq_ok_pairs: number;
};

type WalkResp = {
  summary: WalkSummary;
  diagnostics: WalkDiagnostics;
  trades: WalkTrade[];
};

function fmtUsd(n?: number | null) {
  const v = typeof n === 'number' ? n : 0;
  return `$${Math.round(v).toLocaleString()}`;
}
function pct(n?: number | null) {
  if (typeof n !== 'number') return '—';
  return `${(n * 100).toFixed(2)}%`;
}
function ts(ts: number) {
  return new Date(ts * 1000).toLocaleString();
}

/** =========================
 * Quick Backtest panel (existing)
 * ========================= */
function BacktestPanel({ narrative, parents }: { narrative: string; parents: string[] }) {
  const [parent, setParent] = useState<string>('ALL');
  const [hold, setHold] = useState<'m5' | 'h1' | 'h6' | 'h24'>('h24');
  const [liqMin, setLiqMin] = useState<number>(50000);
  const [maxAge, setMaxAge] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [resp, setResp] = useState<BacktestResp | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runBacktest = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResp(null);
    try {
      const p = new URLSearchParams();
      p.set('narrative', narrative);
      p.set('hold', hold);
      p.set('liqMinUsd', String(liqMin));
      if (parent !== 'ALL') p.set('parent', parent);
      if (maxAge.trim().length > 0) p.set('maxAgeHours', maxAge.trim());

      const url = `${API_BASE}/backtest?${p.toString()}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: BacktestResp = await res.json();
      setResp(json);
    } catch {
      setError('Backtest failed');
    } finally {
      setLoading(false);
    }
  }, [narrative, parent, hold, liqMin, maxAge]);

  const trades = resp?.trades ?? [];

  const csvHref = useMemo(() => {
    if (!trades.length) return null;
    const header = ['parent', 'symbol', 'pairAddress', 'liq', 'vol24h', 'ageHours', 'return'].join(',');
    const rows = trades.map((t) =>
      [t.parent, t.symbol, t.pairAddress ?? '', t.liq ?? '', t.vol24h ?? '', t.ageHours ?? '', t.return ?? ''].join(',')
    );
    const blob = new Blob([header + '\n' + rows.join('\n')], { type: 'text/csv' });
    return URL.createObjectURL(blob);
  }, [trades]);

  return (
    <div style={{ border: '1px solid #222', borderRadius: 8, marginTop: 12, padding: 12, background: '#0f0f0f' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <div style={{ fontWeight: 600 }}>Quick Backtest</div>
        <div style={{ fontSize: 12, opacity: 0.6 }}>
          Uses Dexscreener priceChange windows (not a historical walk-forward test).
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr auto', gap: 8 }}>
        <div>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 4 }}>Parent</div>
          <select
            value={parent}
            onChange={(e) => setParent(e.target.value)}
            style={{ width: '100%', background: '#0a0a0a', border: '1px solid #333', color: 'white', padding: 6, borderRadius: 6 }}
          >
            <option value="ALL">All parents</option>
            {parents.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>

        <div>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 4 }}>Hold</div>
          <select
            value={hold}
            onChange={(e) => setHold(e.target.value as any)}
            style={{ width: '100%', background: '#0a0a0a', border: '1px solid #333', color: 'white', padding: 6, borderRadius: 6 }}
          >
            <option value="m5">5 minutes</option>
            <option value="h1">1 hour</option>
            <option value="h6">6 hours</option>
            <option value="h24">24 hours</option>
          </select>
        </div>

        <div>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 4 }}>Min Liquidity (USD)</div>
          <input
            type="number"
            value={liqMin}
            onChange={(e) => setLiqMin(Number(e.target.value || 0))}
            style={{ width: '100%', background: '#0a0a0a', border: '1px solid #333', color: 'white', padding: 6, borderRadius: 6 }}
            min={0}
          />
        </div>

        <div>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 4 }}>Max Age (hours, optional)</div>
          <input
            placeholder="e.g., 168"
            value={maxAge}
            onChange={(e) => setMaxAge(e.target.value)}
            style={{ width: '100%', background: '#0a0a0a', border: '1px solid #333', color: 'white', padding: 6, borderRadius: 6 }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'end' }}>
          <button
            onClick={runBacktest}
            disabled={loading}
            style={{
              padding: '8px 12px',
              border: '1px solid #333',
              borderRadius: 6,
              background: '#121212',
              cursor: 'pointer',
              fontSize: 13,
              opacity: loading ? 0.6 : 1,
            }}
          >
            {loading ? 'Running…' : 'Run backtest'}
          </button>
        </div>
      </div>

      {error && <div style={{ color: '#f66', marginTop: 8, fontSize: 13 }}>{error}</div>}

      {resp && (
        <div style={{ marginTop: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 13 }}>
            <div>hold: <strong>{resp.summary.hold}</strong></div>
            <div>trades: <strong>{resp.summary.n_trades}</strong></div>
            <div>winrate: <strong>{resp.summary.winrate_gt0 != null ? (resp.summary.winrate_gt0 * 100).toFixed(1) + '%' : '—'}</strong></div>
            <div>mean: <strong>{pct(resp.summary.mean_return)}</strong></div>
            <div>median: <strong>{pct(resp.summary.median_return)}</strong></div>
            <div>min: <strong>{pct(resp.summary.min_return)}</strong></div>
            <div>max: <strong>{pct(resp.summary.max_return)}</strong></div>
            {csvHref && (
              <a
                href={csvHref}
                download={`backtest_${narrative}_${parent}_${hold}.csv`}
                style={{ marginLeft: 'auto', color: '#68a0ff', fontSize: 12 }}
              >
                Download CSV
              </a>
            )}
          </div>

          <div style={{ border: '1px solid #222', borderRadius: 6, overflow: 'hidden', marginTop: 10 }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '120px 140px 120px 120px 100px 100px',
                padding: '8px 10px',
                background: '#111',
                fontSize: 12,
                opacity: 0.85,
              }}
            >
              <div>Parent</div>
              <div>Symbol</div>
              <div>Liquidity</div>
              <div>Vol 24h</div>
              <div>Age</div>
              <div>Return</div>
            </div>
            {trades.map((t, i) => {
              const link = t.pairAddress ? `https://dexscreener.com/solana/${t.pairAddress}` : undefined;
              return (
                <div
                  key={`${t.symbol || '—'}-${i}`}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '120px 140px 120px 120px 100px 100px',
                    padding: '8px 10px',
                    borderTop: '1px solid #191919',
                    fontSize: 13,
                  }}
                >
                  <div>{t.parent}</div>
                  <div>
                    {link ? (
                      <a href={link} target="_blank" rel="noreferrer" style={{ color: '#68a0ff' }}>
                        {t.symbol}
                      </a>
                    ) : (
                      t.symbol
                    )}
                  </div>
                  <div>{fmtUsd(t.liq)}</div>
                  <div>{fmtUsd(t.vol24h)}</div>
                  <div>{typeof t.ageHours === 'number' ? `${t.ageHours.toFixed(1)}h` : '—'}</div>
                  <div>{pct(t.return)}</div>
                </div>
              );
            })}
            {trades.length === 0 && (
              <div style={{ padding: 10, fontSize: 13, opacity: 0.7 }}>No trades matched your filters.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/** =========================
 * Walk-Forward Backtest panel (new)
 * ========================= */
function WalkForwardPanel({ narrative, parents }: { narrative: string; parents: string[] }) {
  const [parent, setParent] = useState<string>('ALL');
  const [hold, setHold] = useState<'m5' | 'h1' | 'h6' | 'h24'>('h6');
  const [minLiq, setMinLiq] = useState<number>(50000);
  const [tolMin, setTolMin] = useState<number>(20);
  const [loading, setLoading] = useState(false);
  const [resp, setResp] = useState<WalkResp | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runWalk = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResp(null);
    try {
      const p = new URLSearchParams();
      p.set('hold', hold);
      p.set('minLiqUsd', String(minLiq));
      p.set('toleranceMin', String(tolMin));
      if (narrative) p.set('narrative', narrative);
      if (parent !== 'ALL') p.set('parent', parent);

      const url = `${API_BASE}/backtest/walk?${p.toString()}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: WalkResp = await res.json();
      setResp(json);
    } catch {
      setError('Walk-forward backtest failed');
    } finally {
      setLoading(false);
    }
  }, [narrative, parent, hold, minLiq, tolMin]);

  const trades = resp?.trades ?? [];

  const csvHref = useMemo(() => {
    if (!trades.length) return null;
    const header = ['parent', 'pairAddress', 'entryTs', 'exitTs', 'entryPrice', 'exitPrice', 'exitLiq', 'return'].join(',');
    const rows = trades.map((t) =>
      [t.parent, t.pairAddress, t.entryTs, t.exitTs, t.entryPrice, t.exitPrice, t.exitLiq ?? '', t.return].join(',')
    );
    const blob = new Blob([header + '\n' + rows.join('\n')], { type: 'text/csv' });
    return URL.createObjectURL(blob);
  }, [trades]);

  return (
    <div style={{ border: '1px solid #222', borderRadius: 8, marginTop: 12, padding: 12, background: '#0f0f0f' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <div style={{ fontWeight: 600 }}>Walk-Forward Backtest</div>
        <div style={{ fontSize: 12, opacity: 0.6 }}>
          Uses your local snapshots; needs ≥2 timepoints spanning the hold window.
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr auto', gap: 8 }}>
        <div>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 4 }}>Parent</div>
          <select
            value={parent}
            onChange={(e) => setParent(e.target.value)}
            style={{ width: '100%', background: '#0a0a0a', border: '1px solid #333', color: 'white', padding: 6, borderRadius: 6 }}
          >
            <option value="ALL">All parents</option>
            {parents.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <div>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 4 }}>Hold</div>
          <select
            value={hold}
            onChange={(e) => setHold(e.target.value as any)}
            style={{ width: '100%', background: '#0a0a0a', border: '1px solid #333', color: 'white', padding: 6, borderRadius: 6 }}
          >
            <option value="m5">5 minutes</option>
            <option value="h1">1 hour</option>
            <option value="h6">6 hours</option>
            <option value="h24">24 hours</option>
          </select>
        </div>
        <div>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 4 }}>Min Liquidity (USD)</div>
          <input
            type="number"
            value={minLiq}
            onChange={(e) => setMinLiq(Number(e.target.value || 0))}
            style={{ width: '100%', background: '#0a0a0a', border: '1px solid #333', color: 'white', padding: 6, borderRadius: 6 }}
            min={0}
          />
        </div>
        <div>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 4 }}>Tolerance (minutes)</div>
          <input
            type="number"
            value={tolMin}
            onChange={(e) => setTolMin(Number(e.target.value || 0))}
            style={{ width: '100%', background: '#0a0a0a', border: '1px solid #333', color: 'white', padding: 6, borderRadius: 6 }}
            min={1}
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'end' }}>
          <button
            onClick={runWalk}
            disabled={loading}
            style={{
              padding: '8px 12px',
              border: '1px solid #333',
              borderRadius: 6,
              background: '#121212',
              cursor: 'pointer',
              fontSize: 13,
              opacity: loading ? 0.6 : 1,
            }}
          >
            {loading ? 'Running…' : 'Run walk-forward'}
          </button>
        </div>
      </div>

      {error && <div style={{ color: '#f66', marginTop: 8, fontSize: 13 }}>{error}</div>}

      {resp && (
        <div style={{ marginTop: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 13, flexWrap: 'wrap' }}>
            <div>hold: <strong>{resp.summary.hold}</strong></div>
            <div>trades: <strong>{resp.summary.n_trades}</strong></div>
            <div>winrate: <strong>{resp.summary.winrate_gt0 != null ? (resp.summary.winrate_gt0 * 100).toFixed(1) + '%' : '—'}</strong></div>
            <div>mean: <strong>{pct(resp.summary.mean_return)}</strong></div>
            <div>median: <strong>{pct(resp.summary.median_return)}</strong></div>
            <div>min: <strong>{pct(resp.summary.min_return)}</strong></div>
            <div>max: <strong>{pct(resp.summary.max_return)}</strong></div>
            {resp.summary.note && <div style={{ marginLeft: 'auto', fontSize: 12, opacity: 0.7 }}>{resp.summary.note}</div>}
            {csvHref && (
              <a
                href={csvHref}
                download={`walk_${narrative}_${parent}_${hold}.csv`}
                style={{ marginLeft: 'auto', color: '#68a0ff', fontSize: 12 }}
              >
                Download CSV
              </a>
            )}
          </div>

          {/* Diagnostics */}
          <div style={{ fontSize: 12, opacity: 0.75, marginTop: 8, display: 'flex', gap: 14, flexWrap: 'wrap' }}>
            <div>pairs: {resp.diagnostics.pairs_considered}</div>
            <div>entry tol ok: {resp.diagnostics.entry_within_tolerance}</div>
            <div>exit tol ok: {resp.diagnostics.exit_within_tolerance}</div>
            <div>priced: {resp.diagnostics.priced_pairs}</div>
            <div>liq ok: {resp.diagnostics.liq_ok_pairs}</div>
          </div>

          {/* Trades */}
          <div style={{ border: '1px solid #222', borderRadius: 6, overflow: 'hidden', marginTop: 10 }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '110px 220px 160px 160px 120px 120px 100px',
                padding: '8px 10px',
                background: '#111',
                fontSize: 12,
                opacity: 0.85,
              }}
            >
              <div>Parent</div>
              <div>Pair</div>
              <div>Entry</div>
              <div>Exit</div>
              <div>Entry Price</div>
              <div>Exit Price</div>
              <div>Return</div>
            </div>
            {trades.map((t, i) => {
              const link = `https://dexscreener.com/solana/${t.pairAddress}`;
              return (
                <div
                  key={`${t.pairAddress}-${i}`}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '110px 220px 160px 160px 120px 120px 100px',
                    padding: '8px 10px',
                    borderTop: '1px solid #191919',
                    fontSize: 13,
                  }}
                >
                  <div>{t.parent}</div>
                  <div>
                    <a href={link} target="_blank" rel="noreferrer" style={{ color: '#68a0ff' }}>
                      {t.pairAddress}
                    </a>
                  </div>
                  <div>{ts(t.entryTs)}</div>
                  <div>{ts(t.exitTs)}</div>
                  <div>{t.entryPrice?.toFixed(6)}</div>
                  <div>{t.exitPrice?.toFixed(6)}</div>
                  <div>{pct(t.return)}</div>
                </div>
              );
            })}
            {trades.length === 0 && (
              <div style={{ padding: 10, fontSize: 13, opacity: 0.7 }}>No trades (yet). Let the snapshot worker run or try a shorter hold.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/** =========================
 * Children drawer (with pagination)
 * ========================= */
function ParentRowItem({ r }: { r: ParentRow }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // pagination state
  const [items, setItems] = useState<DebugChild[]>([]);
  const [counts, setCounts] = useState<DebugResp['counts'] | null>(null);
  const [offset, setOffset] = useState(0);
  const limit = 50;

  const hasMore = useMemo(() => {
    const total = counts?.total ?? 0;
    return items.length < total;
  }, [items.length, counts?.total]);

  const baseParams = useMemo(() => {
    const p = new URLSearchParams();
    p.set('narrative', r.narrative);
    p.set('applyBlocklist', 'true');
    p.set('limit', String(limit));
    return p;
  }, [r.narrative]);

  const pageUrl = useCallback(
    (ofs: number) => {
      const p = new URLSearchParams(baseParams);
      p.set('offset', String(ofs));
      return `${API_BASE}/debug/children/${encodeURIComponent(r.parent)}?${p.toString()}`;
    },
    [r.parent, baseParams]
  );

  const fetchPage = useCallback(
    async (ofs: number) => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(pageUrl(ofs));
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json: DebugResp = await res.json();

        setItems((prev) => (ofs === 0 ? json.children ?? [] : [...prev, ...(json.children ?? [])]));
        setCounts(json.counts ?? null);
        setOffset(ofs + (json.counts?.returned ?? json.children?.length ?? 0));
      } catch {
        setError('Failed to load children');
      } finally {
        setLoading(false);
      }
    },
    [pageUrl]
  );

  const onToggle = useCallback(async () => {
    const next = !open;
    setOpen(next);
    if (next && items.length === 0 && !loading) {
      await fetchPage(0);
    }
  }, [open, items.length, loading, fetchPage]);

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
          <div>
            {r.childrenCount} ({r.childrenNew24h})
          </div>
          <a
            href={`${API_BASE}/debug/children/${encodeURIComponent(r.parent)}?${baseParams.toString()}`}
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
                top child: <strong>{r.topChild.symbol || '—'}</strong>{' '}
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
                {r.topChild.matchedTerms?.length ? <span style={{ opacity: 0.6 }}> (match: {r.topChild.matchedTerms.join(' & ')})</span> : null}
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
          {loading && items.length === 0 && <div style={{ fontSize: 13, opacity: 0.8 }}>Loading children…</div>}
          {error && <div style={{ fontSize: 13, color: '#f66' }}>{error}</div>}

          {!error && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, opacity: 0.8, marginBottom: 8 }}>
                <div>returned: {counts?.returned ?? items.length}</div>
                {counts?.total != null ? <div>total: {counts.total}</div> : null}
                {counts?.offset != null ? <div>offset: {counts.offset}</div> : null}
                {counts?.limit != null ? <div>limit: {counts.limit}</div> : null}
              </div>

              {items.length === 0 && !loading && <div style={{ padding: 10, fontSize: 13, opacity: 0.7 }}>No matches.</div>}

              {items.length > 0 && (
                <>
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
                    {items.map((c, i) => {
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

                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
                    {hasMore ? (
                      <button
                        onClick={() => fetchPage(offset)}
                        disabled={loading}
                        style={{
                          padding: '6px 10px',
                          border: '1px solid '#333',
                          borderRadius: 6,
                          background: '#0f0f0f',
                          cursor: 'pointer',
                          fontSize: 12,
                          opacity: loading ? 0.6 : 1,
                        }}
                      >
                        {loading ? 'Loading…' : 'Load more'}
                      </button>
                    ) : (
                      <div style={{ fontSize: 12, opacity: 0.6 }}>End of results</div>
                    )}
                  </div>
                </>
              )}
            </>
          )}
        </div>
      )}
    </>
  );
}

export default function ParentsTable({ rows }: { rows: ParentRow[] }) {
  const narrative = rows[0]?.narrative ?? '';
  const parentList = rows.map((r) => r.parent);

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

      {/* New research panels */}
      {rows.length > 0 && (
        <>
          <BacktestPanel narrative={narrative} parents={parentList} />
          <WalkForwardPanel narrative={narrative} parents={parentList} />
        </>
      )}

      {rows.map((r) => (
        <ParentRowItem key={r.parent} r={r} />
      ))}
    </div>
  );
}

