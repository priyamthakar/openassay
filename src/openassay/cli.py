"""CLI for openassay."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

try:
    import typer
except ImportError:
    typer = None  # type: ignore[assignment]

from openassay import __version__
from openassay.acceptance import run_acceptance
from openassay.backcalc import Sample, back_calculate
from openassay.curve import StandardCurve
from openassay.ingest import read_plate
from openassay.potency import relative_potency
from openassay.report import generate_html_report, generate_markdown_report
from openassay.types import Role

if typer is not None:
    app = typer.Typer(help="openassay CLI")
    plate_app = typer.Typer(help="Plate layout and plate data commands")
    app.add_typer(plate_app, name="plate")
else:
    app = None
    plate_app = None


def _missing_cli() -> None:
    if typer is None:
        print("CLI dependencies not installed. Run: pip install 'openassay[cli]'", file=sys.stderr)
        sys.exit(1)


def _normalize_model(model: str) -> str:
    aliases = {
        "4pl": "hill4p",
        "5pl": "hill5p",
    }
    model_id = aliases.get(model.lower(), model.lower())
    if model_id not in {"hill4p", "hill5p"}:
        raise ValueError("model must be one of: 4pl, 5pl, hill4p, hill5p")
    return model_id


def _read_fit_result_json(path: Path) -> SimpleNamespace:
    payload = json.loads(path.read_text(encoding="utf-8"))
    model = str(payload.get("model_id", payload.get("model", "")))
    params = payload.get("params")
    if not isinstance(params, dict):
        raise ValueError("fit result JSON must contain a params object")
    covariance = payload.get("covariance")
    return SimpleNamespace(
        model_id=_normalize_model(model),
        params={str(name): float(value) for name, value in params.items()},
        covariance=covariance,
    )


def main() -> None:
    """Console-script entry point."""
    if app is None:
        _missing_cli()
        return
    app()


if typer is not None:

    @app.command()
    def version() -> None:
        """Print openassay version."""
        print(f"openassay version {__version__}")

    @app.command()
    def fit_curve(
        data: Path = typer.Argument(..., help="Path to CSV data file"),
        model: str = typer.Option("4pl", help="Model ID (4pl, 5pl, hill4p, or hill5p)"),
        weights: str = typer.Option("1/y2", help="Weight scheme"),
        report: Path = typer.Option("report.html", help="Output report path"),
    ) -> None:
        """Fit a standard curve and generate a report."""
        import pandas as pd

        df = pd.read_csv(data)
        x = df["concentration"].values
        y = df["response"].values

        curve = StandardCurve(x, y, model=_normalize_model(model), weights=weights)
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
        curve_data: Path = typer.Option(
            ...,
            "--curve",
            "--curve-data",
            help="Path to standard curve CSV",
        ),
        report: Path = typer.Option("results.html", help="Output report path"),
    ) -> None:
        """Back-calculate sample concentrations."""
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

    @app.command("parallelism")
    def parallelism_command(
        reference: Path = typer.Argument(..., help="Reference fit-result JSON"),
        test: Path = typer.Argument(..., help="Test fit-result JSON"),
        method: str = typer.Option("equivalence", help="Parallelism method"),
        tolerance: float = typer.Option(0.20, help="Equivalence tolerance for shape ratios"),
        confidence: float = typer.Option(0.95, help="Confidence level for potency interval"),
    ) -> None:
        """Check curve parallelism and report gated relative potency."""
        result = relative_potency(
            _read_fit_result_json(reference),
            _read_fit_result_json(test),
            method=method,
            tolerance=tolerance,
            confidence=confidence,
        )

        print(f"Method: {result.parallelism.method}")
        print(f"Parallel: {result.parallelism.parallel}")
        if result.point_estimate is None:
            print("Relative potency: not reportable")
        else:
            print(f"Relative potency: {result.point_estimate:.6g}")
        if result.confidence_interval is not None:
            lower, upper = result.confidence_interval
            print(f"{result.confidence:.0%} CI: {lower:.6g} to {upper:.6g}")
        for reason in result.parallelism.reasons:
            print(f"- {reason}")

    @plate_app.command("parse")
    def plate_parse(
        data: Path = typer.Argument(..., help="Path to plate data CSV"),
        format: str = typer.Option("tidy", help="Input format: tidy or matrix"),
        layout: Path | None = typer.Option(None, help="Layout CSV for matrix input"),
        subtract_blank: bool = typer.Option(True, help="Subtract mean blank before collapse"),
    ) -> None:
        """Parse plate data and print a compact summary."""
        plate = read_plate(data, format=format, layout=layout)
        collapsed = plate.collapse_replicates(subtract_blank=subtract_blank)
        roles: tuple[Role, ...] = ("standard", "anchor", "qc", "unknown", "blank")
        role_counts = {role: len(plate.layout.by_role(role)) for role in roles}
        blank = plate.blank_response()

        print(f"Wells: {len(plate.wells)}")
        print(
            "Roles: " + ", ".join(f"{role}={count}" for role, count in role_counts.items() if count)
        )
        if blank is not None:
            print(f"Blank mean: {blank:.6g}")
        print(f"Collapsed groups: {len(collapsed)}")
        for group in collapsed:
            print(
                f"- {group.role}:{group.replicate_group} "
                f"n={group.n} mean={group.mean_response:.6g} cv={group.cv_percent:.3g}%"
            )


if __name__ == "__main__":
    main()
