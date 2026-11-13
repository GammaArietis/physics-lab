"""Independent Phase 10A checks: freeze identity, isolation, bans."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import analyze_phase10a_infrastructure


def test_independent_infrastructure_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase10a_infrastructure(auth)
    after = freeze_path.read_bytes()
    assert before == after
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["MODEL_GRAMMAR_STATUS"] == "READY"
    assert sci["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert sci["KNOWN_PHYSICS_ISOLATION_STATUS"] == "VERIFIED"
    assert sci["MANDATORY_RULES_STATUS"] == "VERIFIED"
    assert sci["REFERENCE_SEPARATION_STATUS"] == "VERIFIED"
    assert sci["EXAMPLE_SEPARATION_STATUS"] == "VERIFIED"
    assert sci["GRAMMAR_REGISTRATION_STATUS"] == "VERIFIED"
    assert sci["WHITELIST_STATUS"] == "VERIFIED"
    assert sci["BLACKLIST_STATUS"] == "VERIFIED"
    assert sci["large_scale_generation_executed"] is False
    assert sci["promoted_to_new_freeze"] is False
    assert sci["phase_9_INTERNAL_CLOSURE_STATUS"] == "CLOSED"
    assert sci["PHASE_10A_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10a_model_grammar.py",
        root / "models" / "examples" / "phase10a_model.py",
        root / "reporting" / "phase10a_report.py",
        root / "tests" / "phase10a_test.py",
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
        assert "phase10a_known_physics" not in text
