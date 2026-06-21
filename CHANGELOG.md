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
