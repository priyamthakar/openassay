"""Tests for package release metadata."""

from __future__ import annotations

from pathlib import Path

import tomllib

import openassay


def test_package_version_matches_pyproject() -> None:
    """The runtime version should match the build metadata version."""
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert openassay.__version__ == pyproject["project"]["version"]
