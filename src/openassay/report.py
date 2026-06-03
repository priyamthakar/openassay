"""HTML/Markdown report generation."""

from __future__ import annotations

from typing import Any

DISCLAIMER = (
    "This report was generated using openassay (open-source). "
    "Final acceptance decisions and regulatory interpretation should be "
    "reviewed by qualified bioanalytical scientists."
)


def generate_html_report(
    curve_result: Any,
    backcalc_results: list[Any],
    acceptance_result: Any,
    path: str,
) -> None:
    """Generate an HTML report.

    Parameters
    ----------
    curve_result : CalibrationResult
        Fitted standard curve result.
    backcalc_results : list
        List of BackCalcResult objects.
    acceptance_result : AcceptanceResult
        Acceptance evaluation result.
    path : str
        Output file path.
    """
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>openassay Run Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .disclaimer {{ color: #666; font-style: italic; margin-top: 40px; }}
    </style>
</head>
<body>
    <h1>openassay Run Report</h1>
    <h2>Standard Curve</h2>
    <p>Model: {curve_result.fit_result.model_id}</p>
    <p>Weighting: {curve_result.fit_result.weight_scheme}</p>
    <p>R^2: {curve_result.fit_result.r_squared:.4f}</p>

    <h2>Parameters</h2>
    <table>
        <tr><th>Parameter</th><th>Value</th><th>SE</th></tr>
"""
    for name, val in curve_result.fit_result.params.items():
        se = curve_result.fit_result.se.get(name, float("nan"))
        html_content += f"        <tr><td>{name}</td><td>{val:.4g}</td><td>{se:.4g}</td></tr>\n"

    html_content += """    </table>

    <h2>Back-Calculated Samples</h2>
    <table>
        <tr>
            <th>Sample</th><th>Predicted</th><th>Diluted</th>
            <th>Below LLOQ</th><th>Above ULOQ</th>
        </tr>
"""
    for res in backcalc_results:
        html_content += (
            f"        <tr><td>{res.sample_name}</td><td>{res.predicted_concentration:.4g}</td>"
            f"<td>{res.diluted_concentration:.4g}</td><td>{res.below_lloq}</td><td>{res.above_uloq}</td></tr>\n"
        )

    html_content += """    </table>

    <h2>Acceptance</h2>
    <p>Passed: {acceptance_result.passed}</p>
    <ul>
"""
    for reason in acceptance_result.reasons:
        html_content += f"        <li>{reason}</li>\n"

    html_content += """    </ul>

    <p class="disclaimer">{DISCLAIMER}</p>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)


def generate_markdown_report(
    curve_result: Any,
    backcalc_results: list[Any],
    acceptance_result: Any,
    path: str,
) -> None:
    """Generate a Markdown report.

    Parameters
    ----------
    curve_result : CalibrationResult
        Fitted standard curve result.
    backcalc_results : list
        List of BackCalcResult objects.
    acceptance_result : AcceptanceResult
        Acceptance evaluation result.
    path : str
        Output file path.
    """
    md_content = f"""# openassay Run Report

## Standard Curve
- Model: {curve_result.fit_result.model_id}
- Weighting: {curve_result.fit_result.weight_scheme}
- R^2: {curve_result.fit_result.r_squared:.4f}

## Parameters
| Parameter | Value | SE |
|-----------|-------|----|
"""
    for name, val in curve_result.fit_result.params.items():
        se = curve_result.fit_result.se.get(name, float("nan"))
        md_content += f"| {name} | {val:.4g} | {se:.4g} |\n"

    md_content += """
## Back-Calculated Samples
| Sample | Predicted | Diluted | Below LLOQ | Above ULOQ |
|--------|-----------|---------|------------|------------|
"""
    for res in backcalc_results:
        md_content += (
            f"| {res.sample_name} | {res.predicted_concentration:.4g} | "
            f"{res.diluted_concentration:.4g} | {res.below_lloq} | {res.above_uloq} |\n"
        )

    md_content += f"""
## Acceptance
- Passed: {acceptance_result.passed}
"""
    for reason in acceptance_result.reasons:
        md_content += f"  - {reason}\n"

    md_content += f"\n> *{DISCLAIMER}*\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(md_content)
