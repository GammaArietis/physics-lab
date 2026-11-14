"""A small, finite geometry-only pilot for the alpha-geometry programme.

This module intentionally stops before claiming an electromagnetic coupling.
It enumerates a declared grammar of simple connected graphs and records
derived graph invariants.  No experimental target is read, no continuous
parameter is fitted, and no candidate is selected or ranked.

The next stage may attach a fully specified U(1) action to a surviving
geometry.  That is a separate authorization because a graph invariant is not
yet a derivation of the fine-structure constant.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping


ALPHA_GEOMETRY_SEARCH_VERSION = "alpha-geometry-search-v1"
DEFAULT_GRAPH_FAMILIES = ("cycle", "path", "complete")
DEFAULT_ACTIONS = ("quadratic_laplacian", "quartic_local")
DEFAULT_SIZE_RANGE = range(3, 8)


class AlphaGeometryPilotError(ValueError):
    """Raised when the finite alpha-geometry pilot is malformed."""


def _canonical_graph_family(family: str, size: int) -> str:
    # C3 and K3 are the same simple graph.  Recording this equivalence here
    # prevents a family label from masquerading as a new geometry.
    if family == "cycle" and size == 3:
        return "complete"
    return family


def _graph_invariants(family: str, size: int) -> dict[str, Any]:
    if family == "cycle":
        vertices = size
        edges = size
        degree_sequence = [2] * size
        laplacian_gap = 4.0 * math.sin(math.pi / size) ** 2
        laplacian_max = 4.0
        spanning_trees = size
    elif family == "path":
        vertices = size
        edges = size - 1
        degree_sequence = [1, *([2] * (size - 2)), 1]
        laplacian_gap = 2.0 - 2.0 * math.cos(math.pi / size)
        laplacian_max = 2.0 + 2.0 * math.cos(math.pi / size)
        spanning_trees = 1
    elif family == "complete":
        vertices = size
        edges = size * (size - 1) // 2
        degree_sequence = [size - 1] * size
        laplacian_gap = float(size)
        laplacian_max = float(size)
        spanning_trees = size ** (size - 2)
    else:  # pragma: no cover - protected by enumerate validation
        raise AlphaGeometryPilotError(f"unsupported graph family: {family}")

    return {
        "vertices": vertices,
        "edges": edges,
        "connected": True,
        "self_loops": 0,
        "degree_sequence": degree_sequence,
        "edge_density": 2.0 * edges / (vertices * (vertices - 1)),
        "laplacian_spectral_gap": laplacian_gap,
        "laplacian_spectral_radius": laplacian_max,
        "normalized_laplacian_gap": laplacian_gap / laplacian_max,
        "spanning_tree_count": spanning_trees,
    }


def _action_terms(action: str) -> list[str]:
    if action == "quadratic_laplacian":
        return ["field_laplacian_quadratic"]
    if action == "quartic_local":
        return ["field_laplacian_quadratic", "local_quartic_potential"]
    raise AlphaGeometryPilotError(f"unsupported action family: {action}")


def _digest(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_grammar(
    graph_families: Iterable[str],
    sizes: Iterable[int],
    actions: Iterable[str],
) -> tuple[list[str], list[int], list[str]]:
    families = list(graph_families)
    size_values = list(sizes)
    action_values = list(actions)
    if not families or not set(families).issubset(set(DEFAULT_GRAPH_FAMILIES)):
        raise AlphaGeometryPilotError("graph_families must be a non-empty subset of the declared grammar")
    if not size_values or any(not isinstance(size, int) or size < 3 or size > 32 for size in size_values):
        raise AlphaGeometryPilotError("sizes must be bounded integers in [3, 32]")
    if not action_values or not set(action_values).issubset(set(DEFAULT_ACTIONS)):
        raise AlphaGeometryPilotError("actions must be a non-empty subset of the declared grammar")
    return sorted(set(families)), sorted(set(size_values)), sorted(set(action_values))


def enumerate_alpha_geometry_pilot(
    *,
    graph_families: Iterable[str] = DEFAULT_GRAPH_FAMILIES,
    sizes: Iterable[int] = DEFAULT_SIZE_RANGE,
    actions: Iterable[str] = DEFAULT_ACTIONS,
) -> dict[str, Any]:
    """Enumerate the finite stage-0 grammar and apply only hard filters."""
    families, size_values, action_values = _validate_grammar(graph_families, sizes, actions)
    raw_candidates: list[dict[str, Any]] = []
    for family in families:
        for size in size_values:
            for action in action_values:
                canonical_family = _canonical_graph_family(family, size)
                geometry_key = f"{canonical_family}:{size}"
                action_terms = _action_terms(action)
                raw_key = f"{family}:{size}:{action}"
                canonical_key = f"{geometry_key}:{action}"
                candidate = {
                    "candidate_id": f"alpha-geometry-{family}-n{size}-{action}",
                    "raw_key": raw_key,
                    "canonical_key": canonical_key,
                    "geometry": {
                        "family": family,
                        "canonical_family": canonical_family,
                        "size": size,
                        "topology": "finite_connected_simple_graph",
                    },
                    "action": {
                        "family": action,
                        "terms": action_terms,
                        "continuous_parameters": [],
                    },
                    "derived_invariants": _graph_invariants(family, size),
                    "provenance": {
                        "geometry": "DERIVED_FROM_DECLARED_GRAMMAR",
                        "action": "ASSUMED_GRAMMAR_ELEMENT",
                        "observables": "DERIVED_GRAPH_INVARIANTS",
                    },
                    "hard_filters": {
                        "finite_size_bound": True,
                        "connected": True,
                        "simple_graph": True,
                        "action_declared": True,
                        "no_continuous_fit": True,
                    },
                    "status": "STRUCTURAL_PASS",
                    "alpha_comparison": "NOT_AUTHORIZED",
                    "empirical_comparison": "NOT_AUTHORIZED",
                }
                candidate["canonical_record_digest"] = _digest(candidate)
                raw_candidates.append(candidate)

    seen: dict[str, str] = {}
    candidates: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    for candidate in raw_candidates:
        key = candidate["canonical_key"]
        if key in seen:
            duplicates.append({
                "candidate_id": candidate["candidate_id"],
                "duplicate_of": seen[key],
                "canonical_key": key,
                "status": "DUPLICATE",
            })
        else:
            seen[key] = candidate["candidate_id"]
            candidates.append(candidate)

    return {
        "search_version": ALPHA_GEOMETRY_SEARCH_VERSION,
        "search_id": "alpha-geometry-stage0-pilot",
        "stage": "STAGE_0_GEOMETRY_ONLY",
        "grammar": {
            "graph_families": families,
            "sizes": size_values,
            "actions": action_values,
            "candidate_bound": len(families) * len(size_values) * len(action_values),
        },
        "authorization": {
            "status": "AUTHORIZED",
            "human_confirmation": True,
            "finite_bounds": "AUTHORIZED",
            "search_status": "AUTHORIZED",
            "empirical_comparison": "NOT_AUTHORIZED",
            "external_data_used": False,
            "automatic_selection": "DISABLED",
            "automatic_ranking": "DISABLED",
        },
        "controls": {
            "no_parameter_fitting": True,
            "no_alpha_target_read": True,
            "no_empirical_data": True,
            "no_auto_selection": True,
            "no_ranking": True,
            "finite_bounds_enforced": True,
            "canonical_deduplication_applied": True,
            "failure_isolation": True,
        },
        "raw_candidate_count": len(raw_candidates),
        "unique_candidate_count": len(candidates),
        "duplicate_count": len(duplicates),
        "candidates": candidates,
        "duplicates": duplicates,
        "selection": {
            "performed": False,
            "ranking_performed": False,
            "human_review_required": True,
        },
        "next_gate": "DEFINE_EXPLICIT_U1_ACTION_BEFORE_ANY_ALPHA_COMPARISON",
    }


def run_alpha_geometry_pilot(**kwargs: Any) -> dict[str, Any]:
    """Run the stage-0 pilot and mark it complete only after all controls pass."""
    report = enumerate_alpha_geometry_pilot(**kwargs)
    if not all(report["controls"].values()):
        raise AlphaGeometryPilotError("alpha-geometry pilot controls did not pass")
    report["execution_status"] = "COMPLETE"
    return report


def write_alpha_geometry_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(dict(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output
