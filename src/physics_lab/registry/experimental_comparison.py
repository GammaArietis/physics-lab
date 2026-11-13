"""Isolated comparison of derived model outputs with experimental data.

The comparison stage is deliberately downstream of derivation.  It accepts a
completed, JSON-safe model report and an immutable comparison-only dataset;
it never constructs or mutates a model, fits parameters, calibrates inputs,
or ranks candidates.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


EXPERIMENTAL_COMPARISON_VERSION = "experimental-comparison-v1"
DATASET_SCHEMA_VERSION = "experimental-comparison-v1"
_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
_DIGEST_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_DATASET_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "examples"
    / "experimental_comparison_template.json"
)


class ExperimentalComparisonError(RuntimeError):
    """Raised when an isolated comparison request is invalid or unauthorized."""


class ComparisonAuthorizationError(ExperimentalComparisonError):
    """Raised when comparison has not received its separate authorization."""


def _fail(message: str) -> None:
    raise ExperimentalComparisonError(message)


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(f"{label} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        _fail(f"{label} must be finite")
    return number


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_experimental_dataset(dataset: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and detach an immutable comparison-only dataset."""
    if not isinstance(dataset, Mapping):
        _fail("experimental dataset must be an object")
    record = copy.deepcopy(dict(dataset))
    required = {"schema_version", "dataset_id", "dataset_version", "kind", "immutable", "source", "observations"}
    missing = sorted(required - record.keys())
    if missing:
        _fail(f"experimental dataset is missing fields: {', '.join(missing)}")
    if record["schema_version"] != DATASET_SCHEMA_VERSION:
        _fail("unsupported experimental dataset schema version")
    if not isinstance(record["dataset_id"], str) or _ID_PATTERN.fullmatch(record["dataset_id"]) is None:
        _fail("dataset_id is not a portable identifier")
    if record["kind"] != "EXPERIMENTAL_DATA":
        _fail("dataset kind must be EXPERIMENTAL_DATA")
    if record["immutable"] is not True:
        _fail("experimental datasets must be immutable")
    source = record["source"]
    if not isinstance(source, Mapping):
        _fail("dataset source must be an object")
    for field in ("source_id", "uri", "digest", "role"):
        if field not in source:
            _fail(f"dataset source is missing {field}")
    if source["role"] != "comparison-only":
        _fail("experimental source role must be comparison-only")
    digest = source["digest"]
    if not isinstance(digest, Mapping) or digest.get("algorithm") != "sha256" or _DIGEST_PATTERN.fullmatch(str(digest.get("value", ""))) is None:
        _fail("dataset source digest must be a sha256 digest")
    observations = record["observations"]
    if not isinstance(observations, list):
        _fail("dataset observations must be a list")
    seen_ids: set[str] = set()
    for index, observation in enumerate(observations):
        label = f"observations[{index}]"
        if not isinstance(observation, Mapping):
            _fail(f"{label} must be an object")
        for field in ("observation_id", "observable", "value", "uncertainty", "unit", "provenance"):
            if field not in observation:
                _fail(f"{label} is missing {field}")
        observation_id = observation["observation_id"]
        if not isinstance(observation_id, str) or _ID_PATTERN.fullmatch(observation_id) is None:
            _fail(f"{label}.observation_id is not portable")
        if observation_id in seen_ids:
            _fail(f"duplicate observation_id {observation_id!r}")
        seen_ids.add(observation_id)
        if not isinstance(observation["observable"], str) or not observation["observable"]:
            _fail(f"{label}.observable must be non-empty")
        _finite_number(observation["value"], f"{label}.value")
        uncertainty = _finite_number(observation["uncertainty"], f"{label}.uncertainty")
        if uncertainty < 0:
            _fail(f"{label}.uncertainty must be non-negative")
        if observation["provenance"] != "EXPERIMENTAL":
            _fail(f"{label}.provenance must be EXPERIMENTAL")
    return record


