"""Tests for the bounded alpha-geometry stage-0 pilot."""

from __future__ import annotations

import pytest

from physics_lab.search.alpha_geometry_pilot import (
    AlphaGeometryPilotError,
    enumerate_alpha_geometry_pilot,
    run_alpha_geometry_pilot,
)


def test_stage0_pilot_is_finite_deduplicated_and_not_empirical() -> None:
    report = run_alpha_geometry_pilot()

    assert report["execution_status"] == "COMPLETE"
    assert report["raw_candidate_count"] == 30
    assert report["unique_candidate_count"] == 28
    assert report["duplicate_count"] == 2
    assert all(report["controls"].values())
    assert report["selection"]["performed"] is False
    assert report["selection"]["ranking_performed"] is False
    assert all(item["alpha_comparison"] == "NOT_AUTHORIZED" for item in report["candidates"])


def test_cycle_three_is_deduplicated_with_complete_three() -> None:
    report = enumerate_alpha_geometry_pilot(sizes=[3], actions=["quadratic_laplacian"])

    assert report["raw_candidate_count"] == 3
    assert report["unique_candidate_count"] == 2
    assert report["duplicate_count"] == 1
    assert report["duplicates"][0]["duplicate_of"] == "alpha-geometry-complete-n3-quadratic_laplacian"


def test_stage0_rejects_unbounded_or_undeclared_grammar() -> None:
    with pytest.raises(AlphaGeometryPilotError, match="bounded integers"):
        enumerate_alpha_geometry_pilot(sizes=[100])
    with pytest.raises(AlphaGeometryPilotError, match="declared grammar"):
        enumerate_alpha_geometry_pilot(graph_families=["arbitrary_manifold"])
