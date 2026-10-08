# Architecture

Prototype for ceramic tile colour comparison and printer-adjustment recommendation.
The calibration layer uses **synthetic calibration data — for prototype demonstration only.**

```
                    MASTER TILE
                         │
                         ▼
                Colour Extraction
                         │
                         │
PRODUCTION TILE ────────┤
                         ▼
                Lab Difference
                ΔL Δa Δb ΔE
                         │
                         ▼
                Calibration Model
                         │
                         ▼
             Printer Recommendation
                         │
                         ▼
                    QC Review
```

## Components

| Component | Module | What it does |
|---|---|---|
| Master tile | `sample_images/`, upload | Reference image for the shade decided when the product was introduced. |
| Production tile | `sample_images/`, upload | Image of the fired sample from the current run. |
| Colour extraction | `src/colour_analysis.py` | Loads and validates both images, converts sRGB to CIELAB and averages Lab over a centred region of interest. |
| Lab difference | `src/colour_analysis.py` | Computes ΔL\*, Δa\*, Δb\* (production minus master) and ΔE76, with ΔE2000 as a reference, then describes the shift in plain words. |
| Calibration model | `src/calibration_model.py` | A Ridge regression that maps (ΔL, Δa, Δb) to four channel adjustments, trained on synthetic data with a fixed seed and saved with joblib. |
| Printer recommendation | `src/recommendation.py` | Runs the model, clamps results to prototype limits, checks the input against the training range and attaches a status. |
| QC review | `app.py` | Shows the result with the "Human/QC validation required before production use." notice and Accept / Reject buttons that change nothing outside the session. |

## Supporting files

- `src/utils.py`: paths, labels, settings and the deterministic synthetic demo tiles.
- `data/synthetic_calibration.csv`: the synthetic dataset; every row carries a `data_source` label.
- `models/calibration_model.pkl`: the trained model bundle (synthetic data).
- `notebooks/calibration_experiment.ipynb`: the experiment behind the model, with outputs.

## Design decisions

- **Sign convention:** every delta is production minus master. A positive ΔL means the production tile is lighter.
- **Range gate:** if any Lab delta falls outside the min/max seen in training, no adjustment is returned and the app shows `LOW CONFIDENCE / OUTSIDE CALIBRATION RANGE`.
- **Review gate:** a clamped adjustment, or a large colour difference, sets the status to "Review required".
- **No control path:** the app writes nothing to a printer, Photoshop file or production system.
- **Under-determined mapping:** four channels are predicted from three colour dimensions, so many channel mixes give the same colour. The model learns an average solution, which is why per-channel R² is moderate. A real pilot needs richer measurements or a restricted set of channels.
