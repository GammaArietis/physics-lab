"""End-to-end tests for the classical Maxwell vacuum baseline."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import (
    MaxwellVacuumPipelineError,
    TheoryCandidateValidationError,
    load_theory_candidate,
    run_maxwell_vacuum_pipeline,
    write_maxwell_vacuum_report,
)


CANDIDATE_PATH = "schemas/examples/theory_candidate_maxwell_vacuum.json"


def test_maxwell_candidate_is_explicit_classical_vacuum_baseline() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)

    assert candidate["registration"]["pipeline_ref"] == "maxwell-vacuum-v1"
    assert candidate["registration"]["selected"] is False
    assert candidate["geometry"]["spacetime"]["dimension"] == 4
    assert candidate["geometry"]["internal_space"]["group"] == "U(1)"
    assert candidate["quantum"]["status"] == "CLASSICAL_ONLY"
    assert candidate["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"


def test_maxwell_runs_action_to_waves_polarizations_and_ratio() -> None:
    report = run_maxwell_vacuum_pipeline(candidate_path=CANDIDATE_PATH)

    assert report["pipeline_status"] == "COMPLETE"
    assert report["action"]["instantiated"] is True
    assert report["checks"]["source_free_field_equation_declared"] is True
    assert report["checks"]["gauge_invariance_declared"] is True
    assert report["checks"]["dispersion_relation_verified"] is True
    assert report["checks"]["two_physical_polarizations_verified"] is True

    ratios = [
        item for item in report["observables"]
        if item["name"] == "dispersion_ratio[transverse_x]"
    ]
    assert ratios[0]["value"] == pytest.approx(1.0)
    assert ratios[0]["free_dependencies"] == []
    assert report["controls"]["parameter_free_observable_generated"] is True
    assert all(report["controls"].values())


def test_maxwell_exposes_only_two_transverse_modes() -> None:
    report = run_maxwell_vacuum_pipeline(candidate_path=CANDIDATE_PATH)

    assert [mode["polarization"] for mode in report["modes"]] == [
        "transverse_x",
        "transverse_y",
    ]
    assert all(mode["transverse"] for mode in report["modes"])
    assert report["observables"][-1]["value"] == 2


def test_maxwell_rejects_non_minkowski_scope() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["geometry"]["spacetime"]["dimension"] = 3

    with pytest.raises(MaxwellVacuumPipelineError, match="four-dimensional"):
        run_maxwell_vacuum_pipeline(candidate=candidate)


def test_maxwell_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"

    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_maxwell_vacuum_pipeline(candidate=candidate)


def test_maxwell_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_maxwell_vacuum_report(tmp_path / "first.json")
    second = write_maxwell_vacuum_report(tmp_path / "second.json")

    assert json.loads(first.read_text(encoding="utf-8")) == json.loads(
        second.read_text(encoding="utf-8")
    )
    assert "/workspace/" not in first.read_text(encoding="utf-8")
    assert "/Users/" not in first.read_text(encoding="utf-8")
    assert "EXPERIMENTAL" not in first.read_text(encoding="utf-8")
