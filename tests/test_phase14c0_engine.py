"""Phase 14C.0 engine tests: dry profiles, P0 reuse, checkpoint, resume, parallelism."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure, generate_candidates
from physics_lab.physics.phase14c0_known_physics import (
    P0_ID,
    dry_profile_metadata_legal,
    dry_profile_registry,
    g6_survivor_hashes,
    p0_executable_registry,
    p0_metadata_legal,
    run_synthetic_dry_run,
    verify_g6_parent_checkpoint,
)


def test_g6_parent_checkpoint_integrity():
    payload = verify_g6_parent_checkpoint()
    assert payload["grammar_id"] == "G6_STRUCTURAL_GAUGE_CONSISTENCY"
    assert len(payload["class_table"]) == 479


def test_dry_profile_prune_and_property_counterexample(tmp_path):
    grammars = dry_profile_registry()
    legal, why = dry_profile_metadata_legal({"color": "red", "marker": "off"}, grammars["14C_DRY_P0"])
    assert legal is False
    assert why == "DRY_C_MARKER_ON"
    legal_p1, why_p1 = dry_profile_metadata_legal({"color": "red", "marker": "on"}, grammars["14C_DRY_P1"])
    assert legal_p1 is False
    assert why_p1 == "DRY_C_NOT_RED"
    engine = ClosureEngine(tmp_path, chain="14c0_dry")
    p0 = engine.evaluate_grammar("14C_DRY_P0")
    assert p0["raw_theoretical_combinations"] == 6
    assert p0["metadata_pruned_candidates"] == 3
    assert p0["compatible"] == 3
    colors = {row["color"] for row in p0["class_table"] if row["status"] == "PASS"}
    assert colors == {"red", "blue", "green"}
    cons = p0["consequences"]
    assert any(item["property"] == "marker_on" for item in cons["FORCED_PROPERTIES"])
    assert cons["destroyed_by_counterexample"]
    p1 = engine.evaluate_grammar("14C_DRY_P1")
    assert p1["compatible"] == 2
    p1_colors = {row["color"] for row in p1["class_table"] if row["status"] == "PASS"}
    assert p1_colors == {"blue", "green"}


def test_dry_checkpoint_resume_and_parallel(tmp_path):
    dry = run_synthetic_dry_run(tmp_path)
    assert dry["status"] == "OK"
    assert dry["resume_matches"] is True
    assert dry["deterministic_parallel"] is True
    assert dry["physical_conclusions_authorized"] is False
    assert dry["P0_compatible"] == 3
    assert dry["P1_compatible"] == 2
    assert "color" in dry["cross_profile_difference"]["newly_forced_properties"] or dry["P1_consequences"]["FORCED_PROPERTIES"]
    engine = ClosureEngine(tmp_path / "dry_run", chain="14c0_dry")
    engine.verify_checkpoint("14C_DRY_P0")
    engine.verify_checkpoint("14C_DRY_P1")
    resumed = engine.resume_closure()
    assert resumed["closure_status"] == "CLOSURE_REACHED"


def test_p0_reuses_g6_space_without_upgrade(tmp_path):
    hashes = g6_survivor_hashes()
    assert len(hashes) == 479
    grammars = p0_executable_registry()
    ok, _ = p0_metadata_legal({"g6_survivor": hashes[0]}, grammars[P0_ID])
    assert ok is True
    bad, why = p0_metadata_legal({"g6_survivor": "00" * 32}, grammars[P0_ID])
    assert bad is False
    assert why == "g6_survivor_unknown"
    engine = ClosureEngine(tmp_path, chain="p0_only")
    stats = engine.evaluate_grammar(P0_ID)
    assert stats["generated_candidates"] == 479
    assert stats["compatible"] == 359
    assert stats["partial"] == 120
    assert stats["rejected"] == 0
    assert stats["g6_survivors_reused"] == 479
    completeness = stats["completeness_statistics"]
    assert completeness["COMPLETE"] == 359
    assert completeness["PARTIAL_G4_DEPENDENCY"] == 120
    generated = list(generate_candidates(grammars[P0_ID]))
    assert [c["assignment"]["g6_survivor"] for c in generated] == list(hashes)


def test_physics_chain_and_unknown_profile_still_blocked(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="physics")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
