"""Parallelism checks for relative-potency workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParallelismResult:
    """Result of a parallelism assessment."""

    parallel: bool
    method: str
    reasons: list[str]
    parameter_ratios: dict[str, float]
    tolerance: float


def _fit_result(value: Any) -> Any:
    return getattr(value, "fit_result", value)


def _parameter_ratio(test_value: float, reference_value: float) -> float:
    if reference_value == 0.0:
        return 1.0 if test_value == 0.0 else float("inf")
    return test_value / reference_value


def _shape_parameters(model_id: str) -> list[str]:
    if model_id == "hill4p":
        return ["Bottom", "Top", "HillSlope"]
    if model_id == "hill5p":
        return ["Bottom", "Top", "HillSlope", "Asymmetry"]
    if model_id in {"linear", "log_linear", "parallel_line"}:
        return ["Slope"]
    raise ValueError("Parallelism currently supports hill4p, hill5p, and linear fits.")


def test_parallelism(
    reference: Any,
    test: Any,
    *,
    method: str = "equivalence",
    tolerance: float = 0.20,
) -> ParallelismResult:
    """Assess 4PL/5PL curve parallelism from fitted shape parameters.

    The equivalence screen compares fitted shape parameters within
    ``1 +/- tolerance``. EC50 is allowed to differ for 4PL/5PL curves, and
    intercept is allowed to differ for parallel-line fits because those shifts
    are the relative-potency signal.
    """
    if method != "equivalence":
        raise ValueError("Only method='equivalence' is currently supported.")
    if tolerance <= 0.0:
        raise ValueError("tolerance must be positive.")

    reference_fit = _fit_result(reference)
    test_fit = _fit_result(test)
    if reference_fit.model_id != test_fit.model_id:
        return ParallelismResult(
            parallel=False,
            method=method,
            reasons=["model mismatch"],
            parameter_ratios={},
            tolerance=tolerance,
        )
    compared = _shape_parameters(str(reference_fit.model_id))

    ratios: dict[str, float] = {}
    reasons: list[str] = []
    lower = 1.0 - tolerance
    upper = 1.0 + tolerance

    for name in compared:
        ratio = _parameter_ratio(float(test_fit.params[name]), float(reference_fit.params[name]))
        ratios[name] = ratio
        if not lower <= ratio <= upper:
            reasons.append(f"{name} ratio {ratio:.4g} outside {lower:.4g}-{upper:.4g}")

    if not reasons:
        reasons.append("Shape parameters within equivalence tolerance")

    return ParallelismResult(
        parallel=not any("outside" in reason for reason in reasons),
        method=method,
        reasons=reasons,
        parameter_ratios=ratios,
        tolerance=tolerance,
    )


setattr(test_parallelism, "__test__", False)
