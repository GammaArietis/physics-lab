"""Phase 14C.5F engine tests."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure
from physics_lab.physics.phase14c0_known_physics import g6_candidate_space_hash
from physics_lab.physics.phase14c5e1_p5e1 import EXPECTED_P5E1_CHECKPOINT_DIGEST, p5e1_checkpoint_path
from physics_lab.physics.phase14c5f_p5f import EXPECTED_CANDIDATE_SPACE_HASH, content_hash, evaluate_all_candidates, p5f_checkpoint_path


def test_p5f_is_not_a_generation_chain(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p5f_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_prior_chains_still_blocked(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p6_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path, chain="p5e1_only")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_deterministic_evaluation():
    a = evaluate_all_candidates()
    b = evaluate_all_candidates()
    ha = content_hash([(r["candidate_hash"], r["Q05"], r["propagator_status"], r["gauge_factors"]) for r in a["records"]])
    hb = content_hash([(r["candidate_hash"], r["Q05"], r["propagator_status"], r["gauge_factors"]) for r in b["records"]])
    assert ha == hb
    assert a["n_candidates"] == 479
    assert g6_candidate_space_hash() == EXPECTED_CANDIDATE_SPACE_HASH


def test_parents_intact():
    p5e1 = __import__("json").loads(p5e1_checkpoint_path().read_text())
    assert p5e1.get("checkpoint_digest") == EXPECTED_P5E1_CHECKPOINT_DIGEST
    if p5f_checkpoint_path().is_file():
        p5f = __import__("json").loads(p5f_checkpoint_path().read_text())
        assert p5f["P6_EXECUTED"] is False
        assert p5f["parent_p5e1_digest"] == EXPECTED_P5E1_CHECKPOINT_DIGEST
