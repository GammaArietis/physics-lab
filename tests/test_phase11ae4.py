"""Phase 11AE.4: T09 closes on one Z_2 parity class."""

from __future__ import annotations

from physics_lab.physics.phase4c_action_freeze import freeze_paths
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11ae4_degenerate_vacuum import (
    CLOSURE_TARGET,
    T09_STATUS,
    run_phase_11AE_4_synthesis,
)
from physics_lab.physics.phase11ag_abfi_operators import T09_STATUS as FROZEN_T09


def test_t09_closes_on_the_parity_class():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    gate = phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json"
    gate_before = gate.read_bytes()
    out = run_phase_11AE_4_synthesis(write_artifacts=True)
    assert freeze_path.read_bytes() == before
    assert gate.read_bytes() == gate_before
    assert FROZEN_T09 == "FROZEN_SYMMETRY_RESIDUAL"
    assert T09_STATUS == "UNFROZEN"
    assert out["status"] == "OK"
    assert out["provenance_log"][0]["T09_STATUS"] == "UNFROZEN"
    assert out["provenance_log"][0]["T10_reexecuted"] is False
    assert out["provenance_log"][0]["T11_activated"] is False
    assert out["provenance_log"][1]["rule"] == "Target-Blind rule"
    assert out["provenance_log"][1]["closure_target"] == CLOSURE_TARGET == "DEGENERATE_CLASS"
    assert out["provenance_log"][1]["logged_before_logical_execution"] is True
    entries = [item["entry"] for item in out["provenance_log"]]
    assert entries.index("Pre-Execution Closure Criterion") < entries.index("vacuum synthesis")
    synthesis = out["synthesis"]
    assert synthesis["moduli_fixed_at_finite_value"] is True
    assert synthesis["t10_solution_count"] == 4
    assert synthesis["mixed_tachyonic_states_eliminated"] is True
    assert synthesis["quadratic_doublet_invariant"] is True
    assert synthesis["equivalence_class_count"] == 1
    assert synthesis["class_size"] == 2
    assert synthesis["symmetry"] == "Z_2"
    assert synthesis["surviving_class"] == [[-1, -1], [1, 1]]
    assert synthesis["V_adm"] == "Z_2 parity class of the same-sign moduli"
    assert out["new_parameter_count"] == 0
    assert out["frozen_action_modified"] is False
    assert out["parent_records_modified"] is False
    assert out["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert out["simultaneous_activation"] is False
    assert out["observed"] == "DEGENERATE_CLASS"
    assert out["objective_met"] is True
    assert out["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert out["T09_STATUS"] == "CLOSED"
    assert out["VACUUM_SELECTION_PRINCIPLE"] == "COMPLETED"
    assert out["closure_comparison"]["completion"] == "degenerate parity vacuum"
    assert out["laboratory_state"]["parent_11AD_decision_unchanged"] is True
    assert out["closure_comparison"]["closure_target_used_as_filter"] is False
