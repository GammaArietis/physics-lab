"""Independent Phase 5D checks: freeze identity, classification, bans."""

from __future__ import annotations

from pathlib import Path

from physics_lab.physics.phase4c_action_freeze import (
    FREEZE_ID,
    authorize_phase5b0_analysis,
    freeze_paths,
    verify_phase4c_action_freeze,
)
from physics_lab.physics.phase5c_gauging import (
    EXPECTED_FROZEN_HASH,
    GAUGED_MATTER_TEST_ACTION_ID,
    GAUGE_DYNAMICS_STATUS_5C,
)
from physics_lab.physics.phase5d_gauge_dynamics import (
    GAUGE_DYNAMICS_TEST_ACTION_ID,
    analyze_phase5d_gauge_dynamics,
)


def test_independent_classification_and_freeze_identity():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase5d_gauge_dynamics(auth)
    after = freeze_path.read_bytes()
    assert before == after
    assert sci["status"] == "OK"
    assert sci["action_integrity"] == "VERIFIED"
    assert sci["final_action_hash"] == auth.action_content_hash
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["GAUGE_DYNAMICS_FROM_EXISTING_ACTION"] == "NOT DERIVED"
    assert sci["GAUGE_DYNAMICS_STATUS"] == "NOT_DETERMINED"
    assert sci["MAXWELL_BENCHMARK_STATUS"] == "VERIFIED"
    assert sci["PROPAGATION_STATUS"] == "ESTABLISHED"
    assert sci["PROPAGATION_STATUS_PROVENANCE"] == "ESTABLISHED IN F^2 TEST COPY"
    assert sci["claims"]["C_frozen_theory_requires_autonomous_F2"] == "NO / NOT DETERMINED"
    assert sci["overclaim_tests_all_pass"] is True
    assert sci["COUPLING_STATUS"] == "DERIVED_AS_NORMALIZATION_RELATION"
    assert sci["phase_5c_GAUGE_DYNAMICS_STATUS"] == GAUGE_DYNAMICS_STATUS_5C
    assert sci["GAUGED_MATTER_TEST_ACTION_ID"] == GAUGED_MATTER_TEST_ACTION_ID
    assert sci["GAUGE_DYNAMICS_TEST_ACTION_ID"] == GAUGE_DYNAMICS_TEST_ACTION_ID
    assert GAUGED_MATTER_TEST_ACTION_ID != GAUGE_DYNAMICS_TEST_ACTION_ID
    assert sci["promoted_to_new_freeze"] is False
    assert sci["FREEZE_ID"] == FREEZE_ID
    assert sci["interaction_current"]["zero_connection_limit_matches_5b0"] is True
    assert sci["proca"]["gauge_invariant"] is False
    assert sci["higher_order"]["gauge_invariance_alone_selects_Maxwell"] is False
    assert sci["local_u1_does_not_imply_maxwell"] is True
    assert sci["canonical_normalization"]["g_inserted_before_normalization"] is False
    assert sci["gravity_changed"] is False
    assert sci["PHASE_5D_CLOSED"] is True
    ver = verify_phase4c_action_freeze()
    assert ver["status"] == "VERIFIED"
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase5d_gauge_dynamics.py",
        root / "models" / "examples" / "phase5d_model.py",
        root / "reporting" / "phase5d_report.py",
        root / "tests" / "phase5d_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "from physics_lab.physics.gauge_internal" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "6." + "674" not in text
