# Drift Monitoring

**Owner:** Model Owner
**Last updated:** 2026-05-23

---

## What We Monitor

| Drift type | Definition | Detection method | Threshold |
|---|---|---|---|
| **Feature drift** | Distribution of an input feature in production differs from training | Population Stability Index (PSI), Kolmogorov-Smirnov test | PSI > 0.10 = investigate; > 0.25 = trigger rollback consideration |
| **Prediction drift** | Distribution of predicted RUL differs from historical | KS test on rolling 7-day prediction distribution vs reference | KS p-value < 0.01 = investigate |
| **Concept drift** | Relationship between inputs and ground truth has changed | Override accuracy from HITL log; back-filled outcomes | Override accuracy > 60% (model wrong) = retraining trigger |
| **Performance drift** | Model error on engines with known outcomes has degraded | Rolling RMSE on cohorts with end-of-life ground truth | RMSE > 1.5× validation RMSE = trigger rollback |

## Reference Distributions

A reference distribution is captured at training time for every input feature and for predicted RUL. References are versioned with the model and stored in the registry.

## Detection Cadence

| Monitor | Cadence | Output |
|---|---|---|
| Feature drift (PSI, KS) | Daily | Per-feature drift score logged; alert if > threshold |
| Prediction drift | Daily | Rolling 7-day vs reference KS; alert if p < 0.01 |
| Concept drift | Continuous (event-driven on outcome ground truth) | Override-accuracy moving average logged |
| Performance drift | Daily | Rolling RMSE on closed cohorts |

## Alerting

Drift alerts route through the same channel as rollback triggers. The drift monitor does not autonomously roll back; it informs the rollback decision.

## False Positive Management

Drift monitors are noisy. False positives erode operator trust faster than missed detections. Mitigations:

- Two-stage thresholds (investigate vs. act)
- Minimum sustained-violation window (24 hours for PSI, 7 days for performance) before triggering rollback consideration
- Quarterly threshold review based on observed false-positive rate

## Audit Implications

Every drift detection event is logged to the audit trail with: timestamp, monitor type, feature (if applicable), metric value, threshold, decision taken. This produces a complete record of "what the system knew about itself" — essential for regulatory review.
