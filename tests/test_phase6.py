"""Phase 6: coupled consistency audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase6_model import build_phase6_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase6_coupled_consistency import BRANCH_I_ID, BRANCH_II_ID
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_integration_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase6_model(signature=sig).solve()
        sci = result.metadata["phase6_analysis"]
        integ = result.metadata["phase6_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert sci["INTEGRATION_STATUS"] == "CONSISTENT"
        assert sci["NEW_PARAMETER_FREE_RELATIONS"] == "NOT_FOUND"
        assert sci["AUTONOMOUS_GAUGE_SECTOR_REQUIRED"] == "NO"
        assert sci["GRAVITY_COEFFICIENTS_CONSTRAINED"] == "NO"
        assert sci["COUPLING_FIXED"] == "NO"
        assert sci["CROSS_SECTOR_UNIFICATION_STATUS"] == "UNCHANGED"
        assert sci["REPORT_UPDATE_STATUS"] == "REQUIRED"
        assert sci["branch_I_locally_consistent_without_F2"] is True
        assert sci["local_U1"]["Branch_I"] == "CONSISTENT"
        assert sci["local_U1"]["Branch_II"] == "CONSISTENT"
        assert sci["equations"]["I"]["A_mu_not_autonomous_wave_equation"] is True
        assert sci["equations"]["II"]["F2"] is True
        assert sci["current"]["C"] == 2
        assert sci["current"]["zero_connection_limit_matches_5b0"] is True
        assert sci["spectrum"]["absolute_masses_derived"] is False
        assert sci["stress"]["gauge_sector_modifies_c0_c1"] is False
        assert sci["F2_vs_connection"]["first_does_not_imply_second"] is True
        assert sci["frozen_action_modified"] is False
        assert sci["phase_5c_unchanged"] is True
        assert sci["phase_5d_unchanged"] is True
        assert sci["overclaim_tests_all_pass"] is True
        assert sci["negative_tests_all_pass"] is True
        assert sci["PHASE_6_CLOSED"] is True
        assert sci["BRANCH_I_ID"] == BRANCH_I_ID
        assert sci["BRANCH_II_ID"] == BRANCH_II_ID
        assert sci["scientific_questions"]["2_new_parameter_free_relation"] == "NO"
        assert sci["scientific_questions"]["7_branch_I_consistent_without_F2"] == "YES"
        oc = sci["overclaims"]
        assert oc["3_local_U1_requires_F2"] == "REJECTED AS OVERCLAIM"
        assert oc["7_F2_modifies_frozen_gravity_coefficients"] == "REJECTED AS OVERCLAIM"


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase6.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 6: pre-analysis gate",
        "Phase 6: coupled consistency",
        "Phase 6: gravity unchanged",
        "Phase 6: banned tokens",
        "Phase 6: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "OBJECTIVE" in text
    assert "SCOPE SUMMARY" in text
    assert text.index("OBJECTIVE") < text.index("SCOPE SUMMARY")
    assert "INTEGRATION_STATUS = CONSISTENT" in text
    assert "NEW_PARAMETER_FREE_RELATIONS = NOT_FOUND" in text
    assert "AUTONOMOUS_GAUGE_SECTOR_REQUIRED = NO" in text
    assert "BRANCH I" in text
    assert "BRANCH II" in text
    assert "PHASE 6 CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase6_coupled_consistency.py",
        root / "models" / "examples" / "phase6_model.py",
        root / "reporting" / "phase6_report.py",
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
