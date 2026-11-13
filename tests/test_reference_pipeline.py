"""End-to-end tests for the single-candidate reference pipeline."""

from __future__ import annotations

import copy
import json

import pytest

from physics_lab.registry import (
    ReferencePipelineError,
    load_theory_candidate,
    run_reference_pipeline,
    write_reference_pipeline_report,
)


CANDIDATE_PATH = "schemas/examples/theory_candidate_circle_reference.json"


def test_reference_candidate_is_ready_but_not_selected() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)
    assert candidate["candidate_id"] == "circle-reference-internal-spectrum"
    assert candidate["registration"]["status"] == "READY_FOR_DERIVATION"
    assert candidate["registration"]["selected"] is False
    assert candidate["authorization"]["search_status"] == "NOT_ACTIVATED"
    assert candidate["authorization"]["external_data_used"] is False


def test_reference_pipeline_runs_from_action_to_observables() -> None:
    report = run_reference_pipeline(candidate_path=CANDIDATE_PATH)

    assert report["pipeline_status"] == "COMPLETE"
    assert report["action"]["expression"] == "H = p_xi^2"
    assert report["action"]["instantiated"] is True
    assert report["derivation"]["integer_n_derived"] is True
    assert report["derivation"]["display_window_is_not_a_search_bound"] is True
    assert len(report["spectrum"]) == 5
    assert len(report["observables"]) == 15
    assert all(report["controls"].values())
    assert report["validation"]["legacy_validator_failures"] == []


def test_reference_pipeline_preserves_assumption_and_free_parameter_status() -> None:
    report = run_reference_pipeline(candidate_path=CANDIDATE_PATH)
    parameters = {item["name"]: item for item in report["parameters"]}
    assert all(item["provenance"] == "INPUT" for item in parameters.values())
    assert all(item["free"] for item in parameters.values())

    masses = [item for item in report["observables"] if item["name"].startswith("mass[")]
    momenta = [item for item in report["observables"] if item["name"].startswith("momentum[")]
    assert masses and momenta
    assert all(item["provenance"] == "ASSUMED" for item in masses)
    assert all(item["provenance"] == "DERIVED" for item in momenta)
    assert all(item["free_dependencies"] for item in momenta)


def test_reference_pipeline_rejects_search_activation() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)
    candidate = copy.deepcopy(candidate)
    candidate["authorization"]["search_status"] = "AUTHORIZED"
    candidate["authorization"]["authorization_ref"] = "manual-gate"
    with pytest.raises(ReferencePipelineError, match="must remain closed"):
        run_reference_pipeline(candidate=candidate)


def test_reference_report_is_portable_and_deterministic(tmp_path) -> None:
    first_path = write_reference_pipeline_report(tmp_path / "first.json")
    second_path = write_reference_pipeline_report(tmp_path / "second.json")
    first = json.loads(first_path.read_text(encoding="utf-8"))
    second = json.loads(second_path.read_text(encoding="utf-8"))
    assert first == second
    serialized = first_path.read_text(encoding="utf-8")
    assert "/workspace/" not in serialized
    assert "/Users/" not in serialized
    assert "EXPERIMENTAL" not in serialized
