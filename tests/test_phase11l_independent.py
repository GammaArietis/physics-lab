"""Independent Phase 11L: freeze identity, parents unchanged."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11j_m7_analyticity import artifact_dir as phase11j_artifact_dir
from physics_lab.physics.phase11k_m8_crossing import artifact_dir as phase11k_artifact_dir
from physics_lab.physics.phase11l_m9_dispersion import analyze_phase11l_m9_dispersion


def test_independent_m9_does_not_mutate_parents():
    freeze_path, _ = freeze_paths()
    paths = {
        "freeze": freeze_path,
        "syn": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "m7": phase11j_artifact_dir() / "PHASE_11J_M7_ANALYTICITY.json",
        "m8": phase11k_artifact_dir() / "PHASE_11K_M8_CROSSING.json",
    }
    before = {key: path.read_bytes() for key, path in paths.items()}
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11l_m9_dispersion(auth)
    for key, path in paths.items():
        assert path.read_bytes() == before[key], key
    assert sci["status"] == "OK"
    assert sci["PHASE_11L_STATUS"] == "PARTIAL"
    assert sci["TREE_DISPERSION_STATUS"] == "VERIFIED"
    assert sci["ONE_LOOP_DISPERSION_STATUS"] == "PARTIAL"
    assert sci["M10_STATUS"] == "DISABLED"
    assert sci["M7_STATUS"] == "PARTIAL"
    assert sci["M8_STATUS"] == "PARTIAL"
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11l_m9_dispersion.py",
        root / "models" / "examples" / "phase11l_model.py",
        root / "reporting" / "phase11l_report.py",
        root / "tests" / "phase11l_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best" + "_" + "model" not in text
        assert "analyze_phase11k" + "_m8_crossing" not in text
        assert "analyze_phase11j" + "_m7_analyticity" not in text
        assert "analyze_phase14c5h2" + "_p5h2" not in text
