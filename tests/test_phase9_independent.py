"""Independent Phase 9 checks: freeze identity, closure, bans."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase9_internal_gap import analyze_phase9_internal_gap


def test_independent_closure_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase9_internal_gap(auth)
    after = freeze_path.read_bytes()
    assert before == after
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["INTERNAL_CLOSURE_STATUS"] == "CLOSED"
    assert sci["NEW_PARAMETER_FREE_RELATION"] == "NOT_FOUND"
    assert sci["REMAINING_INTERNAL_ROUTES"] == []
    assert sci["bianchi_route"]["bianchi_holds_identically"] is True
    assert sci["new_physics_implemented"] is False
    assert sci["promoted_to_new_freeze"] is False
    assert sci["phase_8_MINIMAL_PRINCIPLE_FOUND"] == "NO"
    assert sci["PHASE_9_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase9_internal_gap.py",
        root / "models" / "examples" / "phase9_model.py",
        root / "reporting" / "phase9_report.py",
        root / "tests" / "phase9_test.py",
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
