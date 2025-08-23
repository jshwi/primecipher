# PrimeCipher Quickstart

A fast reference for using PrimeCipher without reading the full tutorial.

---

## 1. Start the API

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Docs → http://localhost:8000/docs  
- Health check → http://localhost:8000/healthz

---

## 2. Core Endpoints

### List narratives
```bash
curl "http://localhost:8000/narratives?source=file&window=24h" | jq
```

### Inspect parents for a narrative
```bash
curl "http://localhost:8000/parents/dogs?source=file&window=24h" | jq
```

### Discover children for a parent
```bash
curl "http://localhost:8000/debug/children/WIF?narrative=dogs&limit=5" | jq
```

### Backtest snapshot
```bash
curl "http://localhost:8000/backtest?parent=WIF&narrative=dogs&window=24h" | jq
```

### Walk through a time range
```bash
curl "http://localhost:8000/backtest/walk?parent=WIF&narrative=dogs&start=2025-08-20T00:00:00Z&end=2025-08-20T06:00:00Z&step=1h" | jq
```

---

## 3. Helpers

### Recent tracked pairs (Python)
```python
from app import storage
print(storage.recent_pairs(max_idle_hours=24))
```

### Synthetic backfill CLI
```bash
python -m app.tools.synthetic_backfill --window h1 --narrative dogs --max 10
```

---

That’s it — PrimeCipher in **one page** 🚀
