"""The broad Phase 17B catalogue does not explore or select a geometry."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase17b_geometry_formalization import (
    ARTIFACT_DIR_NAME,
    CATEGORIES,
    activate_theory_name,
    enable_grammar,
    filter_by_empirical_status,
    reopen_phase16,
    run_phase_17b,
    select_geometry,
    start_geometry_search,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

ROOT = Path(__file__).resolve().parents[1]


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _json(relative: str) -> dict:
    return json.loads((ROOT / "src" / "physics_lab" / "physics" / relative).read_text(encoding="utf-8"))


def test_broad_geometry_catalogue_does_not_select() -> None:
    before = _prior()
    phase16 = _json("phase16e_frontier_artifacts/PHASE_16E_FRONTIER.json")
    phase17a = _json("phase17a_geometry_audit_artifacts/PHASE_17A_GEOMETRY_CATALOG.json")
    result = run_phase_17b(write_artifacts=True)
    repeated = run_phase_17b(write_artifacts=True)
    after = _prior()
    records = result["geometry_meta_grammar"]["records"]
    by_id = {item["geometry_grammar_id"]: item for item in records}
    equivalences = {tuple(sorted((item["left"], item["right"]))): item["equivalence_status"] for item in result["geometric_equivalence_register"]}
    assert before == after
    assert _json("phase16e_frontier_artifacts/PHASE_16E_FRONTIER.json") == phase16
    assert _json("phase17a_geometry_audit_artifacts/PHASE_17A_GEOMETRY_CATALOG.json") == phase17a
    assert result["status"] == "OK"
    assert result["PHASE17B_STATUS"] == "COMPLETE"
    assert result["GEOMETRY_META_GRAMMAR_STATUS"] == "COMPLETE"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["SEARCH_STATUS"] == "NOT_STARTED"
    assert result["NO_GEOMETRY_SELECTED"] is True
    assert len(records) > 1
    assert set(CATEGORIES) <= {item["geometry_category"] for item in records}
    assert by_id["g17b.einstein_baseline"]["catalog_role"] == "REFERENCE_VALIDATION_BASELINE"
    assert by_id["g17b.einstein_baseline"]["search_status"] == "NOT_ENABLED"
    assert by_id["g17b.einstein_baseline"]["privileged_search_status"] is False
    assert result["einsteinian_reference_baseline"]["suppresses_other_families"] is False
    assert all(item["search_status"] == "NOT_ENABLED" and item["parent_grammar"] == "grammar_15f_v1" for item in records)
    assert all(item["dynamical_action"] == "NOT_INCLUDED" and item["MATTER_CONTENT"] == "NONE" and item["fermions_added"] is False for item in records)
    assert equivalences[tuple(sorted(("metric", "frame field")))] == "UNRESOLVED"
    assert equivalences[tuple(sorted(("curvature formulation", "teleparallel formulation")))] == "UNRESOLVED"
    assert by_id["g17b.spin_structure"]["fermions_added"] is False
    assert by_id["g17b.torsionful"]["torsion_dynamics"] == "NOT_INCLUDED"
    assert by_id["g17b.higher_dimensional"]["compactification_defined"] is False
    assert by_id["g17b.noncommutative_coordinates"]["finite_bound_spec"]["finite_boundable"] is False
    assert "deformation" not in "".join(by_id["g17b.noncommutative_coordinates"]["finite_bound_spec"]["bound_axes"])
    assert by_id["g17b.causal_set"]["continuum_class"] == "NON_CONTINUUM_GEOMETRY"
    assert by_id["g17b.causal_set"]["metric_structure"] == "not fundamental"
    assert by_id["g17b.spin_network"]["quantum_structure"] == "QUANTUM_KINEMATIC"
    assert by_id["g17b.spin_network"]["metric_structure"] == "not fundamental"
    assert by_id["g17b.emergent"]["emergence_assumed"] is False
    assert by_id["g17b.emergent"]["spacetime_role"] == "EMERGENT_EFFECTIVE_NOT_ASSUMED"
    assert filter_by_empirical_status(by_id["g17b.einstein_baseline"]["empirical_status"]) == "NOT_PERFORMED"
    assert activate_theory_name("string theory") == "NOT_ENABLED"
    assert enable_grammar("g17b.einstein_baseline") == "NOT_ENABLED"
    assert start_geometry_search() == "NOT_STARTED"
    assert select_geometry(records) == "NOT_PERFORMED"
    assert reopen_phase16() == "REJECTED"
    assert result["ranking_function"] == "ABSENT"
    assert "physical_sense_score" not in json.dumps(result["geometry_meta_grammar"]["categories"])
    unbounded = [item for item in records if item["finite_bound_spec"]["finite_boundable"] is False]
    assert {item["geometry_grammar_id"] for item in unbounded} >= {"g17b.generalized_tangent", "g17b.noncommutative_coordinates", "g17b.emergent"}
    assert all(item["finite_bound_spec"]["finite_bound_status"] == "NOT_YET_BOUNDED" for item in unbounded)
    assert all(item["phase16_reopened"] is False and item["merged"] is False for item in result["phase16_overlap_register"])
    assert any(item["phase16_grammar"] == "g16a.new.extra_connection" for item in result["phase16_overlap_register"])
    assert all(item["status"] == "NOT_AUTHORIZED" and item["geometries"] for item in result["geometry_batch_authorization_candidates"])
    assert [item["grammar_hash"] for item in records] == [item["grammar_hash"] for item in repeated["geometry_meta_grammar"]["records"]]
    assert len({item["grammar_hash"] for item in records}) == len(records)
    assert result["selected_geometry"] == "NONE"
    assert result["next_phase"]["status"] == "NOT_AUTHORIZED"
