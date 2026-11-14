"""End-to-end tests for the spin-only Pauli spin-1/2 baseline."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import (
    PauliSpinHalfPipelineError,
    TheoryCandidateValidationError,
    load_theory_candidate,
    run_pauli_spin_half_pipeline,
    write_pauli_spin_half_report,
)


CANDIDATE_PATH = "schemas/examples/theory_candidate_pauli_spin_half.json"


def test_pauli_candidate_is_explicit_spin_only_baseline() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)

    assert candidate["registration"]["pipeline_ref"] == "pauli-spin-half-v1"
    assert candidate["registration"]["selected"] is False
    assert candidate["geometry"]["internal_space"]["dimension"] == 2
    assert candidate["quantization"]["scope"] == "QUANTUM_MECHANICS"
    assert candidate["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"
    assert candidate["vacuum"]["status"] == "NOT_APPLICABLE"


def test_pauli_runs_algebra_to_spectrum_and_normalized_splitting() -> None:
    report = run_pauli_spin_half_pipeline(candidate_path=CANDIDATE_PATH)

    assert report["pipeline_status"] == "COMPLETE"
    assert report["action"]["instantiated"] is True
    assert report["checks"]["pauli_square_identity_verified"] is True
    assert report["checks"]["pauli_commutator_verified"] is True
    assert report["checks"]["hamiltonian_spectrum_verified"] is True
    assert report["checks"]["parameter_free_splitting_verified"] is True

    splitting = [
        item for item in report["observables"]
        if item["name"] == "dimensionless_spin_splitting"
    ]
    assert splitting[0]["value"] == pytest.approx(1.0)
    assert splitting[0]["free_dependencies"] == []
    assert report["spectrum"][0]["quantum_numbers"]["spin_projection"] == -1
    assert report["spectrum"][1]["quantum_numbers"]["spin_projection"] == 1
    assert all(report["controls"].values())


def test_pauli_rejects_spatial_scope_change() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["geometry"]["spacetime"]["dimension"] = 3

    with pytest.raises(PauliSpinHalfPipelineError, match="time-only"):
        run_pauli_spin_half_pipeline(candidate=candidate)


def test_pauli_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"

    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_pauli_spin_half_pipeline(candidate=candidate)


def test_pauli_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_pauli_spin_half_report(tmp_path / "first.json")
    second = write_pauli_spin_half_report(tmp_path / "second.json")

    assert json.loads(first.read_text(encoding="utf-8")) == json.loads(
        second.read_text(encoding="utf-8")
    )
    assert "/workspace/" not in first.read_text(encoding="utf-8")
    assert "/Users/" not in first.read_text(encoding="utf-8")
    assert "EXPERIMENTAL" not in first.read_text(encoding="utf-8")
