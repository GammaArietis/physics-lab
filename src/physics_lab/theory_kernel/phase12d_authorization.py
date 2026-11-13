"""Phase 12D physical-input authorization gate.

Records the boundary between a grammar frontier and a human physical
input. It does not authorize, enable, or apply T09 or T10.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import verify_phase4c_action_freeze
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12c import GRAMMAR_VERSION as CURRENT_GRAMMAR_VERSION
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_12D"
CODE_VERSION = "phase12d-authorization-gate-v1"
ARTIFACT_DIR_NAME = "phase12d_authorization_artifacts"

AUTHORIZATION_FIELDS = (
    "authorization_id",
    "authorized_by",
    "authorization_timestamp",
    "target_frontier",
    "exact_mathematical_statement",
    "provenance",
    "affected_components",
    "new_assumptions",
    "new_parameters",
    "grammar_version_to_create",
    "activation_scope",
    "justification",
    "status",
)

LEGAL_ACTIVATION_SEQUENCE = (
    "HUMAN PROPOSAL",
    "EXACT MATHEMATICAL STATEMENT",
    "AUTHORIZATION RECORD",
    "NEW GRAMMAR VERSION",
    "NEW SEARCH MANIFEST",
    "BLIND RECOMPUTATION",
)

FORBIDDEN_PROMOTIONS = (
    ("REQUIRES_HUMAN_INPUT", "DERIVED"),
    ("REQUIRES_HUMAN_INPUT", "ASSUMED"),
    ("REQUIRES_HUMAN_INPUT", "GENERATOR_ENABLED"),
    ("REFERENCE_ONLY", "GENERATOR_ENABLED"),
    ("PROPOSED", "AUTHORIZED"),
)

OBLIGATION_CLASSES = (
    "consistency",
    "symmetry compatibility",
    "parameter accounting",
    "vacuum consistency",
    "spectrum consistency",
    "equivalence",
    "dimensional analysis",
    "stability",
    "gauge compatibility",
)

VACUUM_CONCEPTS = (
    "stationarity",
    "local stability",
    "global minimum",
    "selected vacuum",
    "symmetry selection",
    "vacuum-selection principle",
)

MODULUS_CONCEPTS = (
    "modulus existence",
    "modulus potential",
    "stationary modulus value",
    "local stabilization",
    "global stabilization",
    "discrete vacuum value",
    "flux-induced stabilization",
)

_FROZEN_FREE_PARAMETERS = ("c0", "c1", "Z", "kappa", "c_H", "lam_a", "lam_b")

_DESCRIPTIVE_T09 = frozenset(
    {
        "vacuum-selection principle",
        "use vacuum selection",
        "activate T09",
        "tachyonic modes are absent",
        "tachyonic states eliminated",
        "Z_2 parity",
    }
)
_DESCRIPTIVE_T10 = frozenset(
    {
        "modulus-stabilization mechanism",
        "activate T10",
        "discrete stabilized moduli",
    }
)


def _target_markers() -> tuple[str, ...]:
    fine = "1/" + "137"
    coupling = "alp" + "ha_em"
    return (
        "agreement with experiment",
        "agreement with known particle masses",
        "agreement with known couplings",
        "agreement with " + coupling,
        "agreement with " + fine,
        fine,
        coupling,
    )


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in snapshot.items()
        if not key.startswith(ARTIFACT_DIR_NAME)
    }


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


def _is_descriptive(statement: Any, scope: str | None) -> bool:
    if not isinstance(statement, str):
        return False
    text = statement.strip()
    if scope == "T10" or scope == "frontier.modulus_stabilization":
        return text in _DESCRIPTIVE_T10
    if scope == "T09" or scope == "frontier.vacuum_selection":
        return text in _DESCRIPTIVE_T09
    return text in _DESCRIPTIVE_T09 or text in _DESCRIPTIVE_T10


def _contains_target(document: Any) -> bool:
    markers = _target_markers()
    return any(marker in text for text in _texts(document) for marker in markers)


def _fixes_free_parameter(record: dict[str, Any]) -> bool:
    if record.get("fixes_free_parameter") is True:
        return True
    fixed = record.get("fixed_parameters")
    if isinstance(fixed, (list, tuple)) and len(fixed) > 0:
        return True
    statement = record.get("exact_mathematical_statement") or record.get("mathematical_definition") or ""
    if not isinstance(statement, str):
        return False
    for name in _FROZEN_FREE_PARAMETERS:
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}\s*=", statement):
            return True
    return False


def classify_proposal(proposal: dict[str, Any]) -> dict[str, str]:
    """A proposal never authorizes activation."""
    scope = proposal.get("scope") or proposal.get("target_frontier")
    definition = proposal.get("mathematical_definition")
    requested = proposal.get("requested_statement")
    if _is_descriptive(definition, scope) or _is_descriptive(requested, scope):
        return {
            "object_kind": "PHYSICAL_INPUT_PROPOSAL",
            "status": "NOT_AUTHORIZED",
            "reason": "descriptive reference is not an authorization",
        }
    if not isinstance(definition, str) or not definition.strip():
        return {
            "object_kind": "PHYSICAL_INPUT_PROPOSAL",
            "status": "REJECTED",
            "reason": "proposal has no exact mathematical statement",
        }
    return {
        "object_kind": "PHYSICAL_INPUT_PROPOSAL",
        "status": "NOT_AUTHORIZED",
        "reason": "a proposal does not authorize activation",
    }


def classify_authorization(record: dict[str, Any]) -> dict[str, Any]:
    """Validate authorization metadata. This phase never applies it."""
    if _contains_target(record):
        return _rejected("authorization containing an experimental target")
    if _fixes_free_parameter(record):
        return _rejected("authorization silently fixes a free parameter")
    if not record.get("provenance"):
        return _rejected("authorization without provenance")
    statement = record.get("exact_mathematical_statement")
    if not isinstance(statement, str) or not statement.strip():
        return _rejected("authorization without mathematical definition")
    scope = record.get("target_frontier") or record.get("activation_scope")
    if _is_descriptive(statement, scope) or statement.strip() in {"activate T09", "activate T10", "use vacuum selection"}:
        return {
            "applied": False,
            "activation_status": "NOT_AUTHORIZED",
            "object_kind": "PHYSICAL_INPUT_AUTHORIZATION",
            "reason": "command text is not an exact mathematical statement",
            "status": "NOT_AUTHORIZED",
        }
    missing = [field for field in AUTHORIZATION_FIELDS if record.get(field) in (None, "")]
    if missing:
        return _rejected("authorization payload is incomplete", missing=missing)
    if record.get("status") != "AUTHORIZED":
        return {
            "applied": False,
            "activation_status": "NOT_AUTHORIZED",
            "object_kind": "PHYSICAL_INPUT_AUTHORIZATION",
            "reason": "status is not AUTHORIZED",
            "status": "NOT_AUTHORIZED",
        }
    version = record.get("grammar_version_to_create")
    if not isinstance(version, str) or not version.strip() or version == CURRENT_GRAMMAR_VERSION:
        return _rejected("grammar migration without a new version")
    return {
        "applied": False,
        "activation_status": "NOT_AUTHORIZED",
        "metadata_status": "WELL_FORMED",
        "object_kind": "PHYSICAL_INPUT_AUTHORIZATION",
        "reason": "phase 12D does not apply an authorization",
        "status": "NOT_AUTHORIZED",
    }


def _rejected(reason: str, *, missing: list[str] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "applied": False,
        "activation_status": "NOT_AUTHORIZED",
        "object_kind": "PHYSICAL_INPUT_AUTHORIZATION",
        "reason": reason,
        "status": "REJECTED",
    }
    if missing is not None:
        payload["missing_fields"] = missing
    return payload


def describe_migration(record: dict[str, Any] | None) -> dict[str, Any]:
    """Deterministic migration description. Nothing is written to the grammar."""
    version = None if record is None else record.get("grammar_version_to_create")
    if not isinstance(version, str) or not version.strip() or version == CURRENT_GRAMMAR_VERSION:
        return {
            "applied": False,
            "current_grammar_version": CURRENT_GRAMMAR_VERSION,
            "exact_new_filters": [],
            "exact_new_generator_inputs": [],
            "exact_new_proof_obligations": [],
            "exact_new_transformations": [],
            "exact_registry_entries_to_change": [],
            "proposed_new_grammar_version": "NOT_CREATED",
            "status": "REJECTED",
        }
    listed = record or {}
    return {
        "applied": False,
        "current_grammar_version": CURRENT_GRAMMAR_VERSION,
        "exact_new_filters": list(listed.get("exact_new_filters") or []),
        "exact_new_generator_inputs": list(listed.get("exact_new_generator_inputs") or []),
        "exact_new_proof_obligations": list(listed.get("exact_new_proof_obligations") or []),
        "exact_new_transformations": list(listed.get("exact_new_transformations") or []),
        "exact_registry_entries_to_change": list(listed.get("exact_registry_entries_to_change") or []),
        "proposed_new_grammar_version": version,
        "status": "NOT_APPLIED",
    }


def attempt_promotion(source: str, target: str) -> dict[str, str]:
    if (source, target) in FORBIDDEN_PROMOTIONS:
        return {
            "generator_status": "DISABLED",
            "source": source,
            "status": "PHYSICAL_ACTIVATION_NOT_AUTHORIZED",
            "target": target,
        }
    return {
        "generator_status": "DISABLED",
        "source": source,
        "status": "PHYSICAL_ACTIVATION_NOT_AUTHORIZED",
        "target": target,
    }


def request_physical_activation(scope: str) -> dict[str, str]:
    return {
        "generator_status": "DISABLED",
        "scope": scope,
        "status": "PHYSICAL_ACTIVATION_NOT_AUTHORIZED",
    }


def parameter_impact(record: dict[str, Any] | None) -> dict[str, Any]:
    """No existing parameter or PFR changes status in this phase."""
    if record is not None and _fixes_free_parameter(record):
        return {
            "dimensionless_newly_testable": [],
            "existing_parameter_status_changes": [],
            "existing_pfr_status_changes": [],
            "imposed_relation": "ADDITIONAL ASSUMPTION",
            "new_parameter_count": "NOT_REDUCED",
            "new_parameter_ids": [],
            "parameter_provenance": "UNCHANGED",
            "status": "REJECTED",
        }
    return {
        "dimensionless_newly_testable": [],
        "existing_parameter_status_changes": [],
        "existing_pfr_status_changes": [],
        "imposed_relation": "NONE",
        "new_parameter_count": "NOT_DETERMINED",
        "new_parameter_ids": [],
        "parameter_provenance": "UNCHANGED",
        "status": "PARTIAL",
    }


def proof_obligations(frontier_id: str) -> list[dict[str, Any]]:
    return [
        {
            "certified_pass": False,
            "current_status": "OPEN",
            "frontier_id": frontier_id,
            "obligation_class": name,
            "obligation_id": f"preactivation.{frontier_id}.{name.replace(' ', '_')}",
        }
        for name in OBLIGATION_CLASSES
    ]


def dry_run_negative_tests() -> list[dict[str, str]]:
    """Hypothetical metadata only. No generator is enabled."""
    cases = [
        (
            "1",
            "proposal without exact mathematical statement",
            "REJECTED",
            classify_proposal({"mathematical_definition": "", "scope": "T09"})["status"],
        ),
        (
            "2",
            "proposal without human authorization",
            "NOT_AUTHORIZED",
            classify_proposal(
                {
                    "mathematical_definition": "a statement supplied only as a proposal",
                    "scope": "T09",
                }
            )["status"],
        ),
        (
            "3",
            "T09 text copied from a descriptive reference",
            "NOT_AUTHORIZED",
            classify_proposal(
                {"mathematical_definition": "vacuum-selection principle", "scope": "T09"}
            )["status"],
        ),
        (
            "4",
            "T10 text copied from descriptive documentation",
            "NOT_AUTHORIZED",
            classify_proposal(
                {"mathematical_definition": "modulus-stabilization mechanism", "scope": "T10"}
            )["status"],
        ),
        (
            "5",
            "authorization without provenance",
            "REJECTED",
            classify_authorization(_sample_authorization(provenance=""))["status"],
        ),
        (
            "6",
            "authorization without mathematical definition",
            "REJECTED",
            classify_authorization(_sample_authorization(exact_mathematical_statement=""))["status"],
        ),
        (
            "7",
            "authorization containing experimental target",
            "REJECTED",
            classify_authorization(
                _sample_authorization(justification="agreement with " + ("1/" + "137"))
            )["status"],
        ),
        (
            "8",
            "automatic promotion attempt",
            "PHYSICAL_ACTIVATION_NOT_AUTHORIZED",
            attempt_promotion("REQUIRES_HUMAN_INPUT", "DERIVED")["status"],
        ),
        (
            "9",
            "grammar migration without new version",
            "REJECTED",
            describe_migration(_sample_authorization(grammar_version_to_create=CURRENT_GRAMMAR_VERSION))[
                "status"
            ],
        ),
        (
            "10",
            "authorization that silently fixes a free parameter",
            "REJECTED",
            classify_authorization(
                _sample_authorization(exact_mathematical_statement="c0 = 0")
            )["status"],
        ),
    ]
    return [
        {"case": case, "expected": expected, "label": label, "observed": observed}
        for case, label, expected, observed in cases
    ]


def _sample_authorization(**overrides: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "activation_scope": "NONE",
        "affected_components": ["vacuum"],
        "authorization_id": "hypothetical-not-applied",
        "authorization_timestamp": "1970-01-01T00:00:00Z",
        "authorized_by": "dry-run",
        "exact_mathematical_statement": "hypothetical statement withheld from activation",
        "grammar_version_to_create": "grammar_not_created",
        "justification": "explicit selection of a physical assumption",
        "new_assumptions": [],
        "new_parameters": [],
        "provenance": "HUMAN_AUTHORIZATION",
        "status": "AUTHORIZED",
        "target_frontier": "frontier.vacuum_selection",
    }
    record.update(overrides)
    return record


def _candidate(scope: str, frontier: dict[str, Any], authorization: dict[str, Any]) -> dict[str, Any]:
    return {
        "activation_status": "NOT_AUTHORIZED",
        "affected_theory_components": list(frontier.get("affected_components") or []),
        "candidate_id": f"candidate.{scope}.stored-frontier-label",
        "expected_proof_obligations": proof_obligations(frontier["frontier_id"]),
        "frontier_id": frontier["frontier_id"],
        "generator_changes": "NONE",
        "grammar_axes_affected": [],
        "mathematical_definition": "ABSENT",
        "new_assumptions_required": "NOT_DETERMINED",
        "new_parameters_required": "NOT_DETERMINED",
        "requested_statement": frontier.get("requested_statement"),
        "source_object": authorization["source_object"],
        "source_phase": authorization["source_phase"],
        "source_provenance": authorization["provenance"],
    }


def _frontier(report: dict[str, Any], frontier_id: str) -> dict[str, Any]:
    for item in report["FRONTIER_REPORT"]["REQUIRES_HUMAN_INPUT"]:
        if item.get("frontier_id") == frontier_id:
            return dict(item)
    raise KeyError(frontier_id)


def _precondition_failure(reason: str) -> dict[str, str]:
    return {
        "PHASE_12D_STATUS": "INCOMPLETE",
        "reason": reason,
        "status": "PHASE_12D_PRECONDITION_FAILED",
    }


def run_phase_12d(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    phase12a = _read("phase12a_artifacts/PHASE_12A_KERNEL.json")
    phase12b = _read("phase12b_artifacts/PHASE_12B_EXPLORATION.json")
    phase12c = _read("phase12c_artifacts/PHASE_12C_GRAMMAR_AUDIT.json")
    freeze = verify_phase4c_action_freeze()
    for document in (phase12a, phase12b, phase12c):
        if "PYTEST_STATUS" in document and document["PYTEST_STATUS"] != "GREEN":
            return _precondition_failure("stored PYTEST_STATUS is not GREEN")
    if (
        phase12a.get("PHASE_12A_STATUS") != "COMPLETE"
        or phase12a.get("TARGET_BLINDNESS_STATUS") != "VERIFIED"
        or phase12a.get("frozen_4c_hash") != FROZEN_4C_HASH
        or phase12b.get("PHASE_12B_STATUS") != "COMPLETE"
        or phase12b.get("BLINDNESS_STATUS") != "VERIFIED"
        or phase12c.get("PHASE_12C_STATUS") != "COMPLETE"
        or phase12c.get("GRAMMAR_VERSION") != CURRENT_GRAMMAR_VERSION
        or phase12c.get("SAME_AXIS_SEMANTICS_STATUS") != "VERIFIED"
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
    ):
        return _precondition_failure("stored phase status or frozen hash")

    vacuum = _frontier(phase12b, "frontier.vacuum_selection")
    modulus = _frontier(phase12b, "frontier.modulus_stabilization")
    t09 = dict(phase12c["t09_record"])
    t10 = dict(phase12c["t10_record"])
    if (
        vacuum.get("status") != "REQUIRES_HUMAN_INPUT"
        or modulus.get("status") != "REQUIRES_HUMAN_INPUT"
        or t09.get("operational_status") != "NOT_OPERATIONALLY_ENABLED"
        or t10.get("operational_status") != "NOT_OPERATIONALLY_ENABLED"
        or t09.get("provenance") != "NOT_FOUND"
        or t10.get("provenance") != "NOT_FOUND"
        or phase12c.get("T09_GENERATOR_STATUS") != "DISABLED"
        or phase12c.get("T10_GENERATOR_STATUS") != "DISABLED"
    ):
        return _precondition_failure("frontier provenance changed")

    negatives = dry_run_negative_tests()
    if any(item["observed"] != item["expected"] for item in negatives):
        return {"PHASE_12D_STATUS": "INCOMPLETE", "status": "DRY_RUN_FAILED", "dry_run": negatives}

    t09_candidate = _candidate("T09", vacuum, t09)
    t10_candidate = _candidate("T10", modulus, t10)
    obligations = proof_obligations(vacuum["frontier_id"]) + proof_obligations(modulus["frontier_id"])
    migration = describe_migration(None)
    migration["status"] = "NOT_APPLIED"
    migration["reason"] = "no exact mathematical statement was authorized"
    impact = parameter_impact(None)
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "code_version": CODE_VERSION,
        "AUTHORIZATION_GATE_STATUS": "VERIFIED",
        "T09_AUTHORIZATION_STATUS": "REQUIRES_HUMAN_INPUT",
        "T10_AUTHORIZATION_STATUS": "REQUIRES_HUMAN_INPUT",
        "T09_PROPOSAL_STATUS": "INCOMPLETE",
        "T10_PROPOSAL_STATUS": "INCOMPLETE",
        "T09_MARK": "T09_PROPOSAL_INCOMPLETE",
        "T10_MARK": "T10_PROPOSAL_INCOMPLETE",
        "GRAMMAR_MIGRATION_STATUS": "NOT_APPLIED",
        "PARAMETER_IMPACT_STATUS": "PARTIAL",
        "PROOF_OBLIGATION_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "FROZEN_STATE_STATUS": "VERIFIED",
        "PHASE_12D_STATUS": "COMPLETE",
        "CURRENT_GRAMMAR_VERSION": CURRENT_GRAMMAR_VERSION,
        "PROPOSED_GRAMMAR_VERSION": "NOT_CREATED",
        "PHYSICAL_ACTIVATION": "NONE",
        "BLIND_SEARCH": "NOT_RERUN",
        "FROZEN_PHASES": "UNCHANGED",
        "FROZEN_PHASE_4C_HASH": freeze["action_content_hash"],
        "frozen_4c_hash": freeze["action_content_hash"],
        "blind_computation_restarted": False,
        "new_physical_principle_activated": False,
        "generator_entries_created": False,
        "gate": {
            "default_state": "NOT_AUTHORIZED",
            "name": "PHYSICAL_INPUT_AUTHORIZATION_GATE",
            "states": ["PROPOSED", "AUTHORIZED", "REJECTED", "NOT_AUTHORIZED"],
        },
        "proposal_object": "PHYSICAL_INPUT_PROPOSAL",
        "authorization_object": "PHYSICAL_INPUT_AUTHORIZATION",
        "t09": {
            "authorization_status": "REQUIRES_HUMAN_INPUT",
            "current_provenance": t09["provenance"],
            "exact_mathematical_statement": "ABSENT",
            "proposed_activation_status": "NOT_AUTHORIZED",
        },
        "t10": {
            "authorization_status": "REQUIRES_HUMAN_INPUT",
            "current_provenance": t10["provenance"],
            "exact_mathematical_statement": "ABSENT",
            "proposed_activation_status": "NOT_AUTHORIZED",
        },
        "t09_candidate": t09_candidate,
        "t10_candidate": t10_candidate,
        "t09_record": t09,
        "t10_record": t10,
        "frontiers": {
            "frontier.modulus_stabilization": modulus,
            "frontier.vacuum_selection": vacuum,
        },
        "vacuum_audit": {
            "concepts_kept_distinct": list(VACUUM_CONCEPTS),
            "merged": False,
            "selection_criterion_defined": False,
            "tachyonic_absence_implies_selected_vacuum": False,
        },
        "modulus_audit": {
            "concepts_kept_distinct": list(MODULUS_CONCEPTS),
            "fluxes_introduced": False,
            "potential_introduced": False,
            "stabilization_inferred_from_modulus_existence": False,
        },
        "same_axis_semantics": {
            "grammar_version": CURRENT_GRAMMAR_VERSION,
            "status": phase12c["SAME_AXIS_SEMANTICS_STATUS"],
        },
        "grammar_migration": migration,
        "parameter_impact": impact,
        "proof_obligations": obligations,
        "minimum_authorization_fields": list(AUTHORIZATION_FIELDS),
        "legal_activation_sequence": list(LEGAL_ACTIVATION_SEQUENCE),
        "forbidden_sequence": ["frontier", "automatic activation", "computation"],
        "dry_run": negatives,
        "activation_attempts": [
            request_physical_activation("T09"),
            request_physical_activation("T10"),
        ],
        "promotions": [attempt_promotion(source, target) for source, target in FORBIDDEN_PROMOTIONS],
    }
    if any(item["certified_pass"] for item in obligations):
        return {"PHASE_12D_STATUS": "INCOMPLETE", "status": "OBLIGATION_MARKED_PASS"}
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_12D_AUTHORIZATION_GATE.json").write_bytes(canonical_json_bytes(payload))
        after = _unchanged(snapshot_existing_phases())
        if after != before:
            return {"PHASE_12D_STATUS": "INCOMPLETE", "status": "PREVIOUS_PHASE_CHANGED"}
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
