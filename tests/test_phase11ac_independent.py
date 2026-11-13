"""Independent Phase 11AC: freeze identity, parents unchanged, CLASS C/D/E untouched."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11v_susy_mediation import artifact_dir as phase11v_artifact_dir
from physics_lab.physics.phase11x_gauge_mediation import artifact_dir as phase11x_artifact_dir
from physics_lab.physics.phase11y_anomaly_mediation import artifact_dir as phase11y_artifact_dir
from physics_lab.physics.phase11z_modulus_mediation import artifact_dir as phase11z_artifact_dir
from physics_lab.physics.phase11aa_direct_mediation import artifact_dir as phase11aa_artifact_dir
from physics_lab.physics.phase11ab_mediation_synthesis import artifact_dir as phase11ab_artifact_dir
from physics_lab.physics.phase14c5j_p5j import artifact_dir as phase14c5j_artifact_dir
from physics_lab.physics.phase14c5k_p5k import artifact_dir as phase14c5k_artifact_dir
from physics_lab.physics.phase11ac_class_b_resolution import CLASS_CDE_ITEMS, analyze_phase11ac_class_b_resolution


def test_independent_resolution_does_not_mutate_parents():
    freeze_path, _ = freeze_paths()
    paths = {
        "freeze": freeze_path,
        "v": phase11v_artifact_dir() / "PHASE_11V_SUSY_MEDIATION.json",
        "x": phase11x_artifact_dir() / "PHASE_11X_GAUGE_MEDIATION.json",
        "y": phase11y_artifact_dir() / "PHASE_11Y_ANOMALY_MEDIATION.json",
        "z": phase11z_artifact_dir() / "PHASE_11Z_MODULUS_MEDIATION.json",
        "aa": phase11aa_artifact_dir() / "PHASE_11AA_DIRECT_MEDIATION.json",
        "ab": phase11ab_artifact_dir() / "PHASE_11AB_MEDIATION_SYNTHESIS.json",
        "p5j": phase14c5j_artifact_dir() / "PHASE_14C5J_SUMMARY.json",
        "p5k": phase14c5k_artifact_dir() / "PHASE_14C5K_SUMMARY.json",
    }
    before = {key: path.read_bytes() for key, path in paths.items()}
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11ac_class_b_resolution(auth)
    for key, path in paths.items():
        assert path.read_bytes() == before[key], key
    assert sci["status"] == "OK"
    assert sci["T04_STATUS"] == "PARTIAL"
    assert sci["T05_STATUS"] == "PARTIAL"
    assert sci["NEW_PHYSICAL_INPUT_STATUS"] is False
    assert sci["NEW_ASSUMPTION_STATUS"] is False
    assert sci["CLASS_CDE_EXECUTED"] is False
    for item in CLASS_CDE_ITEMS:
        assert sci["analysis"]["class_cde"][item] in {"NOT_ACTIVATED", "OPEN"}
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11ac_class_b_resolution.py",
        root / "models" / "examples" / "phase11ac_model.py",
        root / "reporting" / "phase11ac_report.py",
        root / "tests" / "phase11ac_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best" + "_" + "model" not in text
        assert "analyze_phase11y" + "_anomaly_mediation" not in text
        assert "analyze_phase11x" + "_gauge_mediation" not in text
        assert "two_loop_kinematic" + "_engine" not in text
