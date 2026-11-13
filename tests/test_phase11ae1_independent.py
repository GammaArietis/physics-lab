"""Independent Phase 11AE.1: freeze identity, parents unchanged, no activation."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase11p_vacuum_selection import artifact_dir as phase11p_artifact_dir
from physics_lab.physics.phase11u_supergravity import artifact_dir as phase11u_artifact_dir
from physics_lab.physics.phase11z_modulus_mediation import artifact_dir as phase11z_artifact_dir
from physics_lab.physics.phase11ae_vacuum_selection import artifact_dir as phase11ae_artifact_dir
from physics_lab.physics.phase11ae_vacuum_selection import is_exact_mathematical_statement
from physics_lab.physics.phase11ae1_containment import analyze_phase11ae1_containment


def test_independent_gate_does_not_mutate_parents():
    freeze_path, _ = freeze_paths()
    paths = {
        "freeze": freeze_path,
        "p": phase11p_artifact_dir() / "PHASE_11P_VACUUM_SELECTION.json",
        "u": phase11u_artifact_dir() / "PHASE_11U_SUPERGRAVITY.json",
        "z": phase11z_artifact_dir() / "PHASE_11Z_MODULUS_MEDIATION.json",
        "ae": phase11ae_artifact_dir() / "PHASE_11AE_VACUUM_SELECTION.json",
    }
    before = {key: path.read_bytes() for key, path in paths.items()}
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase11ae1_containment(auth)
    for key, path in paths.items():
        assert path.read_bytes() == before[key], key
    assert sci["status"] == "OK"
    assert sci["CONTAINMENT_STATUS"] == "REQUIRES_NEW_ASSUMPTION"
    assert sci["CONTAINMENT_RECORD"] == "NOT_CONTAINED"
    assert sci["principle_activated"] is False
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_cannot_import_external_lowest_energy():
    assert is_exact_mathematical_statement("vacuum = lowest energy") is False
    auth = authorize_phase5b0_analysis()
    out = analyze_phase11ae1_containment(
        auth,
        write_artifacts=False,
        injected_statement="vacuum = lowest energy",
    )
    assert out["status"] == "STOP"
    assert out["VACUUM_SELECTION_PRINCIPLE"] == "NOT_FOUND"


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11ae1_containment.py",
        root / "models" / "examples" / "phase11ae1_model.py",
        root / "reporting" / "phase11ae1_report.py",
        root / "tests" / "phase11ae1_test.py",
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
        assert "analyze_phase11ae" + "_vacuum_selection" not in text
        assert "analyze_phase11u" + "_supergravity" not in text
        assert "analyze_phase11t" + "_susy_breaking" not in text
        assert "analyze_phase11z" + "_modulus_mediation" not in text
        assert "two_loop_kinematic" + "_engine" not in text
