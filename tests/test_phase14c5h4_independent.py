"""Independent Phase 14C.5H.4 checks."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis, freeze_paths, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase12a_grammar import grammar_hash_12a
from physics_lab.physics.phase14b0_engine import EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14c5h1_p5h1 import EXPECTED_P5H1_CHECKPOINT_DIGEST, artifact_dir as phase14c5h1_artifact_dir, p5h1_checkpoint_path
from physics_lab.physics.phase14c5h2_p5h2 import EXPECTED_P5H2_CHECKPOINT_DIGEST, artifact_dir as phase14c5h2_artifact_dir, p5h2_checkpoint_path
from physics_lab.physics.phase14c5h3_p5h3 import EXPECTED_P5H3_CHECKPOINT_DIGEST, artifact_dir as phase14c5h3_artifact_dir, p5h3_checkpoint_path
from physics_lab.physics.phase14c5h4_p5h4 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_P5H4_CHECKPOINT_DIGEST,
    analyze_phase14c5h4_p5h4,
    artifact_dir,
    g6_checkpoint_path,
    snapshot_prior_artifact_hashes,
)


def test_independent_14c5h4_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_12a = grammar_hash_12a()
    before_prior = snapshot_prior_artifact_hashes()
    before_g6 = g6_checkpoint_path().read_bytes()
    before_p5h1 = p5h1_checkpoint_path().read_bytes()
    before_p5h2 = p5h2_checkpoint_path().read_bytes()
    before_p5h3 = p5h3_checkpoint_path().read_bytes()
    before_p5h1_summary = (phase14c5h1_artifact_dir() / "PHASE_14C5H1_SUMMARY.json").read_bytes()
    before_p5h2_summary = (phase14c5h2_artifact_dir() / "PHASE_14C5H2_SUMMARY.json").read_bytes()
    before_p5h3_summary = (phase14c5h3_artifact_dir() / "PHASE_14C5H3_SUMMARY.json").read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase14c5h4_p5h4(auth)
    assert freeze_path.read_bytes() == before_freeze
    assert snapshot_prior_artifact_hashes()["phase14c5h3"] == before_prior["phase14c5h3"]
    assert snapshot_prior_artifact_hashes()["phase14c5h2"] == before_prior["phase14c5h2"]
    assert snapshot_prior_artifact_hashes()["phase14c5h1"] == before_prior["phase14c5h1"]
    assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["checkpoint_digest"] == EXPECTED_P5H4_CHECKPOINT_DIGEST
    assert sci["Q04_PARTIAL"] == 479
    assert sci["IR_SAFE_OBSERVABLE_STATUS"] == "VERIFIED"
    assert sci["IR_VERIFIED"] == 479
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["exclusive_2to2_declared_finite"] is False
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert g6_checkpoint_path().read_bytes() == before_g6
    assert p5h1_checkpoint_path().read_bytes() == before_p5h1
    assert p5h2_checkpoint_path().read_bytes() == before_p5h2
    assert p5h3_checkpoint_path().read_bytes() == before_p5h3
    assert (phase14c5h1_artifact_dir() / "PHASE_14C5H1_SUMMARY.json").read_bytes() == before_p5h1_summary
    assert (phase14c5h2_artifact_dir() / "PHASE_14C5H2_SUMMARY.json").read_bytes() == before_p5h2_summary
    assert (phase14c5h3_artifact_dir() / "PHASE_14C5H3_SUMMARY.json").read_bytes() == before_p5h3_summary
    p5h1 = __import__("json").loads(p5h1_checkpoint_path().read_text())
    p5h2 = __import__("json").loads(p5h2_checkpoint_path().read_text())
    p5h3 = __import__("json").loads(p5h3_checkpoint_path().read_text())
    assert p5h1.get("checkpoint_digest") == EXPECTED_P5H1_CHECKPOINT_DIGEST
    assert p5h2.get("checkpoint_digest") == EXPECTED_P5H2_CHECKPOINT_DIGEST
    assert p5h3.get("checkpoint_digest") == EXPECTED_P5H3_CHECKPOINT_DIGEST
    assert (artifact_dir() / "checkpoint_P5H4_IR_SAFE_INCLUSIVE_v1.json").is_file()
    _ = grammar_hash()


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5h4_p5h4.py",
        root / "models" / "examples" / "phase14c5h4_model.py",
        root / "reporting" / "phase14c5h4_report.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best_model" not in text
