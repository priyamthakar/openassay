# openassay examples

This directory contains small synthetic datasets for smoke-testing the v0.1.0
workflow from CSV input to report output.

Run from the repository root:

```powershell
python -m openassay.cli fit-curve examples\data\standards.csv --model 4pl --weights 1/y2 --report examples\out\standard_curve.html
python -m openassay.cli backcalc examples\data\samples.csv --curve examples\data\standards.csv --report examples\out\backcalc_report.html
```

The data are illustrative only. Generated reports include the openassay
bioanalytical-scientist review disclaimer.
