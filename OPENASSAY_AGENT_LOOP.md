# OPENASSAY_AGENT_LOOP.md

## Mission

Build `openassay` as a Python 3.10+ immunoassay and ligand-binding-assay workflow
package.

- Repository: `https://github.com/priyamthakar/openassay`
- Package/import name: `openassay`
- Dependency: `openfit`
- Local sibling engine repo: `D:\openfit`
- Style: library-first, CLI-second, no GUI

openassay imports openfit for all curve fitting. It must not copy or reimplement
openfit fitting internals.

## Ground Rules

- Standard curves default to `1/y2` weighting.
- Uniform weighting must be explicit.
- Back-calculated concentrations apply dilution after inverse prediction.
- LLOQ and ULOQ require accuracy and precision.
- Anchor points are included in fitting but excluded from acceptance and
  reportable range decisions.
- Relative potency is not reportable if parallelism fails.
- ADA cut points must use multi-sample biological variability, not a single-run
  default.
- Generated reports include this disclaimer:

> This report was generated using openassay (open-source). Final acceptance decisions and regulatory interpretation should be reviewed by qualified bioanalytical scientists.

## Project Setup

- Keep `CLAUDE.md` openassay-specific. Do not reintroduce openfit guidance or the
  old openassayflow identity.
- Add `pyproject.toml`, `CHANGELOG.md`, `ROADMAP.md`, `src/openassay`, `tests`,
  `examples`, `docs`, and GitHub Actions CI.
- Configure hatchling, ruff, mypy, pytest, and package metadata.
- Core deps: `openfit`, `numpy`, `pandas`, `pydantic`.
- Optional deps: `[cli] typer rich`, `[reports] jinja2 reportlab python-docx`,
  `[dev] pytest pytest-cov ruff mypy build twine`.
- Before fitting-dependent code, inspect `D:\openfit` and write
  `docs/openfit_api_contract.md`.

## Release Loop

### v0.1.0 - Standard Curves, Back-Calculation, Acceptance, HTML

- Implement `curve`: `StandardCurve`, `CalibrationResult`, 4PL/5PL fitting
  through openfit, default `weights="1/y2"`, explicit opt-in for `uniform`.
- Implement `backcalc`: inverse concentration prediction, dilution factor after
  back-calculation, below-LLOQ and above-ULOQ flags.
- Implement `acceptance`: calibrator and QC acceptance criteria, LLOQ/ULOQ, and
  structured pass/fail results.
- Implement HTML and Markdown reports with curve plot, tables, FitSpec, and
  disclaimer.
- Gate: public API unit tests, synthetic 4PL/5PL sanity tests, one end-to-end CSV
  example.

### v0.1.1 - Validation Evidence

- Add validation fixtures for FDA/ICH M10-style calibration and QC scenarios.
- Cross-check 4PL/5PL behavior against R `drda` and R `nplr` when feasible.
- Store reference outputs and provenance only; do not copy R source.
- Add `docs/validation.md`.
- Gate: validation tests, full pytest, ruff, mypy.

### v0.2.0 - Plate Layouts

- Implement 96-well layout model, standards/QCs/unknowns/blanks, replicate
  grouping, blank subtraction, and CSV/Excel import.
- Support tidy long-format input and matrix plate-format input.
- Add CLI plate parsing support.
- Gate: tests for well addressing, duplicate wells, missing wells, blanks, and
  replicate collapse.

### v0.3.0 - LLOQ/ULOQ And Dilution

- Determine validated range from accuracy and precision together.
- Add MRD/minimum required dilution handling.
- Ensure anchors are excluded from acceptance and reportable range decisions.
- Gate: anchor tests, LLOQ/ULOQ failure cases, and 10x/100x dilution checks.

### v0.4.0 - Parallelism And Relative Potency

- Implement parallel-line and parallel-curve workflows using openfit where
  appropriate.
- Implement relative potency with potency not estimable when parallelism fails.
- Cite USP <1032>/<1034> without reproducing paywalled text.
- Gate: synthetic parallel/non-parallel fixtures and at least one reference check.

### v0.5.0 - ADA Cut Points

- Implement screening and confirmatory cut point workflows.
- Support parametric and non-parametric options and documented outlier handling.
- Require biological variability across samples/runs; no single-run default.
- Gate: tests based on Shankar et al. 2008-style scenarios and FDA/EMA guidance.

### v0.6.0 - 384-Well And Batch Processing

- Extend plate support to 384 wells.
- Add batch processing for multiple plates/runs.
- Gate: 96/384 compatibility, multi-plate aggregation, partial failure reporting.

### v0.7.0 - PDF/DOCX Reports

- Add ReportLab PDF and python-docx renderers behind `[reports]`.
- Keep core install functional without optional report deps.
- Gate: generated HTML/PDF/DOCX smoke tests and missing-dependency tests.

### v1.0.0 - Stable Release

- Freeze public APIs, complete docs/examples, align README/CHANGELOG/ROADMAP.
- CI green on Windows, macOS, Linux and Python 3.10-3.12.
- Gate: `python -m build`, `twine check dist/*`, full tests, ruff, mypy.

## Public API Targets

- Dataclasses: `StandardCurve`, `CalibrationResult`, `BackCalcResult`,
  `AcceptanceResult`, `PlateLayout`, `PlateData`, `SampleResult`, `RunReport`,
  `ParallelismResult`, `PotencyResult`, `ADAResult`.
- Functions: `fit_standard_curve`, `back_calculate`, `run_acceptance`,
  `determine_lloq_uloq`, `read_plate`, `test_parallelism`, `relative_potency`,
  `screen_cut_point`, `confirm_cut_point`, `report_run`.
- CLI: `openassay version`, `fit-curve`, `backcalc`, `validate-run`, `plate`,
  `parallelism`, `ada`, `report`.

## Validation References

- FDA Bioanalytical Method Validation Guidance for Industry, May 2018.
- FDA/ICH M10 Bioanalytical Method Validation and Study Sample Analysis, Nov 2022.
- FDA Immunogenicity Testing of Therapeutic Protein Products, 2019.
- EMA Immunogenicity Assessment Guideline, effective Dec 2017.
- Shankar et al. 2008 for ADA cut points.
- USP <1032>/<1034> for parallelism and relative potency concepts.
- openfit validation for fitting-engine correctness.

## Agent Loop Instructions

- Work one release phase at a time.
- Start from a branch or worktree, not `master`.
- Before changes: inspect repo, read this file, and check `git status`.
- After each small feature: run relevant tests.
- Before commit, when package files exist, run:

```powershell
python -m pytest
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src/openassay
```

- Commit with clear conventional messages.
- Never use `--no-verify`.
- Never force-push.
- Never overwrite unrelated user changes.
- If blocked, write a checkpoint in `HANDOFF.md`.

## Assumptions

- Package identity is `openassay`, not `openassayflow`.
- openfit remains separate at `D:\openfit` and is consumed as a dependency only.
- This repo owns assay workflow logic, not fitting-engine logic.

