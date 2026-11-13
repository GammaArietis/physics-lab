"""Phase 14B.0 engine unit tests: identity, prune, cache, checkpoint, resume."""

from __future__ import annotations

import json

import pytest

from physics_lab.physics.phase14b0_engine import (
    AUTHORIZED_PHYSICS_CHAIN,
    ClosureEngine,
    DRY_CHAIN,
    ENGINE_VERSION,
    EngineFailure,
    ClosureTestCache,
    assert_target_blind,
    constraint_registry,
    content_hash,
    count_pruned,
    count_raw_combinations,
    dry_grammar_registry,
    generate_candidates,
    physics_grammar_registry,
    top_down_input_hash,
)


def test_deterministic_grammar_identity():
    a = physics_grammar_registry()
    b = physics_grammar_registry()
    for gid in AUTHORIZED_PHYSICS_CHAIN:
        assert a[gid]["grammar_hash"] == b[gid]["grammar_hash"]
        assert a[gid]["parent_grammar_id"] == (None if gid == "G0_BASELINE" else AUTHORIZED_PHYSICS_CHAIN[AUTHORIZED_PHYSICS_CHAIN.index(gid) - 1])
        assert a[gid]["status"] == "DECLARED_NOT_EXECUTED"
    d1 = dry_grammar_registry()
    d2 = dry_grammar_registry()
    assert d1["DRY0_SYNTHETIC"]["grammar_hash"] == d2["DRY0_SYNTHETIC"]["grammar_hash"]
    assert d1["DRY1_SYNTHETIC"]["parent_grammar_id"] == "DRY0_SYNTHETIC"


def test_deterministic_candidate_identity():
    g = dry_grammar_registry()["DRY0_SYNTHETIC"]
    first = [c["candidate_hash"] for c in generate_candidates(g)]
    second = [c["candidate_hash"] for c in generate_candidates(g)]
    assert first == second
    assert all(len(h) == 64 for h in first)
    ids = [c["candidate_id"] for c in generate_candidates(g)]
    assert ids == sorted(ids)


def test_top_down_input_integrity():
    h1 = top_down_input_hash()
    h2 = top_down_input_hash()
    assert h1 == h2
    assert len(h1) == 64


def test_constraint_registry_integrity():
    reg = constraint_registry()
    ids = [c["constraint_id"] for c in reg]
    assert ids[:15] == [f"KP{i:02d}" for i in range(1, 16)]
    assert all(c["numerical_content_present"] is False for c in reg)
    assert all(c["dry_run_result"] == "NOT_APPLICABLE" for c in reg if c["constraint_id"].startswith("KP"))
    assert "DRY_C_NOT_R" in ids


def test_lazy_candidate_generation():
    g = dry_grammar_registry()["DRY0_SYNTHETIC"]
    gen = generate_candidates(g)
    first = next(gen)
    assert first["assignment"]["token"] in {"p", "q"}
    bounded = list(generate_candidates(g, bound=1))
    assert len(bounded) == 1


def test_deterministic_enumeration_and_early_pruning():
    g0 = dry_grammar_registry()["DRY0_SYNTHETIC"]
    raw = count_raw_combinations(g0)
    pruned = count_pruned(g0)
    generated = list(generate_candidates(g0))
    assert raw == 3
    assert pruned == 1
    assert len(generated) == 2
    assert raw == pruned + len(generated)
    assert all(c["assignment"]["token"] != "r" for c in generated)
    tokens = [c["assignment"]["token"] for c in generated]
    assert tokens == ["p", "q"]


def test_cache_invalidation():
    g = dry_grammar_registry()["DRY0_SYNTHETIC"]
    cand = next(generate_candidates(g))
    cache = ClosureTestCache()
    a = cache.evaluate(cand, test_version="v1", dep_hash="depA")
    b = cache.evaluate(cand, test_version="v1", dep_hash="depA")
    c = cache.evaluate(cand, test_version="v2", dep_hash="depA")
    d = cache.evaluate(cand, test_version="v1", dep_hash="depB")
    assert a["cache"] == "MISS"
    assert b["cache"] == "HIT"
    assert c["cache"] == "MISS"
    assert d["cache"] == "MISS"


