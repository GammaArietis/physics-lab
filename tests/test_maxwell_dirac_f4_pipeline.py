"""Tests for the structural Maxwell–Dirac F^4 EFT pilot."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry.maxwell_dirac_f4_pipeline import (
    MaxwellDiracF4PipelineError,
    run_maxwell_dirac_f4_pipeline,
    write_maxwell_dirac_f4_report,
)
from physics_lab.registry.theory_candidate import TheoryCandidateValidationError, load_theory_candidate


CANDIDATE_PATH = "schemas/examples/theory_candidate_maxwell_dirac_f4.json"


def test_maxwell_dirac_f4_candidate_is_explicit_and_unselected() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)
    assert candidate["registration"]["pipeline_ref"] == "maxwell-dirac-f4-v1"
    assert candidate["registration"]["selected"] is False
    assert candidate["geometry"]["spacetime"]["dimension"] == 4
    assert candidate["geometry"]["internal_space"]["group"] == "U(1)"
    assert {item["id"] for item in candidate["parameters"]} == {"c1", "c2", "lambda-scale"}


def test_structural_pilot_registers_observables_and_stays_underdetermined() -> None:
    report = run_maxwell_dirac_f4_pipeline(candidate_path=CANDIDATE_PATH)
    assert report["pipeline_status"] == "COMPLETE"
    assert report["candidate_status"] == "UNDERDETERMINED"
    assert report["controls"]["u1_gauge_invariance_verified"] is True
    assert report["controls"]["operator_mass_dimension_verified"] is True
    assert report["controls"]["alpha_not_used_as_parameter"] is True
    assert report["controls"]["parameter_free_observable_generated"] is False
    assert len(report["observables"]) == 3
    assert all(item["status"] == "UNDERDETERMINED" for item in report["observables"])


def test_pilot_rejects_alpha_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"].append(
        {
            "id": "alpha",
            "symbol": "alpha",
            "role": "COUPLING",
            "status": "UNRESOLVED",
            "provenance": "NOT_DEFINED",
            "value": None,
            "unit": "dimensionless",
            "formula": None,
            "dependencies": [],
        }
    )
    with pytest.raises(MaxwellDiracF4PipelineError, match="alpha"):
        run_maxwell_dirac_f4_pipeline(candidate=candidate)


def test_pilot_rejects_resolved_wilson_coefficient() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["status"] = "FIXED"
    candidate["parameters"][0]["value"] = 1.0
    with pytest.raises(MaxwellDiracF4PipelineError, match="c1"):
        run_maxwell_dirac_f4_pipeline(candidate=candidate)


def test_pilot_rejects_experimental_input() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"
    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_maxwell_dirac_f4_pipeline(candidate=candidate)


def test_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_maxwell_dirac_f4_report(tmp_path / "first.json")
    second = write_maxwell_dirac_f4_report(tmp_path / "second.json")
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
