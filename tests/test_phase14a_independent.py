"""Independent Phase 14A checks: freeze identity, no ranking, prior phases unchanged."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import declared_dependencies, grammar_hash
from physics_lab.physics.phase12a_grammar import grammar_hash_12a
from physics_lab.physics.phase13_1_low_d import artifact_dir as phase13_1_artifact_dir
from physics_lab.physics.phase14a_reconstruction import (
    EXPECTED_12A_GRAMMAR_HASH,
    analyze_phase14a_reconstruction,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)


def test_independent_reconstruction_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_hash = grammar_hash()
    before_12a = grammar_hash_12a()
    before_prior = snapshot_prior_artifact_hashes()
    before_131 = (phase13_1_artifact_dir() / "PHASE_13_1_SUMMARY.json").read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase14a_reconstruction(auth)
    after_freeze = freeze_path.read_bytes()
    after_prior = snapshot_prior_artifact_hashes()
    assert before_freeze == after_freeze
    assert before_prior == after_prior
    assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["BOTTOM_UP_TOP_DOWN_INTERSECTION"] == "EMPTY"
    assert sci["U1_ONLY_INSUFFICIENT"] is True
    assert sci["NEW_FIELD_REQUIRED"] is True
    assert sci["UNIQUE_STRUCTURE"] == "NO"
    assert sci["string_theory_constraints_imported"] is False
    assert sci["ranking"] is False
    assert sci["phase_14b_executed"] is False
    assert sci["PHASE_14A_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    declared_ids = {row["dependency_id"] for row in declared_dependencies()}
    assert "optional_F2_test_extension->A_mu" not in declared_ids
    assert sci["overclaims"]["1_relabel_input_as_derived"] == "REJECTED AS OVERCLAIM"
    assert sci["overclaims"]["7_import_string_theory"] == "REJECTED AS OVERCLAIM"
    assert (phase13_1_artifact_dir() / "PHASE_13_1_SUMMARY.json").read_bytes() == before_131
    assert (artifact_dir() / "PHASE_14A_SUMMARY.json").is_file()
    _ = before_hash


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14a_reconstruction.py",
        root / "models" / "examples" / "phase14a_model.py",
        root / "reporting" / "phase14a_report.py",
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
        assert "phase10a_" + "known_physics" not in text
        assert "KNOWN_PHYSICS_CATALOG" not in text
        assert "best_model" not in text
        assert "preferred_model" not in text
        assert "top_model" not in text
        assert "superstring" not in text
        assert "worldsheet" not in text
        assert "Calabi" + "-Yau" not in text
