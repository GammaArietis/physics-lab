"""Phase 14C.5E.1 engine tests."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure
from physics_lab.physics.phase14c0_known_physics import g6_candidate_space_hash
from physics_lab.physics.phase14c5e_p5e import EXPECTED_P5E_CHECKPOINT_DIGEST, p5e_checkpoint_path
from physics_lab.physics.phase14c5e1_p5e1 import EXPECTED_CANDIDATE_SPACE_HASH, content_hash, evaluate_all_candidates, loop_scope_manifest, p5e1_checkpoint_path


def test_p5e1_is_not_a_generation_chain(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p5e1_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_prior_chains_still_blocked(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p6_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path, chain="p5e_only")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_deterministic_evaluation():
    a = evaluate_all_candidates()
    b = evaluate_all_candidates()
    ha = content_hash([(r["candidate_hash"], r["scope_status"], r["Q07"], r["Q08"], r["Q09"]) for r in a["records"]])
    hb = content_hash([(r["candidate_hash"], r["scope_status"], r["Q07"], r["Q08"], r["Q09"]) for r in b["records"]])
    assert ha == hb
    assert a["n_candidates"] == 479
    assert loop_scope_manifest()["manifest_hash"] == loop_scope_manifest()["manifest_hash"]
    assert g6_candidate_space_hash() == EXPECTED_CANDIDATE_SPACE_HASH


def test_parents_intact():
    p5e = __import__("json").loads(p5e_checkpoint_path().read_text())
    assert p5e.get("checkpoint_digest") == EXPECTED_P5E_CHECKPOINT_DIGEST
    if p5e1_checkpoint_path().is_file():
        p5e1 = __import__("json").loads(p5e1_checkpoint_path().read_text())
        assert p5e1["P6_EXECUTED"] is False
        assert p5e1["parent_p5e_digest"] == EXPECTED_P5E_CHECKPOINT_DIGEST
