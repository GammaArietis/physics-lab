"""Search policy is separate from the grammar of legal theories.

A policy chooses an order. It does not encode a physical preference.
"""

from __future__ import annotations

TRAVERSAL_POLICIES = (
    "breadth-first",
    "depth-first",
    "deterministic lexicographic",
    "bounded sampling",
)

FORBIDDEN_POLICY_CRITERIA = (
    "aesthetic preference",
    "numerical resemblance",
    "physics preference",
)


def assert_policy_is_structural(policy: str) -> str:
    if policy not in TRAVERSAL_POLICIES:
        raise ValueError(policy)
    return policy
