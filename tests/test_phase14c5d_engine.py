"""Phase 14C.5D engine tests: isolation, no generation, parent immutability."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure
from physics_lab.physics.phase14c0_known_physics import g6_candidate_space_hash
from physics_lab.physics.phase14c5_p5 import p5_checkpoint_path
from physics_lab.physics.phase14c5q_p5q import EXPECTED_P5Q_CHECKPOINT_DIGEST, p5q_checkpoint_path
from physics_lab.physics.phase14c5d_p5d import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_P5_CHECKPOINT_DIGEST,
    content_hash,
    evaluate_all_candidates,
    p5d_checkpoint_path,
)


def test_p5d_is_not_a_generation_chain(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p5d_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_prior_chains_still_blocked(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="physics")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path, chain="p6_only")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ek:
        ClosureEngine(tmp_path, chain="p5q_only")
    assert ek.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_deterministic_evaluation_and_space_hash():
    a = evaluate_all_candidates()
    b = evaluate_all_candidates()
    ha = content_hash([(r["candidate_hash"], r["P5D_status"], {t: r["tests"][t]["status"] for t in r["tests"]}) for r in a["records"]])
    hb = content_hash([(r["candidate_hash"], r["P5D_status"], {t: r["tests"][t]["status"] for t in r["tests"]}) for r in b["records"]])
    assert ha == hb
    assert a["n_candidates"] == 479
    assert all(r["failed_tests"] == [] for r in a["records"])
    assert g6_candidate_space_hash() == EXPECTED_CANDIDATE_SPACE_HASH


def test_parent_p5_and_p5q_still_intact():
    p5 = __import__("json").loads(p5_checkpoint_path().read_text())
    p5q = __import__("json").loads(p5q_checkpoint_path().read_text())
    assert p5.get("checkpoint_digest") == EXPECTED_P5_CHECKPOINT_DIGEST
    assert p5q.get("checkpoint_digest") == EXPECTED_P5Q_CHECKPOINT_DIGEST
    if p5d_checkpoint_path().is_file():
        p5d = __import__("json").loads(p5d_checkpoint_path().read_text())
        assert p5d["P6_EXECUTED"] is False
        assert p5d["P5D_EXECUTED"] is True
        assert p5d["F2_in_frozen_theory"] is False
        assert p5d["g_introduced"] is False
