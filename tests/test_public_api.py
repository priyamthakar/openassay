"""Tests for docs-facing openassay public API exports."""

from __future__ import annotations

import openassay as oa

FROZEN_PUBLIC_API = [
    "AcceptanceResult",
    "ADAResult",
    "BackCalcResult",
    "BatchCollapsedReplicate",
    "BatchItemResult",
    "BatchResult",
    "CalibrationResult",
    "LevelStats",
    "RangeResult",
    "PlateData",
    "PlateLayout",
    "PlateWell",
    "ParallelismResult",
    "PotencyResult",
    "CollapsedReplicate",
    "Sample",
    "StandardCurve",
    "Well",
    "back_calculate",
    "back_calculate_many",
    "aggregate_collapsed_replicates",
    "confirm_cut_point",
    "fit_standard_curve",
    "determine_lloq_uloq",
    "relative_potency",
    "read_plate",
    "report_run",
    "run_batch",
    "run_acceptance",
    "screen_cut_point",
    "test_parallelism",
]


def test_public_api_all_matches_frozen_v1_surface() -> None:
    """The top-level package exports are the v1.0 public API contract."""
    assert oa.__all__ == FROZEN_PUBLIC_API


def test_public_functional_api_exports() -> None:
    """Functions shown in docs should be importable from openassay."""
    assert callable(oa.fit_standard_curve)
    assert callable(oa.back_calculate)
    assert callable(oa.back_calculate_many)
    assert callable(oa.aggregate_collapsed_replicates)
    assert callable(oa.confirm_cut_point)
    assert callable(oa.determine_lloq_uloq)
    assert callable(oa.relative_potency)
    assert callable(oa.read_plate)
    assert callable(oa.run_acceptance)
    assert callable(oa.screen_cut_point)
    assert callable(oa.test_parallelism)
    assert callable(oa.report_run)
    assert callable(oa.run_batch)
