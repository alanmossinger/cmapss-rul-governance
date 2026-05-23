# Audit Trail

**Owner:** Platform Lead
**Retention:** 7 years
**Last updated:** 2026-05-23

---

## Purpose

The audit trail is the system's institutional memory. It is what makes the rest of the governance layer credible: a model card is just a document if there is no audit trail proving the system actually behaved as described.

It serves four audiences:

1. **Regulators** investigating a specific incident
2. **Engineers** debugging unexpected production behavior
3. **The CAIO** reviewing system health quarterly
4. **Future operators** reconstructing why a decision was made

## What Gets Logged

Every prediction produces one audit record. Every governance event (drift detection, rollback, override, retraining) produces a separate record. Records are append-only and immutable once written.

### Prediction record schema

```yaml
record_type: prediction
record_id: <uuid>
timestamp: <iso8601>
model_version: <semver>
model_registry_id: <hash>
input:
  features: <full input vector>
  preprocessing_pipeline_version: <semver>
  schema_version: <semver>
output:
  predicted_rul: <int>
  confidence_interval: [<lower>, <upper>]
  shap_values: <per-feature attribution>
  reference_distribution_id: <hash>
context:
  operating_regime_detected: <enum>
  out_of_distribution_flag: <bool>
  hitl_tier_assigned: <enum>
hitl_outcome:
  reviewer_id: <user_id>     # populated post-review
  decision: <approve | override | defer>
  rationale: <free_text>     # populated for override and defer
  decision_timestamp: <iso8601>
ground_truth:
  actual_rul: <int>           # back-filled when known
  ground_truth_timestamp: <iso8601>
```

### Governance event record schema

```yaml
record_type: governance_event
record_id: <uuid>
timestamp: <iso8601>
event_type: <drift_detected | rollback | retraining_triggered | model_release | risk_register_updated>
model_version: <semver>
event_details: <event-specific payload>
actor: <user_id | system>
decision_authority: <role>
```

## Immutability

Records are written to an append-only store. Update and delete operations are not exposed to application code. Correction of an erroneous record is itself a new record (`record_type: correction`) referencing the original — the original is never altered.

This is what allows the audit trail to serve as evidence in a regulatory or legal context. A mutable log is not an audit trail.

## Retention

7 years from creation, aligned to common industrial recordkeeping requirements. Records older than 7 years may be archived to cold storage but are not deleted unless explicitly required by law (right-to-erasure exception, which does not generally apply to non-personal industrial data).

## Access Control

| Action | Authorized role |
|---|---|
| Write prediction record | API service principal |
| Write governance event | Model Owner, Platform Lead, CAIO, automated monitors |
| Read records | Model Owner, Platform Lead, CAIO, designated auditors |
| Export records for audit | CAIO with documented purpose |
| Delete records | _Not exposed to any role_ |

Access is logged. Read access at scale (bulk export) triggers a review notification to the CAIO.

## Reconstruction Test

Once per quarter the Platform Lead executes an audit-trail reconstruction test: pick a random production prediction from the last 90 days and reconstruct, from the audit trail alone:

1. The exact model version that produced it
2. The exact input vector
3. The SHAP attribution returned to the user
4. The HITL decision and rationale
5. Whether ground truth has been recorded

If reconstruction fails on any field, that is a Severity-2 audit finding requiring CAIO review.

## Performance Considerations

The audit log must not be on the critical path of prediction latency. Writes are asynchronous through a durable queue. Loss of a single audit record is treated as a Severity-2 incident; the system is sized so that the queue never drops messages under nominal load.
