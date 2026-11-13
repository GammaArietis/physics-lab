"""Phase 5D: autonomous gauge-dynamics classification."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase5d_model import build_phase5d_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH, GAUGE_DYNAMICS_STATUS_5C
from physics_lab.physics.phase5d_gauge_dynamics import GAUGE_DYNAMICS_TEST_ACTION_ID
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_classification_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase5d_model(signature=sig).solve()
        sci = result.metadata["phase5d_analysis"]
        integ = result.metadata["phase5d_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert integ["ATOMIC_GATE"] == "VERIFIED"
        assert integ["ACTION_INTEGRITY"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert freeze["fingerprint"] == integ["ANALYSIS_ACTION_HASH"]
        assert sci["GAUGE_DYNAMICS_FROM_EXISTING_ACTION"] == "NOT DERIVED"
        assert sci["GAUGE_DYNAMICS_STATUS"] == "NOT_DETERMINED"
        assert sci["GAUGE_DYNAMICS_STATUS"] != "DERIVED"
        assert "NOT REQUIRED by the frozen" in sci["GAUGE_DYNAMICS_STATUS_INTERPRETATION"]
        assert sci["GAUGE_DYNAMICS_STATUS_FROM_FROZEN_PRE5D"] == "NOT DETERMINED"
        assert sci["GAUGE_DYNAMICS_STATUS_GAUGE_INVARIANCE_ALONE"] == "NOT_DETERMINED"
        assert sci["GAUGE_DYNAMICS_STATUS_TEST_COPY_INSERTION"] == "ALLOWED_BUT_ASSUMED"
        assert sci["GAUGE_DYNAMICS_STATUS_UNDER_BENCHMARK"] == "DERIVED GIVEN MINIMAL GAUGE-DYNAMICS BENCHMARK"
        assert sci["MAXWELL_BENCHMARK_STATUS"] == "VERIFIED"
        assert sci["PROPAGATION_STATUS"] == "ESTABLISHED"
        assert sci["PROPAGATION_STATUS_PROVENANCE"] == "ESTABLISHED IN F^2 TEST COPY"
        assert sci["PROPAGATION_STATUS_5C"] == "NOT_ESTABLISHED"
        assert sci["claims"]["A_gauge_invariance_permits_F2"] == "YES"
        assert sci["claims"]["B_benchmark_selects_F2"] == "YES, under the benchmark"
        assert sci["claims"]["C_frozen_theory_requires_autonomous_F2"] == "NO / NOT DETERMINED"
        assert sci["overclaim_tests_all_pass"] is True
        assert sci["COUPLING_STATUS"] == "DERIVED_AS_NORMALIZATION_RELATION"
        assert sci["phase_5c_GAUGE_DYNAMICS_STATUS"] == GAUGE_DYNAMICS_STATUS_5C
        assert sci["phase_5c_unchanged"] is True
        assert sci["frozen_action_modified"] is False
        assert sci["promoted_to_new_freeze"] is False
        assert sci["quadratic_invariants"]["invariant_quadratic_dimension"] == 2
        assert sci["parity_odd"]["four_dimensional_total_derivative"] is True
        assert sci["parity_odd"]["counted_as_independent_propagating_kinetic_sector"] is False
        assert sci["minimal_benchmark"]["unique_nontopological_quadratic_kinetic_term"] is True
        assert sci["minimal_benchmark"]["not_derived_from_frozen_action"] is True
        assert sci["higher_order"]["gauge_invariance_alone_selects_Maxwell"] is False
        assert sci["higher_order"]["added_to_primary_test_action"] is False
        assert sci["proca"]["classification"] == "NOT GAUGE INVARIANT"
        assert sci["interaction_current"]["zero_connection_limit_matches_5b0"] is True
        assert sci["interaction_current"]["C_matter"] == 2
        assert sci["gauge_el"]["matches_implemented_variation"] is True
        assert sci["propagating_dof"]["independent_local_propagating_gauge_dof"] == 2
        assert sci["positivity"]["healthy_condition"] == "Z_A > 0"
        assert sci["positivity"]["not_a_prediction_of_frozen_theory"] is True
        assert "healthy" in sci["positivity"]["statement"]
        assert sci["canonical_normalization"]["ZA_numerical_value"] == "NOT DETERMINED"
        assert sci["ZA_numerical_value"] == "NOT DETERMINED"
        assert sci["experimental_constants"] is False
        assert sci["gravity_changed"] is False
        assert sci["negative_tests_all_pass"] is True
        oc = sci["negative_tests"]["overclaims"]
        assert oc["1_local_U1_implies_Maxwell"] == "REJECTED AS OVERCLAIM"
        assert oc["2_frozen_theory_requires_autonomous_F2"] == "REJECTED AS OVERCLAIM"
        assert oc["7_benchmark_proves_autonomous_sector_exists_in_frozen_theory"] == "REJECTED AS OVERCLAIM"
        assert sci["negative_tests"]["accepted"]["gauge_dynamics_not_determined_by_frozen_theory"] == "ACCEPTED"
        assert sci["PHASE_5D_CLOSED"] is True
        assert "NOT DETERMINED BY THE FROZEN THEORY" in sci["chain"]
        assert "GIVEN THE BENCHMARK" in sci["required_interpretation"]
        copies = sci["extension_copies"]
        assert copies["merged_into_one_baseline"] is False
        assert copies["A_GAUGED_MATTER_ONLY"]["autonomous_propagation"] == "NOT_ESTABLISHED"
        assert copies["B_GAUGED_MATTER_PLUS_PARITY_EVEN_F2"]["autonomous_propagation"] == "ESTABLISHED"
        assert copies["C_GAUGED_MATTER_PLUS_PARITY_ODD"]["autonomous_propagation"] == "NOT_ESTABLISHED"
        assert sci["GAUGE_DYNAMICS_TEST_ACTION_ID"] == GAUGE_DYNAMICS_TEST_ACTION_ID
        qs = sci["scientific_questions"]
        assert qs["1_5c_contains_autonomous_dynamics"] == "NO"
        assert qs["2_F2_derivable_from_frozen_structure_alone"] == "NO"
        assert qs["8_numerical_gauge_coupling_determined"] == "NO"
        assert qs["9_bare_Proca_survives_local_U1"] == "NO"
        assert qs["11_gauge_sector_modifies_c0_c1"] == "NO"
        assert qs["12_experimental_or_numerical_target_entered"] == "NO"


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase5d.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 5D: pre-analysis gate",
        "Phase 5D: gauge-dynamics classification",
        "Phase 5D: gravity unchanged",
        "Phase 5D: no numerical targets",
        "Phase 5D: banned tokens",
        "Phase 5D: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "OBJECTIVE" in text
    assert "SCOPE SUMMARY" in text
    assert text.index("OBJECTIVE") < text.index("SCOPE SUMMARY")
    assert "GAUGE_DYNAMICS_STATUS" in text
    assert "NOT_DETERMINED" in text
    assert "REQUIRED_GIVEN_ADDITIONAL_ASSUMPTION" not in text
    assert "MAXWELL_BENCHMARK_STATUS" in text
    assert "ESTABLISHED IN F^2 TEST COPY" in text
    assert "NO / NOT DETERMINED" in text
    assert "does not derive the existence" in text
    assert "PHASE_5D_TEST_COPY" in text
    assert "SEPARATE" in text
    assert "DERIVED GIVEN MINIMAL GAUGE-DYNAMICS BENCHMARK" in text
    assert "NOT labelled DERIVED FROM THE FROZEN ACTION" in text or "NOT labelled DERIVED FROM THE FROZEN ACTION." in text
    assert "WHAT IS DERIVED" in text
    assert "WHAT REQUIRES ADDITIONAL ASSUMPTIONS" in text
    assert "WHAT IS ALLOWED BUT ASSUMED" in text
    assert "WHAT REMAINS UNDETERMINED" in text
    assert "Phase 5C remains unchanged." in text
    assert "No experimental matching has been used." in text
    assert "PHASE 5D CLOSED" in text
    assert "local gauge symmetry => Maxwell theory" in text
    assert EXPECTED_FROZEN_HASH in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase5d_gauge_dynamics.py",
        root / "models" / "examples" / "phase5d_model.py",
        root / "reporting" / "phase5d_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "13" + "7.036",
        "alp" + "ha_em",
        "electr" + "ic",
        "from physics_lab.physics." + "constants",
        "from physics_lab.physics." + "gauge_internal",
        "6." + "674",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
