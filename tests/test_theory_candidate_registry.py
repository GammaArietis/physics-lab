"""Contract tests for the theory-candidate registry record."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from physics_lab.registry.theory_candidate import (
    TheoryCandidateValidationError,
    load_theory_candidate,
    validate_theory_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "schemas" / "examples" / "theory_candidate_template.json"


def _template() -> dict[str, object]:
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


def test_neutral_template_is_valid_and_unselected() -> None:
    record = load_theory_candidate(TEMPLATE_PATH)
    assert record["schema_version"] == "theory-candidate-v1"
    assert record["registration"]["selected"] is False
    assert record["authorization"]["search_status"] == "NOT_ACTIVATED"
    assert record["validation"]["physical_claim_status"] == "NO_CLAIM"
    assert record["quantization"]["status"] == "NOT_DEFINED"


def test_repository_sources_must_use_relative_paths() -> None:
    record = _template()
    record["provenance"]["sources"].append(
        {
            "source_id": "local-source",
            "kind": "REPOSITORY_ARTIFACT",
            "repository_path": "/Users/example/private.json",
            "uri": None,
            "digest": None,
            "role": "test",
            "immutable": True,
            "notes": None,
        }
    )
    with pytest.raises(TheoryCandidateValidationError, match="required pattern"):
        validate_theory_candidate(record)


def test_derived_parameter_requires_formula_or_dependencies() -> None:
    record = _template()
    record["parameters"].append(
        {
            "id": "derived-coupling",
            "symbol": "g",
            "role": "COUPLING",
            "status": "DERIVED",
            "provenance": "DERIVED",
            "value": None,
            "unit": None,
            "formula": None,
            "dependencies": [],
            "source_refs": [],
        }
    )
    with pytest.raises(TheoryCandidateValidationError, match="formula or dependencies"):
        validate_theory_candidate(record)


def test_predicted_observable_cannot_hide_free_parameters() -> None:
    record = _template()
    record["observables"].append(
        {
            "id": "predicted-mass",
            "name": "Predicted mass",
            "expression": "g * m",
            "dimension": "mass",
            "status": "PREDICTED",
            "provenance": "DERIVED",
            "dependencies": ["g1", "m1"],
            "free_parameters": ["g1"],
            "uncertainty_status": "SYMBOLIC_ONLY",
            "comparison_status": "NOT_AUTHORIZED",
            "source_refs": [],
        }
    )
    with pytest.raises(TheoryCandidateValidationError, match="free parameters"):
        validate_theory_candidate(record)


def test_experimental_data_cannot_enter_a_derived_step() -> None:
    record = _template()
    record["provenance"]["sources"].append(
        {
            "source_id": "exp-data",
            "kind": "EXPERIMENTAL_DATA",
            "repository_path": None,
            "uri": "urn:physics-lab:test-experimental-data",
            "digest": None,
            "role": "comparison-only",
            "immutable": True,
            "notes": None,
        }
    )
    record["provenance"]["derivation_steps"].append(
        {
            "id": "illegal-derived-step",
            "operation": "use experimental datum",
            "inputs": [],
            "outputs": ["candidate-output"],
            "provenance": "DERIVED",
            "code_ref": None,
            "source_refs": ["exp-data"],
        }
    )
    with pytest.raises(TheoryCandidateValidationError, match="experimental data"):
        validate_theory_candidate(record)


def test_selection_requires_an_explicit_selection_status() -> None:
    record = copy.deepcopy(_template())
    record["registration"]["selected"] = True
    with pytest.raises(TheoryCandidateValidationError, match="selected=true"):
        validate_theory_candidate(record)
