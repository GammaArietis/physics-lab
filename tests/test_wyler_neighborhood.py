"""Tests for the Wyler anchor and pre-registered neighborhood."""

from __future__ import annotations

import pytest

from physics_lab.search.wyler_neighborhood import (
    WylerNeighborhoodError,
    run_wyler_neighborhood_pilot,
    wyler_anchor,
)


def test_wyler_anchor_reproduces_historical_value() -> None:
    anchor = wyler_anchor()

    assert anchor["candidate_id"] == "wyler-anchor"
    assert anchor["alpha_inverse"] == pytest.approx(137.0360824481643, rel=1e-12)
    assert anchor["free_continuous_parameters"] == []


def test_wyler_neighborhood_is_finite_and_keeps_all_variants() -> None:
    report = run_wyler_neighborhood_pilot(target_alpha_inverse=137.035999177)

    assert report["execution_status"] == "COMPLETE"
    assert report["grammar"]["candidate_count"] == 18
    assert len(report["variants"]) == 18
    assert sum(item["status"] == "REFERENCE_ANCHOR" for item in report["variants"]) == 1
    assert all(report["controls"].values())
    assert report["selection"]["performed"] is False
    assert report["selection"]["ranking_performed"] is False


def test_wyler_neighborhood_rejects_invalid_target() -> None:
    with pytest.raises(WylerNeighborhoodError, match="positive finite"):
        run_wyler_neighborhood_pilot(target_alpha_inverse=0.0)
