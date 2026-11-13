"""Phase 14B.4R engine tests: independent stabilizer, orbits, mass matrix, no G5."""

from __future__ import annotations

import numpy as np
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
from physics_lab.physics.phase14b3_g3 import R_MAX
from physics_lab.physics.phase14b3r_g3 import G3R_ID, artifact_dir as phase14b3r_artifact_dir
from physics_lab.physics.phase14b4r_g4 import (
    EXPECTED_G3R_GRAMMAR_HASH,
    EXPECTED_OLD_G4_CHECKPOINT_HASH,
    G4R_ID,
    N_SCALAR_MAX,
    breaking_analysis_orbit,
    g4r_executable_registry,
    g4r_metadata_legal,
    independent_mass_matrix,
    old_g4_checkpoint_path,
    orbit_types,
    parse_g4r_pack,
    pure_u1_breaking,
    representative_vev,
    scalar_generators,
    solve_stabilizer,
    stabilizer_algebra_closes,
    vev_orbit_classification_status,
    verify_g3r_parent_checkpoint,
    verify_old_g4_archive,
)


def test_g3r_parent_and_old_g4_archive():
    payload = verify_g3r_parent_checkpoint()
    assert payload["grammar_id"] == G3R_ID
    assert payload["grammar_hash"] == EXPECTED_G3R_GRAMMAR_HASH
    assert len(payload["survivor_hashes"]) == 112
    archived = verify_old_g4_archive()
    assert archived["grammar_id"] == "G4_SCALAR_MULTIPLETS_VEV"
    assert archived["candidate_statistics"]["compatible"] == 1060
    assert old_g4_checkpoint_path().is_file()
    assert EXPECTED_OLD_G4_CHECKPOINT_HASH


def test_independent_stabilizer_and_mass_matrix():
    gens = list(scalar_generators(2, (1,)))
    vev = representative_vev(2, (1,), "nonzero_fundamental")
    stab = solve_stabilizer(gens, vev, None)
    mass = independent_mass_matrix(gens, vev, None)
    assert stab["dim_H"] == mass["nullity_M2"]
    assert stab["broken_dim"] == mass["rank_M2"]
    assert stab["broken_dim"] == stab["dim_G"] - stab["dim_H"]
    assert stabilizer_algebra_closes(gens, stab["nullspace"]) is True


def test_su2_fundamental_complete_breaking():
    data = breaking_analysis_orbit(2, (1,), 0, "none", "nonzero_fundamental")
    assert data["complete_breaking"] is True
    assert data["partial_breaking"] is False
    assert data["dim_G"] == 3
    assert data["dim_H"] == 0
    assert data["broken_dim"] == 3
    assert data["goldstone_direction_count"] == data["orbit_dimension"] == 3
    other = representative_vev(2, (1,), "nonzero_fundamental")
    alt = np.array([1.0, 1.0j], dtype=np.complex128)
    gens = list(scalar_generators(2, (1,)))
    a = solve_stabilizer(gens, other, None)
    b = solve_stabilizer(gens, alt, None)
    assert a["dim_H"] == b["dim_H"] == 0


def test_su3_adjoint_regular_and_degenerate():
    ids = {item["orbit_type_id"] for item in orbit_types(3, (1, 1))}
    assert "regular_adjoint" in ids
    assert "degenerate_adjoint" in ids
    regular = breaking_analysis_orbit(3, (1, 1), 0, "none", "regular_adjoint")
    degenerate = breaking_analysis_orbit(3, (1, 1), 0, "none", "degenerate_adjoint")
    assert regular["dim_H"] == 2
    assert regular["dim_H"] != 1
    assert degenerate["dim_H"] == 4
    assert regular["dim_H"] != degenerate["dim_H"]
    assert regular["stab_mass_consistent"] is True
    assert degenerate["stab_mass_consistent"] is True
    assert regular["goldstone_direction_count"] == regular["broken_dim"] == 6
    assert degenerate["goldstone_direction_count"] == 4


def test_su4_six_antisymmetric_orbits():
    ids = {item["orbit_type_id"] for item in orbit_types(4, (0, 1, 0))}
    assert "symplectic_2form" in ids
    assert "decomposable_2form" in ids
    symplectic = breaking_analysis_orbit(4, (0, 1, 0), 0, "none", "symplectic_2form")
    decomposable = breaking_analysis_orbit(4, (0, 1, 0), 0, "none", "decomposable_2form")
    assert symplectic["dim_H"] == 10
    assert decomposable["dim_H"] == 6
    assert symplectic["dim_H"] != decomposable["dim_H"]
    assert symplectic["nullity_M2"] == symplectic["dim_H"]
    assert decomposable["rank_M2"] == decomposable["dim_G"] - decomposable["dim_H"]
    mixed = breaking_analysis_orbit(4, (0, 1, 0), 1, "1", "symplectic_2form")
    assert mixed["dim_H"] == 10
    assert mixed["dim_G"] == 16


