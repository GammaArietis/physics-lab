"""Independent Phase 10C checks: freeze identity, isolation, no feedback."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10c_interpretation import analyze_phase10c_interpretation


def test_independent_interpretation_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    catalog = phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json"
    before_freeze = freeze_path.read_bytes()
    before_catalog = catalog.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase10c_interpretation(auth)
    after_freeze = freeze_path.read_bytes()
    after_catalog = catalog.read_bytes()
    assert before_freeze == after_freeze
    assert before_catalog == after_catalog
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["CANDIDATES_INTERPRETED"] == 8
    assert sci["TARGET_ISOLATION_STATUS"] == "VERIFIED"
    assert sci["NO_FEEDBACK_STATUS"] == "VERIFIED"
    assert sci["NO_RANKING_STATUS"] == "VERIFIED"
    assert sci["models_generated"] == 0
    assert sci["PHASE_10C_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets_or_feedback():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10c_interpretation.py",
        root / "models" / "examples" / "phase10c_model.py",
        root / "reporting" / "phase10c_report.py",
        root / "tests" / "phase10c_test.py",
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
        assert "analyze_phase10b1_exploration" not in text
        assert "best" + "_" + "model" not in text
        assert "preferred" + "_" + "model" not in text
