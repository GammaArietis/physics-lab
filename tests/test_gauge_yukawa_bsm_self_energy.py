from __future__ import annotations

import math

import pytest

from physics_lab.search.gauge_yukawa_bsm_self_energy import (
    b0_msbar,
    run_bsm_self_energy_campaign,
    scalar_higgs_self_energy,
    vector_transverse_self_energy,
)


def _case(status: str = "SMDR_COMPLETE") -> dict:
    return {
        "case_id": "precision-Q|singlet-mass=1000",
        "status": status,
        "matched_state": [0.01, 0.02, 0.03, 0.05, 0.01, 0.004, 0.005, 0.001],
        "matching": {
            "singlet_mass_gev": 1000.0,
            "vectorlike_threshold_events": [
                {"multiplet": "Q", "multiplicity_decoupled": 1, "mass_gev": 1.0e8}
            ],
        },
        "backend": {
            "parsed": {
                "top_pole_gev": 8.7,
                "higgs_pole_gev": 24.2,
                "z_pole_gev": 2.64,
                "w_pole_gev": 2.46,
                "alpha_sommerfeld_inverse": 240000.0,
            }
        },
    }


def test_equal_mass_b0_is_finite_and_has_zero_subtracted_limit() -> None:
    assert b0_msbar(0.0, 1000.0, 91.1876) == pytest.approx(-math.log((1000.0 / 91.1876) ** 2))
    assert b0_msbar(24.2**2, 1000.0, 91.1876) > b0_msbar(0.0, 1000.0, 91.1876)


def test_singlet_portal_self_energy_and_wavefunction_are_finite() -> None:
    result = scalar_higgs_self_energy(0.001, 1000.0, vev_gev=246.21965, scale_gev=91.1876, p2_gev2=24.2**2)
    assert all(math.isfinite(result[key]) for key in ("self_energy_gev2", "decoupling_subtracted_self_energy_gev2", "derivative_dimensionless", "higgs_residue_factor"))
    assert result["higgs_residue_factor"] > 0.0
    assert abs(result["decoupling_subtracted_self_energy_gev2"]) < abs(result["self_energy_gev2"])


def test_vectorlike_polarization_decouples_for_heavy_mass() -> None:
    light = vector_transverse_self_energy(0.02, 100.0, q2_gev2=2.64**2)
    heavy = vector_transverse_self_energy(0.02, 1.0e8, q2_gev2=2.64**2)
    assert abs(heavy["transverse_gev2"]) < abs(light["transverse_gev2"])


def test_campaign_retains_upstream_failures_without_selection() -> None:
    report = run_bsm_self_energy_campaign({"matching_version": "test-w17", "candidate_results": [_case(), _case("BACKEND_FAILURE")]})
    assert report["execution_status"] == "COMPLETE"
    assert report["scan"]["status_counts"] == {"BSM_ONE_LOOP_COMPLETE": 1, "UPSTREAM_FAILURE": 1}
    assert report["selection"]["performed"] is False
    assert report["controls"]["full_bsm_renormalization_claimed"] is False
    complete = report["candidate_results"][0]
    assert complete["controls"]["higgs_mass_parameter_zero_momentum_subtracted"] is True
