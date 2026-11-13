"""Contract tests for the isolated experimental comparison gate."""

from __future__ import annotations

import copy

import pytest

from physics_lab.registry import (
    ComparisonAuthorizationError,
    ExperimentalComparisonError,
    load_experimental_dataset,
    run_isolated_experimental_comparison,
    run_reference_pipeline,
    validate_experimental_dataset,
)


AUTHORIZATION = {
    "status": "AUTHORIZED",
    "authorization_ref": "phase6-contract-authorization",
    "target_blind": True,
    "fitting": False,
    "calibration": False,
    "parameter_updates": False,
}


def _dataset() -> dict[str, object]:
    return {
        "schema_version": "experimental-comparison-v1",
        "dataset_id": "comparison-contract-test",
        "dataset_version": "test-v1",
        "kind": "EXPERIMENTAL_DATA",
        "immutable": True,
        "source": {
            "source_id": "comparison-source-test",
            "uri": "urn:physics-lab:experimental:comparison-contract-test",
            "digest": {"algorithm": "sha256", "value": "a" * 64},
            "role": "comparison-only",
            "retrieved_at": None,
            "notes": "Contract fixture; not a theory input.",
        },
        "observations": [
            {
                "observation_id": "alpha-inverse-observation",
                "observable": "alpha_inverse",
                "value": 2.0,
                "uncertainty": 0.1,
                "unit": None,
                "provenance": "EXPERIMENTAL",
            }
        ],
    }


def _parameter_free_model_report() -> dict[str, object]:
    return {
        "candidate_id": "comparison-contract-model",
        "pipeline_status": "COMPLETE",
        "scope": {
            "candidate_selected": False,
            "empirical_comparison": "NOT_AUTHORIZED",
            "external_data_used": False,
        },
        "observables": [
            {
                "name": "alpha_inverse",
                "value": 2.05,
                "provenance": "DERIVED",
                "free_dependencies": [],
                "unit": None,
            }
        ],
    }


def test_authorized_comparison_is_downstream_and_does_not_fit() -> None:
    model = _parameter_free_model_report()
    dataset = _dataset()
    before_model = copy.deepcopy(model)
    before_dataset = copy.deepcopy(dataset)

    report = run_isolated_experimental_comparison(
        model,
        dataset,
        authorization=AUTHORIZATION,
    )

    assert report["comparison_status"] == "COMPLETE"
    assert report["results"][0]["status"] == "WITHIN_UNCERTAINTY"
    assert report["results"][0]["residual"] == pytest.approx(0.05)
    assert report["fit"] == {
        "performed": False,
        "calibration_performed": False,
        "parameter_updates": [],
    }
    assert all(report["controls"].values())
    assert model == before_model
    assert dataset == before_dataset


def test_current_circle_candidate_is_blocked_without_parameter_free_observable() -> None:
    model_report = run_reference_pipeline()
    dataset = _dataset()
    dataset["observations"][0]["observable"] = "momentum[1]"
    dataset["observations"][0]["observation_id"] = "momentum-observation"

    report = run_isolated_experimental_comparison(
        model_report,
        dataset,
        authorization=AUTHORIZATION,
    )

    assert report["comparison_status"] == "BLOCKED"
    assert report["results"][0]["status"] == "BLOCKED_NOT_PARAMETER_FREE_DERIVED"
    assert report["results"][0]["free_dependencies"]
    assert report["fit"]["performed"] is False


def test_comparison_requires_separate_authorization() -> None:
    with pytest.raises(ComparisonAuthorizationError, match="AUTHORIZED or COMPLETE"):
        run_isolated_experimental_comparison(
            _parameter_free_model_report(),
            _dataset(),
            authorization={
                **AUTHORIZATION,
                "status": "NOT_AUTHORIZED",
            },
        )


def test_comparison_rejects_fitting_and_calibration_flags() -> None:
    for field in ("fitting", "calibration", "parameter_updates"):
        authorization = {**AUTHORIZATION, field: True}
        with pytest.raises(ComparisonAuthorizationError, match=field.replace("_", " ")):
            run_isolated_experimental_comparison(
                _parameter_free_model_report(),
                _dataset(),
                authorization=authorization,
            )


def test_experimental_values_cannot_appear_in_model_report() -> None:
    model = _parameter_free_model_report()
    model["observables"][0]["provenance"] = "EXPERIMENTAL"

    with pytest.raises(ExperimentalComparisonError, match="experimental values"):
        run_isolated_experimental_comparison(model, _dataset(), authorization=AUTHORIZATION)


def test_dataset_is_immutable_and_comparison_only() -> None:
    dataset = _dataset()
    assert validate_experimental_dataset(dataset)["immutable"] is True
    dataset["immutable"] = False
    with pytest.raises(ExperimentalComparisonError, match="immutable"):
        validate_experimental_dataset(dataset)


def test_repository_dataset_template_loads() -> None:
    template = load_experimental_dataset(
        "schemas/examples/experimental_comparison_template.json"
    )
    assert template["kind"] == "EXPERIMENTAL_DATA"
    assert template["observations"] == []
