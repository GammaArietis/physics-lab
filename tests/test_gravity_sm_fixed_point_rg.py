"""Tests for the W9 gravity-dressed Standard Model campaign."""

from __future__ import annotations

import json

from physics_lab.search.gravity_sm_fixed_point_rg import (
    beta_vector,
    fixed_points,
    run_gravity_sm_fixed_point_campaign,
    write_gravity_sm_fixed_point_report,
)


def test_gauge_control_has_gaussian_and_abelian_root() -> None:
    points = fixed_points(0.001, 0.0, 0.0)
    assert len(points) >= 2
    assert any(point["g1_nonzero"] for point in points)
    assert all(point["max_residual"] < 1e-9 for point in points)


def test_nonabelian_roots_remain_gaussian_for_positive_f_g() -> None:
    points = fixed_points(0.001, 0.001, 0.001)
    assert all(abs(point["state"][1]) < 1e-12 for point in points)
    assert all(abs(point["state"][2]) < 1e-12 for point in points)


def test_gravity_dressed_yukawa_and_higgs_branches_are_retained() -> None:
    points = fixed_points(0.001, 0.001, 0.001)
    assert any(point["yukawa_nonzero"] for point in points)
    assert any(point["higgs_quartic_nonzero"] for point in points)
    assert beta_vector((0.0, 0.0, 0.0, 0.0, 0.0), f_g=0.001, f_y=0.001, f_lambda=0.001) == (0.0,) * 5


def test_w9_campaign_is_broad_and_unselected() -> None:
    report = run_gravity_sm_fixed_point_campaign()
    assert report["execution_status"] == "COMPLETE"
    assert report["scan"]["parameter_slices"] == 96
    assert report["scan"]["trajectory_count"] == 384
    assert report["scan"]["fixed_point_count"] > 0
    assert report["controls"]["common_quantum_gravity_fixed_point_not_claimed"] is True
    assert report["conclusions"]["alpha_one_over_137_derived"] is False
    assert report["selection"]["performed"] is False


def test_report_is_deterministic_and_portable(tmp_path) -> None:
    report = run_gravity_sm_fixed_point_campaign()
    first = write_gravity_sm_fixed_point_report(tmp_path / "first.json", report)
    second = write_gravity_sm_fixed_point_report(tmp_path / "second.json", report)
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
