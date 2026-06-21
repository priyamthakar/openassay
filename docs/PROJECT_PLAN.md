# openassay — End-to-End Project Plan

Status of this document: master plan for openassay from the current `v0.1.0`
implementation through `v1.0.0` stable release. It is the engineering companion
to `OPENASSAY_AGENT_LOOP.md` (the release loop) and `CLAUDE.md` (the scope and
correctness rules). Where the three documents overlap, `CLAUDE.md` wins on
correctness rules, `OPENASSAY_AGENT_LOOP.md` wins on phase ordering, and this
document owns the detailed design, data model, algorithms, and test strategy.

Last updated: 2026-06-21.

---

## 1. Product Thesis And Boundary

### 1.1 What openassay is

openassay is the **applied assay-workflow product**: the layer a bioanalytical
scientist actually drives. It turns raw plate readouts into reportable
concentrations and regulatory-style run decisions. It owns assay-domain logic:
calibrators, QCs, unknowns, blanks, dilution, LLOQ/ULOQ, reportable range,
parallelism, relative potency, ADA cut points, and run reports.

openfit is the **domain-agnostic fitting/statistics engine**: 4PL/5PL model
equations, weighted least squares, covariance, confidence intervals, and
`FitResult`/`FitSpec` reproducibility metadata. openassay consumes it and never
reimplements it.

### 1.2 The boundary, stated as a decision rule

When deciding where a feature belongs, ask: *"Is this true of any nonlinear
regression problem, or only of immunoassays?"*

- Optimization, model equations, covariance, generic goodness-of-fit, generic
  fitting plots/reports → **openfit**.
- Calibrators/QCs/unknowns, dilution factors, MRD, plate layouts, LLOQ/ULOQ as
  an accuracy+precision decision, anchor handling, parallelism acceptance,
  relative potency reportability, ADA cut points, bioanalytical run reports →
  **openassay**.

This rule is repeated in `README.md` and `CLAUDE.md`. Any PR that blurs it must
justify itself against this sentence.

### 1.3 Hard out-of-scope list (never build here)

Fitting-engine internals; plate-reader hardware drivers/instrument comms; LIMS,
barcode, and sample-tracking integrations; LC-MS/MS methods; electronic
signatures, 21 CFR Part 11 audit trails, or regulated record systems; GUI,
desktop, or web apps; PK/PD, NCA, or simulations. These belong to other systems.
openassay produces analysis artifacts that such systems can consume.

---

## 2. The Nine Correctness Invariants (binding)

These are lifted verbatim in intent from `CLAUDE.md` and are the acceptance
backbone of every phase. Each invariant below names the module(s) that must
enforce it and the test(s) that must prove it.

1. **Default `1/y2` weighting.** Standard curves weight `1/y2` by default;
   uniform weighting is an explicit opt-in. Enforced in `curve`. Test:
   constructing a curve without `weights` yields `weight_scheme == "1/y2"`.
2. **Explicit weights to openfit.** openassay always passes `weights=` to
   `openfit.Fit`; it never relies on an openfit default. Enforced in `curve`.
   Test: a spy/fake openfit records that `weights` was passed.
3. **No silent data repair.** NaN/Inf anywhere in input data raises
   `ValueError`. Never drop, impute, or interpolate. Enforced in every ingestion
   and fitting entry point. Test: NaN in x, y, sd, or sample response raises.
4. **Dilution after inversion.** Back-calculation applies the dilution factor
   *after* inverse prediction (`reported = predicted * dilution_factor`).
   Enforced in `backcalc`. Test: a 10x sample reports 10x its on-curve value.
5. **LLOQ/ULOQ need accuracy and precision.** A level qualifies as LLOQ/ULOQ
   only if it passes *both* accuracy and precision. Enforced in `acceptance` /
   `range`. Test: a level that passes accuracy but fails precision is rejected,
   and vice versa.
6. **Anchors fit, but do not judge.** Anchor standards may be included in the
   fit but are excluded from acceptance and reportable-range decisions. Enforced
   in `curve` (flagging) + `acceptance`/`range` (filtering). Test: an anchor
   point with bad recovery does not fail the run and does not set the range.
7. **Potency requires parallelism.** Relative potency is not reportable unless
   parallelism is demonstrated. Enforced in `potency`. Test: non-parallel
   fixture returns `reportable=False` and no point estimate.
8. **ADA cut points use biological variability.** Cut points must use
   across-sample/across-run variability, never a single-run SD default. Enforced
   in `ada`. Test: a single run with no biological replication refuses to emit a
   cut point.
9. **Mandatory report disclaimer.** Every generated report contains, verbatim:

   > This report was generated using openassay (open-source). Final acceptance
   > decisions and regulatory interpretation should be reviewed by qualified
   > bioanalytical scientists.

   Enforced in `report`. Test: rendered HTML/MD/PDF/DOCX each contain the exact
   string.