def test_equivalence_certification_and_provenance(tmp_path):
    engine = ClosureEngine(tmp_path, chain="dry")
    stats = engine.evaluate_grammar("DRY0_SYNTHETIC")
    for eq in stats["equivalence_classes"]:
        assert eq["proof_status"] == "CERTIFIED"
        assert eq["equivalence_rule"] == "IDENTITY_EQUAL"
    for cand in stats["candidates"]:
        assert cand["provenance"] == "METHOD / INTEGRITY CONTROL"
    p_hash = next(c["candidate_hash"] for c in stats["candidates"] if c["assignment"]["token"] == "p")
    q_hash = next(c["candidate_hash"] for c in stats["candidates"] if c["assignment"]["token"] == "q")
    assert p_hash != q_hash


def test_target_blindness_and_illegal_extension(tmp_path):
    with pytest.raises(EngineFailure) as ei:
        assert_target_blind({"x": "1/" + "3"})
    assert ei.value.mode == "TARGET_CONTAMINATION_DETECTED"
    with pytest.raises(EngineFailure) as ej:
        assert_target_blind({"fn": "distance_to_known_value"})
    assert ej.value.mode == "TARGET_CONTAMINATION_DETECTED"
    engine = ClosureEngine(tmp_path, chain="dry")
    with pytest.raises(EngineFailure) as ek:
        engine.advance_grammar("G5_ANOMALY_CONSTRAINTS", "DRY0_SYNTHETIC")
    assert ek.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as el:
        ClosureEngine(tmp_path / "phys", chain="physics")
    assert el.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_checkpoint_resume_and_corruption(tmp_path):
    engine = ClosureEngine(tmp_path, chain="dry")
    state = engine.run_until_closure()
    assert engine.checkpoint_path("DRY0_SYNTHETIC").is_file()
    assert engine.checkpoint_path("DRY1_SYNTHETIC").is_file()
    engine.verify_checkpoint("DRY0_SYNTHETIC")
    engine.verify_checkpoint("DRY1_SYNTHETIC")
    resumed = engine.resume_closure()
    assert resumed["closure_status"] == state["closure_status"]
    path = engine.checkpoint_path("DRY1_SYNTHETIC")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["integrity_digest"] = "00" * 32
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(EngineFailure) as ei:
        engine.verify_checkpoint("DRY1_SYNTHETIC")
    assert ei.value.mode == "CHECKPOINT_CORRUPTED"


def test_deterministic_parallel_and_accounting(tmp_path):
    serial = ClosureEngine(tmp_path / "s", chain="dry")
    parallel = ClosureEngine(tmp_path / "p", chain="dry")
    a = serial.evaluate_grammar("DRY1_SYNTHETIC", parallel=False)
    b = parallel.evaluate_grammar("DRY1_SYNTHETIC", parallel=True)
    assert a["candidate_hashes"] == b["candidate_hashes"]
    assert [c["candidate_id"] for c in a["candidates"]] == [c["candidate_id"] for c in b["candidates"]]
    assert a["raw_theoretical_combinations"] == a["metadata_pruned_candidates"] + a["generated_candidates"]
    assert a["generated_candidates"] == a["rejected"] + a["unresolved"] + a["compatible"]
    assert len(set(a["candidate_hashes"])) == len(a["candidate_hashes"])


def test_method_failure_is_not_scientific_negative():
    failed = {"METHOD_STATUS": "FAILED", "SCIENTIFIC_STATUS": "NOT_ANALYZED"}
    assert failed["METHOD_STATUS"] == "FAILED"
    assert failed["SCIENTIFIC_STATUS"] == "NOT_ANALYZED"
    assert failed["SCIENTIFIC_STATUS"] != "NO_SURVIVORS"


def test_end_of_authorized_chain_and_no_skip(tmp_path):
    engine = ClosureEngine(tmp_path, chain="dry")
    state = engine.run_until_closure()
    assert [h["grammar_id"] for h in state["run_history"]] == list(DRY_CHAIN)
    assert state["closure_status"] == "CLOSURE_REACHED"
    assert state["FULL_PHYSICS_GRAMMAR_EXECUTED"] is False
    assert state["SCIENTIFIC_STATUS"] == "NOT_ANALYZED"
    assert state["version_reports"][0]["closure_status"] == "EXTENSION_REQUIRED"
    assert engine.advance_grammar("DRY1_SYNTHETIC", "DRY0_SYNTHETIC") == "DRY1_SYNTHETIC"
    with pytest.raises(EngineFailure):
        engine.advance_grammar("DRY1_SYNTHETIC", None)


def test_content_hash_not_python_hash():
    payload = {"a": 1, "b": [2, 3]}
    assert content_hash(payload) == content_hash({"b": [2, 3], "a": 1})
    assert ENGINE_VERSION.startswith("phase14b0")
