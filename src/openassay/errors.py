"""openassay exception hierarchy.

openassay never lets a bare lower-level exception escape its public API; it
wraps them with assay context (which sample, which level, what was attempted)
while chaining the original via ``raise ... from exc``.

``NonFiniteDataError`` subclasses ``ValueError`` so the CLAUDE.md contract
("NaN or Inf in input data raises ValueError") holds for callers that catch
``ValueError`` while still allowing finer-grained handling.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


class OpenassayError(Exception):
    """Base class for all openassay-raised errors."""


class DataError(OpenassayError):
    """Malformed, inconsistent, or invalid input data."""


class NonFiniteDataError(DataError, ValueError):
    """Input contains NaN or Inf. openassay never drops or imputes data."""


class PlateLayoutError(DataError):
    """Invalid plate layout: duplicate wells, missing wells, bad addresses."""


class FittingError(OpenassayError):
    """A curve fit failed; wraps the underlying openfit failure with context."""


class InversionError(OpenassayError):
    """Inverse prediction failed (response outside curve range or no convergence)."""


class RangeError(OpenassayError):
    """Reportable-range determination failed (e.g., LLOQ > ULOQ, no valid levels)."""


class AcceptanceError(OpenassayError):
    """Acceptance criteria are misconfigured or cannot be evaluated."""


class ReportError(OpenassayError):
    """Report generation failed, typically a missing optional dependency."""


def require_finite(values: ArrayLike, name: str) -> NDArray[np.float64]:
    """Return ``values`` as a float array, raising if any element is NaN/Inf.

    Parameters
    ----------
    values : array-like
        Data to validate.
    name : str
        Name used in the error message (e.g., ``"x"``, ``"sample response"``).

    Returns
    -------
    numpy.ndarray
        The values as a float64 array.

    Raises
    ------
    NonFiniteDataError
        If any element is NaN or Inf.
    """
    arr = np.asarray(values, dtype=np.float64)
    if not np.isfinite(arr).all():
        raise NonFiniteDataError(
            f"{name} contains NaN or Inf values; openassay does not "
            "drop, impute, or interpolate input data."
        )
    return arr


__all__ = [
    "OpenassayError",
    "DataError",
    "NonFiniteDataError",
    "PlateLayoutError",
    "FittingError",
    "InversionError",
    "RangeError",
    "AcceptanceError",
    "ReportError",
    "require_finite",
]
