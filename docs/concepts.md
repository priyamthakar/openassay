# openassay Concepts And Glossary

A short domain glossary so the codebase and docs use terms consistently. This is
explanatory, not regulatory guidance. See `docs/PROJECT_PLAN.md` for how each
concept maps to modules and correctness rules.

## Curve and fitting

- **Standard curve / calibration curve.** The relationship between known
  calibrator concentrations (x) and assay response (y), fit with a 4PL or 5PL
  model. openassay fits this through openfit.
- **4PL (`hill4p`).** Four-parameter logistic: `Bottom`, `Top`, `EC50`,
  `HillSlope`. Symmetric sigmoid on a log-concentration axis.
- **5PL (`hill5p`).** Adds an `Asymmetry` parameter for asymmetric sigmoids;
  often a better fit for immunoassays.
- **Weighting.** Down-weights high-response points so the low end (where LLOQ
  lives) is fit well. openassay defaults to **`1/y2`**; uniform weighting must be
  chosen explicitly. openassay always passes `weights=` to openfit.
- **EC50.** The concentration at half-maximal response; also the curve's
  location parameter used in relative-potency shift estimates.

## Sample roles

- **Calibrator / standard.** Known-concentration points used to build and judge
  the curve.
- **Anchor (anchor calibrator).** Points outside the quantification range added
  to stabilize the curve shape. They may be **included in the fit** but are
  **excluded from acceptance and reportable-range decisions**.
- **QC (quality control).** Known-concentration samples (typically low/mid/high)
  used to judge run acceptance independently of the calibrators.
- **Unknown.** Study samples whose concentration is back-calculated.
- **Blank.** No-analyte wells used for background/blank subtraction.

## Quantification range

- **Back-calculation.** Inverse prediction: given a response, solve the fitted
  curve for concentration. The **dilution factor is applied after** inversion.
- **LLOQ / ULOQ.** Lower / upper limit of quantification — the lowest/highest
  concentration measured with acceptable **accuracy and precision** (both
  required). Anchors do not set these limits.
- **Reportable range.** The validated span between LLOQ and ULOQ. Results below
  LLOQ are reported as `<LLOQ`; above ULOQ are flagged for re-assay at higher
  dilution.
- **MRD (minimum required dilution).** The obligatory matrix dilution applied to
  every sample before measurement; folded into the reported concentration after
  inversion.

## Accuracy and precision

- **%RE (percent relative error) / bias.** Accuracy: `mean recovery − 100%`.
  How far the measured mean is from nominal.
- **%CV (percent coefficient of variation).** Precision: `100 × SD / mean`
  across replicates. How scattered replicates are.
- **Total error.** A combined accuracy + precision criterion sometimes applied to
  QC acceptance.
- **4-6-X rule.** A common calibrator acceptance convention: at least 75% (and
  ≥6) of calibrators within tolerance, with relaxed tolerance (X, e.g. 25%) at
  the extremes (LLOQ/ULOQ).

## Relative potency

- **Parallelism.** Whether a test preparation's dose-response curve is parallel
  to a reference's. Required before relative potency is reportable.
- **Relative potency.** The horizontal shift between parallel curves (e.g., EC50
  ratio), expressed as the test's potency relative to the reference. **Not
  reportable** if parallelism is not demonstrated.

## Immunogenicity (ADA)

- **ADA (anti-drug antibody) assay.** Detects antibodies a subject develops
  against a therapeutic.
- **Screening cut point.** The signal threshold above which a sample is
  potentially positive (commonly ~5% false-positive rate).
- **Confirmatory cut point.** A competition-based threshold (commonly ~1% FPR)
  confirming the signal is drug-specific.
- **Fixed vs floating cut point.** Fixed = a single absolute threshold; floating
  = a multiplier applied to each run's negative-control mean. Choice depends on
  run/analyst variability.
- **Biological variability.** Cut points must be derived from variability across
  drug-naive donors/runs — never a single-run SD.

## Reproducibility

- **FitSpec.** openfit's reproducibility manifest carried on every fit.
- **Provenance.** openassay's record attached to results/reports: package and
  openfit versions, input digests, seed, timestamp — enough to reproduce any
  reported number.