def test_product_groups_and_u1_logic():
    charged = breaking_analysis_orbit(2, (1,), 1, "1", "nonzero_fundamental")
    neutral = breaking_analysis_orbit(2, (1,), 1, "0", "nonzero_fundamental")
    assert charged["dim_G"] == 4
    assert charged["dim_H"] == 1
    assert charged["partial_breaking"] is True
    assert neutral["dim_H"] == 1
    assert charged["stab_mass_consistent"] is True
    fund_u1 = breaking_analysis_orbit(3, (1, 0), 1, "1", "nonzero_fundamental")
    assert fund_u1["dim_H"] == 4
    assert fund_u1["dim_G"] == 9
    charged_singlet = breaking_analysis_orbit(3, (0, 0), 1, "1", "nonzero_singlet")
    uncharged_singlet = breaking_analysis_orbit(3, (0, 0), 1, "0", "nonzero_singlet")
    assert charged_singlet["partial_breaking"] is True
    assert charged_singlet["dim_H"] == 8
    assert charged_singlet["broken_dim"] == 1
    assert uncharged_singlet["no_breaking"] is True
    u1_none = pure_u1_breaking(0)
    u1_break = pure_u1_breaking(1)
    assert u1_none["dim_G"] == 1
    assert u1_none["no_breaking"] is True
    assert u1_break["complete_breaking"] is True
    assert u1_break["partial_breaking"] is False


def test_kp13_kp15_and_no_generic_overclaim():
    singlet = breaking_analysis_orbit(2, (0,), 0, "none", "nonzero_singlet")
    assert singlet["no_breaking"] is True
    su2 = breaking_analysis_orbit(2, (1,), 0, "none", "nonzero_fundamental")
    assert su2["complete_breaking"] is True
    su3 = breaking_analysis_orbit(3, (1, 0), 0, "none", "nonzero_fundamental")
    assert su3["partial_breaking"] is True
    twenty_hw = breaking_analysis_orbit(4, (1, 1, 0), 0, "none", "hw_vector")
    twenty_gen = breaking_analysis_orbit(4, (1, 1, 0), 0, "none", "generic_nonzero")
    assert twenty_hw["dim_H"] != twenty_gen["dim_H"]
    assert vev_orbit_classification_status() == "PARTIAL"
    g = g4r_executable_registry()[G4R_ID]
    assert g["VEV_ORBIT_CLASSIFICATION"] == "PARTIAL"
    assert "generic-VEV shortcut treated as exhaustive" in g["explicit_exclusions"]


def test_lazy_enumeration_and_no_g5(tmp_path):
    g = g4r_executable_registry()[G4R_ID]
    legal, _ = g4r_metadata_legal(
        {"g4r_pack": "SU_N:3|k:0|Nf:1|D:1,0|W:none|M:1|SD:1,1|SW:none|SM:1|SO:regular_adjoint"},
        g,
    )
    assert legal is True
    bad, why = g4r_metadata_legal(
        {"g4r_pack": "SU_N:3|k:0|Nf:1|D:1,0|W:none|M:1|SD:1,1|SW:none|SM:1|SO:not_an_orbit"},
        g,
    )
    assert bad is False
    assert why == "orbit_type_not_in_classification"
    assert N_SCALAR_MAX == 1
    assert R_MAX == 1
    first = [c["candidate_hash"] for c in generate_candidates(g)]
    second = [c["candidate_hash"] for c in generate_candidates(g)]
    assert first == second
    raw = count_raw_combinations(g)
    pruned = count_pruned(g)
    all_gen = list(generate_candidates(g))
    assert pruned == 0
    assert raw == len(all_gen)
    assert raw == pruned + len(all_gen)
    assert all(c["provenance"] == "LOGICAL CORRECTION" for c in all_gen)
    parsed = parse_g4r_pack(all_gen[0]["assignment"]["g4r_pack"])
    assert "g3_pack" in parsed
    assert "orbit_type_id" in parsed
    before = (phase14b3r_artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS_R1.json").read_bytes()
    before_g4 = old_g4_checkpoint_path().read_bytes()
    engine = ClosureEngine(tmp_path, chain="g4r_only")
    assert engine.chain == [G4R_ID]
    state = engine.run_until_closure()
    assert state["G4_CORRECTED_EXECUTED"] is True
    assert state["G5_EXECUTED"] is False
    assert state["closure_status"] == "CLOSURE_REACHED"
    rep = state["version_reports"][0]
    assert rep["compatible"] > 0
    assert rep["rejected"] > 0
    assert rep["unresolved"] == 0
    assert rep["generated_candidates"] == raw
    assert (phase14b3r_artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS_R1.json").read_bytes() == before
    assert old_g4_checkpoint_path().read_bytes() == before_g4
    ckpt = engine.verify_checkpoint(G4R_ID)
    assert ckpt["parent_grammar_id"] == G3R_ID
    assert ckpt["search_bounds"]["R_MAX"] == 1
    assert ckpt["search_bounds"]["N_SCALAR_MAX"] == 1
    assert ckpt["VEV_ORBIT_CLASSIFICATION"] == "PARTIAL"
    for cand in rep.get("class_table") or []:
        if cand["status"] == "PASS":
            assert cand["KP15"] == "PASS"
            assert cand["anomaly_status"] == "DEFERRED_TO_G5"
            assert cand["massless_vectors"] == cand["dim_H"]
            assert cand["massive_vectors"] == cand["broken_dim"]
    with pytest.raises(EngineFailure) as ei:
        engine.advance_grammar("G5_ANOMALY_CONSTRAINTS", G4R_ID)
    assert ei.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure) as ej:
        ClosureEngine(tmp_path / "phys", chain="physics")
    assert ej.value.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
    with pytest.raises(EngineFailure):
        assert_target_blind({"x": "1/" + "3"})
    assert content_hash({"a": 1}) == content_hash({"a": 1})
