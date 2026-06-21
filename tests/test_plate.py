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


def test_well_parsing_accepts_valid_384_well_addresses_when_explicit() -> None:
    """384-well parsing should be explicit and preserve 96-well defaults."""
    well = Well.parse("p24", plate_size="384")

    assert str(well) == "P24"
    assert well.plate_size == "384"


@pytest.mark.parametrize("address", ["I1", "A13", "A0", "AA1", "1A"])
def test_well_parsing_rejects_invalid_96_well_addresses(address: str) -> None:
    """Invalid 96-well addresses should fail fast."""
    with pytest.raises(PlateLayoutError):
        Well.parse(address)


@pytest.mark.parametrize("address", ["Q1", "A25", "A0", "AA1", "1A"])
def test_well_parsing_rejects_invalid_384_well_addresses(address: str) -> None:
    """Invalid 384-well addresses should fail fast."""
    with pytest.raises(PlateLayoutError):
        Well.parse(address, plate_size="384")


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


def test_read_plate_tidy_csv_384_well(tmp_path) -> None:
    """Tidy CSV plate input should accept 384-well addresses when requested."""
    path = tmp_path / "plate384.csv"
    path.write_text(
        "\n".join(
            [
                "well,role,sample,response,replicate_group",
                "A1,standard,std-1,12.5,std-1",
                "P24,unknown,sample-1,45.0,sample-1",
            ]
        ),
        encoding="utf-8",
    )

    plate = read_plate(path, plate_size="384")

    assert plate.layout.plate_size == "384"
    assert [str(well.well) for well in plate.wells] == ["A1", "P24"]


def test_read_plate_tidy_excel(tmp_path) -> None:
    """Tidy Excel plate input should parse like tidy CSV."""
    import pandas as pd

    path = tmp_path / "plate.xlsx"
    pd.DataFrame(
        [
            {"well": "A1", "role": "standard", "sample": "std-1", "response": 12.5},
            {"well": "A2", "role": "unknown", "sample": "sample-1", "response": 45.0},
        ]
    ).to_excel(path, index=False)

    plate = read_plate(path)

    assert [str(well.well) for well in plate.wells] == ["A1", "A2"]
    assert plate.wells[0].sample_name == "std-1"


def test_read_plate_can_require_expected_wells(tmp_path) -> None:
    """Tidy ingestion should fail when explicitly required wells are absent."""
    path = tmp_path / "plate.csv"
    path.write_text("well,role,response\nA1,standard,12.5\n", encoding="utf-8")

    with pytest.raises(PlateLayoutError, match="Missing expected wells: A2"):
        read_plate(path, expected_wells=["A1", "A2"])


def test_read_plate_matrix_csv_with_layout_map(tmp_path) -> None:
    """Matrix plate input should use a separate tidy layout map."""
    matrix_path = tmp_path / "matrix.csv"
    layout_path = tmp_path / "layout.csv"
    matrix_path.write_text(
        "\n".join(
            [
                ",1,2,3",
                "A,10.0,11.0,12.0",
                "B,20.0,21.0,22.0",
            ]
        ),
        encoding="utf-8",
    )
    layout_path.write_text(
        "\n".join(
            [
                "well,role,sample,concentration,replicate_group",
                "A1,standard,std-1,1.0,std-1",
                "A2,standard,std-1,1.0,std-1",
                "B1,unknown,sample-1,,sample-1",
            ]
        ),
        encoding="utf-8",
    )

    plate = read_plate(matrix_path, format="matrix", layout=layout_path)

    assert [str(well.well) for well in plate.wells] == ["A1", "A2", "B1"]
    assert [well.response for well in plate.wells] == [10.0, 11.0, 20.0]


def test_read_plate_matrix_csv_384_well_with_layout_map(tmp_path) -> None:
    """Matrix 384-well input should accept rows through P and columns through 24."""
    matrix_path = tmp_path / "matrix384.csv"
    layout_path = tmp_path / "layout384.csv"
    matrix_path.write_text(
        "\n".join(
            [
                ",1,24",
                "A,10.0,11.0",
                "P,20.0,21.0",
            ]
        ),
        encoding="utf-8",
    )
    layout_path.write_text(
        "\n".join(
            [
                "well,role,sample,replicate_group",
                "A1,standard,std-1,std-1",
                "P24,unknown,sample-1,sample-1",
            ]
        ),
        encoding="utf-8",
    )

    plate = read_plate(matrix_path, format="matrix", layout=layout_path, plate_size="384")

    assert plate.layout.plate_size == "384"
    assert [str(well.well) for well in plate.wells] == ["A1", "P24"]
    assert [well.response for well in plate.wells] == [10.0, 21.0]


def test_read_plate_matrix_excel_with_excel_layout_map(tmp_path) -> None:
    """Matrix Excel input should use a separate Excel layout map."""
    import pandas as pd

    matrix_path = tmp_path / "matrix.xlsx"
    layout_path = tmp_path / "layout.xlsx"
    pd.DataFrame({"1": [10.0, 20.0], "2": [11.0, 21.0]}, index=["A", "B"]).to_excel(matrix_path)
    pd.DataFrame(
        [
            {"well": "A1", "role": "standard", "sample": "std-1", "concentration": 1.0},
            {"well": "B2", "role": "unknown", "sample": "sample-1"},
        ]
    ).to_excel(layout_path, index=False)

    plate = read_plate(matrix_path, format="matrix", layout=layout_path)

    assert [str(well.well) for well in plate.wells] == ["A1", "B2"]
    assert [well.response for well in plate.wells] == [10.0, 21.0]


def test_read_plate_matrix_requires_layout(tmp_path) -> None:
    """Matrix format should fail clearly without a layout map."""
    matrix_path = tmp_path / "matrix.csv"
    matrix_path.write_text(",1\nA,10.0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="requires a layout"):
        read_plate(matrix_path, format="matrix")


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
