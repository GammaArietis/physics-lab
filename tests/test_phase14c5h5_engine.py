"""Phase 14C.5H.5 engine tests."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure
from physics_lab.physics.phase14c0_known_physics import g6_candidate_space_hash
from physics_lab.physics.phase14c5h4_p5h4 import EXPECTED_P5H4_CHECKPOINT_DIGEST, p5h4_checkpoint_path
from physics_lab.physics.phase14c5h5_p5h5 import EXPECTED_CANDIDATE_SPACE_HASH, content_hash, evaluate_all_candidates, p5h5_checkpoint_path


def test_p5h5_is_not_a_generation_chain(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p5h5_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_prior_chains_still_blocked(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p6_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path, chain="p5h4_only")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_deterministic_evaluation():
    a = evaluate_all_candidates()
    b = evaluate_all_candidates()
    ha = content_hash([(r["candidate_hash"], r["Q04"], r["CASE"], r["parameter_constraints"]) for r in a["records"]])
    hb = content_hash([(r["candidate_hash"], r["Q04"], r["CASE"], r["parameter_constraints"]) for r in b["records"]])
    assert ha == hb
    assert a["n_candidates"] == 479
    assert g6_candidate_space_hash() == EXPECTED_CANDIDATE_SPACE_HASH


def test_parents_intact():
    p5h4 = __import__("json").loads(p5h4_checkpoint_path().read_text())
    assert p5h4.get("checkpoint_digest") == EXPECTED_P5H4_CHECKPOINT_DIGEST
    if p5h5_checkpoint_path().is_file():
        p5h5 = __import__("json").loads(p5h5_checkpoint_path().read_text())
        assert p5h5["P6_EXECUTED"] is False
        assert p5h5["parent_p5h4_digest"] == EXPECTED_P5H4_CHECKPOINT_DIGEST
        assert p5h5.get("P5H4_overwritten") is False
