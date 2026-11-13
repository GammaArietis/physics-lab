"""Independent Phase 14C.5H.1 checks."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis, freeze_paths, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase12a_grammar import grammar_hash_12a
from physics_lab.physics.phase14b0_engine import EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14c5f_p5f import EXPECTED_P5F_CHECKPOINT_DIGEST, artifact_dir as phase14c5f_artifact_dir, p5f_checkpoint_path
from physics_lab.physics.phase14c5g_p5g import EXPECTED_P5G_CHECKPOINT_DIGEST, artifact_dir as phase14c5g_artifact_dir, p5g_checkpoint_path
from physics_lab.physics.phase14c5g1_p5g1 import EXPECTED_P5G1_CHECKPOINT_DIGEST, artifact_dir as phase14c5g1_artifact_dir, p5g1_checkpoint_path
from physics_lab.physics.phase14c5h_p5h import EXPECTED_P5H_CHECKPOINT_DIGEST, artifact_dir as phase14c5h_artifact_dir, p5h_checkpoint_path
from physics_lab.physics.phase14c5h1_p5h1 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_P5H1_CHECKPOINT_DIGEST,
    analyze_phase14c5h1_p5h1,
    artifact_dir,
    g6_checkpoint_path,
    snapshot_prior_artifact_hashes,
)


def test_independent_14c5h1_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_12a = grammar_hash_12a()
    before_prior = snapshot_prior_artifact_hashes()
    before_g6 = g6_checkpoint_path().read_bytes()
    before_p5f = p5f_checkpoint_path().read_bytes()
    before_p5g = p5g_checkpoint_path().read_bytes()
    before_p5g1 = p5g1_checkpoint_path().read_bytes()
    before_p5h = p5h_checkpoint_path().read_bytes()
    before_p5f_summary = (phase14c5f_artifact_dir() / "PHASE_14C5F_SUMMARY.json").read_bytes()
    before_p5g_summary = (phase14c5g_artifact_dir() / "PHASE_14C5G_SUMMARY.json").read_bytes()
    before_p5g1_summary = (phase14c5g1_artifact_dir() / "PHASE_14C5G1_SUMMARY.json").read_bytes()
    before_p5h_summary = (phase14c5h_artifact_dir() / "PHASE_14C5H_SUMMARY.json").read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase14c5h1_p5h1(auth)
    assert freeze_path.read_bytes() == before_freeze
    assert snapshot_prior_artifact_hashes()["phase14c5h"] == before_prior["phase14c5h"]
    assert snapshot_prior_artifact_hashes()["phase14c5g1"] == before_prior["phase14c5g1"]
    assert snapshot_prior_artifact_hashes()["phase14c5g"] == before_prior["phase14c5g"]
    assert snapshot_prior_artifact_hashes()["phase14c5f"] == before_prior["phase14c5f"]
    assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["checkpoint_digest"] == EXPECTED_P5H1_CHECKPOINT_DIGEST
    assert sci["Q04_TREE_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["Q04_PARTIAL"] == 479
    assert sci["OPTICAL_THEOREM_STATUS"] == "UNTESTED"
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert g6_checkpoint_path().read_bytes() == before_g6
    assert p5f_checkpoint_path().read_bytes() == before_p5f
    assert p5g_checkpoint_path().read_bytes() == before_p5g
    assert p5g1_checkpoint_path().read_bytes() == before_p5g1
    assert p5h_checkpoint_path().read_bytes() == before_p5h
    assert (phase14c5f_artifact_dir() / "PHASE_14C5F_SUMMARY.json").read_bytes() == before_p5f_summary
    assert (phase14c5g_artifact_dir() / "PHASE_14C5G_SUMMARY.json").read_bytes() == before_p5g_summary
    assert (phase14c5g1_artifact_dir() / "PHASE_14C5G1_SUMMARY.json").read_bytes() == before_p5g1_summary
    assert (phase14c5h_artifact_dir() / "PHASE_14C5H_SUMMARY.json").read_bytes() == before_p5h_summary
    p5f = __import__("json").loads(p5f_checkpoint_path().read_text())
    p5g = __import__("json").loads(p5g_checkpoint_path().read_text())
    p5g1 = __import__("json").loads(p5g1_checkpoint_path().read_text())
    p5h = __import__("json").loads(p5h_checkpoint_path().read_text())
    assert p5f.get("checkpoint_digest") == EXPECTED_P5F_CHECKPOINT_DIGEST
    assert p5g.get("checkpoint_digest") == EXPECTED_P5G_CHECKPOINT_DIGEST
    assert p5g1.get("checkpoint_digest") == EXPECTED_P5G1_CHECKPOINT_DIGEST
    assert p5h.get("checkpoint_digest") == EXPECTED_P5H_CHECKPOINT_DIGEST
    assert (artifact_dir() / "checkpoint_P5H1_IR_SAFE_TREE_UNITARITY_v1.json").is_file()
    _ = grammar_hash()


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5h1_p5h1.py",
        root / "models" / "examples" / "phase14c5h1_model.py",
        root / "reporting" / "phase14c5h1_report.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best_model" not in text
