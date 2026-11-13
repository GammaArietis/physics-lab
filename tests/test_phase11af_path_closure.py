"""Negative tests for the Phase 11AF path-closure audit."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.physics.phase11af_path_closure import (
    FROZEN_4C_HASH,
    _guarded_files,
    _snapshot,
    run_phase_11af_closure_audit,
)

PHYSICS = Path(__file__).resolve().parents[1] / "src" / "physics_lab" / "physics"


def test_phase11af_path_closure_records_the_frontier_and_stops() -> None:
    before = _snapshot(_guarded_files())
    result = run_phase_11af_closure_audit()
    after = _snapshot(_guarded_files())

    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE11_INTEGRITY_STATUS"] == "VERIFIED"
    assert result["PHASE11_CONSOLIDATION_STATUS"] == "VERIFIED"
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["PHASE_11AF_STATUS"] == "COMPLETE"
    assert result["PHASE_11AF_STOPPED"] is True
    assert result["PHASE11_CURRENT_PATH_EXHAUSTED"] is True
    assert result["HUMAN_DECISION_REQUIRED"] is True
    assert result["PYTEST_STATUS"] == "GREEN"

    assert result["VACUUM_CLOSURE_STATUS"] == "NOT_FOUND"
    assert result["vacuum"]["VACUUM_SELECTION"] == "NOT_FOUND"
    assert result["vacuum"]["T09"] == "REQUIRES_NEW_PHYSICAL_INPUT"
    assert result["vacuum"]["PRINCIPLE_ID"] == "PRINCIPLE_UNSPECIFIED"
    assert result["vacuum"]["CONTAINMENT_STATUS"] == "REQUIRES_NEW_ASSUMPTION"
    assert result["vacuum"]["GLOBAL_MINIMIZATION_STATUS"] == "ABSENT"
    assert result["vacuum"]["VACUUM_SELECTION_STATUS"] == "NOT_FOUND"
    assert result["vacuum"]["operational_principles_inserted"] == []

    assert result["MODULUS_CLOSURE_STATUS"] == "NOT_FOUND"
    assert result["modulus"]["T10"] == "REQUIRES_NEW_PHYSICAL_INPUT"
    assert result["modulus"]["modulus_exists"] is True
    assert result["modulus"]["modulus_stabilized"] is False
    assert result["modulus"]["inferred_from_T_F_T_f_a_or_Z_i"] is False

    assert result["MEDIATION_CLOSURE_STATUS"] == "VERIFIED"
    assert result["mediation"]["selected_branch"] is None
    assert result["mediation"]["derived_from_another_branch"] is False
    assert result["mediation"]["certified_equivalent_pair"] is False
    assert result["mixed_mediation"] == "NOT_ACTIVATED"

    assert result["class_b"] == {
        "T04": "PARTIAL",
        "T05": "PARTIAL",
        "existing_module_resolution": "EXHAUSTED",
    }
    assert result["CLASS_B_CLOSURE_STATUS"] == "EXHAUSTED"
    assert result["CLASS_C_STATUS"] == "REQUIRES_EXPLICIT_ASSUMPTION"
    assert result["class_c"] == {
        "T06": "REQUIRES_EXPLICIT_ASSUMPTION",
        "T07": "REQUIRES_EXPLICIT_ASSUMPTION",
        "T08": "REQUIRES_EXPLICIT_ASSUMPTION",
    }
    assert result["CLASS_D_STATUS"] == "REQUIRES_NEW_PHYSICAL_INPUT"
    assert set(result["class_d"]) == {"T09", "T10", "T11", "T12", "T13", "T14"}
    assert result["CLASS_E_STATUS"] == "OUT_OF_SCOPE"
    assert result["class_e"]["T17"] == "FORBIDDEN_IN_CURRENT_SCOPE"

    assert result["pfr"]["TOTAL_CERTIFIED_PFR"] == 0
    assert result["pfr"]["cross_branch_count"] == 0
    assert result["PFR_CLOSURE_STATUS"] == "NOT_FOUND"
    assert result["parameters"]["fixed_parameters"] == []
    assert result["parameters"]["reduced_parameter_count"] == 0
    assert result["parameters"]["unauthorized_parameter_identification"] is False
    assert result["PARAMETER_CLOSURE_STATUS"] == "VERIFIED"
    assert result["NEW_PARAMETER_COUNT"] == 0
    assert result["NEW_PHYSICAL_INPUT_STATUS"] is False
    assert result["NEW_ASSUMPTION_STATUS"] is False

    human = result["HUMAN_INPUT_REQUIRED_FOR_NEXT_STEP"]
    assert human["chosen_item"] is None
    assert [row["item"] for row in human["CLASS_C_ASSUMPTIONS"]] == ["T06", "T07", "T08"]
    assert [row["item"] for row in human["CLASS_D_PHYSICAL_INPUTS"]] == [
        "T09",
        "T10",
        "T11",
        "T12",
        "T13",
        "T14",
    ]
    assert [row["item"] for row in human["CLASS_E_SCOPE_CHANGES"]] == ["T15", "T16", "T17"]
    assert all(row["activated"] is False for group in human.values() if isinstance(group, list) for row in group)
    assert result["decision_log"]["chosen_next_input"] is None
    assert result["HUMAN_INPUT_BOUNDARY_STATUS"] == "VERIFIED"

    assert result["experimental_data_used"] is False
    assert result["target_search"] is False
    assert result["calibration_used"] is False
    assert result["ranking_used"] is False
    assert result["EXPERIMENTAL_INPUT_STATUS"] == "ABSENT"
    assert result["RANKING_STATUS"] == "ABSENT"
    assert set(result["future_research"].values()) == {"NOT_ACTIVATED"}

    missing = {row["item"]: row["exact_missing_assumption"] for row in human["CLASS_C_ASSUMPTIONS"]}
    assert missing["T06"] == "human-authorized identification F_X = F_Phi"
    assert "F_T" in missing["T07"]
    assert "f_1(T)" in human["CLASS_C_ASSUMPTIONS"][2]["mathematical_statement"]

    artifact = PHYSICS / "phase11af_closure_artifacts" / "PHASE_11AF_PATH_CLOSURE.json"
    stored = json.loads(artifact.read_text(encoding="utf-8"))
    assert stored["statuses"]["PHASE_11AF_STOPPED"] is True
    assert stored["decision_log"]["pfr_count"] == 0
    assert len(stored["questions"]) == 16
    assert len(stored["consistency_matrix"]) == 12


def test_phase11af_path_closure_does_not_rewrite_prior_records() -> None:
    sentinel = PHYSICS / "phase11ae1_artifacts" / "PHASE_11AE1_CONTAINMENT.json"
    modulus = PHYSICS / "phase11af_artifacts" / "PHASE_11AF_T10_CONTAINMENT.json"
    before_sentinel = sentinel.read_bytes()
    before_modulus = modulus.read_bytes()
    run_phase_11af_closure_audit()
    assert sentinel.read_bytes() == before_sentinel
    assert modulus.read_bytes() == before_modulus
