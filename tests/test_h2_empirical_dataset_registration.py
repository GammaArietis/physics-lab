from __future__ import annotations

import copy

from physics_lab.registry import (
    load_experimental_dataset,
    run_harmonic_oscillator_pipeline,
    run_isolated_experimental_comparison,
)


DATASET_PATH = "schemas/examples/experimental_dataset_h2_harmonic_oscillator_control.json"
AUTHORIZATION_PATH = "schemas/examples/experimental_comparison_authorization_h2_ho_control.json"


def _authorization() -> dict[str, object]:
    import json
    from pathlib import Path

    return json.loads(Path(AUTHORIZATION_PATH).read_text(encoding="utf-8"))


def test_frozen_h2_dataset_is_experimental_and_source_digest_is_registered() -> None:
    dataset = load_experimental_dataset(DATASET_PATH)

    assert dataset["immutable"] is True
    assert dataset["kind"] == "EXPERIMENTAL_DATA"
    assert dataset["source"]["role"] == "comparison-only"
    assert dataset["source"]["digest"]["algorithm"] == "sha256"
    assert dataset["dataset_version"] == "corrected-allowed-j1-2026-11-14"
    observations = {item["observation_id"]: item for item in dataset["observations"]}
    observation_ids = set(observations)
    assert "h2-q1-1-wavenumber" in observation_ids
    assert "h2-q2-1-wavenumber" in observation_ids
    assert "h2-q1-0-wavenumber" not in observation_ids
    assert "h2-q2-0-wavenumber" not in observation_ids
    assert observations["h2-q1-1-wavenumber"]["value"] == 4155.254
    assert observations["h2-q2-1-wavenumber"]["value"] == 8075.3074
    assert len(dataset["observations"]) == 3


def test_h2_scope_control_comparison_is_downstream_and_does_not_fit() -> None:
    dataset = load_experimental_dataset(DATASET_PATH)
    model = run_harmonic_oscillator_pipeline()
    before = copy.deepcopy(model)

    report = run_isolated_experimental_comparison(
        model,
        dataset,
        authorization=_authorization(),
        mappings=[
            {
                "model_observable": "gap_ratio[2]",
                "observation_id": "h2-vibrational-gap-ratio-2",
            }
        ],
    )

    assert report["comparison_status"] == "COMPLETE"
    assert report["results"][0]["status"] == "OUTSIDE_UNCERTAINTY"
    assert report["fit"]["performed"] is False
    assert report["fit"]["calibration_performed"] is False
    assert report["fit"]["parameter_updates"] == []
    assert all(report["controls"].values())
    assert model == before
