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


def fit_result_5pl(
    *,
    bottom: float = 1.0,
    top: float = 100.0,
    ec50: float = 10.0,
    slope: float = 1.2,
    asymmetry: float = 0.9,
):
    return SimpleNamespace(
        model_id="hill5p",
        params={
            "Bottom": bottom,
            "Top": top,
            "EC50": ec50,
            "HillSlope": slope,
            "Asymmetry": asymmetry,
        },
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


def test_parallelism_passes_for_5pl_horizontal_shift() -> None:
    """5PL curves with matching shape and shifted EC50 should be parallel."""
    result = test_parallelism(fit_result_5pl(ec50=10.0), fit_result_5pl(ec50=5.0))

    assert result.parallel is True
    assert result.parameter_ratios["Asymmetry"] == pytest.approx(1.0)


def test_parallelism_fails_for_5pl_asymmetry_change() -> None:
    """5PL asymmetry is a shape parameter and must pass equivalence."""
    result = test_parallelism(
        fit_result_5pl(asymmetry=0.9),
        fit_result_5pl(asymmetry=1.4),
        tolerance=0.2,
    )

    assert result.parallel is False
    assert "Asymmetry" in " ".join(result.reasons)


def test_parallelism_rejects_model_mismatch() -> None:
    """Different curve models are not parallel."""
    reference = fit_result()
    test = fit_result()
    test.model_id = "hill5p"

    result = test_parallelism(reference, test)

    assert result.parallel is False
    assert "model mismatch" in result.reasons
