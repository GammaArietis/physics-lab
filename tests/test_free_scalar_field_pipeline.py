"""End-to-end tests for the known-physics free scalar field baseline."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import (
    TheoryCandidateValidationError,
    load_theory_candidate,
    run_free_scalar_field_pipeline,
    write_free_scalar_field_report,
)


CANDIDATE_PATH = "schemas/examples/theory_candidate_free_scalar_field.json"


def test_free_scalar_candidate_is_explicit_quantum_field_baseline() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)

    assert candidate["registration"]["pipeline_ref"] == "free-scalar-field-v1"
    assert candidate["registration"]["selected"] is False
    assert candidate["geometry"]["spacetime"]["dimension"] == 2
    assert candidate["geometry"]["spacetime"]["manifold"] == "R_t x S1_L"
    assert candidate["quantization"]["scope"] == "QUANTUM_FIELD"
    assert candidate["quantization"]["field_quantization_status"] == "VERIFIED"
    assert candidate["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"


def test_free_scalar_runs_action_to_fock_vacuum_and_parameter_free_ratio() -> None:
    report = run_free_scalar_field_pipeline(candidate_path=CANDIDATE_PATH)

    assert report["pipeline_status"] == "COMPLETE"
    assert report["action"]["instantiated"] is True
    assert report["checks"]["euler_lagrange_equation_verified"] is True
    assert report["checks"]["legendre_transform_verified"] is True
    assert report["checks"]["canonical_field_commutator_declared"] is True
    assert report["checks"]["parameter_free_dispersion_ratio_verified"] is True
    ratios = [item for item in report["observables"] if item["name"] == "dispersion_ratio[3]"]
    assert ratios[0]["value"] == pytest.approx(9.0)
    assert ratios[0]["free_dependencies"] == []
    assert ratios[0]["status"] == "PREDICTION (DERIVED, no free parameters)"
    assert report["vacuum"]["selected_state"] == "all mode occupations n_k=0"
    assert report["quantization"]["field_quantization"] == "VERIFIED_IN_FREE_FIELD_SCOPE"
    assert all(report["controls"].values())


def test_free_scalar_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"
    candidate["authorization"]["empirical_comparison"] = "AUTHORIZED"
    candidate["authorization"]["authorization_ref"] = "comparison-only"

    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_free_scalar_field_pipeline(candidate=candidate)


def test_free_scalar_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_free_scalar_field_report(tmp_path / "first.json")
    second = write_free_scalar_field_report(tmp_path / "second.json")

    assert json.loads(first.read_text(encoding="utf-8")) == json.loads(
        second.read_text(encoding="utf-8")
    )
    assert "/workspace/" not in first.read_text(encoding="utf-8")
    assert "/Users/" not in first.read_text(encoding="utf-8")
    assert "EXPERIMENTAL" not in first.read_text(encoding="utf-8")
