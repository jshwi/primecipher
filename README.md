# Narrative Heatmap × Parent Ecosystems (Stub MVP)

This is the Step‑1 stub implementation: backend API + frontend UI wired with mock JSON data.

---

## Requirements

### System
- Python 3.10+
- Node.js 18+ (with npm)
- jq (optional, used in smoke test)

### Python deps
See `backend/requirements.txt`:
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
```

### Node deps
See `frontend/package.json` (Next.js 15, React 18).

---

## Quickstart

### 1) Setup Python backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Generate stub JSON data
```bash
python scripts/generate_stub_data.py
# writes data/narratives-24h.json and data/parents-dogs-24h.json
```

### 3) Run API
```bash
uvicorn app.main:app --reload --port 8000
```

### 4) Setup Node frontend
```bash
cd frontend
npm install
npm run dev
# open http://localhost:3000
```

### 5) (Optional) Smoke test
```bash
API_BASE=http://localhost:8000 bash scripts/smoke.sh
```

---

## Project Structure
```
backend/    # FastAPI stub API
frontend/   # Next.js 15 stub UI
data/       # JSON snapshots
docs/       # JSON schema docs
scripts/    # smoke test script
```

---

## Next Steps
- Replace stub JSON with real adapters (DEX APIs, CT chatter).
- Expand UI with charts and trendlines.
