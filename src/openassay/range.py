"""Reportable range helpers for LLOQ/ULOQ decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RangeResult:
    """Validated reportable range derived from passing concentration levels."""

    lloq: float | None
    uloq: float | None
    reportable_range: tuple[float, float] | None
    evaluated_levels: list[float]
    passing_levels: list[float]
    excluded_anchor_levels: list[float]


def _level_nominal(level: Any) -> float:
    if hasattr(level, "nominal_concentration"):
        return float(level.nominal_concentration)
    if hasattr(level, "nominal"):
        return float(level.nominal)
    raise ValueError("Level is missing nominal_concentration.")


def _level_passes(level: Any) -> bool:
    return bool(level.accuracy_pass and level.precision_pass)


def _is_anchor(level: Any) -> bool:
    return bool(getattr(level, "is_anchor", False))


def _longest_contiguous_span(
    evaluated_levels: list[float], passing_levels: list[float]
) -> list[float]:
    if not evaluated_levels or not passing_levels:
        return []

    unique = sorted(set(evaluated_levels))
    passing = set(passing_levels)
    best: list[float] = []
    current: list[float] = []

    for level in unique:
        if level in passing:
            current.append(level)
        else:
            if len(current) > len(best):
                best = current
            current = []

    if len(current) > len(best):
        best = current
    return best


def determine_lloq_uloq(levels: list[Any]) -> RangeResult:
    """Determine LLOQ and ULOQ from levels passing accuracy and precision."""
    evaluated_levels: list[float] = []
    passing_levels: list[float] = []
    excluded_anchor_levels: list[float] = []

    for level in levels:
        nominal = _level_nominal(level)
        if _is_anchor(level):
            excluded_anchor_levels.append(nominal)
            continue
        evaluated_levels.append(nominal)
        if _level_passes(level):
            passing_levels.append(nominal)

    span = _longest_contiguous_span(evaluated_levels, passing_levels)
    if not span:
        return RangeResult(
            lloq=None,
            uloq=None,
            reportable_range=None,
            evaluated_levels=sorted(evaluated_levels),
            passing_levels=sorted(passing_levels),
            excluded_anchor_levels=sorted(excluded_anchor_levels),
        )

    lloq = min(span)
    uloq = max(span)
    return RangeResult(
        lloq=lloq,
        uloq=uloq,
        reportable_range=(lloq, uloq),
        evaluated_levels=sorted(evaluated_levels),
        passing_levels=sorted(passing_levels),
        excluded_anchor_levels=sorted(excluded_anchor_levels),
    )
