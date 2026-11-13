"""Computation backends sit behind the theory adapter.

The default backend refuses numerical targets. It does not evaluate physics.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol

from physics_lab.theory_kernel.epistemic import TargetAccessError


class ComputationBackend(Protocol):
    def evaluate(self, theory_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        ...


class RefusingBackend:
    """No experimental database and no numerical objective."""

    def evaluate(self, theory_id: str, request: Mapping[str, Any]) -> dict[str, Any]:
        raise TargetAccessError(theory_id)


def adapt_ir(document: Mapping[str, Any]) -> dict[str, str]:
    """Adapter: identity of the theory, not a physical calculation."""
    return {"grammar_version": str(document["grammar_version"]), "theory_id": str(document["theory_id"])}
