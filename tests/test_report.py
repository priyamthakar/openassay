"""Tests for openassay report generation."""

from __future__ import annotations

import builtins
from types import SimpleNamespace

import pytest

from openassay.acceptance import AcceptanceResult
from openassay.curve import StandardCurve
from openassay.errors import ReportError
from openassay.report import (
    DISCLAIMER,
    generate_docx_report,
    generate_html_report,
    generate_pdf_report,
    report_run,
)


def report_fixture():
    curve = StandardCurve(
        [0.1, 0.3, 1.0, 10.0, 100.0],
        [2.0, 5.0, 20.0, 80.0, 98.0],
        model="hill4p",
    )
    return curve.fit(), AcceptanceResult(passed=True, reasons=["ok"])


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


def test_pdf_report_contains_disclaimer(tmp_path) -> None:
    """PDF reports should be generated and contain the mandatory disclaimer."""
    from pypdf import PdfReader

    result, acceptance = report_fixture()
    path = tmp_path / "report.pdf"

    returned = report_run(result, [], acceptance, path)

    assert returned == path
    text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    assert "openassay Run Report" in text
    assert DISCLAIMER in text


def test_docx_report_contains_disclaimer(tmp_path) -> None:
    """DOCX reports should be generated and contain the mandatory disclaimer."""
    from docx import Document

    result, acceptance = report_fixture()
    path = tmp_path / "report.docx"

    generate_docx_report(result, [], acceptance, str(path))

    text = "\n".join(paragraph.text for paragraph in Document(path).paragraphs)
    assert "openassay Run Report" in text
    assert DISCLAIMER in text


def test_pdf_missing_dependency_error_is_helpful(monkeypatch, tmp_path) -> None:
    """Missing optional report dependencies should raise a clear ReportError."""
    result = SimpleNamespace(
        fit_result=SimpleNamespace(
            model_id="hill4p",
            weight_scheme="1/y2",
            r_squared=0.99,
            params={},
            se={},
        )
    )
    acceptance = AcceptanceResult(passed=True, reasons=["ok"])
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("reportlab"):
            raise ImportError("missing reportlab")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ReportError, match=r"openassay\[reports\]"):
        generate_pdf_report(result, [], acceptance, str(tmp_path / "report.pdf"))


def test_docx_missing_dependency_error_is_helpful(monkeypatch, tmp_path) -> None:
    """Missing python-docx should raise the same clear ReportError."""
    result = SimpleNamespace(
        fit_result=SimpleNamespace(
            model_id="hill4p",
            weight_scheme="1/y2",
            r_squared=0.99,
            params={},
            se={},
        )
    )
    acceptance = AcceptanceResult(passed=True, reasons=["ok"])
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "docx":
            raise ImportError("missing docx")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ReportError, match=r"openassay\[reports\]"):
        generate_docx_report(result, [], acceptance, str(tmp_path / "report.docx"))
