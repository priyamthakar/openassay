"""Shared types, literals, and default constants for openassay.

This module is intentionally dependency-light: it imports nothing from openfit or
the rest of openassay so it can sit at the bottom of the import graph (see
docs/PROJECT_PLAN.md section 4.2).
"""

from __future__ import annotations

from typing import Literal

# --- openfit model and weighting identifiers (mirror docs/openfit_api_contract.md) ---

Model = Literal["hill4p", "hill5p"]
"""Supported curve model identifiers (openfit model IDs)."""

WeightScheme = Literal["uniform", "1/y", "1/y2", "1/sd2", "poisson"]
"""Accepted openfit weight-scheme strings."""

# --- assay-domain enumerations ---

Role = Literal["standard", "anchor", "qc", "unknown", "blank"]
"""Role a well/sample plays in a run."""

RangeFlag = Literal["in_range", "below_lloq", "above_uloq"]
"""Where a back-calculated result falls relative to the reportable range."""

Decision = Literal["pass", "fail", "not_evaluable"]
"""Outcome of an acceptance or reportability evaluation."""

# --- tuples of allowed values for runtime validation ---

MODELS: tuple[Model, ...] = ("hill4p", "hill5p")
WEIGHT_SCHEMES: tuple[WeightScheme, ...] = (
    "uniform",
    "1/y",
    "1/y2",
    "1/sd2",
    "poisson",
)
ROLES: tuple[Role, ...] = ("standard", "anchor", "qc", "unknown", "blank")

# --- defaults (see docs/concepts.md and PROJECT_PLAN.md) ---

DEFAULT_MODEL: Model = "hill4p"
DEFAULT_WEIGHTS: WeightScheme = "1/y2"
"""Standard curves default to 1/y2 weighting (correctness invariant 1)."""

DEFAULT_CONFIDENCE: float = 0.95
DEFAULT_RANDOM_SEED: int = 0

# Ligand-binding-assay acceptance tolerances (percent).
DEFAULT_ACCURACY_PCT: float = 20.0
DEFAULT_PRECISION_PCT: float = 20.0
# Relaxed tolerance at the range extremes (LLOQ/ULOQ), per the 4-6-X convention.
DEFAULT_EXTREME_ACCURACY_PCT: float = 25.0
DEFAULT_EXTREME_PRECISION_PCT: float = 25.0

# False-positive rates conventionally used for ADA cut points.
DEFAULT_SCREENING_FP_RATE: float = 0.05
DEFAULT_CONFIRMATORY_FP_RATE: float = 0.01

# The disclaimer that must appear in every generated report (invariant 9).
REPORT_DISCLAIMER: str = (
    "This report was generated using openassay (open-source). "
    "Final acceptance decisions and regulatory interpretation should be "
    "reviewed by qualified bioanalytical scientists."
)

__all__ = [
    "Model",
    "WeightScheme",
    "Role",
    "RangeFlag",
    "Decision",
    "MODELS",
    "WEIGHT_SCHEMES",
    "ROLES",
    "DEFAULT_MODEL",
    "DEFAULT_WEIGHTS",
    "DEFAULT_CONFIDENCE",
    "DEFAULT_RANDOM_SEED",
    "DEFAULT_ACCURACY_PCT",
    "DEFAULT_PRECISION_PCT",
    "DEFAULT_EXTREME_ACCURACY_PCT",
    "DEFAULT_EXTREME_PRECISION_PCT",
    "DEFAULT_SCREENING_FP_RATE",
    "DEFAULT_CONFIRMATORY_FP_RATE",
    "REPORT_DISCLAIMER",
]
