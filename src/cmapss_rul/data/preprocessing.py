"""Preprocessing pipeline for C-MAPSS — windowing, normalization, RUL labeling."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cmapss_rul.config import DEFAULT_RUL_CLIP, DEFAULT_WINDOW_SIZE

PIPELINE_VERSION = "0.1.0"


def compute_rul(df: pd.DataFrame, clip: int = DEFAULT_RUL_CLIP) -> pd.Series:
    """Compute Remaining Useful Life per row, clipped at `clip` cycles."""
    max_cycle = df.groupby("unit")["cycle"].transform("max")
    rul = max_cycle - df["cycle"]
    return rul.clip(upper=clip)


def make_windows(
    df: pd.DataFrame,
    feature_cols: list[str],
    window_size: int = DEFAULT_WINDOW_SIZE,
) -> tuple[np.ndarray, np.ndarray]:
    """Construct sliding windows of shape (n_windows, window_size, n_features)."""
    raise NotImplementedError("To be implemented in Phase 2")
