"""Independent Phase 7 checks: freeze identity, statuses, bans."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase7_structural_selection import analyze_phase7_structural_selection


def test_independent_selection_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase7_structural_selection(auth)
    after = freeze_path.read_bytes()
    assert before == after
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["STRUCTURAL_SELECTION_STATUS"] == "NOT_FOUND"
    assert sci["SPECTRAL_RATIO_SELECTION"] == "NOT_DETERMINED"
    assert sci["GRAVITY_PARAMETER_SELECTION"] == "NOT_FOUND"
    assert sci["GAUGE_NORMALIZATION_SELECTION"] == "NOT_FOUND"
    assert sci["MASS_COUPLING_RELATION"] == "NOT_FOUND"
    assert sci["VARIATIONAL_SELECTION_STATUS"] == "NOT_FOUND"
    assert sci["NEW_PARAMETER_FREE_CONSTANT"] == "NOT_FOUND"
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    assert sci["promoted_to_new_freeze"] is False
    assert sci["phase_6_NEW_PARAMETER_FREE_RELATIONS"] == "NOT_FOUND"
    assert sci["PHASE_7_CLOSED"] is True
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase7_structural_selection.py",
        root / "models" / "examples" / "phase7_model.py",
        root / "reporting" / "phase7_report.py",
        root / "tests" / "phase7_test.py",
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
