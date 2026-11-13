"""Phase 14C.5G.1 engine tests."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure
from physics_lab.physics.phase14c0_known_physics import g6_candidate_space_hash
from physics_lab.physics.phase14c5g_p5g import EXPECTED_P5G_CHECKPOINT_DIGEST, p5g_checkpoint_path
from physics_lab.physics.phase14c5g1_p5g1 import EXPECTED_CANDIDATE_SPACE_HASH, content_hash, evaluate_all_independent, p5g1_checkpoint_path


def test_p5g1_is_not_a_generation_chain(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p5g1_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_prior_chains_still_blocked(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p6_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path, chain="p5g_only")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_deterministic_evaluation():
    a = evaluate_all_independent()
    b = evaluate_all_independent()
    ha = content_hash([(r["candidate_hash"], r["Q09"], r["beta_coefficient"]) for r in a["records"]])
    hb = content_hash([(r["candidate_hash"], r["Q09"], r["beta_coefficient"]) for r in b["records"]])
    assert ha == hb
    assert a["n_candidates"] == 479
    assert g6_candidate_space_hash() == EXPECTED_CANDIDATE_SPACE_HASH


def test_parents_intact():
    p5g = __import__("json").loads(p5g_checkpoint_path().read_text())
    assert p5g.get("checkpoint_digest") == EXPECTED_P5G_CHECKPOINT_DIGEST
    if p5g1_checkpoint_path().is_file():
        p5g1 = __import__("json").loads(p5g1_checkpoint_path().read_text())
        assert p5g1["P6_EXECUTED"] is False
        assert p5g1["parent_p5g_digest"] == EXPECTED_P5G_CHECKPOINT_DIGEST
        assert p5g1.get("P5G_overwritten") is False
