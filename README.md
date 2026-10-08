# Tile Colour Calibration Engine

Prototype for ceramic tile colour comparison and printer-adjustment recommendation.

> **Prototype only.** No real production dataset was provided. The calibration model is trained on **synthetic calibration data — for prototype demonstration only.** It has not been validated against any real printer and does not control production.

Labels used in this README:

- **SUPPORTED BY CLIENT DISCOVERY**: stated by the client on the discovery call.
- **PROTOTYPE ASSUMPTION**: a choice made here so the prototype can run.
- **FUTURE WORK**: needed for a real pilot, not built.

## 1. Project Overview

A small Python app that compares a master tile with a production tile, quantifies the difference in CIELAB (ΔL\*, Δa\*, Δb\*, ΔE), and shows a model-based recommendation for adjusting the digital printer input. A QC person reviews the result before anything is used.

## 2. Business Problem

**SUPPORTED BY CLIENT DISCOVERY**

- Tiles are digitally printed with patterns and colours, then fired in a kiln.
- Shade is checked in a lab against the master tile.
- When the shade is off, operators change the printer reference image by hand, for example by raising the brown percentage.
- They print, fire and test 6 to 7 variants, and one correction cycle takes about 6 to 7 hours.
- The client wants to compare master and production tiles, quantify the difference (ΔL\*, Δa\*, Δb\* and Δgloss) and be told what to change in the printer input.
- The problem occurs at batch change. Continuous line monitoring is not required.
- Root-cause analysis of raw material or kiln conditions is outside the immediate requirement.

## 3. Current Workflow

**SUPPORTED BY CLIENT DISCOVERY**

1. Print one sample from the reference image, fire it and check it manually in the lab (for example with a spectrophotometer).
2. If the shade is acceptable, run the batch.
3. If not, edit the reference image by eye (Adobe Photoshop), make 6 to 7 variants, print, fire and test them.
4. Repeat until the shade matches.

## 4. Proposed Workflow

**PROTOTYPE ASSUMPTION**

1. Provide the master tile and the first production tile.
2. The tool measures Lab for both and reports ΔL\*, Δa\*, Δb\* and ΔE.
3. A calibration model suggests per-channel adjustments, or says the input is outside its range.
4. QC accepts or rejects. The operator applies any accepted change by hand, as today.

## 5. Architecture

See [docs/architecture.md](docs/architecture.md).

```
MASTER TILE ─┐
             ├─ Colour Extraction ─ Lab Difference ─ Calibration Model ─ Printer Recommendation ─ QC Review
PRODUCTION ──┘
```

## 6. Technical Approach

**PROTOTYPE ASSUMPTION**

- Python 3.12+, Streamlit, Pillow, OpenCV, NumPy, pandas, scikit-learn, scikit-image, joblib, pytest.
- Colour logic, model and recommendation logic are separate modules in `src/`, so each can be tested alone.
- No databases, cloud services, containers or agent frameworks.

## 7. Colour Science

**PROTOTYPE ASSUMPTION**

- Images are read as 8-bit sRGB and converted to CIELAB (D65) with scikit-image.
- Mean Lab is taken over a centred region of interest (60% of the tile by default, adjustable in the sidebar).
- All deltas are production minus master. ΔL > 0 means lighter, Δa > 0 redder, Δb > 0 more yellow.
- ΔE is CIE76 (Euclidean distance in Lab). ΔE2000 is shown as a reference.
- Image-derived Lab depends on camera, lighting and exposure, and lossy JPEG compression shifts values slightly. **Validate against the client's spectrophotometer before any production use.**

## 8. ML Calibration Approach

**PROTOTYPE ASSUMPTION**

- Input: ΔL\*, Δa\*, Δb\*. Target: brown, yellow, cyan and magenta adjustments in percentage points. (The client mentioned 6 primary colours; four are used here for demonstration.)
- Model: Ridge regression, 80/20 split, fixed seed (42), saved with joblib.
- Synthetic data: 600 rows generated from an invented linear effect matrix plus noise. The matrix is **not** a measurement of any client printer.
- Safeguards: adjustments are clamped to ±8%, inputs outside the training min/max get no recommendation, and large or clamped results are marked "Review required".
- Result on synthetic test data: mean MAE about 1.3 percentage points, mean R² about 0.75. Four channels are predicted from three colour dimensions, so the problem is under-determined and per-channel R² ranges from about 0.64 to 0.92. These figures describe the synthetic data only.

## 9. Demo Instructions

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

With no uploads, the app shows "Demo Mode — using synthetic sample tiles." and uses the tiles in `sample_images/`. The sidebar offers a second demo scenario with a large colour drift that falls outside the calibration range, to show the safeguard. You can also upload your own PNG or JPEG tiles.

To rebuild the sample images, dataset and model:

```bash
python -m src.utils
python -m src.calibration_model
```

## 10. Project Structure

```
tile-colour-calibration-engine/
├── README.md
├── requirements.txt
├── pytest.ini
├── app.py
├── .gitignore
├── data/synthetic_calibration.csv
├── models/calibration_model.pkl
├── src/
│   ├── colour_analysis.py
│   ├── calibration_model.py
│   ├── recommendation.py
│   └── utils.py
├── tests/
│   ├── test_colour_analysis.py
│   ├── test_model.py
│   └── test_recommendation.py
├── notebooks/calibration_experiment.ipynb
├── sample_images/{master,production}.png
└── docs/architecture.md
```

## 11. Example Output

Demo mode, typical scenario (synthetic sample tiles, synthetic model):

```
Metric   Master   Production   Difference
L*       57.60    60.09        +2.50
a*       11.97    13.17        +1.20
b*       23.93    22.43        -1.50
ΔE (CIE76): 3.15    ΔE2000: 2.72

Production tile is lighter, slightly redder and less yellow than the master.

Brown: +2.7%   Yellow: +0.6%   Cyan: +1.9%   Magenta: -0.6%
Status: Within calibration range
Human/QC validation required before production use.
```

Large-drift scenario: `LOW CONFIDENCE / OUTSIDE CALIBRATION RANGE`, no recommendation.

## 12. Testing

```bash
python -m pytest
```

26 tests cover image loading and validation, RGB to Lab conversion, ΔL, Δa, Δb and ΔE, interpretation, model training and reproducibility, model saving and loading, recommendation generation, clamping and out-of-range detection.

## 13. Limitations

- No real production dataset was provided.
- Synthetic calibration data is used for demonstration.
- The printer-channel mapping has not been validated against the client's actual printer.
- Image-derived colour measurements should be validated against the client's spectrophotometer.
- Actual production calibration requires paired printer-input and post-fire Lab measurements.
- Gloss measurement is not implemented, because no valid gloss data is available.
- The prototype does not modify Adobe Photoshop files automatically.
- The prototype does not control the production line.
- The prototype does not perform kiln or raw-material root-cause analysis.
- Human/QC approval remains required.
- Model files are pickles: only load files you trust.

## 14. Productionisation Roadmap

**FUTURE WORK**

1. Collect paired data: printer-input channel values and post-fire spectrophotometer Lab, per SKU, across several tile regions.
2. Check measurement repeatability and add per-instrument offsets.
3. Refit the model on real data per SKU, with an updating step after each verified print.
4. Agree tolerance (ΔE2000) and channel limits with QC.
5. Add gloss as a flag once gloss data is available.
6. Run a live pilot at one plant with the manual loop as control, then decide on rollout.
7. Add authentication, audit logging and export of an approved change list.
# tile-colour-calibration-engine
# tile-colour-calibration-engine
