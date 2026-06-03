"""Tests for openassay acceptance module."""

from __future__ import annotations

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
