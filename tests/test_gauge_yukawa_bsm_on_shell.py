from __future__ import annotations

import math

import pytest

from physics_lab.search.gauge_yukawa_bsm_on_shell import (
    run_on_shell_campaign,
    singlet_scalar_self_energy,
    vectorlike_fermion_self_energy,
    vectorlike_gauge_msbar_self_energies,
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


def test_singlet_scalar_os_self_energy_is_finite() -> None:
    result = singlet_scalar_self_energy(
        0.01,
        1.0e8,
        singlet_mass_gev=1000.0,
        scale_gev=91.1876,
        p2_gev2=1000.0**2,
        multiplicity=3,
    )
    assert all(math.isfinite(result[key]) for key in ("self_energy_gev2", "derivative_dimensionless", "field_counterterm"))
    assert result["threshold_safe_real_control"] is True


def test_vectorlike_fermion_os_mass_and_field_terms_are_finite() -> None:
    result = vectorlike_fermion_self_energy(0.01, 1.0e8, 1000.0, scale_gev=91.1876, p2_gev2=1.0e16, multiplicity=3)
    assert math.isfinite(result["mass_counterterm_gev"])
    assert math.isfinite(result["field_counterterm"])


def test_gauge_msbar_polarization_keeps_thomson_derivative_and_mixing() -> None:
    result = vectorlike_gauge_msbar_self_energies(
        [0.01, 0.02, 0.03, 0.05, 0.01, 0.004, 0.005, 0.001],
        [{"multiplet": "Q", "multiplicity_decoupled": 1, "mass_gev": 1.0e8}],
        scale_gev=91.1876,
        w_mass_gev=2.46,
        z_mass_gev=2.64,
    )
    assert math.isfinite(result["totals"]["photon"]["derivative_dimensionless"])
    assert math.isfinite(result["totals"]["z_gamma"]["transverse_gev2"])


def test_campaign_closes_successful_cases_and_retains_upstream_failures() -> None:
    report = run_on_shell_campaign({"matching_version": "test-w17", "candidate_results": [_case(), _case("BACKEND_FAILURE")]})
    assert report["execution_status"] == "COMPLETE"
    assert report["scan"]["status_counts"] == {"BSM_ONE_LOOP_ON_SHELL_COMPLETE": 1, "UPSTREAM_FAILURE": 1}
    assert report["selection"]["performed"] is False
    result = report["candidate_results"][0]
    assert result["controls"]["tadpole_counterterm_fixed"] is True
    assert result["controls"]["thomson_charge_counterterm"] is True
    assert result["renormalized_on_shell_residuals"]["higgs_mass"] == pytest.approx(0.0)
    assert result["controls"]["all_couplings_pure_os"] is False
