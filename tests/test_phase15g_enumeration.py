"""Phase 15G enumerates one authorized symbolic family and then stops."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15g_enumeration import ARTIFACT_DIR_NAME, run_phase_15g
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase15g_enumerates_covariant_u1_family() -> None:
    before = _prior()
    result = run_phase_15g(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_15G_STATUS"] == "COMPLETE"
    assert result["AUTHORIZATION_STATUS"] == "VERIFIED"
    assert result["authorization_record_status"] == "HUMAN-AUTHORIZED BLIND SEARCH"
    assert result["SEARCH_PROFILE"] == "COVARIANT_U1_37"
    assert result["grammar_version"] == "grammar_15f_v1"
    assert result["grammar_hash"] == "f0bdee6da1733a6c2cc83f5a6f6d62d21aeacdf7f0010108fc47b1f4733ca393"
    assert result["parent_grammar_hash"] == "9e2c6b08d9d0ef96a78f52fb097d169bc112aac29b70556aa7be7bf0d4206075"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["AMBIENT_OPERATOR_COUNT"] == 117
    assert result["U1_PRESERVING_COUNT"] == 63
    assert result["COVARIANT_U1_COUNT"] == 37
    assert result["COVARIANT_ALGEBRAIC_RANK"] == 35
    assert result["GENERATED_SYMBOLIC_FAMILIES"] == 1
    assert result["SUPPORT_SUBSET_ENUMERATION"] == "NOT_PERFORMED"
    assert result["PFR_STATUS"] == "NONE_FOUND"
    assert result["PHYSICALLY_INEQUIVALENT_COUNT"] == "NOT_ESTABLISHED"
    assert result["EOM_STATUS"] == "PARTIAL"
    assert result["CONSERVATION_STATUS"] == "UNTESTED"
    assert result["operators_removed"] == 0
    assert result["frozen_action_modified"] is False
    assert result["inactive_profiles"] == ["AMBIENT_117", "LOCAL_U1_63"]
    assert len(result["dry_run_negatives"]) == 23
    assert {item["case"] for item in result["dry_run_negatives"]} == {str(number) for number in range(1, 24)}
