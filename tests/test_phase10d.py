"""Phase 10D: certified equivalence completion."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase10d_model import build_phase10d_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10b1_exploration import artifact_dir as phase10b1_artifact_dir
from physics_lab.physics.phase10d_equivalence import (
    EXPECTED_SOURCE_CATALOG_HASH,
    PHASE_10D_TEST_COPY_ID,
    analyze_phase10d_equivalence,
    artifact_dir,
    basis_transformation_test,
    classify_pair,
    conjugation_test,
    coordinate_reparametrization_test,
    field_redefinition_test,
    normalization_redefinition_test,
    operator_family_identity_proof,
    total_derivative_test,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def _catalog():
    import json

    return json.loads((phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json").read_text(encoding="utf-8"))


def test_source_catalog_hash_and_unchanged():
    catalog = phase10b1_artifact_dir() / "CANDIDATE_CATALOG.json"
    before = catalog.read_bytes()
    result = build_phase10d_model().solve()
    sci = result.metadata["phase10d_analysis"]
    after = catalog.read_bytes()
    assert before == after
    assert sci["SOURCE_CATALOG_HASH"] == EXPECTED_SOURCE_CATALOG_HASH
    assert sci["SOURCE_CATALOG_UNCHANGED"] is True
    assert not (artifact_dir() / "CANDIDATE_CATALOG.json").exists()


def test_field_redefinition_and_inverse():
    sign = field_redefinition_test("sign")
    ident = field_redefinition_test("identity")
    assert sign["status"] == "CERTIFIED_EQUIVALENT"
    assert ident["status"] == "CERTIFIED_EQUIVALENT"
    assert sign["invertible"] is True
    assert sign["inverse"] == sign["transformation"]


def test_basis_and_conjugation():
    basis = basis_transformation_test()
    conj = conjugation_test()
    assert basis["status"] == "CERTIFIED_EQUIVALENT"
    assert basis["O_orthogonal"] is True
    assert basis["physical_representation_content_changed"] is False
    assert conj["status"] == "CERTIFIED_EQUIVALENT"
    assert conj["eigenvalue_coincidence_used"] is False


def test_total_derivative_boundary_rules():
    ok = total_derivative_test(boundary_assumption="as in 5B.0 where used", lagrangian_difference="0")
    absent = total_derivative_test(boundary_assumption=None, lagrangian_difference="0")
    f2 = total_derivative_test(boundary_assumption="as in 5B.0 where used", lagrangian_difference="F2")
    assert ok["status"] == "CERTIFIED_EQUIVALENT"
    assert absent["status"] == "REJECTED"
    assert f2["status"] == "NOT_TOTAL_DERIVATIVE"


def test_coordinate_and_normalization():
    coord = coordinate_reparametrization_test()
    norm = normalization_redefinition_test()
    assert coord["status"] == "CERTIFIED_EQUIVALENT"
    assert coord["kind"] == "DESCRIPTIONAL EQUIVALENCE"
    assert norm["status"] == "CERTIFIED_EQUIVALENT"
    assert norm["absorbs_physical_parameter"] is False


def test_singular_field_redefinition_rejected():
    out = field_redefinition_test("singular")
    assert out["status"] == "REJECTED"
    assert out["invertible"] is False


def test_operator_field_content_and_gauge_axes():
    proof = operator_family_identity_proof()
    assert proof["status"] == "CERTIFIED_EQUIVALENT"
    assert proof["parameter_status_after"] == "PARAMETER-DEPENDENT"
    cat = {item["model_id"]: item for item in _catalog()}
    assert classify_pair(cat["MODEL_0001"], cat["MODEL_0002"])["final_status"] == "CERTIFIED_EQUIVALENT"
    assert classify_pair(cat["MODEL_0001"], cat["MODEL_0005"])["final_status"] == "EQUIVALENCE_UNSUPPORTED"
    assert classify_pair(cat["MODEL_0001"], cat["MODEL_0003"])["final_status"] == "CERTIFIED_DISTINCT"


def test_invariant_mismatch_and_insufficient_proof():
    cat = {item["model_id"]: item for item in _catalog()}
    distinct = classify_pair(cat["MODEL_0005"], cat["MODEL_0007"])
    unsupported = classify_pair(cat["MODEL_0003"], cat["MODEL_0007"])
    assert distinct["final_status"] == "CERTIFIED_DISTINCT"
    assert "independent dynamical" in distinct["invariant_test"]
    assert unsupported["final_status"] == "EQUIVALENCE_UNSUPPORTED"
    assert unsupported["final_status"] != "CERTIFIED_DISTINCT"


def test_equivalence_relation():
    sci = build_phase10d_model().solve().metadata["phase10d_analysis"]
    assert sci["TRANSITIVITY_STATUS"] == "VERIFIED"
    cat = {item["model_id"]: item for item in _catalog()}
    for mid in cat:
        assert classify_pair(cat[mid], cat[mid])["final_status"] == "CERTIFIED_EQUIVALENT"
    a = classify_pair(cat["MODEL_0001"], cat["MODEL_0002"])["final_status"]
    b = classify_pair(cat["MODEL_0002"], cat["MODEL_0001"])["final_status"]
    assert a == b == "CERTIFIED_EQUIVALENT"
    assert sci["CERTIFIED_EQUIVALENCE_COMPONENT_COUNT"] == 4


def test_no_targets_ranking_or_generation():
    sci = build_phase10d_model().solve().metadata["phase10d_analysis"]
    assert sci["numerical_target_search"] is False
    assert sci["NO_TARGET_VALUES_USED"] is True
    assert sci["models_generated"] == 0
    assert sci["NO_RANKING_PERFORMED"] is True
    blob = sci["equivalence_catalog"]

    def walk(obj):
        if isinstance(obj, dict):
            for key, val in obj.items():
                assert key not in {
                    "ra" + "nk",
                    "sc" + "ore",
                    "win" + "ner",
                    "best" + "_" + "model",
                    "top" + "_" + "model",
                    "similarity" + "_" + "score",
                }
                walk(val)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(blob)


def test_grammar_freeze_provenance_and_determinism():
    freeze_before = EXPECTED_FROZEN_HASH
    auth = authorize_phase5b0_analysis()
    a = analyze_phase10d_equivalence(auth, write_artifacts=False)
    b = analyze_phase10d_equivalence(auth, write_artifacts=False)
    assert a["GRAMMAR_UNCHANGED"] is True
    assert a["action_content_hash"] == freeze_before
    assert a["SOURCE_CATALOG_HASH"] == b["SOURCE_CATALOG_HASH"]
    assert a["equivalence_catalog"]["pairwise_results"] == b["equivalence_catalog"]["pairwise_results"]
    for item in a["equivalence_catalog"]["parameter_reclassification_audit"]:
        assert item["INPUT_relabeled_as_DERIVED"] is False
        assert item["PARAMETER_DEPENDENT_relabeled_as_parameter_free"] is False


def test_source_hash_mismatch_invalidates():
    auth = authorize_phase5b0_analysis()
    out = analyze_phase10d_equivalence(
        auth,
        write_artifacts=False,
        expected_source_catalog_hash="0" * 64,
    )
    assert out["status"] == "INTERPRETATION_INVALIDATED"


def test_full_audit_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase10d_model(signature=sig).solve()
        sci = result.metadata["phase10d_analysis"]
        integ = result.metadata["phase10d_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert sci["PHASE_10D_STATUS"] == "COMPLETE"
        assert sci["PHASE_10D_CLOSED"] is True
        assert sci["PHASE_10D_TEST_COPY_ID"] == PHASE_10D_TEST_COPY_ID
        assert sci["UNIQUE_UNORDERED_PAIRS"] == 28
        assert sci["CERTIFIED_EQUIVALENT_PAIR_COUNT"] == 4
        assert sci["CERTIFIED_DISTINCT_PAIR_COUNT"] == 16
        assert sci["EQUIVALENCE_UNSUPPORTED_PAIR_COUNT"] == 8
        assert sci["FIELD_CONTENT_EQUIVALENCE_STATUS"] == "PARTIAL"
        assert sci["OPERATOR_EQUIVALENCE_STATUS"] == "VERIFIED"
        assert sci["GAUGE_SECTOR_EQUIVALENCE_STATUS"] == "VERIFIED"


def test_artifacts_and_yaml_validator():
    build_phase10d_model().solve()
    root = artifact_dir()
    for name in (
        "PHASE_10D_EQUIVALENCE_CATALOG.json",
        "PAIRWISE_RESULTS.json",
        "CERTIFIED_EQUIVALENCE_GRAPH.json",
        "PHASE_10D_SUMMARY.json",
    ):
        assert (root / name).is_file(), name
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase10d.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 10D: pre-analysis gate",
        "Phase 10D: equivalence coverage",
        "Phase 10D: no numerical target comparison",
        "Phase 10D: banned tokens",
        "Phase 10D: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "PHASE 10D — CERTIFIED EQUIVALENCE COMPLETION" in text
    assert "PHASE 10D CLOSED" in text
    assert "EQUIVALENCE_UNSUPPORTED is not CERTIFIED_DISTINCT" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10d_equivalence.py",
        root / "models" / "examples" / "phase10d_model.py",
        root / "reporting" / "phase10d_report.py",
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
        "best" + "_" + "model",
        "top" + "_" + "candidates",
        "analyze_phase10b1_exploration",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
