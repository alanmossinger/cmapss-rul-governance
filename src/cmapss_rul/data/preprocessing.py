"""Preprocessing pipeline for C-MAPSS — RUL labeling, normalization, windowing.

All stateful steps (normalizer, dropped columns, operating-condition clusterer)
are *fit on train only* and reused for validation and test. This is enforced by
the :class:`PreprocessingArtifacts` dataclass — the pipeline serialises it next
to the parquet output, so val/test reads load the same statistics.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler

from cmapss_rul.config import DEFAULT_RUL_CLIP, DEFAULT_WINDOW_SIZE, SEED
from cmapss_rul.data.loader import SENSOR_COLUMNS, SETTING_COLUMNS

PIPELINE_VERSION = "0.1.0"

#: Subsets with multiple operating conditions — need per-condition normalization.
MULTI_CONDITION_SUBSETS = frozenset({"FD002", "FD004"})

#: Number of operating-condition clusters in FD002/FD004 per the original paper.
N_OPERATING_CONDITIONS = 6


# ---------------------------------------------------------------------------
# RUL labeling
# ---------------------------------------------------------------------------


def compute_rul(df: pd.DataFrame, clip: int = DEFAULT_RUL_CLIP) -> pd.Series:
    """Compute Remaining Useful Life per row for **training** trajectories.

    Training trajectories run to failure, so RUL at cycle ``c`` of unit ``u`` is
    ``max_cycle(u) - c``. Clipped at ``clip`` cycles to model the
    piecewise-linear degradation assumption (Heimes 2008): RUL is constant
    early in life and only starts decaying once damage is observable.
    """
    max_cycle = df.groupby("unit")["cycle"].transform("max")
    rul = max_cycle - df["cycle"]
    return rul.clip(upper=clip)


def compute_test_rul(
    test_df: pd.DataFrame, rul_at_last_cycle: pd.Series, clip: int = DEFAULT_RUL_CLIP
) -> pd.Series:
    """Compute RUL for **test** trajectories.

    Test trajectories are truncated before failure. The ground-truth file
    supplies RUL at the final observed cycle of each unit; intermediate cycles
    have RUL = ``true_final_rul + (last_observed_cycle - cycle)``.

    Parameters
    ----------
    test_df : pd.DataFrame
        Long-format test dataframe with columns ``unit`` and ``cycle``.
    rul_at_last_cycle : pd.Series
        Ground-truth RUL at last observed cycle, indexed by unit ID.
    clip : int
        Same piecewise-linear clip as training labels.
    """
    last_cycle = test_df.groupby("unit")["cycle"].transform("max")
    final_rul = test_df["unit"].map(rul_at_last_cycle)
    if final_rul.isna().any():
        missing_units = sorted(test_df.loc[final_rul.isna(), "unit"].unique().tolist())
        raise ValueError(f"RUL ground-truth missing for test units: {missing_units}")
    rul = final_rul + (last_cycle - test_df["cycle"])
    return rul.clip(upper=clip)


# ---------------------------------------------------------------------------
# Constant-column detection
# ---------------------------------------------------------------------------


def find_constant_columns(df: pd.DataFrame, columns: list[str], tol: float = 1e-6) -> list[str]:
    """Return columns whose standard deviation across the train set is below ``tol``.

    C-MAPSS sensors 1, 5, 6, 10, 16, 18, 19 are constant in FD001/FD003; including
    them adds noise without signal and breaks min-max scaling (zero range).
    """
    stds = df[columns].std()
    return sorted(stds[stds < tol].index.tolist())


# ---------------------------------------------------------------------------
# Per-operating-condition normalization
# ---------------------------------------------------------------------------


@dataclass
class OperatingConditionNormalizer:
    """Per-cluster min-max scaler for multi-condition C-MAPSS subsets.

    For FD002 and FD004 the engine is run under six discrete operating
    conditions identified by ``setting_1..3``. Sensor magnitudes vary
    sharply between conditions, so normalising globally compresses the
    signal we care about. The standard remedy (Babu et al. 2016) is to
    cluster operating settings then min-max normalise sensors *within*
    each cluster.

    Fit on train only; the cluster centroids and per-cluster scalers are
    persisted in :class:`PreprocessingArtifacts` and re-applied to val/test.
    """

    n_clusters: int = N_OPERATING_CONDITIONS
    seed: int = SEED
    clusterer: KMeans | None = field(default=None, init=False, repr=False)
    scalers: dict[int, MinMaxScaler] = field(default_factory=dict, init=False, repr=False)
    feature_columns: list[str] = field(default_factory=list, init=False, repr=False)

    def fit(self, df: pd.DataFrame, feature_columns: list[str]) -> OperatingConditionNormalizer:
        self.feature_columns = list(feature_columns)
        self.clusterer = KMeans(n_clusters=self.n_clusters, random_state=self.seed, n_init=10)
        cluster_ids = self.clusterer.fit_predict(df[SETTING_COLUMNS].to_numpy())

        for cid in range(self.n_clusters):
            mask = cluster_ids == cid
            if not mask.any():
                continue
            scaler = MinMaxScaler()
            scaler.fit(df.loc[mask, self.feature_columns].to_numpy())
            self.scalers[cid] = scaler
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.clusterer is None:
            raise RuntimeError("OperatingConditionNormalizer must be fit before transform")
        out = df.copy()
        cluster_ids = self.clusterer.predict(df[SETTING_COLUMNS].to_numpy())
        for cid, scaler in self.scalers.items():
            mask = cluster_ids == cid
            if not mask.any():
                continue
            out.loc[mask, self.feature_columns] = scaler.transform(
                df.loc[mask, self.feature_columns].to_numpy()
            )
        return out


@dataclass
class GlobalNormalizer:
    """Single-cluster min-max scaler for single-condition subsets (FD001/FD003)."""

    scaler: MinMaxScaler | None = field(default=None, init=False, repr=False)
    feature_columns: list[str] = field(default_factory=list, init=False, repr=False)

    def fit(self, df: pd.DataFrame, feature_columns: list[str]) -> GlobalNormalizer:
        self.feature_columns = list(feature_columns)
        self.scaler = MinMaxScaler()
        self.scaler.fit(df[self.feature_columns].to_numpy())
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.scaler is None:
            raise RuntimeError("GlobalNormalizer must be fit before transform")
        out = df.copy()
        out[self.feature_columns] = self.scaler.transform(df[self.feature_columns].to_numpy())
        return out


Normalizer = GlobalNormalizer | OperatingConditionNormalizer


def make_normalizer(subset: str) -> Normalizer:
    """Pick the right normalizer for a given subset."""
    if subset in MULTI_CONDITION_SUBSETS:
        return OperatingConditionNormalizer()
    return GlobalNormalizer()


# ---------------------------------------------------------------------------
# Sliding-window construction
# ---------------------------------------------------------------------------


def make_windows(
    df: pd.DataFrame,
    feature_columns: list[str],
    window_size: int = DEFAULT_WINDOW_SIZE,
    last_only: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Construct sliding windows from a long-format dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain ``unit``, ``cycle``, ``RUL`` and ``feature_columns``.
        Rows must already be sorted by (unit, cycle).
    feature_columns : list[str]
        Sensor / setting columns to stack into each window.
    window_size : int
        Number of consecutive cycles per window.
    last_only : bool
        If True, return only the **last** window per unit. This is the
        canonical evaluation mode for C-MAPSS test sets — one prediction
        per engine, scored against the supplied ground-truth RUL.

    Returns
    -------
    X : ndarray, shape (n_windows, window_size, n_features)
    y : ndarray, shape (n_windows,)
        RUL at the *final* cycle of each window.
    unit_ids : ndarray, shape (n_windows,)
        Unit ID each window originated from — used downstream for
        no-leakage validation and per-unit scoring.
    """
    if window_size < 1:
        raise ValueError(f"window_size must be ≥ 1, got {window_size}")

    n_features = len(feature_columns)
    X_chunks: list[np.ndarray] = []
    y_chunks: list[np.ndarray] = []
    unit_chunks: list[np.ndarray] = []

    for unit, unit_df in df.groupby("unit", sort=True):
        values = unit_df[feature_columns].to_numpy(dtype=np.float32)
        ruls = unit_df["RUL"].to_numpy(dtype=np.float32)
        n_cycles = len(values)
        if n_cycles < window_size:
            # Pad with the first available row so we still emit one window.
            pad = np.repeat(values[:1], window_size - n_cycles, axis=0)
            values = np.concatenate([pad, values], axis=0)
            ruls = np.concatenate([np.full(window_size - n_cycles, ruls[0]), ruls], axis=0)
            n_cycles = window_size

        if last_only:
            X_chunks.append(values[-window_size:].reshape(1, window_size, n_features))
            y_chunks.append(ruls[-1:])
            unit_chunks.append(np.array([unit], dtype=np.int64))
            continue

        n_windows = n_cycles - window_size + 1
        windows = np.lib.stride_tricks.sliding_window_view(
            values, window_shape=(window_size, n_features)
        ).reshape(n_windows, window_size, n_features)
        X_chunks.append(windows)
        y_chunks.append(ruls[window_size - 1 :])
        unit_chunks.append(np.full(n_windows, unit, dtype=np.int64))

    X = np.concatenate(X_chunks, axis=0) if X_chunks else np.empty((0, window_size, n_features))
    y = np.concatenate(y_chunks, axis=0) if y_chunks else np.empty((0,))
    units = np.concatenate(unit_chunks, axis=0) if unit_chunks else np.empty((0,), dtype=np.int64)
    return X, y, units


# ---------------------------------------------------------------------------
# Artifacts — what the pipeline persists for reproducibility
# ---------------------------------------------------------------------------


@dataclass
class PreprocessingArtifacts:
    """Stateful preprocessing objects, fit on train, applied to val/test.

    Persisted alongside the processed parquets so downstream phases (model
    training, inference) can reload the same normalization without recomputing.
    """

    subset: str
    normalizer: Normalizer
    dropped_columns: list[str]
    feature_columns: list[str]
    pipeline_version: str = PIPELINE_VERSION


def feature_columns_for(dropped: list[str]) -> list[str]:
    """Return sensor columns surviving the constant-column drop, in canonical order."""
    return [c for c in SENSOR_COLUMNS if c not in dropped]
