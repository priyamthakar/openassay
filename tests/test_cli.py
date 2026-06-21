"""Tests for the openassay CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from openassay.cli import app

runner = CliRunner()


def test_cli_version() -> None:
    """The version command should be available through the Typer app."""
    assert app is not None

    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "openassay version" in result.output


def test_cli_backcalc_accepts_documented_curve_option(tmp_path) -> None:
    """The backcalc command should accept the documented --curve option."""
    assert app is not None

    curve_path = tmp_path / "standards.csv"
    samples_path = tmp_path / "samples.csv"
    report_path = tmp_path / "results.html"
    curve_path.write_text(
        "\n".join(
            [
                "concentration,response",
                "0.1,2.0",
                "0.3,5.0",
                "1.0,20.0",
                "10.0,80.0",
                "100.0,98.0",
            ]
        ),
        encoding="utf-8",
    )
    samples_path.write_text(
        "\n".join(
            [
                "name,response,dilution_factor",
                "sample-1,50.0,2.0",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "backcalc",
            str(samples_path),
            "--curve",
            str(curve_path),
            "--report",
            str(report_path),
        ],
    )

    assert result.exit_code == 0
    assert report_path.exists()
    assert "Report written to" in result.output
