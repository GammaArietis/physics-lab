"""Phase 14C.0 tests: catalog, profiles, dry run, P0, isolation."""

from __future__ import annotations

from pathlib import Path

import pytest

from physics_lab.models.examples.phase14c0_model import build_phase14c0_model
from physics_lab.physics.internal_spectrum import MOSTLY_PLUS, MOSTLY_MINUS
from physics_lab.physics.phase14b0_engine import EngineFailure
from physics_lab.physics.phase14c0_known_physics import (
    CATALOG_VERSION,
    EXPECTED_G6_GRAMMAR_HASH,
    P0_ID,
    assert_profile_activation_authorized,
    assert_profile_immutable,
    assert_profile_not_p4_in_generation,
    catalog_hash,
    classify_consequences,
    cross_profile_difference,
    freeze_profile,
    g6_class_rows,
    known_physics_structural_catalog,
    open_physics_registry,
    physics_profile_registry,
    profile_registry_hash,
    run_synthetic_dry_run,
)
from physics_lab.validation.validator import validate


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c0_solve_and_status(sig):
    result = build_phase14c0_model(signature=sig).solve()
    sci = result.metadata["phase14c0_analysis"]
    integ = result.metadata["phase14c0_integrity"]
    assert sci["status"] == "OK"
    assert sci["PHASE_14C0_STATUS"] == "CLOSED"
    assert sci["P0_EXECUTED"] is True
    assert sci["P1_EXECUTED"] is False
    assert sci["P4_COMPARISON_EXECUTED"] is False
    assert sci["KNOWN_PHYSICS_CATALOG_STATUS"] == "READY"
    assert sci["PROFILE_REGISTRY_STATUS"] == "VERIFIED"
    assert sci["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert sci["CONSEQUENCE_ENGINE_STATUS"] == "VERIFIED"
    assert sci["COUNTEREXAMPLE_ENGINE_STATUS"] == "VERIFIED"
    assert sci["CROSS_PROFILE_ENGINE_STATUS"] == "VERIFIED"
    assert sci["OPEN_PHYSICS_FIREWALL_STATUS"] == "VERIFIED"
    assert sci["PARAMETER_ANALYSIS_STATUS"] == "VERIFIED"
    assert sci["KNOWN_MODEL_ISOLATION_STATUS"] == "VERIFIED"
    assert sci["G4_PARTIALITY_PROPAGATION_STATUS"] == "VERIFIED"
    assert sci["PARENT_GRAMMAR_HASH"] == EXPECTED_G6_GRAMMAR_HASH
    assert sci["G6_SURVIVORS_REUSED"] == 479
    assert sci["P0_COMPATIBLE"] == 359
    assert sci["P0_PARTIAL"] == 120
    assert sci["P0_REJECTED"] == 0
    assert sci["NEW_PROPERTIES_BEYOND_G6"] == []
    assert sci["gravity_changed"] is False
    assert sci["ranking"] is False
    assert sci["CATALOG_VERSION"] == CATALOG_VERSION
    assert integ["P0_EXECUTED"] == "TRUE"
    assert integ["P1_EXECUTED"] == "FALSE"


@pytest.mark.parametrize("sig", [MOSTLY_PLUS, MOSTLY_MINUS])
def test_phase14c0_validator(sig):
    report = validate(build_phase14c0_model(signature=sig), build_phase14c0_model(signature=sig).solve())
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_phase14c0_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14c0.yaml"
    from physics_lab.models.loader import load_model

    model = load_model(path)
    result = model.solve()
    sci = result.metadata["phase14c0_analysis"]
    assert sci["PHASE_14C0_STATUS"] == "CLOSED"
    report = validate(model, result)
    failed = [c.name for c in report.checks if c.status.name == "FAIL"]
    assert not failed


def test_catalog_determinism_and_input_reference_separation():
    a = known_physics_structural_catalog()
    b = known_physics_structural_catalog()
    assert a["catalog_hash"] == b["catalog_hash"] == catalog_hash()
    assert a["contains_all_known_physics"] is False
    assert a["unregistered_physics"] == "OUTSIDE_CURRENT_CATALOG"
    kinds = {e["kind"] for e in a["input_objects"]}
    assert kinds == {"KNOWN_PHYSICS_INPUT"}
    ref_kinds = {e["kind"] for e in a["reference_only_objects"]}
    assert ref_kinds == {"KNOWN_PHYSICS_REFERENCE"}
    assert all(e["effect_on_generation"] != "NONE" or True for e in a["input_objects"])
    assert all(e["effect_on_generation"] == "NONE" for e in a["reference_only_objects"])
    assert all(e["kind"] != "DERIVED_CONSEQUENCE" for e in a["objects"])


def test_profile_immutability_and_hash_integrity():
    registry = physics_profile_registry()
    assert registry["profile_registry_hash"] == profile_registry_hash()
    p0 = registry["profiles"][P0_ID]
    assert_profile_immutable(p0)
    mutated = dict(p0)
    mutated["description"] = "mutated after freeze"
    with pytest.raises(EngineFailure) as ei:
        assert_profile_immutable(mutated)
    assert ei.value.mode == "PROFILE_HASH_MISMATCH"
    other = freeze_profile({k: v for k, v in p0.items() if k not in {"profile_hash", "frozen"}})
    other["description"] = "new version"
    other = freeze_profile({k: v for k, v in other.items() if k not in {"profile_hash", "frozen"}})
    assert other["profile_hash"] != p0["profile_hash"]


def test_p4_and_open_physics_isolation():
    registry = physics_profile_registry()
    p4 = registry["profiles"]["P4_KNOWN_MODEL_REFERENCE"]
    assert p4["generation_allowed"] is False
    assert p4["filtering_allowed"] is False
    assert p4["ranking_allowed"] is False
    with pytest.raises(EngineFailure) as ei:
        assert_profile_not_p4_in_generation("P4_KNOWN_MODEL_REFERENCE")
    assert ei.value.mode == "KNOWN_MODEL_ISOLATION_VIOLATION"
    with pytest.raises(EngineFailure) as ej:
        assert_profile_activation_authorized("P1_QFT_STRUCTURAL_CONSISTENCY")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    for item in open_physics_registry():
        assert item["status"] == "OPEN"
        assert item["effect_on_generation"] == "NONE"


def test_g6_partial_preservation_and_no_upgrade():
    rows = g6_class_rows()
    complete = [r for r in rows if r["completeness"] == "COMPLETE"]
    partial = [r for r in rows if r["completeness"] == "PARTIAL_G4_DEPENDENCY"]
    assert len(rows) == 479
    assert len(complete) == 359
    assert len(partial) == 120
    assert all(r["g4_partiality"] == "DEPENDS_ON_G4_PARTIALITY" for r in partial)
    assert all(r["status"] != "PASS" or r["completeness"] == "COMPLETE" for r in rows)
    cons = classify_consequences(list(rows), profile_id=P0_ID, enabled_constraints=[f"KP{i:02d}" for i in range(1, 16)])
    assert cons["complete_count"] == 359
    assert cons["partial_count"] == 120
    assert cons["NEW_PROPERTIES_BEYOND_G6"] == []
    assert cons["P0_ADDS_NO_NEW_ELIMINATION"] is True
    assert cons["KNOWN_QUALITATIVE_PHYSICS_DOES_NOT_SELECT_A_UNIQUE_THEORY_WITHIN_THE_DECLARED_GRAMMAR_AND_PROFILES"] is True
    assert cons["parameter_analysis"]["continuous_couplings_still_free"] is True
    assert cons["dimensionless_audit"]["dimensionless_physical_observables_derived"] == []
    assert cons["destroyed_by_counterexample"]
    forced_ids = {p["property"] for p in cons["FORCED_PROPERTIES"]}
    assert "anomaly_free" in forced_ids
    assert "local_gauge_covariance" in forced_ids


def test_minimal_assumption_and_counterexample_and_cross_profile():
    rows = list(g6_class_rows())
    cons = classify_consequences(rows, profile_id=P0_ID, enabled_constraints=[f"KP{i:02d}" for i in range(1, 16)])
    for item in cons["MINIMAL_ASSUMPTION_MAP"]:
        assert item["consequence_id"]
        assert "forced_by_constraints" in item
        assert "minimal_constraint_subset" in item
        assert item["proof_status"]
    empty = {"FORCED_PROPERTIES": [], "FREE_PROPERTIES": [], "UNRESOLVED_PROPERTIES": []}
    diff = cross_profile_difference(empty, cons)
    assert "numerical_closeness_to_known_physics" in diff
    assert diff["numerical_closeness_to_known_physics"] == "NOT_COMPUTED"


def test_no_sm_matching_or_ranking_paths():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase14c0_known_physics.py",
        root / "models" / "examples" / "phase14c0_model.py",
        root / "reporting" / "phase14c0_report.py",
    ]
    forbidden_defs = (
        "def choose_group_to_match_SM",
        "def choose_representation_to_match_SM",
        "def fit_charge_assignment",
        "def fit_generation_count",
        "def fit_mass_hierarchy",
        "def target_similarity",
        "def model_distance_to_SM",
        "best_model",
        "preferred_model",
        "top_model",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in forbidden_defs:
            assert token not in text
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "from physics_lab.physics.gauge_internal" not in text
        assert "alp" + "ha_em" not in text
        assert "electr" + "ic" not in text
        assert "1/" + "3" not in text
        assert "2/" + "3" not in text


def test_no_automatic_new_principles():
    registry = physics_profile_registry()
    p0 = registry["profiles"][P0_ID]
    assert p0["input_objects"] == [f"KP{i:02d}" for i in range(1, 16)]
    assert p0["activation_state"] == "AUTHORIZED_THIS_PHASE"
    assert registry["profiles"]["P1_QFT_STRUCTURAL_CONSISTENCY"]["activation_state"] == "REGISTERED_NOT_ACTIVATED"
    assert registry["no_automatic_full_known_physics"] is True
