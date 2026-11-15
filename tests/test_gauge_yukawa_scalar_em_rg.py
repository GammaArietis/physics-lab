"""Tests for the W7 scalar-completed coupled RG campaign."""

from __future__ import annotations

import json

from physics_lab.search.gauge_yukawa_scalar_em_rg import (
    beta_vector,
    fixed_point_branches,
    run_gauge_yukawa_scalar_em_campaign,
    stability_matrix,
    write_gauge_yukawa_scalar_em_report,
)


def test_scalar_branches_have_zero_residuals() -> None:
    result = fixed_point_branches(0.05)
    assert len(result["branches"]) == 2
    for branch in result["branches"]:
        assert max(abs(value) for value in branch["residual"]) < 1e-12
        assert branch["physical_gauge_yukawa"] is True
    assert result["alpha_em_nonzero_fixed_point"] is False


def test_fp1_and_fp2_are_retained_without_selection() -> None:
    result = fixed_point_branches(0.01)
    labels = {branch["label"] for branch in result["branches"]}
    assert labels == {"FP1_STABLE_POTENTIAL_CANDIDATE", "FP2_UNSTABLE_POTENTIAL_CANDIDATE"}
    for branch in result["branches"]:
        state = (0.0, branch["alpha_g"], branch["alpha_y"], branch["alpha_h"], branch["alpha_v"])
        assert len(stability_matrix(0.01, state)) == 5


def test_scalar_completed_campaign_executes_all_branches() -> None:
    report = run_gauge_yukawa_scalar_em_campaign()
    assert report["execution_status"] == "COMPLETE"
    assert report["epsilon_count"] == 8
    assert report["fixed_point_count"] == 8
    assert report["trajectory_count"] == 48
    assert report["electromagnetic_conclusion"]["nonzero_alpha_em_fixed_point_found"] is False
    assert report["controls"]["two_scalar_branches_recorded"] is True
    assert report["selection"]["performed"] is False


def test_report_is_deterministic_and_portable(tmp_path) -> None:
    report = run_gauge_yukawa_scalar_em_campaign()
    first = write_gauge_yukawa_scalar_em_report(tmp_path / "first.json", report)
    second = write_gauge_yukawa_scalar_em_report(tmp_path / "second.json", report)
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
