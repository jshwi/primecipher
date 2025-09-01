# Primecipher – Refresh Contract

## 🎯 Purpose

The refresh endpoint is the **reset button** for the backend’s view of narratives.
It is not a scraper, not a cron — just a recompute hook.

---

## ✅ What Refresh **MUST** Do

1. **Reload Seeds**
   - Drop any cached copy.
   - Parse `backend/seeds/narratives.seed.json` into structured objects.

2. **Recompute Parents**
   - For each seed narrative, call the active adapter (`DevSource` for MVP).
   - Generate a capped list of parents with branch hits, matches, and scores.

3. **Update Storage**
   - Write recomputed results into the in-memory store (or leave in hot state if you prefer no cache).

4. **Return Lightweight Status**
   - Always return `{ "ok": true }`.
   - Optionally include metadata like `{"narratives": 10, "stale": false}`.

---

## 🚫 What Refresh **MUST NOT** Do

- ❌ Call external APIs directly (keep adapters in charge).
- ❌ Block for long operations (design for async, but can stub sync in dev).
- ❌ Perform UI-side work (frontend just re-queries after refresh).
- ❌ Overwrite the seed JSON (refresh reads seeds; only humans/scripts edit them).

---

## 🔄 Lifecycle

```text
Client (UI) → POST /refresh/async
    └── refresh.py
         ├─ seeds.invalidate_seeds_cache()
         ├─ storage.clear()
         ├─ for each narrative in seeds.list_narrative_names():
         │     └─ storage.put_parents(n, compute_parents(n))
         └─ return { ok: true, narratives: N }
```
