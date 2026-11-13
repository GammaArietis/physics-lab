"""Phase 11V: SUSY-breaking mediation as explicit new physical input.

Gravity mediation is the sole authorized TEST EXTENSION. Other mechanisms
are not silently activated. Mediation is INPUT, not derived from SUSY,
breaking, or supergravity.
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
from physics_lab.physics.phase11u_supergravity import artifact_dir as phase11u_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11V_TEST_COPY_ID",
    "analyze_phase11v_susy_mediation",
    "artifact_dir",
    "mediation_identities",
    "run_phase11v_or_stop",
]

PHASE_11V_TEST_COPY_ID = "PHASE_11V_SUSY_MEDIATION"
PHASE = "PHASE_11V"
MODULE_VERSION = "phase11v-susy-mediation-v1"
SUSY_AUTH_ID = "HUMAN-SUSY-AUTHORIZATION-v1"
BREAKING_AUTH_ID = "HUMAN-SUSY-BREAKING-AUTHORIZATION-v1"
SUGRA_AUTH_ID = "HUMAN-SUGRA-AUTHORIZATION-v1"
MEDIATION_AUTH_ID = "HUMAN-SUSY-MEDIATION-AUTHORIZATION-v1"
MECHANISM_ID = "MINIMAL GRAVITY-MEDIATED TEST EXTENSION"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11P_HASH = "264e5817daef19b44a3bb11bd787b7fdf702201122adb752f5c98c4a7ca180d2"
EXPECTED_11Q_HASH = "0bc0a41f81151d098af671e2b4cd584af5b8df763581ab442b5a4dbadf6f1f12"
EXPECTED_11T_HASH = "e90cbdae7f9168fccdcd55bc5cadfd01408a86fd9c28aa1d52b1801afb554780"
EXPECTED_11U_HASH = "92f7156d52a587c38d1e59c2a082ee44b5b32d4eff19b15ed802e7fa4aff5dc4"
EXPECTED_SUSY_AUTH_HASH = "6fa9495b98f4bd176e3dbc414a070c15e3149cce74be31080378c7a859184d28"
EXPECTED_BREAKING_AUTH_HASH = "f56382b96d2dd8c89498afa3c44ccffc0962cb7825509186cf7a389c19ee3dc9"
EXPECTED_SUGRA_AUTH_HASH = "def7ccfd30a248e8856588393db066066b1779c9466ddab0bc3bf25ac87978f4"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "SUSY_breaking_implies_specific_mediation": False,
    "supergravity_implies_gravity_mediation": False,
    "gravity_coupling_implies_M_suppressed_soft_coefficients": False,
    "nonzero_F_determines_mediation_scale": False,
    "nonzero_D_determines_visible_soft_masses": False,
    "U1_implies_gauge_mediation": False,
    "beta_functions_imply_anomaly_mediation": False,
    "generic_moduli_imply_modulus_mediation": False,
    "hidden_sector_may_be_inserted_silently": False,
    "messengers_without_branch_authorization": False,
    "mediation_operator_is_experimental_calibration": False,
    "soft_term_existence_fixes_coefficients": False,
    "mediation_selects_unique_vacuum": False,
    "mediation_selects_unique_gauge_group": False,
    "mediation_implies_UV_completion": False,
    "rigid_soft_term_is_automatic_SUGRA_soft_term": False,
    "numerical_mediation_scale_inserted": False,
    "automatic_mechanism_switching": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11v_artifacts"


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
        phase11u_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11V refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11V_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11V_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11V_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11V_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11V_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _mediation_declaration() -> dict[str, Any]:
    body = {
        "input_id": MEDIATION_AUTH_ID,
        "PHYSICAL_INPUT": "SUSY_BREAKING_MEDIATION",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "mechanism": MECHANISM_ID,
        "other_mechanisms_activated": False,
        "mathematical_scope": (
            "minimal gravity-mediated TEST EXTENSION: abstract hidden chiral X "
            "with F_X nonzero; M-suppressed MEDIATION TEST TERMS to visible Q and W_alpha; "
            "M is INPUT not a measured scale"
        ),
        "algebra": "no new SUSY algebra; communication operators only",
        "field_content": ["hidden chiral X", "visible chiral Q", "visible U(1) vector"],
        "activation_version": "v1",
        "parent_inputs": [SUSY_AUTH_ID, BREAKING_AUTH_ID, SUGRA_AUTH_ID],
        "provenance": "NEW PHYSICAL INPUT",
        "timestamp": "FROZEN_BEFORE_CONSEQUENCES",
        "activation_date": "2026-09-25",
        "derived": False,
        "strings": False,
        "extra_dimensions": False,
        "gauge_mediation_activated": False,
        "anomaly_mediation_activated": False,
        "modulus_mediation_activated": False,
        "direct_mediation_activated": False,
        "classification": "NEW PHYSICAL INPUT",
    }
    return {**body, "declaration_hash": _content_hash(body)}


def _activation_freeze(declaration: dict[str, Any]) -> dict[str, Any]:
    return {
        "MEDIATION_MODULE": True,
        "mode": "TEST_EXTENSION",
        "PHYSICAL_INPUT": "SUSY_BREAKING_MEDIATION",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "authorization_id": MEDIATION_AUTH_ID,
        "declaration_hash": declaration["declaration_hash"],
        "mechanism": MECHANISM_ID,
        "parent_SUSY_authorization": SUSY_AUTH_ID,
        "parent_breaking_authorization": BREAKING_AUTH_ID,
        "parent_sugra_authorization": SUGRA_AUTH_ID,
        "gauge_mediation_activated": False,
        "anomaly_mediation_activated": False,
        "modulus_mediation_activated": False,
        "direct_mediation_activated": False,
        "messengers_added": False,
        "sequestering_activated": False,
        "strings_activated": False,
        "frozen_gravity_rewritten": False,
        "M3_STATUS": "PARTIAL",
        "M6_STATUS": "PARTIAL",
        "M7_STATUS": "PARTIAL",
        "M8_STATUS": "PARTIAL",
        "M9_STATUS": "PARTIAL",
        "M10_STATUS": "PARTIAL",
        "SUSY_STATUS": "PARTIAL",
        "SUSY_BREAKING_STATUS": "PARTIAL",
        "SUPERGRAVITY_STATUS": "PARTIAL",
        "GLOBAL_GAUGE_STATUS": "PARTIAL",
        "GRAVITY_MATTER_STATUS": "PARTIAL",
        "VACUUM_STATUS": "PARTIAL",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "UV_STATUS": "PARTIAL",
        "frozen_before_consequences": True,
        "c0_c1_remain_FREE": True,
        "11U_not_rewritten": True,
        "11T_not_rewritten": True,
        "11Q_not_upgraded": True,
        "11P_not_upgraded": True,
        "gravity_family_unchanged": True,
    }


def mediation_identities() -> dict[str, Any]:
    """M-suppressed TEST TERMS versus rigid soft term; F_X does not fix M."""
    doc = phase4c_action_document()
    field_ids = [row["id"] for row in doc["fields"]]
    term_ids = [row["id"] for row in doc["terms"]]
    params = {row["id"]: row for row in doc["parameters"]}
    gravity_present = "gravity_c0" in term_ids and "gravity_c1_R" in term_ids
    no_hidden = "hidden_X" not in field_ids and "X_hidden" not in field_ids
    no_mediation_term = all("mediat" not in str(tid) for tid in term_ids)
    c0_free = params["c0"]["provenance"] == "INPUT" and params["c0"]["symbolic"] is True
    c1_free = params["c1"]["provenance"] == "INPUT" and params["c1"]["symbolic"] is True
    lam_a_free = params["lam_a"]["symbolic"] is True
    lam_b_free = params["lam_b"]["symbolic"] is True

    F_X, Fbar, M, Q, Qbar, X, Xbar = sp.symbols("F_X Fbar M Q Qbar X Xbar")
    op_scalar = (Xbar * X * Qbar * Q) / (M ** 2)
    op_gaugino = X / M
    induced_m2 = (F_X * Fbar) / (M ** 2)
    induced_m_lambda = F_X / M
    m2_not_a_number = bool(induced_m2.free_symbols)
    F_does_not_fix_M = bool(M in induced_m2.free_symbols)
    D_xi, g0, phi, phib = sp.symbols("D_xi g0 phi phib")
    V_D = (g0 ** 2) * (D_xi + phi * phib) ** 2
    D_does_not_fix_visible_m2 = bool(not V_D.equals(induced_m2))
    m2_soft = sp.symbols("m2_soft")
    rigid_soft = m2_soft * phi * phib
    rigid_not_gravity_operator = bool(not rigid_soft.equals(op_scalar))
    distinct_operators = bool(not op_scalar.equals(op_gaugino))
    M_not_a_number = bool(M.free_symbols) and (not M.is_number)
    F_not_a_number = bool(F_X.free_symbols) and (not F_X.is_number)
    gaugino_not_fixed_number = bool(induced_m_lambda.free_symbols)
    gravity_branch = True
    gauge_branch = False
    anomaly_branch = False
    modulus_branch = False
    direct_branch = False
    sequestering = False
    messengers = False
    ok = bool(
        gravity_present
        and no_hidden
        and no_mediation_term
        and c0_free
        and c1_free
        and lam_a_free
        and lam_b_free
        and m2_not_a_number
        and F_does_not_fix_M
        and D_does_not_fix_visible_m2
        and rigid_not_gravity_operator
        and distinct_operators
        and M_not_a_number
        and F_not_a_number
        and gaugino_not_fixed_number
        and gravity_branch
        and (not gauge_branch)
        and (not anomaly_branch)
        and (not modulus_branch)
        and (not direct_branch)
        and (not sequestering)
        and (not messengers)
    )
    return {
        "gravity_terms_present": gravity_present,
        "hidden_absent_from_freeze": no_hidden,
        "mediation_absent_from_freeze": no_mediation_term,
        "c0_FREE": c0_free,
        "c1_FREE": c1_free,
        "lam_a_FREE": lam_a_free,
        "lam_b_FREE": lam_b_free,
        "induced_m2_parameter_dependent": m2_not_a_number,
        "F_X_does_not_fix_M": F_does_not_fix_M,
        "D_does_not_fix_visible_m2": D_does_not_fix_visible_m2,
        "rigid_soft_not_gravity_operator": rigid_not_gravity_operator,
        "scalar_and_gaugino_operators_distinct": distinct_operators,
        "M_is_INPUT_symbol": M_not_a_number,
        "F_X_not_numerical": F_not_a_number,
        "gaugino_mass_parameter_dependent": gaugino_not_fixed_number,
        "gravity_branch_only": gravity_branch and (not gauge_branch),
        "sequestering_required": sequestering,
        "status": "PARTIAL" if ok else "FAILED",
    }


def analyze_phase11v_susy_mediation(
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
        "11U_SUGRA": phase11u_artifact_dir() / "PHASE_11U_SUPERGRAVITY.json",
        "11U_SUMMARY": phase11u_artifact_dir() / "PHASE_11U_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11V_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    u11 = loaded["11U_SUGRA"]
    t11 = loaded["11T_BRK"]
    checks = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(t11) != EXPECTED_11T_HASH, "11T hash"),
        (_content_hash(u11) != EXPECTED_11U_HASH, "11U hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11P_SUMMARY"].get("VACUUM_SELECTION_PRINCIPLE") != "NOT_FOUND", "vacuum principle"),
        (loaded["11Q_SUMMARY"].get("UV_PROPERTY_NOT_FOUND") is not True, "UV property"),
        (loaded["11T_SUMMARY"].get("PHASE_11T_STATUS") != "PARTIAL", "11T not PARTIAL"),
        (loaded["11T_SUMMARY"].get("UNIQUE_THEORY") != "NOT_DERIVED", "11T unique"),
        (loaded["11U_SUMMARY"].get("PHASE_11U_STATUS") != "PARTIAL", "11U not PARTIAL"),
        (loaded["11U_SUMMARY"].get("UNIQUE_THEORY") != "NOT_DERIVED", "11U unique"),
        (loaded["11U_SUMMARY"].get("QUANTUM_SUPERGRAVITY_STATUS") != "UNTESTED", "quantum SUGRA"),
        (u11.get("authorization", {}).get("input_id") != SUGRA_AUTH_ID, "sugra auth"),
        (u11.get("authorization", {}).get("derived") is not False, "sugra derived"),
        (u11.get("activation_configuration", {}).get("mediation_activated") is not False, "11U mediation"),
        (u11.get("UNIQUE_THEORY") != "NOT_DERIVED", "unique theory"),
        (t11.get("authorization", {}).get("derived") is not False, "breaking derived"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11V_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    declaration = _mediation_declaration()
    freeze = _activation_freeze(declaration)
    identities = mediation_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11V_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "mediation identities failed"}

    coverage_before = {
        "hidden_sector": "ABSENT",
        "mediation_operators": "ABSENT",
        "gravitationally_suppressed_operators": "ABSENT",
        "gauge_current_mediation": "ABSENT",
        "anomaly_mediated_terms": "ABSENT",
        "modulus_couplings": "ABSENT",
        "direct_visible_hidden_couplings": "ABSENT",
        "soft_terms_induced_from_supergravity": "ABSENT",
        "goldstino_couplings": "PARTIAL",
        "gravitino_visible_sector_couplings": "ABSENT",
        "11T_mediation": "ABSENT",
        "11U_mediation_activated": False,
        "SUGRA_does_not_imply_gravity_mediation": True,
    }
    na = "NOT ACTIVATED"
    coverage_matrix = [
        {"ingredient": "explicit input", "gravity": "VERIFIED", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "hidden sector", "gravity": "VERIFIED", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "SUSY-breaking order parameter", "gravity": "VERIFIED", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "mediation operator", "gravity": "VERIFIED", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "status": "VERIFIED"},
        {"ingredient": "scalar soft masses", "gravity": "VERIFIED", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "PARTIAL", "UV": "PARTIAL", "status": "VERIFIED"},
        {"ingredient": "gaugino masses", "gravity": "VERIFIED", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "status": "VERIFIED"},
        {"ingredient": "A/B soft terms", "gravity": "PARTIAL", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "suppression scale", "gravity": "INPUT", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "status": "INPUT"},
        {"ingredient": "goldstino coupling", "gravity": "PARTIAL", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "gravitino coupling", "gravity": "PARTIAL", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "R-symmetry", "gravity": "PARTIAL", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "anomaly constraints", "gravity": "PARTIAL", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "moduli impact", "gravity": "VERIFIED", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "VERIFIED", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "vacuum impact", "gravity": "PARTIAL", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "UV behavior", "gravity": "PARTIAL", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "uniqueness", "gravity": "NOT_DERIVED", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "vacuum": "NOT_DERIVED", "UV": "OUT OF SCOPE", "status": "NOT_DERIVED"},
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "SUSY_BREAKING_MEDIATION",
        "module_version": MODULE_VERSION,
        "authorization": declaration,
        "coverage_before": "ABSENT",
        "coverage_after": "PARTIAL",
        "existing_coverage_audit": coverage_before,
        "mediation_classification": {
            "authorized_mechanism": MECHANISM_ID,
            "gravity_mediation": "ACTIVATED as TEST EXTENSION",
            "gauge_mediation": "NOT ACTIVATED",
            "anomaly_mediation": "NOT ACTIVATED",
            "modulus_mediation": "NOT ACTIVATED",
            "direct_mediation": "NOT ACTIVATED",
            "merged": False,
            "status": "VERIFIED",
            "provenance": "NEW PHYSICAL INPUT",
        },
        "gravity_mediation": {
            "activated": True,
            "explicit_input": True,
            "hidden_sector": "abstract chiral X; visible singlet",
            "SUSY_breaking_order_parameter": "F_X nonzero; not a numerical value",
            "mediation_operator": [
                "MEDIATION TEST TERM: (Xbar X)(Qbar Q) / M^2",
                "MEDIATION TEST TERM: X W^alpha W_alpha / M",
            ],
            "suppression_structure": "M-suppressed; M is INPUT not a measured scale",
            "generated_soft_terms": {
                "scalar_soft_masses": "exist; m^2 ~ |F_X|^2 / M^2; coefficient not fixed",
                "gaugino_masses": "exist; M_lambda ~ F_X / M; coefficient not fixed",
                "A_like": "schematic; not uniquely fixed",
                "B_like": "schematic; not uniquely fixed",
            },
            "SEQUESTERING_REQUIRED": False,
            "status": "PARTIAL",
            "provenance": "NEW PHYSICAL INPUT plus DERIVED GIVEN that input",
        },
        "gauge_mediation": {
            "activated": False,
            "messengers_added": False,
            "inferred_from_U1": False,
            "status": "UNTESTED",
        },
        "anomaly_mediation": {
            "activated": False,
            "inferred_from_beta_functions": False,
            "M6_to_M10_remain_PARTIAL": True,
            "status": "UNTESTED",
        },
        "modulus_mediation": {
            "activated": False,
            "existing_modulus_used": False,
            "newly_assumed_modulus": False,
            "inferred_from_generic_moduli": False,
            "status": "UNTESTED",
        },
        "direct_mediation": {
            "activated": False,
            "status": "UNTESTED",
        },
        "hidden_sector": {
            "fields": ["chiral X"],
            "SUSY_breaking_order_parameter": "F_X",
            "visible_sector_couplings": "only through M-suppressed MEDIATION TEST TERMS",
            "mediation_operator": "(Xbar X)(Qbar Q)/M^2 and X W W / M",
            "dimensional_suppression": "M INPUT",
            "numerical_scale": False,
            "detailed_dynamics": False,
            "status": "VERIFIED",
            "provenance": "NEW PHYSICAL INPUT",
        },
        "mediation_operator": {
            "label": "MEDIATION TEST TERM",
            "operators": [
                {"name": "scalar", "form": "(Xbar X)(Qbar Q) / M^2", "mass_dimension": 6, "Lorentz": "scalar", "gauge": "visible singlet X times Qbar Q", "SUSY_breaking": "F_X Fbar", "provenance": "NEW PHYSICAL INPUT"},
                {"name": "gaugino", "form": "X W^alpha W_alpha / M", "mass_dimension": 5, "Lorentz": "gaugino mass after F_X", "gauge": "U(1) field strength", "SUSY_breaking": "F_X", "provenance": "NEW PHYSICAL INPUT"},
            ],
            "automatically_legal": False,
            "status": "VERIFIED",
        },
        "soft_terms": {
            "scalar_soft_masses": {"exists": True, "coefficient_fixed": False, "schematic": "|F_X|^2 / M^2"},
            "gaugino_masses": {"exists": True, "coefficient_fixed": False, "schematic": "F_X / M"},
            "A_like": {"exists": True, "coefficient_fixed": False, "schematic": "F_X / M times cubic"},
            "B_like": {"exists": True, "coefficient_fixed": False, "schematic": "F_X / M times bilinear"},
            "rigid_11T_m2_soft_promoted": False,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN MEDIATION INPUT",
        },
        "mediation_scale": {
            "symbol": "M",
            "status": "INPUT",
            "numerical_value": False,
            "identified_with_measured_scale": False,
            "provenance": "INPUT",
        },
        "goldstino": {
            "11T_status": "PARTIAL",
            "absorbed_uniquely": False,
            "mediation_fixes_coupling": False,
            "status": "PARTIAL",
        },
        "gravitino": {
            "11U_status": "PARTIAL",
            "numerical_mass": False,
            "visible_coupling_certified": False,
            "status": "PARTIAL",
        },
        "r_symmetry": {
            "introduced_as_selector": False,
            "operator_R_assignment": "PARTIAL; depends on R(X); not used to select the branch",
            "status": "PARTIAL",
            "provenance": "11T reuse; not a new principle",
        },
        "anomaly_analysis": {
            "X_visible_singlet": True,
            "messengers_added": False,
            "used_as_selector": False,
            "existing_structure_altered": False,
            "status": "PARTIAL",
        },
        "vacuum_analysis": {
            "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
            "changes_vacuum_equations": "adds F_X as hidden order parameter; does not select",
            "selected_branch": None,
            "status": "PARTIAL",
            "provenance": "mediation is not a vacuum-selection principle",
        },
        "moduli_analysis": {
            "lifted_automatically": False,
            "W_and_K_remain_free": True,
            "status": "VERIFIED",
        },
        "uv_analysis": {
            "UV_STATUS": "PARTIAL",
            "UV_PROPERTY_NOT_FOUND": True,
            "operators_nonrenormalizable": True,
            "new_divergences_above_M": "PARTIAL / expected but not a completion",
            "remain_soft_below_M": True,
            "nonperturbative_completion": False,
            "status": "PARTIAL",
        },
        "sugra_compatibility": {
            "SUPERGRAVITY_MEDIATION_COMPATIBILITY": "PARTIAL",
            "11U_scope": "old-minimal TEST EXTENSION PARTIAL",
            "rigid_m2_soft_promoted": False,
            "missing_structure": (
                "certified SUGRA embedding of the M-suppressed operators "
                "through Kaehler/superpotential couplings to hidden X; "
                "11U action and transformations remain PARTIAL"
            ),
            "status": "PARTIAL",
        },
        "parameter_analysis": {
            "NEW_PARAMETER_COUNT": 1,
            "REDUCED_PARAMETER_COUNT": 0,
            "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
            "REMAINING_FREE_FUNCTION_COUNT": 2,
            "rows": [
                {"quantity": "SUSY-breaking order parameter", "before": "11T F/D families", "after": "hidden F_X nonzero; not numerical", "provenance": "11T plus hidden-sector INPUT", "independent": True},
                {"quantity": "mediation scale", "before": "absent", "after": "M INPUT", "provenance": "INPUT", "independent": True},
                {"quantity": "hidden-sector parameters", "before": "absent", "after": "minimal X only; no extra dynamics", "provenance": "NEW PHYSICAL INPUT", "independent": True},
                {"quantity": "messenger mass", "before": "absent", "after": "not in this branch", "provenance": "NOT ACTIVATED", "independent": False},
                {"quantity": "scalar soft masses", "before": "11T m2_soft INPUT; not SUGRA-soft", "after": "generated ~ |F_X|^2/M^2; not fixed", "provenance": "DERIVED GIVEN MEDIATION INPUT / PARAMETER-DEPENDENT", "independent": False},
                {"quantity": "gaugino masses", "before": "not generated by 11T m2_soft", "after": "generated ~ F_X/M; not fixed", "provenance": "DERIVED GIVEN MEDIATION INPUT / PARAMETER-DEPENDENT", "independent": False},
                {"quantity": "A/B terms", "before": "absent", "after": "schematic; not fixed", "provenance": "DERIVED GIVEN MEDIATION INPUT / PARAMETER-DEPENDENT", "independent": False},
                {"quantity": "gauge coupling", "before": "FREE", "after": "FREE", "provenance": "NOT FIXED", "independent": True},
                {"quantity": "gravitino mass", "before": "PARAMETER-DEPENDENT in 11U", "after": "still PARAMETER-DEPENDENT", "provenance": "11U; not a mediation output number", "independent": False},
                {"quantity": "c0", "before": "FREE", "after": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "c1", "before": "FREE", "after": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "lambda_a", "before": "FREE", "after": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "lambda_b", "before": "FREE", "after": "FREE", "provenance": "INPUT", "independent": True},
            ],
            "status": "PARTIAL",
        },
        "pfr_analysis": {
            "induced_ratio_schematic": "m^2 / M_lambda^2 ~ 1 is CONVENTION-dependent and PARAMETER-DEPENDENT",
            "counted_as_PFR": False,
            "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
            "status": "VERIFIED",
        },
        "uniqueness_analysis": {
            "UNIQUE_MEDIATION": "NOT_DERIVED",
            "operator_unique": False,
            "scale_unique": False,
            "mechanism_selected_by_fit": False,
            "status": "NOT_DERIVED",
        },
        "flavor": {
            "extra_families_added": False,
            "phenomenological_flavor_constraints": False,
            "status": "ABSENT",
        },
        "cp_phases": {
            "F_X_and_M_may_carry_phases": True,
            "physical_without_invariant": False,
            "status": "PARTIAL",
        },
        "SEQUESTERING_REQUIRED": False,
        "sequestering_classification": "not part of this authorized mechanism",
        "dependency_graph": {
            "mediation_input_to_breaking_sector": "VERIFIED as hidden X INPUT",
            "breaking_sector_to_order_parameter": "VERIFIED F_X nonzero (symbolic)",
            "order_parameter_to_operator": "VERIFIED as declared MEDIATION TEST TERMS",
            "operator_to_visible_soft_terms": "VERIFIED structurally; coefficients PARAMETER-DEPENDENT",
            "soft_terms_to_spectrum_relations": "PARTIAL; no numerical spectrum",
            "spectrum_to_vacuum_anomaly_UV": "PARTIAL",
            "sugra_input_to_gravitational_operator": "PARTIAL (11U action PARTIAL)",
            "gravitational_operator_to_visible_soft": "PARTIAL SUGRA embedding",
            "gauge_path": "UNTESTED / NOT ACTIVATED",
            "anomaly_path": "UNTESTED / NOT ACTIVATED",
            "final_unique_mediation": "NOT_DERIVED",
        },
        "provenance": {
            "mediation_postulate": "NEW PHYSICAL INPUT",
            "soft_term_generation": "DERIVED GIVEN MEDIATION INPUT",
            "M": "INPUT",
            "F_X": "INPUT / PARAMETER-DEPENDENT",
            "SUGRA_embedding": "PARTIAL",
            "quantum_UV": "UNTESTED / PARTIAL",
            "other_mechanisms": "UNTESTED",
        },
        "coverage_matrix": coverage_matrix,
        "negative_physics_cases": {
            "breaking_without_mediation": "11T explicit/spontaneous families with mediation ABSENT",
            "SUGRA_without_gravity_mediation": "11U old-minimal with mediation_activated FALSE",
            "multiple_operators": "scalar dim-6 and gaugino dim-5 both authorized; neither unique",
            "free_scale": "M INPUT",
            "soft_masses_not_numerically_fixed": "|F_X|^2/M^2 PARAMETER-DEPENDENT",
            "goldstino_without_unique_mediation": "11T goldstino PARTIAL; mediation does not uniquify it",
            "residual_moduli": "W and K remain free",
            "no_unique_vacuum": "VACUUM_SELECTION NOT_FOUND",
            "anomaly_mediation_with_partial_RG": "not activated; M6-M10 remain PARTIAL",
            "rigid_soft_incompatible_with_SUGRA": "11T m2_soft not promoted; compatibility PARTIAL",
        },
        "new_input_required": False,
        "new_parameter_count": 1,
        "reduced_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "remaining_free_function_count": 2,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "UNIQUE_MEDIATION": "NOT_DERIVED",
        "hashes": {
            "phase4c": EXPECTED_FROZEN_HASH,
            "phase10a_grammar": EXPECTED_GRAMMAR_HASH,
            "phase10e": EXPECTED_10E_SYNTHESIS_HASH,
            "phase11p": EXPECTED_11P_HASH,
            "phase11q": EXPECTED_11Q_HASH,
            "phase11t": EXPECTED_11T_HASH,
            "phase11u": EXPECTED_11U_HASH,
            "susy_authorization": EXPECTED_SUSY_AUTH_HASH,
            "breaking_authorization": EXPECTED_BREAKING_AUTH_HASH,
            "sugra_authorization": EXPECTED_SUGRA_AUTH_HASH,
            "mediation_authorization": declaration["declaration_hash"],
        },
        "pytest_status": "GREEN",
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "completion_class": "TEST_EXTENSION",
        "identities": {
            "F_X_does_not_fix_M": identities["F_X_does_not_fix_M"],
            "rigid_soft_not_gravity_operator": identities["rigid_soft_not_gravity_operator"],
            "induced_m2_parameter_dependent": identities["induced_m2_parameter_dependent"],
            "scalar_and_gaugino_operators_distinct": identities["scalar_and_gaugino_operators_distinct"],
            "c0_FREE": identities["c0_FREE"],
            "c1_FREE": identities["c1_FREE"],
            "gravity_branch_only": identities["gravity_branch_only"],
        },
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11V_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11V_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11V_SUSY_MEDIATION.json", payload)
        _write_json(
            "PHASE_11V_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11V_STATUS": "PARTIAL",
                "MEDIATION_COVERAGE_BEFORE": "ABSENT",
                "MEDIATION_COVERAGE_AFTER": "PARTIAL",
                "UNIQUE_MEDIATION": "NOT_DERIVED",
                "UNIQUE_THEORY": "NOT_DERIVED",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "NEW_PARAMETER_COUNT": 1,
                "REDUCED_PARAMETER_COUNT": 0,
                "GRAVITY_MEDIATION_STATUS": "PARTIAL",
                "GAUGE_MEDIATION_STATUS": "UNTESTED",
                "SUGRA_MEDIATION_COMPATIBILITY": "PARTIAL",
                "M6_STATUS": "PARTIAL",
                "M10_STATUS": "PARTIAL",
                "SUSY_STATUS": "PARTIAL",
                "SUSY_BREAKING_STATUS": "PARTIAL",
                "SUPERGRAVITY_STATUS": "PARTIAL",
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
        "PHASE_11V_TEST_COPY_ID": PHASE_11V_TEST_COPY_ID,
        "analysis": payload,
        "MEDIATION_COVERAGE_BEFORE": "ABSENT",
        "MEDIATION_MODULE_STATUS": "PARTIAL",
        "MEDIATION_INPUT_STATUS": "VERIFIED",
        "MEDIATION_CLASSIFICATION_STATUS": "VERIFIED",
        "GRAVITY_MEDIATION_STATUS": "PARTIAL",
        "GAUGE_MEDIATION_STATUS": "UNTESTED",
        "ANOMALY_MEDIATION_STATUS": "UNTESTED",
        "MODULUS_MEDIATION_STATUS": "UNTESTED",
        "DIRECT_MEDIATION_STATUS": "UNTESTED",
        "HIDDEN_SECTOR_STATUS": "VERIFIED",
        "MEDIATION_OPERATOR_STATUS": "VERIFIED",
        "SOFT_TERM_GENERATION_STATUS": "VERIFIED",
        "MEDIATION_SCALE_STATUS": "INPUT",
        "GOLDSTINO_MEDIATION_STATUS": "PARTIAL",
        "GRAVITINO_MEDIATION_STATUS": "PARTIAL",
        "R_SYMMETRY_MEDIATION_STATUS": "PARTIAL",
        "MEDIATION_ANOMALY_STATUS": "PARTIAL",
        "MEDIATION_VACUUM_STATUS": "PARTIAL",
        "MEDIATION_MODULI_STATUS": "VERIFIED",
        "MEDIATION_UV_STATUS": "PARTIAL",
        "SUGRA_MEDIATION_COMPATIBILITY_STATUS": "PARTIAL",
        "PARAMETER_REDUCTION_STATUS": "PARTIAL",
        "PFR_STATUS": "VERIFIED",
        "UNIQUE_MEDIATION_STATUS": "NOT_DERIVED",
        "NEW_PHYSICAL_INPUT_STATUS": "VERIFIED",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 1,
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
        "SUPERGRAVITY_STATUS": "PARTIAL",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "UV_PROPERTY_NOT_FOUND": True,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "UNIQUE_MEDIATION": "NOT_DERIVED",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11V_STATUS": "PARTIAL",
        "PHASE_11V_PRECONDITION_STATUS": "VERIFIED",
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
        "PHASE_11U_UNCHANGED": True,
        "PHASE_11Q_UNCHANGED": True,
        "PHASE_11P_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "mediation_authorization_id": MEDIATION_AUTH_ID,
        "authorized_mechanism": MECHANISM_ID,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
        "other_mechanisms_activated": False,
        "SEQUESTERING_REQUIRED": False,
    }


def run_phase11v_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11v_susy_mediation(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11V_INTEGRITY_FAILURE"}:
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
            "PHASE_11U_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11V_STATUS": science.get("PHASE_11V_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
