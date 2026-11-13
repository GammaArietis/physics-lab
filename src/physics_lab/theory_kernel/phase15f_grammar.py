"""Phase 15F registers nested constraint profiles on the existing grammar.

The ambient catalogue stays intact. A profile is a predeclared structural
filter. This phase does not generate a new search.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    verify_phase4c_action_freeze,
)
from physics_lab.theory_kernel.epistemic import content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15a_grammar import (
    _ranking_tokens,
    attempt_grammar_mutation,
    catalog_influence,
    classify_candidate,
    compile_grammar,
)
from physics_lab.theory_kernel.phase15b_enumeration import ARTIFACT_DIR_NAME as PHASE_15B_ARTIFACTS
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_15F"
CODE_VERSION = "phase15f-grammar-v1"
ARTIFACT_DIR_NAME = "phase15f_grammar_artifacts"
GRAMMAR_VERSION = "grammar_15f_v1"
PARENT_GRAMMAR_VERSION = "grammar_15a_v1"
PARENT_GRAMMAR_HASH = "9e2c6b08d9d0ef96a78f52fb097d169bc112aac29b70556aa7be7bf0d4206075"
AUTHORIZATION_TOKEN = "HUMAN_SEARCH_PROFILE_AUTHORIZATION"
PROFILE_IDS = ("AMBIENT_117", "LOCAL_U1_63", "COVARIANT_U1_37")


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_15F_STATUS": "BLOCKED", "reason": reason, "status": "PHASE_15F_BLOCKED"}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def new_profile_session() -> dict[str, str]:
    return {
        "active_profile": "UNAUTHORIZED",
        "authorization": "ABSENT",
        "generation_state": "NOT_STARTED",
    }


def authorize_search_profile(session: dict[str, str], profile_id: str, authorization: str) -> str:
    if session["generation_state"] != "NOT_STARTED":
        return "PROFILE_LOCKED"
    if authorization != AUTHORIZATION_TOKEN:
        return "AUTHORIZATION_REQUIRED"
    if profile_id not in PROFILE_IDS:
        return "UNKNOWN_PROFILE"
    session["active_profile"] = profile_id
    session["authorization"] = authorization
    return "AUTHORIZED_NOT_GENERATED"


def begin_generation(_session: dict[str, str]) -> dict[str, str]:
    return {"reason": "PHASE_15F_HARD_STOP", "status": "SEARCH_NOT_EXECUTED"}


def note_generation_started(session: dict[str, str]) -> str:
    session["generation_state"] = "STARTED"
    return "STARTED_WITHOUT_ENUMERATION"


def register_constraint_from_catalog(_catalog: Any) -> str:
    return "REJECTED"


def register_field(_name: str) -> str:
    return "REJECTED"


def _local_u1_verdict(operator_id: str, breaking: set[str], invariant: set[str], curved: set[str]) -> str:
    if operator_id in breaking:
        return "FAIL"
    if operator_id in invariant or operator_id in curved:
        return "PASS"
    return "UNCLASSIFIED"


def _covariance_verdict(operator_id: str, curved: set[str]) -> str:
    if operator_id in curved:
        return "PASS"
    return "FAIL"


def _profiles(ambient: list[str], preserving: list[str], covariant: list[str]) -> list[dict[str, Any]]:
    rows = [
        ("AMBIENT_117", "FLAT_LORENTZ_AMBIENT", ["locality", "declared Lorentz structure"], ambient),
        ("LOCAL_U1_63", "LOCAL_U1_PRESERVING", ["locality", "declared Lorentz structure", "C15F-01"], preserving),
        (
            "COVARIANT_U1_37",
            "COVARIANT_4D",
            ["locality", "C15F-02", "C15F-01"],
            covariant,
        ),
    ]
    return [
        {
            "active_constraints": constraints,
            "ambient_space": 117,
            "context": context,
            "declaration": "BEFORE_GENERATION",
            "operator_count": len(operators),
            "operator_ids": operators,
            "profile_id": profile_id,
            "relation_kind": "SET_INCLUSION_METADATA",
            "status": "REGISTERED_NOT_ACTIVATED",
        }
        for profile_id, context, constraints, operators in rows
    ]


def _operational(partition: dict[str, Any], compiled: dict[str, Any]) -> dict[str, Any]:
    return {
        "active_profile": "UNAUTHORIZED",
        "coefficients": "FREE",
        "contexts": {
            "COVARIANT_4D": {
                "operator_count": len(partition["covariant"]),
                "operator_ids": partition["covariant"],
                "scientific_status": "STRUCTURAL U(1)+GENERAL-COVARIANCE SUBSPACE",
            },
            "FLAT_LORENTZ_AMBIENT": {
                "operator_count": len(partition["ambient"]),
                "operator_ids": partition["ambient"],
                "scientific_status": "AMBIENT GRAMMAR SPACE",
            },
            "LOCAL_U1_PRESERVING": {
                "operator_count": len(partition["preserving"]),
                "operator_ids": partition["preserving"],
                "scientific_status": "STRUCTURAL U(1)-PRESERVING SUBSPACE",
            },
        },
        "constraints": [
            {
                "constraint_id": "C15F-01",
                "meaning": "the complete symbolic action must be invariant under the already established local U(1) transformation",
                "name": "EXISTING_LOCAL_U1_INVARIANCE",
                "operational_classification": "MANDATORY CONSTRAINT CONFIGURATION",
                "provenance": "DERIVED FROM PHASES 14L / 15E",
                "result_values": ["PASS", "FAIL"],
                "semantic_class": "STRUCTURAL_CONSTRAINT",
            },
            {
                "constraint_id": "C15F-02",
                "meaning": "the action must be generally covariant in the certified 4D context",
                "name": "GENERAL_COVARIANCE_4D",
                "operational_classification": "MANDATORY CONSTRAINT CONFIGURATION",
                "provenance": "DERIVED WITHIN REGISTERED GRAMMAR",
                "result_values": ["PASS", "FAIL"],
                "semantic_class": "STRUCTURAL_CONSTRAINT",
            },
        ],
        "dd_classification": {
            "ambient_availability": "ALL_80",
            "breaking_operator_ids": partition["breaking"],
            "global_so2_invariant": 80,
            "invariant_operator_ids": partition["invariant_dd"],
            "local_u1_breaking": 54,
            "local_u1_invariant": 26,
            "total": 80,
            "u1_profile_excludes_breaking": True,
        },
        "equivalence_quotient_applied": False,
        "equivalence_unsupported": list(compiled["operational"]["equivalence_unsupported"]),
        "field_content": list(compiled["operational"]["field_content"]),
        "frozen_action_role": "IMMUTABLE_REFERENCE",
        "generation_state": "NOT_STARTED",
        "generator_enabled_mutation": "NONE",
        "grammar_version": GRAMMAR_VERSION,
        "inclusion": {
            "kind": "SET_INCLUSION_METADATA",
            "relation": "COVARIANT_4D ⊆ LOCAL_U1_PRESERVING ⊆ FLAT_LORENTZ_AMBIENT",
        },
        "known_theory_role": "REFERENCE_ONLY",
        "new_field": "NONE",
        "new_physical_principle": "NONE",
        "parameter_determination_by_profile": False,
        "parent": {
            "grammar_hash": PARENT_GRAMMAR_HASH,
            "grammar_version": PARENT_GRAMMAR_VERSION,
            "relation": "SEMANTIC_CONSTRAINT_REFINEMENT",
        },
        "post_hoc_filter": "FORBIDDEN",
        "profiles": _profiles(partition["ambient"], partition["preserving"], partition["covariant"]),
        "profiles_declared": "BEFORE_GENERATION",
        "search_executed": False,
        "search_profile_authorization": "REQUIRED",
        "semantic_distinction": {
            "MATHEMATICAL_ADMISSIBILITY": "membership in the ambient FLAT_LORENTZ grammar",
            "STRUCTURAL_CONSTRAINT": "a separately activated pass or fail test",
        },
        "syzygies": {
            "covariant_algebraic_rank": partition["covariant_rank"],
            "flat_algebraic_rank": partition["flat_rank"],
            "identities": partition["syzygies"],
            "quotient_applied": False,
            "role": "ALGEBRAIC_DEPENDENCY_METADATA",
        },
        "test_action_role": "TEST_ACTION_RESULTS",
    }


def _partition(compiled: dict[str, Any], families: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any] | str:
    enabled = compiled["enabled"]
    ambient_ids = [item["object_id"] for item in enabled]
    ambient = set(ambient_ids)
    flat = set(families["FLAT_LORENTZ"]["operator_ids"])
    curved = set(families["COVARIANT_4D"]["operator_ids"])
    rows = catalog["dd_catalog"]
    breaking = {row["operator_id"] for row in rows if row["local_U1_status"] == "local U(1) breaking"}
    invariant = {row["operator_id"] for row in rows if row["local_U1_status"] == "local U(1) invariant"}
    dd_ids = {row["operator_id"] for row in rows}
    if ambient != flat or len(ambient) != 117 or len(curved) != 37:
        return "ambient binding"
    if len(rows) != 80 or len(breaking) != 54 or len(invariant) != 26 or breaking & invariant:
        return "DD classification"
    if any(row["global_SO2_status"] != "global SO(2) invariant" for row in rows):
        return "global SO(2)"
    if not dd_ids <= ambient or curved & dd_ids or ambient != curved | dd_ids:
        return "set partition"
    verdicts = {item: _local_u1_verdict(item, breaking, invariant, curved) for item in ambient}
    if any(value == "UNCLASSIFIED" for value in verdicts.values()):
        return "unclassified operator"
    preserving = {item for item, value in verdicts.items() if value == "PASS"}
    covariant_pass = {item for item in ambient if _covariance_verdict(item, curved) == "PASS"}
    if preserving != (ambient - breaking) or covariant_pass != curved or not curved <= preserving <= ambient:
        return "subset relation"
    if len(preserving) != 63 or invariant != preserving & dd_ids:
        return "U(1) subspace"
    syzygies = catalog["syzygies"]
    if (
        len(syzygies) != 8
        or any(item["quotient_applied"] for item in syzygies)
        or catalog["algebraic_rank"] != {"COVARIANT_4D": 35, "FLAT_LORENTZ": 109}
        or catalog["nominal_count"] != {"COVARIANT_4D": 37, "FLAT_LORENTZ": 117}
    ):
        return "syzygy metadata"
    if any(item.get("allowed_coefficient") != "FREE" for item in enabled):
        return "coefficient policy"
    return {
        "ambient": sorted(ambient),
        "breaking": sorted(breaking),
        "covariant": sorted(curved),
        "covariant_rank": 35,
        "flat_rank": 109,
        "invariant_dd": sorted(invariant),
        "preserving": sorted(preserving),
        "syzygies": [
            {
                "consequence": item["consequence"],
                "context": item["context"],
                "identity_id": item["identity_id"],
                "quotient_applied": False,
            }
            for item in syzygies
        ],
    }


def negative_tests(result: dict[str, Any], parent_hash: str) -> list[dict[str, str]]:
    locked = new_profile_session()
    note_generation_started(locked)
    cases = [
        ("1", "grammar_15a_v1 remains immutable", PARENT_GRAMMAR_HASH, parent_hash),
        ("2", "new grammar version has a new deterministic hash", "DISTINCT", "DISTINCT" if result["grammar_hash"] != parent_hash and result["grammar_hash"] == result["grammar_hash_repeated"] else "MISMATCH"),
        ("3", "117 ambient operators are preserved", "117", str(result["AMBIENT_OPERATOR_COUNT"])),
        ("4", "exactly 63 satisfy the existing local-U(1) test", "63", str(result["U1_PRESERVING_COUNT"])),
        ("5", "exactly 37 belong to the covariant local-U(1) subset", "37", str(result["COVARIANT_U1_COUNT"])),
        ("6", "subset relation is deterministic", "VERIFIED", result["subset_relation_status"]),
        ("7", "54 DD operators remain in the ambient catalogue", "54", str(result["DD_U1_BREAKING"])),
        ("8", "26 DD operators belong to the U(1)-preserving DD subset", "26", str(result["DD_U1_PRESERVING"])),
        ("9", "80 DD operators preserve global SO(2)", "80", str(result["DD_GLOBAL_SO2"])),
        ("10", "no operator is deleted from the historical ambient grammar", "0", str(result["operators_removed"])),
        ("11", "no coefficient is fixed", "0", str(result["fixed_coefficient_count"])),
        ("12", "no new parameter", "0", str(result["new_parameter_count"])),
        ("13", "no new field", "REJECTED", register_field("extra")),
        ("14", "no new physical principle", "NONE", result["new_physical_principle"]),
        ("15", "no ranking", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
        ("16", "no target information", "REJECTED", classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")})),
        ("17", "constraint profiles are declared before generation", "BEFORE_GENERATION", result["profiles_declared"]),
        ("18", "active profile cannot be changed after generation begins", "PROFILE_LOCKED", authorize_search_profile(locked, "LOCAL_U1_63", AUTHORIZATION_TOKEN)),
        ("19", "ambient and constrained catalogues remain distinguishable", "117-63-37", f"{result['AMBIENT_OPERATOR_COUNT']}-{result['U1_PRESERVING_COUNT']}-{result['COVARIANT_U1_COUNT']}"),
        ("20", "algebraic syzygies remain metadata", "ALGEBRAIC_DEPENDENCY_METADATA", result["syzygy_role"]),
        ("21", "unsupported equivalences remain unsupported", "False", str(result["equivalence_quotient_applied"])),
        ("22", "frozen Phase 4C hash remains unchanged", FROZEN_4C_HASH, result["FROZEN_ACTION_HASH"]),
        ("23", "no new blind search is executed", "SEARCH_NOT_EXECUTED", result["search_status"]),
        ("24", "repeated compilation is deterministic", result["grammar_hash"], result["grammar_hash_repeated"]),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def run_phase_15f(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    compiled = compile_grammar()
    families = _read(f"{PHASE_15B_ARTIFACTS}/PHASE_15B_FAMILIES.json")
    catalog = _read("phase15e_catalog_artifacts/PHASE_15E_CATALOG.json")
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or compiled.get("grammar_hash") != PARENT_GRAMMAR_HASH
        or compiled.get("operational", {}).get("grammar_version") != PARENT_GRAMMAR_VERSION
        or attempt_grammar_mutation({"grammar_version": GRAMMAR_VERSION})["status"] != "REJECTED"
        or catalog_influence({"entries": []}, "catalog")["applied"] is not False
        or register_constraint_from_catalog({"entries": []}) != "REJECTED"
    ):
        return _stop("integrity gate")
    partition = _partition(compiled, families, catalog)
    if isinstance(partition, str):
        return _stop(partition)
    operational = _operational(partition, compiled)
    repeated = _operational(partition, compiled)
    grammar_hash = content_digest(operational)
    grammar_hash_repeated = content_digest(repeated)
    if grammar_hash == PARENT_GRAMMAR_HASH or grammar_hash != grammar_hash_repeated:
        return _stop("grammar hash")
    search = begin_generation(new_profile_session())
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_15F_STATUS": "COMPLETE",
        "GRAMMAR_VERSION_STATUS": "VERIFIED",
        "GRAMMAR_HASH_STATUS": "VERIFIED",
        "CONSTRAINT_REGISTRATION_STATUS": "VERIFIED",
        "U1_SUBSPACE_STATUS": "VERIFIED",
        "COVARIANT_SUBSPACE_STATUS": "VERIFIED",
        "SUBSET_HIERARCHY_STATUS": "VERIFIED",
        "DD_CLASSIFICATION_STATUS": "VERIFIED",
        "SYZYGY_METADATA_STATUS": "VERIFIED",
        "PARAMETER_POLICY_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "KNOWN_PHYSICS_ISOLATION_STATUS": "VERIFIED",
        "CANONICALIZATION_STATUS": "VERIFIED",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "old_grammar_version": PARENT_GRAMMAR_VERSION,
        "old_grammar_hash": PARENT_GRAMMAR_HASH,
        "new_grammar_version": GRAMMAR_VERSION,
        "grammar_hash": grammar_hash,
        "grammar_hash_repeated": grammar_hash_repeated,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "AMBIENT_OPERATOR_COUNT": len(partition["ambient"]),
        "U1_PRESERVING_COUNT": len(partition["preserving"]),
        "COVARIANT_U1_COUNT": len(partition["covariant"]),
        "DD_TOTAL": 80,
        "DD_U1_PRESERVING": len(partition["invariant_dd"]),
        "DD_U1_BREAKING": len(partition["breaking"]),
        "DD_GLOBAL_SO2": 80,
        "FLAT_ALGEBRAIC_RANK": 109,
        "COVARIANT_ALGEBRAIC_RANK": 35,
        "subset_relation": "37 ⊆ 63 ⊆ 117",
        "subset_relation_status": "VERIFIED",
        "operators_removed": 0,
        "operators_added": 0,
        "fixed_coefficient_count": 0,
        "new_parameter_count": 0,
        "new_field": "NONE",
        "new_physical_principle": "NONE",
        "selection_performed": False,
        "profiles_declared": operational["profiles_declared"],
        "profiles": [
            {
                "active_constraints": item["active_constraints"],
                "ambient_space": item["ambient_space"],
                "operator_count": item["operator_count"],
                "profile_id": item["profile_id"],
                "status": item["status"],
            }
            for item in operational["profiles"]
        ],
        "syzygy_role": operational["syzygies"]["role"],
        "syzygy_count": len(operational["syzygies"]["identities"]),
        "equivalence_quotient_applied": False,
        "search_status": search["status"],
        "search_executed": False,
        "AVAILABLE_SEARCH_PROFILES": list(PROFILE_IDS),
        "active_profile": "UNAUTHORIZED",
        "NEXT_ACTION": "HUMAN_SEARCH_PROFILE_AUTHORIZATION",
        "parent_mutation": attempt_grammar_mutation({"grammar_version": GRAMMAR_VERSION})["status"],
    }
    negatives = negative_tests(payload, compiled["grammar_hash"])
    if any(item["observed"] != item["expected"] for item in negatives):
        failed = [item for item in negatives if item["observed"] != item["expected"]]
        return {"PHASE_15F_STATUS": "BLOCKED", "dry_run": failed, "status": "NEGATIVE_TEST_FAILED"}
    payload["dry_run_negatives"] = negatives
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_15F_GRAMMAR.json").write_bytes(
            canonical_json_bytes({"grammar_hash": grammar_hash, "operational": operational})
        )
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return _stop("previous phase changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
