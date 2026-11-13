"""Validation for provenance-preserving theory-candidate records.

The JSON Schema in ``schemas/theory_candidate.schema.json`` is the public
format.  This module deliberately uses only the Python standard library so
that CI can validate a record without installing a second schema engine.
The small Draft 2020-12 subset implemented here covers every keyword used by
the repository schema, then applies laboratory-specific semantic gates.

Registration is not theory selection, search authorization, or a physical
validation result.  Those actions remain explicit fields in the record.
"""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "theory-candidate-v1"
SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "theory_candidate.schema.json"
)

_RELATIVE_PATH_PATTERN = re.compile(r"^(?!/)(?![A-Za-z]:[\\/])[^\x00]+$")


class TheoryCandidateValidationError(ValueError):
    """Raised when a candidate record fails schema or semantic validation."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = tuple(errors)
        message = "Theory candidate validation failed:\n" + "\n".join(
            f"- {error}" for error in self.errors
        )
        super().__init__(message)


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def _type_matches(value: Any, expected: str | list[str]) -> bool:
    expected_types = [expected] if isinstance(expected, str) else expected
    actual = _json_type(value)
    return any(
        actual == candidate or (candidate == "number" and actual == "integer")
        for candidate in expected_types
    )


def _schema_error(errors: list[str], path: str, message: str) -> None:
    errors.append(f"{path}: {message}")


def _validate_schema(value: Any, schema: Mapping[str, Any], path: str, errors: list[str], root: Mapping[str, Any]) -> None:
    """Validate the subset of JSON Schema used by the repository schema."""
    if "$ref" in schema:
        ref = schema["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/"):
            _schema_error(errors, path, f"unsupported reference {ref!r}")
            return
        target: Any = root
        for part in ref[2:].split("/"):
            target = target[part]
        _validate_schema(value, target, path, errors, root)
        return

    if "const" in schema and value != schema["const"]:
        _schema_error(errors, path, f"must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        _schema_error(errors, path, f"must be one of {schema['enum']!r}")
    if "type" in schema and not _type_matches(value, schema["type"]):
        _schema_error(errors, path, f"has type {_json_type(value)!r}, expected {schema['type']!r}")
        return

    actual_type = _json_type(value)
    if actual_type == "object":
        properties = schema.get("properties", {})
        for required in schema.get("required", []):
            if required not in value:
                _schema_error(errors, f"{path}.{required}", "is required")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    _schema_error(errors, f"{path}.{key}", "is not an allowed property")
        for key, child_schema in properties.items():
            if key in value:
                _validate_schema(value[key], child_schema, f"{path}.{key}", errors, root)
    elif actual_type == "array":
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in value]
            if len(encoded) != len(set(encoded)):
                _schema_error(errors, path, "must not contain duplicate items")
        if "items" in schema:
            for index, item in enumerate(value):
                _validate_schema(item, schema["items"], f"{path}[{index}]", errors, root)
    elif actual_type == "string":
        if "minLength" in schema and len(value) < schema["minLength"]:
            _schema_error(errors, path, f"must contain at least {schema['minLength']} characters")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            _schema_error(errors, path, f"must contain at most {schema['maxLength']} characters")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            _schema_error(errors, path, "does not match the required pattern")
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                _schema_error(errors, path, "must be an ISO-8601 date-time")
    elif actual_type in {"integer", "number"}:
        if "minimum" in schema and value < schema["minimum"]:
            _schema_error(errors, path, f"must be at least {schema['minimum']}")


def _object_ids(candidate: Mapping[str, Any], key: str, id_key: str = "id") -> list[tuple[str, str]]:
    values = candidate.get(key, [])
    return [
        (f"{key}[{index}].{id_key}", item[id_key])
        for index, item in enumerate(values)
        if isinstance(item, Mapping) and id_key in item
    ]


def _check_unique_ids(candidate: Mapping[str, Any], errors: list[str]) -> None:
    collections = [
        ("fields", "id"),
        ("constraints", "id"),
        ("parameters", "id"),
        ("observables", "id"),
        ("geometry.connections", "id"),
        ("action.terms", "id"),
        ("provenance.sources", "source_id"),
        ("provenance.derivation_steps", "id"),
        ("provenance.decisions", "id"),
        ("open_questions", "id"),
    ]
    for collection, id_key in collections:
        if "." in collection:
            parent, child = collection.split(".")
            values = candidate.get(parent, {}).get(child, [])
            pairs = [
                (f"{collection}[{index}].{id_key}", item[id_key])
                for index, item in enumerate(values)
                if isinstance(item, Mapping) and id_key in item
            ]
        else:
            pairs = _object_ids(candidate, collection, id_key)
        seen: dict[str, str] = {}
        for path, value in pairs:
            if value in seen:
                errors.append(f"{path}: duplicate identifier {value!r}; first used at {seen[value]}")
            else:
                seen[value] = path


def _source_kinds(candidate: Mapping[str, Any]) -> dict[str, str]:
    return {
        source["source_id"]: source["kind"]
        for source in candidate["provenance"]["sources"]
    }


def _check_semantics(candidate: Mapping[str, Any], errors: list[str]) -> None:
    _check_unique_ids(candidate, errors)

    sources = _source_kinds(candidate)
    for index, source in enumerate(candidate["provenance"]["sources"]):
        path = f"provenance.sources[{index}]"
        repository_path = source.get("repository_path")
        if repository_path is not None and _RELATIVE_PATH_PATTERN.fullmatch(repository_path) is None:
            errors.append(f"{path}.repository_path: must be a relative repository path")
        if source["kind"] == "HISTORICAL_ARTIFACT" and not source["immutable"]:
            errors.append(f"{path}.immutable: historical artifacts must be immutable")

    for index, parameter in enumerate(candidate["parameters"]):
        path = f"parameters[{index}]"
        if parameter["status"] == "DERIVED" and parameter["provenance"] != "DERIVED":
            errors.append(f"{path}: DERIVED status requires DERIVED provenance")
        if parameter["provenance"] == "DERIVED" and not parameter.get("formula") and not parameter["dependencies"]:
            errors.append(f"{path}: DERIVED provenance requires formula or dependencies")
        if parameter["provenance"] == "EXPERIMENTAL":
            errors.append(f"{path}.provenance: parameters cannot be experimental inputs")

    for index, step in enumerate(candidate["provenance"]["derivation_steps"]):
        path = f"provenance.derivation_steps[{index}]"
        if step["provenance"] == "DERIVED":
            experimental_refs = [
                ref for ref in step["source_refs"] if sources.get(ref) == "EXPERIMENTAL_DATA"
            ]
            if experimental_refs:
                errors.append(
                    f"{path}.source_refs: experimental data cannot enter a DERIVED step ({experimental_refs!r})"
                )

    for index, observable in enumerate(candidate["observables"]):
        path = f"observables[{index}]"
        if observable["status"] == "PREDICTED":
            if observable["provenance"] != "DERIVED":
                errors.append(f"{path}: PREDICTED status requires DERIVED provenance")
            if observable["free_parameters"]:
                errors.append(f"{path}: a PREDICTED observable cannot retain free parameters")
            if not observable.get("expression"):
                errors.append(f"{path}.expression: a PREDICTED observable needs an expression")
        if observable["provenance"] == "DERIVED" and not observable.get("expression") and not observable["dependencies"]:
            errors.append(f"{path}: DERIVED provenance requires expression or dependencies")

    authorization = candidate["authorization"]
    active_statuses = {"AUTHORIZED", "RUNNING", "COMPLETE"}
    if authorization["search_status"] in active_statuses and not authorization.get("authorization_ref"):
        errors.append("authorization.authorization_ref: required when search_status is active")
    if authorization["external_data_used"] and authorization["empirical_comparison"] == "NOT_AUTHORIZED":
        errors.append("authorization.empirical_comparison: external data requires an authorized comparison gate")

    registration = candidate["registration"]
    if registration["selected"] and registration["status"] != "SELECTED_FOR_REFERENCE_PIPELINE":
        errors.append("registration: selected=true requires SELECTED_FOR_REFERENCE_PIPELINE status")
    if registration["status"] == "SELECTED_FOR_REFERENCE_PIPELINE" and not registration["selected"]:
        errors.append("registration: SELECTED_FOR_REFERENCE_PIPELINE requires selected=true")

    vacuum = candidate["vacuum"]
    if vacuum["status"] == "NOT_APPLICABLE":
        required_not_applicable = (
            "selection_status",
            "stationarity_status",
            "minimum_status",
            "moduli_status",
        )
        for field in required_not_applicable:
            if vacuum[field] != "NOT_APPLICABLE":
                errors.append(
                    f"vacuum.{field}: must be NOT_APPLICABLE when vacuum.status is NOT_APPLICABLE"
                )

    quantization = candidate["quantization"]
    if quantization["status"] == "DISCRETE_SPECTRUM_DERIVED":
        if quantization["scope"] != "SPECTRAL_PROBLEM":
            errors.append(
                "quantization.scope: a DISCRETE_SPECTRUM_DERIVED record must use SPECTRAL_PROBLEM"
            )
        if not quantization["integer_lattice_derived"]:
            errors.append(
                "quantization.integer_lattice_derived: required for DISCRETE_SPECTRUM_DERIVED"
            )
        if quantization["provenance"] != "DERIVED":
            errors.append(
                "quantization.provenance: DISCRETE_SPECTRUM_DERIVED requires DERIVED provenance"
            )
        if not quantization.get("mechanism"):
            errors.append(
                "quantization.mechanism: required for DISCRETE_SPECTRUM_DERIVED"
            )
    if quantization["field_quantization_status"] == "VERIFIED" and quantization["scope"] != "QUANTUM_FIELD":
        errors.append(
            "quantization.scope: VERIFIED field quantization requires QUANTUM_FIELD scope"
        )

def validate_theory_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a detached, JSON-compatible candidate record.

    The returned object is a deep copy so validation never mutates caller
    state.  ``TheoryCandidateValidationError.errors`` contains stable paths
    suitable for CI logs and review comments.
    """
    if not isinstance(candidate, Mapping):
        raise TheoryCandidateValidationError(["$: record must be a JSON object"])

    record = copy.deepcopy(dict(candidate))
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"Cannot read theory-candidate schema at {SCHEMA_PATH}") from exc

    errors: list[str] = []
    _validate_schema(record, schema, "$", errors, schema)
    if record.get("schema_version") == SCHEMA_VERSION and not errors:
        _check_semantics(record, errors)
    if errors:
        raise TheoryCandidateValidationError(errors)
    return record


def load_theory_candidate(path: str | Path) -> dict[str, Any]:
    """Load JSON from *path* and validate it as a theory candidate."""
    candidate_path = Path(path)
    try:
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TheoryCandidateValidationError([f"$: cannot load JSON from {candidate_path}: {exc}"]) from exc
    return validate_theory_candidate(candidate)


def validate_theory_candidate_file(path: str | Path) -> dict[str, Any]:
    """Explicit file-oriented alias for :func:`load_theory_candidate`."""
    return load_theory_candidate(path)
