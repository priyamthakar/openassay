"""Back-calculation of unknown sample concentrations."""

from __future__ import annotations

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

    model = fit_result._model
    params = fit_result.params

    # Inverse prediction: find x such that model(x, **params) == response
    # Use scipy.optimize.root_scalar for robust 1D root finding
    import scipy.optimize

    def objective(x: float) -> float:
        # Ensure x is positive for typical assay models
        if x <= 0:
            return np.inf
        return float(model.equation(np.array([x]), **params)[0] - sample.response)

    # Bracket the root: start from a reasonable range based on fit x values
    x_min = float(np.min(fit_result.x)) * 0.1
    x_max = float(np.max(fit_result.x)) * 10.0

    try:
        res = scipy.optimize.root_scalar(objective, bracket=[x_min, x_max], method="brentq")
    except ValueError as exc:
        raise ValueError(
            f"Sample {sample.name!r} response is outside the fitted curve range."
        ) from exc

    if not res.converged:
        raise ValueError(f"Inverse prediction did not converge for sample {sample.name!r}.")

    predicted = float(res.root)
    if not np.isfinite(predicted):
        raise ValueError(f"Inverse prediction produced a non-finite value for {sample.name!r}.")

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
