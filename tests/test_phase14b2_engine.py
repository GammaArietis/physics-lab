"""Phase 14B.2 unit tests: groups, algebra, products, incremental reuse, no G3."""

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
from physics_lab.physics.phase14b1_g1 import artifact_dir as phase14b1_artifact_dir
from physics_lab.physics.phase14b2_g2 import (
    EXPECTED_G1_GRAMMAR_HASH,
    GROUP_SEARCH_BOUNDS,
    N_SU_SEARCH_LIMIT,
    U1_FACTOR_SEARCH_LIMIT,
    connection_structure,
    field_strength_structure,
    g2_executable_registry,
    g2_metadata_legal,
    product_representation,
    su_n_generators,
    validate_su_n,
    verify_g1_parent_checkpoint,
)


def test_g1_parent_checkpoint_integrity():
    payload = verify_g1_parent_checkpoint()
    assert payload["grammar_id"] == "G1_FERMIONIC_CHIRAL"
    assert payload["grammar_hash"] == EXPECTED_G1_GRAMMAR_HASH
    assert len(payload["survivor_hashes"]) == 2
    path = phase14b1_artifact_dir() / "closure_checkpoint_G1_FERMIONIC_CHIRAL.json"
    assert path.is_file()


def test_compact_group_and_lie_algebra_validity():
    for n in (2, 3, 4):
        gens = su_n_generators(n)
        assert len(gens) == n * n - 1
        report = validate_su_n(n)
        assert report["compact"] is True
        assert report["connected"] is True
        assert report["non_Abelian"] is True
        assert report["finite_dimensional_Lie_algebra"] is True
        assert report["generator_count_matches"] is True
        assert report["hermitian_traceless_generators"] is True
        assert report["commutation_verified"] is True
        assert report["structure_constants_real"] is True
        assert report["killing_form_on_iT_negative_definite"] is True
        assert report["numerical_coupling_assigned"] is False
    again = validate_su_n(2)
    assert again["commutation_verified"] is True


def test_product_group_and_representation_slots():
    g = g2_executable_registry()["G2_COMPACT_NONABELIAN"]
    axes = g["axes"]
    assert axes["simple_group"] == [f"SU_N:{n}" for n in N_SU_SEARCH_LIMIT]
    assert axes["u1_k"] == list(U1_FACTOR_SEARCH_LIMIT)
    assert "exceptional groups" in g["explicit_exclusions"]
    assert "G3 finite representation catalogue" in g["explicit_exclusions"]
    assert product_representation(0, "1") == "representation_slot"
    assert "representation_slot x U(1)^1" in product_representation(1, "2")
    assert "q_1" in product_representation(1, "2")
    assert "q_2" in product_representation(1, "2")
    legal, _ = g2_metadata_legal({"n_fermion": "1", "simple_group": "SU_N:2", "u1_k": "0"}, g)
    assert legal is True
    illegal, reason = g2_metadata_legal({"n_fermion": "1", "simple_group": "U1_only", "u1_k": "0"}, g)
    assert illegal is False
    assert reason == "not_compact_connected_nonabelian_SU_N"


def test_connection_and_field_strength_structure():
    conn = connection_structure(3)
    assert conn["formula"] == "A_mu = A_mu^a T_a"
    assert conn["coupling_status"] == "FREE / PARAMETER-DEPENDENT"
    assert conn["numerical_coupling_assigned"] is False
    fs = field_strength_structure()
    assert "[A_mu, A_nu]" in fs["formula"]
    assert fs["kinetic_placeholder"] == "DEFERRED TO GAUGE-DYNAMICS ANALYSIS"
    assert fs["new_physical_parameters"] is False
    assert fs["symbolic_covariance"] == "VERIFIED_GIVEN_LIE_ALGEBRA_CLOSURE"


