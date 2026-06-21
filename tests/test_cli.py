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


def test_cli_plate_parse_summarizes_tidy_plate(tmp_path) -> None:
    """The plate parse command should summarize roles and collapsed groups."""
    assert app is not None

    plate_path = tmp_path / "plate.csv"
    plate_path.write_text(
        "\n".join(
            [
                "well,role,sample,response,replicate_group",
                "A1,blank,blank,2.0,blank",
                "B1,qc,qc-low,11.0,qc-low",
                "B2,qc,qc-low,13.0,qc-low",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["plate", "parse", str(plate_path)])

    assert result.exit_code == 0
    assert "Wells: 3" in result.output
    assert "qc=2" in result.output
    assert "blank=1" in result.output
    assert "Collapsed groups: 1" in result.output
    assert "qc:qc-low" in result.output
