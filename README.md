# openassay

openassay is a Python package for immunoassay and ligand-binding-assay workflows:
standard curves, back-calculation, LLOQ/ULOQ, acceptance criteria, plate workflows,
relative potency, ADA cut points, and regulatory-style reports.

## Boundary

openassay depends on [openfit](https://github.com/priyamthakar/openfit) for
nonlinear curve fitting. It does not copy or reimplement openfit fitting logic.

- openfit: domain-agnostic curve fitting engine.
- openassay: assay-domain workflow logic built on top of openfit.

If a feature is about optimization, model equations, covariance, fitting reports,
or generic nonlinear regression, it probably belongs in openfit. If it is about
calibrators, QCs, LLOQ/ULOQ, dilution factors, plate layouts, ADA cut points, or
bioanalytical acceptance, it belongs in openassay.

## Status

v1.0.0 release candidate. Current scope includes standard-curve fitting,
sample back-calculation, LLOQ/ULOQ range decisions, calibrator/QC acceptance,
plate parsing, batch helpers, relative potency, ADA cut points, HTML/Markdown/
PDF/DOCX reports, and CLI entry points. See `ROADMAP.md` and
`docs/PROJECT_PLAN.md` for the release plan.

## Current API

- `StandardCurve(x, y, model="hill4p", weights="1/y2")` and
  `fit_standard_curve(...)` fit 4PL/5PL curves
  through openfit. Inputs with NaN or Inf are rejected.
- `back_calculate(sample, fit_result, lloq=None, uloq=None)` performs inverse
  prediction and applies dilution after inversion. Responses outside the fitted
  curve range raise `ValueError` rather than returning a non-finite result.
- `determine_lloq_uloq(...)` and `run_acceptance(...)` require accuracy and
  precision together for reportable-range and run decisions.
- `read_plate(...)` reads tidy or matrix CSV/XLSX plate data for 96- and
  384-well plates.
- `test_parallelism(...)` and `relative_potency(...)` gate potency reporting on
  demonstrated parallelism.
- `screen_cut_point(...)` and `confirm_cut_point(...)` calculate ADA cut points
  from biological variability.
- `report_run(...)` writes HTML, Markdown, PDF, or DOCX reports with the
  qualified bioanalytical-scientist review disclaimer.

The frozen top-level API candidate is documented in `docs/api/reference.md`.

## Non-Goals

- No curve fitting engine internals.
- No GUI.
- No LIMS or plate reader hardware integration.
- No electronic signature or 21 CFR Part 11 record system.
- No PK/PD or LC-MS/MS workflows.
