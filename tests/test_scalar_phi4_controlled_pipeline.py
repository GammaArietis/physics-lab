"""End-to-end tests for the controlled finite-lattice scalar phi-four baseline."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import ScalarPhi4PipelineError, TheoryCandidateValidationError, load_theory_candidate, run_scalar_phi4_controlled_pipeline, write_scalar_phi4_report


CANDIDATE_PATH = "schemas/examples/theory_candidate_scalar_phi4_controlled.json"


def test_phi4_candidate_declares_finite_interacting_scope() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)
    assert candidate["registration"]["pipeline_ref"] == "scalar-phi4-controlled-v1"
    assert candidate["geometry"]["spacetime"]["manifold"] == "R_t x Z_N"
    assert candidate["parameters"][1]["id"] == "coupling"
    assert candidate["quantum"]["status"] == "CLASSICAL_ONLY"


def test_phi4_runs_action_to_quartic_interaction() -> None:
    report = run_scalar_phi4_controlled_pipeline(candidate_path=CANDIDATE_PATH)
    assert report["pipeline_status"] == "COMPLETE"
    assert report["checks"]["action_to_phi4_equation_verified"] is True
    assert report["checks"]["quartic_interaction_present"] is True
    assert report["checks"]["potential_bounded_below_verified"] is True
    ratio = next(item for item in report["observables"] if item["name"] == "quartic_to_quadratic_force_ratio")
    assert ratio["value"] == pytest.approx(1 / 6)
    assert all(report["controls"].values())


def test_phi4_rejects_uncontrolled_continuum_scope() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["geometry"]["spacetime"]["manifold"] = "R_t x R"
    with pytest.raises(ScalarPhi4PipelineError, match="finite"):
        run_scalar_phi4_controlled_pipeline(candidate=candidate)


def test_phi4_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"
    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_scalar_phi4_controlled_pipeline(candidate=candidate)


def test_phi4_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_scalar_phi4_report(tmp_path / "first.json")
    second = write_scalar_phi4_report(tmp_path / "second.json")
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
