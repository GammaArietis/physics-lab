"""Phase 14B.4 engine tests: scalar VEV, stabilizer, KP13/KP15, no G5."""

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
from physics_lab.physics.phase14b3_g3 import R_MAX, irrep_data
from physics_lab.physics.phase14b3r_g3 import G3R_ID, artifact_dir as phase14b3r_artifact_dir
from physics_lab.physics.phase14b4_g4 import (
    EXPECTED_G3R_GRAMMAR_HASH,
    G4_ID,
    N_SCALAR_MAX,
    breaking_analysis,
    common_stabilizer,
    g4_executable_registry,
    g4_metadata_legal,
    irrep_generators,
    parse_g4_pack,
    pure_u1_breaking,
    verify_g3r_parent_checkpoint,
)


def test_g3r_parent_checkpoint_integrity():
    payload = verify_g3r_parent_checkpoint()
    assert payload["grammar_id"] == G3R_ID
    assert payload["grammar_hash"] == EXPECTED_G3R_GRAMMAR_HASH
    assert len(payload["survivor_hashes"]) == 112
    assert (phase14b3r_artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS_R1.json").is_file()


def test_scalar_representation_validity_and_bounds():
    g = g4_executable_registry()[G4_ID]
    legal, _ = g4_metadata_legal({"g4_pack": "SU_N:3|k:0|Nf:1|D:1,0|W:none|M:1|SD:1,0|SW:none|SM:1"}, g)
    assert legal is True
    bad, why = g4_metadata_legal({"g4_pack": "SU_N:3|k:0|Nf:1|D:1,0|W:none|M:1|SD:1|SW:none|SM:1"}, g)
    assert bad is False
    assert why == "dynkin_rank_mismatch"
    over, why2 = g4_metadata_legal({"g4_pack": "SU_N:3|k:0|Nf:1|D:1,0|W:none|M:1|SD:1,0|SW:none|SM:2"}, g)
    assert over is False
    assert why2 == "scalar_multiplicity_outside_N_SCALAR_MAX"
    assert N_SCALAR_MAX == 1
    assert R_MAX == 1
    assert irrep_data(3, (1, 0))["dimension"] == 3
    gens = irrep_generators(3, (1, 0))
    assert len(gens) == 8
    assert gens[0].shape == (3, 3)


def test_stabilizer_mass_matrix_and_u1_logic():
    su3_fund = breaking_analysis(3, (1, 0), 0, "none")
    assert su3_fund["dim_G"] == 8
    assert su3_fund["dim_H"] == 3
    assert su3_fund["dim_G_over_H"] == 5
    assert su3_fund["partial_breaking"] is True
    assert su3_fund["rank_M2"] == su3_fund["massive_vector_candidate_count"]
    assert su3_fund["nullity_M2"] == su3_fund["massless_vector_count"]
    assert su3_fund["coupling_independent"] is True
    su2_doublet = breaking_analysis(2, (1,), 0, "none")
    assert su2_doublet["complete_breaking"] is True
    assert su2_doublet["partial_breaking"] is False
    su2x_u1 = breaking_analysis(2, (1,), 1, "1")
    assert su2x_u1["partial_breaking"] is True
    assert su2x_u1["dim_G"] == 4
    singlet = breaking_analysis(2, (0,), 0, "none")
    assert singlet["no_breaking"] is True
    u1_none = pure_u1_breaking(0)
    u1_break = pure_u1_breaking(1)
    assert u1_none["no_breaking"] is True
    assert u1_none["dim_G"] == 1
    assert u1_break["complete_breaking"] is True
    assert u1_break["partial_breaking"] is False
    # two VEVs: common stabilizer
    gens = list(irrep_generators(3, (1, 0)))
    v1 = gens[0][:, 0]
    v1 = v1 / (abs(v1[0]) + 1e-12)
    import numpy as np

    v1 = np.array([1.0, 0.0, 0.0], dtype=np.complex128)
    v2 = np.array([0.0, 1.0, 0.0], dtype=np.complex128)
    both = common_stabilizer([(gens, v1, None), (gens, v2, None)])
    one = breaking_analysis(3, (1, 0), 0, "none")
    assert both["dim_H"] <= one["dim_H"]


def test_product_group_not_hardcoded_and_orbit_equivalence():
    a = breaking_analysis(3, (1, 0), 1, "1")
    b = breaking_analysis(3, (0, 1), 1, "1")
    # fund and anti-fund of SU(3) have conjugate but equal stabilizer dimensions
    assert a["dim_H"] == b["dim_H"]
    assert a["dim_G_over_H"] == b["dim_G_over_H"]
    charged_singlet = breaking_analysis(3, (0, 0), 1, "1")
    uncharged_singlet = breaking_analysis(3, (0, 0), 1, "0")
    # do not assume "break SU(N), preserve U(1)"
    assert charged_singlet["partial_breaking"] is True
    assert charged_singlet["dim_G_over_H"] == 1
    assert charged_singlet["dim_H"] == 8
    assert uncharged_singlet["no_breaking"] is True


def test_lazy_enumeration_and_no_g5(tmp_path):
    g = g4_executable_registry()[G4_ID]
    first = [c["candidate_hash"] for c in generate_candidates(g)]
    second = [c["candidate_hash"] for c in generate_candidates(g)]
    assert first == second
    raw = count_raw_combinations(g)
    pruned = count_pruned(g)
    generated = list(generate_candidates(g, bound=3))
    assert len(generated) == 3
    all_gen = list(generate_candidates(g))
    assert raw == 1680
    assert pruned == 0
    assert len(all_gen) == 1680
    assert raw == pruned + len(all_gen)
    assert all(c["provenance"] == "GRAMMAR EXTENSION" for c in all_gen)
    parsed = parse_g4_pack(all_gen[0]["assignment"]["g4_pack"])
    assert "g3_pack" in parsed
    before = (phase14b3r_artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS_R1.json").read_bytes()
    engine = ClosureEngine(tmp_path, chain="g4_only")
    assert engine.chain == [G4_ID]
    state = engine.run_until_closure()
    assert state["G4_EXECUTED"] is True
    assert state["G5_EXECUTED"] is False
    assert state["closure_status"] == "CLOSURE_REACHED"
    rep = state["version_reports"][0]
    assert rep["compatible"] > 0
    assert rep["rejected"] > 0
    assert rep["unresolved"] == 0
    assert rep["generated_candidates"] == 1680
    assert (phase14b3r_artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS_R1.json").read_bytes() == before
    ckpt = engine.verify_checkpoint(G4_ID)
    assert ckpt["parent_grammar_id"] == G3R_ID
    assert ckpt["search_bounds"]["R_MAX"] == 1
    assert ckpt["search_bounds"]["N_SCALAR_MAX"] == 1
    for cand in rep.get("class_table") or []:
        if cand["status"] == "PASS":
            assert cand["KP15"] == "PASS"
            assert cand["anomaly_status"] == "DEFERRED_TO_G5"
    with pytest.raises(EngineFailure) as ei:
        engine.advance_grammar("G5_ANOMALY_CONSTRAINTS", G4_ID)
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path / "phys", chain="physics")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure):
        assert_target_blind({"x": "1/" + "3"})
    assert content_hash({"a": 1}) == content_hash({"a": 1})
