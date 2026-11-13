"""Phase 17E audits readiness and does not continue the search."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase17e_frontier import (
    ARTIFACT_DIR_NAME,
    activate_discovered_family,
    activate_theory_name,
    insert_action,
    register_tier4,
    request_tier2,
    run_phase_17e,
    select_next_from_results,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

ROOT = Path(__file__).resolve().parents[1]
PHYSICS = ROOT / "src" / "physics_lab" / "physics"


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase17e_separates_structure_from_dynamics() -> None:
    before = _prior()
    catalog = (PHYSICS / "phase17_tier1_search_artifacts" / "PHASE_17_TIER1_CATALOG.json").read_bytes()
    authorization = (PHYSICS / "phase17d_batch_authorization_artifacts" / "PHASE_17_BATCH_AUTHORIZATION.json").read_bytes()
    phase16 = (PHYSICS / "phase16e_frontier_artifacts" / "PHASE_16E_FRONTIER.json").read_bytes()
    result = run_phase_17e(write_artifacts=True)
    repeated = run_phase_17e(write_artifacts=True)
    rows = result["per_grammar_action_readiness_table"]
    classes = [item["audit_class"] for item in result["open_obligation_register"]]
    assert before == _prior()
    assert (PHYSICS / "phase17_tier1_search_artifacts" / "PHASE_17_TIER1_CATALOG.json").read_bytes() == catalog
    assert (PHYSICS / "phase17d_batch_authorization_artifacts" / "PHASE_17_BATCH_AUTHORIZATION.json").read_bytes() == authorization
    assert (PHYSICS / "phase16e_frontier_artifacts" / "PHASE_16E_FRONTIER.json").read_bytes() == phase16
    assert result["status"] == "OK"
    assert result["PHASE17E_STATUS"] == "COMPLETE"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["recorded_tier1"]["valid_models"] == 27
    assert result["recorded_tier1"]["verified_PFR"] == 0
    assert result["STRUCTURAL_DYNAMICAL_SEPARATION"] == "VERIFIED"
    assert result["dynamical_pfr_scope_report"]["DYNAMICAL_VERIFIED_PFR"] == "NOT_TESTED"
    assert result["structural_pfr_report"]["STRUCTURAL_VERIFIED_PFR"] == 0
    assert result["dynamical_closure_scope_report"]["DYNAMICAL_PARAMETER_CLOSURE"] == "NOT_TESTED"
    assert result["structural_closure_report"]["STRUCTURAL_PARAMETER_CLOSURE"] == "OPEN"
    assert len(rows) == 27
    assert all(row["action_status"] == "NOT_INCLUDED" and row["complete_dynamical_theory"] is False for row in rows)
    assert all(row["DYNAMICAL_READINESS"] == "ACTION_REQUIRES_NEW_ASSEMBLY" for row in rows)
    assert all(row["new_physical_input"] == "TRUE" for row in rows)
    assert sum(row["STRUCTURAL_READINESS"] == "VERIFIED" for row in rows) == 26
    assert sum(row["STRUCTURAL_READINESS"] == "PARTIAL" for row in rows) == 1
    assert len(result["equivalence_register"]) == 7
    assert all(item["structural_equivalence"] == "EQUIVALENCE_UNRESOLVED" and item["dynamical_equivalence"] == "NOT_TESTED" for item in result["equivalence_register"])
    assert len(result["open_obligation_register"]) == 44
    assert classes.count("action formalization") == 27
    assert insert_action("General Relativity") == "NOT_PERFORMED"
    assert activate_theory_name("string theory") == "NOT_ENABLED"
    assert activate_discovered_family("g17b1.constraint_quotient") == "NOT_ENABLED"
    assert request_tier2() == "NOT_AUTHORIZED"
    assert register_tier4() == "NOT_REGISTERED"
    assert select_next_from_results({"verified_PFR": 0}) == "NOT_PERFORMED"
    assert all(item["status"] == "NOT_AUTHORIZED" for item in result["next_authorization_options"])
    assert result["selected_option"] == "NONE"
    assert result["ranking_function"] == "ABSENT"
    assert result["CATALOG_HASH"] == json.loads(catalog)["catalog_hash"]
    assert repeated["PHASE17E_STATUS"] == "COMPLETE"
