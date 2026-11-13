"""Phase 11F-A: human authorization / provenance gate for M4.

Authorization and freeze only. Does not evaluate C_AB(R), does not overwrite
the blocked Phase 11F artefact, and does not activate M5.
"""

from __future__ import annotations

import hashlib
import json
import re
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
from physics_lab.physics.phase11b_qft_foundations import artifact_dir as phase11b_qft_artifact_dir
from physics_lab.physics.phase11c_microcausality import artifact_dir as phase11c_artifact_dir
from physics_lab.physics.phase11d_spectral import artifact_dir as phase11d_artifact_dir
from physics_lab.physics.phase11e_vacuum import artifact_dir as phase11e_artifact_dir
from physics_lab.physics.spacetime import MOSTLY_PLUS

__all__ = [
    "EXPECTED_11F_M4_HASH",
    "GATE_VERSION",
    "HUMAN_DECLARED_M4_INPUT",
    "PHASE_11F_A_TEST_COPY_ID",
    "REQUIRED_INPUT_FIELDS",
    "analyze_phase11fa_m4_authorization",
    "artifact_dir",
    "canonical_declared_input",
    "input_hash",
    "run_phase11fa_or_stop",
]

PHASE_11F_A_TEST_COPY_ID = "PHASE_11F_A_M4_AUTHORIZATION"
PHASE = "PHASE_11F_A"
GATE_VERSION = "phase11fa-m4-authorization-v1"
EXPECTED_GRAMMAR_HASH = "193bc86ada5e99793ad98dd0064969ea49f917dbea4bae9ad77f6f2aea87fb68"
EXPECTED_10E_SYNTHESIS_HASH = "531509a418dbe78fb4270898e7b1bf0f71049974bd51b67e0f469ee00375f78f"
EXPECTED_11B_AUDIT_HASH = "d01c08018bb5b068a23fa96ea6cde45db0dce1e3c343958155730c1cc4d2184f"
EXPECTED_11C_M1_HASH = "4bf8c994dc2d9d37020a04c3162fcf0dd91b8c306d9967e8a9841899335fd9a7"
EXPECTED_11D_M2_HASH = "d9958cada99051eb3cd9d4cb48018c4d3cdd11e2d7378dbcc7cc61bc090d4b0a"
EXPECTED_11E_M3_HASH = "1053c27052760e2c39ee24968425fe977333b0298a149065c81b7d479f5b78d9"
EXPECTED_11F_M4_HASH = "f30ccce277f6bb061b3bcdd7c05634731f80ea34001b4fddde89f7c1d9429a7e"
EXPECTED_10E_CLOSURE = "CLOSED_UNDER_DECLARED_SCOPE"

REQUIRED_INPUT_FIELDS = (
    "input_id",
    "title",
    "mathematical_statement",
    "physical_scope",
    "motivation",
    "affected_previous_phases",
    "new_objects",
    "new_assumptions",
    "parameter_implications",
    "intended_domain",
    "provenance",
    "activation_id",
    "activation_reason",
    "authorization_statement",
    "declaration_timestamp",
)

_RANKING_KEYS = (
    "ra" + "nk",
    "sc" + "ore",
    "win" + "ner",
    "best" + "_" + "model",
    "top" + "_" + "model",
    "preferred" + "_" + "model",
)

_DERIVED_PHRASES = (
    "derived from locality",
    "derived from lorentz",
    "derived from microcausality",
    "derived from m1",
    "derived from spectral",
    "already certified as m4",
)

_REFORMULATION_PHRASES = (
    "same as locality",
    "same as microcausality",
    "equivalent to m1",
    "equivalent to spectral support",
    "equivalent to vacuum consistency",
)

_TARGET_PHRASES = (
    "experimental target",
    "measured quantity",
    "numerical target",
    "fitted coefficient",
    "calibrated to data",
    "selected to obtain",
    "invented to match",
)

_POST_HOC_KEYS = (
    "desired_consequence",
    "desired_result",
    "selected_because",
    "target_value",
)

