import numpy as np
import pytest

from src.calibration_model import generate_synthetic_calibration, train_model
from src.recommendation import (
    LOW_CONFIDENCE_FLAG,
    STATUS_OUTSIDE,
    STATUS_REVIEW,
    STATUS_WITHIN,
    format_adjustments,
    is_within_range,
    recommend,
)
from src.utils import CHANNELS, QC_NOTICE


@pytest.fixture(scope="module")
def bundle():
    return train_model(generate_synthetic_calibration(n_samples=400, seed=1), seed=1)


def test_recommendation_values_come_from_model(bundle):
    rec = recommend(2.0, 1.0, -1.0, bundle)
    expected = bundle.predict(np.array([2.0, 1.0, -1.0]))[0]
    assert rec.status == STATUS_WITHIN and rec.is_confident
    assert list(rec.adjustments) == list(CHANNELS)
    assert np.allclose(list(rec.adjustments.values()), expected)
    assert rec.qc_notice == QC_NOTICE


def test_out_of_range_input_gives_no_recommendation(bundle):
    rec = recommend(40.0, 0.0, 0.0, bundle)
    assert rec.adjustments is None
    assert rec.status == STATUS_OUTSIDE and not rec.in_training_range
    assert LOW_CONFIDENCE_FLAG in rec.messages


def test_range_check_boundaries(bundle):
    assert is_within_range(np.zeros(3), bundle)
    assert not is_within_range(bundle.feature_max + 0.01, bundle)


def test_adjustments_are_clamped_and_flagged(bundle):
    rec = recommend(5.0, 3.0, -3.0, bundle, max_adjustment=0.5)
    assert all(abs(v) <= 0.5 for v in rec.adjustments.values())
    assert rec.clamped_channels
    assert rec.status == STATUS_REVIEW


def test_tolerance_flag(bundle):
    rec = recommend(0.2, 0.1, -0.1, bundle)
    assert rec.within_tolerance


def test_non_finite_input_rejected(bundle):
    with pytest.raises(ValueError):
        recommend(float("nan"), 0.0, 0.0, bundle)


def test_format_adjustments():
    assert format_adjustments({"brown": 3.24, "cyan": -0.2}) == ["Brown: +3.2%", "Cyan: -0.2%"]
