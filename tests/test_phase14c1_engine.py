"""Phase 14C.1 engine tests: P1 reuse, checkpoint, G4 partiality, no P2."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure, generate_candidates
from physics_lab.physics.phase14c0_known_physics import g6_checkpoint_path, g6_survivor_hashes, verify_g6_parent_checkpoint
from physics_lab.physics.phase14c1_p1 import (
    P1_ID,
    p1_executable_registry,
    p1_metadata_legal,
    snapshot_prior_artifact_hashes,
)


def test_p1_reuses_g6_space_without_upgrade(tmp_path):
    hashes = g6_survivor_hashes()
    assert len(hashes) == 479
    grammars = p1_executable_registry()
    ok, _ = p1_metadata_legal({"g6_survivor": hashes[0]}, grammars[P1_ID])
    assert ok is True
    bad, why = p1_metadata_legal({"g6_survivor": "00" * 32}, grammars[P1_ID])
    assert bad is False
    assert why == "g6_survivor_unknown"
    engine = ClosureEngine(tmp_path, chain="p1_only")
    stats = engine.evaluate_grammar(P1_ID)
    assert stats["generated_candidates"] == 479
    assert stats["compatible"] == 359
    assert stats["partial"] == 120
    assert stats["rejected"] == 0
    assert stats["g6_survivors_reused"] == 479
    assert stats["completeness_statistics"]["COMPLETE"] == 359
    assert stats["completeness_statistics"]["PARTIAL_G4_DEPENDENCY"] == 120
    generated = list(generate_candidates(grammars[P1_ID]))
    assert [c["assignment"]["g6_survivor"] for c in generated] == list(hashes)
    assert stats["consequences"]["NEW_ELIMINATIONS_FROM_P1"] == []
    assert stats["consequences"]["NEW_FORCED_PROPERTIES_FROM_P1"]
    table = stats["class_table"]
    assert all(r["unitarity"] == "UNTESTED" for r in table)
    assert all(r["quantum_gravity"] == "UNTESTED" for r in table)
    assert all(r["EFT"] == "EFT_COMPATIBLE" for r in table)
    assert {r["completeness"] for r in table} == {"COMPLETE", "PARTIAL_G4_DEPENDENCY"}


def test_p1_checkpoint_resume_and_parallel(tmp_path):
    serial = ClosureEngine(tmp_path / "s", chain="p1_only")
    a = serial.evaluate_grammar(P1_ID, parallel=False)
    serial.verify_checkpoint(P1_ID)
    state = serial.run_until_closure()
    resumed = serial.resume_closure()
    assert resumed["closure_status"] == state["closure_status"]
    parallel = ClosureEngine(tmp_path / "p", chain="p1_only")
    b = parallel.evaluate_grammar(P1_ID, parallel=True)
    assert a["candidate_hashes"] == b["candidate_hashes"]
    assert a["compatible"] == b["compatible"] == 359


def test_physics_chain_and_p2_still_blocked(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="physics")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_parent_g6_checkpoint_still_intact():
    payload = verify_g6_parent_checkpoint()
    assert payload["grammar_id"] == "G6_STRUCTURAL_GAUGE_CONSISTENCY"
    assert g6_checkpoint_path().is_file()
    prior = snapshot_prior_artifact_hashes()
    assert "phase14c0" in prior or "phase14b6" in prior
