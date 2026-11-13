"""Independent Phase 12A checks: freeze identity, isolation, no 12B."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import declared_dependencies, grammar_hash
from physics_lab.physics.phase12a_grammar import (
    AXES,
    EXPECTED_GRAMMAR_HASH_10B,
    GRAMMAR_ID,
    analyze_phase12a_grammar,
    artifact_dir,
    grammar_hash_12a,
    snapshot_prior_artifact_hashes,
)


def test_independent_grammar_freeze_and_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_hash = grammar_hash()
    before_prior = snapshot_prior_artifact_hashes()
    grammar_freeze = artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json"
    before_12a = grammar_freeze.read_bytes() if grammar_freeze.is_file() else None
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase12a_grammar(auth)
    after_freeze = freeze_path.read_bytes()
    after_prior = snapshot_prior_artifact_hashes()
    assert before_freeze == after_freeze
    assert before_prior == after_prior
    assert grammar_hash() == before_hash == EXPECTED_GRAMMAR_HASH_10B
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["grammar_id"] == GRAMMAR_ID
    assert sci["grammar_hash"] == grammar_hash_12a()
    assert len(AXES) == 18
    assert sci["TARGET_BLINDNESS"] == "VERIFIED"
    assert sci["sampling"] is False
    assert sci["phase_12b_executed"] is False
    assert sci["PHASE_12A_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    assert sci["claim"] == "EXHAUSTIVE_OVER_EXPANDED_FINITE_GRAMMAR"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH
    declared_ids = {row["dependency_id"] for row in declared_dependencies()}
    assert "optional_F2_test_extension->A_mu" not in declared_ids
    assert sci["overclaims"]["5_start_brute_force_12B"] == "REJECTED AS OVERCLAIM"
    assert grammar_freeze.is_file()
    if before_12a is not None:
        assert grammar_freeze.read_bytes() == before_12a


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase12a_grammar.py",
        root / "models" / "examples" / "phase12a_model.py",
        root / "reporting" / "phase12a_report.py",
        root / "tests" / "phase12a_test.py",
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
        assert "KNOWN_PHYSICS_CATALOG" not in text
