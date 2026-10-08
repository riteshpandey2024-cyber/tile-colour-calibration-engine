"""Synthetic calibration data, Ridge model training and persistence.

Everything trained here uses SYNTHETIC data. The forward effect matrix below is
an invented illustration and is NOT a measurement of any client printer.

Each synthetic row is one historical correction: the Lab deviation of a
production tile from its master (production minus master) and the printer
adjustment that was applied to remove it.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from src.utils import (
    DATA_PATH,
    FEATURES,
    MODEL_PATH,
    SETTINGS,
    SYNTHETIC_LABEL,
    TARGETS,
)

SOURCE_COLUMN = "data_source"

# Invented effect on (L*, a*, b*) of +1 % on each channel: brown, yellow, cyan, magenta.
FORWARD_EFFECT = np.array(
    [
        [-0.80, 0.15, -0.30, -0.20],
        [0.25, -0.10, -0.70, 0.80],
        [0.45, 0.95, -0.25, -0.30],
    ]
)


@dataclass(frozen=True)
class CalibrationBundle:
    """A trained model with the metadata needed to use it safely."""

    estimator: Ridge
    feature_names: tuple[str, ...]
    target_names: tuple[str, ...]
    feature_min: np.ndarray
    feature_max: np.ndarray
    metrics: dict[str, Any]
    coefficients: pd.DataFrame
    data_label: str
    seed: int

    def predict(self, deltas: np.ndarray) -> np.ndarray:
        """Predict raw channel adjustments (%) for rows of (dL, da, db)."""
        return self.estimator.predict(np.atleast_2d(deltas))


def generate_synthetic_calibration(
    n_samples: int = SETTINGS.n_synthetic_samples,
    seed: int = SETTINGS.random_seed,
    noise_std: float = SETTINGS.synthetic_noise_std,
    adjustment_range: float = SETTINGS.synthetic_adjustment_range,
) -> pd.DataFrame:
    """Generate a synthetic calibration dataset. Not client data."""
    rng = np.random.default_rng(seed)
    adjustments = rng.uniform(-adjustment_range, adjustment_range, size=(n_samples, len(TARGETS)))
    corrected_effect = adjustments @ FORWARD_EFFECT.T
    deviations = -corrected_effect + rng.normal(0.0, noise_std, size=(n_samples, len(FEATURES)))
    frame = pd.DataFrame(adjustments, columns=list(TARGETS)).join(
        pd.DataFrame(deviations, columns=list(FEATURES))
    )
    frame = frame.round(3)
    frame[SOURCE_COLUMN] = SYNTHETIC_LABEL
    return frame[[*FEATURES, *TARGETS, SOURCE_COLUMN]]


def save_dataset(frame: pd.DataFrame, path: Path = DATA_PATH) -> Path:
    """Write the dataset to CSV, creating parent folders."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def load_dataset(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load and validate a calibration CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Calibration data not found: {path}")
    frame = pd.read_csv(path)
    missing = [c for c in (*FEATURES, *TARGETS) if c not in frame.columns]
    if missing:
        raise ValueError(f"Calibration data is missing columns: {missing}")
    return frame


def train_model(
    frame: pd.DataFrame,
    seed: int = SETTINGS.random_seed,
    test_size: float = SETTINGS.test_size,
    alpha: float = SETTINGS.ridge_alpha,
) -> CalibrationBundle:
    """Train a Ridge model mapping colour difference to printer adjustments."""
    x, y = frame[list(FEATURES)], frame[list(TARGETS)]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=test_size, random_state=seed
    )
    estimator = Ridge(alpha=alpha).fit(x_train.to_numpy(), y_train.to_numpy())
    predicted = estimator.predict(x_test.to_numpy())

    mae = mean_absolute_error(y_test, predicted, multioutput="raw_values")
    r2 = r2_score(y_test, predicted, multioutput="raw_values")
    metrics = {
        "n_train": len(x_train),
        "n_test": len(x_test),
        "mae_per_channel": dict(zip(TARGETS, map(float, mae))),
        "r2_per_channel": dict(zip(TARGETS, map(float, r2))),
        "mae_mean": float(mae.mean()),
        "r2_mean": float(r2.mean()),
    }
    coefficients = pd.DataFrame(estimator.coef_, index=list(TARGETS), columns=list(FEATURES))
    coefficients["intercept"] = estimator.intercept_
    return CalibrationBundle(
        estimator=estimator,
        feature_names=FEATURES,
        target_names=TARGETS,
        feature_min=x_train.min().to_numpy(),
        feature_max=x_train.max().to_numpy(),
        metrics=metrics,
        coefficients=coefficients,
        data_label=SYNTHETIC_LABEL,
        seed=seed,
    )


def save_model(bundle: CalibrationBundle, path: Path = MODEL_PATH) -> Path:
    """Persist a bundle with joblib as a plain dictionary."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "estimator": bundle.estimator,
            "feature_names": bundle.feature_names,
            "target_names": bundle.target_names,
            "feature_min": bundle.feature_min,
            "feature_max": bundle.feature_max,
            "metrics": bundle.metrics,
            "coefficients": bundle.coefficients,
            "data_label": bundle.data_label,
            "seed": bundle.seed,
        },
        path,
    )
    return path


def load_model(path: Path = MODEL_PATH) -> CalibrationBundle:
    """Load a bundle saved by save_model. Only load model files you trust."""
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    return CalibrationBundle(**joblib.load(path))


def ensure_model(path: Path = MODEL_PATH, data_path: Path = DATA_PATH) -> CalibrationBundle:
    """Load the saved model, or deterministically rebuild it if it is missing."""
    if path.exists():
        return load_model(path)
    frame = load_dataset(data_path) if data_path.exists() else generate_synthetic_calibration()
    if not data_path.exists():
        save_dataset(frame, data_path)
    bundle = train_model(frame)
    save_model(bundle, path)
    return bundle


def main() -> None:
    """Regenerate the synthetic dataset, retrain and save the model."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--keep-data", action="store_true", help="reuse the existing CSV")
    args = parser.parse_args()

    if args.keep_data and DATA_PATH.exists():
        frame = load_dataset()
    else:
        frame = generate_synthetic_calibration()
        save_dataset(frame)
    bundle = train_model(frame)
    save_model(bundle)
    print(SYNTHETIC_LABEL)
    print(f"Train/test: {bundle.metrics['n_train']}/{bundle.metrics['n_test']}")
    print(f"Mean MAE: {bundle.metrics['mae_mean']:.3f} %-points")
    print(f"Mean R2:  {bundle.metrics['r2_mean']:.3f}")
    print(bundle.coefficients.round(3))


if __name__ == "__main__":
    main()
