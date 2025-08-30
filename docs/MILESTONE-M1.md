# Primecipher — Sprint 1 (M1)

**Version:** 0.0.0-beta
**Objective:** End-to-end MVP with 10 seeds, deterministic heat scoring, and a basic UI you can trust.

---

## 🎯 Success Criteria

- `/narratives` returns 10 narratives with `heat`, `avg`, `top`, `count`, `explain`.
- `/n/{narrative}` lists parents with scores + pagination.
- Deterministic scoring implemented (recency constant for now).
- Seeds v2 validated on boot; bad seeds fail fast with clear errors.
- “Refresh” stub returns 200 and recomputes cache.
- UI shows all 10 narratives with believable ordering + explanations.

---

## 📌 Tasks

### 1. Seeds v2 locked & validated

- JSON schema: `name`, `terms`, `synonyms`, `require_all`, `block`, `weight`, `branches`.
- Bad file should produce clear validation error.
- Seeds README explains each field.

### 2. Deterministic adapter (dev mode)

- Returns parents via term/branch matching.
- Same input ⇒ same output (no randomness).

### 3. Heat scoring (deterministic MVP)

- Parent score = breadth + intensity + constant recency + branch weighting.
- Narrative roll-up = 0.45*avg + 0.35*top + 0.20\*presence.
- Seed weight multiplier (soft).
- Scores ∈ [0,1], rounded to 3 decimals.

### 4. Explainability in API

- `/narratives` includes `explain`: top 3 parents with `(breadth, intensity, recency, branchHits)`.
- Field always present (empty list if none).

### 5. Refresh (stubbed) + cache

- `/refresh` or `/refresh/async` recomputes + resets cache.
- Returns `{ ok: true, stale: false }`.

### 6. Frontend: List + Detail

- `/` shows narratives with heat, avg, count, first line of insight.
- `/n/{narrative}` lists parents with score, matches, branch tags; “Load more”.
- Includes “Why is this hot?” panel (top 3 parents).

### 7. Golden set (sanity checks)

- Tiny JSON with expected qualitative results (e.g. dogs > privacy).
- Run manually in <3 min.

### 8. Runbook v0

- Short HOWTO: run backend, frontend, edit seeds, refresh, read heat.
- Should get future-you up to speed in 5 minutes.

---

## 🛑 What’s Out of Scope (M1)

- No external data (Helius/Twitter/etc).
- No background workers.
- No Docker/CI pipelines.
- No charts beyond list/detail.
- No ML/anomaly detection.

---

## 📅 Sprint Timeline

- **Week 1 checkpoint:** `/narratives` returns heat for at least 3 narratives; frontend shows them with explanations.
- **Week 2 demo:** 10 seeds live, refresh works, explanations visible, runbook complete.

---

## ✅ Definition of Done

- API & UI deliver expected outputs.
- Seeds validated with clear error messages.
- Heat ordering believable (passes golden set).
- Runbook v0 exists.
