"""End-to-end tests for the known-physics harmonic oscillator baseline."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import (
    HarmonicOscillatorPipelineError,
    TheoryCandidateValidationError,
    load_theory_candidate,
    run_harmonic_oscillator_pipeline,
    write_harmonic_oscillator_report,
)


CANDIDATE_PATH = "schemas/examples/theory_candidate_quantum_harmonic_oscillator.json"


def test_harmonic_oscillator_candidate_is_explicit_known_physics_baseline() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)

    assert candidate["registration"]["pipeline_ref"] == "quantum-harmonic-oscillator-v1"
    assert candidate["registration"]["selected"] is False
    assert candidate["action"]["formulation"] == "LAGRANGIAN"
    assert candidate["vacuum"]["selection_status"] == "SELECTED"
    assert candidate["quantization"]["scope"] == "QUANTUM_MECHANICS"
    assert candidate["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"


def test_harmonic_oscillator_runs_action_to_parameter_free_ratio() -> None:
    report = run_harmonic_oscillator_pipeline(candidate_path=CANDIDATE_PATH)

    assert report["pipeline_status"] == "COMPLETE"
    assert report["action"]["instantiated"] is True
    assert report["checks"]["euler_lagrange_equation_verified"] is True
    assert report["checks"]["legendre_transform_verified"] is True
    assert report["checks"]["parameter_free_gap_ratio_verified"] is True
    ratios = [item for item in report["observables"] if item["name"] == "gap_ratio[2]"]
    assert ratios[0]["value"] == pytest.approx(2.0)
    assert ratios[0]["free_dependencies"] == []
    assert ratios[0]["status"] == "PREDICTION (DERIVED, no free parameters)"
    assert report["vacuum"]["selected_state"] == "n=0"
    assert report["controls"]["field_quantization_not_claimed"] is True
    assert all(report["controls"].values())


def test_harmonic_oscillator_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"
    candidate["authorization"]["empirical_comparison"] = "AUTHORIZED"
    candidate["authorization"]["authorization_ref"] = "comparison-only"

    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_harmonic_oscillator_pipeline(candidate=candidate)


def test_harmonic_oscillator_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_harmonic_oscillator_report(tmp_path / "first.json")
    second = write_harmonic_oscillator_report(tmp_path / "second.json")

    assert json.loads(first.read_text(encoding="utf-8")) == json.loads(
        second.read_text(encoding="utf-8")
    )
    assert "/workspace/" not in first.read_text(encoding="utf-8")
    assert "/Users/" not in first.read_text(encoding="utf-8")
    assert "EXPERIMENTAL" not in first.read_text(encoding="utf-8")
