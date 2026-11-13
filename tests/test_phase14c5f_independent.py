"""Independent Phase 14C.5F checks."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis, freeze_paths, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase12a_grammar import grammar_hash_12a
from physics_lab.physics.phase14b0_engine import EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14c5d_p5d import EXPECTED_P5D_CHECKPOINT_DIGEST, p5d_checkpoint_path
from physics_lab.physics.phase14c5e_p5e import EXPECTED_P5E_CHECKPOINT_DIGEST, artifact_dir as phase14c5e_artifact_dir, p5e_checkpoint_path
from physics_lab.physics.phase14c5e1_p5e1 import EXPECTED_P5E1_CHECKPOINT_DIGEST, artifact_dir as phase14c5e1_artifact_dir, p5e1_checkpoint_path
from physics_lab.physics.phase14c5f_p5f import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_P5F_CHECKPOINT_DIGEST,
    analyze_phase14c5f_p5f,
    artifact_dir,
    g6_checkpoint_path,
    snapshot_prior_artifact_hashes,
)


def test_independent_14c5f_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_12a = grammar_hash_12a()
    before_prior = snapshot_prior_artifact_hashes()
    before_g6 = g6_checkpoint_path().read_bytes()
    before_p5d = p5d_checkpoint_path().read_bytes()
    before_p5e = p5e_checkpoint_path().read_bytes()
    before_p5e1 = p5e1_checkpoint_path().read_bytes()
    before_p5e_summary = (phase14c5e_artifact_dir() / "PHASE_14C5E_SUMMARY.json").read_bytes()
    before_p5e1_summary = (phase14c5e1_artifact_dir() / "PHASE_14C5E1_SUMMARY.json").read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase14c5f_p5f(auth)
    assert freeze_path.read_bytes() == before_freeze
    assert snapshot_prior_artifact_hashes()["phase14c5e1"] == before_prior["phase14c5e1"]
    assert snapshot_prior_artifact_hashes()["phase14c5e"] == before_prior["phase14c5e"]
    assert snapshot_prior_artifact_hashes()["phase14c5d"] == before_prior["phase14c5d"]
    assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["checkpoint_digest"] == EXPECTED_P5F_CHECKPOINT_DIGEST
    assert sci["F2_provenance"] == "INPUT / TEST EXTENSION"
    assert sci["Q05_BRST_STATUS"] == "VERIFIED"
    assert sci["one_loop_executed"] is False
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert g6_checkpoint_path().read_bytes() == before_g6
    assert p5d_checkpoint_path().read_bytes() == before_p5d
    assert p5e_checkpoint_path().read_bytes() == before_p5e
    assert p5e1_checkpoint_path().read_bytes() == before_p5e1
    assert (phase14c5e_artifact_dir() / "PHASE_14C5E_SUMMARY.json").read_bytes() == before_p5e_summary
    assert (phase14c5e1_artifact_dir() / "PHASE_14C5E1_SUMMARY.json").read_bytes() == before_p5e1_summary
    p5d = __import__("json").loads(p5d_checkpoint_path().read_text())
    p5e = __import__("json").loads(p5e_checkpoint_path().read_text())
    p5e1 = __import__("json").loads(p5e1_checkpoint_path().read_text())
    assert p5d.get("checkpoint_digest") == EXPECTED_P5D_CHECKPOINT_DIGEST
    assert p5e.get("checkpoint_digest") == EXPECTED_P5E_CHECKPOINT_DIGEST
    assert p5e1.get("checkpoint_digest") == EXPECTED_P5E1_CHECKPOINT_DIGEST
    assert (artifact_dir() / "checkpoint_P5F_G6_GAUGE_DYNAMICS_v1.json").is_file()
    _ = grammar_hash()


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5f_p5f.py",
        root / "models" / "examples" / "phase14c5f_model.py",
        root / "reporting" / "phase14c5f_report.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best_model" not in text
