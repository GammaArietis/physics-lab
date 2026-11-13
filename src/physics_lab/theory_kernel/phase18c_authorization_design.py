"""Phase 18C designs a future authorization and does not grant it."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.theory_kernel.epistemic import content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_18C"
CODE_VERSION = "phase18c-authorization-design-v1"
SCHEMA_VERSION = "dynamical_batch_authorization_schema_18c_v1"
ARTIFACT_DIR_NAME = "phase18c_authorization_artifacts"
DESIGN_NAME = "PHASE_18C_DYNAMICAL_BATCH_AUTHORIZATION_DESIGN.json"
DESIGN_TIMESTAMP = "2026-10-26T12:19:00Z"
PROPOSAL_SHA256 = "f6264e49dc0d7c20562833b26891b67ff556477669f308fb646c919632235d84"
PROPOSAL_HASH = "e3031ab3f89acadc60e09cb9045590d78cde4a6f71e0de2cb3bbee5c3e399e89"
AUDIT_HASH = "e5d2310b3d5b57c1aafe86a3e5f14611ea2a8affa4dbc6a83f7674ccf71a8076"
UNRESOLVED = (
    "g17b1.teleparallel",
    "g17b1.symmetric_teleparallel",
    "g17b1.cartan_frame",
    "g17b1.vielbein",
    "g17b1.principal_bundle",
    "g17b1.causal_graph",
    "g17b1.twistor",
)
PLACEHOLDER = "BOUND_TO_BE_AUTHORIZED"
AXIS_SYMBOL = "N_MAX"


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stop(reason: str) -> dict[str, Any]:
    return {
        "HUMAN_AUTHORIZATION_STATUS": "NOT_YET_GRANTED",
        "NO_ACTION_SELECTED": True,
        "NO_NEW_PHYSICAL_INPUT_ACTIVATED": True,
        "NO_VACUUM_SELECTED": True,
        "PHASE18C_STATUS": "INCOMPLETE",
        "SEARCH_ACTIVE": False,
        "SEARCH_STATUS": "NOT_STARTED",
        "reason": reason,
        "status": "DESIGN_FAILED",
    }


def execute_search(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def grant_authorization(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_YET_GRANTED"


def select_formulation(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def _axis(name: str, kind: str) -> dict[str, str]:
    return {
        "acceptable_provenance": "MATHEMATICAL_BOUND only when a registered identity forces the domain; otherwise a human declaration recorded as BOUND_AUTHORIZED",
        "bound_symbol": AXIS_SYMBOL,
        "can_be_mathematically_derived": "ONLY_IF_A_REGISTERED_IDENTITY_FORCES_THE_DOMAIN",
        "expansion_control": "the authorized record is immutable for the batch; a wider domain is a new authorization",
        "kind": kind,
        "name": name,
        "numerical_value": PLACEHOLDER,
        "recording": "axis name, symbol, provenance class, and authorization id in the future authorization object",
        "requires_human_authorization": "YES_UNLESS_THE_DOMAIN_IS_FORCED_BY_A_REGISTERED_IDENTITY",
        "unacceptable_provenance": "convenience, literature habit, framework familiarity, measured values, or a desired output",
        "valid_finite_bound": "an explicit finite domain, recorded before search, with provenance class separate from the search result",
    }


def run_phase_18c(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    physics = _physics_dir()
    audit_path = physics / "phase18a_dynamical_formulation_artifacts" / "PHASE_18A_DYNAMICAL_AUDIT.json"
    proposal_path = physics / "phase18b_batch_proposal_artifacts" / "PHASE_18B_DYNAMICAL_BATCH_PROPOSAL.json"
    audit_bytes = audit_path.read_bytes()
    proposal_bytes = proposal_path.read_bytes()
    proposal = json.loads(proposal_bytes)
    audit = json.loads(audit_bytes)
    if (
        _sha(proposal_path) != PROPOSAL_SHA256
        or proposal.get("proposal_hash") != PROPOSAL_HASH
        or audit.get("audit_hash") != AUDIT_HASH
        or audit.get("formulation_count") != 47
        or len(proposal.get("candidate_classification", [])) != 47
        or proposal.get("SEARCH_STATUS") != "NOT_STARTED"
        or execute_search() != "NOT_PERFORMED"
        or grant_authorization() != "NOT_YET_GRANTED"
        or select_formulation() != "NOT_PERFORMED"
    ):
        return _stop("sealed input")
    inspected = {
        "phase15f_grammar": _sha(physics / "phase15f_grammar_artifacts" / "PHASE_15F_GRAMMAR.json"),
        "phase16e_frontier": _sha(physics / "phase16e_frontier_artifacts" / "PHASE_16E_FRONTIER.json"),
        "phase17_tier1_catalog": _sha(physics / "phase17_tier1_search_artifacts" / "PHASE_17_TIER1_CATALOG.json"),
        "phase17_tier1_manifest": _sha(physics / "phase17_tier1_search_artifacts" / "PHASE_17_TIER1_SEARCH_MANIFEST.json"),
        "phase17b1_grammar": _sha(physics / "phase17b1_fundamental_structure_artifacts" / "PHASE_17B1_FUNDAMENTAL_STRUCTURE.json"),
        "phase17c_bounds": _sha(physics / "phase17c_bound_architecture_artifacts" / "PHASE_17C_BOUND_ARCHITECTURE.json"),
        "phase17d_authorization": _sha(physics / "phase17d_batch_authorization_artifacts" / "PHASE_17_BATCH_AUTHORIZATION.json"),
        "phase17e_frontier": _sha(physics / "phase17e_frontier_artifacts" / "PHASE_17E_FRONTIER.json"),
        "phase18a_audit": _sha(audit_path),
        "phase18b_proposal": _sha(proposal_path),
        "phase4c_freeze": _sha(physics / "phase4c_action_freeze.json"),
    }
    matrix = []
    for item in proposal["candidate_classification"]:
        matrix.append(
            {
                "additional_mathematical_definition_required": True,
                "current_bound_state": "BOUND_MISSING",
                "current_formalization_state": item["formalization_status"],
                "eligible_without_new_physical_input": "NOT_DECIDED",
                "executable": False,
                "formulation_class": item["formulation_type"],
                "formulation_id": item["formulation_id"],
                "future_eligibility_condition": "a class-specific definition record plus a human-authorized finite window, still not a search",
                "parent": item["parent_grammar"],
                "physical_input_state": "STRUCTURAL_FLAG_RECORDED_NOT_AN_EMPIRICAL_CONSTANT_COUNT",
            }
        )
    if len(matrix) != 47 or any(row["executable"] for row in matrix):
        return _stop("matrix")
    schema = {
        "activation_status": "NOT_ACTIVATED",
        "authorization_id": "PHASE_18C_DYNAMICAL_BATCH_AUTHORIZATION_DESIGN",
        "authorization_version": SCHEMA_VERSION,
        "bound_provenance": "BOUND_MISSING until a future record uses BOUND_AUTHORIZED or a forced MATHEMATICAL_BOUND",
        "computational_finiteness_rule": "FINITE_BATCH requires every included axis to have an explicit finite authorized domain",
        "equivalence_policy": "kinematic, dynamical, and physical equivalence stay separate; unresolved records are not deduplication licenses",
        "excluded_formulation_ids": [row["formulation_id"] for row in matrix],
        "exclusion_rule": "PARTIAL formalization, BOUND_MISSING, or an unresolved definition excludes the formulation",
        "failure_status_semantics": {
            "INCOMPLETE": "a required record is absent",
            "INCONCLUSIVE": "the registered search did not decide the question",
            "INVALID": "the record violates its own schema",
            "NOT_FOUND": "nothing with that status was found inside the authorized window",
            "NOT_SPECIFIABLE": "the formulation type has no registered dynamical object yet",
            "NOT_YET_BOUNDED": "no finite window is declared; this is not an impossibility proof",
            "OUT_OF_BOUND": "a generated point would leave the authorized window and must not be kept by widening it",
            "REQUIRES_NEW_PHYSICAL_INPUT": "a structural flag or a missing postulate; not a count of empirical constants",
            "UNTESTED": "the laboratory has not run the corresponding test",
        },
        "finite_numerical_windows": PLACEHOLDER,
        "finite_parameter_axes": "named per formulation class; values remain " + PLACEHOLDER,
        "formulation_definition_status": "PARTIAL",
        "human_authorization_field": "NOT_YET_GRANTED",
        "included_formulation_ids": [],
        "inclusion_rule": "eligible only after the definition gate and an authorized finite window; no non-empty subset is justified now",
        "parameter_classification": "identifier, mathematical role, physical role, provenance, observable, conventional, auxiliary, gauge-related, free, bound status, domain, authorization status",
        "parent_phase": "PHASE_18B",
        "physical_input_policy": "structural flag, mathematical input, physical postulate, empirical input, measured value, derived quantity, free parameter, and conventional parameter stay distinct",
        "provenance_policy": "DERIVED, ASSUMED, INPUT, PARAMETER-DEPENDENT, CONVENTION, UNTESTED; EXPERIMENTAL and CALIBRATED stay prohibited",
        "reproducibility_requirements": "canonical serialization, seed NOT_USED, timestamp of a future execution NOT_ISSUED until that execution exists",
        "source_audit_hash": AUDIT_HASH,
        "source_catalogue_hash": audit["CATALOG_HASH"],
        "source_proposal_hash": PROPOSAL_HASH,
        "state": "PROPOSED",
        "stopping_conditions": [
            "bound exhaustion",
            "candidate exhaustion inside the authorized set",
            "unresolved definition",
            "unauthorized input",
            "equivalence ambiguity",
            "schema violation",
            "hidden assumption",
            "vacuum-firewall violation",
            "provenance failure",
        ],
        "vacuum_firewall": "VACUUM_SELECTION remains NOT_INSERTED; a potential is not a selection principle",
    }
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "PHASE18C_STATUS": "COMPLETE",
        "SEARCH_STATUS": "NOT_STARTED",
        "SEARCH_ACTIVE": False,
        "HUMAN_AUTHORIZATION_STATUS": "NOT_YET_GRANTED",
        "NO_ACTION_SELECTED": True,
        "NO_VACUUM_SELECTED": True,
        "NO_NEW_PHYSICAL_INPUT_ACTIVATED": True,
        "VACUUM_SELECTION": "NOT_INSERTED",
        "design_timestamp": DESIGN_TIMESTAMP,
        "state": "PROPOSED",
        "activation_status": "NOT_ACTIVATED",
        "execution_status": "NOT_EXECUTED",
        "admissible_batch": "EMPTY_ADMISSIBLE_BATCH",
        "subset_selection": "SUBSET_SELECTION_NOT_JUSTIFIED",
        "frozen_action_hash": FROZEN_4C_HASH,
        "inspected_paths": {key: "READ_ONLY_UNMODIFIED" for key in inspected},
        "source_artifact_hashes": inspected,
        "smallest_decision_set": [
            {"decision": "supply the class-specific definition record", "layer": "MATHEMATICAL_FORMALIZATION"},
            {"decision": "declare each finite window and its provenance class", "layer": "SEARCH_AUTHORIZATION"},
            {"decision": "list included and excluded formulation ids by the eligibility rule alone", "layer": "SEARCH_AUTHORIZATION"},
            {"decision": "leave physical reading, vacuum selection, and empirical comparison unopened", "layer": "SEPARATE_DOWNSTREAM_LAYERS"},
        ],
        "layer_independence": ["MATHEMATICAL_FORMALIZATION", "SEARCH_AUTHORIZATION", "PHYSICAL_INTERPRETATION", "VACUUM_SELECTION", "EMPIRICAL_COMPARISON"],
        "authorization_schema": schema,
        "definition_gate": {
            "common_required_records": [
                "mathematical domain",
                "degrees of freedom",
                "configuration or state space",
                "dynamical object type",
                "constraints",
                "admissibility conditions",
                "gauge or conventional redundancies",
                "boundary data",
                "evolution variable",
                "parameter list and roles",
                "provenance",
                "equivalence metadata",
            ],
            "object_type_by_class": {
                "CONSTRAINED_ACTION": "constraint functional, not presumed to be the whole dynamics",
                "DISCRETE_DYNAMICAL_RULE": "update rule on the registered discrete structure",
                "HAMILTONIAN_OR_CANONICAL_FORMULATION": "Hamiltonian or canonical generator",
                "LOCAL_ACTION_FUNCTIONAL": "local scalar density, only for this class",
                "NOT_YET_SPECIFIABLE": "the object type itself is still unregistered",
                "OTHER_FORMAL_DYNAMICS": "a named formal generator that is not forced into another class",
                "RENORMALIZATION_FLOW": "flow operator on a space of actions, with no chosen fixed point",
                "STATE_SUM_OR_TRANSITION_AMPLITUDE": "weight or amplitude, not a continuum density",
            },
            "status": "REQUIRED_NOT_SUPPLIED",
        },
        "bound_policy": {
            "copied_from_phase17c": False,
            "numerical_values_introduced": False,
            "placeholder": PLACEHOLDER,
            "symbol": AXIS_SYMBOL,
            "taxonomy": ["BOUND_DERIVED", "BOUND_AUTHORIZED", "BOUND_PROPOSED", "BOUND_MISSING", "BOUND_NOT_APPLICABLE"],
            "kinds": ["MATHEMATICAL_BOUND", "METHODOLOGICAL_BOUND", "COMPUTATIONAL_BOUND"],
            "axes": [
                _axis("discrete_or_integer_label", "METHODOLOGICAL_BOUND"),
                _axis("combinatorial_or_graph_size", "METHODOLOGICAL_BOUND"),
                _axis("derivative_or_polynomial_order", "METHODOLOGICAL_BOUND"),
                _axis("field_or_coupling_multiplicity", "METHODOLOGICAL_BOUND"),
                _axis("continuous_or_cutoff_parameter", "METHODOLOGICAL_BOUND"),
                _axis("state_space_truncation", "COMPUTATIONAL_BOUND"),
                _axis("representation_label", "METHODOLOGICAL_BOUND"),
                _axis("rg_truncation_depth", "METHODOLOGICAL_BOUND"),
            ],
        },
        "nonuniqueness_policy": {
            "collapse_unresolved": False,
            "multiple_formulations_of_one_parent_may_share_a_batch": "YES_AS_SEPARATE_RECORDS",
            "representative_selection": "NOT_PERMITTED_WITHOUT_A_REGISTERED_EQUIVALENCE_AND_A_HUMAN_AUTHORIZATION",
            "unresolved_equivalence": "KEEP_SEPARATE",
        },
        "equivalence_policy": {
            "future_deduplication_requires": "a registered proof at the same equivalence level, plus human authorization to use it",
            "levels": ["KINEMATIC", "DYNAMICAL", "PHYSICAL"],
            "transfer": "NOT_PERMITTED",
            "unresolved_ids": list(UNRESOLVED),
        },
        "physical_input_schema": {
            "REQUIRES_NEW_PHYSICAL_INPUT_count": 47,
            "meaning": "each formulation inherits the structural input flag; this is not a proof of 47 new empirical constants",
            "slots": ["structural_input_flag", "mathematical_input", "physical_postulate", "empirical_input", "measured_numerical_value", "derived_quantity", "free_parameter", "conventional_parameter"],
        },
        "empirical_firewall": {
            "comparison_layer": "DOWNSTREAM_AND_CLOSED",
            "measured_values_as_selection_or_calibration": "PROHIBITED",
        },
        "vacuum_firewall": {"NO_VACUUM_SELECTED": True, "VACUUM_SELECTION": "NOT_INSERTED"},
        "finiteness": {
            "BOUNDED": "a declared domain exists; it need not be the whole mathematical family",
            "COMPUTATIONALLY_TERMINATING": "a machine halt, not a mathematical exhaustion",
            "FINITE": "every included axis has an explicit finite authorized domain",
            "FINITE_BATCH": "NOT_SATISFIED_FOR_A_NONEMPTY_SEARCH",
            "MATHEMATICALLY_COMPLETE": "not claimed by a finite enumeration",
        },
        "candidate_readiness_matrix": matrix,
        "models_generated": 0,
        "selected_formulation": "NONE",
    }
    if payload["equivalence_policy"]["unresolved_ids"] != list(UNRESOLVED):
        return _stop("equivalence")
    payload["proposal_hash"] = content_digest({key: value for key, value in payload.items() if key != "proposal_hash"})
    if write_artifacts:
        destination = physics / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / DESIGN_NAME).write_bytes(canonical_json_bytes(payload))
        if _unchanged(snapshot_existing_phases()) != before or audit_path.read_bytes() != audit_bytes or proposal_path.read_bytes() != proposal_bytes:
            return _stop("historical artifact changed")
    payload["status"] = "OK"
    return payload
