"""Tests for the broad one-loop QED threshold RG campaign."""

from __future__ import annotations

import json
import math

import pytest

from physics_lab.search.qed_rg_pilot import alpha_trajectory
from physics_lab.search.qed_threshold_rg_campaign import (
    QEDThresholdRGCampaignError,
    alpha_threshold_trajectory,
    run_qed_threshold_rg_campaign,
    write_qed_threshold_rg_report,
)


THRESHOLDS = ({"log_scale_offset": 2.0, "fermion_flavours_after": 2},)


def test_threshold_flow_matches_w4_before_first_threshold() -> None:
    result = alpha_threshold_trajectory(0.05, 1.0, thresholds=THRESHOLDS)
    assert math.isclose(result["alpha"], alpha_trajectory(0.05, 1.0), rel_tol=1e-15)
    assert result["active_fermion_flavours"] == 1
    assert result["threshold_crossings"] == 0


def test_threshold_matching_is_continuous() -> None:
    at_threshold = alpha_threshold_trajectory(0.05, 2.0, thresholds=THRESHOLDS)
    just_after = alpha_threshold_trajectory(0.05, 2.0 + 1e-10, thresholds=THRESHOLDS)
    assert at_threshold["threshold_crossings"] == 1
    assert math.isclose(at_threshold["alpha"], just_after["alpha"], rel_tol=1e-9, abs_tol=1e-12)
    assert just_after["active_fermion_flavours"] == 2


def test_broad_campaign_executes_all_registered_points() -> None:
    report = run_qed_threshold_rg_campaign()
    assert report["execution_status"] == "COMPLETE"
    assert report["scenario_count"] == 5
    assert report["trajectory_count"] == 40
    assert report["point_count"] == 680
    assert report["controls"]["threshold_continuity_rule_explicit"] is True
    assert report["controls"]["only_gaussian_fixed_point_claimed"] is True
    assert report["authorization"]["target_comparison"] == "NOT_AUTHORIZED"
    assert all(item["status"] == "COMPLETE" for item in report["scenarios"])


def test_threshold_schedule_must_be_strictly_increasing() -> None:
    with pytest.raises(QEDThresholdRGCampaignError, match="strictly increasing"):
        alpha_threshold_trajectory(
            0.05,
            3.0,
            thresholds=(
                {"log_scale_offset": 2.0, "fermion_flavours_after": 2},
                {"log_scale_offset": 1.0, "fermion_flavours_after": 3},
            ),
        )


def test_report_is_deterministic_and_portable(tmp_path) -> None:
    report = run_qed_threshold_rg_campaign()
    first = write_qed_threshold_rg_report(tmp_path / "first.json", report)
    second = write_qed_threshold_rg_report(tmp_path / "second.json", report)
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
