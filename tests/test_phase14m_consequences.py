"""Phase 14M audits consequences of the verified symmetry."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase14k_consistency import ACTION_HASH_14I
from physics_lab.theory_kernel.phase14m_consequences import ARTIFACT_DIR_NAME, _physics_dir, run_phase_14m
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase14m_audits_symmetry_consequences() -> None:
    before = _prior()
    result = run_phase_14m(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_14M_STATUS"] == "COMPLETE"
    assert result["ACTION_BINDING_STATUS"] == "VERIFIED"
    assert result["ACTION_HASH_14I_INPUT"] == ACTION_HASH_14I
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["FROZEN_ACTION_MODIFIED"] is False
    assert result["GLOBAL_SYMMETRY_CONSEQUENCES_STATUS"] == "VERIFIED"
    assert result["LOCAL_GAUGE_CONSEQUENCES_STATUS"] == "VERIFIED"
    assert result["CURRENT_RELATION_STATUS"] == "VERIFIED"
    assert result["CURRENT_CONSERVATION_STATUS"] == "VERIFIED"
    assert result["GAUGE_IDENTITY_STATUS"] == "VERIFIED"
    assert result["BASIS_INVARIANCE_STATUS"] == "VERIFIED"
    assert result["GAUGE_INVARIANT_CLASSIFICATION_STATUS"] == "VERIFIED"
    assert result["PARAMETER_DEPENDENCE_STATUS"] == "VERIFIED"
    assert result["QUANTUM_STATUS"] == "UNTESTED"
    assert result["NOETHER_CHARGE_STATUS"] == "UNTESTED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["science"]["gauge_fixing"] == "NOT_INTRODUCED"
    assert result["science"]["absolute_coupling"] == "NOT_DETERMINED"
    assert result["science"]["parameters_fixed"] == []
    assert len(result["dry_run_negatives"]) == 23
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_14M_CURRENTS.json",
        "PHASE_14M_IDENTITIES.json",
        "PHASE_14M_CLASSIFICATION.json",
        "PHASE_14M_PROVENANCE.json",
        "PHASE_14M_FRONTIER.json",
        "SEARCH_MANIFEST_14M.json",
    ):
        assert (destination / name).is_file()