A shared test module (`tests/test_invariants.py`, introduced in v0.1.1) will
assert all nine against representative objects so they cannot silently regress.

---

## 3. Current State (v0.1.0) — Honest Snapshot

What exists on `master` today:

- `curve.StandardCurve` (class) + `CalibrationResult`, fitting via
  `openfit.Fit(...).run()`, default `weights="1/y2"`, NaN/Inf rejection, weight
  whitelist validation.
- `backcalc.Sample`, `BackCalcResult`, `back_calculate(...)` using
  `scipy.optimize.root_scalar` (brentq) against `fit_result._model.equation`,
  dilution applied after inversion, below/above LLOQ/ULOQ flags.
- `acceptance.AcceptanceResult`, `run_acceptance(...)` (range + non-finite
  guards; accuracy/precision thresholds are parameters but not yet computed
  from replicates).
- `report.generate_html_report` / `generate_markdown_report` with the
  disclaimer.
- `cli` (typer, optional) with `version`, `fit-curve`, `backcalc`.
- Tests for curve/backcalc/acceptance/report. CRLF line endings differ from
  HEAD's LF (cosmetic only).

Gaps vs. the agent loop's **Public API Targets** that this plan will close:

- Target functional API (`fit_standard_curve`, `determine_lloq_uloq`,
  `read_plate`, `test_parallelism`, `relative_potency`, `screen_cut_point`,
  `confirm_cut_point`, `report_run`) is not yet present; current API is
  class-first (`StandardCurve`) + ad hoc report functions.
- `backcalc` reaches into `fit_result._model` (a private openfit attribute).
  This must be replaced with a public inverse-prediction path (see §6.4).
- `acceptance.run_acceptance` does not yet compute accuracy (%RE/%bias) or
  precision (%CV) from replicate calibrators/QCs; it only checks range and
  finiteness.
- No pydantic models, no `pandas` ingestion layer, no plate model, no
  `CHANGELOG.md`, `ROADMAP.md`, `examples/`, or CI — all required by the loop.
- openfit is not installable in every environment; tests must run against a
  pinned real openfit or a contract-faithful fake (see §10.3).

§13 defines the API-convergence refactor that reconciles current code with the
targets without breaking the v0.1.0 surface prematurely.

---

## 4. Target Architecture And Package Layout

```
openassay/
├── pyproject.toml            # hatchling, src-layout, deps + extras
├── README.md
├── CHANGELOG.md              # Keep a Changelog format (add in v0.1.1)
├── ROADMAP.md                # condensed public roadmap (add in v0.1.1)
├── CLAUDE.md
├── OPENASSAY_AGENT_LOOP.md
├── docs/
│   ├── PROJECT_PLAN.md       # this file
│   ├── openfit_api_contract.md
│   ├── validation.md         # v0.1.1
│   ├── concepts.md           # domain glossary (LLOQ, MRD, anchor, ...)
│   └── api/                  # generated API reference (v1.0.0)
├── examples/
│   ├── data/                 # synthetic CSV/XLSX fixtures
│   └── *.py / *.md           # runnable end-to-end walkthroughs
├── src/openassay/
│   ├── __init__.py           # curated public API + __version__
│   ├── types.py              # enums, type aliases, shared constants
│   ├── models.py             # pydantic models / dataclasses (data model)
│   ├── errors.py             # exception hierarchy
│   ├── units.py              # unit/label handling (no conversion engine)
│   ├── ingest.py             # CSV/Excel + tidy/matrix readers (v0.2.0)
│   ├── plate.py              # PlateLayout, PlateData, well addressing (v0.2.0)
│   ├── curve.py              # StandardCurve, fit_standard_curve
│   ├── backcalc.py           # inverse prediction + dilution
│   ├── range.py              # LLOQ/ULOQ, reportable range, MRD (v0.3.0)
│   ├── acceptance.py         # calibrator/QC acceptance, run rules
│   ├── parallelism.py        # parallel-line/curve tests (v0.4.0)
│   ├── potency.py            # relative potency (v0.4.0)
│   ├── ada.py                # screening/confirmatory cut points (v0.5.0)
│   ├── batch.py              # multi-plate/run aggregation (v0.6.0)
│   ├── report/
│   │   ├── __init__.py
│   │   ├── model.py          # RunReport assembly (data → report struct)
│   │   ├── html.py
│   │   ├── markdown.py
│   │   ├── pdf.py            # v0.7.0, behind [reports]
│   │   ├── docx.py           # v0.7.0, behind [reports]
│   │   └── templates/        # jinja2 templates
│   └── cli.py                # typer app
└── tests/
    ├── conftest.py           # fixtures, fake-openfit toggle
    ├── fakes/openfit_fake.py # contract-faithful fake engine
    ├── fixtures/             # synthetic + validation datasets
    ├── test_invariants.py    # the nine rules
    └── test_*.py             # per-module
```

