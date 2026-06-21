"""Plate input readers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from openassay.plate import PlateData, PlateLayout, make_plate_well


def _optional_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def _optional_string(value: Any) -> str | None:
    if pd.isna(value):
        return None
    text = str(value)
    return text if text else None


def read_plate(
    path: str | Path,
    *,
    format: str = "tidy",
    expected_wells: list[str] | None = None,
) -> PlateData:
    """Read tidy long-format plate CSV data."""
    if format != "tidy":
        raise ValueError("Only tidy plate format is currently supported.")

    df = pd.read_csv(path)
    required = {"well", "role", "response"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Plate data is missing required columns: {sorted(missing)}")

    wells = [
        make_plate_well(
            well=str(row.well),
            role=str(row.role),
            response=float(row.response),
            sample_name=_optional_string(getattr(row, "sample", None)),
            nominal_concentration=_optional_float(getattr(row, "concentration", None)),
            replicate_group=_optional_string(getattr(row, "replicate_group", None)),
        )
        for row in df.itertuples(index=False)
    ]
    layout = PlateLayout(wells)
    if expected_wells is not None:
        layout.require_wells(expected_wells)
    return PlateData(layout=layout)
