"""Independent Phase 10B.2 checks: freeze identity, 10B.1 isolation, no targets."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10b2_derivation import (
    analyze_phase10b2_derivation,
    snapshot_phase10b1_hashes,
)


def test_independent_derivation_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_10b1 = snapshot_phase10b1_hashes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase10b2_derivation(auth)
    after_freeze = freeze_path.read_bytes()
    after_10b1 = snapshot_phase10b1_hashes()
    assert before_freeze == after_freeze
    assert before_10b1 == after_10b1
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["derivation_summary"]["candidates_analyzed"] == 8
    assert sci["derivation_summary"]["new_assumptions_introduced"] == 0
    assert sci["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert sci["known_physics_comparison_executed"] is False
    assert sci["phase_10c_executed"] is False
    assert sci["PHASE_10B2_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10b2_derivation.py",
        root / "models" / "examples" / "phase10b2_model.py",
        root / "reporting" / "phase10b2_report.py",
        root / "tests" / "phase10b2_test.py",
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