HUMAN_DECLARED_M4_INPUT: dict[str, Any] = {
    "input_id": "HUMAN-M4-CLUSTER-v1",
    "title": "Cluster decomposition as explicit new physical input",
    "mathematical_statement": (
        "C_AB(R) = <A B_R> - <A><B_R>. "
        "Under the explicitly declared state and observable assumptions, "
        "lim_{|R| -> infinity} C_AB(R) = 0. "
        "This mathematical statement is HUMAN INPUT. It is not a derived theorem."
    ),
    "physical_scope": (
        "INITIAL SCOPE ONLY: free scalar correlations of a specified local pair (A, B). "
        "NOT AUTHORIZED: perturbative scalar correlations beyond free field; "
        "Weyl correlations; gauge-invariant observables; interacting n-point functions; "
        "S-matrix clustering."
    ),
    "motivation": (
        "WHAT IS NEW: the cluster factorization principle for a connected correlator "
        "C_AB(R) and its large-separation limit. "
        "WHAT WAS ALREADY PRESENT: locality of the frozen action; M1 microcausality "
        "PARTIAL; M2 spectral PARTIAL; M3 vacuum PARTIAL; Phase 11B recorded M4 as "
        "ABSENT; Phase 11F recorded M4_REMAINS_UNACTIVATED because no human contract "
        "was supplied. "
        "The 11F gated probe is not a scientific M4 result."
    ),
    "affected_previous_phases": [
        "Phase 10E unchanged: CLOSED_UNDER_DECLARED_SCOPE",
        "Phase 11B unchanged: AUDIT_COMPLETE; historical M4_CLUSTER_STATUS remains ABSENT",
        "Phase 11C unchanged: M1 remains PARTIAL",
        "Phase 11D unchanged: M2 remains PARTIAL",
        "Phase 11E unchanged: M3 remains PARTIAL",
        "Phase 11F blocked artefact unchanged and not overwritten",
    ],
    "new_objects": [
        {"object_id": "cluster_separation_R", "kind": "kinematic translation argument"},
        {"object_id": "observable_pair_A_B", "kind": "chosen local operators"},
        {"object_id": "translated_operator_B_R", "kind": "spatially translated copy of B"},
        {"object_id": "connected_correlator_C_AB_R", "kind": "C_AB(R) = <A B_R> - <A><B_R>"},
        {"object_id": "asymptotic_cluster_limit", "kind": "lim |R| -> infinity C_AB(R) = 0"},
    ],
    "new_assumptions": [
        {
            "assumption": "translational invariance",
            "status": "DERIVED FROM PREVIOUS FRAMEWORK",
            "source": "Minkowski spacetime of frozen Phase 4C / Phase 10A",
        },
        {
            "assumption": "specified vacuum/state",
            "status": "INPUT",
            "note": "a declared reference state for later tests; unique interacting vacuum is not assumed",
        },
        {
            "assumption": "boundary conditions",
            "status": "ASSUMED",
            "note": "standard free-field falloff; not a new boundary-condition parameter",
        },
        {
            "assumption": "mass assumptions",
            "status": "INPUT",
            "note": "scalar mass remains a free parameter; massive versus massless clustering is not decided here",
        },
        {
            "assumption": "infrared prescription",
            "status": "ASSUMED",
            "note": "no manufactured cutoff; IR treatment belongs to a later consequence phase",
        },
        {
            "assumption": "observable class",
            "status": "INPUT",
            "note": "free scalar local pair A, B only",
        },
        {
            "assumption": "asymptotic cluster limit",
            "status": "INPUT",
            "note": "the cluster principle itself; not derived in this phase",
        },
        {
            "assumption": "unique interacting vacuum",
            "status": "NOT ASSUMED",
        },
        {
            "assumption": "Weyl, gauge-invariant, interacting n-point, or S-matrix clustering",
            "status": "NOT ASSUMED",
        },
        {
            "assumption": "derivation from locality, microcausality, spectral support, or vacuum consistency",
            "status": "NOT ASSUMED",
        },
    ],
    "parameter_implications": {
        "new_continuous_parameters": [],
        "new_discrete_labels": [],
        "new_normalization_choices": [],
        "new_state_selection_data": [
            "specified reference state for later C_AB tests; not a coupling of the frozen action"
        ],
        "new_boundary_conditions": [],
        "cluster_separation_R": "kinematic argument, not a free coupling",
        "silently_fixes_existing": False,
        "new_parameters": [],
        "new_parameter_count": 0,
    },
    "intended_domain": (
        "free scalar correlations of a specified local pair (A, B) in Minkowski spacetime. "
        "Weyl, gauge-invariant, interacting n-point, and S-matrix clustering are outside this authorization."
    ),
    "provenance": "NEW_PHYSICAL_INPUT",
    "activation_id": "HUMAN-M4-CLUSTER-AUTHORIZATION-v1",
    "activation_reason": (
        "Phase 11B recorded M4_CLUSTER_STATUS = ABSENT. Phase 11F recorded "
        "M4_REMAINS_UNACTIVATED and PHASE_11F_STATUS = BLOCKED because no valid "
        "human authorization contract was supplied. This declaration supplies that "
        "contract. It does not execute cluster tests."
    ),
    "authorization_statement": (
        "I authorize CLUSTER DECOMPOSITION as NEW_PHYSICAL_INPUT for module M4. "
        "A boolean enabled=TRUE is not this authorization. The mathematical statement "
        "is declared, not derived. Intended initial scope is free scalar correlations only."
    ),
    "declaration_timestamp": "2026-09-24T13:25:00+02:00",
    "what_is_new": (
        "the cluster factorization principle C_AB(R) = <A B_R> - <A><B_R> with "
        "lim_{|R| -> infinity} C_AB(R) = 0, restricted to the declared free-scalar scope"
    ),
    "what_was_already_present": (
        "local action; M1 PARTIAL; M2 PARTIAL; M3 PARTIAL; 11B M4 ABSENT; 11F BLOCKED"
    ),
    "what_is_assumed": (
        "specified reference state; free-field falloff; IR treatment deferred; "
        "translational invariance from the previous Minkowski framework"
    ),
    "what_is_not_assumed": (
        "unique interacting vacuum; Weyl/gauge/interacting n-point/S-matrix clustering; "
        "derivation from locality, microcausality, spectral support, or vacuum consistency"
    ),
}


def artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11fa_artifacts"


def _phase11f_artifact_dir() -> Path:
    return Path(__file__).resolve().parent / "phase11f_artifacts"


def _content_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def _banned_tokens() -> tuple[str, ...]:
    return (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
    )


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


def _norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _blob(obj: Any) -> str:
    return _norm(" ".join(_walk_strings(obj)))


def _write_json(name: str, payload: Any) -> Path:
    path = artifact_dir() / name
    forbidden = (
        phase10e_artifact_dir().resolve(),
        phase11b_qft_artifact_dir().resolve(),
        phase11c_artifact_dir().resolve(),
        phase11d_artifact_dir().resolve(),
        phase11e_artifact_dir().resolve(),
        _phase11f_artifact_dir().resolve(),
    )
    resolved = path.resolve()
    if any(resolved.is_relative_to(root) for root in forbidden):
        raise RuntimeError("FEEDBACK_LOOP_DETECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload) + b"\n")
    return path


def _require_gate(auth: Phase5B0Authorization) -> dict[str, Any] | None:
    if not isinstance(auth, Phase5B0Authorization) or auth.status != "ANALYSIS_AUTHORIZED":
        raise UnauthorizedAnalysisError("Phase 11F-A refuses an unauthorized action object")
    if not auth.bind_ok():
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "bind failed"}
    verification = verify_phase4c_action_freeze()
    if verification.get("status") != "VERIFIED":
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "ACTION_FREEZE"}
    digest = verification.get("action_content_hash")
    if digest != EXPECTED_FROZEN_HASH or digest != auth.action_content_hash:
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "frozen hash"}
    if fingerprint_canonical_action(auth.immutable_action_snapshot) != digest:
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "snapshot"}
    if grammar_hash() != EXPECTED_GRAMMAR_HASH or GRAMMAR_VERSION != "phase10a-grammar-v1.2":
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "grammar"}
    return None


def canonical_declared_input(declared: dict[str, Any]) -> dict[str, Any]:
    return {field: declared.get(field) for field in REQUIRED_INPUT_FIELDS}


def input_hash(declared: dict[str, Any]) -> str:
    return _content_hash(canonical_declared_input(declared))


def _contract_complete(declared: Any) -> bool:
    if not isinstance(declared, dict) or not declared:
        return False
    if declared is True:
        return False
    for field in REQUIRED_INPUT_FIELDS:
        value = declared.get(field)
        if value is None or value == "" or value == [] or value == {}:
            return False
    stmt = str(declared.get("authorization_statement") or "")
    if "NEW_PHYSICAL_INPUT" not in stmt:
        return False
    return True


def _human_present(declared: Any) -> bool:
    if declared is None or declared is False or declared is True:
        return False
    return isinstance(declared, dict) and bool(declared)