def test_deterministic_g2_identity_and_accounting():
    g = g2_executable_registry()["G2_COMPACT_NONABELIAN"]
    first = [c["candidate_hash"] for c in generate_candidates(g)]
    second = [c["candidate_hash"] for c in generate_candidates(g)]
    assert first == second
    assert all(len(h) == 64 for h in first)
    assert len(set(first)) == 12
    raw = count_raw_combinations(g)
    pruned = count_pruned(g)
    generated = list(generate_candidates(g))
    assert raw == 12
    assert pruned == 0
    assert len(generated) == 12
    assert raw == pruned + len(generated)
    assert all(c["assignment"]["simple_group"].startswith("SU_N:") for c in generated)
    assert all(c["provenance"] == "GRAMMAR EXTENSION" for c in generated)
    kinds = {(c["assignment"]["simple_group"], c["assignment"]["u1_k"], c["assignment"]["n_fermion"]) for c in generated}
    assert len(kinds) == 12


def test_incremental_reuse_no_g3(tmp_path):
    before = (phase14b1_artifact_dir() / "closure_checkpoint_G1_FERMIONIC_CHIRAL.json").read_bytes()
    engine = ClosureEngine(tmp_path, chain="g2_only")
    assert engine.chain == ["G2_COMPACT_NONABELIAN"]
    state = engine.run_until_closure()
    assert [h["grammar_id"] for h in state["run_history"]] == ["G2_COMPACT_NONABELIAN"]
    assert state["G2_EXECUTED"] is True
    assert state["G3_EXECUTED"] is False
    assert state["closure_status"] == "CLOSURE_REACHED"
    rep = state["version_reports"][0]
    assert rep["g1_survivors_reused"] == 2
    assert rep["g2_new_candidates_generated"] == 12
    assert rep["compatible"] == 12
    assert (phase14b1_artifact_dir() / "closure_checkpoint_G1_FERMIONIC_CHIRAL.json").read_bytes() == before
    ckpt = engine.verify_checkpoint("G2_COMPACT_NONABELIAN")
    assert ckpt["parent_grammar_id"] == "G1_FERMIONIC_CHIRAL"
    assert ckpt["search_bounds"]["N_range"] == list(N_SU_SEARCH_LIMIT)
    assert ckpt["target_blindness"] == "VERIFIED"
    for eq in ckpt["equivalence_classes"]:
        assert eq["proof_status"] == "CERTIFIED"
        assert eq["equivalence_rule"] == "IDENTITY_EQUAL"
    with pytest.raises(EngineFailure) as ei:
        engine.advance_grammar("G3_FINITE_REPRESENTATIONS", "G2_COMPACT_NONABELIAN")
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path / "phys", chain="physics")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_chirality_deferred_and_no_mass_inference(tmp_path):
    engine = ClosureEngine(tmp_path, chain="g2_only")
    stats = engine.evaluate_grammar("G2_COMPACT_NONABELIAN")
    for cand in stats["candidates"]:
        tests = {t["test_id"]: t for t in cand["tests"]["results"]}
        assert tests["chirality_preservation"]["status"] == "PASS"
        assert tests["KP12"]["status"] == "UNTESTED"
        assert tests["KP13"]["status"] == "NOT_APPLICABLE"
        assert tests["KP15"]["status"] == "NOT_APPLICABLE"
        assert tests["anomaly_status"]["status"] == "UNTESTED"
        assert tests["vector_mass_structure"]["status"] == "NOT_APPLICABLE"
        assert "generator count is not a mass spectrum" in tests["vector_mass_structure"]["note"]
        assert cand["tests"]["anomaly_status"] == "DEFERRED_TO_G5"
        assert cand["tests"]["vector_mass_structure"] == "DEFERRED_TO_G4"
        assert cand["tests"]["chirality_preserved"] is True
        assert cand["assignment"].get("fermion_kind") is None
    inv = stats["parameter_inventory"]
    assert all("g_SU_N" in row["independent_symbolic_gauge_couplings"] for row in inv)
    assert all(row["independent_continuous_gauge_couplings"] in {1, 2} for row in inv)
    groups = {row["gauge_group"] for row in inv}
    assert "SU(2)" in groups
    assert "SU(3)" in groups
    assert "SU(4)" in groups
    assert "SU(2) x U(1)" in groups
    _ = GROUP_SEARCH_BOUNDS
    with pytest.raises(EngineFailure):
        assert_target_blind({"x": "1/" + "3"})
    assert content_hash({"a": 1, "b": 2}) == content_hash({"b": 2, "a": 1})