### 4.1 Dependency tiers

- **Core** (always installed): `openfit`, `numpy`, `pandas`, `pydantic`,
  `scipy` (used by `backcalc` inversion and stats; add to core deps — it is a
  hidden dependency today).
- **`[cli]`**: `typer`, `rich`.
- **`[reports]`**: `jinja2` (HTML/MD), `reportlab` (PDF), `python-docx` (DOCX),
  plus a headless plotting path for the curve plot (matplotlib, optional within
  reports). Core install must stay functional with reports absent.
- **`[dev]`**: `pytest`, `pytest-cov`, `ruff`, `mypy`, `build`, `twine`,
  `hypothesis` (property tests).

### 4.2 Layering rules

`types`/`errors`/`units` depend on nothing internal. `models` depends on those.
`curve`/`backcalc` depend on `models` + openfit. `range`/`acceptance` depend on
`curve`/`backcalc`/`models`. `parallelism`/`potency`/`ada`/`batch` are
higher-level. `report` and `cli` are top of the stack and depend downward only.
No upward imports; no cycles. `mypy --strict` and an import-linter contract
(added in v0.6.0) enforce this.

---

## 5. Domain Data Model

All public result objects are immutable-by-convention dataclasses or pydantic
models with explicit units and provenance. Every result that drives a decision
carries enough metadata to reconstruct it.

### 5.1 Shared types (`types.py`)

- `Model = Literal["hill4p", "hill5p"]` (openfit model IDs).
- `WeightScheme = Literal["uniform", "1/y", "1/y2", "1/sd2", "poisson"]`.
- `Role = Literal["standard", "anchor", "qc", "unknown", "blank"]`.
- `RangeFlag = Literal["in_range", "below_lloq", "above_uloq"]`.
- `Decision = Literal["pass", "fail", "not_evaluable"]`.
- Constants: default thresholds (LBA `±20%` accuracy/precision, `±25%` at LLOQ
  per the 4-6-X convention), default `confidence=0.95`.

### 5.2 Core models (`models.py`)

- `CalibrationResult`: wraps openfit `FitResult`; adds `model`, `weight_scheme`,
  per-level `recovery` (%RE), `is_anchor` mask, `lloq`, `uloq`,
  `reportable_range`, and the `FitSpec` for reproducibility.
- `Sample`: `name`, `response`, `dilution_factor=1.0`, `nominal=None`
  (for QCs/calibrators), `role`, `replicate_id`, `well` (optional).
- `BackCalcResult`: `sample_name`, `predicted_concentration`,
  `reported_concentration` (dilution applied), `dilution_factor`, `range_flag`,
  `lloq`, `uloq`, plus `percent_recovery` when `nominal` is known.
- `LevelStats`: per-nominal-level aggregate — `nominal`, `n`, `mean`,
  `sd`, `cv_percent`, `bias_percent` (mean recovery − 100), `accuracy_pass`,
  `precision_pass`, `total_error_percent`.
- `AcceptanceResult`: `decision`, per-level `LevelStats`, applied thresholds,
  `passed_levels`, `failed_levels`, human-readable `reasons`.
- `RangeResult`: `lloq`, `uloq`, `reportable_range`, the levels evaluated, and
  which were excluded as anchors.
- `PlateLayout` / `PlateData`: §8 (v0.2.0).
- `ParallelismResult`, `PotencyResult`, `ADAResult`: §8 (later phases).
- `RunReport`: the assembled object a renderer consumes — curve, samples,
  acceptance, range, environment/provenance, disclaimer.

### 5.3 Provenance block (every result)

A `Provenance` model is embedded in `RunReport` and `CalibrationResult`:
openassay version, openfit version, `FitSpec` hash, input file digests
(SHA-256), timestamp (UTC, ISO-8601), and the random seed. This makes any
reported number reproducible and is the foundation for `docs/validation.md`.

### 5.4 Error hierarchy (`errors.py`)

```
OpenassayError (base)
├── DataError              # malformed/NaN/Inf/duplicate-well input
│   ├── NonFiniteDataError
│   └── PlateLayoutError
├── FittingError           # wraps/contextualizes openfit failures
├── InversionError         # response outside curve range, no convergence
├── RangeError             # LLOQ>ULOQ, no qualifying levels
├── AcceptanceError        # misconfigured thresholds
└── ReportError            # missing optional report dependency
```

