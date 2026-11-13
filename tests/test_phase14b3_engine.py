"""Phase 14B.3 unit tests: catalogue, Dynkin, conjugation, U(1), no G4."""

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
    EXPECTED_G2_GRAMMAR_HASH,
    M_MAX,
    N_U1_MAX,
    R_MAX,
    build_representation_catalogue,
    conjugate_dynkin,
    g3_executable_registry,
    g3_metadata_legal,
    irrep_data,
    product_is_complex,
    su_n_dimension,
    verify_g2_parent_checkpoint,
)


def test_g2_parent_checkpoint_integrity():
    payload = verify_g2_parent_checkpoint()
    assert payload["grammar_id"] == "G2_COMPACT_NONABELIAN"
    assert payload["grammar_hash"] == EXPECTED_G2_GRAMMAR_HASH
    assert len(payload["survivor_hashes"]) == 12
    assert (phase14b2_artifact_dir() / "closure_checkpoint_G2_COMPACT_NONABELIAN.json").is_file()


def test_deterministic_representation_catalogue_and_dynkin():
    a = build_representation_catalogue()
    b = build_representation_catalogue()
    assert a == b
    assert len(a) == 14
    assert su_n_dimension(2, (0,)) == 1
    assert su_n_dimension(2, (1,)) == 2
    assert su_n_dimension(3, (0, 0)) == 1
    assert su_n_dimension(3, (1, 0)) == 3
    assert su_n_dimension(3, (0, 1)) == 3
    assert su_n_dimension(3, (1, 1)) == 8
    assert su_n_dimension(4, (1, 0, 0)) == 4
    assert su_n_dimension(4, (0, 0, 1)) == 4
    assert conjugate_dynkin((1, 0)) == (0, 1)
    assert conjugate_dynkin((1, 0, 0)) == (0, 0, 1)
    fund = irrep_data(3, (1, 0))
    anti = irrep_data(3, (0, 1))
    assert fund["reality_type"] == "complex"
    assert fund["dimension"] == 3
    assert anti["dimension"] == 3
    assert fund["C2"] == anti["C2"]
    assert fund["T"] == anti["T"]
    assert fund["C2"] == [4, 3]
    assert fund["T"] == [1, 2]
    assert fund["REPRESENTATION_CONTENT_HASH"] == content_hash({"group": "SU(3)", "dynkin": [1, 0]})
    adj = irrep_data(3, (1, 1))
    assert adj["reality_type"] == "real"
    assert adj["self_conjugate"] is True
    su2 = irrep_data(2, (1,))
    assert su2["reality_type"] == "pseudoreal"
    assert product_is_complex(2, (1,), 0, "none") is False
    assert product_is_complex(2, (1,), 1, "1") is True
    assert product_is_complex(2, (1,), 1, "0") is False
    assert product_is_complex(3, (1, 0), 0, "none") is True
    hashes = [row["REPRESENTATION_CONTENT_HASH"] for row in a]
    assert len(set(hashes)) == len(hashes)
    _ = R_MAX
    _ = M_MAX
    _ = N_U1_MAX


def test_u1_character_and_product_validity():
    g = g3_executable_registry()["G3_FINITE_REPRESENTATIONS"]
    legal, _ = g3_metadata_legal({"g3_pack": "SU_N:3|k:1|Nf:1|D:1,0|W:-1|M:1"}, g)
    assert legal is True
    illegal, reason = g3_metadata_legal({"g3_pack": "SU_N:2|k:0|Nf:1|D:1|W:none|M:1"}, g)
    assert illegal is False
    assert reason == "cannot_support_chiral_gauge_structure"
    bad, why = g3_metadata_legal({"g3_pack": "SU_N:3|k:0|Nf:1|D:1|W:none|M:1"}, g)
    assert bad is False
    assert why == "dynkin_rank_mismatch"
    over, why2 = g3_metadata_legal({"g3_pack": "SU_N:3|k:1|Nf:1|D:1,0|W:2|M:1"}, g)
    assert over is False
    assert why2 == "u1_weight_outside_N_U1_MAX"


