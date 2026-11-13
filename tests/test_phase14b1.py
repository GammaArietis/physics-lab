"""Phase 14B.1: G1 fermionic chiral activation."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase14b1_model import build_phase14b1_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase12a_grammar import EXPECTED_GRAMMAR_HASH_10B, grammar_hash_12a
from physics_lab.physics.phase14b0_engine import ENGINE_VERSION, EXPECTED_12A_GRAMMAR_HASH, artifact_dir as phase14b0_artifact_dir
from physics_lab.physics.phase14b1_g1 import (
    AUDIT_VERSION,
    N_FERMION_SEARCH_LIMIT,
    PHASE_14B1_TEST_COPY_ID,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_g1_activation_preserves_history():
    before = snapshot_prior_artifact_hashes()
    before_14b0 = (phase14b0_artifact_dir() / "PHASE_14B0_SUMMARY.json").read_bytes()
    before_dry = (phase14b0_artifact_dir() / "closure_checkpoint_DRY0_SYNTHETIC.json").read_bytes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase14b1_model(signature=sig).solve()
        sci = result.metadata["phase14b1_analysis"]
        integ = result.metadata["phase14b1_integrity"]
        freeze = result.metadata["action_freeze"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert grammar_hash_10a() == EXPECTED_GRAMMAR_HASH_10B
        assert grammar_hash_12a() == EXPECTED_12A_GRAMMAR_HASH
        assert sci["GRAMMAR_ID"] == "G1_FERMIONIC_CHIRAL"
        assert sci["PARENT_GRAMMAR"] == "G0_BASELINE"
        assert sci["G1_EXECUTED"] is True
        assert sci["G2_EXECUTED"] is False
        assert sci["G1_STATUS"] == "CLOSURE_REACHED"
        assert sci["G0_COMPATIBLE"] == 0
        assert sci["G1_COMPATIBLE"] == 2
        assert sci["METADATA_PRUNED"] == 8
        assert sci["GENERATED"] == 8
        assert sci["REJECTED"] == 6
        assert sci["TOP_DOWN_COMPATIBLE"] == 2
        assert sci["FERMIONIC_GRAMMAR_REDUCES_PREVIOUS_EMPTY_INTERSECTION"] is True
        assert sci["CHIRAL_FERMION_CONTENT_ALONE_DOES_NOT_SELECT_UNIQUE_THEORY"] is True
        assert sci["NEXT_AUTHORIZED_EXTENSION"] == "G2_COMPACT_NONABELIAN"
        assert sci["audit_summary"]["G1_REQUIRES_NONABELIAN"] is False
        assert sci["audit_summary"]["U1_ONLY_SUPPORTS_CHIRAL_FERMIONS_STRUCTURALLY"] is True
        assert list(sci["N_fermion_search_limit"]) == list(N_FERMION_SEARCH_LIMIT)
        assert sci["ranking"] is False
        assert sci["gravity_changed"] is False
        assert sci["experimental_inputs"] == 0
        assert sci["PHASE_14B1_TEST_COPY_ID"] == PHASE_14B1_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["negative_tests_all_pass"] is True
        inv = sci["parameter_inventory"]
        assert all("q_" in row["symbolic_U1_charges"] for row in inv)
        assert all(row["provenance"]["anomaly_cancellation"] == "UNTESTED IN G1" for row in inv)
        assert (phase14b0_artifact_dir() / "PHASE_14B0_SUMMARY.json").read_bytes() == before_14b0
        assert (phase14b0_artifact_dir() / "closure_checkpoint_DRY0_SYNTHETIC.json").read_bytes() == before_dry
        after = snapshot_prior_artifact_hashes()
        assert before["phase14b0"] == after["phase14b0"]
        assert (artifact_dir() / "closure_checkpoint_G1_FERMIONIC_CHIRAL.json").is_file()
        assert (artifact_dir() / "closure_checkpoint_G0_BASELINE.json").is_file()
        _ = ENGINE_VERSION


def test_phase14b1_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14b1.yaml"
    model = load_model(path)
    report = validate(model)
    statuses = {c.name: c.status for c in report.checks}
    assert statuses["Phase 14B.1: pre-analysis gate"] == CheckStatus.PASS
    assert statuses["Phase 14B.1: G1 coverage"] == CheckStatus.PASS
    assert statuses["Phase 14B.1: no numerical target search"] == CheckStatus.PASS
    assert statuses["Phase 14B.1: banned tokens"] == CheckStatus.PASS
    assert statuses["Phase 14B.1: experimental firewall"] == CheckStatus.PASS
