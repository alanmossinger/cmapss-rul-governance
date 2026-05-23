# Data Directory

This directory holds the NASA C-MAPSS dataset and any processed artifacts. **Raw data files are not committed to the repository** — see `.gitignore`. Provenance is tracked through a hash recorded with each model release; see [governance/data-card.md](../governance/data-card.md).

## Download

The C-MAPSS dataset is hosted at NASA's Prognostics Center of Excellence Data Repository.

Original source: https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/

Direct dataset page: https://data.nasa.gov/dataset/c-mapss-aircraft-engine-simulator-data

## Expected Layout

After download, the `data/raw/` directory should contain:

```
data/raw/
├── train_FD001.txt
├── train_FD002.txt
├── train_FD003.txt
├── train_FD004.txt
├── test_FD001.txt
├── test_FD002.txt
├── test_FD003.txt
├── test_FD004.txt
├── RUL_FD001.txt
├── RUL_FD002.txt
├── RUL_FD003.txt
└── RUL_FD004.txt
```

## File Format

Each `train_*` and `test_*` file is whitespace-delimited with 26 columns:

| Index | Column |
|---|---|
| 1 | unit number |
| 2 | cycle number |
| 3 | operational setting 1 |
| 4 | operational setting 2 |
| 5 | operational setting 3 |
| 6–26 | sensor measurements 1–21 |

The `RUL_*` files contain the true RUL for the last cycle of each test trajectory.

## Integrity Check

After download, verify file count and run the smoke test:

```bash
ls data/raw/*.txt | wc -l   # should be 12
pytest tests/test_smoke.py
```

A provenance hash will be computed and recorded automatically with each model release. See `src/cmapss_rul/data/loader.py::dataset_hash`.

## Citation

Saxena, A., Goebel, K., Simon, D., & Eklund, N. (2008). _Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation_. International Conference on Prognostics and Health Management.
