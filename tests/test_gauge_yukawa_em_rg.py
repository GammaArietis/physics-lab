"""Tests for the W6 literature-anchored coupled RG campaign."""

from __future__ import annotations

import json
import math

from physics_lab.search.gauge_yukawa_em_rg import (
    beta_vector,
    gauge_yukawa_fixed_point,
    run_gauge_yukawa_em_campaign,
    stability_matrix,
    write_gauge_yukawa_em_report,
)


def test_litim_sannino_fixed_point_is_physical_for_small_epsilon() -> None:
    result = gauge_yukawa_fixed_point(0.05)
    interacting = result["interacting"]
    assert interacting["physical"] is True
    assert interacting["perturbative"] is True
    assert interacting["alpha_em"] == 0.0
    assert interacting["alpha_g"] > 0
    assert interacting["alpha_y"] > 0
    residual = beta_vector(0.05, (0.0, interacting["alpha_g"], interacting["alpha_y"]))
    assert max(abs(value) for value in residual) < 1e-12


def test_fixed_point_has_nontrivial_gauge_yukawa_but_gaussian_abelian_sector() -> None:
    result = gauge_yukawa_fixed_point(0.01)
    eigenvalues = stability_matrix(0.01, (0.0, result["interacting"]["alpha_g"], result["interacting"]["alpha_y"]))
    assert eigenvalues[0][0] == 0.0
    assert result["alpha_em_nonzero_fixed_point"] is False
    assert result["interacting"]["alpha_g"] != 0.0
    assert result["interacting"]["alpha_y"] != 0.0


def test_campaign_records_all_epsilon_values_and_em_trajectories() -> None:
    report = run_gauge_yukawa_em_campaign()
    assert report["execution_status"] == "COMPLETE"
    assert report["epsilon_count"] == 8
    assert report["fixed_point_count"] == 8
    assert report["trajectory_count"] == 24
    assert report["physical_interacting_fixed_point_count"] == 8
    assert report["electromagnetic_conclusion"]["nonzero_alpha_em_fixed_point_found"] is False
    assert report["controls"]["no_automatic_selection"] is True
    assert report["controls"]["alpha_em_not_used_as_fit_target"] is True


def test_report_is_deterministic_and_portable(tmp_path) -> None:
    report = run_gauge_yukawa_em_campaign()
    first = write_gauge_yukawa_em_report(tmp_path / "first.json", report)
    second = write_gauge_yukawa_em_report(tmp_path / "second.json", report)
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
