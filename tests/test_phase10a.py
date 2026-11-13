"""Phase 10A: model-space grammar infrastructure."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import pytest

from physics_lab.models.examples.phase10a_model import build_phase10a_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import (
    PHASE_10A_TEST_COPY_ID,
    AssumptionLockError,
    GrammarValidationError,
    add_assumption,
    baseline_model_spec,
    canonicalize_model_spec,
    deduplicate_models,
    enumerate_combination_ids,
    example_catalog,
    example_catalog_hash,
    grammar_hash,
    is_legal_generator_input,
    legal_generator_inputs,
    lock_for_solve,
    mandatory_rule_set,
    model_hash,
    reference_catalog,
    reference_catalog_hash,
    refuse_example_as_generator_input,
    refuse_reference_as_generator_input,
    refuse_large_scale_generation,
    reject_if_not_legal_generator_input,
    search_manifest,
    search_size_estimate,
    validate_claim_separation,
    validate_model_spec,
    whitelist,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_infrastructure_both_signatures():
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase10a_model(signature=sig).solve()
        sci = result.metadata["phase10a_analysis"]
        integ = result.metadata["phase10a_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert sci["MODEL_GRAMMAR_STATUS"] == "READY"
        assert sci["PROVENANCE_FIREWALL_STATUS"] == "VERIFIED"
        assert sci["CANONICALIZATION_STATUS"] == "VERIFIED"
        assert sci["DEDUPLICATION_STATUS"] == "VERIFIED"
        assert sci["PARAMETER_ACCOUNTING_STATUS"] == "VERIFIED"
        assert sci["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
        assert sci["SEARCH_REPRODUCIBILITY_STATUS"] == "VERIFIED"
        assert sci["KNOWN_PHYSICS_ISOLATION_STATUS"] == "VERIFIED"
        assert sci["MANDATORY_RULES_STATUS"] == "VERIFIED"
        assert sci["REFERENCE_SEPARATION_STATUS"] == "VERIFIED"
        assert sci["EXAMPLE_SEPARATION_STATUS"] == "VERIFIED"
        assert sci["GRAMMAR_REGISTRATION_STATUS"] == "VERIFIED"
        assert sci["WHITELIST_STATUS"] == "VERIFIED"
        assert sci["BLACKLIST_STATUS"] == "VERIFIED"
        assert sci["PHASE_10A_STATUS"] == "CLOSED"
        assert sci["large_scale_generation_executed"] is False
        assert sci["ranking_score_introduced"] is False
        assert sci["target_based_objective_function"] is False
        assert sci["baseline_serialization_deterministic"] is True
        assert sci["operator_order_equivalence"] == "DUPLICATE"
        assert sci["unsupported_basis_equivalence"] == "EQUIVALENCE_UNSUPPORTED"
        assert sci["assumption_lock_ok"] is True
        assert sci["F2_in_baseline"] is False
        assert sci["phase_5c_unchanged"] is True
        assert sci["phase_5d_unchanged"] is True
        assert sci["phase_6_unchanged"] is True
        assert sci["phase_7_unchanged"] is True
        assert sci["phase_8_unchanged"] is True
        assert sci["phase_9_unchanged"] is True
        assert sci["phase_9_INTERNAL_CLOSURE_STATUS"] == "CLOSED"
        assert sci["PHASE_10A_CLOSED"] is True
        assert sci["PHASE_10A_TEST_COPY_ID"] == PHASE_10A_TEST_COPY_ID
        assert sci["number_of_models_examined"] == 1
        assert sci["number_of_models_generated"] == 0
        assert sci["search_size_estimate"]["finite_combination_count"] == 8
        assert sci["examples_not_in_generation"] is True
        assert sci["example_change_does_not_change_grammar_hash"] is True
        assert sci["reference_change_does_not_change_grammar_hash"] is True
        assert sci["rule_change_changes_hash"] is True
        assert sci["whitelist_change_changes_hash"] is True
        assert sci["frozen_hash_unchanged"] is True
        manifest = sci["search_manifest"]
        assert manifest["grammar_version"] == sci["grammar_version"]
        assert manifest["generation_bounds"]["large_scale_generation"] is False
        assert manifest["stage_A"] == "PREPARED_NOT_RUN"
        assert manifest["stage_B"] == "PREPARED_NOT_RUN"


def test_canonicalization_hash_dedup_and_seed():
    base = baseline_model_spec()
    assert canonicalize_model_spec(base) == canonicalize_model_spec(copy.deepcopy(base))
    assert model_hash(base) == model_hash(copy.deepcopy(base))
    a = copy.deepcopy(base)
    b = copy.deepcopy(base)
    a["operator_spec"]["operators"] = [{"id": "A_op", "class": "probe"}, {"id": "B_op", "class": "probe"}]
    b["operator_spec"]["operators"] = [{"id": "B_op", "class": "probe"}, {"id": "A_op", "class": "probe"}]
    assert deduplicate_models(a, b) == "DUPLICATE"
    c = copy.deepcopy(base)
    d = copy.deepcopy(base)
    d["internal_basis_convention"] = "rotated_ONB_unsupported"
    assert deduplicate_models(c, d) == "EQUIVALENCE_UNSUPPORTED"
    e = copy.deepcopy(base)
    e["gravity_spec"] = {"family": "different"}
    assert deduplicate_models(base, e) == "DISTINCT"
    assert enumerate_combination_ids(seed=7) == enumerate_combination_ids(seed=7)
    assert enumerate_combination_ids(seed=7) != enumerate_combination_ids(seed=11)
    assert search_size_estimate()["finite_combination_count"] == 8


def test_mandatory_rules_separated_from_examples():
    claims = validate_claim_separation()
    assert claims["status"] == "VERIFIED"
    rules = mandatory_rule_set()
    assert [item["identifier"] for item in rules] == [f"M{i}" for i in range(1, 21)]
    assert all(item["status"] == "MANDATORY" for item in rules)
    assert all(item["generator_enabled"] is False for item in rules)
    examples = example_catalog()
    assert [item["identifier"] for item in examples] == [
        "E1_internal_dimension_illustrations",
        "E2_symmetry_illustrations",
        "E3_operator_illustrations",
        "E4_gauge_sector_illustrations",
        "E5_complexity_illustrations",
        "E6_cluster_label_illustrations",
        "E7_unregistered_axis_illustrations",
    ]
    assert all(item["status"] == "EXAMPLE_ONLY" for item in examples)
    assert all(item["generator_enabled"] is False for item in examples)
    references = reference_catalog()
    assert all(item["status"] == "REFERENCE_ONLY" for item in references)
    assert all(item["generator_enabled"] is False for item in references)
    combo = "\n".join(enumerate_combination_ids())
    legal_ids = {item["identifier"] for item in legal_generator_inputs()}
    for item in examples:
        assert item["identifier"] not in combo
        assert item["identifier"] not in legal_ids
        assert not is_legal_generator_input(item["identifier"])
        with pytest.raises(GrammarValidationError):
            refuse_example_as_generator_input(item)
        with pytest.raises(GrammarValidationError):
            reject_if_not_legal_generator_input(item["identifier"])
    for item in references:
        assert item["identifier"] not in combo
        assert item["identifier"] not in legal_ids
        assert not is_legal_generator_input(item["identifier"])
        with pytest.raises(GrammarValidationError):
            refuse_reference_as_generator_input(item)
        with pytest.raises(GrammarValidationError):
            reject_if_not_legal_generator_input(item["identifier"])
    with pytest.raises(GrammarValidationError):
        reject_if_not_legal_generator_input("unregistered_structure")
    for item in whitelist():
        assert "identifier" in item
        assert "mathematical_definition" in item
        assert "status" in item
        assert "provenance" in item
        assert "generator_enabled" in item
        assert "bounds" in item
        assert "dependencies" in item
        if item["generator_enabled"] is True:
            assert item["status"] == "MANDATORY"
            assert is_legal_generator_input(item["identifier"])
            assert "allowed_parameters" in item
            assert "maximum_complexity" in item
            assert "known_symmetries" in item
    h_g = grammar_hash()
    from physics_lab.physics.action_serializer import canonical_json_bytes
    from physics_lab.physics.phase10a_model_grammar import (
        LEGAL_CLAIM_CLASSES,
        _grammar_hash_payload,
        claim_classifications,
    )
    from physics_lab.physics.phase10a_known_physics import KNOWN_PHYSICS_CATALOG

    mutated = copy.deepcopy(examples)
    mutated[0]["mathematical_definition"] += " extra illustration"
    assert hashlib.sha256(canonical_json_bytes(mutated)).hexdigest() != example_catalog_hash()
    assert grammar_hash() == h_g
    mutated_ref = copy.deepcopy(references)
    mutated_ref[0]["mathematical_definition"] += " extra reference"
    assert hashlib.sha256(canonical_json_bytes(mutated_ref)).hexdigest() != reference_catalog_hash()
    assert grammar_hash() == h_g
    payload = _grammar_hash_payload()
    payload["mandatory_rules"][0]["mathematical_definition"] += " extra rule"
    assert hashlib.sha256(canonical_json_bytes(payload)).hexdigest() != h_g
    payload_w = _grammar_hash_payload()
    payload_w["legal_generator_inputs"][0]["mathematical_definition"] += " extra whitelist"
    assert hashlib.sha256(canonical_json_bytes(payload_w)).hexdigest() != h_g
    classes = {claim["claim_class"] for claim in claim_classifications()}
    assert classes <= LEGAL_CLAIM_CLASSES
    assert "CLASSIFICATION_ERROR" not in classes
    assert "AMBIGUOUS" not in classes
    for token in ("1/" + "13" + "7", "alp" + "ha_em"):
        assert not is_legal_generator_input(token)
        with pytest.raises(GrammarValidationError):
            reject_if_not_legal_generator_input(token)
    for name, entry in KNOWN_PHYSICS_CATALOG.items():
        assert entry["status"] == "REFERENCE_ONLY"
        assert entry["generator_enabled"] is False
        assert not is_legal_generator_input(name)
        with pytest.raises(GrammarValidationError):
            reject_if_not_legal_generator_input(name)
    with pytest.raises(RuntimeError, match="refuses large-scale generation"):
        refuse_large_scale_generation()


def test_firewall_rejects_experimental_targets_and_silent_fix():
    bad = baseline_model_spec()
    bad["provenance_manifest"]["sneak"] = "EXPERIMENTAL"
    with pytest.raises(GrammarValidationError):
        validate_model_spec(bad)
    cal = baseline_model_spec()
    cal["provenance_manifest"]["sneak"] = "CALIBRATED"
    with pytest.raises(GrammarValidationError):
        validate_model_spec(cal)
    tgt = baseline_model_spec()
    tgt["notes"] = "1/" + "13" + "7"
    with pytest.raises(GrammarValidationError):
        validate_model_spec(tgt)
    silent = baseline_model_spec()
    silent["silently_fixed_parameters"] = ["lambda_a"]
    with pytest.raises(GrammarValidationError):
        validate_model_spec(silent)
    locked = lock_for_solve(baseline_model_spec())
    with pytest.raises(AssumptionLockError):
        add_assumption(
            locked,
            {
                "assumption_id": "late",
                "mathematical_statement": "after solve",
                "reason_for_presence": "invalid",
                "introduced_before_solve": True,
                "provenance": "ASSUMED",
                "affected_components": ["test"],
            },
        )
    with pytest.raises(RuntimeError, match="refuses large-scale generation"):
        refuse_large_scale_generation()
    validated = validate_model_spec(baseline_model_spec())
    assert validated["status"] == "VALIDATED"
    assert validated["counts"]["experimental_dependency_count"] == 0
    man = search_manifest(seed=3)
    assert man["seed"] == 3
    assert man["whitelist_version"]
    assert man["blacklist_version"]
    assert man["search_space_version"]
    assert man["generation_bounds"]["large_scale_generation"] is False


def test_known_physics_isolated_from_generator_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab" / "physics"
    gen = (root / "phase10a_model_grammar.py").read_text(encoding="utf-8")
    assert "phase10a_known_physics" not in gen
    assert "KNOWN_PHYSICS_CATALOG" not in gen
    assert "klein_gordon" not in gen
    assert "yang_mills" not in gen


def test_yaml_and_validator():
    model = load_model(Path(__file__).resolve().parents[1] / "examples" / "phase10a.yaml")
    report = validate(model)
    by_name = {c.name: c for c in report.checks}
    for name in (
        "Phase 10A: pre-analysis gate",
        "Phase 10A: grammar infrastructure",
        "Phase 10A: gravity unchanged",
        "Phase 10A: no numerical target search",
        "Phase 10A: banned tokens",
        "Phase 10A: experimental firewall",
        "Action freeze: verified",
    ):
        assert by_name[name].status is CheckStatus.PASS, (name, by_name[name].message)
    assert by_name["Massless state"].status is CheckStatus.UNTESTED
    text = report.text
    assert "OBJECTIVE" in text
    assert "SCOPE SUMMARY" in text
    assert "MODEL_GRAMMAR_STATUS = READY" in text
    assert "MANDATORY_RULES_STATUS = VERIFIED" in text
    assert "REFERENCE_SEPARATION_STATUS = VERIFIED" in text
    assert "EXAMPLE_SEPARATION_STATUS = VERIFIED" in text
    assert "A. MANDATORY RULE SET" in text
    assert "B. REFERENCE CATALOG" in text
    assert "C. EXAMPLE CATALOG" in text
    assert "EXAMPLE_ONLY" in text
    assert "REFERENCE_ONLY" in text
    assert "PHASE 10A CLOSED" in text
    assert EXPECTED_FROZEN_HASH in text
    assert "large_scale_generation_executed = False" in text


def test_no_banned_tokens_in_source():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "phase10a_model_grammar.py",
        root / "models" / "examples" / "phase10a_model.py",
        root / "reporting" / "phase10a_report.py",
    ]
    banned = (
        "1/" + "13" + "7",
        "alp" + "ha_em",
        "electr" + "ic",
        "1/" + "3",
        "2/" + "3",
        "from physics_lab.physics." + "constants",
        "from physics_lab.physics." + "gauge_internal",
    )
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{token} in {path}"
