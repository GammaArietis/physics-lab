"""Phase 18C designs an authorization and does not grant it."""

from __future__ import annotations

from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase18c_authorization_design import (
    ARTIFACT_DIR_NAME,
    PLACEHOLDER,
    execute_search,
    grant_authorization,
    run_phase_18c,
    select_formulation,
)

ROOT = Path(__file__).resolve().parents[1]
PHYSICS = ROOT / "src" / "physics_lab" / "physics"


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase18c_designs_authorization_without_granting_it() -> None:
    before = _prior()
    audit = (PHYSICS / "phase18a_dynamical_formulation_artifacts" / "PHASE_18A_DYNAMICAL_AUDIT.json").read_bytes()
    proposal = (PHYSICS / "phase18b_batch_proposal_artifacts" / "PHASE_18B_DYNAMICAL_BATCH_PROPOSAL.json").read_bytes()
    result = run_phase_18c(write_artifacts=True)
    repeated = run_phase_18c(write_artifacts=True)
    assert before == _prior()
    assert (PHYSICS / "phase18a_dynamical_formulation_artifacts" / "PHASE_18A_DYNAMICAL_AUDIT.json").read_bytes() == audit
    assert (PHYSICS / "phase18b_batch_proposal_artifacts" / "PHASE_18B_DYNAMICAL_BATCH_PROPOSAL.json").read_bytes() == proposal
    assert result["status"] == "OK"
    assert result["PHASE18C_STATUS"] == "COMPLETE"
    assert result["SEARCH_STATUS"] == "NOT_STARTED"
    assert result["SEARCH_ACTIVE"] is False
    assert result["HUMAN_AUTHORIZATION_STATUS"] == "NOT_YET_GRANTED"
    assert result["state"] == "PROPOSED"
    assert result["activation_status"] == "NOT_ACTIVATED"
    assert result["execution_status"] == "NOT_EXECUTED"
    assert result["admissible_batch"] == "EMPTY_ADMISSIBLE_BATCH"
    assert result["subset_selection"] == "SUBSET_SELECTION_NOT_JUSTIFIED"
    assert result["models_generated"] == 0
    assert len(result["candidate_readiness_matrix"]) == 47
    assert all(row["executable"] is False and row["additional_mathematical_definition_required"] is True for row in result["candidate_readiness_matrix"])
    assert result["authorization_schema"]["included_formulation_ids"] == []
    assert result["bound_policy"]["numerical_values_introduced"] is False
    assert result["bound_policy"]["copied_from_phase17c"] is False
    assert all(axis["numerical_value"] == PLACEHOLDER for axis in result["bound_policy"]["axes"])
    assert len(result["equivalence_policy"]["unresolved_ids"]) == 7
    assert execute_search() == "NOT_PERFORMED"
    assert grant_authorization() == "NOT_YET_GRANTED"
    assert select_formulation() == "NOT_PERFORMED"
    assert repeated["proposal_hash"] == result["proposal_hash"]
