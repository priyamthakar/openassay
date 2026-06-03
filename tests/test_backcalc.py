"""Tests for openassay backcalc module."""

from __future__ import annotations

import pytest

from openassay.backcalc import Sample, back_calculate
from openassay.curve import StandardCurve


def test_back_calculate_applies_dilution():
    """Back-calculation should apply dilution factor after inverse prediction."""
    x = [0.1, 0.3, 1.0, 10.0, 100.0]
    y = [2.0, 5.0, 20.0, 80.0, 98.0]

    curve = StandardCurve(x, y, model="hill4p")
    result = curve.fit()

    sample = Sample(name="test", response=50.0, dilution_factor=10.0)
    bc_result = back_calculate(sample, result.fit_result)

    # Predicted should be around 5 (since y=50 is between 20 and 80, x between 1 and 10)
    # Diluted should be predicted * 10
    assert bc_result.diluted_concentration == bc_result.predicted_concentration * 10.0


def test_back_calculate_rejects_nan_response():
    """Back-calculation should raise ValueError for NaN response."""
    x = [0.1, 0.3, 1.0, 10.0, 100.0]
    y = [2.0, 5.0, 20.0, 80.0, 98.0]

    curve = StandardCurve(x, y, model="hill4p")
    result = curve.fit()

    sample = Sample(name="test", response=float("nan"), dilution_factor=1.0)

    with pytest.raises(ValueError, match="finite"):
        back_calculate(sample, result.fit_result)


def test_back_calculate_flags_lloq_uloq():
    """Back-calculation should flag below LLOQ and above ULOQ."""
    x = [0.1, 0.3, 1.0, 10.0, 100.0]
    y = [2.0, 5.0, 20.0, 80.0, 98.0]

    curve = StandardCurve(x, y, model="hill4p")
    result = curve.fit()

    # Response near bottom of curve (x ~ 0.1, y ~ 2.0)
    # With dilution 1.0, diluted will be ~0.1, which is < lloq=0.5
    sample_low = Sample(name="low", response=2.5, dilution_factor=1.0)
    bc_low = back_calculate(sample_low, result.fit_result, lloq=0.5, uloq=90.0)
    assert bc_low.below_lloq is True

    # Response near top of curve (x ~ 100.0, y ~ 98.0)
    # With dilution 1.0, diluted will be ~100, which is > uloq=90.0
    sample_high = Sample(name="high", response=95.0, dilution_factor=1.0)
    bc_high = back_calculate(sample_high, result.fit_result, lloq=0.5, uloq=90.0)
    assert bc_high.above_uloq is True
