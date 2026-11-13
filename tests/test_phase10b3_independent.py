"""Independent Phase 10B.3 checks: freeze identity, prior-artifact isolation."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10b3_audit import (
    analyze_phase10b3_audit,
    snapshot_prior_artifact_hashes,
)


def test_independent_audit_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before_freeze = freeze_path.read_bytes()
    before_prior = snapshot_prior_artifact_hashes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase10b3_audit(auth)
    after_freeze = freeze_path.read_bytes()
    after_prior = snapshot_prior_artifact_hashes()
    assert before_freeze == after_freeze
    assert before_prior == after_prior
    assert sci["status"] == "OK"
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["audit_summary"]["syntactic_candidates"] == 8
    assert sci["audit_summary"]["TOTAL_GENERATED"] == 8
    assert sci["audit_summary"]["new_physical_assumptions"] == 0
    assert sci["audit_summary"]["grammar_changes"] == 0
    assert sci["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert sci["known_physics_comparison_executed"] is False
    assert sci["phase_10c_executed"] is False
    assert sci["candidates_repaired"] is False
    assert sci["models_merged"] is False
    assert sci["PHASE_10B3_CLOSED"] is True
    assert sci["SCIENTIFIC_STOP"] == "STOP"
    ver = verify_phase4c_action_freeze()
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10b3_audit.py",
        root / "models" / "examples" / "phase10b3_model.py",
        root / "reporting" / "phase10b3_report.py",
        root / "tests" / "phase10b3_test.py",
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
