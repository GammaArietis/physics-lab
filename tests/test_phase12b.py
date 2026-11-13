"""Phase 12B blind exploration tests."""

from __future__ import annotations

from pathlib import Path

from physics_lab.theory_kernel.phase12b import (
    REFERENCE_SEEDS,
    build_search_manifest,
    explore,
    gate_authorizes,
    reject_post_hoc_assumption,
    run_phase_12b,
    search_bounds,
    snapshot_prior_phases,
)
from physics_lab.theory_kernel.phase12a import run_phase_12a

KERNEL = Path(__file__).resolve().parents[1] / "src" / "physics_lab" / "theory_kernel" / "phase12b.py"
BANNED = ("1/137", "alpha_em", "interestingness", "fitness")


def test_phase12a_gate_is_required() -> None:
    assert gate_authorizes({"PHASE_12A_STATUS": "FAILED"}) is False
    phase12a = run_phase_12a(write_artifacts=False)
    assert gate_authorizes(phase12a) is True


def test_reference_seeds_are_not_generator_inputs_and_search_is_reproducible() -> None:
    first = explore(build_search_manifest(seed=0))
    second = explore(build_search_manifest(seed=0))
    left = [(item["theory_id"], item["content_hash"], item["status"]) for item in first["catalogue"]]
    right = [(item["theory_id"], item["content_hash"], item["status"]) for item in second["catalogue"]]
    assert left == right
    assert first["stop"] == "GRAMMAR_EXHAUSTED"
    assert len(first["catalogue"]) <= search_bounds()["max_generated_objects"]
    ids = {item["theory_id"] for item in first["catalogue"]}
    assert REFERENCE_SEEDS[0] not in ids
    assert any(item["termination_context"] == "REPEATED_THEORY" for item in first["catalogue"])
    assert any(item["termination_context"] == "PROOF_ENGINE_UNAVAILABLE" for item in first["catalogue"])
    assert all(item["verified_pfr"] is False for item in first["catalogue"])
    assert all(item["vacuum_audit"]["VACUUM_SELECTION"] == "NOT_FOUND" for item in first["catalogue"])


def test_post_hoc_assumption_is_rejected_and_bounds_stop_the_job() -> None:
    rejected = reject_post_hoc_assumption(
        {"model_id": "explore.baseline", "solve_begun": True},
        {"introduced_before_solve": True},
    )
    assert rejected["status"] == "POST_HOC_ASSUMPTION_DETECTED"
    manifest = build_search_manifest(seed=0)
    manifest["generation_bounds"] = {**search_bounds(), "max_generated_objects": 1}
    stopped = explore(manifest)
    assert stopped["stop"] == "RESOURCE_BOUND_REACHED"
    assert len(stopped["catalogue"]) == 1


def test_phase12b_closes_without_changing_previous_phases() -> None:
    source = KERNEL.read_text(encoding="utf-8")
    for token in BANNED:
        assert token not in source
    before = snapshot_prior_phases()
    result = run_phase_12b(write_artifacts=True, seed=0)
    after = snapshot_prior_phases()
    assert before == after
    assert result["status"] == "OK"
    assert result["SEARCH_AUTHORIZATION_STATUS"] == "AUTHORIZED"
    assert result["SEARCH_MANIFEST_STATUS"] == "VERIFIED"
    assert result["BLINDNESS_STATUS"] == "VERIFIED"
    assert result["GENERATION_STATUS"] == "COMPLETE"
    assert result["VALIDATION_STATUS"] == "VERIFIED"
    assert result["DEDUPLICATION_STATUS"] == "VERIFIED"
    assert result["DERIVATION_STATUS"] == "PARTIAL"
    assert result["PARAMETER_AUDIT_STATUS"] == "VERIFIED"
    assert result["PFR_AUDIT_STATUS"] == "NONE_FOUND"
    assert result["FRONTIER_STATUS"] == "REQUIRES_HUMAN_INPUT"
    assert result["RESOURCE_STATUS"] == "VERIFIED"
    assert result["TERMINATION_STATUS"] == "VERIFIED"
    assert result["PHASE_12B_STATUS"] == "COMPLETE"
    assert result["summary"]["TOTAL_VERIFIED_PFR"] == 0
    assert result["summary"]["TOTAL_HUMAN_INPUT_FRONTIERS"] == 2
    assert result["summary"]["TOTAL_GRAMMAR_BOUNDARIES"] == 1
    assert result["summary"]["TOTAL_GENERATED"] <= 8
    assert result["ranking_used"] is False
    assert result["experimental_data_used"] is False
    assert result["large_scale_scan"] is False
    assert result["recurrence"]["fundamental_law_inferred"] is False
    assert result["search_manifest"]["blind_mode"] is True
    roles = {row["role"] for row in result["STRUCTURAL_CATALOGUE"]["reference_seeds"]}
    assert roles == {"REFERENCE_ONLY"}
    assert "quality" not in result
