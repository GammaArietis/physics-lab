"""End-to-end tests for the controlled classical SU(2) Yang-Mills baseline."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import ClassicalYangMillsPipelineError, TheoryCandidateValidationError, load_theory_candidate, run_classical_yang_mills_pipeline, write_classical_yang_mills_report


CANDIDATE_PATH = "schemas/examples/theory_candidate_classical_yang_mills.json"


def test_yang_mills_candidate_declares_su2_classical_scope() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)
    assert candidate["registration"]["pipeline_ref"] == "classical-yang-mills-v1"
    assert candidate["geometry"]["internal_space"]["group"] == "SU(2)"
    assert candidate["quantum"]["status"] == "CLASSICAL_ONLY"


def test_yang_mills_runs_nonabelian_action_to_observable() -> None:
    report = run_classical_yang_mills_pipeline(candidate_path=CANDIDATE_PATH)
    assert report["pipeline_status"] == "COMPLETE"
    assert report["checks"]["su2_structure_constants_verified"] is True
    assert report["checks"]["nonabelian_field_strength_verified"] is True
    assert report["checks"]["bianchi_identity_declared"] is True
    ratio = next(item for item in report["observables"] if item["name"] == "normalized_nonabelian_commutator")
    assert ratio["value"] == pytest.approx(1.0)
    assert all(report["controls"].values())


def test_yang_mills_rejects_abelian_scope() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["geometry"]["internal_space"]["group"] = "U(1)"
    with pytest.raises(ClassicalYangMillsPipelineError, match="SU\\(2\\)"):
        run_classical_yang_mills_pipeline(candidate=candidate)


def test_yang_mills_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"
    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_classical_yang_mills_pipeline(candidate=candidate)


def test_yang_mills_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_classical_yang_mills_report(tmp_path / "first.json")
    second = write_classical_yang_mills_report(tmp_path / "second.json")
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
