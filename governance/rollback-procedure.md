# Rollback Procedure

**Owner:** Platform Lead
**Last updated:** 2026-05-23
**Drill cadence:** Quarterly

---

## Purpose

This document defines the triggers, decision authority, and mechanics for rolling back a model in production. Rollback is treated as a routine operational capability, not an emergency improvisation.

## Triggers

Any one of the following triggers immediate rollback consideration:

| Trigger | Detection | Decision authority |
|---|---|---|
| RMSE on rolling 7-day window exceeds 1.5× validation RMSE | Automated monitor | Auto-rollback to previous stable version; CAIO notified |
| Drift monitor reports PSI > 0.25 on any input feature for > 24 hours | Automated monitor | Auto-rollback; CAIO notified |
| Override rate exceeds 30% over 7 days | Automated monitor | Manual review by Model Owner within 24 hours |
| Override accuracy (when truth available) shows model wrong > 60% of cases | Quarterly review | Model Owner triggers rollback or retraining |
| External signal (regulatory notice, safety report, customer escalation) | Manual | CAIO authorizes rollback |
| API error rate > 1% over 1 hour | Automated monitor | Platform Lead investigates; rollback if model-related |

## Mechanics

The model registry holds at minimum the **previous two stable production versions** alongside the current. Each version carries:

- Model weights / serialized estimator
- Input schema (Pydantic model)
- Preprocessing pipeline version
- Performance metrics on the validation set
- SHAP background distribution
- Release notes with CAIO sign-off

A rollback is a routing change at the API layer:

```python
# pseudo
ACTIVE_MODEL_VERSION = "1.2.0"  # change to "1.1.0" to roll back
```

In production this is configuration, not code — change takes effect on next request without redeployment.

## Blue/Green Deployment Pattern

New model releases are deployed alongside the current production model. Traffic is shifted gradually:

| Stage | Duration | Traffic to new model |
|---|---|---|
| Shadow | 7 days | 0% (predictions logged for comparison, not served) |
| Canary | 3 days | 5% |
| Ramp | 4 days | 25% |
| Production | — | 100% |

Any trigger condition above the rollback table during ramp halts the rollout and reverts traffic to the prior version.

## Post-Rollback Procedure

After a rollback:

1. The rolled-back version is **not** purged. It is retained for audit and post-mortem.
2. Within 5 business days, the Model Owner produces a post-mortem covering: trigger, root cause, mitigation, prevention.
3. The risk register is updated if a new risk class was surfaced.
4. The post-mortem is reviewed in the next quarterly governance review.

## Rollback Drill

Once per quarter, the Platform Lead executes a rollback drill in staging:

1. Deploy a model release.
2. Execute rollback.
3. Verify previous version serves correctly.
4. Verify audit log records the rollback event.
5. Verify metrics return to baseline.
6. Document drill outcome.

If a quarterly drill fails, that constitutes a Severity-2 operational finding requiring CAIO review.

## What Rollback Does Not Solve

Rollback returns the system to a prior state. It does not address:

- Bad predictions already made and acted upon
- Customer or regulatory communication
- Underlying data drift driving the failure

These are addressed by the incident response process (separate document), not by the rollback procedure itself.
