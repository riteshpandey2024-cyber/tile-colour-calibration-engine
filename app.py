"""Streamlit prototype: ceramic tile colour comparison and printer-adjustment recommendation."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from src.calibration_model import CalibrationBundle, ensure_model
from src.colour_analysis import (
    ImageValidationError,
    compare_tiles,
    interpret_difference,
    load_image,
)
from src.recommendation import (
    LOW_CONFIDENCE_FLAG,
    STATUS_OUTSIDE,
    STATUS_REVIEW,
    Recommendation,
    recommend,
)
from src.utils import (
    DEMO_LABEL,
    MASTER_SAMPLE_PATH,
    MODEL_LABEL,
    PRODUCTION_SAMPLE_PATH,
    QC_NOTICE,
    SETTINGS,
    SYNTHETIC_LABEL,
    centered_roi,
    draw_roi_outline,
    make_demo_tiles,
)

DEMO_SCENARIOS = {
    "Typical drift (inside calibration range)": "typical",
    "Large drift (outside calibration range)": "large",
}


@st.cache_resource(show_spinner=False)
def get_model() -> CalibrationBundle:
    """Load the saved calibration model once per session."""
    return ensure_model()


@st.cache_data(show_spinner=False)
def get_demo_tiles(scenario: str) -> tuple[np.ndarray, np.ndarray]:
    """Return deterministic demo tiles; the typical scenario uses the shipped PNG files."""
    if scenario == "typical" and MASTER_SAMPLE_PATH.exists() and PRODUCTION_SAMPLE_PATH.exists():
        return load_image(MASTER_SAMPLE_PATH), load_image(PRODUCTION_SAMPLE_PATH)
    return make_demo_tiles(scenario)  # type: ignore[arg-type]


def record_decision(signature: str, decision: str) -> None:
    """Remember the QC decision for the current inputs (session only)."""
    st.session_state["qc_decision"] = (signature, decision)


def render_analysis(result: dict[str, float]) -> None:
    st.subheader("C. Colour Analysis")
    table = pd.DataFrame(
        {
            "Metric": ["L*", "a*", "b*"],
            "Master": [result["master_L"], result["master_a"], result["master_b"]],
            "Production": [result["production_L"], result["production_a"], result["production_b"]],
            "Difference": [result["delta_L"], result["delta_a"], result["delta_b"]],
        }
    ).round(2)
    st.dataframe(table, hide_index=True)
    col_a, col_b = st.columns(2)
    col_a.metric("ΔE (CIE76)", f"{result['delta_E']:.2f}")
    col_b.metric("ΔE2000 (reference)", f"{result['delta_E2000']:.2f}")
    st.caption(
        "Image-derived Lab values are a prototype approximation. Validate against the "
        "client's spectrophotometer before production use. Gloss (Δgloss) is not implemented."
    )


def render_recommendation(rec: Recommendation) -> None:
    st.subheader("E. Printer Recommendation")
    st.caption(f"{MODEL_LABEL} {SYNTHETIC_LABEL}")
    if rec.adjustments is None:
        st.error(f"**{LOW_CONFIDENCE_FLAG}** — no recommendation provided.")
        return
    table = pd.DataFrame(
        {
            "Channel": [c.capitalize() for c in rec.adjustments],
            "Recommended Adjustment": [f"{v:+.1f}%" for v in rec.adjustments.values()],
        }
    )
    st.dataframe(table, hide_index=True)


def render_confidence(rec: Recommendation) -> None:
    st.subheader("F. Confidence")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Calibration status", "Inside range" if rec.in_training_range else "Outside range")
    col_b.metric("Recommendation status", rec.status)
    col_c.metric("Within training range", "Yes" if rec.in_training_range else "No")
    for message in rec.messages:
        if message == LOW_CONFIDENCE_FLAG:
            continue
        if rec.status == STATUS_OUTSIDE:
            st.error(message)
        else:
            st.warning(message)
    if rec.status == STATUS_REVIEW:
        st.warning("Review required before this recommendation is used.")


def render_qc_gate(rec: Recommendation, signature: str) -> None:
    st.subheader("G. QC Gate")
    st.warning(f"### {QC_NOTICE}")
    accept_col, reject_col = st.columns(2)
    accept_col.button(
        "Accept Recommendation",
        disabled=rec.adjustments is None,
        on_click=record_decision,
        args=(signature, "accepted"),
    )
    reject_col.button("Reject Recommendation", on_click=record_decision, args=(signature, "rejected"))
    stored = st.session_state.get("qc_decision")
    if stored and stored[0] == signature:
        st.info(
            f"Recommendation {stored[1]} for this session. "
            "No production system or Photoshop file was changed."
        )


def main() -> None:
    st.set_page_config(page_title="Tile Colour Calibration Engine", layout="wide")
    st.title("Tile Colour Calibration Engine")
    st.caption("Prototype for ceramic tile colour comparison and printer-adjustment recommendation")
    st.warning(
        "Prototype only. The calibration model uses synthetic data and has not been validated "
        "against any real printer. It does not control production."
    )

    bundle = get_model()
    roi_fraction = st.sidebar.slider("Measured area (centre of tile)", 0.2, 1.0, SETTINGS.roi_fraction, 0.05)
    roi = centered_roi(roi_fraction)

    st.subheader("A. Upload")
    up_master, up_production = st.columns(2)
    master_file = up_master.file_uploader("Upload Master Tile", type=["png", "jpg", "jpeg"])
    production_file = up_production.file_uploader("Upload Production Tile", type=["png", "jpg", "jpeg"])

    try:
        if master_file is None and production_file is None:
            st.info(DEMO_LABEL)
            choice = st.sidebar.radio("Demo scenario", list(DEMO_SCENARIOS))
            master, production = get_demo_tiles(DEMO_SCENARIOS[choice])
            source = f"demo-{DEMO_SCENARIOS[choice]}"
        elif master_file is None or production_file is None:
            st.info("Upload both tiles to run an analysis, or clear the upload to use demo mode.")
            return
        else:
            master, production = load_image(master_file), load_image(production_file)
            source = f"upload-{master_file.name}-{production_file.name}"
    except ImageValidationError as exc:
        st.error(str(exc))
        return

    st.subheader("B. Image Preview")
    prev_master, prev_production = st.columns(2)
    prev_master.image(draw_roi_outline(master, roi), caption="Master tile (measured area outlined)")
    prev_production.image(draw_roi_outline(production, roi), caption="Production tile (measured area outlined)")

    result = compare_tiles(master, production, roi)
    render_analysis(result)

    st.subheader("D. Interpretation")
    st.info(interpret_difference(result["delta_L"], result["delta_a"], result["delta_b"]))

    rec = recommend(result["delta_L"], result["delta_a"], result["delta_b"], bundle)
    render_recommendation(rec)
    render_confidence(rec)
    render_qc_gate(rec, f"{source}-{roi_fraction}-{result['delta_E']:.4f}")

    with st.expander("Model details (synthetic data)"):
        st.caption(MODEL_LABEL)
        st.write(
            f"Test MAE: {bundle.metrics['mae_mean']:.2f} percentage points · "
            f"Test R²: {bundle.metrics['r2_mean']:.2f}"
        )
        st.dataframe(bundle.coefficients.round(3))


main()
