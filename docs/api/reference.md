# openassay Public API Reference

Status: v1.0 freeze candidate.

The top-level `openassay` package exports the supported public API below. These
names are pinned by `tests/test_public_api.py`; removing or renaming one requires
a deliberate compatibility decision.

## Curve And Back-Calculation

- `StandardCurve`: object-oriented standard-curve fitting entry point.
- `CalibrationResult`: fitted-curve result with openfit result metadata and
  reportable-range fields.
- `fit_standard_curve`: functional standard-curve fitting API.
- `Sample`: sample input for inverse prediction and dilution handling.
- `BackCalcResult`: inverse-prediction output with reported concentration and
  LLOQ/ULOQ flags.
- `back_calculate`: back-calculate one sample from a fitted curve.
- `back_calculate_many`: back-calculate multiple samples using one fitted curve.

## Acceptance And Range

- `AcceptanceResult`: run acceptance decision, reasons, and per-level stats.
- `LevelStats`: per-level bias and precision summary.
- `run_acceptance`: evaluate calibrator/QC or sample-like results.
- `RangeResult`: LLOQ/ULOQ and evaluated-level metadata.
- `determine_lloq_uloq`: determine the validated reportable range from level
  accuracy and precision.

## Plates And Batch Runs

- `Well`: parsed plate-well address.
- `PlateWell`: well plus role, sample identity, concentration, and response.
- `PlateLayout`: validated plate layout.
- `PlateData`: parsed plate responses and replicate-collapse helpers.
- `CollapsedReplicate`: replicate-collapsed plate result.
- `read_plate`: read tidy or matrix CSV/XLSX plate data.
- `BatchItemResult`: one item outcome from batch processing.
- `BatchResult`: aggregate batch outcome with successes and failures.
- `BatchCollapsedReplicate`: collapsed replicate with batch item provenance.
- `run_batch`: run a callable across batch items while preserving partial
  failures.
- `aggregate_collapsed_replicates`: combine collapsed replicate outputs across
  plates or runs.

## Parallelism, Potency, And ADA

- `ParallelismResult`: result from parallel-line or parallel-curve comparison.
- `test_parallelism`: evaluate whether a test preparation is parallel to a
  reference preparation.
- `PotencyResult`: relative-potency estimate and reportability decision.
- `relative_potency`: estimate potency only when parallelism is demonstrated.
- `ADAResult`: screening or confirmatory cut-point result.
- `screen_cut_point`: calculate ADA screening cut points from biological
  variability.
- `confirm_cut_point`: calculate ADA confirmatory cut points.

## Reports

- `report_run`: render HTML, Markdown, PDF, or DOCX run reports from curve,
  back-calculation, and acceptance results.

