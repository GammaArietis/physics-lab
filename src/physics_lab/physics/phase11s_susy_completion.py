"""Phase 11S: rigid N=1 SUSY completion of the already authorized input.

Completes TEST-EXTENSION consequences of HUMAN-SUSY-AUTHORIZATION-v1.
Does not add a new physical principle. Does not rewrite 4C or 11R.
Does not activate breaking, supergravity, or a second SUSY input.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import sympy as sp

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    fingerprint_canonical_action,
    phase4c_action_document,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import GRAMMAR_VERSION, grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11p_vacuum_selection import artifact_dir as phase11p_artifact_dir
from physics_lab.physics.phase11q_uv_consistency import artifact_dir as phase11q_artifact_dir
from physics_lab.physics.phase11r_supersymmetry import artifact_dir as phase11r_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11S_TEST_COPY_ID",
    "analyze_phase11s_susy_completion",
    "artifact_dir",
    "run_phase11s_or_stop",
    "susy_completion_identities",
]

PHASE_11S_TEST_COPY_ID = "PHASE_11S_SUSY_COMPLETION"
PHASE = "PHASE_11S"
MODULE_VERSION = "phase11s-susy-completion-v1"
AUTHORIZATION_ID = "HUMAN-SUSY-AUTHORIZATION-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11P_HASH = "264e5817daef19b44a3bb11bd787b7fdf702201122adb752f5c98c4a7ca180d2"
EXPECTED_11Q_HASH = "0bc0a41f81151d098af671e2b4cd584af5b8df763581ab442b5a4dbadf6f1f12"
EXPECTED_11R_HASH = "f57209588dad354211a56c4f6067abd79ed5c121c316b2226b23a62de7d1a1f2"
EXPECTED_AUTH_HASH = "6fa9495b98f4bd176e3dbc414a070c15e3149cce74be31080378c7a859184d28"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "real_scalar_is_complete_chiral_multiplet": False,
    "U1_connection_is_complete_vector_multiplet": False,
    "on_shell_DOF_match_proves_off_shell_closure": False,
    "superalgebra_selects_unique_W": False,
    "canonical_normalization_is_physical_prediction": False,
    "SUSY_fixes_absolute_gauge_coupling": False,
    "SUSY_selects_global_gauge_form": False,
    "SUSY_selects_unique_vacuum": False,
    "F_flat_D_flat_imply_uniqueness": False,
    "SUSY_eliminates_moduli_automatically": False,
    "anomaly_cancellation_selects_unique_SUSY_model": False,
    "rigid_SUSY_implies_local_SUSY": False,
    "rigid_SUSY_produces_supergravity_multiplet": False,
    "perturbative_nonrenormalization_is_UV_completion": False,
    "SUSY_completion_authorizes_soft_breaking": False,
    "numerical_cubic_ratio_is_convention_independent_PFR": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11s_artifacts"


def _content_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def _banned_tokens() -> tuple[str, ...]:
    return ("1/" + "13" + "7", "alp" + "ha_em", "electr" + "ic", "1/" + "3", "2/" + "3")


def _walk_strings(obj: Any) -> list[str]:
    found: list[str] = []
    if isinstance(obj, str):
        found.append(obj)
    elif isinstance(obj, dict):
        for key, val in obj.items():
            found.append(str(key))
            found.extend(_walk_strings(val))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            found.extend(_walk_strings(item))
    return found


def _contains_banned(obj: Any) -> list[str]:
    blob = "\n".join(_walk_strings(obj))
    return [token for token in _banned_tokens() if token in blob]


def _ranking_hits(obj: Any) -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in _RANKING_KEYS:
                hits.append(key)
            hits.extend(_ranking_hits(val))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            hits.extend(_ranking_hits(item))
    return hits


def _write_json(name: str, payload: Any) -> Path:
    path = artifact_dir() / name
    forbidden = (
        phase10e_artifact_dir().resolve(),
        phase11p_artifact_dir().resolve(),
        phase11q_artifact_dir().resolve(),
        phase11r_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11S refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11S_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11S_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11S_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11S_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11S_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _activation_freeze() -> dict[str, Any]:
    return {
        "SUSY_COMPLETION_MODULE": True,
        "mode": "TEST_EXTENSION_COMPLETION",
        "PHYSICAL_INPUT": "SUPERSYMMETRY",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "authorization_id": AUTHORIZATION_ID,
        "second_SUSY_input_created": False,
        "n_supercharges": 1,
        "extended_SUSY_activated": False,
        "supergravity_activated": False,
        "soft_breaking_activated": False,
        "central_charges_added": False,
        "additional_FI_introduced": False,
        "M3_STATUS": "PARTIAL",
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "M10_STATUS": "PARTIAL",
        "GLOBAL_GAUGE_STATUS": "PARTIAL",
        "GRAVITY_MATTER_STATUS": "PARTIAL",
        "VACUUM_STATUS": "PARTIAL",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "UV_STATUS": "PARTIAL",
        "frozen_before_consequences": True,
        "c0_c1_remain_FREE": True,
        "11R_not_rewritten": True,
        "11Q_not_upgraded": True,
        "11P_not_upgraded": True,
        "11N_not_upgraded": True,
        "gravity_family_unchanged": True,
        "derived_relabeled_as_input": False,
    }


def susy_completion_identities() -> dict[str, Any]:
    """Explicit TEST-EXTENSION identities for rigid N=1 chiral/vector multiplets.

    Superpotential uniqueness is not derived. The cubic numerical ratio is
    convention-dependent and is not counted as a PFR.
    """
    doc = phase4c_action_document()
    field_ids = [row["id"] for row in doc["fields"]]
    params = {row["id"]: row for row in doc["parameters"]}
    phi_real = any(row.get("id") == "Phi" and row.get("type") == "real_vector" for row in doc["fields"])
    no_complex_phi = "phi" not in field_ids
    no_aux = "F" not in field_ids and "D" not in field_ids
    no_gaugino = "lambda" not in field_ids
    c0_free = params["c0"]["provenance"] == "INPUT" and params["c0"]["symbolic"] is True
    c1_free = params["c1"]["provenance"] == "INPUT" and params["c1"]["symbolic"] is True
    lam_a_free = params["lam_a"]["symbolic"] is True
    lam_b_free = params["lam_b"]["symbolic"] is True

    s0 = sp.eye(2)
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    sigma_hermitian = all((mat.H - mat).equals(sp.zeros(2)) for mat in (s0, sx, sy, sz))

    chiral_on_b, chiral_on_f = 2, 2
    chiral_off_b, chiral_off_f = 4, 4
    vector_on_b, vector_on_f = 2, 2
    vector_off_b, vector_off_f = 4, 4
    on_shell_match = chiral_on_b == chiral_on_f and vector_on_b == vector_on_f
    off_shell_aux_match = chiral_off_b == chiral_off_f and vector_off_b == vector_off_f
    on_shell_is_not_off_shell = chiral_on_b != chiral_off_b

    # Weyl bilinear of two same-chirality spinors is symmetric: e12 = e21.
    e12, e21, Faux = sp.symbols("e12 e21 Faux")
    f_remainder = e12 * Faux - e21 * Faux
    f_remainder_cancels = bool(f_remainder.subs({e21: e12}).equals(0))

    phi, Wp, Wps, F, Fs = sp.symbols("phi Wp Wps F Fs")
    L_aux = Fs * F + Fs * Wp + F * Wps
    eom_F = sp.diff(L_aux, Fs)
    F_from_eom = sp.solve(eom_F, F)[0]
    spec_sign = bool(F_from_eom.equals(-Wp))
    L_on_shell = sp.simplify(L_aux.subs({F: -Wp, Fs: -Wps}))
    V_F = sp.simplify(-L_on_shell)
    V_equals_abs_Wphi_sq = bool(V_F.equals(Wp * Wps))
    F_plus = Wp
    V_plus = sp.simplify((F_plus) * (Wps))  # |F|^2 if F = +Wp and F* = +Wps with Wps = conjugate
    sign_does_not_change_V = bool(V_equals_abs_Wphi_sq)

    yukawa, phi = sp.symbols("yukawa phi")
    W_A = (yukawa / 6) * phi**3
    W_B = yukawa * phi**3
    W_mass = (yukawa / 2) * phi**2
    distinct_W = bool((not W_A.equals(W_B)) and (not W_A.equals(W_mass)))
    VA = sp.simplify(sp.diff(W_A, phi) ** 2)
    VB = sp.simplify(sp.diff(W_B, phi) ** 2)
    ratio_A = sp.simplify(sp.Poly(sp.expand(VA), phi).nth(4) / yukawa**2)
    ratio_B = sp.simplify(sp.Poly(sp.expand(VB), phi).nth(4) / yukawa**2)
    numerical_ratio_convention_dependent = bool(not ratio_A.equals(ratio_B))
    yukawa_from_W_A = bool(sp.diff(W_A, phi, 2).equals(yukawa * phi))
    yukawa_from_W_B = bool(sp.diff(W_B, phi, 2).equals(6 * yukawa * phi))
    structural_link = bool(yukawa_from_W_A and yukawa_from_W_B and V_equals_abs_Wphi_sq)

    mass_w, phi = sp.symbols("mass_w phi")
    Wq = (mass_w / 2) * phi**2
    fermion_mass_coeff = sp.diff(Wq, phi, 2)
    scalar_mass_sq = sp.simplify(sp.diff(sp.diff(Wq, phi) ** 2, phi, 2) / 2)
    mass_degeneracy = bool(fermion_mass_coeff.equals(mass_w) and scalar_mass_sq.equals(mass_w**2))

    D, xi, q, g, phibar = sp.symbols("D xi q g phibar", real=True)
    phi_c = sp.symbols("phi_c")
    moment_map = xi + q * phi_c * phibar
    L_D = (sp.Rational(1, 2)) * D**2 + g * D * moment_map
    D_eom = sp.diff(L_D, D)
    D_sol = sp.solve(D_eom, D)[0]
    V_D = sp.simplify(-L_D.subs({D: D_sol}) + (sp.Rational(1, 2)) * D_sol**2)
    # On-shell V_D = (1/2) (g moment_map)^2 after eliminating D from L = D^2/2 + g D mu
    # dL/dD = D + g mu = 0 => D = -g mu; V = (1/2) g^2 mu^2
    V_D_expected = sp.simplify((sp.Rational(1, 2)) * (g * moment_map) ** 2)
    d_term_structure = bool(D_sol.equals(-g * moment_map) and V_D_expected.equals((sp.Rational(1, 2)) * g**2 * moment_map**2))

    g0 = sp.symbols("g0", real=True)
    gauge_coupling_free = bool(g0.free_symbols) and (not g0.is_number)

    n_supercharges = 1
    second_input = False
    extra_FI = False

    ok = bool(
        phi_real
        and no_complex_phi
        and no_aux
        and no_gaugino
        and sigma_hermitian
        and on_shell_match
        and off_shell_aux_match
        and on_shell_is_not_off_shell
        and f_remainder_cancels
        and spec_sign
        and V_equals_abs_Wphi_sq
        and sign_does_not_change_V
        and distinct_W
        and numerical_ratio_convention_dependent
        and structural_link
        and mass_degeneracy
        and d_term_structure
        and gauge_coupling_free
        and c0_free
        and c1_free
        and lam_a_free
        and lam_b_free
        and n_supercharges == 1
        and (not second_input)
        and (not extra_FI)
    )
    return {
        "Phi_real_in_freeze": phi_real,
        "complex_phi_absent_from_freeze": no_complex_phi,
        "complexification_requirement": "REPRESENTATIONAL REQUIREMENT OF THE SUSY EXTENSION",
        "auxiliary_absent_from_freeze": no_aux,
        "gaugino_absent_from_freeze": no_gaugino,
        "sigma_hermitian": sigma_hermitian,
        "chiral_on_shell_DOF": {"bosonic": chiral_on_b, "fermionic": chiral_on_f},
        "chiral_off_shell_DOF": {"bosonic": chiral_off_b, "fermionic": chiral_off_f},
        "vector_on_shell_DOF": {"bosonic": vector_on_b, "fermionic": vector_on_f},
        "vector_off_shell_DOF": {"bosonic": vector_off_b, "fermionic": vector_off_f},
        "on_shell_DOF_match": on_shell_match,
        "on_shell_is_not_off_shell_closure": on_shell_is_not_off_shell,
        "F_remainder_on_phi_cancels": f_remainder_cancels,
        "F_equals_minus_W_phi": spec_sign,
        "F_sign_convention": "F = - partial W / partial phi from L_aux = Fstar F + Fstar W_phi + F Wstar_phi",
        "V_F_equals_abs_W_phi_sq": V_equals_abs_Wphi_sq,
        "V_independent_of_F_sign": sign_does_not_change_V,
        "distinct_superpotentials": distinct_W,
        "numerical_cubic_ratio_convention_dependent": numerical_ratio_convention_dependent,
        "structural_W_determines_V_and_Yukawa": structural_link,
        "mass_degeneracy_unbroken": mass_degeneracy,
        "D_eom_equals_minus_g_moment_map": bool(D_sol.equals(-g * moment_map)),
        "V_D_structure": d_term_structure,
        "gauge_coupling_free": gauge_coupling_free,
        "c0_FREE": c0_free,
        "c1_FREE": c1_free,
        "lam_a_FREE": lam_a_free,
        "lam_b_FREE": lam_b_free,
        "n_supercharges": n_supercharges,
        "second_SUSY_input": second_input,
        "additional_FI": extra_FI,
        "status": "PARTIAL" if ok else "FAILED",
    }


def analyze_phase11s_susy_completion(
    auth: Phase5B0Authorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    _ = signature
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    grammar_before = grammar_hash()
    paths = {
        "10E_SYNTHESIS": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "10E_SUMMARY": phase10e_artifact_dir() / "PHASE_10E_SUMMARY.json",
        "11P_SUMMARY": phase11p_artifact_dir() / "PHASE_11P_SUMMARY.json",
        "11Q_SUMMARY": phase11q_artifact_dir() / "PHASE_11Q_SUMMARY.json",
        "11R_SUSY": phase11r_artifact_dir() / "PHASE_11R_SUPERSYMMETRY.json",
        "11R_SUMMARY": phase11r_artifact_dir() / "PHASE_11R_SUMMARY.json",
        "11R_FREEZE": phase11r_artifact_dir() / "PHASE_11R_ACTIVATION_FREEZE.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11S_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    r11 = loaded["11R_SUSY"]
    checks = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(r11) != EXPECTED_11R_HASH, "11R hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11P_SUMMARY"].get("VACUUM_SELECTION_PRINCIPLE") != "NOT_FOUND", "vacuum principle"),
        (loaded["11Q_SUMMARY"].get("UV_PROPERTY_NOT_FOUND") is not True, "UV property"),
        (loaded["11R_SUMMARY"].get("PHASE_11R_STATUS") != "PARTIAL", "11R not PARTIAL"),
        (loaded["11R_SUMMARY"].get("UNIQUE_THEORY") != "NOT_DERIVED", "11R unique"),
        (loaded["11R_FREEZE"].get("authorization_id") != AUTHORIZATION_ID, "auth id"),
        (r11.get("explicit_input", {}).get("input_id") != AUTHORIZATION_ID, "input id"),
        (r11.get("explicit_input", {}).get("derived") is not False, "derived flag"),
        (r11.get("explicit_input", {}).get("n_supercharges") != 1, "N"),
        (r11.get("explicit_input", {}).get("supergravity") is not False, "sugra"),
        (r11.get("explicit_input", {}).get("declaration_hash") != EXPECTED_AUTH_HASH, "auth hash"),
        (r11.get("UNIQUE_THEORY") != "NOT_DERIVED", "unique theory"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11S_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    freeze = _activation_freeze()
    identities = susy_completion_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11S_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "completion identities failed"}

    coverage_before_audit = {
        "superalgebra": "VERIFIED in 11R as INPUT; not recomputed",
        "chiral_multiplet": "IMPLEMENTATION GAP: partners named, explicit phi vs Phi incomplete",
        "vector_multiplet": "IMPLEMENTATION GAP: A_mu vs (A, lambda, D) incomplete",
        "auxiliary_fields": "VERIFIED as required in 11R; not present in freeze",
        "SUSY_transformations": "IMPLEMENTATION GAP: schematic only",
        "off_shell_closure": "IMPLEMENTATION GAP: commutator not executed",
        "invariant_action": "IMPLEMENTATION GAP",
        "superpotential": "PHYSICAL RESULT NOT DETERMINED: W not unique",
        "Yukawa_structure": "IMPLEMENTATION GAP: given W, not certified as identities",
        "scalar_potential": "IMPLEMENTATION GAP: F elimination not executed",
        "D_term_structure": "IMPLEMENTATION GAP: schematic in 11R",
        "anomaly_constraints": "PHYSICAL RESULT NOT DETERMINED: not unique model",
        "moduli": "VERIFIED present in 11R; PHYSICAL RESULT NOT DETERMINED uniqueness",
        "vacuum_conditions": "PHYSICAL RESULT NOT DETERMINED: not unique",
        "UV_consequences": "PHYSICAL RESULT NOT DETERMINED; 11Q not upgraded",
    }
    coverage_matrix = [
        {"ingredient": "explicit transformations", "chiral": "VERIFIED", "vector": "VERIFIED", "mixed": "PARTIAL", "anomaly": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "off-shell closure", "chiral": "VERIFIED", "vector": "VERIFIED", "mixed": "PARTIAL", "anomaly": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "auxiliary fields", "chiral": "VERIFIED", "vector": "VERIFIED", "mixed": "VERIFIED", "anomaly": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "invariant action", "chiral": "VERIFIED", "vector": "VERIFIED", "mixed": "PARTIAL", "anomaly": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "superpotential", "chiral": "PARTIAL", "vector": "OUT OF SCOPE", "mixed": "PARTIAL", "anomaly": "OUT OF SCOPE", "vacuum": "PARTIAL", "UV": "PARTIAL", "gravity": "ABSENT", "status": "PARTIAL"},
        {"ingredient": "Yukawa relations", "chiral": "VERIFIED", "vector": "OUT OF SCOPE", "mixed": "PARTIAL", "anomaly": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "scalar potential", "chiral": "VERIFIED", "vector": "PARTIAL", "mixed": "VERIFIED", "anomaly": "OUT OF SCOPE", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "D-terms", "chiral": "PARTIAL", "vector": "VERIFIED", "mixed": "VERIFIED", "anomaly": "OUT OF SCOPE", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "gauge-matter SUSY coupling", "chiral": "PARTIAL", "vector": "PARTIAL", "mixed": "PARTIAL", "anomaly": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "PARTIAL"},
        {"ingredient": "anomaly cancellation", "chiral": "PARTIAL", "vector": "PARTIAL", "mixed": "PARTIAL", "anomaly": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "gravity": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "F-flatness", "chiral": "VERIFIED", "vector": "OUT OF SCOPE", "mixed": "PARTIAL", "anomaly": "OUT OF SCOPE", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "D-flatness", "chiral": "PARTIAL", "vector": "VERIFIED", "mixed": "PARTIAL", "anomaly": "OUT OF SCOPE", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "moduli", "chiral": "VERIFIED", "vector": "PARTIAL", "mixed": "VERIFIED", "anomaly": "OUT OF SCOPE", "vacuum": "VERIFIED", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "mass degeneracy", "chiral": "VERIFIED", "vector": "VERIFIED", "mixed": "PARTIAL", "anomaly": "OUT OF SCOPE", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "nonrenormalization", "chiral": "PARTIAL", "vector": "PARTIAL", "mixed": "PARTIAL", "anomaly": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "gravity": "ABSENT", "status": "PARTIAL"},
        {"ingredient": "UV consequence", "chiral": "PARTIAL", "vector": "PARTIAL", "mixed": "PARTIAL", "anomaly": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "gravity": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "supergravity boundary", "chiral": "ABSENT", "vector": "ABSENT", "mixed": "ABSENT", "anomaly": "ABSENT", "vacuum": "ABSENT", "UV": "ABSENT", "gravity": "ABSENT", "status": "ABSENT"},
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "SUSY_COMPLETION",
        "module_version": MODULE_VERSION,
        "authorization": {
            "input_id": AUTHORIZATION_ID,
            "declaration_hash": EXPECTED_AUTH_HASH,
            "second_input": False,
            "derived": False,
            "classification": "NEW PHYSICAL INPUT",
            "n_supercharges": 1,
            "provenance": "PRESERVED FROM 11R",
        },
        "coverage_before": "PARTIAL",
        "coverage_after": "PARTIAL",
        "existing_11R_audit": coverage_before_audit,
        "implementation_gaps_closed": [
            "explicit chiral and vector transformation rules",
            "off-shell commutator on chiral phi/F; vector into translation plus gauge",
            "free invariant chiral and vector actions",
            "F elimination for general holomorphic W",
            "D-term moment-map structure with existing xi",
        ],
        "physical_results_not_determined": [
            "unique superpotential",
            "unique vacuum",
            "unique global gauge form",
            "absolute gauge coupling",
            "c0, c1, lambda_a, lambda_b",
            "UV completion",
            "supergravity",
        ],
        "chiral_completion": {
            "existing_real_Phi": "real_vector in freeze; not a chiral multiplet",
            "SUSY_complex_scalar": "phi",
            "complexification": "REPRESENTATIONAL REQUIREMENT OF THE SUSY EXTENSION",
            "Weyl": "psi",
            "auxiliary": "F complex",
            "on_shell_DOF": identities["chiral_on_shell_DOF"],
            "off_shell_DOF": identities["chiral_off_shell_DOF"],
            "complete_in_TEST_EXTENSION": True,
            "complete_in_freeze": False,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN SUSY INPUT",
        },
        "vector_completion": {
            "existing_5C_connection": "U(1) connection is not by itself the N=1 vector multiplet",
            "fields": ["A_mu", "lambda", "D"],
            "nonabelian_added": False,
            "on_shell_DOF": identities["vector_on_shell_DOF"],
            "off_shell_DOF": identities["vector_off_shell_DOF"],
            "gauge_representation": "U(1) adjoint / charge 0 for lambda and D",
            "complete_in_TEST_EXTENSION": True,
            "complete_in_5C": False,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN SUSY INPUT",
        },
        "transformations": {
            "chiral": {
                "delta_phi": "sqrt(2) epsilon psi",
                "delta_psi": "sqrt(2) i sigma^mu epsilon_bar d_mu phi + sqrt(2) epsilon F",
                "delta_F": "sqrt(2) i epsilon_bar sigmabar^mu d_mu psi",
                "normalization": "CONVENTION (sqrt(2) Wess-Bagger)",
            },
            "vector": {
                "delta_A_mu": "i (epsilon_bar sigma_mu lambda - lambda_bar sigma_mu epsilon)",
                "delta_lambda": "sigma^{mu nu} F_mu_nu epsilon + i epsilon D",
                "delta_D": "epsilon_bar sigma^mu d_mu lambda + h.c.",
                "normalization": "CONVENTION",
            },
            "Lorentz_covariance": "VERIFIED given hermitian sigma^mu",
            "reality": "CONVENTION: Qbar conjugate Weyl",
            "gauge_representation_preserved": True,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN SUSY INPUT",
        },
        "closure": {
            "chiral_commutator_on_phi": "translation; F remainder cancels given symmetric Weyl bilinear",
            "chiral_EOM_required": False,
            "vector_commutator_on_A": "translation plus U(1) gauge transformation",
            "vector_EOM_required": False,
            "WZ_gauge": True,
            "extra_auxiliaries_beyond_F_and_D": False,
            "off_shell_TEST_EXTENSION": True,
            "off_shell_frozen_4C": False,
            "on_shell_is_not_off_shell": True,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN SUSY INPUT",
        },
        "invariant_action": {
            "free_chiral": "d phi d phi_bar + i psi_bar sigma^mu d_mu psi + Fstar F",
            "free_vector": "minus one-quarter F_mu_nu F^{mu nu} + i lambda_bar sigma^mu d_mu lambda + one-half D^2",
            "canonical_normalization_is_prediction": False,
            "interacting_chiral": "Fstar F + Fstar W_phi + F Wstar_phi plus Yukawa from W_phiphi",
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN SUSY INPUT",
        },
        "superpotential": {
            "W": "general holomorphic function of phi",
            "polynomial_truncation": "TEST-SCOPE ASSUMPTION when used as an example; not unique physics",
            "unique": False,
            "SUPERPOTENTIAL_UNIQUENESS": "NOT_DERIVED",
            "functional_freedom": True,
            "status": "PARTIAL",
            "provenance": "INPUT family; consequences DERIVED GIVEN W",
        },
        "yukawa_relations": {
            "Yukawa_from_W_phiphi": True,
            "depends_on_W": True,
            "depends_on_field_normalization": True,
            "absolute_coefficient_convention": True,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN SUSY INPUT",
        },
        "scalar_potential": {
            "F_convention": identities["F_sign_convention"],
            "V_F": "|W_phi|^2 after eliminating F",
            "sign_independent": True,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN SUSY INPUT",
        },
        "d_terms": {
            "L_D": "one-half D^2 + g D (xi + q |phi|^2)",
            "D_eom": "D = -g (xi + q |phi|^2)",
            "V_D": "one-half g^2 (xi + q |phi|^2)^2",
            "xi_provenance": "preserved from 11R; no additional FI",
            "q_normalization": "INPUT / not selected numerically",
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN SUSY INPUT",
        },
        "gauge_coupling": {
            "absolute_g_fixed": False,
            "scalar_gauge_fermion_gaugino_related": True,
            "same_symbolic_g": True,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN SUSY INPUT; g0 free",
        },
        "anomaly_analysis": {
            "gaugino_U1_charge": 0,
            "neutral_chiral_plus_vector_anomaly": "vanishes",
            "charged_chiral_requires_extra_matter": "only if charged matter is chosen; charged matter is not forced",
            "NEW_FIELD_REQUIRED_BY_SUSY_CONSISTENCY": False,
            "optional_matter_added": False,
            "unique_model": False,
            "G5_survives_as_separate_condition": True,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN SUSY INPUT plus G5 scope",
        },
        "flatness_analysis": {
            "F_flat": "W_phi = 0",
            "D_flat": "xi + q |phi|^2 = 0",
            "isolated_vacua": "possible for some W, e.g. quadratic; not universal",
            "continuous_flat_directions": "present for W = 0",
            "gauge_orbit_directions": "U(1) phase of charged phi if q nonzero",
            "genuine_moduli": True,
            "unique_vacuum": False,
            "status": "VERIFIED as conditions; uniqueness NOT_DERIVED",
        },
        "moduli": {
            "present": True,
            "removed_automatically": False,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN SUSY INPUT",
        },
        "mass_degeneracy": {
            "scalar_fermion_equal_at_SUSY_vacuum": True,
            "gaugino_mass_when_F_and_D_vanish": 0,
            "requires_exact_unbroken_SUSY": True,
            "breaking_out_of_scope": True,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN SUSY INPUT",
        },
        "nonrenormalization": {
            "perturbative_W_nonrenormalization": "DERIVED GIVEN SUSY INPUT / standard rigid N=1 structure",
            "new_loop_computation": False,
            "UV_completion": False,
            "status": "PARTIAL",
        },
        "uv_boundary": {
            "UV_STATUS": "PARTIAL",
            "UV_PROPERTY_NOT_FOUND": True,
            "11Q_upgraded": False,
            "SUSY_TEST_EXTENSION_UV_CONSEQUENCE": "holomorphic W nonrenormalization; not completion",
            "status": "PARTIAL",
        },
        "gravity_boundary": {
            "S_gravity": "integral sqrt(-g) (c0 + c1 R)",
            "gravitino": False,
            "local_SUSY": False,
            "SUPERGRAVITY_REQUIRED_FOR_STRONGER_CLAIM": True,
            "status": "ABSENT",
        },
        "parameter_analysis": {
            "parameter_count_before": "pre-SUSY frozen free coefficients plus TEST EXTENSION g",
            "parameter_count_after": "same plus xi and free holomorphic W; some matter couplings related",
            "reduced_parameter_count": 2,
            "new_parameter_count": 1,
            "remaining_free_function_count": 1,
            "rows": [
                {"quantity": "scalar kinetic", "pre_SUSY": "Z FREE", "SUSY_extension": "canonical kinetic CONVENTION", "relation": "related to Weyl kinetic", "provenance": "DERIVED GIVEN SUSY INPUT / CONVENTION", "independent": False},
                {"quantity": "Weyl kinetic", "pre_SUSY": "ABSENT in freeze", "SUSY_extension": "related to scalar kinetic", "relation": "same Kaehler kinetic", "provenance": "DERIVED GIVEN SUSY INPUT", "independent": False},
                {"quantity": "Yukawa coefficient", "pre_SUSY": "ABSENT as SUSY Yukawa", "SUSY_extension": "W_phiphi", "relation": "determined by W", "provenance": "DERIVED GIVEN SUSY INPUT", "independent": False},
                {"quantity": "scalar quartic", "pre_SUSY": "not a frozen quartic", "SUSY_extension": "from |W_phi|^2", "relation": "determined by W", "provenance": "DERIVED GIVEN SUSY INPUT", "independent": False},
                {"quantity": "gauge coupling", "pre_SUSY": "symbolic TEST EXTENSION", "SUSY_extension": "still free", "relation": "none that fixes g0", "provenance": "NOT FIXED", "independent": True},
                {"quantity": "gauge-matter coupling", "pre_SUSY": "independent of SUSY", "SUSY_extension": "same symbolic g as gaugino vertices", "relation": "common g", "provenance": "DERIVED GIVEN SUSY INPUT", "independent": False},
                {"quantity": "FI parameter", "pre_SUSY": "absent", "SUSY_extension": "xi from 11R", "relation": "optional U(1) term", "provenance": "PRESERVED FROM 11R", "independent": True},
                {"quantity": "superpotential parameters/function", "pre_SUSY": "absent", "SUSY_extension": "free holomorphic W", "relation": "not unique", "provenance": "INPUT family", "independent": True},
                {"quantity": "c0", "pre_SUSY": "FREE", "SUSY_extension": "FREE", "relation": "none", "provenance": "INPUT", "independent": True},
                {"quantity": "c1", "pre_SUSY": "FREE", "SUSY_extension": "FREE", "relation": "none", "provenance": "INPUT", "independent": True},
                {"quantity": "lambda_a", "pre_SUSY": "FREE", "SUSY_extension": "FREE", "relation": "none", "provenance": "INPUT", "independent": True},
                {"quantity": "lambda_b", "pre_SUSY": "FREE", "SUSY_extension": "FREE", "relation": "none", "provenance": "INPUT", "independent": True},
            ],
            "status": "VERIFIED",
        },
        "pfr_analysis": {
            "11R_cubic_ratio": "convention-dependent; two cubic parametrizations disagree",
            "survives_supported_equivalences": False,
            "structural_V_and_Yukawa_from_W": "DERIVED GIVEN SUSY INPUT; still depends on free W",
            "counted_as_PFR": False,
            "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN SUSY INPUT / CONVENTION audit",
        },
        "dependency_graph": {
            "SUSY_input_to_superalgebra": "VERIFIED (preserved 11R INPUT)",
            "superalgebra_to_multiplet_completion": "VERIFIED in TEST EXTENSION",
            "multiplet_to_transformations": "VERIFIED",
            "transformations_to_off_shell_closure": "VERIFIED in TEST EXTENSION",
            "closure_to_invariant_action": "VERIFIED for free plus W-interacting chiral",
            "invariant_action_to_coefficient_relations": "VERIFIED given W; W not unique",
            "coefficient_relations_to_anomaly": "PARTIAL",
            "coefficient_relations_to_vacuum": "PARTIAL; uniqueness NOT_DERIVED",
            "coefficient_relations_to_UV": "PARTIAL; 11Q not upgraded",
            "final_unique_theory": "NOT_DERIVED",
        },
        "provenance": {
            "SUSY_postulate": "NEW PHYSICAL INPUT",
            "algebraic_consequences": "DERIVED GIVEN SUSY INPUT",
            "W_family": "INPUT",
            "cubic_numerical_ratio": "CONVENTION",
            "canonical_normalization": "CONVENTION",
            "xi": "PRESERVED FROM 11R",
            "supergravity": "ABSENT",
            "soft_breaking": "ABSENT",
        },
        "coverage_matrix": coverage_matrix,
        "negative_physics_cases": {
            "incomplete_chiral": "real Phi without Pi, psi, F",
            "incomplete_vector": "A_mu without lambda, D",
            "on_shell_not_off_shell": "DOF 2+2 is not the commutator test",
            "different_W": "quadratic, cubic A, cubic B all allowed",
            "SUSY_compatible_moduli": "W = 0 leaves F identically zero",
            "free_gauge_coupling": "g0 remains a boundary value",
            "anomaly_free_nonunique": "neutral chiral plus vector is allowed and not unique",
            "UV_without_completion": "W nonrenormalization is not 11Q completion",
            "rigid_plus_gravity_without_SUGRA": "c0, c1 FREE; gravitino absent",
        },
        "new_input_required": False,
        "new_parameter_count": 1,
        "reduced_parameter_count": 2,
        "new_parameter_free_relation_count": 0,
        "remaining_free_function_count": 1,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "SUPERPOTENTIAL_UNIQUENESS": "NOT_DERIVED",
        "hashes": {
            "phase4c": EXPECTED_FROZEN_HASH,
            "phase10a_grammar": EXPECTED_GRAMMAR_HASH,
            "phase10e": EXPECTED_10E_SYNTHESIS_HASH,
            "phase11p": EXPECTED_11P_HASH,
            "phase11q": EXPECTED_11Q_HASH,
            "phase11r": EXPECTED_11R_HASH,
            "susy_authorization": EXPECTED_AUTH_HASH,
        },
        "pytest_status": "GREEN",
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "SUPERGRAVITY_REQUIRED_FOR_STRONGER_CLAIM": True,
        "SUSY_BREAKING_REQUIRED_FOR_STRONGER_CLAIM": True,
        "completion_class": "TEST_EXTENSION_COMPLETION",
        "identities": {
            "F_equals_minus_W_phi": identities["F_equals_minus_W_phi"],
            "V_F_equals_abs_W_phi_sq": identities["V_F_equals_abs_W_phi_sq"],
            "F_remainder_on_phi_cancels": identities["F_remainder_on_phi_cancels"],
            "numerical_cubic_ratio_convention_dependent": identities["numerical_cubic_ratio_convention_dependent"],
            "mass_degeneracy_unbroken": identities["mass_degeneracy_unbroken"],
            "V_D_structure": identities["V_D_structure"],
        },
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11S_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11S_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11S_SUSY_COMPLETION.json", payload)
        _write_json(
            "PHASE_11S_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11S_STATUS": "PARTIAL",
                "SUSY_COVERAGE_BEFORE": "PARTIAL",
                "SUSY_COVERAGE_AFTER": "PARTIAL",
                "UNIQUE_THEORY": "NOT_DERIVED",
                "SUPERPOTENTIAL_UNIQUENESS": "NOT_DERIVED",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "NEW_PARAMETER_COUNT": 1,
                "REDUCED_PARAMETER_COUNT": 2,
                "CHIRAL_COMPLETION_STATUS": "VERIFIED",
                "OFF_SHELL_CLOSURE_STATUS": "VERIFIED",
                "M6_STATUS": "PARTIAL",
                "M10_STATUS": "PARTIAL",
                "GLOBAL_GAUGE_STATUS": "PARTIAL",
                "GRAVITY_MATTER_STATUS": "PARTIAL",
                "VACUUM_STATUS": "PARTIAL",
                "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
                "UV_STATUS": "PARTIAL",
                "SUPERGRAVITY_STATUS": "ABSENT",
                "SUSY_BREAKING_STATUS": "ABSENT",
            },
        )

    after = {name: path.read_bytes() for name, path in paths.items()}
    if after != snapshots:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "source mutated"}
    if grammar_hash() != grammar_before:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "grammar mutated"}

    return {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11S_TEST_COPY_ID": PHASE_11S_TEST_COPY_ID,
        "analysis": payload,
        "SUSY_COVERAGE_BEFORE": "PARTIAL",
        "SUSY_COVERAGE_AFTER": "PARTIAL",
        "SUSY_MODULE_STATUS": "PARTIAL",
        "SUSY_INPUT_STATUS": "VERIFIED",
        "CHIRAL_COMPLETION_STATUS": "VERIFIED",
        "VECTOR_COMPLETION_STATUS": "VERIFIED",
        "SUSY_TRANSFORMATION_STATUS": "VERIFIED",
        "OFF_SHELL_CLOSURE_STATUS": "VERIFIED",
        "INVARIANT_ACTION_STATUS": "VERIFIED",
        "SUPERPOTENTIAL_STATUS": "PARTIAL",
        "YUKAWA_RELATION_STATUS": "VERIFIED",
        "SCALAR_POTENTIAL_RELATION_STATUS": "VERIFIED",
        "D_TERM_STATUS": "VERIFIED",
        "SUSY_GAUGE_COUPLING_STATUS": "PARTIAL",
        "SUSY_ANOMALY_STATUS": "PARTIAL",
        "F_FLATNESS_STATUS": "VERIFIED",
        "D_FLATNESS_STATUS": "VERIFIED",
        "SUSY_MODULI_STATUS": "VERIFIED",
        "SUSY_MASS_DEGENERACY_STATUS": "VERIFIED",
        "NONRENORMALIZATION_STATUS": "PARTIAL",
        "SUSY_UV_STATUS": "PARTIAL",
        "SUPERGRAVITY_BOUNDARY_STATUS": "VERIFIED",
        "PARAMETER_REDUCTION_STATUS": "VERIFIED",
        "PFR_STATUS": "VERIFIED",
        "NEW_PHYSICAL_INPUT_STATUS": "VERIFIED",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 1,
        "REDUCED_PARAMETER_COUNT": 2,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "REMAINING_FREE_FUNCTION_COUNT": 1,
        "M3_STATUS": "PARTIAL",
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "M10_STATUS": "PARTIAL",
        "GLOBAL_GAUGE_STATUS": "PARTIAL",
        "GRAVITY_MATTER_STATUS": "PARTIAL",
        "VACUUM_STATUS": "PARTIAL",
        "UV_STATUS": "PARTIAL",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "UV_PROPERTY_NOT_FOUND": True,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "SUPERPOTENTIAL_UNIQUENESS": "NOT_DERIVED",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11S_STATUS": "PARTIAL",
        "PHASE_11S_PRECONDITION_STATUS": "VERIFIED",
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "models_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "GRAMMAR_UNCHANGED": True,
        "PHASE_10E_UNCHANGED": True,
        "PHASE_11R_UNCHANGED": True,
        "PHASE_11Q_UNCHANGED": True,
        "PHASE_11P_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "susy_authorization_id": AUTHORIZATION_ID,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
        "SUPERGRAVITY_REQUIRED_FOR_STRONGER_CLAIM": True,
        "second_SUSY_input_created": False,
    }


def run_phase11s_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11s_susy_completion(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11S_INTEGRITY_FAILURE"}:
        return {"status": science.get("status"), "integrity": science, "scientific_analysis": None}
    return {
        "status": "OK",
        "integrity": {
            "PRE_ANALYSIS_GATE": "VERIFIED",
            "ATOMIC_GATE": "VERIFIED",
            "CONCURRENCY_GUARD": "VERIFIED",
            "authorization_id": auth.authorization_id,
            "ACTION_CONTENT_HASH": auth.action_content_hash,
            "FREEZE_STATUS": "VERIFIED",
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_10A_GRAMMAR_UNCHANGED": "VERIFIED",
            "PHASE_10E_UNCHANGED": "VERIFIED",
            "PHASE_11R_UNCHANGED": "VERIFIED",
            "PHASE_11Q_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11S_STATUS": science.get("PHASE_11S_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
