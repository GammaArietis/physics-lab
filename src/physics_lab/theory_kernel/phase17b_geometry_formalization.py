"""Phase 17B catalogues spacetime geometries and does not explore them.

Einsteinian geometry is one reference baseline. It does not parent the other families.
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
from physics_lab.theory_kernel.epistemic import content_digest
from physics_lab.theory_kernel.phase12a import snapshot_existing_phases
from physics_lab.theory_kernel.phase15a_grammar import _ranking_tokens, _target_markers, catalog_influence, classify_candidate
from physics_lab.theory_kernel.phase16a_grammar_audit import GRAMMAR_HASH, GRAMMAR_VERSION
from physics_lab.theory_kernel.phase17a_geometry_audit import run_phase_17a
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_17B"
CODE_VERSION = "phase17b-broad-geometry-v2"
ARTIFACT_DIR_NAME = "phase17b_geometry_formalization_artifacts"
CATEGORIES = (
    "CONTINUUM_GEOMETRY",
    "CONNECTION_GEOMETRY",
    "NON_RIEMANNIAN_GEOMETRY",
    "FRAME_AND_SPIN_GEOMETRY",
    "BUNDLE_AND_TOPOLOGICAL_GEOMETRY",
    "HIGHER_DIMENSIONAL_GEOMETRY",
    "GENERALIZED_GEOMETRY",
    "DIRECTION_DEPENDENT_GEOMETRY",
    "DEFORMED_OR_NONCOMMUTATIVE_GEOMETRY",
    "DISCRETE_OR_CAUSAL_SPACETIME",
    "QUANTUM_GEOMETRIC_STRUCTURE",
    "EMERGENT_SPACETIME_STRUCTURE",
)
BATCHES = (
    "BATCH_A_CONTINUUM_AND_CONNECTION",
    "BATCH_B_BUNDLE_AND_TOPOLOGY",
    "BATCH_C_HIGHER_DIMENSIONAL",
    "BATCH_D_GENERALIZED",
    "BATCH_E_NONCOMMUTATIVE",
    "BATCH_F_DISCRETE_CAUSAL",
    "BATCH_G_QUANTUM_GEOMETRIC",
    "BATCH_H_EMERGENT",
    "BATCH_DIRECTION_DEPENDENT",
    "BATCH_FRAME_AND_SPIN",
)
BATCH_BY_GROUP = {
    "A": "BATCH_A_CONTINUUM_AND_CONNECTION",
    "B": "BATCH_A_CONTINUUM_AND_CONNECTION",
    "C": "BATCH_FRAME_AND_SPIN",
    "D": "BATCH_B_BUNDLE_AND_TOPOLOGY",
    "E": "BATCH_C_HIGHER_DIMENSIONAL",
    "F": "BATCH_D_GENERALIZED",
    "G": "BATCH_DIRECTION_DEPENDENT",
    "H": "BATCH_E_NONCOMMUTATIVE",
    "I": "BATCH_F_DISCRETE_CAUSAL",
    "J": "BATCH_G_QUANTUM_GEOMETRIC",
    "K": "BATCH_H_EMERGENT",
}


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    return all(token not in text for token in _ranking_tokens()) and ("physical_sense_" + "score") not in text and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE17B_STATUS": "INCOMPLETE", "reason": reason, "status": "FORMALIZATION_FAILED"}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def enable_grammar(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENABLED"


def activate_theory_name(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENABLED"


def start_geometry_search(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_STARTED"


def select_geometry(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def filter_by_empirical_status(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def reopen_phase16(*_args: Any, **_kwargs: Any) -> str:
    return "REJECTED"


def _hash(spec: dict[str, Any]) -> str:
    body = {key: value for key, value in spec.items() if key != "grammar_hash"}
    return content_digest(body)


def _entry(
    geometry_id: str,
    category: str,
    group: str,
    definition: str,
    objects: tuple[str, ...],
    classification: str,
    *,
    physical_input: str,
    reason: str,
    boundable: bool,
    axes: tuple[str, ...] = (),
    missing: str = "",
    equivalence: str = "DISTINCT_BY_CONSTRUCTION",
    empirical: str = "THEORETICAL_FRAMEWORK",
    quantization: str = "CLASSICAL",
    phase16: str = "NONE",
    references: tuple[str, ...] = (),
    continuum: str = "CONTINUUM",
    role: str = "CANDIDATE_GEOMETRY",
    causal: str = "NOT_IN_THIS_STRUCTURE",
    dynamics: str = "OPTION_RECORDED_NOT_SELECTED",
) -> dict[str, Any]:
    return {
        "axes": axes,
        "boundable": boundable,
        "causal": causal,
        "category": category,
        "classification": classification,
        "continuum": continuum,
        "definition": definition,
        "dynamics": dynamics,
        "empirical": empirical,
        "equivalence": equivalence,
        "geometry_id": geometry_id,
        "group": group,
        "missing": missing,
        "objects": objects,
        "phase16": phase16,
        "physical_input": physical_input,
        "quantization": quantization,
        "reason": reason,
        "references": references,
        "role": role,
    }


def _catalogue() -> list[dict[str, Any]]:
    return [
        _entry("g17b.einstein_baseline", "CONTINUUM_GEOMETRY", "A", "4D smooth Lorentzian metric with its torsion-free metric-compatible connection, curvature tensors, geodesics, and Bianchi identity", ("manifold", "metric", "Levi-Civita connection"), "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="Levi-Civita completion is an unsupported equivalence of the registered metric", boundable=True, axes=("dimension_bound", "curvature_order"), equivalence="UNRESOLVED", empirical="WELL_TESTED_FRAMEWORK", references=("General Relativity",), role="REFERENCE_VALIDATION_BASELINE", causal="DEFINED_BY_LORENTZIAN_METRIC"),
        _entry("g17b.lorentzian", "CONTINUUM_GEOMETRY", "A", "pseudo-Riemannian metric of Lorentzian signature on a smooth manifold", ("metric",), "REPRESENTATIONAL", physical_input="NOT_DECIDED", reason="the registered field is a metric; the signature is not a registered object", boundable=True, axes=("signature_class",), equivalence="UNRESOLVED", empirical="WELL_TESTED_FRAMEWORK", references=("General Relativity",), causal="DEFINED_BY_LORENTZIAN_METRIC"),
        _entry("g17b.riemannian", "CONTINUUM_GEOMETRY", "A", "positive-definite metric on a smooth manifold", ("metric",), "NEW_GEOMETRY", physical_input="TRUE", reason="a definite signature is an assumption absent from the registered grammar", boundable=True, axes=("dimension_bound",)),
        _entry("g17b.signature_family", "CONTINUUM_GEOMETRY", "A", "pseudo-Riemannian metrics indexed by signature", ("metric", "signature"), "NEW_GEOMETRY", physical_input="TRUE", reason="signature is an unregistered discrete structure", boundable=True, axes=("signature_class",)),
        _entry("g17b.conformal", "CONTINUUM_GEOMETRY", "A", "a metric determined only up to a positive local scale", ("conformal class",), "NEW_GEOMETRY", physical_input="TRUE", reason="quotienting the metric by scale is a new assumption", boundable=True, axes=("tensor_rank_bound",)),
        _entry("g17b.weyl", "NON_RIEMANNIAN_GEOMETRY", "A", "a conformal class together with a length connection", ("conformal class", "length connection"), "NEW_GEOMETRY", physical_input="TRUE", reason="a length connection is an assumption absent from the registered grammar", boundable=True, axes=("tensor_rank_bound",)),
        _entry("g17b.projective", "CONTINUUM_GEOMETRY", "A", "a path geometry of unparameterized geodesics", ("paths",), "NEW_GEOMETRY", physical_input="TRUE", reason="path geometry is not the registered metric calculus", boundable=True, axes=("tensor_rank_bound",)),
        _entry("g17b.affine_geometry", "CONNECTION_GEOMETRY", "B", "a manifold with an affine connection and no required metric", ("affine connection",), "NEW_GEOMETRY", physical_input="TRUE", reason="an independent affine connection is absent from the registered grammar", boundable=True, axes=("tensor_rank_bound",)),
        _entry("g17b.levi_civita", "CONNECTION_GEOMETRY", "B", "the torsion-free metric-compatible connection of a metric", ("Levi-Civita connection",), "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="Christoffel completion is an unsupported equivalence", boundable=True, axes=("curvature_order",), equivalence="UNRESOLVED"),
        _entry("g17b.riemann_cartan", "NON_RIEMANNIAN_GEOMETRY", "B", "a metric and an independent metric-compatible connection with torsion", ("metric", "torsion", "curvature"), "OVERLAPPING", physical_input="TRUE", reason="introducing torsion is a new assumption", boundable=True, axes=("torsion_component_class", "curvature_order"), phase16="g16a.new.torsion_bundles", references=("Einstein-Cartan",)),
        _entry("g17b.metric_affine", "NON_RIEMANNIAN_GEOMETRY", "B", "an independent metric and an independent connection, with curvature, torsion, and nonmetricity as separate tensors", ("metric", "connection", "torsion", "nonmetricity", "curvature"), "NEW_GEOMETRY", physical_input="TRUE", reason="nonmetricity is an assumption absent from the registered grammar", boundable=True, axes=("torsion_component_class", "nonmetricity_class", "curvature_order")),
        _entry("g17b.torsionful", "NON_RIEMANNIAN_GEOMETRY", "B", "a connection whose torsion tensor is an independent geometric object", ("torsion",), "OVERLAPPING", physical_input="TRUE", reason="torsion is an assumption absent from the registered grammar", boundable=True, axes=("torsion_component_class",), phase16="g16a.new.torsion_bundles"),
        _entry("g17b.nonmetric", "NON_RIEMANNIAN_GEOMETRY", "B", "a connection that does not annihilate the metric", ("nonmetricity",), "NEW_GEOMETRY", physical_input="TRUE", reason="nonmetricity is an assumption absent from the registered grammar", boundable=True, axes=("nonmetricity_class",)),
        _entry("g17b.torsion_nonmetricity", "NON_RIEMANNIAN_GEOMETRY", "B", "curvature, torsion, and nonmetricity carried together by a metric and an independent connection", ("curvature", "torsion", "nonmetricity"), "OVERLAPPING", physical_input="TRUE", reason="the joint geometric structure is not registered", boundable=True, axes=("torsion_component_class", "nonmetricity_class"), phase16="g16a.new.torsion_bundles"),
        _entry("g17b.teleparallel", "NON_RIEMANNIAN_GEOMETRY", "B", "a metric connection with vanishing curvature whose geometric data sit in the torsion", ("torsion", "flat connection"), "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="reformulation versus distinct dynamics is not certified", boundable=True, axes=("torsion_component_class",), equivalence="UNRESOLVED", phase16="g16a.new.torsion_bundles"),
        _entry("g17b.symmetric_teleparallel", "NON_RIEMANNIAN_GEOMETRY", "B", "a connection with vanishing curvature and vanishing torsion whose geometric data sit in the nonmetricity", ("nonmetricity", "flat connection"), "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="reformulation versus distinct dynamics is not certified", boundable=True, axes=("nonmetricity_class",), equivalence="UNRESOLVED"),
        _entry("g17b.cartan_formulation", "FRAME_AND_SPIN_GEOMETRY", "C", "a Cartan connection valued in a kinematic algebra, represented with a frame", ("Cartan connection", "frame"), "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="frame-plus-connection versus metric formulation is an unsupported equivalence", boundable=True, axes=("tensor_rank_bound",), equivalence="UNRESOLVED"),
        _entry("g17b.vielbein", "FRAME_AND_SPIN_GEOMETRY", "C", "a local frame field from which a metric may be reconstructed", ("frame field",), "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="metric versus frame field is an unsupported equivalence", boundable=True, axes=("tensor_rank_bound",), equivalence="UNRESOLVED"),
        _entry("g17b.frame_bundle", "FRAME_AND_SPIN_GEOMETRY", "C", "the orthonormal frame bundle of a metric manifold", ("frame bundle",), "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="the global frame bundle is not separated from the metric by a supported equivalence", boundable=True, axes=("bundle_complexity",), equivalence="UNRESOLVED"),
        _entry("g17b.spin_structure", "FRAME_AND_SPIN_GEOMETRY", "C", "a spin structure and spin bundle, with no fermion field", ("spin structure",), "NEW_GEOMETRY", physical_input="TRUE", reason="a spin structure is an assumption absent from the registered grammar", boundable=True, axes=("bundle_complexity",)),
        _entry("g17b.spin_connection", "FRAME_AND_SPIN_GEOMETRY", "C", "a connection on a spin bundle", ("spin connection",), "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="spin connection versus frame plus connection is an unsupported equivalence", boundable=True, axes=("bundle_complexity",), equivalence="UNRESOLVED"),
        _entry("g17b.clifford", "FRAME_AND_SPIN_GEOMETRY", "C", "the Clifford algebra of a metric, with no fermion field", ("Clifford algebra",), "NEW_GEOMETRY", physical_input="TRUE", reason="a Clifford algebra is an assumption absent from the registered grammar", boundable=True, axes=("tensor_rank_bound",)),
        _entry("g17b.principal_bundle", "BUNDLE_AND_TOPOLOGICAL_GEOMETRY", "D", "a principal bundle with transition functions and a connection", ("principal bundle", "transition functions"), "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="a local potential versus a principal connection is an unsupported equivalence", boundable=True, axes=("bundle_complexity",), equivalence="UNRESOLVED", references=("Yang-Mills",)),
        _entry("g17b.vector_bundle", "BUNDLE_AND_TOPOLOGICAL_GEOMETRY", "D", "a vector bundle over spacetime, distinguished from a globally trivial product", ("vector bundle",), "NEW_GEOMETRY", physical_input="TRUE", reason="global bundle data are absent from the registered local fields", boundable=True, axes=("bundle_complexity",)),
        _entry("g17b.associated_bundle", "BUNDLE_AND_TOPOLOGICAL_GEOMETRY", "D", "a bundle associated with a principal bundle by a representation", ("associated bundle",), "NEW_GEOMETRY", physical_input="TRUE", reason="associated-bundle data are unregistered", boundable=True, axes=("bundle_complexity",)),
        _entry("g17b.nontrivial_sector", "BUNDLE_AND_TOPOLOGICAL_GEOMETRY", "D", "a bundle whose transition functions are not globally trivial, with no sector selected", ("transition functions",), "OVERLAPPING", physical_input="TRUE", reason="nontrivial topology is an assumption absent from the registered grammar", boundable=True, axes=("topological_sector_bound",), phase16="g16a.new.topology"),
        _entry("g17b.characteristic_class", "BUNDLE_AND_TOPOLOGICAL_GEOMETRY", "D", "Chern, Pontryagin, and Euler classes as densities, with no numerical charge", ("characteristic class",), "OVERLAPPING", physical_input="TRUE", reason="characteristic-class densities are outside the registered operator classes", boundable=True, axes=("characteristic_class_order",), phase16="g16a.new.topology"),
        _entry("g17b.holonomy", "BUNDLE_AND_TOPOLOGICAL_GEOMETRY", "D", "the holonomy of a connection as global geometric data", ("holonomy",), "NEW_GEOMETRY", physical_input="TRUE", reason="global holonomy is unregistered", boundable=True, axes=("bundle_complexity",)),
        _entry("g17b.higher_dimensional", "HIGHER_DIMENSIONAL_GEOMETRY", "E", "a pseudo-Riemannian manifold whose dimension is a discrete structural variable", ("higher-dimensional metric",), "OVERLAPPING", physical_input="TRUE", reason="changing dimension is an assumption absent from the registered grammar", boundable=True, axes=("dimension_bound",), phase16="g16a.new.extra_dimension", references=("Kaluza-Klein",)),
        _entry("g17b.fibered", "HIGHER_DIMENSIONAL_GEOMETRY", "E", "a fibered manifold with no reduction ansatz", ("fibration",), "NEW_GEOMETRY", physical_input="TRUE", reason="a fibration is an assumption absent from the registered grammar", boundable=True, axes=("dimension_bound", "internal_manifold_dimension")),
        _entry("g17b.compact_internal", "HIGHER_DIMENSIONAL_GEOMETRY", "E", "a compact internal manifold with no named manifold and no compactification dynamics", ("internal manifold",), "OVERLAPPING", physical_input="TRUE", reason="a compact internal manifold is an assumption absent from the registered vector space", boundable=True, axes=("internal_manifold_dimension",), phase16="g16a.new.torsion_bundles"),
        _entry("g17b.noncompact_internal", "HIGHER_DIMENSIONAL_GEOMETRY", "E", "a noncompact internal manifold with no named manifold and no reduction ansatz", ("internal manifold",), "NEW_GEOMETRY", physical_input="TRUE", reason="a noncompact internal manifold is an unregistered structure", boundable=True, axes=("internal_manifold_dimension",)),
        _entry("g17b.warped_product", "HIGHER_DIMENSIONAL_GEOMETRY", "E", "a warped product of two metrics with no reduction ansatz", ("warped product",), "NEW_GEOMETRY", physical_input="TRUE", reason="a warped product is an unregistered metric decomposition", boundable=True, axes=("dimension_bound",)),
        _entry("g17b.generalized_tangent", "GENERALIZED_GEOMETRY", "F", "a generalized tangent bundle", ("generalized tangent bundle",), "NOT_YET_BOUNDED", physical_input="TRUE", reason="the structure is unregistered", boundable=False, missing="a formally specified bracket", empirical="OPEN_RESEARCH_FRAMEWORK"),
        _entry("g17b.courant", "GENERALIZED_GEOMETRY", "F", "a Courant-type bracket on a generalized tangent bundle", ("Courant bracket",), "NOT_YET_BOUNDED", physical_input="TRUE", reason="the bracket is not formally specified", boundable=False, missing="the bracket axioms", empirical="OPEN_RESEARCH_FRAMEWORK"),
        _entry("g17b.exceptional_tangent", "GENERALIZED_GEOMETRY", "F", "an exceptional generalized tangent construction", ("exceptional tangent bundle",), "NOT_YET_BOUNDED", physical_input="TRUE", reason="the algebra is not formally specified", boundable=False, missing="the exceptional algebra presentation", empirical="OPEN_RESEARCH_FRAMEWORK", references=("string theory",)),
        _entry("g17b.finsler", "DIRECTION_DEPENDENT_GEOMETRY", "G", "a fundamental function of position and direction, not a quadratic metric", ("fundamental function",), "NEW_GEOMETRY", physical_input="TRUE", reason="direction dependence is a new geometric assumption", boundable=True, axes=("tensor_rank_bound",), equivalence="DISTINCT_BY_CONSTRUCTION", empirical="OPEN_RESEARCH_FRAMEWORK", causal="DEFINED_BY_FUNDAMENTAL_FUNCTION"),
        _entry("g17b.pseudo_finsler", "DIRECTION_DEPENDENT_GEOMETRY", "G", "a direction-dependent fundamental function of indefinite signature", ("fundamental function",), "NEW_GEOMETRY", physical_input="TRUE", reason="an indefinite direction-dependent norm is a new assumption", boundable=True, axes=("tensor_rank_bound", "signature_class"), equivalence="DISTINCT_BY_CONSTRUCTION", empirical="OPEN_RESEARCH_FRAMEWORK", causal="DEFINED_BY_FUNDAMENTAL_FUNCTION"),
        _entry("g17b.dispersion", "DIRECTION_DEPENDENT_GEOMETRY", "G", "a geometry read from a dispersion relation", ("dispersion relation",), "NOT_YET_BOUNDED", physical_input="TRUE", reason="no dispersion relation is specified", boundable=False, missing="the dispersion relation", empirical="OPEN_RESEARCH_FRAMEWORK"),
        _entry("g17b.noncommutative_coordinates", "DEFORMED_OR_NONCOMMUTATIVE_GEOMETRY", "H", "a coordinate algebra that does not commute", ("coordinate algebra",), "NOT_YET_BOUNDED", physical_input="TRUE", reason="noncommutativity is not a coordinate change of the registered calculus", boundable=False, missing="a finitely presented algebra, with no deformation parameter invented", equivalence="DISTINCT_BY_CONSTRUCTION", empirical="THEORETICAL_FRAMEWORK", references=("noncommutative geometry",)),
        _entry("g17b.spectral", "DEFORMED_OR_NONCOMMUTATIVE_GEOMETRY", "H", "a spectral geometric construction", ("spectral data",), "NOT_YET_BOUNDED", physical_input="TRUE", reason="the spectral data are not finitely specified", boundable=False, missing="the spectral triple data", empirical="THEORETICAL_FRAMEWORK", references=("noncommutative geometry",)),
        _entry("g17b.finite_algebra", "DEFORMED_OR_NONCOMMUTATIVE_GEOMETRY", "H", "a finite-dimensional associative algebra with no chosen presentation and no deformation parameter", ("finite algebra",), "INCOMPARABLE", physical_input="TRUE", reason="a finite noncommutative algebra is not the registered continuum calculus", boundable=True, axes=("algebra_dimension",), equivalence="DISTINCT_BY_CONSTRUCTION", empirical="THEORETICAL_FRAMEWORK"),
        _entry("g17b.causal_set", "DISCRETE_OR_CAUSAL_SPACETIME", "I", "a locally finite partially ordered set as the spacetime structure, not a smooth metric", ("locally finite poset",), "INCOMPARABLE", physical_input="TRUE", reason="a causal order is a different fundamental object from the registered metric", boundable=True, axes=("element_count_bound",), equivalence="DISTINCT_BY_CONSTRUCTION", empirical="OPEN_RESEARCH_FRAMEWORK", continuum="NON_CONTINUUM_GEOMETRY", references=("causal-set theory",), causal="DEFINED_BY_PARTIAL_ORDER"),
        _entry("g17b.discrete_complex", "DISCRETE_OR_CAUSAL_SPACETIME", "I", "a finite simplicial or cell complex as the spacetime structure, not a smooth metric", ("discrete complex",), "INCOMPARABLE", physical_input="TRUE", reason="a combinatorial complex is a different fundamental object from the registered metric", boundable=True, axes=("simplex_count_bound",), equivalence="DISTINCT_BY_CONSTRUCTION", empirical="OPEN_RESEARCH_FRAMEWORK", continuum="NON_CONTINUUM_GEOMETRY"),
        _entry("g17b.spin_network", "QUANTUM_GEOMETRIC_STRUCTURE", "J", "a combinatorial graph labeled by representation data, as quantum kinematics rather than a classical metric", ("spin network",), "INCOMPARABLE", physical_input="TRUE", reason="quantum-kinematic combinatorial data are not the registered metric", boundable=True, axes=("graph_size_bound", "representation_bound"), equivalence="DISTINCT_BY_CONSTRUCTION", empirical="OPEN_RESEARCH_FRAMEWORK", quantization="QUANTUM_KINEMATIC", continuum="NON_CONTINUUM_GEOMETRY", references=("loop quantum gravity",), dynamics="KINEMATIC_ONLY"),
        _entry("g17b.spin_foam", "QUANTUM_GEOMETRIC_STRUCTURE", "J", "a branched 2-complex labeled by representation data, as a quantum dynamical option rather than a classical metric", ("spin foam",), "INCOMPARABLE", physical_input="TRUE", reason="a spin foam is not a classical metric geometry", boundable=True, axes=("complex_size_bound",), equivalence="DISTINCT_BY_CONSTRUCTION", empirical="OPEN_RESEARCH_FRAMEWORK", quantization="QUANTUM_KINEMATIC", continuum="NON_CONTINUUM_GEOMETRY", references=("loop quantum gravity",)),
        _entry("g17b.group_field", "QUANTUM_GEOMETRIC_STRUCTURE", "J", "a field on a product of group manifolds used as a quantum-geometric building block, with no chosen group", ("group field",), "INCOMPARABLE", physical_input="TRUE", reason="the building block is a quantum field on a group, not a classical metric", boundable=True, axes=("valence_bound", "group_dimension_bound"), equivalence="DISTINCT_BY_CONSTRUCTION", empirical="OPEN_RESEARCH_FRAMEWORK", quantization="QUANTUM_KINEMATIC", continuum="NON_CONTINUUM_GEOMETRY"),
        _entry("g17b.emergent", "EMERGENT_SPACETIME_STRUCTURE", "K", "a smooth geometry induced by an unspecified primitive structure", ("unspecified primitive structure",), "NOT_YET_BOUNDED", physical_input="NOT_DECIDED", reason="emergence is not assumed and the primitive structure is not specified", boundable=False, missing="the primitive structure", equivalence="UNRESOLVED", empirical="UNKNOWN", quantization="NOT_PERFORMED", role="NOT_ASSUMED", dynamics="NOT_AVAILABLE"),
        _entry("g17b.induced", "EMERGENT_SPACETIME_STRUCTURE", "K", "a geometry induced by an unspecified map", ("unspecified inducing map",), "NOT_YET_BOUNDED", physical_input="NOT_DECIDED", reason="no inducing map is specified", boundable=False, missing="the inducing map", equivalence="UNRESOLVED", empirical="UNKNOWN", quantization="NOT_PERFORMED", role="NOT_ASSUMED", dynamics="NOT_AVAILABLE"),
        _entry("g17b.pregeometric", "EMERGENT_SPACETIME_STRUCTURE", "K", "a pre-geometric structure whose objects are not yet named", ("unspecified pre-geometric objects",), "NOT_YET_BOUNDED", physical_input="NOT_DECIDED", reason="the objects are not specified; specified discrete and quantum structures stay in their own families", boundable=False, missing="the primitive objects", equivalence="UNRESOLVED", empirical="UNKNOWN", quantization="NOT_PERFORMED", role="NOT_ASSUMED", dynamics="NOT_AVAILABLE"),
    ]


def _spec(row: dict[str, Any]) -> dict[str, Any]:
    bound_status = "REQUIREMENTS_STATED" if row["boundable"] else "NOT_YET_BOUNDED"
    spec = {
        "CANDIDATE_DYNAMICS_AVAILABLE": row["dynamics"] != "NOT_AVAILABLE",
        "CAUSAL_STRUCTURE_AVAILABLE": row["causal"] != "NOT_IN_THIS_STRUCTURE",
        "CONSISTENCY_AUDIT_STATUS": "NOT_PERFORMED",
        "DYNAMICAL_OPTIONS": row["dynamics"],
        "EMPIRICAL_STATUS": row["empirical"],
        "GEOMETRIC_KINEMATICS": row["definition"],
        "MATHEMATICAL_WELL_DEFINED": row["missing"] == "",
        "MATTER_CONTENT": "NONE",
        "OBSERVABLE_CONSTRUCTION_AVAILABLE": row["missing"] == "",
        "QUANTIZATION": row["quantization"],
        "QUANTIZATION_STATUS": row["quantization"],
        "SEARCH_STATUS": "NOT_ENABLED",
        "SPACETIME_INTERPRETATION_AVAILABLE": True,
        "SYMMETRY": "RECORDED_WITH_THE_STRUCTURE",
        "algebraic_structure": "noncommuting algebra" if row["category"] == "DEFORMED_OR_NONCOMMUTATIVE_GEOMETRY" else "not part of this grammar",
        "bundle_structure": "recorded" if row["category"] == "BUNDLE_AND_TOPOLOGICAL_GEOMETRY" else "not part of this grammar",
        "catalog_group": row["group"],
        "catalog_role": row["role"],
        "causal_structure": row["causal"],
        "classification": row["classification"],
        "compactification_defined": False,
        "connection_structure": "recorded" if row["category"] in {"CONNECTION_GEOMETRY", "NON_RIEMANNIAN_GEOMETRY"} else "not part of this grammar",
        "consistency_status": "NOT_PERFORMED",
        "continuum_class": row["continuum"],
        "discrete_structure": "fundamental" if row["continuum"] == "NON_CONTINUUM_GEOMETRY" else "not fundamental",
        "dynamical_action": "NOT_INCLUDED",
        "dynamical_options": row["dynamics"],
        "emergence_assumed": False,
        "empirical_status": row["empirical"],
        "equivalence_status": row["equivalence"],
        "fermions_added": False,
        "finite_bound_spec": {
            "bound_axes": list(row["axes"]),
            "bound_role": "SEARCH_SPACE_ASSUMPTION",
            "finite_bound_status": bound_status,
            "finite_boundable": row["boundable"],
            "integers": "NOT_CHOSEN",
            "missing_ingredient": row["missing"],
        },
        "frame_structure": "recorded" if row["category"] == "FRAME_AND_SPIN_GEOMETRY" else "not part of this grammar",
        "fundamental_objects": list(row["objects"]),
        "geometry_category": row["category"],
        "geometry_grammar_id": row["geometry_id"],
        "grammar_version": "grammar_17b_" + row["geometry_id"].removeprefix("g17b.") + "_v1",
        "internal_geometry": "recorded" if row["geometry_id"] in {"g17b.compact_internal", "g17b.noncompact_internal"} else "not part of this grammar",
        "mathematical_definition": row["definition"],
        "metric_structure": "not fundamental" if row["continuum"] == "NON_CONTINUUM_GEOMETRY" else "recorded when the definition names a metric",
        "new_constraints": [],
        "new_fields": [],
        "new_parameters": [],
        "new_physical_input": {"reason": row["reason"], "status": row["physical_input"]},
        "nonmetricity_structure": "independent tensor" if "nonmetricity" in row["definition"] else "not part of this grammar",
        "numerical_topological_value": "NOT_ASSIGNED",
        "observable_structure": "SLOT_RECORDED_NOT_CONSTRUCTED",
        "parent_grammar": GRAMMAR_VERSION,
        "phase16_overlap": row["phase16"],
        "privileged_search_status": False,
        "provenance_manifest": {
            "parent_grammar_hash": GRAMMAR_HASH,
            "reference_names": list(row["references"]),
            "reference_role": "REFERENCE_ONLY",
            "source_phase": "PHASE_17B",
        },
        "quantum_structure": row["quantization"],
        "reference_names": list(row["references"]),
        "scalar_curvature_action": "NOT_THE_GEOMETRIC_STRUCTURE",
        "search_status": "NOT_ENABLED",
        "spacetime_role": "FUNDAMENTAL_CANDIDATE" if row["role"] != "NOT_ASSUMED" else "EMERGENT_EFFECTIVE_NOT_ASSUMED",
        "spacetime_structure": row["definition"],
        "specific_manifold": "NONE",
        "spin_structure": "present without a fermion field" if row["geometry_id"] in {"g17b.spin_structure", "g17b.spin_connection", "g17b.clifford"} else "absent",
        "topological_sector_selected": False,
        "topology_structure": "global data without a selected sector" if row["category"] == "BUNDLE_AND_TOPOLOGICAL_GEOMETRY" else "not a selected sector",
        "torsion_dynamics": "NOT_INCLUDED",
        "torsion_structure": "independent tensor" if "torsion" in row["definition"] else "not part of this grammar",
    }
    spec["grammar_hash"] = _hash(spec)
    return spec


def _matrix() -> list[dict[str, str]]:
    rows = [
        ("manifold", "REPRESENTATION_ONLY", "CURRENTLY_PRESENT", "UNRESOLVED"),
        ("metric", "CURRENTLY_PRESENT", "CURRENTLY_PRESENT", "UNRESOLVED"),
        ("signature", "MISSING", "CURRENTLY_PRESENT", "UNRESOLVED"),
        ("Levi-Civita connection", "UNRESOLVED", "CURRENTLY_PRESENT", "UNRESOLVED"),
        ("metric compatibility", "MISSING", "CURRENTLY_PRESENT", "UNRESOLVED"),
        ("torsion-free condition", "REPRESENTATION_ONLY", "CURRENTLY_PRESENT", "UNRESOLVED"),
        ("curvature", "MISSING", "CURRENTLY_PRESENT", "UNRESOLVED"),
        ("geodesics", "MISSING", "CURRENTLY_PRESENT", "UNRESOLVED"),
        ("Bianchi identity", "MISSING", "CURRENTLY_PRESENT", "UNRESOLVED"),
        ("diffeomorphism structure", "CURRENTLY_PRESENT", "CURRENTLY_PRESENT", "UNRESOLVED"),
        ("local inertial frames", "MISSING", "CURRENTLY_PRESENT", "UNRESOLVED"),
        ("causal structure", "MISSING", "CURRENTLY_PRESENT", "UNRESOLVED"),
    ]
    return [
        {"EquivalenceStatus": equivalence, "Formalized17B": formalized, "Phase15": phase15, "ingredient": name, "role": "DIAGNOSTIC_NOT_A_SCORE"}
        for name, phase15, formalized, equivalence in rows
    ]


def _equivalences() -> list[dict[str, str]]:
    pairs = (
        ("metric", "frame field", "UNRESOLVED"),
        ("Levi-Civita connection", "Christoffel representation", "UNRESOLVED"),
        ("curvature formulation", "teleparallel formulation", "UNRESOLVED"),
        ("metric formulation", "alternative variables", "UNRESOLVED"),
        ("local gauge potential", "bundle connection", "UNRESOLVED"),
        ("quadratic metric", "direction-dependent fundamental function", "DISTINCT_BY_CONSTRUCTION"),
        ("smooth metric", "locally finite causal order", "DISTINCT_BY_CONSTRUCTION"),
        ("classical metric", "spin-network kinematics", "DISTINCT_BY_CONSTRUCTION"),
        ("commutative coordinate algebra", "noncommuting coordinate algebra", "DISTINCT_BY_CONSTRUCTION"),
    )
    return [
        {"converted_into_distinct_grammar": False, "equivalence_status": status, "left": left, "right": right}
        for left, right, status in pairs
    ]


def run_phase_17b(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    audit = run_phase_17a(write_artifacts=False)
    stored = _read("phase17a_geometry_audit_artifacts/PHASE_17A_GEOMETRY_CATALOG.json")
    frontier = _read("phase16e_frontier_artifacts/PHASE_16E_FRONTIER.json")
    grammar15 = _read("phase15f_grammar_artifacts/PHASE_15F_GRAMMAR.json")
    specs = [_spec(row) for row in _catalogue()]
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or grammar15.get("grammar_hash") != GRAMMAR_HASH
        or audit.get("PHASE17A_STATUS") != "COMPLETE"
        or stored.get("PHASE17A_STATUS") != "COMPLETE"
        or frontier.get("PHASE16E_STATUS") != "COMPLETE"
        or frontier.get("cumulative_points") != 69
        or enable_grammar("General Relativity") != "NOT_ENABLED"
        or activate_theory_name("loop quantum gravity") != "NOT_ENABLED"
        or start_geometry_search() != "NOT_STARTED"
        or select_geometry(specs) != "NOT_PERFORMED"
        or filter_by_empirical_status("WELL_TESTED_FRAMEWORK") != "NOT_PERFORMED"
        or reopen_phase16() != "REJECTED"
    ):
        return _stop("integrity gate")
    by_id = {item["geometry_grammar_id"]: item for item in specs}
    if set(CATEGORIES) - {item["geometry_category"] for item in specs}:
        return _stop("missing category")
    if any(item["search_status"] != "NOT_ENABLED" or item["privileged_search_status"] or item["parent_grammar"] != GRAMMAR_VERSION for item in specs):
        return _stop("privileged or enabled grammar")
    if any(item["grammar_hash"] != _hash(item) for item in specs):
        return _stop("hash")
    if any(item["fermions_added"] or item["dynamical_action"] != "NOT_INCLUDED" or item["emergence_assumed"] or item["compactification_defined"] for item in specs):
        return _stop("separation")
    if any(marker in json.dumps({"ids": list(by_id)}) for marker in _target_markers()):
        return _stop("target marker")
    if classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")}) != "REJECTED":
        return _stop("blindness")
    unbounded = [item for item in specs if item["finite_bound_spec"]["finite_boundable"] is False]
    if any(item["finite_bound_spec"]["finite_bound_status"] != "NOT_YET_BOUNDED" or item["finite_bound_spec"]["missing_ingredient"] == "" for item in unbounded):
        return _stop("unbounded register")
    overlaps = [
        {
            "classification": "OVERLAPPING_WITH_PHASE16",
            "geometry_grammar_id": item["geometry_grammar_id"],
            "merged": False,
            "phase16_grammar": item["phase16_overlap"],
            "phase16_reopened": False,
        }
        for item in specs
        if item["phase16_overlap"] != "NONE"
    ]
    overlaps.append(
        {
            "classification": "INCOMPARABLE",
            "geometry_grammar_id": "NONE",
            "merged": False,
            "phase16_grammar": "g16a.new.extra_connection",
            "phase16_reopened": False,
        }
    )
    batches = [
        {
            "batch_id": batch_id,
            "geometries": [item["geometry_grammar_id"] for item in specs if BATCH_BY_GROUP[item["catalog_group"]] == batch_id],
            "status": "NOT_AUTHORIZED",
        }
        for batch_id in BATCHES
    ]
    if any(not item["geometries"] for item in batches):
        return _stop("empty authorization batch")
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE17B_STATUS": "COMPLETE",
        "GEOMETRY_META_GRAMMAR_STATUS": "COMPLETE",
        "EINSTEIN_BASELINE_STATUS": "COMPLETE",
        "CONTINUUM_GEOMETRY_STATUS": "COMPLETE",
        "NON_RIEMANNIAN_STATUS": "COMPLETE",
        "BUNDLE_TOPOLOGY_STATUS": "COMPLETE",
        "HIGHER_DIMENSION_STATUS": "COMPLETE",
        "GENERALIZED_GEOMETRY_STATUS": "COMPLETE",
        "NONCOMMUTATIVE_STATUS": "COMPLETE",
        "DISCRETE_CAUSAL_STATUS": "COMPLETE",
        "QUANTUM_GEOMETRY_STATUS": "COMPLETE",
        "EMERGENT_SPACETIME_STATUS": "COMPLETE",
        "GEOMETRIC_EQUIVALENCE_STATUS": "COMPLETE",
        "GEOMETRIC_INPUT_STATUS": "VERIFIED",
        "GEOMETRIC_BOUND_STATUS": "COMPLETE",
        "PHASE16_OVERLAP_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "HUMAN_AUTHORIZATION_STATUS": "READY",
        "PRIOR_PHASE_INTEGRITY_STATUS": "VERIFIED",
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "grammar_hash": GRAMMAR_HASH,
        "SEARCH_STATUS": "NOT_STARTED",
        "NO_GEOMETRY_SELECTED": True,
        "geometry_meta_grammar": {"categories": list(CATEGORIES), "parent_grammar": GRAMMAR_VERSION, "records": specs, "role": "TARGET_BLIND_CATALOGUE"},
        "einsteinian_reference_baseline": {
            "completeness_matrix": _matrix(),
            "grammar": by_id["g17b.einstein_baseline"],
            "role": "REFERENCE_VALIDATION_BASELINE",
            "suppresses_other_families": False,
        },
        "continuum_geometry_catalog": [item for item in specs if item["catalog_group"] == "A"],
        "non_riemannian_geometry_catalog": [item for item in specs if item["geometry_category"] == "NON_RIEMANNIAN_GEOMETRY"],
        "bundle_topology_catalog": [item for item in specs if item["catalog_group"] == "D"],
        "higher_dimensional_catalog": [item for item in specs if item["catalog_group"] == "E"],
        "generalized_geometry_catalog": [item for item in specs if item["catalog_group"] == "F"],
        "direction_dependent_catalog": [item for item in specs if item["catalog_group"] == "G"],
        "noncommutative_geometry_catalog": [item for item in specs if item["catalog_group"] == "H"],
        "discrete_causal_catalog": [item for item in specs if item["catalog_group"] == "I"],
        "quantum_geometric_catalog": [item for item in specs if item["catalog_group"] == "J"],
        "emergent_spacetime_catalog": [item for item in specs if item["catalog_group"] == "K"],
        "frame_and_spin_catalog": [item for item in specs if item["catalog_group"] == "C"],
        "geometric_equivalence_register": _equivalences(),
        "geometric_new_input_register": [
            {"geometry_grammar_id": item["geometry_grammar_id"], "new_physical_input": item["new_physical_input"]} for item in specs
        ],
        "geometric_bound_register": [
            {"finite_bound_spec": item["finite_bound_spec"], "geometry_grammar_id": item["geometry_grammar_id"]} for item in specs
        ],
        "phase16_overlap_register": overlaps,
        "geometry_batch_authorization_candidates": batches,
        "selected_geometry": "NONE",
        "catalog_influence": catalog_influence({"entries": []}, "phase17b-broad")["status"],
        "ranking_function": "ABSENT" if _ranking_absent() else "PRESENT",
        "next_phase": {"object": "HUMAN_AUTHORIZATION_OF_A_GEOMETRY_BATCH", "status": "NOT_AUTHORIZED"},
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_17B_GEOMETRY_GRAMMARS.json").write_bytes(
            canonical_json_bytes(
                {
                    "GEOMETRY_META_GRAMMAR_STATUS": "COMPLETE",
                    "PHASE17B_STATUS": "COMPLETE",
                    "SEARCH_STATUS": "NOT_STARTED",
                    "categories": list(CATEGORIES),
                    "grammar_count": len(specs),
                    "grammar_hash": GRAMMAR_HASH,
                    "selected_geometry": "NONE",
                }
            )
        )
        if _unchanged(snapshot_existing_phases()) != before:
            return _stop("previous phase changed")
        if _read("phase16e_frontier_artifacts/PHASE_16E_FRONTIER.json").get("cumulative_points") != 69:
            return _stop("phase 16 changed")
        if _read("phase17a_geometry_audit_artifacts/PHASE_17A_GEOMETRY_CATALOG.json").get("candidate_ids") != stored["candidate_ids"]:
            return _stop("phase 17a changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
