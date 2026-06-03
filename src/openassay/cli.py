"""CLI for openassay."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import typer
except ImportError:
    typer = None  # type: ignore[assignment]

from openassay import __version__
from openassay.acceptance import run_acceptance
from openassay.backcalc import Sample, back_calculate
from openassay.curve import StandardCurve
from openassay.report import generate_html_report, generate_markdown_report

if typer is not None:
    app = typer.Typer(help="openassay CLI")
else:
    app = None


def _check_cli() -> None:
    if typer is None:
        print("CLI dependencies not installed. Run: pip install 'openassay[cli]'", file=sys.stderr)
        sys.exit(1)


if typer is not None:

    @app.command()
    def version() -> None:
        """Print openassay version."""
        _check_cli()
        print(f"openassay version {__version__}")

    @app.command()
    def fit_curve(
        data: Path = typer.Argument(..., help="Path to CSV data file"),
        model: str = typer.Option("hill4p", help="Model ID (hill4p or hill5p)"),
        weights: str = typer.Option("1/y2", help="Weight scheme"),
        report: Path = typer.Option("report.html", help="Output report path"),
    ) -> None:
        """Fit a standard curve and generate a report."""
        _check_cli()
        import pandas as pd

        df = pd.read_csv(data)
        x = df["concentration"].values
        y = df["response"].values

        curve = StandardCurve(x, y, model=model, weights=weights)
        result = curve.fit()

        from openassay.acceptance import AcceptanceResult

        acceptance = AcceptanceResult(passed=True, reasons=["CLI example"])

        if str(report).endswith(".md"):
            generate_markdown_report(result, [], acceptance, str(report))
        else:
            generate_html_report(result, [], acceptance, str(report))

        print(f"Report written to {report}")

    @app.command()
    def backcalc(
        data: Path = typer.Argument(..., help="Path to CSV data file"),
        curve_data: Path = typer.Option(..., help="Path to standard curve CSV"),
        report: Path = typer.Option("results.html", help="Output report path"),
    ) -> None:
        """Back-calculate sample concentrations."""
        _check_cli()
        import pandas as pd

        df_curve = pd.read_csv(curve_data)
        curve = StandardCurve(df_curve["concentration"].values, df_curve["response"].values)
        curve_result = curve.fit()

        df_samples = pd.read_csv(data)

        backcalc_results = []
        for _, row in df_samples.iterrows():
            sample = Sample(
                name=str(row["name"]),
                response=float(row["response"]),
                dilution_factor=float(row.get("dilution_factor", 1.0)),
            )
            res = back_calculate(sample, curve_result.fit_result)
            backcalc_results.append(res)

        acceptance = run_acceptance(backcalc_results)

        if str(report).endswith(".md"):
            generate_markdown_report(curve_result, backcalc_results, acceptance, str(report))
        else:
            generate_html_report(curve_result, backcalc_results, acceptance, str(report))

        print(f"Report written to {report}")


if __name__ == "__main__":
    if app is not None:
        app()
