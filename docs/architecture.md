# Architecture

## System View

```mermaid
flowchart TB
    subgraph CLIENT["Client Layer"]
        UI[Maintenance Operator UI]
        API_CLIENT[Programmatic API Client]
    end

    subgraph API["API Layer — FastAPI"]
        AUTH[Auth / RBAC]
        VALIDATE[Pydantic Input Validation]
        ROUTER[Request Router]
        EXPLAIN[SHAP Explanation Service]
    end

    subgraph MODEL["Model Layer"]
        REGISTRY[Model Registry]
        ACTIVE[Active Model<br/>CNN-LSTM v1.x]
        SHADOW[Shadow Model<br/>Next Candidate]
        BASELINE[RF Baseline<br/>Interpretable Floor]
    end

    subgraph GOV["Governance Layer — Always On"]
        AUDIT[Audit Logger<br/>Append-Only]
        DRIFT[Drift Monitor<br/>PSI · KS]
        HITL[HITL Gate]
        ROLLBACK[Rollback Controller]
    end

    subgraph DATA["Data Layer"]
        FEATURE_STORE[Feature Store]
        REFERENCE[Reference Distributions]
        TRUTH[Ground Truth Backfill]
    end

    UI --> AUTH
    API_CLIENT --> AUTH
    AUTH --> VALIDATE
    VALIDATE --> ROUTER
    ROUTER --> ACTIVE
    ACTIVE --> EXPLAIN
    EXPLAIN --> HITL
    HITL --> UI

    ROUTER -.shadow traffic.-> SHADOW

    ACTIVE --> AUDIT
    HITL --> AUDIT
    DRIFT --> AUDIT
    ROLLBACK --> AUDIT

    VALIDATE --> DRIFT
    DRIFT --> ROLLBACK
    ROLLBACK --> REGISTRY
    REGISTRY --> ACTIVE

    FEATURE_STORE --> ACTIVE
    REFERENCE --> DRIFT
    TRUTH --> AUDIT
```

## Request Flow — A Single Prediction

```mermaid
sequenceDiagram
    participant Op as Operator
    participant API as FastAPI
    participant V as Validator
    participant D as Drift Monitor
    participant M as Model
    participant E as SHAP Explainer
    participant H as HITL Gate
    participant A as Audit Logger

    Op->>API: POST /predict (sensor vector)
    API->>V: validate(input)
    V->>D: check_distribution(input)
    D-->>A: log drift score
    V->>M: predict(features)
    M-->>A: log prediction
    M->>E: explain(prediction)
    E-->>A: log SHAP attribution
    M->>H: assign_tier(prediction, confidence, drift_flag)
    H-->>Op: return prediction + explanation + tier
    Op->>H: approve | override | defer
    H-->>A: log HITL decision
```

## Model Training Pipeline

```mermaid
flowchart LR
    A[NASA C-MAPSS Raw] --> B[Data Quality Checks]
    B --> C[Preprocessing<br/>Pipeline v.X]
    C --> D[Sliding Window Features]
    D --> E[Train/Val Split<br/>per-unit, not per-cycle]
    E --> F[RF Baseline]
    E --> G[LSTM]
    E --> H[CNN-LSTM]
    F & G & H --> I[Validation Metrics<br/>per-subset]
    I --> J{Pass Performance<br/>Threshold?}
    J -- Yes --> K[Generate Model Card]
    J -- No --> L[Reject; investigate]
    K --> M[Compute SHAP Background]
    M --> N[Register Model<br/>w/ Dataset Hash]
    N --> O[Shadow Deploy<br/>7 days]
    O --> P{Shadow Performance<br/>Matches Validation?}
    P -- Yes --> Q[Canary 5%]
    P -- No --> R[Block; investigate]
    Q --> S[Ramp 25% → 100%]
```

## Component Responsibilities

| Component | Responsibility | Source path |
|---|---|---|
| Data loader | Read C-MAPSS, validate schema, hash dataset | `src/cmapss_rul/data/loader.py` |
| Preprocessor | Normalize, window, regime-detect | `src/cmapss_rul/data/preprocessing.py` |
| RF baseline | Interpretable performance floor | `src/cmapss_rul/models/baseline_rf.py` |
| LSTM | Sequence model, intermediate complexity | `src/cmapss_rul/models/lstm.py` |
| CNN-LSTM | Production model | `src/cmapss_rul/models/cnn_lstm.py` |
| SHAP service | Per-prediction attribution | `src/cmapss_rul/explainability/shap_analysis.py` |
| Drift monitor | PSI, KS, alerting | `src/cmapss_rul/governance/drift.py` |
| Audit logger | Append-only structured logs | `src/cmapss_rul/governance/audit_logger.py` |
| HITL gate | Tier assignment, override capture | `src/cmapss_rul/governance/hitl.py` |
| API service | Public interface | `src/cmapss_rul/api/main.py` |

## Non-Functional Requirements

| Concern | Target |
|---|---|
| Prediction latency (p95) | < 200 ms including SHAP |
| API availability | 99.9% monthly |
| Audit-log durability | Zero loss under nominal load; durable queue with at-least-once delivery |
| Drift-monitor cadence | Daily; alert within 1 hour of breach |
| Rollback time | < 60 seconds from decision to traffic-shifted |
| Model retraining | Quarterly, or upon drift-triggered |
