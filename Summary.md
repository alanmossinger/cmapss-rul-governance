# Project Context — VEX MADS Capstone / Predictive Maintenance + Governance

## Identity
- Owner: Alan Mössinger (CEO & CAIO, VEX AI-Tech)
- Course: University of Michigan MADS — Milestone II Capstone
- Deliverable: production-grade industrial AI system + governance layer + executive-grade README
- Repo audience is dual: technical reviewers (faculty/grading) AND C-suite/board (job market signal). Code must satisfy the first; documentation must satisfy the second.

## What this system is
Predictive maintenance for turbofan engines. RUL (Remaining Useful Life) prediction on the NASA C-MAPSS dataset (FD001–FD004), with explainability, governance, and FastAPI deployment.

## Stack
- Python 3.11+ (CI tests both 3.11 and 3.12)
- License: Apache 2.0 (chosen for patent grant + enterprise signal; mirrors Kubeflow/MLflow/Ray)
- Data: pandas, numpy, C-MAPSS FD001–FD004 (train/test/RUL)
- Models: scikit-learn (RandomForest baseline), **PyTorch** (LSTM, CNN-LSTM)
- Explainability: SHAP — DeepExplainer for CNN-LSTM, TreeExplainer for RF baseline
- API: FastAPI + Uvicorn, Pydantic schemas
- Drift: PSI + KS on input features and prediction distributions (scipy; Evidently optional later)
- Packaging: `pyproject.toml` (PEP 621, single source of truth) + Dockerfile. No `requirements.txt`.
- Tests: pytest + pytest-cov
- CI: GitHub Actions (lint + black + mypy warn-only + pytest + governance-check)

## Repo layout
```
data/                            raw C-MAPSS + processed parquet (gitignored)
src/cmapss_rul/                  installable package (PEP 621)
  config.py                      paths, seeds, window size, PSI thresholds
  data/                          loader, preprocessing, windowing, splits
  models/                        baseline_rf, lstm, cnn_lstm (cnn_lstm is production)
  explainability/                SHAP wrappers, global + local plots
  governance/                    audit_logger, drift, hitl
  api/                           FastAPI app: /predict /explain /health /version /audit
governance/                      MODEL_CARD, RISK_REGISTER, DRIFT, HITL, ROLLBACK, AUDIT, NIST + EU mappings
notebooks/                       EDA, model comparison, SHAP analysis (clean, no orphan cells)
tests/
docs/                            architecture.md, deployment, README is at repo root
```

## Model progression
1. Random Forest baseline → floor RMSE on FD001
2. LSTM → sequence model, window length tuned
3. CNN-LSTM → production: 1D conv over sensor windows feeding LSTM

Report metrics for all three on identical held-out folds. CNN-LSTM is deployed.

## Governance layer (the differentiator)
Every artifact maps explicitly to:
- **NIST AI RMF**: tag each artifact with Govern / Map / Measure / Manage
- **EU AI Act**: system is **high-risk** (industrial safety / critical infrastructure). Documentation must be notified-body-review ready.

Required files:
- Model Card (Mitchell et al. format, adapted)
- Risk Register (failure modes, mitigations, residual risk, owner)
- Drift Monitor (input + prediction drift, thresholds, escalation)
- HITL Workflow (review triggers, owner, SLA)
- Rollback Procedure (versioning, fallback model, decision tree)
- Audit Trail (every prediction → model version, inputs, SHAP top-5, timestamp, latency)

## README requirements
Executive-grade. Opens with business case — asset uptime, capital allocation, regulatory exposure — not architecture. Governance section prominent, not buried. One Mermaid diagram of end-to-end system. No ML jargon in the first 300 words.

## Code standards
- Type hints everywhere
- NumPy-style docstrings
- Black + ruff, lines ≤ 100
- No notebooks committed with execution output unless intentional
- All randomness seeded
- Every model artifact saved with version + git SHA + training data hash

## Execution plan
Phased roadmap with binary done-gates lives in [`ROADMAP.md`](ROADMAP.md). Critical path: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10. Never cut governance (Phase 6) — it's the differentiator.

## Current state (fill in before the session starts)
- Repo path: `C:\Users\alanm\OneDrive\Área de Trabalho\cmapss-rul-governance\cmapss-rul-governance`
- Current branch: `main` (clean)
- Last shipped: `bf44ddb` — ruff UP017 fix (`datetime.UTC` alias) + black formatting (#2). Initial scaffold landed in `87085a4`.
- Active phase:
- Next up:
- Blockers:

## How to work with me
- Direct, short, implementation-first. No preamble.
- No "would you like me to..." unless there's a real fork.
- Show code, then explain briefly if needed — not the reverse.
- If ambiguous, make the call and flag the assumption in one line.
- Surface real tradeoffs (latency vs. accuracy, governance overhead vs. simplicity); skip generic best-practice lectures.
- Governance doc changes: write the diff in markdown, don't paraphrase what you'd change.

## First task on load
Read repo structure, run `pytest`, then summarize:
1. What's shipped
2. What's broken
3. What's missing against the governance checklist above

Wait for my call on what to pick up.
