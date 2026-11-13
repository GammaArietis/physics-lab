"""Independent Phase 11O: freeze identity, parents unchanged."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11e_vacuum import artifact_dir as phase11e_artifact_dir
from physics_lab.physics.phase11n_global_gauge import artifact_dir as phase11n_artifact_dir
from physics_lab.physics.phase11o_gravity_matter import analyze_phase11o_gravity_matter


def test_independent_gravity_matter_does_not_mutate_parents():
    freeze_path, _ = freeze_paths()
    paths = {
        "freeze": freeze_path,
        "syn": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "m3": phase11e_artifact_dir() / "PHASE_11E_M3_VACUUM.json",
        "g11n": phase11n_artifact_dir() / "PHASE_11N_GLOBAL_GAUGE_STRUCTURE.json",
    }
    before = {key: path.read_bytes() for key, path in paths.items()}
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11o_gravity_matter(auth)
    for key, path in paths.items():
        assert path.read_bytes() == before[key], key
    assert sci["status"] == "OK"
    assert sci["PHASE_11O_STATUS"] == "PARTIAL"
    assert sci["MINIMAL_COUPLING_STATUS"] == "NOT_UNIQUE"
    assert sci["GLOBAL_GAUGE_STATUS"] == "PARTIAL"
    assert sci["GRAVITY_CHANGED"] is False
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11o_gravity_matter.py",
        root / "models" / "examples" / "phase11o_model.py",
        root / "reporting" / "phase11o_report.py",
        root / "tests" / "phase11o_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best" + "_" + "model" not in text
        assert "analyze_phase11n" + "_global_gauge" not in text
        assert "analyze_phase6" + "_coupled_consistency" not in text
