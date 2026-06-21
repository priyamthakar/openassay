"""Plate layout and plate data models."""

from __future__ import annotations

from collections import defaultdict
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

    def missing_wells(self, expected_wells: list[str]) -> list[Well]:
        """Return expected wells that are absent from the layout."""
        observed = {plate_well.well for plate_well in self.wells}
        expected = [Well.parse(well) for well in expected_wells]
        return [well for well in expected if well not in observed]

    def require_wells(self, expected_wells: list[str]) -> None:
        """Raise if any expected wells are absent from the layout."""
        missing = self.missing_wells(expected_wells)
        if missing:
            missing_text = ", ".join(str(well) for well in missing)
            raise PlateLayoutError(f"Missing expected wells: {missing_text}.")


@dataclass
class PlateData:
    """Parsed plate data and layout."""

    layout: PlateLayout

    @property
    def wells(self) -> list[PlateWell]:
        return self.layout.wells

    def blank_response(self) -> float | None:
        """Return the mean blank response, if blank wells are present."""
        blanks = [well.response for well in self.layout.by_role("blank")]
        if not blanks:
            return None
        return float(np.mean(np.asarray(blanks, dtype=np.float64)))

    def collapse_replicates(self, *, subtract_blank: bool = True) -> list[CollapsedReplicate]:
        """Collapse wells by replicate group, optionally subtracting mean blank."""
        blank = self.blank_response() if subtract_blank else None
        groups: dict[tuple[Role, str], list[PlateWell]] = defaultdict(list)
        for well in self.wells:
            if well.role == "blank":
                continue
            group = well.replicate_group or well.sample_name or str(well.well)
            groups[(well.role, group)].append(well)

        collapsed: list[CollapsedReplicate] = []
        for (role, group), wells in sorted(groups.items()):
            responses = np.asarray(
                [well.response - (blank or 0.0) for well in wells],
                dtype=np.float64,
            )
            mean = float(np.mean(responses))
            sd = float(np.std(responses, ddof=1)) if len(responses) > 1 else 0.0
            cv = float(abs(sd / mean) * 100.0) if mean != 0.0 else float("inf")
            collapsed.append(
                CollapsedReplicate(
                    role=role,
                    replicate_group=group,
                    n=len(wells),
                    mean_response=mean,
                    sd_response=sd,
                    cv_percent=cv,
                    sample_name=wells[0].sample_name,
                    nominal_concentration=wells[0].nominal_concentration,
                )
            )
        return collapsed


@dataclass(frozen=True)
class CollapsedReplicate:
    """Replicate-collapsed plate response summary."""

    role: Role
    replicate_group: str
    n: int
    mean_response: float
    sd_response: float
    cv_percent: float
    sample_name: str | None = None
    nominal_concentration: float | None = None


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
