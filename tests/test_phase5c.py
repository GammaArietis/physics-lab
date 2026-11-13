"""Phase 5C: local gauging of the derived global SO(2)."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase5c_model import build_phase5c_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import (
    EXPECTED_FROZEN_HASH,
    GAUGED_MATTER_TEST_ACTION_ID,
    GAUGE_DYNAMICS_STATUS_5C,
    gauge_dynamics_status,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_local_u1_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase5c_model(signature=sig).solve()
        sci = result.metadata["phase5c_analysis"]
        integ = result.metadata["phase5c_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert integ["ATOMIC_GATE"] == "VERIFIED"
        assert integ["ACTION_INTEGRITY"] == "VERIFIED"
        assert integ["CONCURRENCY_GUARD"] == "VERIFIED"
        assert integ["GAUGING_INVARIANCE_VERIFIED"] == "VERIFIED"
        assert integ["NO_GRAVITY_CHANGE"] == "VERIFIED"
        assert integ["ANALYSIS_ACTION_HASH"] == integ["FINAL_ACTION_HASH"]
        assert integ["GAUGED_TEST_ACTION_ID"] == GAUGED_MATTER_TEST_ACTION_ID
        assert freeze["fingerprint"] == integ["ANALYSIS_ACTION_HASH"]
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert sci["GAUGING_STATUS"] == "CONSISTENT"
        assert sci["GAUGE_DYNAMICS_STATUS"] == GAUGE_DYNAMICS_STATUS_5C
        assert sci["case"] == "LOCAL U(1) CONSISTENT"
        assert sci["local_U1"] is True
        assert sci["LOCAL_GAUGE_INVARIANCE"] == "YES"
        assert sci["PROPAGATING_GAUGE_DOF"] == "NOT ESTABLISHED"
        assert sci["GAUGE_CONNECTION"] == "GAUGE CONNECTION"
        assert sci["GAUGE_CONNECTION_STATUS"] == "PRESENT IN THE GAUGED MATTER TEST ACTION"
        assert sci["GAUGE_CONNECTION_INTERPRETATION"] == "gauge connection required for local covariance"
        assert sci["GAUGE_DYNAMICS"] == "NOT TESTED / NOT INCLUDED"
        assert sci["autonomous_gauge_dynamics"] == "NOT TESTED / NOT INCLUDED"
        assert sci["gauge_kinetic_term"] == "ABSENT IN PHASE 5C"
        assert sci["ZA_status"] == "NOT INTRODUCED"
        assert sci["claims"]["C_full_theory_has_no_possible_gauge_dynamics"] == "OUT OF SCOPE / MUST NOT BE MADE"
        assert "does not determine whether" in sci["conceptual_distinction"]
        assert sci["local_invariance_does_not_imply_propagation"] is True
        assert sci["connection_does_not_imply_kinetic_term"] is True
        assert sci["F_exists_does_not_imply_F2_in_action"] is True
        assert sci["PHASE_5C_CLOSED"] is True
        assert sci["Q_rep_gJ_defined"] is False
        assert sci["covariance"]["ordinary_derivative_fails_for_local_alpha"] is True
        assert sci["covariance"]["covariant_derivative_succeeds"] is True
        assert sci["covariance"]["wrong_sign_fails"] is True
        assert sci["covariance"]["removing_connection_fails"] is True
        assert sci["covariance"]["complexified_J_used"] is False
        assert sci["F_mu_nu"]["invariant"] is True
        assert sci["F_mu_nu"]["kinetic_term_included"] is False
        assert sci["F_mu_nu"]["field_strength"] == "CONNECTION CURVATURE / DEFINED"
        assert sci["F_mu_nu"]["F2_status"] == "ABSENT FROM PHASE 5C ACTION"
        assert sci["F_mu_nu"]["gauge_kinetic_dynamics"] == "ABSENT"
        assert sci["H_int_compatible"] is True
        assert sci["term_invariance"]["kinetic_terms"] is True
        assert sci["term_invariance"]["H_int_terms"] is True
        assert sci["interaction"]["linear_matches_noether"] is True
        assert sci["interaction"]["C"] == 2
        assert sci["interaction"]["quadratic_term_is_gauge_kinetic"] is False
        assert sci["interaction"]["classification"] == "ALGEBRAIC MATTER-SECTOR RESPONSE TO THE CONNECTION"
        assert sci["interaction"]["does_not_claim_fundamentally_nondynamical"] is True
        assert sci["interaction"]["called_gauge_field_eom"] is False
        assert sci["interaction"]["gauge_field_dof_counted"] is False
        assert sci["g_introduced"] is False
        assert sci["ZA_introduced"] is False
        assert sci["phys_coupling_introduced"] is False
        assert sci["mathcalA_decomposed_as_gA"] is False
        assert sci["experimental_constants"] is False
        assert sci["gravity_changed"] is False
        assert sci["frozen_action_modified"] is False
        assert sci["promoted_to_new_freeze"] is False
        assert sci["negative_tests_all_pass"] is True
        assert sci["negative_tests"]["1_connection_required_for_covariance"] is True
        assert sci["negative_tests"]["5_F2_only_on_dynamics_test_copy"] is True
        assert sci["negative_tests"]["6_absence_of_F2_is_not_gauging_failure"] is True
        assert sci["negative_tests"]["7_no_propagation_inferred_from_missing_F2"] is True
        assert sci["negative_tests"]["11_no_independent_gauge_dof_counted"] is True
        assert sci["negative_tests"]["12_linear_matches_noether_C"] is True
        assert sci["overclaim_tests_all_pass"] is True
        oc = sci["negative_tests"]["overclaims"]
        assert oc["A_no_F2_implies_dynamics_can_never_exist"] == "REJECTED AS OVERCLAIM"
        assert oc["B_no_F2_means_dynamics_not_included_in_5c"] == "ACCEPTED"
        assert oc["C_A_in_D_implies_propagating_gauge_field"] == "REJECTED"
        assert oc["D_A_in_D_implies_connection_present"] == "ACCEPTED"
        assert oc["E_no_F2_means_propagation_not_established"] == "ACCEPTED"
        assert oc["F_algebraic_variation_is_matter_response_not_theorem"] == "ACCEPTED"
        assert sci["GAUGING_INVARIANCE_VERIFIED"] is True
        assert sci["tag"] == "GAUGED_MATTER_TEST_ACTION"
        assert sci["future_gauge_dynamics"]["implemented"] is False
        assert sci["future_gauge_dynamics"]["title"] == "PHASE 5D — GAUGE DYNAMICS"
        assert sci["phase_5a_imported"] is False
        assert sci["chain"] == "EXACT GLOBAL U(1) -> CONSISTENT LOCAL GAUGING -> NO GAUGE DYNAMICS TESTED."
        scope = sci["scope_summary"]
        assert "consistent local gauging" in scope["tests_only"]
        assert "alpha(x)" in scope["in_scope"]
        assert "real gauge connection mathcal A_mu" in scope["in_scope"]
        assert "gauge kinetic term F_mu_nu F^mu_nu" in scope["out_of_scope"]
        assert "autonomous gauge-field action" in scope["out_of_scope"]
        assert "Phase 4C frozen action" in scope["immutable"]
        assert "Phase 4A/4B gravity family." in scope["immutable"]
        assert scope["final_output"]["GAUGE_DYNAMICS_STATUS"] == GAUGE_DYNAMICS_STATUS_5C
        assert scope["stop"] == "STOP after determining GAUGING_STATUS."
        assert scope["next_phase"] == "PHASE 5D — GAUGE DYNAMICS."
        assert "CONNECTION PRESENT does NOT imply GAUGE DYNAMICS ESTABLISHED." in scope["important_distinction"]
        assert "F_mu_nu DEFINED does NOT imply F_mu_nu F^mu_nu PRESENT IN THE ACTION." in scope["important_distinction"]
        assert "OBJECTIVE" in sci["objective"]
        assert "SCOPE SUMMARY" in sci["scope_summary_text"]
        assert ("g" + "_" + "phys") in scope["out_of_scope"]
        assert ("alp" + "ha_em" + " / 1/" + "13" + "7") in scope["out_of_scope"]


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase5c.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 5C: pre-analysis gate",
        "Phase 5C: gauging invariance",
        "Phase 5C: gravity unchanged",
        "Phase 5C: no coupling constants",
        "Phase 5C: banned tokens",
        "Phase 5C: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "ACTION_CONTENT_HASH:" in text
    assert "PRE_ANALYSIS_GATE:" in text
    assert "GAUGED_MATTER_TEST_ACTION" in text
    assert "GAUGING_STATUS:" in text
    assert "GAUGE_DYNAMICS_STATUS:" in text
    assert "NOT_TESTED_IN_5C" in text
    assert "LOCAL U(1) CONSISTENT" in text or "CONSISTENT" in text
    assert "NOT ESTABLISHED" in text
    assert "NOT INTRODUCED" in text
    assert "PHASE 5C CLOSED" in text
    assert "PHASE 5D" in text
    assert "PRESENT IN THE GAUGED MATTER TEST ACTION" in text
    assert "CONNECTION PRESENT" in text
    assert "does not determine whether" in text
    assert "OBJECTIVE" in text
    assert "SCOPE SUMMARY" in text
    assert "PHASE 5C TESTS ONLY:" in text
    assert "IN SCOPE:" in text
    assert "OUT OF SCOPE:" in text
    assert "IMMUTABLE:" in text
    assert "IMPORTANT DISTINCTION:" in text
    assert "does NOT imply" in text
    assert "GAUGE DYNAMICS ESTABLISHED" in text
    assert "F_mu_nu DEFINED" in text
    assert "STOP after determining GAUGING_STATUS." in text
    assert text.index("OBJECTIVE") < text.index("SCOPE SUMMARY")
    assert ("alp" + "ha_em") in text
    assert ("1/" + "13" + "7") in text
    assert EXPECTED_FROZEN_HASH in text


def test_dynamics_status_independent_of_gauging():
    assert gauge_dynamics_status(gauging_status="CONSISTENT") == GAUGE_DYNAMICS_STATUS_5C
    assert gauge_dynamics_status(gauging_status="OBSTRUCTED") == GAUGE_DYNAMICS_STATUS_5C
    assert gauge_dynamics_status(gauging_status="REQUIRES_ADDITIONAL_ASSUMPTION") == GAUGE_DYNAMICS_STATUS_5C
    assert gauge_dynamics_status() == GAUGE_DYNAMICS_STATUS_5C


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase5c_gauging.py",
        root / "models" / "examples" / "phase5c_model.py",
        root / "reporting" / "phase5c_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "13" + "7.036",
        "alp" + "ha_em",
        "electr" + "ic",
        "g_" + "phys",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "from physics_lab.physics." + "gauge_internal",
        "6." + "674",
        "non-dynamical",
        "auxiliary field",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
