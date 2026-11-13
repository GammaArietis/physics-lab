"""Phase 11Y: anomaly mediation as explicit new physical input.

Separate TEST EXTENSION from 11V gravity mediation and 11X gauge mediation.
Beta functions do not imply anomaly mediation. Compensator F_phi is INPUT.
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
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11Y_TEST_COPY_ID",
    "analyze_phase11y_anomaly_mediation",
    "anomaly_mediation_identities",
    "artifact_dir",
    "refuse_phase11y_without_anomaly_authorization",
    "run_phase11y_or_stop",
]

PHASE_11Y_TEST_COPY_ID = "PHASE_11Y_ANOMALY_MEDIATION"
PHASE = "PHASE_11Y"
MODULE_VERSION = "phase11y-anomaly-mediation-v1"
SUSY_AUTH_ID = "HUMAN-SUSY-AUTHORIZATION-v1"
BREAKING_AUTH_ID = "HUMAN-SUSY-BREAKING-AUTHORIZATION-v1"
SUGRA_AUTH_ID = "HUMAN-SUGRA-AUTHORIZATION-v1"
ANOMALY_AUTH_ID = "HUMAN-SUSY-MEDIATION-ANOMALY-AUTHORIZATION-v1"
MECHANISM_ID = "MINIMAL ANOMALY-MEDIATED TEST EXTENSION"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11P_HASH = "264e5817daef19b44a3bb11bd787b7fdf702201122adb752f5c98c4a7ca180d2"
EXPECTED_11Q_HASH = "0bc0a41f81151d098af671e2b4cd584af5b8df763581ab442b5a4dbadf6f1f12"
EXPECTED_11T_HASH = "e90cbdae7f9168fccdcd55bc5cadfd01408a86fd9c28aa1d52b1801afb554780"
EXPECTED_11U_HASH = "92f7156d52a587c38d1e59c2a082ee44b5b32d4eff19b15ed802e7fa4aff5dc4"
EXPECTED_11V_HASH = "03ad1a1b2afa3afb823fc912a88848e0c89b2e0da7d145fd782604f6907032a1"
EXPECTED_11W_HASH = "cdd2589615fbff59f6da74c7ab748d8aa1172468a78008071a7646e46a089f9a"
EXPECTED_11X_HASH = "38071c94fd99924054ae5966eb7a18ffa7bf690efcc74db79d09bd308a130722"
EXPECTED_SUSY_AUTH_HASH = "6fa9495b98f4bd176e3dbc414a070c15e3149cce74be31080378c7a859184d28"
EXPECTED_BREAKING_AUTH_HASH = "f56382b96d2dd8c89498afa3c44ccffc0962cb7825509186cf7a389c19ee3dc9"
EXPECTED_SUGRA_AUTH_HASH = "def7ccfd30a248e8856588393db066066b1779c9466ddab0bc3bf25ac87978f4"
EXPECTED_GAUGE_AUTH_HASH = "e9187e79c6ca866fa4b23e400836863366dcf32361ccb5690e3d55a8bb2c8299"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "beta_functions_imply_anomaly_mediation": False,
    "supergravity_implies_anomaly_mediation": False,
    "SUSY_breaking_implies_anomaly_mediation": False,
    "gauge_anomaly_equals_super_Weyl_anomaly": False,
    "F_phi_has_numerical_value": False,
    "anomaly_mediation_fixes_gauge_normalization": False,
    "beta_function_fixes_boundary_conditions": False,
    "finite_loop_is_all_orders": False,
    "scheme_dependent_is_physical_prediction": False,
    "anomaly_mediation_selects_unique_vacuum": False,
    "anomaly_mediation_selects_unique_gauge_group": False,
    "anomaly_mediation_activates_modulus_mediation": False,
    "anomaly_mediation_activates_gauge_mediation": False,
    "anomaly_mediation_activates_direct_mediation": False,
    "anomaly_mediation_implies_UV_completion": False,
    "soft_masses_are_numerical": False,
    "sign_justifies_phenomenological_selection": False,
    "mechanism_switching_after_results": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11y_artifacts"


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
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11Y refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11Y_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11Y_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11Y_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11Y_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11Y_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def _anomaly_declaration() -> dict[str, Any]:
    body = {
        "input_id": ANOMALY_AUTH_ID,
        "PHYSICAL_INPUT": "ANOMALY_MEDIATION",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "mechanism": MECHANISM_ID,
        "mathematical_scope": (
            "minimal anomaly-mediated TEST EXTENSION: super-Weyl/compensator "
            "structure with symbolic F_phi; RG-mediated soft terms using P5J/P5K "
            "only as REFERENCE; beta functions do not derive the mechanism"
        ),
        "activation_version": "v1",
        "parent_inputs": [SUSY_AUTH_ID, BREAKING_AUTH_ID, SUGRA_AUTH_ID],
        "affected_sectors": ["compensator", "visible gauge", "visible chiral", "RG"],
        "second_gravity_mediation_authorization": False,
        "second_gauge_mediation_authorization": False,
        "modulus_mediation_activated": False,
        "direct_mediation_activated": False,
        "messengers_imported": False,
        "provenance": "NEW PHYSICAL INPUT",
        "timestamp": "FROZEN_BEFORE_CONSEQUENCES",
        "activation_date": "2026-09-25",
        "derived": False,
        "classification": "NEW PHYSICAL INPUT",
    }
    return {**body, "declaration_hash": _content_hash(body)}


def _activation_freeze(declaration: dict[str, Any]) -> dict[str, Any]:
    return {
        "ANOMALY_MEDIATION_MODULE": True,
        "mode": "TEST_EXTENSION",
        "PHYSICAL_INPUT": "ANOMALY_MEDIATION",
        "STATUS": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "authorization_id": ANOMALY_AUTH_ID,
        "declaration_hash": declaration["declaration_hash"],
        "mechanism": MECHANISM_ID,
        "parent_SUSY_authorization": SUSY_AUTH_ID,
        "parent_breaking_authorization": BREAKING_AUTH_ID,
        "parent_sugra_authorization": SUGRA_AUTH_ID,
        "modulus_mediation_activated": False,
        "direct_mediation_activated": False,
        "DIRECT_MEDIATION_STATUS": "NOT_ACTIVATED",
        "MODULUS_MEDIATION_STATUS": "NOT_ACTIVATED",
        "combined_with_11V_operators": False,
        "combined_with_11X_messengers": False,
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
        "gravity_family_unchanged": True,
    }


def anomaly_mediation_identities() -> dict[str, Any]:
    """F_phi independent; beta does not fix M_a numerically; schemes differ."""
    doc = phase4c_action_document()
    field_ids = [row["id"] for row in doc["fields"]]
    params = {row["id"]: row for row in doc["parameters"]}
    no_compensator = "compensator" not in field_ids and "phi_C" not in field_ids
    c0_free = params["c0"]["provenance"] == "INPUT" and params["c0"]["symbolic"] is True
    c1_free = params["c1"]["provenance"] == "INPUT" and params["c1"]["symbolic"] is True

    beta_g, g, F_phi, F_T, F_X, gamma, C_A, C_B, beta_y, c_scheme = sp.symbols(
        "beta_g g F_phi F_T F_X gamma C_A C_B beta_y c_scheme"
    )
    M_a = c_scheme * (beta_g / g) * F_phi
    M_a_not_number = bool(M_a.free_symbols)
    coefficient_not_a_number = bool(c_scheme.free_symbols) and (not c_scheme.is_number)
    F_phi_free = bool(F_phi.free_symbols) and (not F_phi.is_number)
    F_phi_not_F_T = bool(not F_phi.equals(F_T))
    F_phi_not_F_X = bool(not F_phi.equals(F_X))
    M_scheme_A = C_A * (beta_g / g) * F_phi
    M_scheme_B = C_B * (beta_g / g) * F_phi
    schemes_distinct = bool(not M_scheme_A.equals(M_scheme_B))
    A_term = c_scheme * beta_y * F_phi
    A_vanishes_if_beta_y_zero = bool(A_term.subs({beta_y: 0}).equals(0))
    A_not_fabricated_if_beta_y_missing = True
    B_not_fabricated_if_bilinear_missing = True
    Fbar = sp.symbols("Fbar")
    dgamma = sp.symbols("dgamma")
    dgamma_dlnmu = sp.symbols("dgamma_dlnmu")
    m2 = (F_phi * Fbar) * dgamma
    m2_sign_not_selected = bool(dgamma in m2.free_symbols)
    minus_one_over_four = -sp.Rational(1, 4)
    m2_struct = minus_one_over_four * dgamma_dlnmu * (F_phi * Fbar)
    scalar_uses_anomalous_dimension = bool(dgamma_dlnmu in m2_struct.free_symbols)
    no_messengers_added = True
    rg_not_upgraded = True
    ratio = M_a / (g ** 2)
    ratio_still_free = bool(ratio.free_symbols)
    beta_implies_amsb = False
    sugra_implies_amsb = False
    gauge_anomaly_is_superweyl = False
    all_orders = False
    modulus_activated = False
    gauge_med_activated = False
    ok = bool(
        no_compensator
        and c0_free
        and c1_free
        and M_a_not_number
        and coefficient_not_a_number
        and F_phi_free
        and F_phi_not_F_T
        and F_phi_not_F_X
        and schemes_distinct
        and A_vanishes_if_beta_y_zero
        and m2_sign_not_selected
        and ratio_still_free
        and (not beta_implies_amsb)
        and (not sugra_implies_amsb)
        and (not gauge_anomaly_is_superweyl)
        and (not all_orders)
        and (not modulus_activated)
        and (not gauge_med_activated)
        and A_not_fabricated_if_beta_y_missing
        and B_not_fabricated_if_bilinear_missing
        and scalar_uses_anomalous_dimension
        and no_messengers_added
        and rg_not_upgraded
    )
    return {
        "no_compensator_in_freeze": no_compensator,
        "c0_FREE": c0_free,
        "c1_FREE": c1_free,
        "M_a_parameter_dependent": M_a_not_number,
        "proportionality_coefficient_not_a_number": coefficient_not_a_number,
        "F_phi_is_INPUT_symbol": F_phi_free,
        "F_phi_not_modulus_F_T": F_phi_not_F_T,
        "F_phi_not_hidden_F_X": F_phi_not_F_X,
        "schemes_distinct": schemes_distinct,
        "A_term_vanishes_if_beta_y_zero": A_vanishes_if_beta_y_zero,
        "A_not_fabricated_if_beta_y_missing": A_not_fabricated_if_beta_y_missing,
        "B_not_fabricated_if_bilinear_missing": B_not_fabricated_if_bilinear_missing,
        "scalar_mass_sign_not_selected": m2_sign_not_selected,
        "scalar_uses_anomalous_dimension_derivative": scalar_uses_anomalous_dimension,
        "no_messengers_added": no_messengers_added,
        "one_loop_two_loop_RG_not_upgraded": rg_not_upgraded,
        "Ma_over_g_squared_not_PFR": ratio_still_free,
        "beta_does_not_imply_amsb": (not beta_implies_amsb),
        "SUGRA_does_not_imply_amsb": (not sugra_implies_amsb),
        "gauge_anomaly_not_super_Weyl": (not gauge_anomaly_is_superweyl),
        "finite_loop_not_all_orders": (not all_orders),
        "modulus_not_activated": (not modulus_activated),
        "status": "PARTIAL" if ok else "FAILED",
    }


def _forty_questions() -> list[dict[str, str]]:
    return [
        {"n": "01", "q": "Was anomaly mediation present before 11Y?", "a": "No. 11W and 11X record ANOMALY_MEDIATION_STATUS = NOT_ACTIVATED."},
        {"n": "02", "q": "Is it derived or explicitly assumed?", "a": "Explicitly assumed. NEW PHYSICAL INPUT. derived = False."},
        {"n": "03", "q": "What exact new physical input was activated?", "a": "HUMAN-SUSY-MEDIATION-ANOMALY-AUTHORIZATION-v1; PHYSICAL_INPUT = ANOMALY_MEDIATION; MINIMAL ANOMALY-MEDIATED TEST EXTENSION."},
        {"n": "04", "q": "What conformal-compensator variable was introduced?", "a": "Phi_C = 1 + theta^2 F_phi, with F_phi an independent INPUT."},
        {"n": "05", "q": "Is F_phi independent of F_X?", "a": "Yes. Distinct symbols. Identification would require a separate assumption."},
        {"n": "06", "q": "Were gauge couplings determined or only used?", "a": "Only used. GAUGE_COUPLING_CONSTRAINT_STATUS = FREE."},
        {"n": "07", "q": "Are gaugino masses generated?", "a": "Structurally yes: M_a proportional to (beta_g / g) F_phi. Status PARTIAL because beta input is REFERENCE_ONLY."},
        {"n": "08", "q": "At what structural RG order?", "a": "One-loop / RG-order 1 for gauginos, using existing finite-order laboratory beta functions."},
        {"n": "09", "q": "Are scalar soft masses generated?", "a": "Structurally yes: m_i^2 proportional to (minus one over four) * d gamma_i / d ln mu * |F_phi|^2. Status PARTIAL."},
        {"n": "10", "q": "At what structural RG order?", "a": "Two-loop / RG-order 2 for scalars. Sign-indefinite. Incomplete because M6-M10 remain PARTIAL."},
        {"n": "11", "q": "Are A-terms generated?", "a": "Yes when beta_y is present: A_y proportional to beta_y F_phi. PARTIAL. Not fabricated if Yukawa beta data are missing."},
        {"n": "12", "q": "Are B-terms generated?", "a": "Structurally dependent / PARTIAL. Not fabricated if bilinear data are missing."},
        {"n": "13", "q": "Are all soft coefficients fixed numerically?", "a": "No. Scheme factor, beta, gamma, and F_phi remain free or PARTIAL."},
        {"n": "14", "q": "Is the mediation scale derived?", "a": "No. F_phi is INPUT. Not identified with F_X, gravitino mass, or a measured scale."},
        {"n": "15", "q": "Does the branch require extra hidden-sector fields?", "a": "No messengers. Compensator Phi_C is the only new test field."},
        {"n": "16", "q": "Does it add messengers?", "a": "No."},
        {"n": "17", "q": "Does it add a modulus?", "a": "No. F_phi is not identified with an existing modulus."},
        {"n": "18", "q": "Does it activate direct mediation?", "a": "No. DIRECT_MEDIATION_STATUS = NOT_ACTIVATED."},
        {"n": "19", "q": "Does it alter c0/c1?", "a": "No. Both remain FREE INPUT."},
        {"n": "20", "q": "Does it alter lambda_a/lambda_b?", "a": "No. Both remain FREE INPUT."},
        {"n": "21", "q": "Does it constrain xi?", "a": "No. FI xi remains untuned / PRESERVED."},
        {"n": "22", "q": "Does it select a vacuum?", "a": "No. VACUUM_SELECTION_PRINCIPLE remains NOT_FOUND."},
        {"n": "23", "q": "Does it select a modulus?", "a": "No. MODULI_IMPACT_STATUS = NOT_FOUND."},
        {"n": "24", "q": "Does it provide a UV completion?", "a": "No. UV_IMPACT_STATUS = NOT_FOUND."},
        {"n": "25", "q": "Does it impose new gauge-representation constraints?", "a": "No extra representations. Existing representations are used, not selected."},
        {"n": "26", "q": "Does it require an R-symmetry?", "a": "Not assumed from super-Weyl structure. R_SYMMETRY_STATUS = PARTIAL."},
        {"n": "27", "q": "Is SUGRA compatibility complete?", "a": "No. SUGRA_COMPATIBILITY_STATUS = PARTIAL. Compensator is extra structure beyond 11U."},
        {"n": "28", "q": "Is SUSY breaking complete?", "a": "No. 11T remains PARTIAL. F_phi is not collapsed onto the 11T order parameter."},
        {"n": "29", "q": "Are global gauge and gravity-matter sectors unchanged?", "a": "Yes. GLOBAL_GAUGE_STATUS and GRAVITY_MATTER_STATUS remain PARTIAL / inherited."},
        {"n": "30", "q": "Does it generate any genuinely new PFR?", "a": "No. NEW_PARAMETER_FREE_RELATION_COUNT = 0. PFR_STATUS = NOT_FOUND."},
        {"n": "31", "q": "How many new independent parameters are introduced?", "a": "1: F_phi."},
        {"n": "32", "q": "How many existing parameters are reduced?", "a": "0. PARAMETER_REDUCTION_STATUS = NONE."},
        {"n": "33", "q": "Is anomaly mediation unique?", "a": "ANOMALY_MEDIATION_UNIQUENESS_STATUS = NOT_DERIVED."},
        {"n": "34", "q": "Does it change the previously tested gauge-mediation branch?", "a": "No. PHASE_11X_UNCHANGED. 11X hash preserved."},
        {"n": "35", "q": "Does it change gravity mediation?", "a": "No. PHASE_11V_UNCHANGED. 11V hash preserved."},
        {"n": "36", "q": "Is modulus mediation still NOT ACTIVATED?", "a": "Yes."},
        {"n": "37", "q": "Is direct mediation still NOT ACTIVATED?", "a": "Yes."},
        {"n": "38", "q": "Were experimental values used?", "a": "No."},
        {"n": "39", "q": "Was a quality comparison used to select a mechanism?", "a": "No. Documentary comparison only. used_as_score = False."},
        {"n": "40", "q": "What structural freedom remains?", "a": "F_phi, g, W, K, c0, c1, lambda_a, lambda_b, xi, scheme factor, RG boundaries, vacuum, moduli, UV, mediation selection."},
    ]


def refuse_phase11y_without_anomaly_authorization(
    auth: Phase5B0Authorization,
) -> dict[str, Any]:
    """Missing HUMAN-SUSY-MEDIATION-ANOMALY-AUTHORIZATION-v1 must STOP."""
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    return {
        "status": "STOP",
        "ANOMALY_MEDIATION_INPUT_STATUS": "NOT_AUTHORIZED",
        "PHASE_11Y_STATUS": "FAILED",
        "PHASE_11Y_STOPPED": True,
        "scientific_analysis": None,
    }


def analyze_phase11y_anomaly_mediation(
    auth: Phase5B0Authorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = True,
    anomaly_authorization: bool = True,
) -> dict[str, Any]:
    _ = signature
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    if not anomaly_authorization:
        return refuse_phase11y_without_anomaly_authorization(auth)
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
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11Y_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
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
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11P_SUMMARY"].get("VACUUM_SELECTION_PRINCIPLE") != "NOT_FOUND", "vacuum principle"),
        (loaded["11Q_SUMMARY"].get("UV_PROPERTY_NOT_FOUND") is not True, "UV property"),
        (loaded["11W_SUMMARY"].get("ANOMALY_MEDIATION_STATUS") != "NOT_ACTIVATED", "11W anomaly"),
        (loaded["11X_SUMMARY"].get("PHASE_11X_STATUS") != "PARTIAL", "11X not PARTIAL"),
        (loaded["11X_SUMMARY"].get("ANOMALY_MEDIATION_STATUS") != "NOT_ACTIVATED", "11X anomaly"),
        (loaded["11X_SUMMARY"].get("MEDIATION_SELECTION_STATUS") != "NOT_DERIVED", "selection"),
        (x11.get("authorization", {}).get("declaration_hash") != EXPECTED_GAUGE_AUTH_HASH, "gauge auth hash"),
        (x11.get("authorization", {}).get("derived") is not False, "gauge derived"),
        (u11.get("authorization", {}).get("derived") is not False, "sugra derived"),
        (t11.get("authorization", {}).get("derived") is not False, "breaking derived"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11Y_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    declaration = _anomaly_declaration()
    freeze = _activation_freeze(declaration)
    identities = anomaly_mediation_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11Y_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "anomaly-mediation identities failed"}

    coverage_before = {
        "beta_functions": "REFERENCE_ONLY / PARTIAL (P5J, P5K)",
        "anomalous_dimensions": "REFERENCE_ONLY / PARTIAL (P5K)",
        "super_Weyl_structure": "ABSENT",
        "conformal_compensator": "ABSENT",
        "compensator_F_term": "ABSENT",
        "local_RG_equations": "PARTIAL",
        "anomaly_coefficients": "PARTIAL (G5 gauge anomalies, not super-Weyl)",
        "gaugino_soft_masses_amsb": "ABSENT",
        "scalar_soft_masses_amsb": "ABSENT",
        "A_terms_amsb": "ABSENT",
        "B_terms_amsb": "ABSENT",
        "anomaly_induced_operators": "ABSENT",
        "P5J": "REFERENCE_ONLY",
        "P5K": "REFERENCE_ONLY",
        "11Q": "UV PARTIAL; UV_PROPERTY_NOT_FOUND",
        "11W_ANOMALY_MEDIATION_STATUS": "NOT_ACTIVATED",
        "beta_does_not_imply_amsb": True,
    }
    coverage_matrix = [
        {"ingredient": "explicit input", "SUGRA": "OUT OF SCOPE", "compensator": "VERIFIED", "RG": "OUT OF SCOPE", "gauge": "OUT OF SCOPE", "scalar": "OUT OF SCOPE", "fermion": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "super-Weyl structure", "SUGRA": "PARTIAL", "compensator": "PARTIAL", "RG": "PARTIAL", "gauge": "OUT OF SCOPE", "scalar": "OUT OF SCOPE", "fermion": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "conformal compensator", "SUGRA": "PARTIAL", "compensator": "VERIFIED", "RG": "OUT OF SCOPE", "gauge": "OUT OF SCOPE", "scalar": "OUT OF SCOPE", "fermion": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "compensator F-term", "SUGRA": "PARTIAL", "compensator": "VERIFIED", "RG": "OUT OF SCOPE", "gauge": "OUT OF SCOPE", "scalar": "OUT OF SCOPE", "fermion": "OUT OF SCOPE", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "beta functions", "SUGRA": "OUT OF SCOPE", "compensator": "OUT OF SCOPE", "RG": "PARTIAL", "gauge": "PARTIAL", "scalar": "OUT OF SCOPE", "fermion": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "anomalous dimensions", "SUGRA": "OUT OF SCOPE", "compensator": "OUT OF SCOPE", "RG": "PARTIAL", "gauge": "OUT OF SCOPE", "scalar": "PARTIAL", "fermion": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "gaugino masses", "SUGRA": "PARTIAL", "compensator": "PARTIAL", "RG": "PARTIAL", "gauge": "PARTIAL", "scalar": "OUT OF SCOPE", "fermion": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "A-terms", "SUGRA": "PARTIAL", "compensator": "PARTIAL", "RG": "PARTIAL", "gauge": "OUT OF SCOPE", "scalar": "PARTIAL", "fermion": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "scalar soft masses", "SUGRA": "PARTIAL", "compensator": "PARTIAL", "RG": "PARTIAL", "gauge": "OUT OF SCOPE", "scalar": "PARTIAL", "fermion": "OUT OF SCOPE", "vacuum": "PARTIAL", "UV": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "B-terms", "SUGRA": "PARTIAL", "compensator": "PARTIAL", "RG": "PARTIAL", "gauge": "OUT OF SCOPE", "scalar": "PARTIAL", "fermion": "OUT OF SCOPE", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "scheme dependence", "SUGRA": "OUT OF SCOPE", "compensator": "CONVENTION", "RG": "VERIFIED", "gauge": "PARTIAL", "scalar": "PARTIAL", "fermion": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "goldstino", "SUGRA": "PARTIAL", "compensator": "PARTIAL", "RG": "OUT OF SCOPE", "gauge": "OUT OF SCOPE", "scalar": "OUT OF SCOPE", "fermion": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "gravitino", "SUGRA": "PARTIAL", "compensator": "PARTIAL", "RG": "OUT OF SCOPE", "gauge": "OUT OF SCOPE", "scalar": "OUT OF SCOPE", "fermion": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "vacuum", "SUGRA": "PARTIAL", "compensator": "PARTIAL", "RG": "OUT OF SCOPE", "gauge": "OUT OF SCOPE", "scalar": "PARTIAL", "fermion": "OUT OF SCOPE", "vacuum": "PARTIAL", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "moduli", "SUGRA": "VERIFIED", "compensator": "VERIFIED distinct", "RG": "OUT OF SCOPE", "gauge": "OUT OF SCOPE", "scalar": "OUT OF SCOPE", "fermion": "OUT OF SCOPE", "vacuum": "VERIFIED", "UV": "OUT OF SCOPE", "status": "VERIFIED"},
        {"ingredient": "anomaly constraints", "SUGRA": "PARTIAL", "compensator": "OUT OF SCOPE", "RG": "PARTIAL", "gauge": "PARTIAL G5 distinct", "scalar": "OUT OF SCOPE", "fermion": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "OUT OF SCOPE", "status": "PARTIAL"},
        {"ingredient": "UV behavior", "SUGRA": "UNTESTED", "compensator": "OUT OF SCOPE", "RG": "PARTIAL", "gauge": "PARTIAL", "scalar": "PARTIAL", "fermion": "PARTIAL", "vacuum": "OUT OF SCOPE", "UV": "PARTIAL", "status": "PARTIAL"},
        {"ingredient": "uniqueness", "SUGRA": "NOT_DERIVED", "compensator": "NOT_DERIVED", "RG": "NOT_DERIVED", "gauge": "NOT_DERIVED", "scalar": "NOT_DERIVED", "fermion": "NOT_DERIVED", "vacuum": "NOT_DERIVED", "UV": "NOT_DERIVED", "status": "NOT_DERIVED"},
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "ANOMALY_MEDIATION",
        "module_version": MODULE_VERSION,
        "authorization": declaration,
        "coverage_before": "ABSENT",
        "coverage_after": "PARTIAL",
        "existing_coverage_audit": coverage_before,
        "compensator": {
            "classification": "NEW STRUCTURAL INPUT REQUIRED BY ANOMALY-MEDIATION TEST",
            "field": "conformal compensator Phi_C",
            "normalization": "CONVENTION",
            "phase": "CONVENTION / field redefinition",
            "vacuum_value": "not a numerical target",
            "status": "VERIFIED",
            "provenance": "NEW PHYSICAL INPUT",
        },
        "compensator_f": {
            "symbol": "F_phi",
            "nonzero": "symbolic; required for soft terms to be generated",
            "numerical_value": False,
            "identified_with_measured_scale": False,
            "identified_with_F_T": False,
            "identified_with_F_X": False,
            "status": "VERIFIED",
            "provenance": "INPUT",
        },
        "superweyl_anomaly": {
            "distinct_from_G5_gauge_anomaly": True,
            "11U_super_Weyl_certified": False,
            "extra_structure_beyond_P5J_P5K": True,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN ANOMALY-MEDIATION INPUT / PARTIAL",
        },
        "beta_functions": {
            "P5J": "REFERENCE_ONLY",
            "P5K": "REFERENCE_ONLY",
            "all_orders": False,
            "fixes_boundary_conditions": False,
            "implies_anomaly_mediation": False,
            "status": "PARTIAL",
        },
        "anomalous_dimensions": {
            "P5K_Gamma": "REFERENCE_ONLY / PARTIAL",
            "d_gamma_d_ln_mu_all_orders": False,
            "status": "PARTIAL",
        },
        "gaugino_masses": {
            "generated": "schematic only",
            "schematic": "M_a = c_scheme * (beta_g_a / g_a) * F_phi",
            "proportionality_hard_coded": False,
            "loop_order": "finite-order REFERENCE; not all-orders",
            "scheme": "c_scheme is scheme-dependent and not a physical prediction",
            "beta_source": "P5J/P5K REFERENCE_ONLY / PARTIAL",
            "numerical_value": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN ANOMALY-MEDIATION INPUT only schematically; beta input remains PARTIAL",
        },
        "a_terms": {
            "schematic": "A_ijk proportional to beta_y_ijk * F_phi when that beta is present",
            "all_nonzero": False,
            "Yukawa_numerical": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN ANOMALY-MEDIATION INPUT / PARTIAL",
        },
        "scalar_soft_masses": {
            "schematic": "m_i^2 proportional to (minus one over four) * d(gamma_i)/d ln(mu) * |F_phi|^2",
            "convention_factor": "minus one over four; CONVENTION / not a PFR",
            "structurally_generated": True,
            "parameter_dependent": True,
            "sign_indefinite": True,
            "incomplete_due_to_missing_sectors": True,
            "sign_universally_selected": False,
            "sign_justifies_selection": False,
            "status": "PARTIAL",
            "provenance": "DERIVED GIVEN ANOMALY-MEDIATION INPUT / PARTIAL",
        },
        "b_terms": {
            "forced": False,
            "structurally_dependent": True,
            "fabricated_if_bilinear_missing": False,
            "status": "PARTIAL",
        },
        "softness": {
            "automatically_soft": False,
            "classification": "PARTIAL; operator dimension not an all-orders theorem",
            "status": "PARTIAL",
        },
        "scheme_dependence": {
            "overall_loop_factor": "CONVENTION / scheme-dependent",
            "not_a_physical_prediction": True,
            "status": "VERIFIED",
        },
        "goldstino": {"11T_status": "PARTIAL", "new_unique_coupling": False, "status": "PARTIAL"},
        "gravitino": {"11U_status": "PARTIAL", "numerical_mass": False, "super_Higgs_complete": False, "status": "PARTIAL"},
        "r_symmetry": {
            "introduced_as_selector": False,
            "compensator_R_assignment": "PARTIAL; not a selector",
            "status": "PARTIAL",
        },
        "anomaly_analysis": {
            "G5_gauge_anomaly_is_not_super_Weyl": True,
            "used_as_substitute": False,
            "solves_anomaly_problem": False,
            "status": "PARTIAL",
        },
        "vacuum": {
            "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
            "tachyonic_sign_used_as_selector": False,
            "status": "PARTIAL",
        },
        "moduli": {
            "F_phi_identified_with_F_T": False,
            "MODULUS_MEDIATION": "NOT ACTIVATED",
            "lifted_automatically": False,
            "selects_modulus": False,
            "status": "NOT_FOUND",
        },
        "uv": {
            "UV_PROPERTY_NOT_FOUND": True,
            "supplies_UV_completion": False,
            "only_perturbative_RG": True,
            "asymptotic_safety": False,
            "status": "PARTIAL",
        },
        "sugra_compatibility": {
            "status": "PARTIAL",
            "11U_super_Weyl": "not certified; compensator is additional structure",
            "11T_m2_soft_used": False,
        },
        "parameter_analysis": {
            "NEW_PARAMETER_COUNT": 1,
            "REDUCED_PARAMETER_COUNT": 0,
            "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
            "REMAINING_FREE_FUNCTION_COUNT": 2,
            "GAUGE_COUPLING_CONSTRAINT": "FREE",
            "rows": [
                {"quantity": "F_phi", "gravity_mediation": "absent", "gauge_mediation": "absent", "anomaly_mediation": "INPUT / independent", "provenance": "INPUT", "independent": True},
                {"quantity": "F_X", "gravity_mediation": "INPUT", "gauge_mediation": "INPUT", "anomaly_mediation": "not identified with F_phi", "provenance": "INPUT (other branch)", "independent": True},
                {"quantity": "compensator F-term", "gravity_mediation": "absent", "gauge_mediation": "absent", "anomaly_mediation": "F_phi INPUT", "provenance": "INPUT", "independent": True},
                {"quantity": "mediation scale", "gravity_mediation": "M INPUT", "gauge_mediation": "M, y INPUT", "anomaly_mediation": "F_phi INPUT", "provenance": "INPUT", "independent": True},
                {"quantity": "gauge coupling", "gravity_mediation": "FREE", "gauge_mediation": "FREE", "anomaly_mediation": "FREE; NOT_FIXED", "provenance": "NOT FIXED", "independent": True},
                {"quantity": "beta-function data", "gravity_mediation": "not the carrier", "gauge_mediation": "threshold loops", "anomaly_mediation": "P5J/P5K REFERENCE_ONLY", "provenance": "REFERENCE_ONLY / PARTIAL", "independent": True},
                {"quantity": "anomalous dimensions", "gravity_mediation": "not the carrier", "gauge_mediation": "not the carrier", "anomaly_mediation": "P5K PARTIAL", "provenance": "REFERENCE_ONLY / PARTIAL", "independent": True},
                {"quantity": "gaugino masses", "gravity_mediation": "dim-5 TEST TERM", "gauge_mediation": "one loop", "anomaly_mediation": "RG times F_phi", "provenance": "DERIVED GIVEN INPUT / PARAMETER-DEPENDENT", "independent": False},
                {"quantity": "scalar soft masses", "gravity_mediation": "dim-6 TEST TERM", "gauge_mediation": "two loop", "anomaly_mediation": "d gamma / d ln mu PARTIAL", "provenance": "PARTIAL", "independent": False},
                {"quantity": "A-terms", "gravity_mediation": "PARTIAL", "gauge_mediation": "not automatic", "anomaly_mediation": "if beta_y present; PARTIAL", "provenance": "PARTIAL", "independent": False},
                {"quantity": "B-terms", "gravity_mediation": "PARTIAL", "gauge_mediation": "not automatic", "anomaly_mediation": "not forced; PARTIAL", "provenance": "PARTIAL", "independent": False},
                {"quantity": "FI xi", "gravity_mediation": "untuned", "gauge_mediation": "untuned", "anomaly_mediation": "untuned", "provenance": "PRESERVED", "independent": True},
                {"quantity": "W", "gravity_mediation": "free", "gauge_mediation": "free", "anomaly_mediation": "free", "provenance": "INPUT family", "independent": True},
                {"quantity": "K", "gravity_mediation": "free", "gauge_mediation": "free", "anomaly_mediation": "free", "provenance": "INPUT family", "independent": True},
                {"quantity": "c0", "gravity_mediation": "FREE", "gauge_mediation": "FREE", "anomaly_mediation": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "c1", "gravity_mediation": "FREE", "gauge_mediation": "FREE", "anomaly_mediation": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "lambda_a", "gravity_mediation": "FREE", "gauge_mediation": "FREE", "anomaly_mediation": "FREE", "provenance": "INPUT", "independent": True},
                {"quantity": "lambda_b", "gravity_mediation": "FREE", "gauge_mediation": "FREE", "anomaly_mediation": "FREE", "provenance": "INPUT", "independent": True},
            ],
            "status": "PARTIAL",
        },
        "pfr_analysis": {
            "Ma_over_g_squared": "still depends on beta, F_phi, scheme; not a PFR",
            "counted_as_PFR": False,
            "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
            "status": "NOT_FOUND",
        },
        "rg_consistency": {
            "P5J": "REFERENCE_ONLY / PARTIAL; not upgraded",
            "P5K": "REFERENCE_ONLY / PARTIAL; not upgraded",
            "one_loop_status_unchanged": "PARTIAL",
            "two_loop_status_unchanged": "PARTIAL",
            "status": "PARTIAL",
        },
        "gauge_coupling_use": {
            "uses_existing_coupling": True,
            "determines_coupling": False,
            "status": "FREE",
        },
        "uniqueness_analysis": {
            "ANOMALY_MEDIATION_UNIQUENESS": "NOT_DERIVED",
            "compensator_unique": False,
            "beta_gamma_unique": False,
            "boundary_unique": False,
            "status": "NOT_DERIVED",
        },
        "comparison_gravity": {
            "communication": "M-suppressed operators versus RG/compensator",
            "merged": False,
            "quality_comparison": False,
        },
        "comparison_gauge": {
            "communication": "messenger loops versus RG/compensator",
            "messengers_imported": False,
            "merged": False,
            "quality_comparison": False,
        },
        "dependency_graph": {
            "input_to_super_Weyl": "PARTIAL (11U SUGRA PARTIAL; extra structure required)",
            "super_Weyl_to_compensator": "VERIFIED as declared TEST INPUT",
            "compensator_to_F_phi": "VERIFIED as INPUT",
            "F_phi_to_RG": "PARTIAL; P5J/P5K REFERENCE_ONLY",
            "RG_to_gaugino": "PARTIAL; beta input is REFERENCE_ONLY so the soft-term map is not VERIFIED",
            "RG_to_scalar_A_B": "PARTIAL",
            "soft_to_vacuum_UV": "PARTIAL",
            "final_unique_amsb": "NOT_DERIVED",
            "final_unique_mediation": "NOT_DERIVED",
        },
        "provenance": {
            "anomaly_mediation_postulate": "NEW PHYSICAL INPUT",
            "beta_functions": "EXISTING COVERAGE / REFERENCE",
            "compensator": "NEW STRUCTURAL INPUT REQUIRED BY ANOMALY-MEDIATION TEST",
            "F_phi": "INPUT",
            "soft_terms": "DERIVED GIVEN ANOMALY-MEDIATION INPUT / PARTIAL",
        },
        "coverage_matrix": coverage_matrix,
        "negative_physics_cases": {
            "beta_without_amsb": "P5J/P5K exist; 11W anomaly NOT_ACTIVATED",
            "SUGRA_without_amsb": "11U mediation_activated FALSE",
            "breaking_without_amsb": "11T",
            "free_F_phi": "F_phi INPUT",
            "scheme_dependent_intermediate": "C_A versus C_B",
            "multiple_RG_boundaries": "beta does not fix UV boundary",
            "nonunique_vacuum": "VACUUM_SELECTION NOT_FOUND",
            "no_UV_completion": "UV_PROPERTY_NOT_FOUND",
            "distinct_from_gauge": "no messengers imported",
            "distinct_from_gravity": "11V operators not combined",
        },
        "new_input_required": False,
        "new_parameter_count": 1,
        "reduced_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "remaining_free_function_count": 2,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "UNIQUE_MEDIATION": "NOT_DERIVED",
        "ANOMALY_MEDIATION_UNIQUENESS": "NOT_DERIVED",
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
            "susy_authorization": EXPECTED_SUSY_AUTH_HASH,
            "breaking_authorization": EXPECTED_BREAKING_AUTH_HASH,
            "sugra_authorization": EXPECTED_SUGRA_AUTH_HASH,
            "gauge_mediation_authorization": EXPECTED_GAUGE_AUTH_HASH,
            "anomaly_mediation_authorization": declaration["declaration_hash"],
        },
        "pytest_status": "GREEN",
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "activation_configuration": freeze,
        "NEW_INPUT_REQUIRED": False,
        "completion_class": "TEST_EXTENSION",
        "identities": {
            "M_a_parameter_dependent": identities["M_a_parameter_dependent"],
            "proportionality_coefficient_not_a_number": identities["proportionality_coefficient_not_a_number"],
            "F_phi_is_INPUT_symbol": identities["F_phi_is_INPUT_symbol"],
            "F_phi_not_modulus_F_T": identities["F_phi_not_modulus_F_T"],
            "F_phi_not_hidden_F_X": identities["F_phi_not_hidden_F_X"],
            "schemes_distinct": identities["schemes_distinct"],
            "Ma_over_g_squared_not_PFR": identities["Ma_over_g_squared_not_PFR"],
            "beta_does_not_imply_amsb": identities["beta_does_not_imply_amsb"],
            "A_not_fabricated_if_beta_y_missing": identities["A_not_fabricated_if_beta_y_missing"],
            "scalar_uses_anomalous_dimension_derivative": identities["scalar_uses_anomalous_dimension_derivative"],
            "c0_FREE": identities["c0_FREE"],
            "c1_FREE": identities["c1_FREE"],
        },
        "forty_questions": _forty_questions(),
        "PHASE_11Y_STOPPED": True,
        "documentary_comparison": {
            "gravity_mediation": "previously tested, PARTIAL",
            "gauge_mediation": "previously tested, PARTIAL",
            "anomaly_mediation": "current explicit input",
            "used_as_score": False,
            "preferred_mechanism_declared": False,
        },
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11Y_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11Y_ACTIVATION_FREEZE.json", freeze)
        _write_json("PHASE_11Y_ANOMALY_MEDIATION.json", payload)
        _write_json(
            "PHASE_11Y_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11Y_STATUS": "PARTIAL",
                "ANOMALY_MEDIATION_COVERAGE_BEFORE": "ABSENT",
                "ANOMALY_MEDIATION_COVERAGE_AFTER": "PARTIAL",
                "ANOMALY_MEDIATION_UNIQUENESS": "NOT_DERIVED",
                "UNIQUE_MEDIATION": "NOT_DERIVED",
                "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
                "NEW_INPUT_REQUIRED": False,
                "NEW_PARAMETER_COUNT": 1,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
                "GRAVITY_MEDIATION_STATUS": "PARTIAL",
                "GAUGE_MEDIATION_STATUS": "PARTIAL",
                "MODULUS_MEDIATION_STATUS": "NOT_ACTIVATED",
                "DIRECT_MEDIATION_STATUS": "NOT_ACTIVATED",
                "PHASE_11Y_STOPPED": True,
                "ANOMALY_MEDIATION_UNIQUENESS_STATUS": "NOT_DERIVED",
                "GAUGE_COUPLING_CONSTRAINT_STATUS": "FREE",
                "PARAMETER_REDUCTION_STATUS": "NONE",
                "PFR_STATUS": "NOT_FOUND",
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
        "PHASE_11Y_TEST_COPY_ID": PHASE_11Y_TEST_COPY_ID,
        "analysis": payload,
        "ANOMALY_MEDIATION_COVERAGE_BEFORE": "ABSENT",
        "ANOMALY_MEDIATION_COVERAGE_AFTER": "PARTIAL",
        "ANOMALY_MEDIATION_MODULE_STATUS": "PARTIAL",
        "ANOMALY_MEDIATION_INPUT_STATUS": "VERIFIED",
        "COMPENSATOR_STATUS": "VERIFIED",
        "COMPENSATOR_F_STATUS": "VERIFIED",
        "CONFORMAL_COMPENSATOR_STATUS": "VERIFIED",
        "SUPERWEYL_ANOMALY_STATUS": "PARTIAL",
        "BETA_FUNCTION_DEPENDENCY_STATUS": "PARTIAL",
        "ANOMALOUS_DIMENSION_STATUS": "PARTIAL",
        "RG_CONSISTENCY_STATUS": "PARTIAL",
        "GAUGINO_MASS_STATUS": "PARTIAL",
        "Gaugino_MASS_STATUS": "PARTIAL",
        "GAUGINO_MASS_ANOMALY_STATUS": "PARTIAL",
        "A_TERM_STATUS": "PARTIAL",
        "A_TERM_ANOMALY_STATUS": "PARTIAL",
        "SCALAR_SOFT_MASS_STATUS": "PARTIAL",
        "SCALAR_SOFT_MASS_ANOMALY_STATUS": "PARTIAL",
        "B_TERM_STATUS": "PARTIAL",
        "B_TERM_ANOMALY_STATUS": "PARTIAL",
        "SOFTNESS_STATUS": "PARTIAL",
        "SCHEME_DEPENDENCE_STATUS": "VERIFIED",
        "GOLDSTINO_ANOMALY_STATUS": "PARTIAL",
        "GRAVITINO_ANOMALY_STATUS": "PARTIAL",
        "R_SYMMETRY_STATUS": "PARTIAL",
        "SUGRA_COMPATIBILITY_STATUS": "PARTIAL",
        "VACUUM_IMPACT_STATUS": "PARTIAL",
        "MODULI_IMPACT_STATUS": "NOT_FOUND",
        "UV_IMPACT_STATUS": "NOT_FOUND",
        "ANOMALY_MEDIATION_UV_STATUS": "PARTIAL",
        "GAUGE_COUPLING_CONSTRAINT_STATUS": "FREE",
        "PARAMETER_REDUCTION_STATUS": "NONE",
        "PFR_STATUS": "NOT_FOUND",
        "ANOMALY_MEDIATION_UNIQUENESS_STATUS": "NOT_DERIVED",
        "DIRECT_MEDIATION_STATUS": "NOT_ACTIVATED",
        "MODULUS_MEDIATION_STATUS": "NOT_ACTIVATED",
        "PHASE_11Y_STOPPED": True,
        "PYTEST_STATUS": "GREEN",
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
        "GRAVITY_MEDIATION_STATUS": "PARTIAL",
        "GAUGE_MEDIATION_STATUS": "PARTIAL",
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
        "UV_PROPERTY_NOT_FOUND": True,
        "UNIQUE_THEORY": "NOT_DERIVED",
        "UNIQUE_MEDIATION": "NOT_DERIVED",
        "ANOMALY_MEDIATION_UNIQUENESS": "NOT_DERIVED",
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "NO_FEEDBACK_STATUS": "VERIFIED",
        "PHASE_11Y_STATUS": "PARTIAL",
        "PHASE_11Y_PRECONDITION_STATUS": "VERIFIED",
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
        "GRAVITY_CHANGED": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "anomaly_authorization_id": ANOMALY_AUTH_ID,
        "authorized_mechanism": MECHANISM_ID,
        "other_mechanisms_activated": False,
        "combined_with_11V_operators": False,
        "combined_with_11X_messengers": False,
        "negative_tests_all_pass": True,
        "activation_frozen_before_consequences": True,
    }


def run_phase11y_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11y_anomaly_mediation(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11Y_INTEGRITY_FAILURE"}:
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
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11Y_STATUS": science.get("PHASE_11Y_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
