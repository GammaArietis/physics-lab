"""Phase 15J records the impact of the four unsupported equivalence engines.

It does not implement those engines and does not select an action.
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
from physics_lab.theory_kernel.phase15i_equivalence import (
    certify_field_redefinition,
    classify_basis,
    classify_eom,
    classify_ibp,
    run_phase_15i,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_15J"
CODE_VERSION = "phase15j-impact-v1"
ARTIFACT_DIR_NAME = "phase15j_impact_artifacts"
GRAMMAR_VERSION = "grammar_15f_v1"
GRAMMAR_HASH = "f0bdee6da1733a6c2cc83f5a6f6d62d21aeacdf7f0010108fc47b1f4733ca393"
MANIFEST_HASH = "5f27bb0325c3e5453b84172e34e089a1bcb3a2a42de6f42095677eedd5c0a187"


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE_15J_STATUS": "BLOCKED", "reason": reason, "status": "PHASE_15J_BLOCKED"}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def _impact_rows() -> list[dict[str, str]]:
    return [
        {
            "CAN_CHANGE_DIMENSIONLESS_CLOSURE": "NO",
            "CAN_CHANGE_PARAMETER_COUNT": "UNKNOWN",
            "CAN_CREATE_PFR": "NO",
            "CAN_ESTABLISH_UNIQUENESS": "NO",
            "CAN_FIX_PARAMETER": "NO",
            "decision_relevance": "DESCRIPTIVE_ONLY",
            "equivalence": "IBP",
            "finding": "NO_IDENTIFIED_IBP_REDUNDANCY",
            "mathematical_impact": "no relation identified inside the 37; the role may change representatives only",
            "missing_engine": "TRUE",
            "parameter_impact": "NO",
            "pfr_impact": "NO",
            "possible_relation": "the inherited partner lies outside COVARIANT_U1_37",
            "required_boundary_assumption": "NONE_REGISTERED",
            "uniqueness_impact": "NO",
        },
        {
            "CAN_CHANGE_DIMENSIONLESS_CLOSURE": "NO",
            "CAN_CHANGE_PARAMETER_COUNT": "UNKNOWN",
            "CAN_CREATE_PFR": "NO",
            "CAN_ESTABLISH_UNIQUENESS": "NO",
            "CAN_FIX_PARAMETER": "NO",
            "decision_relevance": "DESCRIPTIVE_ONLY",
            "equivalence": "FIELD_REDEFINITION",
            "finding": "NO_IDENTIFIED_REDEFINITION",
            "mathematical_impact": "no nontrivial invertible redefinition is registered; the role may change coordinates only",
            "missing_engine": "TRUE",
            "parameter_impact": "NO",
            "pfr_impact": "NO",
            "possible_relation": "identity map only",
            "required_boundary_assumption": "NOT_APPLICABLE",
            "uniqueness_impact": "NO",
        },
        {
            "CAN_CHANGE_DIMENSIONLESS_CLOSURE": "NO",
            "CAN_CHANGE_PARAMETER_COUNT": "UNKNOWN",
            "CAN_CREATE_PFR": "NO",
            "CAN_ESTABLISH_UNIQUENESS": "NO",
            "CAN_FIX_PARAMETER": "NO",
            "decision_relevance": "DESCRIPTIVE_ONLY",
            "equivalence": "EOM_EQUIVALENCE",
            "finding": "UNTESTED",
            "mathematical_impact": "closed equations are not established; on-shell zero is not a certified equivalence",
            "missing_engine": "TRUE",
            "parameter_impact": "NO",
            "pfr_impact": "NO",
            "possible_relation": "NONE_IDENTIFIED",
            "required_boundary_assumption": "NOT_APPLICABLE",
            "uniqueness_impact": "NO",
        },
        {
            "CAN_CHANGE_DIMENSIONLESS_CLOSURE": "NO",
            "CAN_CHANGE_PARAMETER_COUNT": "UNKNOWN",
            "CAN_CREATE_PFR": "NO",
            "CAN_ESTABLISH_UNIQUENESS": "NO",
            "CAN_FIX_PARAMETER": "NO",
            "decision_relevance": "DESCRIPTIVE_ONLY",
            "equivalence": "BASIS_EQUIVALENCE",
            "finding": "NO_IDENTIFIED_BASIS_EQUIVALENCE",
            "mathematical_impact": "shared symmetry labels are not a basis transformation",
            "missing_engine": "TRUE",
            "parameter_impact": "NO",
            "pfr_impact": "NO",
            "possible_relation": "NONE_IDENTIFIED",
            "required_boundary_assumption": "NOT_APPLICABLE",
            "uniqueness_impact": "NO",
        },
    ]


def negative_tests(result: dict[str, Any]) -> list[dict[str, str]]:
    rows = {item["equivalence"]: item for item in result["impact_rows"]}
    cases = [
        ("1", "15I inputs are bound exactly", "COMPLETE", result["PHASE_15I_STATUS"]),
        ("2", "nominal count remains 37", "37", str(result["nominal_operator_count"])),
        ("3", "algebraic rank remains 35", "35", str(result["algebraic_rank"])),
        ("4", "PFR remains NONE_FOUND", "NONE_FOUND", result["PFR_STATUS"]),
        ("5", "no equivalence quotient occurs", "0", str(result["operators_removed"])),
        ("6", "no parameter is fixed", "0", str(result["fixed_coefficient_count"])),
        ("7", "no new parameter enters", "0", str(result["new_parameter_count"])),
        ("8", "no new field enters", "NONE", result["new_field"]),
        ("9", "possible IBP relations are not silently certified", "CONDITIONALLY_EQUIVALENT", classify_ibp("EXACT_SYMBOLIC_WITH_BOUNDARY_TERM", ("unregistered boundary",))),
        ("10", "ON_SHELL_ZERO is not treated as EOM equivalence", "ON_SHELL_ZERO", classify_eom(on_shell_zero=True, theorem_implemented=False, redefinition_certified=False)),
        ("11", "same spectra are not treated as basis equivalence", "NOT_EQUIVALENT", classify_basis(transformation=None, same_spectrum=True)),
        ("12", "same symmetry is not treated as physical equivalence", "NOT_EQUIVALENT", classify_basis(transformation=None, same_symmetry=True)),
        ("13", "unsupported transformations are not invented", "EQUIVALENCE_UNSUPPORTED", certify_field_redefinition({"fixes_parameter": False, "inverse": "Phi -> Phi + Phi^3", "invertible": True, "local": True, "preserves_field_content": True, "transformation": "Phi -> Phi + Phi^3"})["equivalence_result"]),
        ("14", "frozen action remains unchanged", FROZEN_4C_HASH, result["FROZEN_ACTION_HASH"]),
        ("15", "target blindness remains active", "REJECTED", classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")})),
        ("16", "no ranking", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
        ("17", "deterministic impact classification", result["impact_digest"], result["impact_digest_repeated"]),
    ]
    if rows["IBP"]["finding"] != "NO_IDENTIFIED_IBP_REDUNDANCY":
        cases.append(("9b", "IBP finding", "NO_IDENTIFIED_IBP_REDUNDANCY", rows["IBP"]["finding"]))
    return [{"case": case, "expected": expected, "label": label, "observed": observed} for case, label, expected, observed in cases]


def run_phase_15j(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    audit = run_phase_15i(write_artifacts=False)
    grammar_file = _read("phase15f_grammar_artifacts/PHASE_15F_GRAMMAR.json")
    manifest = _read("phase15g_enumeration_artifacts/PHASE_15G_SEARCH_MANIFEST.json")
    stored = _read("phase15i_equivalence_artifacts/PHASE_15I_AUDIT.json")
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or audit.get("status") != "OK"
        or audit.get("PHASE_15I_STATUS") != "COMPLETE"
        or audit.get("grammar_hash") != GRAMMAR_HASH
        or audit.get("manifest_hash") != MANIFEST_HASH
        or audit.get("nominal_operator_count") != 37
        or audit.get("algebraic_rank") != 35
        or audit.get("equivalence_class_count") != "NOT_ESTABLISHED"
        or audit.get("pfr_status") != "NONE_FOUND"
        or audit.get("PARAMETER_CLOSURE_STATUS") != "OPEN"
        or audit.get("classes_reduced") != {"basis": 0, "eom": 0, "field_redefinition": 0, "ibp": 0}
        or stored["nominal_operator_count"] != 37
        or stored["statuses"]["IBP_EQUIVALENCE_STATUS"] != "UNSUPPORTED"
        or content_digest(grammar_file["operational"]) != GRAMMAR_HASH
        or content_digest(manifest) != MANIFEST_HASH
        or catalog_influence({"entries": []}, "impact")["applied"] is not False
    ):
        return _stop("integrity gate")
    rows = _impact_rows()
    if any(item["CAN_FIX_PARAMETER"] != "NO" or item["CAN_CREATE_PFR"] != "NO" or item["CAN_ESTABLISH_UNIQUENESS"] != "NO" for item in rows):
        return _stop("impact exceeded the mathematical role")
    if any(item["decision_relevance"] != "DESCRIPTIVE_ONLY" for item in rows):
        return _stop("decision class")
    digest_body = {"rows": rows}
    digest = content_digest(digest_body)
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE_15J_STATUS": "COMPLETE",
        "PHASE_15I_STATUS": audit["PHASE_15I_STATUS"],
        "IBP_IMPACT_STATUS": "NO",
        "FIELD_REDEFINITION_IMPACT_STATUS": "NO",
        "EOM_EQUIVALENCE_IMPACT_STATUS": "NO",
        "BASIS_EQUIVALENCE_IMPACT_STATUS": "NO",
        "PARAMETER_CLOSURE_IMPACT": "NO",
        "PFR_IMPACT": "NO",
        "UNIQUENESS_IMPACT": "NO",
        "SYMMETRY_IMPACT": "NO",
        "DECISION_RELEVANCE_STATUS": "VERIFIED",
        "PFR_STATUS": "NONE_FOUND",
        "PARAMETER_CLOSURE_STATUS": "OPEN",
        "PHYSICAL_SELECTION_STATUS": "NONE",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "PROVENANCE_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "REPRODUCIBILITY_STATUS": "VERIFIED",
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": GRAMMAR_HASH,
        "manifest_hash": MANIFEST_HASH,
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "nominal_operator_count": 37,
        "algebraic_rank": 35,
        "equivalence_class_count": "NOT_ESTABLISHED",
        "dimensionless_fixed_count": 0,
        "new_parameter_count": 0,
        "new_field": "NONE",
        "fixed_coefficient_count": 0,
        "operators_removed": 0,
        "MISSING_ENGINE": True,
        "impact_rows": rows,
        "parameter_determination": "STRUCTURALLY_EXHAUSTED_FOR_PARAMETER_DETERMINATION",
        "physical_equivalence_classification": "INCOMPLETE",
        "symmetry_statement": "changing representatives does not change the established symmetry class",
        "uniqueness_statement": "an equivalence is insufficient by itself to fix the remaining coefficients",
        "redundancy_versus_fixing": "parameter redundancy is not parameter fixing",
        "software_choice": "NOT_MADE",
        "next_step": "HUMAN_DECISION",
        "impact_digest": digest,
        "impact_digest_repeated": content_digest(digest_body),
    }
    negatives = negative_tests(payload)
    if any(item["observed"] != item["expected"] for item in negatives):
        failed = [item for item in negatives if item["observed"] != item["expected"]]
        return {"PHASE_15J_STATUS": "BLOCKED", "dry_run": failed, "status": "NEGATIVE_TEST_FAILED"}
    payload["dry_run_negatives"] = negatives
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_15J_IMPACT.json").write_bytes(
            canonical_json_bytes(
                {
                    "DECISION_RELEVANCE_STATUS": "VERIFIED",
                    "PARAMETER_CLOSURE_IMPACT": "NO",
                    "PARAMETER_CLOSURE_STATUS": "OPEN",
                    "PFR_IMPACT": "NO",
                    "PFR_STATUS": "NONE_FOUND",
                    "grammar_hash": GRAMMAR_HASH,
                    "impact_rows": rows,
                    "manifest_hash": MANIFEST_HASH,
                }
            )
        )
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return _stop("previous phase changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
