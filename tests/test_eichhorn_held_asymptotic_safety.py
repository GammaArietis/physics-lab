from __future__ import annotations

import math

from physics_lab.search.eichhorn_held_asymptotic_safety import (
    DEFAULT_INITIAL_STATES,
    beta_gravity,
    f_g,
    f_lambda,
    f_y,
    gravity_equation_fixed_point,
    literature_anchor_audit,
    matter_fixed_points,
    run_eichhorn_held_campaign,
)


def test_published_threshold_functions_are_finite_away_from_poles() -> None:
    assert all(math.isfinite(function(-4.51)) for function in (f_g, f_y, f_lambda))


def test_printed_gravity_equations_have_a_separate_root_from_quoted_anchor() -> None:
    audit = literature_anchor_audit()
    assert audit["anchor_max_residual"] > 1.0
    assert audit["equation_root"]["max_residual"] < 1e-8


def test_equation_root_is_a_positive_newton_negative_lambda_root() -> None:
    root = gravity_equation_fixed_point()
    assert root["status"] == "COMPLETE"
    assert root["positive_newton"] is True
    assert root["negative_cosmological_constant"] is True
    assert max(abs(value) for value in beta_gravity(root["state"])) < 1e-8


def test_matter_fixed_points_retain_the_gaussian_branch() -> None:
    points = matter_fixed_points(G_N=3.29, Lambda=-4.51)
    assert points
    assert any(max(abs(value) for value in point["state"]) < 1e-8 for point in points)
    assert all(point["max_residual"] < 1e-8 for point in points)


def test_full_campaign_is_target_blind_and_deterministic_in_shape() -> None:
    report = run_eichhorn_held_campaign()
    assert report["execution_status"] == "COMPLETE"
    assert report["scan"]["parameter_slices"] == 45
    assert report["scan"]["initial_state_count"] == len(DEFAULT_INITIAL_STATES)
    assert report["scan"]["trajectory_count"] == 3
    assert report["scan"]["trajectory_status_counts"] == {"COMPLETE": 3}
    assert report["conclusions"]["nonzero_cosmological_constant_included"] is True
    assert report["conclusions"]["literature_anchor_reproduced_without_adjustment"] is False
    assert report["conclusions"]["alpha_one_over_137_derived"] is False
    assert report["selection"]["performed"] is False
    assert report["selection"]["ranking_performed"] is False
