# PrimeCipher — Project Status
Generated: 2025-08-23T00:32:17

## Structure
- frontend/ — Next.js app
- backend/ — FastAPI backend
- docs/, seeds/, scripts/, README.md, .github/

## Backend
Routes: app/api/routes/narratives.py (/narratives), app/api/routes/parents.py (/parents/{narrative}), app/debug.py (/debug/children/{parent})
Worker: app/workers/snapshot_worker.py
Seeds/tools: app/seeds.py, scripts/generate_stub_data.py
Adapters: app/adapters/onchain.py
Tests: tests/test_adapter.py, tests/test_parents.py

## Frontend
Pages: src/app/page.tsx, src/app/n/page.tsx, src/app/n/[narrative]/page.tsx
Components: ParentsTable.tsx, LiveToolbar.tsx
API client: src/lib/api.ts

## Known Issues
- ParentsTable can throw if rows is not an array
- Narrative discovery is seed/heuristic-heavy
- Worker/backfill may need retries/backoff

## Next Steps (MVP)
1) Data-driven narratives from DB with seed fallback
2) Harden ParentsTable (guards + empty/loading states)
3) Worker reliability (retry/backoff + metrics)
4) Stricter MOODENG discovery (`requireAllTerms`)
5) Add minimal endpoint tests

## Backend files
__init__.py
app/__init__.py
app/adapters/__init__.py
app/adapters/onchain.py
app/api/__init__.py
app/api/routes/__init__.py
app/api/routes/narratives.py
app/api/routes/parents.py
app/backtest.py
app/backtest_walk.py
app/compute.py
app/config.py
app/debug.py
app/main.py
app/parents.py
app/seeds.py
app/storage.py
app/tools/__init__.py
app/tools/synthetic_backfill.py
app/workers/snapshot_worker.py
scripts/generate_stub_data.py
tests/__init__.py
tests/test_adapter.py
tests/test_parents.py

## Frontend files
next-env.d.ts
src/app/_components/LiveToolbar.tsx
src/app/layout.tsx
src/app/n/[narrative]/_components/ParentsTable.tsx
src/app/n/[narrative]/page.tsx
src/app/n/page.tsx
src/app/page.tsx
src/lib/api.ts
