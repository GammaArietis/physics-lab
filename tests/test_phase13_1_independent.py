"""Independent Phase 13.1 checks: freeze identity, no ranking, Phase 13 unchanged."""

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
from physics_lab.physics.phase13_dimension import artifact_dir as phase13_artifact_dir
from physics_lab.physics.phase13_1_low_d import (
    EXPECTED_12A_GRAMMAR_HASH,
    analyze_phase13_1_low_d,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)


def test_independent_low_d_exception_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_hash = grammar_hash()
    before_12a = grammar_hash_12a()
    before_prior = snapshot_prior_artifact_hashes()
    before_13 = (phase13_artifact_dir() / "PHASE_13_SUMMARY.json").read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase13_1_low_d(auth)
    after_freeze = freeze_path.read_bytes()
    after_prior = snapshot_prior_artifact_hashes()
    assert before_freeze == after_freeze
    assert before_prior == after_prior
    assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["D1_status"] == "D_NOT_APPLICABLE"
    assert sci["D2_status"] == "D_IS_ALLOWED"
    assert sci["D3_status"] == "D_IS_ALLOWED"
    assert sci["NO_LOWER_DIMENSION_EXCLUSION"] is True
    assert sci["UNIQUE_DIMENSION"] == "NO"
    assert sci["string_theory_constraints_imported"] is False
    assert sci["ranking"] is False
    assert sci["phase_14_executed"] is False
    assert sci["PHASE_13_1_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    declared_ids = {row["dependency_id"] for row in declared_dependencies()}
    assert "optional_F2_test_extension->A_mu" not in declared_ids
    assert sci["overclaims"]["1_force_D4"] == "REJECTED AS OVERCLAIM"
    assert sci["overclaims"]["6_import_string_theory"] == "REJECTED AS OVERCLAIM"
    assert (phase13_artifact_dir() / "PHASE_13_SUMMARY.json").read_bytes() == before_13
    assert (artifact_dir() / "PHASE_13_1_SUMMARY.json").is_file()
    _ = before_hash


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase13_1_low_d.py",
        root / "models" / "examples" / "phase13_1_model.py",
        root / "reporting" / "phase13_1_report.py",
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
