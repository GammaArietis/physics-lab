from __future__ import annotations

from physics_lab.search.eichhorn_held_ir_matching import (
    dimensionless_ir_observables,
    integrate_target_blind_trajectory,
    run_ir_matching_campaign,
)


def test_dimensionless_observables_do_not_require_mass_inputs() -> None:
    observables = dimensionless_ir_observables((0.0, 0.0, 0.1, 0.2, 0.3, 0.4, 0.0, 0.05))
    assert observables["gauge_norm"] > 0.0
    assert observables["top_to_qcd_ratio"] is not None
    assert observables["quartic_to_top_squared"] is not None


def test_target_blind_flow_has_explicit_gravity_match_point() -> None:
    trajectory = integrate_target_blind_trajectory(
        (3.2945094357, -4.5139868308, 0.02, 0.03, 0.04, 0.36, 0.0, 0.01),
        gravity_transition_offset=-2.0,
        ir_endpoint_offset=-8.0,
        steps_per_unit=8,
    )
    assert trajectory["status"] == "COMPLETE"
    assert [point["stage"] for point in trajectory["points"]] == ["UV", "GRAVITY_MATCH", "IR"]
    assert trajectory["gravity_decoupled_below_transition"] is True


def test_small_campaign_retain_branches_and_has_no_selection() -> None:
    report = run_ir_matching_campaign(
        transition_offsets=(-2.0,),
        ir_endpoint_offsets=(-8.0,),
        include_neighborhood=False,
        steps_per_unit=6,
    )
    assert report["execution_status"] == "COMPLETE"
    assert report["scan"]["trajectory_count"] > 0
    assert report["scan"]["complete_count"] == report["scan"]["trajectory_count"]
    assert report["controls"]["target_blind_generation"] is True
    assert report["controls"]["no_measured_masses"] is True
    assert report["selection"]["performed"] is False
    assert report["conclusions"]["physical_sm_mass_matching_completed"] is False
