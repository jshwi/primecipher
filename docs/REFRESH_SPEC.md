# Primecipher — Refresh v1 (Useful, Safe, Small)

## Goals

- Make `refresh` actually **recompute from real sources** (when enabled), not just seeds.
- Keep costs and complexity low.
- Be observable and debuggable.
- Never block the UI.

---

## Endpoints

### 1) Kick off a refresh

**POST** `/refresh?mode=dev|live&window=24h`

- `mode=dev` (default): deterministic adapter, no network.
- `mode=live`: use the live adapter (e.g., Helius) with budget limits.
- `window`: analysis window (e.g., `24h`, `6h`, `7d`).

**Response 202**

```json
{
  "ok": true,
  "jobId": "r_2025-09-01T02:03:04Z_x7",
  "mode": "dev",
  "window": "24h",
  "startedAt": "2025-09-01T02:03:04Z",
  "message": "refresh queued"
}
```
