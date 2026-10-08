"""Shared configuration, paths, labels and synthetic demo-tile generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
from PIL import Image
from skimage import color

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "synthetic_calibration.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "calibration_model.pkl"
SAMPLE_DIR = PROJECT_ROOT / "sample_images"
MASTER_SAMPLE_PATH = SAMPLE_DIR / "master.png"
PRODUCTION_SAMPLE_PATH = SAMPLE_DIR / "production.png"

SYNTHETIC_LABEL = "Synthetic calibration data — for prototype demonstration only."
MODEL_LABEL = "Model trained on synthetic calibration data."
QC_NOTICE = "Human/QC validation required before production use."
DEMO_LABEL = "Demo Mode — using synthetic sample tiles."

CHANNELS: tuple[str, ...] = ("brown", "yellow", "cyan", "magenta")
FEATURES: tuple[str, ...] = ("delta_L", "delta_a", "delta_b")
TARGETS: tuple[str, ...] = tuple(f"{c}_adjustment" for c in CHANNELS)

RoiBox = tuple[float, float, float, float]
DemoScenario = Literal["typical", "large"]


@dataclass(frozen=True)
class Settings:
    """Prototype configuration. Values are demonstration defaults, not client specifications."""

    random_seed: int = 42
    roi_fraction: float = 0.6
    min_image_side: int = 32
    n_synthetic_samples: int = 600
    synthetic_noise_std: float = 0.15
    synthetic_adjustment_range: float = 6.0
    test_size: float = 0.2
    ridge_alpha: float = 1.0
    max_adjustment: float = 8.0
    tolerance_delta_e: float = 1.0
    review_delta_e: float = 6.0


SETTINGS = Settings()


def centered_roi(fraction: float) -> RoiBox:
    """Return a centred region of interest as fractional (x0, y0, x1, y1)."""
    if not 0.0 < fraction <= 1.0:
        raise ValueError("ROI fraction must be in the range (0, 1].")
    margin = (1.0 - fraction) / 2.0
    return (margin, margin, 1.0 - margin, 1.0 - margin)


def roi_to_pixels(shape: tuple[int, ...], roi: RoiBox) -> tuple[int, int, int, int]:
    """Convert a fractional ROI to pixel slices (y0, y1, x0, x1) for an image shape."""
    x0, y0, x1, y1 = roi
    if not (0.0 <= x0 < x1 <= 1.0 and 0.0 <= y0 < y1 <= 1.0):
        raise ValueError("ROI must satisfy 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1.")
    height, width = shape[:2]
    px0, px1 = int(round(x0 * width)), int(round(x1 * width))
    py0, py1 = int(round(y0 * height)), int(round(y1 * height))
    return py0, max(py1, py0 + 1), px0, max(px1, px0 + 1)


def draw_roi_outline(image: np.ndarray, roi: RoiBox) -> np.ndarray:
    """Return a copy of an RGB image with the measured ROI outlined."""
    y0, y1, x0, x1 = roi_to_pixels(image.shape, roi)
    outlined = image.copy()
    cv2.rectangle(outlined, (x0, y0), (x1 - 1, y1 - 1), (255, 255, 255), 2)
    cv2.rectangle(outlined, (x0 + 2, y0 + 2), (x1 - 3, y1 - 3), (0, 0, 0), 1)
    return outlined


_BASE_LAB = (58.0, 12.0, 24.0)
_DEMO_SHIFTS: dict[str, tuple[float, float, float]] = {
    "typical": (2.5, 1.2, -1.5),
    "large": (14.0, 9.0, -12.0),
}


def _master_lab(size: int, seed: int) -> np.ndarray:
    """Build a deterministic marble-like master pattern in CIELAB."""
    rng = np.random.default_rng(seed)
    smooth = cv2.GaussianBlur(
        rng.standard_normal((size, size)).astype(np.float32), (0, 0), sigmaX=size / 20
    )
    smooth /= np.abs(smooth).max()
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size
    veins = (1.0 - np.abs(np.sin(np.pi * (3.0 * xx + 2.0 * yy + 1.5 * smooth)))) ** 12
    lab = np.empty((size, size, 3), dtype=np.float32)
    lab[..., 0] = _BASE_LAB[0] + 5.0 * smooth - 14.0 * veins
    lab[..., 1] = _BASE_LAB[1] + 1.5 * smooth - 2.0 * veins
    lab[..., 2] = _BASE_LAB[2] + 2.5 * smooth - 4.0 * veins
    return lab


def _lab_to_rgb8(lab: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(color.lab2rgb(lab) * 255.0), 0, 255).astype(np.uint8)


def make_demo_tiles(
    scenario: DemoScenario = "typical", size: int = 512, seed: int = 7
) -> tuple[np.ndarray, np.ndarray]:
    """Generate a deterministic synthetic (master, production) tile pair.

    The production tile is the master with a fixed CIELAB shift applied.
    These are synthetic images, not photographs of client tiles.
    """
    if scenario not in _DEMO_SHIFTS:
        raise ValueError(f"Unknown demo scenario: {scenario!r}")
    master_lab = _master_lab(size, seed)
    shift = np.asarray(_DEMO_SHIFTS[scenario], dtype=np.float32)
    return _lab_to_rgb8(master_lab), _lab_to_rgb8(master_lab + shift)


def write_demo_tiles(directory: Path = SAMPLE_DIR) -> tuple[Path, Path]:
    """Write the typical-scenario demo tiles to disk as PNG files."""
    directory.mkdir(parents=True, exist_ok=True)
    master, production = make_demo_tiles("typical")
    master_path, production_path = directory / "master.png", directory / "production.png"
    Image.fromarray(master).save(master_path)
    Image.fromarray(production).save(production_path)
    return master_path, production_path


if __name__ == "__main__":
    for written in write_demo_tiles():
        print(f"Wrote {written.relative_to(PROJECT_ROOT)}")
