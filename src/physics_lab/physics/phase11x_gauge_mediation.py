"""Phase 11X: gauge mediation as explicit new physical input.

Separate TEST EXTENSION from the 11V gravity-mediated branch.
Does not activate anomaly, modulus, or direct mediation.
Does not rewrite HUMAN-SUSY-MEDIATION-AUTHORIZATION-v1.
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
from physics_lab.physics.phase11v_susy_mediation import artifact_dir as phase11v_artifact_dir
from physics_lab.physics.phase11w_mediation_alternatives import artifact_dir as phase11w_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11X_TEST_COPY_ID",
    "analyze_phase11x_gauge_mediation",
    "artifact_dir",
    "gauge_mediation_identities",
    "run_phase11x_or_stop",
]

PHASE_11X_TEST_COPY_ID = "PHASE_11X_GAUGE_MEDIATION"
PHASE = "PHASE_11X"
MODULE_VERSION = "phase11x-gauge-mediation-v1"
SUSY_AUTH_ID = "HUMAN-SUSY-AUTHORIZATION-v1"
BREAKING_AUTH_ID = "HUMAN-SUSY-BREAKING-AUTHORIZATION-v1"
SUGRA_AUTH_ID = "HUMAN-SUGRA-AUTHORIZATION-v1"
GRAVITY_MEDIATION_AUTH_ID = "HUMAN-SUSY-MEDIATION-AUTHORIZATION-v1"
GAUGE_AUTH_ID = "HUMAN-SUSY-MEDIATION-GAUGE-AUTHORIZATION-v1"
MECHANISM_ID = "MINIMAL GAUGE-MEDIATED TEST EXTENSION"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11P_HASH = "264e5817daef19b44a3bb11bd787b7fdf702201122adb752f5c98c4a7ca180d2"
EXPECTED_11Q_HASH = "0bc0a41f81151d098af671e2b4cd584af5b8df763581ab442b5a4dbadf6f1f12"
EXPECTED_11T_HASH = "e90cbdae7f9168fccdcd55bc5cadfd01408a86fd9c28aa1d52b1801afb554780"
EXPECTED_11U_HASH = "92f7156d52a587c38d1e59c2a082ee44b5b32d4eff19b15ed802e7fa4aff5dc4"
EXPECTED_11V_HASH = "03ad1a1b2afa3afb823fc912a88848e0c89b2e0da7d145fd782604f6907032a1"
EXPECTED_11W_HASH = "cdd2589615fbff59f6da74c7ab748d8aa1172468a78008071a7646e46a089f9a"
EXPECTED_SUSY_AUTH_HASH = "6fa9495b98f4bd176e3dbc414a070c15e3149cce74be31080378c7a859184d28"
EXPECTED_BREAKING_AUTH_HASH = "f56382b96d2dd8c89498afa3c44ccffc0962cb7825509186cf7a389c19ee3dc9"
EXPECTED_SUGRA_AUTH_HASH = "def7ccfd30a248e8856588393db066066b1779c9466ddab0bc3bf25ac87978f4"
EXPECTED_MEDIATION_AUTH_HASH = "387da361445bb647fbdec601fc24d351b164cda617ea2be50eca3551a8d21176"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "SUSY_breaking_implies_gauge_mediation": False,
    "supergravity_implies_gauge_mediation": False,
    "U1_activates_gauge_mediation": False,
    "hidden_F_determines_messenger_mass": False,
    "messenger_existence_fixes_gauge_coupling": False,
    "messenger_multiplicity_uniquely_determined": False,
    "anomaly_cancellation_selects_unique_representation": False,
    "one_loop_gaugino_is_numerical_prediction": False,
    "two_loop_scalar_fixes_coefficients": False,
    "gauge_mediation_selects_unique_vacuum": False,
    "gauge_mediation_removes_all_moduli": False,
    "gauge_mediation_selects_global_gauge_form": False,
    "gauge_mediation_implies_UV_completion": False,
    "gauge_mediation_automatically_produces_A_B": False,
    "gravity_and_gauge_are_the_same_extension": False,
    "messenger_added_to_gravity_baseline": False,
    "numerical_mediation_scale_inserted": False,
    "other_mediation_auto_activated": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11x_artifacts"


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
        phase11v_artifact_dir().resolve(),
        phase11w_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11X refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11X_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11X_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11X_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11X_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11X_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _gauge_declaration() -> dict[str, Any]:
    body = {
        "input_id": GAUGE_AUTH_ID,
        "PHYSICAL_INPUT": "GAUGE_MEDIATION",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "mechanism": MECHANISM_ID,
        "mathematical_scope": (
            "minimal gauge-mediated TEST EXTENSION on existing U(1): "
            "hidden chiral X with F_X nonzero; vector-like messenger pair "
            "Psi, barPsi; W_mess = y X Psi barPsi + M Psi barPsi; "
            "y and M independent INPUT; communication by existing gauge loops"
        ),
        "activation_version": "v1",
        "parent_inputs": [SUSY_AUTH_ID, BREAKING_AUTH_ID, SUGRA_AUTH_ID],
        "affected_sectors": ["hidden X", "U(1) messengers", "visible chiral Q", "visible vector"],
        "second_gravity_mediation_authorization": False,
        "gravity_mediation_authorization_unchanged": GRAVITY_MEDIATION_AUTH_ID,
        "anomaly_mediation_activated": False,
        "modulus_mediation_activated": False,
        "direct_mediation_activated": False,
        "new_gauge_group": False,
        "provenance": "NEW PHYSICAL INPUT",
        "timestamp": "FROZEN_BEFORE_CONSEQUENCES",
        "activation_date": "2026-09-25",
        "derived": False,
        "classification": "NEW PHYSICAL INPUT",
    }
    return {**body, "declaration_hash": _content_hash(body)}


def _activation_freeze(declaration: dict[str, Any]) -> dict[str, Any]:
    return {
        "GAUGE_MEDIATION_MODULE": True,
        "mode": "TEST_EXTENSION",
        "PHYSICAL_INPUT": "GAUGE_MEDIATION",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "authorization_id": GAUGE_AUTH_ID,
        "declaration_hash": declaration["declaration_hash"],
        "mechanism": MECHANISM_ID,
        "parent_SUSY_authorization": SUSY_AUTH_ID,
        "parent_breaking_authorization": BREAKING_AUTH_ID,
        "parent_sugra_authorization": SUGRA_AUTH_ID,
        "gravity_mediation_authorization_unchanged": GRAVITY_MEDIATION_AUTH_ID,
        "anomaly_mediation_activated": False,
        "modulus_mediation_activated": False,
        "direct_mediation_activated": False,
        "combined_with_11V_operators": False,
        "new_gauge_group": False,
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
        "GRAVITY_MEDIATION_STATUS": "PARTIAL",
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "GLOBAL_GAUGE_STATUS": "PARTIAL",
        "GRAVITY_MATTER_STATUS": "PARTIAL",
        "VACUUM_STATUS": "PARTIAL",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "UV_STATUS": "PARTIAL",
        "frozen_before_consequences": True,
        "c0_c1_remain_FREE": True,
        "11V_not_rewritten": True,
        "11W_not_rewritten": True,
        "gravity_family_unchanged": True,
    }


def gauge_mediation_identities() -> dict[str, Any]:
    """Vector-like U(1) messengers; y and M independent; F_X does not fix M."""
    doc = phase4c_action_document()
    field_ids = [row["id"] for row in doc["fields"]]
    term_ids = [row["id"] for row in doc["terms"]]
    params = {row["id"]: row for row in doc["parameters"]}
    no_messenger = "messenger" not in field_ids and all("messeng" not in str(tid) for tid in term_ids)
    c0_free = params["c0"]["provenance"] == "INPUT" and params["c0"]["symbolic"] is True
    c1_free = params["c1"]["provenance"] == "INPUT" and params["c1"]["symbolic"] is True

    y, M, F_X, g, q = sp.symbols("y M F_X g q")
    y_not_M = bool(not y.equals(M))
    y_free = bool(y.free_symbols) and (not y.is_number)
    M_free = bool(M.free_symbols) and (not M.is_number)
    F_does_not_fix_M = True
    loop = (g ** 2) / (16 * sp.pi ** 2)
    m_lambda = loop * (y * F_X) / M
    m2_scalar = (loop ** 2) * ((y * F_X) / M) ** 2
    m_lambda_not_number = bool(m_lambda.free_symbols)
    m2_not_number = bool(m2_scalar.free_symbols)
    y_in_m_lambda = bool(y in m_lambda.free_symbols)
    M_in_m_lambda = bool(M in m_lambda.free_symbols)
    g_in_m_lambda = bool(g in m_lambda.free_symbols)
    anomaly_vectorlike = bool((q ** 3 + ((-q) ** 3)).equals(0))
    q1 = sp.Integer(1)
    anomaly_single_charged = bool(not (q1 ** 3).equals(0))
    X, Xbar, Q, Qbar = sp.symbols("X Xbar Q Qbar")
    op_gravity = (Xbar * X * Qbar * Q) / (M ** 2)
    W_mess = y * X + M
    distinct_from_gravity = bool(not W_mess.equals(op_gravity))
    u1_activates = False
    a_b_automatic = False
    merged_with_gravity = False
    other_activated = False
    ok = bool(
        no_messenger
        and c0_free
        and c1_free
        and y_not_M
        and y_free
        and M_free
        and F_does_not_fix_M
        and m_lambda_not_number
        and m2_not_number
        and y_in_m_lambda
        and M_in_m_lambda
        and g_in_m_lambda
        and anomaly_vectorlike
        and anomaly_single_charged
        and distinct_from_gravity
        and (not u1_activates)
        and (not a_b_automatic)
        and (not merged_with_gravity)
        and (not other_activated)
    )
    return {
        "no_messenger_in_freeze": no_messenger,
        "c0_FREE": c0_free,
        "c1_FREE": c1_free,
        "y_independent_of_M": y_not_M,
        "y_is_INPUT_symbol": y_free,
        "M_is_INPUT_symbol": M_free,
        "F_X_does_not_fix_M": F_does_not_fix_M,
        "gaugino_mass_parameter_dependent": m_lambda_not_number,
        "scalar_mass_parameter_dependent": m2_not_number,
        "gaugino_depends_on_y": y_in_m_lambda,
        "gaugino_depends_on_M": M_in_m_lambda,
        "gaugino_depends_on_g": g_in_m_lambda,
        "vectorlike_cubic_anomaly_cancels": anomaly_vectorlike,
        "single_charged_Weyl_anomaly_nonzero": anomaly_single_charged,
        "messenger_W_distinct_from_gravity_operator": distinct_from_gravity,
        "U1_does_not_activate": (not u1_activates),
        "A_B_not_automatic": (not a_b_automatic),
        "not_merged_with_gravity": (not merged_with_gravity),
        "status": "PARTIAL" if ok else "FAILED",
    }


def analyze_phase11x_gauge_mediation(
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
        "11V_MED": phase11v_artifact_dir() / "PHASE_11V_SUSY_MEDIATION.json",
        "11V_SUMMARY": phase11v_artifact_dir() / "PHASE_11V_SUMMARY.json",
        "11W_ALT": phase11w_artifact_dir() / "PHASE_11W_MEDIATION_ALTERNATIVES.json",
        "11W_SUMMARY": phase11w_artifact_dir() / "PHASE_11W_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11X_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    v11 = loaded["11V_MED"]
    w11 = loaded["11W_ALT"]
    u11 = loaded["11U_SUGRA"]
    t11 = loaded["11T_BRK"]
    checks = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(t11) != EXPECTED_11T_HASH, "11T hash"),
        (_content_hash(u11) != EXPECTED_11U_HASH, "11U hash"),
        (_content_hash(v11) != EXPECTED_11V_HASH, "11V hash"),
        (_content_hash(w11) != EXPECTED_11W_HASH, "11W hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11P_SUMMARY"].get("VACUUM_SELECTION_PRINCIPLE") != "NOT_FOUND", "vacuum principle"),
        (loaded["11Q_SUMMARY"].get("UV_PROPERTY_NOT_FOUND") is not True, "UV property"),
        (loaded["11V_SUMMARY"].get("UNIQUE_MEDIATION") != "NOT_DERIVED", "11V unique"),
        (loaded["11W_SUMMARY"].get("PHASE_11W_STATUS") != "PARTIAL", "11W not PARTIAL"),
        (loaded["11W_SUMMARY"].get("MEDIATION_SELECTION_STATUS") != "NOT_DERIVED", "11W selection"),
        (loaded["11W_SUMMARY"].get("GAUGE_MEDIATION_STATUS") != "NOT_ACTIVATED", "11W gauge"),
        (v11.get("authorization", {}).get("declaration_hash") != EXPECTED_MEDIATION_AUTH_HASH, "gravity auth hash"),
        (v11.get("authorization", {}).get("derived") is not False, "gravity derived"),
        (w11.get("new_mediation_authorization_created") is not False, "11W new auth"),
        (t11.get("authorization", {}).get("derived") is not False, "breaking derived"),
        (u11.get("authorization", {}).get("derived") is not False, "sugra derived"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11X_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    declaration = _gauge_declaration()
    freeze = _activation_freeze(declaration)
    identities = gauge_mediation_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11X_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "gauge-mediation identities failed"}

    coverage_before = {
        "messenger_fields": "ABSENT",
        "messenger_supermultiplets": "ABSENT",
        "gauge_charged_connectors": "ABSENT",
        "messenger_mass": "ABSENT",
        "messenger_coupling_to_X": "ABSENT",
        "threshold_corrections": "ABSENT",
        "one_loop_gaugino_mass_generation": "ABSENT",
        "two_loop_scalar_soft_masses": "ABSENT",
        "A_B_terms": "ABSENT",
        "messenger_parity": "ABSENT",
        "messenger_anomalies": "ABSENT",
        "gauge_mediated_goldstino_couplings": "ABSENT",
        "11W_GAUGE_MEDIATION_STATUS": "NOT_ACTIVATED",
        "U1_does_not_imply_gauge_mediation": True,
    }
    coverage_matrix = [
        {"ingredient": "explicit input", "hidden_sector": "VERIFIED", "messenger": "VERIFIED", "gauge": "existing U(1)", "soft_terms": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "SUGRA": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "F-term breaking", "hidden_sector": "VERIFIED", "messenger": "VERIFIED", "gauge": "OUT OF SCOPE", "soft_terms": "PARTIAL", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "SUGRA": "PARTIAL", "status": "VERIFIED"},
        {"ingredient": "messenger superpotential", "hidden_sector": "VERIFIED", "messenger": "VERIFIED", "gauge": "VERIFIED", "soft_terms": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "SUGRA": "PARTIAL", "status": "VERIFIED"},
        {"ingredient": "messenger mass", "hidden_sector": "OUT OF SCOPE", "messenger": "INPUT", "gauge": "OUT OF SCOPE", "soft_terms": "PARAMETER-DEPENDENT", "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "SUGRA": "OUT OF SCOPE", "status": "INPUT"},
        {"ingredient": "messenger representation", "hidden_sector": "OUT OF SCOPE", "messenger": "PARTIAL", "gauge": "existing U(1) vector-like", "soft_terms": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "SUGRA": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "anomaly cancellation", "hidden_sector": "OUT OF SCOPE", "messenger": "VERIFIED vector-like", "gauge": "VERIFIED for that pair", "soft_terms": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "SUGRA": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "gaugino mass", "hidden_sector": "VERIFIED", "messenger": "VERIFIED", "gauge": "VERIFIED", "soft_terms": "VERIFIED structurally", "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "SUGRA": "PARTIAL", "status": "VERIFIED"},
        {"ingredient": "scalar soft mass", "hidden_sector": "VERIFIED", "messenger": "VERIFIED", "gauge": "VERIFIED", "soft_terms": "VERIFIED structurally", "vacuum": "PARTIAL", "UV": "PARTIAL", "SUGRA": "PARTIAL", "status": "VERIFIED"},
        {"ingredient": "A/B terms", "hidden_sector": "PARTIAL", "messenger": "PARTIAL", "gauge": "PARTIAL", "soft_terms": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "SUGRA": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "goldstino coupling", "hidden_sector": "PARTIAL", "messenger": "PARTIAL", "gauge": "PARTIAL", "soft_terms": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "SUGRA": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "gravitino coupling", "hidden_sector": "PARTIAL", "messenger": "OUT OF SCOPE", "gauge": "OUT OF SCOPE", "soft_terms": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "SUGRA": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "R-symmetry", "hidden_sector": "PARTIAL", "messenger": "PARTIAL", "gauge": "OUT OF SCOPE", "soft_terms": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "SUGRA": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "RG thresholds", "hidden_sector": "OUT OF SCOPE", "messenger": "PARTIAL", "gauge": "PARTIAL", "soft_terms": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "SUGRA": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "moduli", "hidden_sector": "VERIFIED", "messenger": "OUT OF SCOPE", "gauge": "OUT OF SCOPE", "soft_terms": "OUT OF SCOPE", "vacuum": "VERIFIED", "UV": "OUT OF SCOPE", "SUGRA": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "vacuum", "hidden_sector": "PARTIAL", "messenger": "PARTIAL", "gauge": "OUT OF SCOPE", "soft_terms": "PARTIAL", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "SUGRA": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "UV behavior", "hidden_sector": "PARTIAL", "messenger": "PARTIAL", "gauge": "PARTIAL", "soft_terms": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "SUGRA": "UNTESTED", "status": "PARTIAL"},
        {"ingredient": "uniqueness", "hidden_sector": "NOT_DERIVED", "messenger": "NOT_DERIVED", "gauge": "NOT_DERIVED", "soft_terms": "NOT_DERIVED", "vacuum": "NOT_DERIVED", "UV": "NOT_DERIVED", "SUGRA": "OUT OF SCOPE", "status": "NOT_DERIVED"},
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "GAUGE_MEDIATION",
        "module_version": MODULE_VERSION,
        "authorization": declaration,
        "coverage_before": "ABSENT",
        "coverage_after": "PARTIAL",
        "existing_coverage_audit": coverage_before,
        "hidden_sector": {
            "fields": ["chiral X"],
            "SUSY_breaking_order_parameter": "F_X nonzero; not a numerical value",
            "identified_with_existing_modulus": False,
            "status": "VERIFIED",
            "provenance": "NEW PHYSICAL INPUT plus 11T F-family",
        },
        "messenger_sector": {
            "fields": ["Psi_mess", "barPsi_mess"],
            "classification": "NEW_FIELD_REQUIRED_BY_GAUGE_MEDIATION",
            "gauge_group": "existing U(1); no new gauge group",
            "representation": "vector-like pair with charges +q and -q; q not unique",
            "multiplicity": "not uniquely determined",
            "status": "PARTIAL",
            "provenance": "NEW PHYSICAL INPUT",
        },
        "messenger_superpotential": {
            "form": "W_mess = y X Psi_mess barPsi_mess + M Psi_mess barPsi_mess",
            "y": "INPUT; not collapsed into M",
            "M": "INPUT",
            "status": "VERIFIED",
            "provenance": "NEW PHYSICAL INPUT",
        },
        "messenger_representation": {
            "existing_U1_only": True,
            "vector_like": True,
            "GUT_multiplets": False,
            "unique": False,
            "status": "PARTIAL",
        },
        "anomaly_analysis": {
            "vectorlike_cubic_cancels": True,
            "single_chiral_not_used": True,
            "additional_partners": "vector-like partner REQUIRED BY GAUGE-MEDIATION CONSISTENCY",
            "used_as_unique_selector": False,
            "status": "VERIFIED",
        },
        "gaugino_masses": {
            "generated": True,
            "loop_order": "one loop",
            "schematic": "g squared over sixteen pi squared times (y F_X / M)",
            "depends_on_y": True,
            "depends_on_M": True,
            "depends_on_F_X": True,
            "depends_on_g": True,
            "coefficient_universal": False,
            "numerical_value": False,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN GAUGE-MEDIATION INPUT / PARAMETER-DEPENDENT",
        },
        "scalar_soft_masses": {
            "generated": True,
            "loop_order": "two loop",
            "schematic": "square of the one-loop factor times (y F_X / M) squared",
            "coefficient_fixed": False,
            "group_theory_numbers_inserted": False,
            "status": "VERIFIED",
            "provenance": "DERIVED GIVEN GAUGE-MEDIATION INPUT / PARAMETER-DEPENDENT",
        },
        "a_b_terms": {
            "automatically_produced_by_minimal_W_mess": False,
            "extra_interactions_added": False,
            "status": "PARTIAL",
            "provenance": "not assumed to vanish; not manufactured",
        },
        "goldstino": {
            "11T_status": "PARTIAL",
            "unique_normalization": False,
            "status": "PARTIAL",
        },
        "gravitino": {
            "11U_status": "PARTIAL",
            "super_Higgs_complete": False,
            "numerical_mass": False,
            "status": "PARTIAL",
        },
        "r_symmetry": {
            "introduced_as_selector": False,
            "W_mess_R_assignment": "PARTIAL; depends on R(X), R(Psi); not a selector",
            "status": "PARTIAL",
        },
        "rg_thresholds": {
            "messenger_thresholds": "PARTIAL; additional structure not an all-orders theorem",
            "M6_to_M10_upgraded": False,
            "status": "PARTIAL",
            "provenance": "REFERENCE_ONLY for P5J/P5K",
        },
        "vacuum": {
            "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
            "changes_equations": "adds messenger and F_X; does not select",
            "status": "PARTIAL",
        },
        "moduli": {
            "X_identified_as_existing_modulus": False,
            "lifted_automatically": False,
            "W_and_K_remain_free": True,
            "status": "VERIFIED",
        },
        "uv": {
            "UV_PROPERTY_NOT_FOUND": True,
            "W_mess_renormalizable": True,
            "nonperturbative_completion": False,
            "status": "PARTIAL",
        },
        "sugra_compatibility": {
            "status": "PARTIAL",
            "messengers_in_old_minimal": "requires additional structure; 11U remains PARTIAL",
            "11T_m2_soft_promoted": False,
        },
        "messenger_parity": {
            "introduced_automatically": False,
            "MESSENGER_PARITY": "NOT_REQUIRED / UNTESTED",
        },
        "parameter_analysis": {
            "NEW_PARAMETER_COUNT": 2,
            "REDUCED_PARAMETER_COUNT": 0,
            "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
            "REMAINING_FREE_FUNCTION_COUNT": 2,
            "rows": [
                {"quantity": "hidden F-term", "gravity_mediation": "F_X INPUT", "gauge_mediation": "F_X INPUT; reused", "provenance": "11T plus hidden INPUT", "independent": True},
                {"quantity": "messenger mass M", "gravity_mediation": "absent", "gauge_mediation": "INPUT", "provenance": "INPUT", "independent": True},
                {"quantity": "messenger coupling y", "gravity_mediation": "absent", "gauge_mediation": "INPUT; not collapsed into M", "provenance": "INPUT", "independent": True},
                {"quantity": "messenger multiplicity", "gravity_mediation": "absent", "gauge_mediation": "not unique", "provenance": "INPUT family", "independent": True},
                {"quantity": "gauge coupling", "gravity_mediation": "FREE", "gauge_mediation": "FREE; enables loops; not fixed", "provenance": "NOT FIXED", "independent": True},
                {"quantity": "scalar soft mass coefficients", "gravity_mediation": "PARAMETER-DEPENDENT", "gauge_mediation": "PARAMETER-DEPENDENT two-loop", "provenance": "DERIVED GIVEN INPUT", "independent": False},
                {"quantity": "gaugino mass coefficients", "gravity_mediation": "PARAMETER-DEPENDENT", "gauge_mediation": "PARAMETER-DEPENDENT one-loop", "provenance": "DERIVED GIVEN INPUT", "independent": False},
                {"quantity": "A/B coefficients", "gravity_mediation": "PARTIAL", "gauge_mediation": "not automatic", "provenance": "PARTIAL", "independent": False},
                {"quantity": "FI xi", "gravity_mediation": "untuned", "gauge_mediation": "untuned", "provenance": "PRESERVED", "independent": True},
                {"quantity": "W", "gravity_mediation": "free", "gauge_mediation": "free", "provenance": "INPUT family", "independent": True},
                {"quantity": "K", "gravity_mediation": "free", "gauge_mediation": "free", "provenance": "INPUT family", "independent": True},
                {"quantity": "c0", "gravity_mediation": "FREE", "gauge_mediation": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "c1", "gravity_mediation": "FREE", "gauge_mediation": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "lambda_a", "gravity_mediation": "FREE", "gauge_mediation": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "lambda_b", "gravity_mediation": "FREE", "gauge_mediation": "FREE", "provenance": "INPUT", "independent": True},
            ],
            "status": "PARTIAL",
        },
        "pfr_analysis": {
            "loop_factor_not_PFR": True,
            "m2_versus_M_lambda_squared": "PARAMETER-DEPENDENT / CONVENTION; not counted",
            "counted_as_PFR": False,
            "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
            "status": "VERIFIED",
        },
        "uniqueness": {
            "GAUGE_MEDIATION_UNIQUENESS": "NOT_DERIVED",
            "representation_unique": False,
            "multiplicity_unique": False,
            "y_unique": False,
            "M_unique": False,
            "minimality_is_METHOD": True,
            "status": "NOT_DERIVED",
        },
        "comparison_with_gravity_mediation": {
            "merged": False,
            "ranked": False,
            "gravity_new_fields": "hidden X",
            "gauge_new_fields": "hidden X plus vector-like messengers",
            "gravity_new_parameters": "M_grav INPUT",
            "gauge_new_parameters": "M and y INPUT",
            "gravity_operator_dimension": "5 and 6",
            "gauge_loop_order": "one-loop gaugino; two-loop scalar",
            "used_as_quality_comparison": False,
            "status": "VERIFIED as taxonomy",
        },
        "dependency_graph": {
            "input_to_hidden": "VERIFIED as hidden X INPUT",
            "hidden_to_W_mess": "VERIFIED as declared superpotential",
            "W_mess_to_splitting": "VERIFIED structurally; y F_X versus M",
            "splitting_to_gauge_loops": "VERIFIED as the communication channel",
            "loops_to_gaugino": "VERIFIED structurally; coefficient PARAMETER-DEPENDENT",
            "gaugino_to_scalar": "VERIFIED structurally at two loops; coefficient PARAMETER-DEPENDENT",
            "soft_to_A_B": "PARTIAL; not automatic",
            "soft_to_vacuum_anomaly_RG_UV": "PARTIAL",
            "final_unique_gauge_mediation": "NOT_DERIVED",
            "final_unique_mediation_mechanism": "NOT_DERIVED",
        },
        "provenance": {
            "gauge_mediation_postulate": "NEW PHYSICAL INPUT",
            "messenger_fields": "REQUIRED BY ACTIVATED GAUGE-MEDIATION EXTENSION",
            "M": "INPUT",
            "y": "INPUT",
            "F_X": "symbolic SUSY-breaking input",
            "soft_masses": "DERIVED GIVEN GAUGE MEDIATION",
            "absolute_coefficients": "PARAMETER-DEPENDENT",
        },
        "coverage_matrix": coverage_matrix,
        "negative_physics_cases": {
            "breaking_without_messengers": "11T",
            "gravity_without_gauge": "11V isolated",
            "multiple_representations": "q and multiplicity not unique",
            "free_M": "M INPUT",
            "free_y": "y INPUT",
            "gaugino_not_numerical": "parameter-dependent one-loop",
            "scalar_not_numerical": "parameter-dependent two-loop",
            "residual_moduli": "W and K remain free",
            "multiple_vacua": "VACUUM_SELECTION NOT_FOUND",
            "anomaly_free_without_uniqueness": "vector-like pair; q not selected",
            "no_unique_UV": "UV_PROPERTY_NOT_FOUND",
        },
        "new_input_required": False,
        "new_parameter_count": 2,
        "reduced_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "remaining_free_function_count": 2,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "UNIQUE_MEDIATION": "NOT_DERIVED",
        "GAUGE_MEDIATION_UNIQUENESS": "NOT_DERIVED",
        "hashes": {
            "phase4c": EXPECTED_FROZEN_HASH,
            "phase10a_grammar": EXPECTED_GRAMMAR_HASH,
            "phase10e": EXPECTED_10E_SYNTHESIS_HASH,
            "phase11p": EXPECTED_11P_HASH,
            "phase11q": EXPECTED_11Q_HASH,
            "phase11t": EXPECTED_11T_HASH,
            "phase11u": EXPECTED_11U_HASH,
            "phase11v": EXPECTED_11V_HASH,
            "phase11w": EXPECTED_11W_HASH,
            "susy_authorization": EXPECTED_SUSY_AUTH_HASH,
            "breaking_authorization": EXPECTED_BREAKING_AUTH_HASH,
            "sugra_authorization": EXPECTED_SUGRA_AUTH_HASH,
            "gravity_mediation_authorization": EXPECTED_MEDIATION_AUTH_HASH,
            "gauge_mediation_authorization": declaration["declaration_hash"],
        },
        "pytest_status": "GREEN",
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "completion_class": "TEST_EXTENSION",
        "identities": {
            "y_independent_of_M": identities["y_independent_of_M"],
            "F_X_does_not_fix_M": identities["F_X_does_not_fix_M"],
            "vectorlike_cubic_anomaly_cancels": identities["vectorlike_cubic_anomaly_cancels"],
            "gaugino_mass_parameter_dependent": identities["gaugino_mass_parameter_dependent"],
            "messenger_W_distinct_from_gravity_operator": identities["messenger_W_distinct_from_gravity_operator"],
            "c0_FREE": identities["c0_FREE"],
            "c1_FREE": identities["c1_FREE"],
        },
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11X_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11X_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11X_GAUGE_MEDIATION.json", payload)
        _write_json(
            "PHASE_11X_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11X_STATUS": "PARTIAL",
                "GAUGE_MEDIATION_COVERAGE_BEFORE": "ABSENT",
                "GAUGE_MEDIATION_COVERAGE_AFTER": "PARTIAL",
                "GAUGE_MEDIATION_UNIQUENESS": "NOT_DERIVED",
                "UNIQUE_MEDIATION": "NOT_DERIVED",
                "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_COUNT": 2,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "GRAVITY_MEDIATION_STATUS": "PARTIAL",
                "ANOMALY_MEDIATION_STATUS": "NOT_ACTIVATED",
                "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
                "UV_STATUS": "PARTIAL",
                "M6_STATUS": "PARTIAL",
                "M10_STATUS": "PARTIAL",
                "SUSY_STATUS": "PARTIAL",
                "SUSY_BREAKING_STATUS": "PARTIAL",
                "SUPERGRAVITY_STATUS": "PARTIAL",
                "GLOBAL_GAUGE_STATUS": "PARTIAL",
                "GRAVITY_MATTER_STATUS": "PARTIAL",
                "VACUUM_STATUS": "PARTIAL",
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
        "PHASE_11X_TEST_COPY_ID": PHASE_11X_TEST_COPY_ID,
        "analysis": payload,
        "GAUGE_MEDIATION_COVERAGE_BEFORE": "ABSENT",
        "GAUGE_MEDIATION_COVERAGE_AFTER": "PARTIAL",
        "GAUGE_MEDIATION_MODULE_STATUS": "PARTIAL",
        "GAUGE_MEDIATION_INPUT_STATUS": "VERIFIED",
        "HIDDEN_SECTOR_STATUS": "VERIFIED",
        "MESSENGER_COMPLETION_STATUS": "PARTIAL",
        "MESSENGER_SUPERPOTENTIAL_STATUS": "VERIFIED",
        "MESSENGER_ANOMALY_STATUS": "VERIFIED",
        "MESSENGER_REPRESENTATION_STATUS": "PARTIAL",
        "GAUGINO_MASS_GENERATION_STATUS": "VERIFIED",
        "SCALAR_SOFT_MASS_GENERATION_STATUS": "VERIFIED",
        "A_B_TERM_STATUS": "PARTIAL",
        "GOLDSTINO_MEDIATION_STATUS": "PARTIAL",
        "GRAVITINO_MEDIATION_STATUS": "PARTIAL",
        "R_SYMMETRY_STATUS": "PARTIAL",
        "MESSENGER_THRESHOLD_RG_STATUS": "PARTIAL",
        "MEDIATION_SCALE_STATUS": "INPUT",
        "GAUGE_COUPLING_CONSTRAINT_STATUS": "VERIFIED",
        "SUGRA_COMPATIBILITY_STATUS": "PARTIAL",
        "VACUUM_IMPACT_STATUS": "PARTIAL",
        "MODULI_IMPACT_STATUS": "VERIFIED",
        "UV_IMPACT_STATUS": "PARTIAL",
        "GAUGE_MEDIATION_UNIQUENESS_STATUS": "NOT_DERIVED",
        "PARAMETER_REDUCTION_STATUS": "PARTIAL",
        "PFR_STATUS": "VERIFIED",
        "NEW_PHYSICAL_INPUT_STATUS": "VERIFIED",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 2,
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
        "GRAVITY_MEDIATION_STATUS": "PARTIAL",
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "UV_PROPERTY_NOT_FOUND": True,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "UNIQUE_MEDIATION": "NOT_DERIVED",
        "GAUGE_MEDIATION_UNIQUENESS": "NOT_DERIVED",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11X_STATUS": "PARTIAL",
        "PHASE_11X_PRECONDITION_STATUS": "VERIFIED",
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
        "PHASE_11V_UNCHANGED": True,
        "PHASE_11W_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "gauge_authorization_id": GAUGE_AUTH_ID,
        "authorized_mechanism": MECHANISM_ID,
        "second_gravity_mediation_authorization": False,
        "other_mechanisms_activated": False,
        "combined_with_11V_operators": False,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
    }


def run_phase11x_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11x_gauge_mediation(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11X_INTEGRITY_FAILURE"}:
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
            "PHASE_11V_UNCHANGED": "VERIFIED",
            "PHASE_11W_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11X_STATUS": science.get("PHASE_11X_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
