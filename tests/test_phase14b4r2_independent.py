"""Independent G4R orbit-closure v2 checks."""

from __future__ import annotations

from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis, freeze_paths
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase12a_grammar import grammar_hash_12a
from physics_lab.physics.phase14b0_engine import EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14b4r_g4 import artifact_dir as phase14b4r_artifact_dir
from physics_lab.physics.phase14b4r2_g4 import analyze_phase14b4r2_g4
from physics_lab.physics.phase14b5_g5 import artifact_dir as phase14b5_artifact_dir
from physics_lab.physics.phase14b6_g6 import artifact_dir as phase14b6_artifact_dir


def test_independent_orbit_closure_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_12a = grammar_hash_12a()
    before_g4r = (phase14b4r_artifact_dir() / "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV_R1.json").read_bytes()
    before_g5 = (phase14b5_artifact_dir() / "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json").read_bytes()
    before_g6 = (phase14b6_artifact_dir() / "closure_checkpoint_G6_STRUCTURAL_GAUGE_CONSISTENCY.json").read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase14b4r2_g4(auth)
    assert freeze_path.read_bytes() == before_freeze
    assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
    assert (phase14b4r_artifact_dir() / "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV_R1.json").read_bytes() == before_g4r
    assert (phase14b5_artifact_dir() / "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json").read_bytes() == before_g5
    assert (phase14b6_artifact_dir() / "closure_checkpoint_G6_STRUCTURAL_GAUGE_CONSISTENCY.json").read_bytes() == before_g6
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["G4R_CLOSURE"] == "PARTIAL"
    assert sci["gravity_changed"] is False
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    assert sci["sampling_promoted_to_COMPLETE"] is False