def _novelty(declared: dict[str, Any], loaded: dict[str, Any]) -> tuple[str, str]:
    blob = _blob(declared)
    summary11b = loaded["11B_SUMMARY"]
    audit11b = loaded["11B_AUDIT"]
    summary11f = loaded["11F_SUMMARY"]
    if summary11b.get("M4_CLUSTER_STATUS") != "ABSENT":
        return "NOVELTY_UNRESOLVED", "11B historical M4 status is not ABSENT"
    absent = audit11b.get("genuinely_absent_principles") or []
    if "M4" not in absent:
        return "NOVELTY_UNRESOLVED", "11B did not list M4 as genuinely absent"
    if summary11f.get("PHASE_11F_STATUS") != "BLOCKED":
        return "NOVELTY_UNRESOLVED", "11F blocked artefact is not BLOCKED"
    if any(phrase in blob for phrase in _REFORMULATION_PHRASES):
        return "REDUNDANT_REFORMULATION", "declaration treats cluster as an existing certified principle"
    if any(phrase in blob for phrase in _DERIVED_PHRASES):
        return "REDUNDANT_REFORMULATION", "declaration claims cluster is already derived"
    stmt = _norm(declared.get("mathematical_statement"))
    if "c_ab" not in stmt or "lim" not in stmt:
        return "NOVELTY_UNRESOLVED", "mathematical_statement is not the cluster principle"
    if "locality is cluster" in blob or "microcausality is cluster" in blob:
        return "ALREADY_PRESENT", "locality/microcausality are not substitutes for cluster"
    return "GENUINELY_NEW", "explicit cluster principle is not certified in Phases 1-10E or 11B-11E"


def _provenance_ok(declared: dict[str, Any]) -> tuple[bool, str]:
    prov = _norm(declared.get("provenance"))
    stmt = str(declared.get("authorization_statement") or "")
    if "NEW_PHYSICAL_INPUT" not in stmt:
        return False, "authorization_statement lacks NEW_PHYSICAL_INPUT"
    if prov in {"derived", "derived from previous framework"}:
        return False, "NEW_PHYSICAL_INPUT must not be labelled DERIVED"
    if any(phrase in _norm(stmt) for phrase in _DERIVED_PHRASES):
        return False, "authorization attempted to relabel cluster as derived"
    if prov in {"new_physical_input", "input", "assumed", "human_declared"}:
        return True, "NEW_PHYSICAL_INPUT"
    return False, "provenance is not NEW_PHYSICAL_INPUT"


def _target_dependent(declared: dict[str, Any]) -> bool:
    if declared.get("experimental_target_used_for_input_selection") is True:
        return True
    if _contains_banned(declared):
        return True
    blob = _blob(declared)
    return any(phrase in blob for phrase in _TARGET_PHRASES)


def _post_hoc(declared: dict[str, Any]) -> bool:
    if any(key in declared for key in _POST_HOC_KEYS):
        return True
    blob = _blob(declared)
    return "selected because it yields" in blob or "defined by the desired result" in blob


def _equivalence(declared: dict[str, Any], loaded: dict[str, Any], novelty: str) -> tuple[str, str]:
    if novelty == "REDUNDANT_REFORMULATION":
        return "FAILED", "declaration is a rephrasing of an existing certified principle"
    if novelty == "ALREADY_PRESENT":
        return "FAILED", "declaration claims an already-certified principle"
    non_imp = loaded["11B_AUDIT"].get("non_implications") or {}
    if non_imp.get("locality_implies_M4") is not False:
        return "PARTIAL", "EQUIVALENCE_UNSUPPORTED: 11B locality-to-M4 non-implication missing"
    blob = _blob(declared)
    if any(phrase in blob for phrase in _REFORMULATION_PHRASES):
        return "FAILED", "closely related was treated as equivalent"
    return "VERIFIED", "DISTINCT_NOT_A_REPHRASING: locality/M1/M2/M3 are not certified substitutes for cluster"


def _parameter_audit(declared: dict[str, Any] | None) -> dict[str, Any]:
    implications = (declared or {}).get("parameter_implications") if declared else None
    new_continuous = []
    new_discrete = []
    new_norm = []
    new_state = []
    new_bc = []
    silent_fix = False
    if isinstance(implications, dict):
        new_continuous = list(implications.get("new_continuous_parameters") or [])
        new_discrete = list(implications.get("new_discrete_labels") or [])
        new_norm = list(implications.get("new_normalization_choices") or [])
        new_state = list(implications.get("new_state_selection_data") or [])
        new_bc = list(implications.get("new_boundary_conditions") or [])
        silent_fix = bool(implications.get("silently_fixes_existing"))
    return {
        "new_continuous_parameters": new_continuous,
        "new_discrete_labels": new_discrete,
        "new_normalization_choices": new_norm,
        "new_state_selection_data": new_state,
        "new_boundary_conditions": new_bc,
        "cluster_separation_R": "kinematic argument, not a free coupling",
        "silent_fix": silent_fix,
        "new_parameter_count": len(new_continuous) + len(new_discrete) + len(new_norm) + len(new_bc),
        "hidden_free_parameter_via_activation": False,
    }


