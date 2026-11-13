"""Independent Phase 11D: freeze identity, isolated M2, no targets."""

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
from physics_lab.physics.phase11c_microcausality import artifact_dir as phase11c_artifact_dir
from physics_lab.physics.phase11d_spectral import analyze_phase11d_spectral


def test_independent_m2_isolated_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    syn = phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json"
    audit = phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json"
    m1 = phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json"
    before_freeze = freeze_path.read_bytes()
    before_syn = syn.read_bytes()
    before_audit = audit.read_bytes()
    before_m1 = m1.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11d_spectral(auth)
    assert freeze_path.read_bytes() == before_freeze
    assert syn.read_bytes() == before_syn
    assert audit.read_bytes() == before_audit
    assert m1.read_bytes() == before_m1
    assert sci["status"] == "OK"
    assert sci["PHASE_11D_STATUS"] == "PARTIAL"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["M1_REMAINS_PARTIAL"] is True
    assert sci["M3_ENABLED"] is False
    assert sci["M5_ENABLED"] is False
    assert sci["GAUGE_SPECTRAL_STATUS"] == "UNTESTED"
    assert sci["FULL_QUANTUM_UNITARITY"] == "UNTESTED"
    assert sci["NEW_INPUT_REQUIRED"] is False
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11d_spectral.py",
        root / "models" / "examples" / "phase11d_model.py",
        root / "reporting" / "phase11d_report.py",
        root / "tests" / "phase11d_test.py",
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
        assert "analyze_phase11c_microcausality" not in text
