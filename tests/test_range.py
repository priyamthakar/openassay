"""Tests for reportable range decisions."""

from __future__ import annotations

from types import SimpleNamespace

from openassay.range import RangeResult, determine_lloq_uloq


def level(
    nominal: float,
    *,
    accuracy_pass: bool = True,
    precision_pass: bool = True,
    is_anchor: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        nominal_concentration=nominal,
        accuracy_pass=accuracy_pass,
        precision_pass=precision_pass,
        is_anchor=is_anchor,
    )


def test_determine_lloq_uloq_requires_accuracy_and_precision() -> None:
    """Only levels passing both checks should define the range."""
    result = determine_lloq_uloq(
        [
            level(0.1, accuracy_pass=False, precision_pass=True),
            level(0.3),
            level(1.0, accuracy_pass=True, precision_pass=False),
            level(10.0),
        ]
    )

    assert isinstance(result, RangeResult)
    assert result.reportable_range == (0.3, 0.3)
    assert result.passing_levels == [0.3, 10.0]


def test_determine_lloq_uloq_excludes_anchor_levels() -> None:
    """Anchors should not define LLOQ or ULOQ even if they pass."""
    result = determine_lloq_uloq(
        [
            level(0.03, is_anchor=True),
            level(0.1),
            level(1.0),
            level(10.0, is_anchor=True),
        ]
    )

    assert result.reportable_range == (0.1, 1.0)
    assert result.excluded_anchor_levels == [0.03, 10.0]


def test_determine_lloq_uloq_returns_none_when_no_levels_pass() -> None:
    """No passing non-anchor levels means no validated reportable range."""
    result = determine_lloq_uloq(
        [
            level(0.1, accuracy_pass=False),
            level(1.0, precision_pass=False),
        ]
    )

    assert result.lloq is None
    assert result.uloq is None
    assert result.reportable_range is None
