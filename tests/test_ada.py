"""Tests for ADA cut-point workflows."""

from __future__ import annotations

import pytest

from openassay.ada import ADAResult, confirm_cut_point, screen_cut_point


def negative_controls() -> list[dict[str, object]]:
    return [
        {"sample_id": "d1", "run_id": "r1", "response": 101.0},
        {"sample_id": "d2", "run_id": "r1", "response": 103.0},
        {"sample_id": "d1", "run_id": "r2", "response": 99.0},
        {"sample_id": "d2", "run_id": "r2", "response": 104.0},
    ]


def confirmatory_controls() -> list[dict[str, object]]:
    return [
        {"sample_id": "d1", "run_id": "r1", "percent_inhibition": 14.0},
        {"sample_id": "d2", "run_id": "r1", "percent_inhibition": 18.0},
        {"sample_id": "d1", "run_id": "r2", "percent_inhibition": 16.0},
        {"sample_id": "d2", "run_id": "r2", "percent_inhibition": 20.0},
    ]


def test_screen_cut_point_parametric_uses_false_positive_rate() -> None:
    """Screening cut point should use mean + z*SD for parametric mode."""
    result = screen_cut_point(negative_controls())

    assert isinstance(result, ADAResult)
    assert result.evaluable is True
    assert result.cut_point == pytest.approx(105.397226)
    assert result.fp_rate == 0.05
    assert result.n_samples == 2
    assert result.n_runs == 2
    assert result.excluded_indices == []


def test_screen_cut_point_nonparametric_percentile() -> None:
    """Nonparametric screening should use the upper empirical percentile."""
    result = screen_cut_point(negative_controls(), method="nonparametric", fp_rate=0.25)

    assert result.evaluable is True
    assert result.cut_point == pytest.approx(103.25)


def test_confirm_cut_point_uses_confirmatory_default_fp_rate() -> None:
    """Confirmatory cut point defaults to the stricter 1% false-positive rate."""
    result = confirm_cut_point(confirmatory_controls())

    assert result.evaluable is True
    assert result.fp_rate == 0.01
    assert result.cut_point == pytest.approx(23.006604)


def test_screen_cut_point_tukey_outlier_method_excludes_documented_rows() -> None:
    """Tukey outlier handling should be explicit and reproducible."""
    data = [
        {"sample_id": "d1", "run_id": "r1", "response": 100.0},
        {"sample_id": "d2", "run_id": "r1", "response": 101.0},
        {"sample_id": "d3", "run_id": "r1", "response": 102.0},
        {"sample_id": "d1", "run_id": "r2", "response": 100.0},
        {"sample_id": "d2", "run_id": "r2", "response": 101.0},
        {"sample_id": "d3", "run_id": "r2", "response": 150.0},
    ]

    result = screen_cut_point(data, outlier_method="tukey")

    assert result.evaluable is True
    assert result.excluded_indices == [5]
    assert result.cut_point == pytest.approx(102.176183)
    assert "Excluded 1 observation" in " ".join(result.reasons)


def test_screen_cut_point_default_keeps_outlying_values() -> None:
    """Outlier handling is opt-in, never silent."""
    data = negative_controls() + [{"sample_id": "d3", "run_id": "r2", "response": 150.0}]

    result = screen_cut_point(data)

    assert result.excluded_indices == []
    assert result.cut_point is not None
    assert result.cut_point > 120.0


def test_ada_cut_point_refuses_single_run() -> None:
    """Invariant 8: a single analytical run is not enough biological variability."""
    result = screen_cut_point(
        [
            {"sample_id": "d1", "run_id": "r1", "response": 101.0},
            {"sample_id": "d2", "run_id": "r1", "response": 103.0},
        ]
    )

    assert result.evaluable is False
    assert result.cut_point is None
    assert "two analytical runs" in " ".join(result.reasons)


def test_ada_cut_point_refuses_single_sample() -> None:
    """Invariant 8: one donor sampled across runs is still insufficient."""
    result = screen_cut_point(
        [
            {"sample_id": "d1", "run_id": "r1", "response": 101.0},
            {"sample_id": "d1", "run_id": "r2", "response": 103.0},
        ]
    )

    assert result.evaluable is False
    assert result.cut_point is None
    assert "two biological samples" in " ".join(result.reasons)


def test_ada_cut_point_rejects_non_finite_values() -> None:
    """ADA data must not silently drop or repair non-finite responses."""
    data = negative_controls()
    data[0]["response"] = float("nan")

    with pytest.raises(ValueError, match="finite"):
        screen_cut_point(data)
