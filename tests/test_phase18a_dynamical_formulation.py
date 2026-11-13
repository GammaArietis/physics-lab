"""Phase 18A registers dynamical formulations and does not search."""

from __future__ import annotations

from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase18a_dynamical_formulation import (
    ARTIFACT_DIR_NAME,
    PROVENANCE,
    activate_theory_name,
    combine_grammars,
    enable_formulation,
    insert_vacuum_principle,
    request_search,
    run_phase_18a,
    select_action,
    select_by_familiarity,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

ROOT = Path(__file__).resolve().parents[1]
PHYSICS = ROOT / "src" / "physics_lab" / "physics"


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase18a_audits_formulations_without_search() -> None:
    before = _prior()
    catalog = (PHYSICS / "phase17_tier1_search_artifacts" / "PHASE_17_TIER1_CATALOG.json").read_bytes()
    freeze = (PHYSICS / "phase4c_action_freeze.json").read_bytes()
    phase16 = (PHYSICS / "phase16e_frontier_artifacts" / "PHASE_16E_FRONTIER.json").read_bytes()
    phase17e = (PHYSICS / "phase17e_frontier_artifacts" / "PHASE_17E_FRONTIER.json").read_bytes()
    result = run_phase_18a(write_artifacts=True)
    repeated = run_phase_18a(write_artifacts=True)
    specs = result["dynamical_grammar_catalog"]
    parents = {item["structural_grammar_id"]: item for item in result["parent_structures"]}
    causal = [spec for spec in specs if spec["parent_structural_grammar_id"] == "g17b1.causal_set"]
    assert before == _prior()
    assert (PHYSICS / "phase17_tier1_search_artifacts" / "PHASE_17_TIER1_CATALOG.json").read_bytes() == catalog
    assert (PHYSICS / "phase4c_action_freeze.json").read_bytes() == freeze
    assert (PHYSICS / "phase16e_frontier_artifacts" / "PHASE_16E_FRONTIER.json").read_bytes() == phase16
    assert (PHYSICS / "phase17e_frontier_artifacts" / "PHASE_17E_FRONTIER.json").read_bytes() == phase17e
    assert result["status"] == "OK"
    assert result["PHASE18A_STATUS"] == "COMPLETE"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["SEARCH_STATUS"] == "NOT_STARTED"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["selected_formulation"] == "NONE"
    assert result["models_generated"] == 0
    assert len(parents) == 27
    assert len(specs) > 27
    assert all(spec["search_status"] == "NOT_ENABLED" and spec["FORMALIZATION_STATUS"] == "PARTIAL" for spec in specs)
    assert all(item["provenance"] in PROVENANCE for spec in specs for item in spec["ingredients"])
    assert any(len([spec for spec in specs if spec["parent_structural_grammar_id"] == grammar_id]) > 1 for grammar_id in parents)
    assert all(item["KINEMATIC_EQUIVALENCE"] == "EQUIVALENCE_UNRESOLVED" and item["DYNAMICAL_EQUIVALENCE"] == "EQUIVALENCE_UNRESOLVED" and item["equivalence_transfer"] == "NOT_PERFORMED" for item in result["dynamical_equivalence_register"])
    assert len(result["dynamical_equivalence_register"]) == 7
    assert all(spec["parameter_inventory"]["dynamical_verified_pfr"] == "NOT_TESTED" for spec in specs)
    assert all(spec["parameter_inventory"]["dynamical_parameter_freedom"] == "NOT_TESTED" for spec in specs)
    assert causal and all(spec["formulation_type"] != "LOCAL_ACTION_FUNCTIONAL" for spec in causal)
    assert all(spec["vacuum_selection"]["principle"] == "NOT_INSERTED" for spec in specs)
    assert all(item["new_physical_input"] == "TRUE" and item["relabelled_as_derived"] is False for item in result["new_physical_input_register"])
    assert all(item["provenance"] != "DERIVED" for spec in specs for item in spec["ingredients"] if item["name"] == "dynamical_law")
    assert select_action("General Relativity") == "NOT_PERFORMED"
    assert activate_theory_name("loop quantum gravity") == "NOT_ENABLED"
    assert enable_formulation(specs[0]["dynamical_grammar_id"]) == "NOT_ENABLED"
    assert combine_grammars(list(parents)[:2]) == "NOT_GENERATED"
    assert request_search() == "NOT_STARTED"
    assert insert_vacuum_principle() == "NOT_PERFORMED"
    assert select_by_familiarity() == "NOT_PERFORMED"
    assert result["combination_status"] == "NOT_GENERATED"
    assert result["phase_18_batch_authorization_candidates"][0]["status"] == "PREPARED_NOT_ACTIVATED"
    assert result["ranking_function"] == "ABSENT"
    assert repeated["audit_hash"] == result["audit_hash"]
    assert parents["g17b1.finite_algebra"]["structural_readiness"] == "PARTIAL"
    assert parents["g17b1.conformal"]["structural_readiness"] == "VERIFIED"
