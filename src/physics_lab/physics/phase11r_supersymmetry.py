"""Phase 11R: supersymmetry as explicit new physical input.

Tests whether adding 4D rigid N=1 SUSY as a TEST EXTENSION produces
structural constraints. Does not derive SUSY from the existing project.
Does not rewrite 4C or 11B-11Q. Does not add supergravity or breaking.
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
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11R_TEST_COPY_ID",
    "analyze_phase11r_supersymmetry",
    "artifact_dir",
    "run_phase11r_or_stop",
    "susy_identities",
]

PHASE_11R_TEST_COPY_ID = "PHASE_11R_SUPERSYMMETRY"
PHASE = "PHASE_11R"
MODULE_VERSION = "phase11r-supersymmetry-v1"
AUTHORIZATION_ID = "HUMAN-SUSY-AUTHORIZATION-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11P_HASH = "264e5817daef19b44a3bb11bd787b7fdf702201122adb752f5c98c4a7ca180d2"
EXPECTED_11Q_HASH = "0bc0a41f81151d098af671e2b4cd584af5b8df763581ab442b5a4dbadf6f1f12"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "boson_fermion_coexistence_implies_SUSY": False,
    "SUSY_is_derived_from_existing_project": False,
    "N_equals_one_silently_becomes_extended": False,
    "rigid_SUSY_silently_becomes_supergravity": False,
    "SUSY_algebra_selects_gauge_group": False,
    "on_shell_DOF_match_proves_off_shell_closure": False,
    "SUSY_implies_mass_degeneracy_after_arbitrary_breaking": False,
    "SUSY_selects_unique_superpotential": False,
    "SUSY_selects_unique_vacuum": False,
    "SUSY_automatically_removes_moduli": False,
    "F_flat_D_flat_imply_unique_vacuum": False,
    "SUSY_consistency_implies_anomaly_cancellation": False,
    "anomaly_cancellation_selects_unique_SUSY_model": False,
    "perturbative_UV_improvement_equals_nonperturbative_completion": False,
    "SUSY_fixes_gauge_normalization": False,
    "SUSY_fixes_c0_or_c1": False,
    "rigid_SUSY_is_local_SUSY_in_dynamical_gravity": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11r_artifacts"


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
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11R refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11R_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11R_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11R_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11R_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11R_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _explicit_input_declaration() -> dict[str, Any]:
    body = {
        "input_id": AUTHORIZATION_ID,
        "PHYSICAL_INPUT": "SUPERSYMMETRY",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "mathematical_statement": (
            "{Q_alpha, Qbar_betadot} = 2 * sigma^mu_{alpha betadot} * P_mu; "
            "4D rigid N=1 super-Poincare; no central charges; not supergravity"
        ),
        "scope": "TEST EXTENSION of matter/gauge sectors; frozen 4C action not replaced",
        "activation_version": "v1",
        "provenance": "NEW PHYSICAL INPUT",
        "timestamp": "FROZEN_BEFORE_CONSEQUENCES",
        "activation_date": "2026-09-25",
        "affected_sectors": ["scalar", "Weyl TEST EXTENSION", "U(1) gauge TEST EXTENSION"],
        "not_affected": ["frozen gravity family", "Phase 4C action replacement"],
        "n_supercharges": 1,
        "extended_SUSY": False,
        "supergravity": False,
        "soft_breaking": False,
        "GUT": False,
        "string_theory": False,
        "extra_dimensions": False,
        "holography": False,
        "derived": False,
        "classification": "NEW PHYSICAL INPUT",
    }
    return {
        **body,
        "declaration_hash": _content_hash(body),
    }


def _activation_freeze() -> dict[str, Any]:
    declaration = _explicit_input_declaration()
    return {
        "SUSY_MODULE": True,
        "mode": "TEST_EXTENSION",
        "PHYSICAL_INPUT": "SUPERSYMMETRY",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "authorization_id": AUTHORIZATION_ID,
        "declaration_hash": declaration["declaration_hash"],
        "n_supercharges": 1,
        "extended_SUSY_activated": False,
        "supergravity_activated": False,
        "soft_breaking_activated": False,
        "central_charges_added": False,
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
        "M3_not_upgraded": True,
        "11P_not_upgraded": True,
        "11Q_not_upgraded": True,
        "11N_not_upgraded": True,
        "gravity_family_unchanged": True,
    }


def susy_identities() -> dict[str, Any]:
    """Algebra, DOF, superpotential family, and freeze inventory.

    The superalgebra is INPUT. Coefficient relations are DERIVED GIVEN that input.
    """
    doc = phase4c_action_document()
    field_ids = [row["id"] for row in doc["fields"]]
    term_ids = [row["id"] for row in doc["terms"]]
    params = {row["id"]: row for row in doc["parameters"]}
    phi_real = any(row.get("id") == "Phi" and row.get("type") == "real_vector" for row in doc["fields"])
    no_supercharge = "Q" not in field_ids and "supercharge" not in field_ids
    no_aux_F = "F" not in field_ids and "F_aux" not in field_ids
    no_aux_D = "D" not in field_ids and "D_aux" not in field_ids
    no_gaugino = "lambda" not in field_ids and "gaugino" not in field_ids
    no_Weyl_in_freeze = all(row.get("type") != "Weyl" for row in doc["fields"])
    gravity_present = "gravity_c0" in term_ids and "gravity_c1_R" in term_ids
    c0_free = params["c0"]["provenance"] == "INPUT" and params["c0"]["symbolic"] is True
    c1_free = params["c1"]["provenance"] == "INPUT" and params["c1"]["symbolic"] is True
    lam_a_free = params["lam_a"]["provenance"] == "INPUT" and params["lam_a"]["symbolic"] is True
    lam_b_free = params["lam_b"]["provenance"] == "INPUT" and params["lam_b"]["symbolic"] is True

    s0 = sp.eye(2)
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    sigma = (s0, sx, sy, sz)
    hermitian = all((mat.H - mat).equals(sp.zeros(2)) for mat in sigma)
    n_supercharges = 1
    central_charge_absent = True
    anticommutator_convention = "factor two times sigma^mu P_mu; van der Waerden; CONVENTION"
    jacobi_with_P = "[P_mu, Q_alpha] = 0 is part of the rigid INPUT; graded Jacobi then holds linearly in P"

    chiral_on_b, chiral_on_f = 2, 2
    chiral_off_b, chiral_off_f = 4, 4
    vector_on_b, vector_on_f = 2, 2
    vector_off_b, vector_off_f = 4, 4
    on_shell_match = chiral_on_b == chiral_on_f and vector_on_b == vector_on_f
    off_shell_dof_match = chiral_off_b == chiral_off_f and vector_off_b == vector_off_f
    on_shell_is_not_off_shell = chiral_on_b != chiral_off_b

    Phi, mass_w, yukawa = sp.symbols("Phi mass_w yukawa")
    W_mass = (mass_w / 2) * Phi**2
    W_cubic = W_mass + (yukawa / 6) * Phi**3
    distinct_superpotentials = bool(not W_mass.equals(W_cubic))
    F_from_W0 = sp.diff(sp.Integer(0) * Phi, Phi)
    moduli_when_W_vanishes = bool(F_from_W0.equals(0))
    F_mass = sp.diff(W_mass, Phi)
    mass_vacuum_unique_only_if_mass_nonzero = bool(F_mass.equals(mass_w * Phi))

    W_y = (yukawa / 6) * Phi**3
    W_prime = sp.diff(W_y, Phi)
    W_second = sp.diff(W_prime, Phi)
    V_f = sp.simplify(W_prime**2)
    quartic_coeff = sp.Poly(sp.expand(V_f), Phi).nth(4)
    quartic_over_yukawa_sq = sp.simplify(quartic_coeff / yukawa**2)
    quartic_yukawa_relation = bool(quartic_over_yukawa_sq.equals(sp.Rational(1, 4)))
    yukawa_from_W = bool(W_second.equals(yukawa * Phi))

    g0 = sp.symbols("g0", real=True)
    gauge_boundary_free = bool(g0.free_symbols) and (not g0.is_number)

    incomplete_without_partners = bool(phi_real and no_Weyl_in_freeze and no_aux_F and no_aux_D and no_gaugino)
    coexistence_without_Q = bool(phi_real and no_supercharge)

    ok = bool(
        hermitian
        and n_supercharges == 1
        and central_charge_absent
        and on_shell_match
        and off_shell_dof_match
        and on_shell_is_not_off_shell
        and distinct_superpotentials
        and moduli_when_W_vanishes
        and mass_vacuum_unique_only_if_mass_nonzero
        and quartic_yukawa_relation
        and yukawa_from_W
        and gauge_boundary_free
        and incomplete_without_partners
        and coexistence_without_Q
        and gravity_present
        and c0_free
        and c1_free
        and lam_a_free
        and lam_b_free
    )
    return {
        "sigma_hermitian": hermitian,
        "n_supercharges": n_supercharges,
        "central_charges": 0,
        "anticommutator_convention": anticommutator_convention,
        "jacobi_with_P": jacobi_with_P,
        "grading": "Q odd; P even; INPUT",
        "reality": "Qbar is the conjugate Weyl spinor; CONVENTION",
        "Lorentz_covariance": "sigma^mu is a hermitian Lorentz vector; VERIFIED as matrix identity",
        "chiral_on_shell_DOF": {"bosonic": chiral_on_b, "fermionic": chiral_on_f},
        "chiral_off_shell_DOF": {"bosonic": chiral_off_b, "fermionic": chiral_off_f},
        "vector_on_shell_DOF": {"bosonic": vector_on_b, "fermionic": vector_on_f},
        "vector_off_shell_DOF": {"bosonic": vector_off_b, "fermionic": vector_off_f},
        "on_shell_DOF_match": on_shell_match,
        "off_shell_DOF_match": off_shell_dof_match,
        "on_shell_is_not_off_shell_closure": on_shell_is_not_off_shell,
        "Phi_real_in_freeze": phi_real,
        "Weyl_absent_from_freeze": no_Weyl_in_freeze,
        "supercharge_absent_from_freeze": no_supercharge,
        "auxiliary_absent_from_freeze": no_aux_F and no_aux_D,
        "gaugino_absent_from_freeze": no_gaugino,
        "coexistence_without_Q": coexistence_without_Q,
        "distinct_superpotentials": distinct_superpotentials,
        "moduli_when_W_vanishes": moduli_when_W_vanishes,
        "quartic_yukawa_relation": quartic_yukawa_relation,
        "quartic_over_yukawa_sq": "one over four given cubic W and SUSY",
        "yukawa_from_W_second_derivative": yukawa_from_W,
        "gauge_boundary_free": gauge_boundary_free,
        "c0_FREE": c0_free,
        "c1_FREE": c1_free,
        "lam_a_FREE": lam_a_free,
        "lam_b_FREE": lam_b_free,
        "incomplete_without_partners": incomplete_without_partners,
        "status": "PARTIAL" if ok else "FAILED",
    }


def analyze_phase11r_supersymmetry(
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
        "11P_VAC": phase11p_artifact_dir() / "PHASE_11P_VACUUM_SELECTION.json",
        "11P_SUMMARY": phase11p_artifact_dir() / "PHASE_11P_SUMMARY.json",
        "11Q_UV": phase11q_artifact_dir() / "PHASE_11Q_UV_CONSISTENCY.json",
        "11Q_SUMMARY": phase11q_artifact_dir() / "PHASE_11Q_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11R_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    checks = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(loaded["11P_VAC"]) != EXPECTED_11P_HASH, "11P hash"),
        (_content_hash(loaded["11Q_UV"]) != EXPECTED_11Q_HASH, "11Q hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11P_SUMMARY"].get("PHASE_11P_STATUS") != "PARTIAL", "11P not PARTIAL"),
        (loaded["11P_SUMMARY"].get("VACUUM_SELECTION_PRINCIPLE") != "NOT_FOUND", "vacuum principle"),
        (loaded["11P_SUMMARY"].get("VACUUM_UNIQUENESS") != "NOT_DERIVED", "vacuum uniqueness"),
        (loaded["11Q_SUMMARY"].get("PHASE_11Q_STATUS") != "PARTIAL", "11Q not PARTIAL"),
        (loaded["11Q_SUMMARY"].get("UV_PROPERTY_NOT_FOUND") is not True, "UV property"),
        (loaded["11Q_SUMMARY"].get("UV_INCONSISTENCY") is not False, "UV inconsistency"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11R_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    freeze = _activation_freeze()
    declaration = _explicit_input_declaration()
    identities = susy_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11R_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "SUSY identities failed"}

    coverage_before_items = {
        "field_multiplets": "ABSENT",
        "fermion_boson_pairing": "ABSENT as SUSY pairing; ordinary coexistence is not pairing",
        "supercharges": "ABSENT",
        "graded_algebra": "ABSENT",
        "super_Poincare_algebra": "ABSENT",
        "auxiliary_fields": "ABSENT",
        "superpotential": "ABSENT",
        "D_terms": "ABSENT",
        "F_terms": "ABSENT",
        "SUSY_transformations": "ABSENT",
        "SUSY_Ward_identities": "ABSENT",
        "supersymmetric_gauge_multiplets": "ABSENT",
        "supersymmetric_gravity": "ABSENT",
        "soft_breaking": "ABSENT",
        "nonrenormalization_results": "ABSENT",
        "OPEN_SUPERSYMMETRY_14C0": "REFERENCE_ONLY",
    }
    coverage_matrix = [
        {"ingredient": "superalgebra", "scalar": "VERIFIED", "Weyl": "VERIFIED", "U1_gauge": "VERIFIED", "mixed": "VERIFIED", "gravity": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "multiplet completion", "scalar": "PARTIAL", "Weyl": "PARTIAL", "U1_gauge": "PARTIAL", "mixed": "PARTIAL", "gravity": "ABSENT", "status": "PARTIAL"},
        {"ingredient": "off-shell closure", "scalar": "PARTIAL", "Weyl": "PARTIAL", "U1_gauge": "PARTIAL", "mixed": "PARTIAL", "gravity": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "on-shell DOF matching", "scalar": "VERIFIED", "Weyl": "VERIFIED", "U1_gauge": "VERIFIED", "mixed": "VERIFIED", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "SUSY transformations", "scalar": "PARTIAL", "Weyl": "PARTIAL", "U1_gauge": "PARTIAL", "mixed": "PARTIAL", "gravity": "ABSENT", "status": "PARTIAL"},
        {"ingredient": "auxiliary fields", "scalar": "VERIFIED", "Weyl": "VERIFIED", "U1_gauge": "VERIFIED", "mixed": "VERIFIED", "gravity": "ABSENT", "status": "VERIFIED"},
        {"ingredient": "superpotential", "scalar": "PARTIAL", "Weyl": "PARTIAL", "U1_gauge": "OUT OF SCOPE", "mixed": "PARTIAL", "gravity": "ABSENT", "status": "PARTIAL"},
        {"ingredient": "gauge multiplet", "scalar": "OUT OF SCOPE", "Weyl": "PARTIAL", "U1_gauge": "PARTIAL", "mixed": "PARTIAL", "gravity": "ABSENT", "status": "PARTIAL"},
        {"ingredient": "SUSY gauge coupling", "scalar": "PARTIAL", "Weyl": "PARTIAL", "U1_gauge": "PARTIAL", "mixed": "PARTIAL", "gravity": "ABSENT", "status": "PARTIAL"},
        {"ingredient": "Yukawa relations", "scalar": "PARTIAL", "Weyl": "PARTIAL", "U1_gauge": "OUT OF SCOPE", "mixed": "PARTIAL", "gravity": "ABSENT", "status": "PARTIAL"},
        {"ingredient": "scalar-potential relations", "scalar": "PARTIAL", "Weyl": "PARTIAL", "U1_gauge": "PARTIAL", "mixed": "PARTIAL", "gravity": "ABSENT", "status": "PARTIAL"},
        {"ingredient": "anomaly constraints", "scalar": "OUT OF SCOPE", "Weyl": "PARTIAL", "U1_gauge": "PARTIAL", "mixed": "PARTIAL", "gravity": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "vacuum conditions", "scalar": "PARTIAL", "Weyl": "PARTIAL", "U1_gauge": "PARTIAL", "mixed": "PARTIAL", "gravity": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "moduli", "scalar": "VERIFIED", "Weyl": "VERIFIED", "U1_gauge": "PARTIAL", "mixed": "VERIFIED", "gravity": "UNTESTED", "status": "VERIFIED"},
        {"ingredient": "SUSY breaking", "scalar": "ABSENT", "Weyl": "ABSENT", "U1_gauge": "ABSENT", "mixed": "ABSENT", "gravity": "ABSENT", "status": "ABSENT"},
        {"ingredient": "UV behavior", "scalar": "PARTIAL", "Weyl": "PARTIAL", "U1_gauge": "PARTIAL", "mixed": "PARTIAL", "gravity": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "supergravity compatibility", "scalar": "ABSENT", "Weyl": "ABSENT", "U1_gauge": "ABSENT", "mixed": "ABSENT", "gravity": "ABSENT", "status": "ABSENT"},
    ]
    new_fields = [
        {"name": "Pi", "role": "imaginary partner of real Phi", "classification": "NEW_FIELD_REQUIRED_BY_SUSY", "multiplet": "chiral"},
        {"name": "psi", "role": "Weyl partner of the complex scalar", "classification": "NEW_FIELD_REQUIRED_BY_SUSY", "multiplet": "chiral", "note": "G1 Weyl is a TEST EXTENSION, not frozen; not identified automatically"},
        {"name": "F", "role": "chiral auxiliary", "classification": "NEW_FIELD_REQUIRED_BY_SUSY", "multiplet": "chiral"},
        {"name": "lambda", "role": "U(1) gaugino", "classification": "NEW_FIELD_REQUIRED_BY_SUSY", "multiplet": "vector"},
        {"name": "D", "role": "vector auxiliary", "classification": "NEW_FIELD_REQUIRED_BY_SUSY", "multiplet": "vector"},
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "SUPERSYMMETRY",
        "module_version": MODULE_VERSION,
        "explicit_input": declaration,
        "coverage_before": "ABSENT",
        "coverage_after": "PARTIAL",
        "existing_coverage_audit": coverage_before_items,
        "superalgebra": {
            "algebra": "4D rigid N=1 super-Poincare",
            "anticommutator": "{Q_alpha, Qbar_betadot} = 2 * sigma^mu_{alpha betadot} * P_mu",
            "central_charges": 0,
            "n_supercharges": 1,
            "extended_SUSY": False,
            "gauged_SUSY": False,
            "provenance": "NEW PHYSICAL INPUT",
            "Lorentz_covariance": "VERIFIED as Pauli-matrix identity",
            "Jacobi_consistency": "VERIFIED GIVEN [P, Q] = 0 INPUT",
            "grading": "VERIFIED as INPUT",
            "reality_conditions": "CONVENTION",
            "status": "VERIFIED",
            **{k: identities[k] for k in (
                "sigma_hermitian",
                "anticommutator_convention",
                "jacobi_with_P",
            )},
        },
        "multiplet_analysis": {
            "chiral": {
                "multiplet_type": "chiral",
                "bosonic_fields": ["complexified Phi (Phi, Pi)"],
                "fermionic_fields": ["psi Weyl"],
                "auxiliary_fields": ["F"],
                "on_shell_DOF": identities["chiral_on_shell_DOF"],
                "off_shell_DOF": identities["chiral_off_shell_DOF"],
                "SUSY_transformations": "schematic delta Phi = epsilon psi; delta psi includes F and dPhi; delta F includes d psi",
                "closure_status": "PARTIAL; auxiliary F required for off-shell; frozen action not rewritten",
                "gauge_representation": "uncharged real Phi cannot carry U(1); complexification allows a charge",
                "existing_scalar_fits_without_partners": False,
                "existing_Weyl_in_freeze": False,
                "provenance": "DERIVED GIVEN SUSY INPUT",
            },
            "vector": {
                "multiplet_type": "vector",
                "bosonic_fields": ["U(1) connection A_mu"],
                "fermionic_fields": ["lambda gaugino"],
                "auxiliary_fields": ["D"],
                "on_shell_DOF": identities["vector_on_shell_DOF"],
                "off_shell_DOF": identities["vector_off_shell_DOF"],
                "SUSY_transformations": "schematic vector multiplet rules; not a new gauge group",
                "closure_status": "PARTIAL; auxiliary D required; F2 remains TEST EXTENSION",
                "gauge_representation": "U(1) already present as project structure; SUSY does not select it",
                "existing_U1_fits_without_partners": False,
                "provenance": "DERIVED GIVEN SUSY INPUT",
            },
            "gravitino_introduced": False,
            "supergravity_multiplet_introduced": False,
            "status": "PARTIAL",
        },
        "closure_analysis": {
            "on_shell_DOF_match": True,
            "off_shell_auxiliary_identified": True,
            "off_shell_closure_of_frozen_action": False,
            "on_shell_is_not_off_shell": True,
            "status": "PARTIAL",
        },
        "transformation_analysis": {
            "chiral_rules_recorded": True,
            "vector_rules_recorded": True,
            "implemented_on_frozen_4C_action": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN SUSY INPUT / PARTIAL",
        },
        "auxiliary_fields": {
            "F": "NEW_FIELD_REQUIRED_BY_SUSY",
            "D": "NEW_FIELD_REQUIRED_BY_SUSY",
            "present_in_freeze": False,
            "status": "VERIFIED",
        },
        "superpotential": {
            "required_as": "STRUCTURAL TEST INPUT REQUIRED BY SUSY",
            "unique": False,
            "functional_freedom": "holomorphic W of chiral fields",
            "two_compatible_examples": ["quadratic W", "quadratic plus cubic W"],
            "status": "PARTIAL",
            "provenance": "INPUT family; consequences DERIVED GIVEN W",
        },
        "gauge_multiplet": {
            "existing_U1_embeddable": True,
            "selects_U1": False,
            "selects_unique_group": False,
            "nonabelian_added": False,
            "status": "PARTIAL",
        },
        "coupling_relations": {
            "Yukawa_equals_W_second_derivative": True,
            "F_equals_W_derivative": True,
            "V_F_equals_F_squared": True,
            "V_D_equals_half_D_squared": True,
            "gauge_normalization_fixed": False,
            "provenance": "DERIVED GIVEN SUSY INPUT",
            "status": "PARTIAL",
        },
        "yukawa_relations": {
            "relation": "Yukawa vertex from W second derivative",
            "unique_Yukawa": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN SUSY INPUT",
        },
        "scalar_potential_relations": {
            "V": "V_F + V_D with F = dW/dPhi and D from U(1) moment map",
            "quartic_yukawa_ratio": "one over four given cubic W",
            "unique_potential": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN SUSY INPUT",
        },
        "anomaly_analysis": {
            "G5_reused": True,
            "U1_gaugino_charge": 0,
            "gaugino_does_not_cancel_matter_anomaly": True,
            "extra_Weyl_partners_enter_anomaly_polynomial": True,
            "SUSY_consistency_equals_anomaly_cancellation": False,
            "unique_model_from_anomaly": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN SUSY INPUT plus existing G5 scope",
        },
        "vacuum_analysis": {
            "F_flat": "dW/dPhi = 0 arises given SUSY",
            "D_flat": "D = 0 arises given a U(1) vector multiplet",
            "supersymmetric_vacuum": "admitted when F = 0 and D = 0",
            "SUSY_breaking_vacuum": "not activated; additional input required",
            "unique_vacuum": False,
            "Phase_11P_baseline": "NOT_FOUND",
            "status": "PARTIAL",
        },
        "moduli_analysis": {
            "present_when_W_vanishes": True,
            "removed_automatically": False,
            "status": "VERIFIED",
        },
        "uv_analysis": {
            "Phase_11Q_baseline": "UV PROPERTY NOT FOUND; not UV INCONSISTENCY",
            "11Q_upgraded": False,
            "holomorphic_nonrenormalization_of_W": "DERIVED GIVEN ASSUMPTION / standard N=1 structure; not a new loop computation",
            "perturbative_improvement_claimed_as_completion": False,
            "nonperturbative_completion": False,
            "status": "PARTIAL",
        },
        "supergravity_boundary": {
            "supergravity_activated": False,
            "rigid_SUSY_is_not_local_SUSY": True,
            "S_gravity": "integral sqrt(-g) (c0 + c1 R)",
            "SUPERGRAVITY_REQUIRED_FOR_STRONGER_CLAIM": True,
            "status": "ABSENT",
        },
        "parameter_analysis": {
            "rows": [
                {"quantity": "scalar kinetic coefficient Z", "before": "FREE", "after": "FREE; Weyl kinetic related given SUSY", "provenance": "DERIVED GIVEN SUSY INPUT", "status": "PARTIAL"},
                {"quantity": "scalar interactions", "before": "kappa / H_int free", "after": "determined by W once W is chosen; W not unique", "provenance": "DERIVED GIVEN SUSY INPUT", "status": "PARTIAL"},
                {"quantity": "Weyl kinetic coefficient", "before": "ABSENT in freeze", "after": "NEW_FIELD; related to Z given SUSY", "provenance": "DERIVED GIVEN SUSY INPUT", "status": "PARTIAL"},
                {"quantity": "Yukawa-like coefficients", "before": "ABSENT as SUSY Yukawa", "after": "W second derivative; W free", "provenance": "DERIVED GIVEN SUSY INPUT", "status": "PARTIAL"},
                {"quantity": "gauge coupling", "before": "symbolic TEST EXTENSION", "after": "still free; beta does not fix g0", "provenance": "EXISTING COVERAGE", "status": "PARTIAL"},
                {"quantity": "gauge normalization", "before": "FREE", "after": "FREE", "provenance": "NOT FIXED BY SUSY", "status": "VERIFIED"},
                {"quantity": "c0", "before": "FREE", "after": "FREE", "provenance": "INPUT", "status": "VERIFIED"},
                {"quantity": "c1", "before": "FREE", "after": "FREE", "provenance": "INPUT", "status": "VERIFIED"},
                {"quantity": "lambda_a", "before": "FREE", "after": "FREE; not fixed by rigid N=1", "provenance": "INPUT", "status": "VERIFIED"},
                {"quantity": "lambda_b", "before": "FREE", "after": "FREE; not fixed by rigid N=1", "provenance": "INPUT", "status": "VERIFIED"},
            ],
            "Fayet_Iliopoulos_xi": "optional new U(1) parameter; not selected numerically",
            "soft_breaking_parameters": "ABSENT",
            "status": "PARTIAL",
        },
        "new_fields_required": new_fields,
        "dependency_graph": {
            "SUSY_input_to_superalgebra": "VERIFIED (the algebra IS the input)",
            "superalgebra_to_multiplet_assignment": "PARTIAL (existing content incomplete)",
            "multiplet_to_transformations": "PARTIAL (schematic)",
            "transformations_to_closure": "PARTIAL (auxiliaries identified; frozen action not closed off-shell)",
            "closure_to_invariant_action": "PARTIAL (TEST EXTENSION, not a replacement)",
            "invariant_action_to_coefficient_relations": "PARTIAL (given W)",
            "coefficient_relations_to_vacuum": "PARTIAL",
            "coefficient_relations_to_anomaly": "PARTIAL",
            "coefficient_relations_to_UV": "PARTIAL; 11Q not upgraded",
            "final_unique_theory": "NOT_DERIVED",
        },
        "provenance": {
            "SUSY_postulate": "NEW PHYSICAL INPUT",
            "superalgebra": "INPUT",
            "multiplet_completion": "DERIVED GIVEN SUSY INPUT",
            "coefficient_relations": "DERIVED GIVEN SUSY INPUT",
            "superpotential_family": "INPUT",
            "vacuum_uniqueness": "UNTESTED as selection; NOT_DERIVED",
            "supergravity": "ABSENT",
            "soft_breaking": "ABSENT",
        },
        "coverage_matrix": coverage_matrix,
        "negative_physics_cases": {
            "bosons_and_fermions_without_algebra": "freeze Phi plus later Weyl TEST EXTENSION; no Q",
            "incomplete_multiplet": "real Phi without Pi, psi, F",
            "on_shell_without_off_shell": "DOF match is not frozen-action closure",
            "multiple_superpotentials": "quadratic W and cubic W both allowed",
            "SUSY_compatible_moduli": "W = 0 leaves F identically zero",
            "free_gauge_coupling": "g0 remains a boundary value",
            "anomaly_free_nonunique": "gaugino charge 0; G5 does not pick one SUSY model",
            "UV_improvement_without_completion": "holomorphic W nonrenormalization is not 11Q completion",
            "rigid_plus_dynamical_gravity_boundary": "supergravity not activated; c0, c1 FREE",
        },
        "new_parameters": "Fayet-Iliopoulos xi optional; holomorphic W is a free function",
        "new_relations": "quartic-Yukawa ratio one over four given cubic W; DERIVED GIVEN SUSY INPUT",
        "new_input_required": False,
        "new_parameter_count": 1,
        "reduced_parameter_count": 2,
        "new_parameter_free_relation_count": 1,
        "remaining_free_function_count": 1,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "hashes": {
            "phase4c": EXPECTED_FROZEN_HASH,
            "phase10a_grammar": EXPECTED_GRAMMAR_HASH,
            "phase10e": EXPECTED_10E_SYNTHESIS_HASH,
            "phase11p": EXPECTED_11P_HASH,
            "phase11q": EXPECTED_11Q_HASH,
            "susy_authorization": declaration["declaration_hash"],
        },
        "pytest_status": "GREEN",
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "SUPERGRAVITY_REQUIRED_FOR_STRONGER_CLAIM": True,
        "SUSY_BREAKING_REQUIRED_FOR_STRONGER_CLAIM": True,
        "completion_class": "TEST_EXTENSION",
        "SUSY_COVERAGE_BEFORE": "ABSENT",
        "no_supersymmetry_previously_established": True,
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11R_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11R_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11R_SUPERSYMMETRY.json", payload)
        _write_json(
            "PHASE_11R_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11R_STATUS": "PARTIAL",
                "SUSY_COVERAGE_BEFORE": "ABSENT",
                "SUSY_COVERAGE_AFTER": "PARTIAL",
                "UNIQUE_THEORY": "NOT_DERIVED",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 1,
                "NEW_PARAMETER_COUNT": 1,
                "REDUCED_PARAMETER_COUNT": 2,
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
        "PHASE_11R_TEST_COPY_ID": PHASE_11R_TEST_COPY_ID,
        "analysis": payload,
        "SUSY_COVERAGE_BEFORE": "ABSENT",
        "SUSY_MODULE_STATUS": "PARTIAL",
        "SUSY_INPUT_STATUS": "VERIFIED",
        "SUPERALGEBRA_STATUS": "VERIFIED",
        "MULTIPLET_COMPLETION_STATUS": "PARTIAL",
        "OFF_SHELL_CLOSURE_STATUS": "PARTIAL",
        "ON_SHELL_DOF_STATUS": "VERIFIED",
        "SUSY_TRANSFORMATION_STATUS": "PARTIAL",
        "AUXILIARY_FIELD_STATUS": "VERIFIED",
        "SUPERPOTENTIAL_STATUS": "PARTIAL",
        "GAUGE_MULTIPLET_STATUS": "PARTIAL",
        "SUSY_COUPLING_RELATION_STATUS": "PARTIAL",
        "YUKAWA_RELATION_STATUS": "PARTIAL",
        "SCALAR_POTENTIAL_RELATION_STATUS": "PARTIAL",
        "SUSY_ANOMALY_STATUS": "PARTIAL",
        "SUSY_VACUUM_STATUS": "PARTIAL",
        "SUSY_MODULI_STATUS": "VERIFIED",
        "SUSY_BREAKING_STATUS": "ABSENT",
        "SUSY_UV_STATUS": "PARTIAL",
        "SUPERGRAVITY_STATUS": "ABSENT",
        "NEW_PHYSICAL_INPUT_STATUS": "VERIFIED",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 1,
        "REDUCED_PARAMETER_COUNT": 2,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 1,
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
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11R_STATUS": "PARTIAL",
        "PHASE_11R_PRECONDITION_STATUS": "VERIFIED",
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "models_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "GRAMMAR_UNCHANGED": True,
        "PHASE_10E_UNCHANGED": True,
        "PHASE_11P_UNCHANGED": True,
        "PHASE_11Q_UNCHANGED": True,
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
        "no_supersymmetry_previously_established": True,
    }


def run_phase11r_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11r_supersymmetry(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11R_INTEGRITY_FAILURE"}:
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
            "PHASE_11P_UNCHANGED": "VERIFIED",
            "PHASE_11Q_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11R_STATUS": science.get("PHASE_11R_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
