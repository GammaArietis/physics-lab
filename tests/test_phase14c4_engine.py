"""Phase 14C.4 engine tests: isolation, no generation, no P5, hash preservation."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure
from physics_lab.physics.phase14c0_known_physics import g6_candidate_space_hash, g6_checkpoint_path, verify_g6_parent_checkpoint
from physics_lab.physics.phase14c3_p3 import artifact_dir as phase14c3_artifact_dir
from physics_lab.physics.phase14c4_p4 import (
    EXPECTED_CANDIDATE_SPACE_HASH,
    EXPECTED_P3_CHECKPOINT_DIGEST,
    compare_all_candidates,
    content_hash,
    p3_checkpoint_path,
    p4_checkpoint_path,
    snapshot_prior_artifact_hashes,
)


def test_p4_is_not_a_generation_chain(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p4_only")
    assert ei.value.mode == "KNOWN_MODEL_ISOLATION_VIOLATION"


def test_p5_and_physics_chain_still_blocked(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="physics")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path, chain="p5_only")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_deterministic_comparison_and_space_hash():
    a = compare_all_candidates()
    b = compare_all_candidates()
    ha = content_hash([(r["candidate_hash"], r["reference_id"], r["match_status"]) for r in a["records"]])
    hb = content_hash([(r["candidate_hash"], r["reference_id"], r["match_status"]) for r in b["records"]])
    assert ha == hb
    assert a["n_candidates"] == 479
    assert a["n_complete"] == 359
    assert a["n_partial"] == 120
    assert g6_candidate_space_hash() == EXPECTED_CANDIDATE_SPACE_HASH


def test_parent_p3_and_g6_checkpoints_still_intact():
    payload = verify_g6_parent_checkpoint()
    assert payload["grammar_id"] == "G6_STRUCTURAL_GAUGE_CONSISTENCY"
    assert g6_checkpoint_path().is_file()
    assert p3_checkpoint_path().is_file()
    live = __import__("json").loads(p3_checkpoint_path().read_text())
    assert live.get("checkpoint_digest") == EXPECTED_P3_CHECKPOINT_DIGEST
    prior = snapshot_prior_artifact_hashes()
    assert "phase14c3" in prior
    assert (phase14c3_artifact_dir() / "PHASE_14C3_SUMMARY.json").is_file()
    if p4_checkpoint_path().is_file():
        p4 = __import__("json").loads(p4_checkpoint_path().read_text())
        assert p4["P3_candidate_space_hash"] == EXPECTED_CANDIDATE_SPACE_HASH
        assert p4["P5_EXECUTED"] is False
        assert p4["P4_EXECUTED"] is True
