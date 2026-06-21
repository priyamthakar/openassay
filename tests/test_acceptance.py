"""Tests for openassay acceptance module."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from openassay.acceptance import run_acceptance
from openassay.backcalc import BackCalcResult


def test_run_acceptance_passes_when_in_range():
    """Acceptance should pass when all samples are within range."""
    results = [
        BackCalcResult(
            sample_name="s1",
            predicted_concentration=10.0,
            diluted_concentration=10.0,
            below_lloq=False,
            above_uloq=False,
        )
    ]

    acc = run_acceptance(results)
    assert acc.passed is True
    assert "within acceptance criteria" in acc.reasons[0]


def test_run_acceptance_fails_when_out_of_range():
    """Acceptance should fail when samples are outside reportable range."""
    results = [
        BackCalcResult(
            sample_name="s1",
            predicted_concentration=0.1,
            diluted_concentration=0.1,
            below_lloq=True,
            above_uloq=False,
        )
    ]

    acc = run_acceptance(results)
    assert acc.passed is False
    assert "outside reportable range" in acc.reasons[0]


def test_run_acceptance_fails_on_non_finite_concentration():
    """Acceptance should fail defensively if a non-finite result is provided."""
    results = [
        BackCalcResult(
            sample_name="s1",
            predicted_concentration=float("nan"),
            diluted_concentration=float("nan"),
            below_lloq=False,
            above_uloq=False,
        )
    ]

    acc = run_acceptance(results)
    assert acc.passed is False
    assert "non-finite" in acc.reasons[0]


def test_run_acceptance_computes_level_accuracy_and_precision():
    """Replicate nominal levels should produce %bias and %CV summaries."""
    results = [
        SimpleNamespace(
            sample_name="qc-1a",
            predicted_concentration=98.0,
            diluted_concentration=98.0,
            nominal_concentration=100.0,
            below_lloq=False,
            above_uloq=False,
        ),
        SimpleNamespace(
            sample_name="qc-1b",
            predicted_concentration=102.0,
            diluted_concentration=102.0,
            nominal_concentration=100.0,
            below_lloq=False,
            above_uloq=False,
        ),
    ]

    acc = run_acceptance(results)

    assert acc.passed is True
    assert len(acc.level_stats) == 1
    level = acc.level_stats[0]
    assert level.bias_percent == pytest.approx(0.0)
    assert level.cv_percent == pytest.approx(2.828427, rel=1e-5)
    assert level.accuracy_pass is True
    assert level.precision_pass is True


def test_run_acceptance_fails_level_accuracy():
    """A nominal level should fail when mean bias exceeds the threshold."""
    results = [
        SimpleNamespace(
            sample_name="qc-1a",
            predicted_concentration=130.0,
            diluted_concentration=130.0,
            nominal_concentration=100.0,
            below_lloq=False,
            above_uloq=False,
        ),
        SimpleNamespace(
            sample_name="qc-1b",
            predicted_concentration=132.0,
            diluted_concentration=132.0,
            nominal_concentration=100.0,
            below_lloq=False,
            above_uloq=False,
        ),
    ]

    acc = run_acceptance(results)

    assert acc.passed is False
    assert "failed accuracy" in " ".join(acc.reasons)
    assert acc.level_stats[0].accuracy_pass is False


def test_run_acceptance_fails_level_precision():
    """A nominal level should fail when replicate CV exceeds the threshold."""
    results = [
        SimpleNamespace(
            sample_name="qc-1a",
            predicted_concentration=80.0,
            diluted_concentration=80.0,
            nominal_concentration=100.0,
            below_lloq=False,
            above_uloq=False,
        ),
        SimpleNamespace(
            sample_name="qc-1b",
            predicted_concentration=120.0,
            diluted_concentration=120.0,
            nominal_concentration=100.0,
            below_lloq=False,
            above_uloq=False,
        ),
    ]

    acc = run_acceptance(results)

    assert acc.passed is False
    assert "failed precision" in " ".join(acc.reasons)
    assert acc.level_stats[0].precision_pass is False
