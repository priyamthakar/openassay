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

Planning/scaffold stage. See `OPENASSAY_AGENT_LOOP.md` for the implementation
roadmap.

## Non-Goals

- No curve fitting engine internals.
- No GUI.
- No LIMS or plate reader hardware integration.
- No electronic signature or 21 CFR Part 11 record system.
- No PK/PD or LC-MS/MS workflows.

