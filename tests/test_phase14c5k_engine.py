"""Phase 14C.5K engine tests."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure
from physics_lab.physics.phase14c0_known_physics import g6_candidate_space_hash
from physics_lab.physics.phase14c5j_p5j import EXPECTED_P5J_CHECKPOINT_DIGEST, p5j_checkpoint_path
from physics_lab.physics.phase14c5k_p5k import EXPECTED_CANDIDATE_SPACE_HASH, content_hash, evaluate_all_candidates, p5k_checkpoint_path


def test_p5k_is_not_a_generation_chain(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p5k_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_prior_chains_still_blocked(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p6_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path, chain="p5j_only")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_deterministic_evaluation():
    a = evaluate_all_candidates()
    b = evaluate_all_candidates()
    ha = content_hash([(r["candidate_hash"], r["domain_status"], r["new_parameter_free_relation"]) for r in a["records"]])
    hb = content_hash([(r["candidate_hash"], r["domain_status"], r["new_parameter_free_relation"]) for r in b["records"]])
    assert ha == hb
    assert a["n_candidates"] == 479
    assert g6_candidate_space_hash() == EXPECTED_CANDIDATE_SPACE_HASH


def test_parents_intact():
    p5j = __import__("json").loads(p5j_checkpoint_path().read_text())
    assert p5j.get("checkpoint_digest") == EXPECTED_P5J_CHECKPOINT_DIGEST
    if p5k_checkpoint_path().is_file():
        p5k = __import__("json").loads(p5k_checkpoint_path().read_text())
        assert p5k["P6_EXECUTED"] is False
        assert p5k["parent_p5j_digest"] == EXPECTED_P5J_CHECKPOINT_DIGEST
        assert p5k.get("P5J_overwritten") is False
