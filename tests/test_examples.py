"""Smoke tests for bundled examples."""

from __future__ import annotations

from typer.testing import CliRunner

from openassay.cli import app
from openassay.report import DISCLAIMER

runner = CliRunner()


def test_example_csv_workflow_generates_reports(tmp_path) -> None:
    """Bundled CSV examples should run through the CLI and emit reports."""
    assert app is not None

    curve_report = tmp_path / "standard_curve.html"
    backcalc_report = tmp_path / "backcalc_report.html"

    curve_result = runner.invoke(
        app,
        [
            "fit-curve",
            "examples/data/standards.csv",
            "--model",
            "4pl",
            "--weights",
            "1/y2",
            "--report",
            str(curve_report),
        ],
    )
    backcalc_result = runner.invoke(
        app,
        [
            "backcalc",
            "examples/data/samples.csv",
            "--curve",
            "examples/data/standards.csv",
            "--report",
            str(backcalc_report),
        ],
    )

    assert curve_result.exit_code == 0
    assert backcalc_result.exit_code == 0
    assert DISCLAIMER in curve_report.read_text(encoding="utf-8")
    assert DISCLAIMER in backcalc_report.read_text(encoding="utf-8")
