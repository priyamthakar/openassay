"""Tests for docs-facing openassay public API exports."""

from __future__ import annotations

import openassay as oa


def test_public_functional_api_exports() -> None:
    """Functions shown in docs should be importable from openassay."""
    assert callable(oa.fit_standard_curve)
    assert callable(oa.back_calculate)
    assert callable(oa.back_calculate_many)
    assert callable(oa.determine_lloq_uloq)
    assert callable(oa.read_plate)
    assert callable(oa.run_acceptance)
    assert callable(oa.report_run)
