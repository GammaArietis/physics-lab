"""Phase 10B.10: global closure and stop audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase10b10_model import build_phase10b10_model
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
from physics_lab.physics.phase10b2_derivation import artifact_dir as phase10b2_artifact_dir
from physics_lab.physics.phase10b3_audit import artifact_dir as phase10b3_artifact_dir
from physics_lab.physics.phase10b4_validation import artifact_dir as phase10b4_artifact_dir
from physics_lab.physics.phase10b5_semantics import artifact_dir as phase10b5_artifact_dir
from physics_lab.physics.phase10b6_schema import artifact_dir as phase10b6_artifact_dir
from physics_lab.physics.phase10b7_revalidation import artifact_dir as phase10b7_artifact_dir
from physics_lab.physics.phase10b8_euler_lagrange import artifact_dir as phase10b8_artifact_dir
from physics_lab.physics.phase10b9_linearized_ghost import artifact_dir as phase10b9_artifact_dir
from physics_lab.physics.phase10b10_closure import (
    AUDIT_VERSION,
    EXPECTED_GRAMMAR_HASH,
    PHASE_10B10_TEST_COPY_ID,
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


def test_closure_run_preserves_history():
    before = snapshot_prior_artifact_hashes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase10b10_model(signature=sig).solve()
        sci = result.metadata["phase10b10_analysis"]
        integ = result.metadata["phase10b10_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["audit_summary"]
        q = sci["closure_questions"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert sci["grammar_hash"] == EXPECTED_GRAMMAR_HASH
        assert summary["candidates_analyzed"] == 8
        assert summary["syntactic_candidates"] == 8
        assert summary["new_assumptions"] == 0
        assert summary["new_dependencies"] == 0
        assert summary["ranking"] is False
        assert summary["known_physics_comparison"] is False
        assert summary["F2_A_MU_DEPENDENCY"] == "UNDECLARED"
        assert summary["candidates_regenerated"] is False
        assert summary["MODEL_SPEC_rewrites"] == 0
        assert summary["unique_action"] == "NO"
        assert summary["unique_kinetic_structure"] == "NO"
        assert summary["unique_dimensionless_quantity"] == "NO"
        assert summary["parameter_free_closure"] == "NO"
        assert summary["global_closure"] == "NO"
        assert summary["FINAL_PARAMETER_FREE_RELATIONS"] == "NONE"
        assert summary["PHASE_10B_STATUS"] == "CLOSED_NO_INTERNAL_CLOSURE"
        assert q["C1_unique_action_modulo_certified_equivalence"] == "NO"
        assert q["C5_unique_physically_inequivalent_theory"] == "NO"
        assert sci["PHASE_10B10_STATUS"] == "CLOSED"
        assert sci["PHASE_10B10_TEST_COPY_ID"] == PHASE_10B10_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["ranking_score_introduced"] is False
        assert sci["known_physics_comparison_executed"] is False
        assert sci["phase_10c_executed"] is False
        assert sci["overclaims"]["10_start_phase_10c"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["9_physics_is_impossible"] == "REJECTED AS OVERCLAIM"
        assert len(sci["master_table"]) >= 12
        assert summary["dependency_valid"] == 2
        assert summary["dependency_unchecked"] == 6
        assert summary["dependency_invalid"] == 0
    after = snapshot_prior_artifact_hashes()
    assert before == after


def test_artifacts_exist_and_do_not_overwrite_priors():
    before = snapshot_prior_artifact_hashes()
    build_phase10b10_model().solve()
    after = snapshot_prior_artifact_hashes()
    assert before == after
    root = artifact_dir()
    for name in (
        "CLOSURE_MASTER_TABLE.json",
        "PARAMETER_STATUS_TABLE.json",
        "DIMENSIONLESS_CATALOG.json",
        "NO_ESCAPE_CHECKLIST.json",
        "PHASE_10B10_SUMMARY.json",
    ):
        assert (root / name).is_file(), name
    assert root != phase10b1_artifact_dir()
    assert root != phase10b2_artifact_dir()
    assert root != phase10b3_artifact_dir()
    assert root != phase10b4_artifact_dir()
    assert root != phase10b5_artifact_dir()
    assert root != phase10b6_artifact_dir()
    assert root != phase10b7_artifact_dir()
    assert root != phase10b8_artifact_dir()
    assert root != phase10b9_artifact_dir()


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase10b10.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 10B.10: pre-analysis gate",
        "Phase 10B.10: closure coverage",
        "Phase 10B.10: no numerical target search",
        "Phase 10B.10: banned tokens",
        "Phase 10B.10: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE_10B.10_SUMMARY" in text
    assert "PHASE 10B.10 CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "UNCHECKED is not INVALID" in text
    assert "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND" in text
    assert "CLOSED_NO_INTERNAL_CLOSURE" in text
    assert "no internal closure within current grammar" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10b10_closure.py",
        root / "models" / "examples" / "phase10b10_model.py",
        root / "reporting" / "phase10b10_report.py",
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
