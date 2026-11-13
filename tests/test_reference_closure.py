"""Semantic closure tests for parameters, vacuum and quantization."""

from __future__ import annotations

import copy

import pytest

from physics_lab.registry import (
    ReferenceClosureError,
    TheoryCandidateValidationError,
    audit_reference_closure,
    load_theory_candidate,
    run_reference_pipeline,
)


CANDIDATE_PATH = "schemas/examples/theory_candidate_circle_reference.json"


def test_reference_record_closes_scope_without_overclaiming() -> None:
    candidate = load_theory_candidate(CANDIDATE_PATH)
    audit = audit_reference_closure(candidate)

    assert audit["status"] == "SEMANTICALLY_CLOSED_INTERNAL_ONLY"
    assert audit["parameter_closure"]["free_input_ids"] == [
        "radius",
        "hbar",
        "charge-coupling",
        "mass-conversion",
    ]
    assert audit["parameter_closure"]["calibrated_ids"] == []
    assert audit["parameter_closure"]["experimental_ids"] == []
    assert audit["vacuum"]["status"] == "NOT_APPLICABLE_BY_SCOPE"
    assert audit["quantization"]["status"] == (
        "DISCRETE_SPECTRUM_DERIVED_SEPARATE_FROM_FIELD_QUANTIZATION"
    )


def test_reference_pipeline_exposes_semantic_closure() -> None:
    report = run_reference_pipeline(candidate_path=CANDIDATE_PATH)

    assert report["closure_audit"]["status"] == "SEMANTICALLY_CLOSED_INTERNAL_ONLY"
    assert report["controls"]["vacuum_scope_closed"] is True
    assert report["controls"]["discrete_spectrum_separate_from_field_quantization"] is True
    assert report["closure_audit"]["quantization"]["field_quantization_status"] == "NOT_PERFORMED"


def test_vacuum_not_applicable_requires_all_vacuum_checks_closed() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["vacuum"]["minimum_status"] = "NOT_TESTED"

    with pytest.raises(TheoryCandidateValidationError, match="minimum_status"):
        audit_reference_closure(candidate)


def test_field_quantization_cannot_be_marked_verified_outside_field_scope() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["quantization"]["field_quantization_status"] = "VERIFIED"

    with pytest.raises(TheoryCandidateValidationError, match="QUANTUM_FIELD"):
        audit_reference_closure(candidate)


def test_semantic_audit_rejects_missing_vacuum_scope_decision() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["provenance"]["decisions"] = [
        decision
        for decision in candidate["provenance"]["decisions"]
        if decision["id"] != "vacuum-scope"
    ]

    with pytest.raises(ReferenceClosureError, match="vacuum_not_applicable_by_scope"):
        audit_reference_closure(candidate)


def test_semantic_audit_rejects_an_unlisted_assumed_parameter() -> None:
    candidate = copy.deepcopy(load_theory_candidate(CANDIDATE_PATH))
    candidate["parameters"].append(
        {
            "id": "hidden-assumption",
            "symbol": "g",
            "role": "COUPLING",
            "status": "ASSUMED",
            "provenance": "ASSUMED",
            "value": 1.0,
            "unit": None,
            "formula": None,
            "dependencies": [],
            "source_refs": [],
        }
    )

    with pytest.raises(ReferenceClosureError, match="four_explicit_free_inputs"):
        audit_reference_closure(candidate)
