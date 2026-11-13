"""Phase 14B.6 engine tests: covariance, KP15, anomaly integrity, no G7."""

from __future__ import annotations

import pytest

from physics_lab.physics.phase14b0_engine import (
    ClosureEngine,
    EngineFailure,
    assert_target_blind,
    content_hash,
    generate_candidates,
)
from physics_lab.physics.phase14b4r_g4 import breaking_analysis_orbit
from physics_lab.physics.phase14b5_g5 import G5_ID, anomaly_analysis
from physics_lab.physics.phase14b6_g6 import (
    EXPECTED_G5_CHECKPOINT_HASH,
    EXPECTED_G5_GRAMMAR_HASH,
    G6_ID,
    g5_checkpoint_path,
    g6_executable_registry,
    g6_metadata_legal,
    local_covariance_check,
    parse_g6_pack,
    structural_analysis,
    verify_g5_parent_checkpoint,
)


def test_g5_parent_checkpoint_integrity():
    payload = verify_g5_parent_checkpoint()
    assert payload["grammar_id"] == G5_ID
    assert payload["grammar_hash"] == EXPECTED_G5_GRAMMAR_HASH
    assert len(payload["survivor_hashes"]) == 479
    assert g5_checkpoint_path().is_file()
    assert EXPECTED_G5_CHECKPOINT_HASH


def test_local_covariance_scalar_fermion_and_product():
    su2 = local_covariance_check(2, (1,), 0, "none")
    su3 = local_covariance_check(3, (1, 1), 0, "none")
    prod = local_covariance_check(3, (0, 0), 1, "0")
    fund = local_covariance_check(3, (1, 0), 1, "0")
    assert su2["status"] == "PASS"
    assert su3["status"] == "PASS"
    assert prod["status"] == "PASS"
    assert fund["status"] == "PASS"
    assert su2["infinitesimal_covariance"] is True
    assert prod["product_u1"] is True
    assert su2["curvature_covariance"] is True
    assert fund["matter_kinetic_invariance"] is True


def test_nonabelian_connection_and_matter_invariance():
    out = local_covariance_check(4, (0, 1, 0), 0, "none")
    assert out["status"] == "PASS"
    assert out["global_covariance"] is True
    assert out["generators_hermitian"] is True
    assert out["convention"].startswith("D_mu")


def test_vev_stabilizer_and_mass_matrix_and_kp15():
    complete = structural_analysis(3, (1, 1), (1, 1), 1, 0, "none", "none", "regular_adjoint")
    assert complete["layers"]["LAYER_C_SCALAR_VEV"] == "PASS"
    assert complete["KP15"] == "PASS"
    assert complete["layer_c"]["massless_vector_count"] > 0
    assert complete["layer_c"]["massive_vector_count"] > 0
    assert complete["layer_c"]["stab_mass_consistent"] is True
    br = breaking_analysis_orbit(3, (1, 1), 0, "none", "regular_adjoint")
    assert complete["layer_c"]["dim_H"] == br["dim_H"]
    partial = structural_analysis(4, (1, 1, 1), (1, 1, 1), 1, 0, "none", "none", "hw_vector")
    assert partial["layers"]["LAYER_C_SCALAR_VEV"] == "PARTIAL"
    assert partial["total_status"] == "PARTIAL"
    assert partial["failure_mode"] == "UNRESOLVED_BY_G4_ORBIT_CLASSIFICATION"


def test_anomaly_integrity_and_vectorlike_separation():
    st = structural_analysis(3, (1, 1), (1, 1), 1, 0, "none", "none", "regular_adjoint")
    an = anomaly_analysis(3, (1, 1), 1, 0, "none")
    assert an["total_anomaly_status"] == "PASS"
    assert st["layers"]["LAYER_E_ANOMALY_INTEGRITY"] == "PASS"
    assert st["VECTORLIKE_STATUS"] == "UNTESTED"
    assert st["total_status"] == "PASS"
    with pytest.raises(EngineFailure) as ei:
        structural_analysis(3, (1, 0), (0, 0), 1, 0, "none", "none", "nonzero_singlet")
    assert ei.value.mode == "ANOMALY_DEPENDENCY_MISMATCH"


def test_lazy_enumeration_and_no_g7(tmp_path):
    g6 = g6_executable_registry()[G6_ID]
    raw_ok, why = g6_metadata_legal({"g6_pack": g6["axes"]["g6_pack"][0]}, g6)
    assert raw_ok, why
    all_gen = list(generate_candidates(g6))
    assert len(all_gen) == 479
    assert all(c["provenance"] == "GRAMMAR EXTENSION" for c in all_gen)
    parsed = parse_g6_pack(all_gen[0]["assignment"]["g6_pack"])
    assert "g5_pack" in parsed
    before = g5_checkpoint_path().read_bytes()
    engine = ClosureEngine(tmp_path, chain="g6_only")
    assert engine.chain == [G6_ID]
    state = engine.run_until_closure()
    assert state["G6_EXECUTED"] is True
    assert state["G7_EXECUTED"] is False
    assert state["closure_status"] == "CLOSURE_REACHED"
    rep = state["version_reports"][0]
    assert rep["generated_candidates"] == 479
    assert rep["unresolved"] == 0
    assert g5_checkpoint_path().read_bytes() == before
    ckpt = engine.verify_checkpoint(G6_ID)
    assert ckpt["parent_grammar_id"] == G5_ID
    assert ckpt["parent_grammar_hash"] == EXPECTED_G5_GRAMMAR_HASH
    assert ckpt["parent_checkpoint_hash"] == EXPECTED_G5_CHECKPOINT_HASH
    assert ckpt["search_bounds"]["R_MAX"] == 1
    assert ckpt["structural_engine_version"]
    couplings = set()
    for cand in rep.get("class_table") or []:
        couplings.update(cand.get("free_couplings") or [])
        assert cand["VECTORLIKE_STATUS"] == "UNTESTED"
        if cand["status"] == "PASS":
            assert cand["structural_consistency"] == "PASS"
            assert cand["local_covariance"] == "PASS"
            assert cand["anomaly_integrity"] == "PASS"
    assert "g_SU_N" in couplings
    with pytest.raises(EngineFailure) as ei:
        engine.advance_grammar("G7_INVENTED", G6_ID)
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path / "phys", chain="physics")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure):
        assert_target_blind({"x": "1/" + "3"})
    assert content_hash({"a": 1}) == content_hash({"a": 1})
