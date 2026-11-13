"""Phase 9: final internal gap audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase9_model import build_phase9_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase9_internal_gap import PHASE_9_TEST_COPY_ID
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_closure_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase9_model(signature=sig).solve()
        sci = result.metadata["phase9_analysis"]
        integ = result.metadata["phase9_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert sci["INTERNAL_CLOSURE_STATUS"] == "CLOSED"
        assert sci["EOM_COVERAGE"] == "COMPLETE"
        assert sci["REPRESENTATION_COVERAGE"] == "COMPLETE"
        assert sci["OPERATOR_COVERAGE"] == "COMPLETE"
        assert sci["SPECTRAL_CLOSURE"] == "COMPLETE"
        assert sci["MASS_CHARGE_COUPLING_CLOSURE"] == "COMPLETE"
        assert sci["NORMALIZATION_CLOSURE"] == "COMPLETE"
        assert sci["GRAVITY_CLOSURE"] == "COMPLETE"
        assert sci["GAUGE_DYNAMICS_CLOSURE"] == "COMPLETE"
        assert sci["CROSS_SECTOR_CLOSURE"] == "COMPLETE"
        assert sci["GLOBAL_BOUNDARY_CLOSURE"] == "COMPLETE"
        assert sci["CONSTRAINT_CLOSURE"] == "COMPLETE"
        assert sci["DIMENSIONAL_CLOSURE"] == "COMPLETE"
        assert sci["NEW_PARAMETER_FREE_RELATION"] == "NOT_FOUND"
        assert sci["CONSERVATION_CONSTRAINT_GAIN"] == "NONE"
        assert sci["REMAINING_INTERNAL_ROUTES"] == []
        assert sci["REPORT_UPDATE_STATUS"] == "REQUIRED"
        assert sci["new_physics_implemented"] is False
        assert sci["SCIENTIFIC_STOP"] == "STOP"
        bianchi = sci["bianchi_route"]
        assert bianchi["bianchi_holds_identically"] is True
        assert bianchi["double_divergence_vanishes_by_antisymmetry"] is True
        assert bianchi["new_parameter_relation"] is False
        assert bianchi["new_physics_introduced"] is False
        assert sci["representation"]["commutant_independent_entries"] == 2
        assert sci["representation"]["ratio_constrained"] is False
        assert sci["operator"]["P_idempotent"] is True
        assert len(sci["REMAINING_ROUTES_REQUIRING_NEW_PHYSICS"]) >= 5
        assert sci["frozen_action_modified"] is False
        assert sci["phase_8_unchanged"] is True
        assert sci["overclaim_tests_all_pass"] is True
        assert sci["negative_tests_all_pass"] is True
        assert sci["PHASE_9_CLOSED"] is True
        assert sci["PHASE_9_TEST_COPY_ID"] == PHASE_9_TEST_COPY_ID
        assert sci["scientific_questions"]["1_untested_internal_consequence"] == "NO"
        assert sci["scientific_questions"]["3_internal_closure"] == "YES"
        assert sci["scientific_questions"]["7_absolute_mass_scale"] == "NO"
        assert sci["scientific_questions"]["8_absolute_gauge_coupling"] == "NO"
        oc = sci["overclaims"]
        assert oc["9_introduce_F2_as_forced_by_local_U1"] == "REJECTED AS OVERCLAIM"
        assert oc["12_search_for_fine_structure"] == "REJECTED AS OVERCLAIM"
        assert integ["PHASE_9_TEST_COPY"] == "SEPARATE"


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase9.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 9: pre-analysis gate",
        "Phase 9: internal closure",
        "Phase 9: gravity unchanged",
        "Phase 9: no numerical target search",
        "Phase 9: banned tokens",
        "Phase 9: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "OBJECTIVE" in text
    assert "SCOPE SUMMARY" in text
    assert text.index("OBJECTIVE") < text.index("SCOPE SUMMARY")
    assert "INTERNAL_CLOSURE_STATUS = CLOSED" in text
    assert "NEW_PARAMETER_FREE_RELATION = NOT_FOUND" in text
    assert "PHASE 9 CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "REMAINING_INTERNAL_ROUTES" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase9_internal_gap.py",
        root / "models" / "examples" / "phase9_model.py",
        root / "reporting" / "phase9_report.py",
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
