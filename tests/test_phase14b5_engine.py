"""Phase 14B.5 engine tests: anomalies, Witten, scalars excluded, no G6."""

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
from physics_lab.physics.phase14b3_g3 import R_MAX, conjugate_dynkin
from physics_lab.physics.phase14b4r_g4 import G4R_ID, artifact_dir as phase14b4r_artifact_dir
from physics_lab.physics.phase14b5_g5 import (
    EXPECTED_G4R_CHECKPOINT_HASH,
    EXPECTED_G4R_GRAMMAR_HASH,
    G5_ID,
    N_SCALAR_MAX,
    anomaly_analysis,
    cubic_anomaly_coefficient,
    g4r_checkpoint_path,
    g5_executable_registry,
    g5_metadata_legal,
    parse_g5_pack,
    t_index,
    verify_g4r_parent_checkpoint,
)


def test_g4r_parent_checkpoint_integrity():
    payload = verify_g4r_parent_checkpoint()
    assert payload["grammar_id"] == G4R_ID
    assert payload["grammar_hash"] == EXPECTED_G4R_GRAMMAR_HASH
    assert len(payload["survivor_hashes"]) == 2428
    assert g4r_checkpoint_path().is_file()


def test_cubic_anomaly_and_conjugate_sign():
    assert cubic_anomaly_coefficient(3, (1, 0)) == 1
    assert cubic_anomaly_coefficient(3, (0, 1)) == -1
    assert cubic_anomaly_coefficient(3, conjugate_dynkin((1, 0))) == -cubic_anomaly_coefficient(3, (1, 0))
    assert cubic_anomaly_coefficient(3, (1, 1)) == 0
    assert cubic_anomaly_coefficient(2, (1,)) == 0
    assert cubic_anomaly_coefficient(4, (0, 1, 0)) == 0
    assert cubic_anomaly_coefficient(4, (1, 1, 0)) == -cubic_anomaly_coefficient(4, (0, 1, 1))
    assert cubic_anomaly_coefficient(4, (1, 1, 0)) != 0


def test_su2_global_and_fund_2t():
    assert t_index(2, (1,)) * 2 == 1
    odd = anomaly_analysis(2, (1,), 1, 0, "none")
    even = anomaly_analysis(2, (1,), 2, 0, "none")
    singlet = anomaly_analysis(2, (0,), 1, 0, "none")
    assert odd["tests"]["SU2_GLOBAL"] == "FAIL"
    assert even["tests"]["SU2_GLOBAL"] == "PASS"
    assert singlet["tests"]["SU2_GLOBAL"] == "PASS"
    assert odd["tests"]["SU_N_CUBIC"] == "NOT_APPLICABLE"
    assert odd["WITTEN_GLOBAL_ANOMALY"] == "FAIL"


def test_mixed_u1_and_gravity_and_failure_detection():
    charged = anomaly_analysis(3, (1, 1), 1, 1, "1")
    neutral = anomaly_analysis(3, (1, 1), 1, 1, "0")
    none = anomaly_analysis(3, (1, 1), 1, 0, "none")
    fund = anomaly_analysis(3, (1, 0), 1, 0, "none")
    assert charged["tests"]["U1_CUBIC"] == "FAIL"
    assert charged["tests"]["GRAVITY_SQUARE_U1"] == "FAIL"
    assert charged["total_anomaly_status"] == "FAIL"
    assert neutral["tests"]["U1_CUBIC"] == "PASS"
    assert neutral["tests"]["GRAVITY_SQUARE_U1"] == "PASS"
    assert neutral["tests"]["SU_N_SQUARE_U1"] == "PASS"
    assert none["tests"]["U1_CUBIC"] == "NOT_APPLICABLE"
    assert none["tests"]["MULTI_U1_TENSOR"] == "NOT_APPLICABLE"
    assert fund["tests"]["SU_N_CUBIC"] == "FAIL"
    assert none["total_anomaly_status"] == "PASS"
    two = anomaly_analysis(3, (1, 0), 2, 0, "none")
    assert two["A_G"] == 2
    assert two["tests"]["SU_N_CUBIC"] == "FAIL"


