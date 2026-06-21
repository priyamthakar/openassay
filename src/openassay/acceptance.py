"""LBA acceptance criteria and run acceptance."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from openassay.types import DEFAULT_ACCURACY_PCT, DEFAULT_PRECISION_PCT


@dataclass
class LevelStats:
    """Accuracy and precision summary for one nominal concentration level."""

    nominal_concentration: float
    n: int
    mean_concentration: float
    sd_concentration: float
    bias_percent: float
    cv_percent: float
    accuracy_pass: bool
    precision_pass: bool


@dataclass
class AcceptanceResult:
    """Result of acceptance criteria evaluation."""

    passed: bool
    reasons: list[str]
    level_stats: list[LevelStats] = field(default_factory=list)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _reported_concentration(result: Any) -> float:
    return float(result.diluted_concentration)


def _nominal_concentration(result: Any) -> float | None:
    for attr in ("nominal_concentration", "nominal"):
        nominal = _optional_float(getattr(result, attr, None))
        if nominal is not None:
            return nominal
    return None


def _is_anchor(result: Any) -> bool:
    return bool(getattr(result, "is_anchor", False))


def _calculate_level_stats(
    backcalc_results: Sequence[Any],
    accuracy_threshold: float,
    precision_threshold: float,
) -> tuple[list[LevelStats], list[str]]:
    groups: dict[float, list[float]] = {}
    reasons: list[str] = []

    for res in backcalc_results:
        if _is_anchor(res):
            continue
        nominal = _nominal_concentration(res)
        if nominal is None:
            continue
        if nominal <= 0.0 or not np.isfinite(nominal):
            reasons.append(f"Sample {res.sample_name} has invalid nominal concentration")
            continue
        groups.setdefault(nominal, []).append(_reported_concentration(res))

    stats: list[LevelStats] = []
    for nominal, concentrations in sorted(groups.items()):
        values = np.asarray(concentrations, dtype=np.float64)
        if not np.isfinite(values).all():
            reasons.append(f"Nominal level {nominal:g} has non-finite concentrations")
            continue

        mean = float(np.mean(values))
        sd = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
        bias_percent = float((mean / nominal - 1.0) * 100.0)
        cv_percent = float(abs(sd / mean) * 100.0) if mean != 0.0 else float("inf")
        accuracy_pass = abs(bias_percent) <= accuracy_threshold
        precision_pass = cv_percent <= precision_threshold
        stats.append(
            LevelStats(
                nominal_concentration=nominal,
                n=len(values),
                mean_concentration=mean,
                sd_concentration=sd,
                bias_percent=bias_percent,
                cv_percent=cv_percent,
                accuracy_pass=accuracy_pass,
                precision_pass=precision_pass,
            )
        )

        if not accuracy_pass:
            reasons.append(
                f"Nominal level {nominal:g} failed accuracy: "
                f"bias {bias_percent:.2f}% exceeds {accuracy_threshold:.2f}%"
            )
        if not precision_pass:
            reasons.append(
                f"Nominal level {nominal:g} failed precision: "
                f"CV {cv_percent:.2f}% exceeds {precision_threshold:.2f}%"
            )

    return stats, reasons


def run_acceptance(
    backcalc_results: Sequence[Any],
    accuracy_threshold: float = DEFAULT_ACCURACY_PCT,
    precision_threshold: float = DEFAULT_PRECISION_PCT,
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
        if _is_anchor(res):
            continue
        if not np.isfinite(res.predicted_concentration) or not np.isfinite(
            res.diluted_concentration
        ):
            passed = False
            reasons.append(f"Sample {res.sample_name} has non-finite concentration")
            continue
        if res.below_lloq or res.above_uloq:
            passed = False
            reasons.append(f"Sample {res.sample_name} outside reportable range")

    level_stats, level_reasons = _calculate_level_stats(
        backcalc_results,
        accuracy_threshold,
        precision_threshold,
    )
    if level_reasons:
        passed = False
        reasons.extend(level_reasons)

    if not reasons:
        reasons.append("All samples within acceptance criteria")

    return AcceptanceResult(passed=passed, reasons=reasons, level_stats=level_stats)
