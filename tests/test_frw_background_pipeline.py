"""End-to-end tests for the controlled flat FRW background."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import FRWBackgroundPipelineError, TheoryCandidateValidationError, load_theory_candidate, run_frw_background_pipeline, write_frw_background_report


CANDIDATE_PATH = "schemas/examples/theory_candidate_frw_background.json"


def test_frw_candidate_declares_flat_lambda_zero_scope() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)
    assert candidate["registration"]["pipeline_ref"] == "frw-background-v1"
    assert candidate["geometry"]["spacetime"]["manifold"] == "FRW_flat_Lambda0"
    assert candidate["quantum"]["status"] == "CLASSICAL_ONLY"


def test_frw_runs_friedmann_and_continuity_checks() -> None:
    report = run_frw_background_pipeline(candidate_path=CANDIDATE_PATH)
    assert report["pipeline_status"] == "COMPLETE"
    assert report["checks"]["friedmann_equation_verified"] is True
    assert report["checks"]["continuity_scaling_verified"] is True
    assert next(item for item in report["observables"] if item["name"] == "density_scaling_exponent")["value"] == pytest.approx(3.0)
    assert all(report["controls"].values())


def test_frw_rejects_unbounded_equation_of_state() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][3]["value"] = -1
    with pytest.raises(FRWBackgroundPipelineError, match="greater than -1"):
        run_frw_background_pipeline(candidate=candidate)


def test_frw_rejects_experimental_parameter_leak() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"][0]["provenance"] = "EXPERIMENTAL"
    with pytest.raises(TheoryCandidateValidationError, match="experimental inputs"):
        run_frw_background_pipeline(candidate=candidate)


def test_frw_report_is_deterministic_and_portable(tmp_path) -> None:
    first = write_frw_background_report(tmp_path / "first.json")
    second = write_frw_background_report(tmp_path / "second.json")
    assert json.loads(first.read_text()) == json.loads(second.read_text())
    assert "/workspace/" not in first.read_text()
    assert "/Users/" not in first.read_text()
