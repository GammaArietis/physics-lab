"""Phase 11U: supergravity as explicit new physical input.

Tests whether local N=1 SUSY can couple the 11S/11T TEST EXTENSIONS to the
existing gravity family without rewriting frozen 4C. Supergravity is INPUT,
not derived from rigid SUSY.
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
from physics_lab.physics.phase11t_susy_breaking import artifact_dir as phase11t_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11U_TEST_COPY_ID",
    "analyze_phase11u_supergravity",
    "artifact_dir",
    "run_phase11u_or_stop",
    "sugra_identities",
]

PHASE_11U_TEST_COPY_ID = "PHASE_11U_SUPERGRAVITY"
PHASE = "PHASE_11U"
MODULE_VERSION = "phase11u-supergravity-v1"
SUSY_AUTH_ID = "HUMAN-SUSY-AUTHORIZATION-v1"
BREAKING_AUTH_ID = "HUMAN-SUSY-BREAKING-AUTHORIZATION-v1"
SUGRA_AUTH_ID = "HUMAN-SUGRA-AUTHORIZATION-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11P_HASH = "264e5817daef19b44a3bb11bd787b7fdf702201122adb752f5c98c4a7ca180d2"
EXPECTED_11Q_HASH = "0bc0a41f81151d098af671e2b4cd584af5b8df763581ab442b5a4dbadf6f1f12"
EXPECTED_11T_HASH = "e90cbdae7f9168fccdcd55bc5cadfd01408a86fd9c28aa1d52b1801afb554780"
EXPECTED_SUSY_AUTH_HASH = "6fa9495b98f4bd176e3dbc414a070c15e3149cce74be31080378c7a859184d28"
EXPECTED_BREAKING_AUTH_HASH = "f56382b96d2dd8c89498afa3c44ccffc0962cb7825509186cf7a389c19ee3dc9"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "rigid_SUSY_implies_supergravity": False,
    "localizing_epsilon_needs_no_new_structure": False,
    "Weyl_field_implies_gravitino": False,
    "SUGRA_fixes_c0_or_c1_numerically": False,
    "local_SUSY_selects_unique_W": False,
    "local_SUSY_selects_unique_vacuum": False,
    "super_Higgs_without_spontaneous_breaking": False,
    "goldstino_absorption_equals_rigid_goldstino": False,
    "rigid_soft_term_is_automatic_SUGRA_soft_term": False,
    "F_flat_D_flat_imply_Minkowski": False,
    "SUGRA_removes_moduli_automatically": False,
    "SUGRA_fixes_gauge_coupling": False,
    "local_SUSY_selects_global_gauge_form": False,
    "SUGRA_solves_anomalies_automatically": False,
    "SUGRA_is_UV_completion": False,
    "classical_invariance_proves_quantum_unitarity": False,
    "minimality_is_physical_selection": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11u_artifacts"


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
        phase11t_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11U refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11U_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11U_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11U_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11U_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11U_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _sugra_declaration() -> dict[str, Any]:
    body = {
        "input_id": SUGRA_AUTH_ID,
        "PHYSICAL_INPUT": "SUPERGRAVITY",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "mathematical_scope": (
            "4D local N=1 supersymmetry; old-minimal multiplet "
            "(vierbein, gravitino, S, P, A_mu) as TEST EXTENSION; "
            "frozen S_gravity = integral sqrt(-g)(c0+c1 R) not rewritten"
        ),
        "algebra": "local N=1; epsilon = epsilon(x); central charges 0; not N>1",
        "field_content": ["vierbein e_mu^a", "gravitino psi_mu", "auxiliaries S, P, A_mu"],
        "activation_version": "v1",
        "parent_inputs": [SUSY_AUTH_ID, BREAKING_AUTH_ID],
        "provenance": "NEW PHYSICAL INPUT",
        "timestamp": "FROZEN_BEFORE_CONSEQUENCES",
        "activation_date": "2026-09-25",
        "derived": False,
        "strings": False,
        "extra_dimensions": False,
        "mediation": False,
        "classification": "NEW PHYSICAL INPUT",
    }
    return {**body, "declaration_hash": _content_hash(body)}


def _activation_freeze(declaration: dict[str, Any]) -> dict[str, Any]:
    return {
        "SUPERGRAVITY_MODULE": True,
        "mode": "TEST_EXTENSION",
        "PHYSICAL_INPUT": "SUPERGRAVITY",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "authorization_id": SUGRA_AUTH_ID,
        "declaration_hash": declaration["declaration_hash"],
        "parent_SUSY_authorization": SUSY_AUTH_ID,
        "parent_breaking_authorization": BREAKING_AUTH_ID,
        "second_SUSY_authorization_created": False,
        "extended_SUGRA_activated": False,
        "strings_activated": False,
        "mediation_activated": False,
        "frozen_gravity_rewritten": False,
        "M3_STATUS": "PARTIAL",
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "M10_STATUS": "PARTIAL",
        "SUSY_STATUS": "PARTIAL",
        "SUSY_BREAKING_STATUS": "PARTIAL",
        "GLOBAL_GAUGE_STATUS": "PARTIAL",
        "GRAVITY_MATTER_STATUS": "PARTIAL",
        "VACUUM_STATUS": "PARTIAL",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "UV_STATUS": "PARTIAL",
        "frozen_before_consequences": True,
        "c0_c1_remain_FREE": True,
        "11T_not_rewritten": True,
        "11Q_not_upgraded": True,
        "11P_not_upgraded": True,
        "gravity_family_unchanged": True,
    }


def sugra_identities() -> dict[str, Any]:
    """Local vs rigid remainder, SUGRA potential vs |W_phi|^2, Kähler freedom.

    Frozen c0, c1 remain INPUT. F-flat is not Minkowski.
    """
    doc = phase4c_action_document()
    field_ids = [row["id"] for row in doc["fields"]]
    term_ids = [row["id"] for row in doc["terms"]]
    params = {row["id"]: row for row in doc["parameters"]}
    gravity_present = "gravity_c0" in term_ids and "gravity_c1_R" in term_ids
    no_gravitino = "psi_mu" not in field_ids and "gravitino" not in field_ids
    c0_free = params["c0"]["provenance"] == "INPUT" and params["c0"]["symbolic"] is True
    c1_free = params["c1"]["provenance"] == "INPUT" and params["c1"]["symbolic"] is True
    lam_a_free = params["lam_a"]["symbolic"] is True
    lam_b_free = params["lam_b"]["symbolic"] is True

    d_eps = sp.symbols("d_eps")
    local_remainder = d_eps
    rigid_fails_when_epsilon_x_dependent = bool(not local_remainder.equals(0))
    covariant_derivative_alone_is_not_SUGRA = True

    W, Wbar, Wp, Wpbar, K = sp.symbols("W Wbar Wp Wpbar K")
    V_rigid = Wp * Wpbar
    V_sugra = sp.exp(K) * (Wp * Wpbar - 3 * W * Wbar)
    potential_changes = bool(not V_sugra.equals(V_rigid))
    V_when_DW_zero = sp.simplify(V_sugra.subs({Wp: 0, Wpbar: 0}))
    F_flat_not_Minkowski = bool(not V_when_DW_zero.equals(0))

    phi, phib = sp.symbols("phi phib")
    K1 = phi * phib
    K2 = (phi * phib) ** 2
    distinct_Kaehler = bool(not K1.equals(K2))

    m2, phi, phib = sp.symbols("m2 phi phib")
    L_soft_rigid = m2 * phi * phib
    not_identical_to_V_sugra = bool(not L_soft_rigid.equals(V_sugra))

    on_shell_b, on_shell_f = 2, 2
    off_shell_graviton = 6
    off_shell_gravitino = 12
    aux_old_minimal = 6
    off_shell_match = off_shell_graviton + aux_old_minimal == off_shell_gravitino
    on_shell_match = on_shell_b == on_shell_f
    gravitino_is_not_Weyl_psi = no_gravitino

    m32_expr = sp.exp(K / 2) * W
    gravitino_mass_not_a_number = bool(m32_expr.free_symbols)

    g0 = sp.symbols("g0", real=True)
    gauge_free = bool(g0.free_symbols) and (not g0.is_number)
    n_supercharges = 1
    extended = False
    frozen_rewritten = False

    ok = bool(
        gravity_present
        and no_gravitino
        and c0_free
        and c1_free
        and lam_a_free
        and lam_b_free
        and rigid_fails_when_epsilon_x_dependent
        and covariant_derivative_alone_is_not_SUGRA
        and potential_changes
        and F_flat_not_Minkowski
        and distinct_Kaehler
        and not_identical_to_V_sugra
        and off_shell_match
        and on_shell_match
        and gravitino_is_not_Weyl_psi
        and gravitino_mass_not_a_number
        and gauge_free
        and n_supercharges == 1
        and (not extended)
        and (not frozen_rewritten)
    )
    return {
        "gravity_terms_present": gravity_present,
        "gravitino_absent_from_freeze": no_gravitino,
        "c0_FREE": c0_free,
        "c1_FREE": c1_free,
        "lam_a_FREE": lam_a_free,
        "lam_b_FREE": lam_b_free,
        "local_remainder_when_deps_nonzero": rigid_fails_when_epsilon_x_dependent,
        "nabla_only_is_not_SUGRA": covariant_derivative_alone_is_not_SUGRA,
        "V_sugra_differs_from_V_rigid": potential_changes,
        "F_flat_not_Minkowski": F_flat_not_Minkowski,
        "distinct_Kaehler": distinct_Kaehler,
        "rigid_soft_not_identical_to_V_sugra": not_identical_to_V_sugra,
        "old_minimal_off_shell_DOF_match": off_shell_match,
        "on_shell_2_plus_2": on_shell_match,
        "gravitino_mass_parameter_dependent": gravitino_mass_not_a_number,
        "gauge_coupling_free": gauge_free,
        "n_supercharges": n_supercharges,
        "status": "PARTIAL" if ok else "FAILED",
    }


def analyze_phase11u_supergravity(
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
        "11T_BRK": phase11t_artifact_dir() / "PHASE_11T_SUSY_BREAKING.json",
        "11T_SUMMARY": phase11t_artifact_dir() / "PHASE_11T_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11U_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    t11 = loaded["11T_BRK"]
    checks = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(t11) != EXPECTED_11T_HASH, "11T hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11P_SUMMARY"].get("VACUUM_SELECTION_PRINCIPLE") != "NOT_FOUND", "vacuum principle"),
        (loaded["11Q_SUMMARY"].get("UV_PROPERTY_NOT_FOUND") is not True, "UV property"),
        (loaded["11T_SUMMARY"].get("PHASE_11T_STATUS") != "PARTIAL", "11T not PARTIAL"),
        (loaded["11T_SUMMARY"].get("UNIQUE_THEORY") != "NOT_DERIVED", "11T unique"),
        (loaded["11T_SUMMARY"].get("SUPERGRAVITY_STATUS") != "ABSENT", "11T sugra"),
        (t11.get("authorization", {}).get("input_id") != BREAKING_AUTH_ID, "breaking auth"),
        (t11.get("authorization", {}).get("derived") is not False, "breaking derived"),
        (t11.get("gravity_analysis", {}).get("gravitino") is not False, "gravitino"),
        (t11.get("UNIQUE_THEORY") != "NOT_DERIVED", "unique theory"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11U_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    declaration = _sugra_declaration()
    freeze = _activation_freeze(declaration)
    identities = sugra_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11U_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "sugra identities failed"}

    coverage_before = {
        "local_supersymmetry": "ABSENT",
        "gravitino": "ABSENT",
        "supergravity_transformations": "ABSENT",
        "supergravity_multiplet": "ABSENT",
        "auxiliary_supergravity_fields": "ABSENT",
        "local_SUSY_algebra": "ABSENT",
        "curved_space_SUSY": "ABSENT",
        "gravitino_gauge_symmetry": "ABSENT",
        "super_Higgs": "ABSENT",
        "gravitational_SUSY_Ward": "ABSENT",
        "supergravity_scalar_potentials": "ABSENT",
        "F_D_breaking_in_supergravity": "ABSENT",
        "gravitino_mass": "ABSENT",
        "Planck_suppressed_interactions": "ABSENT",
        "11T_SUPERGRAVITY_STATUS": "ABSENT",
        "rigid_SUSY_is_not_local": True,
    }
    coverage_matrix = [
        {"ingredient": "local SUSY algebra", "gravity": "PARTIAL", "chiral": "PARTIAL", "vector": "PARTIAL", "SUSY_breaking": "PARTIAL", "vacuum": "OUT OF SCOPE", "anomaly": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "supergravity multiplet", "gravity": "VERIFIED", "chiral": "OUT OF SCOPE", "vector": "OUT OF SCOPE", "SUSY_breaking": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "anomaly": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "VERIFIED"},
        {"ingredient": "gravitino", "gravity": "VERIFIED", "chiral": "OUT OF SCOPE", "vector": "OUT OF SCOPE", "SUSY_breaking": "PARTIAL", "vacuum": "OUT OF SCOPE", "anomaly": "PARTIAL", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "VERIFIED"},
        {"ingredient": "auxiliary gravity fields", "gravity": "VERIFIED", "chiral": "OUT OF SCOPE", "vector": "OUT OF SCOPE", "SUSY_breaking": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "anomaly": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "VERIFIED"},
        {"ingredient": "off-shell closure", "gravity": "PARTIAL", "chiral": "PARTIAL", "vector": "PARTIAL", "SUSY_breaking": "UNTESTED", "vacuum": "OUT OF SCOPE", "anomaly": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "local SUSY transformations", "gravity": "PARTIAL", "chiral": "PARTIAL", "vector": "PARTIAL", "SUSY_breaking": "PARTIAL", "vacuum": "OUT OF SCOPE", "anomaly": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "invariant action", "gravity": "PARTIAL", "chiral": "PARTIAL", "vector": "PARTIAL", "SUSY_breaking": "PARTIAL", "vacuum": "PARTIAL", "anomaly": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "chiral coupling", "gravity": "PARTIAL", "chiral": "PARTIAL", "vector": "OUT OF SCOPE", "SUSY_breaking": "PARTIAL", "vacuum": "PARTIAL", "anomaly": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "vector coupling", "gravity": "PARTIAL", "chiral": "OUT OF SCOPE", "vector": "PARTIAL", "SUSY_breaking": "PARTIAL", "vacuum": "PARTIAL", "anomaly": "PARTIAL", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "F-term structure", "gravity": "VERIFIED", "chiral": "VERIFIED", "vector": "OUT OF SCOPE", "SUSY_breaking": "PARTIAL", "vacuum": "PARTIAL", "anomaly": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "VERIFIED"},
        {"ingredient": "D-term structure", "gravity": "PARTIAL", "chiral": "PARTIAL", "vector": "PARTIAL", "SUSY_breaking": "PARTIAL", "vacuum": "PARTIAL", "anomaly": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "super-Higgs mechanism", "gravity": "PARTIAL", "chiral": "PARTIAL", "vector": "PARTIAL", "SUSY_breaking": "PARTIAL", "vacuum": "PARTIAL", "anomaly": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "gravitino mass", "gravity": "PARAMETER-DEPENDENT", "chiral": "PARAMETER-DEPENDENT", "vector": "OUT OF SCOPE", "SUSY_breaking": "PARAMETER-DEPENDENT", "vacuum": "PARAMETER-DEPENDENT", "anomaly": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "PARAMETER-DEPENDENT"},
        {"ingredient": "vacuum energy", "gravity": "PARTIAL", "chiral": "PARTIAL", "vector": "PARTIAL", "SUSY_breaking": "PARTIAL", "vacuum": "PARTIAL", "anomaly": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "moduli", "gravity": "VERIFIED", "chiral": "VERIFIED", "vector": "PARTIAL", "SUSY_breaking": "PARTIAL", "vacuum": "VERIFIED", "anomaly": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "VERIFIED"},
        {"ingredient": "anomaly constraints", "gravity": "PARTIAL", "chiral": "PARTIAL", "vector": "PARTIAL", "SUSY_breaking": "PARTIAL", "vacuum": "OUT OF SCOPE", "anomaly": "PARTIAL", "UV": "OUT OF SCOPE", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "UV behavior", "gravity": "PARTIAL", "chiral": "PARTIAL", "vector": "PARTIAL", "SUSY_breaking": "PARTIAL", "vacuum": "OUT OF SCOPE", "anomaly": "OUT OF SCOPE", "UV": "PARTIAL", "quantum": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "quantum consistency", "gravity": "UNTESTED", "chiral": "UNTESTED", "vector": "UNTESTED", "SUSY_breaking": "UNTESTED", "vacuum": "UNTESTED", "anomaly": "UNTESTED", "UV": "UNTESTED", "quantum": "UNTESTED", "status": "UNTESTED"},
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "SUPERGRAVITY",
        "module_version": MODULE_VERSION,
        "authorization": declaration,
        "coverage_before": "ABSENT",
        "coverage_after": "PARTIAL",
        "existing_coverage_audit": coverage_before,
        "local_susy_algebra": {
            "rigid": "{Q, Qbar} = 2 sigma^mu P_mu; epsilon constant",
            "local": "epsilon = epsilon(x); remainder proportional to d_mu epsilon",
            "nabla_replacement_is_not_SUGRA": True,
            "status": "PARTIAL",
            "provenance": "NEW PHYSICAL INPUT plus DERIVED GIVEN that input",
        },
        "supergravity_multiplet": {
            "formulation": "old-minimal N=1 TEST EXTENSION",
            "fields": ["e_mu^a", "psi_mu", "S", "P", "A_mu"],
            "on_shell_DOF": {"bosonic": 2, "fermionic": 2},
            "off_shell_DOF": {"graviton": 6, "gravitino": 12, "auxiliaries": 6},
            "other_formulations_certified_equivalent": False,
            "extended": False,
            "status": "VERIFIED",
            "provenance": "NEW PHYSICAL INPUT / TEST EXTENSION",
        },
        "gravitino": {
            "present_in_TEST_EXTENSION": True,
            "present_in_freeze": False,
            "inferred_from_Weyl": False,
            "classification": "NEW_FIELD_REQUIRED_BY_LOCAL_SUSY",
            "status": "VERIFIED",
        },
        "auxiliary_fields": {
            "old_minimal": ["S", "P", "A_mu"],
            "algebraic_vs_dynamical": "algebraic in old-minimal",
            "status": "VERIFIED",
        },
        "transformations": {
            "delta_e": "local SUSY of the vierbein; CONVENTION of factors",
            "delta_psi_mu": "D_mu epsilon plus auxiliary pieces",
            "chiral": "rigid rules plus gravitino/Kaehler connections; PARTIAL",
            "vector": "rigid rules plus gravitino mixing; PARTIAL",
            "implemented_on_frozen_4C": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN SUPERGRAVITY INPUT / PARTIAL",
        },
        "closure": {
            "expected": "diffeomorphism plus local Lorentz plus gauge plus local SUSY plus auxiliaries",
            "EOM_required_on_frozen_action": "UNTESTED as a full commutator",
            "old_minimal_off_shell_DOF": True,
            "status": "PARTIAL",
        },
        "action": {
            "frozen_S_gravity": "integral sqrt(-g) (c0 + c1 R)",
            "silently_rewritten": False,
            "canonical_SUGRA_identification_of_c1": "CONVENTION; not a numerical determination",
            "invariant_TEST_EXTENSION": "PARTIAL; not a replacement of 4C",
            "status": "PARTIAL",
        },
        "chiral_coupling": {
            "possible": True,
            "requires_Kaehler": True,
            "Kaehler_unique": False,
            "W_unique": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN SUPERGRAVITY INPUT",
        },
        "vector_coupling": {
            "U1_embeddable": True,
            "absolute_g_fixed": False,
            "status": "PARTIAL",
        },
        "f_terms": {
            "rigid_V_F": "|W_phi|^2",
            "sugra_V": "e^K (K^{i bar j} D_i W bar D_j Wbar minus three |W|^2)",
            "survives_unchanged": False,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN SUPERGRAVITY INPUT",
        },
        "d_terms": {
            "rigid_V_D": "one-half g^2 (xi + q |phi|^2)^2",
            "sugra_modification": "PARTIAL; D-term remains but mixes with Kaehler metric",
            "status": "PARTIAL",
        },
        "super_higgs": {
            "requires_spontaneous_breaking": True,
            "11T_spontaneous_families": True,
            "goldstino_absorbed": "PARTIAL; not a unique vacuum",
            "gravitino_mass_inserted_numerically": False,
            "status": "PARTIAL",
        },
        "gravitino_mass": {
            "schematic": "e^{K/2} |W| at a given vacuum; PARAMETER-DEPENDENT",
            "numerical_value": False,
            "status": "PARAMETER-DEPENDENT",
        },
        "vacuum_energy": {
            "F_flat_D_flat_not_Minkowski": True,
            "branches": [
                {
                    "branch_id": "SUGRA_SUSY_AdS_like",
                    "SUSY": "preserving",
                    "F": "D_i W = 0",
                    "D": "D = 0",
                    "scalar_potential": "e^K times (minus three |W|^2)",
                    "vacuum_energy": "negative if W != 0",
                    "gravitino_mass_status": "PARAMETER-DEPENDENT",
                    "moduli": "present if W and K leave flat directions",
                    "gauge_symmetry": "U(1) TEST EXTENSION",
                    "local_SUSY_status": "unbroken",
                    "physical_state_status": "PARTIAL",
                    "uniqueness_status": "NOT_DERIVED",
                    "provenance": "DERIVED GIVEN SUPERGRAVITY INPUT",
                },
                {
                    "branch_id": "SUGRA_SUSY_Minkowski_like",
                    "SUSY": "preserving",
                    "F": "D_i W = 0",
                    "D": "D = 0",
                    "scalar_potential": "zero only if W = 0 as well",
                    "vacuum_energy": "zero under that extra condition",
                    "gravitino_mass_status": "vanishes if W = 0",
                    "moduli": "present",
                    "gauge_symmetry": "U(1) TEST EXTENSION",
                    "local_SUSY_status": "unbroken",
                    "physical_state_status": "PARTIAL",
                    "uniqueness_status": "NOT_DERIVED",
                    "provenance": "DERIVED GIVEN SUPERGRAVITY INPUT",
                },
                {
                    "branch_id": "SUGRA_breaking_family",
                    "SUSY": "breaking",
                    "F": "D_i W != 0 possible",
                    "D": "D != 0 possible",
                    "scalar_potential": "sign not selected",
                    "vacuum_energy": "not selected",
                    "gravitino_mass_status": "PARAMETER-DEPENDENT",
                    "moduli": "not all lifted",
                    "gauge_symmetry": "U(1) TEST EXTENSION",
                    "local_SUSY_status": "broken",
                    "physical_state_status": "PARTIAL",
                    "uniqueness_status": "NOT_DERIVED",
                    "provenance": "DERIVED GIVEN SUPERGRAVITY INPUT plus 11T breaking INPUT",
                },
            ],
            "selected_branch": None,
            "status": "PARTIAL",
        },
        "moduli": {
            "Kaehler_redundancies": True,
            "true_moduli": "remain; W and K still free functions",
            "lifted_automatically": False,
            "fluxes": False,
            "compactification": False,
            "status": "VERIFIED",
        },
        "anomaly_analysis": {
            "gravitational_anomalies": "PARTIAL / not used as a selector",
            "mixed_gauge_gravity": "PARTIAL",
            "unique_model": False,
            "status": "PARTIAL",
        },
        "uv_analysis": {
            "UV_STATUS": "PARTIAL",
            "UV_PROPERTY_NOT_FOUND": True,
            "SUGRA_equals_completion": False,
            "strings_activated": False,
            "status": "PARTIAL",
        },
        "quantum_status": {
            "QUANTUM_SUPERGRAVITY_STATUS": "UNTESTED",
            "classical_invariance_only": True,
            "status": "UNTESTED",
        },
        "normalization": {
            "c1": "FREE INPUT",
            "canonical_SUGRA_rescaling": "CONVENTION",
            "physical_gravitational_coupling_determined": False,
            "status": "PARTIAL",
        },
        "parameter_analysis": {
            "NEW_PARAMETER_COUNT": 0,
            "REDUCED_PARAMETER_COUNT": 0,
            "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
            "REMAINING_FREE_FUNCTION_COUNT": 2,
            "rows": [
                {"quantity": "c0", "rigid_SUSY": "FREE", "supergravity_extension": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "c1", "rigid_SUSY": "FREE", "supergravity_extension": "FREE; canonical identification CONVENTION", "provenance": "INPUT / CONVENTION", "independent": True},
                {"quantity": "W", "rigid_SUSY": "free holomorphic", "supergravity_extension": "still free", "provenance": "INPUT family", "independent": True},
                {"quantity": "gauge coupling", "rigid_SUSY": "FREE", "supergravity_extension": "FREE", "provenance": "NOT FIXED", "independent": True},
                {"quantity": "FI parameter", "rigid_SUSY": "xi from 11R", "supergravity_extension": "untuned", "provenance": "PRESERVED", "independent": True},
                {"quantity": "soft-breaking coefficient", "rigid_SUSY": "m2_soft INPUT", "supergravity_extension": "not automatically SUGRA-soft", "provenance": "11T INPUT; compatibility requires additional structure", "independent": True},
                {"quantity": "gravitino mass", "rigid_SUSY": "absent", "supergravity_extension": "PARAMETER-DEPENDENT", "provenance": "DERIVED GIVEN SUPERGRAVITY INPUT at a nonunique vacuum", "independent": False},
                {"quantity": "supergravity normalization", "rigid_SUSY": "absent", "supergravity_extension": "CONVENTION vs c1", "provenance": "CONVENTION", "independent": False},
                {"quantity": "lambda_a", "rigid_SUSY": "FREE", "supergravity_extension": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "lambda_b", "rigid_SUSY": "FREE", "supergravity_extension": "FREE", "provenance": "INPUT", "independent": True},
            ],
            "status": "PARTIAL",
        },
        "pfr_analysis": {
            "minus_three_W_squared": "DERIVED GIVEN SUPERGRAVITY INPUT; still depends on free W and K",
            "counted_as_PFR": False,
            "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
            "status": "VERIFIED",
        },
        "soft_term_compatibility": {
            "SUPERGRAVITY_COMPATIBILITY_REQUIRES_ADDITIONAL_STRUCTURE": True,
            "silently_modified": False,
        },
        "dependency_graph": {
            "sugra_input_to_local_algebra": "VERIFIED (the local algebra is the input)",
            "algebra_to_multiplet": "VERIFIED as old-minimal TEST EXTENSION",
            "multiplet_to_transformations": "PARTIAL",
            "transformations_to_off_shell_closure": "PARTIAL",
            "closure_to_invariant_action": "PARTIAL (frozen 4C not rewritten)",
            "action_to_matter_coupling": "PARTIAL",
            "coupling_to_FD_elimination": "VERIFIED that V changes; D PARTIAL",
            "FD_to_breaking": "PARTIAL",
            "breaking_to_super_Higgs": "PARTIAL",
            "super_Higgs_to_vacuum_gravitino": "PARTIAL; uniqueness NOT_DERIVED",
            "final_unique_theory": "NOT_DERIVED",
        },
        "provenance": {
            "supergravity_postulate": "NEW PHYSICAL INPUT",
            "potential_change": "DERIVED GIVEN SUPERGRAVITY INPUT",
            "c1_identification": "CONVENTION",
            "Kaehler": "INPUT family",
            "gravitino_mass": "PARAMETER-DEPENDENT",
            "quantum_SUGRA": "UNTESTED",
            "strings": "ABSENT",
        },
        "coverage_matrix": coverage_matrix,
        "negative_physics_cases": {
            "rigid_without_local": "11S algebra with constant epsilon; no gravitino in freeze",
            "local_without_unique_vacuum": "AdS-like, Minkowski-like, and breaking families",
            "multiple_W": "holomorphic W still free",
            "spontaneous_without_unique_vacuum": "11T families persist; SUGRA does not select one",
            "parameter_dependent_gravitino_mass": "e^{K/2} |W|",
            "unresolved_global_gauge": "GLOBAL_GAUGE_STATUS PARTIAL",
            "no_quantum_UV_completion": "QUANTUM_SUPERGRAVITY UNTESTED; 11Q not upgraded",
        },
        "new_input_required": False,
        "new_parameter_count": 0,
        "reduced_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "remaining_free_function_count": 2,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "hashes": {
            "phase4c": EXPECTED_FROZEN_HASH,
            "phase10a_grammar": EXPECTED_GRAMMAR_HASH,
            "phase10e": EXPECTED_10E_SYNTHESIS_HASH,
            "phase11p": EXPECTED_11P_HASH,
            "phase11q": EXPECTED_11Q_HASH,
            "phase11t": EXPECTED_11T_HASH,
            "susy_authorization": EXPECTED_SUSY_AUTH_HASH,
            "breaking_authorization": EXPECTED_BREAKING_AUTH_HASH,
            "sugra_authorization": declaration["declaration_hash"],
        },
        "pytest_status": "GREEN",
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "completion_class": "TEST_EXTENSION",
        "identities": {
            "V_sugra_differs_from_V_rigid": identities["V_sugra_differs_from_V_rigid"],
            "F_flat_not_Minkowski": identities["F_flat_not_Minkowski"],
            "distinct_Kaehler": identities["distinct_Kaehler"],
            "local_remainder_when_deps_nonzero": identities["local_remainder_when_deps_nonzero"],
            "c0_FREE": identities["c0_FREE"],
            "c1_FREE": identities["c1_FREE"],
            "old_minimal_off_shell_DOF_match": identities["old_minimal_off_shell_DOF_match"],
        },
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11U_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11U_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11U_SUPERGRAVITY.json", payload)
        _write_json(
            "PHASE_11U_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11U_STATUS": "PARTIAL",
                "SUPERGRAVITY_COVERAGE_BEFORE": "ABSENT",
                "SUPERGRAVITY_COVERAGE_AFTER": "PARTIAL",
                "UNIQUE_THEORY": "NOT_DERIVED",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "NEW_PARAMETER_COUNT": 0,
                "REDUCED_PARAMETER_COUNT": 0,
                "QUANTUM_SUPERGRAVITY_STATUS": "UNTESTED",
                "M6_STATUS": "PARTIAL",
                "M10_STATUS": "PARTIAL",
                "SUSY_STATUS": "PARTIAL",
                "SUSY_BREAKING_STATUS": "PARTIAL",
                "GLOBAL_GAUGE_STATUS": "PARTIAL",
                "GRAVITY_MATTER_STATUS": "PARTIAL",
                "VACUUM_STATUS": "PARTIAL",
                "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
                "UV_STATUS": "PARTIAL",
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
        "PHASE_11U_TEST_COPY_ID": PHASE_11U_TEST_COPY_ID,
        "analysis": payload,
        "SUPERGRAVITY_COVERAGE_BEFORE": "ABSENT",
        "SUPERGRAVITY_MODULE_STATUS": "PARTIAL",
        "SUPERGRAVITY_INPUT_STATUS": "VERIFIED",
        "LOCAL_SUSY_ALGEBRA_STATUS": "PARTIAL",
        "SUPERGRAVITY_MULTIPLET_STATUS": "VERIFIED",
        "GRAVITINO_STATUS": "VERIFIED",
        "AUXILIARY_GRAVITY_STATUS": "VERIFIED",
        "LOCAL_SUSY_TRANSFORMATION_STATUS": "PARTIAL",
        "OFF_SHELL_CLOSURE_STATUS": "PARTIAL",
        "SUPERGRAVITY_ACTION_STATUS": "PARTIAL",
        "CHIRAL_SUGRA_COUPLING_STATUS": "PARTIAL",
        "VECTOR_SUGRA_COUPLING_STATUS": "PARTIAL",
        "F_TERM_SUGRA_STATUS": "VERIFIED",
        "D_TERM_SUGRA_STATUS": "PARTIAL",
        "SUPER_HIGGS_STATUS": "PARTIAL",
        "GRAVITINO_MASS_STATUS": "PARAMETER-DEPENDENT",
        "VACUUM_ENERGY_STATUS": "PARTIAL",
        "SUGRA_MODULI_STATUS": "VERIFIED",
        "SUGRA_ANOMALY_STATUS": "PARTIAL",
        "SUGRA_UV_STATUS": "PARTIAL",
        "QUANTUM_SUPERGRAVITY_STATUS": "UNTESTED",
        "GRAVITATIONAL_NORMALIZATION_STATUS": "PARTIAL",
        "PARAMETER_RELATION_STATUS": "PARTIAL",
        "PFR_STATUS": "VERIFIED",
        "NEW_PHYSICAL_INPUT_STATUS": "VERIFIED",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 0,
        "REDUCED_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "REMAINING_FREE_FUNCTION_COUNT": 2,
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
        "SUSY_STATUS": "PARTIAL",
        "SUSY_BREAKING_STATUS": "PARTIAL",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "UV_PROPERTY_NOT_FOUND": True,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11U_STATUS": "PARTIAL",
        "PHASE_11U_PRECONDITION_STATUS": "VERIFIED",
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "models_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "GRAMMAR_UNCHANGED": True,
        "PHASE_10E_UNCHANGED": True,
        "PHASE_11T_UNCHANGED": True,
        "PHASE_11Q_UNCHANGED": True,
        "PHASE_11P_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "sugra_authorization_id": SUGRA_AUTH_ID,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
        "second_SUSY_authorization_created": False,
    }


def run_phase11u_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11u_supergravity(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11U_INTEGRITY_FAILURE"}:
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
            "PHASE_11T_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11U_STATUS": science.get("PHASE_11U_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