Rule: openassay never lets a bare openfit/scipy exception escape its public API;
it wraps with context (which sample, which level, what was attempted) while
chaining `from exc`. NaN/Inf always raise `NonFiniteDataError` (a `ValueError`
subclass, preserving the `CLAUDE.md` "raises `ValueError`" contract).

---

## 6. Public API Contract (target, stable by v1.0.0)

Functional API is primary; classes back it. Both are kept; the functions are the
documented surface.

### 6.1 Curve

```python
def fit_standard_curve(
    x, y, *,
    model: Model = "hill4p",
    weights: WeightScheme = "1/y2",
    sd=None,
    anchors=None,            # bool mask or indices: fit-only points
    confidence: float = 0.95,
    random_seed: int = 0,
    **fit_kwargs,
) -> CalibrationResult
```

Semantics: validates finiteness (invariant 3), requires explicit weight value
that defaults to `1/y2` (invariants 1–2), forwards `weights=` to `openfit.Fit`
(invariant 2), records anchors but keeps them in the fit (invariant 6).
`StandardCurve` remains as the OO entry point and delegates to this function.

### 6.2 Back-calculation

```python
def back_calculate(
    sample: Sample, curve: CalibrationResult, *,
    lloq=None, uloq=None,
) -> BackCalcResult

def back_calculate_many(
    samples: Iterable[Sample], curve: CalibrationResult, *,
    lloq=None, uloq=None,
) -> list[BackCalcResult]
```

Dilution applied after inversion (invariant 4). Out-of-range response raises
`InversionError` rather than extrapolating to a non-finite value.

### 6.3 Range and acceptance

```python
def determine_lloq_uloq(
    levels: Sequence[LevelStats], *,
    accuracy_pct: float = 20.0,
    precision_pct: float = 20.0,
    lloq_accuracy_pct: float = 25.0,   # relaxed at the extremes
    lloq_precision_pct: float = 25.0,
    exclude_anchors: bool = True,
) -> RangeResult

def run_acceptance(
    calibrators: Sequence[BackCalcResult],
    qcs: Sequence[BackCalcResult] = (), *,
    accuracy_pct: float = 20.0,
    precision_pct: float = 20.0,
    rule: AcceptanceRule = "4-6-15",   # 4-6-X calibrator rule
) -> AcceptanceResult
```

LLOQ/ULOQ require both accuracy and precision (invariant 5); anchors excluded
(invariant 6). The 4-6-X rule: at least 75% of calibrators (and ≥6) within
tolerance, with ≥2/3 of QC levels and ≥50% per level within tolerance.

### 6.4 Inverse prediction without private openfit access

The current `backcalc` uses `fit_result._model.equation`. The convergence plan:

1. Prefer a public openfit inverse/predict API if one exists (`predict`,
   `inverse_predict`); record the chosen API in `docs/openfit_api_contract.md`.
2. Otherwise implement the closed-form 4PL/5PL inverse in openassay (this is
   *assay-curve algebra applied to reported params*, which is in-scope; it does
   not reimplement fitting):
   - 4PL `y = Bottom + (Top−Bottom)/(1 + (x/EC50)^Hill)` ⇒
     `x = EC50 * ((Top−Bottom)/(y−Bottom) − 1)^(1/Hill)`.
   - 5PL adds the asymmetry exponent `s`:
     `x = EC50 * (((Top−Bottom)/(y−Bottom))^(1/s) − 1)^(1/Hill)`.
   - Guard the domain: `(y−Bottom)/(Top−Bottom) ∈ (0,1)`; outside ⇒
     `InversionError`. Keep brentq as a numeric fallback/cross-check.
3. Either way, never touch a leading-underscore openfit attribute in shipped
   code. This is a v0.1.1 cleanup item (§9).

### 6.5 Higher-level functions (later phases)

```python
read_plate(path, *, layout=None, format="auto") -> PlateData          # v0.2.0
test_parallelism(reference, test, *, method="f-test") -> ParallelismResult  # v0.4.0
relative_potency(reference, test, *, require_parallelism=True) -> PotencyResult  # v0.4.0
screen_cut_point(data, *, method="parametric", fp_rate=0.05) -> ADAResult   # v0.5.0
confirm_cut_point(data, *, fp_rate=0.01) -> ADAResult                  # v0.5.0
report_run(run, path, *, format="html") -> Path                       # report
```

### 6.6 Backward-compatibility policy

Until `v1.0.0`, additive changes are free; signature changes to already-shipped
public names require a deprecation shim for one minor version. From `v1.0.0`,
semantic versioning is strict and the public surface in `__all__` is frozen.

---

## 7. Cross-Cutting Engineering Standards

- **NaN/Inf policy:** validated at every public boundary; raises, never repairs
  (invariant 3). One helper `_require_finite(arr, name)` in `errors`/`units`.
