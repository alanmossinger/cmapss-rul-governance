# NIST AI RMF 1.0 — Alignment Mapping

This document maps the four NIST AI Risk Management Framework functions — **GOVERN, MAP, MEASURE, MANAGE** — to concrete artifacts and processes in this repository. It is not aspirational. Every row points to a specific file, code path, or workflow.

**Last updated:** 2026-05-23
**Owner:** Alan Mössinger (Chief AI Officer)

---

## GOVERN — Cultivate a culture of risk management

| NIST Sub-category | Repository Artifact |
|---|---|
| GV-1.1: Legal and regulatory requirements understood | [EU AI Act mapping](./eu-ai-act-mapping.md), this document |
| GV-1.2: Characteristics of trustworthy AI integrated into organizational policies | [Risk Register](./risk-register.md), [Model Card](./model-card.md) |
| GV-1.4: Risk management is documented | [Risk Register](./risk-register.md) with quarterly review cadence |
| GV-2.1: Roles, responsibilities, and lines of communication documented | [CODEOWNERS](../.github/CODEOWNERS), risk register owner column |
| GV-3.2: Policies and procedures for human-AI configurations | [HITL Protocol](./hitl-protocol.md) |
| GV-4.1: Organizational practices in place for AI risk management | This repository's structure: governance as code, not governance as PDF |
| GV-5.1: Policies for stakeholder engagement | Model card "intended users" section; HITL disagreement logging |
| GV-6.1: Policies for third-party risks | Dependency audit in CI, [data card](./data-card.md) source provenance |

## MAP — Context is recognized and risks are identified

| NIST Sub-category | Repository Artifact |
|---|---|
| MP-1.1: Intended purpose, settings, users documented | [Model Card](./model-card.md) "Intended Use" and "Out-of-Scope Use" |
| MP-1.2: Inter-disciplinary AI actors collaborate | Model card lists Model Owner, Platform Lead, Operations Lead, CAIO |
| MP-2.1: Tasks and methods documented | [README](../README.md) architecture section + model card |
| MP-2.2: Information about system's knowledge limits documented | Model card "Limitations and Known Risks" |
| MP-2.3: Scientific integrity and TEVV considerations identified | Per-subset performance reporting (no aggregate-only metrics) |
| MP-3.1: Potential benefits assessed | Risk register implicitly via residual-risk acceptance |
| MP-3.4: Processes for human oversight defined | [HITL Protocol](./hitl-protocol.md) |
| MP-4.1: Approaches for mapping AI risks documented | [Risk Register](./risk-register.md) scoring methodology |
| MP-5.1: Likelihood and magnitude of impact characterized | Risk register likelihood × impact scoring |
| MP-5.2: Risk tolerance defined | Acceptance threshold ≤ 6 documented in risk register |

## MEASURE — Risks are assessed, analyzed, and tracked

| NIST Sub-category | Repository Artifact |
|---|---|
| MS-1.1: Approaches and metrics for measurement identified | Model card per-subset RMSE table |
| MS-1.3: Internal experts and external stakeholders engaged | HITL disagreement review (quarterly) |
| MS-2.1: Test sets, metrics, details documented | Model card, data card, training scripts |
| MS-2.2: Evaluations involve domain experts | HITL protocol mandates maintenance engineer review |
| MS-2.3: AI system performance evaluated | CI `model-validation.yml` workflow with performance gates |
| MS-2.5: AI system reliability assessed | Drift monitor (PSI, KS) with thresholds |
| MS-2.6: Computational efficiency assessed | Model card "Inference (ms)" column |
| MS-2.7: AI system security assessed | Risk R-007 (adversarial input) with mitigations |
| MS-2.8: Risks of underrepresented groups assessed | Per-subset reporting (FD001–FD004) — surfaces operating-regime disparities |
| MS-2.9: Model explanation methods assessed | [SHAP analysis](../src/cmapss_rul/explainability/) |
| MS-2.10: Privacy risks assessed | N/A — non-human data; documented in model card |
| MS-2.11: Fairness assessed | Per-subset reporting prevents masking of regime-specific failures |
| MS-2.12: Environmental impact assessed | _TBD — to be added with training-run carbon tracking_ |
| MS-2.13: System metrics tracked over time | Audit log + drift monitor with historical retention |
| MS-3.2: Risk tracking approaches considered | Quarterly risk register review |

## MANAGE — Risks are prioritized and acted upon

| NIST Sub-category | Repository Artifact |
|---|---|
| MG-1.1: Determination of risk treatment | Risk register acceptance threshold and CAIO sign-off |
| MG-1.2: Treatment of unacceptable negative risks | Risks above threshold block release via `governance-check.yml` |
| MG-1.3: Treatment determinations responsive | Rollback procedure for in-production risk realization |
| MG-2.1: Resources allocated to risk treatment | Risk register owner column |
| MG-2.2: Treatment plans documented | Mitigations column in risk register |
| MG-2.3: Risk treatments monitored | Drift monitor, audit trail, quarterly review |
| MG-2.4: Mechanisms for sustaining value | Retraining cadence in model card |
| MG-3.1: AI risks and benefits from third-party tracked | Dependency audit |
| MG-4.1: Post-deployment monitoring plans | Drift monitor + audit trail + HITL disagreement log |
| MG-4.2: Measurable activities for continual improvement | Quarterly risk register review, model retraining cadence |
| MG-4.3: Incident response procedures | [Rollback procedure](./rollback-procedure.md) |

---

## Coverage Summary

This mapping covers the NIST AI RMF Core. Where a sub-category is marked _TBD_, it is on the roadmap with target completion before production release. The `governance-check.yml` CI workflow validates that every sub-category in this mapping points to an existing artifact.

## References

- NIST AI 100-1, _Artificial Intelligence Risk Management Framework (AI RMF 1.0)_, January 2023.
- NIST AI RMF Playbook (companion document).
