"""C-MAPSS data loading.

Reference: Saxena et al. (2008), NASA Prognostics Center of Excellence.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from cmapss_rul.config import CMAPSS_SUBSETS, RAW_DATA_DIR

SENSOR_COLUMNS = [f"sensor_{i}" for i in range(1, 22)]
SETTING_COLUMNS = [f"setting_{i}" for i in range(1, 4)]
META_COLUMNS = ["unit", "cycle"]
ALL_COLUMNS = META_COLUMNS + SETTING_COLUMNS + SENSOR_COLUMNS


def load_subset(subset: str, split: str = "train", data_dir: Path | None = None) -> pd.DataFrame:
    """Load a single C-MAPSS subset.

    Parameters
    ----------
    subset : str
        One of FD001, FD002, FD003, FD004.
    split : str
        "train" or "test".
    data_dir : Path | None
        Optional override of the data directory.

    Returns
    -------
    pd.DataFrame
        Columns: unit, cycle, setting_1..3, sensor_1..21
    """
    if subset not in CMAPSS_SUBSETS:
        raise ValueError(f"Unknown subset {subset!r}; expected one of {CMAPSS_SUBSETS}")
    if split not in ("train", "test"):
        raise ValueError(f"Unknown split {split!r}; expected 'train' or 'test'")

    base = data_dir or RAW_DATA_DIR
    path = base / f"{split}_{subset}.txt"

    if not path.exists():
        raise FileNotFoundError(
            f"C-MAPSS data not found at {path}. " f"See data/README.md for download instructions."
        )

    df = pd.read_csv(path, sep=r"\s+", header=None, names=ALL_COLUMNS)
    return df


def load_rul_file(subset: str, data_dir: Path | None = None) -> pd.Series:
    """Load the ground-truth RUL file accompanying a C-MAPSS test set.

    NASA C-MAPSS test trajectories are truncated *before* failure. The RUL_*.txt
    file gives the true remaining cycles at the last observed cycle of each unit,
    indexed in unit order (line 1 = unit 1, line 2 = unit 2, ...).

    Parameters
    ----------
    subset : str
        One of FD001, FD002, FD003, FD004.
    data_dir : Path | None
        Optional override of the data directory.

    Returns
    -------
    pd.Series
        RUL at the final observed cycle for each unit, indexed by unit number (1-based).
    """
    if subset not in CMAPSS_SUBSETS:
        raise ValueError(f"Unknown subset {subset!r}; expected one of {CMAPSS_SUBSETS}")

    base = data_dir or RAW_DATA_DIR
    path = base / f"RUL_{subset}.txt"
    if not path.exists():
        raise FileNotFoundError(
            f"C-MAPSS ground-truth RUL file not found at {path}. "
            "See data/README.md for download instructions."
        )

    values = pd.read_csv(path, sep=r"\s+", header=None).iloc[:, 0]
    values.index = pd.RangeIndex(start=1, stop=len(values) + 1, name="unit")
    values.name = "true_rul_at_last_cycle"
    return values


def dataset_hash(data_dir: Path | None = None) -> str:
    """Compute a SHA-256 hash of all canonical C-MAPSS files for provenance tracking."""
    base = data_dir or RAW_DATA_DIR
    hasher = hashlib.sha256()
    for subset in CMAPSS_SUBSETS:
        for split in ("train", "test"):
            path = base / f"{split}_{subset}.txt"
            if path.exists():
                hasher.update(path.read_bytes())
    return hasher.hexdigest()
