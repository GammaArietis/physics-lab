"""Phase 10B.4: enforce declared grammar dependencies."""

from __future__ import annotations

import copy
from pathlib import Path

from physics_lab.models.examples.phase10b4_model import build_phase10b4_model
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
from physics_lab.physics.phase10b4_validation import (
    PHASE_10B4_TEST_COPY_ID,
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


def test_satisfied_declared_dependency_is_valid():
    result = validate_dependencies(_spec_0005())
    assert result["status"] == "VALID"
    assert result["violated_dependency_ids"] == []
    assert result["unchecked_dependency_ids"] == []
    assert "commutant_symmetric_K->real_u1_1plus2" in result["satisfied_dependency_ids"]
    assert "real_u1_1plus2->H_int" in result["satisfied_dependency_ids"]


def test_violated_declared_dependency_is_invalid():
    spec = _spec_0005()
    spec["axis_selection"] = dict(spec["axis_selection"])
    spec["axis_selection"]["REPRESENTATION_CLASS"] = "missing_representation"
    result = validate_dependencies(spec)
    assert result["status"] == "INVALID"
    assert "commutant_symmetric_K->real_u1_1plus2" in result["violated_dependency_ids"]


def test_same_axis_declared_dependency_is_unchecked():
    selection = dict(_spec_0005()["axis_selection"])
    selection["GAUGE_DYNAMICS_CLASS"] = "optional_F2_test_extension"
    spec = build_model_spec("MODEL_0007", selection)
    result = validate_dependencies(spec)
    assert result["status"] == "UNCHECKED"
    assert "optional_F2_test_extension->connection_without_autonomous_F2" in result["unchecked_dependency_ids"]
    assert result["status"] != "VALID"


def test_undeclared_inferences_are_not_invented():
    ids = {row["dependency_id"] for row in declared_dependencies()}
    assert "optional_F2_test_extension->A_mu" not in ids
    assert "optional_F2_test_extension->metric_Phi_plus_connection" not in ids
    inferences = {item["inference_id"]: item["status"] for item in undeclared_inferences()}
    assert inferences["F2_A_MU_DEPENDENCY"] == "UNDECLARED"
    spec = build_model_spec(
        "MODEL_0007",
        {
            **_spec_0005()["axis_selection"],
            "GAUGE_DYNAMICS_CLASS": "optional_F2_test_extension",
        },
    )
    result = validate_dependencies(spec)
    assert "F2_A_MU_DEPENDENCY" in result["undeclared_inferences_not_applied"]
    evaluated = result["unchecked_dependency_ids"] + result["violated_dependency_ids"] + result["satisfied_dependency_ids"]
    assert not any(dep_id.endswith("->A_mu") for dep_id in evaluated)


def test_dependency_validation_is_deterministic():
    spec = _spec_0005()
    first = validate_dependencies(spec)
    second = validate_dependencies(copy.deepcopy(spec))
    assert first == second


def test_patch_run_and_historical_preservation():
    before = snapshot_prior_artifact_hashes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase10b4_model(signature=sig).solve()
        sci = result.metadata["phase10b4_analysis"]
        integ = result.metadata["phase10b4_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["audit_summary"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert summary["RAW_SEARCH_SPACE_SIZE"] == 8
        assert summary["raw_search_space_size"] == 8
        assert summary["grammar_changes"] == 0
        assert summary["new_physics"] == 0
        assert summary["ranking"] is False
        assert summary["F2_A_MU_DEPENDENCY"] == "UNDECLARED"
        assert summary["parameter_reparameterization_unchanged"] is True
        assert summary["models_merged"] is False
        assert summary["large_scale_exploration_launched"] is False
        assert sci["PHASE_10B4_STATUS"] == "CLOSED"
        assert sci["PHASE_10B4_TEST_COPY_ID"] == PHASE_10B4_TEST_COPY_ID
        assert sci["ranking_score_introduced"] is False
        assert sci["known_physics_comparison_executed"] is False
        assert sci["large_scale_generation_executed"] is False
        assert len(sci["dependency_validation_results"]) == 8
        ids = [item["model_id"] for item in sci["dependency_validation_results"]]
        assert ids == [f"MODEL_{i:04d}" for i in range(1, 9)]
        for item in sci["dependency_validation_results"]:
            assert item["historical_candidate_preserved"] is True
            assert item["syntax"] == "SYNTACTICALLY_GENERATED"
    after = snapshot_prior_artifact_hashes()
    assert before == after


def test_artifacts_exist_and_do_not_overwrite_priors():
    before = snapshot_prior_artifact_hashes()
    build_phase10b4_model().solve()
    after = snapshot_prior_artifact_hashes()
    assert before == after
    root = artifact_dir()
    for name in (
        "DEPENDENCY_VALIDATION_RESULTS.json",
        "DEPENDENCY_DEFINITIONS.json",
        "DEPENDENCY_AUDIT.json",
        "PHASE_10B4_SUMMARY.json",
    ):
        assert (root / name).is_file(), name
    assert root != phase10b1_artifact_dir()
    assert root != phase10b2_artifact_dir()
    assert root != phase10b3_artifact_dir()


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase10b4.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 10B.4: pre-analysis gate",
        "Phase 10B.4: dependency coverage",
        "Phase 10B.4: no numerical target search",
        "Phase 10B.4: banned tokens",
        "Phase 10B.4: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE 10B.4 SUMMARY" in text
    assert "PHASE 10B.4 CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "F2_A_MU_DEPENDENCY" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10b4_validation.py",
        root / "models" / "examples" / "phase10b4_model.py",
        root / "reporting" / "phase10b4_report.py",
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
