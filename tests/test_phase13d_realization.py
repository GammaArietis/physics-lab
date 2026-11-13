"""Phase 13D realization tests. The eight catalogue theories stay fixed."""

from __future__ import annotations

import json

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase13d_realization import ARTIFACT_DIR_NAME, _physics_dir, run_phase_13d
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {
        key: value
        for key, value in snapshot_existing_phases().items()
        if not key.startswith(ARTIFACT_DIR_NAME)
    }


def test_phase13d_realizes_only_registered_components() -> None:
    before = _prior()
    result = run_phase_13d(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_13D_STATUS"] == "COMPLETE"
    assert result["T09_STATUS"] == "DISABLED"
    assert result["T10_STATUS"] == "DISABLED"
    assert result["new_theory_generated"] is False
    assert result["new_primitive_added"] is False
    assert result["new_physical_principle_activated"] is False
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    summary = result["summary"]
    assert summary["TOTAL_THEORIES_PROCESSED"] == 8
    assert summary["TOTAL_ACTIONS_RECONSTRUCTED"] == 0
    assert summary["TOTAL_ACTIONS_COMPLETE"] == 0
    assert summary["TOTAL_ACTIONS_PARTIAL"] == 0
    assert summary["TOTAL_ACTIONS_UNRESOLVED"] == 8
    assert summary["TOTAL_EOMS_DERIVED"] == 0
    assert summary["TOTAL_EXACT_SYMMETRIES_CERTIFIED"] == 0
    assert summary["TOTAL_MASS_MATRICES"] == 8
    assert summary["TOTAL_PARAMETER_DEPENDENT_MASS_RATIOS"] == 8
    assert summary["TOTAL_VERIFIED_PFR"] == 0
    assert summary["TOTAL_PROOF_OBLIGATIONS_VERIFIED"] == 0
    assert summary["TOTAL_PROOF_OBLIGATIONS_OPEN"] == 56
    assert summary["TOTAL_EQUIVALENCE_CLASSES"] == 8
    assert summary["TOTAL_EQUIVALENCE_UNSUPPORTED"] == 28
    assert summary["NEW_PARAMETER_COUNT"] == 0
    assert summary["TOTAL_HUMAN_INPUT_FRONTIERS"] == 24
    assert len(result["dry_run"]) == 25
    assert [item["observed"] for item in result["dry_run"]] == [item["expected"] for item in result["dry_run"]]
    assert all(item["action"]["status"] == "ACTION_RECONSTRUCTION_UNRESOLVED" for item in result["REALIZATION"])
    assert all(item["action"]["stop"] == "NEW_ASSEMBLY_RULE_REQUIRED" for item in result["REALIZATION"])
    assert all(item["eom"]["status"] == "UNTESTED" for item in result["REALIZATION"])
    assert all(item["mass"]["generated_mass"] is False for item in result["REALIZATION"])
    assert all(item["symmetry"]["exact_symmetry_certified"] is False for item in result["REALIZATION"])
    assert all(item["vacuum"]["selected_physical_vacuum"] == "NOT_DEFINED" for item in result["REALIZATION"])
    stored = json.loads(
        (_physics_dir() / "phase13b_exploration_artifacts" / "PHASE_13B_EXPLORATION.json").read_text(encoding="utf-8")
    )
    assert {item["theory_id"] for item in result["REALIZATION"]} == {item["theory_id"] for item in stored["THEORY_CATALOGUE"]}
    assert {item["theory_hash"] for item in result["REALIZATION"]} == {item["hash"] for item in stored["THEORY_CATALOGUE"]}
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_13D_ACTION_REALIZATION.json",
        "PHASE_13D_EOM_DERIVATION.json",
        "PHASE_13D_SYMMETRY_AUDIT.json",
        "PHASE_13D_GAUGE_AUDIT.json",
        "PHASE_13D_GRAVITY_AUDIT.json",
        "PHASE_13D_PARAMETER_CLOSURE.json",
        "PHASE_13D_PFR_AUDIT.json",
        "PHASE_13D_DIMENSIONAL_AUDIT.json",
        "PHASE_13D_EQUIVALENCE_AUDIT.json",
        "PHASE_13D_PROOF_CLOSURE.json",
        "PHASE_13D_FRONTIER.json",
        "SEARCH_MANIFEST_13D.json",
    ):
        assert (destination / name).is_file()
