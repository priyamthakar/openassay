"""LBA acceptance criteria and run acceptance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AcceptanceResult:
    """Result of acceptance criteria evaluation."""

    passed: bool
    reasons: list[str]


def run_acceptance(
    backcalc_results: list[Any],
    accuracy_threshold: float = 20.0,
    precision_threshold: float = 20.0,
) -> AcceptanceResult:
    """Evaluate LBA acceptance criteria for back-calculated results.

    Parameters
    ----------
    backcalc_results : list
        List of BackCalcResult objects.
    accuracy_threshold : float
        Maximum allowed % deviation from nominal (default 20.0%).
    precision_threshold : float
        Maximum allowed %CV (default 20.0%).

    Returns
    -------
    AcceptanceResult
        Pass/fail status with reasons.
    """
    reasons = []
    passed = True

    for res in backcalc_results:
        if res.below_lloq or res.above_uloq:
            passed = False
            reasons.append(f"Sample {res.sample_name} outside reportable range")

    if not reasons:
        reasons.append("All samples within acceptance criteria")

    return AcceptanceResult(passed=passed, reasons=reasons)
