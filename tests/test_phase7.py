"""Phase 7: structural parameter-selection audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase7_model import build_phase7_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase7_structural_selection import PHASE_7_TEST_COPY_ID
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_selection_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase7_model(signature=sig).solve()
        sci = result.metadata["phase7_analysis"]
        integ = result.metadata["phase7_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert sci["STRUCTURAL_SELECTION_STATUS"] == "NOT_FOUND"
        assert sci["SPECTRAL_SELECTION_STATUS"] == "NOT_DETERMINED"
        assert sci["SPECTRAL_RATIO_SELECTION"] == "NOT_DETERMINED"
        assert sci["GRAVITY_SELECTION_STATUS"] == "NOT_FOUND"
        assert sci["GRAVITY_PARAMETER_SELECTION"] == "NOT_FOUND"
        assert sci["GAUGE_NORMALIZATION_SELECTION"] == "NOT_FOUND"
        assert sci["MASS_COUPLING_RELATION"] == "NOT_FOUND"
        assert sci["VARIATIONAL_SELECTION_STATUS"] == "NOT_FOUND"
        assert sci["NEW_PARAMETER_FREE_CONSTANT"] == "NOT_FOUND"
        assert sci["REPORT_UPDATE_STATUS"] == "REQUIRED"
        assert sci["central_answer"] == "NO, freedom remains."
        assert sci["successful_negative_result"] is True
        assert sci["SCIENTIFIC_STOP"] == "STOP"
        assert sci["further_interaction_added_to_force_positive"] is False
        assert sci["spectral"]["K_commutes_for_generic_ratio"] is True
        assert sci["spectral"]["ratio_scan_performed"] is False
        assert sci["spectral"]["preferred_ratio_inserted"] is False
        assert sci["mass_coupling"]["statement"] == "NO PARAMETER-FREE MASS-COUPLING RELATION FOUND."
        assert sci["variational"]["ad_hoc_effective_potential_introduced"] is False
        assert sci["variational"]["stationarity_distinct_from_stability"] is True
        assert sci["minimality"]["undefined_minimality_used_as_rescue"] is False
        assert sci["minimality"]["unique_value_derived"] is False
        assert sci["dimensionless"]["numerical_pattern_matching"] is False
        assert sci["no_target_search"]["NUMERICAL_TARGET_SEARCH"] == "NONE"
        assert sci["frozen_action_modified"] is False
        assert sci["phase_5c_unchanged"] is True
        assert sci["phase_5d_unchanged"] is True
        assert sci["phase_6_unchanged"] is True
        assert sci["overclaim_tests_all_pass"] is True
        assert sci["negative_tests_all_pass"] is True
        assert sci["PHASE_7_CLOSED"] is True
        assert sci["PHASE_7_TEST_COPY_ID"] == PHASE_7_TEST_COPY_ID
        assert sci["scientific_questions"]["1_existing_principle_reduced_freedom"] == "NO"
        assert sci["scientific_questions"]["2_spectral_ratio_uniquely_selected"] == "NO"
        assert "FOUND" not in (
            sci["STRUCTURAL_SELECTION_STATUS"],
            sci["GRAVITY_SELECTION_STATUS"],
            sci["GAUGE_NORMALIZATION_SELECTION"],
            sci["MASS_COUPLING_RELATION"],
            sci["VARIATIONAL_SELECTION_STATUS"],
            sci["NEW_PARAMETER_FREE_CONSTANT"],
        )
        oc = sci["overclaims"]
        assert oc["1_fix_by_inserting_desired_value"] == "REJECTED AS OVERCLAIM"
        assert oc["5_canonical_normalization_as_physical_prediction"] == "REJECTED AS OVERCLAIM"
        assert oc["10_call_convention_a_physical_constraint"] == "REJECTED AS OVERCLAIM"
        assert integ["EXPERIMENTAL_INPUTS"] == "NONE"
        assert integ["FITTING"] == "NONE"
        assert integ["CALIBRATION"] == "NONE"
        assert integ["NUMERICAL_TARGET_SEARCH"] == "NONE"
        assert integ["PHASE_7_TEST_COPY"] == "SEPARATE"


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase7.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 7: pre-analysis gate",
        "Phase 7: structural selection",
        "Phase 7: gravity unchanged",
        "Phase 7: no numerical target search",
        "Phase 7: banned tokens",
        "Phase 7: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "OBJECTIVE" in text
    assert "SCOPE SUMMARY" in text
    assert text.index("OBJECTIVE") < text.index("SCOPE SUMMARY")
    assert "STRUCTURAL_SELECTION_STATUS = NOT_FOUND" in text
    assert "SPECTRAL_SELECTION_STATUS = NOT_DETERMINED" in text
    assert "GRAVITY_SELECTION_STATUS = NOT_FOUND" in text
    assert "NO PARAMETER-FREE MASS-COUPLING RELATION FOUND." in text
    assert "PHASE 7 CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "NUMERICAL_TARGET_SEARCH" in text or "no numerical target" in text.lower()


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase7_structural_selection.py",
        root / "models" / "examples" / "phase7_model.py",
        root / "reporting" / "phase7_report.py",
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
