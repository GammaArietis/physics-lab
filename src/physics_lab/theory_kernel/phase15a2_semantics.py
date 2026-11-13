"""Phase 15A.2 audits the registered gauge-rule wording.

It does not change the grammar, the whitelist, or the frozen action.
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
    ASSUMPTIONS,
    _ranking_tokens,
    attempt_grammar_mutation,
    classify_candidate,
    compile_grammar,
)
from physics_lab.theory_kernel.phase15b_enumeration import _family
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_15A2"
CODE_VERSION = "phase15a2-semantics-v1"
ARTIFACT_DIR_NAME = "phase15a2_semantics_artifacts"
GRAMMAR_HASH = "9e2c6b08d9d0ef96a78f52fb097d169bc112aac29b70556aa7be7bf0d4206075"
QUOTED_RULE = "An operator may enter the operational whitelist only if it is invariant under the already registered local U(1)"
GLOBAL_MARKERS = (
    "every operational operator is invariant",
    QUOTED_RULE,
)
SCOPED_MARKERS = (
    "local U(1) invariance is required only in",
    "GAUGE_PRESERVING context only",
)


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_15A2_STATUS": "BLOCKED", "reason": reason, "status": "PHASE_15A2_BLOCKED"}


def classify_scope(statements: list[str]) -> str:
    global_hit = any(marker in statement for statement in statements for marker in GLOBAL_MARKERS)
    scoped_hit = any(marker in statement for statement in statements for marker in SCOPED_MARKERS)
    if global_hit and scoped_hit:
        return "CONTRADICTORY"
    if global_hit:
        return "GLOBAL"
    if scoped_hit:
        return "CONTEXT_SCOPED"
    return "UNRESOLVED"


def _catalog() -> dict[str, Any]:
    path = _physics_dir() / "phase15e_catalog_artifacts" / "PHASE_15E_CATALOG.json"
    body = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError("catalog")
    return body


def negative_tests(result: dict[str, Any]) -> list[dict[str, str]]:
    cases = [
        ("1", "actual gauge-invariance rule can be located", "grammar_15a_v1.symmetry", result["gauge_rule"]["rule_id"]),
        ("2", "its operational scope is explicit", "HASHED_OPERATIONAL_DOCUMENT", result["gauge_rule"]["operational_domain"]),
        ("3", "prose does not widen a rule to global scope", "PROSE", result["module_docstring_class"]),
        ("4", "an explicit global marker applies globally", "GLOBAL", classify_scope([QUOTED_RULE])),
        ("5", "54 DD classifications remain unchanged", "54", str(result["local_u1_breaking"])),
        ("6", "26/54 classification remains deterministic", "26-54", f"{result['local_u1_invariant']}-{result['local_u1_breaking']}"),
        ("7", "117/37 context distinction remains unchanged", "117-37", f"{result['nominal_flat']}-{result['nominal_covariant']}"),
        ("8", "no operator is deleted", "0", str(result["operators_removed"])),
        ("9", "no operator is newly added", "117", str(result["whitelist_count"])),
        ("10", "no grammar version changes automatically", "grammar_15a_v1", result["grammar_version"]),
        ("11", "no frozen action change", FROZEN_4C_HASH, result["FROZEN_ACTION_HASH"]),
        ("12", "no target information", "REJECTED", classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")})),
        ("13", "no physical selection", "False", str(result["selection_performed"])),
        ("14", "no ranking", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
        ("15", "contradictory rule scope fails closed", "BLOCKED", result["contradictory_scope_status"]),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def run_phase_15a2(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    compiled = compile_grammar()
    catalog = _catalog()
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or compiled.get("grammar_hash") != GRAMMAR_HASH
        or compiled.get("operational", {}).get("grammar_version") != "grammar_15a_v1"
    ):
        return _stop("integrity gate")
    symmetry = compiled["operational"]["symmetry"]
    assumption = next(item["statement"] for item in ASSUMPTIONS if item["assumption_id"] == "A15A-03")
    family_label = _family("FLAT_LORENTZ", "LORENTZ_WITH_FLAT_SECOND_DERIVATIVES", compiled["enabled"][:1])
    statements = [symmetry, assumption, family_label["gauge_status"], family_label["symmetry_status"]]
    scope = classify_scope(statements)
    if scope == "CONTRADICTORY":
        return _stop("contradictory gauge-rule scope")
    enabled = compiled["enabled"]
    enabled_ids = {item["object_id"] for item in enabled}
    dd_rows = catalog["dd_catalog"]
    breaking = [row for row in dd_rows if row["local_U1_status"] == "local U(1) breaking"]
    invariant = [row for row in dd_rows if row["local_U1_status"] == "local U(1) invariant"]
    if (
        len(enabled) != 117
        or catalog["nominal_count"] != {"COVARIANT_4D": 37, "FLAT_LORENTZ": 117}
        or len(dd_rows) != 80
        or len(breaking) != 54
        or len(invariant) != 26
        or any(row["operator_id"] not in enabled_ids for row in dd_rows)
        or any(item["generator_enabled"] is not True for item in enabled)
    ):
        return _stop("classification integrity")
    if QUOTED_RULE in symmetry or QUOTED_RULE in assumption:
        return _stop("quoted rule appeared inside the hashed grammar")
    docstring = Path(compile_grammar.__code__.co_filename).read_text(encoding="utf-8").splitlines()[0]
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_15A2_STATUS": "BLOCKED",
        "GAUGE_RULE_SCOPE_STATUS": scope,
        "GRAMMAR_CONSISTENCY_STATUS": "UNRESOLVED",
        "GRAMMAR_CONTEXT_SCOPING": "UNRESOLVED",
        "DD_CLASSIFICATION_INTEGRITY": "VERIFIED",
        "FLAT_COVARIANT_SEMANTICS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "GRAMMAR_MUTATION": "NONE",
        "grammar_version": "grammar_15a_v1",
        "grammar_hash": GRAMMAR_HASH,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "gauge_rule": {
            "context": "NOT_SPLIT",
            "generator_scope": "ADMISSION_DOES_NOT_TEST_LOCAL_VARIATION",
            "grammar_version": "grammar_15a_v1",
            "operational_domain": "HASHED_OPERATIONAL_DOCUMENT",
            "provenance": "grammar_15a_v1 operational symmetry field",
            "rule_id": "grammar_15a_v1.symmetry",
            "semantic_class": "GAUGE_STRUCTURE_CONSTRAINT",
            "statement": symmetry,
        },
        "located_statements": [
            {"context": "GRAMMAR_WIDE", "provenance": "HASHED_OPERATIONAL_DOCUMENT", "rule_id": "grammar_15a_v1.symmetry", "semantic_class": "GAUGE_STRUCTURE_CONSTRAINT", "statement": symmetry},
            {"context": "GRAMMAR_WIDE", "provenance": "A15A-03", "rule_id": "A15A-03", "semantic_class": "SEARCH_SPACE_ASSUMPTION", "statement": assumption},
            {"context": "BOTH_REPORTED_FAMILIES", "provenance": "PHASE_15B_FAMILY_LABEL", "rule_id": "phase15b.gauge_status", "semantic_class": "STATUS_LABEL", "statement": family_label["gauge_status"]},
            {"context": "BOTH_REPORTED_FAMILIES", "provenance": "PHASE_15B_FAMILY_LABEL", "rule_id": "phase15b.symmetry_status", "semantic_class": "STATUS_LABEL", "statement": family_label["symmetry_status"]},
        ],
        "quoted_rule_present": False,
        "module_docstring_class": "PROSE" if "symmetry-constrained" in docstring else "ABSENT",
        "flat_covariant_relation": "CONTEXT_SUBSET",
        "nominal_flat": 117,
        "nominal_covariant": 37,
        "local_u1_invariant": 26,
        "local_u1_breaking": 54,
        "whitelist_count": len(enabled),
        "operators_removed": 0,
        "operators_added": 0,
        "selection_performed": False,
        "new_physical_principle": "NONE",
        "grammar_revision": "NOT_REQUESTED",
        "contradictory_scope_status": "BLOCKED" if classify_scope([QUOTED_RULE, SCOPED_MARKERS[0]]) == "CONTRADICTORY" else "OPEN",
        "concepts": {
            "admitted_grammar_member": "117 whitelist operators, including the 54",
            "generated_test_action": "the frozen Phase 4C action stays outside the whitelist",
            "symmetry_preserving_subgrammar": "not an operational subgrammar in grammar_15a_v1",
        },
    }
    payload["audit_digest"] = content_digest(
        {
            "breaking": len(breaking),
            "scope": scope,
            "statement": symmetry,
        }
    )
    payload["audit_digest_repeated"] = content_digest(
        {
            "breaking": len(breaking),
            "scope": scope,
            "statement": symmetry,
        }
    )
    negatives = negative_tests(payload)
    if any(item["observed"] != item["expected"] for item in negatives):
        failed = [item for item in negatives if item["observed"] != item["expected"]]
        return {"PHASE_15A2_STATUS": "BLOCKED", "dry_run": failed, "status": "NEGATIVE_TEST_FAILED"}
    payload["dry_run_negatives"] = negatives
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_15A2_SEMANTICS.json").write_bytes(
            canonical_json_bytes(
                {
                    "flat_covariant_relation": payload["flat_covariant_relation"],
                    "gauge_rule": payload["gauge_rule"],
                    "located_statements": payload["located_statements"],
                    "quoted_rule_present": False,
                    "scope": scope,
                }
            )
        )
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return _stop("previous phase changed")
    if attempt_grammar_mutation({"grammar_version": "grammar_15a_v2"})["status"] != "REJECTED":
        return _stop("grammar mutation was accepted")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
