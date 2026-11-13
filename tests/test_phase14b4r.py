"""Phase 14B.4R: G4 stabilizer and mass-matrix audit."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase14b4r_model import build_phase14b4r_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase12a_grammar import EXPECTED_GRAMMAR_HASH_10B, grammar_hash_12a
from physics_lab.physics.phase14b0_engine import ENGINE_VERSION, EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14b3r_g3 import artifact_dir as phase14b3r_artifact_dir
from physics_lab.physics.phase14b4r_g4 import (
    AUDIT_VERSION,
    EXPECTED_G3R_GRAMMAR_HASH,
    EXPECTED_OLD_G4_CHECKPOINT_HASH,
    EXPECTED_OLD_G4_GRAMMAR_HASH,
    G4R_ID,
    PHASE_14B4R_TEST_COPY_ID,
    artifact_dir,
    old_g4_checkpoint_path,
    snapshot_prior_artifact_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_g4_stabilizer_audit_preserves_history():
    before = snapshot_prior_artifact_hashes()
    before_g3 = (phase14b3r_artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS_R1.json").read_bytes()
    before_g4 = old_g4_checkpoint_path().read_bytes()
    before_14b4 = (Path(old_g4_checkpoint_path().parent) / "PHASE_14B4_SUMMARY.json").read_bytes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase14b4r_model(signature=sig).solve()
        sci = result.metadata["phase14b4r_analysis"]
        integ = result.metadata["phase14b4r_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert grammar_hash_10a() == EXPECTED_GRAMMAR_HASH_10B
        assert grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
        assert sci["GRAMMAR_ID"] == G4R_ID
        assert sci["PARENT_GRAMMAR"] == "G3_FINITE_REPRESENTATIONS_R1"
        assert sci["PARENT_GRAMMAR_HASH"] == EXPECTED_G3R_GRAMMAR_HASH
        assert sci["OLD_G4_GRAMMAR_HASH"] == EXPECTED_OLD_G4_GRAMMAR_HASH
        assert sci["NEW_G4_GRAMMAR_HASH"] != EXPECTED_OLD_G4_GRAMMAR_HASH
        assert sci["G3_CORRECTED_HASH"] == EXPECTED_G3R_GRAMMAR_HASH
        assert sci["G4_CORRECTED_EXECUTED"] is True
        assert sci["G5_EXECUTED"] is False
        assert sci["G4_STATUS"] == "CLOSURE_REACHED"
        assert sci["CORRECTION_STATUS"] == "APPLIED"
        assert sci["OLD_G4_COMPATIBLE"] == 1060
        assert sci["CORRECTED_G4_COMPATIBLE"] > 0
        assert sci["UNRESOLVED"] == 0
        assert sci["METADATA_PRUNED"] == 0
        assert sci["REJECTED"] == sci["GENERATED"] - sci["CORRECTED_G4_COMPATIBLE"]
        assert sci["KP13_STATUS"] == "PASS"
        assert sci["KP15_STATUS"] == "PASS"
        assert sci["STRUCTURAL_SSB_SUPPORTED"] is True
        assert sci["KP15_STRUCTURALLY_SUPPORTED"] is True
        assert sci["VEV_ORBIT_CLASSIFICATION"] == "PARTIAL"
        assert sci["STABILIZER_MASS_MATRIX_CONSISTENCY"] == "VERIFIED"
        assert sci["G4_STABILIZER_CLASSIFICATION_PARTIAL"] is True
        assert sci["QUALITATIVE_SSB_DOES_NOT_SELECT_A_UNIQUE_BREAKING_PATTERN"] is True
        assert sci["uniqueness"]["UNIQUE_GAUGE_GROUP"] == "NO"
        assert sci["uniqueness"]["UNIQUE_BREAKING_PATTERN"] == "NO"
        assert sci["anomaly_status"] == "DEFERRED_TO_G5"
        assert sci["vacuum_existence"] == "G4 STRUCTURAL ASSUMPTION"
        assert sci["vacuum_dynamics"] == "NOT_TESTED"
        assert sci["NEXT_AUTHORIZED_EXTENSION"] == "G5_ANOMALY_CONSTRAINTS"
        assert sci["ranking"] is False
        assert sci["gravity_changed"] is False
        assert sci["experimental_inputs"] == 0
        assert sci["PHASE_14B4R_TEST_COPY_ID"] == PHASE_14B4R_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["negative_tests_all_pass"] is True
        assert sci["correction_provenance"] == "MATHEMATICAL CONSISTENCY CORRECTION"
        assert sci["OLD_G4_STATUS"] == "G4_SUPERSEDED_BY_STABILIZER_AUDIT"
        assert sci["SCALAR_SEARCH_BOUNDS"]["R_MAX"] == 1
        assert sci["SCALAR_SEARCH_BOUNDS"]["N_SCALAR_MAX"] == 1
        inv = sci["parameter_inventory"]
        assert all(row["anomaly_status"] == "DEFERRED_TO_G5" for row in inv)
        assert all(row["VEV_magnitude"] == "NOT PROVIDED" for row in inv)
        assert (phase14b3r_artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS_R1.json").read_bytes() == before_g3
        assert old_g4_checkpoint_path().read_bytes() == before_g4
        assert (old_g4_checkpoint_path().parent / "PHASE_14B4_SUMMARY.json").read_bytes() == before_14b4
        after = snapshot_prior_artifact_hashes()
        assert before["phase14b3r"] == after["phase14b3r"]
        assert before["phase14b4"] == after["phase14b4"]
        assert (artifact_dir() / "closure_checkpoint_G4_SCALAR_MULTIPLETS_VEV_R1.json").is_file()
        assert (old_g4_checkpoint_path().parent / "PHASE_14B4_SUPERSEDED_BY_STABILIZER_AUDIT.json").is_file()
        _ = ENGINE_VERSION
        _ = EXPECTED_OLD_G4_CHECKPOINT_HASH
        _ = before_14b4


def test_phase14b4r_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14b4r.yaml"
    model = load_model(path)
    report = validate(model)
    statuses = {c.name: c.status for c in report.checks}
    assert statuses["Phase 14B.4R: pre-analysis gate"] == CheckStatus.PASS
    assert statuses["Phase 14B.4R: G4 correction coverage"] == CheckStatus.PASS
    assert statuses["Phase 14B.4R: no numerical target search"] == CheckStatus.PASS
    assert statuses["Phase 14B.4R: banned tokens"] == CheckStatus.PASS
    assert statuses["Phase 14B.4R: experimental firewall"] == CheckStatus.PASS
