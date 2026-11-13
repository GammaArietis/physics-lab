"""Phase 14C prepares slot-binding requests and authorizes none of them."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase14c_authorization import (
    ARTIFACT_DIR_NAME,
    EXPECTED_LEXICON_HASH,
    _physics_dir,
    run_phase_14c,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase14c_prepares_unauthorized_binding_requests() -> None:
    before = _prior()
    result = run_phase_14c(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_14C_STATUS"] == "COMPLETE"
    assert result["ACTION_SLOT_MODEL_STATUS"] == "VERIFIED"
    assert result["GAUGE_BINDING_CANDIDATE_STATUS"] == "PARTIAL"
    assert result["OPERATOR_BINDING_CANDIDATE_STATUS"] == "PARTIAL"
    assert result["GRAVITY_BINDING_CANDIDATE_STATUS"] == "PARTIAL"
    assert result["MATTER_BINDING_CANDIDATE_STATUS"] == "PARTIAL"
    assert result["MATTER_SLOT_SEMANTICS"] == "REQUIRES_EXPLICIT_AUTHORIZATION"
    assert result["PARAMETER_IDENTITY_STATUS"] == "HUMAN-AUTHORIZED"
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
    assert result["LEXICON_HASH"] == EXPECTED_LEXICON_HASH
    assert result["READY_FOR_HUMAN_AUTHORIZATION_COUNT"] == 32
    assert result["NOT_READY_COUNT"] == 4
    assert result["REJECTED_COUNT"] == 0
    assert result["NUMBER_OF_THEORIES_READY_IF_AUTHORIZED"] == 4
    assert result["NUMBER_OF_THEORIES_REMAINING_PARTIAL"] == 4
    assert result["NUMBER_OF_THEORIES_REMAINING_UNRESOLVED"] == 0
    assert result["NUMBER_OF_MISSING_BINDINGS"] == 4
    requests = result["PACKAGE"]["requests"]
    assert all(item["authorization_status"] == "NOT_AUTHORIZED" for item in requests)
    assert all(item["new_integrand"] is False and item["new_parameter"] is False for item in requests)
    assert all(item["new_physical_content"] == "NONE" for item in requests)
    gravity = [item for item in requests if item["selected_value"] == "volume_plus_ricci"]
    assert len(gravity) == 8
    assert all(item["provenance_match"] is False and item["parameter_match"] is True for item in gravity)
    assert all(item["decision"] == "READY_FOR_HUMAN_AUTHORIZATION" for item in gravity)
    operators = [item for item in requests if item["target_slot"] == "INTERNAL_OPERATOR_SLOT"]
    assert all(item["exact_expression_match"] is False for item in operators)
    assert all(item["decision"] == "READY_FOR_HUMAN_AUTHORIZATION" for item in operators)
    function_rows = [item for item in operators if item["selected_value"] == "function_of_KTK"]
    assert all(item["parameter_match"] is False for item in function_rows)
    assert all("PHASE_10D_OPERATOR_FAMILY" in item["mathematical_equivalence_dependencies"] for item in function_rows)
    connection_fields = [item for item in requests if item["selected_value"] == "metric_Phi_plus_connection"]
    assert len(connection_fields) == 4
    assert all(item["decision"] == "NOT_READY" and item["field_match"] is False for item in connection_fields)
    certified_fields = [item for item in requests if item["selected_value"] == "metric_plus_internal_Phi"]
    assert len(certified_fields) == 4
    assert all(item["decision"] == "ALREADY_AUTHORIZED" and item["field_match"] is True for item in certified_fields)
    assert all(item["persisted"] is False and item["included_terms"] == [] for item in result["PACKAGE"]["dry_run"])
    assert {item["selected_value"] for item in result["DECISION_PACKAGE"]} == {
        "volume_plus_ricci",
        "commutant_symmetric_K",
        "function_of_KTK",
        "connection_without_autonomous_F2",
        "optional_F2_test_extension",
        "matter_kinetic+matter_phi_sq",
    }
    assert all(item["authorization_status"] == "NOT_AUTHORIZED" for item in result["DECISION_PACKAGE"])
    assert all(item["new_physical_content"] == "NONE" for item in result["DECISION_PACKAGE"])
    assert result["gauge_audit"]["connection"]["axis_named_in_module"] is False
    assert result["gauge_audit"]["optional"]["axis_named_in_module"] is False
    assert result["gauge_audit"]["optional"]["connection_dependence"] == "UNDECLARED"
    assert len(result["dry_run_negatives"]) == 17
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_14C_ACTION_SLOT_MODEL.json",
        "PHASE_14C_BINDING_REQUESTS.json",
        "PHASE_14C_GAUGE_BINDINGS.json",
        "PHASE_14C_OPERATOR_BINDINGS.json",
        "PHASE_14C_GRAVITY_BINDINGS.json",
        "PHASE_14C_MATTER_BINDINGS.json",
        "PHASE_14C_DECISION_PACKAGE.json",
        "PHASE_14C_FRONTIER.json",
        "SEARCH_MANIFEST_14C.json",
    ):
        assert (destination / name).is_file()
