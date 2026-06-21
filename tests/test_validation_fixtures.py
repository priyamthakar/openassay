"""Validation-fixture tests for calibration and QC workflows."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from openassay.acceptance import run_acceptance
from openassay.ada import confirm_cut_point, screen_cut_point
from openassay.backcalc import Sample, back_calculate_many
from openassay.curve import fit_standard_curve
from openassay.potency import relative_potency

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "validation"


def test_m10_style_calibration_qc_fixture_passes_acceptance() -> None:
    """Synthetic FDA/ICH M10-style calibration/QC fixture should pass acceptance."""
    data = pd.read_csv(FIXTURE_DIR / "m10_calibration_qc.csv")
    expected = json.loads((FIXTURE_DIR / "m10_calibration_qc_expected.json").read_text())

    standards = data[data["role"] == "standard"]
    qcs = data[data["role"] == "qc"]
    calibration = fit_standard_curve(
        standards["nominal_concentration"].to_numpy(),
        standards["response"].to_numpy(),
        model=expected["model"],
        weights=expected["weighting"],
    )
    samples = [
        Sample(
            name=str(row.name),
            response=float(row.response),
            dilution_factor=float(row.dilution_factor),
        )
        for row in qcs.itertuples(index=False)
    ]
    results = back_calculate_many(samples, calibration.fit_result)

    for result, row in zip(results, qcs.itertuples(index=False), strict=True):
        result.nominal_concentration = float(row.nominal_concentration)

    acceptance = run_acceptance(
        results,
        accuracy_threshold=expected["acceptance"]["max_abs_bias_percent"],
        precision_threshold=expected["acceptance"]["max_cv_percent"],
    )

    assert acceptance.passed is True
    assert (
        sorted(stat.nominal_concentration for stat in acceptance.level_stats)
        == expected["qc_nominal_concentrations"]
    )
    for stat in acceptance.level_stats:
        assert abs(stat.bias_percent) <= expected["acceptance"]["max_abs_bias_percent"]
        assert stat.cv_percent <= expected["acceptance"]["max_cv_percent"]


def test_parallelism_reference_fixture_matches_expected_ratios_and_potency() -> None:
    """Stored reference output should gate potency on demonstrated parallelism."""
    payload = json.loads((FIXTURE_DIR / "parallelism_reference.json").read_text())
    reference = SimpleNamespace(**payload["reference"])
    test = SimpleNamespace(**payload["test"])

    result = relative_potency(reference, test, tolerance=float(payload["tolerance"]))
    expected = payload["expected"]

    assert result.reportable is expected["reportable"]
    assert result.parallelism.parallel is expected["parallel"]
    assert result.point_estimate == pytest.approx(expected["relative_potency"])
    for name, ratio in expected["parameter_ratios"].items():
        assert result.parallelism.parameter_ratios[name] == pytest.approx(ratio)


def test_ada_cut_point_validation_fixture_matches_expected_outputs() -> None:
    """Stored ADA fixture should reproduce expected screening and confirmatory cut points."""
    data = pd.read_csv(FIXTURE_DIR / "ada_cut_points.csv")
    expected = json.loads((FIXTURE_DIR / "ada_cut_points_expected.json").read_text())
    records = data.to_dict(orient="records")

    screening = screen_cut_point(records)
    screening_nonparametric = screen_cut_point(
        records,
        method="nonparametric",
        fp_rate=float(expected["screening"]["fp_rate"]),
    )
    screening_floating = screen_cut_point(records, cut_point_type="floating")
    confirmatory = confirm_cut_point(records)

    assert screening.cut_point == pytest.approx(expected["screening"]["parametric_cut_point"])
    assert screening_nonparametric.cut_point == pytest.approx(
        expected["screening"]["nonparametric_cut_point"]
    )
    assert screening_floating.cut_point == pytest.approx(
        expected["screening"]["floating_multiplier"]
    )
    assert confirmatory.cut_point == pytest.approx(expected["confirmatory"]["parametric_cut_point"])
