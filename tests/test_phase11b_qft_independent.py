"""Independent Phase 11B QFT audit: freeze identity, no activation, no targets."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11b_qft_foundations import analyze_phase11b_qft_audit


def test_independent_audit_only_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    syn = phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json"
    before_freeze = freeze_path.read_bytes()
    before_syn = syn.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11b_qft_audit(auth)
    assert freeze_path.read_bytes() == before_freeze
    assert syn.read_bytes() == before_syn
    assert sci["status"] == "OK"
    assert sci["PHASE_11B_STATUS"] == "AUDIT_COMPLETE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["audit"]["modules_enabled"] == []
    assert sci["M4_CLUSTER_STATUS"] == "ABSENT"
    assert sci["M5_OS_STATUS"] == "ABSENT"
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11b_qft_foundations.py",
        root / "models" / "examples" / "phase11b_qft_model.py",
        root / "reporting" / "phase11b_qft_report.py",
        root / "tests" / "phase11b_qft_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best" + "_" + "model" not in text
        assert "analyze_phase10e_synthesis" not in text
        assert "generate_principle" not in text
