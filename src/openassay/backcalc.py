"""Back-calculation of unknown sample concentrations."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
from openfit import FitResult


@dataclass
class Sample:
    """Sample with observed response and optional dilution factor."""

    name: str
    response: float
    dilution_factor: float = 1.0


@dataclass
class BackCalcResult:
    """Result of back-calculating a sample concentration."""

    sample_name: str
    predicted_concentration: float
    diluted_concentration: float
    below_lloq: bool
    above_uloq: bool
    lloq: float | None = None
    uloq: float | None = None


def _inverse_hill_response(response: float, fit_result: FitResult) -> float:
    """Return concentration from public openfit result parameters."""
    params = fit_result.params
    model_id = fit_result.model_id

    try:
        bottom = float(params["Bottom"])
        top = float(params["Top"])
        ec50 = float(params["EC50"])
        slope = float(params["HillSlope"])
    except KeyError as exc:
        raise ValueError(f"FitResult for model {model_id!r} is missing parameter {exc}.") from exc

    if model_id == "hill4p":
        asymmetry = 1.0
    elif model_id == "hill5p":
        try:
            asymmetry = float(params["Asymmetry"])
        except KeyError as exc:
            raise ValueError(
                "FitResult for model 'hill5p' is missing parameter 'Asymmetry'."
            ) from exc
    else:
        raise ValueError(
            f"Back-calculation supports openfit hill4p and hill5p results, got {model_id!r}."
        )

    values = np.asarray([bottom, top, ec50, slope, asymmetry, response], dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError("FitResult parameters and sample response must be finite.")
    if ec50 <= 0.0:
        raise ValueError("FitResult EC50 must be positive for inverse prediction.")
    if slope == 0.0:
        raise ValueError("FitResult HillSlope must be non-zero for inverse prediction.")
    if asymmetry <= 0.0:
        raise ValueError("FitResult Asymmetry must be positive for 5PL inverse prediction.")

    span = top - bottom
    if span == 0.0:
        raise ValueError("FitResult Top and Bottom must differ for inverse prediction.")

    fraction = (response - bottom) / span
    if not 0.0 < fraction < 1.0:
        raise ValueError("response is outside the fitted curve range.")

    if model_id == "hill5p":
        ratio = (1.0 / fraction) ** (1.0 / asymmetry) - 1.0
    else:
        ratio = (1.0 / fraction) - 1.0

    if ratio <= 0.0 or not np.isfinite(ratio):
        raise ValueError("response is outside the fitted curve range.")

    predicted = ec50 / (ratio ** (1.0 / slope))
    if not np.isfinite(predicted) or predicted <= 0.0:
        raise ValueError("Inverse prediction produced a non-finite concentration.")
    return float(predicted)


def back_calculate(
    sample: Sample,
    fit_result: FitResult,
    lloq: float | None = None,
    uloq: float | None = None,
) -> BackCalcResult:
    """Back-calculate sample concentration from observed response.

    Parameters
    ----------
    sample : Sample
        Sample with response and dilution factor.
    fit_result : FitResult
        Fitted standard curve result from openfit.
    lloq : float | None
        Lower limit of quantification.
    uloq : float | None
        Upper limit of quantification.

    Returns
    -------
    BackCalcResult
        Back-calculated concentration with dilution applied and LLOQ/ULOQ flags.

    Raises
    ------
    ValueError
        If sample response is NaN/Inf or inverse prediction fails.
    """
    if not np.isfinite(sample.response):
        raise ValueError(f"Sample response must be finite, got {sample.response}")

    try:
        predicted = _inverse_hill_response(sample.response, fit_result)
    except ValueError as exc:
        raise ValueError(f"Inverse prediction failed for sample {sample.name!r}: {exc}") from exc

    # Apply dilution factor AFTER inverse prediction
    diluted = predicted * sample.dilution_factor
    if not np.isfinite(diluted):
        raise ValueError(f"Diluted concentration is non-finite for sample {sample.name!r}.")

    below_lloq = lloq is not None and diluted < lloq
    above_uloq = uloq is not None and diluted > uloq

    return BackCalcResult(
        sample_name=sample.name,
        predicted_concentration=predicted,
        diluted_concentration=diluted,
        below_lloq=below_lloq,
        above_uloq=above_uloq,
        lloq=lloq,
        uloq=uloq,
    )


def back_calculate_many(
    samples: Iterable[Sample],
    fit_result: FitResult,
    lloq: float | None = None,
    uloq: float | None = None,
) -> list[BackCalcResult]:
    """Back-calculate many samples with the same fitted curve result."""
    return [back_calculate(sample, fit_result, lloq=lloq, uloq=uloq) for sample in samples]
