"""Theory intermediate representation and immutable theory objects."""

from __future__ import annotations

from typing import Any, Mapping

from physics_lab.theory_kernel.epistemic import (
    EpistemicError,
    canonical_bytes,
    content_digest,
    freeze_document,
)

THEORY_STATES = (
    "FORMALIZED",
    "VALIDATED",
    "DERIVABLE",
    "PARTIAL",
    "INCONSISTENT",
    "EQUIVALENCE_UNSUPPORTED",
    "REQUIRES_HUMAN_INPUT",
    "CLOSED",
)

IR_FIELDS = (
    "theory_id",
    "parent_theory_id",
    "grammar_id",
    "grammar_version",
    "assumptions",
    "fields",
    "field_domains",
    "symmetries",
    "representations",
    "operators",
    "action",
    "constraints",
    "boundary_data",
    "parameter_registry",
    "derived_quantities",
    "proof_obligations",
    "equivalence_metadata",
    "provenance",
    "validation_state",
    "transformation_history",
    "content_hash",
)


class TheoryIntegrityError(EpistemicError):
    pass


def _empty_ir(theory_id: str, grammar_id: str, grammar_version: str) -> dict[str, Any]:
    return {
        "action": [],
        "assumptions": [],
        "boundary_data": [],
        "constraints": [],
        "derived_quantities": [],
        "equivalence_metadata": [],
        "field_domains": [],
        "fields": [],
        "grammar_id": grammar_id,
        "grammar_version": grammar_version,
        "operators": [],
        "parameter_registry": [],
        "parent_theory_id": None,
        "proof_obligations": [],
        "provenance": [],
        "representations": [],
        "symmetries": [],
        "theory_id": theory_id,
        "transformation_history": [],
        "validation_state": "FORMALIZED",
    }


def validate_ir(document: Mapping[str, Any]) -> None:
    missing = [name for name in IR_FIELDS if name not in document and name != "content_hash"]
    if missing:
        raise TheoryIntegrityError("missing IR fields: " + ", ".join(missing))
    state = document.get("validation_state")
    if state not in THEORY_STATES:
        raise TheoryIntegrityError(f"unknown validation state {state}")
    if not isinstance(document.get("theory_id"), str) or not document["theory_id"]:
        raise TheoryIntegrityError("theory_id is required")


def seal_ir(document: Mapping[str, Any]) -> dict[str, Any]:
    """Validate, then attach a hash of the document without the hash field."""
    body = freeze_document(document)
    body.pop("content_hash", None)
    validate_ir(body)
    digest = content_digest(
        {
            "assumptions": body["assumptions"],
            "equivalence_metadata": body["equivalence_metadata"],
            "grammar_version": body["grammar_version"],
            "parameter_registry": body["parameter_registry"],
            "theory_ir": {key: value for key, value in body.items() if key != "content_hash"},
            "transformation_history": body["transformation_history"],
        }
    )
    sealed = dict(body)
    sealed["content_hash"] = digest
    return freeze_document(sealed)


class TheoryObject:
    """Immutable theory. Callers receive copies; the stored bytes do not change."""

    def __init__(self, document: Mapping[str, Any]) -> None:
        sealed = seal_ir(document)
        object.__setattr__(self, "_bytes", canonical_bytes(sealed))
        object.__setattr__(self, "_hash", sealed["content_hash"])
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name: str, value: Any) -> None:
        raise TheoryIntegrityError("theory objects are immutable")

    def __delattr__(self, name: str) -> None:
        raise TheoryIntegrityError("theory objects are immutable")

    @property
    def theory_id(self) -> str:
        return str(self.document()["theory_id"])

    @property
    def content_hash(self) -> str:
        return str(object.__getattribute__(self, "_hash"))

    @property
    def validation_state(self) -> str:
        return str(self.document()["validation_state"])

    def canonical(self) -> bytes:
        return bytes(object.__getattribute__(self, "_bytes"))

    def document(self) -> dict[str, Any]:
        import json

        parsed = json.loads(self.canonical().decode("utf-8"))
        if not isinstance(parsed, dict):
            raise TheoryIntegrityError("sealed document is not an object")
        return parsed


def blank_theory(theory_id: str, grammar_id: str, grammar_version: str) -> dict[str, Any]:
    return _empty_ir(theory_id, grammar_id, grammar_version)
