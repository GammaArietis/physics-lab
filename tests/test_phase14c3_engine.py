"""Phase 14C.3 engine tests: P3 reuse, checkpoint, G4 partiality, no P4."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure, generate_candidates
from physics_lab.physics.phase14c0_known_physics import g6_checkpoint_path, g6_survivor_hashes, verify_g6_parent_checkpoint
from physics_lab.physics.phase14c3_p3 import (
    P3_ID,
    p2_checkpoint_path,
    p3_executable_registry,
    p3_metadata_legal,
    snapshot_prior_artifact_hashes,
)


def test_p3_reuses_g6_space_without_upgrade(tmp_path):
    hashes = g6_survivor_hashes()
    assert len(hashes) == 479
    grammars = p3_executable_registry()
    ok, _ = p3_metadata_legal({"g6_survivor": hashes[0]}, grammars[P3_ID])
    assert ok is True
    bad, why = p3_metadata_legal({"g6_survivor": "00" * 32}, grammars[P3_ID])
    assert bad is False
    assert why == "g6_survivor_unknown"
    engine = ClosureEngine(tmp_path, chain="p3_only")
    stats = engine.evaluate_grammar(P3_ID)
    assert stats["generated_candidates"] == 479
    assert stats["compatible"] == 359
    assert stats["partial"] == 120
    assert stats["rejected"] == 0
    assert stats["g6_survivors_reused"] == 479
    assert stats["completeness_statistics"]["COMPLETE"] == 359
    assert stats["completeness_statistics"]["PARTIAL_G4_DEPENDENCY"] == 120
    generated = list(generate_candidates(grammars[P3_ID]))
    assert [c["assignment"]["g6_survivor"] for c in generated] == list(hashes)
    assert stats["consequences"]["NEW_ELIMINATIONS_FROM_P3"] == []
    table = stats["class_table"]
    assert all(r["Yukawa"] == "UNTESTED" for r in table)
    assert all(r["VECTORLIKE_STATUS"] == "UNTESTED" for r in table)
    assert all(r["finite_species"] == "FINITE" for r in table)
    assert {r["completeness"] for r in table} == {"COMPLETE", "PARTIAL_G4_DEPENDENCY"}
    assert all(r["P3_status"] in {"COMPLETE", "PARTIAL"} for r in table)


def test_p3_checkpoint_resume_and_parallel(tmp_path):
    serial = ClosureEngine(tmp_path / "s", chain="p3_only")
    a = serial.evaluate_grammar(P3_ID, parallel=False)
    serial.verify_checkpoint(P3_ID)
    state = serial.run_until_closure()
    resumed = serial.resume_closure()
    assert resumed["closure_status"] == state["closure_status"]
    parallel = ClosureEngine(tmp_path / "p", chain="p3_only")
    b = parallel.evaluate_grammar(P3_ID, parallel=True)
    assert a["candidate_hashes"] == b["candidate_hashes"]
    assert a["compatible"] == b["compatible"] == 359
    assert a["interaction_statistics"]["NEW_INTERACTION_RESTRICTIONS"] == 0


def test_physics_chain_and_p4_still_blocked(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="physics")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_parent_p2_and_g6_checkpoints_still_intact():
    payload = verify_g6_parent_checkpoint()
    assert payload["grammar_id"] == "G6_STRUCTURAL_GAUGE_CONSISTENCY"
    assert g6_checkpoint_path().is_file()
    assert p2_checkpoint_path().is_file()
    prior = snapshot_prior_artifact_hashes()
    assert "phase14c2" in prior
    assert "phase14c1" in prior or "phase14c0" in prior or "phase14b6" in prior
