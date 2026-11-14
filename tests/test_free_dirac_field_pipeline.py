"""End-to-end tests for the free Dirac field baseline."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import FreeDiracFieldPipelineError, TheoryCandidateValidationError, load_theory_candidate, run_free_dirac_field_pipeline, write_free_dirac_field_report


CANDIDATE_PATH = "schemas/examples/theory_candidate_free_dirac_field.json"


def test_dirac_candidate_is_explicit_quantized_free_field() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)
    assert candidate["registration"]["pipeline_ref"] == "free-dirac-field-v1"
    assert candidate["registration"]["selected"] is False
    assert candidate["geometry"]["spacetime"]["dimension"] == 4
    assert candidate["geometry"]["spacetime"]["signature"] == "(+,-,-,-)"
    assert candidate["quantum"]["status"] == "VERIFIED"
    assert candidate["quantization"]["field_quantization_status"] == "VERIFIED"


def test_dirac_runs_action_to_fermionic_dispersion() -> None:
    report = run_free_dirac_field_pipeline(candidate_path=CANDIDATE_PATH)
    assert report["pipeline_status"] == "COMPLETE"
    assert report["checks"]["action_to_dirac_equation_verified"] is True
    assert report["checks"]["canonical_anticommutator_declared"] is True
    assert report["checks"]["dispersion_relation_verified"] is True
    ratio = next(item for item in report["observables"] if item["name"] == "mass_shell_ratio")
    assert ratio["value"] == pytest.approx(1.0)
    assert ratio["free_dependencies"] == []
    assert all(report["controls"].values())


def test_dirac_rejects_non_minkowski_scope() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["geometry"]["spacetime"]["dimension"] = 2
    with pytest.raises(FreeDiracFieldPipelineError, match="Minkowski"):
        run_free_dirac_field_pipeline(candidate=candidate)


def test_dirac_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"
    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_free_dirac_field_pipeline(candidate=candidate)


def test_dirac_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_free_dirac_field_report(tmp_path / "first.json")
    second = write_free_dirac_field_report(tmp_path / "second.json")
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
