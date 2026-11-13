"""Phase 8: minimal additional-principle audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase8_model import build_phase8_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase8_minimal_principle import PHASE_8_TEST_COPIES_ID
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_principles_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase8_model(signature=sig).solve()
        sci = result.metadata["phase8_analysis"]
        integ = result.metadata["phase8_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert sci["MINIMAL_PRINCIPLE_FOUND"] == "NO"
        assert sci["SPECTRAL_FREEDOM_REDUCED"] == "NO"
        assert sci["MASS_COUPLING_FREEDOM_REDUCED"] == "NO"
        assert sci["GAUGE_NORMALIZATION_FREEDOM_REDUCED"] == "NO"
        assert sci["GRAVITY_FREEDOM_REDUCED"] == "NO"
        assert sci["NEW_PARAMETER_FREE_RELATION"] == "NOT_FOUND"
        assert sci["REPORT_UPDATE_STATUS"] == "REQUIRED"
        assert sci["principles_tested_one_at_a_time"] is True
        assert sci["second_principle_added_to_force_selection"] is False
        assert sci["SCIENTIFIC_STOP"] == "STOP"
        a = sci["principle_A"]
        assert a["outcome"] == "NO UNIQUE SPECTRAL RATIO"
        assert a["lambda_a_equals_lambda_b_forced"] is False
        assert a["details"]["n_independent_symmetric_entries_after_commutant"] == 2
        assert a["details"]["matches_frozen_two_parameter_family"] is True
        b = sci["principle_B"]
        assert b["function_class_declared_before_solving"] is True
        assert b["P_idempotent"] is True
        assert b["quadratic_reduces_to_linear"] is True
        assert b["linear_matches_frozen_family"] is True
        assert b["fixes_spectral_ratio"] is False
        assert b["equivalent_to_existing_commutant"] is True
        c = sci["principle_C"]
        assert c["there_exists_a_Laplacian_is_unique_geometry"] is False
        assert c["geometry_chosen_from_desired_spectrum"] is False
        assert c["CONSTRAINT_GAIN"] == 0
        d = sci["principle_D"]
        assert d["ad_hoc_potential_introduced"] is False
        assert d["stationarity_distinct_from_stability"] is True
        e = sci["principle_E"]
        assert e["parameter_free_mass_coupling_relation"] is False
        f = sci["principle_F"]
        assert f["set_all_coefficients_to_one_is_derivation"] is False
        assert f["equivalent_to_convention"] is True
        g = sci["principle_G"]
        assert g["notions_merged"] is False
        assert g["unique_values"] is False
        assert g["main_test"] == "PARTIAL"
        assert sci["frozen_action_modified"] is False
        assert sci["phase_7_unchanged"] is True
        assert sci["overclaim_tests_all_pass"] is True
        assert sci["negative_tests_all_pass"] is True
        assert sci["PHASE_8_CLOSED"] is True
        assert sci["PHASE_8_TEST_COPIES_ID"] == PHASE_8_TEST_COPIES_ID
        assert sci["scientific_questions"]["1_single_principle_removed_genuine_freedom"] == "NO"
        assert sci["scientific_questions"]["2_unique_spectral_ratio_from_representation"] == "NO UNIQUE SPECTRAL RATIO"
        oc = sci["overclaims"]
        assert oc["2_choose_geometry_from_resulting_spectrum"] == "REJECTED AS OVERCLAIM"
        assert oc["7_combine_assumptions_attribute_to_one"] == "REJECTED AS OVERCLAIM"
        assert integ["PHASE_8_TEST_COPIES"] == "SEPARATE"
        assert integ["NUMERICAL_TARGET_SEARCH"] == "NONE"


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase8.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 8: pre-analysis gate",
        "Phase 8: isolated principles",
        "Phase 8: gravity unchanged",
        "Phase 8: no numerical target search",
        "Phase 8: banned tokens",
        "Phase 8: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "OBJECTIVE" in text
    assert "SCOPE SUMMARY" in text
    assert text.index("OBJECTIVE") < text.index("SCOPE SUMMARY")
    assert "MINIMAL_PRINCIPLE_FOUND = NO" in text
    assert "NO UNIQUE SPECTRAL RATIO" in text
    assert "PHASE 8 CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "WHAT THE OLD MODEL DERIVES" in text
    assert "WHAT THE NEW PRINCIPLE ASSUMES" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase8_minimal_principle.py",
        root / "models" / "examples" / "phase8_model.py",
        root / "reporting" / "phase8_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "from physics_lab.physics." + "gauge_internal",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
