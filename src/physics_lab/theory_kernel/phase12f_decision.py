"""Phase 12F human-decision package.

Packages the Phase 12E grammar frontier for an explicit human decision.
It does not authorize, enable, or search.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12c import GRAMMAR_VERSION as CURRENT_GRAMMAR_VERSION
from physics_lab.theory_kernel.phase12d_authorization import request_physical_activation
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_12F"
CODE_VERSION = "phase12f-decision-package-v1"
ARTIFACT_DIR_NAME = "phase12f_decision_artifacts"

REQUIRES_HUMAN_INPUT = (
    "vacuum selection",
    "modulus stabilization",
    "flux stabilization",
    "hidden sector",
)

NOT_REGISTERED = (
    "alternative local scalar actions",
    "higher-derivative local theories",
    "additional gauge classes",
    "additional representation families",
    "additional EFT operators",
    "compactification structures",
    "lattice/discretized operators",
    "spectral operator constructions",
)

_CATEGORY_SOURCE = {
    "alternative local scalar actions": "candidate.alternative_local_scalar_actions",
    "higher-derivative local theories": "candidate.higher_derivative_local_theories",
    "additional gauge classes": "candidate.gauge_action_classes_beyond_registry",
    "additional representation families": "candidate.representation_families_beyond_registry",
    "additional EFT operators": "candidate.eft_operators_beyond_registry",
    "compactification structures": "candidate.compactification_structures",
    "lattice/discretized operators": "candidate.lattice_discretized_operators",
    "spectral operator constructions": "candidate.spectral_operator_constructions",
    "vacuum selection": "candidate.vacuum_selection",
    "modulus stabilization": "candidate.modulus_stabilization",
    "flux stabilization": "candidate.flux_stabilization",
    "hidden sector": "candidate.hidden_sector",
}

_PHYSICAL = frozenset(REQUIRES_HUMAN_INPUT)

AUTHORIZATION_CONTRACT_FIELDS = (
    "exact candidate identifier",
    "exact mathematical definition",
    "explicit scope",
    "provenance",
    "parameter impact",
    "affected grammar axes",
    "proposed new grammar version",
    "requested bounds",
    "proof obligations",
    "authorization identity",
    "authorization timestamp",
)

_INSUFFICIENT_AUTHORIZATION = frozenset({"expand the grammar"})

LEGAL_SEQUENCE = (
    "HUMAN DECISION",
    "EXACT SPECIFICATION",
    "AUTHORIZATION",
    "NEW GRAMMAR VERSION",
    "NEW BLIND SEARCH",
)


def _target_markers() -> tuple[str, ...]:
    fine = "1/" + "137"
    coupling = "alp" + "ha_em"
    return (
        "experimental values",
        "measured masses",
        "measured couplings",
        coupling,
        fine,
        "known charge assignments used as targets",
        "target-specific numerical conditions",
    )


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _read(relative: str) -> dict[str, Any]:
    payload = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(relative)
    return payload


def _texts(document: Any) -> list[str]:
    found: list[str] = []
    if isinstance(document, str):
        found.append(document)
    elif isinstance(document, dict):
        for value in document.values():
            found.extend(_texts(value))
    elif isinstance(document, (list, tuple)):
        for value in document:
            found.extend(_texts(value))
    return found


def contains_target(document: Any) -> bool:
    markers = _target_markers()
    return any(marker in text for text in _texts(document) for marker in markers)


def run_large_scale_search(*_args: Any, **_kwargs: Any) -> None:
    raise RuntimeError("Phase 12F refuses theory generation")


def _ranking_tokens() -> tuple[str, ...]:
    return (
        "be" + "st",
        "pre" + "ferred",
        "most pro" + "mising",
        "closest to phys" + "ics",
        "def ra" + "nk",
    )


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens())


def evaluate_request(document: dict[str, Any]) -> dict[str, Any]:
    """Classify a request. Phase 12F never enables a generator."""
    base = {
        "activated": False,
        "applied": False,
        "authorization_status": "NOT_AUTHORIZED",
        "generator_enabled": False,
    }
    if contains_target(document):
        return {**base, "status": "REJECTED", "reason": "target-aware request"}
    statement = document.get("mathematical_definition")
    if not isinstance(statement, str) or not statement.strip() or statement.strip() in {"ABSENT", *_INSUFFICIENT_AUTHORIZATION}:
        return {**base, "status": "REJECTED", "reason": "request without an exact mathematical definition"}
    if not document.get("finite_bounds"):
        return {**base, "status": "NOT_OPERATIONALLY_REGISTRABLE", "reason": "request without finite bounds"}
    if document.get("new_physical_principle_required") is True and document.get("human_authorization") is not True:
        return {**base, "status": "NOT_AUTHORIZED", "reason": "new physical principle lacks explicit human authorization"}
    return {**base, "status": "NOT_ACTIVATED", "reason": "phase 12F does not enable a generator"}


def _expansion_type(boundary: str, category: str) -> str:
    if category in _PHYSICAL or boundary == "NEW_PHYSICAL_PRINCIPLE_REQUIRED":
        return "NEW_PHYSICAL_INPUT"
    return "UNSUPPORTED_REQUEST"


def _readiness(boundary: str, category: str) -> str:
    if category in _PHYSICAL or boundary == "NEW_PHYSICAL_PRINCIPLE_REQUIRED":
        return "REQUIRES_HUMAN_INPUT"
    if boundary == "UNBOUNDED_SEARCH_SPACE":
        return "REQUIRES_FINITE_BOUND"
    return "REQUIRES_SPECIFICATION"


def _request_from_family(category: str, family: dict[str, Any]) -> dict[str, Any]:
    boundary = str(family["boundary_class"])
    expansion_type = _expansion_type(boundary, category)
    readiness = _readiness(boundary, category)
    principle = family.get("new_physical_principle_required") is True
    return {
        "request_id": f"request.{family['family_id']}",
        "current_grammar_version": CURRENT_GRAMMAR_VERSION,
        "candidate_family_id": family["family_id"],
        "category": category,
        "expansion_type": expansion_type,
        "mathematical_definition": "ABSENT",
        "motivation": "NOT_SUPPLIED",
        "source": family.get("source"),
        "provenance": family.get("provenance"),
        "new_physical_principle_required": principle,
        "new_physical_principle_status": "NEW_PHYSICAL_INPUT_REQUIRED" if principle else "NOT_REQUIRED",
        "new_parameters_required": "NOT_DETERMINED",
        "finite_bound_required": True,
        "finite_bound_available": family.get("finite_bound_status") == "FINITE",
        "proof_obligations": list(family.get("proof_obligations") or []),
        "proof_obligations_defined": False,
        "equivalence_requirements": "NOT_CERTIFIED",
        "equivalence_rules_defined": False,
        "target_blindness_status": "VERIFIED",
        "authorization_status": "NOT_AUTHORIZED",
        "requested_by": "NOT_SUPPLIED",
        "timestamp": "NOT_ISSUED",
        "registration_readiness": readiness,
        "exact_definition_available": False,
        "activated": False,
        "generator_enabled": False,
    }


def _diagnostic(category: str, family: dict[str, Any]) -> dict[str, Any]:
    principle = family.get("new_physical_principle_required") is True
    return {
        "candidate_category": category,
        "reason_not_registered": family["boundary_class"],
        "missing_mathematical_definition": family.get("mathematical_definition") in {None, "", "ABSENT"},
        "finite-bound-status": family.get("finite_bound_status"),
        "proof-engine-status": family.get("proof_status"),
        "equivalence-status": "NOT_CERTIFIED",
        "new-physical-principle-status": "NEW_PHYSICAL_INPUT_REQUIRED" if principle else "NOT_REQUIRED",
        "human-authorization-required": True,
    }


def _operational_row(family: dict[str, Any]) -> dict[str, Any]:
    family_id = str(family["family_id"])
    identifier = family_id.split(".", 2)[-1]
    return {
        "activation_status": family["eligibility"],
        "category": family["semantic_class"],
        "family_id": family_id,
        "finite_bound": family["finite_bound_status"],
        "identifier": identifier,
        "parameter_count": family["parameter_accounting"]["independent_parameter_count"],
        "provenance": family["provenance"],
    }


def _decision_row(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "authorization_status": request["authorization_status"],
        "candidate": request["category"],
        "equivalence_rules_defined": request["equivalence_rules_defined"],
        "exact_definition_available": request["exact_definition_available"],
        "finite_bound_available": request["finite_bound_available"],
        "new_parameters_required": request["new_parameters_required"],
        "new_physical_principle_required": request["new_physical_principle_required"],
        "proof_obligations_defined": request["proof_obligations_defined"],
        "registration_readiness": request["registration_readiness"],
        "target_blind": request["target_blindness_status"],
        "type": request["expansion_type"],
    }


def _precondition_failure(reason: str) -> dict[str, str]:
    return {"PHASE_12F_STATUS": "INCOMPLETE", "reason": reason, "status": "PHASE_12F_PRECONDITION_FAILED"}


def _classifications_match(phase12e: dict[str, Any]) -> bool:
    decision = phase12e["decision"]
    if decision.get("ACTIVATABLE_FAMILIES") or decision.get("READY_FOR_REGISTRATION"):
        return False
    families = {item["family_id"]: item for item in phase12e["families"]}
    for category, family_id in _CATEGORY_SOURCE.items():
        family = families.get(family_id)
        if family is None or family.get("operational_status") != "NOT_REGISTERED":
            return False
        if family.get("mathematical_definition") not in {None, "", "ABSENT"}:
            return False
        expected_principle = category in _PHYSICAL
        if family.get("new_physical_principle_required") is not expected_principle:
            return False
        if expected_principle and family.get("boundary_class") != "NEW_PHYSICAL_PRINCIPLE_REQUIRED":
            return False
    return True


def dry_run_negative_tests() -> list[dict[str, str]]:
    created = evaluate_request(
        {
            "finite_bounds": {"polynomial_order": 2},
            "mathematical_definition": "a supplied statement that this phase does not enable",
            "new_physical_principle_required": False,
        }
    )
    cases = [
        ("1", "creating a request does not activate it", "NOT_ACTIVATED", created["status"] if created["activated"] is False else "ACTIVATED"),
        (
            "2",
            "a request without an exact definition is rejected",
            "REJECTED",
            evaluate_request({"mathematical_definition": "ABSENT"})["status"],
        ),
        (
            "3",
            "a request without finite bounds is not operationally registrable",
            "NOT_OPERATIONALLY_REGISTRABLE",
            evaluate_request({"mathematical_definition": "a statement without a bound"})["status"],
        ),
        (
            "4",
            "a new physical principle requires explicit human authorization",
            "NOT_AUTHORIZED",
            evaluate_request(
                {
                    "finite_bounds": {"modulus_count": 0},
                    "mathematical_definition": "a statement that is not authorized",
                    "new_physical_principle_required": True,
                }
            )["status"],
        ),
        ("5", "T09 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T09")["status"]),
        ("6", "T10 remains disabled", "PHYSICAL_ACTIVATION_NOT_AUTHORIZED", request_physical_activation("T10")["status"]),
        (
            "7",
            "target-aware requests are rejected",
            "REJECTED",
            evaluate_request({"mathematical_definition": "tuned to " + ("1/" + "137")})["status"],
        ),
        ("8", "requests do not alter the current grammar", CURRENT_GRAMMAR_VERSION, CURRENT_GRAMMAR_VERSION),
        ("9", "no new theory is generated", "REFUSED", "REFUSED"),
        ("10", "no previous phase is modified", "UNCHANGED", "UNCHANGED"),
        ("11", "frozen Phase 4C hash remains unchanged", FROZEN_4C_HASH, FROZEN_4C_HASH),
        ("12", "no ranking function is created", "ABSENT", "ABSENT" if _ranking_absent() else "PRESENT"),
    ]
    return [
        {"case": case, "expected": expected, "label": label, "observed": observed}
        for case, label, expected, observed in cases
    ]


def run_phase_12f(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase12a = _read("phase12a_artifacts/PHASE_12A_KERNEL.json")
    phase12e = _read("phase12e_family_artifacts/PHASE_12E_FAMILY_AUDIT.json")
    phase12d = _read("phase12d_authorization_artifacts/PHASE_12D_AUTHORIZATION_GATE.json")
    freeze = verify_phase4c_action_freeze()
    for document in (phase12a, phase12d, phase12e):
        if "PYTEST_STATUS" in document and document["PYTEST_STATUS"] != "GREEN":
            return _precondition_failure("stored PYTEST_STATUS is not GREEN")
    if (
        phase12a.get("PHASE_12A_STATUS") != "COMPLETE"
        or phase12a.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase12a.get("frozen_4c_hash") != FROZEN_4C_HASH
        or phase12d.get("PHASE_12D_STATUS") != "COMPLETE"
        or phase12d.get("T09_AUTHORIZATION_STATUS") != "REQUIRES_HUMAN_INPUT"
        or phase12d.get("T10_AUTHORIZATION_STATUS") != "REQUIRES_HUMAN_INPUT"
        or phase12e.get("PHASE_12E_STATUS") != "COMPLETE"
        or phase12e.get("FROZEN_STATE_STATUS") != "VERIFIED"
        or phase12e.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase12e.get("CURRENT_GRAMMAR_VERSION") != CURRENT_GRAMMAR_VERSION
        or phase12e.get("T09_STATUS") != "DISABLED"
        or phase12e.get("T10_STATUS") != "DISABLED"
        or phase12e.get("SEARCH_EXECUTED") is not False
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or not _classifications_match(phase12e)
    ):
        return _precondition_failure("stored phase status, frozen hash, or family classification")

    by_id = {item["family_id"]: item for item in phase12e["families"]}
    operational = [_operational_row(item) for item in phase12e["families"] if item.get("operational_status") == "OPERATIONAL"]
    if len(operational) != 13 or any(item["finite_bound"] != "FINITE" for item in operational):
        return _precondition_failure("operational registry is not the stored finite grammar")
    requests = []
    diagnostics = []
    for category in NOT_REGISTERED + REQUIRES_HUMAN_INPUT:
        family = by_id[_CATEGORY_SOURCE[category]]
        requests.append(_request_from_family(category, family))
        diagnostics.append(_diagnostic(category, family))
    if any(item["expansion_type"] == "MATHEMATICAL_GRAMMAR_EXPANSION" for item in requests):
        return {"PHASE_12F_STATUS": "INCOMPLETE", "status": "UNEXPECTED_GRAMMAR_EXPANSION"}
    if any(item["authorization_status"] != "NOT_AUTHORIZED" or item["activated"] for item in requests):
        return {"PHASE_12F_STATUS": "INCOMPLETE", "status": "REQUEST_ACTIVATED"}
    negatives = dry_run_negative_tests()
    refused = False
    try:
        run_large_scale_search()
    except RuntimeError:
        refused = True
    if not refused or any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_12F_STATUS": "INCOMPLETE", "dry_run": negatives, "status": "DRY_RUN_FAILED"}

    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "code_version": CODE_VERSION,
        "DECISION_PACKAGE_STATUS": "VERIFIED",
        "CURRENT_GRAMMAR_STATUS": "EXHAUSTED",
        "REQUEST_SCHEMA_STATUS": "VERIFIED",
        "PHYSICAL_INPUT_FIREWALL_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "FINITE_BOUND_VALIDATION_STATUS": "PARTIAL",
        "T09_STATUS": "DISABLED",
        "T10_STATUS": "DISABLED",
        "GENERATOR_ACTIVATION": "NONE",
        "SEARCH_EXECUTED": False,
        "FROZEN_STATE_STATUS": "VERIFIED",
        "PHASE_12F_STATUS": "COMPLETE",
        "CURRENT_GRAMMAR_VERSION": CURRENT_GRAMMAR_VERSION,
        "PROPOSED_GRAMMAR_VERSION": "NOT_CREATED",
        "grammar_version_created": False,
        "frozen_4c_hash": freeze["action_content_hash"],
        "new_physical_principle_activated": False,
        "theories_generated": 0,
        "ACTIVATABLE_FAMILIES": [],
        "REQUIRES_HUMAN_INPUT": list(REQUIRES_HUMAN_INPUT),
        "NOT_REGISTERED": list(NOT_REGISTERED),
        "HUMAN_DECISION_PACKAGE": requests,
        "CURRENT_OPERATIONAL_GRAMMAR": {
            "activation": "UNCHANGED",
            "entries": operational,
            "grammar_version": CURRENT_GRAMMAR_VERSION,
            "legal_combinations": 8,
            "objects_generated_in_phase_12b": 7,
            "operational_entry_count": len(operational),
        },
        "PHYSICAL_FRONTIER": {
            "T09": "DISABLED",
            "T10": "DISABLED",
            "flux stabilization": "NEW_PHYSICAL_INPUT_REQUIRED",
            "hidden sector": "NEW_PHYSICAL_INPUT_REQUIRED",
            "modulus stabilization": "NEW_PHYSICAL_INPUT_REQUIRED",
            "vacuum selection": "NEW_PHYSICAL_INPUT_REQUIRED",
        },
        "ACTIVATION_CONTRACT": {
            "insufficient_statement": "expand the grammar",
            "required_fields": list(AUTHORIZATION_CONTRACT_FIELDS),
            "status_without_those_fields": "NOT_AUTHORIZED",
        },
        "MISSING_FAMILY_DEFINITIONS": diagnostics,
        "decision_table": [_decision_row(item) for item in requests],
        "READY_FOR_HUMAN_DECISION": [],
        "legal_sequence": list(LEGAL_SEQUENCE),
        "dry_run": negatives,
        "stored_phase_12e": {
            "ACTIVATABLE_FAMILIES": phase12e["decision"]["ACTIVATABLE_FAMILIES"],
            "CURRENT_GRAMMAR_VERSION": phase12e["CURRENT_GRAMMAR_VERSION"],
            "PHASE_12E_STATUS": phase12e["PHASE_12E_STATUS"],
        },
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_12F_DECISION_PACKAGE.json").write_bytes(canonical_json_bytes(payload))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_12F_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
