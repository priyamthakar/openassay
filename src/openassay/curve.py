"""Standard curve fitting and calibration results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from openfit import Fit, FitResult


@dataclass
class CalibrationResult:
    """Result of a standard curve calibration."""

    fit_result: FitResult
    lloq: float | None = None
    uloq: float | None = None
    reportable_range: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        if self.lloq is not None and self.uloq is not None:
            self.reportable_range = (self.lloq, self.uloq)


class StandardCurve:
    """Standard curve for 4PL/5PL assays."""

    def __init__(
        self,
        x: Any,
        y: Any,
        model: str = "hill4p",
        weights: str = "1/y2",
        **fit_kwargs: Any,
    ) -> None:
        """Initialize a StandardCurve.

        Parameters
        ----------
        x : array-like
            Standard concentrations.
        y : array-like
            Observed responses.
        model : str
            Model identifier, "hill4p" or "hill5p".
        weights : str
            Weight scheme. Defaults to "1/y2". Must be explicit.
        **fit_kwargs : Any
            Additional arguments passed to openfit.Fit.
        """
        x_arr = np.asarray(x, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.float64)

        if not np.isfinite(x_arr).all():
            raise ValueError("x contains NaN or Inf values.")
        if not np.isfinite(y_arr).all():
            raise ValueError("y contains NaN or Inf values.")

        if weights not in ("uniform", "1/y", "1/y2", "1/sd2", "poisson"):
            raise ValueError(
                f"Invalid weights: {weights}. Must be one of "
                "'uniform', '1/y', '1/y2', '1/sd2', 'poisson'."
            )

        self._x = x_arr
        self._y = y_arr
        self._model = model
        self._weights = weights
        self._fit_kwargs = fit_kwargs
        self._fit_result: FitResult | None = None

    def fit(self) -> CalibrationResult:
        """Fit the standard curve."""
        fit_obj = Fit(
            model=self._model,
            x=self._x,
            y=self._y,
            weights=self._weights,
            **self._fit_kwargs,
        )
        self._fit_result = fit_obj.run()
        return CalibrationResult(fit_result=self._fit_result)

    @property
    def fit_result(self) -> FitResult | None:
        """Return the underlying FitResult if fitted."""
        return self._fit_result
