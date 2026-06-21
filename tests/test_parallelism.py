"""Tests for parallelism checks."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from openassay.parallelism import ParallelismResult, test_parallelism


def fit_result(*, bottom: float = 1.0, top: float = 100.0, ec50: float = 10.0, slope: float = 1.2):
    return SimpleNamespace(
        model_id="hill4p",
        params={"Bottom": bottom, "Top": top, "EC50": ec50, "HillSlope": slope},
    )


def test_parallelism_passes_for_horizontal_shift() -> None:
    """Different EC50 with similar shape should be parallel."""
    result = test_parallelism(fit_result(ec50=10.0), fit_result(ec50=5.0))

    assert isinstance(result, ParallelismResult)
    assert result.parallel is True
    assert result.parameter_ratios["HillSlope"] == pytest.approx(1.0)


def test_parallelism_fails_for_slope_change() -> None:
    """A large HillSlope change should fail the equivalence screen."""
    result = test_parallelism(fit_result(slope=1.0), fit_result(slope=1.8), tolerance=0.2)

    assert result.parallel is False
    assert "HillSlope" in " ".join(result.reasons)


def test_parallelism_rejects_model_mismatch() -> None:
    """Different curve models are not parallel."""
    reference = fit_result()
    test = fit_result()
    test.model_id = "hill5p"

    result = test_parallelism(reference, test)

    assert result.parallel is False
    assert "model mismatch" in result.reasons
