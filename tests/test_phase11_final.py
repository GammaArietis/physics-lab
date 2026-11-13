"""Phase 11 final closure records the outcomes already obtained."""

from __future__ import annotations

from physics_lab.physics.phase4c_action_freeze import freeze_paths
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11_final_closure import PROGRAM_STATUS, run_phase_11_synthesis


def test_phase_11_closes_with_the_recorded_outcomes():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    out = run_phase_11_synthesis(write_artifacts=True)
    assert freeze_path.read_bytes() == before
    assert out["status"] == "OK"
    assert out["PROGRAM_CLOSURE_STATUS"] == PROGRAM_STATUS == "PHASE_11_CLOSED_UNDER_DECLARED_SCOPE"
    assert out["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert out["frozen_action_modified"] is False
    assert out["new_parameter_count"] == 0
    assert out["T12_observed"] == "RELATION_NOT_DERIVED"
    assert out["topics"]["T10"]["outcome"] == "SUCCESS"
    assert out["topics"]["T09"]["outcome"] == "SUCCESS"
    assert out["topics"]["T09"]["observed"] == "DEGENERATE_CLASS"
    assert out["topics"]["T06"]["outcome"] == "FAILED"
    assert out["topics"]["T07"]["outcome"] == "FAILED"
    assert out["topics"]["T08"]["outcome"] == "FAILED"
    assert out["topics"]["T12"]["outcome"] == "FAILED"
    assert out["topics"]["T12"]["observed"] == "RELATION_NOT_DERIVED"
    assert len(out["laboratory_hash"]) == 64
    repeat = run_phase_11_synthesis(write_artifacts=False)
    assert repeat["laboratory_hash"] == out["laboratory_hash"]
    assert repeat["action_content_hash"] == out["action_content_hash"]
