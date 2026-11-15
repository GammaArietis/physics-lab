from __future__ import annotations

from physics_lab.search.eichhorn_held_physical_matching import (
    ELECTROWEAK_VEV_GEV,
    ThresholdSchedule,
    run_physical_matching_campaign,
    sm_matching_beta,
)


def test_physical_matching_has_explicit_dimensional_scales_and_scope() -> None:
    report = run_physical_matching_campaign(
        transition_offsets=(-2.0,),
        loop_modes=("one-loop-sm", "two-loop-gauge-control"),
        threshold_schedules=({"id": "no-decoupling", "top_over_v": None, "higgs_over_v": None, "ew_over_v": None},),
        include_neighborhood=False,
        steps_per_unit=3,
    )
    assert report["execution_status"] in {"COMPLETE", "PARTIAL_FAILURES_RETAINED"}
    assert report["scope"]["uv_scale_gev"] > 1e18
    assert report["scope"]["electroweak_matching_scale_gev"] == ELECTROWEAK_VEV_GEV
    assert report["controls"]["comparison_last"] is True
    assert report["controls"]["full_sm_nnlo_not_claimed"] is True


def test_physical_matching_retains_comparison_separate_from_selection() -> None:
    report = run_physical_matching_campaign(
        transition_offsets=(-2.0,),
        loop_modes=("two-loop-gauge-control",),
        threshold_schedules=({"id": "threshold-central", "top_over_v": 0.75, "higgs_over_v": 0.50, "ew_over_v": 0.40},),
        include_neighborhood=False,
        compare_experiment=True,
        steps_per_unit=2,
    )
    assert report["experimental_comparison"]["performed_after_generation"] is True
    assert report["experimental_comparison"]["used_for_fit"] is False
    assert report["selection"]["performed"] is False


def test_two_loop_top_dominance_is_distinct_from_gauge_only_control() -> None:
    state = (0.35, 0.65, 1.10, 0.90, 0.02, 0.065)
    schedule = ThresholdSchedule("no-decoupling", None, None, None)
    gauge_only = sm_matching_beta(
        state,
        loop_mode="two-loop-gauge-control",
        scale_gev=ELECTROWEAK_VEV_GEV,
        thresholds=schedule,
    )
    full_top = sm_matching_beta(
        state,
        loop_mode="two-loop-sm-top-dominance",
        scale_gev=ELECTROWEAK_VEV_GEV,
        thresholds=schedule,
    )
    assert full_top[3] != gauge_only[3]
    assert full_top[5] != gauge_only[5]
