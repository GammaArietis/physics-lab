"""Independent Phase 14C.5H.5 checks."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis, freeze_paths, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash
from physics_lab.physics.phase12a_grammar import grammar_hash_12a
from physics_lab.physics.phase14b0_engine import EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14c5h1_p5h1 import EXPECTED_P5H1_CHECKPOINT_DIGEST, artifact_dir as phase14c5h1_artifact_dir, p5h1_checkpoint_path
from physics_lab.physics.phase14c5h4_p5h4 import EXPECTED_P5H4_CHECKPOINT_DIGEST, artifact_dir as phase14c5h4_artifact_dir, p5h4_checkpoint_path
from physics_lab.physics.phase14c5h5_p5h5 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_P5H5_CHECKPOINT_DIGEST,
    analyze_phase14c5h5_p5h5,
    artifact_dir,
    g6_checkpoint_path,
    snapshot_prior_artifact_hashes,
)


def test_independent_14c5h5_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_12a = grammar_hash_12a()
    before_prior = snapshot_prior_artifact_hashes()
    before_g6 = g6_checkpoint_path().read_bytes()
    before_p5h1 = p5h1_checkpoint_path().read_bytes()
    before_p5h4 = p5h4_checkpoint_path().read_bytes()
    before_p5h1_summary = (phase14c5h1_artifact_dir() / "PHASE_14C5H1_SUMMARY.json").read_bytes()
    before_p5h4_summary = (phase14c5h4_artifact_dir() / "PHASE_14C5H4_SUMMARY.json").read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase14c5h5_p5h5(auth)
    assert freeze_path.read_bytes() == before_freeze
    assert snapshot_prior_artifact_hashes()["phase14c5h4"] == before_prior["phase14c5h4"]
    assert snapshot_prior_artifact_hashes()["phase14c5h1"] == before_prior["phase14c5h1"]
    assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["checkpoint_digest"] == EXPECTED_P5H5_CHECKPOINT_DIGEST
    assert sci["Q04_PARTIAL"] == 479
    assert sci["Q04_VERIFIED"] == 0
    assert sci["PARAMETER_DOMAIN_CONSTRAINT"] == "VERIFIED"
    assert sci["unique_coupling"] is False
    assert sci["P5H4_does_not_replace_Q04"] is True
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert g6_checkpoint_path().read_bytes() == before_g6
    assert p5h1_checkpoint_path().read_bytes() == before_p5h1
    assert p5h4_checkpoint_path().read_bytes() == before_p5h4
    assert (phase14c5h1_artifact_dir() / "PHASE_14C5H1_SUMMARY.json").read_bytes() == before_p5h1_summary
    assert (phase14c5h4_artifact_dir() / "PHASE_14C5H4_SUMMARY.json").read_bytes() == before_p5h4_summary
    p5h1 = __import__("json").loads(p5h1_checkpoint_path().read_text())
    p5h4 = __import__("json").loads(p5h4_checkpoint_path().read_text())
    assert p5h1.get("checkpoint_digest") == EXPECTED_P5H1_CHECKPOINT_DIGEST
    assert p5h4.get("checkpoint_digest") == EXPECTED_P5H4_CHECKPOINT_DIGEST
    assert (artifact_dir() / "checkpoint_P5H5_Q04_PARAMETER_DOMAIN_v1.json").is_file()
    _ = grammar_hash()


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c5h5_p5h5.py",
        root / "models" / "examples" / "phase14c5h5_model.py",
        root / "reporting" / "phase14c5h5_report.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best_model" not in text
