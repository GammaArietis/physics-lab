"""Independent Phase 11N: freeze identity, parents unchanged."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11m_m10_positivity import artifact_dir as phase11m_artifact_dir
from physics_lab.physics.phase11n_global_gauge import analyze_phase11n_global_gauge


def test_independent_global_gauge_does_not_mutate_parents():
    freeze_path, _ = freeze_paths()
    paths = {
        "freeze": freeze_path,
        "syn": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "m10": phase11m_artifact_dir() / "PHASE_11M_M10_POSITIVITY.json",
    }
    before = {key: path.read_bytes() for key, path in paths.items()}
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11n_global_gauge(auth)
    for key, path in paths.items():
        assert path.read_bytes() == before[key], key
    assert sci["status"] == "OK"
    assert sci["PHASE_11N_STATUS"] == "PARTIAL"
    assert sci["GLOBAL_GROUP_FORM"] == "NOT_UNIQUE"
    assert sci["M10_STATUS"] == "PARTIAL"
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11n_global_gauge.py",
        root / "models" / "examples" / "phase11n_model.py",
        root / "reporting" / "phase11n_report.py",
        root / "tests" / "phase11n_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best" + "_" + "model" not in text
        assert "analyze_phase11m" + "_m10_positivity" not in text
        assert "analyze_phase5c" + "_gauging" not in text
