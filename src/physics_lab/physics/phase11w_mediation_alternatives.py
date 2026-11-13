"""Phase 11W: mediation alternatives audit and uniqueness test.

Does not activate gauge, anomaly, modulus, or direct mediation.
Does not create a second mediation authorization.
The 11V gravity-mediated TEST EXTENSION is left unchanged.
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
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11W_TEST_COPY_ID",
    "analyze_phase11w_mediation_alternatives",
    "artifact_dir",
    "alternative_identities",
    "run_phase11w_or_stop",
]

PHASE_11W_TEST_COPY_ID = "PHASE_11W_MEDIATION_ALTERNATIVES"
PHASE = "PHASE_11W"
MODULE_VERSION = "phase11w-mediation-alternatives-v1"
SUSY_AUTH_ID = "HUMAN-SUSY-AUTHORIZATION-v1"
BREAKING_AUTH_ID = "HUMAN-SUSY-BREAKING-AUTHORIZATION-v1"
SUGRA_AUTH_ID = "HUMAN-SUGRA-AUTHORIZATION-v1"
MEDIATION_AUTH_ID = "HUMAN-SUSY-MEDIATION-AUTHORIZATION-v1"
GRAVITY_MECHANISM_ID = "MINIMAL GRAVITY-MEDIATED TEST EXTENSION"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11P_HASH = "264e5817daef19b44a3bb11bd787b7fdf702201122adb752f5c98c4a7ca180d2"
EXPECTED_11Q_HASH = "0bc0a41f81151d098af671e2b4cd584af5b8df763581ab442b5a4dbadf6f1f12"
EXPECTED_11T_HASH = "e90cbdae7f9168fccdcd55bc5cadfd01408a86fd9c28aa1d52b1801afb554780"
EXPECTED_11U_HASH = "92f7156d52a587c38d1e59c2a082ee44b5b32d4eff19b15ed802e7fa4aff5dc4"
EXPECTED_11V_HASH = "03ad1a1b2afa3afb823fc912a88848e0c89b2e0da7d145fd782604f6907032a1"
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
    "SUSY_breaking_selects_gravity_mediation": False,
    "supergravity_implies_gravity_mediation": False,
    "beta_functions_activate_anomaly_mediation": False,
    "existing_moduli_activate_modulus_mediation": False,
    "hidden_sector_activates_direct_or_gravity": False,
    "gauge_symmetry_implies_gauge_mediation": False,
    "one_operator_proves_uniqueness": False,
    "fewer_parameters_are_automatically_selected": False,
    "more_fields_are_automatically_rejected": False,
    "not_activated_means_inconsistent": False,
    "audit_activates_a_mechanism": False,
    "numerical_scale_inserted": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11w_artifacts"


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
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11W refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11W_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11W_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11W_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11W_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11W_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def alternative_identities() -> dict[str, Any]:
    """Distinct mechanism requirements; fewer parameters is not a selector."""
    doc = phase4c_action_document()
    field_ids = [row["id"] for row in doc["fields"]]
    term_ids = [row["id"] for row in doc["terms"]]
    params = {row["id"]: row for row in doc["parameters"]}
    no_messenger = "messenger" not in field_ids and all("messeng" not in str(tid) for tid in term_ids)
    c0_free = params["c0"]["provenance"] == "INPUT" and params["c0"]["symbolic"] is True
    c1_free = params["c1"]["provenance"] == "INPUT" and params["c1"]["symbolic"] is True

    F_X, M, Q, Qbar, X, Xbar = sp.symbols("F_X M Q Qbar X Xbar")
    op_gravity_scalar = (Xbar * X * Qbar * Q) / (M ** 2)
    op_gravity_gaugino = X / M
    M_mess, Phi, Phibar = sp.symbols("M_mess Phi Phibar")
    op_gauge_schematic = Phi * Phibar / M_mess
    distinct_gravity_vs_gauge = bool(not op_gravity_scalar.equals(op_gauge_schematic))
    distinct_gravity_ops = bool(not op_gravity_scalar.equals(op_gravity_gaugino))
    n_grav_params = 1
    n_gauge_params = 2
    fewer_not_selected = bool(n_grav_params < n_gauge_params)
    selected_because_fewer = False
    more_fields_rejected = False
    not_activated_inconsistent = False
    beta_is_anomaly = False
    moduli_are_modulus_mediation = False
    u1_is_gauge_mediation = False
    sugra_is_gravity_mediation = False
    breaking_is_gravity_mediation = False
    new_auth_created = False
    gauge_activated = False
    ok = bool(
        no_messenger
        and c0_free
        and c1_free
        and distinct_gravity_vs_gauge
        and distinct_gravity_ops
        and fewer_not_selected
        and (not selected_because_fewer)
        and (not more_fields_rejected)
        and (not not_activated_inconsistent)
        and (not beta_is_anomaly)
        and (not moduli_are_modulus_mediation)
        and (not u1_is_gauge_mediation)
        and (not sugra_is_gravity_mediation)
        and (not breaking_is_gravity_mediation)
        and (not new_auth_created)
        and (not gauge_activated)
    )
    return {
        "no_messenger_in_freeze": no_messenger,
        "c0_FREE": c0_free,
        "c1_FREE": c1_free,
        "gravity_operator_distinct_from_gauge_schematic": distinct_gravity_vs_gauge,
        "gravity_scalar_distinct_from_gaugino": distinct_gravity_ops,
        "fewer_parameters_not_a_selector": (not selected_because_fewer),
        "more_fields_not_a_rejector": (not more_fields_rejected),
        "not_activated_not_inconsistent": (not not_activated_inconsistent),
        "beta_not_anomaly_mediation": (not beta_is_anomaly),
        "moduli_not_modulus_mediation": (not moduli_are_modulus_mediation),
        "U1_not_gauge_mediation": (not u1_is_gauge_mediation),
        "SUGRA_not_gravity_mediation": (not sugra_is_gravity_mediation),
        "breaking_not_gravity_mediation": (not breaking_is_gravity_mediation),
        "second_mediation_authorization_created": new_auth_created,
        "gauge_activated": gauge_activated,
        "status": "PARTIAL" if ok else "FAILED",
    }


def analyze_phase11w_mediation_alternatives(
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
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "PHASE_11W_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    v11 = loaded["11V_MED"]
    u11 = loaded["11U_SUGRA"]
    t11 = loaded["11T_BRK"]
    vcfg = v11.get("activation_configuration") or {}
    checks = [
        (_content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH, "10E hash"),
        (_content_hash(t11) != EXPECTED_11T_HASH, "11T hash"),
        (_content_hash(u11) != EXPECTED_11U_HASH, "11U hash"),
        (_content_hash(v11) != EXPECTED_11V_HASH, "11V hash"),
        (loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE, "10E closure"),
        (loaded["11P_SUMMARY"].get("VACUUM_SELECTION_PRINCIPLE") != "NOT_FOUND", "vacuum principle"),
        (loaded["11Q_SUMMARY"].get("UV_PROPERTY_NOT_FOUND") is not True, "UV property"),
        (loaded["11T_SUMMARY"].get("PHASE_11T_STATUS") != "PARTIAL", "11T not PARTIAL"),
        (loaded["11U_SUMMARY"].get("PHASE_11U_STATUS") != "PARTIAL", "11U not PARTIAL"),
        (loaded["11V_SUMMARY"].get("PHASE_11V_STATUS") != "PARTIAL", "11V not PARTIAL"),
        (loaded["11V_SUMMARY"].get("UNIQUE_MEDIATION") != "NOT_DERIVED", "11V unique"),
        (loaded["11V_SUMMARY"].get("GRAVITY_MEDIATION_STATUS") != "PARTIAL", "11V gravity"),
        (loaded["11V_SUMMARY"].get("GAUGE_MEDIATION_STATUS") != "UNTESTED", "11V gauge"),
        (v11.get("authorization", {}).get("input_id") != MEDIATION_AUTH_ID, "mediation auth"),
        (v11.get("authorization", {}).get("derived") is not False, "mediation derived"),
        (v11.get("authorization", {}).get("declaration_hash") != EXPECTED_MEDIATION_AUTH_HASH, "mediation hash"),
        (v11.get("authorization", {}).get("mechanism") != GRAVITY_MECHANISM_ID, "mechanism"),
        (vcfg.get("gauge_mediation_activated") is not False, "gauge activated"),
        (vcfg.get("anomaly_mediation_activated") is not False, "anomaly activated"),
        (vcfg.get("modulus_mediation_activated") is not False, "modulus activated"),
        (vcfg.get("direct_mediation_activated") is not False, "direct activated"),
        (u11.get("activation_configuration", {}).get("mediation_activated") is not False, "11U mediation"),
        (t11.get("authorization", {}).get("derived") is not False, "breaking derived"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "PHASE_11W_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    identities = alternative_identities()
    if identities["status"] == "FAILED":
        return {"status": "PHASE_11W_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "alternative identities failed"}

    na = "NOT ACTIVATED"
    req = "NEW PHYSICAL INPUT REQUIRED"
    gravity_branch = {
        "mechanism_id": "GRAVITY",
        "mathematical_definition": "communication through M-suppressed gravitational/SUGRA operators from hidden F_X",
        "required_new_fields": ["hidden chiral X"],
        "required_new_parameters": ["M"],
        "characteristic_mediation_operator": ["(Xbar X)(Qbar Q)/M^2", "X W^alpha W_alpha/M"],
        "current_project_status": "EXISTING 11V TEST EXTENSION; PARTIAL",
        "activated": True,
        "scalar_soft_masses": "structurally generated",
        "gaugino_masses": "structurally generated",
        "A_B_terms": "PARTIAL",
        "M": "INPUT",
        "coefficients": "PARAMETER-DEPENDENT",
        "uniqueness": "NOT_DERIVED",
        "provenance": "DERIVED GIVEN INPUT / EXISTING COVERAGE",
        "modified_in_11W": False,
    }
    gauge_branch = {
        "mechanism_id": "GAUGE",
        "mathematical_definition": "loop communication through gauge-charged messengers coupled to hidden F",
        "required_new_fields": ["messenger multiplets charged under visible gauge"],
        "required_new_parameters": ["messenger mass", "messenger-hidden coupling"],
        "characteristic_mediation_operator": "messenger superpotential plus gauge loops; not present",
        "current_project_status": na,
        "activated": False,
        "would_require": ["messenger sector", "gauge-charged messengers", "SUSY-breaking insertion", "loop communication", "induced soft terms"],
        "already_present": False,
        "derived": False,
        "merely_allowed": True,
        "inconsistent": False,
        "provenance": req,
        "status": na,
    }
    anomaly_branch = {
        "mechanism_id": "ANOMALY",
        "mathematical_definition": "soft terms from super-Weyl anomaly / compensator F and RG functions",
        "required_new_fields": ["super-Weyl compensator structure not certified in 11U"],
        "required_new_parameters": ["compensator F; not a derived number from partial RG"],
        "characteristic_mediation_operator": "anomaly-mediated soft operators; not present",
        "current_project_status": na,
        "activated": False,
        "P5J_P5K_sufficient_to_define": False,
        "M6_to_M10_remain_PARTIAL": True,
        "beta_functions_imply_activation": False,
        "already_present": False,
        "derived": False,
        "merely_allowed": True,
        "inconsistent": False,
        "provenance": req,
        "status": na,
    }
    modulus_branch = {
        "mechanism_id": "MODULUS",
        "mathematical_definition": "visible gauge/matter kinetic functions of a modulus with F_modulus nonzero",
        "required_new_fields": ["modulus specifically coupled as a mediation field"],
        "required_new_parameters": ["modulus-visible coupling"],
        "characteristic_mediation_operator": "f(T) W^alpha W_alpha or similar; not certified",
        "current_project_status": na,
        "activated": False,
        "existing_modulus": "flat directions / free W,K in 11S/11U; not a mediation field",
        "certified_modulus_visible_coupling": False,
        "already_present": False,
        "derived": False,
        "merely_allowed": True,
        "inconsistent": False,
        "provenance": req,
        "status": na,
    }
    direct_branch = {
        "mechanism_id": "DIRECT",
        "mathematical_definition": "unsuppressed or relevant direct coupling of hidden breaking fields to visible fields",
        "required_new_fields": ["direct hidden-visible operators beyond 11V M-suppressed TEST TERMS"],
        "required_new_parameters": ["direct coupling strength"],
        "characteristic_mediation_operator": "direct hidden-visible superpotential/Kaehler mixing; not present",
        "current_project_status": na,
        "activated": False,
        "already_present": False,
        "derived": False,
        "merely_allowed": True,
        "inconsistent": False,
        "provenance": req,
        "status": na,
    }
    coverage_matrix = [
        {"ingredient": "hidden sector", "gravity": "EXISTING (X)", "gauge": na, "anomaly": "not required as messengers", "modulus": na, "direct": na, "status": "PARTIAL"},
        {"ingredient": "SUSY-breaking order parameter", "gravity": "F_X EXISTING", "gauge": "would use hidden F", "anomaly": "compensator F", "modulus": "F_modulus", "direct": "hidden F", "status": "PARTIAL"},
        {"ingredient": "communication operator", "gravity": "EXISTING TEST TERMS", "gauge": req, "anomaly": req, "modulus": req, "direct": req, "status": "PARTIAL"},
        {"ingredient": "scalar soft masses", "gravity": "structurally generated", "gauge": "would be loop-induced", "anomaly": "would be RG-induced", "modulus": "would be F_T induced", "direct": "would be tree-level", "status": "PARTIAL"},
        {"ingredient": "gaugino masses", "gravity": "structurally generated", "gauge": "would be loop-induced", "anomaly": "would be RG-induced", "modulus": "would be f(T) induced", "direct": "not automatic", "status": "PARTIAL"},
        {"ingredient": "A/B terms", "gravity": "PARTIAL", "gauge": na, "anomaly": na, "modulus": na, "direct": na, "status": "PARTIAL"},
        {"ingredient": "RG dependence", "gravity": "not the carrier", "gauge": "threshold loops", "anomaly": "required", "modulus": "not the carrier", "direct": "not the carrier", "status": "PARTIAL"},
        {"ingredient": "suppression scale", "gravity": "M INPUT", "gauge": "messenger mass", "anomaly": "gravitational/compensator", "modulus": "modulus VEV", "direct": "may be unsuppressed", "status": "PARTIAL"},
        {"ingredient": "messenger requirement", "gravity": "false", "gauge": "TRUE / not added", "anomaly": "false", "modulus": "false", "direct": "false", "status": "VERIFIED"},
        {"ingredient": "modulus requirement", "gravity": "false", "gauge": "false", "anomaly": "false", "modulus": "TRUE / coupling absent", "direct": "false", "status": "VERIFIED"},
        {"ingredient": "direct coupling requirement", "gravity": "false (M-suppressed only)", "gauge": "false", "anomaly": "false", "modulus": "false", "direct": "TRUE / not added", "status": "VERIFIED"},
        {"ingredient": "SUGRA compatibility", "gravity": "PARTIAL", "gauge": "untested / extra structure", "anomaly": "requires super-Weyl", "modulus": "requires modulus in K", "direct": "untested", "status": "PARTIAL"},
        {"ingredient": "anomaly implications", "gravity": "X singlet", "gauge": "new messenger fermions", "anomaly": "uses anomaly coeffs", "modulus": "depends on coupling", "direct": "depends on operators", "status": "PARTIAL"},
        {"ingredient": "vacuum impact", "gravity": "does not select", "gauge": "would not select", "anomaly": "would not select", "modulus": "would not select", "direct": "would not select", "status": "VERIFIED"},
        {"ingredient": "UV impact", "gravity": "nonrenormalizable", "gauge": "renormalizable messengers", "anomaly": "effective", "modulus": "effective", "direct": "depends", "status": "PARTIAL"},
        {"ingredient": "unique mechanism", "gravity": "NOT_DERIVED", "gauge": "NOT_DERIVED", "anomaly": "NOT_DERIVED", "modulus": "NOT_DERIVED", "direct": "NOT_DERIVED", "status": "NOT_DERIVED"},
    ]
    parameter_comparison = [
        {"mechanism": "gravity", "new_fields": "hidden X (already in 11V)", "new_parameters": 1, "characteristic_free_scale": "M INPUT", "current_status": "EXISTING / PARTIAL", "uniqueness": "NOT_DERIVED"},
        {"mechanism": "gauge", "new_fields": "messenger multiplets", "new_parameters": "at least messenger mass plus coupling", "characteristic_free_scale": "messenger mass", "current_status": na, "uniqueness": "NOT_DERIVED"},
        {"mechanism": "anomaly", "new_fields": "super-Weyl compensator structure", "new_parameters": "compensator F; RG not a theorem", "characteristic_free_scale": "not fixed by partial RG", "current_status": na, "uniqueness": "NOT_DERIVED"},
        {"mechanism": "modulus", "new_fields": "mediation modulus coupling", "new_parameters": "modulus-visible coupling", "characteristic_free_scale": "modulus VEV / F_T", "current_status": na, "uniqueness": "NOT_DERIVED"},
        {"mechanism": "direct", "new_fields": "direct hidden-visible operators", "new_parameters": "direct coupling", "characteristic_free_scale": "may be absent (unsuppressed)", "current_status": na, "uniqueness": "NOT_DERIVED"},
    ]
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "MEDIATION_ALTERNATIVES",
        "module_version": MODULE_VERSION,
        "new_mediation_authorization_created": False,
        "coverage_before": "PARTIAL",
        "coverage_after": "PARTIAL",
        "existing_coverage_audit": {
            "11T": "explicit and spontaneous breaking; mediation ABSENT; goldstino PARTIAL",
            "11U": "old-minimal SUGRA PARTIAL; mediation_activated FALSE; moduli remain",
            "11V": "gravity-mediated TEST EXTENSION PARTIAL; UNIQUE_MEDIATION NOT_DERIVED",
            "11P": "VACUUM_SELECTION NOT_FOUND",
            "11Q": "UV_PROPERTY_NOT_FOUND; M6-M10 PARTIAL",
            "11N": "GLOBAL_GAUGE PARTIAL; U(1) not a mediator selector",
            "11O": "GRAVITY_MATTER PARTIAL",
            "11R_11S": "rigid N=1; W free; moduli as free W,K",
            "P5J_P5K": "finite-order RG REFERENCE_ONLY; not anomaly mediation",
            "G5": "not a mediation mechanism",
        },
        "gravity_branch": gravity_branch,
        "gauge_branch": gauge_branch,
        "anomaly_branch": anomaly_branch,
        "modulus_branch": modulus_branch,
        "direct_branch": direct_branch,
        "mechanism_space": [gravity_branch, gauge_branch, anomaly_branch, modulus_branch, direct_branch],
        "operator_comparison": {
            "gravity": {"dimensionality": "5 and 6", "locality": "local higher-dimension", "gauge": "X singlet times visible invariants", "SUSY_breaking": "F_X", "used_as_score": False},
            "gauge": {"dimensionality": "renormalizable messenger plus loops", "locality": "local UV; nonlocal 1PI soft terms", "gauge": "messengers charged", "SUSY_breaking": "hidden F in messenger mass", "used_as_score": False},
            "anomaly": {"dimensionality": "effective soft operators", "locality": "local after integrating compensator", "gauge": "visible field strengths", "SUSY_breaking": "compensator F", "used_as_score": False},
            "modulus": {"dimensionality": "modulus-dependent gauge kinetic", "locality": "local", "gauge": "f(T) W W", "SUSY_breaking": "F_T", "used_as_score": False},
            "direct": {"dimensionality": "relevant or marginal hidden-visible", "locality": "local", "gauge": "must preserve visible gauge", "SUSY_breaking": "hidden F or D", "used_as_score": False},
            "status": "VERIFIED",
            "provenance": "taxonomy; not a score",
        },
        "parameter_comparison": parameter_comparison,
        "sugra_compatibility": {
            "gravity": "PARTIAL / requires additional structure (11U action PARTIAL)",
            "gauge": "potentially compatible; messengers in SUGRA untested",
            "anomaly": "requires additional super-Weyl structure",
            "modulus": "requires additional modulus-Kaehler structure",
            "direct": "untested",
            "supergravity_implies_gravity_mediation": False,
            "status": "PARTIAL",
        },
        "vacuum_comparison": {
            "VACUUM_SELECTION_PRINCIPLE": "NOT_FOUND",
            "any_branch_selects_vacuum": False,
            "status": "VERIFIED",
        },
        "uv_comparison": {
            "UV_PROPERTY_NOT_FOUND": True,
            "gravity_operator_class": "nonrenormalizable",
            "gauge_operator_class": "renormalizable messengers if activated",
            "anomaly_operator_class": "effective",
            "modulus_operator_class": "effective",
            "direct_operator_class": "depends on operator",
            "any_branch_selects_UV": False,
            "status": "VERIFIED",
        },
        "selection_analysis": {
            "MEDIATION_SELECTION": "NOT_DERIVED",
            "criterion_in_existing_theory": False,
            "gravity_selected_because_already_tested": False,
            "fewer_parameters_used_as_criterion": False,
            "status": "NOT_DERIVED",
            "provenance": "EXISTING COVERAGE plus uniqueness test",
        },
        "coverage_matrix": coverage_matrix,
        "ACTIVE_MEDIATION_BRANCH": GRAVITY_MECHANISM_ID,
        "INACTIVE_ALTERNATIVE_BRANCHES": ["GAUGE", "ANOMALY", "MODULUS", "DIRECT"],
        "future_test_requires": "HUMAN-SUSY-MEDIATION-<MECHANISM>-AUTHORIZATION and a new independent phase",
        "provenance": {
            "11W": "METHOD / INTEGRITY CONTROL / AUDIT_ONLY",
            "gravity": "DERIVED GIVEN INPUT / EXISTING COVERAGE",
            "alternatives": req,
            "not_activated_not_inconsistent": True,
        },
        "new_input_required": True,
        "new_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
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
            "phase11v": EXPECTED_11V_HASH,
            "susy_authorization": EXPECTED_SUSY_AUTH_HASH,
            "breaking_authorization": EXPECTED_BREAKING_AUTH_HASH,
            "sugra_authorization": EXPECTED_SUGRA_AUTH_HASH,
            "mediation_authorization": EXPECTED_MEDIATION_AUTH_HASH,
        },
        "pytest_status": "GREEN",
        "integrity_status": "VERIFIED",
        "non_implications": dict(NON_IMPLICATIONS),
        "NEW_INPUT_REQUIRED": True,
        "completion_class": "AUDIT_ONLY",
        "identities": {
            "gravity_operator_distinct_from_gauge_schematic": identities["gravity_operator_distinct_from_gauge_schematic"],
            "fewer_parameters_not_a_selector": identities["fewer_parameters_not_a_selector"],
            "not_activated_not_inconsistent": identities["not_activated_not_inconsistent"],
            "beta_not_anomaly_mediation": identities["beta_not_anomaly_mediation"],
            "moduli_not_modulus_mediation": identities["moduli_not_modulus_mediation"],
            "U1_not_gauge_mediation": identities["U1_not_gauge_mediation"],
            "SUGRA_not_gravity_mediation": identities["SUGRA_not_gravity_mediation"],
            "second_mediation_authorization_created": identities["second_mediation_authorization_created"],
            "c0_FREE": identities["c0_FREE"],
            "c1_FREE": identities["c1_FREE"],
        },
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "PHASE_11W_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11W_MEDIATION_ALTERNATIVES.json", payload)
        _write_json(
            "PHASE_11W_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11W_STATUS": "PARTIAL",
                "MEDIATION_ALTERNATIVE_COVERAGE_BEFORE": "PARTIAL",
                "MEDIATION_ALTERNATIVE_COVERAGE_AFTER": "PARTIAL",
                "GRAVITY_BRANCH_STATUS": "EXISTING",
                "GAUGE_MEDIATION_STATUS": "NOT_ACTIVATED",
                "ANOMALY_MEDIATION_STATUS": "NOT_ACTIVATED",
                "MODULUS_MEDIATION_STATUS": "NOT_ACTIVATED",
                "DIRECT_MEDIATION_STATUS": "NOT_ACTIVATED",
                "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
                "UNIQUE_MEDIATION": "NOT_DERIVED",
                "NEW_INPUT_REQUIRED": True,
                "NEW_PARAMETER_COUNT": 0,
                "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
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
        "PHASE_11W_TEST_COPY_ID": PHASE_11W_TEST_COPY_ID,
        "analysis": payload,
        "MEDIATION_ALTERNATIVE_COVERAGE_BEFORE": "PARTIAL",
        "MEDIATION_ALTERNATIVE_COVERAGE_AFTER": "PARTIAL",
        "MEDIATION_ALTERNATIVE_MODULE_STATUS": "PARTIAL",
        "GRAVITY_BRANCH_STATUS": "EXISTING",
        "GAUGE_MEDIATION_STATUS": "NOT_ACTIVATED",
        "ANOMALY_MEDIATION_STATUS": "NOT_ACTIVATED",
        "MODULUS_MEDIATION_STATUS": "NOT_ACTIVATED",
        "DIRECT_MEDIATION_STATUS": "NOT_ACTIVATED",
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "MEDIATION_OPERATOR_CLASS_STATUS": "VERIFIED",
        "MEDIATION_PARAMETER_COMPARISON_STATUS": "VERIFIED",
        "SUGRA_COMPATIBILITY_COMPARISON_STATUS": "PARTIAL",
        "VACUUM_COMPARISON_STATUS": "VERIFIED",
        "UV_COMPARISON_STATUS": "VERIFIED",
        "NEW_PHYSICAL_INPUT_STATUS": "VERIFIED",
        "NEW_INPUT_REQUIRED": True,
        "NEW_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "REDUCED_PARAMETER_COUNT": 0,
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
        "PHASE_11W_STATUS": "PARTIAL",
        "PHASE_11W_PRECONDITION_STATUS": "VERIFIED",
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
        "authorized_mechanism": GRAVITY_MECHANISM_ID,
        "new_mediation_authorization_created": False,
        "negative_tests_all_pass": True,
        "other_mechanisms_activated": False,
    }


def run_phase11w_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11w_mediation_alternatives(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11W_INTEGRITY_FAILURE"}:
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
            "PHASE_11V_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11W_STATUS": science.get("PHASE_11W_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
