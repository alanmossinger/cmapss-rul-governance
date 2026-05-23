# Model Card: C-MAPSS RUL Predictor

**Version:** 0.1.0 (scaffold)
**Owner:** Alan Mössinger (Chief AI Officer)
**Last Updated:** 2026-05-23
**Status:** Pre-production — under development

---

## Model Details

- **Model name:** `cmapss-rul-predictor`
- **Primary architectures:** Random Forest (baseline), LSTM, CNN-LSTM
- **Task:** Regression — predict Remaining Useful Life (RUL) in operational cycles for turbofan engines
- **Output:** Integer RUL estimate + confidence interval + SHAP attribution vector
- **Framework:** PyTorch (deep models), scikit-learn (baseline)
- **License:** Apache 2.0

## Intended Use

**Primary intended use.** Decision support for maintenance planning teams in industrial settings analogous to the C-MAPSS turbofan domain. The model produces RUL estimates that inform — but do not autonomously decide — maintenance scheduling.

**Primary intended users.** Maintenance engineers, reliability engineers, and operations supervisors with domain expertise sufficient to contextualize model output against physical inspection data.

**Operational role.** The model is a tier-2 decision support tool. All maintenance actions with safety, regulatory, or material cost implications require human confirmation through the documented [HITL protocol](./hitl-protocol.md).

## Out-of-Scope Use

The model **must not** be used for:

- Autonomous maintenance scheduling without human review
- Safety-critical go/no-go decisions on equipment not represented in training data
- Equipment classes outside aviation turbofan engines without re-validation
- Insurance, regulatory, or litigation determinations
- Any use that contradicts the documented HITL protocol

## Training Data

- **Source:** NASA C-MAPSS dataset (Saxena et al., 2008), subsets FD001–FD004
- **Provenance:** Public NASA Prognostics Center of Excellence Data Repository
- **Size:** ~30,000 engine cycles across four operational regimes
- **Known limitations:**
  - Simulated, not field-collected — model performance on real engine data requires independent validation
  - Single fault mode per subset
  - Limited operating-condition coverage relative to the global commercial aviation fleet
- See [Data Card](./data-card.md) for full detail.

## Performance

Performance is reported per-subset because operating-regime differences between FD001–FD004 produce materially different model behavior. **Aggregate performance metrics are not reported** because they would mask sub-population disparities — a violation of the model card discipline.

_To be populated as models ship._

| Subset | Operating Conditions | Fault Modes | RMSE (target) | Coverage |
|---|---|---|---|---|
| FD001 | 1 | 1 | _TBD_ | _TBD_ |
| FD002 | 6 | 1 | _TBD_ | _TBD_ |
| FD003 | 1 | 2 | _TBD_ | _TBD_ |
| FD004 | 6 | 2 | _TBD_ | _TBD_ |

## Limitations and Known Risks

- **Distribution shift.** The model assumes operating conditions remain within the training distribution. The [drift monitor](./drift-monitoring.md) detects and escalates excursions.
- **Late-life prediction degradation.** RUL prediction accuracy typically degrades for engines in the late stage of life where degradation is non-linear and sensor noise increases.
- **Simulated-data bias.** Performance on real engines may differ; field deployment requires shadow-mode validation.

## Ethical Considerations

While turbofan RUL prediction does not involve human-subject data, two considerations apply:

1. **Worker displacement risk.** Predictive maintenance systems can be used to justify reductions in maintenance staffing. The HITL protocol explicitly preserves maintenance engineer judgment as the decision authority, not as a check-the-box overlay.
2. **Liability allocation.** When the model is wrong, who is accountable? The audit trail and rollback procedure are designed to make this answerable rather than diffuse.

## Maintenance and Versioning

- **Retraining cadence:** Quarterly, or upon drift threshold breach (see [drift monitoring](./drift-monitoring.md))
- **Model versioning:** Semantic versioning with model registry tracking input schema, training data hash, and performance metrics
- **Deprecation policy:** Models are retired 90 days after a successor reaches production; deprecated models remain queryable for audit purposes for 7 years

## References

- Saxena, A., Goebel, K., Simon, D., & Eklund, N. (2008). Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation. _International Conference on Prognostics and Health Management_.
- Mitchell, M. et al. (2019). Model Cards for Model Reporting. _Proceedings of FAT*_.
- NIST AI Risk Management Framework 1.0 (2023).
