"""ADA screening and confirmatory cut-point workflows."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from statistics import NormalDist
from typing import Any

import numpy as np

from openassay.types import DEFAULT_CONFIRMATORY_FP_RATE, DEFAULT_SCREENING_FP_RATE


@dataclass(frozen=True)
class ADAResult:
    """Anti-drug-antibody cut-point result."""

    evaluable: bool
    cut_point: float | None
    method: str
    fp_rate: float
    n_samples: int
    n_runs: int
    reasons: list[str]
    excluded_indices: list[int]


def _field(record: Any, *names: str) -> Any:
    for name in names:
        if isinstance(record, dict) and name in record:
            return record[name]
        if hasattr(record, name):
            return getattr(record, name)
    expected = ", ".join(names)
    raise ValueError(f"record is missing one of: {expected}")


def _values(data: Sequence[Any], value_fields: tuple[str, ...]) -> np.ndarray:
    values = np.asarray([float(_field(record, *value_fields)) for record in data], dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError("ADA cut-point data must contain only finite values.")
    return values


def _apply_outlier_method(values: np.ndarray, outlier_method: str) -> tuple[np.ndarray, list[int]]:
    if outlier_method == "none":
        return values, []
    if outlier_method != "tukey":
        raise ValueError("outlier_method must be 'none' or 'tukey'.")

    q1 = float(np.quantile(values, 0.25, method="linear"))
    q3 = float(np.quantile(values, 0.75, method="linear"))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    keep = (values >= lower) & (values <= upper)
    excluded = [index for index, keep_value in enumerate(keep) if not bool(keep_value)]
    return values[keep], excluded


def _validate_fp_rate(fp_rate: float) -> None:
    if not 0.0 < fp_rate < 1.0:
        raise ValueError("fp_rate must be between 0 and 1.")


def _validate_method(method: str) -> None:
    if method not in {"parametric", "nonparametric"}:
        raise ValueError("method must be 'parametric' or 'nonparametric'.")


def _biological_variability(data: Sequence[Any]) -> tuple[int, int, list[str]]:
    sample_ids = {str(_field(record, "sample_id", "donor_id", "sample")) for record in data}
    run_ids = {str(_field(record, "run_id", "run")) for record in data}
    reasons: list[str] = []
    if len(sample_ids) < 2:
        reasons.append("ADA cut points require at least two biological samples.")
    if len(run_ids) < 2:
        reasons.append("ADA cut points require at least two analytical runs.")
    return len(sample_ids), len(run_ids), reasons


def _cut_point(values: np.ndarray, *, method: str, fp_rate: float) -> float:
    if method == "nonparametric":
        return float(np.quantile(values, 1.0 - fp_rate, method="linear"))

    sd = float(np.std(values, ddof=1))
    z = NormalDist().inv_cdf(1.0 - fp_rate)
    return float(np.mean(values) + z * sd)


def _evaluate_cut_point(
    data: Sequence[Any],
    *,
    method: str,
    fp_rate: float,
    value_fields: tuple[str, ...],
    label: str,
    outlier_method: str,
) -> ADAResult:
    _validate_method(method)
    _validate_fp_rate(fp_rate)
    n_samples, n_runs, variability_reasons = _biological_variability(data)
    if variability_reasons:
        return ADAResult(
            evaluable=False,
            cut_point=None,
            method=method,
            fp_rate=fp_rate,
            n_samples=n_samples,
            n_runs=n_runs,
            reasons=variability_reasons,
            excluded_indices=[],
        )

    values = _values(data, value_fields)
    values, excluded_indices = _apply_outlier_method(values, outlier_method)
    if len(values) < 2:
        return ADAResult(
            evaluable=False,
            cut_point=None,
            method=method,
            fp_rate=fp_rate,
            n_samples=n_samples,
            n_runs=n_runs,
            reasons=[f"{label} cut point requires at least two observations."],
            excluded_indices=excluded_indices,
        )

    reasons = [f"{label} cut point estimated using {method} method."]
    if excluded_indices:
        reasons.append(
            f"Excluded {len(excluded_indices)} observation(s) using "
            f"{outlier_method} outlier method."
        )

    return ADAResult(
        evaluable=True,
        cut_point=_cut_point(values, method=method, fp_rate=fp_rate),
        method=method,
        fp_rate=fp_rate,
        n_samples=n_samples,
        n_runs=n_runs,
        reasons=reasons,
        excluded_indices=excluded_indices,
    )


def screen_cut_point(
    data: Sequence[Any],
    *,
    method: str = "parametric",
    fp_rate: float = DEFAULT_SCREENING_FP_RATE,
    outlier_method: str = "none",
) -> ADAResult:
    """Estimate an ADA screening cut point from biological negative controls."""
    return _evaluate_cut_point(
        data,
        method=method,
        fp_rate=fp_rate,
        value_fields=("response", "signal", "value"),
        label="Screening",
        outlier_method=outlier_method,
    )


def confirm_cut_point(
    data: Sequence[Any],
    *,
    method: str = "parametric",
    fp_rate: float = DEFAULT_CONFIRMATORY_FP_RATE,
    outlier_method: str = "none",
) -> ADAResult:
    """Estimate an ADA confirmatory cut point from percent-inhibition data."""
    return _evaluate_cut_point(
        data,
        method=method,
        fp_rate=fp_rate,
        value_fields=("percent_inhibition", "inhibition", "value"),
        label="Confirmatory",
        outlier_method=outlier_method,
    )
