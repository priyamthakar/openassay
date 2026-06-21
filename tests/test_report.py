"""Tests for openassay report generation."""

from __future__ import annotations

from openassay.acceptance import AcceptanceResult
from openassay.curve import StandardCurve
from openassay.report import DISCLAIMER, generate_html_report, report_run


def test_html_report_interpolates_acceptance_and_disclaimer(tmp_path):
    """HTML reports should render real acceptance values and the disclaimer."""
    curve = StandardCurve(
        [0.1, 0.3, 1.0, 10.0, 100.0],
        [2.0, 5.0, 20.0, 80.0, 98.0],
        model="hill4p",
    )
    result = curve.fit()
    acceptance = AcceptanceResult(passed=False, reasons=["failed check"])
    path = tmp_path / "report.html"

    generate_html_report(result, [], acceptance, str(path))

    html = path.read_text(encoding="utf-8")
    assert "<p>Passed: False</p>" in html
    assert DISCLAIMER in html
    assert "{acceptance_result.passed}" not in html
    assert "{DISCLAIMER}" not in html


def test_report_run_dispatches_by_extension(tmp_path):
    """Functional report API should generate reports and return the output path."""
    curve = StandardCurve(
        [0.1, 0.3, 1.0, 10.0, 100.0],
        [2.0, 5.0, 20.0, 80.0, 98.0],
        model="hill4p",
    )
    result = curve.fit()
    acceptance = AcceptanceResult(passed=True, reasons=["ok"])
    path = tmp_path / "report.md"

    returned = report_run(result, [], acceptance, path)

    assert returned == path
    assert DISCLAIMER in path.read_text(encoding="utf-8")
