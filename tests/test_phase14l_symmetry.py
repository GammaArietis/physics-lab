"""Phase 14L reverifies symmetry of the completed test action."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase14k_consistency import ACTION_HASH_14I
from physics_lab.theory_kernel.phase14l_symmetry import ARTIFACT_DIR_NAME, _physics_dir, run_phase_14l
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase14l_reverifies_the_completed_action() -> None:
    before = _prior()
    result = run_phase_14l(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_14L_STATUS"] == "COMPLETE"
    assert result["FREEZE_STATUS"] == "VERIFIED"
    assert result["ACTION_BINDING_STATUS"] == "VERIFIED"
    assert result["ACTION_HASH_14I_INPUT"] == ACTION_HASH_14I
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["FROZEN_ACTION_MODIFIED"] is False
    assert result["BRANCH_A_GLOBAL_SYMMETRY_STATUS"] == "EXACT"
    assert result["BRANCH_A_LOCAL_COVARIANCE_STATUS"] == "VERIFIED"
    assert result["BRANCH_B_GLOBAL_SYMMETRY_STATUS"] == "EXACT"
    assert result["BRANCH_B_LOCAL_GAUGE_STATUS"] == "EXACT"
    assert result["NOETHER_CURRENT_STATUS"] == "DIFFERENT"
    assert result["NOETHER_CHARGE_STATUS"] == "UNTESTED"
    assert result["GAUGE_IDENTITY_STATUS"] == "VERIFIED"
    assert result["BASIS_INVARIANCE_STATUS"] == "VERIFIED"
    assert result["PARAMETER_DEPENDENCE_STATUS"] == "VERIFIED"
    assert result["QUANTUM_STATUS"] == "UNTESTED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["science"]["current_comparison"] == "DIFFERENT"
    assert result["science"]["breaking_terms"] == []
    assert result["science"]["parameters_fixed"] == []
    assert len(result["dry_run_negatives"]) == 27
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_14L_GLOBAL.json",
        "PHASE_14L_LOCAL.json",
        "PHASE_14L_CURRENT.json",
        "PHASE_14L_PROVENANCE.json",
        "PHASE_14L_FRONTIER.json",
        "SEARCH_MANIFEST_14L.json",
    ):
        assert (destination / name).is_file()