- **Units:** openassay tracks unit *labels* (e.g., `ng/mL`) and propagates them
  into reports; it does not perform unit conversion (out of scope, avoids silent
  errors). Mismatched units between curve and samples raise `DataError`.
- **Reproducibility:** every fit carries a seed and `FitSpec`; reports embed the
  `Provenance` block (§5.3).
- **Determinism:** default `random_seed=0` everywhere; no wall-clock-dependent
  behavior except the report timestamp (which is recorded, not used in logic).
- **Logging:** standard library `logging` under the `openassay` logger; library
  never configures handlers or prints (except the CLI).
- **Typing:** `from __future__ import annotations`, full annotations,
  `mypy --strict` clean. Public arrays typed as `numpy.typing.NDArray[np.float64]`.
- **Style:** ruff (`E,F,I,W,UP`, line length 100), `ruff format`.
- **Docstrings:** NumPy style; every public symbol documented with Parameters,
  Returns, Raises, and a runnable example by v1.0.0.
- **Performance:** vectorize back-calculation of many samples; a full 96-well
  plate run should complete in well under a second on a laptop.

---

## 8. Release Plan — Phase By Phase

Each phase: **Goal → Modules/API → Algorithms & edge cases → Tests → Gate →
Docs → Risks.** Phases map 1:1 to `OPENASSAY_AGENT_LOOP.md`. Work each phase on
its own branch/worktree (e.g., `agent/openassay-v020`), never on `master`.

The universal per-phase gate (from the agent loop) is:

```
python -m pytest
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src/openassay
```

plus the phase-specific gates listed below. Commit only after the gate passes;
never `--no-verify`, never force-push.

### v0.1.0 — Standard Curves, Back-Calc, Acceptance, HTML (DONE, to harden)

- **Status:** implemented; see §3. Remaining hardening folded into v0.1.1.
- **Carryover bugs/risks:** private `fit_result._model` access (§6.4);
  `run_acceptance` not yet computing %CV/%RE; `scipy` undeclared in deps;
  CLI builds a placeholder `AcceptanceResult` in `fit-curve`.

### v0.1.1 — Validation Evidence

- **Goal:** prove the v0.1.0 numbers are correct and reproducible; close the
  carryover risks; establish the validation harness.
- **Work:**
  - Add `scipy` to core deps; remove private-attribute access via §6.4.
  - Implement %RE (accuracy = mean recovery − 100) and %CV (precision) in
    `acceptance` from replicate calibrators/QCs; wire `LevelStats`.
  - Add `CHANGELOG.md` (Keep a Changelog), `ROADMAP.md`, `docs/validation.md`,
    `docs/concepts.md`, and `tests/test_invariants.py`.
  - Add `examples/` end-to-end (one CSV in, HTML+MD out).
  - Validation fixtures for FDA/ICH M10-style calibration and QC scenarios with
    stored reference outputs + provenance.
- **Cross-checks:** compare 4PL/5PL parameter recovery and back-calculated
  concentrations against R `drda`/`nplr` on shared synthetic datasets where
  feasible. Store *reference outputs and provenance only* — never copy R source.
  Tolerances documented in `docs/validation.md` (e.g., relative param error
  bounds, recovery within X%).
- **Tests:** synthetic 4PL/5PL with known params → recover params within
  tolerance; round-trip (fit → back-calc on calibrators) recovers nominals;
  the nine invariants; golden-file report tests.
- **Gate:** validation tests + full pytest + ruff + mypy green.
- **Risks:** openfit/R numerical differences; mitigate with tolerance bands and
  documented seeds.

### v0.2.0 — Plate Layouts

- **Goal:** ingest real plate data and turn it into curve/sample inputs.
- **Modules/API:** `plate.PlateLayout`, `plate.PlateData`, `ingest.read_plate`.
- **Design:**
  - 96-well addressing `A1..H12`; `Well` value object with `(row, col)` and
    string parsing; ordering and iteration helpers.
  - `PlateLayout` maps wells → `Role` + nominal/sample identity + replicate
    group. Supports standards, anchors, QCs, unknowns, blanks.
  - Two input shapes: **tidy long** (`well,role,sample,concentration,response`)
    and **matrix plate** (8×12 grid of responses + a separate layout map).
    `format="auto"` sniffs.
  - Replicate grouping by `(role, sample/nominal)`; replicate collapse to mean
    (with %CV retained); blank subtraction (mean blank per plate, configurable).
- **Edge cases (all tested):** duplicate well entries → `PlateLayoutError`;
  missing expected wells → explicit error or documented partial behavior;
  blanks present/absent; NaN response in a well → raises (invariant 3);
  inconsistent units; partial plates.
