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


def test_relative_potency_not_reportable_when_parallelism_fails() -> None:
    """Invariant 7: no potency estimate is emitted without parallelism."""
    result = relative_potency(fit_result(slope=1.0), fit_result(slope=1.8), tolerance=0.2)

    assert result.reportable is False
    assert result.point_estimate is None
    assert result.confidence_interval is None
    assert result.parallelism.parallel is False
