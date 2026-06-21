# Changelog

All notable changes to openassay are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
(strict from v1.0.0; pre-1.0 minor versions may make additive API changes with a
deprecation shim where practical).

## [Unreleased]

### Added
- `docs/PROJECT_PLAN.md`: end-to-end engineering plan from v0.1.0 to v1.0.0.
- `.gitattributes`: enforce LF line endings to stop spurious CRLF/LF diffs.
- `CHANGELOG.md` and `ROADMAP.md`.
- `docs/concepts.md`: domain glossary (LLOQ/ULOQ, MRD, anchor, %RE, %CV, cut points).
- `src/openassay/types.py`: shared literal types, roles, flags, and default
  thresholds.
- `src/openassay/errors.py`: openassay exception hierarchy (`OpenassayError`
  and subclasses; `NonFiniteDataError` subclasses `ValueError`).
- End-to-end CSV examples for standard-curve fitting and sample back-calculation.
- Closed-form 4PL/5PL back-calculation using public `FitResult.model_id` and
  `FitResult.params` instead of private openfit attributes.
- Functional API wrappers: `fit_standard_curve`, `back_calculate_many`, and
  `report_run`.
- `determine_lloq_uloq` and `RangeResult` for reportable-range decisions from
  accuracy/precision level summaries.
- GitHub Actions CI for pytest, Ruff, mypy, and package build checks across
  Python 3.10-3.12 on Windows, macOS, and Linux.
- Synthetic FDA/ICH M10-style calibration/QC validation fixture.
- Initial 96-well tidy CSV plate reader with duplicate-well and non-finite
  response validation.
- Mean blank subtraction and replicate response collapse for parsed plate data.
- Missing expected-well detection for plate layouts and tidy plate ingestion.
- Matrix-format plate CSV reader using a separate tidy layout map.
- Excel (`.xlsx`/`.xls`) support for tidy and matrix plate readers.
- Roadmap/project-plan status updated for completed v0.1.1/v0.2.0 work and
  v0.3.0 as the next active phase.
- Minimum required dilution (MRD) support in back-calculation, applied after
  inverse prediction alongside sample dilution.
- Reportable range helper can evaluate raw bias/CV level stats with relaxed
  LLOQ/ULOQ extreme tolerances.
- Explicit 10x/100x dilution-linearity regression tests.
- Roadmap/project-plan status updated for completed v0.3.0 work and v0.4.0
  as the next active phase.
- Initial equivalence-based `test_parallelism` and EC50-ratio
  `relative_potency`, with potency suppressed when parallelism fails.
- Stored parallelism/potency reference fixture with hand-computed expected
  ratios and USP <1032>/<1034> conceptual provenance.
- CLI `openassay parallelism` command for JSON fit-result parallelism checks and
  gated relative-potency output.
- Optional covariance-based confidence interval for EC50-ratio relative potency.
- Selectable parallelism method and confidence level passthrough for potency
  estimation and the `openassay parallelism` CLI.
- Explicit 5PL parallelism coverage, including asymmetry-ratio failure.
- Parallel-line relative-potency support from slope equivalence and intercept
  displacement.
- Project plan updated to mark v0.4.0 complete and route the next phase to ADA
  cut-point workflows.
- Initial ADA screening and confirmatory cut-point API with parametric and
  nonparametric methods, plus refusal on insufficient biological variability.
- Explicit ADA outlier handling via opt-in Tukey exclusion with excluded row
  indices recorded in `ADAResult`.
- CLI `openassay ada screen` and `openassay ada confirm` commands for CSV
  cut-point workflows.
- Fixed vs floating ADA cut-point modes, with floating mode reported as a
  run-normalized multiplier.
- Raw or log-transformed ADA cut-point estimation, with log results
  back-transformed to the reporting scale.
- Stored ADA cut-point validation fixture for screening, confirmatory,
  nonparametric, and floating-multiplier outputs.
- Project plan updated to mark v0.5.0 complete and route the next phase to
  384-well and batch-processing work.
- Explicit 384-well plate parsing for tidy and matrix inputs while preserving
  96-well defaults.
- Batch helpers for partial-failure processing and multi-plate collapsed
  replicate aggregation.
- Project plan updated to mark v0.6.0 complete and route the next phase to
  PDF/DOCX report renderers.
- Optional ReportLab PDF and python-docx DOCX run-report renderers with
  `report_run` dispatch and missing-dependency `ReportError` guidance.
- CLI report generation now routes through `report_run`, enabling PDF/DOCX
  report output from existing fit/backcalc commands.
- Missing optional dependency checks now cover both PDF and DOCX report paths.
- Project plan and validation evidence updated to mark v0.7.0 reporting
  complete and route the next phase to v1.0.0 hardening.
- Public roadmap status aligned through v0.7.0, and the top-level v1.0 API
  surface is now pinned by an exact `__all__` regression test.
- Added `docs/api/reference.md` and refreshed the README around the current
  v1.0 API surface.
- Expanded bundled examples to cover plate parsing, parallelism/potency, and
  ADA CLI workflows with smoke-test coverage.
- Validation evidence updated with the current v1.0 hardening gate and full
  runnable example command set.
- CLI `openassay plate parse` command for plate role and replicate summaries.
- `LevelStats` and `AcceptanceResult.level_stats` for per-level %bias and %CV
  acceptance checks from replicate nominal concentrations.
- `tests/test_invariants.py` covering implemented correctness invariants.
- `docs/validation.md`: initial validation evidence ledger and verification
  commands.

### Planned (v0.1.1 hardening, see PROJECT_PLAN.md §9)
- External R/reference-output validation fixtures.

## [0.1.0] - 2026-06-03

### Added
- `StandardCurve` / `CalibrationResult`: 4PL/5PL fitting through openfit with
  default `1/y2` weighting and NaN/Inf rejection.
- `Sample` / `BackCalcResult` / `back_calculate`: inverse prediction with
  dilution applied after inversion and LLOQ/ULOQ flags.
- `AcceptanceResult` / `run_acceptance`: range and finiteness checks.
- HTML and Markdown reports with the mandatory bioanalytical review disclaimer.
- CLI (`openassay version`, `fit-curve`, `backcalc`) behind the `[cli]` extra.

[Unreleased]: https://github.com/priyamthakar/openassay/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/priyamthakar/openassay/releases/tag/v0.1.0
