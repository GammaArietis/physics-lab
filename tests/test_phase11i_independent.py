"""Independent Phase 11I: freeze identity, parents unchanged."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11h_smatrix_audit import artifact_dir as phase11h_artifact_dir
from physics_lab.physics.phase11i_m6_smatrix import analyze_phase11i_m6_smatrix


def test_independent_m6_does_not_mutate_parents():
    freeze_path, _ = freeze_paths()
    paths = {
        "freeze": freeze_path,
        "syn": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "audit": phase11h_artifact_dir() / "PHASE_11H_S_MATRIX_COVERAGE_AUDIT.json",
    }
    before = {key: path.read_bytes() for key, path in paths.items()}
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11i_m6_smatrix(auth)
    for key, path in paths.items():
        assert path.read_bytes() == before[key], key
    assert sci["status"] == "OK"
    assert sci["PHASE_11I_STATUS"] == "PARTIAL"
    assert sci["EXACT_S_MATRIX_STATUS"] == "PARTIAL"
    assert sci["M7_STATUS"] == "DISABLED"
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11i_m6_smatrix.py",
        root / "models" / "examples" / "phase11i_model.py",
        root / "reporting" / "phase11i_report.py",
        root / "tests" / "phase11i_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best" + "_" + "model" not in text
        assert "analyze_phase11h" + "_smatrix_audit" not in text
        assert "analyze_phase14c5h2" + "_p5h2" not in text
