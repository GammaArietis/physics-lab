"""Phase 12C grammar-audit tests. No search and no physical activation."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12b import snapshot_prior_phases
from physics_lab.theory_kernel.phase12c import (
    TYPE_B_OBLIGATIONS,
    request_physical_activation,
    run_phase_12c,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_prior_phases().items() if not key.startswith("phase12c_artifacts")}


def test_phase12c_defines_grammar_without_activating_physics() -> None:
    before = _prior()
    result = run_phase_12c(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_12C_STATUS"] == "COMPLETE"
    assert result["GRAMMAR_UPDATE_STATUS"] == "VERIFIED"
    assert result["SAME_AXIS_SEMANTICS_STATUS"] == "VERIFIED"
    assert result["TYPE_B_RESOLUTION_STATUS"] == "VERIFIED"
    assert result["T09_PROVENANCE_STATUS"] == "REQUIRES_HUMAN_INPUT"
    assert result["T10_PROVENANCE_STATUS"] == "REQUIRES_HUMAN_INPUT"
    assert result["T09_GENERATOR_STATUS"] == "DISABLED"
    assert result["T10_GENERATOR_STATUS"] == "DISABLED"
    assert result["PHYSICAL_ACTIVATION_STATUS"] == "NOT_AUTHORIZED"
    assert result["GRAMMAR_VERSION"] == "grammar_12b_v2"
    assert result["PREVIOUS_GRAMMAR_VERSION"] == "phase10a-grammar-v1.2"
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["blind_computation_restarted"] is False
    assert result["new_physical_principle_activated"] is False
    assert result["frontiers"]["frontier.vacuum_selection"]["status"] == "REQUIRES_HUMAN_INPUT"
    assert result["frontiers"]["frontier.modulus_stabilization"]["status"] == "REQUIRES_HUMAN_INPUT"
    assert result["t09_record"]["provenance"] == "NOT_FOUND"
    assert result["t09_record"]["operational_status"] == "NOT_OPERATIONALLY_ENABLED"
    assert result["t09_record"]["mathematical_statement"] == "vacuum-selection principle"
    assert result["t10_record"]["provenance"] == "NOT_FOUND"
    assert result["t10_record"]["operational_status"] == "NOT_OPERATIONALLY_ENABLED"
    semantics = result["same_axis_semantics"]
    assert semantics["physical_equivalence"] is False
    assert semantics["mathematical_identity"] is False
    assert semantics["composition_permitted"] is False
    assert [item["obligation_id"] for item in result["type_b_resolutions"]] == list(TYPE_B_OBLIGATIONS)
    assert {item["result"] for item in result["type_b_resolutions"]} == {"RESOLVED_VIA_GRAMMAR_UPDATE"}
    assert all(item["physical_consequence_derived"] is False for item in result["type_b_resolutions"])
    assert len(result["mass_obligations_unchanged"]) == 7
    assert request_physical_activation("T09")["status"] == "PHYSICAL_ACTIVATION_NOT_AUTHORIZED"
    assert request_physical_activation("T10")["status"] == "PHYSICAL_ACTIVATION_NOT_AUTHORIZED"
    assert len(result["answers"]) == 10
