"""Phase 14C.5E engine tests."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure
from physics_lab.physics.phase14c0_known_physics import g6_candidate_space_hash
from physics_lab.physics.phase14c5d_p5d import EXPECTED_P5D_CHECKPOINT_DIGEST, p5d_checkpoint_path
from physics_lab.physics.phase14c5q_p5q import EXPECTED_P5Q_CHECKPOINT_DIGEST, p5q_checkpoint_path
from physics_lab.physics.phase14c5e_p5e import EXPECTED_CANDIDATE_SPACE_HASH, content_hash, evaluate_all_candidates, one_loop_engine, p5e_checkpoint_path
from physics_lab.physics.phase4c_action_freeze import authorize_phase5b0_analysis


def test_p5e_is_not_a_generation_chain(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p5e_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_prior_chains_still_blocked(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p6_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path, chain="p5d_only")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_deterministic_evaluation():
    auth = authorize_phase5b0_analysis()
    loop = one_loop_engine(auth)
    a = evaluate_all_candidates(loop)
    b = evaluate_all_candidates(loop)
    ha = content_hash([(r["candidate_hash"], {t: r["tests"][t]["status"] for t in r["tests"]}) for r in a["records"]])
    hb = content_hash([(r["candidate_hash"], {t: r["tests"][t]["status"] for t in r["tests"]}) for r in b["records"]])
    assert ha == hb
    assert a["n_candidates"] == 479
    assert g6_candidate_space_hash() == EXPECTED_CANDIDATE_SPACE_HASH


def test_parents_intact():
    p5q = __import__("json").loads(p5q_checkpoint_path().read_text())
    p5d = __import__("json").loads(p5d_checkpoint_path().read_text())
    assert p5q.get("checkpoint_digest") == EXPECTED_P5Q_CHECKPOINT_DIGEST
    assert p5d.get("checkpoint_digest") == EXPECTED_P5D_CHECKPOINT_DIGEST
    if p5e_checkpoint_path().is_file():
        p5e = __import__("json").loads(p5e_checkpoint_path().read_text())
        assert p5e["P6_EXECUTED"] is False
        assert p5e["F2_in_frozen_theory"] is False
