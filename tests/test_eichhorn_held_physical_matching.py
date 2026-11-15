from __future__ import annotations

from physics_lab.search.eichhorn_held_physical_matching import (
    ELECTROWEAK_VEV_GEV,
    run_physical_matching_campaign,
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
