"""Phase 14C.4 tests: P4 known-model reference comparison only."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c4_model import build_phase14c4_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase14b0_engine import EngineFailure
from physics_lab.physics.phase14c0_known_physics import (
    assert_profile_activation_authorized,
    assert_profile_not_p4_in_generation,
    catalog_hash,
    g6_candidate_space_hash,
    g6_class_rows,
)
from physics_lab.physics.phase14c4_p4 import (
    ALLOWED_MATCH_STATUSES,
    CATALOG_REFERENCE_IDS,
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_CATALOG_HASH,
    EXPECTED_G6_GRAMMAR_HASH,
    EXPECTED_P4_PROFILE_HASH,
    FORBIDDEN_RANK_LABELS,
    P4_ID,
    candidate_structural_fingerprint,
    compare_all_candidates,
    compare_candidate_to_reference,
    comparison_engine_registry,
    p4_profile,
    p4_test_registry,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c4_solve_and_status(sig):
    result = build_phase14c4_model(signature=sig).solve()
    sci = result.metadata["phase14c4_analysis"]
    integ = result.metadata["phase14c4_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C4_STATUS"] == "CLOSED"
    assert sci["P3_EXECUTED"] is True
    assert sci["P4_EXECUTED"] is True
    assert sci["P5_EXECUTED"] is False
    assert sci["P4_STATUS"] == "CLOSURE_REACHED"
    assert sci["G6_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["CANDIDATES_TESTED"] == 479
    assert sci["P3_COMPLETE"] == 359
    assert sci["P3_PARTIAL"] == 120
    assert sci["P4_ELIMINATED"] == 0
    assert sci["P4_GENERATED_NEW_CANDIDATES"] is False
    assert sci["P4_FILTERED_CANDIDATES"] is False
    assert sci["P4_RANKED"] is False
    assert sci["gravity_changed"] is False
    assert sci["ranking"] is False
    assert sci["CANDIDATE_SPACE_HASH_BEFORE"] == sci["CANDIDATE_SPACE_HASH_AFTER"] == EXPECTED_CANDIDATE_SPACE_HASH
    assert sci["COMPARISON_NUMERICAL_DATA"] == "DISABLED"
    assert sci["NO_EXACT_REGISTERED_REFERENCE_MATCHES_WITHIN_DECLARED_CATALOG"] is True
    assert sci["catalog_exact_MATCH_count"] == 0
    assert sci["NEXT_AUTHORIZED_EXTENSION_EXECUTED"] is False
    assert integ["P4_EXECUTED"] == "TRUE"
    assert integ["P5_EXECUTED"] == "FALSE"


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c4_validator(sig):
    report = validate(build_phase14c4_model(signature=sig), build_phase14c4_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c4_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c4.yaml"
    from physics_lab.models.loader import load_model

    model = load_model(path)
    result = model.solve()
    sci = result.metadata["phase14c4_analysis"]
    assert sci["PHASE_14C4_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_p3_p4_profile_integrity_and_isolation():
    profile = p4_profile()
    assert profile["profile_id"] == P4_ID
    assert profile["profile_hash"] == EXPECTED_P4_PROFILE_HASH
    assert profile["activation_state"] == "REFERENCE_ONLY_ISOLATED"
    assert profile["generation_allowed"] is False
    assert profile["filtering_allowed"] is False
    assert profile["ranking_allowed"] is False
    assert catalog_hash() == EXPECTED_CATALOG_HASH
    with pytest.raises(EngineFailure) as ei:
        assert_profile_activation_authorized(P4_ID)
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        assert_profile_not_p4_in_generation(P4_ID)
    assert ej.value.mode == "KNOWN_MODEL_ISOLATION_VIOLATION"


def test_exact_partial_none_unresolved_classification():
    rows = g6_class_rows()
    complete = next(r for r in rows if r["completeness"] == "COMPLETE")
    fp = candidate_structural_fingerprint(dict(complete))
    refs = {item["reference_id"]: item for item in comparison_engine_registry()["catalog_references"] + comparison_engine_registry()["framework_references"]}
    eh = compare_candidate_to_reference(fp, refs["FW_EINSTEIN_HILBERT"])
    assert eh["match_status"] == "MATCH"
    assert eh["provenance"] == "RECOGNIZED_MATCH"
    assert eh["structural_equivalence_certified"] is False
    kg = compare_candidate_to_reference(fp, refs["FW_KLEIN_GORDON_TYPE"])
    assert kg["match_status"] == "MATCH"
    ym = compare_candidate_to_reference(fp, refs["FW_YANG_MILLS_TYPE"])
    assert ym["match_status"] == "PARTIAL_MATCH"
    assert "F2_present" in ym["unmatched_features"]
    assert "has_nonabelian_factor" in ym["matched_features"]
    sm_rep = compare_candidate_to_reference(fp, refs["REF_SM_REPRESENTATION_ASSIGNMENTS"])
    assert sm_rep["match_status"] == "COMPARISON_UNRESOLVED"
    assert "reference_fingerprint_incomplete" in sm_rep["unresolved_features"]
    no_u1 = next(r for r in rows if r["completeness"] == "COMPLETE" and "U(1)" not in r["gauge_group"])
    mx = compare_candidate_to_reference(candidate_structural_fingerprint(dict(no_u1)), refs["FW_MAXWELL_TYPE"])
    assert mx["match_status"] == "NO_MATCH"
    assert mx["filtering_effect"] == "NONE"


def test_g4_partiality_never_upgraded():
    partial = next(r for r in g6_class_rows() if r["completeness"] == "PARTIAL_G4_DEPENDENCY")
    fp = candidate_structural_fingerprint(dict(partial))
    assert fp["SSB"] == "g4_partial"
    refs = {item["reference_id"]: item for item in comparison_engine_registry()["framework_references"]}
    ssb = compare_candidate_to_reference(fp, refs["FW_SSB_GAUGE"])
    assert ssb["match_status"] in {"PARTIAL_MATCH", "COMPARISON_UNRESOLVED"}
    assert ssb["match_status"] != "MATCH"
    assert ssb["G4_partiality_dependency"] == "DEPENDS_ON_G4_PARTIALITY"
    assert ssb["upgraded_from_partial"] is False


def test_no_ranking_and_multiple_references():
    compared = compare_all_candidates()
    records = compared["records"]
    assert all(item["match_status"] in ALLOWED_MATCH_STATUSES for item in records)
    blob = str(records)
    for label in FORBIDDEN_RANK_LABELS:
        assert label not in blob
    one_hash = records[0]["candidate_hash"]
    subset = [item for item in records if item["candidate_hash"] == one_hash]
    assert len(subset) == len(compared["references"])
    assert len({item["reference_id"] for item in subset}) == len(compared["references"])


def test_qed_qcd_isolation_not_identity():
    compared = compare_all_candidates()
    for item in compared["records"]:
        if item["reference_id"] in {"REF_QCD_STRUCTURE", "FW_QED_TYPE"}:
            assert item["match_status"] != "MATCH"
            assert item["identity_claim"] == "NOT_ASSERTED"
            assert item["structural_equivalence_certified"] is False
        if item["reference_id"] in CATALOG_REFERENCE_IDS:
            assert item["match_status"] != "MATCH"
            assert "DERIVED_FROM_MODEL_REFERENCE" not in str(item)


def test_registry_has_twenty_tests_and_no_banned_tokens():
    registry = p4_test_registry()
    assert registry["registry_id"] == "P4_KNOWN_MODEL_REFERENCE_TEST_REGISTRY"
    assert len(registry["tests"]) == 20
    assert g6_candidate_space_hash() == EXPECTED_CANDIDATE_SPACE_HASH
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c4_p4.py",
        root / "models" / "examples" / "phase14c4_model.py",
        root / "reporting" / "phase14c4_report.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "from physics_lab.physics.gauge_internal" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text
        assert "best_model" not in text
        assert "preferred_model" not in text
        assert "top_model" not in text
        assert "def choose_group_to_match_SM" not in text
        for label in FORBIDDEN_RANK_LABELS:
            assert label not in text
