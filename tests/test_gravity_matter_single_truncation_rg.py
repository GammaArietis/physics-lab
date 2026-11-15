"""Tests for the W10 correlated gravity--matter truncation campaign."""

from __future__ import annotations

import json

from physics_lab.search.gravity_matter_single_truncation_rg import (
    correlated_coefficients,
    run_gravity_matter_single_truncation_campaign,
    source_beta_vector,
    source_fixed_points,
    threshold_integral,
    write_gravity_matter_single_truncation_report,
)


def test_published_universal_limits_are_correlated_and_regulator_independent() -> None:
    standard_litim = correlated_coefficients(setting="standard", regulator="litim", a=0.0)
    standard_exponential = correlated_coefficients(setting="standard", regulator="exponential", a=0.0)
    assert standard_litim["f_g"] == 10.0 / 17.0
    assert standard_litim["f_lambda"] == -38.0 / 17.0
    assert standard_litim["f_y"] == -173.0 / 272.0
    assert standard_litim["f_g"] == standard_exponential["f_g"]
    assert standard_litim["f_lambda"] == standard_exponential["f_lambda"]
    assert standard_litim["f_y"] == standard_exponential["f_y"]


def test_threshold_integral_and_newton_fixed_point_are_finite_away_from_limit() -> None:
    assert threshold_integral(1.0, 2.0, regulator="litim", a=0.5) < 0.0
    assert threshold_integral(1.0, 2.0, regulator="exponential", a=0.5) < 0.0
    record = correlated_coefficients(setting="standard", regulator="litim", a=0.5)
    assert record["G_star"] > 0.0
    assert record["f_g"] > 0.0


def test_source_gauge_and_yukawa_branches_have_zero_residual() -> None:
    record = correlated_coefficients(setting="standard", regulator="litim", a=0.0)
    points = source_fixed_points(f_g=record["f_g"], f_y=record["f_y"], f_lambda=record["f_lambda"])
    assert any(point["state"][0] > 0.0 for point in points)
    assert all(point["max_residual"] < 1e-9 for point in points)
    assert source_beta_vector((0.0, 0.0, 0.0), f_g=record["f_g"], f_y=record["f_y"], f_lambda=record["f_lambda"]) == (0.0, 0.0, 0.0)


def test_w10_campaign_records_lambda_closure_failure_without_invention() -> None:
    report = run_gravity_matter_single_truncation_campaign()
    assert report["execution_status"] == "COMPLETE"
    assert report["scan"]["parameter_slices"] == 40
    assert report["scan"]["trajectory_count"] == 80
    assert report["conclusions"]["common_f_g_f_y_f_lambda_derivation"] is True
    assert report["cosmological_constant_audit"]["single_source_requirement_satisfied"] is False
    assert report["controls"]["nonzero_lambda_extension_not_invented"] is True
    assert report["conclusions"]["alpha_one_over_137_derived"] is False
    assert report["selection"]["performed"] is False


def test_report_is_deterministic_and_portable(tmp_path) -> None:
    report = run_gravity_matter_single_truncation_campaign()
    first = write_gravity_matter_single_truncation_report(tmp_path / "first.json", report)
    second = write_gravity_matter_single_truncation_report(tmp_path / "second.json", report)
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
