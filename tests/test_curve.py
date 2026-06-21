"""Tests for openassay curve module."""

from __future__ import annotations

import numpy as np
import pytest

from openassay.curve import CalibrationResult, StandardCurve, fit_standard_curve


def test_standard_curve_defaults_to_1y2():
    """StandardCurve should default to 1/y2 weighting."""
    x = [0.1, 1.0, 10.0, 100.0]
    y = [2.0, 20.0, 80.0, 98.0]

    curve = StandardCurve(x, y)
    assert curve._weights == "1/y2"


def test_standard_curve_explicit_uniform():
    """StandardCurve should allow explicit uniform weighting."""
    x = [0.1, 1.0, 10.0, 100.0]
    y = [2.0, 20.0, 80.0, 98.0]

    curve = StandardCurve(x, y, weights="uniform")
    assert curve._weights == "uniform"


def test_standard_curve_rejects_invalid_weights():
    """StandardCurve should reject invalid weight strings."""
    x = [0.1, 1.0, 10.0, 100.0]
    y = [2.0, 20.0, 80.0, 98.0]

    with pytest.raises(ValueError, match="Invalid weights"):
        StandardCurve(x, y, weights="invalid")


def test_standard_curve_rejects_nan_inf():
    """StandardCurve should raise ValueError for NaN or Inf in input."""
    x = [0.1, 1.0, np.nan, 100.0]
    y = [2.0, 20.0, 80.0, 98.0]

    with pytest.raises(ValueError, match="NaN or Inf"):
        StandardCurve(x, y)


def test_standard_curve_fit_returns_calibration_result():
    """StandardCurve.fit() should return a CalibrationResult."""
    x = [0.1, 0.3, 1.0, 10.0, 100.0]
    y = [2.0, 5.0, 20.0, 80.0, 98.0]

    curve = StandardCurve(x, y, model="hill4p")
    result = curve.fit()

    assert isinstance(result, CalibrationResult)
    assert result.fit_result is not None
    assert result.fit_result.model_id == "hill4p"


def test_fit_standard_curve_functional_api_sets_reportable_range():
    """Functional API should fit and preserve optional reportable range metadata."""
    result = fit_standard_curve(
        [0.1, 0.3, 1.0, 10.0, 100.0],
        [2.0, 5.0, 20.0, 80.0, 98.0],
        lloq=0.3,
        uloq=100.0,
    )

    assert isinstance(result, CalibrationResult)
    assert result.fit_result.model_id == "hill4p"
    assert result.reportable_range == (0.3, 100.0)
