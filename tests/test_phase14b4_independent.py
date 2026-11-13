"""Independent Phase 14B.4 checks."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis, freeze_paths, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import declared_dependencies, grammar_hash
from physics_lab.physics.phase12a_grammar import grammar_hash_12a
from physics_lab.physics.phase14b0_engine import EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14b3r_g3 import artifact_dir as phase14b3r_artifact_dir
from physics_lab.physics.phase14b4_g4 import analyze_phase14b4_g4, artifact_dir, snapshot_prior_artifact_hashes


def test_independent_g4_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_hash = grammar_hash()
    before_12a = grammar_hash_12a()
    before_prior = snapshot_prior_artifact_hashes()
    before_g3 = (phase14b3r_artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS_R1.json").read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase14b4_g4(auth)
    assert freeze_path.read_bytes() == before_freeze
    assert snapshot_prior_artifact_hashes()["phase14b3r"] == before_prior["phase14b3r"]
    assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["G4_EXECUTED"] is True
    assert sci["G5_EXECUTED"] is False
    assert sci["PARENT_GRAMMAR"] == "G3_FINITE_REPRESENTATIONS_R1"
    assert sci["gravity_changed"] is False
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert "optional_F2_test_extension->A_mu" not in {row["dependency_id"] for row in declared_dependencies()}
    assert sci["overclaims"]["1_activate_G5_automatically"] == "REJECTED AS OVERCLAIM"
    assert (phase14b3r_artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS_R1.json").read_bytes() == before_g3
    assert (artifact_dir() / "PHASE_14B4_SUMMARY.json").is_file()
    _ = before_hash


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14b4_g4.py",
        root / "models" / "examples" / "phase14b4_model.py",
        root / "reporting" / "phase14b4_report.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "from physics_lab.physics.gauge_internal" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best_model" not in text
        assert "preferred_model" not in text
        assert "top_model" not in text
        assert "superstring" not in text
        assert "worldsheet" not in text
