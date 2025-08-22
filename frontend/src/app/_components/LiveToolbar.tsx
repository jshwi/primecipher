'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useMemo, useState, useTransition } from 'react';

type Props = {
  windowParam?: string; // default: 24h
};

export default function LiveToolbar({ windowParam = '24h' }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const sp = useSearchParams();
  const [pending, startTransition] = useTransition();
  const [refreshing, setRefreshing] = useState(false);

  const isLive = (sp.get('source') || '').toLowerCase() === 'live';

  const updateQuery = useCallback(
    (nextLive: boolean) => {
      const params = new URLSearchParams(sp.toString());
      if (nextLive) params.set('source', 'live');
      else params.delete('source');
      const q = params.toString();
      const url = q ? `${pathname}?${q}` : pathname;
      startTransition(() => {
        router.replace(url);
        router.refresh();
      });
    },
    [router, pathname, sp]
  );

  const onToggle = useCallback(() => updateQuery(!isLive), [isLive, updateQuery]);

  const onRefresh = useCallback(async () => {
    try {
      setRefreshing(true);
      const base = process.env.NEXT_PUBLIC_API_BASE || '';
      const res = await fetch(`${base}/refresh?window=${encodeURIComponent(windowParam)}`, { method: 'GET' });
      // ignore response body; just refresh UI
    } catch {
      // noop; UI still tries to refresh
    } finally {
      setRefreshing(false);
      router.refresh();
    }
  }, [router, windowParam]);

  const stateLabel = useMemo(() => (isLive ? 'Live' : 'Snapshots'), [isLive]);

  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
      <button
        type="button"
        onClick={onToggle}
        disabled={pending || refreshing}
        style={{
          padding: '6px 10px',
          borderRadius: 6,
          border: '1px solid #333',
          background: isLive ? '#163317' : '#111',
          color: isLive ? '#9ef59e' : '#ddd',
          cursor: 'pointer',
        }}
        title="Toggle between stored snapshots and querying the API live"
      >
        {stateLabel}
      </button>
      <button
        type="button"
        onClick={onRefresh}
        disabled={refreshing || pending}
        style={{
          padding: '6px 10px',
          borderRadius: 6,
          border: '1px solid #333',
          background: refreshing ? '#111' : '#181818',
          color: '#ddd',
          cursor: 'pointer',
        }}
        title="Call /refresh?window=24h on the backend and re-render"
      >
        {refreshing ? 'Refreshing…' : 'Refresh'}
      </button>
    </div>
  );
}

