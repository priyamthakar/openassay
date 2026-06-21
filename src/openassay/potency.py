"""Relative potency estimation gated by parallelism."""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist
from typing import Any

from openassay.parallelism import ParallelismResult, test_parallelism


@dataclass(frozen=True)
class PotencyResult:
    """Relative potency result."""

    reportable: bool
    point_estimate: float | None
    confidence_interval: tuple[float, float] | None
    confidence: float
    parallelism: ParallelismResult
    reasons: list[str]


def _fit_result(value: Any) -> Any:
    return getattr(value, "fit_result", value)


def _ec50_variance(fit: Any) -> float | None:
    covariance = getattr(fit, "covariance", None)
    if covariance is None:
        return None
    try:
        variance = float(covariance[2][2])
    except (IndexError, KeyError, TypeError, ValueError):
        return None
    if not math.isfinite(variance) or variance < 0.0:
        return None
    return variance


def _potency_confidence_interval(
    *,
    potency: float,
    reference_ec50: float,
    test_ec50: float,
    reference_ec50_variance: float,
    test_ec50_variance: float,
    confidence: float,
) -> tuple[float, float] | None:
    if reference_ec50 <= 0.0 or test_ec50 <= 0.0 or potency <= 0.0:
        return None

    log_variance = reference_ec50_variance / (reference_ec50**2) + test_ec50_variance / (
        test_ec50**2
    )
    if not math.isfinite(log_variance) or log_variance < 0.0:
        return None

    z = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    margin = z * math.sqrt(log_variance)
    log_potency = math.log(potency)
    return (math.exp(log_potency - margin), math.exp(log_potency + margin))


def relative_potency(
    reference: Any,
    test: Any,
    *,
    require_parallelism: bool = True,
    method: str = "equivalence",
    tolerance: float = 0.20,
    confidence: float = 0.95,
) -> PotencyResult:
    """Estimate relative potency from EC50 ratio when parallelism is demonstrated."""
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1.")

    parallelism = test_parallelism(reference, test, method=method, tolerance=tolerance)
    if require_parallelism and not parallelism.parallel:
        return PotencyResult(
            reportable=False,
            point_estimate=None,
            confidence_interval=None,
            confidence=confidence,
            parallelism=parallelism,
            reasons=["Relative potency is not reportable because parallelism failed."],
        )

    reference_fit = _fit_result(reference)
    test_fit = _fit_result(test)
    reference_ec50 = float(reference_fit.params["EC50"])
    test_ec50 = float(test_fit.params["EC50"])
    potency = reference_ec50 / test_ec50
    reasons = ["Relative potency estimated from EC50 ratio."]
    confidence_interval = None
    reference_ec50_variance = _ec50_variance(reference_fit)
    test_ec50_variance = _ec50_variance(test_fit)
    if reference_ec50_variance is None or test_ec50_variance is None:
        reasons.append("Confidence interval unavailable because EC50 covariance is unavailable.")
    else:
        confidence_interval = _potency_confidence_interval(
            potency=potency,
            reference_ec50=reference_ec50,
            test_ec50=test_ec50,
            reference_ec50_variance=reference_ec50_variance,
            test_ec50_variance=test_ec50_variance,
            confidence=confidence,
        )
        if confidence_interval is None:
            reasons.append("Confidence interval unavailable because EC50 variance is invalid.")

    return PotencyResult(
        reportable=parallelism.parallel,
        point_estimate=potency,
        confidence_interval=confidence_interval,
        confidence=confidence,
        parallelism=parallelism,
        reasons=reasons,
    )
