"""Phase 13C closure tests. The Phase 13B catalogue is not regenerated."""

from __future__ import annotations

import json

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase13c_closure import (
    ARTIFACT_DIR_NAME,
    _physics_dir,
    run_phase_13c,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {
        key: value
        for key, value in snapshot_existing_phases().items()
        if not key.startswith(ARTIFACT_DIR_NAME)
    }


def test_phase13c_certifies_the_fixed_catalogue() -> None:
    before = _prior()
    catalogue_path = _physics_dir() / "phase13b_exploration_artifacts" / "PHASE_13B_EXPLORATION.json"
    stored = json.loads(catalogue_path.read_text(encoding="utf-8"))
    result = run_phase_13c(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_13C_STATUS"] == "COMPLETE"
    assert result["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert result["REPRODUCIBILITY_STATUS"] == "VERIFIED"
    assert result["T09_STATUS"] == "DISABLED"
    assert result["T10_STATUS"] == "DISABLED"
    assert result["new_theory_generated"] is False
    assert result["new_grammar_generated"] is False
    assert result["new_primitive_added"] is False
    assert result["new_physical_principle_activated"] is False
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["source_catalogue_hash"] == stored["INTEGRITY_REPORT"]["catalogue_hash"]
    assert result["PYTEST_STATUS"] == "GREEN"
    summary = result["summary"]
    assert summary["TOTAL_THEORIES_PROCESSED"] == 8
    assert summary["TOTAL_THEORIES_MATHEMATICALLY_WELL_DEFINED"] == 8
    assert summary["TOTAL_ACTIONS_DERIVED"] == 0
    assert summary["TOTAL_MASS_MATRICES_DERIVED"] == 8
    assert summary["TOTAL_MASS_RATIOS_DERIVED"] == 0
    assert summary["TOTAL_PARAMETER_DEPENDENT_MASS_RATIOS"] == 8
    assert summary["TOTAL_CHARGE_STRUCTURES_DERIVED"] == 8
    assert summary["TOTAL_GAUGE_COUPLING_STRUCTURES_DERIVED"] == 0
    assert summary["TOTAL_DIMENSIONLESS_QUANTITIES"] == 8
    assert summary["TOTAL_PFR_CANDIDATES"] == 16
    assert summary["TOTAL_PFR_CANDIDATES"] == stored["counts"]["total_PFR_candidates"]
    assert summary["TOTAL_VERIFIED_PFR"] == 0
    assert summary["TOTAL_OPEN_PROOF_OBLIGATIONS"] == 56
    assert summary["TOTAL_OPEN_PROOF_OBLIGATIONS"] == stored["counts"]["total_open_proof_obligations"]
    assert summary["TOTAL_CLOSED_PROOF_OBLIGATIONS"] == 0
    assert summary["TOTAL_EQUIVALENCE_CLASSES"] == 8
    assert summary["TOTAL_REQUIRES_HUMAN_INPUT"] == 16
    assert len(result["dry_run"]) == 24
    assert [item["observed"] for item in result["dry_run"]] == [item["expected"] for item in result["dry_run"]]
    assert len(result["DERIVATION"]) == 8
    assert {item["theory_id"] for item in result["DERIVATION"]} == {item["theory_id"] for item in stored["THEORY_CATALOGUE"]}
    assert all(item["mass"]["generated_mass"] is False for item in result["DERIVATION"])
    assert all(item["mass"]["mass_ratio"]["parameters_cancel"] is False for item in result["DERIVATION"])
    assert all(item["gauge"]["g_phys"] == "NOT_DEFINED" for item in result["DERIVATION"])
    assert all(item["action"]["euler_lagrange"] == "UNTESTED" for item in result["DERIVATION"])
    assert all(item["vacuum"]["status"] == "REQUIRES_HUMAN_INPUT" for item in result["DERIVATION"])
    assert all(item["certification"]["PHYSICALLY_CERTIFIED"] is False for item in result["DERIVATION"])
    assert any(item["gauge"]["Z_A_retained"] is True for item in result["DERIVATION"])
    assert any(item["mass"]["mass_ratio"]["expression"] == "lambda_a/lambda_b" for item in result["DERIVATION"])
    assert any(item["mass"]["mass_ratio"]["expression"] == "a0/(a0 + a1)" for item in result["DERIVATION"])
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_13C_DERIVATION.json",
        "PHASE_13C_PROOF_CLOSURE.json",
        "PHASE_13C_PARAMETER_CLOSURE.json",
        "PHASE_13C_MASS_AUDIT.json",
        "PHASE_13C_CHARGE_COUPLING_AUDIT.json",
        "PHASE_13C_DIMENSIONAL_AUDIT.json",
        "PHASE_13C_EQUIVALENCE_AUDIT.json",
        "PHASE_13C_FRONTIER.json",
        "SEARCH_MANIFEST_13C.json",
    ):
        assert (destination / name).is_file()
    pairs = json.loads((destination / "PHASE_13C_EQUIVALENCE_AUDIT.json").read_text(encoding="utf-8"))
    assert len(pairs["pairs"]) == 28
    assert all(item["outcome"] == "EQUIVALENCE_UNSUPPORTED" for item in pairs["pairs"])
