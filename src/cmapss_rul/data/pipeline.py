"""End-to-end preprocessing pipeline.

Reads raw C-MAPSS, computes RUL labels, fits normalization on train only,
applies it to val/test, and writes ``data/processed/{subset}_{split}.parquet``
along with a JSON manifest recording git SHA, raw-data hash, dropped columns,
and the chosen train/val unit IDs.

Invoke as a module:

.. code-block:: bash

    python -m cmapss_rul.data.pipeline                 # all 4 subsets
    python -m cmapss_rul.data.pipeline FD001 FD004     # specific subsets
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from cmapss_rul.config import (
    CMAPSS_SUBSETS,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    SEED,
)
from cmapss_rul.data.loader import (
    SENSOR_COLUMNS,
    SETTING_COLUMNS,
    dataset_hash,
    load_rul_file,
    load_subset,
)
from cmapss_rul.data.preprocessing import (
    PIPELINE_VERSION,
    PreprocessingArtifacts,
    compute_rul,
    compute_test_rul,
    feature_columns_for,
    find_constant_columns,
    make_normalizer,
)
from cmapss_rul.data.splits import apply_split, split_units

log = logging.getLogger(__name__)

MANIFEST_FILENAME = "manifest.json"


def _git_sha() -> str:
    """Best-effort current commit SHA. Returns ``"unknown"`` outside a git tree."""
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        return sha or "unknown"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def build_subset(
    subset: str,
    raw_dir: Path | None = None,
    out_dir: Path | None = None,
    val_fraction: float = 0.2,
    seed: int = SEED,
) -> dict[str, object]:
    """Run the full preprocessing pipeline for one C-MAPSS subset.

    Writes three parquets (``{subset}_train.parquet``, ``{subset}_val.parquet``,
    ``{subset}_test.parquet``) and returns a manifest dict describing what
    happened. The caller is responsible for persisting the manifest.
    """
    raw = raw_dir or RAW_DATA_DIR
    out = out_dir or PROCESSED_DATA_DIR
    out.mkdir(parents=True, exist_ok=True)

    log.info("Loading %s from %s", subset, raw)
    raw_train = load_subset(subset, split="train", data_dir=raw)
    raw_test = load_subset(subset, split="test", data_dir=raw)
    rul_truth = load_rul_file(subset, data_dir=raw)

    # Split train units → train/val before any fitting, so val is fully held out.
    train_units, val_units = split_units(raw_train, val_fraction=val_fraction, seed=seed)
    train_only, val_only = apply_split(raw_train, train_units, val_units)

    # Detect constant sensors *on the training partition only*.
    dropped = find_constant_columns(train_only, list(SENSOR_COLUMNS))
    features = feature_columns_for(dropped)
    log.info(
        "Subset %s: dropped %d constant sensor(s) %s; %d features remain",
        subset,
        len(dropped),
        dropped,
        len(features),
    )

    # Fit normalizer on train, transform all three splits.
    normalizer = make_normalizer(subset).fit(train_only, features)
    train_norm = normalizer.transform(train_only)
    val_norm = normalizer.transform(val_only)
    test_norm = normalizer.transform(raw_test)

    # RUL labels — train/val use piecewise-linear from max cycle; test uses ground truth.
    train_norm["RUL"] = compute_rul(train_only)
    val_norm["RUL"] = compute_rul(val_only)
    test_norm["RUL"] = compute_test_rul(raw_test, rul_truth)

    # Trim each partition to its canonical column set.
    output_columns = ["unit", "cycle", *SETTING_COLUMNS, *features, "RUL"]
    train_norm = train_norm[output_columns].sort_values(["unit", "cycle"]).reset_index(drop=True)
    val_norm = val_norm[output_columns].sort_values(["unit", "cycle"]).reset_index(drop=True)
    test_norm = test_norm[output_columns].sort_values(["unit", "cycle"]).reset_index(drop=True)

    train_path = out / f"{subset}_train.parquet"
    val_path = out / f"{subset}_val.parquet"
    test_path = out / f"{subset}_test.parquet"
    train_norm.to_parquet(train_path, index=False)
    val_norm.to_parquet(val_path, index=False)
    test_norm.to_parquet(test_path, index=False)

    artifacts = PreprocessingArtifacts(
        subset=subset,
        normalizer=normalizer,
        dropped_columns=dropped,
        feature_columns=features,
    )

    return {
        "subset": subset,
        "pipeline_version": PIPELINE_VERSION,
        "seed": seed,
        "val_fraction": val_fraction,
        "train_units": train_units,
        "val_units": val_units,
        "n_train_rows": len(train_norm),
        "n_val_rows": len(val_norm),
        "n_test_rows": len(test_norm),
        "dropped_columns": dropped,
        "feature_columns": features,
        "normalizer_class": type(artifacts.normalizer).__name__,
        "outputs": {
            "train": str(train_path.relative_to(out.parent.parent)),
            "val": str(val_path.relative_to(out.parent.parent)),
            "test": str(test_path.relative_to(out.parent.parent)),
        },
    }


def build_all(
    subsets: tuple[str, ...] = CMAPSS_SUBSETS,
    raw_dir: Path | None = None,
    out_dir: Path | None = None,
    val_fraction: float = 0.2,
    seed: int = SEED,
) -> dict[str, object]:
    """Run :func:`build_subset` for each requested subset and write the manifest."""
    out = out_dir or PROCESSED_DATA_DIR
    out.mkdir(parents=True, exist_ok=True)

    per_subset: dict[str, dict[str, object]] = {}
    for subset in subsets:
        per_subset[subset] = build_subset(
            subset, raw_dir=raw_dir, out_dir=out, val_fraction=val_fraction, seed=seed
        )

    manifest = {
        "pipeline_version": PIPELINE_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "git_sha": _git_sha(),
        "raw_data_sha256": dataset_hash(raw_dir),
        "seed": seed,
        "val_fraction": val_fraction,
        "subsets": per_subset,
    }
    manifest_path = out / MANIFEST_FILENAME
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log.info("Wrote manifest %s", manifest_path)
    return manifest


def _cli(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    requested = tuple(argv) if argv else CMAPSS_SUBSETS
    unknown = [s for s in requested if s not in CMAPSS_SUBSETS]
    if unknown:
        log.error("Unknown subset(s): %s. Expected any of %s", unknown, CMAPSS_SUBSETS)
        return 2
    build_all(subsets=requested)
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))


def load_processed(subset: str, split: str, processed_dir: Path | None = None) -> pd.DataFrame:
    """Convenience reader for the parquets emitted by :func:`build_subset`."""
    if split not in ("train", "val", "test"):
        raise ValueError(f"Unknown split {split!r}; expected train/val/test")
    base = processed_dir or PROCESSED_DATA_DIR
    path = base / f"{subset}_{split}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Processed parquet not found at {path}. "
            "Run `python -m cmapss_rul.data.pipeline` to build it."
        )
    return pd.read_parquet(path)
