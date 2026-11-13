"""Phase 14G derives stored consequences and leaves the Phase 14F actions unchanged."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase14g_derivation import (
    ARTIFACT_DIR_NAME,
    CONNECTION_EQUATION,
    POTENTIAL_EQUATION,
    QUADRATIC_PHI_EQUATION,
    _physics_dir,
    run_phase_14g,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase14g_derives_only_stored_action_content() -> None:
    before = _prior()
    result = run_phase_14g(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_14G_STATUS"] == "COMPLETE"
    assert result["EULER_LAGRANGE_STATUS"] == "PARTIAL"
    assert result["PHI_EOM_STATUS"] == "PARTIAL"
    assert result["CONNECTION_VARIATION_STATUS"] == "PARTIAL"
    assert result["METRIC_VARIATION_STATUS"] == "PARTIAL"
    assert result["SYMMETRY_STATUS"] == "UNTESTED"
    assert result["NOETHER_STATUS"] == "UNTESTED"
    assert result["MASS_OPERATOR_STATUS"] == "VERIFIED"
    assert result["CHARGE_STRUCTURE_STATUS"] == "UNTESTED"
    assert result["GAUGE_DEPENDENCY_STATUS"] == "UNDECLARED"
    assert result["PFR_STATUS"] == "NONE_FOUND"
    assert result["DIMENSIONAL_SCALE_STATUS"] == "PARTIAL"
    assert result["PARAMETER_CLOSURE_STATUS"] == "PARTIAL"
    assert result["PROOF_CLOSURE_STATUS"] == "PARTIAL"
    assert result["COMPLETE_EOM_COUNT"] == 0
    assert result["PARTIAL_EOM_COUNT"] == 12
    assert result["UNTESTED_EOM_COUNT"] == 2
    assert result["VERIFIED_SYMMETRY_COUNT"] == 0
    assert result["VERIFIED_PFR_COUNT"] == 0
    assert result["NEW_PARAMETER_COUNT"] == 0
    assert result["NEW_INTEGRAND_COUNT"] == 0
    assert result["NEW_PHYSICAL_CONTENT"] == "NONE"
    assert result["T09_STATUS"] == "DISABLED"
    assert result["T10_STATUS"] == "DISABLED"
    assert result["SEARCH_EXECUTED"] is False
    assert result["EXPERIMENTAL_INPUT"] is False
    assert result["REPRODUCIBILITY_STATUS"] == "VERIFIED"
    assert result["FROZEN_STATE_STATUS"] == "VERIFIED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["frozen_4c_hash"] == FROZEN_4C_HASH
    assert result["TOTAL_THEORIES"] == 4
    assert result["TOTAL_COMPLETE_EOMS"] == 0
    assert result["TOTAL_PARTIAL_EOMS"] == 12
    assert result["TOTAL_UNTESTED_EOMS"] == 2
    assert result["TOTAL_VERIFIED_SYMMETRIES"] == 0
    assert result["TOTAL_VERIFIED_PFR"] == 0
    assert result["TOTAL_PARAMETER_DEPENDENT_RATIOS"] == 4
    assert result["TOTAL_OPEN_PROOF_OBLIGATIONS"] == 28
    assert result["TOTAL_UNRESOLVED_GAUGE_DEPENDENCIES"] == 2
    rows = result["rows"]
    assert len(rows) == 4
    assert all(item["Phi_EOM"]["equation"] == f"{POTENTIAL_EQUATION} + {QUADRATIC_PHI_EQUATION}" for item in rows)
    assert all(item["Phi_EOM"]["second_order_piece"] == "UNTESTED" for item in rows)
    assert all(item["connection_variation"]["equation"] == CONNECTION_EQUATION for item in rows)
    assert all(item["connection_variation"]["propagation"] is False for item in rows)
    assert all(item["operator_diagonal"] == ["lam_a", "lam_b", "lam_b"] for item in rows)
    assert all(item["mass_operator"]["physical_mass"] is False for item in rows)
    assert all(item["phase10d_merged_with_lexicon"] is False for item in rows)
    assert all(item["physical_certification"] == "NOT_CLAIMED" for item in rows)
    f2 = [item for item in rows if item["f2"]["status"] == "UNTESTED"]
    plain = [item for item in rows if item["f2"]["status"] == "NOT_APPLICABLE"]
    assert len(f2) == 2 and len(plain) == 2
    assert all(item["f2"]["gauge_eom"] == "NOT_DERIVED" for item in f2)
    assert all("Z_A" in [row["parameter_id"] for row in item["parameters"]] for item in f2)
    assert all("Z_A" not in [row["parameter_id"] for row in item["parameters"]] for item in plain)
    assert all(item["dimensional"]["derived_absolute_scale"] == "NOT_DERIVED" for item in rows)
    assert len(result["dry_run_negatives"]) == 21
    assert [item["observed"] for item in result["dry_run_negatives"]] == [item["expected"] for item in result["dry_run_negatives"]]
    destination = _physics_dir() / ARTIFACT_DIR_NAME
    for name in (
        "PHASE_14G_EULER_LAGRANGE.json",
        "PHASE_14G_METRIC_VARIATION.json",
        "PHASE_14G_SYMMETRY_AUDIT.json",
        "PHASE_14G_NOETHER.json",
        "PHASE_14G_MASS_OPERATOR.json",
        "PHASE_14G_PARAMETER_CLOSURE.json",
        "PHASE_14G_PFR_AUDIT.json",
        "PHASE_14G_DIMENSIONAL_AUDIT.json",
        "PHASE_14G_GAUGE_DEPENDENCY.json",
        "PHASE_14G_PROOF_CLOSURE.json",
        "PHASE_14G_FRONTIER.json",
        "SEARCH_MANIFEST_14G.json",
    ):
        assert (destination / name).is_file()
