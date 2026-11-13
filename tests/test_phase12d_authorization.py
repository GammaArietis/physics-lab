"""Phase 12D authorization-gate tests. No search and no physical activation."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12d_authorization import (
    AUTHORIZATION_FIELDS,
    ARTIFACT_DIR_NAME,
    classify_authorization,
    request_physical_activation,
    run_phase_12d,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {
        key: value
        for key, value in snapshot_existing_phases().items()
        if not key.startswith(ARTIFACT_DIR_NAME)
    }


def test_phase12d_gate_does_not_authorize_physics() -> None:
    before = _prior()
    result = run_phase_12d(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_12D_STATUS"] == "COMPLETE"
    assert result["AUTHORIZATION_GATE_STATUS"] == "VERIFIED"
    assert result["T09_AUTHORIZATION_STATUS"] == "REQUIRES_HUMAN_INPUT"
    assert result["T10_AUTHORIZATION_STATUS"] == "REQUIRES_HUMAN_INPUT"
    assert result["T09_PROPOSAL_STATUS"] == "INCOMPLETE"
    assert result["T10_PROPOSAL_STATUS"] == "INCOMPLETE"
    assert result["GRAMMAR_MIGRATION_STATUS"] == "NOT_APPLIED"
    assert result["PARAMETER_IMPACT_STATUS"] == "PARTIAL"
    assert result["PROOF_OBLIGATION_STATUS"] == "VERIFIED"
    assert result["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert result["FROZEN_STATE_STATUS"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["CURRENT_GRAMMAR_VERSION"] == "grammar_12b_v2"
    assert result["PROPOSED_GRAMMAR_VERSION"] == "NOT_CREATED"
    assert result["PHYSICAL_ACTIVATION"] == "NONE"
    assert result["BLIND_SEARCH"] == "NOT_RERUN"
    assert result["FROZEN_PHASES"] == "UNCHANGED"
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["blind_computation_restarted"] is False
    assert result["new_physical_principle_activated"] is False
    assert result["generator_entries_created"] is False
    assert result["frontiers"]["frontier.vacuum_selection"]["status"] == "REQUIRES_HUMAN_INPUT"
    assert result["frontiers"]["frontier.modulus_stabilization"]["status"] == "REQUIRES_HUMAN_INPUT"
    assert result["t09"]["current_provenance"] == "NOT_FOUND"
    assert result["t09"]["exact_mathematical_statement"] == "ABSENT"
    assert result["t09"]["proposed_activation_status"] == "NOT_AUTHORIZED"
    assert result["t10"]["current_provenance"] == "NOT_FOUND"
    assert result["t10"]["exact_mathematical_statement"] == "ABSENT"
    assert result["t09_candidate"]["mathematical_definition"] == "ABSENT"
    assert result["t09_candidate"]["activation_status"] == "NOT_AUTHORIZED"
    assert result["t09_candidate"]["generator_changes"] == "NONE"
    assert result["t10_candidate"]["activation_status"] == "NOT_AUTHORIZED"
    assert result["t09_record"]["operational_status"] == "NOT_OPERATIONALLY_ENABLED"
    assert result["t10_record"]["operational_status"] == "NOT_OPERATIONALLY_ENABLED"
    assert result["vacuum_audit"]["merged"] is False
    assert result["vacuum_audit"]["tachyonic_absence_implies_selected_vacuum"] is False
    assert result["vacuum_audit"]["selection_criterion_defined"] is False
    assert result["modulus_audit"]["stabilization_inferred_from_modulus_existence"] is False
    assert result["modulus_audit"]["fluxes_introduced"] is False
    assert result["modulus_audit"]["potential_introduced"] is False
    assert result["same_axis_semantics"]["status"] == "VERIFIED"
    assert result["grammar_migration"]["applied"] is False
    assert result["grammar_migration"]["exact_new_generator_inputs"] == []
    assert result["parameter_impact"]["existing_parameter_status_changes"] == []
    assert result["parameter_impact"]["existing_pfr_status_changes"] == []
    assert all(item["certified_pass"] is False for item in result["proof_obligations"])
    assert all(item["current_status"] == "OPEN" for item in result["proof_obligations"])
    assert {item["observed"] for item in result["dry_run"] if item["case"] == "8"} == {
        "PHYSICAL_ACTIVATION_NOT_AUTHORIZED"
    }
    assert [item["observed"] for item in result["dry_run"]] == [item["expected"] for item in result["dry_run"]]
    assert len(result["dry_run"]) == 10
    assert request_physical_activation("T09")["status"] == "PHYSICAL_ACTIVATION_NOT_AUTHORIZED"
    assert request_physical_activation("T10")["status"] == "PHYSICAL_ACTIVATION_NOT_AUTHORIZED"
    assert {item["status"] for item in result["promotions"]} == {"PHYSICAL_ACTIVATION_NOT_AUTHORIZED"}
    held = classify_authorization(
        {
            "activation_scope": "T09",
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
    )
    assert held["applied"] is False
    assert held["activation_status"] == "NOT_AUTHORIZED"
    assert list(AUTHORIZATION_FIELDS) == list(result["minimum_authorization_fields"])
    assert result["gate"]["default_state"] == "NOT_AUTHORIZED"
    assert result["proposal_object"] != result["authorization_object"]
