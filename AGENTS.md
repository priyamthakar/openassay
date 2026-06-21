# AGENTS.md -- openassay

This file provides guidance to agents working in the openassay repository.

## Scope And Boundary

openassay is a Python package for immunoassay and ligand-binding-assay workflows.
It adds assay-domain logic on top of openfit.

In scope:
- Standard curves for 4PL/5PL assays through openfit.
- Back-calculation of unknown sample concentrations.
- LLOQ/ULOQ and reportable range handling.
- Calibrator and QC acceptance criteria.
- Plate layouts, blank subtraction, replicate collapse, and batch runs.
- Relative potency and parallelism workflows.
- ADA screening and confirmatory cut point workflows.
- Bioanalytical run reports.

Out of scope:
- Curve fitting engine internals. Those belong in openfit.
- Plate reader hardware drivers or instrument communication.
- LIMS integration, barcode workflows, and sample tracking systems.
- LC-MS/MS bioanalytical methods.
- Electronic signatures, 21 CFR Part 11 audit trails, or regulated record systems.
- GUI, desktop, or web apps.
- PK/PD calculations, NCA, or simulations.

## Identity

- Package: `openassay`
- Import name: `openassay`
- Repository: `https://github.com/priyamthakar/openassay`
- Dependency: `openfit`
- Python: 3.10+
- Build: hatchling with `src/` layout

Do not rename this project to `openassayflow`. If older notes mention
openassayflow, migrate the useful domain guidance to openassay naming.

## Relationship To openfit

openfit is the domain-agnostic nonlinear curve fitting engine. openassay imports
openfit and never copies its fitting logic.

Use openfit for:
- 4PL/5PL fitting.
- Weighted least-squares optimization.
- FitResult and FitSpec reproducibility metadata.
- Fitting reports or plots when they are generic enough.

Use openassay for:
- Assay-specific defaults such as `1/y2` standard curve weighting.
- Back-calculation and dilution handling.
- LBA acceptance criteria.
- LLOQ/ULOQ and reportable range decisions.
- Regulatory-style assay run reporting.

Before writing fitting-dependent code, inspect the local openfit source at
`D:\openfit` and record any required API assumptions in
`docs/openfit_api_contract.md`.

## Correctness Rules

1. Standard curves default to `1/y2` weighting. Uniform weighting must be an
   explicit user choice.
2. openassay must always pass `weights=` explicitly to openfit.
3. NaN or Inf in input data raises `ValueError`; never drop or interpolate data.
4. Back-calculated concentrations apply dilution factors after inverse prediction.
5. LLOQ and ULOQ require both accuracy and precision to pass.
6. Anchor standards may be included in fitting but are excluded from acceptance
   and reportable range decisions.
7. Relative potency is not reportable if parallelism is not demonstrated.
8. ADA cut points must account for biological variability; do not default to a
   single-run SD.
9. Reports must include this disclaimer:

> This report was generated using openassay (open-source). Final acceptance decisions and regulatory interpretation should be reviewed by qualified bioanalytical scientists.

## Commands

After the package is scaffolded:

```powershell
pip install -e ".[dev]"
python -m pytest
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src/openassay
python -m build
```

CLI targets:

```powershell
openassay version
openassay fit-curve plate_data.csv --model 4pl --weights 1/y2 --report run_report.html
openassay backcalc plate_data.csv --curve standards.json --report results.html
```

## Agent Workflow

- Work on branches or worktrees, not directly on `master`.
- Read `OPENASSAY_AGENT_LOOP.md` before starting implementation.
- Keep changes phase-scoped and commit only after relevant checks pass.
- Never use `--no-verify`.
- Never force-push.
- Never overwrite unrelated user changes.
- If blocked, write a concrete `HANDOFF.md` with exact resume commands.

Recommended isolated worktree pattern:

```powershell
git -C D:\openassay worktree add D:\worktrees\openassay-agent -b agent/openassay-v001
```

