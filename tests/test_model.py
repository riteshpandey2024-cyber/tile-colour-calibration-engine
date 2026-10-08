import numpy as np
import pytest

from src.calibration_model import (
    FORWARD_EFFECT,
    generate_synthetic_calibration,
    load_dataset,
    load_model,
    save_dataset,
    save_model,
    train_model,
)
from src.utils import FEATURES, MODEL_PATH, SYNTHETIC_LABEL, TARGETS


@pytest.fixture(scope="module")
def frame():
    return generate_synthetic_calibration(n_samples=400, seed=1)


@pytest.fixture(scope="module")
def bundle(frame):
    return train_model(frame, seed=1)


def test_synthetic_data_is_labelled_and_reproducible(frame):
    again = generate_synthetic_calibration(n_samples=400, seed=1)
    assert frame.equals(again)
    assert (frame["data_source"] == SYNTHETIC_LABEL).all()
    assert set(FEATURES + TARGETS) <= set(frame.columns)


def test_dataset_round_trip(frame, tmp_path):
    path = save_dataset(frame, tmp_path / "data.csv")
    assert len(load_dataset(path)) == len(frame)


def test_training_is_reproducible(frame, bundle):
    other = train_model(frame, seed=1)
    assert np.allclose(bundle.coefficients.to_numpy(), other.coefficients.to_numpy())


def test_training_reports_metrics(bundle):
    assert bundle.metrics["n_train"] + bundle.metrics["n_test"] == 400
    assert set(bundle.metrics["mae_per_channel"]) == set(TARGETS)
    assert 0.0 < bundle.metrics["r2_mean"] < 1.0
    assert bundle.coefficients.shape == (4, 4)


def test_model_reduces_synthetic_colour_error(bundle, frame):
    deviations = frame[list(FEATURES)].to_numpy()
    predicted = bundle.predict(deviations)
    residual = deviations + predicted @ FORWARD_EFFECT.T
    before = np.linalg.norm(deviations, axis=1).mean()
    after = np.linalg.norm(residual, axis=1).mean()
    assert after < 0.25 * before


def test_save_and_load_model(bundle, tmp_path):
    path = save_model(bundle, tmp_path / "model.pkl")
    loaded = load_model(path)
    sample = np.array([[1.0, 0.5, -1.0]])
    assert np.allclose(bundle.predict(sample), loaded.predict(sample))
    assert np.allclose(bundle.feature_min, loaded.feature_min)


def test_shipped_model_loads():
    loaded = load_model(MODEL_PATH)
    assert loaded.data_label == SYNTHETIC_LABEL
    assert loaded.predict(np.zeros(3)).shape == (1, 4)
