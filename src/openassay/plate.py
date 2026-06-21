"""Plate layout and plate data models."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from openassay.errors import PlateLayoutError
from openassay.types import ROLES, Role

_ROW_LABELS_96 = tuple("ABCDEFGH")
_MAX_COL_96 = 12


@dataclass(frozen=True, order=True)
class Well:
    """A 96-well plate address such as A1 or H12."""

    row: str
    column: int

    def __post_init__(self) -> None:
        row = self.row.upper()
        if row not in _ROW_LABELS_96:
            raise PlateLayoutError(f"Invalid 96-well row {self.row!r}.")
        if not 1 <= self.column <= _MAX_COL_96:
            raise PlateLayoutError(f"Invalid 96-well column {self.column!r}.")
        object.__setattr__(self, "row", row)

    @classmethod
    def parse(cls, value: str) -> Well:
        """Parse a well address like A1."""
        text = value.strip().upper()
        if len(text) < 2:
            raise PlateLayoutError(f"Invalid well address {value!r}.")
        row = text[0]
        column_text = text[1:]
        if not column_text.isdigit():
            raise PlateLayoutError(f"Invalid well address {value!r}.")
        return cls(row=row, column=int(column_text))

    def __str__(self) -> str:
        return f"{self.row}{self.column}"


@dataclass(frozen=True)
class PlateWell:
    """One measured well with role and optional nominal concentration."""

    well: Well
    role: Role
    response: float
    sample_name: str | None = None
    nominal_concentration: float | None = None
    replicate_group: str | None = None


@dataclass
class PlateLayout:
    """Collection of unique wells for a plate run."""

    wells: list[PlateWell]

    def __post_init__(self) -> None:
        seen: set[Well] = set()
        for plate_well in self.wells:
            if plate_well.well in seen:
                raise PlateLayoutError(f"Duplicate well {plate_well.well}.")
            seen.add(plate_well.well)

    def by_role(self, role: Role) -> list[PlateWell]:
        """Return wells with the requested role."""
        return [well for well in self.wells if well.role == role]


@dataclass
class PlateData:
    """Parsed plate data and layout."""

    layout: PlateLayout

    @property
    def wells(self) -> list[PlateWell]:
        return self.layout.wells


def make_plate_well(
    *,
    well: str,
    role: str,
    response: float,
    sample_name: str | None = None,
    nominal_concentration: float | None = None,
    replicate_group: str | None = None,
) -> PlateWell:
    """Validate and construct one plate well."""
    normalized_role = role.strip().lower()
    if normalized_role not in ROLES:
        raise PlateLayoutError(f"Invalid role {role!r}; expected one of {ROLES}.")
    if not np.isfinite(response):
        raise ValueError(f"Well {well} response contains NaN or Inf values.")
    if nominal_concentration is not None and not np.isfinite(nominal_concentration):
        raise ValueError(f"Well {well} concentration contains NaN or Inf values.")

    return PlateWell(
        well=Well.parse(well),
        role=normalized_role,
        response=float(response),
        sample_name=sample_name,
        nominal_concentration=nominal_concentration,
        replicate_group=replicate_group,
    )
