"""Independent Phase 14C.4 checks."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis, freeze_paths, verify_phase4c_action_freeze
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import declared_dependencies, grammar_hash
from physics_lab.physics.phase12a_grammar import grammar_hash_12a
from physics_lab.physics.phase14b0_engine import EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14c0_known_physics import artifact_dir as phase14c0_artifact_dir, catalog_hash
from physics_lab.physics.phase14c3_p3 import artifact_dir as phase14c3_artifact_dir
from physics_lab.physics.phase14c4_p4 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_CATALOG_HASH,
    analyze_phase14c4_p4,
    artifact_dir,
    g6_checkpoint_path,
    p3_checkpoint_path,
    snapshot_prior_artifact_hashes,
)


def test_independent_14c4_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_hash = grammar_hash()
    before_12a = grammar_hash_12a()
    before_prior = snapshot_prior_artifact_hashes()
    before_g6 = g6_checkpoint_path().read_bytes()
    before_p0 = (phase14c0_artifact_dir() / "closure_checkpoint_14C0_KNOWN_PHYSICS_STRUCTURAL.json").read_bytes()
    before_p3 = p3_checkpoint_path().read_bytes()
    before_p3_summary = (phase14c3_artifact_dir() / "PHASE_14C3_SUMMARY.json").read_bytes()
    before_catalog = catalog_hash()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase14c4_p4(auth)
    assert freeze_path.read_bytes() == before_freeze
    assert snapshot_prior_artifact_hashes()["phase14b6"] == before_prior["phase14b6"]
    assert snapshot_prior_artifact_hashes()["phase14c0"] == before_prior["phase14c0"]
    assert snapshot_prior_artifact_hashes()["phase14c3"] == before_prior["phase14c3"]
    assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["P4_EXECUTED"] is True
    assert sci["P5_EXECUTED"] is False
    assert sci["gravity_changed"] is False
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert catalog_hash() == before_catalog == EXPECTED_CATALOG_HASH
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert "optional_F2_test_extension->A_mu" not in {row["dependency_id"] for row in declared_dependencies()}
    assert sci["overclaims"]["known_theory_derived"] == "REJECTED AS OVERCLAIM"
    assert sci["overclaims"]["P5_automatically_activated"] == "REJECTED AS OVERCLAIM"
    assert g6_checkpoint_path().read_bytes() == before_g6
    assert (phase14c0_artifact_dir() / "closure_checkpoint_14C0_KNOWN_PHYSICS_STRUCTURAL.json").read_bytes() == before_p0
    assert p3_checkpoint_path().read_bytes() == before_p3
    assert (phase14c3_artifact_dir() / "PHASE_14C3_SUMMARY.json").read_bytes() == before_p3_summary
    assert (artifact_dir() / "checkpoint_P4_KNOWN_MODEL_REFERENCE.json").is_file()
    assert (artifact_dir() / "PHASE_14C4_SUMMARY.json").is_file()
    assert (artifact_dir() / "KNOWN_MODEL_COMPARISON_REPORT.json").is_file()
    _ = before_hash


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c4_p4.py",
        root / "models" / "examples" / "phase14c4_model.py",
        root / "reporting" / "phase14c4_report.py",
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
        assert "DERIVED_FROM_MODEL_REFERENCE" not in text