- **CLI:** `openassay plate parse data.csv --layout layout.csv` summarizes wells,
  roles, replicates, and flags.
- **Gate:** tests for well addressing, duplicate wells, missing wells, blank
  handling, replicate collapse; plus universal gate.
- **Risks:** layout-format ambiguity; mitigate with strict schema validation and
  clear errors rather than guessing.

### v0.3.0 — LLOQ/ULOQ And Dilution

- **Goal:** decide the validated reportable range and handle dilution properly.
- **Modules/API:** `range.determine_lloq_uloq`, MRD support in `backcalc`.
- **Design:**
  - Validated range = the contiguous span of calibrator levels that pass both
    accuracy and precision (invariant 5), with anchors excluded (invariant 6).
  - **MRD (minimum required dilution):** the obligatory matrix dilution applied
    to every sample before measurement; reported concentration multiplies the
    inverse-predicted value by MRD × any additional dilution, applied *after*
    inversion (invariant 4). MRD is curve/method-level metadata.
  - Above-ULOQ samples are flagged for re-assay at higher dilution; below-LLOQ
    reported as `<LLOQ`.
- **Edge cases:** anchor with poor recovery does not set/limit the range;
  level passing accuracy but failing precision (and vice versa) excluded;
  10x/100x dilution linearity (diluted recovery within tolerance); LLOQ at the
  lowest non-anchor level only if it passes the relaxed extreme tolerance.
- **Gate:** anchor exclusion tests, LLOQ/ULOQ failure-mode tests, 10x/100x
  dilution checks; universal gate.
- **Risks:** off-by-one in "contiguous passing span"; cover with table-driven
  tests over hand-computed level sets.

### v0.4.0 — Parallelism And Relative Potency

- **Goal:** compare a test preparation to a reference and report potency only
  when justified.
- **Modules/API:** `parallelism.test_parallelism`, `potency.relative_potency`,
  `ParallelismResult`, `PotencyResult`.
- **Design:**
  - Parallel-line (log-linear region) and parallel-curve (4PL/5PL) workflows.
    Use openfit for the fits; openassay assembles the comparison.
  - Parallelism tests: classical **F-test** for coincidence of shape parameters
    (and/or an **equivalence-test** option on the ratio of slope/upper/lower/
    Hill parameters, which modern guidance prefers). Method selectable.
  - **Relative potency** estimated from the horizontal shift between parallel
    curves (EC50 ratio for 4PL/5PL, or intercept difference for parallel lines),
    with a confidence interval derived from openfit covariance.
  - **Invariant 7:** if parallelism is not demonstrated, `PotencyResult` returns
    `reportable=False` and `point_estimate=None` (no number is emitted).
  - Cite USP <1032>/<1034> conceptually; never reproduce paywalled text.
- **Tests:** synthetic parallel fixture → reportable potency near the true ratio;
  non-parallel fixture → not reportable; at least one external reference check.
- **Gate:** parallel/non-parallel fixtures + reference check + universal gate.
- **Risks:** choice of F-test vs equivalence default; expose both, document the
  trade-off, default to the more conservative reportability.

### v0.5.0 — ADA Cut Points

