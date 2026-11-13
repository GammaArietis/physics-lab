"""Phase 14B.3R: G3 chirality-criterion logical correction."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase14b3r_model import build_phase14b3r_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase12a_grammar import EXPECTED_GRAMMAR_HASH_10B, grammar_hash_12a
from physics_lab.physics.phase14b0_engine import ENGINE_VERSION, EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14b2_g2 import artifact_dir as phase14b2_artifact_dir
from physics_lab.physics.phase14b3r_g3 import (
    AUDIT_VERSION,
    EXPECTED_G2_GRAMMAR_HASH,
    EXPECTED_OLD_G3_CHECKPOINT_HASH,
    EXPECTED_OLD_G3_GRAMMAR_HASH,
    G3R_ID,
    PHASE_14B3R_TEST_COPY_ID,
    artifact_dir,
    old_g3_checkpoint_path,
    snapshot_prior_artifact_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_g3_correction_preserves_history_and_restores_su2():
    before = snapshot_prior_artifact_hashes()
    before_g2 = (phase14b2_artifact_dir() / "closure_checkpoint_G2_COMPACT_NONABELIAN.json").read_bytes()
    before_g3 = old_g3_checkpoint_path().read_bytes()
    before_14b2 = (phase14b2_artifact_dir() / "PHASE_14B2_SUMMARY.json").read_bytes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase14b3r_model(signature=sig).solve()
        sci = result.metadata["phase14b3r_analysis"]
        integ = result.metadata["phase14b3r_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert grammar_hash_10a() == EXPECTED_GRAMMAR_HASH_10B
        assert grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
        assert sci["GRAMMAR_ID"] == G3R_ID
        assert sci["PARENT_GRAMMAR"] == "G2_COMPACT_NONABELIAN"
        assert sci["G2_GRAMMAR_HASH"] == EXPECTED_G2_GRAMMAR_HASH
        assert sci["OLD_G3_GRAMMAR_HASH"] == EXPECTED_OLD_G3_GRAMMAR_HASH
        assert sci["NEW_G3_GRAMMAR_HASH"] != EXPECTED_OLD_G3_GRAMMAR_HASH
        assert sci["G3_CORRECTED_EXECUTED"] is True
        assert sci["G4_EXECUTED"] is False
        assert sci["G3_STATUS"] == "CLOSURE_REACHED"
        assert sci["CORRECTION_STATUS"] == "APPLIED"
        assert sci["OLD_G3_COMPATIBLE"] == 80
        assert sci["CORRECTED_G3_COMPATIBLE"] == 112
        assert len(sci["RESTORED_CLASSES"]) == 32
        assert sci["REMOVED_CLASSES"] == []
        assert sci["UNRESOLVED"] == 0
        assert sci["RAW_COMBINATIONS"] == 112
        assert sci["METADATA_PRUNED"] == 0
        assert sci["GENERATED"] == 112
        assert sci["REJECTED"] == 0
        assert sci["CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION"] == "NO"
        assert sci["REPRESENTATION_REALITY_TYPE"] == "INDEPENDENT PROPERTY"
        assert sci["anomaly_status"] == "DEFERRED_TO_G5"
        assert sci["SSB_STATUS"] == "DEFERRED_TO_G4"
        assert sci["uniqueness"]["UNIQUE_REPRESENTATION_CONTENT"] == "NO"
        assert sci["uniqueness"]["UNIQUE_GAUGE_GROUP"] == "NO"
        assert sci["NEXT_AUTHORIZED_EXTENSION"] == "G4_SCALAR_MULTIPLETS_VEV"
        assert sci["ranking"] is False
        assert sci["gravity_changed"] is False
        assert sci["experimental_inputs"] == 0
        assert sci["PHASE_14B3R_TEST_COPY_ID"] == PHASE_14B3R_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["negative_tests_all_pass"] is True
        assert sci["correction_provenance"] == "LOGICAL CORRECTION"
        assert sci["OLD_G3_STATUS"] == "SUPERSEDED_BY_LOGICAL_CORRECTION"
        assert "SU_N:2|k:0|Nf:1|D:1|W:none|M:1" in sci["SU2_RESTORED_CLASSES"]
        inv = sci["parameter_inventory"]
        assert all(row["anomaly_status"] == "DEFERRED_TO_G5" for row in inv)
        assert all(row["vectorlike_status"] == "UNTESTED" for row in inv)
        assert all(row["lorentz_chirality"] == "Weyl" for row in inv)
        assert all(row["CHIRALITY_REQUIRES_COMPLEX_REPRESENTATION"] == "NO" for row in inv)
        assert old_g3_checkpoint_path().read_bytes() == before_g3
        assert (phase14b2_artifact_dir() / "closure_checkpoint_G2_COMPACT_NONABELIAN.json").read_bytes() == before_g2
        assert (phase14b2_artifact_dir() / "PHASE_14B2_SUMMARY.json").read_bytes() == before_14b2
        after = snapshot_prior_artifact_hashes()
        assert before["phase14b2"] == after["phase14b2"]
        assert before["phase14b3"]["closure_checkpoint_G3_FINITE_REPRESENTATIONS.json"] == after["phase14b3"]["closure_checkpoint_G3_FINITE_REPRESENTATIONS.json"]
        assert (artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS_R1.json").is_file()
        assert not (phase14b2_artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS_R1.json").is_file()
        _ = ENGINE_VERSION
        _ = EXPECTED_OLD_G3_CHECKPOINT_HASH


def test_phase14b3r_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14b3r.yaml"
    model = load_model(path)
    report = validate(model)
    statuses = {c.name: c.status for c in report.checks}
    assert statuses["Phase 14B.3R: pre-analysis gate"] == CheckStatus.PASS
    assert statuses["Phase 14B.3R: G3 correction coverage"] == CheckStatus.PASS
    assert statuses["Phase 14B.3R: no numerical target search"] == CheckStatus.PASS
    assert statuses["Phase 14B.3R: banned tokens"] == CheckStatus.PASS
    assert statuses["Phase 14B.3R: experimental firewall"] == CheckStatus.PASS
