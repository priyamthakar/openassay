"""Tests for relative potency."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from openassay.potency import PotencyResult, relative_potency


def fit_result(
    *,
    ec50: float = 10.0,
    slope: float = 1.2,
    ec50_variance: float | None = None,
):
    covariance = None
    if ec50_variance is not None:
        covariance = [
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, ec50_variance, 0.0],
            [0.0, 0.0, 0.0, 0.0],
        ]
    return SimpleNamespace(
        model_id="hill4p",
        params={"Bottom": 1.0, "Top": 100.0, "EC50": ec50, "HillSlope": slope},
        covariance=covariance,
    )


def fit_result_linear(
    *,
    slope: float = 2.0,
    intercept: float = 1.0,
    log_base: float = 10.0,
):
    return SimpleNamespace(
        model_id="linear",
        params={"Slope": slope, "Intercept": intercept},
        log_base=log_base,
    )


def test_relative_potency_reportable_when_parallel() -> None:
    """Parallel horizontal shifts should report EC50-ratio potency."""
    result = relative_potency(fit_result(ec50=10.0), fit_result(ec50=5.0))

    assert isinstance(result, PotencyResult)
    assert result.reportable is True
    assert result.point_estimate == 2.0
    assert result.confidence_interval is None
    assert "covariance is unavailable" in " ".join(result.reasons)


def test_relative_potency_ci_uses_ec50_covariance() -> None:
    """EC50-ratio confidence intervals should use openfit covariance."""
    result = relative_potency(
        fit_result(ec50=10.0, ec50_variance=0.04),
        fit_result(ec50=5.0, ec50_variance=0.01),
    )

    assert result.confidence_interval is not None
    lower, upper = result.confidence_interval
    assert lower == pytest.approx(1.8921449)
    assert upper == pytest.approx(2.1140031)
    assert result.confidence == 0.95


def test_relative_potency_passes_parallelism_method() -> None:
    """Potency should expose the selected parallelism method."""
    result = relative_potency(fit_result(), fit_result(), method="equivalence")

    assert result.parallelism.method == "equivalence"


def test_relative_potency_rejects_unknown_parallelism_method() -> None:
    """Unsupported parallelism methods should fail explicitly."""
    with pytest.raises(ValueError, match="method='equivalence'"):
        relative_potency(fit_result(), fit_result(), method="f-test")


def test_relative_potency_from_parallel_line_intercept_shift() -> None:
    """Parallel-line potency should come from the intercept displacement."""
    result = relative_potency(
        fit_result_linear(slope=2.0, intercept=1.0),
        fit_result_linear(slope=2.0, intercept=3.0),
    )

    assert result.reportable is True
    assert result.point_estimate == pytest.approx(10.0)
    assert result.confidence_interval is None
    assert "intercept shift" in " ".join(result.reasons)


def test_relative_potency_suppresses_parallel_line_when_slope_fails() -> None:
    """Parallel-line potency is not reportable without slope equivalence."""
    result = relative_potency(
        fit_result_linear(slope=2.0),
        fit_result_linear(slope=3.0),
        tolerance=0.1,
    )

    assert result.reportable is False
    assert result.point_estimate is None


def test_relative_potency_not_reportable_when_parallelism_fails() -> None:
    """Invariant 7: no potency estimate is emitted without parallelism."""
    result = relative_potency(fit_result(slope=1.0), fit_result(slope=1.8), tolerance=0.2)

    assert result.reportable is False
    assert result.point_estimate is None
    assert result.confidence_interval is None
    assert result.parallelism.parallel is False
