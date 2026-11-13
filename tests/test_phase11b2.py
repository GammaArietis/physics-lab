"""Phase 11B.2: ENHANCED_INTERNAL_SYMMETRY test."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11b2_model import build_phase11b2_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import (
    declared_dependencies,
    undeclared_inferences,
    validate_dependencies,
)
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10b1_exploration import build_model_spec
from physics_lab.physics.phase11b1_scales import artifact_dir as phase11b1_artifact_dir
from physics_lab.physics.phase11b2_symmetry import (
    AUDIT_VERSION,
    EXPECTED_GRAMMAR_HASH,
    PHASE_11B2_TEST_COPY_ID,
    PRINCIPLE_ID,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_unchecked_is_never_valid_or_invalid():
    selection = {
        "INTERNAL_OPERATOR_CLASS": "commutant_symmetric_K",
        "REPRESENTATION_CLASS": "real_u1_1plus2",
        "SYMMETRY_CLASS": "diffeo_plus_so2",
        "GEOMETRY_CLASS": "internal_R3_no_manifold_laplacian",
        "GAUGE_DYNAMICS_CLASS": "optional_F2_test_extension",
        "MINIMALITY_CLASS": "two_derivative_quadratic",
        "MODULUS_CLASS": "no_dynamical_modulus",
        "FIELD_CONTENT_CLASS": "metric_plus_internal_Phi",
        "GRAVITY_CLASS": "volume_plus_ricci",
        "HILBERT_BOUND": "real_finite_dim_at_most_3",
    }
    spec = build_model_spec("MODEL_0007", selection)
    result = validate_dependencies(spec)
    assert result["status"] == "UNCHECKED"
    assert result["status"] != "VALID"
    assert result["status"] != "INVALID"


def test_no_new_dependency_or_f2_a_mu():
    ids = {row["dependency_id"] for row in declared_dependencies()}
    assert "optional_F2_test_extension->A_mu" not in ids
    inferences = {item["inference_id"]: item["status"] for item in undeclared_inferences()}
    assert inferences["F2_A_MU_DEPENDENCY"] == "UNDECLARED"


def test_symmetry_test_preserves_history():
    before = snapshot_prior_artifact_hashes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase11b2_model(signature=sig).solve()
        sci = result.metadata["phase11b2_analysis"]
        integ = result.metadata["phase11b2_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["audit_summary"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert sci["grammar_hash"] == EXPECTED_GRAMMAR_HASH
        assert summary["candidates_analyzed"] == 8
        assert summary["new_principle_count"] == 1
        assert summary["new_principle_id"] == PRINCIPLE_ID
        assert summary["second_principle_introduced"] is False
        assert summary["ranking"] is False
        assert summary["MODEL_SPEC_rewrites"] == 0
        assert summary["PHASE_10B_STATUS"] == "CLOSED_NO_INTERNAL_CLOSURE"
        assert sci["PHASE_11B2_STATUS"] == "CLOSED"
        assert sci["PHASE_11B2_TEST_COPY_ID"] == PHASE_11B2_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["PRINCIPLE_EFFECT"] == "INCONSISTENT"
        assert sci["SYMMETRY_REQUIRES_PARAMETER_TUNING"] is True
        assert sci["NO_NEW_CROSS_SECTOR_RELATION"] is True
        assert sci["NEW_PFR"] == "NO_NEW_PFR"
        assert sci["UNIQUE_ACTION"] == "NO"
        assert sci["GLOBAL_CLOSURE"] == "NO"
        assert sci["phase_11b3_executed"] is False
        assert sci["H_int_audit"]["K_commutes_with_H_identically"] is True
        assert sci["H_int_audit"]["Jy_commutes_with_H_identically"] is False
        assert sci["H_int_audit"]["Jy_commutes_after_equal_eigenvalues"] is True
        assert sci["kinetic_obstruction"]["kinetic_invariant_for_arbitrary_A"] is False
        assert sci["generic_branch"]["independent_physical_parameters"] == 6
        assert sci["principle"]["provenance"] == "INPUT / FUTURE TEST"
        assert sci["overclaims"]["1_lambda_equality_is_a_PFR_of_the_original_theory"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["2_H_int_commutant_is_full_action_invariance"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["4_SU2_acts_faithfully_on_R3"] == "REJECTED AS OVERCLAIM"
        so3 = next(g for g in sci["group_search"] if g["candidate_group"] == "SO(3)")
        assert so3["admissible_on_R3"] is True
        assert so3["exact_full_action_symmetry"] is False
        su2 = next(g for g in sci["group_search"] if g["candidate_group"] == "SU(2)")
        assert su2["admissible_on_R3"] is False
        assert len(sci["candidate_table"]) == 8
        assert all(row["kinetic_obstruction"] is True for row in sci["candidate_table"])
    after = snapshot_prior_artifact_hashes()
    assert before == after


def test_artifacts_exist_and_do_not_overwrite_priors():
    before = snapshot_prior_artifact_hashes()
    build_phase11b2_model().solve()
    after = snapshot_prior_artifact_hashes()
    assert before == after
    root = artifact_dir()
    for name in (
        "GROUP_SEARCH.json",
        "ACTION_VARIATION_RESULTS.json",
        "PARAMETER_CONSTRAINTS.json",
        "CANDIDATE_RESULTS.json",
        "CLOSURE_COMPARISON.json",
        "PHASE_11B2_SUMMARY.json",
    ):
        assert (root / name).is_file(), name
    assert root != phase10b1_artifact_dir()
    assert root != phase11b1_artifact_dir()


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11b2.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11B.2: pre-analysis gate",
        "Phase 11B.2: principle-test coverage",
        "Phase 11B.2: no numerical target search",
        "Phase 11B.2: banned tokens",
        "Phase 11B.2: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE_11B.2_SUMMARY" in text
    assert "PHASE 11B.2 CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "INCONSISTENT" in text
    assert "DERIVED GIVEN ASSUMPTION" in text
    assert "No next 11B phase" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11b2_symmetry.py",
        root / "models" / "examples" / "phase11b2_model.py",
        root / "reporting" / "phase11b2_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "from physics_lab.physics." + "gauge_internal",
        "phase10a_" + "known_physics",
        "best_model",
        "preferred_model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
