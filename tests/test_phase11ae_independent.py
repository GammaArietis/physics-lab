"""Independent Phase 11AE: freeze identity, parents unchanged, no invented principle."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11p_vacuum_selection import artifact_dir as phase11p_artifact_dir
from physics_lab.physics.phase11v_susy_mediation import artifact_dir as phase11v_artifact_dir
from physics_lab.physics.phase11ad_closure_gate import artifact_dir as phase11ad_artifact_dir
from physics_lab.physics.phase11ae_vacuum_selection import (
    analyze_phase11ae_vacuum_selection,
    is_exact_mathematical_statement,
)


def test_independent_gate_does_not_mutate_parents():
    freeze_path, _ = freeze_paths()
    paths = {
        "freeze": freeze_path,
        "p": phase11p_artifact_dir() / "PHASE_11P_VACUUM_SELECTION.json",
        "v": phase11v_artifact_dir() / "PHASE_11V_SUSY_MEDIATION.json",
        "ad": phase11ad_artifact_dir() / "PHASE_11AD_CLOSURE_GATE.json",
    }
    before = {key: path.read_bytes() for key, path in paths.items()}
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11ae_vacuum_selection(auth)
    for key, path in paths.items():
        assert path.read_bytes() == before[key], key
    assert sci["status"] == "OK"
    assert sci["VACUUM_SELECTION_INPUT_STATUS"] == "PRINCIPLE_UNSPECIFIED"
    assert sci["principle_invented"] is False
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_cannot_auto_select_reference_examples():
    for phrase in ("global minimum", "local stability", "uniqueness condition"):
        assert is_exact_mathematical_statement(phrase) is False
    auth = authorize_phase5b0_analysis()
    out = analyze_phase11ae_vacuum_selection(auth, write_artifacts=False, injected_statement="global minimum")
    assert out["POST_HOC_PRINCIPLE_SELECTION"] is True


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11ae_vacuum_selection.py",
        root / "models" / "examples" / "phase11ae_model.py",
        root / "reporting" / "phase11ae_report.py",
        root / "tests" / "phase11ae_test.py",
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
        assert "analyze_phase11ad" + "_closure_gate" not in text
        assert "two_loop_kinematic" + "_engine" not in text
