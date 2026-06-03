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

v0.1.0 implementation branch. Current scope includes standard-curve fitting,
sample back-calculation, basic LLOQ/ULOQ range checks, HTML/Markdown reports,
and CLI entry points. See `OPENASSAY_AGENT_LOOP.md` for the future roadmap.

## Current API

- `StandardCurve(x, y, model="hill4p", weights="1/y2")` fits 4PL/5PL curves
  through openfit. Inputs with NaN or Inf are rejected.
- `back_calculate(sample, fit_result, lloq=None, uloq=None)` performs inverse
  prediction and applies dilution after inversion. Responses outside the fitted
  curve range raise `ValueError` rather than returning a non-finite result.
- `run_acceptance(results)` fails samples outside LLOQ/ULOQ and defensively
  fails any non-finite predicted or diluted concentration.
- HTML and Markdown reports include the qualified bioanalytical-scientist
  review disclaimer.

## Non-Goals

- No curve fitting engine internals.
- No GUI.
- No LIMS or plate reader hardware integration.
- No electronic signature or 21 CFR Part 11 record system.
- No PK/PD or LC-MS/MS workflows.

