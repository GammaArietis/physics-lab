"""Phase 11A: parameter-constraint strategy audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase11a_model import build_phase11a_model
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
from physics_lab.physics.phase11a_strategy import (
    AUDIT_VERSION,
    EXPECTED_GRAMMAR_HASH,
    PHASE_11A_TEST_COPY_ID,
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


def test_strategy_run_preserves_history():
    before = snapshot_prior_artifact_hashes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase11a_model(signature=sig).solve()
        sci = result.metadata["phase11a_analysis"]
        integ = result.metadata["phase11a_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["audit_summary"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert sci["grammar_hash"] == EXPECTED_GRAMMAR_HASH
        assert summary["candidates_analyzed"] == 8
        assert summary["new_assumptions"] == 0
        assert summary["new_dependencies"] == 0
        assert summary["ranking"] is False
        assert summary["known_physics_comparison"] is False
        assert summary["principle_chosen"] == "NONE"
        assert summary["principle_implemented"] is False
        assert summary["F2_A_MU_DEPENDENCY"] == "UNDECLARED"
        assert summary["candidates_regenerated"] is False
        assert summary["MODEL_SPEC_rewrites"] == 0
        assert summary["PHASE_10B_STATUS"] == "CLOSED_NO_INTERNAL_CLOSURE"
        assert sci["PHASE_11A_STATUS"] == "CLOSED"
        assert sci["PHASE_11A_TEST_COPY_ID"] == PHASE_11A_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["ranking_score_introduced"] is False
        assert sci["phase_11b_executed"] is False
        assert sci["principle_chosen"] == "NONE"
        assert sci["overclaims"]["5_start_phase_11b"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["1_choose_a_principle"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["2_canonical_norm_is_physical_determination"] == "REJECTED AS OVERCLAIM"
        assert len(sci["master_matrix"]) == 7
        assert len(sci["mechanism_table"]) == 22
        assert len(sci["parameter_mechanism_matrix"]) == 7 * 22
        assert "no_external_dimensionful_scales" in sci["NOT_TESTED_RELEVANT_MECHANISMS"]
        assert sci["design_filter"]["chosen_mechanism"] == "NONE"
        assert sci["design_filter"]["not_called_best"] is True
        assert summary["dependency_valid"] == 2
        assert summary["dependency_unchecked"] == 6
        assert summary["dependency_invalid"] == 0
    after = snapshot_prior_artifact_hashes()
    assert before == after


def test_artifacts_exist_and_do_not_overwrite_priors():
    before = snapshot_prior_artifact_hashes()
    build_phase11a_model().solve()
    after = snapshot_prior_artifact_hashes()
    assert before == after
    root = artifact_dir()
    for name in (
        "PARAMETER_INVENTORY.json",
        "MECHANISM_TAXONOMY.json",
        "PARAMETER_MECHANISM_MATRIX.json",
        "MASTER_MATRIX.json",
        "MECHANISM_TABLE.json",
        "NEW_PRINCIPLE_CANDIDATES.json",
        "NOT_TESTED_RELEVANT_MECHANISMS.json",
        "PHASE_11A_SUMMARY.json",
    ):
        assert (root / name).is_file(), name
    assert root != phase10b1_artifact_dir()
    assert root != phase10b10_artifact_dir()


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase11a.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 11A: pre-analysis gate",
        "Phase 11A: strategy coverage",
        "Phase 11A: no numerical target search",
        "Phase 11A: banned tokens",
        "Phase 11A: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE_11A_SUMMARY" in text
    assert "PHASE 11A CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "UNCHECKED is not INVALID" in text
    assert "No mechanism is selected" in text
    assert "canonical normalization is not physical determination" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase11a_strategy.py",
        root / "models" / "examples" / "phase11a_model.py",
        root / "reporting" / "phase11a_report.py",
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
        "most_promising",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
