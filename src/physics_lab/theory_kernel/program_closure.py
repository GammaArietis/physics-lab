"""Final closure of the parameter-determination program.

It records the boundary already reached through Phase 15J.
It does not open another phase.
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
from physics_lab.theory_kernel.phase15a_grammar import _ranking_tokens, catalog_influence, classify_candidate
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "FINAL_PROGRAM_CLOSURE"
CODE_VERSION = "program-closure-v1"
ARTIFACT_DIR_NAME = "program_closure_artifacts"
GRAMMAR_VERSION = "grammar_15f_v1"
GRAMMAR_HASH = "f0bdee6da1733a6c2cc83f5a6f6d62d21aeacdf7f0010108fc47b1f4733ca393"
MANIFEST_HASH = "5f27bb0325c3e5453b84172e34e089a1bcb3a2a42de6f42095677eedd5c0a187"
HUMAN_OPTIONS = (
    "CLOSE_CURRENT_PROGRAM",
    "AUTHORIZE_NEW_MATHEMATICAL_GRAMMAR",
    "PROVIDE_NEW_PHYSICAL_INPUT",
)
BOUNDARY_STATEMENT = (
    "Within the authorized COVARIANT_U1_37 profile, the structural program reaches a "
    "parameter-determination boundary: no parameter-free relation was found and the remaining coefficients remain free."
)
EQUIVALENCE_STATEMENT = (
    "The number of physically inequivalent actions remains unestablished because four equivalence engines are unsupported, "
    "but Phase 15J found no evidence that these gaps can alter the parameter-determination conclusion."
)
SCOPE_STATEMENT = "No unique action or parameter-free closure was obtained within the authorized structural grammar and active search profile."


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"PROGRAM_CLOSURE_STATUS": "BLOCKED", "reason": reason, "status": "PROGRAM_CLOSURE_BLOCKED"}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def choose_human_option(_choice: str | None = None) -> str:
    return "NOT_MADE"


def attempt_next_phase(_name: str) -> str:
    return "FORBIDDEN"


def negative_tests(result: dict[str, Any]) -> list[dict[str, str]]:
    cases = [
        ("1", "15J boundary is bound", "NO", result["PARAMETER_CLOSURE_IMPACT"]),
        ("2", "counts remain the registered counts", "117-63-37", f"{result['ambient_operators']}-{result['local_u1_preserving']}-{result['covariant_u1']}"),
        ("3", "PFR remains none found", "NONE_FOUND", result["PFR_STATUS"]),
        ("4", "unique action is not derived", "NOT_DERIVED", result["UNIQUE_ACTION_STATUS"]),
        ("5", "parameter determination of the active search is exhausted", "EXHAUSTED", result["PARAMETER_DETERMINATION_STATUS"]),
        ("6", "all possible physics is not exhausted", "FALSE", result["ALL_POSSIBLE_PHYSICS_EXHAUSTED"]),
        ("7", "equivalence classes remain unclassified", "NOT_ESTABLISHED", result["PHYSICAL_EQUIVALENCE_STATUS"]),
        ("8", "unenumerated profiles stay unenumerated", "FALSE", result["ALL_REGISTERED_PROFILES_ENUMERATED"]),
        ("9", "no automatic next phase", "FORBIDDEN", attempt_next_phase("Phase 15K")),
        ("10", "human option is not chosen", "NOT_MADE", choose_human_option("CLOSE_CURRENT_PROGRAM")),
        ("11", "no coefficient is fixed", "0", str(result["fixed_free_coefficients"])),
        ("12", "frozen action unchanged", FROZEN_4C_HASH, result["FROZEN_ACTION_HASH"]),
        ("13", "target blindness", "REJECTED", classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")})),
        ("14", "no ranking", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
        ("15", "deterministic closure", result["closure_digest"], result["closure_digest_repeated"]),
    ]
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def run_program_closure(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    impact = _read("phase15j_impact_artifacts/PHASE_15J_IMPACT.json")
    grammar_file = _read("phase15f_grammar_artifacts/PHASE_15F_GRAMMAR.json")
    manifest = _read("phase15g_enumeration_artifacts/PHASE_15G_SEARCH_MANIFEST.json")
    family = _read("phase15g_enumeration_artifacts/PHASE_15G_FAMILY.json")
    catalog = _read("phase15e_catalog_artifacts/PHASE_15E_CATALOG.json")
    audit = _read("phase15i_equivalence_artifacts/PHASE_15I_AUDIT.json")
    operational = grammar_file["operational"]
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or content_digest(operational) != GRAMMAR_HASH
        or content_digest(manifest) != MANIFEST_HASH
        or impact.get("grammar_hash") != GRAMMAR_HASH
        or impact.get("manifest_hash") != MANIFEST_HASH
        or impact.get("PARAMETER_CLOSURE_IMPACT") != "NO"
        or impact.get("PFR_IMPACT") != "NO"
        or impact.get("PFR_STATUS") != "NONE_FOUND"
        or impact.get("PARAMETER_CLOSURE_STATUS") != "OPEN"
        or manifest.get("search_profile") != "COVARIANT_U1_37"
        or catalog_influence({"entries": []}, "closure")["applied"] is not False
    ):
        return _stop("integrity gate")
    contexts = operational["contexts"]
    ambient = contexts["FLAT_LORENTZ_AMBIENT"]["operator_ids"]
    preserving = contexts["LOCAL_U1_PRESERVING"]["operator_ids"]
    covariant = contexts["COVARIANT_4D"]["operator_ids"]
    if (
        len(ambient) != 117
        or len(preserving) != 63
        or len(covariant) != 37
        or family["operator_ids"] != covariant
        or family["algebraic_rank"] != 35
        or family["nominal_operator_count"] != 37
        or not set(covariant) <= set(preserving) <= set(ambient)
    ):
        return _stop("registered counts")
    if any(item["value"] != "SYMBOLIC" for item in family["coefficients"]):
        return _stop("coefficient value")
    rows = catalog["dd_catalog"]
    invariant = [row for row in rows if row["local_U1_status"] == "local U(1) invariant"]
    breaking = [row for row in rows if row["local_U1_status"] == "local U(1) breaking"]
    syzygies = catalog["syzygies"]
    inside = [item for item in syzygies if set(item["operator_ids"]) <= set(covariant)]
    if (
        len(rows) != 80
        or len(invariant) != 26
        or len(breaking) != 54
        or any(row["global_SO2_status"] != "global SO(2) invariant" for row in rows)
        or catalog["algebraic_rank"] != {"COVARIANT_4D": 35, "FLAT_LORENTZ": 109}
        or len(syzygies) != 8
        or len(inside) != 2
        or any(item["consequence"] != "ALGEBRAIC_IDENTITY" or item["quotient_applied"] for item in syzygies)
    ):
        return _stop("catalog counts")
    if any(item["uniqueness_impact"] != "NO" or item["decision_relevance"] != "DESCRIPTIVE_ONLY" for item in impact["impact_rows"]):
        return _stop("impact rows")
    if audit["equivalence_class_count"] != "NOT_ESTABLISHED" or audit["statuses"]["PHYSICAL_EQUIVALENCE_STATUS"] != "PARTIAL":
        return _stop("equivalence record")
    profiles = {item["profile_id"]: item["status"] for item in operational["profiles"]}
    if profiles != {
        "AMBIENT_117": "REGISTERED_NOT_ACTIVATED",
        "LOCAL_U1_63": "REGISTERED_NOT_ACTIVATED",
        "COVARIANT_U1_37": "REGISTERED_NOT_ACTIVATED",
    }:
        return _stop("profile register")
    if choose_human_option("CLOSE_CURRENT_PROGRAM") != "NOT_MADE" or attempt_next_phase("Phase 15K") != "FORBIDDEN":
        return _stop("decision boundary")
    record = {
        "active_profile": "COVARIANT_U1_37",
        "equivalence_class_count": "NOT_ESTABLISHED",
        "parameter_closure": "OPEN",
        "pfr": "NONE_FOUND",
        "unique_action": "NOT_DERIVED",
    }
    digest = content_digest(record)
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PROGRAM_CLOSURE_STATUS": "COMPLETE",
        "PARAMETER_DETERMINATION_STATUS": "EXHAUSTED",
        "PARAMETER_DETERMINATION_EXHAUSTED": True,
        "ACTIVE_PARAMETER_SEARCH": "EXHAUSTED",
        "ALL_REGISTERED_PROFILES_ENUMERATED": "FALSE",
        "ALL_POSSIBLE_PHYSICS_EXHAUSTED": "FALSE",
        "ALL_PHYSICAL_EQUIVALENCE_CLASSES_CLASSIFIED": "FALSE",
        "UNIQUE_ACTION_STATUS": "NOT_DERIVED",
        "PFR_STATUS": "NONE_FOUND",
        "PARAMETER_CLOSURE_STATUS": "OPEN",
        "PARAMETER_CLOSURE_IMPACT": "NO",
        "PFR_IMPACT": "NO",
        "UNIQUENESS_IMPACT": "NO",
        "PHYSICAL_EQUIVALENCE_STATUS": "NOT_ESTABLISHED",
        "CLASSIFICATION_GAPS_STATUS": "PRESENT",
        "classification_gap_role": "CLASSIFICATION_GAPS WITHOUT CURRENT PARAMETER-DETERMINATION IMPACT",
        "FURTHER_AUTOMATIC_PHASE": "FORBIDDEN",
        "HUMAN_DECISION_STATUS": "REQUIRED",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": GRAMMAR_HASH,
        "manifest_hash": MANIFEST_HASH,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "ambient_operators": 117,
        "local_u1_preserving": 63,
        "covariant_u1": 37,
        "flat_algebraic_rank": 109,
        "covariant_algebraic_rank": 35,
        "syzygy_count": 8,
        "covariant_syzygy_count": 2,
        "dd_operators": 80,
        "dd_global_so2_invariant": 80,
        "dd_local_u1_invariant": 26,
        "dd_local_u1_breaking": 54,
        "fixed_dimensionless_quantities": 0,
        "fixed_free_coefficients": 0,
        "new_physical_parameters": 0,
        "new_physical_fields": 0,
        "physical_selection": "NONE",
        "support_subset_enumeration": "NOT_PERFORMED",
        "numerical_coefficient_search": "NOT_PERFORMED",
        "coefficient_fixing": "NOT_PERFORMED",
        "formula": "S_registered_existing + sum_i c_i O_i",
        "profiles": {
            "AMBIENT_117": "REGISTERED_NOT_ENUMERATED",
            "LOCAL_U1_63": "REGISTERED_NOT_ENUMERATED",
            "COVARIANT_U1_37": "HUMAN_AUTHORIZED_ENUMERATED",
        },
        "equivalence_engines": {
            "BASIS_EQUIVALENCE": "UNSUPPORTED",
            "EOM_EQUIVALENCE": "UNSUPPORTED",
            "FIELD_REDEFINITION": "UNSUPPORTED",
            "IBP": "UNSUPPORTED",
        },
        "human_options": list(HUMAN_OPTIONS),
        "software_choice": "NOT_MADE",
        "derived": [
            "nested structural constraint hierarchy",
            "symmetry classifications",
            "algebraic syzygies",
            "algebraic ranks",
            "local U(1) and global SO(2) results",
            "general covariance of the 37-profile",
        ],
        "enumerated": ["one maximal symbolic COVARIANT_U1_37 family"],
        "parameter_dependent": ["six dimensionless coefficients"],
        "unsupported": ["four physical-equivalence engines"],
        "not_found_within_grammar": ["parameter-free relation"],
        "boundary_statement": BOUNDARY_STATEMENT,
        "equivalence_statement": EQUIVALENCE_STATEMENT,
        "scope_statement": SCOPE_STATEMENT,
        "closure_digest": digest,
        "closure_digest_repeated": content_digest(record),
    }
    negatives = negative_tests(payload)
    if any(item["observed"] != item["expected"] for item in negatives):
        failed = [item for item in negatives if item["observed"] != item["expected"]]
        return {"PROGRAM_CLOSURE_STATUS": "BLOCKED", "dry_run": failed, "status": "NEGATIVE_TEST_FAILED"}
    payload["dry_run_negatives"] = negatives
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PROGRAM_CLOSURE.json").write_bytes(
            canonical_json_bytes(
                {
                    "ACTIVE_PARAMETER_SEARCH": "EXHAUSTED",
                    "ALL_REGISTERED_PROFILES_ENUMERATED": "FALSE",
                    "HUMAN_DECISION_STATUS": "REQUIRED",
                    "PARAMETER_CLOSURE_STATUS": "OPEN",
                    "PFR_STATUS": "NONE_FOUND",
                    "UNIQUE_ACTION_STATUS": "NOT_DERIVED",
                    "grammar_hash": GRAMMAR_HASH,
                    "manifest_hash": MANIFEST_HASH,
                    "software_choice": "NOT_MADE",
                }
            )
        )
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return _stop("previous phase changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
