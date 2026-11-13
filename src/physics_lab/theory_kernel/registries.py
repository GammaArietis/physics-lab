"""Parameter registry, derived quantities, and proof obligations."""

from __future__ import annotations

from typing import Any, Mapping

from physics_lab.theory_kernel.epistemic import EpistemicError, freeze_document

PARAMETER_KINDS = (
    "physical parameter",
    "normalization parameter",
    "convention",
    "discrete label",
    "derived quantity",
    "external input",
)

CLOSURE_STATUSES = (
    "INPUT",
    "DERIVED",
    "CONVENTION",
    "DISCRETE",
    "PARAMETER_DEPENDENT",
    "UNRESOLVED",
)

OBLIGATION_STATES = (
    "OPEN",
    "RESOLVED",
    "BLOCKED",
    "REQUIRES_HUMAN_INPUT",
    "OUT_OF_SCOPE",
)


class RegistryError(EpistemicError):
    pass


class ObligationError(EpistemicError):
    pass


def parameter_record(
    *,
    parameter_id: str,
    symbol: str,
    dimension: str,
    origin: str,
    provenance: str,
    branch: str,
    independent: bool,
    constrained_by: list[str],
    derived_from: list[str],
    current_status: str,
    kind: str,
) -> dict[str, Any]:
    if kind not in PARAMETER_KINDS:
        raise RegistryError(f"unknown parameter kind {kind}")
    if current_status not in CLOSURE_STATUSES:
        raise RegistryError(f"unknown parameter status {current_status}")
    return freeze_document(
        {
            "branch": branch,
            "constrained_by": list(constrained_by),
            "current_status": current_status,
            "derived_from": list(derived_from),
            "dimension": dimension,
            "independent": independent,
            "kind": kind,
            "origin": origin,
            "parameter_id": parameter_id,
            "provenance": provenance,
            "symbol": symbol,
        }
    )


def derived_quantity_record(
    *,
    quantity_id: str,
    expression: str,
    parent_parameters: list[str],
    derivation_id: str,
    provenance: str,
    assumptions: list[str],
    validity_scope: str,
) -> dict[str, Any]:
    if provenance == "INPUT":
        raise RegistryError("a derived quantity cannot be stored as an independent input")
    return freeze_document(
        {
            "assumptions": list(assumptions),
            "derivation_id": derivation_id,
            "expression": expression,
            "parent_parameters": list(parent_parameters),
            "provenance": provenance,
            "quantity_id": quantity_id,
            "validity_scope": validity_scope,
        }
    )


def proof_obligation(
    *,
    obligation_id: str,
    theory_id: str,
    missing_statement: str,
    dependencies: list[str],
    allowed_methods: list[str],
    forbidden_inputs: list[str],
    current_status: str,
) -> dict[str, Any]:
    if current_status not in OBLIGATION_STATES:
        raise ObligationError(current_status)
    return freeze_document(
        {
            "allowed_methods": list(allowed_methods),
            "current_status": current_status,
            "dependencies": list(dependencies),
            "forbidden_inputs": list(forbidden_inputs),
            "missing_statement": missing_statement,
            "obligation_id": obligation_id,
            "theory_id": theory_id,
        }
    )


class ObligationStore:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}

    def add(self, item: Mapping[str, Any]) -> dict[str, Any]:
        stored = proof_obligation(
            obligation_id=str(item["obligation_id"]),
            theory_id=str(item["theory_id"]),
            missing_statement=str(item["missing_statement"]),
            dependencies=list(item.get("dependencies") or []),
            allowed_methods=list(item.get("allowed_methods") or []),
            forbidden_inputs=list(item.get("forbidden_inputs") or []),
            current_status=str(item["current_status"]),
        )
        self._items[stored["obligation_id"]] = stored
        return stored

    def convert_open_to_assumption(self, obligation_id: str) -> None:
        item = self._items.get(obligation_id)
        if item is None:
            raise ObligationError("unknown obligation")
        if item["current_status"] == "OPEN":
            raise ObligationError("an OPEN obligation cannot become an assumption")
        raise ObligationError("obligations are not assumptions")

    def items(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._items[key] for key in sorted(self._items))


def merge_symbols(left: Mapping[str, Any], right: Mapping[str, Any]) -> None:
    """Identical symbols on different branches stay distinct."""
    if left["symbol"] == right["symbol"] and left["branch"] != right["branch"]:
        raise RegistryError("shared symbols are not merged across branches")
    if left["parameter_id"] != right["parameter_id"]:
        raise RegistryError("distinct parameter ids are not merged")
