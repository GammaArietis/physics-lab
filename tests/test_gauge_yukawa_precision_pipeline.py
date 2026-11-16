from __future__ import annotations

import math

from physics_lab.search.gauge_yukawa_precision_pipeline import (
    SM_TWO_LOOP_GAUGE_MATRIX,
    run_precision_campaign,
    run_precision_candidate,
    search_fixed_points,
    two_loop_gauge_matrix,
    vacuum_stability,
)


def _candidate() -> dict:
    return {
        "candidate_id": "precision-Q",
        "multiplicities": {"Q": 1},
        "yukawa_multiplet": "Q",
        "thresholds_gev": {"Q": 1.0e4},
        "initial_state": [0.01, 0.02, 0.03, 0.05, 0.01, 0.005, 0.005, 0.001],
    }


def test_two_loop_matrix_reproduces_sm_control_without_new_matter() -> None:
    assert two_loop_gauge_matrix({}) == SM_TWO_LOOP_GAUGE_MATRIX.tolist()


def test_vectorlike_representation_changes_two_loop_gauge_matrix() -> None:
    base = two_loop_gauge_matrix({})
    extended = two_loop_gauge_matrix({"Q": 1})
    assert extended[0][0] > base[0][0]
    assert extended[1][1] > base[1][1]
    assert extended[2][2] > base[2][2]


def test_fixed_point_search_retains_gaussian_and_critical_exponents() -> None:
    points = search_fixed_points(
        [[0.0] * 8, [0.01] * 8],
        active={"Q": 1},
        yukawa_multiplet="Q",
    )
    assert points
    gaussian = min(points, key=lambda item: max(abs(value) for value in item["couplings"]))
    assert max(abs(value) for value in gaussian["couplings"]) < 1.0e-8
    assert len(gaussian["critical_exponents"]) == 8


def test_precision_candidate_runs_thresholds_and_stability_controls() -> None:
    result = run_precision_candidate(
        _candidate(),
        uv_scale_gev=1.0e6,
        ir_scale_gev=1.0e2,
        fixed_point_seeds=[[0.0] * 8, [0.01] * 8],
    )
    assert result["status"] == "COMPLETE"
    assert result["controls"]["two_loop_gauge_control"] is True
    assert result["matching"]["smdr_status"] == "DEFERRED_EXTERNAL_BACKEND"
    assert math.isfinite(result["ir_observables"]["alpha_em"])


def test_campaign_is_target_blind_and_does_not_select_a_branch() -> None:
    report = run_precision_campaign(
        {
            "campaign_id": "precision-control",
            "uv_scale_gev": 1.0e6,
            "ir_scale_gev": 1.0e2,
            "fixed_point_seeds": [[0.0] * 8, [0.01] * 8],
            "candidates": [_candidate()],
        }
    )
    assert report["execution_status"] == "COMPLETE"
    assert report["controls"]["no_fitting"] is True
    assert report["selection"]["performed"] is False


def test_vacuum_stability_boundary_is_explicit() -> None:
    stable = vacuum_stability([0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.2, -0.1])
    unstable = vacuum_stability([0.0, 0.0, 0.0, 0.0, 0.0, -0.1, 0.2, 0.0])
    assert stable["stable_at_declared_point"] is True
    assert unstable["stable_at_declared_point"] is False
