"""Phase 14N separates constraint and evolution for the completed test action."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase14k_consistency import ACTION_HASH_14I
from physics_lab.theory_kernel.phase14n_constraints import ARTIFACT_DIR_NAME, _physics_dir, run_phase_14n
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase14n_separates_constraint_and_evolution() -> None:
    before = _prior()
    result = run_phase_14n(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_14N_STATUS"] == "COMPLETE"
    assert result["ACTION_BINDING_STATUS"] == "VERIFIED"
    assert result["ACTION_HASH_14I_INPUT"] == ACTION_HASH_14I
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["FROZEN_ACTION_MODIFIED"] is False
    assert result["PHI_SECTOR_STATUS"] == "VERIFIED"
    assert result["BRANCH_A_PROPAGATION_STATUS"] == "NON_PROPAGATING"
    assert result["BRANCH_B_PROPAGATION_STATUS"] == "CONSTRAINT_PLUS_EVOLUTION"
    assert result["CONSTRAINT_PRESERVATION"] == "PRESERVED"
    assert result["CONFIGURATION_COUNT_STATUS"] == "QUALIFIED"
    assert result["QUANTUM_STATUS"] == "UNTESTED"
    assert result["CURVED_CONSERVATION_STATUS"] == "UNTESTED"
    assert result["NOETHER_CHARGE_STATUS"] == "UNTESTED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["science"]["gauge_fixing"] == "NOT_INTRODUCED"
    assert result["science"]["dirac_reduction"] == "NOT_PERFORMED"
    assert result["science"]["parameters_fixed"] == []
    assert len(result["dry_run_negatives"]) == 20
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_14N_HESSIAN.json",
        "PHASE_14N_CONSTRAINTS.json",
        "PHASE_14N_PROPAGATION.json",
        "PHASE_14N_PROVENANCE.json",
        "PHASE_14N_FRONTIER.json",
        "SEARCH_MANIFEST_14N.json",
    ):
        assert (destination / name).is_file()
