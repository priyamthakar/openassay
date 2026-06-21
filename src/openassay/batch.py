"""Batch processing helpers for multi-plate assay runs."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TypeVar

from openassay.plate import CollapsedReplicate, PlateData
from openassay.types import Role

InputT = TypeVar("InputT")
ResultT = TypeVar("ResultT")


@dataclass(frozen=True)
class BatchItemResult:
    """Outcome for one item in a batch run."""

    item_id: str
    success: bool
    result: object | None = None
    error: str | None = None


@dataclass(frozen=True)
class BatchResult:
    """Aggregated outcome for a batch run."""

    items: list[BatchItemResult]

    @property
    def passed(self) -> bool:
        """Return True only when every item completed successfully."""
        return all(item.success for item in self.items)

    @property
    def successes(self) -> list[BatchItemResult]:
        """Successful item results."""
        return [item for item in self.items if item.success]

    @property
    def failures(self) -> list[BatchItemResult]:
        """Failed item results."""
        return [item for item in self.items if not item.success]


@dataclass(frozen=True)
class BatchCollapsedReplicate:
    """Replicate summary annotated with its source plate index."""

    plate_index: int
    role: Role
    replicate_group: str
    n: int
    mean_response: float
    sd_response: float
    cv_percent: float
    sample_name: str | None = None
    nominal_concentration: float | None = None


def run_batch(
    items: Sequence[InputT],
    processor: Callable[[InputT], ResultT],
    *,
    item_ids: Sequence[str] | None = None,
) -> BatchResult:
    """Process a batch of items while collecting per-item failures."""
    if item_ids is not None and len(item_ids) != len(items):
        raise ValueError("item_ids length must match items length.")

    results: list[BatchItemResult] = []
    for index, item in enumerate(items):
        item_id = item_ids[index] if item_ids is not None else str(index)
        try:
            result = processor(item)
        except Exception as exc:  # noqa: BLE001 - batch reports must preserve partial failures.
            results.append(BatchItemResult(item_id=item_id, success=False, error=str(exc)))
        else:
            results.append(BatchItemResult(item_id=item_id, success=True, result=result))
    return BatchResult(items=results)


def aggregate_collapsed_replicates(
    plates: Sequence[PlateData],
    *,
    subtract_blank: bool = True,
) -> list[BatchCollapsedReplicate]:
    """Collapse and annotate replicates across multiple plates."""
    aggregated: list[BatchCollapsedReplicate] = []
    for plate_index, plate in enumerate(plates):
        for collapsed in plate.collapse_replicates(subtract_blank=subtract_blank):
            aggregated.append(_annotate_collapsed(plate_index, collapsed))
    return aggregated


def _annotate_collapsed(
    plate_index: int,
    collapsed: CollapsedReplicate,
) -> BatchCollapsedReplicate:
    return BatchCollapsedReplicate(
        plate_index=plate_index,
        role=collapsed.role,
        replicate_group=collapsed.replicate_group,
        n=collapsed.n,
        mean_response=collapsed.mean_response,
        sd_response=collapsed.sd_response,
        cv_percent=collapsed.cv_percent,
        sample_name=collapsed.sample_name,
        nominal_concentration=collapsed.nominal_concentration,
    )
