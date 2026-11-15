"""Tests for the W8 Standard Model, gravity and mixing campaign."""

from __future__ import annotations

import json

from physics_lab.search.sm_gravity_mixing_rg import (
    gravity_abelian_beta,
    gravity_abelian_fixed_points,
    mixing_control_beta,
    reduced_standard_model_beta,
    run_sm_gravity_mixing_campaign,
    write_sm_gravity_mixing_report,
)


def test_reduced_standard_model_gaussian_residual_is_zero() -> None:
    assert reduced_standard_model_beta((0.0, 0.0, 0.0, 0.0, 0.0)) == (0.0, 0.0, 0.0, 0.0, 0.0)


def test_gravity_control_records_nonzero_root_but_not_uv_attraction() -> None:
    roots = gravity_abelian_fixed_points(0.001)
    assert len(roots) == 2
    assert roots[0]["uv_attractive"] is True
    assert roots[1]["uv_attractive"] is False
    assert abs(roots[1]["beta_residual"]) < 1e-12
    assert gravity_abelian_beta(0.0, 0.001) == 0.0


def test_positive_semidefinite_mixing_control_has_gaussian_residual() -> None:
    matrix = ((4.1, 0.5), (0.5, 3.0))
    assert mixing_control_beta((0.0, 0.0), matrix) == (0.0, 0.0)
    assert all(value > 0 for value in mixing_control_beta((0.1, 0.2), matrix))


def test_w8_campaign_runs_all_subcampaigns_without_selection() -> None:
    report = run_sm_gravity_mixing_campaign()
    assert report["execution_status"] == "COMPLETE"
    assert report["subcampaigns"]["reduced_standard_model"]["trajectory_count"] == 4
    assert report["subcampaigns"]["gravity_abelian_control"]["trajectory_count"] == 18
    assert report["subcampaigns"]["multi_u1_mixing_control"]["trajectory_count"] == 9
    assert report["controls"]["sm_physical_non_gaussian_fixed_point_found"] is False
    assert report["controls"]["gravity_abelian_nonzero_uv_fixed_point_found"] is False
    assert report["controls"]["mixing_control_only"] is True
    assert report["selection"]["performed"] is False


def test_report_is_deterministic_and_portable(tmp_path) -> None:
    report = run_sm_gravity_mixing_campaign()
    first = write_sm_gravity_mixing_report(tmp_path / "first.json", report)
    second = write_sm_gravity_mixing_report(tmp_path / "second.json", report)
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
