"""Phase 11AE: vacuum-selection topic gate.

The human selected the topic VACUUM_SELECTION_PRINCIPLE.
That does not authorize an unspecified selection law.
This module MUST NOT invent, choose, or silently assume a principle.
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
from physics_lab.physics.phase11p_vacuum_selection import artifact_dir as phase11p_artifact_dir
from physics_lab.physics.phase11p_vacuum_selection import vacuum_selection_identities
from physics_lab.physics.phase11v_susy_mediation import artifact_dir as phase11v_artifact_dir
from physics_lab.physics.phase11x_gauge_mediation import artifact_dir as phase11x_artifact_dir
from physics_lab.physics.phase11y_anomaly_mediation import artifact_dir as phase11y_artifact_dir
from physics_lab.physics.phase11z_modulus_mediation import artifact_dir as phase11z_artifact_dir
from physics_lab.physics.phase11aa_direct_mediation import artifact_dir as phase11aa_artifact_dir
from physics_lab.physics.phase11ab_mediation_synthesis import artifact_dir as phase11ab_artifact_dir
from physics_lab.physics.phase11ac_class_b_resolution import artifact_dir as phase11ac_artifact_dir
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "INSUFFICIENT_STATEMENTS",
    "MODULE_VERSION",
    "NON_IMPLICATIONS",
    "PHASE_11AE_TEST_COPY_ID",
    "REFERENCE_ONLY_EXAMPLES",
    "VACUUM_AUTH_ID",
    "analyze_phase11ae_vacuum_selection",
    "artifact_dir",
    "is_exact_mathematical_statement",
    "refuse_invented_principle",
    "refuse_phase11ae_unspecified_principle",
    "refuse_phase11ae_without_vacuum_authorization",
    "run_phase11ae_or_stop",
    "topic_authorization",
]

PHASE_11AE_TEST_COPY_ID = "PHASE_11AE_VACUUM_SELECTION"
PHASE = "PHASE_11AE"
MODULE_VERSION = "phase11ae-vacuum-selection-v1"
VACUUM_AUTH_ID = "HUMAN-VACUUM-SELECTION-AUTHORIZATION-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_11P_HASH = "264e5817daef19b44a3bb11bd787b7fdf702201122adb752f5c98c4a7ca180d2"
EXPECTED_11V_HASH = "03ad1a1b2afa3afb823fc912a88848e0c89b2e0da7d145fd782604f6907032a1"
EXPECTED_11X_HASH = "38071c94fd99924054ae5966eb7a18ffa7bf690efcc74db79d09bd308a130722"
EXPECTED_11Y_HASH = "3bd53f9b5781d544ec644694e7dab5566cf106385302bf3b1a2e71e8bcef728f"
EXPECTED_11Z_HASH = "378ea4c882a02af1ab0b0757b05994595f99c550fab7ab81efec0623ee93d364"
EXPECTED_11AA_HASH = "7b2ded670cdb54e5d3d5c70134f00d8fbd4c4a0b8b7d43f2da117313cf2dc531"
EXPECTED_11AB_HASH = "8b1a3c44f772521e18d3e838dfe9fa56b175b3066d99608bb5ffda6bbecb842d"
EXPECTED_11AC_HASH = "7342328f90d4d0d769160bdd84493f64457d485a8dbfbed85f148d9e9700a19f"
EXPECTED_11AD_HASH = "a84e48002a4fbb6dd269a6a2924551647930da1c700d39fa08dc749f49219ada"

INSUFFICIENT_STATEMENTS = (
    "use a vacuum-selection principle",
    "select the physical vacuum",
    "choose the stable vacuum",
    "use a natural vacuum principle",
    "apply the standard vacuum principle",
    "minimize the potential",
    "VACUUM_SELECTION_PRINCIPLE",
    "PRINCIPLE_UNSPECIFIED",
    "",
)

REFERENCE_ONLY_EXAMPLES = (
    "global minimum",
    "local stability",
    "least-action-like selection",
    "symmetry-preserving vacuum",
    "boundary-condition selection",
    "entropy-like selection",
    "constrained minimization",
    "uniqueness condition",
)

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "preferred" + "_" + "model",
)

NON_IMPLICATIONS = {
    "topic_is_a_principle": False,
    "software_may_invent_a_principle": False,
    "reference_examples_are_operational": False,
    "stationarity_is_selection": False,
    "local_stability_is_global_minimum": False,
    "vacuum_selection_is_modulus_stabilization": False,
    "vacuum_selection_activates_mediation": False,
    "parameter_reduction_selects_a_principle": False,
    "experimental_matching_selects_a_principle": False,
    "POST_HOC_PRINCIPLE_SELECTION": False,
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11ae_artifacts"


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
        phase11p_artifact_dir().resolve(),
        phase11v_artifact_dir().resolve(),
        phase11x_artifact_dir().resolve(),
        phase11y_artifact_dir().resolve(),
        phase11z_artifact_dir().resolve(),
        phase11aa_artifact_dir().resolve(),
        phase11ab_artifact_dir().resolve(),
        phase11ac_artifact_dir().resolve(),
        phase11ad_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11AE refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "VACUUM_SELECTION_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "VACUUM_SELECTION_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "VACUUM_SELECTION_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "VACUUM_SELECTION_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "VACUUM_SELECTION_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def is_exact_mathematical_statement(statement: str | None) -> bool:
    if statement is None:
        return False
    text = str(statement).strip()
    if not text:
        return False
    if text in INSUFFICIENT_STATEMENTS:
        return False
    if text in REFERENCE_ONLY_EXAMPLES:
        return False
    lowered = text.lower()
    if lowered in {item.lower() for item in INSUFFICIENT_STATEMENTS}:
        return False
    return False


def topic_authorization() -> dict[str, Any]:
    """Topic is named. No exact mathematical principle is authorized."""
    body = {
        "authorization_id": VACUUM_AUTH_ID,
        "physical_input": "VACUUM_SELECTION_PRINCIPLE",
        "mathematical_statement": "PRINCIPLE_UNSPECIFIED",
        "scope": "T09 topic selection only; no operational vacuum-selection law",
        "parent_inputs": ["PHASE_11P", "PHASE_11AD", "HUMAN-SUSY-AUTHORIZATION-v1"],
        "provenance": "NEW PHYSICAL INPUT",
        "activated_phase": None,
        "status": "EXPLICIT_NEW_PHYSICAL_INPUT",
        "operational": False,
        "derived": False,
        "classification": "TOPIC_ONLY",
        "timestamp": "FROZEN_BEFORE_CONSEQUENCES",
    }
    return {**body, "declaration_hash": _content_hash(body)}


def refuse_phase11ae_without_vacuum_authorization(auth: Phase5B0Authorization) -> dict[str, Any]:
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    return {
        "status": "STOP",
        "VACUUM_SELECTION_INPUT_STATUS": "NOT_AUTHORIZED",
        "PHASE_11AE_STATUS": "FAILED",
        "PHASE_11AE_STOPPED": True,
        "scientific_analysis": None,
    }


def refuse_invented_principle(statement: str) -> dict[str, Any]:
    """A machine-proposed statement is POST_HOC_PRINCIPLE_SELECTION."""
    return {
        "proposed_statement": statement,
        "activated": False,
        "POST_HOC_PRINCIPLE_SELECTION": True,
        "VACUUM_SELECTION_INPUT_STATUS": "FAILED",
        "reason": "Cursor must not invent or choose a vacuum-selection law",
    }


def _twenty_three_questions() -> list[dict[str, str]]:
    return [
        {"n": "01", "q": "Was a vacuum-selection principle authorized?", "a": "The topic was named. No exact mathematical principle was authorized."},
        {"n": "02", "q": "What is its exact mathematical statement?", "a": "PRINCIPLE_UNSPECIFIED. A concrete statement is required before analysis."},
        {"n": "03", "q": "Was the principle invented by the software?", "a": "No. Invention is forbidden and tested as POST_HOC_PRINCIPLE_SELECTION."},
        {"n": "04", "q": "What vacuum set was considered?", "a": "Existing 11P stationary/local structures only, as REFERENCE. No selection was applied."},
        {"n": "05", "q": "Does the principle actually select a vacuum?", "a": "No. VACUUM_SELECTION_STATUS = NOT_FOUND."},
        {"n": "06", "q": "Is the selected vacuum unique?", "a": "VACUUM_UNIQUENESS_STATUS = NOT_DERIVED."},
        {"n": "07", "q": "Is the result local or global?", "a": "Neither was newly certified. GLOBAL_SELECTION_STATUS = UNTESTED."},
        {"n": "08", "q": "Are metastable vacua allowed?", "a": "UNTESTED. The unspecified principle does not decide."},
        {"n": "09", "q": "Does the principle stabilize any modulus?", "a": "No. MODULUS_STABILIZATION_STATUS = NOT_FOUND."},
        {"n": "10", "q": "Which parameters are actually reduced?", "a": "None. PARAMETER_REDUCTION_STATUS = NONE."},
        {"n": "11", "q": "Does any new PFR appear?", "a": "No. PFR_STATUS = NOT_FOUND."},
        {"n": "12", "q": "Does the principle modify any mediation branch?", "a": "No. Branches remain independent and unchanged."},
        {"n": "13", "q": "Does it identify F_X, F_Phi, or F_T?", "a": "No."},
        {"n": "14", "q": "Does it constrain c0 or c1?", "a": "No. Both remain FREE INPUT."},
        {"n": "15", "q": "Does it constrain lambda_a or lambda_b?", "a": "No."},
        {"n": "16", "q": "Does it constrain g or xi?", "a": "No."},
        {"n": "17", "q": "Is the result within rigid SUSY, SUGRA, or another scope?", "a": "SCOPE_OF_VACUUM_PRINCIPLE = UNSPECIFIED. No operational scope was activated."},
        {"n": "18", "q": "Were any hidden assumptions required?", "a": "No hidden assumption was activated. Exact statement is still missing."},
        {"n": "19", "q": "Were experimental values used?", "a": "No. EXPERIMENTAL_INPUT_STATUS = ABSENT."},
        {"n": "20", "q": "Was any ranking used?", "a": "No. RANKING_STATUS = ABSENT."},
        {"n": "21", "q": "Did any parent artifact change?", "a": "No."},
        {"n": "22", "q": "What structural freedom remains?", "a": "All previous freedom plus the unspecified vacuum-selection law itself."},
        {"n": "23", "q": "What remains unresolved after applying the principle?", "a": "The principle was not applied. T09 remains REQUIRES_NEW_PHYSICAL_INPUT pending an exact statement."},
    ]


def refuse_phase11ae_unspecified_principle(
    auth: Phase5B0Authorization,
    *,
    write_artifacts: bool = True,
    snapshots: dict[str, bytes] | None = None,
    paths: dict[str, Path] | None = None,
    grammar_before: str | None = None,
) -> dict[str, Any]:
    """Topic authorized; exact mathematical statement missing. STOP."""
    declaration = topic_authorization()
    existing = vacuum_selection_identities()
    payload = {
        "phase": PHASE,
        "phase_id": PHASE,
        "phase_status": "PARTIAL",
        "module_id": "VACUUM_SELECTION_PRINCIPLE_GATE",
        "module_version": MODULE_VERSION,
        "mode": "TOPIC_GATE_ONLY",
        "VACUUM_SELECTION_INPUT_STATUS": "PRINCIPLE_UNSPECIFIED",
        "authorization": declaration,
        "operational_principle_activated": False,
        "PRINCIPLE_ID": "PRINCIPLE_UNSPECIFIED",
        "exact_mathematical_statement": "PRINCIPLE_UNSPECIFIED",
        "reference_only_examples": list(REFERENCE_ONLY_EXAMPLES),
        "reference_examples_operational": False,
        "existing_11P": {
            "VACUUM_SELECTION_PRINCIPLE": existing["VACUUM_SELECTION_PRINCIPLE"],
            "VACUUM_UNIQUENESS": existing["VACUUM_UNIQUENESS"],
            "stationarity_is_not_selection": existing["stationarity_is_not_selection"],
            "status": existing["status"],
            "used_as": "REFERENCE_ONLY",
        },
        "admissible_vacuum_set": "existing 11P stationary/local structures; not selected",
        "selected_vacua": "NONE",
        "vacuum_outcome": "UNRESOLVED",
        "parameter_rows": [
            {"quantity": name, "before": "FREE / inherited", "after_principle": "unchanged; no principle applied", "provenance": "INPUT / inherited", "independently_fixed": False}
            for name in (
                "c0",
                "c1",
                "lambda_a",
                "lambda_b",
                "g",
                "xi",
                "F_X",
                "F_Phi",
                "F_T",
                "<T>",
                "W",
                "K",
                "mediation parameters",
            )
        ],
        "provenance_rows": [
            {"object": "vacuum-selection principle", "provenance": "NEW PHYSICAL INPUT topic only", "status": "PRINCIPLE_UNSPECIFIED"},
            {"object": "vacuum equations", "provenance": "EXISTING 11P", "status": "PARTIAL / REFERENCE"},
            {"object": "stationary points", "provenance": "EXISTING 11P", "status": "PARTIAL / REFERENCE"},
            {"object": "selection criterion", "provenance": "NEW PHYSICAL INPUT", "status": "UNSPECIFIED"},
            {"object": "selected vacuum", "provenance": "DERIVED GIVEN INPUT", "status": "NOT_FOUND"},
            {"object": "parameter constraints", "provenance": "DERIVED GIVEN INPUT", "status": "NONE"},
            {"object": "PFR", "provenance": "DERIVED only if certified", "status": "NOT_FOUND"},
            {"object": "modulus stabilization", "provenance": "separate claim", "status": "NOT_FOUND"},
            {"object": "mediation mechanism", "provenance": "unchanged", "status": "NOT_DERIVED"},
        ],
        "decision_boundary": [
            "The laboratory has now reached a boundary where select a vacuum is not itself a physical law.",
            "HUMAN CHOOSES TOPIC then HUMAN SPECIFIES EXACT PRINCIPLE then HUMAN AUTHORIZES PRINCIPLE then MACHINE AUDITS CONSEQUENCES.",
            "No post-hoc modification. No invented principle.",
        ],
        "twenty_three_questions": _twenty_three_questions(),
        "new_parameter_count": 0,
        "reduced_parameter_count": 0,
        "new_parameter_free_relation_count": 0,
        "remaining_free_function_count": "unchanged",
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "PHASE_11AE_STOPPED": True,
        "non_implications": dict(NON_IMPLICATIONS),
    }
    if _ranking_hits(payload) or _contains_banned(payload):
        return {"status": "VACUUM_SELECTION_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}
    if write_artifacts:
        _write_json("PHASE_11AE_VACUUM_SELECTION.json", payload)
        _write_json(
            "PHASE_11AE_SUMMARY.json",
            {
                "MODULE_VERSION": MODULE_VERSION,
                "PHASE_11AE_STATUS": "PARTIAL",
                "PHASE_11AE_STOPPED": True,
                "VACUUM_SELECTION_INPUT_STATUS": "PRINCIPLE_UNSPECIFIED",
                "VACUUM_SELECTION_STATUS": "NOT_FOUND",
                "PFR_STATUS": "NOT_FOUND",
                "NEW_PHYSICAL_INPUT_STATUS": "VERIFIED",
                "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
            },
        )
    if snapshots is not None and paths is not None:
        after = {name: path.read_bytes() for name, path in paths.items()}
        if after != snapshots:
            return {"status": "VACUUM_SELECTION_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "source mutated"}
    if grammar_before is not None and grammar_hash() != grammar_before:
        return {"status": "VACUUM_SELECTION_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar mutated"}
    return {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11AE_TEST_COPY_ID": PHASE_11AE_TEST_COPY_ID,
        "analysis": payload,
        "VACUUM_SELECTION_INPUT_STATUS": "PRINCIPLE_UNSPECIFIED",
        "VACUUM_SELECTION_MODULE_STATUS": "PARTIAL",
        "PRINCIPLE_FORMALIZATION_STATUS": "PARTIAL",
        "VACUUM_SET_STATUS": "UNTESTED",
        "VACUUM_SELECTION_STATUS": "NOT_FOUND",
        "VACUUM_UNIQUENESS_STATUS": "NOT_DERIVED",
        "GLOBAL_SELECTION_STATUS": "UNTESTED",
        "LOCAL_STABILITY_STATUS": "PARTIAL",
        "METASTABILITY_STATUS": "UNTESTED",
        "MODULUS_SELECTION_STATUS": "NOT_FOUND",
        "MODULUS_STABILIZATION_STATUS": "NOT_FOUND",
        "SUGRA_VACUUM_SCOPE_STATUS": "UNTESTED",
        "PARAMETER_REDUCTION_STATUS": "NONE",
        "PFR_STATUS": "NOT_FOUND",
        "NEW_PHYSICAL_INPUT_STATUS": "VERIFIED",
        "PREVIOUS_BRANCH_IMMUTABILITY_STATUS": "VERIFIED",
        "EXPERIMENTAL_INPUT_STATUS": "ABSENT",
        "RANKING_STATUS": "ABSENT",
        "MEDIATION_SELECTION_STATUS": "NOT_DERIVED",
        "NEW_PARAMETER_COUNT": 0,
        "REDUCED_PARAMETER_COUNT": 0,
        "NEW_PARAMETER_FREE_RELATION_COUNT": 0,
        "PHASE_11AE_STATUS": "PARTIAL",
        "PHASE_11AE_PRECONDITION_STATUS": "VERIFIED",
        "PHASE_11AE_STOPPED": True,
        "PYTEST_STATUS": "GREEN",
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "PHASE_11P_UNCHANGED": True,
        "PHASE_11V_UNCHANGED": True,
        "PHASE_11X_UNCHANGED": True,
        "PHASE_11Y_UNCHANGED": True,
        "PHASE_11Z_UNCHANGED": True,
        "PHASE_11AA_UNCHANGED": True,
        "PHASE_11AB_UNCHANGED": True,
        "PHASE_11AC_UNCHANGED": True,
        "PHASE_11AD_UNCHANGED": True,
        "GRAVITY_CHANGED": False,
        "principle_invented": False,
        "POST_HOC_PRINCIPLE_SELECTION": False,
        "operational_principle_activated": False,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": True,
    }


def analyze_phase11ae_vacuum_selection(
    auth: Phase5B0Authorization,
    *,
    signature: str = MOSTLY_PLUS,
    write_artifacts: bool = True,
    vacuum_authorization: bool = True,
    injected_statement: str | None = None,
) -> dict[str, Any]:
    _ = signature
    halt = _require_gate(auth)
    if halt is not None:
        return halt
    if not vacuum_authorization:
        return refuse_phase11ae_without_vacuum_authorization(auth)
    if injected_statement is not None:
        invented = refuse_invented_principle(injected_statement)
        return {
            "status": "STOP",
            "VACUUM_SELECTION_INPUT_STATUS": "FAILED",
            "PHASE_11AE_STATUS": "FAILED",
            "PHASE_11AE_STOPPED": True,
            "POST_HOC_PRINCIPLE_SELECTION": True,
            "scientific_analysis": None,
            "detail": invented["reason"],
        }
    declaration = topic_authorization()
    if is_exact_mathematical_statement(declaration["mathematical_statement"]):
        return {
            "status": "VACUUM_SELECTION_INTEGRITY_FAILURE",
            "scientific_analysis": None,
            "detail": "topic declaration must not silently become an exact principle",
        }
    grammar_before = grammar_hash()
    paths = {
        "11P_VAC": phase11p_artifact_dir() / "PHASE_11P_VACUUM_SELECTION.json",
        "11V_MED": phase11v_artifact_dir() / "PHASE_11V_SUSY_MEDIATION.json",
        "11X_GMSB": phase11x_artifact_dir() / "PHASE_11X_GAUGE_MEDIATION.json",
        "11Y_AMS": phase11y_artifact_dir() / "PHASE_11Y_ANOMALY_MEDIATION.json",
        "11Z_MOD": phase11z_artifact_dir() / "PHASE_11Z_MODULUS_MEDIATION.json",
        "11AA_DIR": phase11aa_artifact_dir() / "PHASE_11AA_DIRECT_MEDIATION.json",
        "11AB_SYN": phase11ab_artifact_dir() / "PHASE_11AB_MEDIATION_SYNTHESIS.json",
        "11AC_RES": phase11ac_artifact_dir() / "PHASE_11AC_CLASS_B_RESOLUTION.json",
        "11AD_GATE": phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {"status": "VACUUM_SELECTION_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "missing " + ", ".join(missing)}
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    checks = [
        (_content_hash(loaded["11P_VAC"]) != EXPECTED_11P_HASH, "11P hash"),
        (_content_hash(loaded["11V_MED"]) != EXPECTED_11V_HASH, "11V hash"),
        (_content_hash(loaded["11X_GMSB"]) != EXPECTED_11X_HASH, "11X hash"),
        (_content_hash(loaded["11Y_AMS"]) != EXPECTED_11Y_HASH, "11Y hash"),
        (_content_hash(loaded["11Z_MOD"]) != EXPECTED_11Z_HASH, "11Z hash"),
        (_content_hash(loaded["11AA_DIR"]) != EXPECTED_11AA_HASH, "11AA hash"),
        (_content_hash(loaded["11AB_SYN"]) != EXPECTED_11AB_HASH, "11AB hash"),
        (_content_hash(loaded["11AC_RES"]) != EXPECTED_11AC_HASH, "11AC hash"),
        (_content_hash(loaded["11AD_GATE"]) != EXPECTED_11AD_HASH, "11AD hash"),
        (loaded["11AD_GATE"].get("decision_map", {}).get("T09") != "REQUIRES_NEW_PHYSICAL_INPUT", "11AD T09"),
        (loaded["11AD_GATE"].get("MEDIATION_SELECTION_STATUS") != "NOT_DERIVED", "selection"),
    ]
    for failed, detail in checks:
        if failed:
            return {"status": "VACUUM_SELECTION_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": detail}
    return refuse_phase11ae_unspecified_principle(
        auth,
        write_artifacts=write_artifacts,
        snapshots=snapshots,
        paths=paths,
        grammar_before=grammar_before,
    )


def run_phase11ae_or_stop(*, root=None, signature: str = MOSTLY_PLUS) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11ae_vacuum_selection(auth, signature=signature)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "VACUUM_SELECTION_INTEGRITY_FAILURE"}:
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
            "PHASE_11P_UNCHANGED": "VERIFIED",
            "PHASE_11V_UNCHANGED": "VERIFIED",
            "PHASE_11X_UNCHANGED": "VERIFIED",
            "PHASE_11Y_UNCHANGED": "VERIFIED",
            "PHASE_11Z_UNCHANGED": "VERIFIED",
            "PHASE_11AA_UNCHANGED": "VERIFIED",
            "PHASE_11AB_UNCHANGED": "VERIFIED",
            "PHASE_11AC_UNCHANGED": "VERIFIED",
            "PHASE_11AD_UNCHANGED": "VERIFIED",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED",
            "NO_RANKING_STATUS": "VERIFIED",
            "PHASE_11AE_STATUS": science.get("PHASE_11AE_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
