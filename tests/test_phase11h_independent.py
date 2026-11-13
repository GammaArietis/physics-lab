"""Independent Phase 11H audit: freeze identity, no activation, no targets."""

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
from physics_lab.physics.phase11f_cluster import artifact_dir as phase11f_artifact_dir
from physics_lab.physics.phase11fa_m4_authorization import artifact_dir as phase11fa_artifact_dir
from physics_lab.physics.phase11fb_cluster_consequence import artifact_dir as phase11fb_artifact_dir
from physics_lab.physics.phase11g_os import artifact_dir as phase11g_artifact_dir
from physics_lab.physics.phase11h_smatrix_audit import analyze_phase11h_smatrix_audit


def test_independent_audit_only_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    paths = {
        "freeze": freeze_path,
        "syn": phase10e_artifact_dir() / "PHASE_10E_GLOBAL_SYNTHESIS.json",
        "audit": phase11b_qft_artifact_dir() / "PHASE_11B_QFT_FOUNDATIONAL_AUDIT.json",
        "m1": phase11c_artifact_dir() / "PHASE_11C_M1_MICROCAUSALITY.json",
        "m2": phase11d_artifact_dir() / "PHASE_11D_M2_SPECTRAL.json",
        "m3": phase11e_artifact_dir() / "PHASE_11E_M3_VACUUM.json",
        "blocked": phase11f_artifact_dir() / "PHASE_11F_M4_CLUSTER.json",
        "authz": phase11fa_artifact_dir() / "PHASE_11F_A_M4_AUTHORIZATION.json",
        "fb": phase11fb_artifact_dir() / "PHASE_11F_B_M4_CLUSTER_CONSEQUENCE.json",
        "os": phase11g_artifact_dir() / "PHASE_11G_M5_OS_CONSEQUENCE.json",
    }
    before = {key: path.read_bytes() for key, path in paths.items()}
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11h_smatrix_audit(auth)
    for key, path in paths.items():
        assert path.read_bytes() == before[key], key
    assert sci["status"] == "OK"
    assert sci["PHASE_11H_STATUS"] == "AUDIT_COMPLETE"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["audit"]["modules_enabled"] == []
    assert sci["M6_S_MATRIX_UNITARITY_STATUS"] == "PARTIAL"
    assert sci["M10_POSITIVITY_BOUNDS_STATUS"] == "ABSENT"
    assert sci["M5_STATUS"] == "PARTIAL"
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11h_smatrix_audit.py",
        root / "models" / "examples" / "phase11h_model.py",
        root / "reporting" / "phase11h_report.py",
        root / "tests" / "phase11h_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best" + "_" + "model" not in text
        assert "analyze_phase10e" + "_synthesis" not in text
        assert "analyze_phase11g" + "_os" not in text
        assert "generate_principle" not in text
