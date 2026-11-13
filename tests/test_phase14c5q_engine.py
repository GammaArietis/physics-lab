"""Phase 14C.5Q engine tests: isolation, no generation, no P6, hash preservation."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure
from physics_lab.physics.phase14c0_known_physics import g6_candidate_space_hash, g6_checkpoint_path, verify_g6_parent_checkpoint
from physics_lab.physics.phase14c5_p5 import p5_checkpoint_path
from physics_lab.physics.phase14c5q_p5q import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_P5_CHECKPOINT_DIGEST,
    content_hash,
    evaluate_all_candidates,
    p5q_checkpoint_path,
    snapshot_prior_artifact_hashes,
)


def test_p5q_is_not_a_generation_chain(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p5q_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_p5_p6_p4_and_physics_chain_still_blocked(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="physics")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path, chain="p6_only")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ek:
        ClosureEngine(tmp_path, chain="p5_only")
    assert ek.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as el:
        ClosureEngine(tmp_path, chain="p4_only")
    assert el.value.mode == "KNOWN_MODEL_ISOLATION_VIOLATION"


def test_deterministic_evaluation_and_space_hash():
    a = evaluate_all_candidates()
    b = evaluate_all_candidates()
    ha = content_hash([(r["candidate_hash"], r["P5Q_status"], {t: r["tests"][t]["status"] for t in r["tests"]}) for r in a["records"]])
    hb = content_hash([(r["candidate_hash"], r["P5Q_status"], {t: r["tests"][t]["status"] for t in r["tests"]}) for r in b["records"]])
    assert ha == hb
    assert a["n_candidates"] == 479
    assert all(r["failed_tests"] == [] for r in a["records"])
    assert g6_candidate_space_hash() == EXPECTED_CANDIDATE_SPACE_HASH


def test_parent_p5_and_g6_checkpoints_still_intact():
    payload = verify_g6_parent_checkpoint()
    assert payload["grammar_id"] == "G6_STRUCTURAL_GAUGE_CONSISTENCY"
    assert g6_checkpoint_path().is_file()
    assert p5_checkpoint_path().is_file()
    live = __import__("json").loads(p5_checkpoint_path().read_text())
    assert live.get("checkpoint_digest") == EXPECTED_P5_CHECKPOINT_DIGEST
    prior = snapshot_prior_artifact_hashes()
    assert "phase14c5" in prior
    if p5q_checkpoint_path().is_file():
        p5q = __import__("json").loads(p5q_checkpoint_path().read_text())
        assert p5q["candidate_space_hash"] == EXPECTED_CANDIDATE_SPACE_HASH
        assert p5q["P6_EXECUTED"] is False
        assert p5q["P5Q_EXECUTED"] is True
        assert p5q["parent_checkpoint_digest"] == EXPECTED_P5_CHECKPOINT_DIGEST
        assert p5q["F2_introduced"] is False
