"""Phase 11B.6: SCALE_INVARIANCE and CONFORMAL_INVARIANCE test."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11b6_model import build_phase11b6_model
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
from physics_lab.physics.phase11b5_boundary import artifact_dir as phase11b5_artifact_dir
from physics_lab.physics.phase11b6_scale_conformal import (
    AUDIT_VERSION,
    EXPECTED_GRAMMAR_HASH,
    PHASE_11B6_TEST_COPY_ID,
    PRINCIPLE_IDS,
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


def test_scale_conformal_test_preserves_history():
    before = snapshot_prior_artifact_hashes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase11b6_model(signature=sig).solve()
        sci = result.metadata["phase11b6_analysis"]
        integ = result.metadata["phase11b6_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["audit_summary"]
        scale = sci["scale_summary"]
        conf = sci["conformal_summary"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert sci["grammar_hash"] == EXPECTED_GRAMMAR_HASH
        assert summary["candidates_analyzed"] == 8
        assert summary["new_principle_count"] == 2
        assert summary["new_principle_ids"] == list(PRINCIPLE_IDS)
        assert summary["third_principle_introduced"] is False
        assert summary["ranking"] is False
        assert summary["MODEL_SPEC_rewrites"] == 0
        assert summary["PHASE_10B_STATUS"] == "CLOSED_NO_INTERNAL_CLOSURE"
        assert sci["PHASE_11B6_STATUS"] == "CLOSED"
        assert sci["PHASE_11B6_TEST_COPY_ID"] == PHASE_11B6_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["GRAVITY_SCALE_INVARIANCE_OBSTRUCTED"] is True
        assert sci["CONFORMAL_COMPLETION_REQUIRED"] is True
        assert sci["dilaton_added"] is False
        assert sci["improvement_added"] is False
        assert sci["NO_NEW_CROSS_SECTOR_RELATION"] is True
        assert scale["PRINCIPLE_EFFECT"] == "INCONSISTENT"
        assert conf["PRINCIPLE_EFFECT"] == "CONFORMAL_COMPLETION_REQUIRED"
        assert scale["NEW_PFR"] == "NONE"
        assert conf["NEW_PFR"] == "NONE"
        assert scale["UNIQUE_ACTION"] == "NO"
        assert conf["UNIQUE_ACTION"] == "NO"
        assert scale["GLOBAL_CLOSURE"] == "NO"
        assert conf["GLOBAL_CLOSURE"] == "NO"
        assert sci["phase_11b7_executed"] is False
        assert sci["principle"]["provenance"] == "INPUT / FUTURE TEST"
        assert scale["inconsistent_candidates"] == 8
        assert conf["inconsistent_candidates"] == 8
        assert scale["N_physical_before"] == 6
        assert scale["N_physical_after"] == 6
        assert conf["N_physical_before"] == 6
        assert conf["N_physical_after"] == 6
        assert sci["scale_variation"]["kinetic_invariant"] is True
        assert sci["scale_variation"]["c0_invariant"] is False
        assert sci["scale_variation"]["c1_invariant"] is False
        assert sci["scale_variation"]["potential_invariant"] is False
        assert sci["scale_variation"]["background_c0_equals_zero_not_used"] is True
        assert sci["weyl_kinetic"]["CONFORMAL_COMPLETION_REQUIRED"] is True
        assert sci["weyl_kinetic"]["improvement_term_added"] is False
        assert sci["special_conformal"]["potential_invariant"] is False
        assert sci["special_conformal"]["flat_massless_kinetic_invariant"] is True
        assert sci["special_conformal"]["not_inferred_from_scale"] is True
        assert sci["overclaims"]["1_scale_implies_conformal"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["2_add_dilaton_or_compensator"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["3_add_improvement_coupling"] == "REJECTED AS OVERCLAIM"
        assert len(sci["scale_table"]) == 8
        assert len(sci["conformal_table"]) == 8
        assert all(row["scale_invariant"] == "NO" for row in sci["scale_table"])
        assert all(row["conformal_invariant"] == "NO" for row in sci["conformal_table"])
        assert all(row["GRAVITY_SCALE_INVARIANCE_OBSTRUCTED"] is True for row in sci["scale_table"])
        assert all(row["CONFORMAL_COMPLETION_REQUIRED"] is True for row in sci["conformal_table"])
        mismatch = [row for row in sci["scale_table"] if row["model"] in {"MODEL_0007", "MODEL_0008"}]
        assert all(row["mismatch_preserved"] is True for row in mismatch)
    after = snapshot_prior_artifact_hashes()
    assert before == after


def test_artifacts_exist_and_do_not_overwrite_priors():
    before = snapshot_prior_artifact_hashes()
    build_phase11b6_model().solve()
    after = snapshot_prior_artifact_hashes()
    assert before == after
    root = artifact_dir()
    for name in (
        "DIMENSION_ASSIGNMENTS.json",
        "SCALE_VARIATION.json",
        "WEYL_KINETIC_REMAINDER.json",
        "SPECIAL_CONFORMAL.json",
        "SCALE_BRANCH.json",
        "CONFORMAL_BRANCH.json",
        "PARAMETER_EFFECTS.json",
        "DIMENSIONLESS_FREEDOM.json",
        "CLOSURE_COMPARISON.json",
        "PHASE_11B6_SUMMARY.json",
    ):
        assert (root / name).is_file(), name
    assert root != phase10b1_artifact_dir()
    assert root != phase11b5_artifact_dir()


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11b6.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11B.6: pre-analysis gate",
        "Phase 11B.6: principle-test coverage",
        "Phase 11B.6: no numerical target search",
        "Phase 11B.6: banned tokens",
        "Phase 11B.6: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE_11B.6_SUMMARY" in text
    assert "PHASE 11B.6 CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "GRAVITY_SCALE_INVARIANCE_OBSTRUCTED" in text
    assert "CONFORMAL_COMPLETION_REQUIRED" in text
    assert "SCALE_INVARIANCE" in text
    assert "CONFORMAL_INVARIANCE" in text
    assert "No next 11B phase" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11b6_scale_conformal.py",
        root / "models" / "examples" / "phase11b6_model.py",
        root / "reporting" / "phase11b6_report.py",
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
