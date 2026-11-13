"""Phase 15A compiles the finite grammar and does not generate models."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15a_grammar import (
    ACTION_HASH_14I,
    ARTIFACT_DIR_NAME,
    GRAMMAR_VERSION,
    MAX_DERIVATIVE_ORDER,
    MAX_FIELD_ORDER,
    run_phase_15a,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase15a_compiles_the_finite_grammar() -> None:
    before = _prior()
    result = run_phase_15a(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_15A_STATUS"] == "READY"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["grammar_version"] == GRAMMAR_VERSION
    assert result["grammar_version"] != "grammar_12b_v2"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["ACTION_HASH_14I_INPUT"] == ACTION_HASH_14I
    assert result["number_of_generated_models"] == 0
    assert result["SEARCH_EXECUTED"] is False
    assert result["report"]["MAX_DERIVATIVE_ORDER"] == MAX_DERIVATIVE_ORDER
    assert result["report"]["MAX_FIELD_ORDER"] == MAX_FIELD_ORDER
    assert result["estimated_post_canonicalization_size"] > 0
    assert result["estimated_raw_combinations"] >= result["estimated_post_canonicalization_size"]
    assert all(item["derivative_order"] <= MAX_DERIVATIVE_ORDER for item in result["enabled_operators"])
    assert all(item["field_order"] <= MAX_FIELD_ORDER for item in result["enabled_operators"])
    assert all(item["allowed_coefficient"] == "FREE" for item in result["enabled_operators"])
    assert result["OPERATOR_GRAMMAR_STATUS"] == "PARTIAL"
    assert result["CANONICALIZATION_STATUS"] == "PARTIAL"
    assert result["GENERAL_COVARIANCE_GRAMMAR_STATUS"] == "PARTIAL"
    assert result["GAUGE_INVARIANCE_GRAMMAR_STATUS"] == "VERIFIED"
    assert result["TARGET_BLINDNESS_STATUS"] == "VERIFIED"
    assert result["AUTHORIZATION_STATUS"] == "HUMAN-AUTHORIZED SEARCH-GRAMMAR EXTENSION"
    assert len(result["dry_run_negatives"]) == 30
    assert {item["case"] for item in result["dry_run_negatives"]} == {str(number) for number in range(1, 31)}
