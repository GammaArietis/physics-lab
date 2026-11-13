"""Phase 14B binds axes to stored action components and adds no terms."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase12c import GRAMMAR_VERSION
from physics_lab.theory_kernel.phase14b_binding import ARTIFACT_DIR_NAME, _physics_dir, run_phase_14b
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase14b_materializes_only_from_stored_components() -> None:
    before = _prior()
    result = run_phase_14b(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_14B_STATUS"] == "COMPLETE"
    assert result["ACTION_TEMPLATE_STATUS"] == "VERIFIED"
    assert result["ACTION_COMPONENT_REGISTRY_STATUS"] == "VERIFIED"
    assert result["AXIS_SLOT_BINDING_STATUS"] == "PARTIAL"
    assert result["FIELD_CONTENT_BINDING_STATUS"] == "PARTIAL"
    assert result["GAUGE_BINDING_STATUS"] == "UNRESOLVED"
    assert result["INTERNAL_OPERATOR_BINDING_STATUS"] == "PARTIAL"
    assert result["PARAMETER_IDENTITY_STATUS"] == "HUMAN-AUTHORIZED"
    assert result["ACTION_MATERIALIZATION_STATUS"] == "PARTIAL"
    assert result["NEW_INTEGRAND"] is False
    assert result["NEW_PARAMETER_COUNT"] == 0
    assert result["NEW_PHYSICAL_CONTENT"] == "NONE"
    assert result["T09_STATUS"] == "DISABLED"
    assert result["T10_STATUS"] == "DISABLED"
    assert result["EOM_EXECUTED"] is False
    assert result["SEARCH_EXECUTED"] is False
    assert result["FROZEN_STATE_STATUS"] == "VERIFIED"
    assert result["REPRODUCIBILITY_STATUS"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["grammar_version"] == GRAMMAR_VERSION
    assert result["NUMBER_OF_THEORIES_PROCESSED"] == 8
    assert result["NUMBER_OF_COMPLETE_ACTIONS"] == 0
    assert result["NUMBER_OF_PARTIAL_ACTIONS"] == 4
    assert result["NUMBER_OF_UNRESOLVED_ACTIONS"] == 4
    assert result["CERTIFIED_AXIS_ACTION_BINDINGS"] == 4
    assert result["PARTIAL_AXIS_ACTION_BINDINGS"] == 20
    assert result["NO_BINDING_AXIS_ACTION_BINDINGS"] == 64
    assert result["UNRESOLVED_AXIS_ACTION_BINDINGS"] == 0
    actions = result["MATERIALIZATION"]["actions"]
    partial = [item for item in actions if item["status"] == "PARTIAL"]
    unresolved = [item for item in actions if item["status"] == "UNRESOLVED"]
    assert len(partial) == 4
    assert len(unresolved) == 4
    assert all(item["included_terms"] == [] for item in actions)
    assert all(item["persisted"] is False for item in actions)
    assert all(item["materialized_action_hash"] != FROZEN_4C_HASH for item in partial)
    assert all("materialized_action_hash" not in item for item in unresolved)
    bindings = result["MATERIALIZATION"]["bindings"]
    certified = [item for item in bindings if item["binding_status"] == "CERTIFIED_BINDING"]
    assert {item["selected_value"] for item in certified} == {"metric_plus_internal_Phi"}
    assert all(item["derived_without_assumption"] is False for item in certified)
    assert all(item["binding_status"] == "NO_BINDING" for item in bindings if item["selected_value"] == "function_of_KTK")
    assert all(item["binding_status"] == "PARTIAL_BINDING" for item in bindings if item["selected_value"] == "commutant_symmetric_K")
    assert all(item["binding_status"] == "NO_BINDING" for item in bindings if item["slot"] == "GAUGE_SLOT")
    assert all(item["f2_introduced"] is False for item in bindings if item["slot"] == "GAUGE_SLOT")
    assert all(item["explicit_correspondence"] is False for item in bindings if item["slot"] == "GAUGE_SLOT")
    identities = result["MATERIALIZATION"]["identities"]
    assert all(item.get("physical_relation") != "DERIVED" for item in identities)
    assert result["MATERIALIZATION"]["operator_test"]["action_expression_identity"] == "NOT_INFERRED"
    assert result["MATERIALIZATION"]["operator_test"]["merged_with_lexicon"] is False
    assert len(result["dry_run_negatives"]) == 17
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_14B_ACTION_TEMPLATE.json",
        "PHASE_14B_ACTION_COMPONENT_REGISTRY.json",
        "PHASE_14B_AXIS_SLOT_BINDINGS.json",
        "PHASE_14B_MATERIALIZED_ACTIONS.json",
        "PHASE_14B_PARAMETER_AUDIT.json",
        "PHASE_14B_FRONTIER.json",
        "SEARCH_MANIFEST_14B.json",
    ):
        assert (destination / name).is_file()
