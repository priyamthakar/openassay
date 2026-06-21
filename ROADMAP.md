# openassay Roadmap

A condensed public view of the release plan. The full engineering detail lives in
[`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md); the working release loop lives in
[`OPENASSAY_AGENT_LOOP.md`](OPENASSAY_AGENT_LOOP.md).

openassay is the applied assay-workflow layer built on top of
[openfit](https://github.com/priyamthakar/openfit) (the curve-fitting engine).
openassay never reimplements fitting logic.

| Version | Theme | Highlights |
|---------|-------|-----------|
| **0.1.0** ✅ | Standard curves, back-calc, acceptance, HTML | 4PL/5PL via openfit, `1/y2` default weighting, dilution after inversion, HTML/MD reports |
| **0.1.1** 🔭 | Validation evidence + hardening | %RE/%CV acceptance, invariant test suite, validation fixtures, public inverse path, CHANGELOG/ROADMAP/examples |
| **0.2.0** | Plate layouts | 96-well model, roles (standard/anchor/QC/unknown/blank), tidy + matrix import, replicate collapse, blank subtraction |
| **0.3.0** | LLOQ/ULOQ & dilution | Validated range from accuracy + precision, MRD handling, anchor exclusion, 10x/100x checks |
| **0.4.0** | Parallelism & relative potency | F-test/equivalence parallelism, potency reportable only when parallel |
| **0.5.0** | ADA cut points | Screening + confirmatory cut points, parametric & non-parametric, biological variability required |
| **0.6.0** | 384-well & batch | 384-well plates, multi-plate/run aggregation, partial-failure reporting |
| **0.7.0** | PDF/DOCX reports | ReportLab + python-docx renderers behind `[reports]`, core install stays lean |
| **1.0.0** | Stable release | Frozen public API, full docs/examples, CI green on 3 OSes × Python 3.10–3.12 |

Legend: ✅ done · 🔭 in progress · (blank) planned.

Every generated report includes:

> This report was generated using openassay (open-source). Final acceptance
> decisions and regulatory interpretation should be reviewed by qualified
> bioanalytical scientists.
