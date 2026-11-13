"""Phase 5A: internal generator, gauge quantum numbers, and g_phys."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.gauge_internal_model import build_gauge_internal_model
from physics_lab.models.loader import load_model
from physics_lab.physics.gauge_internal import MOSTLY_MINUS, MOSTLY_PLUS, analyze_gauge_internal
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_null_result_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_gauge_internal_model(signature=sig).solve()
        data = result.metadata["gauge_internal_analysis"]
        assert data["unique_generator"] == "NO"
        assert "DERIVED GIVEN K" in data["J_status"]
        assert data["g"] == "INPUT"
        assert data["Z_A"] == "INPUT"
        assert data["g_phys_derived"] is False
        assert data["Z_A_derived"] is False
        assert data["predictivity"] == "NO"
        assert data["parameter_free_gauge_quantity"] == "NO"
        assert data["gravity_changed"] == "NO"
        assert data["c0"] == "INPUT / FREE"
        assert data["c1"] == "INPUT / FREE"
        assert data["c1_identified_with_ZA"] is False
        assert data["J_hermitian"] is True
        assert data["J_spectrum_invariant"] is True
        assert data["H_int_K_commute_canonical"] is False
        assert data["H_int_K_commute_aligned"] is True
        assert data["generic_diagonal_accepted"] is False
        assert data["gauge_covariance"]["holds"] is True
        assert data["matrix_covariance"] is True
        assert data["F_invariant"] is True
        assert data["A_rescaling_invariant"] is True
        assert data["canonical_kinetic"] is True
        assert data["maxwell_wave_conservation"] is True
        assert data["ZA_candidate"]["overall_coefficient_free"] is True
        assert data["experimental_constants"] is False
        assert data["searched_familiar_values"] is False
        assert data["not_extra_dimension"] is True
        assert data["representation_audit"]["spectrum_labels"] == "{0, +q, -q}"
        assert data["final_status"]["g_phys"] == "PARAMETER-DEPENDENT"
        assert "COMPATIBLE WITH THE REAL REPRESENTATION" in data["conclusion"]
        assert data["answers"]["5_q_determined"].startswith("NO")
        assert data["answers"]["7_absolute_coupling"].startswith("NO")
        assert data["answers"]["10_experimental"].startswith("NO")
        compact = data["compactness_audit"]
        assert compact["mapping"]["mapping_holds"] is True
        assert compact["mapping"]["physically_distinct"] is False
        assert compact["mapping"]["g_absorbed_into_period"] is False
        assert compact["equivalent_parameterizations"] is True
        assert compact["new_physical_prediction"] is False
        assert compact["rescaling"]["gJ_invariant"] is True
        assert compact["rescaling"]["Q_rep_invariant"] is True
        assert compact["double_count_illegal"] is True
        assert compact["g_phys_derived"] is False
        assert compact["one_oplus_two"] is True
        assert compact["gravity_changed"] == "NO"
        assert compact["answers"]["6_gphys"].startswith("NO")
        assert compact["answers"]["8_absolute"].startswith("NO")
        assert compact["PINNED_Q_REP"] == "g J"
        assert compact["locked_u1_convention"]["Q_rep"] == "g J"
        assert compact["lock_tests"]["Q_rep_equals_gJ"] is True
        assert compact["lock_tests"]["reject_compactness_implies_g_integer"] is True
        assert compact["lock_tests"]["reject_compactness_implies_qn_integer"] is True
        assert data["PINNED_Q_REP"] == "g J"
        assert data["locked_u1_convention"]["compactness_weights"] == "g q_n in Z"
        assert data["locked_u1_convention"]["group_parameter"] == "alpha"
        assert data["locked_u1_convention"]["local_gauge_parameter"] == "alpha(x)"
        assert data["locked_u1_convention"]["alpha_definition"] == "canonical 2 pi-periodic group parameter"
        assert data["gauging"]["Q_rep"] == "g J"
        assert data["rejected_false_inferences"]["compactness_implies_g_phys_fixed"] is False
        assert data["tr_J2_normalization_invariant"] is False
        assert data["ZA_candidate_Q_rep"]["Z_A_derived"] is False


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "gauge_internal.py",
        root / "physics" / "gauge_representation.py",
        root / "physics" / "gauge_compactness.py",
        root / "models" / "examples" / "gauge_internal_model.py",
        root / "reporting" / "gauge_internal_report.py",
    ]
    banned = (
        "1/" + "3",
        "2/" + "3",
        "1/" + "13" + "7",
        "13" + "7.036",
        "alp" + "ha_em",
        "electr" + "ic",
        "from physics_lab.physics." + "constants",
        "6." + "674",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "gauge_internal.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Gauge internal: Hermiticity",
        "Gauge internal: eigenvalues",
        "Gauge internal: basis invariance",
        "Gauge internal: degeneracy",
        "Gauge internal: commutator",
        "Gauge internal: gauge covariance",
        "Gauge internal: field rescaling",
        "Gauge internal: canonical kinetic",
        "Gauge internal: g_phys invariance",
        "Gauge internal: internal invariants",
        "Gauge internal: provenance labels",
        "Gauge internal: provenance firewall",
        "Gauge internal: gravity",
        "Gauge internal: banned tokens",
        "Gauge internal: real representation",
        "Gauge internal: reject generic diagonal",
        "Gauge internal: compactness mapping",
        "Gauge internal: no double-count",
        "Gauge internal: U(1) lock",
        "Gauge internal: rejected false inferences",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    assert "PHASE 5A — INTERNAL SYMMETRY TO GAUGE COUPLING" in report.text
    assert "PHASE 5A.0 — REAL U(1) REPRESENTATION AUDIT" in report.text
    assert "PHASE 5A.1 — COMPACTNESS NORMALIZATION AUDIT" in report.text
    analysis = analyze_gauge_internal(signature=MOSTLY_PLUS)
    assert analysis["predictivity"] == "NO"
    assert analysis["unique_generator"] == "NO"
    assert analysis["generic_diagonal_accepted"] is False
    assert analysis["compactness_audit"]["equivalent_parameterizations"] is True
    assert analysis["compactness_audit"]["new_physical_prediction"] is False
    assert analysis["PINNED_Q_REP"] == "g J"
    assert "LOCKED GLOBAL U(1) CONVENTION" in report.text
    assert "just absorbed" not in report.text
    assert "g q_n is the representation weight" in report.text
