"""Phase 18E classifies closure gaps and does not close them."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase18c_authorization_design import UNRESOLVED
from physics_lab.theory_kernel.phase18e_formalization_closure import (
    ARTIFACT_DIR_NAME,
    EXPECTED_IDS,
    SCHEMA_VERSION,
    execute_search,
    introduce_bound,
    run_phase_18e,
    select_action,
    select_theory,
    select_vacuum,
)

ROOT = Path(__file__).resolve().parents[1]
PHYSICS = ROOT / "src" / "physics_lab" / "physics"


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase18e_classifies_gaps_without_closing_them() -> None:
    before = _prior()
    sealed = {
        "phase18a_dynamical_formulation_artifacts/PHASE_18A_DYNAMICAL_AUDIT.json": None,
        "phase18b_batch_proposal_artifacts/PHASE_18B_DYNAMICAL_BATCH_PROPOSAL.json": None,
        "phase18c_authorization_artifacts/PHASE_18C_DYNAMICAL_BATCH_AUTHORIZATION_DESIGN.json": None,
        "phase18d_formalization_artifacts/PHASE_18D_CLASS_SPECIFIC_FORMALIZATION_AUDIT.json": None,
    }
    sealed = {path: (PHYSICS / path).read_bytes() for path in sealed}
    v23 = (ROOT / "docs/history/26Ottobre2026/rapporto_laboratorio_struttura_interna_FINAL_v23_TOPDOWN_QFT_CUMULATIVE.docx").read_bytes()
    result = run_phase_18e(write_artifacts=True)
    repeated = run_phase_18e(write_artifacts=True)
    assert before == _prior()
    for path, blob in sealed.items():
        assert (PHYSICS / path).read_bytes() == blob
    assert (ROOT / "docs/history/26Ottobre2026/rapporto_laboratorio_struttura_interna_FINAL_v23_TOPDOWN_QFT_CUMULATIVE.docx").read_bytes() == v23
    assert result["status_flag"] == "OK"
    assert result["PHASE18E_STATUS"] == "COMPLETE"
    assert result["schema_version"] == SCHEMA_VERSION
    assert result["search_active"] is False
    assert result["search_status"] == "NOT_STARTED"
    assert result["action_selected"] is False
    assert result["vacuum_selected"] is False
    assert result["new_physical_input_activated"] is False
    assert result["theory_selected"] is False
    assert result["bound_authorized"] == 0
    assert result["bound_derived"] == 0
    assert result["bound_proposed"] == 0
    assert result["BOUND_AUTHORIZATION_STATUS"] == "NOT_AUTHORIZED"
    assert result["dynamical_pfr_status"] == "NOT_TESTED"
    assert result["parameter_closure_status"] == "NOT_TESTED"
    audited = result["per_formulation_audit"]
    assert [item["formulation_id"] for item in audited] 
    assert set(item["formulation_id"] for item in audited) == set(EXPECTED_IDS)
    assert len(audited) == 47
    assert result["formulations_complete"] == 0
    assert result["formulations_partial"] == 34
    assert result["formulations_unresolved"] == 9
    assert result["formulations_not_yet_specifiable"] == 4
    assert result["derived_structure_count"] + result["neutral_definition_count"] + result["theory_selection_required_count"] + result["new_physical_input_required_count"] + result["undecided_count"] == 47
    assert result["ready_for_finite_bounding_count"] == 0
    assert all(item["ready_for_finite_bounding"] is False for item in audited)
    assert all(item["SEARCH_ELIGIBILITY"] == "NOT_ELIGIBLE" for item in audited)
    assert all(item["PHYSICAL_INPUT_REQUIREMENT"] == "NOT_DECIDED" for item in audited)
    assert all(item["new_physical_input_required"] is False for item in audited)
    assert all(item["closure_classification"] in {"THEORY_SELECTION_REQUIRED", "UNDECIDED"} for item in audited)
    assert all(item["object_classification"] for item in audited)
    finite = next(item for item in audited if item["formulation_id"] == "g17b1.finite_algebra__not_yet_specifiable__0")
    assert finite["algebra_selected"] is False
    assert finite["closure_classification"] == "THEORY_SELECTION_REQUIRED"
    assert all(item["reclassified"] is False and item["dynamical_class_resolved"] is False for item in audited if item["dynamical_class"] == "OTHER_FORMAL_DYNAMICS")
    assert result["firewall_status"]["unresolved_equivalence_ids"] == list(UNRESOLVED)
    assert result["equivalence_resolved_count"] == 0
    assert result["historical_integrity"]["v23_docx"]["rewritten"] is False
    assert result["historical_integrity"]["v23_pdf"]["correction"] == "NOT_PERFORMED"
    assert result["NEXT_ALLOWED_PHASE"] == "NOT_ACTIVATED"
    text = json.dumps(result)
    assert ("1/" + "137") not in text
    assert ("alp" + "ha_em") not in text
    assert execute_search() == "NOT_PERFORMED"
    assert select_theory() == "NOT_PERFORMED"
    assert select_action() == "NOT_PERFORMED"
    assert select_vacuum() == "NOT_PERFORMED"
    assert introduce_bound() == "NOT_PERFORMED"
    assert repeated["audit_hash"] == result["audit_hash"]
    assert result["HISTORICAL_ARTIFACTS_MODIFIED"] is False
