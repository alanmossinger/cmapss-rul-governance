# ROADMAP.md — VEX MADS Capstone Execution Plan

Sequenced for Claude Code sessions. Each phase has a binary done-gate. Don't advance until the gate is green.

---

## Phase 0 — Skeleton (1 session)
**Goal:** repo runnable end-to-end before any real code.

- Init repo, **Apache 2.0 license** (patent grant + enterprise signal), `.gitignore` (Python + data + .venv)
- `pyproject.toml` (PEP 621, single source of truth) with black/ruff/pytest/mypy config — **no `requirements.txt`**
- Folder structure per `CLAUDE.md` (installable package layout: `src/cmapss_rul/...`)
- Pinned deps in `pyproject.toml`: pandas, numpy, scikit-learn, **torch**, shap, fastapi, uvicorn, pydantic, scipy, structlog. Dev extras: pytest, pytest-cov, ruff, black, mypy
- `.env.example` (paths, seeds, model version); runtime constants in `src/cmapss_rul/config.py` (Python module, not YAML)
- GitHub Actions: `ci.yml` (lint + black + mypy warn-only + pytest + coverage) and `governance-check.yml` (validates 9 governance docs present + cross-referenced)
- Placeholder `tests/test_smoke.py` passes

**Gate:** `pytest` green, `ruff check` clean, `black --check` clean, CI green, repo clones and installs clean on a fresh venv via `pip install -e ".[dev]"`.

---

## Phase 1 — Data Layer (1–2 sessions)
**Goal:** C-MAPSS in, processed parquet out, reproducibly.

- `src/data/load.py` — ingest FD001–FD004 from `data/raw/`
- `src/data/preprocess.py` — RUL labeling (piecewise-linear cap at 125), min-max normalization per operating condition
- `src/data/windowing.py` — sliding window generator (default 30 timesteps, stride 1)
- `src/data/splits.py` — train/val by engine ID (no leakage across units)
- `notebooks/01_eda.ipynb` — sensor distributions per fault mode, RUL distribution, operating condition clusters
- Save processed: `data/processed/{fd00X}_{train|val|test}.parquet`
- Tests: shape contracts, no NaN, no leakage across splits

**Gate:** processed parquets exist, shape tests pass, EDA notebook renders.

---

## Phase 2 — RF Baseline (1 session)
**Goal:** floor metric, fast.

- `src/models/rf_baseline.py` — flatten window → RandomForestRegressor
- Train on FD001, evaluate on test
- Metrics: RMSE, MAE, **NASA scoring function** (asymmetric — late predictions punished harder)
- Save model: `artifacts/rf_v1/` with `model.pkl`, `metrics.json`, `git_sha.txt`, `data_hash.txt`
- `notebooks/02_rf_baseline.ipynb` — prediction vs. actual, residual plot

**Gate:** RMSE ≤ 25 on FD001 test (typical RF floor). Artifact directory complete.

---

## Phase 3 — LSTM (1–2 sessions)
**Goal:** beat RF on sequence-aware model.

- `src/cmapss_rul/models/lstm.py` — **PyTorch** 2-layer LSTM, dropout, MSE loss
- Train script with early stopping, TensorBoard logs (via `torch.utils.tensorboard`)
- Hyperparams in `src/cmapss_rul/config.py`: window=30, units=[64,32], lr=1e-3, batch=256, patience=10
- Same metrics suite as RF, same artifact pattern → `artifacts/lstm_v1/` (state_dict `.pt` + metadata)
- Seed everything via `cmapss_rul.config.SEED` — numpy, torch, torch.cuda, stdlib random

**Gate:** RMSE ≤ 18 on FD001 test. Beats RF on NASA score.

---

## Phase 4 — CNN-LSTM (production) (2 sessions)
**Goal:** the model that ships.

- `src/cmapss_rul/models/cnn_lstm.py` — **PyTorch** 1D conv stack (kernel 3, filters [32,64]) → LSTM(50) → Dense
- Train on all four subsets (FD001–FD004), report per-subset metrics
- Save best by validation NASA score (state_dict `.pt` + `metadata.json` with git SHA + data hash)
- Artifact: `artifacts/cnn_lstm_v1/` + training curves saved as PNG
- `notebooks/03_model_comparison.ipynb` — RF vs. LSTM vs. CNN-LSTM table + plots

**Gate:** RMSE ≤ 14 on FD001, ≤ 22 on FD004. Comparison notebook clean.

---

## Phase 5 — SHAP Explainability (1 session)
**Goal:** local + global explanations, exec-readable.

- `src/cmapss_rul/explainability/shap_analysis.py` — `shap.DeepExplainer` for PyTorch CNN-LSTM, `shap.TreeExplainer` for RF
- Global: summary plot, feature importance over test set
- Local: force plot + top-5 contributors per prediction (used by API later)
- Cache background dataset for API speed
- `notebooks/04_shap_analysis.ipynb` — narrative: which sensors drive RUL collapse

