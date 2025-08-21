import { fetchJSON } from '@/lib/api';

type Props = { params: { narrative: string } };

export default async function Page({ params }: Props) {
  const rows = await fetchJSON(`/parents/${params.narrative}?window=24h`);
  return (
    <main style={{ padding: 24, fontFamily: 'ui-sans-serif, system-ui' }}>
      <h1 style={{ fontSize: 24, marginBottom: 16 }}>Parent Ecosystems — {params.narrative}</h1>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ textAlign: 'left', borderBottom: '1px solid #444', padding: 8 }}>Parent</th>
            <th style={{ textAlign: 'right', borderBottom: '1px solid #444', padding: 8 }}>Children</th>
            <th style={{ textAlign: 'right', borderBottom: '1px solid #444', padding: 8 }}>24h Survival %</th>
            <th style={{ textAlign: 'right', borderBottom: '1px solid #444', padding: 8 }}>Top Child</th>
            <th style={{ textAlign: 'right', borderBottom: '1px solid #444', padding: 8 }}>Top Child Vol 24h</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r: any) => (
            <tr key={r.parent}>
              <td style={{ padding: 8, borderBottom: '1px solid #333' }}>{r.parent}</td>
              <td style={{ padding: 8, textAlign: 'right', borderBottom: '1px solid #333' }}>{r.childrenCount}</td>
              <td style={{ padding: 8, textAlign: 'right', borderBottom: '1px solid #333' }}>{(r.survivalRates.h24 * 100).toFixed(2)}%</td>
              <td style={{ padding: 8, textAlign: 'right', borderBottom: '1px solid #333' }}>{r.topChild.symbol}</td>
              <td style={{ padding: 8, textAlign: 'right', borderBottom: '1px solid #333' }}>${'{'}r.topChild.volume24hUsd.toLocaleString(){'}'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
