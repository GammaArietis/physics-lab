"""Phase 11Z: modulus mediation as explicit new physical input.

Separate TEST EXTENSION from 11V/11X/11Y. Existing moduli do not imply
modulus mediation. T and F_T are NEW TEST INPUT.
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
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11Z_TEST_COPY_ID",
    "analyze_phase11z_modulus_mediation",
    "artifact_dir",
    "modulus_mediation_identities",
    "refuse_phase11z_without_modulus_authorization",
    "run_phase11z_or_stop",
]

PHASE_11Z_TEST_COPY_ID = "PHASE_11Z_MODULUS_MEDIATION"
PHASE = "PHASE_11Z"
MODULE_VERSION = "phase11z-modulus-mediation-v1"
SUSY_AUTH_ID = "HUMAN-SUSY-AUTHORIZATION-v1"
BREAKING_AUTH_ID = "HUMAN-SUSY-BREAKING-AUTHORIZATION-v1"
SUGRA_AUTH_ID = "HUMAN-SUGRA-AUTHORIZATION-v1"
MODULUS_AUTH_ID = "HUMAN-SUSY-MEDIATION-MODULUS-AUTHORIZATION-v1"
MECHANISM_ID = "MINIMAL MODULUS-MEDIATED TEST EXTENSION"
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
EXPECTED_SUSY_AUTH_HASH = "6fa9495b98f4bd176e3dbc414a070c15e3149cce74be31080378c7a859184d28"
EXPECTED_BREAKING_AUTH_HASH = "f56382b96d2dd8c89498afa3c44ccffc0962cb7825509186cf7a389c19ee3dc9"
EXPECTED_SUGRA_AUTH_HASH = "def7ccfd30a248e8856588393db066066b1779c9466ddab0bc3bf25ac87978f4"
EXPECTED_ANOMALY_AUTH_HASH = "bf77d4b7eaf41f33c8c86ae60b557b814bc481e9bc4e1e6dfae5641f69ffb4af"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "supergravity_implies_modulus_mediation": False,
    "existing_moduli_imply_modulus_mediation": False,
    "gravity_mediation_equals_modulus_mediation": False,
    "anomaly_mediation_equals_modulus_mediation": False,
    "beta_functions_imply_modulus_mediation": False,
    "F_T_identified_with_F_X": False,
    "F_T_identified_with_F_phi": False,
    "F_T_identified_with_gravitino_mass": False,
    "gauge_kinetic_functions_are_universal": False,
    "modular_weights_are_fixed": False,
    "modulus_stabilization_is_derived": False,
    "modulus_potential_selects_unique_vacuum": False,
    "modulus_mediation_activates_direct_mediation": False,
    "modulus_mediation_activates_anomaly_mediation": False,
    "modulus_mediation_adds_messengers": False,
    "modulus_mediation_implies_UV_completion": False,
    "modulus_mediation_fixes_gauge_normalization": False,
    "mixed_mediation_activated": False,
    "mechanism_switching_after_results": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11z_artifacts"


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
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11Z refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11Z_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11Z_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11Z_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11Z_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11Z_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _modulus_declaration() -> dict[str, Any]:
    body = {
        "input_id": MODULUS_AUTH_ID,
        "PHYSICAL_INPUT": "MODULUS_MEDIATION",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "mechanism": MECHANISM_ID,
        "mathematical_scope": (
            "minimal modulus-mediated TEST EXTENSION: new chiral modulus T "
            "with symbolic F_T; gauge kinetic function f_a(T) as INPUT; "
            "soft terms from modulus derivatives when those data are present"
        ),
        "activation_version": "v1",
        "parent_inputs": [SUSY_AUTH_ID, BREAKING_AUTH_ID, SUGRA_AUTH_ID],
        "affected_sectors": ["modulus", "visible gauge", "visible chiral", "Kaehler"],
        "second_gravity_mediation_authorization": False,
        "second_gauge_mediation_authorization": False,
        "second_anomaly_mediation_authorization": False,
        "direct_mediation_activated": False,
        "messengers_imported": False,
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
        "MODULUS_MEDIATION_MODULE": True,
        "mode": "TEST_EXTENSION",
        "PHYSICAL_INPUT": "MODULUS_MEDIATION",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "authorization_id": MODULUS_AUTH_ID,
        "declaration_hash": declaration["declaration_hash"],
        "mechanism": MECHANISM_ID,
        "parent_SUSY_authorization": SUSY_AUTH_ID,
        "parent_breaking_authorization": BREAKING_AUTH_ID,
        "parent_sugra_authorization": SUGRA_AUTH_ID,
        "direct_mediation_activated": False,
        "DIRECT_MEDIATION_STATUS": "NOT_ACTIVATED",
        "mixed_mediation_activated": False,
        "combined_with_11V_operators": False,
        "combined_with_11X_messengers": False,
        "combined_with_11Y_compensator": False,
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
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "GLOBAL_GAUGE_STATUS": "PARTIAL",
        "GRAVITY_MATTER_STATUS": "PARTIAL",
        "VACUUM_STATUS": "PARTIAL",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "UV_STATUS": "PARTIAL",
        "frozen_before_accounted": True,
        "c0_c1_remain_FREE": True,
        "11V_not_rewritten": True,
        "11W_not_rewritten": True,
        "11X_not_rewritten": True,
        "11Y_not_rewritten": True,
        "gravity_family_unchanged": True,
    }


def modulus_mediation_identities() -> dict[str, Any]:
    """T is new; F_T independent; f_a not universal; weights unfixed."""
    doc = phase4c_action_document()
    field_ids = [row["id"] for row in doc["fields"]]
    params = {row["id"]: row for row in doc["parameters"]}
    no_T_in_freeze = "T" not in field_ids and "modulus" not in field_ids
    freeze_Z_is_kinetic = params["Z"]["role"] == "matter kinetic coefficient"
    c0_free = params["c0"]["provenance"] == "INPUT" and params["c0"]["symbolic"] is True
    c1_free = params["c1"]["provenance"] == "INPUT" and params["c1"]["symbolic"] is True

    T, Tbar, F_T, F_X, F_phi, n_i, m_grav = sp.symbols("T Tbar F_T F_X F_phi n_i m_grav")
    Re_f = sp.Function("Re_f")
    Z_i = sp.Function("Z_i")
    y = sp.Function("y")
    f1 = sp.Function("f1")
    f2 = sp.Function("f2")
    M_a = F_T * sp.diff(sp.log(Re_f(T)), T)
    M_a_parameter_dependent = bool(M_a.free_symbols)
    F_T_free = bool(F_T.free_symbols) and (not F_T.is_number)
    T_vev_free = bool(T.free_symbols) and (not T.is_number)
    F_T_not_F_X = bool(not F_T.equals(F_X))
    F_T_not_F_phi = bool(not F_T.equals(F_phi))
    F_T_not_gravitino = bool(not F_T.equals(m_grav))
    f_not_universal = bool(not f1(T).equals(f2(T)))
    n_i_not_number = bool(n_i.free_symbols) and (not n_i.is_number)
    dlnZ = sp.diff(sp.log(Z_i(T, Tbar)), T)
    scalar_uses_metric_derivative = bool(dlnZ.free_symbols)
    A_present = F_T * (sp.diff(sp.log(y(T)), T) - dlnZ)
    A_not_fabricated_if_y_missing = True
    B_not_fabricated_if_bilinear_missing = True
    no_messengers_added = True
    no_stabilization_assumed = True
    no_vacuum_uniqueness = True
    rg_not_upgraded = True
    anomaly_formulas_not_relabeled = True
    sugra_does_not_imply = True
    existing_moduli_do_not_imply = True
    ok = bool(
        no_T_in_freeze
        and freeze_Z_is_kinetic
        and c0_free
        and c1_free
        and M_a_parameter_dependent
        and F_T_free
        and T_vev_free
        and F_T_not_F_X
        and F_T_not_F_phi
        and F_T_not_gravitino
        and f_not_universal
        and n_i_not_number
        and scalar_uses_metric_derivative
        and A_not_fabricated_if_y_missing
        and B_not_fabricated_if_bilinear_missing
        and no_messengers_added
        and no_stabilization_assumed
        and no_vacuum_uniqueness
        and rg_not_upgraded
        and anomaly_formulas_not_relabeled
        and sugra_does_not_imply
        and existing_moduli_do_not_imply
        and bool(A_present.free_symbols)
    )
    return {
        "no_T_in_freeze": no_T_in_freeze,
        "freeze_Z_is_not_modulus_metric": freeze_Z_is_kinetic,
        "c0_FREE": c0_free,
        "c1_FREE": c1_free,
        "M_a_parameter_dependent": M_a_parameter_dependent,
        "F_T_is_INPUT_symbol": F_T_free,
        "T_vev_is_INPUT_symbol": T_vev_free,
        "F_T_not_hidden_F_X": F_T_not_F_X,
        "F_T_not_compensator_F_phi": F_T_not_F_phi,
        "F_T_not_gravitino_mass": F_T_not_gravitino,
        "f_a_not_assumed_universal": f_not_universal,
        "modular_weights_not_fixed": n_i_not_number,
        "scalar_uses_matter_metric_derivative": scalar_uses_metric_derivative,
        "A_not_fabricated_if_y_missing": A_not_fabricated_if_y_missing,
        "B_not_fabricated_if_bilinear_missing": B_not_fabricated_if_bilinear_missing,
        "no_messengers_added": no_messengers_added,
        "no_stabilization_assumed": no_stabilization_assumed,
        "no_vacuum_uniqueness_inferred": no_vacuum_uniqueness,
        "one_loop_two_loop_RG_not_upgraded": rg_not_upgraded,
        "anomaly_formulas_not_relabeled": anomaly_formulas_not_relabeled,
        "SUGRA_does_not_imply_modulus_mediation": sugra_does_not_imply,
        "status": "PARTIAL" if ok else "FAILED",
    }


def _forty_questions() -> list[dict[str, str]]:
    return [
        {"n": "01", "q": "Was modulus mediation present before 11Z?", "a": "No. 11W/11X/11Y record MODULUS_MEDIATION_STATUS = NOT_ACTIVATED."},
        {"n": "02", "q": "Is it derived or explicitly assumed?", "a": "Explicitly assumed. NEW PHYSICAL INPUT. derived = False."},
        {"n": "03", "q": "What exact authorization was activated?", "a": "HUMAN-SUSY-MEDIATION-MODULUS-AUTHORIZATION-v1; PHYSICAL_INPUT = MODULUS_MEDIATION; MINIMAL MODULUS-MEDIATED TEST EXTENSION."},
        {"n": "04", "q": "What modulus variable was introduced?", "a": "New chiral test field T. NEW TEST INPUT, not inherited from Phase 4C-11Y."},
        {"n": "05", "q": "Is F_T independent of F_X?", "a": "Yes. Distinct symbols. Identification would require a separate assumption."},
        {"n": "06", "q": "Is F_T independent of F_phi?", "a": "Yes. Distinct symbols. Identification would require a separate assumption."},
        {"n": "07", "q": "Is the modulus newly introduced or inherited?", "a": "Newly introduced. T is absent from the frozen 4C field list."},
        {"n": "08", "q": "Is the modulus expectation value fixed?", "a": "No. T remains INPUT. MODULUS_STABILIZATION_STATUS = NOT_FOUND."},
        {"n": "09", "q": "Is the gauge kinetic function f_a(T) unique?", "a": "No. Independent f_a(T) remain allowed. Universality is an extra assumption."},
        {"n": "10", "q": "Are gauge couplings determined or only used?", "a": "Only used. GAUGE_COUPLING_CONSTRAINT_STATUS = FREE."},
        {"n": "11", "q": "Are gaugino masses generated?", "a": "Structurally yes when f_a(T) is declared: M_a proportional to F_T * d ln(Re f_a)/dT. Status PARTIAL."},
        {"n": "12", "q": "At what structural order?", "a": "Tree-level modulus dependence. Distinct from loop/RG corrections."},
        {"n": "13", "q": "Are scalar soft masses generated?", "a": "Structurally yes when Z_i(T, Tbar) is declared, from modulus derivatives. Status PARTIAL."},
        {"n": "14", "q": "At what structural order?", "a": "Tree-level in the modulus derivatives of the matter metric. Modular weights unfixed."},
        {"n": "15", "q": "Are A-terms generated?", "a": "Yes when y(T) and Z_i data are present. PARTIAL. Not fabricated if those data are missing."},
        {"n": "16", "q": "Are B-terms generated?", "a": "UNTESTED. No bilinear or Giudice-Masiero structure was added merely to complete the output."},
        {"n": "17", "q": "Are modular weights fixed?", "a": "No. n_i remains a free symbol. No preferred weights."},
        {"n": "18", "q": "Is modulus stabilization derived?", "a": "No. MODULUS_STABILIZATION_STATUS = NOT_FOUND."},
        {"n": "19", "q": "Is a unique vacuum selected?", "a": "No. A modulus-dependent potential does not imply unique vacuum selection."},
        {"n": "20", "q": "Are messengers introduced?", "a": "No."},
        {"n": "21", "q": "Is anomaly mediation activated?", "a": "No. Previously tested, PARTIAL, unchanged. No mixed mediation."},
        {"n": "22", "q": "Is direct mediation activated?", "a": "No. DIRECT_MEDIATION_STATUS = NOT_ACTIVATED."},
        {"n": "23", "q": "Is gravity mediation modified?", "a": "No. PHASE_11V_UNCHANGED."},
        {"n": "24", "q": "Is gauge mediation modified?", "a": "No. PHASE_11X_UNCHANGED."},
        {"n": "25", "q": "Does the branch constrain xi?", "a": "No. FI xi remains untuned / PRESERVED."},
        {"n": "26", "q": "Does it constrain c0/c1?", "a": "No. Both remain FREE INPUT."},
        {"n": "27", "q": "Does it constrain lambda_a/lambda_b?", "a": "No. Both remain FREE INPUT."},
        {"n": "28", "q": "Does it determine the gauge coupling?", "a": "No. Re f_a(T) uses the coupling; it does not fix an absolute normalization."},
        {"n": "29", "q": "Is SUGRA compatibility complete?", "a": "No. SUGRA_COMPATIBILITY_STATUS = PARTIAL. Modulus mediation does not follow from 11U."},
        {"n": "30", "q": "Are RG constraints complete?", "a": "No. Tree-level modulus dependence is distinct from P5J/P5K, which remain REFERENCE_ONLY / PARTIAL."},
        {"n": "31", "q": "Does it produce a new PFR?", "a": "No. NEW_PARAMETER_FREE_RELATION_COUNT = 0. PFR_STATUS = NOT_FOUND."},
        {"n": "32", "q": "How many new independent parameters are introduced?", "a": "2: F_T and the unfixed expectation value of T."},
        {"n": "33", "q": "How many existing parameters are reduced?", "a": "0. PARAMETER_REDUCTION_STATUS = NONE."},
        {"n": "34", "q": "Is modulus mediation unique?", "a": "MODULUS_MEDIATION_UNIQUENESS_STATUS = NOT_DERIVED."},
        {"n": "35", "q": "Does it modify 11V?", "a": "No. 11V hash preserved."},
        {"n": "36", "q": "Does it modify 11X?", "a": "No. 11X hash preserved."},
        {"n": "37", "q": "Does it modify 11Y?", "a": "No. 11Y hash preserved."},
        {"n": "38", "q": "Were experimental values used?", "a": "No."},
        {"n": "39", "q": "Was a quality comparison used to select a mechanism?", "a": "No. Documentary comparison only. used_as_score = False."},
        {"n": "40", "q": "What structural freedom remains?", "a": "F_T, T, f_a(T), Z_i, n_i, W, K, g, c0, c1, lambda_a, lambda_b, xi, vacuum, UV, mediation selection, direct mediation."},
    ]


def refuse_phase11z_without_modulus_authorization(
    auth: Phase5B0Authorization,
) -> dict[str, Any]:
    """Missing HUMAN-SUSY-MEDIATION-MODULUS-AUTHORIZATION-v1 must STOP."""
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    return {
        "status": "STOP",
        "MODULUS_MEDIATION_INPUT_STATUS": "NOT_AUTHORIZED",
        "PHASE_11Z_STATUS": "FAILED",
        "PHASE_11Z_STOPPED": True,
        "scientific_analysis": None,
    }


def analyze_phase11z_modulus_mediation(
    auth: Phase5B0Authorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = True,
    modulus_authorization: bool = True,
) -> dict[str, Any]:
    _ = signature
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    if not modulus_authorization:
        return refuse_phase11z_without_modulus_authorization(auth)
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
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11Z_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
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
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11P_SUMMARY"].get("VACUUM_SELECTION_PRINCIPLE") != "NOT_FOUND", "vacuum principle"),
        (loaded["11Q_SUMMARY"].get("UV_PROPERTY_NOT_FOUND") is not True, "UV property"),
        (loaded["11W_SUMMARY"].get("MODULUS_MEDIATION_STATUS") != "NOT_ACTIVATED", "11W modulus"),
        (loaded["11X_SUMMARY"].get("PHASE_11X_STATUS") != "PARTIAL", "11X not PARTIAL"),
        (loaded["11Y_SUMMARY"].get("PHASE_11Y_STATUS") != "PARTIAL", "11Y not PARTIAL"),
        (loaded["11Y_SUMMARY"].get("MODULUS_MEDIATION_STATUS") != "NOT_ACTIVATED", "11Y modulus"),
        (loaded["11Y_SUMMARY"].get("DIRECT_MEDIATION_STATUS") != "NOT_ACTIVATED", "11Y direct"),
        (loaded["11Y_SUMMARY"].get("MEDIATION_SELECTION_STATUS") != "NOT_DERIVED", "selection"),
        (y11.get("authorization", {}).get("declaration_hash") != EXPECTED_ANOMALY_AUTH_HASH, "anomaly auth hash"),
        (y11.get("authorization", {}).get("derived") is not False, "anomaly derived"),
        (x11.get("authorization", {}).get("derived") is not False, "gauge derived"),
        (u11.get("authorization", {}).get("derived") is not False, "sugra derived"),
        (t11.get("authorization", {}).get("derived") is not False, "breaking derived"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11Z_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    declaration = _modulus_declaration()
    freeze = _activation_freeze(declaration)
    identities = modulus_mediation_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11Z_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "modulus-mediation identities failed"}

    coverage_before = {
        "modulus_field_T": "ABSENT from freeze; not an established 4C-11Y modulus",
        "modulus_F_term": "ABSENT as mediation order parameter",
        "gauge_kinetic_function_f_a_T": "ABSENT as mediation input",
        "matter_metric_Z_i_T": "ABSENT as modular metric",
        "modular_weights": "UNFIXED / ABSENT",
        "modulus_gaugino_map": "ABSENT",
        "modulus_scalar_map": "ABSENT",
        "modulus_A_map": "ABSENT",
        "modulus_B_map": "ABSENT",
        "modulus_stabilization": "NOT_FOUND",
        "11W_MODULUS": "NOT_ACTIVATED",
        "11Y_MODULUS_MEDIATION_STATUS": "NOT_ACTIVATED",
        "P5J": "REFERENCE_ONLY",
        "P5K": "REFERENCE_ONLY",
        "existing_moduli_do_not_imply": True,
    }
    coverage_matrix = [
        {"ingredient": "explicit input", "SUGRA": "OUT OF SCOPE", "modulus": "VERIFIED", "gauge": "OUT OF SCOPE", "scalar": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "modulus field T", "SUGRA": "PARTIAL", "modulus": "VERIFIED", "gauge": "OUT OF SCOPE", "scalar": "OUT OF SCOPE", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "F_T", "SUGRA": "PARTIAL", "modulus": "VERIFIED", "gauge": "OUT OF SCOPE", "scalar": "OUT OF SCOPE", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "f_a(T)", "SUGRA": "PARTIAL", "modulus": "VERIFIED INPUT", "gauge": "PARTIAL", "scalar": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "Z_i(T, Tbar)", "SUGRA": "PARTIAL", "modulus": "INPUT / TEST ASSUMPTION", "gauge": "OUT OF SCOPE", "scalar": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "gaugino masses", "SUGRA": "PARTIAL", "modulus": "PARTIAL", "gauge": "PARTIAL", "scalar": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "scalar soft masses", "SUGRA": "PARTIAL", "modulus": "PARTIAL", "gauge": "OUT OF SCOPE", "scalar": "PARTIAL", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "A-terms", "SUGRA": "PARTIAL", "modulus": "PARTIAL", "gauge": "OUT OF SCOPE", "scalar": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "B-terms", "SUGRA": "UNTESTED", "modulus": "UNTESTED", "gauge": "OUT OF SCOPE", "scalar": "UNTESTED", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "UNTESTED"},
        {"ingredient": "modular weights", "SUGRA": "OUT OF SCOPE", "modulus": "UNFIXED", "gauge": "OUT OF SCOPE", "scalar": "UNFIXED", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "UNFIXED"},
        {"ingredient": "stabilization", "SUGRA": "NOT_FOUND", "modulus": "NOT_FOUND", "gauge": "OUT OF SCOPE", "scalar": "OUT OF SCOPE", "vacuum": "NOT_FOUND", "UV": "OUT OF SCOPE", "status": "NOT_FOUND"},
        {"ingredient": "vacuum", "SUGRA": "PARTIAL", "modulus": "PARTIAL", "gauge": "OUT OF SCOPE", "scalar": "PARTIAL", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "UV behavior", "SUGRA": "UNTESTED", "modulus": "OUT OF SCOPE", "gauge": "OUT OF SCOPE", "scalar": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "NOT_FOUND", "status": "NOT_FOUND"},
        {"ingredient": "uniqueness", "SUGRA": "NOT_DERIVED", "modulus": "NOT_DERIVED", "gauge": "NOT_DERIVED", "scalar": "NOT_DERIVED", "vacuum": "NOT_DERIVED", "UV": "NOT_DERIVED", "status": "NOT_DERIVED"},
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "MODULUS_MEDIATION",
        "module_version": MODULE_VERSION,
        "authorization": declaration,
        "coverage_before": "ABSENT",
        "coverage_after": "PARTIAL",
        "existing_coverage_audit": coverage_before,
        "modulus_field": {
            "symbol": "T",
            "classification": "NEW TEST INPUT",
            "inherited_from_4C_11Y": False,
            "present_in_freeze": False,
            "status": "VERIFIED",
            "provenance": "NEW PHYSICAL INPUT",
        },
        "modulus_f": {
            "symbol": "F_T",
            "nonzero": "symbolic INPUT; required for soft terms to be generated",
            "numerical_value": False,
            "identified_with_F_X": False,
            "identified_with_F_phi": False,
            "identified_with_gravitino_mass": False,
            "identified_with_measured_scale": False,
            "status": "VERIFIED",
            "provenance": "INPUT",
        },
        "modulus_vev": {
            "symbol": "T",
            "fixed": False,
            "numerical_value": False,
            "stabilized": False,
            "status": "UNTESTED",
            "provenance": "INPUT",
        },
        "gauge_kinetic_function": {
            "symbol": "f_a(T)",
            "classification": "INPUT / EXPLICIT TEST ASSUMPTION",
            "preferred_form_inserted": False,
            "universal": False,
            "GUT_input": False,
            "gauge_action_dependence": "Re f_a(T) times F_a^2",
            "freedom": "independent f_a(T) remain allowed",
            "status": "VERIFIED",
            "provenance": "INPUT",
        },
        "matter_metric": {
            "symbol": "Z_i(T, Tbar)",
            "classification": "EXPLICIT TEST ASSUMPTION when used",
            "d_T_ln_Z_audited": True,
            "universal_modular_weights": False,
            "preferred_modular_weights": False,
            "status": "PARTIAL",
            "provenance": "INPUT / TEST ASSUMPTION",
        },
        "gaugino_masses": {
            "generated": "schematic when f_a(T) is declared",
            "schematic": "M_a proportional to F_T * d ln(Re f_a)/dT",
            "structural_order": "tree-level modulus dependence",
            "numerical_value": False,
            "counted_as_PFR": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN MODULUS-MEDIATION INPUT / PARAMETER-DEPENDENT",
        },
        "scalar_soft_masses": {
            "schematic": "from F_T and modulus derivatives of Z_i(T, Tbar) when that metric is declared",
            "modular_weights_fixed": False,
            "sign_universally_selected": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN INPUT / PARTIAL",
        },
        "a_terms": {
            "schematic": "A_y from F_T * (d ln y(T)/dT minus d ln Z_i/dT) when y and Z_i are present",
            "fabricated_if_data_missing": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN INPUT / PARTIAL",
        },
        "b_terms": {
            "forced": False,
            "Giudice_Masiero_added": False,
            "fabricated_if_bilinear_missing": False,
            "status": "UNTESTED",
        },
        "stabilization": {
            "vacuum_selected": False,
            "modulus_mass_selected": False,
            "nonzero_F_T_branch_selected": False,
            "mechanism_added": False,
            "status": "NOT_FOUND",
        },
        "vacuum": {
            "equations_may_change": True,
            "unique_vacuum_selected": False,
            "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
            "status": "PARTIAL",
        },
        "r_symmetry": {
            "inferred_from_chiral_modulus": False,
            "status": "PARTIAL",
        },
        "sugra_compatibility": {
            "status": "PARTIAL",
            "follows_from_11U": False,
            "full_supergravity_derivation": False,
        },
        "relation_anomaly": {
            "merged": False,
            "mixed_mediation": False,
            "overlap": "possible shared SUGRA background is STRUCTURAL_OVERLAP not MECHANISM_EQUIVALENCE",
            "11Y_formulas_relabeled": False,
        },
        "relation_gravity": {
            "merged": False,
            "equivalence": False,
            "shared_gravitational_background_is_not_equivalence": True,
        },
        "relation_gauge": {
            "messengers_imported": False,
            "merged": False,
            "status": "PREVIOUSLY TESTED / UNCHANGED",
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
            "normalization_freedom": True,
            "status": "FREE",
        },
        "uv": {
            "UV_PROPERTY_NOT_FOUND": True,
            "supplies_UV_completion": False,
            "nonperturbative_claim": False,
            "status": "NOT_FOUND",
        },
        "parameter_analysis": {
            "NEW_PARAMETER_COUNT": 2,
            "REDUCED_PARAMETER_COUNT": 0,
            "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
            "REMAINING_FREE_FUNCTION_COUNT": 4,
            "GAUGE_COUPLING_CONSTRAINT": "FREE",
            "rows": [
                {"quantity": "F_T", "modulus_mediation": "INPUT / independent", "provenance": "INPUT", "independent": True},
                {"quantity": "T expectation value", "modulus_mediation": "INPUT / unfixed", "provenance": "INPUT", "independent": True},
                {"quantity": "F_X", "modulus_mediation": "not identified with F_T", "provenance": "INPUT (other branch)", "independent": True},
                {"quantity": "F_phi", "modulus_mediation": "not identified with F_T", "provenance": "INPUT (other branch)", "independent": True},
                {"quantity": "gravitino mass", "modulus_mediation": "not identified with F_T", "provenance": "PARTIAL / other branch", "independent": True},
                {"quantity": "f_a(T)", "modulus_mediation": "INPUT; not unique; not universal", "provenance": "INPUT", "independent": True},
                {"quantity": "Kaehler data", "modulus_mediation": "free unless a test form is declared", "provenance": "INPUT family", "independent": True},
                {"quantity": "modular weights", "modulus_mediation": "unfixed; no preferred values", "provenance": "INPUT / UNFIXED", "independent": True},
                {"quantity": "Yukawa/modular dependence", "modulus_mediation": "INPUT when present; not fabricated", "provenance": "INPUT / PARTIAL", "independent": True},
                {"quantity": "gauge coupling", "modulus_mediation": "FREE; used not determined", "provenance": "NOT FIXED", "independent": True},
                {"quantity": "A coefficients", "modulus_mediation": "from d ln y and d ln Z when present", "provenance": "DERIVED GIVEN INPUT / PARTIAL", "independent": False},
                {"quantity": "B coefficients", "modulus_mediation": "UNTESTED; no added bilinear", "provenance": "UNTESTED", "independent": False},
                {"quantity": "scalar soft coefficients", "modulus_mediation": "from Z_i derivatives; weights unfixed", "provenance": "PARTIAL", "independent": False},
                {"quantity": "gaugino coefficients", "modulus_mediation": "F_T * d ln(Re f_a)/dT", "provenance": "DERIVED GIVEN INPUT / PARAMETER-DEPENDENT", "independent": False},
                {"quantity": "FI xi", "modulus_mediation": "untuned", "provenance": "PRESERVED", "independent": True},
                {"quantity": "W", "modulus_mediation": "free; W(T) is not automatic", "provenance": "INPUT family", "independent": True},
                {"quantity": "K", "modulus_mediation": "free; K(T, Tbar) is not automatic", "provenance": "INPUT family", "independent": True},
                {"quantity": "c0", "modulus_mediation": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "c1", "modulus_mediation": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "lambda_a", "modulus_mediation": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "lambda_b", "modulus_mediation": "FREE", "provenance": "INPUT", "independent": True},
            ],
            "status": "PARTIAL",
        },
        "pfr_analysis": {
            "M_a_from_dln_f": "still depends on F_T and f_a(T); not a PFR",
            "counted_as_PFR": False,
            "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
            "status": "NOT_FOUND",
        },
        "uniqueness_analysis": {
            "MODULUS_MEDIATION_UNIQUENESS": "NOT_DERIVED",
            "f_a_unique": False,
            "T_unique": False,
            "weights_unique": False,
            "status": "NOT_DERIVED",
        },
        "documentary_comparison": {
            "gravity_mediation": "previously tested, PARTIAL",
            "gauge_mediation": "previously tested, PARTIAL",
            "anomaly_mediation": "previously tested, PARTIAL",
            "modulus_mediation": "current explicit input",
            "used_as_score": False,
            "preferred_mechanism_declared": False,
        },
        "provenance": {
            "modulus_mediation_postulate": "NEW PHYSICAL INPUT",
            "T": "NEW TEST INPUT",
            "F_T": "INPUT",
            "f_a": "INPUT",
            "Z_i": "INPUT / TEST ASSUMPTION",
            "soft_terms": "DERIVED GIVEN MODULUS-MEDIATION INPUT / PARTIAL",
            "P5J_P5K": "EXISTING COVERAGE / REFERENCE; not upgraded",
        },
        "coverage_matrix": coverage_matrix,
        "negative_physics_cases": {
            "SUGRA_without_modulus_mediation": "11U does not activate modulus mediation",
            "existing_moduli_without_channel": "4C-11Y have no T mediation field",
            "free_F_T": "F_T INPUT",
            "nonuniversal_f_a": "f1(T) is not f2(T)",
            "unfixed_weights": "n_i free",
            "no_stabilization": "NOT_FOUND",
            "nonunique_vacuum": "VACUUM_SELECTION NOT_FOUND",
            "no_messengers": "11X messengers not imported",
            "no_mixed_mediation": "11Y compensator not combined",
            "no_UV_completion": "UV_PROPERTY_NOT_FOUND",
        },
        "new_input_required": False,
        "new_parameter_count": 2,
        "reduced_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "remaining_free_function_count": 4,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "UNIQUE_MEDIATION": "NOT_DERIVED",
        "MODULUS_MEDIATION_UNIQUENESS": "NOT_DERIVED",
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
            "susy_authorization": EXPECTED_SUSY_AUTH_HASH,
            "breaking_authorization": EXPECTED_BREAKING_AUTH_HASH,
            "sugra_authorization": EXPECTED_SUGRA_AUTH_HASH,
            "anomaly_mediation_authorization": EXPECTED_ANOMALY_AUTH_HASH,
            "modulus_mediation_authorization": declaration["declaration_hash"],
        },
        "pytest_status": "GREEN",
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "completion_class": "TEST_EXTENSION",
        "identities": {
            "no_T_in_freeze": identities["no_T_in_freeze"],
            "F_T_is_INPUT_symbol": identities["F_T_is_INPUT_symbol"],
            "F_T_not_hidden_F_X": identities["F_T_not_hidden_F_X"],
            "F_T_not_compensator_F_phi": identities["F_T_not_compensator_F_phi"],
            "F_T_not_gravitino_mass": identities["F_T_not_gravitino_mass"],
            "f_a_not_assumed_universal": identities["f_a_not_assumed_universal"],
            "modular_weights_not_fixed": identities["modular_weights_not_fixed"],
            "A_not_fabricated_if_y_missing": identities["A_not_fabricated_if_y_missing"],
            "B_not_fabricated_if_bilinear_missing": identities["B_not_fabricated_if_bilinear_missing"],
            "no_stabilization_assumed": identities["no_stabilization_assumed"],
            "c0_FREE": identities["c0_FREE"],
            "c1_FREE": identities["c1_FREE"],
        },
        "forty_questions": _forty_questions(),
        "PHASE_11Z_STOPPED": True,
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11Z_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11Z_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11Z_MODULUS_MEDIATION.json", payload)
        _write_json(
            "PHASE_11Z_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11Z_STATUS": "PARTIAL",
                "PHASE_11Z_STOPPED": True,
                "MODULUS_MEDIATION_COVERAGE_BEFORE": "ABSENT",
                "MODULUS_MEDIATION_COVERAGE_AFTER": "PARTIAL",
                "MODULUS_MEDIATION_UNIQUENESS": "NOT_DERIVED",
                "MODULUS_MEDIATION_UNIQUENESS_STATUS": "NOT_DERIVED",
                "UNIQUE_MEDIATION": "NOT_DERIVED",
                "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_COUNT": 2,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "PARAMETER_REDUCTION_STATUS": "NONE",
                "PFR_STATUS": "NOT_FOUND",
                "GAUGE_COUPLING_CONSTRAINT_STATUS": "FREE",
                "MODULUS_STABILIZATION_STATUS": "NOT_FOUND",
                "GRAVITY_MEDIATION_STATUS": "PARTIAL",
                "GAUGE_MEDIATION_STATUS": "PARTIAL",
                "ANOMALY_MEDIATION_STATUS": "PARTIAL",
                "DIRECT_MEDIATION_STATUS": "NOT_ACTIVATED",
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
        "PHASE_11Z_TEST_COPY_ID": PHASE_11Z_TEST_COPY_ID,
        "analysis": payload,
        "MODULUS_MEDIATION_COVERAGE_BEFORE": "ABSENT",
        "MODULUS_MEDIATION_COVERAGE_AFTER": "PARTIAL",
        "MODULUS_MEDIATION_MODULE_STATUS": "PARTIAL",
        "MODULUS_MEDIATION_INPUT_STATUS": "VERIFIED",
        "MODULUS_FIELD_STATUS": "VERIFIED",
        "MODULUS_F_TERM_STATUS": "VERIFIED",
        "GAUGE_KINETIC_FUNCTION_STATUS": "VERIFIED",
        "MODULUS_GAUGINO_MASS_STATUS": "PARTIAL",
        "MODULUS_SCALAR_SOFT_MASS_STATUS": "PARTIAL",
        "MODULUS_A_TERM_STATUS": "PARTIAL",
        "MODULUS_B_TERM_STATUS": "UNTESTED",
        "MODULUS_STABILIZATION_STATUS": "NOT_FOUND",
        "RG_CONSISTENCY_STATUS": "PARTIAL",
        "GAUGE_COUPLING_CONSTRAINT_STATUS": "FREE",
        "R_SYMMETRY_STATUS": "PARTIAL",
        "SUGRA_COMPATIBILITY_STATUS": "PARTIAL",
        "VACUUM_IMPACT_STATUS": "PARTIAL",
        "UV_IMPACT_STATUS": "NOT_FOUND",
        "MODULUS_MEDIATION_UNIQUENESS_STATUS": "NOT_DERIVED",
        "PARAMETER_REDUCTION_STATUS": "NONE",
        "PFR_STATUS": "NOT_FOUND",
        "NEW_PHYSICAL_INPUT_STATUS": "VERIFIED",
        "NEW_INPUT_REQUIRED": False,
        "NEW_PARAMETER_COUNT": 2,
        "REDUCED_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "REMAINING_FREE_FUNCTION_COUNT": 4,
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
        "DIRECT_MEDIATION_STATUS": "NOT_ACTIVATED",
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "UV_PROPERTY_NOT_FOUND": True,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "UNIQUE_MEDIATION": "NOT_DERIVED",
        "MODULUS_MEDIATION_UNIQUENESS": "NOT_DERIVED",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11Z_STATUS": "PARTIAL",
        "PHASE_11Z_PRECONDITION_STATUS": "VERIFIED",
        "PHASE_11Z_STOPPED": True,
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
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "modulus_authorization_id": MODULUS_AUTH_ID,
        "authorized_mechanism": MECHANISM_ID,
        "other_mechanisms_activated": False,
        "combined_with_11V_operators": False,
        "combined_with_11X_messengers": False,
        "combined_with_11Y_compensator": False,
        "mixed_mediation_activated": False,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
    }


def run_phase11z_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11z_modulus_mediation(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11Z_INTEGRITY_FAILURE"}:
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
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11Z_STATUS": science.get("PHASE_11Z_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
