"""G4R orbit-closure v2 tests."""

from __future__ import annotations

from pathlib import Path

from scipy.linalg import expm
import numpy as np

from physics_lab.models.examples.phase14b4r2_model import build_phase14b4r2_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase14b0_engine import ClosureEngine, EngineFailure
from physics_lab.physics.phase14b3_g3 import R_MAX, all_dynkin
from physics_lab.physics.phase14b4r_g4 import (
    EXPECTED_OLD_G4_CHECKPOINT_HASH,
    artifact_dir as phase14b4r_artifact_dir,
    breaking_analysis_orbit,
    orbit_types,
    scalar_generators,
)
from physics_lab.physics.phase14b4r2_g4 import (
    EXPECTED_G4R2_GRAMMAR_HASH,
    EXPECTED_G6R2_RESULT_HASH,
    G4R2_ID,
    artifact_dir,
    extra_loci_numerical_evidence,
    hw_mixed_tensor,
    irrep_embedding,
    irrep_orbit_list_status,
    orbit_types_v2,
    tensor_stabilizer_dim,
)
from physics_lab.physics.phase14b5_g5 import EXPECTED_G4R_CHECKPOINT_HASH, EXPECTED_G4R_GRAMMAR_HASH
from physics_lab.physics.phase14b5_g5 import artifact_dir as phase14b5_artifact_dir
from physics_lab.physics.phase14b6_g6 import EXPECTED_G5_CHECKPOINT_HASH
from physics_lab.physics.phase14b6_g6 import artifact_dir as phase14b6_artifact_dir
from physics_lab.physics.phase14c0_known_physics import EXPECTED_G6_GRAMMAR_HASH
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_orbit_closure_preserves_frozen_parents():
    before_g4r = (phase14b4r_artifact_dir() / "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV_R1.json").read_bytes()
    before_g5 = (phase14b5_artifact_dir() / "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json").read_bytes()
    before_g6 = (phase14b6_artifact_dir() / "closure_checkpoint_G6_STRUCTURAL_GAUGE_CONSISTENCY.json").read_bytes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase14b4r2_model(signature=sig).solve()
        sci = result.metadata["phase14b4r2_analysis"]
        integ = result.metadata["phase14b4r2_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert sci["GRAMMAR_ID"] == G4R2_ID
        assert sci["GRAMMAR_HASH"] == EXPECTED_G4R2_GRAMMAR_HASH
        assert sci["old_G4_hash"] == EXPECTED_G4R_GRAMMAR_HASH
        assert sci["new_G4_hash"] == EXPECTED_G4R2_GRAMMAR_HASH
        assert sci["new_G4_hash"] != sci["old_G4_hash"]
        assert sci["old_G6_hash"] == EXPECTED_G6_GRAMMAR_HASH
        assert sci["new_G6_hash"] == EXPECTED_G6R2_RESULT_HASH
        assert sci["G4R_CLOSURE"] == "PARTIAL"
        assert sci["RESOLUTION_COUNTS"]["became_COMPLETE"] == 120
        assert sci["RESOLUTION_COUNTS"]["became_FAIL"] == 0
        assert sci["RESOLUTION_COUNTS"]["remain_PARTIAL"] == 0
        assert sci["RESOLUTION_COUNTS"]["previously_COMPLETE_unchanged"] == 359
        assert sci["NEW_G6"] == {"COMPLETE": 479, "PARTIAL": 0, "FAIL": 0}
        assert sci["R_MAX_UNCHANGED"] is True
        assert sci["GRAMMAR_EXPANDED"] is False
        assert sci["G5_anomaly_logic_changed"] is False
        assert sci["G6_local_gauge_consistency_logic_changed"] is False
        assert sci["sampling_promoted_to_COMPLETE"] is False
        assert sci["negative_tests_all_pass"] is True
        assert sci["QUANTUM_MACHINERY_STARTED"] is False
        assert sci["F2_INTRODUCED"] is False
        assert sci["YUKAWA_INTRODUCED"] is False
    assert (phase14b4r_artifact_dir() / "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV_R1.json").read_bytes() == before_g4r
    assert (phase14b5_artifact_dir() / "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json").read_bytes() == before_g5
    assert (phase14b6_artifact_dir() / "closure_checkpoint_G6_STRUCTURAL_GAUGE_CONSISTENCY.json").read_bytes() == before_g6
    import hashlib

    assert hashlib.sha256(before_g4r).hexdigest() == EXPECTED_G4R_CHECKPOINT_HASH
    assert hashlib.sha256(before_g5).hexdigest() == EXPECTED_G5_CHECKPOINT_HASH


def test_placeholders_are_not_exhaustive():
    hw = next(x for x in orbit_types(4, (0, 1, 1)) if x["orbit_type_id"] == "hw_vector")
    gen = next(x for x in orbit_types(4, (0, 1, 1)) if x["orbit_type_id"] == "generic_nonzero")
    assert hw["classification"] == "PARTIAL"
    assert gen["classification"] == "PARTIAL"
    hw2 = next(x for x in orbit_types_v2(4, (0, 1, 1)) if x["orbit_type_id"] == "hw_vector")
    gen2 = next(x for x in orbit_types_v2(4, (0, 1, 1)) if x["orbit_type_id"] == "generic_nonzero")
    assert hw2["classification"] == "COMPLETE"
    assert gen2["classification"] == "COMPLETE"
    assert hw2["list_exhaustive"] is False
    assert gen2["list_exhaustive"] is False
    assert irrep_orbit_list_status(4, (0, 1, 1)) == "PARTIAL"
    assert irrep_orbit_list_status(4, (1, 1, 0)) == "PARTIAL"
    assert irrep_orbit_list_status(4, (1, 1, 1)) == "PARTIAL"
    dim_hw = breaking_analysis_orbit(4, (0, 1, 1), 0, "none", "hw_vector")["dim_H"]
    dim_gen = breaking_analysis_orbit(4, (0, 1, 1), 0, "none", "generic_nonzero")["dim_H"]
    assert dim_hw != dim_gen
    assert extra_loci_numerical_evidence()["status"] == "PARTIAL"
    assert extra_loci_numerical_evidence()["not_promoted_to_COMPLETE"] is True


def test_orbit_stabilizer_and_conjugation_and_basis():
    br = breaking_analysis_orbit(4, (0, 1, 1), 0, "none", "hw_vector")
    assert br["dim_H"] + br["orbit_dimension"] == br["dim_G"]
    assert tensor_stabilizer_dim(hw_mixed_tensor()) == br["dim_H"]
    gens = scalar_generators(4, (0, 1, 1))
    vev = np.zeros(20, dtype=np.complex128)
    vev[0] = 1.0
    x = sum(0.02 * g for g in gens[:3])
    rotated = expm(-1j * x) @ vev
    from physics_lab.physics.phase14b4r_g4 import solve_stabilizer

    rotated_h = solve_stabilizer(list(gens), rotated / np.linalg.norm(rotated), None)["dim_H"]
    assert rotated_h == br["dim_H"]
    assert irrep_embedding((0, 1, 1))["irrep_dimension"] == 20
    assert irrep_embedding((1, 1, 1))["irrep_dimension"] == 64
    labels = list(all_dynkin(3, R_MAX))
    assert (0, 1, 1) in labels
    assert R_MAX == 1
    extra = [
        lab
        for lab in labels
        if lab
        not in {
            (0, 0, 0),
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
            (1, 0, 1),
            (0, 1, 1),
            (1, 1, 0),
            (1, 1, 1),
        }
    ]
    assert extra == []


def test_engine_does_not_auto_extend():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        try:
            ClosureEngine(Path(tmp) / "no_physics", chain="physics")
            raise AssertionError("physics chain must remain blocked")
        except EngineFailure as exc:
            assert exc.mode == "ILLEGAL_AUTOMATIC_EXTENSION"
        try:
            ClosureEngine(Path(tmp) / "no_p6", chain="p6_only")
            raise AssertionError("P6 must remain uninvented")
        except EngineFailure as exc:
            assert exc.mode == "ILLEGAL_AUTOMATIC_EXTENSION"


def test_phase14b4r2_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14b4r2.yaml"
    model = load_model(path)
    result = model.solve()
    report = validate(model, result)
    names = {item.name: item.status for item in report.checks}
    assert names["Phase 14B.4R2: pre-analysis gate"] == CheckStatus.PASS
    assert names["Phase 14B.4R2: orbit-closure coverage"] == CheckStatus.PASS
    assert names["Phase 14B.4R2: no numerical target search"] == CheckStatus.PASS
    assert names["Phase 14B.4R2: banned tokens"] == CheckStatus.PASS
    assert names["Phase 14B.4R2: experimental firewall"] == CheckStatus.PASS
    assert (artifact_dir() / "CANDIDATE_120_RESOLUTION.json").is_file()
    assert (artifact_dir() / "SUPERSEDED_PARENTS.json").is_file()
    _ = EXPECTED_OLD_G4_CHECKPOINT_HASH
