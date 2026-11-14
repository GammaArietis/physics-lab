"""End-to-end tests for the controlled linear scalar perturbation mode."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import CosmologicalPerturbationPipelineError, TheoryCandidateValidationError, load_theory_candidate, run_cosmological_perturbations_pipeline, write_cosmological_perturbations_report


CANDIDATE_PATH = "schemas/examples/theory_candidate_cosmological_perturbations.json"


def test_cosmological_perturbation_candidate_declares_linear_scope() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)
    assert candidate["registration"]["pipeline_ref"] == "cosmological-perturbations-v1"
    assert candidate["geometry"]["spacetime"]["manifold"] == "FRW_power_law_perturbation_background"
    assert candidate["quantum"]["status"] == "CLASSICAL_ONLY"


def test_cosmological_perturbation_runs_mode_coefficients() -> None:
    report = run_cosmological_perturbations_pipeline(candidate_path=CANDIDATE_PATH)
    assert report["pipeline_status"] == "COMPLETE"
    assert report["checks"]["mukhanov_sasaki_mode_equation_verified"] is True
    assert report["checks"]["power_law_background_explicit"] is True
    assert next(item for item in report["observables"] if item["name"] == "horizon_crossing_ratio")["value"] == pytest.approx(2.0)
    assert all(report["controls"].values())


def test_cosmological_perturbation_rejects_superluminal_sound_speed() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["value"] = 1.1
    with pytest.raises(CosmologicalPerturbationPipelineError, match="sound_speed"):
        run_cosmological_perturbations_pipeline(candidate=candidate)


def test_cosmological_perturbation_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"
    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_cosmological_perturbations_pipeline(candidate=candidate)


def test_cosmological_perturbation_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_cosmological_perturbations_report(tmp_path / "first.json")
    second = write_cosmological_perturbations_report(tmp_path / "second.json")
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
