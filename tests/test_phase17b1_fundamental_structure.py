"""Phase 17B.1 adds a fundamental-structure catalogue without rewriting Phase 17B."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase17b1_fundamental_structure import (
    ARTIFACT_DIR_NAME,
    activate_discovered_family,
    activate_theory_name,
    enable_grammar,
    filter_by_empirical_status,
    reopen_phase16,
    run_phase_17b1,
    select_structure,
    start_search,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

ROOT = Path(__file__).resolve().parents[1]


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _json(relative: str) -> dict:
    return json.loads((ROOT / "src" / "physics_lab" / "physics" / relative).read_text(encoding="utf-8"))


def test_phase17b1_upgrades_without_rewriting_history() -> None:
    before = _prior()
    historical = _json("phase17b_geometry_formalization_artifacts/PHASE_17B_GEOMETRY_GRAMMARS.json")
    phase16 = _json("phase16e_frontier_artifacts/PHASE_16E_FRONTIER.json")
    result = run_phase_17b1(write_artifacts=True)
    repeated = run_phase_17b1(write_artifacts=True)
    after = _prior()
    records = result["fundamental_structure_candidate_catalog"]
    by_id = {item["grammar_candidate_id"]: item for item in records}
    categories = {item["structure_category"] for item in records}
    assert before == after
    assert _json("phase17b_geometry_formalization_artifacts/PHASE_17B_GEOMETRY_GRAMMARS.json") == historical
    assert _json("phase16e_frontier_artifacts/PHASE_16E_FRONTIER.json") == phase16
    assert result["status"] == "OK"
    assert result["PHASE17B1_STATUS"] == "COMPLETE"
    assert result["HISTORICAL_PHASE17B_PRESERVATION_STATUS"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["SEARCH_STATUS"] == "NOT_STARTED"
    assert result["upgrade_relation"]["from"] == "HISTORICAL_PHASE17B_VERSION"
    assert result["upgrade_relation"]["to"] == "PHASE17B.1_UPGRADE"
    assert result["upgrade_relation"]["historical_grammar_count"] == 50
    assert result["grammar_hash"] == repeated["grammar_hash"]
    assert len({item["grammar_hash"] for item in records}) == len(records)
    assert by_id["g17b1.einstein_baseline"]["SEARCHABILITY_STATUS"] == "REFERENCE_ONLY"
    assert len(categories) > 1
    assert "STRING_BRANE_STRUCTURE" in categories
    assert "QUANTUM_GEOMETRIC_STRUCTURE" in categories
    assert "DISCRETE_CAUSAL_SPACETIME" in categories
    assert "NONCOMMUTATIVE_GEOMETRY" in categories
    assert "QUANTUM_FIELD_THEORETIC_GRAVITY" in categories
    assert "HOLOGRAPHIC_DUAL_STRUCTURE" in categories
    assert by_id["g17b1.worldsheet"]["extended_object_structure"] == "worldvolume"
    assert by_id["g17b1.worldsheet"]["matter_spectrum"] == "NONE"
    assert by_id["g17b1.worldsheet"]["compactification_defined"] is False
    assert by_id["g17b1.spin_network"]["metric_structure"] == "not fundamental"
    assert by_id["g17b1.causal_set"]["discrete_structure"] == "fundamental"
    assert by_id["g17b1.spin_structure"]["fermions_added"] is False
    assert by_id["g17b1.higher_dimensional"]["compactification_defined"] is False
    assert by_id["g17b1.noncommutative_coordinates"]["finite_bound_spec"]["finite_bound_status"] == "NOT_YET_BOUNDED"
    assert by_id["g17b1.deformed_symmetry"]["finite_bound_spec"]["missing_ingredient"] != ""
    assert by_id["g17b1.teleparallel"]["equivalence_status"] == "EQUIVALENCE_UNRESOLVED"
    assert by_id["g17b1.rg_flow"]["mathematical_definition"].find("fixed point") == -1 or "no chosen fixed point" in by_id["g17b1.rg_flow"]["mathematical_definition"]
    assert all(item["search_status"] == "NOT_ENABLED" and item["new_physical_input"]["status"] != "DERIVED" for item in records)
    assert all(item["role"] == "REFERENCE_ONLY" and item["generator_enabled"] is False for item in result["reference_framework_catalog"])
    assert activate_theory_name("string theory") == "NOT_ENABLED"
    assert enable_grammar("g17b1.einstein_baseline") == "NOT_ENABLED"
    discovered = result["new_candidate_family_register"]
    assert discovered
    assert all(item["search_status"] == "NOT_ENABLED" and item["provenance_manifest"]["discovered"] is True for item in discovered)
    assert activate_discovered_family(discovered[0]["grammar_candidate_id"]) == "NOT_ENABLED"
    assert "infinite_dimensional" in result["meta_grammar_discovery_report"]["missing_poles"]
    assert filter_by_empirical_status("WELL_TESTED_FRAMEWORK") == "NOT_PERFORMED"
    assert start_search() == "NOT_STARTED"
    assert select_structure(records) == "NOT_PERFORMED"
    assert reopen_phase16() == "REJECTED"
    assert all(item["phase16_reopened"] is False and item["merged"] is False for item in result["phase16_overlap_register"])
    assert any(item["phase16_grammar"] == "g16a.new.higher_derivative_order" for item in result["phase16_overlap_register"])
    assert any(item["phase16_grammar"] == "g16a.new.degeneracy_constraint" for item in result["phase16_overlap_register"])
    assert all(item["status"] == "NOT_AUTHORIZED" and item["structures"] for item in result["human_authorization_frontier"])
    assert result["ranking_function"] == "ABSENT"
    assert result["NO_THEORY_SELECTED"] is True
    assert result["selected_structure"] == "NONE"
