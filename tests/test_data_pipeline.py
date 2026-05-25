"""Phase 1 data layer tests.

Covers loader, RUL labeling, splits, normalization, windowing, and the
end-to-end pipeline orchestrator. All tests use the synthetic fixture from
``conftest.py`` — no real C-MAPSS data required.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from cmapss_rul.config import DEFAULT_RUL_CLIP, DEFAULT_WINDOW_SIZE
from cmapss_rul.data.loader import ALL_COLUMNS, load_rul_file, load_subset
from cmapss_rul.data.pipeline import build_all, build_subset, load_processed
from cmapss_rul.data.preprocessing import (
    GlobalNormalizer,
    OperatingConditionNormalizer,
    compute_rul,
    compute_test_rul,
    find_constant_columns,
    make_windows,
)
from cmapss_rul.data.splits import apply_split, split_units

# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def test_load_subset_returns_canonical_columns(cmapss_raw: Callable[..., Path]) -> None:
    raw = cmapss_raw(subsets=("FD001",))
    df = load_subset("FD001", split="train", data_dir=raw)
    assert list(df.columns) == ALL_COLUMNS
    assert df["unit"].min() == 1
    assert not df.isna().any().any()


def test_load_subset_rejects_unknown_subset(cmapss_raw: Callable[..., Path]) -> None:
    raw = cmapss_raw(subsets=("FD001",))
    with pytest.raises(ValueError, match="Unknown subset"):
        load_subset("FD999", data_dir=raw)


def test_load_subset_raises_when_data_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        load_subset("FD001", data_dir=tmp_path / "no_such_dir")


def test_load_rul_file_indexes_by_unit(cmapss_raw: Callable[..., Path]) -> None:
    raw = cmapss_raw(subsets=("FD001",), n_test_units=4)
    series = load_rul_file("FD001", data_dir=raw)
    assert series.index.tolist() == [1, 2, 3, 4]
    assert (series > 0).all()


# ---------------------------------------------------------------------------
# RUL labeling
# ---------------------------------------------------------------------------


def test_compute_rul_clips_and_decays_monotonically() -> None:
    df = pd.DataFrame({"unit": [1, 1, 1, 2, 2], "cycle": [1, 2, 200, 1, 2]})
    rul = compute_rul(df, clip=DEFAULT_RUL_CLIP)
    # unit 1 max=200; rul = [199, 198, 0] clipped at 125
    assert rul.tolist() == [DEFAULT_RUL_CLIP, DEFAULT_RUL_CLIP, 0, 1, 0]


def test_compute_test_rul_uses_ground_truth() -> None:
    test_df = pd.DataFrame({"unit": [1, 1, 1, 2, 2], "cycle": [10, 20, 30, 5, 15]})
    truth = pd.Series([20, 50], index=pd.Index([1, 2], name="unit"))
    rul = compute_test_rul(test_df, truth, clip=DEFAULT_RUL_CLIP)
    # unit 1 last cycle=30, truth=20 → 20 + (30-cycle) at each row
    assert rul.tolist() == [40, 30, 20, 60, 50]


def test_compute_test_rul_rejects_missing_units() -> None:
    test_df = pd.DataFrame({"unit": [1, 2], "cycle": [5, 5]})
    truth = pd.Series([20], index=pd.Index([1], name="unit"))
    with pytest.raises(ValueError, match="RUL ground-truth missing"):
        compute_test_rul(test_df, truth)


# ---------------------------------------------------------------------------
# Constant-column detection
# ---------------------------------------------------------------------------


def test_find_constant_columns_flags_zero_variance(cmapss_raw: Callable[..., Path]) -> None:
    raw = cmapss_raw(subsets=("FD001",))
    df = load_subset("FD001", split="train", data_dir=raw)
    sensors = [c for c in df.columns if c.startswith("sensor_")]
    constant = find_constant_columns(df, sensors)
    # Synthetic fixture pins sensor_5 at a constant.
    assert "sensor_5" in constant


# ---------------------------------------------------------------------------
# Splits
# ---------------------------------------------------------------------------


def test_split_units_is_deterministic_and_disjoint() -> None:
    df = pd.DataFrame({"unit": list(range(1, 21))})
    train_a, val_a = split_units(df, val_fraction=0.2, seed=42)
    train_b, val_b = split_units(df, val_fraction=0.2, seed=42)
    assert (train_a, val_a) == (train_b, val_b)
    assert set(train_a).isdisjoint(set(val_a))
    assert set(train_a) | set(val_a) == set(range(1, 21))
    assert len(val_a) == 4  # 20% of 20


def test_apply_split_detects_unassigned_units() -> None:
    df = pd.DataFrame({"unit": [1, 1, 2, 2, 3, 3], "cycle": [1, 2, 1, 2, 1, 2]})
    with pytest.raises(ValueError, match="unassigned"):
        apply_split(df, train_units=[1], val_units=[2])  # unit 3 missing


def test_apply_split_detects_overlap() -> None:
    df = pd.DataFrame({"unit": [1, 2], "cycle": [1, 1]})
    with pytest.raises(ValueError, match="overlap"):
        apply_split(df, train_units=[1, 2], val_units=[2])


# ---------------------------------------------------------------------------
# Normalizers
# ---------------------------------------------------------------------------


def test_global_normalizer_scales_to_unit_interval(cmapss_raw: Callable[..., Path]) -> None:
    raw = cmapss_raw(subsets=("FD001",))
    df = load_subset("FD001", split="train", data_dir=raw)
    features = [f"sensor_{i}" for i in range(2, 5)]  # skip constant sensor_5
    norm = GlobalNormalizer().fit(df, features)
    transformed = norm.transform(df)
    assert ((transformed[features] >= -1e-9) & (transformed[features] <= 1 + 1e-9)).all().all()


def test_operating_condition_normalizer_handles_clusters(
    cmapss_raw: Callable[..., Path],
) -> None:
    raw = cmapss_raw(subsets=("FD002",))
    df = load_subset("FD002", split="train", data_dir=raw)
    # Fixture generates 2 clusters; use n_clusters=2 to match.
    features = [f"sensor_{i}" for i in range(2, 6) if i != 5]
    norm = OperatingConditionNormalizer(n_clusters=2).fit(df, features)
    transformed = norm.transform(df)
    assert transformed[features].notna().all().all()
    # Within each cluster the scaled values should not blow up far past [0, 1].
    assert transformed[features].max().max() < 2.0
    assert transformed[features].min().min() > -1.0


# ---------------------------------------------------------------------------
# Windowing
# ---------------------------------------------------------------------------


def _toy_long_df(n_units: int, length: int, n_features: int) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    rows = []
    for u in range(1, n_units + 1):
        for c in range(1, length + 1):
            row = {"unit": u, "cycle": c, "RUL": float(length - c)}
            for f in range(n_features):
                row[f"sensor_{f + 1}"] = rng.normal()
            rows.append(row)
    return pd.DataFrame(rows)


def test_make_windows_shape_and_label() -> None:
    df = _toy_long_df(n_units=3, length=50, n_features=4)
    feature_cols = [f"sensor_{i}" for i in range(1, 5)]
    X, y, units = make_windows(df, feature_cols, window_size=DEFAULT_WINDOW_SIZE)
    # 3 units x (50 - 30 + 1) windows = 63
    assert X.shape == (63, DEFAULT_WINDOW_SIZE, 4)
    assert y.shape == (63,)
    assert units.shape == (63,)
    # Label of first window for unit 1 = RUL at cycle 30 = 50 - 30 = 20
    assert y[0] == pytest.approx(20.0)


def test_make_windows_last_only_returns_one_per_unit() -> None:
    df = _toy_long_df(n_units=5, length=80, n_features=3)
    feature_cols = [f"sensor_{i}" for i in range(1, 4)]
    X, _y, units = make_windows(df, feature_cols, window_size=DEFAULT_WINDOW_SIZE, last_only=True)
    assert X.shape == (5, DEFAULT_WINDOW_SIZE, 3)
    assert sorted(units.tolist()) == [1, 2, 3, 4, 5]


def test_make_windows_pads_short_trajectories() -> None:
    df = _toy_long_df(n_units=1, length=15, n_features=2)
    feature_cols = ["sensor_1", "sensor_2"]
    X, y, _ = make_windows(df, feature_cols, window_size=30)
    # Padded to a single window of full length.
    assert X.shape == (1, 30, 2)
    assert y.shape == (1,)


# ---------------------------------------------------------------------------
# End-to-end pipeline
# ---------------------------------------------------------------------------


def test_build_subset_writes_three_parquets(
    cmapss_raw: Callable[..., Path], tmp_path: Path
) -> None:
    raw = cmapss_raw(subsets=("FD001",))
    out = tmp_path / "processed"
    summary = build_subset("FD001", raw_dir=raw, out_dir=out)

    for split in ("train", "val", "test"):
        path = out / f"FD001_{split}.parquet"
        assert path.exists(), f"missing {path}"
        df = pd.read_parquet(path)
        assert not df.isna().any().any(), f"{split} contains NaN"
        assert "RUL" in df.columns
        assert (df["RUL"] >= 0).all()
        assert (df["RUL"] <= DEFAULT_RUL_CLIP).all()

    # Constant sensor was dropped during preprocessing.
    assert "sensor_5" in summary["dropped_columns"]
    assert "sensor_5" not in summary["feature_columns"]


def test_build_subset_enforces_engine_id_isolation(
    cmapss_raw: Callable[..., Path], tmp_path: Path
) -> None:
    raw = cmapss_raw(subsets=("FD001",))
    out = tmp_path / "processed"
    summary = build_subset("FD001", raw_dir=raw, out_dir=out)
    train_units = set(summary["train_units"])
    val_units = set(summary["val_units"])
    assert train_units.isdisjoint(val_units), "engine leakage between train and val"

    train_df = pd.read_parquet(out / "FD001_train.parquet")
    val_df = pd.read_parquet(out / "FD001_val.parquet")
    assert set(train_df["unit"].unique()) == train_units
    assert set(val_df["unit"].unique()) == val_units


def test_build_all_writes_manifest(cmapss_raw: Callable[..., Path], tmp_path: Path) -> None:
    raw = cmapss_raw(subsets=("FD001", "FD002"))
    out = tmp_path / "processed"
    manifest = build_all(subsets=("FD001", "FD002"), raw_dir=raw, out_dir=out)
    manifest_path = out / "manifest.json"
    assert manifest_path.exists()

    persisted = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert persisted["pipeline_version"]
    assert persisted["raw_data_sha256"]
    assert set(persisted["subsets"].keys()) == {"FD001", "FD002"}
    assert manifest["subsets"]["FD002"]["normalizer_class"] == "OperatingConditionNormalizer"
    assert manifest["subsets"]["FD001"]["normalizer_class"] == "GlobalNormalizer"


def test_load_processed_round_trip(cmapss_raw: Callable[..., Path], tmp_path: Path) -> None:
    raw = cmapss_raw(subsets=("FD001",))
    out = tmp_path / "processed"
    build_subset("FD001", raw_dir=raw, out_dir=out)
    df = load_processed("FD001", "train", processed_dir=out)
    assert {"unit", "cycle", "RUL"}.issubset(df.columns)


def test_load_processed_rejects_unknown_split(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown split"):
        load_processed("FD001", "holdout", processed_dir=tmp_path)
