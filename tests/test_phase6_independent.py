"""Independent Phase 6 checks: freeze identity, statuses, bans."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH, GAUGE_DYNAMICS_STATUS_5C
from physics_lab.physics.phase6_coupled_consistency import analyze_phase6_coupled_consistency


def test_independent_integration_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase6_coupled_consistency(auth)
    after = freeze_path.read_bytes()
    assert before == after
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["INTEGRATION_STATUS"] == "CONSISTENT"
    assert sci["NEW_PARAMETER_FREE_RELATIONS"] == "NOT_FOUND"
    assert sci["AUTONOMOUS_GAUGE_SECTOR_REQUIRED"] == "NO"
    assert sci["GRAVITY_COEFFICIENTS_CONSTRAINED"] == "NO"
    assert sci["COUPLING_FIXED"] == "NO"
    assert sci["CROSS_SECTOR_UNIFICATION_STATUS"] == "UNCHANGED"
    assert sci["phase_5c_GAUGE_DYNAMICS_STATUS"] == GAUGE_DYNAMICS_STATUS_5C
    assert sci["phase_5d_GAUGE_DYNAMICS_STATUS"] == "NOT_DETERMINED"
    assert sci["promoted_to_new_freeze"] is False
    assert sci["layers"]["C_is_not_a_consequence_of_A"] is True
    assert sci["PHASE_6_CLOSED"] is True
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase6_coupled_consistency.py",
        root / "models" / "examples" / "phase6_model.py",
        root / "reporting" / "phase6_report.py",
        root / "tests" / "phase6_test.py",
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
