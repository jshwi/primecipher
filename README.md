# Narrative Heatmap × Parent Ecosystems (Stub MVP)

This bundle includes:
- Backend API (FastAPI) with live DexScreener adapter + heat scoring
- Frontend UI (Next.js) reading JSON snapshots
- Seeds (tiny, assumed subsets) separate from generated data

---

## Requirements

### System
- Python 3.10+
- Node.js 18+ (with npm)
- jq (optional, for smoke script)

### Python deps
See `backend/requirements.txt`:
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
httpx==0.27.2
```

### Node deps
See `frontend/package.json` (Next.js 15, React 18).

---

## Quickstart

### 1) Backend setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Create stub snapshots (from seeds)
```bash
python scripts/generate_stub_data.py
# writes data/narratives-24h.json and data/parents-<narrative>-24h.json
```

### 3) Run API
```bash
uvicorn app.main:app --reload --port 8000
```

### 4) Frontend setup
```bash
cd ../frontend
npm install
npm run dev
# open http://localhost:3000
```

### 5) (Optional) Live refresh from DexScreener
In another terminal (API running):
```bash
curl "http://localhost:8000/refresh?window=24h"
# or fetch live without writing snapshots:
curl "http://localhost:8000/narratives?window=24h&source=live" | jq .
curl "http://localhost:8000/parents/dogs?window=24h&source=live" | jq .
```

### Seeds vs Data
- `/seeds/` — small, assumed subsets (committed inputs)
- `/data/` — generated snapshots (ignored by git in your repo)

