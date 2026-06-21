"""Tests for plate layout and tidy plate ingestion."""

from __future__ import annotations

import pytest

from openassay.errors import PlateLayoutError
from openassay.ingest import read_plate
from openassay.plate import PlateLayout, Well, make_plate_well


def test_well_parsing_accepts_valid_96_well_addresses() -> None:
    """Well addresses should normalize row case and preserve column."""
    assert str(Well.parse("a1")) == "A1"
    assert str(Well.parse("H12")) == "H12"


@pytest.mark.parametrize("address", ["I1", "A13", "A0", "AA1", "1A"])
def test_well_parsing_rejects_invalid_96_well_addresses(address: str) -> None:
    """Invalid 96-well addresses should fail fast."""
    with pytest.raises(PlateLayoutError):
        Well.parse(address)


def test_plate_layout_rejects_duplicate_wells() -> None:
    """A physical well should appear at most once."""
    well = make_plate_well(well="A1", role="standard", response=10.0)

    with pytest.raises(PlateLayoutError, match="Duplicate well"):
        PlateLayout([well, well])


def test_plate_layout_reports_missing_expected_wells() -> None:
    """Layouts should be able to report absent expected wells."""
    layout = PlateLayout([make_plate_well(well="A1", role="standard", response=10.0)])

    missing = layout.missing_wells(["A1", "A2", "B1"])

    assert [str(well) for well in missing] == ["A2", "B1"]


def test_plate_layout_can_require_expected_wells() -> None:
    """Missing expected wells should raise a plate-layout error when required."""
    layout = PlateLayout([make_plate_well(well="A1", role="standard", response=10.0)])

    with pytest.raises(PlateLayoutError, match="Missing expected wells: A2"):
        layout.require_wells(["A1", "A2"])


def test_read_plate_tidy_csv(tmp_path) -> None:
    """Tidy CSV plate input should parse wells, roles, and responses."""
    path = tmp_path / "plate.csv"
    path.write_text(
        "\n".join(
            [
                "well,role,sample,concentration,response,replicate_group",
                "A1,standard,std-1,1.0,12.5,std-1",
                "A2,qc,qc-low,0.8,10.1,qc-low",
                "A3,unknown,sample-1,,45.0,sample-1",
            ]
        ),
        encoding="utf-8",
    )

    plate = read_plate(path)

    assert len(plate.wells) == 3
    assert [str(well.well) for well in plate.wells] == ["A1", "A2", "A3"]
    assert len(plate.layout.by_role("standard")) == 1
    assert plate.wells[2].nominal_concentration is None


def test_read_plate_can_require_expected_wells(tmp_path) -> None:
    """Tidy ingestion should fail when explicitly required wells are absent."""
    path = tmp_path / "plate.csv"
    path.write_text("well,role,response\nA1,standard,12.5\n", encoding="utf-8")

    with pytest.raises(PlateLayoutError, match="Missing expected wells: A2"):
        read_plate(path, expected_wells=["A1", "A2"])


def test_read_plate_rejects_non_finite_response(tmp_path) -> None:
    """NaN plate responses should raise rather than being dropped."""
    path = tmp_path / "plate.csv"
    path.write_text("well,role,response\nA1,standard,nan\n", encoding="utf-8")

    with pytest.raises(ValueError, match="NaN or Inf"):
        read_plate(path)


def test_plate_data_collapses_replicates_with_blank_subtraction(tmp_path) -> None:
    """Replicate collapse should subtract mean blank response when requested."""
    path = tmp_path / "plate.csv"
    path.write_text(
        "\n".join(
            [
                "well,role,sample,concentration,response,replicate_group",
                "A1,blank,blank,,1.0,blank",
                "A2,blank,blank,,3.0,blank",
                "B1,qc,qc-low,10.0,11.0,qc-low",
                "B2,qc,qc-low,10.0,13.0,qc-low",
            ]
        ),
        encoding="utf-8",
    )

    plate = read_plate(path)
    collapsed = plate.collapse_replicates()

    assert plate.blank_response() == pytest.approx(2.0)
    assert len(collapsed) == 1
    assert collapsed[0].replicate_group == "qc-low"
    assert collapsed[0].mean_response == pytest.approx(10.0)
    assert collapsed[0].n == 2


def test_plate_data_can_collapse_without_blank_subtraction(tmp_path) -> None:
    """Blank subtraction should be optional."""
    path = tmp_path / "plate.csv"
    path.write_text(
        "\n".join(
            [
                "well,role,sample,response,replicate_group",
                "A1,blank,blank,2.0,blank",
                "B1,unknown,sample-1,11.0,sample-1",
                "B2,unknown,sample-1,13.0,sample-1",
            ]
        ),
        encoding="utf-8",
    )

    collapsed = read_plate(path).collapse_replicates(subtract_blank=False)

    assert collapsed[0].mean_response == pytest.approx(12.0)
