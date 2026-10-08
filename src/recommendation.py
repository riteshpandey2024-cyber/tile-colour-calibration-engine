"""Printer-adjustment recommendations with range checks and safety flags.

Recommendations come from the trained model only. They are for human/QC review
and never control a production system.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from src.calibration_model import CalibrationBundle
from src.utils import CHANNELS, QC_NOTICE, SETTINGS, Settings

STATUS_WITHIN = "Within calibration range"
STATUS_OUTSIDE = "Outside calibration range"
STATUS_REVIEW = "Review required"
LOW_CONFIDENCE_FLAG = "LOW CONFIDENCE / OUTSIDE CALIBRATION RANGE"


@dataclass(frozen=True)
class Recommendation:
    """Result of a recommendation request."""

    adjustments: dict[str, float] | None
    status: str
    in_training_range: bool
    delta_E: float
    within_tolerance: bool
    clamped_channels: tuple[str, ...] = ()
    messages: list[str] = field(default_factory=list)
    qc_notice: str = QC_NOTICE

    @property
    def is_confident(self) -> bool:
        """True only when a recommendation exists and is inside the calibration range."""
        return self.adjustments is not None and self.status == STATUS_WITHIN


def is_within_range(deltas: np.ndarray, bundle: CalibrationBundle) -> bool:
    """Check that every Lab delta lies inside the training data's min/max range."""
    return bool(np.all(deltas >= bundle.feature_min) and np.all(deltas <= bundle.feature_max))


def recommend(
    delta_L: float,
    delta_a: float,
    delta_b: float,
    bundle: CalibrationBundle,
    settings: Settings = SETTINGS,
    max_adjustment: float | None = None,
) -> Recommendation:
    """Recommend per-channel printer adjustments (percentage points) for a Lab difference."""
    values = (delta_L, delta_a, delta_b)
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Lab differences must be finite numbers.")
    limit = settings.max_adjustment if max_adjustment is None else max_adjustment
    deltas = np.asarray(values, dtype=float)
    delta_e = float(np.linalg.norm(deltas))
    within_tolerance = delta_e <= settings.tolerance_delta_e
    in_range = is_within_range(deltas, bundle)

    if not in_range:
        return Recommendation(
            adjustments=None,
            status=STATUS_OUTSIDE,
            in_training_range=False,
            delta_E=delta_e,
            within_tolerance=within_tolerance,
            messages=[
                LOW_CONFIDENCE_FLAG,
                "The colour difference is outside the range covered by the calibration data, "
                "so no adjustment is recommended.",
            ],
        )

    raw = bundle.predict(deltas)[0]
    clipped = np.clip(raw, -limit, limit)
    clamped = tuple(c for c, r, k in zip(CHANNELS, raw, clipped) if r != k)
    adjustments = {c: float(v) for c, v in zip(CHANNELS, clipped)}

    messages: list[str] = []
    if within_tolerance:
        messages.append("Colour difference is within the prototype tolerance; adjustment may be unnecessary.")
    if clamped:
        messages.append(f"Clamped to ±{limit:g}% for: {', '.join(clamped)}.")
    needs_review = bool(clamped) or delta_e >= settings.review_delta_e
    if delta_e >= settings.review_delta_e:
        messages.append("Large colour difference; review the recommendation carefully.")

    return Recommendation(
        adjustments=adjustments,
        status=STATUS_REVIEW if needs_review else STATUS_WITHIN,
        in_training_range=True,
        delta_E=delta_e,
        within_tolerance=within_tolerance,
        clamped_channels=clamped,
        messages=messages,
    )


def format_adjustments(adjustments: dict[str, float]) -> list[str]:
    """Format adjustments as lines such as 'Brown: +3.2%'."""
    return [f"{channel.capitalize()}: {value:+.1f}%" for channel, value in adjustments.items()]
