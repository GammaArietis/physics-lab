"""End-to-end tests for the classical Einstein-Hilbert vacuum baseline."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import (
    EinsteinHilbertVacuumPipelineError,
    TheoryCandidateValidationError,
    load_theory_candidate,
    run_einstein_hilbert_vacuum_pipeline,
    write_einstein_hilbert_vacuum_report,
)


CANDIDATE_PATH = "schemas/examples/theory_candidate_einstein_hilbert_vacuum.json"


def test_einstein_candidate_is_explicit_classical_vacuum_baseline() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)

    assert candidate["registration"]["pipeline_ref"] == "einstein-hilbert-vacuum-v1"
    assert candidate["registration"]["selected"] is False
    assert candidate["geometry"]["spacetime"]["dimension"] == 4
    assert candidate["geometry"]["spacetime"]["manifold"] == "Schwarzschild exterior r>2GM"
    assert candidate["action"]["formulation"] == "LAGRANGIAN"
    assert candidate["quantum"]["status"] == "CLASSICAL_ONLY"
    assert candidate["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"


def test_einstein_runs_action_to_schwarzschild_curvature_ratio() -> None:
    report = run_einstein_hilbert_vacuum_pipeline(candidate_path=CANDIDATE_PATH)

    assert report["pipeline_status"] == "COMPLETE"
    assert report["action"]["instantiated"] is True
    assert report["checks"]["action_to_einstein_equation_verified"] is True
    assert report["checks"]["vacuum_equation_reduction_verified"] is True
    assert report["checks"]["ricci_flat_exterior_verified"] is True
    assert report["checks"]["kretschmann_invariant_verified"] is True

    ratio = [
        item for item in report["observables"]
        if item["name"] == "kretschmann_ratio"
    ]
    assert ratio[0]["value"] == pytest.approx(64.0)
    assert ratio[0]["free_dependencies"] == []
    assert report["controls"]["parameter_free_observable_generated"] is True
    assert all(report["controls"].values())


def test_einstein_rejects_non_schwarzschild_scope() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["geometry"]["spacetime"]["manifold"] = "R^1,3"

    with pytest.raises(EinsteinHilbertVacuumPipelineError, match="Schwarzschild exterior"):
        run_einstein_hilbert_vacuum_pipeline(candidate=candidate)


def test_einstein_rejects_interior_radius() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][2]["value"] = 1.0

    with pytest.raises(ValueError, match="outside the Schwarzschild radius"):
        run_einstein_hilbert_vacuum_pipeline(candidate=candidate)


def test_einstein_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"

    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_einstein_hilbert_vacuum_pipeline(candidate=candidate)


def test_einstein_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_einstein_hilbert_vacuum_report(tmp_path / "first.json")
    second = write_einstein_hilbert_vacuum_report(tmp_path / "second.json")

    assert json.loads(first.read_text(encoding="utf-8")) == json.loads(
        second.read_text(encoding="utf-8")
    )
    assert "/workspace/" not in first.read_text(encoding="utf-8")
    assert "/Users/" not in first.read_text(encoding="utf-8")
    assert "EXPERIMENTAL" not in first.read_text(encoding="utf-8")
