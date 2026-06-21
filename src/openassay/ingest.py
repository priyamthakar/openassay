"""Plate input readers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from openassay.plate import PlateData, PlateLayout, Well, make_plate_well


def _read_table(path: str | Path, *, index_col: int | None = None) -> pd.DataFrame:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(file_path, index_col=index_col)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(file_path, index_col=index_col)
    raise ValueError("Plate input must be a .csv, .xlsx, or .xls file.")


def _optional_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def _optional_string(value: Any) -> str | None:
    if pd.isna(value):
        return None
    text = str(value)
    return text if text else None


def _read_tidy_plate(path: str | Path, expected_wells: list[str] | None = None) -> PlateData:
    df = _read_table(path)
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


def _read_matrix_plate(
    path: str | Path,
    *,
    layout: str | Path,
    expected_wells: list[str] | None = None,
) -> PlateData:
    matrix = _read_table(path, index_col=0)
    layout_df = _read_table(layout)
    required = {"well", "role"}
    missing = required.difference(layout_df.columns)
    if missing:
        raise ValueError(f"Plate layout is missing required columns: {sorted(missing)}")

    responses: dict[str, float] = {}
    for row_label, row in matrix.iterrows():
        for column_label, value in row.items():
            well = str(Well.parse(f"{row_label}{column_label}"))
            responses[well] = float(value)

    wells = []
    for row in layout_df.itertuples(index=False):
        well = str(row.well).strip().upper()
        if well not in responses:
            raise ValueError(f"Layout references well {well!r} missing from matrix data.")
        wells.append(
            make_plate_well(
                well=well,
                role=str(row.role),
                response=responses[well],
                sample_name=_optional_string(getattr(row, "sample", None)),
                nominal_concentration=_optional_float(getattr(row, "concentration", None)),
                replicate_group=_optional_string(getattr(row, "replicate_group", None)),
            )
        )

    plate_layout = PlateLayout(wells)
    if expected_wells is not None:
        plate_layout.require_wells(expected_wells)
    return PlateData(layout=plate_layout)


def read_plate(
    path: str | Path,
    *,
    format: str = "tidy",
    layout: str | Path | None = None,
    expected_wells: list[str] | None = None,
) -> PlateData:
    """Read plate CSV data."""
    normalized_format = format.lower()
    if normalized_format == "tidy":
        return _read_tidy_plate(path, expected_wells=expected_wells)
    if normalized_format == "matrix":
        if layout is None:
            raise ValueError("Matrix plate format requires a layout CSV path.")
        return _read_matrix_plate(
            path,
            layout=layout,
            expected_wells=expected_wells,
        )
    raise ValueError("format must be 'tidy' or 'matrix'.")
