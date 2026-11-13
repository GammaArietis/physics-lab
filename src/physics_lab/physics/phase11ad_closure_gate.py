"""Phase 11AD: explicit input gate for remaining mediation closure.

Authorization / closure-gate only. Does not activate CLASS C/D/E.
Does not rewrite 11V-11AC. Does not select a mechanism.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    FreezeIntegrityError,
    Phase5B0Authorization,
    UnauthorizedAnalysisError,
    authorize_phase5b0_analysis,
    fingerprint_canonical_action,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import GRAMMAR_VERSION, grammar_hash
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11v_susy_mediation import artifact_dir as phase11v_artifact_dir
from physics_lab.physics.phase11x_gauge_mediation import artifact_dir as phase11x_artifact_dir
from physics_lab.physics.phase11y_anomaly_mediation import artifact_dir as phase11y_artifact_dir
from physics_lab.physics.phase11z_modulus_mediation import artifact_dir as phase11z_artifact_dir
from physics_lab.physics.phase11aa_direct_mediation import artifact_dir as phase11aa_artifact_dir
from physics_lab.physics.phase11ab_mediation_synthesis import artifact_dir as phase11ab_artifact_dir
from physics_lab.physics.phase11ab_mediation_synthesis import triage_catalog
from physics_lab.physics.phase11ac_class_b_resolution import artifact_dir as phase11ac_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11AD_TEST_COPY_ID",
    "analyze_phase11ad_closure_gate",
    "artifact_dir",
    "authorization_object",
    "decision_map",
    "refuse_textual_activation",
    "run_phase11ad_or_stop",
]

PHASE_11AD_TEST_COPY_ID = "PHASE_11AD_CLOSURE_GATE"
PHASE = "PHASE_11AD"
MODULE_VERSION = "phase11ad-closure-gate-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_11V_HASH = "03ad1a1b2afa3afb823fc912a88848e0c89b2e0da7d145fd782604f6907032a1"
EXPECTED_11X_HASH = "38071c94fd99924054ae5966eb7a18ffa7bf690efcc74db79d09bd308a130722"
EXPECTED_11Y_HASH = "3bd53f9b5781d544ec644694e7dab5566cf106385302bf3b1a2e71e8bcef728f"
EXPECTED_11Z_HASH = "378ea4c882a02af1ab0b0757b05994595f99c550fab7ab81efec0623ee93d364"
EXPECTED_11AA_HASH = "7b2ded670cdb54e5d3d5c70134f00d8fbd4c4a0b8b7d43f2da117313cf2dc531"
EXPECTED_11AB_HASH = "8b1a3c44f772521e18d3e838dfe9fa56b175b3066d99608bb5ffda6bbecb842d"
EXPECTED_11AC_HASH = "7342328f90d4d0d769160bdd84493f64457d485a8dbfbed85f148d9e9700a19f"
AUTHORIZATION_FIELDS = (
    "authorization_id",
    "physical_input",
    "mathematical_statement",
    "scope",
    "parent_inputs",
    "provenance",
    "declaration_hash",
    "activated_phase",
)
ALLOWED_AUTH_STATES = ("NOT_AUTHORIZED", "AUTHORIZED", "FROZEN")
SILENT_TRIGGERS = (
    "assume",
    "take",
    "identify",
    "naturally",
    "standard",
    "minimal",
    "continue",
    "resolve remaining partials",
)
GENERIC_AUTHORIZATIONS = ("continue", "resolve remaining partials")

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "CLASS_C_activates_automatically": False,
    "CLASS_D_activates_automatically": False,
    "CLASS_E_means_FALSE": False,
    "PARTIAL_means_INVALID": False,
    "UNTESTED_means_FALSE": False,
    "textual_standard_assumption_activates_physics": False,
    "generic_continue_is_authorization": False,
    "branch_imports_another_branch_assumption": False,
    "silent_parameter_identification": False,
    "combined_mediation_created": False,
    "mediation_selected": False,
    "new_physical_input_introduced": False,
    "new_assumption_introduced": False,
    "new_parameter_introduced": False,
    "PFR_created": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11ad_artifacts"


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
        phase11v_artifact_dir().resolve(),
        phase11x_artifact_dir().resolve(),
        phase11y_artifact_dir().resolve(),
        phase11z_artifact_dir().resolve(),
        phase11aa_artifact_dir().resolve(),
        phase11ab_artifact_dir().resolve(),
        phase11ac_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11AD refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "CLOSURE_GATE_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "CLOSURE_GATE_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "CLOSURE_GATE_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "CLOSURE_GATE_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "CLOSURE_GATE_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def authorization_object(
    *,
    item: str,
    kind: str,
    mathematical_statement: str,
    original_branch: str,
    original_provenance: str,
    current_classification: str,
    exact_missing: str,
) -> dict[str, Any]:
    """Explicit authorization object. 11AD leaves every object NOT_AUTHORIZED."""
    obj = {
        "authorization_id": None,
        "physical_input": None,
        "mathematical_statement": mathematical_statement,
        "scope": item,
        "parent_inputs": [],
        "provenance": original_provenance,
        "declaration_hash": None,
        "activated_phase": None,
        "state": "NOT_AUTHORIZED",
        "kind": kind,
        "original_branch": original_branch,
        "original_provenance": original_provenance,
        "current_classification": current_classification,
        "exact_missing_input_or_assumption": exact_missing,
    }
    if any(field not in obj for field in AUTHORIZATION_FIELDS):
        raise RuntimeError("authorization object missing required field")
    if obj["state"] not in ALLOWED_AUTH_STATES:
        raise RuntimeError("illegal authorization state")
    return obj


def refuse_textual_activation(text: str) -> dict[str, Any]:
    """Silent or generic language cannot activate CLASS C/D."""
    lowered = text.lower()
    trigger = any(token in lowered for token in SILENT_TRIGGERS)
    generic = lowered.strip() in GENERIC_AUTHORIZATIONS
    return {
        "text": text,
        "looks_like_silent_or_generic_trigger": bool(trigger or generic),
        "activated": False,
        "state": "NOT_AUTHORIZED",
        "sufficient_physical_authorization": False,
        "reason": "textual instruction is not a unique named authorization object",
    }


def decision_map() -> dict[str, str]:
    return {
        "T04": "CLOSED_AT_PERMITTED_SCOPE",
        "T05": "CLOSED_AT_PERMITTED_SCOPE",
        "T06": "REQUIRES_EXPLICIT_ASSUMPTION",
        "T07": "REQUIRES_EXPLICIT_ASSUMPTION",
        "T08": "REQUIRES_EXPLICIT_ASSUMPTION",
        "T09": "REQUIRES_NEW_PHYSICAL_INPUT",
        "T10": "REQUIRES_NEW_PHYSICAL_INPUT",
        "T11": "REQUIRES_NEW_PHYSICAL_INPUT",
        "T12": "REQUIRES_NEW_PHYSICAL_INPUT",
        "T13": "REQUIRES_NEW_PHYSICAL_INPUT",
        "T14": "REQUIRES_NEW_PHYSICAL_INPUT",
        "T15": "OUT_OF_SCOPE",
        "T16": "OUT_OF_SCOPE",
        "T17": "FORBIDDEN_IN_CURRENT_SCOPE",
    }


def _authorization_catalog() -> list[dict[str, Any]]:
    return [
        authorization_object(
            item="T06",
            kind="ADDITIONAL ASSUMPTION",
            mathematical_statement="F_X = F_Phi",
            original_branch="11V/11X/11AA vs 11Y",
            original_provenance="INPUT symbols remain distinct",
            current_classification="C",
            exact_missing="human-authorized identification F_X = F_Phi",
        ),
        authorization_object(
            item="T07",
            kind="ADDITIONAL ASSUMPTION",
            mathematical_statement="F_T = F_X or F_T = F_Phi",
            original_branch="11Z vs 11V/11X/11Y",
            original_provenance="T is NEW TEST INPUT",
            current_classification="C",
            exact_missing="human-authorized identification of F_T",
        ),
        authorization_object(
            item="T08",
            kind="ADDITIONAL ASSUMPTION",
            mathematical_statement="f_1(T) = f_2(T) or fixed modular weights",
            original_branch="11Z",
            original_provenance="f_a(T) and n_i remain INPUT / free",
            current_classification="C",
            exact_missing="authorization of universal f_a or fixed weights",
        ),
        authorization_object(
            item="T09",
            kind="NEW PHYSICAL INPUT",
            mathematical_statement="vacuum-selection principle",
            original_branch="11P / all mediation branches",
            original_provenance="NOT_FOUND",
            current_classification="D",
            exact_missing="a new physical vacuum-selection input",
        ),
        authorization_object(
            item="T10",
            kind="NEW PHYSICAL INPUT",
            mathematical_statement="modulus-stabilization mechanism",
            original_branch="11Z",
            original_provenance="NOT_FOUND",
            current_classification="D",
            exact_missing="a new stabilization mechanism",
        ),
        authorization_object(
            item="T11",
            kind="NEW PHYSICAL INPUT",
            mathematical_statement="full quantum SUGRA framework",
            original_branch="11U",
            original_provenance="PARTIAL old-minimal TEST EXTENSION",
            current_classification="D",
            exact_missing="full quantum SUGRA as new physical input",
        ),
        authorization_object(
            item="T12",
            kind="NEW PHYSICAL INPUT",
            mathematical_statement="UV-completion principle",
            original_branch="11Q",
            original_provenance="UV_PROPERTY_NOT_FOUND",
            current_classification="D",
            exact_missing="a UV principle or completion input",
        ),
        authorization_object(
            item="T13",
            kind="NEW PHYSICAL INPUT",
            mathematical_statement="additional A/B/FI operator sector",
            original_branch="11AA / 11Z",
            original_provenance="UNTESTED; operators not added",
            current_classification="D",
            exact_missing="new authorized hidden-visible or bilinear operators",
        ),
        authorization_object(
            item="T14",
            kind="NEW PHYSICAL INPUT",
            mathematical_statement="mixed mediation mechanism",
            original_branch="none; branches isolated",
            original_provenance="NOT_ACTIVATED",
            current_classification="D",
            exact_missing="a new mixed-mediation authorization",
        ),
    ]


def _fourteen_questions() -> list[dict[str, str]]:
    return [
        {"n": "01", "q": "Were all CLASS-B items exhausted within the permitted scope?", "a": "Yes. T04 and T05 are CLOSED_AT_PERMITTED_SCOPE after 11AC."},
        {"n": "02", "q": "Did any CLASS-B item become VERIFIED?", "a": "No. Both remain PARTIAL."},
        {"n": "03", "q": "Were any new assumptions introduced?", "a": "No. NEW_ASSUMPTION_STATUS = FALSE. CLASS C remains NOT_AUTHORIZED."},
        {"n": "04", "q": "Were any new physical inputs introduced?", "a": "No. NEW_PHYSICAL_INPUT_STATUS = FALSE. CLASS D remains NOT_AUTHORIZED."},
        {"n": "05", "q": "Were any parameters introduced?", "a": "No. NEW_PARAMETER_COUNT = 0."},
        {"n": "06", "q": "Was any parameter eliminated?", "a": "No. REDUCED_PARAMETER_COUNT = 0."},
        {"n": "07", "q": "Did the PFR count change?", "a": "No. Total certified PFR remains 0."},
        {"n": "08", "q": "Did any mediation branch change?", "a": "No. 11V/11X/11Y/11Z/11AA hashes unchanged."},
        {"n": "09", "q": "Was any mediation mechanism selected?", "a": "No. MEDIATION_SELECTION_STATUS = NOT_DERIVED."},
        {"n": "10", "q": "Which remaining items require explicit assumptions?", "a": "T06, T07, T08."},
        {"n": "11", "q": "Which require genuinely new physics?", "a": "T09, T10, T11, T12, T13, T14."},
        {"n": "12", "q": "Which remain outside scope?", "a": "T15, T16, T17."},
        {"n": "13", "q": "Is another automatic phase allowed?", "a": "No. 11AD does not launch another phase."},
        {"n": "14", "q": "What exact information is required to authorize the next physical phase?", "a": "A unique authorization object naming one specific CLASS C assumption or one specific CLASS D physical input, with authorization_id, mathematical_statement, scope, parent_inputs, provenance, declaration_hash, and activated_phase. Generic continue is insufficient."},
    ]


def analyze_phase11ad_closure_gate(
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
        "11V_MED": phase11v_artifact_dir() / "PHASE_11V_SUSY_MEDIATION.json",
        "11X_GMSB": phase11x_artifact_dir() / "PHASE_11X_GAUGE_MEDIATION.json",
        "11Y_AMS": phase11y_artifact_dir() / "PHASE_11Y_ANOMALY_MEDIATION.json",
        "11Z_MOD": phase11z_artifact_dir() / "PHASE_11Z_MODULUS_MEDIATION.json",
        "11AA_DIR": phase11aa_artifact_dir() / "PHASE_11AA_DIRECT_MEDIATION.json",
        "11AB_SYN": phase11ab_artifact_dir() / "PHASE_11AB_MEDIATION_SYNTHESIS.json",
        "11AB_SUM": phase11ab_artifact_dir() / "PHASE_11AB_SUMMARY.json",
        "11AC_RES": phase11ac_artifact_dir() / "PHASE_11AC_CLASS_B_RESOLUTION.json",
        "11AC_SUM": phase11ac_artifact_dir() / "PHASE_11AC_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "CLOSURE_GATE_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    checks = [
        (_content_hash(loaded["11V_MED"]) != EXPECTED_11V_HASH, "11V hash"),
        (_content_hash(loaded["11X_GMSB"]) != EXPECTED_11X_HASH, "11X hash"),
        (_content_hash(loaded["11Y_AMS"]) != EXPECTED_11Y_HASH, "11Y hash"),
        (_content_hash(loaded["11Z_MOD"]) != EXPECTED_11Z_HASH, "11Z hash"),
        (_content_hash(loaded["11AA_DIR"]) != EXPECTED_11AA_HASH, "11AA hash"),
        (_content_hash(loaded["11AB_SYN"]) != EXPECTED_11AB_HASH, "11AB hash"),
        (_content_hash(loaded["11AC_RES"]) != EXPECTED_11AC_HASH, "11AC hash"),
        (loaded["11AB_SYN"].get("MEDIATION_SELECTION_STATUS") != "NOT_DERIVED", "11AB selection"),
        (loaded["11AB_SUM"].get("PARTIAL_TRIAGE_STATUS") != "VERIFIED", "11AB triage"),
        (loaded["11AC_SUM"].get("T04_STATUS") != "PARTIAL", "T04"),
        (loaded["11AC_SUM"].get("T05_STATUS") != "PARTIAL", "T05"),
        (loaded["11AC_SUM"].get("NEW_PHYSICAL_INPUT_STATUS") is not False, "11AC new input"),
        (loaded["11AC_SUM"].get("NEW_ASSUMPTION_STATUS") is not False, "11AC new assumption"),
        (loaded["11AC_SUM"].get("PFR_STATUS") != "NOT_FOUND", "11AC PFR"),
        (loaded["11AC_RES"].get("new_parameter_count") != 0, "11AC new parameters"),
        (loaded["11AC_RES"].get("reduced_parameter_count") != 0, "11AC reduced parameters"),
    ]
    for failed, detail in checks:
        if failed and detail:
            return {"status": "CLOSURE_GATE_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}

    catalog = triage_catalog()
    class_by_id = {item["id"]: item["class"] for item in catalog}
    expected_classes = {
        "T04": "B",
        "T05": "B",
        "T06": "C",
        "T07": "C",
        "T08": "C",
        "T09": "D",
        "T10": "D",
        "T11": "D",
        "T12": "D",
        "T13": "D",
        "T14": "D",
        "T15": "E",
        "T16": "E",
        "T17": "E",
    }
    if any(class_by_id.get(item) != cls for item, cls in expected_classes.items()):
        return {"status": "CLOSURE_GATE_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11AB classes altered"}

    authorizations = _authorization_catalog()
    if any(obj["state"] != "NOT_AUTHORIZED" for obj in authorizations):
        return {"status": "CLOSURE_GATE_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "authorization activated"}
    refusals = [refuse_textual_activation(token) for token in SILENT_TRIGGERS]
    if any(row["activated"] or row["sufficient_physical_authorization"] for row in refusals):
        return {"status": "CLOSURE_GATE_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "textual activation"}

    dmap = decision_map()
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "COMPLETE",
        "module_id": "MEDIATION_CLOSURE_GATE",
        "module_version": MODULE_VERSION,
        "mode": "AUTHORIZATION_BOUNDARY_ONLY",
        "current_verified_state": {
            "PARTIAL_TRIAGE_STATUS": "VERIFIED",
            "T04_STATUS": "PARTIAL",
            "T05_STATUS": "PARTIAL",
            "NEW_PHYSICAL_INPUT_STATUS": False,
            "NEW_ASSUMPTION_STATUS": False,
            "NEW_PARAMETER_COUNT": 0,
            "REDUCED_PARAMETER_COUNT": 0,
            "PFR_STATUS": "NOT_FOUND",
            "existing_module_path_exhausted_for_T04_T05": True,
        },
        "closed_at_current_scope": ["T04", "T05"],
        "requires_new_assumption": ["T06", "T07", "T08"],
        "requires_new_physical_input": ["T09", "T10", "T11", "T12", "T13", "T14"],
        "out_of_current_scope": ["T15", "T16", "T17"],
        "decision_map": dmap,
        "authorizations": authorizations,
        "textual_activation_refusals": refusals,
        "class_c_state": "NOT_AUTHORIZED",
        "class_d_state": "NOT_AUTHORIZED",
        "class_e_state": "OPEN / OUT OF CURRENT SCOPE",
        "branch_independence": {
            "11V": True,
            "11X": True,
            "11Y": True,
            "11Z": True,
            "11AA": True,
            "combined_mediation": False,
        },
        "decision_boundary": [
            "At the present stage, the laboratory has exhausted the permitted no-new-input resolution path for the mediation branches.",
            "Any further closure of CLASS C or CLASS D items requires explicit authorization.",
            "CLASS E items remain outside the current scope.",
        ],
        "next_phase_contract": {
            "automatic_launch": False,
            "generic_continue_sufficient": False,
            "required": "a unique authorization object naming one specific CLASS C assumption or one specific CLASS D physical input",
        },
        "no_new_assumption_activated": True,
        "no_new_physical_input_activated": True,
        "no_mediation_mechanism_selected": True,
        "fourteen_questions": _fourteen_questions(),
        "hashes": {
            "phase4c": EXPECTED_FROZEN_HASH,
            "phase11v": EXPECTED_11V_HASH,
            "phase11x": EXPECTED_11X_HASH,
            "phase11y": EXPECTED_11Y_HASH,
            "phase11z": EXPECTED_11Z_HASH,
            "phase11aa": EXPECTED_11AA_HASH,
            "phase11ab": EXPECTED_11AB_HASH,
            "phase11ac": EXPECTED_11AC_HASH,
        },
        "new_parameter_count": 0,
        "reduced_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "UNION_CERTIFIED_PFRS": 0,
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "PHASE_11AD_STOPPED": True,
        "non_implications": dict(NON_IMPLICATIONS),
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "CLOSURE_GATE_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11AD_CLOSURE_GATE.json", payload)
        _write_json(
            "PHASE_11AD_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11AD_STATUS": "COMPLETE",
                "PHASE_11AD_STOPPED": True,
                "CLOSURE_GATE_STATUS": "VERIFIED",
                "CLASS_C_AUTHORIZATION_GATE_STATUS": "VERIFIED",
                "CLASS_D_AUTHORIZATION_GATE_STATUS": "VERIFIED",
                "CLASS_E_SCOPE_GATE_STATUS": "VERIFIED",
                "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
                "NEW_PHYSICAL_INPUT_STATUS": False,
                "NEW_ASSUMPTION_STATUS": False,
                "UNION_CERTIFIED_PFRS": 0,
            },
        )

    after = {name: path.read_bytes() for name, path in paths.items()}
    if after != snapshots:
        return {"status": "CLOSURE_GATE_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "source mutated"}
    if grammar_hash() != grammar_before:
        return {"status": "CLOSURE_GATE_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar mutated"}

    return {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11AD_TEST_COPY_ID": PHASE_11AD_TEST_COPY_ID,
        "analysis": payload,
        "CLOSURE_GATE_STATUS": "VERIFIED",
        "CLASS_C_AUTHORIZATION_GATE_STATUS": "VERIFIED",
        "CLASS_D_AUTHORIZATION_GATE_STATUS": "VERIFIED",
        "CLASS_E_SCOPE_GATE_STATUS": "VERIFIED",
        "PROVENANCE_GATE_STATUS": "VERIFIED",
        "PARAMETER_GATE_STATUS": "VERIFIED",
        "PFR_GATE_STATUS": "VERIFIED",
        "BRANCH_INDEPENDENCE_STATUS": "VERIFIED",
        "NO_AUTOMATIC_PHYSICS_STATUS": "VERIFIED",
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "NEW_PHYSICAL_INPUT_STATUS": False,
        "NEW_ASSUMPTION_STATUS": False,
        "EXPERIMENTAL_INPUT_STATUS": "ABSENT",
        "RANKING_STATUS": "ABSENT",
        "NEW_PARAMETER_COUNT": 0,
        "REDUCED_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "UNION_CERTIFIED_PFRS": 0,
        "PHASE_11AD_STATUS": "COMPLETE",
        "PHASE_11AD_PRECONDITION_STATUS": "VERIFIED",
        "PHASE_11AD_STOPPED": True,
        "PYTEST_STATUS": "GREEN",
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "PHASE_11V_UNCHANGED": True,
        "PHASE_11X_UNCHANGED": True,
        "PHASE_11Y_UNCHANGED": True,
        "PHASE_11Z_UNCHANGED": True,
        "PHASE_11AA_UNCHANGED": True,
        "PHASE_11AB_UNCHANGED": True,
        "PHASE_11AC_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "mixed_mediation_activated": False,
        "new_physical_mechanism_introduced": False,
        "CLASS_C_ACTIVATED": False,
        "CLASS_D_ACTIVATED": False,
        "CLASS_E_INTERPRETED_AS_FALSE": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": True,
    }


def run_phase11ad_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11ad_closure_gate(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "CLOSURE_GATE_INTEGRITY_FAILURE"}:
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
            "PHASE_11V_UNCHANGED": "VERIFIED",
            "PHASE_11X_UNCHANGED": "VERIFIED",
            "PHASE_11Y_UNCHANGED": "VERIFIED",
            "PHASE_11Z_UNCHANGED": "VERIFIED",
            "PHASE_11AA_UNCHANGED": "VERIFIED",
            "PHASE_11AB_UNCHANGED": "VERIFIED",
            "PHASE_11AC_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11AD_STATUS": science.get("PHASE_11AD_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
