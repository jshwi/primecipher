# PrimeCipher Tutorial

A quick, hands-on guide for running the API, exploring narratives/parents,
probing discovery, backtesting, and using the synthetic backfill CLI.

---

## Prerequisites

- Python 3.12
- macOS/Linux shell with `curl` and (optionally) `jq` for pretty JSON

---

## 1. Setup

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional: point to a custom seeds file (JSON):

```bash
export NARRATIVES_SEEDS_FILE=seeds/narratives.seed.json
```

If unset, the app uses its internal, built-in narrative seeds.

---

## 2. Start the API server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open:

- Docs: http://localhost:8000/docs  
- Health: http://localhost:8000/healthz

Stop with `Ctrl+C`.

---

## 3. Core concepts

- **Narrative** — a theme like `dogs` or `ai`, defined by seed rules.
- **Parent** — a canonical token symbol inside a narrative (e.g. `WIF`).
- **Children** — discovered tokens that match the parent via seed terms/rules.
- **Backtest** — evaluate simple returns over a holding window (e.g. `h6`).

---

## 4. Explore the API

All examples assume the server is running on `localhost:8000`.

### List narratives

```bash
curl "http://localhost:8000/narratives?source=file&window=24h" | jq
```

Example:

```json
{
  "narratives": [
    {"key": "dogs", "parents": ["WIF","MOODENG"], "num_parents": 2},
    {"key": "ai",   "parents": ["FET","TAO"],     "num_parents": 2}
  ]
}
```

### Inspect parents for a narrative

```bash
curl "http://localhost:8000/parents/dogs?source=file&window=24h" | jq
```

### Debug child discovery

```bash
curl "http://localhost:8000/debug/children/WIF?narrative=dogs&liqMinUsd=10000&limit=5" | jq
```

Example output (truncated):

```json
{
  "resolved": {
    "parent": "WIF",
    "narrative": "dogs",
    "terms": ["wif","dogwifhat","wifhat","dogwif","dog with hat"],
    "block": ["WITH","SANTA"]
  },
  "counts": {"total": 5, "returned": 5},
  "children": [
    {"symbol": "DOGWIF", "liquidityUsd": 7791.79},
    {"symbol": "CWIF", "liquidityUsd": 40046.9}
  ]
}
```

### Run a backtest snapshot

```bash
curl "http://localhost:8000/backtest?parent=WIF&narrative=dogs&window=24h" | jq
```

Example output (truncated):

```json
{
  "summary": {
    "hold": "h6",
    "n_trades": 3,
    "mean_return": -0.03759
  },
  "trades": [
    {"pairAddress": "7eX...", "return": -0.0210}
  ]
}
```

### Walk through a time range

```bash
curl "http://localhost:8000/backtest/walk?parent=WIF&narrative=dogs&start=2025-08-20T00:00:00Z&end=2025-08-20T06:00:00Z&step=1h" | jq
```

---

## 5. Storage Helpers

From Python:

```python
from app import storage
print(storage.recent_pairs(max_idle_hours=24))
```

---

## 6. Synthetic Backfill CLI

Run synthetic snapshots for demo/testing:

```bash
python -m app.tools.synthetic_backfill --window h1 --narrative dogs --max 10
```

Arguments:
- `--window` timeframe (e.g. `m5`, `h1`, `h6`, `h24`)
- `--narrative` seed narrative key
- `--parent` restrict to a parent symbol
- `--max` cap number of pairs

---

Happy exploring!
