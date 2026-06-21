"""Cross-module tests for implemented openassay correctness invariants."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from openassay.acceptance import AcceptanceResult, run_acceptance
from openassay.ada import screen_cut_point
from openassay.backcalc import Sample, back_calculate
from openassay.curve import StandardCurve
from openassay.potency import relative_potency
from openassay.report import (
    DISCLAIMER,
    generate_docx_report,
    generate_html_report,
    generate_markdown_report,
    generate_pdf_report,
)


def test_standard_curves_default_to_1_y2_weighting() -> None:
    """Invariant 1: standard curves default to 1/y2 weighting."""
    curve = StandardCurve([0.1, 1.0, 10.0, 100.0], [2.0, 20.0, 80.0, 98.0])

    assert curve._weights == "1/y2"


def test_standard_curve_passes_weights_explicitly_to_openfit(monkeypatch) -> None:
    """Invariant 2: openassay always passes weights= to openfit."""
    seen: dict[str, object] = {}

    class FakeFit:
        def __init__(self, **kwargs) -> None:
            seen.update(kwargs)

        def run(self) -> SimpleNamespace:
            return SimpleNamespace(model_id="hill4p")

    monkeypatch.setattr("openassay.curve.Fit", FakeFit)

    StandardCurve([0.1, 1.0, 10.0, 100.0], [2.0, 20.0, 80.0, 98.0]).fit()

    assert seen["weights"] == "1/y2"


def test_nan_or_inf_inputs_raise_value_error() -> None:
    """Invariant 3: NaN/Inf data are rejected, never repaired."""
    with pytest.raises(ValueError, match="NaN or Inf"):
        StandardCurve([0.1, float("nan"), 10.0, 100.0], [2.0, 20.0, 80.0, 98.0])

    fit_result = SimpleNamespace(
        model_id="hill4p",
        params={"Bottom": 0.0, "Top": 100.0, "EC50": 10.0, "HillSlope": 1.0},
    )
    with pytest.raises(ValueError, match="finite"):
        back_calculate(Sample(name="bad", response=float("inf")), fit_result)


def test_back_calculation_applies_dilution_after_inverse_prediction() -> None:
    """Invariant 4: dilution is applied after inverse prediction."""
    fit_result = SimpleNamespace(
        model_id="hill4p",
        params={"Bottom": 0.0, "Top": 100.0, "EC50": 10.0, "HillSlope": 1.0},
    )

    result = back_calculate(
        Sample(name="diluted", response=50.0, dilution_factor=10.0),
        fit_result,
        minimum_required_dilution=2.0,
    )

    assert result.predicted_concentration == pytest.approx(10.0)
    assert result.diluted_concentration == pytest.approx(200.0)


def test_level_acceptance_requires_accuracy_and_precision() -> None:
    """Invariant 5: nominal levels need both accuracy and precision to pass."""
    poor_accuracy = [
        SimpleNamespace(
            sample_name="high-a",
            predicted_concentration=130.0,
            diluted_concentration=130.0,
            nominal_concentration=100.0,
            below_lloq=False,
            above_uloq=False,
        ),
        SimpleNamespace(
            sample_name="high-b",
            predicted_concentration=132.0,
            diluted_concentration=132.0,
            nominal_concentration=100.0,
            below_lloq=False,
            above_uloq=False,
        ),
    ]
    poor_precision = [
        SimpleNamespace(
            sample_name="wide-a",
            predicted_concentration=80.0,
            diluted_concentration=80.0,
            nominal_concentration=100.0,
            below_lloq=False,
            above_uloq=False,
        ),
        SimpleNamespace(
            sample_name="wide-b",
            predicted_concentration=120.0,
            diluted_concentration=120.0,
            nominal_concentration=100.0,
            below_lloq=False,
            above_uloq=False,
        ),
    ]

    assert run_acceptance(poor_accuracy).passed is False
    assert run_acceptance(poor_accuracy).level_stats[0].accuracy_pass is False
    assert run_acceptance(poor_precision).passed is False
    assert run_acceptance(poor_precision).level_stats[0].precision_pass is False


def test_anchor_results_are_excluded_from_acceptance_decisions() -> None:
    """Invariant 6: anchors do not drive acceptance decisions."""
    results = [
        SimpleNamespace(
            sample_name="anchor-low",
            predicted_concentration=0.1,
            diluted_concentration=0.1,
            nominal_concentration=1.0,
            below_lloq=True,
            above_uloq=False,
            is_anchor=True,
        ),
        SimpleNamespace(
            sample_name="qc",
            predicted_concentration=100.0,
            diluted_concentration=100.0,
            nominal_concentration=100.0,
            below_lloq=False,
            above_uloq=False,
        ),
    ]

    acceptance = run_acceptance(results)

    assert acceptance.passed is True
    assert len(acceptance.level_stats) == 1
    assert acceptance.level_stats[0].nominal_concentration == 100.0


def test_relative_potency_requires_parallelism() -> None:
    """Invariant 7: potency is not reportable if parallelism fails."""
    reference = SimpleNamespace(
        model_id="hill4p",
        params={"Bottom": 1.0, "Top": 100.0, "EC50": 10.0, "HillSlope": 1.0},
    )
    test = SimpleNamespace(
        model_id="hill4p",
        params={"Bottom": 1.0, "Top": 100.0, "EC50": 5.0, "HillSlope": 1.8},
    )

    potency = relative_potency(reference, test)

    assert potency.reportable is False
    assert potency.point_estimate is None


def test_ada_cut_points_require_biological_variability() -> None:
    """Invariant 8: ADA cut points refuse single-run biological data."""
    result = screen_cut_point(
        [
            SimpleNamespace(sample_id="donor-1", run_id="run-1", response=100.0),
            SimpleNamespace(sample_id="donor-2", run_id="run-1", response=105.0),
        ]
    )

    assert result.evaluable is False
    assert result.cut_point is None


def test_reports_include_required_disclaimer(tmp_path) -> None:
    """Invariant 9: every generated report includes the disclaimer."""
    curve = StandardCurve(
        [0.1, 0.3, 1.0, 10.0, 100.0],
        [2.0, 5.0, 20.0, 80.0, 98.0],
    )
    curve_result = curve.fit()
    acceptance = AcceptanceResult(passed=True, reasons=["ok"])
    html_path = tmp_path / "report.html"
    md_path = tmp_path / "report.md"
    pdf_path = tmp_path / "report.pdf"
    docx_path = tmp_path / "report.docx"

    generate_html_report(curve_result, [], acceptance, str(html_path))
    generate_markdown_report(curve_result, [], acceptance, str(md_path))
    generate_pdf_report(curve_result, [], acceptance, str(pdf_path))
    generate_docx_report(curve_result, [], acceptance, str(docx_path))

    assert DISCLAIMER in html_path.read_text(encoding="utf-8")
    assert DISCLAIMER in md_path.read_text(encoding="utf-8")
    assert pdf_path.exists()
    assert docx_path.exists()
