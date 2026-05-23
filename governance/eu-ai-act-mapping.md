# EU AI Act — Alignment Mapping

This document maps the EU AI Act's high-risk system requirements (primarily Title III, Chapter 2, Articles 8–15) to concrete artifacts in this repository.

Industrial predictive maintenance systems used as safety components in regulated machinery may fall within Annex III high-risk classification depending on deployment context. This repository is built to that bar regardless of the specific deployment determination — meeting the higher standard preserves optionality.

**Last updated:** 2026-05-23
**Owner:** Alan Mössinger (Chief AI Officer)

---

## Article 9 — Risk Management System

> _High-risk AI systems shall have a risk management system established, implemented, documented and maintained._

| Requirement | Repository Artifact |
|---|---|
| Iterative risk management process throughout lifecycle | [Risk Register](./risk-register.md) with quarterly review cadence |
| Identification and analysis of known and foreseeable risks | Risk register sections R-001 through R-007 |
| Estimation and evaluation of risks under reasonably foreseeable misuse | Model card "Out-of-Scope Use" section |
| Adoption of suitable risk management measures | Mitigations column in risk register |
| Testing to identify most appropriate risk management measures | Pre-production validation in shadow mode (rollback procedure) |

## Article 10 — Data and Data Governance

> _High-risk AI systems shall be developed on the basis of training, validation and testing data sets that meet quality criteria._

| Requirement | Repository Artifact |
|---|---|
| Data governance and management practices | [Data Card](./data-card.md) |
| Examination of possible biases | Per-subset performance reporting in model card surfaces operating-regime disparities |
| Relevant data preparation operations documented | Preprocessing pipeline in `src/cmapss_rul/data/` with version control |
| Data quality criteria specified | Data card "Known Limitations" section |
| Data appropriate for the intended purpose | Data card "Provenance" and model card "Intended Use" |
| Statistically representative datasets | C-MAPSS subsets FD001–FD004 cover four operating-regime / fault-mode combinations |

## Article 11 — Technical Documentation

> _Technical documentation of a high-risk AI system shall be drawn up before that system is placed on the market._

| Annex IV Requirement | Repository Artifact |
|---|---|
| General description of the AI system | [README](../README.md) |
| Detailed description of the elements of the AI system and process for development | [Architecture](../docs/architecture.md), source tree, model card |
| Detailed information about the monitoring, functioning and control | [Drift monitoring](./drift-monitoring.md), [HITL protocol](./hitl-protocol.md), [audit trail](./audit-trail.md) |
| Detailed description of the risk management system | [Risk register](./risk-register.md) |
| Description of any change made through lifecycle | Git history, model registry version log |
| Standards applied | This document, [NIST AI RMF mapping](./nist-ai-rmf-mapping.md) |
| EU declaration of conformity | _Generated upon production deployment from registry metadata_ |

## Article 12 — Record-Keeping

> _High-risk AI systems shall be designed and developed with capabilities enabling the automatic recording of events ('logs') while the systems are operating._

| Requirement | Repository Artifact |
|---|---|
| Automatic event logging over lifetime | [Audit trail](./audit-trail.md) — append-only, 7-year retention |
| Logs enable monitoring relevant to risk and substantial modification | Drift monitor outputs logged with predictions |
| Logs enable post-market monitoring | Audit log schema includes model version, input snapshot, prediction, SHAP attribution, HITL decision |

## Article 13 — Transparency and Provision of Information to Users

> _High-risk AI systems shall be designed and developed in such a way to ensure that their operation is sufficiently transparent._

| Requirement | Repository Artifact |
|---|---|
| Instructions for use accompanying the system | [Model card](./model-card.md) "Intended Use" and "Out-of-Scope Use" |
| Identity and contact of the provider | Model card "Owner" + repository [CODEOWNERS](../.github/CODEOWNERS) |
| Characteristics, capabilities, limitations of performance | Model card per-subset performance table + limitations section |
| Foreseeable circumstances which may lead to risks | Risk register |
| Performance regarding specific persons or groups | Per-subset reporting in model card |
| Specifications for input data | API schemas in `src/cmapss_rul/api/schemas.py` with Pydantic validation |
| Human oversight measures | [HITL protocol](./hitl-protocol.md) |
| Expected lifetime and maintenance measures | Model card "Maintenance and Versioning" section |

## Article 14 — Human Oversight

> _High-risk AI systems shall be designed and developed in such a way that they can be effectively overseen by natural persons during the period in which the AI system is in use._

| Requirement | Repository Artifact |
|---|---|
| Capability to fully understand system capacities and limitations | SHAP explanations surfaced with every prediction |
| Awareness of automation bias | HITL protocol explicitly addresses; quarterly disagreement review |
| Ability to correctly interpret output | SHAP attribution + confidence interval + reference distribution |
| Ability to decide not to use the system | HITL gate is mandatory, not advisory |
| Ability to intervene or interrupt | Override mechanism in HITL protocol; [rollback procedure](./rollback-procedure.md) |

## Article 15 — Accuracy, Robustness, and Cybersecurity

> _High-risk AI systems shall be designed and developed in such a way that they achieve, in light of their intended purpose, an appropriate level of accuracy, robustness and cybersecurity._

| Requirement | Repository Artifact |
|---|---|
| Accuracy levels declared in instructions for use | Model card per-subset RMSE table |
| Resilient to errors, faults, inconsistencies | Drift monitor + input validation + rollback procedure |
| Technical redundancy solutions | Blue/green deployment pattern in rollback procedure |
| Self-learning systems — feedback loops addressed | Retraining cadence with shadow-mode validation gate |
| Resilient against unauthorized attempts to alter behavior | Risk R-007 (adversarial input) mitigations |
| Cybersecurity measures appropriate to circumstances | API authentication, rate limiting, dependency audit |

---

## Conformity Assessment Readiness

Where the EU AI Act requires a conformity assessment, the artifacts above provide the substantive basis. The conformity assessment itself is a process executed at deployment time and is out of scope of this repository — but the repository is designed so that the assessment can be executed without retroactive documentation work.

## References

- Regulation (EU) 2024/1689 of the European Parliament and of the Council of 13 June 2024 laying down harmonised rules on artificial intelligence (AI Act).
- EU AI Act Annex III — High-Risk AI Systems.
- EU AI Act Annex IV — Technical Documentation.
