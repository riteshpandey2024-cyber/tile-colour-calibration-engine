import io

import numpy as np
import pytest
from PIL import Image

from src.colour_analysis import (
    ImageValidationError,
    compare_tiles,
    delta_e_76,
    interpret_difference,
    load_image,
    mean_lab,
    rgb_to_lab,
    validate_image,
)


def flat(rgb: tuple[int, int, int], size: int = 64) -> np.ndarray:
    return np.full((size, size, 3), rgb, dtype=np.uint8)


def test_load_image_from_path_and_bytes(tmp_path):
    path = tmp_path / "tile.png"
    Image.fromarray(flat((120, 80, 40))).save(path)
    from_path = load_image(path)
    buffer = io.BytesIO()
    Image.fromarray(flat((120, 80, 40))).save(buffer, format="PNG")
    from_bytes = load_image(buffer.getvalue())
    assert from_path.shape == (64, 64, 3) and from_path.dtype == np.uint8
    assert np.array_equal(from_path, from_bytes)


def test_load_image_rejects_missing_and_corrupt(tmp_path):
    with pytest.raises(ImageValidationError):
        load_image(tmp_path / "missing.png")
    with pytest.raises(ImageValidationError):
        load_image(b"not an image")


def test_validate_image_rejects_bad_arrays():
    with pytest.raises(ImageValidationError):
        validate_image(np.zeros((64, 64), dtype=np.uint8))
    with pytest.raises(ImageValidationError):
        validate_image(np.zeros((64, 64, 3), dtype=np.float32))
    with pytest.raises(ImageValidationError):
        validate_image(np.zeros((8, 8, 3), dtype=np.uint8))


def test_rgb_to_lab_known_values():
    white = rgb_to_lab(flat((255, 255, 255)))[0, 0]
    black = rgb_to_lab(flat((0, 0, 0)))[0, 0]
    assert white[0] == pytest.approx(100.0, abs=0.1)
    assert abs(white[1]) < 0.1 and abs(white[2]) < 0.1
    assert black[0] == pytest.approx(0.0, abs=0.1)


def test_mean_lab_uses_roi():
    image = flat((100, 100, 100))
    image[:, :32] = (250, 250, 250)
    left = mean_lab(image, roi=(0.0, 0.0, 0.5, 1.0))
    right = mean_lab(image, roi=(0.5, 0.0, 1.0, 1.0))
    assert left[0] > right[0] + 40


def test_delta_L_sign():
    result = compare_tiles(flat((120, 120, 120)), flat((140, 140, 140)))
    assert result["delta_L"] > 0
    assert result["delta_L"] == pytest.approx(result["production_L"] - result["master_L"])


def test_delta_a_sign():
    result = compare_tiles(flat((120, 120, 120)), flat((140, 120, 120)))
    assert result["delta_a"] > 0


def test_delta_b_sign():
    result = compare_tiles(flat((120, 120, 120)), flat((120, 120, 150)))
    assert result["delta_b"] < 0


def test_delta_e_matches_components():
    result = compare_tiles(flat((100, 110, 120)), flat((130, 100, 115)))
    expected = np.sqrt(result["delta_L"] ** 2 + result["delta_a"] ** 2 + result["delta_b"] ** 2)
    assert result["delta_E"] == pytest.approx(expected)
    assert delta_e_76((50, 0, 0), (53, 4, 0)) == pytest.approx(5.0)


def test_identical_tiles_have_zero_difference():
    result = compare_tiles(flat((90, 60, 30)), flat((90, 60, 30)))
    assert result["delta_E"] == pytest.approx(0.0, abs=1e-9)


def test_interpretation_directions():
    text = interpret_difference(3.0, 1.0, -2.0)
    assert text == "Production tile is lighter, slightly redder and less yellow than the master."
    darker = interpret_difference(-3.0, -3.0, 3.0)
    assert "darker" in darker and "greener" in darker and "more yellow" in darker


def test_interpretation_negligible_difference():
    assert "No perceptible difference" in interpret_difference(0.1, -0.2, 0.3)
