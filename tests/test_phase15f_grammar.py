"""Phase 15F registers constraint profiles and does not start a search."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15f_grammar import ARTIFACT_DIR_NAME, run_phase_15f
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase15f_registers_constraint_hierarchy() -> None:
    before = _prior()
    result = run_phase_15f(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_15F_STATUS"] == "COMPLETE"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["old_grammar_version"] == "grammar_15a_v1"
    assert result["old_grammar_hash"] == "9e2c6b08d9d0ef96a78f52fb097d169bc112aac29b70556aa7be7bf0d4206075"
    assert result["new_grammar_version"] == "grammar_15f_v1"
    assert result["grammar_hash"] != result["old_grammar_hash"]
    assert result["grammar_hash"] == result["grammar_hash_repeated"]
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["AMBIENT_OPERATOR_COUNT"] == 117
    assert result["U1_PRESERVING_COUNT"] == 63
    assert result["COVARIANT_U1_COUNT"] == 37
    assert result["DD_TOTAL"] == 80
    assert result["DD_U1_PRESERVING"] == 26
    assert result["DD_U1_BREAKING"] == 54
    assert result["FLAT_ALGEBRAIC_RANK"] == 109
    assert result["COVARIANT_ALGEBRAIC_RANK"] == 35
    assert result["subset_relation_status"] == "VERIFIED"
    assert result["operators_removed"] == 0
    assert result["selection_performed"] is False
    assert result["active_profile"] == "UNAUTHORIZED"
    assert result["search_executed"] is False
    assert result["AVAILABLE_SEARCH_PROFILES"] == ["AMBIENT_117", "LOCAL_U1_63", "COVARIANT_U1_37"]
    assert result["NEXT_ACTION"] == "HUMAN_SEARCH_PROFILE_AUTHORIZATION"
    assert [item["operator_count"] for item in result["profiles"]] == [117, 63, 37]
    assert {item["status"] for item in result["profiles"]} == {"REGISTERED_NOT_ACTIVATED"}
    assert len(result["dry_run_negatives"]) == 24
    assert {item["case"] for item in result["dry_run_negatives"]} == {str(number) for number in range(1, 25)}