**Gate:** SHAP outputs reproducible, top-5 contributor logic returns dict per prediction.

---

## Phase 6 — Governance Layer (2 sessions) ⭐
**Goal:** the differentiator. This is what makes the repo a job-market artifact.

Create in `docs/governance/`:

- **`MODEL_CARD.md`** — Mitchell template. Intended use, out-of-scope, training data, metrics per subset, ethical considerations, contact
- **`RISK_REGISTER.md`** — table: risk ID, description, likelihood, impact, NIST RMF function (Govern/Map/Measure/Manage), mitigation, owner, residual risk
- **`DRIFT_MONITORING.md`** — methodology (PSI thresholds: <0.1 stable, 0.1–0.25 watch, >0.25 alert), KS test on predictions, sample dashboard screenshot
- **`HITL_WORKFLOW.md`** — review triggers (RUL < 20 cycles, drift alert, low-confidence prediction), reviewer SLA, escalation path
- **`ROLLBACK.md`** — versioning scheme, fallback model (RF baseline), decision tree, rollback runbook
- **`AUDIT_TRAIL.md`** — what's logged, retention, access controls
- **`EU_AI_ACT_MAPPING.md`** — system classification (high-risk, Annex III), Article-by-Article compliance evidence
- **`NIST_AI_RMF_MAPPING.md`** — each governance artifact tagged to Govern / Map / Measure / Manage

Code side:
- `src/governance/drift_monitor.py` — PSI + KS implementation, alert thresholds
- `src/governance/audit_log.py` — append-only JSONL: timestamp, model_version, git_sha, inputs hash, prediction, SHAP top-5, latency_ms
- `src/governance/hitl.py` — decision function: returns `route_to_human: bool` + reason

**Gate:** all 8 governance docs exist with real content (no `TBD`). Drift monitor unit-tested. Audit log writes verifiable.

---

## Phase 7 — FastAPI Service (1–2 sessions)
**Goal:** deployable inference layer.

- `src/api/main.py` — endpoints:
  - `POST /predict` — input: sensor window → output: RUL, confidence, model_version, audit_id
  - `POST /explain` — same input + SHAP top-5
  - `GET /health` — model loaded, drift status
  - `GET /version` — model version, git SHA, training date
  - `GET /audit/{id}` — fetch audit record
- Pydantic schemas with validation (sensor count, window length)
- Drift check runs async on every N predictions
- HITL routing triggers logged
- `tests/test_api.py` — happy path + validation failures + drift trigger

**Gate:** `uvicorn` serves, all endpoints return correctly, tests green.

---

## Phase 8 — Docker + Deployment (1 session)
**Goal:** runs anywhere.

- `Dockerfile` — multi-stage, slim base, non-root user, healthcheck
- `docker-compose.yml` — API + volume for audit logs
- `docs/DEPLOYMENT.md` — local run, Docker, env vars, scaling notes
- Test: `docker compose up` → `/health` returns 200

**Gate:** container builds clean, runs clean, < 1.5 GB image.

---

## Phase 9 — Executive README (1 session)
**Goal:** the document a CIO opens first.

Structure (in this order, non-negotiable):
1. **One-line value statement** — business outcome, not architecture
2. **The business case** — asset uptime, unplanned downtime cost, capital allocation framing (no ML jargon in first 300 words)
3. **Mermaid diagram** — end-to-end: data → model → governance → API → human-in-loop
4. **Governance posture** — NIST AI RMF + EU AI Act mapping, link to docs
5. **Results** — table: model, RMSE, NASA score, latency
6. **How it works** — short, layered (exec → engineer)
7. **Quickstart** — clone, install, run, predict
8. **Repo map** — tree with one-line annotations
9. **Author** — Alan Mössinger, links to LinkedIn + VEX AI-Tech

**Gate:** README renders clean on GitHub. First 300 words contain zero acronyms a board member wouldn't recognize. Mermaid diagram renders.

---

## Phase 10 — Final QA + Submission (1 session)
**Goal:** ship.

- Run full pipeline from clean clone — document any friction
- Re-run all notebooks top-to-bottom, clear stale output, commit
- Tag release: `v1.0.0`
- Record 5-min walkthrough (Loom): business case → model → governance → API demo
- Submit to MADS portal
- LinkedIn post: governance angle, link to repo, no humblebrag
- Pin repo on GitHub profile

**Gate:** submitted, public, link-shareable to recruiters.

---

## Total: ~13–16 focused sessions
Sequencing is strict for Phases 0–5. Phase 6 (governance) can run partially in parallel with Phase 7 (API) once Phase 5 lands.

## Critical path
0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10

## What ships even if time compresses
If forced to cut: drop FD002/FD003 deep analysis (keep FD001 + FD004), keep all governance docs, keep API. **Never cut governance — it's the differentiator.**
