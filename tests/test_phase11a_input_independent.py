"""Independent Phase 11A input-gate checks: freeze identity, isolation, no invention."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11a_strategy import artifact_dir as phase11a_strategy_artifact_dir
from physics_lab.physics.phase11a_input_gate import analyze_phase11a_input_gate, artifact_dir


def test_independent_blocked_gate_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    syn = phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json"
    strat = phase11a_strategy_artifact_dir() / "PHASE_11A_SUMMARY.json"
    before_freeze = freeze_path.read_bytes()
    before_syn = syn.read_bytes()
    before_strat = strat.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11a_input_gate(auth)
    after_freeze = freeze_path.read_bytes()
    after_syn = syn.read_bytes()
    after_strat = strat.read_bytes()
    assert before_freeze == after_freeze
    assert before_syn == after_syn
    assert before_strat == after_strat
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["HUMAN_INPUT_PRESENT"] is False
    assert sci["PHASE_11A_STATUS"] == "BLOCKED"
    assert sci["INPUT_FREEZE_STATUS"] == "NOT_CREATED"
    assert sci["machine_chose_principle"] is False
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    assert not (artifact_dir() / "PHASE_11A_INPUT_FREEZE.json").exists()
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets_or_invention():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11a_input_gate.py",
        root / "models" / "examples" / "phase11a_input_model.py",
        root / "reporting" / "phase11a_input_report.py",
        root / "tests" / "phase11a_input_test.py",
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
        assert "generate_principle" not in text
        assert "best" + "_" + "model" not in text
        assert "preferred" + "_" + "model" not in text
        assert "analyze_phase10e_synthesis" not in text
