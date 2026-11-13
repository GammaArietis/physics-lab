"""Phase 14K audits consistency of the verified Phase 14J equations."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase14j_eom import BRANCH_A_DIRECT, BRANCH_B_EQUATION, PHI_COMPONENT
from physics_lab.theory_kernel.phase14k_consistency import (
    ACTION_HASH_14I,
    ARTIFACT_DIR_NAME,
    _physics_dir,
    run_phase_14k,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase14k_audits_the_verified_equations() -> None:
    before = _prior()
    result = run_phase_14k(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_14K_STATUS"] == "COMPLETE"
    assert result["FREEZE_STATUS"] == "VERIFIED"
    assert result["ACTION_BINDING_STATUS"] == "VERIFIED"
    assert result["ACTION_HASH_14I_INPUT"] == ACTION_HASH_14I
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["FROZEN_ACTION_MODIFIED"] is False
    assert result["BRANCH_A_CONSISTENCY_STATUS"] == "VERIFIED"
    assert result["BRANCH_B_CONSISTENCY_STATUS"] == "VERIFIED"
    assert result["CURRENT_IDENTITY_STATUS"] == "VERIFIED"
    assert result["CONSERVATION_STATUS"] == "VERIFIED"
    assert result["METRIC_CONSISTENCY_STATUS"] == "VERIFIED"
    assert result["PRINCIPAL_SYMBOL_STATUS"] == "VERIFIED"
    assert result["CONSTRAINT_STATUS"] == "VERIFIED"
    assert result["OSTROGRADSKY_STATUS"] == "NOT_TRIGGERED"
    assert result["SYMMETRY_STATUS"] == "PENDING_REVERIFICATION"
    assert result["QUANTUM_STATUS"] == "UNTESTED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["BIANCHI_STATUS"] == "RETAINED_NOT_REDERIVED"
    science = result["science"]
    assert science["phi_component"] == PHI_COMPONENT
    assert science["branch_a_equation"] == BRANCH_A_DIRECT
    assert science["branch_b_equation"] == BRANCH_B_EQUATION
    assert science["parameters_fixed"] == []
    assert science["physical_dof_count"] == "NOT_PERFORMED"
    assert science["derived_relations"] == ["[K, H_int] = 0"]
    assert len(result["dry_run_negatives"]) == 20
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_14K_CURRENT_IDENTITY.json",
        "PHASE_14K_CONSTRAINTS.json",
        "PHASE_14K_CONSERVATION.json",
        "PHASE_14K_PROVENANCE.json",
        "PHASE_14K_FRONTIER.json",
        "SEARCH_MANIFEST_14K.json",
    ):
        assert (destination / name).is_file()
