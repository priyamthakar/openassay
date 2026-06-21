"""Tests for relative potency."""

from __future__ import annotations

from types import SimpleNamespace

from openassay.potency import PotencyResult, relative_potency


def fit_result(*, ec50: float = 10.0, slope: float = 1.2):
    return SimpleNamespace(
        model_id="hill4p",
        params={"Bottom": 1.0, "Top": 100.0, "EC50": ec50, "HillSlope": slope},
    )


def test_relative_potency_reportable_when_parallel() -> None:
    """Parallel horizontal shifts should report EC50-ratio potency."""
    result = relative_potency(fit_result(ec50=10.0), fit_result(ec50=5.0))

    assert isinstance(result, PotencyResult)
    assert result.reportable is True
    assert result.point_estimate == 2.0


def test_relative_potency_not_reportable_when_parallelism_fails() -> None:
    """Invariant 7: no potency estimate is emitted without parallelism."""
    result = relative_potency(fit_result(slope=1.0), fit_result(slope=1.8), tolerance=0.2)

    assert result.reportable is False
    assert result.point_estimate is None
    assert result.parallelism.parallel is False