def test_scalars_excluded_and_vev_independence():
    a = anomaly_analysis(4, (0, 1, 0), 1, 0, "none", scalar_dynkin="1,0,0", scalar_u1="1", orbit_type_id="symplectic_2form")
    b = anomaly_analysis(4, (0, 1, 0), 1, 0, "none", scalar_dynkin="0,1,0", scalar_u1="none", orbit_type_id="decomposable_2form")
    assert a["tests"] == b["tests"]
    assert a["A_G"] == b["A_G"]
    assert a["scalar_included_in_chiral_anomaly"] is False
    assert a["VEV_orbit_required"] is False
    assert a["VEV_orbit_dependency"] == "NOT REQUIRED"
    assert a["VECTORLIKE_STATUS"] == "UNTESTED"
    assert a["ANOMALY_STATUS"] == a["total_anomaly_status"]
    assert a["VECTORLIKE_STATUS"] != a["ANOMALY_STATUS"] or a["ANOMALY_STATUS"] == "UNTESTED"


def test_lazy_enumeration_and_no_g6(tmp_path):
    g = g5_executable_registry()[G5_ID]
    legal, _ = g5_metadata_legal({"g5_pack": g["axes"]["g5_pack"][0]}, g)
    assert legal is True
    bad, why = g5_metadata_legal({"g5_pack": "not-a-pack"}, g)
    assert bad is False
    assert N_SCALAR_MAX == 1
    assert R_MAX == 1
    first = [c["candidate_hash"] for c in generate_candidates(g)]
    second = [c["candidate_hash"] for c in generate_candidates(g)]
    assert first == second
    raw = count_raw_combinations(g)
    pruned = count_pruned(g)
    all_gen = list(generate_candidates(g))
    assert raw == 2428
    assert pruned == 0
    assert len(all_gen) == 2428
    assert raw == pruned + len(all_gen)
    assert all(c["provenance"] == "GRAMMAR EXTENSION" for c in all_gen)
    parsed = parse_g5_pack(all_gen[0]["assignment"]["g5_pack"])
    assert "g3_pack" in parsed
    before = g4r_checkpoint_path().read_bytes()
    engine = ClosureEngine(tmp_path, chain="g5_only")
    assert engine.chain == [G5_ID]
    state = engine.run_until_closure()
    assert state["G5_EXECUTED"] is True
    assert state["G6_EXECUTED"] is False
    assert state["closure_status"] == "CLOSURE_REACHED"
    rep = state["version_reports"][0]
    assert rep["compatible"] > 0
    assert rep["rejected"] > 0
    assert rep["unresolved"] == 0
    assert rep["generated_candidates"] == 2428
    assert g4r_checkpoint_path().read_bytes() == before
    assert (phase14b4r_artifact_dir() / "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV_R1.json").read_bytes() == before
    ckpt = engine.verify_checkpoint(G5_ID)
    assert ckpt["parent_grammar_id"] == G4R_ID
    assert ckpt["parent_grammar_hash"] == EXPECTED_G4R_GRAMMAR_HASH
    assert ckpt["parent_checkpoint_hash"] == EXPECTED_G4R_CHECKPOINT_HASH
    assert ckpt["search_bounds"]["R_MAX"] == 1
    assert ckpt["anomaly_engine_version"]
    for cand in rep.get("class_table") or []:
        if cand["status"] == "PASS":
            assert cand["total_anomaly_status"] == "PASS"
            assert cand["VECTORLIKE_STATUS"] == "UNTESTED"
            assert cand["VEV_orbit_dependency"] == "NOT REQUIRED"
    with pytest.raises(EngineFailure) as ei:
        engine.advance_grammar("G6_STRUCTURAL_GAUGE_CONSISTENCY", G5_ID)
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path / "phys", chain="physics")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure):
        assert_target_blind({"x": "1/" + "3"})
    assert content_hash({"a": 1}) == content_hash({"a": 1})
