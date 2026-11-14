"""End-to-end tests for the structural Standard Model baseline."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import StandardModelStructuralPipelineError, TheoryCandidateValidationError, load_theory_candidate, run_standard_model_structural_pipeline, write_standard_model_structural_report


CANDIDATE_PATH = "schemas/examples/theory_candidate_standard_model_structural.json"


def test_standard_model_candidate_declares_structural_scope() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)
    assert candidate["registration"]["pipeline_ref"] == "standard-model-structural-v1"
    assert candidate["geometry"]["internal_space"]["group"] == "SU(3)_C x SU(2)_L x U(1)_Y"
    assert candidate["quantum"]["status"] == "PARTIAL"


def test_standard_model_runs_counts_and_anomaly_checks() -> None:
    report = run_standard_model_structural_pipeline(candidate_path=CANDIDATE_PATH)
    assert report["pipeline_status"] == "COMPLETE"
    assert report["checks"]["gauge_group_verified"] is True
    assert report["checks"]["perturbative_anomalies_cancelled"] is True
    assert report["checks"]["su2_witten_anomaly_absent"] is True
    assert next(item for item in report["observables"] if item["name"] == "gauge_boson_count")["value"] == 12
    assert report["derivation"]["anomaly_coefficients"] == {
        "SU(3)^3": "0", "SU(3)^2U(1)": "0", "SU(2)^2U(1)": "0", "U(1)^3": "0", "gravity^2U(1)": "0"
    }
    assert all(report["controls"].values())


def test_standard_model_rejects_wrong_gauge_group() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["geometry"]["internal_space"]["group"] = "SU(5)"
    with pytest.raises(StandardModelStructuralPipelineError, match="SU\\(3\\)"):
        run_standard_model_structural_pipeline(candidate=candidate)


def test_standard_model_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"
    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_standard_model_structural_pipeline(candidate=candidate)


def test_standard_model_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_standard_model_structural_report(tmp_path / "first.json")
    second = write_standard_model_structural_report(tmp_path / "second.json")
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
