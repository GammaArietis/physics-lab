"""Phase 13.1: low-dimensional exception test D=1,2,3."""

from __future__ import annotations

from pathlib import Path

from physics_lab.models.examples.phase13_1_model import build_phase13_1_model
from physics_lab.models.loader import load_model
from physics_lab.physics.internal_spectrum import MOSTLY_MINUS, MOSTLY_PLUS
from physics_lab.physics.phase5c_gauging import EXPECTED_FROZEN_HASH
from physics_lab.physics.phase10a_model_grammar import grammar_hash as grammar_hash_10a
from physics_lab.physics.phase12a_grammar import (
    EXPECTED_GRAMMAR_HASH_10B,
    artifact_dir as phase12a_artifact_dir,
    grammar_hash_12a,
)
from physics_lab.physics.phase13_dimension import artifact_dir as phase13_artifact_dir
from physics_lab.physics.phase13_1_low_d import (
    AUDIT_VERSION,
    DIMENSIONS_13_1,
    EXPECTED_12A_GRAMMAR_HASH,
    PHASE_13_1_TEST_COPY_ID,
    artifact_dir,
    snapshot_prior_artifact_hashes,
)
from physics_lab.validation.checks import CheckStatus
from physics_lab.validation.validator import validate


def test_low_d_exception_preserves_history():
    before = snapshot_prior_artifact_hashes()
    before_10a = grammar_hash_10a()
    before_12a = grammar_hash_12a()
    before_13 = (phase13_artifact_dir() / "PHASE_13_SUMMARY.json").read_bytes()
    before_freeze = (phase12a_artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json").read_bytes()
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        result = build_phase13_1_model(signature=sig).solve()
        sci = result.metadata["phase13_1_analysis"]
        integ = result.metadata["phase13_1_integrity"]
        freeze = result.metadata["action_freeze"]
        summary = sci["audit_summary"]
        closure = sci["closure_results"]
        assert integ["PRE_ANALYSIS_GATE"] == "VERIFIED"
        assert freeze["fingerprint"] == EXPECTED_FROZEN_HASH
        assert grammar_hash_10a() == before_10a == EXPECTED_GRAMMAR_HASH_10B
        assert grammar_hash_12a() == before_12a == EXPECTED_12A_GRAMMAR_HASH
        assert sci["grammar_hash_12A"] == EXPECTED_12A_GRAMMAR_HASH
        assert sci["frozen_hash_4C"] == EXPECTED_FROZEN_HASH
        assert list(DIMENSIONS_13_1) == [1, 2, 3]
        assert sci["D1_status"] == "D_NOT_APPLICABLE"
        assert sci["D2_status"] == "D_IS_ALLOWED"
        assert sci["D3_status"] == "D_IS_ALLOWED"
        assert sci["lower_dimensions_allowed"] == [2, 3]
        assert sci["lower_dimensions_excluded"] == []
        assert sci["lower_dimensions_not_applicable"] == [1]
        assert sci["lower_dimensions_untested"] == []
        assert sci["NO_LOWER_DIMENSION_EXCLUSION"] is True
        assert sci["UNIQUE_DIMENSION"] == "NO"
        assert sci["DIMENSION_REQUIRED"] is False
        assert closure["MINIMAL_CONSISTENT_D"] != 4
        assert closure["DIMENSION_UNIQUELY_SELECTED"] is False
        assert sci["string_theory_constraints_imported"] is False
        assert sci["ranking"] is False
        assert sci["phase_14_executed"] is False
        assert sci["new_physical_principle"] is False
        assert sci["PHASE_13_1_STATUS"] == "CLOSED"
        assert sci["PHASE_13_1_TEST_COPY_ID"] == PHASE_13_1_TEST_COPY_ID
        assert sci["audit_version"] == AUDIT_VERSION
        assert sci["PARAMETER_FREE_CLOSURE"] == "NO"
        assert sci["UNIQUE_ACTION"] == "NO"
        assert sci["new_parameter_free_relations"] == []
        d1 = next(r for r in sci["dimension_rows"] if r["D"] == 1)
        d2 = next(r for r in sci["dimension_rows"] if r["D"] == 2)
        d3 = next(r for r in sci["dimension_rows"] if r["D"] == 3)
        assert d1["gravity"]["probe"]["R_identically_zero"] is True
        assert d1["gauge"]["NO_LOCAL_GAUGE_DOF"] is True
        assert d1["scalar"]["local_DOF"] == 1
        assert d1["internal_vs_spacetime"]["identified_with_D"] is False
        assert d2["gravity"]["status"] == "TOPOLOGICAL / NO_LOCAL_DYNAMICS"
        assert d2["gauge"]["physical_gauge_DOF"] == 0
        assert d2["gravity"]["dilaton_added"] is False
        assert d3["gravity"]["local_gravitational_DOF"] == 0
        assert d3["gravity"]["Einstein_Hilbert_dynamical"] is True
        assert d3["gauge"]["physical_gauge_DOF"] == 1
        assert d3["internal_vs_spacetime"]["identified_with_D"] is False
        assert sci["overclaims"]["1_force_D4"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["2_zero_DOF_means_inconsistent"] == "REJECTED AS OVERCLAIM"
        assert sci["overclaims"]["3_identify_H_int_with_D3"] == "REJECTED AS OVERCLAIM"
        combined = {r["D"]: r for r in sci["combined_table"]}
        assert combined[1]["combined_result"] == "D_NOT_APPLICABLE"
        assert combined[2]["combined_result"] == "D_IS_ALLOWED"
        assert combined[3]["combined_result"] == "D_IS_ALLOWED"
        assert combined[4]["Phase_13_status"] == "CONSISTENT"
        assert combined[4]["combined_result"] == "D_IS_ALLOWED"
        assert combined[16]["Phase_13_status"] == "CONSISTENT"
        assert sci["negative_tests_all_pass"] is True
        assert summary["experimental_inputs"] == 0
        assert summary["target_inputs"] == 0
        assert (phase13_artifact_dir() / "PHASE_13_SUMMARY.json").read_bytes() == before_13
        assert (phase12a_artifact_dir() / "PHASE_12A_GRAMMAR_FREEZE.json").read_bytes() == before_freeze
        after = snapshot_prior_artifact_hashes()
        assert before["phase13"] == after["phase13"]
        assert before["phase12a"] == after["phase12a"]
        assert (artifact_dir() / "PHASE_13_1_SUMMARY.json").is_file()


def test_phase13_1_yaml_and_validator():
    path = Path(__file__).resolve().parents[1] / "examples" / "phase13_1.yaml"
    model = load_model(path)
    report = validate(model)
    statuses = {c.name: c.status for c in report.checks}
    assert statuses["Phase 13.1: pre-analysis gate"] == CheckStatus.PASS
    assert statuses["Phase 13.1: low-D coverage"] == CheckStatus.PASS
    assert statuses["Phase 13.1: no numerical target search"] == CheckStatus.PASS
    assert statuses["Phase 13.1: banned tokens"] == CheckStatus.PASS
    assert statuses["Phase 13.1: experimental firewall"] == CheckStatus.PASS
