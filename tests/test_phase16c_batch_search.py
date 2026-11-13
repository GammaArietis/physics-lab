"""Phase 16C requires an explicit batch authorization before exploration."""

from __future__ import annotations

from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase16b_batch_grammar import run_phase_16b
from physics_lab.theory_kernel.phase16c_batch_search import (
    ARTIFACT_DIR_NAME,
    audit_relation,
    classify_authorization,
    classify_cross_grammar,
    run_phase_16c,
    select_next_grammar,
    validate_skeleton,
)
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH


def _prior() -> dict[str, str]:
    return {key: value for key, value in snapshot_existing_phases().items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _authorization(batch: dict) -> dict:
    return {
        "authorized_grammar_ids": list(batch["imported_ids"]),
        "bound_policy_version": "bound_policy_16b_v1",
        "exclusion_manifest": batch["exclusion_manifest"],
        "grammar_catalog_version": "grammar_16b_batch_catalog_v1",
        "new_physical_input_manifest": batch["new_physical_input_register"],
        "search_tier": "TIER_1",
        "target_blindness_status": "VERIFIED",
    }


def test_phase16c_stops_without_authorization() -> None:
    before = _prior()
    batch = run_phase_16b(write_artifacts=False)
    result = run_phase_16c(write_artifacts=True)
    after = _prior()
    assert before == after
    assert result["PHASE16C_STATUS"] == "NOT_AUTHORIZED"
    assert result["search_started"] is False
    assert result["grammar_hash"] == "f0bdee6da1733a6c2cc83f5a6f6d62d21aeacdf7f0010108fc47b1f4733ca393"
    assert result["FROZEN_ACTION_HASH"] == FROZEN_4C_HASH
    assert classify_authorization(None, batch) == "NOT_AUTHORIZED"
    assert classify_authorization(batch["batch_authorization"], batch) == "NOT_AUTHORIZED"
    prepared = _authorization(batch)
    prepared["search_tier"] = "NOT_SELECTED"
    assert classify_authorization(prepared, batch) == "NOT_AUTHORIZED"
    partial = _authorization(batch)
    partial["authorized_grammar_ids"] = partial["authorized_grammar_ids"][:10]
    assert classify_authorization(partial, batch) == "NOT_AUTHORIZED"


def test_phase16c_explores_only_an_explicit_batch() -> None:
    batch = run_phase_16b(write_artifacts=False)
    authorization = _authorization(batch)
    assert classify_authorization(authorization, batch) == "VERIFIED"
    first = run_phase_16c(authorization=authorization, write_artifacts=False, stop_after=2)
    assert first["PHASE16C_STATUS"] == "INCOMPLETE"
    assert [item["grammar_candidate_id"] for item in first["records"]] == batch["imported_ids"][:2]
    resumed = run_phase_16c(
        authorization=authorization,
        write_artifacts=False,
        resume_from={**first["manifest"], "records": first["records"]},
    )
    repeated = run_phase_16c(authorization=authorization, write_artifacts=False)
    assert resumed["PHASE16C_STATUS"] == "COMPLETE"
    assert repeated["MANIFEST_ID"] == resumed["MANIFEST_ID"] == first["MANIFEST_ID"]
    assert repeated["search_order"] == batch["imported_ids"]
    assert [item["grammar_candidate_id"] for item in repeated["records"]] == batch["imported_ids"]
    assert repeated["manifest"]["generation_bounds"] == first["manifest"]["generation_bounds"]
    assert repeated["manifest"]["seed"] == "NOT_USED"
    assert all(item["verified_PFR_count"] == 0 for item in repeated["records"])
    assert all(item["PARAMETER_CLOSURE"] == "OPEN" for item in repeated["records"])
    assert all(item["selected_grammar"] == "NONE" for item in (repeated,))
    higher = next(item for item in repeated["records"] if item["grammar_candidate_id"] == "g16a.new.higher_derivative_order")
    assert higher["branch"]["rejected_for_higher_derivative"] is False
    assert higher["valid_model_count"] == 1
    assert classify_cross_grammar(
        "g16a.new.internal_dimension",
        "g16a.new.extra_scalar",
        {frozenset({"g16a.new.internal_dimension", "g16a.new.extra_scalar"})},
    ) == "EQUIVALENCE_UNSUPPORTED"
    assert "g16a.unresolved.internal_basis" not in repeated["search_order"]
    assert select_next_grammar() == "NOT_PERFORMED"
    assert audit_relation({"follows_from_structure": True, "provenance": "EXPERIMENTAL", "survives_declared_equivalence": True}) == "REJECTED"
    assert audit_relation({"mathematical_definition": "matched to " + ("1/" + "137")}) == "REJECTED"
    skeleton = next(item for item in batch["batch_grammar_catalog"] if item["grammar_candidate_id"] == "g16a.new.higher_derivative_order")
    assert validate_skeleton(skeleton, ["Phi", "metric", "mathcal A_mu"], 5) == "VALID"
    assert validate_skeleton(skeleton, ["unregistered"], 5) == "INVALID"
    assert repeated["global_summary"]["total_grammars"] == 11
    assert repeated["next_grammar_selection"] == "NOT_PERFORMED"
    assert repeated["PYTEST_STATUS"] == "GREEN"
