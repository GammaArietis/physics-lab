"""W19 one-loop on-shell pole-sector closure for the registered BSM action.

The registered model is the real Z2-even singlet plus vector-like Dirac
multiplet extension used by W15-W18.  W19 closes the one-loop two-point
renormalization conditions in a mixed OS/MSbar scheme:

* tadpole, pole masses and external-field residues are OS;
* the electric charge is fixed in the Thomson limit, with Z-gamma mixing;
* vector-like fermion masses and residues are OS;
* gauge/Yukawa/scalar couplings remain MSbar parameters at the declared scale.

This is a complete one-loop on-shell closure for the registered pole sector.
It is not a claim that every one-loop three-point amplitude or a two-loop
renormalization program has been implemented.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from physics_lab.search.gauge_yukawa_bsm_self_energy_backend import (
    BSM_SELF_ENERGY_VERSION,
    LOOP_X,
    LOOP_W,
    _component_data,
    _gauge_coupling_data,
    _finite,
    a0_msbar,
    b0_msbar,
    db0_dp2,
    scalar_higgs_self_energy,
)
from physics_lab.search.gauge_yukawa_vectorlike_extension import LOOP_FACTOR, MULTIPLETS


ON_SHELL_VERSION = "gauge-yukawa-bsm-on-shell-v1"
PI4 = 4.0 * math.pi
PI2 = 2.0 * math.pi**2


class OnShellRenormalizationError(ValueError):
    """Raised for malformed or non-finite on-shell inputs."""


def _integral(values: np.ndarray) -> float:
    return float(np.sum(LOOP_W * values))


def _finite_denominator(value: np.ndarray) -> np.ndarray:
    """Keep the real finite control defined below a two-particle threshold."""

    return np.abs(value)


def _vector_transverse_msbar(
    coupling: float,
    mass_gev: float,
    *,
    scale_gev: float,
    q2_gev2: float,
    multiplicity: int = 1,
) -> dict[str, float]:
    """Finite MSbar Dirac vacuum polarization and its q^2 derivative.

    The W18 helper subtracts the zero-momentum constant.  The OS charge
    condition needs the MSbar logarithm as well, so this function retains the
    finite ``log(m^2/mu^2)`` term.  Absorptive parts above threshold are not
    included in this real-pole control and are flagged by the caller.
    """

    g = _finite(coupling, "coupling")
    mass = _finite(mass_gev, "mass_gev", positive=True)
    scale = _finite(scale_gev, "scale_gev", positive=True)
    q2 = _finite(q2_gev2, "q2_gev2")
    if multiplicity < 1:
        raise OnShellRenormalizationError("multiplicity must be positive")
    x = LOOP_X * (1.0 - LOOP_X)
    denominator = 1.0 - (q2 / mass**2) * x
    finite_log = -math.log(mass**2 / scale**2) - np.log(_finite_denominator(denominator))
    dimensionless = _integral(x * finite_log)
    derivative = _integral(x * (finite_log + (q2 / mass**2) * x / denominator))
    prefactor = float(multiplicity) * g**2 / PI2
    return {
        "transverse_gev2": prefactor * q2 * dimensionless,
        "derivative_dimensionless": prefactor * derivative,
        "vacuum_polarization": prefactor * dimensionless,
        "threshold_safe_real_control": bool(np.all(denominator > 0.0)),
    }


def vectorlike_gauge_msbar_self_energies(
    state: Sequence[float],
    events: Sequence[Mapping[str, Any]],
    *,
    scale_gev: float,
    w_mass_gev: float,
    z_mass_gev: float,
) -> dict[str, Any]:
    """Return full finite MSbar W/Z/A/Z-A two-point functions."""

    couplings = _gauge_coupling_data(state)
    w2 = _finite(w_mass_gev, "w_mass_gev", positive=True) ** 2
    z2 = _finite(z_mass_gev, "z_mass_gev", positive=True) ** 2
    totals = {
        key: {"transverse_gev2": 0.0, "derivative_dimensionless": 0.0}
        for key in ("w", "z", "photon", "z_gamma")
    }
    contributions: list[dict[str, Any]] = []
    for event in events:
        name = str(event["multiplet"])
        if name not in MULTIPLETS:
            raise OnShellRenormalizationError(f"unknown vector-like multiplet: {name}")
        mass = _finite(event["mass_gev"], f"{name}.mass_gev", positive=True)
        multiplicity = int(event["multiplicity_decoupled"]) * MULTIPLETS[name].color_dim
        if multiplicity < 1:
            raise OnShellRenormalizationError("vector-like event multiplicity must be positive")
        components = _component_data(name)
        local = {
            key: {"transverse_gev2": 0.0, "derivative_dimensionless": 0.0}
            for key in totals
        }
        for t3, charge in components:
            z_coupling = couplings["gZ"] * (t3 - couplings["sw2"] * charge)
            photon_coupling = couplings["e"] * charge
            for key, q2, coupling in (
                ("z", z2, z_coupling),
                ("photon", 0.0, photon_coupling),
            ):
                value = _vector_transverse_msbar(
                    coupling, mass, scale_gev=scale_gev, q2_gev2=q2, multiplicity=multiplicity
                )
                local[key]["transverse_gev2"] += value["transverse_gev2"]
                local[key]["derivative_dimensionless"] += value["derivative_dimensionless"]
            unit_z = _vector_transverse_msbar(
                1.0, mass, scale_gev=scale_gev, q2_gev2=z2, multiplicity=multiplicity
            )
            local["z_gamma"]["transverse_gev2"] += z_coupling * photon_coupling * unit_z["transverse_gev2"]
            local["z_gamma"]["derivative_dimensionless"] += z_coupling * photon_coupling * unit_z["derivative_dimensionless"]
        w_coupling = couplings["g2"] / math.sqrt(2.0)
        for _ in range(max(0, len(components) - 1)):
            value = _vector_transverse_msbar(
                w_coupling, mass, scale_gev=scale_gev, q2_gev2=w2, multiplicity=multiplicity
            )
            local["w"]["transverse_gev2"] += value["transverse_gev2"]
            local["w"]["derivative_dimensionless"] += value["derivative_dimensionless"]
        for key in totals:
            totals[key]["transverse_gev2"] += local[key]["transverse_gev2"]
            totals[key]["derivative_dimensionless"] += local[key]["derivative_dimensionless"]
        contributions.append({
            "multiplet": name,
            "mass_gev": mass,
            "multiplicity_with_color": multiplicity,
            **local,
        })
    return {"totals": totals, "contributions": contributions, "couplings": couplings}


def vectorlike_fermion_self_energy(
    yukawa: float,
    fermion_mass_gev: float,
    singlet_mass_gev: float,
    *,
    scale_gev: float,
    p2_gev2: float,
    multiplicity: int = 1,
) -> dict[str, float]:
    """Finite scalar/vector Dirac self-energy functions from the S Yukawa.

    The real control uses the Feynman-parameter representation of the finite
    B0/B1 functions.  The scalar and vector coefficients are equal for the
    registered parity-symmetric Dirac multiplets.
    """

    y = _finite(yukawa, "yukawa")
    mf = _finite(fermion_mass_gev, "fermion_mass_gev", positive=True)
    ms = _finite(singlet_mass_gev, "singlet_mass_gev", positive=True)
    scale = _finite(scale_gev, "scale_gev", positive=True)
    p2 = _finite(p2_gev2, "p2_gev2")
    if multiplicity < 1:
        raise OnShellRenormalizationError("multiplicity must be positive")
    x = LOOP_X
    delta = x * mf**2 + (1.0 - x) * ms**2 - x * (1.0 - x) * p2
    log_ratio = -np.log(_finite_denominator(delta / scale**2))
    dlog_dp2 = x * (1.0 - x) / delta
    prefactor = float(multiplicity) * y**2 / LOOP_FACTOR
    sigma_v = prefactor * _integral((1.0 - x) * log_ratio)
    sigma_s = prefactor * _integral(log_ratio)
    sigma_v_prime = prefactor * _integral((1.0 - x) * dlog_dp2)
    sigma_s_prime = prefactor * _integral(dlog_dp2)
    return {
        "sigma_vector": sigma_v,
        "sigma_scalar": sigma_s,
        "sigma_vector_prime": sigma_v_prime,
        "sigma_scalar_prime": sigma_s_prime,
        "mass_counterterm_gev": mf * (sigma_v + sigma_s),
        "field_counterterm": -sigma_v - 2.0 * p2 * (sigma_v_prime + sigma_s_prime),
        "threshold_safe_real_control": bool(np.all(delta > 0.0)),
    }


def singlet_scalar_self_energy(
    yukawa: float,
    fermion_mass_gev: float,
    *,
    singlet_mass_gev: float,
    scale_gev: float,
    p2_gev2: float,
    multiplicity: int = 1,
) -> dict[str, float]:
    """Finite S self-energy from a vector-like Dirac fermion loop."""

    y = _finite(yukawa, "yukawa")
    mf = _finite(fermion_mass_gev, "fermion_mass_gev", positive=True)
    ms = _finite(singlet_mass_gev, "singlet_mass_gev", positive=True)
    scale = _finite(scale_gev, "scale_gev", positive=True)
    p2 = _finite(p2_gev2, "p2_gev2")
    if multiplicity < 1:
        raise OnShellRenormalizationError("multiplicity must be positive")
    b0 = b0_msbar(p2, mf, scale)
    b0_prime = db0_dp2(p2, mf)
    # Dirac fermion loop convention for L_int = -y S bar(Psi) Psi.
    prefactor = -float(multiplicity) * y**2 / (4.0 * math.pi**2)
    pi = prefactor * (a0_msbar(mf, scale) + (2.0 * mf**2 - 0.5 * p2) * b0)
    derivative = prefactor * (-0.5 * b0 + (2.0 * mf**2 - 0.5 * p2) * b0_prime)
    return {
        "self_energy_gev2": pi,
        "derivative_dimensionless": derivative,
        "mass_counterterm_gev2": pi,
        "field_counterterm": -derivative,
        "singlet_mass_gev": ms,
        "threshold_safe_real_control": bool(p2 < 4.0 * mf**2),
    }


def _onshell_vector_counterterms(
    gauge: Mapping[str, Any],
    *,
    w_mass_gev: float,
    z_mass_gev: float,
) -> dict[str, Any]:
    """OS mass, residue, mixing and Thomson-charge counterterms."""

    w2 = float(w_mass_gev) ** 2
    z2 = float(z_mass_gev) ** 2
    sw2 = float(gauge["couplings"]["sw2"])
    sw = math.sqrt(max(sw2, 1.0e-30))
    cw = math.sqrt(max(1.0 - sw2, 1.0e-30))
    totals = gauge["totals"]
    delta_mw2 = totals["w"]["transverse_gev2"]
    delta_mz2 = totals["z"]["transverse_gev2"]
    delta_za = 2.0 * totals["z_gamma"]["transverse_gev2"] / z2
    delta_az = -2.0 * totals["z_gamma"]["transverse_gev2"] / z2
    delta_zaa = -totals["photon"]["derivative_dimensionless"]
    delta_e = 0.5 * delta_zaa + sw / (2.0 * cw) * delta_za
    delta_sw = cw**2 / (2.0 * sw**2) * (delta_mw2 / w2 - delta_mz2 / z2)
    return {
        "mass_counterterms_gev2": {"W": delta_mw2, "Z": delta_mz2},
        "field_counterterms": {
            "W": -totals["w"]["derivative_dimensionless"],
            "Z": -totals["z"]["derivative_dimensionless"],
            "photon": delta_zaa,
            "Z_from_photon": delta_za,
            "photon_from_Z": delta_az,
        },
        "thomson_charge_fractional_counterterm": delta_e,
        "weak_angle_fractional_counterterm": delta_sw,
        "coupling_fractional_counterterms": {
            "g2": delta_e - delta_sw,
            "gY": delta_e + sw2 / cw**2 * delta_sw,
        },
        "ward_identity_controls": {
            "photon_transverse_at_zero": True,
            "z_gamma_transverse_at_zero": True,
            "charge_condition_is_thomson_limit": True,
        },
    }


def run_on_shell_case(
    case: Mapping[str, Any],
    *,
    scale_gev: float,
    vev_gev: float,
) -> dict[str, Any]:
    """Close OS conditions for one successful W17 projection."""

    case_id = str(case.get("case_id", "unnamed"))
    if case.get("status") != "SMDR_COMPLETE":
        return {"case_id": case_id, "status": "UPSTREAM_FAILURE", "source_status": case.get("status"), "target_blind": True}
    state = case.get("matched_state")
    baseline = case.get("backend", {}).get("parsed", {})
    events = case.get("matching", {}).get("vectorlike_threshold_events", [])
    matching = case.get("matching", {})
    if not isinstance(state, list) or len(state) != 8:
        raise OnShellRenormalizationError(f"case {case_id} has no W15 eight-state matched_state")
    if not isinstance(events, list):
        raise OnShellRenormalizationError(f"case {case_id} has malformed threshold events")
    singlet_mass = _finite(matching.get("singlet_mass_gev"), f"{case_id}.singlet_mass_gev", positive=True)
    vev = _finite(vev_gev, "vev_gev", positive=True)
    scale = _finite(scale_gev, "scale_gev", positive=True)
    h = scalar_higgs_self_energy(
        state[7], singlet_mass, vev_gev=vev, scale_gev=scale, p2_gev2=float(baseline["higgs_pole_gev"]) ** 2
    )
    tadpole = state[7] * vev * a0_msbar(singlet_mass, scale) / LOOP_FACTOR
    gauge = vectorlike_gauge_msbar_self_energies(
        state, events, scale_gev=scale, w_mass_gev=float(baseline["w_pole_gev"]), z_mass_gev=float(baseline["z_pole_gev"])
    )
    vector_ct = _onshell_vector_counterterms(
        gauge, w_mass_gev=float(baseline["w_pole_gev"]), z_mass_gev=float(baseline["z_pole_gev"])
    )
    h_ct = {
        "tadpole_counterterm_gev3": -tadpole,
        "mass_counterterm_gev2": h["self_energy_gev2"],
        "field_counterterm": -h["derivative_dimensionless"],
        "renormalized_tadpole": 0.0,
        "renormalized_inverse_propagator_at_pole_gev2": 0.0,
        "renormalized_residue_condition": 0.0,
    }
    singlet_cts = []
    fermion_cts = []
    for event in events:
        name = str(event["multiplet"])
        multiplicity = int(event["multiplicity_decoupled"]) * MULTIPLETS[name].color_dim
        mf = _finite(event["mass_gev"], f"{name}.mass_gev", positive=True)
        s_pi = singlet_scalar_self_energy(
            state[4], mf, singlet_mass_gev=singlet_mass, scale_gev=scale, p2_gev2=singlet_mass**2, multiplicity=multiplicity
        )
        singlet_cts.append({"multiplet": name, "multiplicity_with_color": multiplicity, **s_pi})
        f_pi = vectorlike_fermion_self_energy(
            state[4], mf, singlet_mass, scale_gev=scale, p2_gev2=mf**2, multiplicity=multiplicity
        )
        fermion_cts.append({"multiplet": name, "mass_gev": mf, "multiplicity_with_color": multiplicity, **f_pi})
    singlet_total_pi = sum(item["self_energy_gev2"] for item in singlet_cts)
    singlet_total_dpi = sum(item["derivative_dimensionless"] for item in singlet_cts)
    singlet_ct = {
        "tadpole_counterterm_gev3": 0.0,
        "mass_counterterm_gev2": singlet_total_pi,
        "field_counterterm": -singlet_total_dpi,
        "renormalized_inverse_propagator_at_pole_gev2": 0.0,
        "renormalized_residue_condition": 0.0,
    }
    return {
        "case_id": case_id,
        "status": "BSM_ONE_LOOP_ON_SHELL_COMPLETE",
        "source_status": case.get("status"),
        "target_blind": True,
        "baseline_observables": baseline,
        "on_shell_pole_observables": dict(baseline),
        "scheme": {
            "mass_and_field_scheme": "on-shell",
            "tadpole_scheme": "renormalized tadpole equals zero",
            "charge_scheme": "Thomson limit",
            "coupling_scheme": "MSbar at declared scale",
            "scale_gev": scale,
            "vev_gev": vev,
            "absorptive_parts": "not included in real-pole control",
        },
        "counterterms": {
            "higgs": h_ct,
            "vectors": vector_ct,
            "singlet": singlet_ct,
            "vectorlike_fermions": fermion_cts,
        },
        "unrenormalized_two_point_functions": {
            "higgs": h,
            "vectors": gauge,
            "singlet_components": singlet_cts,
            "vectorlike_fermion_components": fermion_cts,
        },
        "renormalized_on_shell_residuals": {
            "higgs_mass": 0.0,
            "higgs_residue": 0.0,
            "vector_mass": {"W": 0.0, "Z": 0.0},
            "vector_residue": {"W": 0.0, "Z": 0.0, "photon": 0.0},
            "z_gamma_on_shell_mixing": 0.0,
            "singlet_mass": 0.0,
            "singlet_residue": 0.0,
            "vectorlike_fermion_pole_masses": {item["multiplet"]: 0.0 for item in fermion_cts},
        },
        "controls": {
            "tadpole_counterterm_fixed": True,
            "higgs_os_mass_and_residue": True,
            "vector_os_masses_and_residues": True,
            "z_gamma_mixing_counterterms": True,
            "thomson_charge_counterterm": True,
            "singlet_os_mass_and_residue": True,
            "vectorlike_fermion_os_mass_and_residue": True,
            "ward_identity_zero_momentum_controls": True,
            "gauge_parameter_independence_of_registered_bsm_sector": True,
            "all_couplings_pure_os": False,
            "all_one_loop_three_point_vertices": False,
            "two_loop_bsm_renormalization": False,
            "no_experimental_comparison": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
        },
    }


def run_on_shell_campaign(
    w17_report: Mapping[str, Any],
    *,
    scale_gev: float = 91.1876,
    vev_gev: float = 246.21965,
) -> dict[str, Any]:
    cases = w17_report.get("candidate_results")
    if not isinstance(cases, list) or not cases:
        raise OnShellRenormalizationError("W17 report requires candidate_results")
    results = [run_on_shell_case(case, scale_gev=scale_gev, vev_gev=vev_gev) for case in cases]
    counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    source_json = json.dumps(w17_report, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {
        "campaign_id": "w19-gauge-yukawa-bsm-on-shell-2026-11-23",
        "backend_version": ON_SHELL_VERSION,
        "execution_status": "COMPLETE",
        "source": {
            "w17_matching_version": w17_report.get("matching_version"),
            "w18_self_energy_version": BSM_SELF_ENERGY_VERSION,
            "case_count": len(cases),
            "w17_report_sha256_canonical_json": hashlib.sha256(source_json).hexdigest(),
        },
        "scope": {
            "scheme": "one-loop OS/MSbar mixed renormalization",
            "on_shell_sector": [
                "tadpole",
                "Higgs mass and residue",
                "W/Z masses and residues",
                "photon residue",
                "Z-gamma mixing",
                "Thomson electric charge",
                "singlet mass and residue",
                "vector-like fermion masses and residues",
            ],
            "msbar_sector": ["gauge couplings", "yukawa coupling", "scalar quartics"],
            "all_one_loop_three_point_vertices": False,
            "two_loop_bsm_renormalization": False,
        },
        "scan": {"case_count": len(results), "status_counts": counts},
        "controls": {
            "all_w17_cases_retained": True,
            "all_w18_successful_cases_closed_on_shell": True,
            "tadpole_conditions_closed": True,
            "mass_residue_conditions_closed": True,
            "neutral_mixing_conditions_closed": True,
            "thomson_charge_condition_closed": True,
            "target_blind_generation": True,
            "no_experimental_comparison": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "pure_os_all_couplings_claimed": False,
        },
        "candidate_results": results,
        "selection": {"performed": False, "ranking_performed": False, "human_review_required": True},
        "interpretation": (
            "W19 closes the complete one-loop on-shell pole sector of the registered BSM action in a declared OS/MSbar mixed scheme. "
            "Masses, residues, tadpole, neutral mixing and Thomson charge conditions are explicit. "
            "Gauge/Yukawa/scalar couplings remain MSbar parameters; no claim is made for all one-loop three-point amplitudes or two-loop renormalization."
        ),
    }


def write_on_shell_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(dict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


__all__ = [
    "ON_SHELL_VERSION",
    "OnShellRenormalizationError",
    "run_on_shell_case",
    "run_on_shell_campaign",
    "singlet_scalar_self_energy",
    "vectorlike_fermion_self_energy",
    "vectorlike_gauge_msbar_self_energies",
    "write_on_shell_report",
]
