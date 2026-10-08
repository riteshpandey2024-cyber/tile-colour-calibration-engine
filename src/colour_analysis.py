"""Image loading, CIELAB conversion, colour difference and interpretation.

Image-derived Lab values are a prototype approximation: they assume sRGB / D65
and depend on camera, lighting and exposure. They must be validated against the
client's spectrophotometer measurements before any production use.

Sign convention: every delta is production minus master.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

import numpy as np
from PIL import Image, UnidentifiedImageError
from skimage import color

from src.utils import SETTINGS, RoiBox, centered_roi, roi_to_pixels

ImageSource = str | Path | bytes | BinaryIO

NEGLIGIBLE = 0.5
SLIGHT = 1.5
STRONG = 4.0


class ImageValidationError(ValueError):
    """Raised when an image cannot be loaded or fails validation."""


def load_image(source: ImageSource) -> np.ndarray:
    """Load an image from a path, bytes or file-like object as an RGB uint8 array.

    Transparent pixels are composited onto white.
    """
    try:
        if isinstance(source, bytes):
            source = io.BytesIO(source)
        elif hasattr(source, "getvalue"):
            source = io.BytesIO(source.getvalue())
        with Image.open(source) as img:
            rgba = img.convert("RGBA")
    except (FileNotFoundError, UnidentifiedImageError, OSError) as exc:
        raise ImageValidationError(f"Could not read image: {exc}") from exc
    background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    rgb = Image.alpha_composite(background, rgba).convert("RGB")
    return validate_image(np.asarray(rgb))


def validate_image(image: np.ndarray, min_side: int | None = None) -> np.ndarray:
    """Check that an array is a usable RGB uint8 image and return it unchanged."""
    min_side = SETTINGS.min_image_side if min_side is None else min_side
    if not isinstance(image, np.ndarray):
        raise ImageValidationError("Image must be a NumPy array.")
    if image.ndim != 3 or image.shape[2] != 3:
        raise ImageValidationError("Image must have shape (height, width, 3).")
    if image.dtype != np.uint8:
        raise ImageValidationError("Image must be 8-bit RGB (uint8).")
    if min(image.shape[:2]) < min_side:
        raise ImageValidationError(f"Image is too small: each side must be at least {min_side} px.")
    return image


def rgb_to_lab(image: np.ndarray) -> np.ndarray:
    """Convert an 8-bit sRGB array (..., 3) to CIELAB (D65)."""
    return color.rgb2lab(validate_image(image, min_side=1))


def mean_lab(image: np.ndarray, roi: RoiBox | None = None) -> tuple[float, float, float]:
    """Return the mean (L*, a*, b*) over a region of interest (default: centred ROI)."""
    validate_image(image)
    roi = roi or centered_roi(SETTINGS.roi_fraction)
    y0, y1, x0, x1 = roi_to_pixels(image.shape, roi)
    lab = rgb_to_lab(image[y0:y1, x0:x1]).reshape(-1, 3).mean(axis=0)
    return float(lab[0]), float(lab[1]), float(lab[2])


def delta_e_76(lab_a: tuple[float, float, float], lab_b: tuple[float, float, float]) -> float:
    """Euclidean CIELAB distance (CIE76)."""
    return float(np.linalg.norm(np.subtract(lab_a, lab_b)))


def compare_tiles(
    master: np.ndarray, production: np.ndarray, roi: RoiBox | None = None
) -> dict[str, float]:
    """Compare mean ROI Lab values of a master and production tile.

    Returns the master and production Lab values, delta_L / delta_a / delta_b
    (production minus master) and delta_E (CIE76). delta_E2000 is included as a
    secondary, perceptually weighted reference.
    """
    master_lab = mean_lab(master, roi)
    production_lab = mean_lab(production, roi)
    d_l, d_a, d_b = (p - m for p, m in zip(production_lab, master_lab))
    de2000 = color.deltaE_ciede2000(np.array(master_lab), np.array(production_lab))
    return {
        "master_L": master_lab[0],
        "master_a": master_lab[1],
        "master_b": master_lab[2],
        "production_L": production_lab[0],
        "production_a": production_lab[1],
        "production_b": production_lab[2],
        "delta_L": d_l,
        "delta_a": d_a,
        "delta_b": d_b,
        "delta_E": delta_e_76(production_lab, master_lab),
        "delta_E2000": float(de2000),
    }


def _degree(value: float) -> str:
    magnitude = abs(value)
    if magnitude < SLIGHT:
        return "slightly "
    if magnitude < STRONG:
        return ""
    return "much "


def interpret_difference(delta_L: float, delta_a: float, delta_b: float) -> str:
    """Describe a Lab difference in plain language without implying a physical cause."""
    parts: list[str] = []
    if abs(delta_L) >= NEGLIGIBLE:
        parts.append(f"{_degree(delta_L)}{'lighter' if delta_L > 0 else 'darker'}")
    if abs(delta_a) >= NEGLIGIBLE:
        parts.append(f"{_degree(delta_a)}{'redder' if delta_a > 0 else 'greener'}")
    if abs(delta_b) >= NEGLIGIBLE:
        parts.append(f"{_degree(delta_b)}{'more yellow' if delta_b > 0 else 'less yellow'}")
    if not parts:
        return "No perceptible difference in lightness or hue between production and master."
    body = parts[0] if len(parts) == 1 else f"{', '.join(parts[:-1])} and {parts[-1]}"
    return f"Production tile is {body} than the master."
