"""Phase 14C.5J engine tests."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure
from physics_lab.physics.phase14c0_known_physics import g6_candidate_space_hash
from physics_lab.physics.phase14c5i_p5i import EXPECTED_P5I_CHECKPOINT_DIGEST, p5i_checkpoint_path
from physics_lab.physics.phase14c5j_p5j import EXPECTED_CANDIDATE_SPACE_HASH, content_hash, evaluate_all_candidates, p5j_checkpoint_path


def test_p5j_is_not_a_generation_chain(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p5j_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_prior_chains_still_blocked(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        ClosureEngine(tmp_path, chain="p6_only")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path, chain="p5i_only")
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
    p5i = __import__("json").loads(p5i_checkpoint_path().read_text())
    assert p5i.get("checkpoint_digest") == EXPECTED_P5I_CHECKPOINT_DIGEST
    if p5j_checkpoint_path().is_file():
        p5j = __import__("json").loads(p5j_checkpoint_path().read_text())
        assert p5j["P6_EXECUTED"] is False
        assert p5j["parent_p5i_digest"] == EXPECTED_P5I_CHECKPOINT_DIGEST
        assert p5j.get("P5I_overwritten") is False
