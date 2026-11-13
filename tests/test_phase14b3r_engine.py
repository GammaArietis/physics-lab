"""Phase 14B.3R engine tests: chirality vs representation reality."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import (
    ClosureEngine,
    EngineFailure,
    assert_target_blind,
    content_hash,
    count_pruned,
    count_raw_combinations,
    generate_candidates,
)
from physics_lab.physics.phase14b2_g2 import artifact_dir as phase14b2_artifact_dir
from physics_lab.physics.phase14b3_g3 import (
    g3_executable_registry,
    g3_metadata_legal,
    irrep_data,
)
from physics_lab.physics.phase14b3r_g3 import (
    EXPECTED_OLD_G3_CHECKPOINT_HASH,
    EXPECTED_OLD_G3_GRAMMAR_HASH,
    G3R_ID,
    artifact_dir,
    criterion_pack_diff,
    g3r_executable_registry,
    g3r_metadata_legal,
    g3r_run_tests,
    old_g3_checkpoint_path,
    verify_old_g3_archive,
)


def test_weyl_real_and_pseudoreal_not_automatically_rejected():
    g = g3r_executable_registry()[G3R_ID]
    real_pack = {"g3_pack": "SU_N:3|k:0|Nf:1|D:1,1|W:none|M:1"}
    pseudo_pack = {"g3_pack": "SU_N:2|k:0|Nf:1|D:1|W:none|M:1"}
    real_ok, _ = g3r_metadata_legal(real_pack, g)
    pseudo_ok, _ = g3r_metadata_legal(pseudo_pack, g)
    assert real_ok is True
    assert pseudo_ok is True
    assert irrep_data(3, (1, 1))["reality_type"] == "real"
    assert irrep_data(2, (1,))["reality_type"] == "pseudoreal"
    cand = {
        "assignment": pseudo_pack,
        "grammar_version": G3R_ID,
        "candidate_id": "t",
        "candidate_hash": "0" * 64,
        "provenance": "LOGICAL CORRECTION",
    }
    tested = g3r_run_tests(cand)
    ids = {t["test_id"]: t for t in tested["results"]}
    assert tested["status"] == "PASS"
    assert ids["KP10"]["status"] == "PASS"
    assert ids["KP12"]["status"] == "UNTESTED"
    assert tested["lorentz_chirality"] == "Weyl"
    assert tested["representation_reality_type"] == "pseudoreal"
    assert tested["lorentz_chirality"] != tested["representation_reality_type"]
    assert tested["vectorlike_status"] == "UNTESTED"
    assert tested["anomaly_status"] == "DEFERRED_TO_G5"
    assert tested["CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION"] == "NO"
    old_g = g3_executable_registry()["G3_FINITE_REPRESENTATIONS"]
    old_real, why_real = g3_metadata_legal(real_pack, old_g)
    old_pseudo, why_pseudo = g3_metadata_legal(pseudo_pack, old_g)
    assert old_real is False
    assert old_pseudo is False
    assert why_real == "cannot_support_chiral_gauge_structure"
    assert why_pseudo == "cannot_support_chiral_gauge_structure"


def test_pure_su2_fundamental_survives_and_anomaly_unused(tmp_path):
    engine = ClosureEngine(tmp_path, chain="g3r_only")
    stats = engine.evaluate_grammar(G3R_ID)
    packs = [c["assignment"]["g3_pack"] for c in stats["candidates"] if c["filter_status"] == "PASS"]
    assert "SU_N:2|k:0|Nf:1|D:1|W:none|M:1" in packs
    assert "SU_N:2|k:0|Nf:2|D:1|W:none|M:1" in packs
    for cand in stats["candidates"]:
        tests = {t["test_id"]: t for t in cand["tests"]["results"]}
        assert tests["KP12"]["status"] == "UNTESTED"
        assert tests["anomaly_status"]["status"] == "UNTESTED"
        assert cand["tests"]["anomaly_status"] == "DEFERRED_TO_G5"
        assert "anomaly" not in (cand["tests"].get("irrep") or {})
        assert tests["KP10"]["status"] == "PASS"
        assert tests["CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION"]["note"] == "NO"
        assert cand["tests"]["representation_reality_type"] in {"real", "pseudoreal", "complex"}
        assert cand["tests"]["lorentz_chirality"] == "Weyl"
        assert cand["tests"]["vectorlike_status"] == "UNTESTED"


def test_no_g4_old_checkpoint_immutable_and_new_identity(tmp_path):
    before_old = old_g3_checkpoint_path().read_bytes()
    before_g2 = (phase14b2_artifact_dir() / "closure_checkpoint_G2_COMPACT_NONABELIAN.json").read_bytes()
    archived = verify_old_g3_archive()
    assert archived["grammar_hash"] == EXPECTED_OLD_G3_GRAMMAR_HASH
    g = g3r_executable_registry()[G3R_ID]
    assert g["grammar_hash"] != EXPECTED_OLD_G3_GRAMMAR_HASH
    assert g["grammar_id"] == G3R_ID
    engine = ClosureEngine(tmp_path, chain="g3r_only")
    assert engine.chain == [G3R_ID]
    state = engine.run_until_closure()
    assert state["G3_CORRECTED_EXECUTED"] is True
    assert state["G4_EXECUTED"] is False
    assert state["closure_status"] == "CLOSURE_REACHED"
    rep = state["version_reports"][0]
    assert rep["compatible"] == 112
    assert rep["metadata_pruned_candidates"] == 0
    assert (old_g3_checkpoint_path().read_bytes()) == before_old
    assert (phase14b2_artifact_dir() / "closure_checkpoint_G2_COMPACT_NONABELIAN.json").read_bytes() == before_g2
    ckpt = engine.verify_checkpoint(G3R_ID)
    assert ckpt["grammar_id"] == G3R_ID
    assert ckpt["grammar_hash"] != EXPECTED_OLD_G3_GRAMMAR_HASH
    assert ckpt["parent_grammar_id"] == "G2_COMPACT_NONABELIAN"
    with pytest.raises(EngineFailure) as ei:
        engine.advance_grammar("G4_SCALAR_MULTIPLETS_VEV", G3R_ID)
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path / "phys", chain="physics")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    _ = EXPECTED_OLD_G3_CHECKPOINT_HASH
    _ = artifact_dir


def test_accounting_and_correction_diff():
    g = g3r_executable_registry()[G3R_ID]
    raw = count_raw_combinations(g)
    pruned = count_pruned(g)
    generated = list(generate_candidates(g))
    assert raw == 112
    assert pruned == 0
    assert len(generated) == 112
    assert raw == pruned + len(generated)
    assert all(c["provenance"] == "LOGICAL CORRECTION" for c in generated)
    first = [c["candidate_hash"] for c in generate_candidates(g)]
    second = [c["candidate_hash"] for c in generate_candidates(g)]
    assert first == second
    old_g = g3_executable_registry()["G3_FINITE_REPRESENTATIONS"]
    old_hashes = [c["candidate_hash"] for c in generate_candidates(old_g)]
    assert set(first).isdisjoint(set(old_hashes))
    diff = criterion_pack_diff()
    assert diff["OLD_G3_COMPATIBLE"] == 80
    assert diff["CORRECTED_G3_COMPATIBLE"] == 112
    assert len(diff["RESTORED_CLASSES"]) == 32
    assert diff["REMOVED_CLASSES"] == []
    assert len(diff["UNCHANGED_CLASSES"]) == 80
    assert "SU_N:2|k:0|Nf:1|D:1|W:none|M:1" in diff["RESTORED_CLASSES"]
    assert "SU_N:2|k:0|Nf:2|D:1|W:none|M:1" in diff["RESTORED_CLASSES"]
    with pytest.raises(EngineFailure):
        assert_target_blind({"x": "1/" + "3"})
    assert content_hash({"a": 1}) == content_hash({"a": 1})