def test_lazy_enumeration_accounting_and_identity():
    g = g3_executable_registry()["G3_FINITE_REPRESENTATIONS"]
    first = [c["candidate_hash"] for c in generate_candidates(g)]
    second = [c["candidate_hash"] for c in generate_candidates(g)]
    assert first == second
    raw = count_raw_combinations(g)
    pruned = count_pruned(g)
    generated = list(generate_candidates(g, bound=3))
    assert len(generated) == 3
    all_gen = list(generate_candidates(g))
    assert raw == 112
    assert pruned == 32
    assert len(all_gen) == 80
    assert raw == pruned + len(all_gen)
    assert len(set(first)) == 80
    assert all(c["provenance"] == "GRAMMAR EXTENSION" for c in all_gen)


def test_incremental_reuse_no_g4(tmp_path):
    before = (phase14b2_artifact_dir() / "closure_checkpoint_G2_COMPACT_NONABELIAN.json").read_bytes()
    engine = ClosureEngine(tmp_path, chain="g3_only")
    assert engine.chain == ["G3_FINITE_REPRESENTATIONS"]
    state = engine.run_until_closure()
    assert [h["grammar_id"] for h in state["run_history"]] == ["G3_FINITE_REPRESENTATIONS"]
    assert state["G3_EXECUTED"] is True
    assert state["G4_EXECUTED"] is False
    assert state["closure_status"] == "CLOSURE_REACHED"
    rep = state["version_reports"][0]
    assert rep["g2_survivors_reused"] == 12
    assert rep["g3_new_candidates_generated"] == 80
    assert rep["compatible"] == 80
    assert (phase14b2_artifact_dir() / "closure_checkpoint_G2_COMPACT_NONABELIAN.json").read_bytes() == before
    ckpt = engine.verify_checkpoint("G3_FINITE_REPRESENTATIONS")
    assert ckpt["parent_grammar_id"] == "G2_COMPACT_NONABELIAN"
    assert ckpt["search_bounds"]["R_MAX"] == 1
    assert ckpt["target_blindness"] == "VERIFIED"
    assert ckpt.get("representation_catalogue_hash")
    for eq in ckpt["equivalence_classes"]:
        assert eq["proof_status"] == "CERTIFIED"
        assert eq["equivalence_rule"] == "IDENTITY_EQUAL"
    with pytest.raises(EngineFailure) as ei:
        engine.advance_grammar("G4_SCALAR_MULTIPLETS_VEV", "G3_FINITE_REPRESENTATIONS")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path / "phys", chain="physics")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_deferred_anomaly_ssb_and_invariants(tmp_path):
    engine = ClosureEngine(tmp_path, chain="g3_only")
    stats = engine.evaluate_grammar("G3_FINITE_REPRESENTATIONS")
    for cand in stats["candidates"]:
        tests = {t["test_id"]: t for t in cand["tests"]["results"]}
        assert tests["KP12"]["status"] == "UNTESTED"
        assert tests["KP13"]["status"] == "NOT_APPLICABLE"
        assert tests["KP15"]["status"] == "NOT_APPLICABLE"
        assert tests["anomaly_status"]["status"] == "UNTESTED"
        assert tests["SSB_STATUS"]["status"] == "NOT_APPLICABLE"
        assert cand["tests"]["anomaly_status"] == "DEFERRED_TO_G5"
        assert cand["tests"]["SSB_STATUS"] == "DEFERRED_TO_G4"
        assert cand["tests"]["VECTOR_MASS_STATUS"] == "DEFERRED_TO_G4"
        irrep = cand["tests"]["irrep"]
        assert irrep["dimension"] >= 1
        assert irrep["C2"][1] >= 1
        assert "REPRESENTATION_CONTENT_HASH" in irrep
    inv = stats["parameter_inventory"]
    assert all(row["provenance"]["gauge_coupling"] == "FREE / PARAMETER-DEPENDENT" for row in inv)
    with pytest.raises(EngineFailure):
        assert_target_blind({"x": "1/" + "3"})
    assert content_hash({"a": 1}) == content_hash({"a": 1})
