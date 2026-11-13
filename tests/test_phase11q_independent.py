"""Independent Phase 11Q: freeze identity, parents unchanged."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11p_vacuum_selection import artifact_dir as phase11p_artifact_dir
from physics_lab.physics.phase14c5k_p5k import artifact_dir as phase14c5k_artifact_dir
from physics_lab.physics.phase11q_uv_consistency import analyze_phase11q_uv_consistency


def test_independent_uv_does_not_mutate_parents():
    freeze_path, _ = freeze_paths()
    paths = {
        "freeze": freeze_path,
        "syn": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "vac": phase11p_artifact_dir() / "PHASE_11P_VACUUM_SELECTION.json",
        "p5k": phase14c5k_artifact_dir() / "PHASE_14C5K_SUMMARY.json",
    }
    before = {key: path.read_bytes() for key, path in paths.items()}
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11q_uv_consistency(auth)
    for key, path in paths.items():
        assert path.read_bytes() == before[key], key
    assert sci["status"] == "OK"
    assert sci["PHASE_11Q_STATUS"] == "PARTIAL"
    assert sci["UV_PROPERTY_NOT_FOUND"] is True
    assert sci["UV_INCONSISTENCY"] is False
    assert sci["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11q_uv_consistency.py",
        root / "models" / "examples" / "phase11q_model.py",
        root / "reporting" / "phase11q_report.py",
        root / "tests" / "phase11q_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best" + "_" + "model" not in text
        assert "analyze_phase11p" + "_vacuum_selection" not in text
        assert "analyze_phase14c5k" + "_p5k" not in text
        assert "two_loop_kinematic" + "_engine" not in text
