"""Shared test fixtures.

The synthetic C-MAPSS fixture generates whitespace-delimited files matching
the real dataset layout, so the same loader path is exercised end-to-end in
unit tests as in production.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest


def _write_cmapss_text(path: Path, rows: np.ndarray) -> None:
    """Mirror NASA C-MAPSS file format: space-delimited, no header."""
    np.savetxt(path, rows, fmt="%.6f")


def _generate_subset(
    rng: np.random.Generator,
    raw_dir: Path,
    subset: str,
    n_train_units: int,
    n_test_units: int,
    multi_condition: bool,
    constant_sensor_idx: int = 5,
) -> None:
    """Write train_*, test_*, RUL_* files for one synthetic subset.

    Parameters
    ----------
    constant_sensor_idx : int
        1-indexed sensor that will be held at a constant value across all rows,
        so the constant-column drop step has something to find.
    """
    n_settings = 3
    n_sensors = 21

    def _make_unit(unit_id: int, length: int) -> np.ndarray:
        cycles = np.arange(1, length + 1)
        # Operating settings: cluster into 2 conditions for multi-cond subsets, single for others.
        if multi_condition:
            cluster_id = rng.integers(0, 2)
            centroid = (
                np.array([0.0, 0.5, 60.0]) if cluster_id == 0 else np.array([0.7, 0.9, 100.0])
            )
            settings = centroid + rng.normal(0, 0.02, size=(length, n_settings))
        else:
            settings = np.tile([0.0, 0.0, 100.0], (length, 1)) + rng.normal(
                0, 0.001, size=(length, n_settings)
            )

        # Sensors degrade linearly + noise. One sensor stays constant.
        progress = cycles / length
        sensors = np.zeros((length, n_sensors))
        for s in range(n_sensors):
            if s + 1 == constant_sensor_idx:
                sensors[:, s] = 1.0
            else:
                slope = rng.uniform(-1.0, 1.0)
                sensors[:, s] = slope * progress + rng.normal(0, 0.1, size=length) + s * 0.05

        unit_col = np.full((length, 1), unit_id, dtype=float)
        cycle_col = cycles.reshape(-1, 1).astype(float)
        return np.hstack([unit_col, cycle_col, settings, sensors])

    train_rows: list[np.ndarray] = []
    for u in range(1, n_train_units + 1):
        length = int(rng.integers(80, 160))
        train_rows.append(_make_unit(u, length))
    _write_cmapss_text(raw_dir / f"train_{subset}.txt", np.vstack(train_rows))

    test_rows: list[np.ndarray] = []
    final_ruls: list[float] = []
    for u in range(1, n_test_units + 1):
        length = int(rng.integers(40, 100))
        test_rows.append(_make_unit(u, length))
        # RUL ground truth: a plausible positive value (engine stopped before failure).
        final_ruls.append(float(rng.integers(10, 80)))
    _write_cmapss_text(raw_dir / f"test_{subset}.txt", np.vstack(test_rows))
    np.savetxt(raw_dir / f"RUL_{subset}.txt", np.array(final_ruls), fmt="%d")


@pytest.fixture
def cmapss_raw(tmp_path: Path) -> Callable[..., Path]:
    """Factory that materialises a synthetic C-MAPSS layout in ``tmp_path/raw``.

    Usage::

        raw_dir = cmapss_raw(subsets=("FD001", "FD002"))
        df = load_subset("FD001", data_dir=raw_dir)
    """

    def _build(
        subsets: tuple[str, ...] = ("FD001",),
        n_train_units: int = 8,
        n_test_units: int = 4,
        seed: int = 1234,
    ) -> Path:
        raw = tmp_path / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(seed)
        for subset in subsets:
            _generate_subset(
                rng,
                raw_dir=raw,
                subset=subset,
                n_train_units=n_train_units,
                n_test_units=n_test_units,
                multi_condition=subset in {"FD002", "FD004"},
            )
        return raw

    return _build
