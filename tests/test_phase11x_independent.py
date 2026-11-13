"""Independent Phase 11X: freeze identity, 11V/11W unchanged."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11v_susy_mediation import artifact_dir as phase11v_artifact_dir
from physics_lab.physics.phase11w_mediation_alternatives import artifact_dir as phase11w_artifact_dir
from physics_lab.physics.phase11x_gauge_mediation import analyze_phase11x_gauge_mediation


def test_independent_gmsb_does_not_mutate_parents():
    freeze_path, _ = freeze_paths()
    paths = {
        "freeze": freeze_path,
        "syn": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "grav": phase11v_artifact_dir() / "PHASE_11V_SUSY_MEDIATION.json",
        "alt": phase11w_artifact_dir() / "PHASE_11W_MEDIATION_ALTERNATIVES.json",
    }
    before = {key: path.read_bytes() for key, path in paths.items()}
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11x_gauge_mediation(auth)
    for key, path in paths.items():
        assert path.read_bytes() == before[key], key
    assert sci["status"] == "OK"
    assert sci["PHASE_11X_STATUS"] == "PARTIAL"
    assert sci["GAUGE_MEDIATION_UNIQUENESS"] == "NOT_DERIVED"
    assert sci["MEDIATION_SELECTION_STATUS"] == "NOT_DERIVED"
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["combined_with_11V_operators"] is False
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11x_gauge_mediation.py",
        root / "models" / "examples" / "phase11x_model.py",
        root / "reporting" / "phase11x_report.py",
        root / "tests" / "phase11x_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best" + "_" + "model" not in text
        assert "analyze_phase11w" + "_mediation_alternatives" not in text
        assert "two_loop_kinematic" + "_engine" not in text
