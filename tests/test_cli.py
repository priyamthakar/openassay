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


def test_cli_plate_parse_accepts_384_well_plate(tmp_path) -> None:
    """The plate parser CLI should expose explicit 384-well parsing."""
    assert app is not None

    plate_path = tmp_path / "plate384.csv"
    plate_path.write_text(
        "\n".join(
            [
                "well,role,sample,response,replicate_group",
                "A1,blank,blank,2.0,blank",
                "P24,unknown,sample-1,22.0,sample-1",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["plate", "parse", str(plate_path), "--plate-size", "384"])

    assert result.exit_code == 0
    assert "Plate size: 384" in result.output
    assert "Wells: 2" in result.output


def test_cli_parallelism_reports_gated_relative_potency(tmp_path) -> None:
    """The parallelism command should expose the potency gate."""
    assert app is not None

    reference_path = tmp_path / "reference.json"
    test_path = tmp_path / "test.json"
    reference_path.write_text(
        """
{
  "model_id": "hill4p",
  "params": {"Bottom": 1.0, "Top": 100.0, "EC50": 10.0, "HillSlope": 1.0},
  "covariance": [
    [0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.04, 0.0],
    [0.0, 0.0, 0.0, 0.0]
  ]
}
""".strip(),
        encoding="utf-8",
    )
    test_path.write_text(
        """
{
  "model_id": "hill4p",
  "params": {"Bottom": 1.0, "Top": 100.0, "EC50": 5.0, "HillSlope": 1.0},
  "covariance": [
    [0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.01, 0.0],
    [0.0, 0.0, 0.0, 0.0]
  ]
}
""".strip(),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["parallelism", str(reference_path), str(test_path)])

    assert result.exit_code == 0
    assert "Method: equivalence" in result.output
    assert "Parallel: True" in result.output
    assert "Relative potency: 2" in result.output
    assert "95% CI:" in result.output


def test_cli_ada_screen_reports_cut_point(tmp_path) -> None:
    """The ADA screen command should estimate a CSV cut point."""
    assert app is not None

    data_path = tmp_path / "ada_screen.csv"
    data_path.write_text(
        "\n".join(
            [
                "sample_id,run_id,response",
                "d1,r1,101.0",
                "d2,r1,103.0",
                "d1,r2,99.0",
                "d2,r2,104.0",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["ada", "screen", str(data_path), "--cut-point-type", "floating", "--transform", "log"],
    )

    assert result.exit_code == 0
    assert "Evaluable: True" in result.output
    assert "Cut-point type: floating" in result.output
    assert "Transform: log" in result.output
    assert "Cut point:" in result.output


def test_cli_ada_confirm_reports_not_evaluable(tmp_path) -> None:
    """The ADA confirm command should surface insufficient variability."""
    assert app is not None

    data_path = tmp_path / "ada_confirm.csv"
    data_path.write_text(
        "\n".join(
            [
                "sample_id,run_id,percent_inhibition",
                "d1,r1,14.0",
                "d2,r1,18.0",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["ada", "confirm", str(data_path)])

    assert result.exit_code == 0
    assert "Evaluable: False" in result.output
    assert "Cut-point type: fixed" in result.output
    assert "Transform: raw" in result.output
    assert "Cut point: not evaluable" in result.output
