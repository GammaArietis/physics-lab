"""End-to-end tests for the static Newtonian gravity baseline."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import (
    NewtonianGravityPipelineError,
    TheoryCandidateValidationError,
    load_theory_candidate,
    run_newtonian_gravity_pipeline,
    write_newtonian_gravity_report,
)


CANDIDATE_PATH = "schemas/examples/theory_candidate_newtonian_gravity.json"


def test_newtonian_candidate_is_explicit_classical_field_baseline() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)

    assert candidate["registration"]["pipeline_ref"] == "newtonian-gravity-v1"
    assert candidate["registration"]["selected"] is False
    assert candidate["geometry"]["spacetime"]["dimension"] == 3
    assert candidate["geometry"]["spacetime"]["manifold"] == "R_t x R^3"
    assert candidate["quantum"]["status"] == "CLASSICAL_ONLY"
    assert candidate["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"


def test_newtonian_runs_action_to_poisson_field_and_inverse_square_ratio() -> None:
    report = run_newtonian_gravity_pipeline(candidate_path=CANDIDATE_PATH)

    assert report["pipeline_status"] == "COMPLETE"
    assert report["action"]["instantiated"] is True
    assert report["checks"]["action_to_poisson_equation_verified"] is True
    assert report["checks"]["spherical_point_source_solution_verified"] is True
    assert report["checks"]["inverse_square_acceleration_verified"] is True

    ratio = [
        item for item in report["observables"]
        if item["name"] == "acceleration_ratio"
    ]
    assert ratio[0]["value"] == pytest.approx(0.25)
    assert ratio[0]["free_dependencies"] == []
    assert report["controls"]["parameter_free_observable_generated"] is True
    assert all(report["controls"].values())


def test_newtonian_potential_and_acceleration_are_attractive() -> None:
    report = run_newtonian_gravity_pipeline(candidate_path=CANDIDATE_PATH)

    assert report["observables"][0]["value"] < 0
    assert report["observables"][1]["value"] > 0
    assert report["checks"]["attractive_acceleration_verified"] is True


def test_newtonian_rejects_relativistic_geometry_scope() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["geometry"]["spacetime"]["dimension"] = 4

    with pytest.raises(NewtonianGravityPipelineError, match="absolute time"):
        run_newtonian_gravity_pipeline(candidate=candidate)


def test_newtonian_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"

    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_newtonian_gravity_pipeline(candidate=candidate)


def test_newtonian_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_newtonian_gravity_report(tmp_path / "first.json")
    second = write_newtonian_gravity_report(tmp_path / "second.json")

    assert json.loads(first.read_text(encoding="utf-8")) == json.loads(
        second.read_text(encoding="utf-8")
    )
    assert "/workspace/" not in first.read_text(encoding="utf-8")
    assert "/Users/" not in first.read_text(encoding="utf-8")
    assert "EXPERIMENTAL" not in first.read_text(encoding="utf-8")
