"""Epistemic core.

Provenance, authorization, immutability, hashing, and target blindness live
here. This module does not mention a physical formalism.
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

from physics_lab.physics.action_serializer import canonical_json_bytes

KERNEL_VERSION = "phase12a-kernel-v1"
GRAMMAR_ID = "theory-kernel-grammar"
GRAMMAR_VERSION = "phase12a-theory-grammar-v1"

JSON_SCALARS = (str, int, bool, type(None))


class EpistemicError(Exception):
    """Fail-closed epistemic rejection."""


class SerializationError(EpistemicError):
    pass


class TargetAccessError(EpistemicError):
    """A numerical or experimental catalog was requested."""


class AuthorizationError(EpistemicError):
    pass


class ProvenanceError(EpistemicError):
    pass


def assert_json_tree(value: Any, path: str = "$") -> None:
    """Reject objects, memory addresses, and non-string keys."""
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise SerializationError(f"{path} key is not a string")
            assert_json_tree(item, path + "." + key)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            assert_json_tree(item, f"{path}[{index}]")
        return
    if isinstance(value, JSON_SCALARS):
        return
    raise SerializationError(f"{path} is not a JSON value ({type(value).__name__})")


def freeze_document(document: Mapping[str, Any]) -> dict[str, Any]:
    """Return a detached, order-independent copy."""
    raw = dict(document)
    assert_json_tree(raw)
    encoded = canonical_json_bytes(raw)
    import json

    parsed = json.loads(encoded.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise SerializationError("document root must be an object")
    return parsed


def content_digest(document: Mapping[str, Any]) -> str:
    payload = freeze_document(document)
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def canonical_bytes(document: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(freeze_document(document))


class AuditLog:
    """Append-only record of kernel decisions."""

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def record(self, kind: str, detail: dict[str, Any]) -> None:
        event = freeze_document({"detail": dict(detail), "kind": kind, "ordinal": len(self._events)})
        self._events.append(event)

    def events(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(item) for item in self._events)


class AuthorizationLedger:
    """Records authorizations. It does not grant new physical inputs."""

    def __init__(self) -> None:
        self._grants: list[dict[str, Any]] = []

    def preserve(self, grant: Mapping[str, Any]) -> None:
        stored = freeze_document(dict(grant))
        if stored.get("issued_by_phase_12a") is True:
            raise AuthorizationError("phase 12A cannot issue a physical authorization")
        self._grants.append(stored)

    def issue_new_physical_input(self, *_args: Any, **_kwargs: Any) -> None:
        raise AuthorizationError("phase 12A cannot invent a physical authorization")

    def grants(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(item) for item in self._grants)


class ProvenanceLedger:
    """Preserves origin labels and rejects silent promotion to DERIVED."""

    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}

    def preserve(self, record_id: str, provenance: str, *, origin: str) -> None:
        if record_id in self._records:
            previous = self._records[record_id]["provenance"]
            if previous != provenance:
                raise ProvenanceError(f"{record_id} provenance changed from {previous} to {provenance}")
            return
        self._records[record_id] = freeze_document(
            {"origin": origin, "provenance": provenance, "record_id": record_id}
        )

    def promote_to_derived(self, record_id: str) -> None:
        current = self._records.get(record_id)
        if current is None:
            raise ProvenanceError(f"{record_id} is not registered")
        if current["provenance"] != "DERIVED":
            raise ProvenanceError("an existing origin cannot be reclassified as DERIVED")

    def records(self) -> dict[str, dict[str, Any]]:
        return {key: dict(value) for key, value in sorted(self._records.items())}


def request_experimental_catalog(*_args: Any, **_kwargs: Any) -> None:
    """The kernel has no catalog. Every request fails closed."""
    raise TargetAccessError("experimental catalogs are outside the kernel")


def request_numerical_target(*_args: Any, **_kwargs: Any) -> None:
    raise TargetAccessError("numerical targets are outside the kernel")
