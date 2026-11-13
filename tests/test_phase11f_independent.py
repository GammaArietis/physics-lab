"""Independent Phase 11F: freeze identity, M4 not auto-activated."""

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
from physics_lab.physics.phase11e_vacuum import artifact_dir as phase11e_artifact_dir
from physics_lab.physics.phase11f_cluster import analyze_phase11f_cluster


def test_independent_m4_not_auto_activated_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    syn = phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json"
    audit = phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json"
    m1 = phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json"
    m2 = phase11d_artifact_dir() / "PHASE_11D_M2_SPECTRAL.json"
    m3 = phase11e_artifact_dir() / "PHASE_11E_M3_VACUUM.json"
    before_freeze = freeze_path.read_bytes()
    before_syn = syn.read_bytes()
    before_audit = audit.read_bytes()
    before_m1 = m1.read_bytes()
    before_m2 = m2.read_bytes()
    before_m3 = m3.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11f_cluster(auth)
    assert freeze_path.read_bytes() == before_freeze
    assert syn.read_bytes() == before_syn
    assert audit.read_bytes() == before_audit
    assert m1.read_bytes() == before_m1
    assert m2.read_bytes() == before_m2
    assert m3.read_bytes() == before_m3
    assert sci["status"] == "OK"
    assert sci["PHASE_11F_STATUS"] == "BLOCKED"
    assert sci["NEW_INPUT_STATUS"] == "NOT_ACTIVATED"
    assert sci["M4_REMAINS_UNACTIVATED"] is True
    assert sci["rejection"] == "M4_ACTIVATION_MISSING"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["M1_REMAINS_PARTIAL"] is True
    assert sci["M5_ENABLED"] is False
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11f_cluster.py",
        root / "models" / "examples" / "phase11f_model.py",
        root / "reporting" / "phase11f_report.py",
        root / "tests" / "phase11f_test.py",
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
        assert "analyze_phase11e_vacuum" not in text