def load_experimental_dataset(path: str | Path) -> dict[str, Any]:
    """Load and validate a comparison-only dataset from JSON."""
    dataset_path = Path(path)
    try:
        payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExperimentalComparisonError(f"cannot load experimental dataset from {dataset_path}: {exc}") from exc
    return validate_experimental_dataset(payload)


def _validate_authorization(authorization: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(authorization, Mapping):
        raise ComparisonAuthorizationError("comparison authorization must be an object")
    record = copy.deepcopy(dict(authorization))
    if record.get("status") not in {"AUTHORIZED", "COMPLETE"}:
        raise ComparisonAuthorizationError(
            "isolated comparison requires status AUTHORIZED or COMPLETE"
        )
    if not isinstance(record.get("authorization_ref"), str) or not record["authorization_ref"]:
        raise ComparisonAuthorizationError("comparison authorization requires authorization_ref")
    if record.get("target_blind") is not True:
        raise ComparisonAuthorizationError("comparison authorization must remain target-blind")
    for flag in ("fitting", "calibration", "parameter_updates"):
        if record.get(flag) is not False:
            raise ComparisonAuthorizationError(
                f"comparison authorization forbids {flag.replace('_', ' ')}"
            )
    return record


def _model_observables(model_report: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    observables = model_report.get("observables")
    if not isinstance(observables, list):
        raise ExperimentalComparisonError("model report must expose an observables list")
    result: dict[str, Mapping[str, Any]] = {}
    for index, observable in enumerate(observables):
        if not isinstance(observable, Mapping) or not isinstance(observable.get("name"), str):
            raise ExperimentalComparisonError(f"model observables[{index}] is invalid")
        name = observable["name"]
        if name in result:
            raise ExperimentalComparisonError(f"duplicate model observable {name!r}")
        result[name] = observable
    return result


def run_isolated_experimental_comparison(
    model_report: Mapping[str, Any],
    dataset: Mapping[str, Any],
    *,
    authorization: Mapping[str, Any],
    mappings: Sequence[Mapping[str, str]] | None = None,
) -> dict[str, Any]:
    """Compare parameter-free derived observables without changing the model."""
    if not isinstance(model_report, Mapping):
        raise ExperimentalComparisonError("model report must be an object")
    before = copy.deepcopy(dict(model_report))
    model = copy.deepcopy(dict(model_report))
    if model.get("pipeline_status") != "COMPLETE":
        raise ExperimentalComparisonError("model report must come from a complete derivation")
    if model.get("scope", {}).get("candidate_selected") is True:
        raise ExperimentalComparisonError("selected candidates cannot enter this reference comparison")
    if model.get("scope", {}).get("external_data_used") is True:
        raise ExperimentalComparisonError("model report already contains external data")
    auth = _validate_authorization(authorization)
    data = validate_experimental_dataset(dataset)
    observables = _model_observables(model)
    parameters = model.get("parameters", [])
    if any(item.get("provenance") == "EXPERIMENTAL" for item in observables.values()) or any(
        isinstance(item, Mapping) and item.get("provenance") == "EXPERIMENTAL"
        for item in parameters
    ):
        raise ExperimentalComparisonError("experimental values cannot appear in the model report")

    if mappings is None:
        mappings = [
            {"model_observable": observation["observable"], "observation_id": observation["observation_id"]}
            for observation in data["observations"]
        ]
    observation_by_id = {item["observation_id"]: item for item in data["observations"]}
    results: list[dict[str, Any]] = []
    for mapping in mappings:
        if not isinstance(mapping, Mapping):
            raise ExperimentalComparisonError("comparison mappings must be objects")
        model_name = mapping.get("model_observable")
        observation_id = mapping.get("observation_id")
        if not isinstance(model_name, str) or not isinstance(observation_id, str):
            raise ExperimentalComparisonError("comparison mappings need model_observable and observation_id")
        observation = observation_by_id.get(observation_id)
        if observation is None:
            raise ExperimentalComparisonError(f"unknown experimental observation {observation_id!r}")
        observable = observables.get(model_name)
        if observable is None:
            results.append({
                "model_observable": model_name,
                "observation_id": observation_id,
                "status": "BLOCKED_NO_MODEL_OBSERVABLE",
            })
            continue
        free_dependencies = list(observable.get("free_dependencies", []))
        if observable.get("provenance") != "DERIVED" or free_dependencies:
            results.append({
                "model_observable": model_name,
                "observation_id": observation_id,
                "status": "BLOCKED_NOT_PARAMETER_FREE_DERIVED",
                "model_provenance": observable.get("provenance"),
                "free_dependencies": free_dependencies,
            })
            continue
        model_value = _finite_number(observable.get("value"), f"model observable {model_name}")
        data_value = _finite_number(observation["value"], f"experimental observation {observation_id}")
        uncertainty = float(observation["uncertainty"])
        residual = model_value - data_value
        normalized = None if uncertainty == 0 else residual / uncertainty
        within = abs(residual) == 0 if uncertainty == 0 else abs(residual) <= uncertainty
        results.append({
            "model_observable": model_name,
            "observation_id": observation_id,
            "status": "WITHIN_UNCERTAINTY" if within else "OUTSIDE_UNCERTAINTY",
            "model_value": model_value,
            "experimental_value": data_value,
            "experimental_uncertainty": uncertainty,
            "residual": residual,
            "normalized_residual": normalized,
            "unit": observation["unit"],
        })

    comparable = [item for item in results if "residual" in item]
    blocked = [item for item in results if item["status"].startswith("BLOCKED_")]
    if not results or len(blocked) == len(results):
        status = "BLOCKED"
    elif blocked:
        status = "PARTIAL"
    else:
        status = "COMPLETE"
    model_unchanged = model == before
    controls = {
        "comparison_only_data": True,
        "dataset_immutable": data["immutable"] is True,
        "model_report_unchanged": model_unchanged,
        "no_experimental_values_in_model": not any(
            item.get("provenance") == "EXPERIMENTAL" for item in observables.values()
        ) and not any(
            isinstance(item, Mapping) and item.get("provenance") == "EXPERIMENTAL"
            for item in parameters
        ),
        "no_parameter_fit": auth["fitting"] is False,
        "no_calibration": auth["calibration"] is False,
        "no_parameter_updates": auth["parameter_updates"] is False,
        "target_blind": auth["target_blind"] is True,
        "no_candidate_ranking": True,
    }
    if not all(controls.values()) or not model_unchanged:
        raise ExperimentalComparisonError("isolated comparison control failed")

    return {
        "comparison_version": EXPERIMENTAL_COMPARISON_VERSION,
        "comparison_status": status,
        "candidate_id": model.get("candidate_id"),
        "authorization": auth,
        "dataset": {
            "dataset_id": data["dataset_id"],
            "dataset_version": data["dataset_version"],
            "kind": data["kind"],
            "source_digest": data["source"]["digest"]["value"],
            "observation_count": len(data["observations"]),
        },
        "model_report_digest": _canonical_digest(model),
        "results": results,
        "comparable_result_count": len(comparable),
        "blocked_result_count": len(blocked),
        "controls": controls,
        "fit": {
            "performed": False,
            "calibration_performed": False,
            "parameter_updates": [],
        },
    }


def write_isolated_comparison_report(
    path: str | Path,
    report: Mapping[str, Any],
) -> Path:
    """Write a portable comparison report without adding data to the model."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


__all__ = [
    "ComparisonAuthorizationError",
    "DATASET_SCHEMA_VERSION",
    "EXPERIMENTAL_COMPARISON_VERSION",
    "ExperimentalComparisonError",
    "load_experimental_dataset",
    "run_isolated_experimental_comparison",
    "validate_experimental_dataset",
    "write_isolated_comparison_report",
]
