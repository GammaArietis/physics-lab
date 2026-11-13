"""Independent Phase 10E checks: freeze identity, isolation, no feedback."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10c_interpretation import artifact_dir as phase10c_artifact_dir
from physics_lab.physics.phase10d_equivalence import artifact_dir as phase10d_artifact_dir
from physics_lab.physics.phase10e_synthesis import analyze_phase10e_synthesis


def test_independent_synthesis_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    catalog_b = phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json"
    catalog_c = phase10c_artifact_dir() / "PHASE_10C_INTERPRETATION_CATALOG.json"
    catalog_d = phase10d_artifact_dir() / "PHASE_10D_EQUIVALENCE_CATALOG.json"
    before_freeze = freeze_path.read_bytes()
    before_b = catalog_b.read_bytes()
    before_c = catalog_c.read_bytes()
    before_d = catalog_d.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase10e_synthesis(auth)
    after_freeze = freeze_path.read_bytes()
    after_b = catalog_b.read_bytes()
    after_c = catalog_c.read_bytes()
    after_d = catalog_d.read_bytes()
    assert before_freeze == after_freeze
    assert before_b == after_b
    assert before_c == after_c
    assert before_d == after_d
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["TARGET_ISOLATION_STATUS"] == "VERIFIED"
    assert sci["NO_RANKING_STATUS"] == "VERIFIED"
    assert sci["NO_FEEDBACK_STATUS"] == "VERIFIED"
    assert sci["models_generated"] == 0
    assert sci["PROGRAM_CLOSURE_STATUS"] == "CLOSED_UNDER_DECLARED_SCOPE"
    assert sci["PHASE_10E_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    assert sci["QUANTUM_SCOPE_STATUS"] == "PARTIAL"
    assert sci["FINAL_PARAMETER_FREE_RELATION_COUNT"] == 0
    assert sci["synthesis"]["unresolved_equivalences"]["pair_count"] == 8
    assert sci["synthesis"]["structural_multiplicity"]["catalogue_classes"] == 8
    assert sci["synthesis"]["structural_multiplicity"]["certified_equivalence_components"] == 4
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets_or_feedback():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10e_synthesis.py",
        root / "models" / "examples" / "phase10e_model.py",
        root / "reporting" / "phase10e_report.py",
        root / "tests" / "phase10e_test.py",
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
        assert "analyze_phase10b1" + "_exploration" not in text
        assert "analyze_phase10c" + "_interpretation" not in text
        assert "analyze_phase10d" + "_equivalence" not in text
        assert "best" + "_" + "model" not in text
        assert "preferred" + "_" + "model" not in text
