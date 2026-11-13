"""Phase 14C.5H.2 engine tests."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure
from physics_lab.physics.phase14c0_known_physics import g6_candidate_space_hash
from physics_lab.physics.phase14c5h1_p5h1 import EXPECTED_P5H1_CHECKPOINT_DIGEST, p5h1_checkpoint_path
from physics_lab.physics.phase14c5h2_p5h2 import EXPECTED_CANDIDATE_SPACE_HASH, content_hash, evaluate_all_candidates, p5h2_checkpoint_path


def test_p5h2_is_not_a_generation_chain(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p5h2_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_prior_chains_still_blocked(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p6_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path, chain="p5h1_only")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_deterministic_evaluation():
    a = evaluate_all_candidates()
    b = evaluate_all_candidates()
    ha = content_hash([(r["candidate_hash"], r["Q04"], r["optical_theorem_status"], r["cut_diagrams"]) for r in a["records"]])
    hb = content_hash([(r["candidate_hash"], r["Q04"], r["optical_theorem_status"], r["cut_diagrams"]) for r in b["records"]])
    assert ha == hb
    assert a["n_candidates"] == 479
    assert g6_candidate_space_hash() == EXPECTED_CANDIDATE_SPACE_HASH


def test_parents_intact():
    p5h1 = __import__("json").loads(p5h1_checkpoint_path().read_text())
    assert p5h1.get("checkpoint_digest") == EXPECTED_P5H1_CHECKPOINT_DIGEST
    assert p5h1["P6_EXECUTED"] is False
    if p5h2_checkpoint_path().is_file():
        p5h2 = __import__("json").loads(p5h2_checkpoint_path().read_text())
        assert p5h2["P6_EXECUTED"] is False
        assert p5h2["parent_p5h1_digest"] == EXPECTED_P5H1_CHECKPOINT_DIGEST
        assert p5h2.get("P5H1_overwritten") is False
