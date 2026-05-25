"""Train/validation splits by engine ID.

The C-MAPSS dataset records full run-to-failure trajectories per engine unit.
Splitting *within* a unit (e.g. random rows) leaks future cycles into the
training set, leading to optimistic offline metrics that collapse in
production. This module enforces splits at the **unit** boundary.

The split is deterministic given a seed, so re-running the pipeline produces
identical splits.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cmapss_rul.config import SEED


def split_units(
    train_df: pd.DataFrame,
    val_fraction: float = 0.2,
    seed: int = SEED,
) -> tuple[list[int], list[int]]:
    """Partition engine unit IDs into train and validation lists.

    Parameters
    ----------
    train_df : pd.DataFrame
        Long-format training dataframe with a ``unit`` column.
    val_fraction : float
        Fraction of units to hold out for validation. Default 0.2.
    seed : int
        RNG seed for reproducibility.

    Returns
    -------
    train_units, val_units : tuple[list[int], list[int]]
        Disjoint, sorted lists of unit IDs.
    """
    if not 0.0 < val_fraction < 1.0:
        raise ValueError(f"val_fraction must be in (0, 1), got {val_fraction}")

    units = np.array(sorted(train_df["unit"].unique()))
    if len(units) < 2:
        raise ValueError(
            f"Need at least 2 units to split, got {len(units)}. "
            "Check that the input dataframe contains training data."
        )

    rng = np.random.default_rng(seed)
    shuffled = rng.permutation(units)

    n_val = max(1, round(len(units) * val_fraction))
    val_units = sorted(shuffled[:n_val].tolist())
    train_units = sorted(shuffled[n_val:].tolist())
    return train_units, val_units


def apply_split(
    df: pd.DataFrame,
    train_units: list[int],
    val_units: list[int],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Slice a long-format dataframe into train / val partitions by unit ID.

    Raises if the union of units leaves any unit unassigned or any unit assigned
    to both partitions — both indicate a programming error upstream.
    """
    train_set = set(train_units)
    val_set = set(val_units)
    if overlap := train_set & val_set:
        raise ValueError(f"Train and val unit sets overlap: {sorted(overlap)}")

    all_assigned = train_set | val_set
    all_units = set(df["unit"].unique())
    if missing := all_units - all_assigned:
        raise ValueError(f"Units in df are unassigned to a split: {sorted(missing)}")

    train_part = df[df["unit"].isin(train_set)].reset_index(drop=True)
    val_part = df[df["unit"].isin(val_set)].reset_index(drop=True)
    return train_part, val_part
