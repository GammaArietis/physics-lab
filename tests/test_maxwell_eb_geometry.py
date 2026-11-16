from __future__ import annotations

import math

from physics_lab.search.maxwell_eb_geometry import evaluate_geometry, run_maxwell_geometry_campaign


def test_null_plane_wave_has_orthogonal_fields_and_equal_energy() -> None:
    result = evaluate_geometry(electric=(1.0, 0.0, 0.0), magnetic=(0.0, 1.0 / 299792458.0, 0.0), propagation=(0.0, 0.0, 1.0))
    assert result["maxwell_action_invariants"]["F_squared_zero_for_null_wave"] is True
    assert result["maxwell_action_invariants"]["F_dual_F_zero_for_orthogonal_wave"] is True
    assert math.isclose(result["geometry"]["electric_to_magnetic_energy_ratio"], 1.0)
    assert math.isclose(result["geometry"]["poynting_parallel_to_propagation"], 1.0)


def test_geometry_campaign_is_target_blind_and_keeps_all_records() -> None:
    report = run_maxwell_geometry_campaign({"magnetic_ratios": [1.0], "angles_degrees": [0.0, 90.0]})
    assert report["scan"]["candidate_count"] == 2
    assert report["controls"]["alpha_not_used_during_generation"] is True
    assert report["selection"]["performed"] is False
    assert all(math.isclose(value, 1.0) for value in report["late_comparison"]["electric_to_magnetic_energy_ratios"])

