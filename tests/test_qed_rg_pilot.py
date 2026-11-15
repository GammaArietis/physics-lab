"""Tests for the W4 known-physics one-loop QED RG control pilot."""

from __future__ import annotations

import json
import math

import pytest

from physics_lab.search.qed_rg_pilot import (
    QED_ONE_LOOP_BETA_COEFFICIENT,
    QEDRGPilotError,
    alpha_trajectory,
    beta_alpha,
    run_qed_rg_pilot,
    write_qed_rg_report,
)


def test_one_loop_qed_beta_function_is_reproduced() -> None:
    assert math.isclose(QED_ONE_LOOP_BETA_COEFFICIENT, 2.0 / (3.0 * math.pi), rel_tol=1e-15)
    assert beta_alpha(0.0) == 0.0
    assert math.isclose(beta_alpha(0.1), 2.0 * 0.1**2 / (3.0 * math.pi), rel_tol=1e-15)


def test_report_records_only_the_gaussian_fixed_point() -> None:
    report = run_qed_rg_pilot()
    assert report["execution_status"] == "COMPLETE"
    assert report["fixed_points"] == [
        {
            "coupling": "alpha",
            "value": 0.0,
            "label": "GAUSSIAN",
            "finite_fixed_point": True,
            "interacting": False,
            "infrared_behavior": "ATTRACTIVE",
            "ultraviolet_behavior": "REPULSIVE_AT_ONE_LOOP",
        }
    ]
    assert report["controls"]["gaussian_fixed_point_recorded"] is True
    assert report["controls"]["no_interacting_fixed_point_claimed"] is True


def test_bounded_trajectories_match_the_analytic_flow() -> None:
    report = run_qed_rg_pilot()
    assert len(report["trajectories"]) == 3
    assert all(len(item["points"]) == 5 for item in report["trajectories"])
    for trajectory in report["trajectories"]:
        alpha0 = trajectory["initial_alpha"]
        for point in trajectory["points"]:
            assert math.isclose(
                point["alpha"],
                alpha_trajectory(alpha0, point["log_scale_offset"]),
                rel_tol=1e-15,
            )
    assert report["authorization"]["target_comparison"] == "NOT_AUTHORIZED"
    assert report["authorization"]["target_blind_generation"] is True
    assert report["scope"]["f4_operators"] == "NOT_ACTIVATED"


def test_landau_pole_crossing_is_rejected() -> None:
    with pytest.raises(QEDRGPilotError, match="Landau pole"):
        alpha_trajectory(0.5, 32.0)


def test_report_is_deterministic_and_portable(tmp_path) -> None:
    report = run_qed_rg_pilot()
    first = write_qed_rg_report(tmp_path / "first.json", report)
    second = write_qed_rg_report(tmp_path / "second.json", report)
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
