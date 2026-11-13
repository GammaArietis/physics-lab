"""Phase 17A catalogues geometries and does not search them."""

from __future__ import annotations

import json
from pathlib import Path

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase17a_geometry_audit import (
    ARTIFACT_DIR_NAME,
    activate_reference,
    enable_geometry,
    run_phase_17a,
    select_geometry,
    start_geometry_search,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

ROOT = Path(__file__).resolve().parents[1]


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _json(relative: str) -> dict:
    return json.loads((ROOT / "src" / "physics_lab" / "physics" / relative).read_text(encoding="utf-8"))


def test_phase17a_catalogues_geometries_without_search() -> None:
    before = _prior()
    phase16 = _json("phase16e_frontier_artifacts/PHASE_16E_FRONTIER.json")
    tier3 = _json("phase16_tier3_search_artifacts/PHASE_16_TIER3_CATALOG.json")
    result = run_phase_17a(write_artifacts=True)
    after = _prior()
    assert before == after
    assert _json("phase16e_frontier_artifacts/PHASE_16E_FRONTIER.json") == phase16
    assert _json("phase16_tier3_search_artifacts/PHASE_16_TIER3_CATALOG.json") == tier3
    assert result["status"] == "OK"
    assert result["PHASE17A_STATUS"] == "COMPLETE"
    assert result["PHASE16_INTEGRITY_STATUS"] == "VERIFIED"
    assert result["FROZEN_ACTION_STATUS"] == "VERIFIED"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["SEARCH_STATUS"] == "NOT_STARTED"
    assert result["phase16_recorded_state"]["registered_points"] == 69
    assert result["phase16_recorded_state"]["valid_models"] == 51
    assert result["phase16_recorded_state"]["verified_PFR"] == 0
    references = result["geometry_reference_catalog"]
    candidates = {item["geometry_id"]: item for item in result["geometry_candidate_catalog"]}
    assert [item["reference_id"] for item in references[:10]] == [f"G_REF_{index:02d}" for index in range(1, 11)]
    assert all(item["catalog_role"] == "REFERENCE_ONLY" and item["search_status"] == "NOT_ENABLED" for item in references)
    assert activate_reference("G_REF_01") == "NOT_ENABLED"
    assert enable_geometry("G17-05") == "NOT_ENABLED"
    assert start_geometry_search() == "NOT_STARTED"
    assert select_geometry(candidates) == "NOT_PERFORMED"
    assert all(item["search_status"] == "NOT_ENABLED" for item in candidates.values())
    assert all(item["equivalence_status"] == "EQUIVALENCE_UNRESOLVED" for item in result["geometric_equivalence_register"])
    assert candidates["G17-04"]["current_grammar_status"] == "EQUIVALENCE_UNRESOLVED"
    assert candidates["G17-02"]["equivalence_status"] == "EQUIVALENCE_UNRESOLVED"
    assert candidates["G17-03"]["fermions_added"] is False
    assert candidates["G17-03"]["matter_content_included"] is False
    assert candidates["G17-05"]["dynamics_included"] is False
    assert candidates["G17-08"]["compactification_defined"] is False
    assert candidates["G17-10"]["topological_sector_selected"] is False
    assert candidates["G17-10"]["numerical_topological_value"] == "NOT_ASSIGNED"
    assert candidates["G17-09"]["specific_manifold"] == "NONE"
    assert all("new_physical_input_required" in item for item in result["geometric_new_input_register"])
    assert all(item["finite_bounds"]["finite_bound_status"] in {"REQUIREMENTS_STATED", "CANNOT_YET_BE_BOUNDED"} for item in candidates.values())
    assert candidates["G17-12"]["finite_bounds"]["finite_bound_status"] == "CANNOT_YET_BE_BOUNDED"
    assert result["selected_geometry"] == "NONE"
    assert result["ranking_function"] == "ABSENT"
    assert all(item["status"] == "NOT_AUTHORIZED" for item in result["geometry_human_authorization_frontier"])
