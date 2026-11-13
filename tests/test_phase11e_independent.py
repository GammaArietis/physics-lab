"""Independent Phase 11E: freeze identity, isolated M3, no targets."""

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
from physics_lab.physics.phase11d_spectral import artifact_dir as phase11d_artifact_dir
from physics_lab.physics.phase11e_vacuum import analyze_phase11e_vacuum


def test_independent_m3_isolated_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    syn = phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json"
    audit = phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json"
    m1 = phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json"
    m2 = phase11d_artifact_dir() / "PHASE_11D_M2_SPECTRAL.json"
    before_freeze = freeze_path.read_bytes()
    before_syn = syn.read_bytes()
    before_audit = audit.read_bytes()
    before_m1 = m1.read_bytes()
    before_m2 = m2.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11e_vacuum(auth)
    assert freeze_path.read_bytes() == before_freeze
    assert syn.read_bytes() == before_syn
    assert audit.read_bytes() == before_audit
    assert m1.read_bytes() == before_m1
    assert m2.read_bytes() == before_m2
    assert sci["status"] == "OK"
    assert sci["PHASE_11E_STATUS"] == "PARTIAL"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["M1_REMAINS_PARTIAL"] is True
    assert sci["M2_REMAINS_PARTIAL"] is True
    assert sci["M4_ENABLED"] is False
    assert sci["M5_ENABLED"] is False
    assert sci["INTERACTING_QUANTUM_VACUUM"] == "UNTESTED"
    assert sci["NEW_INPUT_REQUIRED"] is False
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11e_vacuum.py",
        root / "models" / "examples" / "phase11e_model.py",
        root / "reporting" / "phase11e_report.py",
        root / "tests" / "phase11e_test.py",
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
        assert "analyze_phase11d_spectral" not in text
