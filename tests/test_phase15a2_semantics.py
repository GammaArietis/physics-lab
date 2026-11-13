"""Phase 15A.2 audits gauge-rule wording and does not repair the grammar."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15a2_semantics import (
    ARTIFACT_DIR_NAME,
    QUOTED_RULE,
    SCOPED_MARKERS,
    classify_scope,
    run_phase_15a2,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def test_phase15a2_audits_gauge_rule_scope() -> None:
    before = _prior()
    result = run_phase_15a2(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["status"] == "OK"
    assert result["PHASE_15A2_STATUS"] == "BLOCKED"
    assert result["PYTEST_STATUS"] == "GREEN"
    assert result["grammar_version"] == "grammar_15a_v1"
    assert result["grammar_hash"] == "9e2c6b08d9d0ef96a78f52fb097d169bc112aac29b70556aa7be7bf0d4206075"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert result["GAUGE_RULE_SCOPE_STATUS"] == "UNRESOLVED"
    assert result["GRAMMAR_CONSISTENCY_STATUS"] == "UNRESOLVED"
    assert result["GRAMMAR_CONTEXT_SCOPING"] == "UNRESOLVED"
    assert result["DD_CLASSIFICATION_INTEGRITY"] == "VERIFIED"
    assert result["FLAT_COVARIANT_SEMANTICS"] == "VERIFIED"
    assert result["flat_covariant_relation"] == "CONTEXT_SUBSET"
    assert result["GRAMMAR_MUTATION"] == "NONE"
    assert result["quoted_rule_present"] is False
    assert result["gauge_rule"]["statement"] == "existing local U(1) with stored K"
    assert result["local_u1_invariant"] == 26
    assert result["local_u1_breaking"] == 54
    assert result["operators_removed"] == 0
    assert result["operators_added"] == 0
    assert result["selection_performed"] is False
    assert result["grammar_revision"] == "NOT_REQUESTED"
    assert result["new_physical_principle"] == "NONE"
    assert classify_scope([QUOTED_RULE, SCOPED_MARKERS[0]]) == "CONTRADICTORY"
    assert result["contradictory_scope_status"] == "BLOCKED"
    assert len(result["dry_run_negatives"]) == 15
    assert {item["case"] for item in result["dry_run_negatives"]} == {str(number) for number in range(1, 16)}
