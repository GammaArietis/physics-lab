"""Phase 10B.6: formalize the existing typed dependency schema."""

from __future__ import annotations

import copy
from pathlib import Path

from physics_lab.models.examples.phase10b6_model import build_phase10b6_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import (
    LEGAL_DEPENDENCY_RELATION_TYPES,
    declared_dependencies,
    dependency_schema,
    evaluate_typed_dependency,
    undeclared_inferences,
    validate_dependencies,
)
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10b1_exploration import build_model_spec
from physics_lab.physics.phase10b2_derivation import artifact_dir as phase10b2_artifact_dir
from physics_lab.physics.phase10b3_audit import artifact_dir as phase10b3_artifact_dir
from physics_lab.physics.phase10b4_validation import artifact_dir as phase10b4_artifact_dir
from physics_lab.physics.phase10b5_semantics import artifact_dir as phase10b5_artifact_dir
from physics_lab.physics.phase10b6_schema import (
    PHASE_10B6_TEST_COPY_ID,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _spec_0005():
    selection = {
        "INTERNAL_OPERATOR_CLASS": "commutant_symmetric_K",
        "REPRESENTATION_CLASS": "real_u1_1plus2",
        "SYMMETRY_CLASS": "diffeo_plus_so2",
        "GEOMETRY_CLASS": "internal_R3_no_manifold_laplacian",
        "GAUGE_DYNAMICS_CLASS": "connection_without_autonomous_F2",
        "MINIMALITY_CLASS": "two_derivative_quadratic",
        "MODULUS_CLASS": "no_dynamical_modulus",
        "FIELD_CONTENT_CLASS": "metric_plus_internal_Phi",
        "GRAVITY_CLASS": "volume_plus_ricci",
        "HILBERT_BOUND": "real_finite_dim_at_most_3",
    }
    return build_model_spec("MODEL_0005", selection)


def test_every_declared_dependency_is_typed():
    rows = declared_dependencies()
    assert len(rows) == 6
    required = {
        "dependency_id",
        "relation_type",
        "source",
        "target",
        "provenance",
        "declared_scope",
    }
    for row in rows:
        assert required <= set(row)
        assert row["relation_type"] in LEGAL_DEPENDENCY_RELATION_TYPES


def test_same_axis_is_not_co_selection():
    selection = dict(_spec_0005()["axis_selection"])
    selection["GAUGE_DYNAMICS_CLASS"] = "optional_F2_test_extension"
    spec = build_model_spec("MODEL_0007", selection)
    result = validate_dependencies(spec)
    assert result["status"] == "UNCHECKED"
    assert result["status"] != "VALID"
    assert result["status"] != "INVALID"
    assert "optional_F2_test_extension->connection_without_autonomous_F2" in result["unchecked_dependency_ids"]
    assert spec["axis_selection"]["GAUGE_DYNAMICS_CLASS"] == "optional_F2_test_extension"
    assert spec["axis_selection"]["GAUGE_DYNAMICS_CLASS"] != "connection_without_autonomous_F2"


def test_defined_satisfied_dependency_is_valid():
    result = validate_dependencies(_spec_0005())
    assert result["status"] == "VALID"
    assert result["violated_dependency_ids"] == []
    assert result["unchecked_dependency_ids"] == []
    assert "commutant_symmetric_K->real_u1_1plus2" in result["satisfied_dependency_ids"]
    assert "real_u1_1plus2->H_int" in result["satisfied_dependency_ids"]


def test_defined_violated_dependency_is_invalid():
    spec = _spec_0005()
    spec["axis_selection"] = dict(spec["axis_selection"])
    spec["axis_selection"]["REPRESENTATION_CLASS"] = "missing_representation"
    result = validate_dependencies(spec)
    assert result["status"] == "INVALID"
    assert "commutant_symmetric_K->real_u1_1plus2" in result["violated_dependency_ids"]


def test_undefined_dependency_returns_unchecked():
    spec = _spec_0005()
    synthetic = {
        "dependency_id": "synthetic->undefined",
        "relation_type": "UNDEFINED",
        "source": "commutant_symmetric_K",
        "target": "not_a_declared_target",
        "source_axis": "INTERNAL_OPERATOR_CLASS",
        "target_axis": None,
        "provenance": "INPUT",
        "declared_scope": "INTERNAL_OPERATOR_CLASS",
    }
    row = evaluate_typed_dependency(spec, synthetic)
    assert row["status"] == "UNCHECKED"
    assert row["status"] != "VALID"
    assert row["status"] != "INVALID"


def test_no_new_dependency_invented_and_f2_a_mu_undeclared():
    ids = {row["dependency_id"] for row in declared_dependencies()}
    assert ids == {
        "commutant_symmetric_K->real_u1_1plus2",
        "function_of_KTK->real_u1_1plus2",
        "connection_without_autonomous_F2->real_u1_1plus2",
        "real_u1_1plus2->H_int",
        "optional_F2_test_extension->connection_without_autonomous_F2",
        "metric_Phi_plus_connection->metric_plus_internal_Phi",
    }
    assert "optional_F2_test_extension->A_mu" not in ids
    inferences = {item["inference_id"]: item["status"] for item in undeclared_inferences()}
    assert inferences["F2_A_MU_DEPENDENCY"] == "UNDECLARED"
    assert inferences["F2_FIELD_CONTENT_CONNECTION"] == "UNDECLARED"
    assert inferences["CONNECTION_REQUIRES_FIELD_A_MU"] == "UNDECLARED"


def test_schema_run_preserves_candidates_and_raw_space():
    before = snapshot_prior_artifact_hashes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase10b6_model(signature=sig).solve()
        sci = result.metadata["phase10b6_analysis"]
        integ = result.metadata["phase10b6_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["audit_summary"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert summary["RAW_SEARCH_SPACE_SIZE"] == 8
        assert summary["schema_implemented"] is True
        assert summary["grammar_changed"] == 0
        assert summary["new_physics"] == 0
        assert summary["new_dependencies_added"] == 0
        assert summary["ranking"] is False
        assert summary["F2_A_MU_DEPENDENCY"] == "UNDECLARED"
        assert summary["candidates_regenerated"] is False
        assert summary["large_scale_exploration_launched"] is False
        assert summary["search_space_modified"] is False
        assert summary["models_merged"] is False
        assert summary["UNCHECKED_IS_NOT_INVALID"] is True
        assert summary["UNCHECKED_IS_NOT_VALID"] is True
        assert sci["PHASE_10B6_STATUS"] == "CLOSED"
        assert sci["PHASE_10B6_TEST_COPY_ID"] == PHASE_10B6_TEST_COPY_ID
        assert sci["ranking_score_introduced"] is False
        assert sci["known_physics_comparison_executed"] is False
        assert sci["large_scale_generation_executed"] is False
        rows = sci["dependency_evaluation_results"]
        assert len(rows) == 8
        ids = [item["model_id"] for item in rows]
        assert ids == [f"MODEL_{i:04d}" for i in range(1, 9)]
        for item in rows:
            assert item["historical_candidate_preserved"] is True
            assert item["regenerated"] is False
            if item["dependency_status"] == "UNCHECKED":
                assert item["dependency_status"] != "VALID"
                assert item["dependency_status"] != "INVALID"
        schema = dependency_schema()
        assert schema["DEPENDENCY_SCHEMA_STATUS"] in {"CONSISTENT", "UNDEFINED", "INCONSISTENT"}
        assert schema["schema_implemented"] is True
    after = snapshot_prior_artifact_hashes()
    assert before == after


def test_artifacts_exist_and_do_not_overwrite_priors():
    before = snapshot_prior_artifact_hashes()
    build_phase10b6_model().solve()
    after = snapshot_prior_artifact_hashes()
    assert before == after
    root = artifact_dir()
    for name in (
        "DEPENDENCY_SCHEMA.json",
        "TYPED_DEPENDENCY_DEFINITIONS.json",
        "DEPENDENCY_CLASSIFICATION_AUDIT.json",
        "DEPENDENCY_EVALUATION_RESULTS.json",
        "PHASE_10B6_SUMMARY.json",
    ):
        assert (root / name).is_file(), name
    assert root != phase10b1_artifact_dir()
    assert root != phase10b2_artifact_dir()
    assert root != phase10b3_artifact_dir()
    assert root != phase10b4_artifact_dir()
    assert root != phase10b5_artifact_dir()


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase10b6.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 10B.6: pre-analysis gate",
        "Phase 10B.6: typed-schema coverage",
        "Phase 10B.6: no numerical target search",
        "Phase 10B.6: banned tokens",
        "Phase 10B.6: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE_10B.6_SUMMARY" in text
    assert "PHASE 10B.6 CLOSED" in text
    assert "DEPENDENCY_SCHEMA_STATUS" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "UNCHECKED is not VALID" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10b6_schema.py",
        root / "models" / "examples" / "phase10b6_model.py",
        root / "reporting" / "phase10b6_report.py",
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


def test_validation_is_deterministic():
    spec = _spec_0005()
    first = validate_dependencies(spec)
    second = validate_dependencies(copy.deepcopy(spec))
    assert first == second
