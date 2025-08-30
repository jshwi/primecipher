# PrimeCipher (Fresh MVP)

Minimal, clean skeleton that does **one thing**: list narratives and show their parents.

## Run (Docker)

```bash
docker compose build --no-cache
docker compose up
# FE: http://localhost:3000
# API: http://localhost:8000
```

## API

- `GET /narratives` – list from seeds
- `GET /parents/{narrative}` – parents for narrative (in-memory store)
- `POST /refresh` – synthesize parents and mark last refresh

## Seeds

Edit `backend/seeds/narratives.seed.json` (hot-mounted read-only).

## Notes

- No DB. No billing. No workers. Clean growth path from here only if the core is useful.
