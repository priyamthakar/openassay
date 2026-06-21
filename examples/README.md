# openassay examples

This directory contains small synthetic datasets for smoke-testing the documented
CLI workflows from input files to reports or console summaries.

Run from the repository root:

```powershell
python -m openassay.cli fit-curve examples\data\standards.csv --model 4pl --weights 1/y2 --report examples\out\standard_curve.html
python -m openassay.cli backcalc examples\data\samples.csv --curve examples\data\standards.csv --report examples\out\backcalc_report.html
python -m openassay.cli plate parse examples\data\plate_tidy.csv
python -m openassay.cli parallelism examples\data\parallel_reference.json examples\data\parallel_test.json
python -m openassay.cli ada screen examples\data\ada_screen.csv --cut-point-type floating --transform log
python -m openassay.cli ada confirm examples\data\ada_confirm.csv
```

The data are illustrative only. Generated reports include the openassay
bioanalytical-scientist review disclaimer.
