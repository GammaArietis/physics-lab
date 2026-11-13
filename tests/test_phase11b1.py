"""Phase 11B.1: NO_EXTERNAL_DIMENSIONFUL_SCALES test."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11b1_model import build_phase11b1_model
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
from physics_lab.physics.phase10b10_closure import artifact_dir as phase10b10_artifact_dir
from physics_lab.physics.phase11a_strategy import artifact_dir as phase11a_artifact_dir
from physics_lab.physics.phase11b1_scales import (
    AUDIT_VERSION,
    EXPECTED_GRAMMAR_HASH,
    PHASE_11B1_TEST_COPY_ID,
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


def test_scale_test_preserves_history():
    before = snapshot_prior_artifact_hashes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase11b1_model(signature=sig).solve()
        sci = result.metadata["phase11b1_analysis"]
        integ = result.metadata["phase11b1_integrity"]
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
        assert summary["known_physics_comparison"] is False
        assert summary["candidates_regenerated"] is False
        assert summary["MODEL_SPEC_rewrites"] == 0
        assert summary["PHASE_10B_STATUS"] == "CLOSED_NO_INTERNAL_CLOSURE"
        assert sci["PHASE_11B1_STATUS"] == "CLOSED"
        assert sci["PHASE_11B1_TEST_COPY_ID"] == PHASE_11B1_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["PRINCIPLE_EFFECT"] == "INCONSISTENT_WITH_SEALED_MODEL"
        assert sci["GRAVITY_ACTION_INCOMPATIBLE_WITH_NEW_PRINCIPLE"] is True
        assert sci["DYNAMIC_SCALE_GENERATION_NOT_IMPLEMENTED"] is True
        assert sci["NO_NEW_CROSS_SECTOR_RELATION"] is True
        assert sci["NEW_PFR"] == "NO_NEW_PFR"
        assert sci["UNIQUE_ACTION"] == "NO"
        assert sci["GLOBAL_CLOSURE"] == "NO"
        assert sci["DIMENSIONLESS_FREEDOM_REMAINS"] == "YES"
        assert sci["phase_11b2_executed"] is False
        assert sci["overclaims"]["10_start_phase_11b2"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["2_elimination_is_a_derived_numerical_value"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["4_c0_over_c1_is_dimensionless"] == "REJECTED AS OVERCLAIM"
        assert sci["principle"]["provenance"] == "INPUT / FUTURE TEST"
        assert len(sci["candidate_table"]) == 8
        assert all(row["compatibility"] == "INCOMPATIBLE" for row in sci["candidate_table"])
        assert summary["N_physical_before"] == 6
        assert summary["N_physical_after"] == 0
        assert sci["dimensionless"]["c0 / c1"]["dimensionless"] is False
    after = snapshot_prior_artifact_hashes()
    assert before == after


def test_artifacts_exist_and_do_not_overwrite_priors():
    before = snapshot_prior_artifact_hashes()
    build_phase11b1_model().solve()
    after = snapshot_prior_artifact_hashes()
    assert before == after
    root = artifact_dir()
    for name in (
        "PRINCIPLE_DEFINITION.json",
        "PARAMETER_DIMENSION_TABLE.json",
        "CANDIDATE_COMPATIBILITY_TABLE.json",
        "CLOSURE_COMPARISON.json",
        "PHASE_11B1_SUMMARY.json",
    ):
        assert (root / name).is_file(), name
    assert root != phase10b1_artifact_dir()
    assert root != phase10b10_artifact_dir()
    assert root != phase11a_artifact_dir()


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11b1.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11B.1: pre-analysis gate",
        "Phase 11B.1: principle-test coverage",
        "Phase 11B.1: no numerical target search",
        "Phase 11B.1: banned tokens",
        "Phase 11B.1: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE_11B.1_SUMMARY" in text
    assert "PHASE 11B.1 CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "INCONSISTENT_WITH_SEALED_MODEL" in text
    assert "Elimination is not a derived numerical value" in text
    assert "No Phase 11B.2" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11b1_scales.py",
        root / "models" / "examples" / "phase11b1_model.py",
        root / "reporting" / "phase11b1_report.py",
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
        "top_candidates",
        "preferred_model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
