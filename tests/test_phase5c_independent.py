"""Independent Phase 5C checks: gate, covariance, Noether matching, bans."""

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
    analyze_phase5c_gauging,
    gauge_dynamics_status,
    so2_generator_K,
)


def test_independent_gauging_and_noether_match():
    freeze_path, _ = freeze_paths()
    before = freeze_path.read_bytes()
    auth = authorize_phase5b0_analysis()
    sci = analyze_phase5c_gauging(auth)
    after = freeze_path.read_bytes()
    assert before == after
    assert sci["status"] == "OK"
    assert sci["action_integrity"] == "VERIFIED"
    assert sci["final_action_hash"] == auth.action_content_hash
    assert sci["action_content_hash"] == EXPECTED_FROZEN_HASH
    assert sci["case"] == "LOCAL U(1) CONSISTENT"
    assert sci["GAUGING_STATUS"] == "CONSISTENT"
    assert sci["GAUGE_DYNAMICS_STATUS"] == GAUGE_DYNAMICS_STATUS_5C
    assert sci["local_U1"] is True
    assert sci["GAUGED_MATTER_TEST_ACTION_ID"] == GAUGED_MATTER_TEST_ACTION_ID
    assert GAUGED_MATTER_TEST_ACTION_ID != FREEZE_ID
    assert sci["promoted_to_new_freeze"] is False
    k = so2_generator_K()
    assert k.T == -k
    cov = sci["covariance"]
    assert cov["ordinary_derivative_fails_for_local_alpha"] is True
    assert cov["covariant_derivative_succeeds"] is True
    assert cov["wrong_sign_fails"] is True
    assert cov["removing_connection_fails"] is True
    assert cov["exp_closed_form_matches"] is True
    assert sci["F_mu_nu"]["invariant"] is True
    assert sci["interaction"]["C"] == 2
    assert sci["interaction"]["linear_matches_noether"] is True
    assert sci["H_int_compatible"] is True
    assert sci["g_introduced"] is False
    assert sci["ZA_introduced"] is False
    assert sci["phys_coupling_introduced"] is False
    assert sci["gravity_changed"] is False
    assert sci["PROPAGATING_GAUGE_DOF"] == "NOT ESTABLISHED"
    assert sci["GAUGE_DYNAMICS"] == "NOT TESTED / NOT INCLUDED"
    assert sci["GAUGE_CONNECTION"] == "GAUGE CONNECTION"
    assert sci["GAUGE_CONNECTION_STATUS"] == "PRESENT IN THE GAUGED MATTER TEST ACTION"
    assert sci["gauge_kinetic_term"] == "ABSENT IN PHASE 5C"
    assert sci["interaction"]["quadratic_term_is_gauge_kinetic"] is False
    assert sci["interaction"]["classification"] == "ALGEBRAIC MATTER-SECTOR RESPONSE TO THE CONNECTION"
    assert sci["interaction"]["called_gauge_field_eom"] is False
    assert sci["interaction"]["gauge_field_dof_counted"] is False
    assert sci["PHASE_5C_CLOSED"] is True
    assert sci["Q_rep_gJ_defined"] is False
    assert sci["overclaim_tests_all_pass"] is True
    assert sci["negative_tests_all_pass"] is True
    assert sci["negative_tests"]["5_F2_only_on_dynamics_test_copy"] is True
    assert sci["negative_tests"]["6_absence_of_F2_is_not_gauging_failure"] is True
    assert sci["negative_tests"]["11_no_independent_gauge_dof_counted"] is True
    assert sci["negative_tests"]["12_linear_matches_noether_C"] is True
    assert sci["claims"]["A_connection_present"] == "CONNECTION PRESENT"
    assert sci["future_gauge_dynamics"]["implemented"] is False
    assert sci["future_gauge_dynamics"]["title"] == "PHASE 5D — GAUGE DYNAMICS"
    assert sci["levels"]["3_gauge_dynamics"]["status"] == GAUGE_DYNAMICS_STATUS_5C
    scope = sci["scope_summary"]
    assert "alpha(x)" in scope["in_scope"]
    assert "gauge-field dynamics" in scope["out_of_scope"]
    assert "Phase 4C action hash" in scope["immutable"]
    assert scope["next_phase"] == "PHASE 5D — GAUGE DYNAMICS."
    assert "SCOPE SUMMARY" in sci["scope_summary_text"]
    assert gauge_dynamics_status(gauging_status=sci["GAUGING_STATUS"]) == sci["GAUGE_DYNAMICS_STATUS"]
    ver = verify_phase4c_action_freeze()
    assert ver["status"] == "VERIFIED"
    assert ver["action_content_hash"] == EXPECTED_FROZEN_HASH


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase5c_gauging.py",
        root / "models" / "examples" / "phase5c_model.py",
        root / "reporting" / "phase5c_report.py",
        root / "tests" / "phase5c_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "from physics_lab.physics.gauge_internal" not in text
        assert "ALPHA" not in text
        assert "6." + "674" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "non-dynamical" not in text
        assert "auxiliary field" not in text
        assert "pho" + "ton" not in text
