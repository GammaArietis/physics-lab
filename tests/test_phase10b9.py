"""Phase 10B.9: linearized constraint and classical ghost audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase10b9_model import build_phase10b9_model
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
from physics_lab.physics.phase10b9_linearized_ghost import (
    AUDIT_VERSION,
    PHASE_10B9_TEST_COPY_ID,
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


def test_linearized_ghost_run_preserves_history():
    before = snapshot_prior_artifact_hashes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase10b9_model(signature=sig).solve()
        sci = result.metadata["phase10b9_analysis"]
        integ = result.metadata["phase10b9_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["audit_summary"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert summary["candidates_analyzed"] == 8
        assert summary["syntactic_candidates"] == 8
        assert summary["new_assumptions"] == 0
        assert summary["new_dependencies"] == 0
        assert summary["ranking"] is False
        assert summary["known_physics_comparison"] is False
        assert summary["F2_A_MU_DEPENDENCY"] == "UNDECLARED"
        assert summary["candidates_regenerated"] is False
        assert summary["large_scale_exploration_launched"] is False
        assert summary["gravity_family_modified"] is False
        assert summary["NO_NEW_PARAMETER_FREE_RELATIONS_FOUND"] is True
        assert summary["new_parameter_free_relations"] == 0
        assert summary["quantum_unitarity_verified"] == 0
        assert summary["quantum_unitarity_untested"] == 8
        assert summary["Z_A_not_set_to_one"] is True
        assert summary["c1_not_chosen"] is True
        assert summary["ostrogradsky_avoided_by_verified_degeneracy"] == 0
        assert sci["PHASE_10B9_STATUS"] == "CLOSED"
        assert sci["PHASE_10B9_TEST_COPY_ID"] == PHASE_10B9_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["ranking_score_introduced"] is False
        assert sci["known_physics_comparison_executed"] is False
        assert sci["phase_10c_executed"] is False
        rows = sci["linearized_candidate_results"]
        assert len(rows) == 8
        ids = [item["model_id"] for item in rows]
        assert ids == [f"MODEL_{i:04d}" for i in range(1, 9)]
        by_id = {item["model_id"]: item for item in rows}
        assert by_id["MODEL_0001"]["gauge_ghost"] == "NO"
        assert by_id["MODEL_0003"]["gauge_ghost"] == "PARAMETER_DEPENDENT"
        assert by_id["MODEL_0007"]["gauge_ghost"] == "UNTESTED"
        assert by_id["MODEL_0007"]["total_classical_ghost"] == "UNTESTED"
        for item in rows:
            if item["dependency_status"] == "UNCHECKED":
                assert item["dependency_status"] != "VALID"
                assert item["dependency_status"] != "INVALID"
                assert item["dependency_audit_metadata"] == "DERIVED_WITH_UNCHECKED_DEPENDENCY"
            assert item["Ostrogradsky"] == "NOT_TRIGGERED_BY_STORED_SECOND_ORDER_ACTION"
            assert item["matter_ghost"] == "PARAMETER_DEPENDENT"
            assert item["gravity_ghost"] == "PARAMETER_DEPENDENT"
        assert sci["overclaims"]["4_gauge_degeneracy_is_Ostrogradsky"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["10_start_phase_10c"] == "REJECTED AS OVERCLAIM"
    after = snapshot_prior_artifact_hashes()
    assert before == after


def test_artifacts_exist_and_do_not_overwrite_priors():
    before = snapshot_prior_artifact_hashes()
    build_phase10b9_model().solve()
    after = snapshot_prior_artifact_hashes()
    assert before == after
    root = artifact_dir()
    for name in (
        "LINEARIZED_FIELD_TABLE.json",
        "LINEARIZED_CANDIDATE_RESULTS.json",
        "BACKGROUND_CONDITIONS.json",
        "PARAMETER_FREE_RESULTS.json",
        "PHASE_10B9_SUMMARY.json",
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


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase10b9.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 10B.9: pre-analysis gate",
        "Phase 10B.9: linearized-ghost coverage",
        "Phase 10B.9: no numerical target search",
        "Phase 10B.9: banned tokens",
        "Phase 10B.9: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE_10B.9_SUMMARY" in text
    assert "PHASE 10B.9 CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "UNCHECKED is not INVALID" in text
    assert "NO_NEW_PARAMETER_FREE_RELATIONS_FOUND" in text
    assert "gauge degeneracy is not Ostrogradsky" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10b9_linearized_ghost.py",
        root / "models" / "examples" / "phase10b9_model.py",
        root / "reporting" / "phase10b9_report.py",
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
