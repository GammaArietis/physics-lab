"""Phase 18B proposes a batch and does not execute it."""

from __future__ import annotations

from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase18b_batch_proposal import (
    ARTIFACT_DIR_NAME,
    authorize_batch,
    execute_batch,
    run_phase_18b,
    select_action,
)

ROOT = Path(__file__).resolve().parents[1]
PHYSICS = ROOT / "src" / "physics_lab" / "physics"


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase18b_proposes_an_empty_executable_batch() -> None:
    before = _prior()
    audit = (PHYSICS / "phase18a_dynamical_formulation_artifacts" / "PHASE_18A_DYNAMICAL_AUDIT.json").read_bytes()
    catalog = (PHYSICS / "phase17_tier1_search_artifacts" / "PHASE_17_TIER1_CATALOG.json").read_bytes()
    report = (ROOT / "docs" / "history" / "20Ottobre2026" / "rapporto_laboratorio_struttura_interna_FINAL_v22_TOPDOWN_QFT_CUMULATIVE.docx").read_bytes()
    result = run_phase_18b(write_artifacts=True)
    repeated = run_phase_18b(write_artifacts=True)
    batch = result["proposed_batches"][0]
    assert before == _prior()
    assert (PHYSICS / "phase18a_dynamical_formulation_artifacts" / "PHASE_18A_DYNAMICAL_AUDIT.json").read_bytes() == audit
    assert (PHYSICS / "phase17_tier1_search_artifacts" / "PHASE_17_TIER1_CATALOG.json").read_bytes() == catalog
    assert (ROOT / "docs" / "history" / "20Ottobre2026" / "rapporto_laboratorio_struttura_interna_FINAL_v22_TOPDOWN_QFT_CUMULATIVE.docx").read_bytes() == report
    assert result["status"] == "OK"
    assert result["PHASE18B_PROPOSAL_STATUS"] == "COMPLETE"
    assert result["SEARCH_STATUS"] == "NOT_STARTED"
    assert result["SEARCH_ACTIVE"] is False
    assert result["HUMAN_AUTHORIZATION_STATUS"] == "NOT_YET_GRANTED"
    assert result["formulation_count"] == 47
    assert len(result["candidate_classification"]) == 47
    assert batch["included_formulation_ids"] == []
    assert len(batch["excluded_formulation_ids"]) == 47
    assert batch["maximum_generated_candidates"] == 0
    assert result["bound_register"]["BOUND_PROPOSED"] == 0
    assert result["bound_register"]["copied_from_phase17c"] is False
    assert result["models_generated"] == 0
    assert result["VACUUM_SELECTION"] == "NOT_INSERTED"
    assert len(result["equivalence_register"]) == 7
    assert execute_batch() == "NOT_PERFORMED"
    assert authorize_batch() == "NOT_YET_GRANTED"
    assert select_action() == "NOT_PERFORMED"
    assert repeated["proposal_hash"] == result["proposal_hash"]
    assert result["category_counts"]["READY_FOR_FINITE_BOUNDING"] == 0
    assert result["category_counts"]["REQUIRES_NEW_PHYSICAL_INPUT"] == 47
