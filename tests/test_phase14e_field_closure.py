"""Phase 14E audits field closure and does not rewrite the four test actions."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase14e_field_closure import ARTIFACT_DIR_NAME, _physics_dir, run_phase_14e
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase14e_audits_field_closure_without_changing_actions() -> None:
    before = _prior()
    result = run_phase_14e(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_14E_STATUS"] == "COMPLETE"
    assert result["CASE"] == "B"
    assert result["FIELD_INVENTORY_STATUS"] == "VERIFIED"
    assert result["FIELD_TERM_CONSISTENCY_STATUS"] == "PARTIAL"
    assert result["FIELD_ROLE_STATUS"] == "PARTIAL"
    assert result["GAUGE_FIELD_CLOSURE_STATUS"] == "PARTIAL"
    assert result["F2_FIELD_CLOSURE_STATUS"] == "PARTIAL"
    assert result["F2_A_MU_DEPENDENCY_STATUS"] == "UNDECLARED"
    assert result["PARAMETER_CLOSURE_STATUS"] == "PARTIAL"
    assert result["ACTION_CLOSURE_STATUS"] == "PARTIAL"
    assert result["EOM_PRECONDITION_STATUS"] == "NOT_SATISFIED"
    assert result["EOM_EXECUTED"] is False
    assert result["SEARCH_EXECUTED"] is False
    assert result["NEW_FIELD_COUNT"] == 0
    assert result["NEW_PARAMETER_COUNT"] == 0
    assert result["NEW_INTEGRAND_COUNT"] == 0
    assert result["NEW_PHYSICAL_CONTENT"] == "NONE"
    assert result["T09_STATUS"] == "DISABLED"
    assert result["T10_STATUS"] == "DISABLED"
    assert result["FROZEN_STATE_STATUS"] == "VERIFIED"
    assert result["REPRODUCIBILITY_STATUS"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["COMPLETE_ACTIONS_READY_FOR_EOM"] == 0
    assert result["ACTIONS_BLOCKED_BY_FIELD_CLOSURE"] == 4
    assert result["ACTIONS_WITH_UNDECLARED_GAUGE_DEPENDENCY"] == 2
    rows = result["AUDIT"]["rows"]
    assert len(rows) == 4
    assert all(item["declared_fields"] == ["Phi", "metric"] for item in rows)
    assert all(item["fields_in_action_expression"] == ["Phi"] for item in rows)
    assert all(item["source_action_hash"] == item["current_action_hash"] == item["action_hash"] for item in rows)
    assert all(item["eom_precondition"] == "NOT_SATISFIED" for item in rows)
    assert all(item["action_closure_status"] == "PARTIAL" for item in rows)
    assert all("mathcalA_mu" not in item["declared_fields"] for item in rows)
    connection = [item for item in rows if item["gauge_field_status"] == "OMITTED_FROM_ACTION_EXPRESSION"]
    f2 = [item for item in rows if item["f2_status"] == "PRESENT_IN_REFERENCED_COMPONENT_OMITTED_FROM_EXPRESSION"]
    assert len(connection) == 2
    assert len(f2) == 2
    assert all(item["missing_fields"] == ["mathcalA_mu"] for item in connection)
    assert all(item["missing_fields"] == ["F_mu_nu"] for item in f2)
    assert all(item["gauge_field_status"] == "UNRESOLVED" for item in f2)
    assert all(item["f2_a_mu_dependency"] == "UNDECLARED" for item in rows)
    assert result["gauge_records"]["explicit_field_mathcalA_mu"] is False
    assert result["gauge_records"]["f2_dependency"] == "UNDECLARED"
    assert all(item["role"] == "GAUGE CONNECTION" for item in rows[0]["field_roles"] if item["field"] == "mathcalA_mu")
    assert len(result["dry_run_negatives"]) == 14
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_14E_FIELD_INVENTORY.json",
        "PHASE_14E_FIELD_ROLE_AUDIT.json",
        "PHASE_14E_F2_DEPENDENCY_AUDIT.json",
        "PHASE_14E_PARAMETER_AUDIT.json",
        "PHASE_14E_ACTION_CLOSURE.json",
        "PHASE_14E_FRONTIER.json",
        "SEARCH_MANIFEST_14E.json",
    ):
        assert (destination / name).is_file()
