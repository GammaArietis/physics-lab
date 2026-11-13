"""Phase 14B.3: G3 finite representation activation."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase14b3_model import build_phase14b3_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase12a_grammar import EXPECTED_GRAMMAR_HASH_10B, grammar_hash_12a
from physics_lab.physics.phase14b0_engine import ENGINE_VERSION, EXPECTED_12A_GRAMMAR_HASH
from physics_lab.physics.phase14b2_g2 import artifact_dir as phase14b2_artifact_dir
from physics_lab.physics.phase14b3_g3 import (
    AUDIT_VERSION,
    EXPECTED_G2_GRAMMAR_HASH,
    M_MAX,
    N_U1_MAX,
    PHASE_14B3_TEST_COPY_ID,
    R_MAX,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_g3_activation_preserves_history():
    before = snapshot_prior_artifact_hashes()
    before_g2 = (phase14b2_artifact_dir() / "closure_checkpoint_G2_COMPACT_NONABELIAN.json").read_bytes()
    before_14b2 = (phase14b2_artifact_dir() / "PHASE_14B2_SUMMARY.json").read_bytes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase14b3_model(signature=sig).solve()
        sci = result.metadata["phase14b3_analysis"]
        integ = result.metadata["phase14b3_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert grammar_hash_10a() == EXPECTED_GRAMMAR_HASH_10B
        assert grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
        assert sci["GRAMMAR_ID"] == "G3_FINITE_REPRESENTATIONS"
        assert sci["PARENT_GRAMMAR"] == "G2_COMPACT_NONABELIAN"
        assert sci["PARENT_GRAMMAR_HASH"] == EXPECTED_G2_GRAMMAR_HASH
        assert sci["G3_EXECUTED"] is True
        assert sci["G4_EXECUTED"] is False
        assert sci["G3_STATUS"] == "CLOSURE_REACHED"
        assert sci["G2_COMPATIBLE"] == 12
        assert sci["G3_COMPATIBLE"] == 80
        assert sci["RAW_COMBINATIONS"] == 112
        assert sci["METADATA_PRUNED"] == 32
        assert sci["GENERATED"] == 80
        assert sci["REJECTED"] == 0
        assert sci["REPRESENTATION_CATALOGUE_SIZE"] == 14
        assert sci["G2_SURVIVORS_REUSED"] == 12
        assert sci["G3_NEW_CANDIDATES_GENERATED"] == 80
        assert sci["G0_REGENERATED"] == 0
        assert sci["FINITE_REPRESENTATION_STRUCTURE_DOES_NOT_SELECT_A_UNIQUE_MATTER_CONTENT_WITHIN_THE_DECLARED_G3_BOUNDS"] is True
        assert sci["NEXT_AUTHORIZED_EXTENSION"] == "G4_SCALAR_MULTIPLETS_VEV"
        assert sci["anomaly_status"] == "DEFERRED_TO_G5"
        assert sci["SSB_STATUS"] == "DEFERRED_TO_G4"
        assert sci["uniqueness"]["UNIQUE_REPRESENTATION_CONTENT"] == "NO"
        assert sci["uniqueness"]["UNIQUE_GAUGE_GROUP"] == "NO"
        assert sci["REPRESENTATION_SEARCH_BOUNDS"]["R_MAX"] == R_MAX
        assert sci["REPRESENTATION_SEARCH_BOUNDS"]["M_MAX"] == M_MAX
        assert sci["REPRESENTATION_SEARCH_BOUNDS"]["N_U1_MAX"] == N_U1_MAX
        assert sci["ranking"] is False
        assert sci["gravity_changed"] is False
        assert sci["experimental_inputs"] == 0
        assert sci["PHASE_14B3_TEST_COPY_ID"] == PHASE_14B3_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["negative_tests_all_pass"] is True
        assert len(sci["ELIMINATED"]) == 2
        inv = sci["parameter_inventory"]
        assert all(row["anomaly_status"] == "DEFERRED_TO_G5" for row in inv)
        assert all(row["provenance"]["U1_integer_weight"] == "DERIVED GIVEN COMPACT REPRESENTATION CONVENTION" for row in inv)
        assert (phase14b2_artifact_dir() / "closure_checkpoint_G2_COMPACT_NONABELIAN.json").read_bytes() == before_g2
        assert (phase14b2_artifact_dir() / "PHASE_14B2_SUMMARY.json").read_bytes() == before_14b2
        after = snapshot_prior_artifact_hashes()
        assert before["phase14b2"] == after["phase14b2"]
        assert (artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS.json").is_file()
        assert not (phase14b2_artifact_dir() / "closure_checkpoint_G3_FINITE_REPRESENTATIONS.json").is_file()
        _ = ENGINE_VERSION


def test_phase14b3_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14b3.yaml"
    model = load_model(path)
    report = validate(model)
    statuses = {c.name: c.status for c in report.checks}
    assert statuses["Phase 14B.3: pre-analysis gate"] == CheckStatus.PASS
    assert statuses["Phase 14B.3: G3 coverage"] == CheckStatus.PASS
    assert statuses["Phase 14B.3: no numerical target search"] == CheckStatus.PASS
    assert statuses["Phase 14B.3: banned tokens"] == CheckStatus.PASS
    assert statuses["Phase 14B.3: experimental firewall"] == CheckStatus.PASS
