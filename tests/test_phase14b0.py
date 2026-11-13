"""Phase 14B.0 laboratory integration: freeze, dry-run, no G1 activation."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase14b0_model import build_phase14b0_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase12a_grammar import (
    EXPECTED_GRAMMAR_HASH_10B,
    artifact_dir as phase12a_artifact_dir,
    grammar_hash_12a,
)
from physics_lab.physics.phase14a_reconstruction import artifact_dir as phase14a_artifact_dir
from physics_lab.physics.phase14b0_engine import (
    AUDIT_VERSION,
    AUTHORIZED_PHYSICS_CHAIN,
    ENGINE_VERSION,
    EXPECTED_12A_GRAMMAR_HASH,
    PHASE_14B0_TEST_COPY_ID,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_engine_phase_preserves_history():
    before = snapshot_prior_artifact_hashes()
    before_10a = grammar_hash_10a()
    before_12a = grammar_hash_12a()
    before_14a = (phase14a_artifact_dir() / "PHASE_14A_SUMMARY.json").read_bytes()
    before_freeze = (phase12a_artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json").read_bytes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase14b0_model(signature=sig).solve()
        sci = result.metadata["phase14b0_analysis"]
        integ = result.metadata["phase14b0_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["audit_summary"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert grammar_hash_10a() == before_10a == EXPECTED_GRAMMAR_HASH_10B
        assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
        assert sci["ENGINE_VERSION"] == ENGINE_VERSION
        assert sci["ENGINE_STATUS"] == "READY"
        assert sci["TOP_DOWN_CLOSURE_ENGINE"] == "READY"
        assert sci["FULL_PHYSICS_GRAMMAR_EXECUTED"] is False
        assert sci["G1_ACTIVATED"] is False
        assert sci["SCIENTIFIC_STATUS"] == "NOT_ANALYZED"
        assert sci["METHOD_STATUS"] == "VERIFIED"
        assert list(sci["AUTHORIZED_EXTENSION_CHAIN"]) == list(AUTHORIZED_PHYSICS_CHAIN)
        assert sci["NEXT_AUTHORIZED_ACTION"] == "ACTIVATE G1_FERMIONIC_CHIRAL"
        assert sci["ranking"] is False
        assert sci["phase_14b1_executed"] is False
        assert sci["PHASE_14B0_STATUS"] == "CLOSED"
        assert sci["PHASE_14B0_TEST_COPY_ID"] == PHASE_14B0_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["overclaims"]["1_activate_G1_automatically"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["3_interpret_dry_run_as_physics"] == "REJECTED AS OVERCLAIM"
        assert sci["negative_tests_all_pass"] is True
        versions = {r["grammar_id"]: r for r in sci["version_reports"]}
        assert versions["DRY0_SYNTHETIC"]["closure_status"] == "EXTENSION_REQUIRED"
        assert versions["DRY1_SYNTHETIC"]["closure_status"] == "CLOSURE_REACHED"
        assert (phase14a_artifact_dir() / "PHASE_14A_SUMMARY.json").read_bytes() == before_14a
        assert (phase12a_artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json").read_bytes() == before_freeze
        after = snapshot_prior_artifact_hashes()
        assert before["phase14a"] == after["phase14a"]
        assert (artifact_dir() / "PHASE_14B0_SUMMARY.json").is_file()
        assert (artifact_dir() / "closure_checkpoint_DRY0_SYNTHETIC.json").is_file()
        assert summary["experimental_inputs"] == 0


def test_phase14b0_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14b0.yaml"
    model = load_model(path)
    report = validate(model)
    statuses = {c.name: c.status for c in report.checks}
    assert statuses["Phase 14B.0: pre-analysis gate"] == CheckStatus.PASS
    assert statuses["Phase 14B.0: engine coverage"] == CheckStatus.PASS
    assert statuses["Phase 14B.0: no numerical target search"] == CheckStatus.PASS
    assert statuses["Phase 14B.0: banned tokens"] == CheckStatus.PASS
    assert statuses["Phase 14B.0: experimental firewall"] == CheckStatus.PASS
