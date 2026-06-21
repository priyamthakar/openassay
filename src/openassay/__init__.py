"""openassay: Immunoassay and ligand-binding-assay workflow package."""

from __future__ import annotations

__version__ = "1.0.0"

from openassay.acceptance import AcceptanceResult, LevelStats, run_acceptance
from openassay.ada import ADAResult, confirm_cut_point, screen_cut_point
from openassay.backcalc import BackCalcResult, Sample, back_calculate, back_calculate_many
from openassay.batch import (
    BatchCollapsedReplicate,
    BatchItemResult,
    BatchResult,
    aggregate_collapsed_replicates,
    run_batch,
)
from openassay.curve import CalibrationResult, StandardCurve, fit_standard_curve
from openassay.ingest import read_plate
from openassay.parallelism import ParallelismResult, test_parallelism
from openassay.plate import CollapsedReplicate, PlateData, PlateLayout, PlateWell, Well
from openassay.potency import PotencyResult, relative_potency
from openassay.range import RangeResult, determine_lloq_uloq
from openassay.report import report_run

__all__ = [
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