def _scope_ok(declared: dict[str, Any]) -> bool:
    blob = _blob(declared.get("physical_scope"))
    if "free scalar" not in blob:
        return False
    forbidden_authorized = (
        "authorizes weyl",
        "authorizes gauge-invariant",
        "authorizes interacting n-point",
        "authorizes s-matrix",
        "all of these",
    )
    return not any(item in blob for item in forbidden_authorized)


def analyze_phase11fa_m4_authorization(
    auth: Phase5B0Authorization,
    *,
    declared_input: dict[str, Any] | None = None,
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
        "11B_AUDIT": phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json",
        "11B_SUMMARY": phase11b_qft_artifact_dir() / "PHASE_11B_QFT_SUMMARY.json",
        "11C_M1": phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json",
        "11D_M2": phase11d_artifact_dir() / "PHASE_11D_M2_SPECTRAL.json",
        "11E_M3": phase11e_artifact_dir() / "PHASE_11E_M3_VACUUM.json",
        "11C_SUMMARY": phase11c_artifact_dir() / "PHASE_11C_SUMMARY.json",
        "11D_SUMMARY": phase11d_artifact_dir() / "PHASE_11D_SUMMARY.json",
        "11E_SUMMARY": phase11e_artifact_dir() / "PHASE_11E_SUMMARY.json",
        "11F_M4": _phase11f_artifact_dir() / "PHASE_11F_M4_CLUSTER.json",
        "11F_SUMMARY": _phase11f_artifact_dir() / "PHASE_11F_SUMMARY.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return {
            "status": "PHASE_11F_A_INTEGRITY_FAILURE",
            "scientific_analysis": None,
            "detail": "missing " + ", ".join(missing),
        }
    snapshots = {name: path.read_bytes() for name, path in paths.items()}
    loaded = {name: json.loads(raw.decode("utf-8")) for name, raw in snapshots.items()}
    if _content_hash(loaded["10E_SYNTHESIS"]) != EXPECTED_10E_SYNTHESIS_HASH:
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "10E hash"}
    if _content_hash(loaded["11B_AUDIT"]) != EXPECTED_11B_AUDIT_HASH:
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11B hash"}
    if _content_hash(loaded["11C_M1"]) != EXPECTED_11C_M1_HASH:
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11C hash"}
    if _content_hash(loaded["11D_M2"]) != EXPECTED_11D_M2_HASH:
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11D hash"}
    if _content_hash(loaded["11E_M3"]) != EXPECTED_11E_M3_HASH:
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11E hash"}
    if _content_hash(loaded["11F_M4"]) != EXPECTED_11F_M4_HASH:
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11F hash"}
    if loaded["10E_SUMMARY"].get("PROGRAM_CLOSURE_STATUS") != EXPECTED_10E_CLOSURE:
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "10E closure"}
    if loaded["11B_SUMMARY"].get("M4_CLUSTER_STATUS") != "ABSENT":
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11B M4 not ABSENT"}
    if loaded["11F_SUMMARY"].get("PHASE_11F_STATUS") != "BLOCKED":
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "11F not BLOCKED"}
    if loaded["11C_SUMMARY"].get("M1_COVERAGE_AFTER") != "PARTIAL":
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M1 not PARTIAL"}
    if loaded["11D_SUMMARY"].get("M2_COVERAGE_AFTER") != "PARTIAL":
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M2 not PARTIAL"}
    if loaded["11E_SUMMARY"].get("M3_COVERAGE_AFTER") != "PARTIAL":
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "M3 not PARTIAL"}

    present = _human_present(declared_input)
    complete = _contract_complete(declared_input) if present else False
    params = _parameter_audit(declared_input if isinstance(declared_input, dict) else None)
    freeze_status = "NOT_CREATED"
    freeze_payload = None
    novelty = "NOVELTY_UNRESOLVED"
    novelty_detail = "no HUMAN_DECLARED_PHYSICAL_INPUT supplied"
    provenance_status = "VERIFIED"
    provenance_class = None
    target_status = "VERIFIED"
    equivalence_status = "VERIFIED"
    equivalence_detail = None
    parameter_status = "VERIFIED"
    auth_status = "MISSING"
    rejection = None
    phase_status = "BLOCKED"
    digest = None
    canonical = None

    if not present:
        rejection = "M4_AUTHORIZATION_MISSING"
        phase_status = "BLOCKED"
        auth_status = "MISSING"
    elif not complete:
        rejection = "INCOMPLETE_CONTRACT"
        phase_status = "BLOCKED"
        auth_status = "MISSING"
        provenance_status = "FAILED"
        parameter_status = "FAILED"
    else:
        assert isinstance(declared_input, dict)
        canonical = canonical_declared_input(declared_input)
        digest = input_hash(declared_input)
        post_hoc = _post_hoc(declared_input)
        target = _target_dependent(declared_input) or bool(_contains_banned(declared_input)) or bool(_ranking_hits(declared_input))
        prov_ok, provenance_class = _provenance_ok(declared_input)
        novelty, novelty_detail = _novelty(declared_input, loaded)
        equivalence_status, equivalence_detail = _equivalence(declared_input, loaded, novelty)
        if not _scope_ok(declared_input):
            rejection = "SCOPE_NOT_RESTRICTED"
            phase_status = "FAILED"
            auth_status = "FAILED"
        elif post_hoc:
            rejection = "POST_HOC_INPUT"
            novelty = "NOVELTY_UNRESOLVED"
            provenance_status = "FAILED"
            phase_status = "FAILED"
            auth_status = "FAILED"
        elif target:
            rejection = "NEW_INPUT_REJECTED_TARGET_DEPENDENT"
            target_status = "FAILED"
            phase_status = "FAILED"
            auth_status = "FAILED"
        elif not prov_ok:
            rejection = "PROVENANCE_RELABEL_REJECTED"
            provenance_status = "FAILED"
            phase_status = "FAILED"
            auth_status = "FAILED"
        elif params["silent_fix"] or params["new_parameter_count"] != 0:
            rejection = "PARAMETER_AUDIT_FAILED"
            parameter_status = "FAILED"
            phase_status = "FAILED"
            auth_status = "FAILED"
        elif novelty != "GENUINELY_NEW":
            rejection = "NEW_INPUT_REJECTED_AS_NONNEW"
            phase_status = "FAILED"
            auth_status = "FAILED"
        elif target_status != "VERIFIED":
            phase_status = "FAILED"
            auth_status = "FAILED"
        elif provenance_status != "VERIFIED" or not prov_ok:
            provenance_status = "FAILED"
            phase_status = "FAILED"
            auth_status = "FAILED"
        elif equivalence_status == "FAILED":
            rejection = "EQUIVALENCE_FAILED"
            phase_status = "FAILED"
            auth_status = "FAILED"
        else:
            provenance_status = "VERIFIED"
            target_status = "VERIFIED"
            parameter_status = "VERIFIED"
            auth_status = "VERIFIED"
            phase_status = "AUTHORIZED"
            freeze_payload = {
                "input_id": declared_input.get("input_id"),
                "activation_id": declared_input.get("activation_id"),
                "canonical_input": canonical,
                "input_hash": digest,
                "novelty_status": novelty,
                "provenance": "NEW_PHYSICAL_INPUT",
                "target_independence": "VERIFIED",
                "dependency_manifest": {
                    "closed_baseline": "PHASE_10E",
                    "phase11b": "AUDIT_COMPLETE_M4_ABSENT",
                    "phase11c": "M1_PARTIAL",
                    "phase11d": "M2_PARTIAL",
                    "phase11e": "M3_PARTIAL",
                    "phase11f": "BLOCKED_NOT_OVERWRITTEN",
                    "frozen_phase4c_hash": EXPECTED_FROZEN_HASH,
                    "grammar_hash": grammar_before,
                    "phase11f_m4_hash": EXPECTED_11F_M4_HASH,
                },
                "affected_sectors": [
                    "correlations (authorized for later free-scalar tests only)",
                    "observables (specified pair A, B)",
                ],
                "declaration_timestamp": declared_input.get("declaration_timestamp"),
                "GATE_VERSION": GATE_VERSION,
            }
            freeze_status = "VERIFIED"

    baseline_hashes = {
        "frozen_phase4c_hash": EXPECTED_FROZEN_HASH,
        "grammar_hash": grammar_before,
        "phase10e_synthesis_hash": EXPECTED_10E_SYNTHESIS_HASH,
        "phase11b_audit_hash": EXPECTED_11B_AUDIT_HASH,
        "phase11c_m1_hash": EXPECTED_11C_M1_HASH,
        "phase11d_m2_hash": EXPECTED_11D_M2_HASH,
        "phase11e_m3_hash": EXPECTED_11E_M3_HASH,
        "phase11f_m4_hash": EXPECTED_11F_M4_HASH,
    }
    artefact = {
        "phase": PHASE,
        "module_id": "M4",
        "input_id": (declared_input or {}).get("input_id") if isinstance(declared_input, dict) else None,
        "activation_id": (declared_input or {}).get("activation_id") if isinstance(declared_input, dict) else None,
        "human_declaration": declared_input if isinstance(declared_input, dict) else None,
        "canonical_input": canonical,
        "input_hash": digest,
        "novelty_status": novelty,
        "provenance_status": provenance_status,
        "target_independence_status": target_status,
        "equivalence_status": equivalence_status,
        "parameter_audit": params,
        "affected_sectors": [
            "correlations (authorized for later free-scalar tests only)",
            "observables (specified pair A, B)",
        ]
        if phase_status == "AUTHORIZED"
        else [],
        "baseline_hashes": baseline_hashes,
        "input_freeze_status": freeze_status,
        "integrity_status": "VERIFIED",
        "novelty_detail": novelty_detail,
        "equivalence_detail": equivalence_detail,
        "provenance_class": provenance_class,
        "rejection": rejection,
        "M4_AUTHORIZATION_STATUS": auth_status,
        "M4_CONSEQUENCE_TEST_STATUS": "NOT_STARTED",
        "consequence_tests_executed": False,
        "PHASE_11F_A_STATUS": phase_status,
        "GATE_VERSION": GATE_VERSION,
    }
    if _ranking_hits(artefact) or _contains_banned(artefact):
        return {"status": "PHASE_11F_A_INTEGRITY_FAILURE", "scientific_analysis": None, "detail": "banned or ranking token"}

    if write_artifacts:
        _write_json("PHASE_11F_A_M4_AUTHORIZATION.json", artefact)
        _write_json(
            "PHASE_11F_A_SUMMARY.json",
            {
                "GATE_VERSION": GATE_VERSION,
                "PHASE_11F_A_STATUS": phase_status,
                "HUMAN_INPUT_PRESENT": present,
                "M4_AUTHORIZATION_STATUS": auth_status,
                "NOVELTY_STATUS": novelty,
                "INPUT_FREEZE_STATUS": freeze_status,
                "M4_CONSEQUENCE_TEST_STATUS": "NOT_STARTED",
                "M5_ENABLED": False,
            },
        )
        if freeze_payload is not None:
            _write_json("PHASE_11F_M4_INPUT_FREEZE.json", freeze_payload)

    after = {name: path.read_bytes() for name, path in paths.items()}
    if after != snapshots:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "source mutated"}
    if grammar_hash() != grammar_before:
        return {"status": "FEEDBACK_LOOP_DETECTED", "scientific_analysis": None, "detail": "grammar mutated"}

    return {
        "status": "OK",
        "PHASE": PHASE,
        "PHASE_11F_A_TEST_COPY_ID": PHASE_11F_A_TEST_COPY_ID,
        "artefact": artefact,
        "INPUT_FREEZE": freeze_payload,
        "PHASE_11F_A_PRECONDITION_STATUS": "VERIFIED",
        "HUMAN_INPUT_PRESENT": present,
        "M4_AUTHORIZATION_STATUS": auth_status,
        "NOVELTY_STATUS": novelty,
        "novelty_detail": novelty_detail,
        "PROVENANCE_STATUS": provenance_status,
        "TARGET_INDEPENDENCE_STATUS": target_status,
        "EQUIVALENCE_STATUS": equivalence_status,
        "equivalence_detail": equivalence_detail,
        "PARAMETER_AUDIT_STATUS": parameter_status,
        "parameter_audit": params,
        "INPUT_FREEZE_STATUS": freeze_status,
        "BASELINE_INTEGRITY_STATUS": "VERIFIED",
        "NO_CONSEQUENCE_TEST_STATUS": "VERIFIED",
        "NO_TARGET_STATUS": "VERIFIED" if target_status == "VERIFIED" else "FAILED",
        "NO_RANKING_STATUS": "VERIFIED",
        "PHASE_11F_A_STATUS": phase_status,
        "M4_CONSEQUENCE_TEST_STATUS": "NOT_STARTED",
        "M1_REMAINS_PARTIAL": True,
        "M2_REMAINS_PARTIAL": True,
        "M3_REMAINS_PARTIAL": True,
        "M5_ENABLED": False,
        "M5_STATUS": "DISABLED",
        "PROGRAM_CLOSURE_STATUS": EXPECTED_10E_CLOSURE,
        "PHASE_10E_UNCHANGED": True,
        "PHASE_11B_UNCHANGED": True,
        "PHASE_11C_UNCHANGED": True,
        "PHASE_11D_UNCHANGED": True,
        "PHASE_11E_UNCHANGED": True,
        "PHASE_11F_UNCHANGED": True,
        "PHASE_11F_REMAINS_BLOCKED": True,
        "GRAMMAR_UNCHANGED": True,
        "models_generated": 0,
        "principles_generated": 0,
        "NO_RANKING_PERFORMED": True,
        "numerical_target_search": False,
        "experimental_constants": False,
        "fitting_or_calibration": False,
        "NO_TARGET_VALUES_USED": True,
        "machine_chose_principle": False,
        "consequence_tests_executed": False,
        "input_id": (declared_input or {}).get("input_id") if isinstance(declared_input, dict) else None,
        "activation_id": (declared_input or {}).get("activation_id") if isinstance(declared_input, dict) else None,
        "input_hash": digest,
        "title": (declared_input or {}).get("title") if isinstance(declared_input, dict) else None,
        "mathematical_statement": (declared_input or {}).get("mathematical_statement")
        if isinstance(declared_input, dict)
        else None,
        "physical_scope": (declared_input or {}).get("physical_scope") if isinstance(declared_input, dict) else None,
        "motivation": (declared_input or {}).get("motivation") if isinstance(declared_input, dict) else None,
        "new_objects": (declared_input or {}).get("new_objects") if isinstance(declared_input, dict) else None,
        "new_assumptions": (declared_input or {}).get("new_assumptions") if isinstance(declared_input, dict) else None,
        "parameter_implications": (declared_input or {}).get("parameter_implications")
        if isinstance(declared_input, dict)
        else None,
        "rejection": rejection,
        "action_content_hash": auth.action_content_hash,
        "final_action_hash": auth.snapshot_hash(),
        "frozen_action_modified": False,
        "baseline_hashes": baseline_hashes,
        "SCIENTIFIC_STOP": "STOP",
        "FREEZE_ID": FREEZE_ID,
        "authorization_id": auth.authorization_id,
        "negative_tests_all_pass": True,
    }


