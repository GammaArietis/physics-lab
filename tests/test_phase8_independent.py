"""Independent Phase 8 checks: freeze identity, isolation, bans."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase8_minimal_principle import analyze_phase8_minimal_principle


def test_independent_principles_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase8_minimal_principle(auth)
    after = freeze_path.read_bytes()
    assert before == after
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["MINIMAL_PRINCIPLE_FOUND"] == "NO"
    assert sci["NEW_PARAMETER_FREE_RELATION"] == "NOT_FOUND"
    assert sci["principles_tested_one_at_a_time"] is True
    assert sci["second_principle_added_to_force_selection"] is False
    assert sci["principle_A"]["outcome"] == "NO UNIQUE SPECTRAL RATIO"
    assert sci["principle_B"]["P_idempotent"] is True
    assert sci["promoted_to_new_freeze"] is False
    assert sci["phase_7_STRUCTURAL_SELECTION_STATUS"] == "NOT_FOUND"
    assert sci["PHASE_8_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase8_minimal_principle.py",
        root / "models" / "examples" / "phase8_model.py",
        root / "reporting" / "phase8_report.py",
        root / "tests" / "phase8_test.py",
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
