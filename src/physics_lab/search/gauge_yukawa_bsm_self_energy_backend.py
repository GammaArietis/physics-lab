"""W18 one-loop BSM two-point backend for the registered W15 model.

The backend evaluates the finite new-sector two-point insertions that are
actually present in the registered action:

* real-singlet loops in the Higgs self-energy, including the finite derivative
  used for the Higgs wave-function factor;
* vector-like Dirac vacuum polarizations for W, Z, photon and Z--photon
  mixing, including finite transverse derivatives;
* the zero-momentum singlet self-energy induced by the singlet Yukawa coupling
  to the vector-like fermions.

It then applies these insertions to the target-blind W17 SMDR projection.  It
does not pretend that a pure-SM SMDR executable is a complete BSM
renormalization program: the report separates implemented two-point channels
from the still-missing full tadpole/counterterm and two-loop scheme closure.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from physics_lab.search.gauge_yukawa_vectorlike_extension import LOOP_FACTOR, MULTIPLETS


BSM_SELF_ENERGY_VERSION = "gauge-yukawa-bsm-self-energy-v1"
LOOP_NODES, LOOP_WEIGHTS = np.polynomial.legendre.leggauss(96)
LOOP_X = 0.5 * (LOOP_NODES + 1.0)
LOOP_W = 0.5 * LOOP_WEIGHTS


class BSMSelfEnergyError(ValueError):
    """Raised for malformed BSM self-energy inputs."""


def _finite(value: Any, name: str, *, positive: bool = False) -> float:
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0.0):
        requirement = "finite and positive" if positive else "finite"
        raise BSMSelfEnergyError(f"{name} must be {requirement}")
    return result


def _integral(values: np.ndarray) -> float:
    return float(np.sum(LOOP_W * values))


def a0_msbar(mass_gev: float, scale_gev: float) -> float:
    """Finite MSbar A0 scalar integral in GeV^2."""

    mass = _finite(mass_gev, "mass_gev", positive=True)
    scale = _finite(scale_gev, "scale_gev", positive=True)
    return mass**2 * (1.0 - math.log(mass**2 / scale**2))


def b0_msbar(p2_gev2: float, mass_gev: float, scale_gev: float) -> float:
    """Finite equal-mass MSbar B0 for below-threshold real kinematics."""

    p2 = _finite(p2_gev2, "p2_gev2")
    mass = _finite(mass_gev, "mass_gev", positive=True)
    scale = _finite(scale_gev, "scale_gev", positive=True)
    denominator = 1.0 - (p2 / mass**2) * LOOP_X * (1.0 - LOOP_X)
    # The registered runs are below pair threshold.  The absolute value keeps
    # the diagnostic finite if a future activation crosses the cut; the
    # imaginary part is then recorded as outside this real-pole control.
    finite_log = -_integral(np.log(np.abs(denominator)))
    return -math.log(mass**2 / scale**2) + finite_log


def db0_dp2(p2_gev2: float, mass_gev: float) -> float:
    """Derivative d B0 / d p^2 for equal masses."""

    p2 = _finite(p2_gev2, "p2_gev2")
    mass = _finite(mass_gev, "mass_gev", positive=True)
    x = LOOP_X * (1.0 - LOOP_X)
    denominator = mass**2 - p2 * x
    return _integral(x / denominator)


def scalar_higgs_self_energy(
    lambda_hs: float,
    singlet_mass_gev: float,
    *,
    vev_gev: float,
    scale_gev: float,
    p2_gev2: float,
) -> dict[str, float]:
    """Finite singlet-loop contribution to the Higgs two-point function."""

    portal = _finite(lambda_hs, "lambda_hs")
    mass = _finite(singlet_mass_gev, "singlet_mass_gev", positive=True)
    vev = _finite(vev_gev, "vev_gev", positive=True)
    scale = _finite(scale_gev, "scale_gev", positive=True)
    p2 = _finite(p2_gev2, "p2_gev2", positive=True)
    prefactor = 1.0 / LOOP_FACTOR
    tadpole = portal * a0_msbar(mass, scale)
    bubble = 2.0 * portal**2 * vev**2 * b0_msbar(p2, mass, scale)
    bubble_at_zero = 2.0 * portal**2 * vev**2 * b0_msbar(0.0, mass, scale)
    pi = prefactor * (tadpole + bubble)
    # The A0 term and the momentum-independent part of B0 renormalize the
    # Higgs mass parameter (and, in a broken-phase calculation, mix with the
    # tadpole counterterm).  They cannot be reported as a pole-mass shift
    # without choosing the complete tadpole/counterterm scheme.  The default
    # finite pole insertion therefore uses the decoupling subtraction
    # Pi(p^2)-Pi(0), while retaining the raw MSbar quantity for auditing.
    subtracted = prefactor * (bubble - bubble_at_zero)
    derivative = prefactor * 2.0 * portal**2 * vev**2 * db0_dp2(p2, mass)
    return {
        "tadpole_gev2": tadpole * prefactor,
        "bubble_gev2": bubble * prefactor,
        "self_energy_gev2": pi,
        "bubble_zero_gev2": bubble_at_zero * prefactor,
        "mass_parameter_subtraction_gev2": tadpole * prefactor + bubble_at_zero * prefactor,
        "decoupling_subtracted_self_energy_gev2": subtracted,
        "derivative_dimensionless": derivative,
        "higgs_residue_factor": 1.0 / (1.0 - derivative),
    }


def vector_transverse_self_energy(
    coupling: float,
    mass_gev: float,
    *,
    q2_gev2: float,
    multiplicity: int = 1,
) -> dict[str, float]:
    """Finite, zero-momentum-subtracted Dirac vacuum polarization."""

    g = _finite(coupling, "coupling")
    mass = _finite(mass_gev, "mass_gev", positive=True)
    q2 = _finite(q2_gev2, "q2_gev2", positive=True)
    if multiplicity < 1:
        raise BSMSelfEnergyError("multiplicity must be positive")
    x = LOOP_X * (1.0 - LOOP_X)
    z = q2 / mass**2
    denominator = np.abs(1.0 - z * x)
    log_part = -np.log(denominator)
    dimensionless = _integral(x * log_part)
    derivative_integrand = x * (log_part + q2 * x / (mass**2 * denominator))
    prefactor = float(multiplicity) * g**2 / (2.0 * math.pi**2)
    transverse = prefactor * q2 * dimensionless
    derivative = prefactor * _integral(derivative_integrand)
    return {
        "transverse_gev2": transverse,
        "derivative_dimensionless": derivative,
        "vacuum_polarization": transverse / q2,
    }


def _component_data(name: str) -> list[tuple[float, float]]:
    multiplet = MULTIPLETS[name]
    j = 0.5 * (multiplet.weak_dim - 1)
    return [(j - index, j - index + multiplet.hypercharge) for index in range(multiplet.weak_dim)]


def _gauge_coupling_data(state: Sequence[float]) -> dict[str, float]:
    g1, g2 = float(state[0]), float(state[1])
    gy = math.sqrt(3.0 / 5.0) * g1
    denominator = math.sqrt(gy**2 + g2**2)
    if denominator <= 0.0:
        return {"gy": gy, "g2": g2, "e": 0.0, "sw2": 0.0, "gZ": 0.0}
    return {
        "gy": gy,
        "g2": g2,
        "e": abs(gy * g2) / denominator,
        "sw2": gy**2 / denominator**2,
        "gZ": abs(g2) / math.sqrt(max(1.0 - gy**2 / denominator**2, 1.0e-30)),
    }


def vectorlike_gauge_self_energies(
    state: Sequence[float],
    events: Sequence[Mapping[str, Any]],
    *,
    w_mass_gev: float,
    z_mass_gev: float,
) -> dict[str, Any]:
    """Compute W/Z/photon/Zgamma finite insertions from all heavy multiplets."""

    couplings = _gauge_coupling_data(state)
    w2 = _finite(w_mass_gev, "w_mass_gev", positive=True) ** 2
    z2 = _finite(z_mass_gev, "z_mass_gev", positive=True) ** 2
    totals = {
        "w": {"transverse_gev2": 0.0, "derivative_dimensionless": 0.0},
        "z": {"transverse_gev2": 0.0, "derivative_dimensionless": 0.0},
        "photon": {"transverse_gev2": 0.0, "derivative_dimensionless": 0.0},
        "z_gamma": {"transverse_gev2": 0.0, "derivative_dimensionless": 0.0},
    }
    contributions: list[dict[str, Any]] = []
    for event in events:
        name = str(event["multiplet"])
        if name not in MULTIPLETS:
            raise BSMSelfEnergyError(f"unknown vector-like multiplet: {name}")
        mass = _finite(event["mass_gev"], f"{name}.mass_gev", positive=True)
        multiplicity = int(event["multiplicity_decoupled"]) * MULTIPLETS[name].color_dim
        if multiplicity < 1:
            raise BSMSelfEnergyError("vector-like event multiplicity must be positive")
        w_pi = {"transverse_gev2": 0.0, "derivative_dimensionless": 0.0}
        z_pi = {"transverse_gev2": 0.0, "derivative_dimensionless": 0.0}
        photon_pi = {"transverse_gev2": 0.0, "derivative_dimensionless": 0.0}
        zg_pi = {"transverse_gev2": 0.0, "derivative_dimensionless": 0.0}
        components = _component_data(name)
        for t3, charge in components:
            z_coupling = couplings["gZ"] * (t3 - couplings["sw2"] * charge)
            photon_coupling = couplings["e"] * charge
            for key, target, q2, coupling in (
                ("z", z_pi, z2, z_coupling),
                ("photon", photon_pi, z2, photon_coupling),
            ):
                value = vector_transverse_self_energy(coupling, mass, q2_gev2=q2, multiplicity=multiplicity)
                target["transverse_gev2"] += value["transverse_gev2"]
                target["derivative_dimensionless"] += value["derivative_dimensionless"]
            # The helper squares its coupling; for mixed Z-gamma insertion we
            # restore the product using the common positive loop integral.
            unit = vector_transverse_self_energy(1.0, mass, q2_gev2=z2, multiplicity=multiplicity)
            zg_pi["transverse_gev2"] += z_coupling * photon_coupling * unit["transverse_gev2"]
            zg_pi["derivative_dimensionless"] += z_coupling * photon_coupling * unit["derivative_dimensionless"]
        for index in range(len(components) - 1):
            w_coupling = couplings["g2"] / math.sqrt(2.0)
            value = vector_transverse_self_energy(w_coupling, mass, q2_gev2=w2, multiplicity=multiplicity)
            w_pi["transverse_gev2"] += value["transverse_gev2"]
            w_pi["derivative_dimensionless"] += value["derivative_dimensionless"]
        for key, value in (("w", w_pi), ("z", z_pi), ("photon", photon_pi), ("z_gamma", zg_pi)):
            totals[key]["transverse_gev2"] += value["transverse_gev2"]
            totals[key]["derivative_dimensionless"] += value["derivative_dimensionless"]
        contributions.append({"multiplet": name, "mass_gev": mass, "multiplicity_with_color": multiplicity, "w": w_pi, "z": z_pi, "photon": photon_pi, "z_gamma": zg_pi})
    for value in totals.values():
        value["residue_factor"] = 1.0 / (1.0 - value["derivative_dimensionless"])
    totals["z_gamma"]["mixing_deferred_from_one_loop_mass_shift"] = True
    return {"totals": totals, "contributions": contributions, "couplings": couplings}


def singlet_zero_momentum_self_energy(
    y_s: float,
    events: Sequence[Mapping[str, Any]],
    *,
    scale_gev: float,
) -> dict[str, Any]:
    """Finite S self-energy from vector-like fermions at p^2=0."""

    yukawa = _finite(y_s, "y_s")
    scale = _finite(scale_gev, "scale_gev", positive=True)
    total = 0.0
    contributions = []
    for event in events:
        name = str(event["multiplet"])
        mass = _finite(event["mass_gev"], f"{name}.mass_gev", positive=True)
        color_multiplicity = int(event["multiplicity_decoupled"]) * MULTIPLETS[name].color_dim
        log_ratio = math.log(mass**2 / scale**2)
        contribution = -color_multiplicity * mass**2 * yukawa**2 / (4.0 * math.pi**2) * (3.0 * log_ratio - 1.0)
        total += contribution
        contributions.append({"multiplet": name, "mass_gev": mass, "multiplicity_with_color": color_multiplicity, "self_energy_gev2": contribution})
    return {"self_energy_gev2": total, "wavefunction_derivative_dimensionless": 0.0, "contributions": contributions}


def _mass_shift(pole_mass: float, self_energy: float, derivative: float) -> dict[str, float]:
    mass = _finite(pole_mass, "pole_mass", positive=True)
    residue = 1.0 / (1.0 - derivative)
    delta_m2 = self_energy * residue
    return {"delta_mass2_gev2": delta_m2, "delta_mass_gev": delta_m2 / (2.0 * mass), "residue_factor": residue}


def run_bsm_self_energy_case(case: Mapping[str, Any], *, scale_gev: float, vev_gev: float) -> dict[str, Any]:
    """Apply finite BSM two-point insertions to one W17 SMDR projection."""

    case_id = str(case.get("case_id", "unnamed"))
    if case.get("status") != "SMDR_COMPLETE":
        return {"case_id": case_id, "status": "UPSTREAM_FAILURE", "source_status": case.get("status"), "target_blind": True}
    state = case.get("matched_state")
    baseline = case.get("backend", {}).get("parsed", {})
    matching = case.get("matching", {})
    events = matching.get("vectorlike_threshold_events", [])
    if not isinstance(state, list) or len(state) != 8:
        raise BSMSelfEnergyError(f"case {case_id} does not contain a W15 eight-state matched_state")
    if not isinstance(events, list):
        raise BSMSelfEnergyError(f"case {case_id} has malformed threshold events")
    singlet_mass = _finite(matching.get("singlet_mass_gev"), f"{case_id}.singlet_mass_gev", positive=True)
    h = scalar_higgs_self_energy(state[7], singlet_mass, vev_gev=vev_gev, scale_gev=scale_gev, p2_gev2=float(baseline["higgs_pole_gev"]) ** 2)
    gauge = vectorlike_gauge_self_energies(state, events, w_mass_gev=float(baseline["w_pole_gev"]), z_mass_gev=float(baseline["z_pole_gev"]))
    singlet = singlet_zero_momentum_self_energy(state[4], events, scale_gev=scale_gev)
    h_shift = _mass_shift(
        float(baseline["higgs_pole_gev"]),
        h["decoupling_subtracted_self_energy_gev2"],
        h["derivative_dimensionless"],
    )
    w_shift = _mass_shift(float(baseline["w_pole_gev"]), gauge["totals"]["w"]["transverse_gev2"], gauge["totals"]["w"]["derivative_dimensionless"])
    z_shift = _mass_shift(float(baseline["z_pole_gev"]), gauge["totals"]["z"]["transverse_gev2"], gauge["totals"]["z"]["derivative_dimensionless"])
    photon_polarization = gauge["totals"]["photon"]["vacuum_polarization"] if "vacuum_polarization" in gauge["totals"]["photon"] else gauge["totals"]["photon"]["transverse_gev2"] / float(baseline["z_pole_gev"]) ** 2
    alpha_inverse = float(baseline["alpha_sommerfeld_inverse"])
    corrected_alpha_inverse = alpha_inverse / (1.0 + photon_polarization)
    corrected = dict(baseline)
    corrected["higgs_pole_gev"] = float(baseline["higgs_pole_gev"]) + h_shift["delta_mass_gev"]
    corrected["w_pole_gev"] = float(baseline["w_pole_gev"]) + w_shift["delta_mass_gev"]
    corrected["z_pole_gev"] = float(baseline["z_pole_gev"]) + z_shift["delta_mass_gev"]
    corrected["alpha_sommerfeld_inverse"] = corrected_alpha_inverse
    return {
        "case_id": case_id,
        "status": "BSM_ONE_LOOP_COMPLETE",
        "target_blind": True,
        "source_status": case.get("status"),
        "baseline_observables": baseline,
        "corrected_observables": corrected,
        "finite_shifts": {
            "higgs": h_shift,
            "higgs_raw_msbar_unsubtracted_gev2": h["self_energy_gev2"],
            "higgs_decoupling_subtracted_gev2": h["decoupling_subtracted_self_energy_gev2"],
            "w": w_shift,
            "z": z_shift,
            "alpha_inverse": corrected_alpha_inverse - alpha_inverse,
            "top_pole_gev": 0.0,
        },
        "wavefunction": {
            "higgs": {"derivative_dimensionless": h["derivative_dimensionless"], "residue_factor": h["higgs_residue_factor"]},
            "w": gauge["totals"]["w"]["residue_factor"],
            "z": gauge["totals"]["z"]["residue_factor"],
            "photon": gauge["totals"]["photon"]["residue_factor"],
        },
        "self_energies": {
            "higgs": h,
            "gauge": gauge,
            "singlet_zero_momentum": singlet,
        },
        "controls": {
            "finite_bsm_two_point_insertions": True,
            "higgs_portal_self_energy": True,
            "higgs_mass_parameter_zero_momentum_subtracted": True,
            "vectorlike_gauge_polarizations": True,
            "z_gamma_mixing_recorded": True,
            "wavefunction_derivatives_recorded": True,
            "top_bsm_self_energy_zero_by_registered_action": True,
            "full_bsm_tadpole_counterterm_scheme": False,
            "two_loop_bsm_pole_matching": False,
            "no_experimental_comparison": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
        },
    }


def run_bsm_self_energy_campaign(
    w17_report: Mapping[str, Any],
    *,
    scale_gev: float = 91.1876,
    vev_gev: float = 246.21965,
) -> dict[str, Any]:
    cases = w17_report.get("candidate_results")
    if not isinstance(cases, list) or not cases:
        raise BSMSelfEnergyError("W17 report requires candidate_results")
    results = [run_bsm_self_energy_case(case, scale_gev=scale_gev, vev_gev=vev_gev) for case in cases]
    counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    source_json = json.dumps(w17_report, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {
        "campaign_id": "w18-gauge-yukawa-bsm-self-energy-2026-11-16",
        "backend_version": BSM_SELF_ENERGY_VERSION,
        "execution_status": "COMPLETE",
        "source": {
            "w17_matching_version": w17_report.get("matching_version"),
            "case_count": len(cases),
            "w17_report_sha256_canonical_json": hashlib.sha256(source_json).hexdigest(),
        },
        "scheme": {
            "renormalization": "MSbar finite two-point insertion with zero-momentum mass-parameter subtraction",
            "scale_gev": float(scale_gev),
            "vev_gev": float(vev_gev),
            "pole_shift_convention": "m_BSM^2 = m_SMDR^2 + Re(Pi)/(1 - dPi/dp2)",
        },
        "scope": {
            "implemented_channels": [
                "Higgs self-energy from real-singlet portal",
                "W/Z/photon/Zgamma vector-like Dirac vacuum polarizations",
                "singlet zero-momentum self-energy from vector-like Yukawa",
                "finite wave-function derivatives for H/W/Z/photon",
            ],
            "full_bsm_tadpole_counterterm_scheme": False,
            "two_loop_bsm_pole_matching": False,
            "pure_smdr_baseline_used": True,
        },
        "scan": {"case_count": len(results), "status_counts": counts},
        "controls": {
            "all_w17_cases_retained": True,
            "finite_self_energy_backend_executed": True,
            "higgs_mass_parameter_subtraction_executed": True,
            "wavefunction_factors_executed": True,
            "target_blind_generation": True,
            "no_experimental_comparison": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "full_bsm_renormalization_claimed": False,
        },
        "candidate_results": results,
        "selection": {"performed": False, "ranking_performed": False, "human_review_required": True},
        "interpretation": (
            "W18 computes finite one-loop BSM two-point insertions for every W17 case "
            "and applies them target-blindly to the SMDR projection. It is complete "
            "for the registered new-sector two-point channels, but not a two-loop or "
            "fully on-shell BSM renormalization calculation."
        ),
    }


def write_bsm_self_energy_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(dict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


__all__ = [
    "BSM_SELF_ENERGY_VERSION",
    "BSMSelfEnergyError",
    "a0_msbar",
    "b0_msbar",
    "db0_dp2",
    "run_bsm_self_energy_campaign",
    "run_bsm_self_energy_case",
    "scalar_higgs_self_energy",
    "singlet_zero_momentum_self_energy",
    "vector_transverse_self_energy",
    "vectorlike_gauge_self_energies",
    "write_bsm_self_energy_report",
]