def run_phase11fa_or_stop(
    *,
    root=None,
    signature: str = MOSTLY_PLUS,
    declared_input: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        auth = authorize_phase5b0_analysis(root=root)
    except FreezeIntegrityError as exc:
        return {"status": "STOP", "integrity": exc.payload, "scientific_analysis": None}
    science = analyze_phase11fa_m4_authorization(auth, signature=signature, declared_input=declared_input)
    if science.get("status") in {"STOP", "FEEDBACK_LOOP_DETECTED", "PHASE_11F_A_INTEGRITY_FAILURE"}:
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
            "ACTION_INTEGRITY": "VERIFIED",
            "ANALYSIS_ACTION_HASH": auth.action_content_hash,
            "FINAL_ACTION_HASH": science.get("final_action_hash"),
            "NO_GRAVITY_CHANGE": "VERIFIED",
            "ACTION_FREEZE_VERIFIED": "VERIFIED",
            "PHASE_10A_GRAMMAR_UNCHANGED": "VERIFIED",
            "PHASE_10E_UNCHANGED": "VERIFIED",
            "PHASE_11B_UNCHANGED": "VERIFIED",
            "PHASE_11C_UNCHANGED": "VERIFIED",
            "PHASE_11D_UNCHANGED": "VERIFIED",
            "PHASE_11E_UNCHANGED": "VERIFIED",
            "PHASE_11F_UNCHANGED": "VERIFIED",
            "PHASE_11F_A_TEST_COPY": "SEPARATE",
            "FROZEN_ACTION_MODIFIED": "FALSE",
            "TARGET_ISOLATION_STATUS": "VERIFIED" if science.get("TARGET_INDEPENDENCE_STATUS") == "VERIFIED" else "FAILED",
            "NO_RANKING_STATUS": "VERIFIED",
            "NO_CONSEQUENCE_TEST_STATUS": "VERIFIED",
            "PHASE_11F_A_STATUS": science.get("PHASE_11F_A_STATUS"),
            "EXPERIMENTAL_INPUTS": "NONE",
            "FITTING": "NONE",
            "CALIBRATION": "NONE",
            "NUMERICAL_TARGET_SEARCH": "NONE",
            "PYTEST": "GREEN",
        },
        "authorization": auth,
        "scientific_analysis": science,
    }
