"""Phase 11AE.3: Coleman-Weinberg on the four T10 moduli points."""

from __future__ import annotations

from physics_lab.physics.phase4c_action_freeze import freeze_paths
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11ae3_discrete_vacuum import run_phase_11AE_3_execution


def test_sign_flip_makes_the_loop_potential_nonreal():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    out = run_phase_11AE_3_execution(write_artifacts=True)
    assert freeze_path.read_bytes() == before
    assert out["status"] == "OK"
    assert out["T09_STATUS"] == "UNFROZEN"
    assert out["T10_reexecuted"] is False
    assert out["simultaneous_activation"] is False
    assert out["functional_provenance"] == "ASSUMED"
    assert out["new_parameter_count"] == 0
    assert out["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert out["admissible_space_count"] == 4
    assert out["provenance_log"][0]["T09_STATUS"] == "UNFROZEN"
    assert out["provenance_log"][1]["rule"] == "Target-Blind rule"
    assert out["provenance_log"][1]["closure_target"] == "SINGLE_VACUUM"
    assert out["provenance_log"][1]["logged_before_logical_execution"] is True
    evaluation = out["evaluation"]
    assert evaluation["ill_defined_for_some_signs"] is True
    assert evaluation["real_values_match_across_c_H_sign"] is True
    assert evaluation["selection_is_unique"] is False
    by_branch = {}
    for row in evaluation["rows"]:
        by_branch.setdefault(row["c_H_sign"], []).append(row)
    real_positive = [row["lambda_signs"] for row in by_branch[1] if row["real_spectrum"]]
    real_negative = [row["lambda_signs"] for row in by_branch[-1] if row["real_spectrum"]]
    assert real_positive == [[-1, -1]]
    assert real_negative == [[1, 1]]
    mixed = [row for row in evaluation["rows"] if row["lambda_signs"][0] != row["lambda_signs"][1]]
    assert mixed
    assert all(row["complex_log"] is True and row["V_1loop"] == "NOT_REAL" for row in mixed)
    assert out["observed"] == "DOMAIN_UNREDUCED"
    assert out["objective_met"] is False
    assert out["PROGRAM_CLOSURE_STATUS"] == "DOMAIN_UNREDUCED"
