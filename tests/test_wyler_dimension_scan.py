"""Tests for the bounded abstract-dimension Wyler scan."""

from __future__ import annotations

import pytest

from physics_lab.search.wyler_dimension_scan import (
    WylerDimensionScanError,
    run_wyler_dimension_scan,
)


def test_dimension_scan_keeps_physical_spacetime_dimension_four() -> None:
    report = run_wyler_dimension_scan(target_alpha_inverse=137.035999177)

    assert report["execution_status"] == "COMPLETE"
    assert report["dimensions"]["abstract_domain_dimensions"] == [3, 4, 5, 6, 7, 8, 9]
    assert report["dimensions"]["physical_spacetime_dimension"] == 4
    assert report["dimensions"]["physical_dimension_scan"] == "NOT_PERFORMED"
    assert all(report["controls"].values())
    assert report["selection"]["performed"] is False
    assert report["selection"]["ranking_performed"] is False


def test_dimension_five_reproduces_wyler_anchor() -> None:
    report = run_wyler_dimension_scan(target_alpha_inverse=137.035999177)
    n5 = next(item for item in report["candidates"] if item["abstract_domain_dimension"] == 5)

    assert n5["status"] == "HISTORICAL_ANCHOR_REPRODUCED"
    assert n5["alpha_inverse"] == pytest.approx(137.0360824481643, rel=1e-12)
    assert abs(n5["relative_error_ppm"]) < 1


def test_dimension_scan_rejects_unbounded_dimensions() -> None:
    with pytest.raises(WylerDimensionScanError, match="bounded integers"):
        run_wyler_dimension_scan(target_alpha_inverse=137.035999177, dimensions=[2, 33])
