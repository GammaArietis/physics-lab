"""Equivalence firewall.

Theories are merged only by a certified rule. Coinciding labels are not a rule.
"""

from __future__ import annotations

from typing import Any

from physics_lab.theory_kernel.epistemic import EpistemicError, freeze_document

CERTIFIED_RULES = (
    "invertible field redefinition",
    "total derivative",
    "coordinate transformation",
    "declared basis transformation",
    "supported normalization transformation",
)


class EquivalenceError(EpistemicError):
    pass


def certify_rule(*, rule_id: str, certificate: str, scope: str) -> dict[str, Any]:
    if rule_id not in CERTIFIED_RULES:
        return freeze_document(
            {
                "certificate": None,
                "outcome": "EQUIVALENCE_UNSUPPORTED",
                "rule_id": rule_id,
                "scope": scope,
            }
        )
    if not certificate:
        return freeze_document(
            {
                "certificate": None,
                "outcome": "EQUIVALENCE_UNSUPPORTED",
                "rule_id": rule_id,
                "scope": scope,
            }
        )
    return freeze_document(
        {
            "certificate": certificate,
            "outcome": "CERTIFIED",
            "rule_id": rule_id,
            "scope": scope,
        }
    )


def same_output_is_not_equivalence(left_id: str, right_id: str) -> dict[str, Any]:
    return certify_rule(
        rule_id="output coincidence",
        certificate="",
        scope=left_id + " ~ " + right_id,
    )
