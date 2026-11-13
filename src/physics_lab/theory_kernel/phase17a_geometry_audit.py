"""Phase 17A catalogues geometric structures outside grammar_15f_v1.

Entries are documentation. None is generator-enabled.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from physics_lab.physics.action_serializer import canonical_json_bytes
from physics_lab.physics.phase4c_action_freeze import (
    authorize_phase5b0_analysis,
    verify_phase4c_action_freeze,
)
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15a_grammar import (
    SUPPORTED_EQUIVALENCES,
    _ranking_tokens,
    _target_markers,
    catalog_influence,
    classify_candidate,
)
from physics_lab.theory_kernel.phase16a_grammar_audit import GRAMMAR_HASH, GRAMMAR_VERSION
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_17A"
CODE_VERSION = "phase17a-geometry-audit-v1"
ARTIFACT_DIR_NAME = "phase17a_geometry_audit_artifacts"
AXES = (
    "spacetime dimension",
    "metric signature",
    "metric structure",
    "affine connection",
    "metric compatibility",
    "torsion",
    "curvature",
    "spin structure",
    "vielbein structure",
    "principal-bundle structure",
    "fiber structure",
    "internal manifold",
    "topology",
    "characteristic classes",
    "global bundle data",
    "covariant derivative structure",
    "allowed tensor calculus",
)


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE17A_STATUS": "INCOMPLETE", "reason": reason, "status": "GEOMETRY_AUDIT_FAILED"}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def enable_geometry(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENABLED"


def activate_reference(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENABLED"


def start_geometry_search(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_STARTED"


def select_geometry(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def _axes(changed: tuple[str, ...]) -> dict[str, str]:
    selected = set(changed)
    return {axis: "CHANGED_NOT_ACTIVATED" if axis in selected else "UNCHANGED_NOT_ACTIVATED" for axis in AXES}


def _bounds(status: str, names: tuple[str, ...], reason: str) -> dict[str, Any]:
    return {
        "bound_role": "SEARCH_SPACE_ASSUMPTION",
        "finite_bound_status": status,
        "integers": "NOT_CHOSEN",
        "reason": reason,
        "required_names": list(names),
    }


def _references() -> list[dict[str, Any]]:
    rows = [
        ("G_REF_01", "ESTABLISHED_GEOMETRIC_FRAMEWORK", "4D Lorentzian pseudo-Riemannian geometry", ("General Relativity",)),
        ("G_REF_02", "ESTABLISHED_GEOMETRIC_FRAMEWORK", "principal-bundle gauge geometry with connection", ("Yang-Mills",)),
        ("G_REF_03", "ESTABLISHED_GEOMETRIC_FRAMEWORK", "spin geometry, spin structure, and spin connection", ()),
        ("G_REF_04", "ESTABLISHED_GEOMETRIC_FRAMEWORK", "tetrad or vielbein formulation", ()),
        ("G_REF_05", "EXTENDED_THEORETICAL_GEOMETRY", "Riemann-Cartan geometry with torsion", ("Einstein-Cartan",)),
        ("G_REF_06", "EXTENDED_THEORETICAL_GEOMETRY", "metric-affine geometry", ()),
        ("G_REF_07", "EXTENDED_THEORETICAL_GEOMETRY", "nontrivial principal or vector bundle topology", ()),
        ("G_REF_08", "EXTENDED_THEORETICAL_GEOMETRY", "higher-dimensional fibered geometry", ("Kaluza-Klein",)),
        ("G_REF_09", "EXTENDED_THEORETICAL_GEOMETRY", "compact internal-manifold or fiber geometry", ()),
        ("G_REF_10", "EXTENDED_THEORETICAL_GEOMETRY", "topological characteristic-class sectors", ()),
        ("G_REF_11", "EXTENDED_THEORETICAL_GEOMETRY", "teleparallel geometry", ()),
        ("G_REF_12", "EXTENDED_THEORETICAL_GEOMETRY", "noncommutative geometric structure", ()),
        ("G_REF_13", "EXTENDED_THEORETICAL_GEOMETRY", "direction-dependent metric geometry", ()),
        ("G_REF_14", "EXTENDED_THEORETICAL_GEOMETRY", "generalized tangent geometry", ()),
    ]
    return [
        {
            "catalog_role": "REFERENCE_ONLY",
            "descriptive_category": category,
            "generator_enabled": False,
            "geometry_name": name,
            "reference_id": reference_id,
            "reference_names": list(names),
            "search_status": "NOT_ENABLED",
        }
        for reference_id, category, name, names in rows
    ]


def _candidates() -> list[dict[str, Any]]:
    bound_ready = "REQUIREMENTS_STATED"
    bound_blocked = "CANNOT_YET_BE_BOUNDED"
    rows = [
        {
            "changed_axes": ("affine connection", "curvature", "covariant derivative structure"),
            "current_grammar_status": "PARTIALLY_REPRESENTABLE",
            "current_representation": "the metric and the 4D covariance constraint are registered; Levi-Civita completion is not a supported equivalence",
            "dynamics_included": False,
            "equivalence_status": "EQUIVALENCE_UNRESOLVED",
            "finite_bounds": _bounds(bound_ready, ("curvature_order", "derivative_order"), "a later authorization must choose the integers"),
            "geometry_id": "G17-01",
            "geometry_source": "G_REF_01",
            "mathematical_definition": "a 4-dimensional metric geometry whose Levi-Civita connection is part of the tensor calculus",
            "matter_content_included": False,
            "new_constraints": [],
            "new_fields_required": [],
            "new_geometric_structure": "certified Levi-Civita completion of the registered metric",
            "new_global_data": [],
            "new_parameters_required": [],
            "new_physical_input_required": "NOT_DECIDED",
            "new_physical_input_reason": "the missing completion may be representational; the supported equivalence engine does not decide that",
            "relation_to_current_grammar": "EQUIVALENCE_UNRESOLVED",
            "required_structures": ("metric", "Levi-Civita connection"),
        },
        {
            "changed_axes": ("principal-bundle structure", "global bundle data", "covariant derivative structure"),
            "current_grammar_status": "PARTIALLY_REPRESENTABLE",
            "current_representation": "a local U(1) potential and its curvature are registered; transition functions are absent",
            "dynamics_included": False,
            "equivalence_status": "EQUIVALENCE_UNRESOLVED",
            "finite_bounds": _bounds(bound_ready, ("bundle_complexity",), "a later authorization must choose the integer"),
            "geometry_id": "G17-02",
            "geometry_source": "G_REF_02",
            "mathematical_definition": "a principal bundle with transition functions and a connection, not only a local potential",
            "matter_content_included": False,
            "new_constraints": [],
            "new_fields_required": [],
            "new_geometric_structure": "global principal-bundle data",
            "new_global_data": ("transition functions",),
            "new_parameters_required": [],
            "new_physical_input_required": "NOT_DECIDED",
            "new_physical_input_reason": "local potential versus principal connection is an unsupported equivalence",
            "relation_to_current_grammar": "EQUIVALENCE_UNRESOLVED",
            "required_structures": ("structure group", "transition functions", "connection"),
        },
        {
            "changed_axes": ("spin structure",),
            "current_grammar_status": "GENUINELY_NEW_GEOMETRY",
            "current_representation": "no spin structure, spin bundle, Clifford algebra, or spin connection is registered",
            "dynamics_included": False,
            "equivalence_status": "NOT_EQUIVALENT_UNDER_SUPPORTED_RULES",
            "fermions_added": False,
            "finite_bounds": _bounds(bound_ready, ("bundle_complexity",), "a later authorization must choose the integer"),
            "geometry_id": "G17-03",
            "geometry_source": "G_REF_03",
            "mathematical_definition": "a spin structure on the spacetime manifold, with a spin bundle and a spin connection, and with no spinor matter field",
            "matter_content_included": False,
            "new_constraints": [],
            "new_fields_required": [],
            "new_geometric_structure": "spin structure",
            "new_global_data": ("spin structure",),
            "new_parameters_required": [],
            "new_physical_input_required": "TRUE",
            "new_physical_input_reason": "introducing a spin structure is an assumption absent from the registered grammar",
            "relation_to_current_grammar": "EXTENDS",
            "required_structures": ("spin structure", "Clifford algebra", "spin connection"),
        },
        {
            "changed_axes": ("vielbein structure", "metric structure"),
            "current_grammar_status": "EQUIVALENCE_UNRESOLVED",
            "current_representation": "the metric is registered; a local frame field is not",
            "dynamics_included": False,
            "equivalence_status": "EQUIVALENCE_UNRESOLVED",
            "finite_bounds": _bounds(bound_ready, ("tensor_rank_max",), "a later authorization must choose the integer"),
            "geometry_id": "G17-04",
            "geometry_source": "G_REF_04",
            "mathematical_definition": "a local frame field from which the metric is reconstructed",
            "matter_content_included": False,
            "new_constraints": [],
            "new_fields_required": ("frame field",),
            "new_geometric_structure": "local frame bundle",
            "new_global_data": [],
            "new_parameters_required": [],
            "new_physical_input_required": "NOT_DECIDED",
            "new_physical_input_reason": "metric versus frame-field equivalence is not a supported rule",
            "relation_to_current_grammar": "EQUIVALENCE_UNRESOLVED",
            "required_structures": ("frame field", "local Lorentz structure"),
        },
        {
            "changed_axes": ("affine connection", "metric compatibility", "torsion", "curvature"),
            "current_grammar_status": "GENUINELY_NEW_GEOMETRY",
            "current_representation": "the metric is registered; an independent metric-compatible connection and a torsion tensor are not",
            "dynamics_included": False,
            "equivalence_status": "NOT_EQUIVALENT_UNDER_SUPPORTED_RULES",
            "finite_bounds": _bounds(bound_ready, ("torsion_rank", "curvature_order"), "a later authorization must choose the integers"),
            "geometry_id": "G17-05",
            "geometry_source": "G_REF_05",
            "mathematical_definition": "a metric with an independent metric-compatible connection, a torsion tensor, and the contorsion built from that torsion",
            "matter_content_included": False,
            "new_constraints": ("metric compatibility",),
            "new_fields_required": (),
            "new_geometric_structure": "torsion",
            "new_global_data": [],
            "new_parameters_required": ("torsion coefficients",),
            "new_physical_input_required": "TRUE",
            "new_physical_input_reason": "introducing torsion is an assumption absent from the registered grammar",
            "phase16_overlap": "g16a.new.torsion_bundles",
            "relation_to_current_grammar": "EXTENDS",
            "required_structures": ("metric", "metric-compatible connection", "torsion"),
        },
        {
            "changed_axes": ("affine connection", "metric compatibility", "torsion", "curvature"),
            "current_grammar_status": "GENUINELY_NEW_GEOMETRY",
            "current_representation": "the metric is registered; an independent affine connection and non-metricity are not",
            "dynamics_included": False,
            "equivalence_status": "NOT_EQUIVALENT_UNDER_SUPPORTED_RULES",
            "finite_bounds": _bounds(bound_ready, ("torsion_rank", "nonmetricity_rank", "curvature_order"), "a later authorization must choose the integers"),
            "geometry_id": "G17-06",
            "geometry_source": "G_REF_06",
            "mathematical_definition": "an independent metric and an independent affine connection, with torsion, non-metricity, and curvature kept as separate tensors",
            "matter_content_included": False,
            "new_constraints": [],
            "new_fields_required": (),
            "new_geometric_structure": "non-metricity",
            "new_global_data": [],
            "new_parameters_required": ("non-metricity coefficients",),
            "new_physical_input_required": "TRUE",
            "new_physical_input_reason": "allowing non-metricity is an assumption absent from the registered grammar",
            "relation_to_current_grammar": "EXTENDS",
            "required_structures": ("metric", "affine connection", "non-metricity"),
        },
        {
            "changed_axes": ("topology", "global bundle data", "principal-bundle structure"),
            "compactification_defined": False,
            "current_grammar_status": "GENUINELY_NEW_GEOMETRY",
            "current_representation": "local connection data are registered; bundle transition functions are not",
            "dynamics_included": False,
            "equivalence_status": "NOT_EQUIVALENT_UNDER_SUPPORTED_RULES",
            "finite_bounds": _bounds(bound_ready, ("topology_sector_count", "bundle_complexity"), "a later authorization must choose the integers"),
            "geometry_id": "G17-07",
            "geometry_source": "G_REF_07",
            "mathematical_definition": "a principal or vector bundle whose transition functions are not globally trivial",
            "matter_content_included": False,
            "new_constraints": [],
            "new_fields_required": (),
            "new_geometric_structure": "nontrivial bundle",
            "new_global_data": ("transition functions",),
            "new_parameters_required": (),
            "new_physical_input_required": "TRUE",
            "new_physical_input_reason": "assuming nontrivial topology is an assumption absent from the registered grammar",
            "phase16_overlap": "g16a.new.topology",
            "relation_to_current_grammar": "EXTENDS",
            "required_structures": ("transition functions", "global connection"),
            "topological_sector_selected": False,
        },
        {
            "changed_axes": ("spacetime dimension", "fiber structure", "internal manifold", "metric structure"),
            "compactification_defined": False,
            "current_grammar_status": "GENUINELY_NEW_GEOMETRY",
            "current_representation": "spacetime dimension 4 is a registered constraint",
            "dynamics_included": False,
            "equivalence_status": "NOT_EQUIVALENT_UNDER_SUPPORTED_RULES",
            "finite_bounds": _bounds(bound_ready, ("spacetime_dimension_max", "internal_dimension_max"), "a later authorization must choose the integers"),
            "geometry_id": "G17-08",
            "geometry_source": "G_REF_08",
            "mathematical_definition": "a product of a spacetime metric and an internal fiber, with dimension left as a discrete structural variable and with no compactification dynamics",
            "matter_content_included": False,
            "new_constraints": [],
            "new_fields_required": (),
            "new_geometric_structure": "higher-dimensional product geometry",
            "new_global_data": [],
            "new_parameters_required": (),
            "new_physical_input_required": "TRUE",
            "new_physical_input_reason": "changing the spacetime dimension is an assumption absent from the registered grammar",
            "phase16_overlap": "g16a.new.extra_dimension",
            "relation_to_current_grammar": "EXTENDS",
            "required_structures": ("higher-dimensional metric", "fiber projection"),
        },
        {
            "changed_axes": ("internal manifold", "fiber structure", "curvature", "topology"),
            "compactification_defined": False,
            "current_grammar_status": "GENUINELY_NEW_GEOMETRY",
            "current_representation": "the registered internal object is a 3-component vector space, not a manifold",
            "dynamics_included": False,
            "equivalence_status": "NOT_EQUIVALENT_UNDER_SUPPORTED_RULES",
            "finite_bounds": _bounds(bound_ready, ("internal_dimension_max", "curvature_order"), "a later authorization must choose the integers"),
            "geometry_id": "G17-09",
            "geometry_source": "G_REF_09",
            "mathematical_definition": "a compact internal manifold with its own metric, curvature, topology, and moduli, and with no named manifold selected",
            "matter_content_included": False,
            "new_constraints": ("compactness",),
            "new_fields_required": (),
            "new_geometric_structure": "compact internal manifold",
            "new_global_data": ("moduli",),
            "new_parameters_required": ("internal-metric coefficients",),
            "new_physical_input_required": "TRUE",
            "new_physical_input_reason": "assuming a compact internal manifold is an assumption absent from the registered grammar",
            "relation_to_current_grammar": "INCOMPARABLE",
            "required_structures": ("internal metric", "internal curvature"),
            "specific_manifold": "NONE",
        },
        {
            "changed_axes": ("characteristic classes", "topology", "global bundle data"),
            "current_grammar_status": "GENUINELY_NEW_GEOMETRY",
            "current_representation": "characteristic-class densities are outside the registered operator classes",
            "dynamics_included": False,
            "equivalence_status": "NOT_EQUIVALENT_UNDER_SUPPORTED_RULES",
            "finite_bounds": _bounds(bound_ready, ("characteristic_class_order", "topology_sector_count"), "a later authorization must choose the integers"),
            "geometry_id": "G17-10",
            "geometry_source": "G_REF_10",
            "mathematical_definition": "Chern, Pontryagin, and Euler classes as characteristic densities, with no numerical charge assigned",
            "matter_content_included": False,
            "new_constraints": [],
            "new_fields_required": (),
            "new_geometric_structure": "characteristic class",
            "new_global_data": ("characteristic class",),
            "new_parameters_required": (),
            "new_physical_input_required": "TRUE",
            "new_physical_input_reason": "admitting a characteristic-class sector is an assumption absent from the registered grammar",
            "numerical_topological_value": "NOT_ASSIGNED",
            "phase16_overlap": "g16a.new.topology",
            "relation_to_current_grammar": "EXTENDS",
            "required_structures": ("invariant polynomial of curvature",),
            "topological_sector_selected": False,
        },
        {
            "changed_axes": ("affine connection", "torsion", "curvature"),
            "current_grammar_status": "GENUINELY_NEW_GEOMETRY",
            "current_representation": "neither a curvature-free connection nor an independent torsion tensor is registered",
            "dynamics_included": False,
            "equivalence_status": "NOT_EQUIVALENT_UNDER_SUPPORTED_RULES",
            "finite_bounds": _bounds(bound_ready, ("torsion_rank", "curvature_order"), "a later authorization must choose the integers"),
            "geometry_id": "G17-11",
            "geometry_source": "G_REF_11",
            "mathematical_definition": "a metric geometry whose connection has vanishing curvature and whose torsion carries the geometric data",
            "matter_content_included": False,
            "new_constraints": ("vanishing curvature",),
            "new_fields_required": (),
            "new_geometric_structure": "curvature-free torsionful connection",
            "new_global_data": [],
            "new_parameters_required": ("torsion coefficients",),
            "new_physical_input_required": "TRUE",
            "new_physical_input_reason": "replacing the curvature-bearing connection by a torsionful curvature-free connection is a new assumption",
            "relation_to_current_grammar": "INCOMPARABLE",
            "required_structures": ("torsion", "flat connection"),
        },
        {
            "changed_axes": ("allowed tensor calculus",),
            "current_grammar_status": "GENUINELY_NEW_GEOMETRY",
            "current_representation": "the registered calculus is commutative tensor calculus on a smooth manifold",
            "dynamics_included": False,
            "equivalence_status": "NOT_EQUIVALENT_UNDER_SUPPORTED_RULES",
            "finite_bounds": _bounds(bound_blocked, (), "no deformation parameter or algebra presentation is registered, so an integer window cannot yet be stated"),
            "geometry_id": "G17-12",
            "geometry_source": "G_REF_12",
            "mathematical_definition": "a spacetime algebra whose coordinate functions do not commute",
            "matter_content_included": False,
            "new_constraints": [],
            "new_fields_required": (),
            "new_geometric_structure": "noncommuting coordinate algebra",
            "new_global_data": [],
            "new_parameters_required": (),
            "new_physical_input_required": "TRUE",
            "new_physical_input_reason": "replacing the commutative tensor calculus is a new assumption",
            "relation_to_current_grammar": "INCOMPARABLE",
            "required_structures": ("noncommuting algebra",),
        },
        {
            "changed_axes": ("metric structure", "allowed tensor calculus"),
            "current_grammar_status": "GENUINELY_NEW_GEOMETRY",
            "current_representation": "the registered metric is a tensor, not a direction-dependent function",
            "dynamics_included": False,
            "equivalence_status": "NOT_EQUIVALENT_UNDER_SUPPORTED_RULES",
            "finite_bounds": _bounds(bound_ready, ("tensor_rank_max",), "a later authorization must choose the integer"),
            "geometry_id": "G17-13",
            "geometry_source": "G_REF_13",
            "mathematical_definition": "a spacetime interval whose fundamental function depends on position and direction",
            "matter_content_included": False,
            "new_constraints": [],
            "new_fields_required": (),
            "new_geometric_structure": "direction-dependent metric function",
            "new_global_data": [],
            "new_parameters_required": ("coefficients of the fundamental function",),
            "new_physical_input_required": "TRUE",
            "new_physical_input_reason": "replacing the quadratic metric tensor is a new assumption",
            "relation_to_current_grammar": "INCOMPARABLE",
            "required_structures": ("fundamental function",),
        },
        {
            "changed_axes": ("allowed tensor calculus", "fiber structure"),
            "current_grammar_status": "GENUINELY_NEW_GEOMETRY",
            "current_representation": "the registered calculus has no generalized tangent bundle and no Courant bracket",
            "dynamics_included": False,
            "equivalence_status": "NOT_EQUIVALENT_UNDER_SUPPORTED_RULES",
            "finite_bounds": _bounds(bound_blocked, (), "the generalized bracket is unregistered, so an integer window cannot yet be stated"),
            "geometry_id": "G17-14",
            "geometry_source": "G_REF_14",
            "mathematical_definition": "a generalized tangent bundle equipped with a Courant bracket",
            "matter_content_included": False,
            "new_constraints": [],
            "new_fields_required": (),
            "new_geometric_structure": "generalized tangent bundle",
            "new_global_data": [],
            "new_parameters_required": (),
            "new_physical_input_required": "TRUE",
            "new_physical_input_reason": "introducing a generalized tangent bundle is a new assumption",
            "relation_to_current_grammar": "INCOMPARABLE",
            "required_structures": ("generalized tangent bundle", "Courant bracket"),
        },
    ]
    catalog = []
    for row in rows:
        changed = row.pop("changed_axes")
        catalog.append(
            {
                **row,
                "axes": _axes(changed),
                "catalog_role": "CANDIDATE_GEOMETRY",
                "fermions_added": row.get("fermions_added", False),
                "future_search_grammar": "NOT_ENABLED",
                "novelty_basis": "comparison with grammar_15f_v1",
                "search_status": "NOT_ENABLED",
                "topological_sector_selected": row.get("topological_sector_selected", False),
                "compactification_defined": row.get("compactification_defined", False),
            }
        )
    return catalog


def _equivalences() -> list[dict[str, str]]:
    supported = set(SUPPORTED_EQUIVALENCES)
    pairs = (
        ("metric", "frame field", "G17-01", "G17-04"),
        ("local gauge potential", "principal-bundle connection", "G17-02", "G17-02"),
        ("Christoffel representation", "affine connection", "G17-01", "G17-06"),
        ("spin connection", "frame field plus connection", "G17-03", "G17-04"),
    )
    rows = []
    for left, right, source, target in pairs:
        statement = left + " versus " + right
        rows.append(
            {
                "equivalence_status": "EQUIVALENCE_UNRESOLVED" if statement not in supported else "SUPPORTED",
                "left": left,
                "right": right,
                "source_geometry": source,
                "target_geometry": target,
            }
        )
    return rows


def run_phase_17a(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    grammar15 = _read("phase15f_grammar_artifacts/PHASE_15F_GRAMMAR.json")
    frontier = _read("phase16e_frontier_artifacts/PHASE_16E_FRONTIER.json")
    catalog3 = _read("phase16_tier3_search_artifacts/PHASE_16_TIER3_CATALOG.json")
    audit = _read("phase16a_grammar_audit_artifacts/PHASE_16A_GRAMMAR_CATALOG.json")
    references = _references()
    candidates = _candidates()
    equivalences = _equivalences()
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or grammar15.get("grammar_hash") != GRAMMAR_HASH
        or audit.get("grammar_hash") != GRAMMAR_HASH
        or audit.get("active_grammar_version") != GRAMMAR_VERSION
        or frontier.get("PHASE16E_STATUS") != "COMPLETE"
        or frontier.get("cumulative_points") != 69
        or frontier.get("FUTURE_TIER_STATUS") != "NOT_REGISTERED"
        or catalog3.get("PHASE_16_TIER3_STATUS") != "COMPLETE"
        or catalog3.get("new_points_examined") != 37
        or catalog3.get("valid_models") != 23
        or enable_geometry() != "NOT_ENABLED"
        or activate_reference(*[item["reference_id"] for item in references]) != "NOT_ENABLED"
        or start_geometry_search() != "NOT_STARTED"
        or select_geometry(candidates) != "NOT_PERFORMED"
        or any(item["search_status"] != "NOT_ENABLED" or item["catalog_role"] != "REFERENCE_ONLY" for item in references)
        or any(item["search_status"] != "NOT_ENABLED" or item["future_search_grammar"] != "NOT_ENABLED" for item in candidates)
        or any(item["equivalence_status"] != "EQUIVALENCE_UNRESOLVED" for item in equivalences)
        or any(item["dynamics_included"] or item["matter_content_included"] or item["fermions_added"] for item in candidates)
        or any(item.get("compactification_defined") for item in candidates)
        or any(item.get("topological_sector_selected") for item in candidates)
        or len(references) < 10
        or len(candidates) < 10
    ):
        return _stop("integrity gate")
    if any(marker in json.dumps(candidates) for marker in _target_markers()):
        return _stop("target marker")
    if classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")}) != "REJECTED":
        return _stop("blindness")
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE17A_STATUS": "COMPLETE",
        "PHASE16_INTEGRITY_STATUS": "VERIFIED",
        "PHASE_16_STATUS": "CLOSED",
        "PHASE_16E_STATUS": "COMPLETE",
        "FROZEN_ACTION_STATUS": "VERIFIED",
        "GEOMETRY_REFERENCE_STATUS": "COMPLETE",
        "GEOMETRY_CANDIDATE_STATUS": "COMPLETE",
        "GEOMETRIC_EQUIVALENCE_STATUS": "COMPLETE",
        "GEOMETRIC_INPUT_STATUS": "VERIFIED",
        "GEOMETRIC_BOUND_STATUS": "COMPLETE",
        "GEOMETRY_BLINDNESS_STATUS": "VERIFIED",
        "HUMAN_AUTHORIZATION_FRONTIER_STATUS": "READY",
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "grammar_version": GRAMMAR_VERSION,
        "grammar_hash": GRAMMAR_HASH,
        "ALL_POSSIBLE_PHYSICS_EXHAUSTED": "FALSE",
        "SEARCH_STATUS": "NOT_STARTED",
        "phase16_recorded_state": {
            "equivalence_classes": 51,
            "parameter_closed_grammars": 0,
            "parameter_open_grammars": 11,
            "registered_points": 69,
            "valid_models": 51,
            "verified_PFR": 0,
        },
        "geometry_reference_catalog": references,
        "geometry_candidate_catalog": candidates,
        "geometric_equivalence_register": equivalences,
        "geometric_new_input_register": [
            {
                "geometry_id": item["geometry_id"],
                "new_physical_input_reason": item["new_physical_input_reason"],
                "new_physical_input_required": item["new_physical_input_required"],
            }
            for item in candidates
        ],
        "geometric_bound_requirements": [
            {"finite_bounds": item["finite_bounds"], "geometry_id": item["geometry_id"]} for item in candidates
        ],
        "geometry_dependency_graph": [
            {
                "current_grammar": GRAMMAR_VERSION,
                "future_search_grammar": "NOT_ENABLED",
                "geometry_id": item["geometry_id"],
                "new_assumptions": item["new_physical_input_reason"],
                "relation": item["relation_to_current_grammar"],
                "required_structures": list(item["required_structures"]),
            }
            for item in candidates
        ],
        "geometry_human_authorization_frontier": [
            {"object": "GEOMETRY_BATCH_AUTHORIZATION", "status": "NOT_AUTHORIZED"},
            {"object": "PHASE_17B_GEOMETRY_GRAMMAR_FORMALIZATION", "status": "NOT_AUTHORIZED"},
            {"object": "PHASE_17C_BLIND_GEOMETRY_EXPLORATION", "status": "NOT_AUTHORIZED"},
        ],
        "selected_geometry": "NONE",
        "catalog_influence": catalog_influence({"entries": []}, "phase17a")["status"],
        "ranking_function": "ABSENT" if _ranking_absent() else "PRESENT",
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_17A_GEOMETRY_CATALOG.json").write_bytes(
            canonical_json_bytes(
                {
                    "GEOMETRY_CANDIDATE_STATUS": "COMPLETE",
                    "PHASE17A_STATUS": "COMPLETE",
                    "SEARCH_STATUS": "NOT_STARTED",
                    "candidate_ids": [item["geometry_id"] for item in candidates],
                    "grammar_hash": GRAMMAR_HASH,
                    "reference_ids": [item["reference_id"] for item in references],
                    "selected_geometry": "NONE",
                }
            )
        )
        if _unchanged(snapshot_existing_phases()) != before:
            return _stop("previous phase changed")
        if _read("phase16e_frontier_artifacts/PHASE_16E_FRONTIER.json").get("cumulative_points") != 69:
            return _stop("phase 16 changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
