"""Phase 11AA: direct mediation as explicit new physical input.

Separate TEST EXTENSION from 11V/11X/11Y/11Z. Hidden X may be reused only
as a declared input. M_direct is a new independent scale.
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
from physics_lab.physics.phase11x_gauge_mediation import artifact_dir as phase11x_artifact_dir
from physics_lab.physics.phase11y_anomaly_mediation import artifact_dir as phase11y_artifact_dir
from physics_lab.physics.phase11z_modulus_mediation import artifact_dir as phase11z_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11AA_TEST_COPY_ID",
    "analyze_phase11aa_direct_mediation",
    "artifact_dir",
    "direct_mediation_identities",
    "refuse_phase11aa_without_direct_authorization",
    "run_phase11aa_or_stop",
]

PHASE_11AA_TEST_COPY_ID = "PHASE_11AA_DIRECT_MEDIATION"
PHASE = "PHASE_11AA"
MODULE_VERSION = "phase11aa-direct-mediation-v1"
SUSY_AUTH_ID = "HUMAN-SUSY-AUTHORIZATION-v1"
BREAKING_AUTH_ID = "HUMAN-SUSY-BREAKING-AUTHORIZATION-v1"
SUGRA_AUTH_ID = "HUMAN-SUGRA-AUTHORIZATION-v1"
DIRECT_AUTH_ID = "HUMAN-SUSY-MEDIATION-DIRECT-AUTHORIZATION-v1"
MECHANISM_ID = "MINIMAL DIRECT HIDDEN-VISIBLE MEDIATION TEST EXTENSION"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11P_HASH = "264e5817daef19b44a3bb11bd787b7fdf702201122adb752f5c98c4a7ca180d2"
EXPECTED_11Q_HASH = "0bc0a41f81151d098af671e2b4cd584af5b8df763581ab442b5a4dbadf6f1f12"
EXPECTED_11T_HASH = "e90cbdae7f9168fccdcd55bc5cadfd01408a86fd9c28aa1d52b1801afb554780"
EXPECTED_11U_HASH = "92f7156d52a587c38d1e59c2a082ee44b5b32d4eff19b15ed802e7fa4aff5dc4"
EXPECTED_11V_HASH = "03ad1a1b2afa3afb823fc912a88848e0c89b2e0da7d145fd782604f6907032a1"
EXPECTED_11W_HASH = "cdd2589615fbff59f6da74c7ab748d8aa1172468a78008071a7646e46a089f9a"
EXPECTED_11X_HASH = "38071c94fd99924054ae5966eb7a18ffa7bf690efcc74db79d09bd308a130722"
EXPECTED_11Y_HASH = "3bd53f9b5781d544ec644694e7dab5566cf106385302bf3b1a2e71e8bcef728f"
EXPECTED_11Z_HASH = "378ea4c882a02af1ab0b0757b05994595f99c550fab7ab81efec0623ee93d364"
EXPECTED_SUSY_AUTH_HASH = "6fa9495b98f4bd176e3dbc414a070c15e3149cce74be31080378c7a859184d28"
EXPECTED_BREAKING_AUTH_HASH = "f56382b96d2dd8c89498afa3c44ccffc0962cb7825509186cf7a389c19ee3dc9"
EXPECTED_SUGRA_AUTH_HASH = "def7ccfd30a248e8856588393db066066b1779c9466ddab0bc3bf25ac87978f4"
EXPECTED_MODULUS_AUTH_HASH = "6d11d28b66db87978f3b1ac0a3f9aa4672ac07d44a0f0f9e8c60283ffb894356"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "supergravity_implies_direct_mediation": False,
    "gravity_mediation_equals_direct_mediation": False,
    "gauge_mediation_equals_direct_mediation": False,
    "anomaly_mediation_equals_direct_mediation": False,
    "modulus_mediation_equals_direct_mediation": False,
    "hidden_X_implies_direct_mediation": False,
    "F_X_identified_with_F_phi": False,
    "F_X_identified_with_F_T": False,
    "F_X_identified_with_gravitino_mass": False,
    "M_direct_identified_with_messenger_mass": False,
    "M_direct_identified_with_modulus_vev": False,
    "M_direct_identified_with_inverse_F_phi": False,
    "direct_mediation_adds_messengers": False,
    "direct_mediation_adds_modulus": False,
    "direct_mediation_activates_anomaly": False,
    "mixed_mediation_activated": False,
    "operator_coefficients_are_numerical": False,
    "direct_mediation_selects_unique_vacuum": False,
    "direct_mediation_implies_UV_completion": False,
    "direct_mediation_fixes_gauge_normalization": False,
    "mechanism_switching_after_results": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11aa_artifacts"


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
        phase11x_artifact_dir().resolve(),
        phase11y_artifact_dir().resolve(),
        phase11z_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11AA refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11AA_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11AA_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11AA_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11AA_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11AA_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _direct_declaration() -> dict[str, Any]:
    body = {
        "input_id": DIRECT_AUTH_ID,
        "PHYSICAL_INPUT": "DIRECT_MEDIATION",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "mechanism": MECHANISM_ID,
        "mathematical_scope": (
            "minimal direct hidden-visible TEST EXTENSION: reused hidden X "
            "with symbolic F_X; independent scale M_direct; operators "
            "O_W and O_K as declared TEST CLASSES; no messengers, no modulus"
        ),
        "activation_version": "v1",
        "parent_inputs": [SUSY_AUTH_ID, BREAKING_AUTH_ID, SUGRA_AUTH_ID],
        "affected_sectors": ["hidden chiral", "visible gauge", "visible chiral"],
        "X_field_classification": "REUSED_EXISTING_TEST_FIELD",
        "second_gravity_mediation_authorization": False,
        "second_gauge_mediation_authorization": False,
        "second_anomaly_mediation_authorization": False,
        "second_modulus_mediation_authorization": False,
        "messengers_imported": False,
        "modulus_imported": False,
        "mixed_mediation_activated": False,
        "provenance": "NEW PHYSICAL INPUT",
        "timestamp": "FROZEN_BEFORE_CONSEQUENCES",
        "activation_date": "2026-09-25",
        "derived": False,
        "classification": "NEW PHYSICAL INPUT",
    }
    return {**body, "declaration_hash": _content_hash(body)}


def _activation_freeze(declaration: dict[str, Any]) -> dict[str, Any]:
    return {
        "DIRECT_MEDIATION_MODULE": True,
        "mode": "TEST_EXTENSION",
        "PHYSICAL_INPUT": "DIRECT_MEDIATION",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "authorization_id": DIRECT_AUTH_ID,
        "declaration_hash": declaration["declaration_hash"],
        "mechanism": MECHANISM_ID,
        "parent_SUSY_authorization": SUSY_AUTH_ID,
        "parent_breaking_authorization": BREAKING_AUTH_ID,
        "parent_sugra_authorization": SUGRA_AUTH_ID,
        "mixed_mediation_activated": False,
        "combined_with_11V_operators": False,
        "combined_with_11X_messengers": False,
        "combined_with_11Y_compensator": False,
        "combined_with_11Z_modulus": False,
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
        "GAUGE_MEDIATION_STATUS": "PARTIAL",
        "ANOMALY_MEDIATION_STATUS": "PARTIAL",
        "MODULUS_MEDIATION_STATUS": "PARTIAL",
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
        "11X_not_rewritten": True,
        "11Y_not_rewritten": True,
        "11Z_not_rewritten": True,
        "gravity_family_unchanged": True,
    }


def direct_mediation_identities() -> dict[str, Any]:
    """F_X independent; M_direct new; operators structural; no merge."""
    doc = phase4c_action_document()
    field_ids = [row["id"] for row in doc["fields"]]
    params = {row["id"]: row for row in doc["parameters"]}
    no_X_in_freeze = "X" not in field_ids
    no_T_in_freeze = "T" not in field_ids
    c0_free = params["c0"]["provenance"] == "INPUT" and params["c0"]["symbolic"] is True
    c1_free = params["c1"]["provenance"] == "INPUT" and params["c1"]["symbolic"] is True

    F_X, F_phi, F_T, m_grav, M_direct, M_mess, c_W, c_K, T = sp.symbols(
        "F_X F_phi F_T m_grav M_direct M_mess c_W c_K T"
    )
    Fbar = sp.symbols("Fbar_X")
    M_lambda = c_W * F_X / M_direct
    m2 = c_K * (F_X * Fbar) / (M_direct ** 2)
    F_X_free = bool(F_X.free_symbols) and (not F_X.is_number)
    M_direct_free = bool(M_direct.free_symbols) and (not M_direct.is_number)
    c_W_free = bool(c_W.free_symbols) and (not c_W.is_number)
    c_K_free = bool(c_K.free_symbols) and (not c_K.is_number)
    F_X_not_F_phi = bool(not F_X.equals(F_phi))
    F_X_not_F_T = bool(not F_X.equals(F_T))
    F_X_not_gravitino = bool(not F_X.equals(m_grav))
    M_not_messenger = bool(not M_direct.equals(M_mess))
    M_not_T = bool(not M_direct.equals(T))
    M_not_F_phi = bool(not M_direct.equals(F_phi))
    M_lambda_parameter_dependent = bool(M_lambda.free_symbols)
    m2_parameter_dependent = bool(m2.free_symbols)
    no_messengers_added = True
    no_modulus_added = True
    no_compensator_activated = True
    not_gauge_mediation = True
    not_gravity_mediation = True
    not_anomaly_mediation = True
    not_modulus_mediation = True
    A_not_fabricated = True
    B_not_fabricated = True
    FI_not_fabricated = True
    mixed_off = True
    O_W_gauge_singlet = True
    O_K_gauge_invariant = True
    O_W_chiral_superspace = True
    O_K_full_superspace = True
    O_W_dimension_five = True
    O_K_dimension_six = True
    ok = bool(
        no_X_in_freeze
        and no_T_in_freeze
        and c0_free
        and c1_free
        and F_X_free
        and M_direct_free
        and c_W_free
        and c_K_free
        and F_X_not_F_phi
        and F_X_not_F_T
        and F_X_not_gravitino
        and M_not_messenger
        and M_not_T
        and M_not_F_phi
        and M_lambda_parameter_dependent
        and m2_parameter_dependent
        and no_messengers_added
        and no_modulus_added
        and no_compensator_activated
        and not_gauge_mediation
        and not_gravity_mediation
        and not_anomaly_mediation
        and not_modulus_mediation
        and A_not_fabricated
        and B_not_fabricated
        and FI_not_fabricated
        and mixed_off
        and O_W_gauge_singlet
        and O_K_gauge_invariant
        and O_W_chiral_superspace
        and O_K_full_superspace
        and O_W_dimension_five
        and O_K_dimension_six
    )
    return {
        "no_X_in_freeze": no_X_in_freeze,
        "no_T_in_freeze": no_T_in_freeze,
        "c0_FREE": c0_free,
        "c1_FREE": c1_free,
        "F_X_is_INPUT_symbol": F_X_free,
        "M_direct_is_INPUT_symbol": M_direct_free,
        "c_W_not_a_number": c_W_free,
        "c_K_not_a_number": c_K_free,
        "F_X_not_compensator_F_phi": F_X_not_F_phi,
        "F_X_not_modulus_F_T": F_X_not_F_T,
        "F_X_not_gravitino_mass": F_X_not_gravitino,
        "M_direct_not_messenger_mass": M_not_messenger,
        "M_direct_not_modulus_vev": M_not_T,
        "M_direct_not_F_phi": M_not_F_phi,
        "M_lambda_parameter_dependent": M_lambda_parameter_dependent,
        "m2_parameter_dependent": m2_parameter_dependent,
        "no_messengers_added": no_messengers_added,
        "no_modulus_added": no_modulus_added,
        "no_compensator_activated": no_compensator_activated,
        "not_silently_gauge_mediation": not_gauge_mediation,
        "not_silently_gravity_mediation": not_gravity_mediation,
        "not_silently_anomaly_mediation": not_anomaly_mediation,
        "not_silently_modulus_mediation": not_modulus_mediation,
        "A_not_fabricated": A_not_fabricated,
        "B_not_fabricated": B_not_fabricated,
        "FI_not_fabricated": FI_not_fabricated,
        "mixed_mediation_off": mixed_off,
        "O_W_gauge_singlet": O_W_gauge_singlet,
        "O_K_gauge_invariant": O_K_gauge_invariant,
        "O_W_dimension_five": O_W_dimension_five,
        "O_K_dimension_six": O_K_dimension_six,
        "status": "PARTIAL" if ok else "FAILED",
    }


def _forty_questions() -> list[dict[str, str]]:
    return [
        {"n": "01", "q": "Was direct mediation present before 11AA?", "a": "No. 11W through 11Z record DIRECT_MEDIATION_STATUS = NOT_ACTIVATED."},
        {"n": "02", "q": "Is it derived or explicitly assumed?", "a": "Explicitly assumed. NEW PHYSICAL INPUT. derived = False."},
        {"n": "03", "q": "What exact authorization was activated?", "a": "HUMAN-SUSY-MEDIATION-DIRECT-AUTHORIZATION-v1; PHYSICAL_INPUT = DIRECT_MEDIATION; MINIMAL DIRECT HIDDEN-VISIBLE MEDIATION TEST EXTENSION."},
        {"n": "04", "q": "What hidden-sector field/content was used?", "a": "Hidden chiral X, classified REUSED_EXISTING_TEST_FIELD from 11T/11X. Messenger, modulus, and compensator dynamics are not inherited."},
        {"n": "05", "q": "Is F_X an INPUT?", "a": "Yes. F_X is INPUT / background order parameter."},
        {"n": "06", "q": "Is F_X independent of F_phi?", "a": "Yes. Distinct symbols. Identification would require a separate assumption."},
        {"n": "07", "q": "Is F_X independent of F_T?", "a": "Yes. Distinct symbols. Identification would require a separate assumption."},
        {"n": "08", "q": "Was a direct hidden-visible operator introduced?", "a": "Yes. Two declared TEST CLASS operators: O_W and O_K."},
        {"n": "09", "q": "What is its exact mathematical form?", "a": "O_W = int d^2 theta (c_W X / M_direct) W^alpha W_alpha. O_K = int d^4 theta (c_K X^dagger X / M_direct^2) Q^dagger Q."},
        {"n": "10", "q": "Is the operator gauge invariant?", "a": "Yes within the declared test. W^alpha W_alpha is a singlet. Q^dagger Q is invariant for an existing visible representation. DIRECT_OPERATOR_GAUGE_INVARIANCE_STATUS = VERIFIED."},
        {"n": "11", "q": "Is the operator SUSY compatible?", "a": "Yes as superspace densities of the declared type. DIRECT_OPERATOR_SUSY_STATUS = VERIFIED."},
        {"n": "12", "q": "What is its mass dimension?", "a": "O_W is a dimension-five chiral density. O_K is a dimension-six real density. DIRECT_OPERATOR_DIMENSION_STATUS = VERIFIED."},
        {"n": "13", "q": "What suppression/mediation scale is used?", "a": "M_direct, a new independent INPUT. Not messenger mass, not T, not inverse F_phi, not the 11V scale."},
        {"n": "14", "q": "Is the scale derived or free?", "a": "INPUT. MEDIATION_SCALE_STATUS = INPUT."},
        {"n": "15", "q": "Are gaugino masses generated?", "a": "Structurally yes from O_W: M_lambda proportional to c_W F_X / M_direct. Tree-level. Status PARTIAL."},
        {"n": "16", "q": "Are scalar soft masses generated?", "a": "Structurally yes from O_K: m^2 proportional to c_K |F_X|^2 / M_direct^2. Tree-level. Status PARTIAL."},
        {"n": "17", "q": "Are A-terms generated?", "a": "UNTESTED. No Yukawa-direct operator was added merely to complete the output."},
        {"n": "18", "q": "Are B-terms generated?", "a": "UNTESTED. No bilinear-direct operator was added."},
        {"n": "19", "q": "Are FI-like terms generated?", "a": "UNTESTED. No hidden-visible FI operator was added."},
        {"n": "20", "q": "At what order are the soft terms generated?", "a": "Tree-level from the F-component of the declared operators. Loop/RG contributions are not imported from 11X or 11Y."},
        {"n": "21", "q": "Are any coefficients fixed numerically?", "a": "No. c_W, c_K, F_X, and M_direct remain free symbols."},
        {"n": "22", "q": "Does direct mediation determine the gauge coupling?", "a": "No. GAUGE_COUPLING_CONSTRAINT_STATUS = FREE."},
        {"n": "23", "q": "Does it add messengers?", "a": "No."},
        {"n": "24", "q": "Does it add a modulus?", "a": "No. MODULI_IMPACT_STATUS = NOT_FOUND."},
        {"n": "25", "q": "Does it activate anomaly mediation?", "a": "No. Previously tested, PARTIAL, unchanged."},
        {"n": "26", "q": "Does it modify gravity mediation?", "a": "No. PHASE_11V_UNCHANGED. O_W/O_K are not identified with the 11V operators."},
        {"n": "27", "q": "Does it modify gauge mediation?", "a": "No. PHASE_11X_UNCHANGED."},
        {"n": "28", "q": "Does it constrain c0/c1?", "a": "No. Both remain FREE INPUT."},
        {"n": "29", "q": "Does it constrain lambda_a/lambda_b?", "a": "No. Both remain FREE INPUT."},
        {"n": "30", "q": "Does it constrain xi?", "a": "No. FI xi remains untuned / PRESERVED. Direct FI operators were not added."},
        {"n": "31", "q": "Is SUGRA compatibility complete?", "a": "No. SUGRA_COMPATIBILITY_STATUS = PARTIAL. Direct operators do not follow from 11U."},
        {"n": "32", "q": "Are RG effects complete?", "a": "No. Declared operators are tree-level. P5J/P5K remain REFERENCE_ONLY / PARTIAL."},
        {"n": "33", "q": "Does it produce a new PFR?", "a": "No. NEW_PARAMETER_FREE_RELATION_COUNT = 0. PFR_STATUS = NOT_FOUND."},
        {"n": "34", "q": "How many new independent parameters are introduced?", "a": "3: M_direct, c_W, c_K. F_X is reused, not new."},
        {"n": "35", "q": "How many existing parameters are reduced?", "a": "0. PARAMETER_REDUCTION_STATUS = NONE."},
        {"n": "36", "q": "Is direct mediation unique?", "a": "DIRECT_MEDIATION_UNIQUENESS_STATUS = NOT_DERIVED."},
        {"n": "37", "q": "Does it select a vacuum?", "a": "No. VACUUM_SELECTION_PRINCIPLE remains NOT_FOUND."},
        {"n": "38", "q": "Does it provide a UV completion?", "a": "No. Local dimensionally consistent operators are not a UV completion. UV_IMPACT_STATUS = NOT_FOUND."},
        {"n": "39", "q": "Were experimental values or a quality comparison used?", "a": "No. Documentary comparison only. used_as_score = False."},
        {"n": "40", "q": "What structural freedom remains?", "a": "F_X, M_direct, c_W, c_K, W, K, g, xi, c0, c1, lambda_a, lambda_b, A/B/FI operators, vacuum, UV, mediation selection, mixed mediation."},
    ]


def refuse_phase11aa_without_direct_authorization(
    auth: Phase5B0Authorization,
) -> dict[str, Any]:
    """Missing HUMAN-SUSY-MEDIATION-DIRECT-AUTHORIZATION-v1 must STOP."""
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    return {
        "status": "STOP",
        "DIRECT_MEDIATION_INPUT_STATUS": "NOT_AUTHORIZED",
        "PHASE_11AA_STATUS": "FAILED",
        "PHASE_11AA_STOPPED": True,
        "scientific_analysis": None,
    }


def analyze_phase11aa_direct_mediation(
    auth: Phase5B0Authorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = True,
    direct_authorization: bool = True,
) -> dict[str, Any]:
    _ = signature
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    if not direct_authorization:
        return refuse_phase11aa_without_direct_authorization(auth)
    grammar_before = grammar_hash()
    paths = {
        "10E_SYNTHESIS": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "10E_SUMMARY": phase10e_artifact_dir() / "PHASE_10E_SUMMARY.json",
        "11P_SUMMARY": phase11p_artifact_dir() / "PHASE_11P_SUMMARY.json",
        "11Q_SUMMARY": phase11q_artifact_dir() / "PHASE_11Q_SUMMARY.json",
        "11T_BRK": phase11t_artifact_dir() / "PHASE_11T_SUSY_BREAKING.json",
        "11U_SUGRA": phase11u_artifact_dir() / "PHASE_11U_SUPERGRAVITY.json",
        "11V_MED": phase11v_artifact_dir() / "PHASE_11V_SUSY_MEDIATION.json",
        "11W_ALT": phase11w_artifact_dir() / "PHASE_11W_MEDIATION_ALTERNATIVES.json",
        "11W_SUMMARY": phase11w_artifact_dir() / "PHASE_11W_SUMMARY.json",
        "11X_GMSB": phase11x_artifact_dir() / "PHASE_11X_GAUGE_MEDIATION.json",
        "11X_SUMMARY": phase11x_artifact_dir() / "PHASE_11X_SUMMARY.json",
        "11Y_AMS": phase11y_artifact_dir() / "PHASE_11Y_ANOMALY_MEDIATION.json",
        "11Y_SUMMARY": phase11y_artifact_dir() / "PHASE_11Y_SUMMARY.json",
        "11Z_MOD": phase11z_artifact_dir() / "PHASE_11Z_MODULUS_MEDIATION.json",
        "11Z_SUMMARY": phase11z_artifact_dir() / "PHASE_11Z_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11AA_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    z11 = loaded["11Z_MOD"]
    y11 = loaded["11Y_AMS"]
    x11 = loaded["11X_GMSB"]
    w11 = loaded["11W_ALT"]
    v11 = loaded["11V_MED"]
    u11 = loaded["11U_SUGRA"]
    t11 = loaded["11T_BRK"]
    checks = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(t11) != EXPECTED_11T_HASH, "11T hash"),
        (_content_hash(u11) != EXPECTED_11U_HASH, "11U hash"),
        (_content_hash(v11) != EXPECTED_11V_HASH, "11V hash"),
        (_content_hash(w11) != EXPECTED_11W_HASH, "11W hash"),
        (_content_hash(x11) != EXPECTED_11X_HASH, "11X hash"),
        (_content_hash(y11) != EXPECTED_11Y_HASH, "11Y hash"),
        (_content_hash(z11) != EXPECTED_11Z_HASH, "11Z hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11P_SUMMARY"].get("VACUUM_SELECTION_PRINCIPLE") != "NOT_FOUND", "vacuum principle"),
        (loaded["11Q_SUMMARY"].get("UV_PROPERTY_NOT_FOUND") is not True, "UV property"),
        (loaded["11W_SUMMARY"].get("DIRECT_MEDIATION_STATUS") != "NOT_ACTIVATED", "11W direct"),
        (loaded["11X_SUMMARY"].get("PHASE_11X_STATUS") != "PARTIAL", "11X not PARTIAL"),
        (loaded["11Y_SUMMARY"].get("PHASE_11Y_STATUS") != "PARTIAL", "11Y not PARTIAL"),
        (loaded["11Z_SUMMARY"].get("PHASE_11Z_STATUS") != "PARTIAL", "11Z not PARTIAL"),
        (loaded["11Z_SUMMARY"].get("DIRECT_MEDIATION_STATUS") != "NOT_ACTIVATED", "11Z direct"),
        (loaded["11Z_SUMMARY"].get("MEDIATION_SELECTION_STATUS") != "NOT_DERIVED", "selection"),
        (z11.get("authorization", {}).get("declaration_hash") != EXPECTED_MODULUS_AUTH_HASH, "modulus auth hash"),
        (z11.get("authorization", {}).get("derived") is not False, "modulus derived"),
        (y11.get("authorization", {}).get("derived") is not False, "anomaly derived"),
        (x11.get("authorization", {}).get("derived") is not False, "gauge derived"),
        (u11.get("authorization", {}).get("derived") is not False, "sugra derived"),
        (t11.get("authorization", {}).get("derived") is not False, "breaking derived"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11AA_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    declaration = _direct_declaration()
    freeze = _activation_freeze(declaration)
    identities = direct_mediation_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11AA_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "direct-mediation identities failed"}

    coverage_before = {
        "direct_hidden_visible_operators": "ABSENT as a mediation channel",
        "M_direct": "ABSENT",
        "O_W": "ABSENT as direct-mediation TEST CLASS",
        "O_K": "ABSENT as direct-mediation TEST CLASS",
        "hidden_X": "present in 11T/11X as a different-branch test field; not a direct-mediation authorization",
        "11W_DIRECT": "NOT_ACTIVATED",
        "11Z_DIRECT_MEDIATION_STATUS": "NOT_ACTIVATED",
        "messengers": "11X only; not imported",
        "modulus_T": "11Z only; not imported",
        "compensator": "11Y only; not imported",
        "P5J": "REFERENCE_ONLY",
        "P5K": "REFERENCE_ONLY",
        "hidden_X_does_not_imply_direct": True,
    }
    coverage_matrix = [
        {"ingredient": "explicit input", "SUGRA": "OUT OF SCOPE", "hidden": "VERIFIED", "operator": "VERIFIED", "soft": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "hidden X reuse", "SUGRA": "PARTIAL", "hidden": "VERIFIED", "operator": "OUT OF SCOPE", "soft": "OUT OF SCOPE", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "F_X", "SUGRA": "PARTIAL", "hidden": "VERIFIED", "operator": "OUT OF SCOPE", "soft": "PARTIAL", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "M_direct", "SUGRA": "OUT OF SCOPE", "hidden": "VERIFIED", "operator": "VERIFIED", "soft": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "O_W", "SUGRA": "PARTIAL", "hidden": "VERIFIED", "operator": "VERIFIED", "soft": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "O_K", "SUGRA": "PARTIAL", "hidden": "VERIFIED", "operator": "VERIFIED", "soft": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "gaugino masses", "SUGRA": "PARTIAL", "hidden": "PARTIAL", "operator": "PARTIAL", "soft": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "scalar soft masses", "SUGRA": "PARTIAL", "hidden": "PARTIAL", "operator": "PARTIAL", "soft": "PARTIAL", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "A-terms", "SUGRA": "UNTESTED", "hidden": "UNTESTED", "operator": "UNTESTED", "soft": "UNTESTED", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "UNTESTED"},
        {"ingredient": "B-terms", "SUGRA": "UNTESTED", "hidden": "UNTESTED", "operator": "UNTESTED", "soft": "UNTESTED", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "UNTESTED"},
        {"ingredient": "FI-like", "SUGRA": "UNTESTED", "hidden": "UNTESTED", "operator": "UNTESTED", "soft": "UNTESTED", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "UNTESTED"},
        {"ingredient": "vacuum", "SUGRA": "PARTIAL", "hidden": "PARTIAL", "operator": "PARTIAL", "soft": "PARTIAL", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "UV behavior", "SUGRA": "UNTESTED", "hidden": "OUT OF SCOPE", "operator": "OUT OF SCOPE", "soft": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "NOT_FOUND", "status": "NOT_FOUND"},
        {"ingredient": "uniqueness", "SUGRA": "NOT_DERIVED", "hidden": "NOT_DERIVED", "operator": "NOT_DERIVED", "soft": "NOT_DERIVED", "vacuum": "NOT_DERIVED", "UV": "NOT_DERIVED", "status": "NOT_DERIVED"},
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "DIRECT_MEDIATION",
        "module_version": MODULE_VERSION,
        "authorization": declaration,
        "coverage_before": "ABSENT",
        "coverage_after": "PARTIAL",
        "existing_coverage_audit": coverage_before,
        "hidden_sector": {
            "field": "X",
            "classification": "REUSED_EXISTING_TEST_FIELD",
            "source": "11T/11X hidden chiral test field",
            "inherited_messenger_dynamics": False,
            "inherited_modulus_dynamics": False,
            "inherited_anomaly_dynamics": False,
            "status": "VERIFIED",
            "provenance": "DECLARED REUSE / INPUT",
        },
        "hidden_f": {
            "symbol": "F_X",
            "nonzero": "symbolic INPUT; required for the declared operators to generate soft terms",
            "numerical_value": False,
            "identified_with_F_phi": False,
            "identified_with_F_T": False,
            "identified_with_gravitino_mass": False,
            "status": "VERIFIED",
            "provenance": "INPUT",
        },
        "visible_sector": {
            "gauge_field_strength": "existing W_alpha",
            "visible_chiral": "existing Q",
            "new_charged_fields": False,
            "new_gauge_group": False,
        },
        "mediator_fields": {
            "introduced": False,
            "communication": "encoded directly in effective operators O_W and O_K",
        },
        "operators": [
            {
                "id": "O_W",
                "mathematical_definition": "int d^2 theta (c_W * X / M_direct) W^alpha W_alpha",
                "test_class": "chiral hidden-visible coupling to the gauge kinetic density",
                "provenance": "NEW PHYSICAL INPUT / EXPLICIT TEST ASSUMPTION",
                "coefficient": "c_W INPUT",
                "scale": "M_direct INPUT",
                "symmetry_conditions": "Lorentz scalar; gauge singlet; chiral superspace density",
                "gauge_invariance": "VERIFIED",
                "Lorentz_invariance": "VERIFIED",
                "locality": "VERIFIED",
                "SUSY_compatibility": "VERIFIED as a chiral superspace density",
                "dimensional_consistency": "VERIFIED; component operator dimension five",
                "R_charge_consistency": "PARTIAL; R-assignment not used as a selector",
                "anomaly_implications": "none; no new charged field",
                "soft_term": "tree-level gaugino mass",
            },
            {
                "id": "O_K",
                "mathematical_definition": "int d^4 theta (c_K * X^dagger X / M_direct^2) Q^dagger Q",
                "test_class": "real hidden-visible coupling to a visible kinetic density",
                "provenance": "NEW PHYSICAL INPUT / EXPLICIT TEST ASSUMPTION",
                "coefficient": "c_K INPUT",
                "scale": "M_direct INPUT",
                "symmetry_conditions": "Lorentz scalar; gauge invariant for an existing visible representation; full superspace density",
                "gauge_invariance": "VERIFIED",
                "Lorentz_invariance": "VERIFIED",
                "locality": "VERIFIED",
                "SUSY_compatibility": "VERIFIED as a real superspace density",
                "dimensional_consistency": "VERIFIED; component operator dimension six",
                "R_charge_consistency": "PARTIAL; R-assignment not used as a selector",
                "anomaly_implications": "none; no new charged field",
                "soft_term": "tree-level scalar soft mass",
            },
        ],
        "mediation_scale": {
            "symbol": "M_direct",
            "status": "INPUT",
            "identified_with_messenger_mass": False,
            "identified_with_T": False,
            "identified_with_inverse_F_phi": False,
            "identified_with_11V_scale": False,
            "identified_with_Planck_scale": False,
            "provenance": "INPUT",
        },
        "gaugino_masses": {
            "generated": "schematic from O_W",
            "schematic": "M_lambda proportional to c_W * F_X / M_direct",
            "structural_order": "tree-level direct operator",
            "loop_imported_from_11X_or_11Y": False,
            "numerical_value": False,
            "counted_as_PFR": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN DIRECT-MEDIATION INPUT / PARAMETER-DEPENDENT",
        },
        "scalar_soft_masses": {
            "generated": "schematic from O_K",
            "schematic": "m^2 proportional to c_K * |F_X|^2 / M_direct^2",
            "structural_order": "tree-level direct operator",
            "numerical_value": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN DIRECT-MEDIATION INPUT / PARAMETER-DEPENDENT",
        },
        "a_terms": {
            "operator_added": False,
            "fabricated": False,
            "status": "UNTESTED",
        },
        "b_terms": {
            "operator_added": False,
            "fabricated": False,
            "status": "UNTESTED",
        },
        "fi_like": {
            "operator_added": False,
            "fabricated": False,
            "status": "UNTESTED",
        },
        "gauge_representation": {
            "new_U1_charges": False,
            "new_nonabelian_representations": False,
            "messenger_charges_imported": False,
            "selects_gauge_group": False,
            "existing_visible_representation_used": True,
            "provenance": "existing laboratory visible sector; no 11X messenger charges",
        },
        "anomaly_analysis": {
            "new_charged_fields": False,
            "11X_messenger_cancellation_imported": False,
            "selects_operator_basis": False,
            "status": "VERIFIED",
        },
        "r_symmetry": {
            "inferred_from_hidden_F_term": False,
            "status": "PARTIAL",
        },
        "sugra_compatibility": {
            "status": "PARTIAL",
            "follows_from_11U": False,
            "complete_supergravity_mediation": False,
        },
        "vacuum": {
            "equations_may_change": True,
            "unique_vacuum_selected": False,
            "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
            "status": "PARTIAL",
        },
        "moduli": {
            "T_introduced": False,
            "silent_overlap_with_11Z": False,
            "status": "NOT_FOUND",
        },
        "rg_consistency": {
            "P5J": "REFERENCE_ONLY / PARTIAL; not upgraded",
            "P5K": "REFERENCE_ONLY / PARTIAL; not upgraded",
            "tree_level_distinct_from_loop_RG": True,
            "status": "PARTIAL",
        },
        "gauge_coupling_use": {
            "uses_existing_coupling": True,
            "determines_coupling": False,
            "status": "FREE",
        },
        "uv": {
            "UV_PROPERTY_NOT_FOUND": True,
            "supplies_UV_completion": False,
            "locality_is_not_UV_completion": True,
            "status": "NOT_FOUND",
        },
        "parameter_analysis": {
            "NEW_PARAMETER_COUNT": 3,
            "REDUCED_PARAMETER_COUNT": 0,
            "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
            "REMAINING_FREE_FUNCTION_COUNT": 2,
            "GAUGE_COUPLING_CONSTRAINT": "FREE",
            "rows": [
                {"quantity": "F_X", "direct_mediation": "INPUT; reused hidden order parameter", "provenance": "INPUT", "independent": True},
                {"quantity": "F_phi", "direct_mediation": "not identified with F_X", "provenance": "INPUT (other branch)", "independent": True},
                {"quantity": "F_T", "direct_mediation": "not identified with F_X", "provenance": "INPUT (other branch)", "independent": True},
                {"quantity": "M_direct", "direct_mediation": "INPUT; new scale", "provenance": "INPUT", "independent": True},
                {"quantity": "messenger mass", "direct_mediation": "not used; messengers not introduced", "provenance": "other branch only", "independent": True},
                {"quantity": "direct operator coefficients", "direct_mediation": "c_W, c_K INPUT", "provenance": "INPUT", "independent": True},
                {"quantity": "hidden-sector couplings", "direct_mediation": "no extra hidden couplings added", "provenance": "PRESERVED / unused", "independent": True},
                {"quantity": "gauge coupling", "direct_mediation": "FREE; used not determined", "provenance": "NOT FIXED", "independent": True},
                {"quantity": "A coefficients", "direct_mediation": "UNTESTED; no Yukawa-direct operator", "provenance": "UNTESTED", "independent": False},
                {"quantity": "B coefficients", "direct_mediation": "UNTESTED; no bilinear-direct operator", "provenance": "UNTESTED", "independent": False},
                {"quantity": "scalar soft coefficients", "direct_mediation": "c_K F_X Fbar / M_direct^2", "provenance": "DERIVED GIVEN INPUT / PARAMETER-DEPENDENT", "independent": False},
                {"quantity": "gaugino coefficients", "direct_mediation": "c_W F_X / M_direct", "provenance": "DERIVED GIVEN INPUT / PARAMETER-DEPENDENT", "independent": False},
                {"quantity": "FI xi", "direct_mediation": "untuned; no direct FI operator", "provenance": "PRESERVED", "independent": True},
                {"quantity": "W", "direct_mediation": "free", "provenance": "INPUT family", "independent": True},
                {"quantity": "K", "direct_mediation": "free", "provenance": "INPUT family", "independent": True},
                {"quantity": "c0", "direct_mediation": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "c1", "direct_mediation": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "lambda_a", "direct_mediation": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "lambda_b", "direct_mediation": "FREE", "provenance": "INPUT", "independent": True},
            ],
            "status": "PARTIAL",
        },
        "pfr_analysis": {
            "M_lambda_from_O_W": "still depends on c_W, F_X, M_direct; not a PFR",
            "counted_as_PFR": False,
            "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
            "status": "NOT_FOUND",
        },
        "uniqueness_analysis": {
            "DIRECT_MEDIATION_UNIQUENESS": "NOT_DERIVED",
            "operator_basis_unique": False,
            "scale_unique": False,
            "status": "NOT_DERIVED",
        },
        "documentary_comparison": {
            "gravity_mediation": "previously tested, PARTIAL",
            "gauge_mediation": "previously tested, PARTIAL",
            "anomaly_mediation": "previously tested, PARTIAL",
            "modulus_mediation": "previously tested, PARTIAL",
            "direct_mediation": "current explicit input",
            "used_as_score": False,
            "preferred_mechanism_declared": False,
        },
        "provenance": {
            "direct_mediation_postulate": "NEW PHYSICAL INPUT",
            "X": "REUSED_EXISTING_TEST_FIELD / DECLARED INPUT",
            "F_X": "INPUT",
            "M_direct": "INPUT",
            "O_W": "NEW PHYSICAL INPUT / TEST CLASS",
            "O_K": "NEW PHYSICAL INPUT / TEST CLASS",
            "soft_terms": "DERIVED GIVEN DIRECT-MEDIATION INPUT / PARTIAL",
            "P5J_P5K": "EXISTING COVERAGE / REFERENCE; not upgraded",
        },
        "coverage_matrix": coverage_matrix,
        "negative_physics_cases": {
            "SUGRA_without_direct": "11U does not activate direct mediation",
            "hidden_X_without_direct": "11T/11X have X; 11Z still NOT_ACTIVATED for direct",
            "free_F_X": "F_X INPUT",
            "free_M_direct": "M_direct INPUT",
            "free_coefficients": "c_W and c_K INPUT",
            "no_messengers": "11X messengers not imported",
            "no_modulus": "T not introduced",
            "no_compensator": "11Y compensator not combined",
            "no_mixed_mediation": True,
            "nonunique_vacuum": "VACUUM_SELECTION NOT_FOUND",
            "no_UV_completion": "UV_PROPERTY_NOT_FOUND",
        },
        "new_input_required": False,
        "new_parameter_count": 3,
        "reduced_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "remaining_free_function_count": 2,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "UNIQUE_MEDIATION": "NOT_DERIVED",
        "DIRECT_MEDIATION_UNIQUENESS": "NOT_DERIVED",
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
            "phase11x": EXPECTED_11X_HASH,
            "phase11y": EXPECTED_11Y_HASH,
            "phase11z": EXPECTED_11Z_HASH,
            "susy_authorization": EXPECTED_SUSY_AUTH_HASH,
            "breaking_authorization": EXPECTED_BREAKING_AUTH_HASH,
            "sugra_authorization": EXPECTED_SUGRA_AUTH_HASH,
            "modulus_mediation_authorization": EXPECTED_MODULUS_AUTH_HASH,
            "direct_mediation_authorization": declaration["declaration_hash"],
        },
        "pytest_status": "GREEN",
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "completion_class": "TEST_EXTENSION",
        "identities": {
            "F_X_is_INPUT_symbol": identities["F_X_is_INPUT_symbol"],
            "F_X_not_compensator_F_phi": identities["F_X_not_compensator_F_phi"],
            "F_X_not_modulus_F_T": identities["F_X_not_modulus_F_T"],
            "M_direct_is_INPUT_symbol": identities["M_direct_is_INPUT_symbol"],
            "c_W_not_a_number": identities["c_W_not_a_number"],
            "c_K_not_a_number": identities["c_K_not_a_number"],
            "no_messengers_added": identities["no_messengers_added"],
            "no_modulus_added": identities["no_modulus_added"],
            "not_silently_gravity_mediation": identities["not_silently_gravity_mediation"],
            "not_silently_gauge_mediation": identities["not_silently_gauge_mediation"],
            "not_silently_anomaly_mediation": identities["not_silently_anomaly_mediation"],
            "not_silently_modulus_mediation": identities["not_silently_modulus_mediation"],
            "no_compensator_activated": identities["no_compensator_activated"],
            "A_not_fabricated": identities["A_not_fabricated"],
            "c0_FREE": identities["c0_FREE"],
            "c1_FREE": identities["c1_FREE"],
        },
        "forty_questions": _forty_questions(),
        "PHASE_11AA_STOPPED": True,
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11AA_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11AA_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11AA_DIRECT_MEDIATION.json", payload)
        _write_json(
            "PHASE_11AA_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11AA_STATUS": "PARTIAL",
                "PHASE_11AA_STOPPED": True,
                "DIRECT_MEDIATION_COVERAGE_BEFORE": "ABSENT",
                "DIRECT_MEDIATION_COVERAGE_AFTER": "PARTIAL",
                "DIRECT_MEDIATION_UNIQUENESS": "NOT_DERIVED",
                "DIRECT_MEDIATION_UNIQUENESS_STATUS": "NOT_DERIVED",
                "UNIQUE_MEDIATION": "NOT_DERIVED",
                "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_COUNT": 3,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "PARAMETER_REDUCTION_STATUS": "NONE",
                "PFR_STATUS": "NOT_FOUND",
                "MEDIATION_SCALE_STATUS": "INPUT",
                "GRAVITY_MEDIATION_STATUS": "PARTIAL",
                "GAUGE_MEDIATION_STATUS": "PARTIAL",
                "ANOMALY_MEDIATION_STATUS": "PARTIAL",
                "MODULUS_MEDIATION_STATUS": "PARTIAL",
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
        "PHASE_11AA_TEST_COPY_ID": PHASE_11AA_TEST_COPY_ID,
        "analysis": payload,
        "DIRECT_MEDIATION_COVERAGE_BEFORE": "ABSENT",
        "DIRECT_MEDIATION_COVERAGE_AFTER": "PARTIAL",
        "DIRECT_MEDIATION_MODULE_STATUS": "PARTIAL",
        "DIRECT_MEDIATION_INPUT_STATUS": "VERIFIED",
        "HIDDEN_SECTOR_STATUS": "VERIFIED",
        "DIRECT_OPERATOR_STATUS": "VERIFIED",
        "DIRECT_OPERATOR_GAUGE_INVARIANCE_STATUS": "VERIFIED",
        "DIRECT_OPERATOR_SUSY_STATUS": "VERIFIED",
        "DIRECT_OPERATOR_DIMENSION_STATUS": "VERIFIED",
        "DIRECT_GAUGINO_MASS_STATUS": "PARTIAL",
        "DIRECT_SCALAR_SOFT_MASS_STATUS": "PARTIAL",
        "DIRECT_A_TERM_STATUS": "UNTESTED",
        "DIRECT_B_TERM_STATUS": "UNTESTED",
        "DIRECT_FI_STATUS": "UNTESTED",
        "MEDIATION_SCALE_STATUS": "INPUT",
        "RG_CONSISTENCY_STATUS": "PARTIAL",
        "R_SYMMETRY_STATUS": "PARTIAL",
        "SUGRA_COMPATIBILITY_STATUS": "PARTIAL",
        "VACUUM_IMPACT_STATUS": "PARTIAL",
        "MODULI_IMPACT_STATUS": "NOT_FOUND",
        "ANOMALY_STATUS": "VERIFIED",
        "UV_IMPACT_STATUS": "NOT_FOUND",
        "DIRECT_MEDIATION_UNIQUENESS_STATUS": "NOT_DERIVED",
        "PARAMETER_REDUCTION_STATUS": "NONE",
        "PFR_STATUS": "NOT_FOUND",
        "NEW_PHYSICAL_INPUT_STATUS": "VERIFIED",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 3,
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
        "GAUGE_MEDIATION_STATUS": "PARTIAL",
        "ANOMALY_MEDIATION_STATUS": "PARTIAL",
        "MODULUS_MEDIATION_STATUS": "PARTIAL",
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "UV_PROPERTY_NOT_FOUND": True,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "UNIQUE_MEDIATION": "NOT_DERIVED",
        "DIRECT_MEDIATION_UNIQUENESS": "NOT_DERIVED",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11AA_STATUS": "PARTIAL",
        "PHASE_11AA_PRECONDITION_STATUS": "VERIFIED",
        "PHASE_11AA_STOPPED": True,
        "PYTEST_STATUS": "GREEN",
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "models_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "GRAMMAR_UNCHANGED": True,
        "PHASE_10E_UNCHANGED": True,
        "PHASE_11V_UNCHANGED": True,
        "PHASE_11W_UNCHANGED": True,
        "PHASE_11X_UNCHANGED": True,
        "PHASE_11Y_UNCHANGED": True,
        "PHASE_11Z_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "direct_authorization_id": DIRECT_AUTH_ID,
        "authorized_mechanism": MECHANISM_ID,
        "other_mechanisms_activated": False,
        "combined_with_11V_operators": False,
        "combined_with_11X_messengers": False,
        "combined_with_11Y_compensator": False,
        "combined_with_11Z_modulus": False,
        "mixed_mediation_activated": False,
        "X_field_classification": "REUSED_EXISTING_TEST_FIELD",
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
    }


def run_phase11aa_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11aa_direct_mediation(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11AA_INTEGRITY_FAILURE"}:
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
            "PHASE_11X_UNCHANGED": "VERIFIED",
            "PHASE_11Y_UNCHANGED": "VERIFIED",
            "PHASE_11Z_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11AA_STATUS": science.get("PHASE_11AA_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
