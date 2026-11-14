"""End-to-end tests for the quantized free Maxwell U(1) baseline."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import QuantizedMaxwellPipelineError, TheoryCandidateValidationError, load_theory_candidate, run_quantized_maxwell_pipeline, write_quantized_maxwell_report


CANDIDATE_PATH = "schemas/examples/theory_candidate_quantized_maxwell_u1.json"


def test_quantized_maxwell_candidate_is_explicit_u1_field_quantization() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)
    assert candidate["registration"]["pipeline_ref"] == "quantized-maxwell-u1-v1"
    assert candidate["registration"]["selected"] is False
    assert candidate["geometry"]["spacetime"]["signature"] == "(+,-,-,-)"
    assert candidate["geometry"]["internal_space"]["group"] == "U(1)"
    assert candidate["quantum"]["status"] == "VERIFIED"
    assert candidate["quantization"]["field_quantization_status"] == "VERIFIED"


def test_quantized_maxwell_runs_to_photon_modes_and_vacuum() -> None:
    report = run_quantized_maxwell_pipeline(candidate_path=CANDIDATE_PATH)
    assert report["pipeline_status"] == "COMPLETE"
    assert report["checks"]["canonical_quantization_declared"] is True
    assert report["checks"]["fock_vacuum_verified"] is True
    assert report["checks"]["two_physical_polarizations_verified"] is True
    ratio = next(item for item in report["observables"] if item["name"] == "photon_dispersion_ratio")
    count = next(item for item in report["observables"] if item["name"] == "physical_polarization_count")
    assert ratio["value"] == pytest.approx(1.0)
    assert ratio["free_dependencies"] == []
    assert count["value"] == 2
    assert all(report["controls"].values())


def test_quantized_maxwell_rejects_non_u1_scope() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["geometry"]["internal_space"]["group"] = "SU(2)"
    with pytest.raises(QuantizedMaxwellPipelineError, match="U\\(1\\)"):
        run_quantized_maxwell_pipeline(candidate=candidate)


def test_quantized_maxwell_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"
    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_quantized_maxwell_pipeline(candidate=candidate)


def test_quantized_maxwell_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_quantized_maxwell_report(tmp_path / "first.json")
    second = write_quantized_maxwell_report(tmp_path / "second.json")
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
