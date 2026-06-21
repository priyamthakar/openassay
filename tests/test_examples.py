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


def test_example_cli_workflows_are_runnable() -> None:
    """Bundled example files should cover the documented non-report CLI paths."""
    assert app is not None

    plate_result = runner.invoke(app, ["plate", "parse", "examples/data/plate_tidy.csv"])
    parallelism_result = runner.invoke(
        app,
        [
            "parallelism",
            "examples/data/parallel_reference.json",
            "examples/data/parallel_test.json",
        ],
    )
    ada_screen_result = runner.invoke(
        app,
        [
            "ada",
            "screen",
            "examples/data/ada_screen.csv",
            "--cut-point-type",
            "floating",
            "--transform",
            "log",
        ],
    )
    ada_confirm_result = runner.invoke(app, ["ada", "confirm", "examples/data/ada_confirm.csv"])

    assert plate_result.exit_code == 0
    assert "Collapsed groups:" in plate_result.output
    assert parallelism_result.exit_code == 0
    assert "Relative potency: 2" in parallelism_result.output
    assert ada_screen_result.exit_code == 0
    assert "Evaluable: True" in ada_screen_result.output
    assert ada_confirm_result.exit_code == 0
    assert "Cut point: not evaluable" in ada_confirm_result.output