- **Goal:** screening and confirmatory cut points for anti-drug-antibody assays.
- **Modules/API:** `ada.screen_cut_point`, `ada.confirm_cut_point`, `ADAResult`.
- **Design (Shankar et al. 2008; FDA 2019; EMA 2017):**
  - **Screening cut point:** based on drug-naive samples across multiple
    donors/runs. Parametric option: `mean + 1.645·SD` (5% FPR) on raw or
    log/normalized signal after normality check; non-parametric option: 95th
    percentile. Fixed vs floating cut points (floating = multiplier applied to
    each run's negative-control mean) selected by an analysis of run/analyst
    variance.
  - **Confirmatory cut point:** percent inhibition in the competition assay,
    typically at 1% FPR (99th percentile or `mean + 2.33·SD`).
  - **Outlier handling:** documented, reproducible (e.g., boxplot/Tukey or
    3·SD), applied before cut-point estimation, recorded in provenance.
  - **Invariant 8:** require biological variability across samples/runs;
    a single run with no replication refuses to emit a cut point
    (`AcceptanceError`/`not_evaluable`), never falls back to a single-run SD.
- **Tests:** Shankar-style scenarios; balanced vs unbalanced designs;
  fixed vs floating decision; refusal on insufficient biological variability.
- **Gate:** cut-point scenario tests + universal gate.
- **Risks:** distributional assumptions; offer parametric + non-parametric and
  document selection criteria.

### v0.6.0 — 384-Well And Batch Processing

- **Goal:** scale to 384-well plates and multi-plate/run batches.
- **Modules/API:** extend `plate` to 384 (`A1..P24`); `batch.run_batch`,
  multi-plate aggregation, partial-failure reporting.
- **Design:** plate-size abstraction (rows×cols) so 96/384 share code;
  per-plate curve or bridged curve across plates (documented); aggregate run
  report; one failed plate must not abort the batch — collect and report partial
  failures.
- **Tests:** 96/384 compatibility; multi-plate aggregation; partial-failure
  reporting (one bad plate, rest succeed). Add import-linter layering contract
  here.
- **Gate:** above + universal gate.
- **Risks:** memory/perf at 384×N; vectorize and add a perf smoke test.

### v0.7.0 — PDF/DOCX Reports

- **Goal:** regulator-friendly PDF and DOCX outputs.
- **Modules/API:** `report/pdf.py` (reportlab), `report/docx.py` (python-docx),
  behind the `[reports]` extra; `report_run(..., format="pdf"|"docx")`.
- **Design:** shared `RunReport` model feeds all renderers (single source of
  truth); curve plot rendered headlessly; disclaimer in every format
  (invariant 9). Core install without `[reports]` must still import and run
  HTML/MD via stdlib + jinja2-optional fallback; missing-dep path raises a clear
  `ReportError` telling the user to `pip install 'openassay[reports]'`.
- **Tests:** HTML/PDF/DOCX smoke tests (file generated, parseable, contains
  disclaimer + key fields); missing-dependency test asserts the helpful error.
- **Gate:** above + universal gate.
- **Risks:** native deps on CI; pin versions, test on all OSes.

### v1.0.0 — Stable Release

- **Goal:** freeze public API, complete docs/examples, ship to PyPI.
- **Work:** finalize `__all__`; generate `docs/api/`; align
  README/CHANGELOG/ROADMAP; complete runnable examples for every workflow;
  CI matrix green on Windows/macOS/Linux × Python 3.10–3.12.
- **Gate:** `python -m build`, `twine check dist/*`, full pytest, ruff, mypy,
  docs build, examples execute; semantic-version freeze begins.
- **Risks:** API regret post-freeze; mitigate with an API-review checkpoint
  during 0.7→1.0 and a deprecation policy (§6.6).

---

## 9. API-Convergence Refactor (bridges current code → targets)

Tracked as part of v0.1.1 so the surface stabilizes early:

1. Introduce `models.py`, `types.py`, `errors.py`; move `CalibrationResult`,
   `Sample`, `BackCalcResult`, `AcceptanceResult` there; re-export from their
   current modules for compatibility.
2. Add functional wrappers (`fit_standard_curve`, `back_calculate_many`,
   `determine_lloq_uloq`, `report_run`) that delegate to existing code;
   keep `StandardCurve` and the `generate_*_report` functions as thin shims
   (deprecate `generate_*_report` in favor of `report_run` with a warning).
3. Replace `fit_result._model` usage with the §6.4 public/closed-form path.
4. Compute %RE/%CV in `acceptance`; expand `AcceptanceResult` (additive).
5. Update `__init__.__all__` to the curated target surface; keep old names
   importable until v1.0.0.
6. Normalize line endings (`.gitattributes` enforcing LF for `*.py`) to stop the
   cosmetic CRLF churn seen in the working tree.

No public name is removed before v1.0.0; everything above is additive +
deprecation-warned.

---

## 10. Testing Strategy

### 10.1 Test tiers

- **Unit:** every public function/edge case per module.
- **Property-based (hypothesis):** e.g., fit→back-calc round-trip recovers
  nominal within tolerance for random-but-valid 4PL/5PL params; dilution scaling
  is exactly linear; NaN injected anywhere always raises.
- **Invariant suite:** `tests/test_invariants.py` asserts all nine rules.
- **Validation suite:** FDA/ICH M10-style fixtures with stored reference outputs;
  optional R `drda`/`nplr` cross-checks behind a marker (skipped if R absent).
- **Golden-file:** report renderers compared to stored expected output (modulo
  timestamp/provenance), each format asserted to contain the disclaimer.
- **CLI:** invoke commands on example data; assert artifacts + exit codes.

### 10.2 Coverage and markers

Target ≥90% line coverage on `src/openassay` by v1.0.0 (`pytest-cov`). Markers:
`@pytest.mark.validation`, `@pytest.mark.requires_r`, `@pytest.mark.slow`.

### 10.3 The openfit dependency in tests

openfit may be absent in some environments (it is right now). Strategy:

- CI installs a pinned real openfit (preferred) so behavior is genuinely
  verified.
- A **contract-faithful fake** (`tests/fakes/openfit_fake.py`) implements the
  documented `Fit`/`FitResult`/`FitSpec` surface from
  `docs/openfit_api_contract.md` (params, se, ci, covariance, r_squared, x, y,
  y_fitted, model_id, weight_scheme, spec). A `conftest.py` switch selects real
  vs fake. The fake lets unit tests run offline and pins the API assumptions;
  the real engine in CI catches drift. Keep `docs/openfit_api_contract.md` the
  single source of truth and update it whenever openfit changes.

### 10.4 Numerical tolerances

Documented per check in `docs/validation.md` (relative parameter error bounds,
back-calc recovery bands, cut-point agreement). No assertion uses exact float
equality on fitted quantities.

---

## 11. Validation And Regulatory Mapping

| Workflow / phase            | Primary references |
|-----------------------------|--------------------|
| Calibration, QC, LLOQ/ULOQ, dilution (v0.1.x–v0.3.0) | FDA BMV 2018; FDA/ICH M10 (Nov 2022) |
| Parallelism, relative potency (v0.4.0) | USP <1032>/<1034> (concepts only) |
| ADA screening/confirmatory cut points (v0.5.0) | Shankar et al. 2008; FDA Immunogenicity 2019; EMA Immunogenicity (Dec 2017) |
| Fitting-engine correctness  | openfit's own validation |

`docs/validation.md` records, per scenario: input data + digest, expected
outputs + source, openassay output, tolerance, pass/fail, and provenance. Only
reference outputs and provenance are stored — never copied paywalled or
third-party source text.

---

## 12. CI/CD, Packaging, Release

- **CI (GitHub Actions):** matrix Windows/macOS/Linux × Python 3.10–3.12. Jobs:
  ruff check, ruff format --check, mypy --strict, pytest (with coverage),
  validation suite, `python -m build`, `twine check dist/*`. Optional R job for
  cross-checks. Import-linter layering check from v0.6.0.
- **Branching:** feature work on `agent/openassay-vXYZ` branches/worktrees;
  squash-or-merge into `master` only on green gate. Conventional Commits.
- **Versioning:** single source in `__init__.__version__` (and pyproject);
  SemVer, strict from v1.0.0. Tag `vX.Y.Z` triggers a build/publish workflow.
- **Release checklist (per tag):** changelog updated, version bumped, docs build,
  examples run, gate green, `twine check` clean, artifacts attached.
- **Repo hygiene:** `.gitattributes` (LF for source), `.gitignore` for build
  artifacts, no committed secrets.

---

## 13. Risk Register

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Private openfit attr (`_model`) breaks on openfit update | back-calc fails | Med | §6.4 public/closed-form inverse; pin openfit; contract test |
| openfit absent in dev/CI | can't test | High (now) | contract-faithful fake + pinned real openfit in CI (§10.3) |
| Regulatory misinterpretation in acceptance logic | wrong decisions | Med | conservative defaults, validation suite, mandatory disclaimer, expert-review framing |
| Parallelism method choice disputed | potency reportability differs | Med | offer F-test + equivalence; default conservative; document |
| ADA single-run SD shortcut | invalid cut points | Med | invariant 8 enforced; refuse when biological variability absent |
| Plate-format ambiguity | mis-parsed data | Med | strict schema, explicit errors, no guessing |
| Float exactness in tests | flaky CI | Med | tolerance bands, fixed seeds |
| Scope creep into openfit/LIMS/GUI | boundary erosion | Low–Med | §1.2 decision rule gates every PR |
| API regret after 1.0 freeze | breaking churn | Med | early functional API (v0.1.1), deprecation policy, pre-1.0 API review |

---

## 14. Definition Of Done

**Per phase:** universal gate green (pytest/ruff/ruff-format/mypy) + the phase's
specific gate tests + docs/changelog updated + invariants still pass + example(s)
for the new workflow run.

**v1.0.0:** all phases complete; ≥90% coverage; CI matrix green on 3 OSes ×
3 Python versions; `build` + `twine check` clean; full docs and runnable
examples; public API frozen in `__all__`; every report format carries the
disclaimer; validation suite documents agreement with references.

---

## 15. Immediate Next Actions (when implementation resumes)

1. Make openfit available (install pinned real openfit, or wire the
   contract-faithful fake + `conftest.py` switch) so the v0.1.0 gate can run.
2. Add `.gitattributes` (LF) and normalize line endings to kill the CRLF churn.
3. Add `scipy` to core deps; replace `fit_result._model` with the §6.4 path.
4. Implement %RE/%CV in `acceptance`; add `tests/test_invariants.py`.
5. Add `CHANGELOG.md`, `ROADMAP.md`, `docs/validation.md`, `docs/concepts.md`,
   and `examples/`; tag the hardened result `v0.1.1`.
6. Then proceed to v0.2.0 (plate layouts) on `agent/openassay-v020`.

> This plan is a living document. Update it at the start and end of each phase so
> it always reflects the real state of openassay.
