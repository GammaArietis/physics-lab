"""Independent Phase 14C.0 checks."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis, freeze_paths, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import declared_dependencies, grammar_hash
from physics_lab.physics.phase12a_grammar import grammar_hash_12a
from physics_lab.physics.phase14b0_engine import EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14c0_known_physics import (
    EXPECTED_G6_CHECKPOINT_HASH,
    analyze_phase14c0_known_physics,
    artifact_dir,
    g6_checkpoint_path,
    snapshot_prior_artifact_hashes,
)


def test_independent_14c0_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_hash = grammar_hash()
    before_12a = grammar_hash_12a()
    before_prior = snapshot_prior_artifact_hashes()
    before_g6 = g6_checkpoint_path().read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase14c0_known_physics(auth)
    assert freeze_path.read_bytes() == before_freeze
    assert snapshot_prior_artifact_hashes()["phase14b6"] == before_prior["phase14b6"]
    assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["P0_EXECUTED"] is True
    assert sci["P1_EXECUTED"] is False
    assert sci["PARENT_GRAMMAR"] == "G6_STRUCTURAL_GAUGE_CONSISTENCY"
    assert sci["gravity_changed"] is False
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    assert sci["VECTORLIKE_STATUS"] == "UNTESTED"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert "optional_F2_test_extension->A_mu" not in {row["dependency_id"] for row in declared_dependencies()}
    assert sci["overclaims"]["all_known_physics_encoded"] == "REJECTED AS OVERCLAIM"
    assert sci["overclaims"]["standard_model_rediscovered"] == "REJECTED AS OVERCLAIM"
    assert g6_checkpoint_path().read_bytes() == before_g6
    assert (artifact_dir() / "closure_checkpoint_14C0_KNOWN_PHYSICS_STRUCTURAL.json").is_file()
    assert (artifact_dir() / "PHASE_14C0_SUMMARY.json").is_file()
    _ = before_hash
    _ = EXPECTED_G6_CHECKPOINT_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c0_known_physics.py",
        root / "models" / "examples" / "phase14c0_model.py",
        root / "reporting" / "phase14c0_report.py",
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
