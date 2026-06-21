"""Tests for batch processing helpers."""

from __future__ import annotations

import pytest

from openassay.batch import BatchResult, aggregate_collapsed_replicates, run_batch
from openassay.ingest import read_plate


def test_run_batch_collects_partial_failures() -> None:
    """A failed item should not abort the rest of a batch."""

    def processor(value: int) -> int:
        if value == 2:
            raise ValueError("bad plate")
        return value * 10

    result = run_batch([1, 2, 3], processor, item_ids=["plate-1", "plate-2", "plate-3"])

    assert isinstance(result, BatchResult)
    assert result.passed is False
    assert [item.item_id for item in result.successes] == ["plate-1", "plate-3"]
    assert [item.result for item in result.successes] == [10, 30]
    assert result.failures[0].item_id == "plate-2"
    assert result.failures[0].error == "bad plate"


def test_run_batch_rejects_mismatched_item_ids() -> None:
    """Item identifiers should align one-to-one with batch inputs."""
    with pytest.raises(ValueError, match="item_ids"):
        run_batch([1, 2], lambda value: value, item_ids=["plate-1"])


def test_aggregate_collapsed_replicates_across_multiple_plates(tmp_path) -> None:
    """Multi-plate aggregation should keep each source plate visible."""
    plate_paths = []
    for index, response in enumerate((11.0, 21.0), start=1):
        path = tmp_path / f"plate-{index}.csv"
        path.write_text(
            "\n".join(
                [
                    "well,role,sample,response,replicate_group",
                    "A1,blank,blank,1.0,blank",
                    f"B1,unknown,sample-{index},{response},sample-{index}",
                    f"B2,unknown,sample-{index},{response + 2.0},sample-{index}",
                ]
            ),
            encoding="utf-8",
        )
        plate_paths.append(path)

    plates = [read_plate(path) for path in plate_paths]
    aggregated = aggregate_collapsed_replicates(plates)

    assert [item.plate_index for item in aggregated] == [0, 1]
    assert [item.replicate_group for item in aggregated] == ["sample-1", "sample-2"]
    assert [item.mean_response for item in aggregated] == pytest.approx([11.0, 21.0])
