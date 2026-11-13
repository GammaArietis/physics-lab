"""Phase 10B.5: dependency-semantics audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase10b5_model import build_phase10b5_model
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
from physics_lab.physics.phase10b5_semantics import (
    PHASE_10B5_TEST_COPY_ID,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_audit_does_not_invent_dependencies():
    before = {row["dependency_id"] for row in declared_dependencies()}
    result = build_phase10b5_model().solve()
    sci = result.metadata["phase10b5_analysis"]
    summary = sci["audit_summary"]
    after = {row["dependency_id"] for row in declared_dependencies()}
    assert before == after
    assert summary["new_dependencies_added"] == 0
    classified = sci["dependency_semantics_audit"]["declared_dependencies"]
    ids = {row["dependency_id"] for row in classified}
    assert ids == before
    assert "optional_F2_test_extension->A_mu" not in ids
    inferences = {item["inference_id"]: item["status"] for item in undeclared_inferences()}
    assert inferences["F2_A_MU_DEPENDENCY"] == "UNDECLARED"
    assert summary["F2_A_MU_DEPENDENCY"] == "UNDECLARED"


def test_same_axis_remains_unchecked_not_invalid():
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
    assert result["status"] != "INVALID"
    assert result["status"] != "VALID"


def test_audit_run_and_historical_preservation():
    before = snapshot_prior_artifact_hashes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase10b5_model(signature=sig).solve()
        sci = result.metadata["phase10b5_analysis"]
        integ = result.metadata["phase10b5_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["audit_summary"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert summary["RAW_SEARCH_SPACE_SIZE"] == 8
        assert summary["raw_search_space_size"] == 8
        assert summary["grammar_changed"] == 0
        assert summary["new_physics"] == 0
        assert summary["new_dependencies_added"] == 0
        assert summary["ranking"] is False
        assert summary["F2_A_MU_DEPENDENCY"] == "UNDECLARED"
        assert summary["DEPENDENCY_SCHEMA_STATUS"] == "UNDEFINED"
        assert summary["UNCHECKED_IS_NOT_INVALID"] is True
        assert summary["candidates_regenerated"] is False
        assert summary["search_space_modified"] is False
        assert sci["PHASE_10B5_STATUS"] == "CLOSED"
        assert sci["PHASE_10B5_TEST_COPY_ID"] == PHASE_10B5_TEST_COPY_ID
        assert sci["DEPENDENCY_SCHEMA_STATUS"] == "UNDEFINED"
        assert sci["ranking_score_introduced"] is False
        assert sci["known_physics_comparison_executed"] is False
        assert sci["large_scale_generation_executed"] is False
        rows = sci["dependency_candidate_audit"]["results"]
        assert len(rows) == 8
        ids = [item["model_id"] for item in rows]
        assert ids == [f"MODEL_{i:04d}" for i in range(1, 9)]
        for item in rows:
            assert item["historical_candidate_preserved"] is True
            assert item["regenerated"] is False
            if item["dependency_status"] == "UNCHECKED":
                assert item["overall_state"] != "INVALID"
                assert item["dependency_status"] != "INVALID"
        assert summary["invalid_dependency_candidates"] == 0
        assert summary["dependency_unresolved_search_space_size"] == summary["unresolved_dependency_candidates"]
        same_axis = summary["same_axis_dependencies"]
        assert "optional_F2_test_extension->connection_without_autonomous_F2" in same_axis
        assert "metric_Phi_plus_connection->metric_plus_internal_Phi" in same_axis
        f2 = sci["dependency_semantics_audit"]["f2_dependency_audit"]
        assert f2["both_labels_are_GAUGE_DYNAMICS_CLASS_alternatives"] is True
        assert f2["formally_declared_as_extension_of_target"] is False
        assert f2["converted_to_F2_requires_A_mu"] is False
        field = sci["dependency_semantics_audit"]["field_content_dependency_audit"]
        assert field["both_labels_are_FIELD_CONTENT_CLASS_alternatives"] is True
        assert field["declared_as_inheritance"] is False
        eval_sem = sci["dependency_semantics_audit"]["evaluation_semantics"]
        assert eval_sem["logical_implications"] is False
        assert eval_sem["validate_dependencies_evaluates"] == "LABEL_PRESENCE_OR_EQUALITY"
        assert eval_sem["DEPENDENCY_SEMANTICS_UNDEFINED"] is True
    after = snapshot_prior_artifact_hashes()
    assert before == after


def test_artifacts_exist_and_do_not_overwrite_priors():
    before = snapshot_prior_artifact_hashes()
    build_phase10b5_model().solve()
    after = snapshot_prior_artifact_hashes()
    assert before == after
    root = artifact_dir()
    for name in (
        "DEPENDENCY_SEMANTICS_AUDIT.json",
        "DEPENDENCY_SCHEMA_AUDIT.json",
        "DEPENDENCY_CANDIDATE_AUDIT.json",
        "PHASE_10B5_SUMMARY.json",
    ):
        assert (root / name).is_file(), name
    assert root != phase10b1_artifact_dir()
    assert root != phase10b2_artifact_dir()
    assert root != phase10b3_artifact_dir()
    assert root != phase10b4_artifact_dir()


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase10b5.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 10B.5: pre-analysis gate",
        "Phase 10B.5: dependency-semantics coverage",
        "Phase 10B.5: no numerical target search",
        "Phase 10B.5: banned tokens",
        "Phase 10B.5: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE_10B.5_SUMMARY" in text
    assert "PHASE 10B.5 CLOSED" in text
    assert "DEPENDENCY_SCHEMA_STATUS" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "UNCHECKED is not INVALID" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10b5_semantics.py",
        root / "models" / "examples" / "phase10b5_model.py",
        root / "reporting" / "phase10b5_report.py",
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
