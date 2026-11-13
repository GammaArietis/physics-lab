"""Independent Phase 11C: freeze identity, isolated M1, no targets."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10e_synthesis import artifact_dir as phase10e_artifact_dir
from physics_lab.physics.phase11b_qft_foundations import artifact_dir as phase11b_qft_artifact_dir
from physics_lab.physics.phase11c_microcausality import analyze_phase11c_microcausality


def test_independent_m1_isolated_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    syn = phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json"
    audit = phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json"
    before_freeze = freeze_path.read_bytes()
    before_syn = syn.read_bytes()
    before_audit = audit.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11c_microcausality(auth)
    assert freeze_path.read_bytes() == before_freeze
    assert syn.read_bytes() == before_syn
    assert audit.read_bytes() == before_audit
    assert sci["status"] == "OK"
    assert sci["PHASE_11C_STATUS"] == "PARTIAL"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["M2_ENABLED"] is False
    assert sci["M5_ENABLED"] is False
    assert sci["GAUGE_MICROCAUSALITY_STATUS"] == "UNTESTED"
    assert sci["NEW_INPUT_REQUIRED"] is False
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11c_microcausality.py",
        root / "models" / "examples" / "phase11c_model.py",
        root / "reporting" / "phase11c_report.py",
        root / "tests" / "phase11c_test.py",
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
        assert "analyze_phase11b_qft_audit" not in text
        assert "cluster decomposition" not in text
        assert "reflection positivity" not in text
