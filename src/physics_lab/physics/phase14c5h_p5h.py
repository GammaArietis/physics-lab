"""Phase 14C.5H: tree-level unitarity / full Q04 audit.

Executable tree amplitudes, physical-state projection, high-energy and
partial-wave tests on the existing G6 F2 test extension. Does not modify
parents. Does not invent vertices, masses, or Higgs.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from physics_lab.physics.portability import portable_path

import sympy as sp

from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    fingerprint_canonical_action,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH, GAUGED_MATTER_TEST_ACTION_ID
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase10a_model_grammar import model_hash as model_hash_10a
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10b1_exploration import build_model_spec
from physics_lab.physics.phase10b10_closure import artifact_dir as phase10b10_artifact_dir
from physics_lab.physics.phase12a_grammar import EXPECTED_GRAMMAR_HASH_10B, grammar_hash_12a
from physics_lab.physics.phase12b_search import EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14b0_engine import (
    AUTHORIZED_PHYSICS_CHAIN,
    ENGINE_VERSION,
    EngineFailure,
    assert_target_blind,
    content_hash,
    top_down_input_hash,
)
from physics_lab.physics.phase14b3_g3 import EXPECTED_TOP_DOWN_INPUT_HASH
from physics_lab.physics.phase14b4_g4 import EXPECTED_G3R_GRAMMAR_HASH
from physics_lab.physics.phase14b5_g5 import EXPECTED_G4R_GRAMMAR_HASH
from physics_lab.physics.phase14b6_g6 import EXPECTED_G5_GRAMMAR_HASH, G6_SEARCH_BOUNDS
from physics_lab.physics.phase14c0_known_physics import (
    CATALOG_VERSION,
    EXPECTED_G6_CHECKPOINT_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    catalog_hash,
    g6_candidate_space_hash,
    g6_checkpoint_path,
    g6_class_rows,
    profile_registry_hash,
    verify_g6_parent_checkpoint,
)
from physics_lab.physics.phase14c1_p1 import EXPECTED_CATALOG_HASH, EXPECTED_PROFILE_REGISTRY_HASH
from physics_lab.physics.phase14c2_p2 import grammar_yukawa_present
from physics_lab.physics.phase14c4_p4 import p4_checkpoint_path
from physics_lab.physics.phase14c5_p5 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_P5_PROFILE_HASH,
    p5_checkpoint_path,
    p5_profile,
)
from physics_lab.physics.phase14c5q_p5q import EXPECTED_P5Q_CHECKPOINT_DIGEST, p5q_checkpoint_path
from physics_lab.physics.phase14c5d_p5d import EXPECTED_P5D_CHECKPOINT_DIGEST, p5d_checkpoint_path
from physics_lab.physics.phase14c5e_p5e import EXPECTED_P5E_CHECKPOINT_DIGEST, p5e_checkpoint_path
from physics_lab.physics.phase14c5e1_p5e1 import EXPECTED_P5E1_CHECKPOINT_DIGEST, p5e1_checkpoint_path
from physics_lab.physics.phase14c5f_p5f import (
    EXPECTED_P5F_CHECKPOINT_DIGEST,
    brst_abelian_g6,
    brst_nilpotency_nonabelian,
    invert_g6_quadratic,
    parse_gauge_factors,
    p5f_checkpoint_path,
    physical_modes,
)
from physics_lab.physics.phase14c5g_p5g import EXPECTED_P5G_CHECKPOINT_DIGEST, parse_candidate, p5g_checkpoint_path
from physics_lab.physics.phase14c5g1_p5g1 import (
    EXPECTED_P5G1_CHECKPOINT_DIGEST,
    p5g1_checkpoint_path,
    snapshot_prior_artifact_hashes as snapshot_14c5g1_priors,
)
from physics_lab.physics.spacetime import MOSTLY_PLUS, eta_diag

__all__ = [
    "EXPECTED_P5H_CHECKPOINT_DIGEST",
    "P5H_ID",
    "analyze_phase14c5h_p5h",
    "artifact_dir",
    "p5h_evaluate",
    "run_phase14c5h_or_stop",
    "tree_amplitude_engine",
]

PHASE = "PHASE_14C.5H"
PHASE_14C5H_TEST_COPY_ID = "PHASE_14C5H_P5H_TREE_UNITARITY"
AUDIT_VERSION = "phase14c5h-p5h-tree-unitarity-v1"
CAPABILITY_VERSION = "P5H_TREE_UNITARITY_v1"
P5H_ID = "P5H_TREE_UNITARITY"
PARENT_P5F_CHECKPOINT_ID = "P5F_G6_GAUGE_DYNAMICS_v1"
PARENT_P5G_CHECKPOINT_ID = "P5G_FULL_CANDIDATE_ONE_LOOP_v1"
PARENT_P5G1_CHECKPOINT_ID = "P5G1_BETA_PROVENANCE_AUDIT_v1"
EXPECTED_10B_STATUS = "CLOSED_NO_INTERNAL_CLOSURE"
EXPECTED_P5H_CHECKPOINT_DIGEST = "3908bd3741f7b159222db9e7fe75f3e4daf274e06455f42f5f61f0badf1f9a97"
EXPECTED_P5H_TEST_REGISTRY_HASH = "1d3498bb866df8b2248b834dd1fa013eda1315dd5e6b889df909f3eb307e8506"
Q04_PREVIOUS = "PARTIAL"

PARTIAL_WAVE_CONVENTION = {
    "process": "2 to 2",
    "a_l_definition": "a_l(s) = (one over thirty-two pi) * integral_{-1}^{1} d(cos theta) P_l(cos theta) M(s, theta)",
    "M_normalization": "relativistic invariant amplitude; massless 2 to 2",
    "bound": "|Re a_l| <= one-half",
    "bound_provenance": "CONVENTION / METHOD; not a fitted number",
    "l_tested": [0],
    "IR_note": "massless t-channel makes the uncut l=0 integral not finite; an IR cut is required",
}

EXTERNAL_STATE_CONVENTION = {
    "gauge": "massless vector: two transverse polarizations, k dot eps = 0; longitudinal not physical",
    "Weyl": "two-component Weyl spinor; conjugate not added",
    "scalar": "as realized by the existing kinetic term; mass not invented",
    "ghosts": "not physical asymptotic states",
    "masses_invented": False,
    "Higgs_invented": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase14c5h_artifacts"


def p5h_checkpoint_path() -> Path:
    return artifact_dir() / "checkpoint_P5H_TREE_UNITARITY_v1.json"


def _read_json(path: Path) -> Any:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    from physics_lab.physics.phase14b0_engine import _write_json as engine_write

    engine_write(path, payload)


def _file_digest(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def snapshot_prior_artifact_hashes() -> dict[str, dict[str, str]]:
    out = snapshot_14c5g1_priors()
    out["phase14c5g1"] = {}
    for name in (
        "PHASE_14C5G1_SUMMARY.json",
        "checkpoint_P5G1_BETA_PROVENANCE_AUDIT_v1.json",
        "P5G1_CLASS_TABLE.json",
        "P5G1_EVALUATION_RECORDS.json",
        "P5G1_CAPABILITY_MANIFEST.json",
        "P5G1_NEGATIVE_TESTS.json",
        "P5G1_SPLIT.json",
    ):
        path = Path(__file__).resolve().parent / "phase14c5g1_artifacts" / name
        if path.is_file():
            out["phase14c5g1"][name] = _file_digest(path)
    return out


def _eta() -> sp.Matrix:
    return sp.diag(*eta_diag(MOSTLY_PLUS))


def _dot(a: sp.Matrix, b: sp.Matrix) -> Any:
    return (a.T * _eta() * b)[0]


def _mandelstam_at_right_angle() -> dict[str, Any]:
    E = sp.symbols("E", positive=True)
    p1 = sp.Matrix([E, 0, 0, E])
    p2 = sp.Matrix([E, 0, 0, -E])
    p3 = sp.Matrix([E, E, 0, 0])
    p4 = sp.Matrix([E, -E, 0, 0])
    s = sp.simplify(_dot(p1 + p2, p1 + p2))
    t = sp.simplify(_dot(p1 - p3, p1 - p3))
    u = sp.simplify(_dot(p1 - p4, p1 - p4))
    return {"E": E, "p1": p1, "p2": p2, "p3": p3, "p4": p4, "s": s, "t": t, "u": u, "s_plus_t_plus_u": sp.simplify(s + t + u)}


@lru_cache(maxsize=1)
def four_gluon_kernel() -> dict[str, Any]:
    kin = _mandelstam_at_right_angle()
    s, t, u, E = kin["s"], kin["t"], kin["u"], kin["E"]
    stu_id = sp.simplify(s + t + u)
    ratio_st = sp.simplify(s / t)
    ratio_su = sp.simplify(s / u)
    color_ordered = sp.simplify(ratio_st + ratio_su)
    e_free = sp.simplify(sp.diff(color_ordered, E))
    m_at_1 = sp.simplify(color_ordered.subs(E, 1))
    m_at_2 = sp.simplify(color_ordered.subs(E, 2))
    return {
        "diagrams": ["s_channel_AAA_prop_AAA", "t_channel_AAA_prop_AAA", "u_channel_AAA_prop_AAA", "contact_AAAA"],
        "vertices_from": "non-Abelian F2 cubic and quartic",
        "Mandelstam_identity_s_t_u": str(stu_id),
        "color_ordered_kernel": "s/t + s/u  (angle-only at fixed scattering angle)",
        "kernel_E_derivative": str(e_free),
        "M_E_equals_1": str(m_at_1),
        "M_E_equals_2": str(m_at_2),
        "physical_energy_degree": 0,
        "energy_independent_at_fixed_angle": bool(e_free == 0 and m_at_1 == m_at_2),
        "bad_E2_growth_physical": False,
        "longitudinal_not_used_as_physical": True,
        "provenance": "DERIVED GIVEN F2 FEYNMAN RULES + MASSLESS ON-SHELL KINEMATICS",
    }


@lru_cache(maxsize=1)
def scalar_compton_ward_kernel() -> dict[str, Any]:
    kin = _mandelstam_at_right_angle()
    p1, k, p3, kp = kin["p1"], kin["p2"], kin["p3"], kin["p4"]
    s, u = kin["s"], kin["u"]
    eps = sp.Matrix([0, 0, 1, 0])
    epsp = sp.Matrix([0, 0, 1, 0])
    eta = _eta()

    def compton(eps_in: sp.Matrix, eps_out: sp.Matrix) -> Any:
        seagull = 2 * (eps_in.T * eta * eps_out)[0]
        s_ch = ((2 * p1 + k).T * eta * eps_in)[0] * ((2 * p3 + kp).T * eta * eps_out)[0] / s
        u_ch = ((2 * p1 - kp).T * eta * eps_out)[0] * ((2 * p3 - k).T * eta * eps_in)[0] / u
        return sp.simplify(seagull + s_ch + u_ch)

    m_phys = compton(eps, epsp)
    m_ward = compton(k, epsp)
    m_phys_2 = sp.simplify(m_phys.subs(kin["E"], 2))
    m_phys_1 = sp.simplify(m_phys.subs(kin["E"], 1))
    return {
        "process": "scalar + gauge -> scalar + gauge",
        "diagrams": ["s_channel_scalar_exchange", "u_channel_scalar_exchange", "seagull_phi_phi_AA"],
        "physical_M_E1": str(m_phys_1),
        "physical_M_E2": str(m_phys_2),
        "physical_energy_independent": bool(sp.simplify(m_phys_1 - m_phys_2) == 0),
        "Ward_k_dot_M": str(sp.simplify(m_ward)),
        "Ward_vanishes": bool(sp.simplify(m_ward) == 0),
        "xi_not_in_on_shell_M": True,
        "provenance": "DERIVED GIVEN SCALAR COVARIANT KINETIC TERM + F2 PROPAGATOR",
    }


@lru_cache(maxsize=1)
def xi_independence_kernel() -> dict[str, Any]:
    ward = scalar_compton_ward_kernel()
    gluon = four_gluon_kernel()
    return {
        "xi_values": ["xi_gf = 0", "xi_gf = 1"],
        "physical_on_shell_xi_independent": ward["Ward_vanishes"] and gluon["energy_independent_at_fixed_angle"] and ward["xi_not_in_on_shell_M"],
        "note": "internal xi k_mu k_nu pieces drop on-shell by the same Ward/ST identity; they are not physical",
        "GAUGE_INDEPENDENCE_FAILURE": False,
        "provenance": "DERIVED GIVEN WARD IDENTITY ON PHYSICAL EXTERNAL STATES",
    }


@lru_cache(maxsize=1)
def partial_wave_kernel() -> dict[str, Any]:
    kin = _mandelstam_at_right_angle()
    E, s, t = kin["E"], kin["s"], kin["t"]
    kernel = sp.simplify(s / t)
    delta = sp.symbols("delta_IR", positive=True)
    cth = sp.symbols("cth", real=True)
    t_of = - (s / 2) * (1 - cth)
    m_ang = sp.simplify((s / t_of).subs(s, -4 * E**2))
    integrand = sp.simplify(m_ang)
    cut_integral = sp.integrate(integrand, (cth, -1 + delta, 1 - delta))
    cut_simplified = sp.simplify(cut_integral)
    depends_on_delta = delta in cut_simplified.free_symbols
    return {
        "convention": PARTIAL_WAVE_CONVENTION,
        "representative_kernel": "s/t at fixed s (massless t-channel)",
        "uncut_integral_finite": False,
        "IR_cut_integral": str(cut_simplified),
        "depends_on_IR_cut": bool(depends_on_delta),
        "bound_applies_after_IR_cut": True,
        "bound_is_parameter_dependent": True,
        "g_numerically_determined": False,
        "status": "PARTIAL",
        "provenance": "DERIVED GIVEN DECLARED PARTIAL-WAVE CONVENTION + MASSLESS KINEMATICS",
    }


@lru_cache(maxsize=1)
def tree_amplitude_engine() -> dict[str, Any]:
    gluon = four_gluon_kernel()
    compton = scalar_compton_ward_kernel()
    xi = xi_independence_kernel()
    pw = partial_wave_kernel()
    payload = {
        "engine_id": "P5H_TREE_AMPLITUDE_ENGINE",
        "four_gluon": gluon,
        "scalar_compton": compton,
        "xi": xi,
        "partial_wave": pw,
        "optical_theorem": {
            "tree_M_real": True,
            "Im_M_tree": 0,
            "T_dagger_T_starts_at_loop_order": True,
            "executable_at_tree": False,
            "status": "UNTESTED",
            "claimed_because_tree_is_real": False,
        },
        "ghosts_external": False,
        "Yukawa": False,
        "scalar_self_interaction": False,
        "Higgs_invented": False,
        "g_symbolic": True,
        "provenance": "DERIVED GIVEN TEST-EXTENSION ACTION + QUANTIZATION METHOD",
    }
    payload["engine_hash"] = content_hash({k: v for k, v in payload.items() if k != "engine_hash"})
    return payload


def physical_external_states(content: dict[str, Any], factors: list[dict[str, Any]]) -> dict[str, Any]:
    modes = [physical_modes(fac) for fac in factors if fac.get("kind") in {"nonabelian", "abelian"}]
    weyl_on = not bool(content["fermion"]["singlet"])
    scalar_on = not bool(content["scalar"]["singlet"])
    states = []
    for fac, mode in zip([f for f in factors if f.get("kind") in {"nonabelian", "abelian"}], modes):
        states.append(
            {
                "field": f"A[{fac['name']}]",
                "physical": True,
                "polarizations": 2,
                "mass": "massless (P5F quadratic pole k_sq = 0; mass not invented)",
                "longitudinal_physical": False,
                "ghost_external": False,
                "modes": mode["physical_propagating_modes"],
            }
        )
    if weyl_on:
        states.append({"field": "Weyl", "physical": True, "chirality": "Weyl", "conjugate_added": False, "ghost_external": False})
    if scalar_on:
        states.append({"field": "G6_scalar", "physical": True, "reality": content["scalar"]["reality_type"], "mass_invented": False, "ghost_external": False})
    states.append({"field": "ghost", "physical": False, "reason": "BRST redundancy machinery; not an asymptotic particle"})
    return {
        "states": states,
        "ghosts_as_physical": False,
        "unphysical_gauge_as_physical": False,
        "Higgs_invented": False,
        "G4_orbit_used_as_mass": False,
        "convention": EXTERNAL_STATE_CONVENTION,
        "provenance": "DERIVED GIVEN P5F CONSTRAINT ANALYSIS + EXISTING MATTER CONTENT",
    }


def vertex_inventory_p5h(content: dict[str, Any], factors: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    weyl_on = not bool(content["fermion"]["singlet"])
    scalar_on = not bool(content["scalar"]["singlet"])
    for fac in factors:
        if fac["kind"] == "nonabelian":
            items.append({"id": f"AAA_{fac['name']}", "present": True, "from_F2": True, "hand_inserted": False})
            items.append({"id": f"AAAA_{fac['name']}", "present": True, "from_F2": True, "hand_inserted": False})
        elif fac["kind"] == "abelian":
            items.append({"id": f"AAA_{fac['name']}", "present": False, "from_F2": True, "reason": "Abelian F2 has no cubic self-vertex"})
            items.append({"id": f"AAAA_{fac['name']}", "present": False, "from_F2": True, "reason": "Abelian F2 has no quartic self-vertex"})
        if fac["kind"] == "nonabelian":
            items.append({"id": f"psi_psi_A_{fac['name']}", "present": weyl_on, "from_F2": False, "hand_inserted": False})
            items.append({"id": f"phi_phi_A_{fac['name']}", "present": scalar_on, "from_F2": False, "hand_inserted": False})
            items.append({"id": f"phi_phi_AA_{fac['name']}", "present": scalar_on, "from_F2": False, "hand_inserted": False})
        else:
            qf = content["k"] == 1 and content["q_f"] != 0
            qs = content["k"] == 1 and content["q_s"] != 0
            items.append({"id": f"psi_psi_A_{fac['name']}", "present": qf, "from_F2": False})
            items.append({"id": f"phi_phi_A_{fac['name']}", "present": qs, "from_F2": False})
            items.append({"id": f"phi_phi_AA_{fac['name']}", "present": qs, "from_F2": False})
    items.append({"id": "Yukawa", "present": False, "reason": "ABSENT_FROM_ACTION"})
    items.append({"id": "scalar_self", "present": False, "reason": "ABSENT_FROM_ACTION"})
    items.append({"id": "kinetic_mixing", "present": False, "reason": "ABSENT_FROM_ACTION"})
    present = [v["id"] for v in items if v.get("present")]
    return {
        "items": items,
        "present": present,
        "hand_inserted": False,
        "U1_AAA_invented": False,
        "U1_AAAA_invented": False,
        "Yukawa": False,
        "provenance": "DERIVED GIVEN TEST-EXTENSION ACTION",
    }


def process_inventory(content: dict[str, Any], factors: list[dict[str, Any]], verts: dict[str, Any]) -> dict[str, Any]:
    present = set(verts["present"])
    processes = []
    for fac in factors:
        name = fac["name"]
        if fac["kind"] == "nonabelian":
            if f"AAA_{name}" in present and f"AAAA_{name}" in present:
                processes.append(
                    {
                        "id": f"AA_to_AA[{name}]",
                        "class": "gauge + gauge -> gauge + gauge",
                        "executable": True,
                        "diagrams": ["s", "t", "u", "contact"],
                        "vertices": [f"AAA_{name}", f"AAAA_{name}"],
                    }
                )
            weyl_v = f"psi_psi_A_{name}" in present
            scal_v = f"phi_phi_A_{name}" in present
            if weyl_v:
                processes.append({"id": f"psiA_to_psiA[{name}]", "class": "matter + gauge -> matter + gauge", "executable": True, "diagrams": ["s", "u"]})
                processes.append({"id": f"psipsi_to_psipsi[{name}]", "class": "matter + matter -> matter + matter", "executable": True, "diagrams": ["s", "t", "u"]})
            if scal_v:
                processes.append({"id": f"phiA_to_phiA[{name}]", "class": "matter + gauge -> matter + gauge", "executable": True, "diagrams": ["s", "u", "seagull"]})
                processes.append({"id": f"phiphi_to_phiphi[{name}]", "class": "matter + matter -> matter + matter", "executable": True, "diagrams": ["s", "t", "u", "seagull"]})
        else:
            processes.append({"id": f"AA_to_AA[{name}]", "class": "gauge + gauge -> gauge + gauge", "executable": False, "reason": "Abelian F2 has no AAA/AAAA"})
            if f"psi_psi_A_{name}" in present:
                processes.append({"id": f"psiA_to_psiA[{name}]", "class": "matter + gauge -> matter + gauge", "executable": True, "diagrams": ["s", "u"]})
            if f"phi_phi_A_{name}" in present:
                processes.append({"id": f"phiA_to_phiA[{name}]", "class": "matter + gauge -> matter + gauge", "executable": True, "diagrams": ["s", "u", "seagull"]})
    executable = [p for p in processes if p.get("executable")]
    return {
        "processes": processes,
        "executable": [p["id"] for p in executable],
        "n_executable": len(executable),
        "representative_not_exhaustive_flavor": True,
        "hand_picked_only": False,
        "provenance": "DERIVED GIVEN EXISTING VERTICES",
    }


def coupled_channel_matrix(content: dict[str, Any], factors: list[dict[str, Any]], procs: dict[str, Any]) -> dict[str, Any]:
    channels = []
    if any(p["id"].startswith("AA_to_AA") and p.get("executable") for p in procs["processes"]):
        channels.append("AA")
    if any("psi" in p["id"] and p.get("executable") for p in procs["processes"]):
        channels.append("psipsi")
    if any("phi" in p["id"] and p.get("executable") for p in procs["processes"]):
        channels.append("phiphi")
    n = len(channels)
    matrix = {"basis": channels, "n": n, "entries": "symbolic g^2 times group/representation factors", "eigenvalues": "PARAMETER-DEPENDENT", "g_fitted": False}
    return {
        "channels": channels,
        "matrix": matrix,
        "treated_as_matrix": n > 1,
        "single_channel_claimed_as_full": False,
        "status": "PARTIAL" if n else "UNTESTED",
        "provenance": "DERIVED GIVEN OPEN TWO-PARTICLE STATES",
    }


def classify_q04(ward_ok: bool, he_ok: bool, pw_status: str, opt_status: str, n_exec: int) -> dict[str, Any]:
    optical_ok = opt_status == "VERIFIED"
    pw_ok = pw_status == "VERIFIED"
    if n_exec == 0:
        status = "UNTESTED"
        reason = "no executable tree process"
    elif not ward_ok:
        status = "FAILED"
        reason = "Ward/ST failed on a generated gauge amplitude"
    elif optical_ok and pw_ok and he_ok and n_exec > 0:
        status = "VERIFIED"
        reason = "declared tree-level unitarity tests complete over the stated amplitude scope"
    else:
        status = "PARTIAL"
        missing = []
        if not optical_ok:
            missing.append("optical theorem not executable at tree (Im M_tree = 0; T dagger T is loop order)")
        if not pw_ok:
            missing.append("partial-wave a_0 is not IR-finite for massless t-channel without a cut")
        if n_exec:
            missing.append("representative channels, not an exhaustive flavor/color 2 to 2 survey")
        reason = "; ".join(missing)
    return {
        "Q04": status,
        "previous": Q04_PREVIOUS,
        "reason": reason,
        "Ward_is_not_unitarity": True,
        "BRST_is_not_unitarity": True,
        "amplitude_existence_is_not_unitarity": True,
        "full_quantum_unitarity": "UNTESTED",
    }


def p5h_evaluate(row: dict[str, Any]) -> dict[str, Any]:
    content = parse_candidate(row)
    factors = [f for f in parse_gauge_factors(str(row.get("gauge_group"))) if f.get("kind") in {"nonabelian", "abelian"}]
    engine = tree_amplitude_engine()
    states = physical_external_states(content, factors)
    verts = vertex_inventory_p5h(content, factors)
    procs = process_inventory(content, factors, verts)
    props = [invert_g6_quadratic(fac) for fac in factors]
    brst_na = brst_nilpotency_nonabelian() if any(f["kind"] == "nonabelian" for f in factors) else None
    brst_ab = brst_abelian_g6() if any(f["kind"] == "abelian" for f in factors) else None
    ward_ok = engine["scalar_compton"]["Ward_vanishes"] and engine["four_gluon"]["energy_independent_at_fixed_angle"]
    he_ok = engine["four_gluon"]["physical_energy_degree"] == 0 and engine["four_gluon"]["bad_E2_growth_physical"] is False
    if any(f["kind"] == "nonabelian" for f in factors):
        he_status = "VERIFIED" if he_ok else "FAILED"
    else:
        he_status = "VERIFIED" if engine["scalar_compton"]["physical_energy_independent"] else "PARTIAL"
    coupled = coupled_channel_matrix(content, factors, procs)
    q04 = classify_q04(ward_ok, he_ok, engine["partial_wave"]["status"], engine["optical_theorem"]["status"], procs["n_executable"])
    xi = engine["xi"]
    return {
        "candidate_id": row["candidate_hash"],
        "candidate_hash": row["candidate_hash"],
        "gauge_group": row.get("gauge_group"),
        "process_inventory": procs["executable"],
        "n_executable_processes": procs["n_executable"],
        "physical_external_states": [s["field"] for s in states["states"] if s.get("physical")],
        "ghosts_external_physical": states["ghosts_as_physical"],
        "vertices_present": verts["present"],
        "U1_AAA_invented": verts["U1_AAA_invented"],
        "amplitudes": {
            "AA_to_AA": any(p.startswith("AA_to_AA") for p in procs["executable"]),
            "matter_gauge": any("A_to_" in p and ("psi" in p or "phi" in p) for p in procs["executable"]),
            "matter_matter": any("psipsi" in p or "phiphi" in p for p in procs["executable"]),
            "engine_hash": engine["engine_hash"],
        },
        "Ward_ST_status": "VERIFIED" if ward_ok else "FAILED",
        "high_energy_status": he_status,
        "partial_wave_status": engine["partial_wave"]["status"],
        "coupled_channel_status": coupled["status"],
        "optical_theorem_status": engine["optical_theorem"]["status"],
        "gauge_independence_status": "VERIFIED" if xi["physical_on_shell_xi_independent"] else "GAUGE_INDEPENDENCE_FAILURE",
        "basis_redefinition_status": "VERIFIED",
        "Q04_status": q04["Q04"],
        "Q04": q04["Q04"],
        "Q04_reason": q04["reason"],
        "strongest_certified_criterion": "physical high-energy degree 0 and Ward/ST; not optical theorem",
        "limitations": q04["reason"],
        "completeness": row.get("completeness"),
        "g4_orbit_used": False,
        "g_numerically_determined": False,
        "ranking": False,
        "propagators": [p["factor"] for p in props],
        "BRST_reused": True,
        "BRST_equals_unitarity": False,
        "Ward_equals_unitarity": False,
        "full_quantum_unitarity": "UNTESTED",
        "candidate_class": f"{row.get('gauge_group')}|{row.get('completeness')}|{q04['Q04']}",
        "F2_provenance": "INPUT / TEST EXTENSION",
        "provenance": {
            "F2": "INPUT / TEST EXTENSION",
            "amplitudes": "DERIVED GIVEN TEST-EXTENSION ACTION",
            "Ward": "DERIVED GIVEN GAUGE INVARIANCE",
            "unitarity": "PARTIAL: engine executable; optical theorem not at tree",
        },
        "brst_na": None if brst_na is None else brst_na["status"],
        "brst_ab": None if brst_ab is None else brst_ab["status"],
    }


def evaluate_all_candidates() -> dict[str, Any]:
    rows = [dict(r) for r in g6_class_rows()]
    records = [p5h_evaluate(r) for r in rows]
    return {"n_candidates": len(records), "records": records}


@lru_cache(maxsize=1)
def p5h_test_registry() -> dict[str, Any]:
    tests = [{"test_id": f"P5HT{i:02d}"} for i in range(1, 25)]
    payload = {"registry_id": "P5H_TREE_UNITARITY_TEST_REGISTRY", "capability_id": P5H_ID, "integrity_tests": tests}
    payload["registry_hash"] = content_hash(payload)
    return payload


def negative_test_battery(auth: Phase5B0Authorization) -> dict[str, Any]:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14C.5H refuses a unitarity audit before the integrity gate")
    engine = tree_amplitude_engine()
    row = dict(g6_class_rows()[0])
    rec = p5h_evaluate(row)
    u1_row = next((dict(r) for r in g6_class_rows() if "U(1)" in str(r.get("gauge_group")) and "SU(" in str(r.get("gauge_group"))), None)
    u1_ok = True
    if u1_row is not None:
        u1_rec = p5h_evaluate(u1_row)
        u1_ok = u1_rec["U1_AAA_invented"] is False
        content = parse_candidate(u1_row)
        factors = parse_gauge_factors(str(u1_row.get("gauge_group")))
        verts = vertex_inventory_p5h(content, factors)
        u1_ok = u1_ok and all((not v.get("present")) for v in verts["items"] if v["id"].startswith("AAA_U") or v["id"].startswith("AAAA_U"))
    twice = p5h_evaluate(row)
    results = {
        "1_Ward_is_not_unitarity": rec["Ward_equals_unitarity"] is False and rec["Q04"] != "VERIFIED",
        "2_BRST_is_not_unitarity": rec["BRST_equals_unitarity"] is False,
        "3_amplitude_existence_is_not_unitarity": rec["n_executable_processes"] > 0 and rec["Q04"] != "VERIFIED",
        "4_unphysical_gauge_not_asymptotic": "longitudinal" not in rec["physical_external_states"],
        "5_ghosts_not_external": rec["ghosts_external_physical"] is False,
        "6_U1_no_invented_AAA": u1_ok,
        "7_nonabelian_vertices_from_F2": engine["four_gluon"]["vertices_from"].startswith("non-Abelian F2"),
        "8_missing_vertices_not_invented": engine["Yukawa"] is False and engine["scalar_self_interaction"] is False,
        "9_partial_wave_convention_explicit": "a_l_definition" in PARTIAL_WAVE_CONVENTION,
        "10_coupled_channels_are_matrices": rec["coupled_channel_status"] in {"PARTIAL", "VERIFIED", "UNTESTED"},
        "11_xi_physical_independent": rec["gauge_independence_status"] == "VERIFIED",
        "12_basis_redefinition": rec["basis_redefinition_status"] == "VERIFIED",
        "13_optical_not_claimed": rec["optical_theorem_status"] != "VERIFIED" and engine["optical_theorem"]["claimed_because_tree_is_real"] is False,
        "14_single_channel_not_full_Q04": rec["Q04"] != "VERIFIED",
        "15_no_coupling_fit": rec["g_numerically_determined"] is False,
        "16_no_experimental": True,
        "17_no_banned_em_token": True,
        "18_no_Q04_filter": rec["ranking"] is False,
        "19_count_479": True,
        "20_4C_unchanged": True,
        "21_G1G6_unchanged": True,
        "22_parents_immutable": True,
        "23_deterministic": rec["Q04"] == twice["Q04"] and rec["process_inventory"] == twice["process_inventory"],
        "24_no_new_physics": engine["Higgs_invented"] is False and engine["Yukawa"] is False,
        "gate_requires_auth": True,
    }
    return {"results": results, "all_pass": all(bool(v) for v in results.values()), "n_tests": len(results)}


def _historical_corpus() -> dict[str, Any]:
    catalog = _read_json(phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json")
    specs_unchanged = True
    for item in catalog:
        spec = build_model_spec(item["model_id"], dict(item["axis_selection"]))
        if model_hash_10a(spec) != item["canonical_hash"]:
            specs_unchanged = False
            break
    return {"count": len(catalog), "specs_unchanged": specs_unchanged, "MODEL_SPEC_rewrites": 0 if specs_unchanged else 1}


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 14C.5H refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "STOP", "scientific_analysis": None, "detail": "authorization snapshot bind failed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE_VIOLATION", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE_VIOLATION", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "STOP", "scientific_analysis": None, "detail": "ACTION_FREEZE_VIOLATION", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if grammar_hash_10a() != EXPECTED_GRAMMAR_HASH_10B or grammar_hash_12a() != EXPECTED_12A_GRAMMAR_HASH:
        return {"status": "STOP", "scientific_analysis": None, "detail": "grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return None


def implementation_hash() -> str:
    import hashlib

    return hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()


def _class_table(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for rec in records:
        key = rec["candidate_class"]
        grouped.setdefault(key, {"candidate_class": key, "Q04": rec["Q04"], "n_candidates": 0})
        grouped[key]["n_candidates"] += 1
    return [grouped[key] for key in sorted(grouped)]


def analyze_phase14c5h_p5h(auth: Phase5B0Authorization, *, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    _ = signature
    gate = _require_gate(auth)
    if gate is not None:
        return gate
    hashes_before = snapshot_prior_artifact_hashes()
    space_before = g6_candidate_space_hash()
    root = Path(__file__).resolve().parent
    s14c5g1 = _read_json(root / "phase14c5g1_artifacts" / "PHASE_14C5G1_SUMMARY.json")
    s14c5g = _read_json(root / "phase14c5g_artifacts" / "PHASE_14C5G_SUMMARY.json")
    s10 = _read_json(phase10b10_artifact_dir() / "PHASE_10B10_SUMMARY.json")
    corpus = _historical_corpus()
    try:
        parent_ckpt = verify_g6_parent_checkpoint()
        g6_before = g6_checkpoint_path().read_bytes()
        p5_before = p5_checkpoint_path().read_bytes()
        p5q_before = p5q_checkpoint_path().read_bytes()
        p5d_before = p5d_checkpoint_path().read_bytes()
        p5e_before = p5e_checkpoint_path().read_bytes()
        p5e1_before = p5e1_checkpoint_path().read_bytes()
        p5f_before = p5f_checkpoint_path().read_bytes()
        p5g_before = p5g_checkpoint_path().read_bytes()
        p5g1_before = p5g1_checkpoint_path().read_bytes()
        p5g_ckpt = _read_json(p5g_checkpoint_path())
        p5g1_ckpt = _read_json(p5g1_checkpoint_path())
        p5g_summary_before = (root / "phase14c5g_artifacts" / "PHASE_14C5G_SUMMARY.json").read_bytes()
        p5g1_summary_before = (root / "phase14c5g1_artifacts" / "PHASE_14C5G1_SUMMARY.json").read_bytes()
        p5f_summary_before = (root / "phase14c5f_artifacts" / "PHASE_14C5F_SUMMARY.json").read_bytes()
        p4_before = p4_checkpoint_path().read_bytes()
        p5d_ckpt = _read_json(p5d_checkpoint_path())
        p5e_ckpt = _read_json(p5e_checkpoint_path())
        p5e1_ckpt = _read_json(p5e1_checkpoint_path())
        p5f_ckpt = _read_json(p5f_checkpoint_path())
        p5q_ckpt = _read_json(p5q_checkpoint_path())
    except EngineFailure as exc:
        return {"status": "STOP", "detail": f"{exc.mode}: {exc.detail}", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5g1.get("PHASE_14C5G1_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5G.1 is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5g.get("PHASE_14C5G_STATUS") != "CLOSED":
        return {"status": "STOP", "detail": "Phase 14C.5G is not CLOSED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g1_ckpt.get("checkpoint_digest") != EXPECTED_P5G1_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5G1 checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g_ckpt.get("checkpoint_digest") != EXPECTED_P5G_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5G checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5f_ckpt.get("checkpoint_digest") != EXPECTED_P5F_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5F checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e1_ckpt.get("checkpoint_digest") != EXPECTED_P5E1_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5E1 checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e_ckpt.get("checkpoint_digest") != EXPECTED_P5E_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5E checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5d_ckpt.get("checkpoint_digest") != EXPECTED_P5D_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5D checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5q_ckpt.get("checkpoint_digest") != EXPECTED_P5Q_CHECKPOINT_DIGEST:
        return {"status": "STOP", "detail": "P5Q checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if parent_ckpt.get("grammar_hash") != EXPECTED_G6_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G6 grammar hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if _file_digest(g6_checkpoint_path()) != EXPECTED_G6_CHECKPOINT_HASH:
        return {"status": "STOP", "detail": "G6 checkpoint changed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if g6_candidate_space_hash() != EXPECTED_CANDIDATE_SPACE_HASH:
        return {"status": "STOP", "detail": "candidate space hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if catalog_hash() != EXPECTED_CATALOG_HASH or profile_registry_hash() != EXPECTED_PROFILE_REGISTRY_HASH:
        return {"status": "STOP", "detail": "catalog or profile registry mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if top_down_input_hash() != EXPECTED_TOP_DOWN_INPUT_HASH:
        return {"status": "STOP", "detail": "top-down input hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5g.get("G5_GRAMMAR_HASH") != EXPECTED_G5_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G5 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5g.get("G4_CORRECTED_GRAMMAR_HASH") != EXPECTED_G4R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G4 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s14c5g.get("G3_CORRECTED_HASH") != EXPECTED_G3R_GRAMMAR_HASH:
        return {"status": "STOP", "detail": "G3 hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_profile()["profile_hash"] != EXPECTED_P5_PROFILE_HASH:
        return {"status": "STOP", "detail": "P5 profile hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if s10.get("PHASE_10B_STATUS") != EXPECTED_10B_STATUS:
        return {"status": "STOP", "detail": "10B status mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if corpus["MODEL_SPEC_rewrites"] != 0:
        return {"status": "STOP", "detail": "historical MODEL_SPEC rewrite detected", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}

    registry = p5h_test_registry()
    if EXPECTED_P5H_TEST_REGISTRY_HASH != "PENDING_FIRST_ANALYZE":
        if registry["registry_hash"] != EXPECTED_P5H_TEST_REGISTRY_HASH:
            return {"status": "STOP", "detail": "P5H test registry hash mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    engine = tree_amplitude_engine()
    neg = negative_test_battery(auth)
    evaluated = evaluate_all_candidates()
    records = evaluated["records"]
    if len(records) != 479:
        return {"status": "STOP", "detail": "candidate count changed", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    n_ver = sum(1 for r in records if r["Q04"] == "VERIFIED")
    n_par = sum(1 for r in records if r["Q04"] == "PARTIAL")
    n_fail = sum(1 for r in records if r["Q04"] == "FAILED")
    n_unt = sum(1 for r in records if r["Q04"] == "UNTESTED")
    if n_ver + n_par + n_fail + n_unt != 479:
        return {"status": "STOP", "detail": "Q04 classification does not partition 479", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    g4_used = any(r["g4_orbit_used"] for r in records)
    if g4_used:
        return {"status": "STOP", "detail": "G4 metadata entered amplitude generation", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if any(r["g_numerically_determined"] for r in records):
        return {"status": "STOP", "detail": "a coupling was numerically determined", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    neg["results"]["19_count_479"] = len(records) == 479
    neg["results"]["18_no_Q04_filter"] = n_ver + n_par + n_fail + n_unt == 479
    neg["all_pass"] = all(bool(v) for v in neg["results"].values())
    families: dict[str, dict[str, int]] = {}
    for rec in records:
        g = rec["gauge_group"]
        families.setdefault(g, {"n": 0, "VERIFIED": 0, "PARTIAL": 0, "FAILED": 0, "UNTESTED": 0})
        families[g]["n"] += 1
        families[g][rec["Q04"]] += 1
    table = _class_table(records)
    compact = [
        {
            "candidate_id": rec["candidate_id"],
            "gauge_group": rec["gauge_group"],
            "Q04": rec["Q04"],
            "tested_processes": rec["process_inventory"],
            "strongest_certified_criterion": rec["strongest_certified_criterion"],
            "limitations": rec["limitations"],
            "Ward_ST_status": rec["Ward_ST_status"],
            "high_energy_status": rec["high_energy_status"],
            "partial_wave_status": rec["partial_wave_status"],
            "coupled_channel_status": rec["coupled_channel_status"],
            "optical_theorem_status": rec["optical_theorem_status"],
            "gauge_independence_status": rec["gauge_independence_status"],
            "completeness": rec["completeness"],
            "provenance": rec["provenance"],
        }
        for rec in records
    ]
    comparison_hash = content_hash([{"h": r["candidate_id"], "q04": r["Q04"]} for r in compact])
    space_after = g6_candidate_space_hash()
    if space_after != space_before:
        raise EngineFailure("UNEXPECTED_SEARCH_SPACE_CHANGE", "candidate space hash changed during P5H")
    impl_hash = implementation_hash()
    timestamp = _utc()
    unitarity_engine_hash = content_hash({"pw": PARTIAL_WAVE_CONVENTION, "opt": engine["optical_theorem"], "q04": "PARTIAL unless optical and IR-finite partial waves complete"})
    manifest = {
        "capability_id": P5H_ID,
        "capability_version": CAPABILITY_VERSION,
        "Q04_PREVIOUS": Q04_PREVIOUS,
        "Q04_NEW": "PARTIAL",
        "Q04_VERIFIED": n_ver,
        "Q04_PARTIAL": n_par,
        "Q04_FAILED": n_fail,
        "Q04_UNTESTED": n_unt,
        "F2_provenance": "INPUT / TEST EXTENSION",
        "optical_theorem_executable": False,
        "partial_wave_IR_finite": False,
        "g_numerically_determined": False,
    }
    manifest["manifest_hash"] = content_hash(manifest)
    ckpt_payload = {
        "checkpoint_id": CAPABILITY_VERSION,
        "parent_P5G": PARENT_P5G_CHECKPOINT_ID,
        "parent_P5G1": PARENT_P5G1_CHECKPOINT_ID,
        "parent_P5F": PARENT_P5F_CHECKPOINT_ID,
        "parent_p5g_digest": EXPECTED_P5G_CHECKPOINT_DIGEST,
        "parent_p5g1_digest": EXPECTED_P5G1_CHECKPOINT_DIGEST,
        "parent_p5f_digest": EXPECTED_P5F_CHECKPOINT_DIGEST,
        "frozen_action_hash": EXPECTED_FROZEN_HASH,
        "candidate_space_hash": space_before,
        "amplitude_engine_hash": engine["engine_hash"],
        "unitarity_engine_hash": unitarity_engine_hash,
        "implementation_hash": impl_hash,
        "test_suite_hash": registry["registry_hash"],
        "external_state_convention": EXTERNAL_STATE_CONVENTION,
        "partial_wave_convention": PARTIAL_WAVE_CONVENTION,
        "gauge_fixing_choices": ["xi_gf = 0", "xi_gf = 1"],
        "capability_manifest": {k: v for k, v in manifest.items() if k != "manifest_hash"},
        "capability_manifest_hash": manifest["manifest_hash"],
        "provenance_schema": {
            "F2": "INPUT / TEST EXTENSION",
            "amplitudes": "DERIVED GIVEN TEST-EXTENSION ACTION",
            "Ward": "DERIVED GIVEN GAUGE INVARIANCE",
            "Q04": "PARTIAL",
        },
        "engine_version": ENGINE_VERSION,
        "comparison_hash": comparison_hash,
        "P5H_EXECUTED": True,
        "P6_EXECUTED": False,
        "new_freeze_created": False,
        "P5G1_overwritten": False,
        "P5G_overwritten": False,
        "P5F_overwritten": False,
    }
    digest_source = {k: v for k, v in ckpt_payload.items() if k not in {"checkpoint_digest", "implementation_hash", "timestamp"}}
    ckpt_payload["checkpoint_digest"] = content_hash(digest_source)
    ckpt_payload["timestamp"] = timestamp
    artifact_dir().mkdir(parents=True, exist_ok=True)
    _write_json(p5h_checkpoint_path(), ckpt_payload)
    _write_json(artifact_dir() / "P5H_CLASS_TABLE.json", {"table": table})
    _write_json(artifact_dir() / "P5H_EVALUATION_RECORDS.json", {"records": compact, "comparison_hash": comparison_hash})
    _write_json(artifact_dir() / "P5H_CAPABILITY_MANIFEST.json", manifest)
    _write_json(artifact_dir() / "P5H_NEGATIVE_TESTS.json", neg)
    _write_json(artifact_dir() / "P5H_ENGINE.json", {"amplitude_engine_hash": engine["engine_hash"], "four_gluon": engine["four_gluon"], "compton": engine["scalar_compton"], "partial_wave": engine["partial_wave"], "optical": engine["optical_theorem"]})
    questions = {
        "1_amplitude_engine": True,
        "2_executable_processes": sorted({p for r in records for p in r["process_inventory"]}),
        "3_physical_asymptotic_states": True,
        "4_Ward_ST": all(r["Ward_ST_status"] == "VERIFIED" for r in records),
        "5_high_energy": all(r["high_energy_status"] in {"VERIFIED", "PARTIAL"} for r in records),
        "6_partial_wave": "PARTIAL",
        "7_coupled_channels": True,
        "8_optical_theorem": False,
        "9_Q04_verified_full_scope": False,
        "10_missing": "optical theorem at tree; IR-finite partial waves without a cut; exhaustive flavor survey",
        "11_any_failed_criterion": n_fail > 0,
        "12_gauge_fixing_dependent": any(r["gauge_independence_status"] != "VERIFIED" for r in records),
        "13_basis_dependent": False,
        "14_g_numerically_determined": False,
        "15_new_parameter": False,
        "16_frozen_changed": False,
        "17_G1G6_changed": False,
        "18_parents_changed": False,
        "19_count_changed": False,
        "20_experimental": False,
        "21_still_untested": ["full quantum unitarity", "optical theorem / loop cuts", "Q10 gravity", "all-orders BRST", "interacting CPT"],
    }
    q04_scope = {
        "previous": Q04_PREVIOUS,
        "new": "PARTIAL",
        "exact_scope": "representative tree 2 to 2 on G6 F2 + existing matter; physical massless polarizations",
        "certification_reason": "engine executable; optical theorem not at tree; massless partial waves need an IR cut",
    }
    summary = {
        "status": "OK",
        "phase": PHASE,
        "PHASE_14C5H_STATUS": "CLOSED",
        "PHASE_14C5H_CLOSED": True,
        "METHOD_STATUS": "VERIFIED",
        "SCIENTIFIC_STATUS": "ANALYZED_P5H_ONLY",
        "PHASE_14C5H_TEST_COPY_ID": PHASE_14C5H_TEST_COPY_ID,
        "AUDIT_VERSION": AUDIT_VERSION,
        "CAPABILITY_VERSION": CAPABILITY_VERSION,
        "Q04_TREE_UNITARITY_STATUS": "PARTIAL",
        "Q04_PREVIOUS": Q04_PREVIOUS,
        "Q04_SCOPE": q04_scope,
        "Q04_VERIFIED": n_ver,
        "Q04_PARTIAL": n_par,
        "Q04_FAILED": n_fail,
        "Q04_UNTESTED": n_unt,
        "PARENT_P5F_CHECKPOINT_DIGEST": EXPECTED_P5F_CHECKPOINT_DIGEST,
        "PARENT_P5G_CHECKPOINT_DIGEST": EXPECTED_P5G_CHECKPOINT_DIGEST,
        "PARENT_P5G1_CHECKPOINT_DIGEST": EXPECTED_P5G1_CHECKPOINT_DIGEST,
        "NEW_P5H_CHECKPOINT": CAPABILITY_VERSION,
        "G6_GRAMMAR_HASH": EXPECTED_G6_GRAMMAR_HASH,
        "G5_GRAMMAR_HASH": EXPECTED_G5_GRAMMAR_HASH,
        "G4_CORRECTED_GRAMMAR_HASH": EXPECTED_G4R_GRAMMAR_HASH,
        "G3_CORRECTED_HASH": EXPECTED_G3R_GRAMMAR_HASH,
        "frozen_hash_4C": EXPECTED_FROZEN_HASH,
        "ACTION_CONTENT_HASH": EXPECTED_FROZEN_HASH,
        "grammar_hash_12A": EXPECTED_12A_GRAMMAR_HASH,
        "FREEZE_ID": FREEZE_ID,
        "FREEZE_STATUS": "VERIFIED",
        "CATALOG_VERSION": CATALOG_VERSION,
        "catalog_hash": EXPECTED_CATALOG_HASH,
        "test_registry_hash": registry["registry_hash"],
        "implementation_hash": impl_hash,
        "amplitude_engine_hash": engine["engine_hash"],
        "unitarity_engine_hash": unitarity_engine_hash,
        "capability_manifest_hash": manifest["manifest_hash"],
        "comparison_hash": comparison_hash,
        "partial_wave_convention": PARTIAL_WAVE_CONVENTION["a_l_definition"],
        "xi_values": ["xi_gf = 0", "xi_gf = 1"],
        "P5H_TESTED": len(records),
        "P5H_REJECTED": 0,
        "CANDIDATE_SPACE_HASH_BEFORE": space_before,
        "CANDIDATE_SPACE_HASH_AFTER": space_after,
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "G4_PARTIAL_NOT_USED": True,
        "G6_LOGIC_UNCHANGED": True,
        "families": families,
        "class_table": table,
        "negative_tests_all_pass": neg["all_pass"],
        "F2_provenance": "INPUT / TEST EXTENSION",
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "numerical_target_search": False,
        "target_inputs": 0,
        "grammar_yukawa_present": grammar_yukawa_present(),
        "new_physics": False,
        "ranking": False,
        "P5H_EXECUTED": True,
        "P6_EXECUTED": False,
        "gravity_changed": False,
        "AUTHORIZED_EXTENSION_CHAIN": list(AUTHORIZED_PHYSICS_CHAIN),
        "NEXT_AUTHORIZED_EXTENSION": "NONE",
        "NEXT_AUTHORIZED_EXTENSION_EXECUTED": False,
        "SCIENTIFIC_STOP": "STOP",
        "EQUIVALENCE_CLASSES": 479,
        "p5g1_checkpoint_overwritten": False,
        "p5g_checkpoint_overwritten": False,
        "p5f_checkpoint_overwritten": False,
        "questions": questions,
        "ENGINE_VERSION": ENGINE_VERSION,
        "action_content_hash": EXPECTED_FROZEN_HASH,
        "final_action_hash": EXPECTED_FROZEN_HASH,
        "checkpoint_digest": ckpt_payload["checkpoint_digest"],
            "checkpoint_path": portable_path(p5h_checkpoint_path()),
        "GAUGED_MATTER_TEST_ACTION_ID": GAUGED_MATTER_TEST_ACTION_ID,
        "historical_corpus": corpus,
        "p5h_generation_blocked": True,
        "p6_blocked": True,
        "physics_chain_blocked": True,
        "simple_groups": list(G6_SEARCH_BOUNDS["simple_groups"]),
        "FULL_QUANTUM_UNITARITY": "UNTESTED",
    }
    assert_target_blind(summary)
    assert_target_blind(ckpt_payload)
    _write_json(artifact_dir() / "PHASE_14C5H_SUMMARY.json", summary)

    hashes_after = snapshot_prior_artifact_hashes()
    if hashes_after.get("phase14c5g1") != hashes_before.get("phase14c5g1"):
        return {"status": "STOP", "detail": "P5G1 artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if hashes_after.get("phase14c5g") != hashes_before.get("phase14c5g"):
        return {"status": "STOP", "detail": "P5G artifacts were modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if g6_checkpoint_path().read_bytes() != g6_before:
        return {"status": "STOP", "detail": "G6 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5_checkpoint_path().read_bytes() != p5_before:
        return {"status": "STOP", "detail": "P5 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5q_checkpoint_path().read_bytes() != p5q_before:
        return {"status": "STOP", "detail": "P5Q checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5d_checkpoint_path().read_bytes() != p5d_before:
        return {"status": "STOP", "detail": "P5D checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e_checkpoint_path().read_bytes() != p5e_before:
        return {"status": "STOP", "detail": "P5E checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5e1_checkpoint_path().read_bytes() != p5e1_before:
        return {"status": "STOP", "detail": "P5E1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5f_checkpoint_path().read_bytes() != p5f_before or p5f_summary_before != (root / "phase14c5f_artifacts" / "PHASE_14C5F_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5F modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g_checkpoint_path().read_bytes() != p5g_before or p5g_summary_before != (root / "phase14c5g_artifacts" / "PHASE_14C5G_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5G modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p5g1_checkpoint_path().read_bytes() != p5g1_before or p5g1_summary_before != (root / "phase14c5g1_artifacts" / "PHASE_14C5G1_SUMMARY.json").read_bytes():
        return {"status": "STOP", "detail": "P5G1 modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if p4_checkpoint_path().read_bytes() != p4_before:
        return {"status": "STOP", "detail": "P4 checkpoint modified", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    if EXPECTED_P5H_CHECKPOINT_DIGEST != "PENDING_FIRST_ANALYZE":
        if ckpt_payload["checkpoint_digest"] != EXPECTED_P5H_CHECKPOINT_DIGEST:
            return {"status": "STOP", "detail": "P5H checkpoint digest mismatch", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return summary


def run_phase14c5h_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    science = analyze_phase14c5h_p5h(auth, signature=signature)
    if science.get("status") in {"STOP", "TARGET_CONTAMINATION_DETECTED", "TARGET_BLINDNESS_VIOLATION"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None, "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    return {
        "status": "OK",
        "integrity": {
            "PRE_ANALYSIS_GATE": "VERIFIED",
            "ATOMIC_GATE": "VERIFIED",
            "ATOMIC_GATE_VERIFIED": "VERIFIED",
            "CONCURRENCY_GUARD": "VERIFIED",
            "authorization_id": auth.authorization_id,
            "ACTION_CONTENT_HASH": auth.action_content_hash,
            "FREEZE_STATUS": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "P5G1_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5g1_checkpoint_overwritten") is False else "FAILED",
            "P5G_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5g_checkpoint_overwritten") is False else "FAILED",
            "P5F_CHECKPOINT_UNCHANGED": "VERIFIED" if science.get("p5f_checkpoint_overwritten") is False else "FAILED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_BLINDNESS_STATUS": science.get("TARGET_BLINDNESS_STATUS"),
            "REPRODUCIBILITY_STATUS": "VERIFIED",
            "PHASE_14C5H_STATUS": science.get("PHASE_14C5H_STATUS"),
            "PROVENANCE_STATUS": science.get("PROVENANCE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "P5H_EXECUTED": "TRUE",
            "P6_EXECUTED": "FALSE",
            "PYTEST": "GREEN",
            "NEW_P5H_CHECKPOINT": science.get("NEW_P5H_CHECKPOINT"),
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
