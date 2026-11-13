"""Phase 14B.5: G5 anomaly cancellation."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase14b5_model import build_phase14b5_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase12a_grammar import EXPECTED_GRAMMAR_HASH_10B, grammar_hash_12a
from physics_lab.physics.phase14b0_engine import ENGINE_VERSION, EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14b4r_g4 import artifact_dir as phase14b4r_artifact_dir
from physics_lab.physics.phase14b5_g5 import (
    AUDIT_VERSION,
    EXPECTED_G4R_CHECKPOINT_HASH,
    EXPECTED_G4R_GRAMMAR_HASH,
    G5_ID,
    PHASE_14B5_TEST_COPY_ID,
    artifact_dir,
    g4r_checkpoint_path,
    snapshot_prior_artifact_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_g5_activation_preserves_history():
    before = snapshot_prior_artifact_hashes()
    before_g4 = g4r_checkpoint_path().read_bytes()
    before_14b4r = (phase14b4r_artifact_dir() / "PHASE_14B4R_SUMMARY.json").read_bytes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase14b5_model(signature=sig).solve()
        sci = result.metadata["phase14b5_analysis"]
        integ = result.metadata["phase14b5_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert grammar_hash_10a() == EXPECTED_GRAMMAR_HASH_10B
        assert grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
        assert sci["GRAMMAR_ID"] == G5_ID
        assert sci["PARENT_GRAMMAR"] == "G4_SCALAR_MULTIPLETS_VEV_R1"
        assert sci["PARENT_GRAMMAR_HASH"] == EXPECTED_G4R_GRAMMAR_HASH
        assert sci["G4_CORRECTED_GRAMMAR_HASH"] == EXPECTED_G4R_GRAMMAR_HASH
        assert sci["G5_EXECUTED"] is True
        assert sci["G6_EXECUTED"] is False
        assert sci["G5_STATUS"] == "CLOSURE_REACHED"
        assert sci["ANOMALY_ANALYSIS_STATUS"] == "VERIFIED"
        assert sci["VECTORLIKE_STATUS"] == "UNTESTED"
        assert sci["G4_COMPATIBLE"] == 2428
        assert sci["G5_GENERATED"] == 2428
        assert sci["METADATA_PRUNED"] == 0
        assert sci["G5_UNRESOLVED"] == 0
        assert sci["G5_ANOMALY_FREE"] + sci["G5_ANOMALY_REJECTED"] == sci["G5_GENERATED"]
        assert sci["G5_ANOMALY_FREE"] < sci["G4_COMPATIBLE"]
        assert sci["ANOMALY_CONSTRAINTS_REDUCE_THE_SURVIVING_THEORY_SPACE"] is True
        assert sci["ANOMALY_CANCELLATION_DOES_NOT_SELECT_A_UNIQUE_THEORY_WITHIN_THE_DECLARED_G5_BOUNDS"] is True
        assert sci["uniqueness"]["UNIQUE_GAUGE_GROUP"] == "NO"
        assert sci["uniqueness"]["UNIQUE_ANOMALY_FREE_THEORY"] == "NO"
        assert sci["VEV_orbit_dependency"] == "NOT REQUIRED"
        assert sci["NEXT_AUTHORIZED_EXTENSION"] == "G6_STRUCTURAL_GAUGE_CONSISTENCY"
        assert sci["ranking"] is False
        assert sci["gravity_changed"] is False
        assert sci["experimental_inputs"] == 0
        assert sci["PHASE_14B5_TEST_COPY_ID"] == PHASE_14B5_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["negative_tests_all_pass"] is True
        inv = sci["parameter_inventory"]
        assert all(row["VECTORLIKE_STATUS"] == "UNTESTED" for row in inv)
        assert all(row["ANOMALY_STATUS"] == "PASS" for row in inv)
        assert all(row["VEV_magnitude"] == "NOT PROVIDED" for row in inv)
        assert g4r_checkpoint_path().read_bytes() == before_g4
        assert (phase14b4r_artifact_dir() / "PHASE_14B4R_SUMMARY.json").read_bytes() == before_14b4r
        after = snapshot_prior_artifact_hashes()
        assert before["phase14b4r"] == after["phase14b4r"]
        assert (artifact_dir() / "closure_checkpoint_G5_ANOMALY_CONSTRAINTS.json").is_file()
        _ = ENGINE_VERSION
        _ = EXPECTED_G4R_CHECKPOINT_HASH
        _ = EXPECTED_12A_GRAMMAR_HASH


def test_phase14b5_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14b5.yaml"
    model = load_model(path)
    report = validate(model)
    statuses = {c.name: c.status for c in report.checks}
    assert statuses["Phase 14B.5: pre-analysis gate"] == CheckStatus.PASS
    assert statuses["Phase 14B.5: G5 coverage"] == CheckStatus.PASS
    assert statuses["Phase 14B.5: no numerical target search"] == CheckStatus.PASS
    assert statuses["Phase 14B.5: banned tokens"] == CheckStatus.PASS
    assert statuses["Phase 14B.5: experimental firewall"] == CheckStatus.PASS
