# Human-in-the-Loop (HITL) Protocol

**Owner:** Operations Lead
**Effective:** Upon production release
**Last updated:** 2026-05-23

---

## Purpose

This protocol defines when human review is mandatory, who reviews, and how disagreements are logged. It is designed to satisfy EU AI Act Article 14 (Human Oversight) and NIST AI RMF MP-3.4 (Processes for human oversight defined).

## Principle

**The model is decision support. The human is the decision authority.**

This is not a slogan. It is enforced at three points: at the API contract, at the audit log, and at the operating procedure. A maintenance action that proceeds without recorded human review is a process failure, not an acceptable optimization.

## When Human Review is Mandatory

Human review is mandatory in **all** of the following cases:

1. **High-impact action.** Any maintenance action with safety, regulatory, or material cost implications above the threshold set by the operating unit (default: any action exceeding $10K labor + parts, or any action affecting flight-critical components).
2. **Low confidence.** Predicted RUL with confidence interval width exceeding 30% of the predicted value.
3. **Out-of-distribution input.** Drift monitor flags input as out of distribution.
4. **Conflicting signals.** Model prediction contradicts physical inspection data, recent maintenance history, or sensor anomaly flags.
5. **First-time operating regime.** Input falls into an operating regime the model has not been validated against.

For low-impact, in-distribution, high-confidence predictions, human review is **recommended** but not blocking — the audit log records the prediction and the human's acknowledgment.

## Who Reviews

| Decision tier | Reviewer |
|---|---|
| Tier 1 — informational | Maintenance technician (acknowledges) |
| Tier 2 — schedule maintenance | Maintenance engineer (approves) |
| Tier 3 — defer maintenance against schedule | Reliability engineer + maintenance engineer (both approve) |
| Tier 4 — emergency / safety-related | Operations supervisor + reliability engineer (both approve) |

Reviewer authority is enforced at the API authorization layer.

## Review Workflow

1. Model produces RUL prediction with confidence interval and SHAP attribution.
2. Tier is determined by the rule set above.
3. Reviewer is notified through the operations interface.
4. Reviewer sees: prediction, confidence interval, top-5 SHAP features, reference distribution, recent maintenance history, sensor anomaly flags.
5. Reviewer chooses: **Approve**, **Override**, or **Defer for second opinion**.
6. Decision is logged to the audit trail with reviewer identity, timestamp, decision, and free-text rationale (mandatory for Override and Defer).

## Disagreement Logging

Every override is logged with structured fields:

```yaml
override_id: <uuid>
prediction_id: <uuid>
model_version: <semver>
reviewer_id: <user_id>
reviewer_role: <enum>
predicted_rul: <int>
human_rul_estimate: <int>
disagreement_magnitude: <int>  # |predicted - human|
override_rationale: <free_text, required>
contextual_factors: <list>     # sensor anomaly, inspection finding, prior maintenance, other
outcome_actual: <int, populated upon engine end-of-life or scheduled inspection>
```

The `outcome_actual` field is back-filled when ground truth becomes available. The override log thereby becomes a continuously growing dataset of model-vs-human disagreements with known outcomes — the most valuable feedback signal a production AI system can have.

## Quarterly Disagreement Review

Every quarter, the Model Owner reviews the override log and computes:

- Override rate (overrides per 1000 predictions)
- Override accuracy when ground truth is available (was the human right, or the model?)
- Patterns in override rationale
- Reviewer-level variation in override behavior

The output of this review is one of:

- **No action** — disagreement rate and pattern within expected bounds
- **Retraining trigger** — model is systematically wrong in a recoverable way
- **Threshold adjustment** — confidence intervals require recalibration
- **Reviewer training** — disagreement pattern indicates automation bias or anti-bias

## Anti-Automation-Bias Measures

Automation bias is the single largest residual risk in HITL designs. Mitigations:

- **Confidence is communicated, not assumed.** Every prediction shows confidence interval and reference distribution.
- **SHAP attribution is required, not optional.** Reviewers see _why_, not just _what_.
- **Override is one click, not three.** The friction of overriding must not exceed the friction of approving.
- **Quarterly review surfaces reviewers with override rates near zero.** Near-zero override rates may indicate rubber-stamping rather than agreement.
- **Reviewer training emphasizes that the system is rewarded for being overruled when wrong.** Overriding a model is a feature, not a failure.
