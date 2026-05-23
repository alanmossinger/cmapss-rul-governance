# Risk Register

**Owner:** Alan Mössinger (Chief AI Officer)
**Review cadence:** Quarterly, or upon material change
**Last updated:** 2026-05-23

---

## Risk Scoring

- **Likelihood:** 1 (rare) → 5 (almost certain)
- **Impact:** 1 (negligible) → 5 (catastrophic)
- **Inherent risk:** Likelihood × Impact (before mitigation)
- **Residual risk:** Likelihood × Impact (after mitigation)
- **Acceptance threshold:** Residual ≤ 6 (Low/Moderate) auto-accept; > 6 requires CAIO sign-off

---

## Active Risks

### R-001 — Distribution Shift / Concept Drift

| Field | Value |
|---|---|
| **Category** | Model performance |
| **Description** | Real-world sensor distributions diverge from training distribution, causing silent degradation in RUL accuracy |
| **Inherent likelihood** | 4 |
| **Inherent impact** | 4 |
| **Inherent risk** | 16 (High) |
| **Mitigations** | (a) Drift monitor with KS and PSI thresholds; (b) automated alerting to model owner; (c) shadow-mode re-validation gate before redeployment |
| **Residual likelihood** | 2 |
| **Residual impact** | 3 |
| **Residual risk** | 6 (Moderate — accepted) |
| **Owner** | Model Owner |
| **Reference** | [drift-monitoring.md](./drift-monitoring.md) |

### R-002 — Over-Reliance / Automation Bias

| Field | Value |
|---|---|
| **Category** | Human factors |
| **Description** | Maintenance teams treat model output as authoritative, eroding domain judgment over time |
| **Inherent likelihood** | 4 |
| **Inherent impact** | 4 |
| **Inherent risk** | 16 (High) |
| **Mitigations** | (a) Mandatory HITL gate with override logging; (b) SHAP explanations surfaced with every prediction; (c) confidence intervals and explicit uncertainty communication; (d) quarterly disagreement review |
| **Residual likelihood** | 2 |
| **Residual impact** | 3 |
| **Residual risk** | 6 (Moderate — accepted) |
| **Owner** | Operations Lead |
| **Reference** | [hitl-protocol.md](./hitl-protocol.md) |

### R-003 — Inability to Explain a Specific Prediction

| Field | Value |
|---|---|
| **Category** | Explainability / regulatory |
| **Description** | A specific high-impact prediction cannot be explained to a regulator, engineer, or affected party |
| **Inherent likelihood** | 3 |
| **Inherent impact** | 5 |
| **Inherent risk** | 15 (High) |
| **Mitigations** | (a) SHAP values stored with every prediction in audit log; (b) reference distribution stored; (c) input feature snapshot stored; (d) model version pinned |
| **Residual likelihood** | 1 |
| **Residual impact** | 3 |
| **Residual risk** | 3 (Low — accepted) |
| **Owner** | Model Owner |
| **Reference** | [audit-trail.md](./audit-trail.md) |

### R-004 — Model Misbehavior Without Rollback Path

| Field | Value |
|---|---|
| **Category** | Operational resilience |
| **Description** | A model release behaves anomalously in production and there is no documented, tested rollback path |
| **Inherent likelihood** | 3 |
| **Inherent impact** | 5 |
| **Inherent risk** | 15 (High) |
| **Mitigations** | (a) Documented rollback procedure with defined triggers; (b) prior model version retained and queryable; (c) blue/green or canary deployment pattern; (d) quarterly rollback drill |
| **Residual likelihood** | 1 |
| **Residual impact** | 4 |
| **Residual risk** | 4 (Low — accepted) |
| **Owner** | Platform Lead |
| **Reference** | [rollback-procedure.md](./rollback-procedure.md) |

### R-005 — Audit Trail Incompleteness

| Field | Value |
|---|---|
| **Category** | Regulatory / forensics |
| **Description** | Audit trail lacks the information needed to reconstruct a past prediction during incident investigation or regulatory review |
| **Inherent likelihood** | 3 |
| **Inherent impact** | 4 |
| **Inherent risk** | 12 (Moderate) |
| **Mitigations** | (a) Defined audit schema; (b) immutable append-only log; (c) 7-year retention; (d) quarterly audit-trail reconstruction test |
| **Residual likelihood** | 1 |
| **Residual impact** | 3 |
| **Residual risk** | 3 (Low — accepted) |
| **Owner** | Platform Lead |
| **Reference** | [audit-trail.md](./audit-trail.md) |

### R-006 — Training Data Provenance Loss

| Field | Value |
|---|---|
| **Category** | Reproducibility / regulatory |
| **Description** | The exact training dataset used to produce a deployed model cannot be reconstructed |
| **Inherent likelihood** | 3 |
| **Inherent impact** | 4 |
| **Inherent risk** | 12 (Moderate) |
| **Mitigations** | (a) Dataset hash recorded in model registry; (b) raw data versioned and immutable; (c) preprocessing pipeline versioned in source control |
| **Residual likelihood** | 1 |
| **Residual impact** | 3 |
| **Residual risk** | 3 (Low — accepted) |
| **Owner** | Model Owner |
| **Reference** | [data-card.md](./data-card.md) |

### R-007 — Adversarial Input

| Field | Value |
|---|---|
| **Category** | Security |
| **Description** | An adversary submits crafted sensor data to elicit misleading predictions (e.g., to justify or avoid maintenance) |
| **Inherent likelihood** | 2 |
| **Inherent impact** | 4 |
| **Inherent risk** | 8 (Moderate) |
| **Mitigations** | (a) Input validation and range checks; (b) anomaly detection on input distributions; (c) authentication and authorization on API; (d) rate limiting |
| **Residual likelihood** | 1 |
| **Residual impact** | 3 |
| **Residual risk** | 3 (Low — accepted) |
| **Owner** | Platform Lead |
| **Reference** | [audit-trail.md](./audit-trail.md) |

---

## Risk Acceptance

All residual risks above the threshold require explicit CAIO sign-off documented in the model release notes. Current residual risk profile: **all risks at Moderate or Low — no risks above acceptance threshold**.

Sign-off below indicates acceptance of the residual risk profile as documented.

| Role | Name | Date | Signature |
|---|---|---|---|
| Chief AI Officer | Alan Mössinger | _pending release_ | _pending_ |
| Model Owner | _TBD_ | _pending release_ | _pending_ |
| Platform Lead | _TBD_ | _pending release_ | _pending_ |
