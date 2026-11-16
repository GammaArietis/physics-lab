from __future__ import annotations

import math

import pytest

from physics_lab.search.gauge_yukawa_threshold_eft import (
    GaugeYukawaExtensionError,
    run_threshold_campaign,
    run_threshold_candidate,
    thresholded_gauge_coefficients,
)


def _candidate(mass: float = 1.0e4) -> dict:
    return {
        "candidate_id": "threshold-Q",
        "multiplicities": {"Q": 1},
        "yukawa_multiplet": "Q",
        "thresholds_gev": {"Q": mass},
        "initial_state": [0.20, 0.20, 0.20, 0.10, 0.05, 0.02, 0.02, 0.01],
    }


def test_threshold_changes_are_derived_from_active_representation() -> None:
    above = thresholded_gauge_coefficients(1.0e6, {"Q": 1}, {"Q": 1.0e4})
    below = thresholded_gauge_coefficients(1.0e2, {"Q": 1}, {"Q": 1.0e4})
    assert above["g1"] > below["g1"]
    assert above["g2"] > below["g2"]
    assert above["g3"] > below["g3"]


def test_threshold_candidate_runs_action_to_ir_observables() -> None:
    report = run_threshold_candidate(_candidate(), uv_scale_gev=1.0e6, ir_scale_gev=1.0e2)
    assert report["status"] == "COMPLETE"
    assert len(report["segments"]) == 2
    assert len(report["threshold_events"]) == 1
    assert report["controls"]["continuous_dimensionless_matching"] is True
    assert math.isfinite(report["ir_observables"]["alpha_em"])


def test_zero_gauge_seed_remains_zero_through_thresholds() -> None:
    candidate = _candidate()
    candidate["initial_state"][:3] = [0.0, 0.0, 0.0]
    report = run_threshold_candidate(candidate, uv_scale_gev=1.0e6, ir_scale_gev=1.0e2)
    assert report["status"] == "ZERO_PROTECTED"
    assert report["final_state"][:3] == [0.0, 0.0, 0.0]


def test_campaign_retains_all_threshold_branches_without_selection() -> None:
    activation = {
        "campaign_id": "threshold-control",
        "uv_scale_gev": 1.0e6,
        "ir_scale_gev": 1.0e2,
        "candidates": [_candidate(), {**_candidate(1.0e5), "candidate_id": "threshold-Q-high"}],
    }
    report = run_threshold_campaign(activation)
    assert report["execution_status"] == "COMPLETE"
    assert report["scan"]["candidate_count"] == 2
    assert report["controls"]["no_alpha_target_used"] is True
    assert report["selection"]["performed"] is False


def test_present_multiplet_requires_explicit_threshold() -> None:
    candidate = _candidate()
    candidate["thresholds_gev"] = {}
    with pytest.raises(GaugeYukawaExtensionError):
        run_threshold_candidate(candidate, uv_scale_gev=1.0e6, ir_scale_gev=1.0e2)
