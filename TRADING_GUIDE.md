# PrimeCipher Trading Guide

How to use PrimeCipher to enhance your trading decisions.

---

## 1. Use narratives as idea generators

- Check `/narratives` to see which themes (e.g. `dogs`, `ai`) have active parents.
- Narratives with many active parents/children show where market attention is clustering.

**Tip:** Focus on narratives with multiple new children; it indicates stronger meme momentum.

---

## 2. Parent → child discovery as entry radar

- Use `/debug/children/{parent}` to find new tokens linked to a parent symbol.
- Early child listings are often "copycat pumps" that can run quickly.

**Tip:** Watch for high-liquidity new children attached to strong brands like `WIF`.

---

## 3. Backtest to filter noise

- Use `/backtest` and `/backtest/walk` to simulate buy-and-hold returns over windows (`h1`, `h6`, `h24`).
- Positive average returns suggest narrative strength; negative indicates exhaustion.

**Tip:** Only enter trades in narratives where backtests show consistent positive expectancy.

---

## 4. Storage + recent pairs for monitoring

- In Python, use:

```python
from app import storage
print(storage.recent_pairs(max_idle_hours=24))
```

- This surfaces tokens that are still active and not yet dead liquidity traps.

**Tip:** Drop positions if a narrative’s pairs stop appearing here.

---

## 5. Synthetic backfill for sandbox learning

- Run:

```bash
python -m app.tools.synthetic_backfill --window h1 --narrative dogs --max 10
```

- This simulates discovery without live risk, letting you practice decision-making.

**Tip:** Replay scenarios to learn how winning vs. losing narratives looked early.

---

## Workflow Checklist

1. **Check narratives** → Which themes are hot? (`/narratives`)
2. **Inspect parents** → Which symbols lead? (`/parents/{narrative}`)
3. **Run discovery** → Which children are launching now? (`/debug/children/{parent}`)
4. **Backtest returns** → Do trades show expectancy? (`/backtest`, `/walk`)
5. **Confirm active pairs** → Is liquidity sustained? (`storage.recent_pairs()`)
6. **Trade decision** → Only enter if:  
   - Narrative is hot  
   - Children are numerous  
   - Backtest expectancy is positive  
   - Active liquidity remains

---

**Bottom line:** PrimeCipher helps you avoid FOMO and only trade when the data shows a narrative is both hot and profitable.
