"""Relative potency estimation gated by parallelism."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openassay.parallelism import ParallelismResult, test_parallelism


@dataclass(frozen=True)
class PotencyResult:
    """Relative potency result."""

    reportable: bool
    point_estimate: float | None
    parallelism: ParallelismResult
    reasons: list[str]


def _fit_result(value: Any) -> Any:
    return getattr(value, "fit_result", value)


def relative_potency(
    reference: Any,
    test: Any,
    *,
    require_parallelism: bool = True,
    tolerance: float = 0.20,
) -> PotencyResult:
    """Estimate relative potency from EC50 ratio when parallelism is demonstrated."""
    parallelism = test_parallelism(reference, test, tolerance=tolerance)
    if require_parallelism and not parallelism.parallel:
        return PotencyResult(
            reportable=False,
            point_estimate=None,
            parallelism=parallelism,
            reasons=["Relative potency is not reportable because parallelism failed."],
        )

    reference_fit = _fit_result(reference)
    test_fit = _fit_result(test)
    potency = float(reference_fit.params["EC50"]) / float(test_fit.params["EC50"])
    return PotencyResult(
        reportable=parallelism.parallel,
        point_estimate=potency,
        parallelism=parallelism,
        reasons=["Relative potency estimated from EC50 ratio."],
    )
