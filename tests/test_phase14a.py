"""Phase 14A: physics-anchored top-down reconstruction."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase14a_model import build_phase14a_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase12a_grammar import (
    EXPECTED_GRAMMAR_HASH_10B,
    artifact_dir as phase12a_artifact_dir,
    grammar_hash_12a,
)
from physics_lab.physics.phase13_1_low_d import artifact_dir as phase13_1_artifact_dir
from physics_lab.physics.phase14a_reconstruction import (
    AUDIT_VERSION,
    EXPECTED_12A_GRAMMAR_HASH,
    PHASE_14A_TEST_COPY_ID,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_reconstruction_preserves_history():
    before = snapshot_prior_artifact_hashes()
    before_10a = grammar_hash_10a()
    before_12a = grammar_hash_12a()
    before_131 = (phase13_1_artifact_dir() / "PHASE_13_1_SUMMARY.json").read_bytes()
    before_freeze = (phase12a_artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json").read_bytes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase14a_model(signature=sig).solve()
        sci = result.metadata["phase14a_analysis"]
        integ = result.metadata["phase14a_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["audit_summary"]
        inter = sci["intersection"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert grammar_hash_10a() == before_10a == EXPECTED_GRAMMAR_HASH_10B
        assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
        assert sci["grammar_hash_12A"] == EXPECTED_12A_GRAMMAR_HASH
        assert sci["frozen_hash_4C"] == EXPECTED_FROZEN_HASH
        assert sci["structural_inputs"] == 15
        assert sci["U1_ONLY_INSUFFICIENT"] is True
        assert sci["NEW_FIELD_REQUIRED"] is True
        assert sci["BOTTOM_UP_TOP_DOWN_INTERSECTION"] == "EMPTY"
        assert sci["BOTTOM_UP_TOP_DOWN_OBSTRUCTION"] is True
        assert inter["repair_attempted"] is False
        assert sci["UNIQUE_STRUCTURE"] == "NO"
        assert sci["UNIQUE_PARAMETER_SET"] == "NO"
        assert sci["UNIQUE_DIMENSIONLESS_QUANTITY"] == "NO"
        assert sci["unique_dimension"] == "YES_AS_TOP_DOWN_INPUT"
        assert sci["string_theory_constraints_imported"] is False
        assert sci["ranking"] is False
        assert sci["phase_14b_executed"] is False
        assert sci["new_physical_principle"] is False
        assert sci["PHASE_14A_STATUS"] == "CLOSED"
        assert sci["PHASE_14A_TEST_COPY_ID"] == PHASE_14A_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["parameter_fixes_found"] == []
        assert sci["new_parameter_free_relations"] == []
        assert set(sci["surviving_structures"]) == {
            "S1_U1xU1_partial",
            "S2_SUN_times_U1s",
            "S3_SU2_times_U1s",
            "S4_simple_SUN_to_torus",
        }
        assert all(e["provenance"] == "TOP_DOWN_INPUT" for e in sci["registry"])
        assert all(e["numerical_content_present"] is False for e in sci["registry"])
        assert sci["anomaly_space"]["solution_space_unique"] is False
        assert sci["anomaly_space"]["two_weyl_family"]["cancels"] is True
        assert sci["anomaly_space"]["four_weyl_family"]["cancels"] is True
        assert sci["u1_only_test"]["verdict"] == "U1_ONLY_INSUFFICIENT"
        assert sci["u1_only_test"]["nonabelian_uniquely_derived"] is False
        assert sci["overclaims"]["1_relabel_input_as_derived"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["6_repair_empty_intersection"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["8_treat_D4_as_bottom_up_derived"] == "REJECTED AS OVERCLAIM"
        assert sci["negative_tests_all_pass"] is True
        assert summary["experimental_inputs"] == 0
        assert summary["target_inputs"] == 0
        assert (phase13_1_artifact_dir() / "PHASE_13_1_SUMMARY.json").read_bytes() == before_131
        assert (phase12a_artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json").read_bytes() == before_freeze
        after = snapshot_prior_artifact_hashes()
        assert before["phase13_1"] == after["phase13_1"]
        assert before["phase12a"] == after["phase12a"]
        assert (artifact_dir() / "PHASE_14A_SUMMARY.json").is_file()


def test_phase14a_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase14a.yaml"
    model = load_model(path)
    report = validate(model)
    statuses = {c.name: c.status for c in report.checks}
    assert statuses["Phase 14A: pre-analysis gate"] == CheckStatus.PASS
    assert statuses["Phase 14A: reconstruction coverage"] == CheckStatus.PASS
    assert statuses["Phase 14A: no numerical target search"] == CheckStatus.PASS
    assert statuses["Phase 14A: banned tokens"] == CheckStatus.PASS
    assert statuses["Phase 14A: experimental firewall"] == CheckStatus.PASS
