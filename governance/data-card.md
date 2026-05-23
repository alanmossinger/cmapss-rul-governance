# Data Card: NASA C-MAPSS Turbofan Engine Dataset

**Owner:** Model Owner
**Last updated:** 2026-05-23

---

## Dataset Identity

- **Name:** Commercial Modular Aero-Propulsion System Simulation (C-MAPSS)
- **Source:** NASA Prognostics Center of Excellence Data Repository
- **Citation:** Saxena, A., Goebel, K., Simon, D., & Eklund, N. (2008). _Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation._ International Conference on Prognostics and Health Management.
- **License:** Public domain (NASA-produced)
- **Original purpose:** Benchmark dataset for prognostics and health management research

## What's in the Dataset

The dataset comprises four subsets (FD001–FD004), each containing run-to-failure trajectories for turbofan engines simulated under varying operating conditions and fault modes.

| Subset | Trajectories (train) | Trajectories (test) | Operating Conditions | Fault Modes |
|---|---|---|---|---|
| FD001 | 100 | 100 | 1 | 1 (HPC degradation) |
| FD002 | 260 | 259 | 6 | 1 (HPC degradation) |
| FD003 | 100 | 100 | 1 | 2 (HPC + Fan degradation) |
| FD004 | 248 | 249 | 6 | 2 (HPC + Fan degradation) |

### Features per cycle

- 3 operational settings
- 21 sensor measurements (temperature, pressure, fan speed, etc.)
- Unit number (engine identifier)
- Cycle number

### Target

Remaining Useful Life (RUL) in operational cycles.

## Sampling and Coverage

- Engines start with varying degrees of initial wear; failure trajectories span 128 to 525 cycles depending on subset.
- Sensor noise and operating-condition variability are simulated, not field-measured.
- Each engine experiences exactly one fault mode through to failure.

## Known Limitations

1. **Simulated, not field data.** C-MAPSS is a high-fidelity simulation, but it is not real engine telemetry. Performance on production engines requires independent validation through shadow-mode deployment.
2. **Single fault mode per trajectory.** Real engines may experience multiple concurrent degradation modes; the model trained here will not have seen those combinations.
3. **No environmental detail.** Ambient conditions, altitude, and humidity are abstracted; if these matter operationally they are not represented.
4. **No maintenance interventions.** Real engine trajectories include maintenance events; C-MAPSS trajectories run to failure uninterrupted.
5. **Cycle definition.** A "cycle" is a flight in commercial aviation; cycle-time variability is not modeled.

## Bias Considerations

C-MAPSS does not contain personal or demographic data, so traditional fairness concerns do not directly apply. However, **operating-regime bias** is material: models trained primarily on FD001 conditions will not transfer to FD002 conditions without retraining. This is why this repository reports performance per-subset rather than as a pooled average.

## Preprocessing

Documented in `src/cmapss_rul/data/preprocessing.py`. Pipeline includes:

1. Min-max normalization per sensor per operating regime
2. Sliding-window feature construction (window size and stride configurable)
3. RUL clipping (typically to 125 cycles, per standard benchmark practice)
4. Operating-regime classification as an explicit feature for FD002 and FD004

Preprocessing pipeline is versioned and logged with each model release.

## Data Quality Checks

| Check | Action on failure |
|---|---|
| Sensor value within physical range | Reject row, log to audit trail |
| Cycle numbers monotonic per unit | Reject trajectory, alert Model Owner |
| RUL target non-negative | Reject row, log to audit trail |
| Operating-regime cluster count matches expected | Investigate before training |

## Refresh Cadence

C-MAPSS is a static research dataset and does not refresh. For deployments using real engine telemetry, refresh cadence is set at the deployment level and documented in the deployment's own data card derived from this template.

## Download Instructions

The C-MAPSS dataset is hosted at NASA's Prognostics Center of Excellence Data Repository. See `data/README.md` for current download instructions and integrity check hashes.

## Provenance Hash

A SHA-256 hash of the canonical dataset is stored with each model release. Models referencing a dataset hash that cannot be reproduced from the canonical source are blocked from production deployment.
