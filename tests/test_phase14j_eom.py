"""Phase 14J derives classical equations from the completed Phase 14I test action."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase14j_eom import (
    ALGEBRAIC,
    ARTIFACT_DIR_NAME,
    BRANCH_A_DIRECT,
    BRANCH_B_EQUATION,
    PHI_COMPONENT,
    _physics_dir,
    run_phase_14j,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase14j_derives_the_completed_action() -> None:
    before = _prior()
    result = run_phase_14j(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_14J_STATUS"] == "COMPLETE"
    assert result["FREEZE_STATUS"] == "VERIFIED"
    assert result["ACTION_BINDING_STATUS"] == "VERIFIED"
    assert result["BRANCH_A_EOM_STATUS"] == "VERIFIED"
    assert result["BRANCH_B_EOM_STATUS"] == "VERIFIED"
    assert result["METRIC_EOM_STATUS"] == "VERIFIED"
    assert result["STRESS_ENERGY_STATUS"] == "VERIFIED"
    assert result["EOM_ORDER_STATUS"] == "VERIFIED"
    assert result["F2_DEPENDENCY_STATUS"] == "VERIFIED"
    assert result["CONSERVATION_STATUS"] == "UNTESTED"
    assert result["OSTROGRADSKY_STATUS"] == "NOT_TRIGGERED"
    assert result["SYMMETRY_STATUS"] == "PENDING_REVERIFICATION"
    assert result["QUANTUM_STATUS"] == "UNTESTED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["FROZEN_ACTION_MODIFIED"] is False
    assert result["ATOMIC_GATE"] == "VERIFIED"
    assert result["CONCURRENCY_GUARD"] == "VERIFIED"
    assert result["CLASSICAL_EOM"] == "DERIVED"
    assert result["EOM_ORDER_PHI"] == "SECOND_ORDER"
    science = result["science"]
    assert science["phi_component"] == PHI_COMPONENT
    assert science["branch_a_equation"] == BRANCH_A_DIRECT
    assert science["branch_a_classification"] == ALGEBRAIC
    assert science["branch_b_equation"] == BRANCH_B_EQUATION
    assert science["quadratic_is_gauge_kinetic"] is False
    assert science["parameters_fixed"] == []
    branch_a = [item for item in result["actions"] if item["f2_term"] == "ABSENT"]
    branch_b = [item for item in result["actions"] if item["f2_term"] != "ABSENT"]
    assert len(branch_a) == 2 and len(branch_b) == 2
    assert len(result["dry_run_negatives"]) == 24
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_14J_PHI_EOM.json",
        "PHASE_14J_CONNECTION_EOM.json",
        "PHASE_14J_METRIC_EOM.json",
        "PHASE_14J_ORDER_AUDIT.json",
        "PHASE_14J_PROVENANCE.json",
        "PHASE_14J_FRONTIER.json",
        "SEARCH_MANIFEST_14J.json",
    ):
        assert (destination / name).is_file()
