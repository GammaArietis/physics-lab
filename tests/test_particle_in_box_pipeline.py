"""End-to-end tests for the particle-in-a-box known-physics baseline."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import (
    ParticleInBoxPipelineError,
    TheoryCandidateValidationError,
    load_theory_candidate,
    run_particle_in_box_pipeline,
    write_particle_in_box_report,
)


CANDIDATE_PATH = "schemas/examples/theory_candidate_particle_in_box.json"


def test_particle_in_box_candidate_is_explicit_baseline() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)

    assert candidate["registration"]["pipeline_ref"] == "particle-in-box-v1"
    assert candidate["registration"]["selected"] is False
    assert candidate["geometry"]["spacetime"]["boundary_conditions"] == [
        "psi(0)=0",
        "psi(L)=0",
    ]
    assert candidate["quantization"]["scope"] == "QUANTUM_MECHANICS"
    assert candidate["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"


def test_particle_in_box_runs_action_to_parameter_free_ratio() -> None:
    report = run_particle_in_box_pipeline(candidate_path=CANDIDATE_PATH)

    assert report["pipeline_status"] == "COMPLETE"
    assert report["action"]["instantiated"] is True
    assert report["checks"]["n_squared_spectrum_verified"] is True
    assert report["checks"]["parameter_free_gap_ratio_verified"] is True
    ratios = [item for item in report["observables"] if item["name"] == "gap_ratio[3]"]
    assert ratios[0]["value"] == pytest.approx(8.0 / 3.0)
    assert ratios[0]["free_dependencies"] == []
    assert ratios[0]["status"] == "PREDICTION (DERIVED, no free parameters)"
    assert report["vacuum"]["selected_state"] == "n=1"
    assert all(report["controls"].values())


def test_particle_in_box_rejects_boundary_scope_change() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["geometry"]["spacetime"]["boundary_conditions"] = ["periodic"]

    with pytest.raises(ParticleInBoxPipelineError, match="Dirichlet"):
        run_particle_in_box_pipeline(candidate=candidate)


def test_particle_in_box_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"

    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_particle_in_box_pipeline(candidate=candidate)


def test_particle_in_box_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_particle_in_box_report(tmp_path / "first.json")
    second = write_particle_in_box_report(tmp_path / "second.json")

    assert json.loads(first.read_text(encoding="utf-8")) == json.loads(
        second.read_text(encoding="utf-8")
    )
    assert "/workspace/" not in first.read_text(encoding="utf-8")
    assert "/Users/" not in first.read_text(encoding="utf-8")
    assert "EXPERIMENTAL" not in first.read_text(encoding="utf-8")
