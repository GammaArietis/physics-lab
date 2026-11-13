"""Phase 14H audits stored gauge sources and does not repair them."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase14h_source_audit import ARTIFACT_DIR_NAME, _physics_dir, run_phase_14h
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase14h_finds_the_source_boundary() -> None:
    before = _prior()
    result = run_phase_14h(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_14H_STATUS"] == "COMPLETE"
    assert result["CASE"] == "B"
    assert result["SOURCE_ACTION_STATUS"] == "EXPANSION_FRAGMENT"
    assert result["COVARIANT_KINETIC_SOURCE_STATUS"] == "ABSENT"
    assert result["EXPANSION_CONSISTENCY_STATUS"] == "INCOMPLETE"
    assert result["CURRENT_DEFINITION_STATUS"] == "EXPLICIT"
    assert result["CONNECTION_TERM_STATUS"] == "PARTIAL"
    assert result["F2_SOURCE_STATUS"] == "PARTIAL"
    assert result["F2_A_MU_DEPENDENCY_STATUS"] == "UNDECLARED"
    assert result["SOURCE_FIELD_INVENTORY_STATUS"] == "VERIFIED"
    assert result["SOURCE_PARAMETER_INVENTORY_STATUS"] == "VERIFIED"
    assert result["EMBEDDING_STATUS"] == "FRAGMENT_EMBEDDED"
    assert result["MATERIALIZED_DYNAMICAL_ACTION_STATUS"] == "PARTIAL"
    assert result["MISSING_COMPLETE_KINETIC_SOURCE"] is True
    assert result["ACTION_DERIVATION_READY"] is False
    assert result["CURRENT_ACTION_SOURCE_BOUNDARY"] is True
    assert result["NEW_INTEGRAND"] is False
    assert result["NEW_PARAMETER_COUNT"] == 0
    assert result["NEW_FIELD_COUNT"] == 0
    assert result["NEW_PHYSICAL_CONTENT"] == "NONE"
    assert result["T09_STATUS"] == "DISABLED"
    assert result["T10_STATUS"] == "DISABLED"
    assert result["EOM_EXECUTED"] is False
    assert result["LEAN_EXECUTED"] is False
    assert result["SEARCH_EXECUTED"] is False
    assert result["REPRODUCIBILITY_STATUS"] == "VERIFIED"
    assert result["FROZEN_STATE_STATUS"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    audit = result["audit"]
    assert audit["gauge"]["name_implies_complete"] is False
    assert audit["gauge"]["parent_kinetic_density"] == "ABSENT"
    assert audit["gauge"]["stress_tensor_is_action_density"] is False
    assert audit["gauge"]["current"]["gauged_action_noether"] == "NOT_DERIVED"
    assert audit["gauge"]["current"]["formula"].startswith("j^mu = 2 Z")
    assert audit["f2"]["dependency_not_upgraded"] is True
    assert audit["f2"]["complete_matter_action"] is False
    assert audit["lambda_a_in_source_expressions"] is False
    assert "mathcalA_mu" in audit["gauge"]["fields_undefined"]
    assert all(item["dynamical_action_status"] == "PARTIAL" for item in audit["comparisons"])
    assert len(audit["comparisons"]) == 4
    assert len(result["dry_run_negatives"]) == 18
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_14H_SOURCE_ACTION_AUDIT.json",
        "PHASE_14H_COVARIANT_KINETIC_AUDIT.json",
        "PHASE_14H_CURRENT_DEFINITION_AUDIT.json",
        "PHASE_14H_F2_SOURCE_AUDIT.json",
        "PHASE_14H_FIELD_INVENTORY.json",
        "PHASE_14H_PARAMETER_INVENTORY.json",
        "PHASE_14H_14F_COMPARISON.json",
        "PHASE_14H_FRONTIER.json",
        "SEARCH_MANIFEST_14H.json",
    ):
        assert (destination / name).is_file()
