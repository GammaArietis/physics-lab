"""Semantic closure audit for the internal circle reference candidate.

The audit does not add physics to the benchmark.  It makes the boundary of
the benchmark explicit: its four parameters remain free inputs, the vacuum
sector is out of scope, and a discrete spectrum derived from periodicity is
not the same operation as quantizing a field.
"""

from __future__ import annotations

from typing import Any, Mapping

from physics_lab.registry.theory_candidate import validate_theory_candidate


REFERENCE_CLOSURE_VERSION = "circle-reference-closure-v1"
REFERENCE_CANDIDATE_ID = "circle-reference-internal-spectrum"
REFERENCE_PIPELINE_REF = "circle-reference-v1"


class ReferenceClosureError(RuntimeError):
    """Raised when the reference record is semantically ambiguous."""


def _parameter_closure(candidate: Mapping[str, Any]) -> dict[str, Any]:
    free_inputs: list[str] = []
    derived: list[str] = []
    assumed: list[str] = []
    calibrated: list[str] = []
    experimental: list[str] = []
    unresolved: list[str] = []
    for parameter in candidate["parameters"]:
        parameter_id = parameter["id"]
        if parameter["status"] == "FREE" and parameter["provenance"] == "INPUT":
            free_inputs.append(parameter_id)
        elif parameter["status"] == "DERIVED" or parameter["provenance"] == "DERIVED":
            derived.append(parameter_id)
        elif parameter["status"] == "CALIBRATED" or parameter["provenance"] == "CALIBRATED":
            calibrated.append(parameter_id)
        elif parameter["provenance"] == "EXPERIMENTAL":
            experimental.append(parameter_id)
        elif parameter["status"] in {"ASSUMED", "FIXED"} or parameter["provenance"] in {"ASSUMED", "CONVENTION"}:
            assumed.append(parameter_id)
        else:
            unresolved.append(parameter_id)
    return {
        "free_input_ids": free_inputs,
        "derived_ids": derived,
        "assumed_ids": assumed,
        "calibrated_ids": calibrated,
        "experimental_ids": experimental,
        "unresolved_ids": unresolved,
        "all_inputs_explicit": (
            bool(free_inputs)
            and not derived
            and not assumed
            and not calibrated
            and not experimental
            and not unresolved
        ),
    }


def _observable_closure(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for observable in candidate["observables"]:
        if observable["provenance"] == "DERIVED":
            classification = "DERIVED_FORM_WITH_FREE_PARAMETERS"
        elif observable["provenance"] == "ASSUMED" and observable["status"] == "UNRESOLVED":
            classification = "ASSUMED_MAP_UNRESOLVED"
        elif observable["provenance"] == "ASSUMED":
            classification = "ASSUMED_MAP_WITH_FREE_PARAMETERS"
        else:
            classification = f"{observable['status']}_{observable['provenance']}"
        records.append(
            {
                "id": observable["id"],
                "status": observable["status"],
                "provenance": observable["provenance"],
                "classification": classification,
                "free_parameters": list(observable["free_parameters"]),
            }
        )
    return records


def audit_reference_closure(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic semantic-closure report for the circle record."""
    record = validate_theory_candidate(candidate)
    if record["registration"].get("pipeline_ref") != REFERENCE_PIPELINE_REF:
        raise ReferenceClosureError(
            f"Reference closure requires pipeline_ref={REFERENCE_PIPELINE_REF!r}."
        )

    parameters = _parameter_closure(record)
    vacuum = record["vacuum"]
    quantization = record["quantization"]
    decision_ids = {decision["id"] for decision in record["provenance"]["decisions"]}
    observables = _observable_closure(record)
    observable_by_id = {item["id"]: item for item in observables}

    checks = {
        "four_explicit_free_inputs": (
            parameters["free_input_ids"] == [
                "radius",
                "hbar",
                "charge-coupling",
                "mass-conversion",
            ]
            and parameters["all_inputs_explicit"]
        ),
        "no_calibrated_or_experimental_parameters": not parameters["calibrated_ids"] and not parameters["experimental_ids"],
        "vacuum_not_applicable_by_scope": (
            vacuum["status"] == "NOT_APPLICABLE"
            and vacuum["selection_status"] == "NOT_APPLICABLE"
            and vacuum["stationarity_status"] == "NOT_APPLICABLE"
            and vacuum["minimum_status"] == "NOT_APPLICABLE"
            and vacuum["moduli_status"] == "NOT_APPLICABLE"
            and "vacuum-scope" in decision_ids
        ),
        "discrete_spectrum_is_derived": (
            quantization["status"] == "DISCRETE_SPECTRUM_DERIVED"
            and quantization["scope"] == "SPECTRAL_PROBLEM"
            and quantization["integer_lattice_derived"]
            and quantization["provenance"] == "DERIVED"
        ),
        "field_quantization_is_not_claimed": (
            quantization["field_quantization_status"] == "NOT_PERFORMED"
            and record["quantum"]["status"] == "QUANTIZATION_NOT_PERFORMED"
        ),
        "observable_provenance_is_explicit": (
            observable_by_id.get("internal-momentum", {}).get("classification") == "DERIVED_FORM_WITH_FREE_PARAMETERS"
            and observable_by_id.get("internal-eigenvalue", {}).get("classification") == "DERIVED_FORM_WITH_FREE_PARAMETERS"
            and observable_by_id.get("internal-charge", {}).get("classification") == "ASSUMED_MAP_WITH_FREE_PARAMETERS"
            and observable_by_id.get("internal-mass", {}).get("classification") == "ASSUMED_MAP_UNRESOLVED"
        ),
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ReferenceClosureError(
            "Reference semantic-closure audit failed: " + ", ".join(failed)
        )

    return {
        "audit_version": REFERENCE_CLOSURE_VERSION,
        "status": "SEMANTICALLY_CLOSED_INTERNAL_ONLY",
        "parameter_closure": parameters,
        "vacuum": {
            "status": "NOT_APPLICABLE_BY_SCOPE",
            "reason": "No spacetime action, potential, or vacuum sector is part of this benchmark.",
        },
        "quantization": {
            "status": "DISCRETE_SPECTRUM_DERIVED_SEPARATE_FROM_FIELD_QUANTIZATION",
            "mechanism": quantization["mechanism"],
            "field_quantization_status": quantization["field_quantization_status"],
        },
        "observables": observables,
        "checks": checks,
    }


__all__ = [
    "REFERENCE_CLOSURE_VERSION",
    "REFERENCE_CANDIDATE_ID",
    "REFERENCE_PIPELINE_REF",
    "ReferenceClosureError",
    "audit_reference_closure",
]
