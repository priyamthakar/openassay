# Validation Evidence

Status: initial v0.1.1 evidence ledger.

openassay uses openfit for fitting-engine correctness. This document records
openassay-specific validation evidence: assay defaults, back-calculation,
dilution, acceptance decisions, reporting, and CLI workflows.

## Current Validation Scope

Covered in the current test suite:

- Standard curves default to `1/y2` weighting.
- `weights=` is passed explicitly to openfit.
- NaN and Inf inputs raise `ValueError`.
- Back-calculation applies dilution after inverse prediction.
- 4PL/5PL inverse prediction uses public `FitResult.model_id` and
  `FitResult.params`, not private openfit attributes.
- Below-LLOQ and above-ULOQ flags are propagated into acceptance decisions.
- Nominal replicate levels compute bias percent and CV percent.
- Acceptance requires both accuracy and precision to pass when nominal
  replicate data are supplied.
- Anchor results are excluded from acceptance decisions.
- HTML and Markdown reports contain the required openassay disclaimer.
- Bundled CSV examples run through the CLI and generate reports.
- A synthetic FDA/ICH M10-style calibration/QC fixture runs through fitting,
  back-calculation, and replicate acceptance checks.

## Synthetic Example Data

The repository includes a small illustrative CSV workflow:

- `examples/data/standards.csv`: five standard-curve points.
- `examples/data/samples.csv`: three unknown samples with dilution factors.

The repository also includes a validation fixture:

- `tests/fixtures/validation/m10_calibration_qc.csv`
- `tests/fixtures/validation/m10_calibration_qc_expected.json`

This fixture is generated from a known 4PL curve:

- Bottom: `1.0`
- Top: `100.0`
- EC50: `5.0`
- HillSlope: `1.2`
- Weighting: `1/y2`

Smoke-test command:

```powershell
python -m pytest tests/test_examples.py
python -m pytest tests/test_validation_fixtures.py
```

Manual CLI commands:

```powershell
python -m openassay.cli fit-curve examples\data\standards.csv --model 4pl --weights 1/y2 --report examples\out\standard_curve.html
python -m openassay.cli backcalc examples\data\samples.csv --curve examples\data\standards.csv --report examples\out\backcalc_report.html
```

## Verification Commands

Run from the repository root:

```powershell
python -m pytest
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src/openassay
python -m build
```

Latest local evidence when this document was added:

- `python -m pytest`: 27 passed.
- `python -m ruff check src tests`: passed.
- `python -m ruff format --check src tests`: passed.
- `python -m mypy src/openassay`: passed.
- `python -m build`: built sdist and wheel.

## External Reference Checks

Not yet added:

- R `drda` / `nplr` cross-checks for shared synthetic 4PL/5PL datasets.
- Stored reference outputs with parameter and back-calculation tolerances.
- External FDA/ICH M10-style reference outputs.

When added, reference checks should store only input data, outputs, tolerances,
software versions, and provenance. Do not copy third-party package source.

## Known Limits

- The current examples are smoke tests, not regulatory validation datasets.
- Acceptance computes per-level bias and CV only when nominal concentrations are
  present on result-like objects.
- Plate layout, replicate collapse, blank subtraction, and batch validation are
  planned for later phases.
- PDF/DOCX report validation is planned for the reports phase.
