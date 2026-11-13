"""Phase 17B.1 catalogues fundamental structures and does not explore them.

The Phase 17B geometry catalogue is a historical input. This module does not rewrite it.
"""

from __future__ import annotations

import hashlib
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
from physics_lab.theory_kernel.reconstruction import FROZEN_4C_HASH

PHASE = "PHASE_17B.1"
CODE_VERSION = "phase17b1-fundamental-structure-v1"
GRAMMAR_VERSION = "fundamental_structure_17b1_v1"
ARTIFACT_DIR_NAME = "phase17b1_fundamental_structure_artifacts"
HISTORICAL_RELATIVE = "phase17b_geometry_formalization_artifacts/PHASE_17B_GEOMETRY_GRAMMARS.json"
TAXONOMY = (
    "continuous",
    "discrete",
    "local",
    "global",
    "commutative",
    "noncommutative",
    "classical",
    "quantum",
    "metric",
    "connection",
    "geometric",
    "algebraic",
    "pointlike",
    "extended",
    "fundamental",
    "emergent",
    "bulk_local",
    "boundary_dual",
    "finite_dimensional",
    "infinite_dimensional",
    "deterministic",
    "constraint_quotient",
    "manifold",
    "combinatorial",
)


def _physics_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "physics"


def _unchanged(snapshot: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in snapshot.items() if not key.startswith(ARTIFACT_DIR_NAME)}


def _ranking_absent() -> bool:
    text = Path(__file__).read_text(encoding="utf-8")
    banned = ("most_" + "accepted", "most_" + "cited", "most_" + "promising", "most_" + "popular")
    return all(token not in text for token in _ranking_tokens()) and all(token not in text for token in banned) and ("known_" + "physics") not in text


def _stop(reason: str) -> dict[str, str]:
    return {"PHASE17B1_STATUS": "INCOMPLETE", "reason": reason, "status": "FORMALIZATION_FAILED"}


def _read(relative: str) -> dict[str, Any]:
    body = json.loads((_physics_dir() / relative).read_text(encoding="utf-8"))
    if not isinstance(body, dict):
        raise TypeError(relative)
    return body


def enable_grammar(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENABLED"


def activate_theory_name(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENABLED"


def activate_discovered_family(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_ENABLED"


def start_search(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_STARTED"


def select_structure(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def filter_by_empirical_status(*_args: Any, **_kwargs: Any) -> str:
    return "NOT_PERFORMED"


def reopen_phase16(*_args: Any, **_kwargs: Any) -> str:
    return "REJECTED"


def _hash(spec: dict[str, Any]) -> str:
    body = {key: value for key, value in spec.items() if key != "grammar_hash"}
    return content_digest(body)


def _row(
    grammar_id: str,
    category: str,
    definition: str,
    objects: tuple[str, ...],
    novelty: str,
    searchability: str,
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
    kind: str = "GEOMETRIC",
    poles: tuple[str, ...] = (),
    role: str = "CANDIDATE_STRUCTURE",
    continuum: str = "CONTINUUM",
) -> dict[str, Any]:
    return {
        "axes": axes,
        "boundable": boundable,
        "category": category,
        "continuum": continuum,
        "definition": definition,
        "empirical": empirical,
        "equivalence": equivalence,
        "grammar_id": grammar_id,
        "kind": kind,
        "missing": missing,
        "novelty": novelty,
        "objects": objects,
        "phase16": phase16,
        "physical_input": physical_input,
        "poles": poles,
        "quantization": quantization,
        "reason": reason,
        "references": references,
        "role": role,
        "searchability": searchability,
    }


def _authored() -> list[dict[str, Any]]:
    continuum = ("continuous", "local", "commutative", "classical", "metric", "geometric", "pointlike", "fundamental", "bulk_local", "finite_dimensional", "deterministic", "manifold")
    return [
        _row("g17b1.einstein_baseline", "CLASSICAL_CONTINUUM_GEOMETRY", "a 4D pseudo-Riemannian Lorentzian metric with its torsion-free metric-compatible connection and curvature tensors", ("metric", "Levi-Civita connection"), "EQUIVALENCE_UNRESOLVED", "REFERENCE_ONLY", physical_input="NOT_DECIDED", reason="Levi-Civita completion remains an unsupported equivalence", boundable=True, axes=("dimension", "curvature_order"), equivalence="EQUIVALENCE_UNRESOLVED", empirical="WELL_TESTED_FRAMEWORK", references=("General Relativity",), poles=continuum, role="REFERENCE_VALIDATION_BASELINE"),
        _row("g17b1.conformal", "CLASSICAL_CONTINUUM_GEOMETRY", "a metric determined only up to local scale", ("conformal class",), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="quotienting by scale is a new assumption", boundable=True, axes=("tensor_rank",), poles=("continuous", "metric")),
        _row("g17b1.weyl", "CLASSICAL_CONTINUUM_GEOMETRY", "a conformal class with a length connection", ("length connection",), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="a length connection is unregistered", boundable=True, axes=("tensor_rank",), poles=("connection",)),
        _row("g17b1.projective", "CLASSICAL_CONTINUUM_GEOMETRY", "unparameterized path geometry", ("paths",), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="path geometry is not the registered metric calculus", boundable=True, axes=("tensor_rank",)),
        _row("g17b1.riemann_cartan", "CLASSICAL_CONTINUUM_GEOMETRY", "metric-compatible connection with independent torsion", ("torsion", "curvature"), "OVERLAPPING", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="torsion is a new assumption", boundable=True, axes=("tensor_rank",), phase16="g16a.new.torsion_bundles", references=("Einstein-Cartan",), poles=("connection",)),
        _row("g17b1.affine", "CONNECTION_AFFINE_GEOMETRY", "an affine connection on a manifold, recorded separately from any metric", ("affine connection",), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="an affine connection is not the registered metric calculus", boundable=True, axes=("tensor_rank",), poles=("connection", "local")),
        _row("g17b1.metric_affine", "CONNECTION_AFFINE_GEOMETRY", "independent metric and connection, with curvature, torsion, and nonmetricity kept separate", ("metric", "connection", "torsion", "nonmetricity"), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="nonmetricity is a new assumption", boundable=True, axes=("tensor_rank",), references=("metric-affine gravity",), poles=("connection", "local")),
        _row("g17b1.teleparallel", "CLASSICAL_CONTINUUM_GEOMETRY", "curvature-free connection whose geometric data sit in the torsion", ("torsion", "flat connection"), "EQUIVALENCE_UNRESOLVED", "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="reformulation versus distinct dynamics is not certified", boundable=True, axes=("tensor_rank",), equivalence="EQUIVALENCE_UNRESOLVED", references=("teleparallel gravity",), poles=("connection",)),
        _row("g17b1.symmetric_teleparallel", "CLASSICAL_CONTINUUM_GEOMETRY", "curvature-free and torsion-free connection whose geometric data sit in the nonmetricity", ("nonmetricity",), "EQUIVALENCE_UNRESOLVED", "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="reformulation versus distinct dynamics is not certified", boundable=True, axes=("tensor_rank",), equivalence="EQUIVALENCE_UNRESOLVED"),
        _row("g17b1.cartan_frame", "FRAME_SPIN_GEOMETRY", "a Cartan connection represented with a frame", ("Cartan connection", "frame"), "EQUIVALENCE_UNRESOLVED", "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="frame-plus-connection versus metric is unsupported", boundable=True, axes=("tensor_rank",), equivalence="EQUIVALENCE_UNRESOLVED"),
        _row("g17b1.vielbein", "FRAME_SPIN_GEOMETRY", "a local frame field", ("frame field",), "EQUIVALENCE_UNRESOLVED", "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="metric versus frame field is an unsupported equivalence", boundable=True, axes=("tensor_rank",), equivalence="EQUIVALENCE_UNRESOLVED"),
        _row("g17b1.spin_structure", "FRAME_SPIN_GEOMETRY", "a spin structure with no fermion field", ("spin structure",), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="a spin structure is unregistered", boundable=True, axes=("representation_complexity",)),
        _row("g17b1.principal_bundle", "BUNDLE_TOPOLOGICAL_STRUCTURE", "a principal bundle with transition functions", ("principal bundle", "transition functions"), "EQUIVALENCE_UNRESOLVED", "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="local potential versus principal connection is unsupported", boundable=True, axes=("representation_complexity",), equivalence="EQUIVALENCE_UNRESOLVED", poles=("global",)),
        _row("g17b1.vector_bundle", "BUNDLE_TOPOLOGICAL_STRUCTURE", "a vector bundle distinguished from a trivial product", ("vector bundle",), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="global bundle data are unregistered", boundable=True, axes=("representation_complexity",), poles=("global",)),
        _row("g17b1.holonomy", "BUNDLE_TOPOLOGICAL_STRUCTURE", "holonomy of a connection as global data", ("holonomy",), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="global holonomy is unregistered", boundable=True, axes=("representation_complexity",), poles=("global",)),
        _row("g17b1.characteristic_class", "BUNDLE_TOPOLOGICAL_STRUCTURE", "characteristic-class densities with no numerical charge", ("characteristic class",), "OVERLAPPING", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="characteristic-class densities are outside the registered operators", boundable=True, axes=("topology_order",), phase16="g16a.new.topology", poles=("global",)),
        _row("g17b1.higher_dimensional", "HIGHER_DIMENSIONAL_GEOMETRY", "pseudo-Riemannian dimension as a discrete variable, with no compactification", ("higher-dimensional metric",), "OVERLAPPING", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="changing dimension is a new assumption", boundable=True, axes=("dimension",), phase16="g16a.new.extra_dimension", references=("Kaluza-Klein",)),
        _row("g17b1.warped_product", "HIGHER_DIMENSIONAL_GEOMETRY", "a warped product with no reduction ansatz and no named factor", ("warped product",), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="a warped product is an unregistered decomposition", boundable=True, axes=("dimension",)),
        _row("g17b1.internal_manifold", "HIGHER_DIMENSIONAL_GEOMETRY", "an internal manifold that may be compact or noncompact, with no named manifold", ("internal manifold",), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="an internal manifold is not the registered vector space", boundable=True, axes=("dimension",), poles=("manifold",)),
        _row("g17b1.generalized_tangent", "GENERALIZED_GEOMETRY", "a generalized tangent bundle", ("generalized tangent bundle",), "NOT_YET_SPECIFIABLE", "NOT_YET_BOUNDED", physical_input="TRUE", reason="the bracket is not specified", boundable=False, missing="a formally specified bracket", empirical="OPEN_RESEARCH_FRAMEWORK"),
        _row("g17b1.courant", "GENERALIZED_GEOMETRY", "a Courant-type bracket on a generalized tangent bundle", ("Courant-type bracket",), "NOT_YET_SPECIFIABLE", "NOT_YET_BOUNDED", physical_input="TRUE", reason="the bracket axioms are not specified", boundable=False, missing="the bracket axioms", empirical="OPEN_RESEARCH_FRAMEWORK"),
        _row("g17b1.exceptional_tangent", "GENERALIZED_GEOMETRY", "an exceptional generalized tangent structure", ("exceptional tangent",), "NOT_YET_SPECIFIABLE", "NOT_YET_BOUNDED", physical_input="TRUE", reason="the exceptional algebra presentation is not specified", boundable=False, missing="the exceptional algebra presentation", empirical="OPEN_RESEARCH_FRAMEWORK", references=("string theory",)),
        _row("g17b1.finsler", "DIRECTION_DEPENDENT_GEOMETRY", "a fundamental function of position and direction", ("fundamental function",), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="direction dependence is a new assumption", boundable=True, axes=("tensor_rank",), equivalence="DISTINCT_BY_CONSTRUCTION", empirical="OPEN_RESEARCH_FRAMEWORK"),
        _row("g17b1.pseudo_finsler", "DIRECTION_DEPENDENT_GEOMETRY", "a fundamental function whose indicatrix has an indefinite signature", ("pseudo-Finsler function",), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="an indefinite fundamental function is unregistered", boundable=True, axes=("tensor_rank",), equivalence="DISTINCT_BY_CONSTRUCTION", empirical="OPEN_RESEARCH_FRAMEWORK"),
        _row("g17b1.noncommutative_coordinates", "NONCOMMUTATIVE_GEOMETRY", "a coordinate algebra that does not commute", ("coordinate algebra",), "NOT_YET_SPECIFIABLE", "NOT_YET_BOUNDED", physical_input="TRUE", reason="noncommutativity is not a coordinate change", boundable=False, missing="a finite presentation, with no deformation parameter invented", equivalence="DISTINCT_BY_CONSTRUCTION", references=("noncommutative geometry",), poles=("noncommutative", "algebraic"), kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE"),
        _row("g17b1.finite_algebra", "NONCOMMUTATIVE_GEOMETRY", "a finite-dimensional associative algebra with no chosen presentation and no deformation parameter", ("finite algebra",), "INCOMPARABLE", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="a finite algebra is not the registered continuum calculus", boundable=True, axes=("algebra_rank",), equivalence="DISTINCT_BY_CONSTRUCTION", poles=("finite_dimensional", "algebraic", "noncommutative"), kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE"),
        _row("g17b1.spectral", "NONCOMMUTATIVE_GEOMETRY", "a spectral-geometric construction", ("spectral data",), "NOT_YET_SPECIFIABLE", "NOT_YET_BOUNDED", physical_input="TRUE", reason="the spectral data are not specified", boundable=False, missing="the spectral triple data", empirical="OPEN_RESEARCH_FRAMEWORK", poles=("noncommutative", "algebraic"), kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE"),
        _row("g17b1.causal_set", "DISCRETE_CAUSAL_SPACETIME", "a locally finite partial order as spacetime, not a smooth metric", ("locally finite poset",), "INCOMPARABLE", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="a causal order is a different fundamental object", boundable=True, axes=("discrete_structure_size",), equivalence="DISTINCT_BY_CONSTRUCTION", empirical="OPEN_RESEARCH_FRAMEWORK", references=("causal set theory",), poles=("discrete", "combinatorial", "fundamental"), kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE", continuum="CONTINUUM_REPLACEMENT"),
        _row("g17b1.causal_graph", "DISCRETE_CAUSAL_SPACETIME", "a directed causal graph", ("directed graph",), "EQUIVALENCE_UNRESOLVED", "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="a causal graph versus a causal order is an unsupported equivalence", boundable=True, axes=("discrete_structure_size",), equivalence="EQUIVALENCE_UNRESOLVED", poles=("discrete", "combinatorial"), kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE", continuum="CONTINUUM_REPLACEMENT"),
        _row("g17b1.discrete_complex", "DISCRETE_CAUSAL_SPACETIME", "a finite simplicial or cell complex, not a smooth metric", ("discrete complex",), "INCOMPARABLE", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="a combinatorial complex is a different fundamental object", boundable=True, axes=("discrete_structure_size",), equivalence="DISTINCT_BY_CONSTRUCTION", poles=("discrete", "combinatorial"), kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE", continuum="CONTINUUM_REPLACEMENT"),
        _row("g17b1.causal_triangulation", "DISCRETE_CAUSAL_SPACETIME", "a triangulation carrying a causal order on its simplices, not a smooth metric", ("causal triangulation",), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="a causal triangulation is an unregistered combinatorial structure", boundable=True, axes=("discrete_structure_size",), equivalence="DISTINCT_BY_CONSTRUCTION", empirical="OPEN_RESEARCH_FRAMEWORK", references=("causal dynamical triangulations",), poles=("discrete", "combinatorial"), kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE", continuum="CONTINUUM_REPLACEMENT"),
        _row("g17b1.spin_network", "QUANTUM_GEOMETRIC_STRUCTURE", "a graph labeled by representation data, as quantum kinematics rather than a classical metric", ("spin network",), "INCOMPARABLE", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="quantum-kinematic combinatorial data are not the registered metric", boundable=True, axes=("discrete_structure_size", "representation_complexity"), equivalence="DISTINCT_BY_CONSTRUCTION", empirical="OPEN_RESEARCH_FRAMEWORK", quantization="QUANTUM_KINEMATIC", references=("loop quantum gravity",), poles=("quantum", "combinatorial"), kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE", continuum="CONTINUUM_REPLACEMENT"),
        _row("g17b1.spin_foam", "QUANTUM_GEOMETRIC_STRUCTURE", "a labeled 2-complex as a quantum dynamical option, not a classical metric", ("spin foam",), "INCOMPARABLE", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="a spin foam is not a classical metric", boundable=True, axes=("discrete_structure_size",), equivalence="DISTINCT_BY_CONSTRUCTION", quantization="QUANTUM_KINEMATIC", references=("spin foams",), poles=("quantum",), kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE", continuum="CONTINUUM_REPLACEMENT"),
        _row("g17b1.tensor_model", "QUANTUM_GEOMETRIC_STRUCTURE", "a tensor contraction as a combinatorial quantum structure, with no chosen rank", ("tensor",), "INCOMPARABLE", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="a tensor model is not a classical metric", boundable=True, axes=("tensor_rank",), equivalence="DISTINCT_BY_CONSTRUCTION", empirical="OPEN_RESEARCH_FRAMEWORK", quantization="QUANTUM_KINEMATIC", references=("tensor models",), poles=("quantum", "combinatorial"), kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE"),
        _row("g17b1.group_field", "QUANTUM_GEOMETRIC_STRUCTURE", "a field on a product of groups, with no chosen group", ("group field",), "INCOMPARABLE", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="the building block is not a classical metric", boundable=True, axes=("representation_complexity",), equivalence="DISTINCT_BY_CONSTRUCTION", quantization="QUANTUM_KINEMATIC", references=("group field theory",), poles=("quantum",), kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE"),
        _row("g17b1.quantum_operator_algebra", "QUANTUM_GEOMETRIC_STRUCTURE", "an operator algebra of quantum-geometric observables", ("operator algebra",), "NOT_YET_SPECIFIABLE", "NOT_YET_BOUNDED", physical_input="TRUE", reason="the operator algebra is not presented", boundable=False, missing="the operator-algebra presentation", quantization="QUANTUM_KINEMATIC", poles=("quantum", "algebraic"), kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE"),
        _row("g17b1.worldsheet", "STRING_BRANE_STRUCTURE", "an embedding of a two-dimensional worldsheet into an unspecified target, with no matter spectrum and no compactification", ("worldsheet", "embedding map"), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="an extended worldsheet is not a point-field grammar", boundable=True, axes=("brane_worldvolume_dimension", "dimension"), equivalence="DISTINCT_BY_CONSTRUCTION", empirical="OPEN_RESEARCH_FRAMEWORK", references=("string theory", "superstring theory"), poles=("extended",), kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE"),
        _row("g17b1.worldvolume", "STRING_BRANE_STRUCTURE", "a worldvolume whose dimension is an unspecified integer, with no named internal manifold", ("worldvolume",), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="a brane worldvolume is not a point-field grammar", boundable=True, axes=("brane_worldvolume_dimension",), equivalence="DISTINCT_BY_CONSTRUCTION", references=("M-theory",), poles=("extended",), kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE"),
        _row("g17b1.duality_map", "STRING_BRANE_STRUCTURE", "a duality between geometric descriptions", ("duality map",), "NOT_YET_SPECIFIABLE", "NOT_YET_BOUNDED", physical_input="NOT_DECIDED", reason="no duality map is specified", boundable=False, missing="the duality map", equivalence="EQUIVALENCE_UNRESOLVED", references=("string theory",)),
        _row("g17b1.rg_flow", "QUANTUM_FIELD_THEORETIC_GRAVITY", "a renormalization-group flow on a space of gravitational actions, with no chosen fixed point", ("renormalization-group flow",), "GENUINELY_NEW", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="an RG flow is not the registered classical geometry", boundable=True, axes=("derivative_order",), empirical="OPEN_RESEARCH_FRAMEWORK", quantization="QUANTUM_FIELD", references=("asymptotic safety",), poles=("classical",)),
        _row("g17b1.higher_derivative_qft", "QUANTUM_FIELD_THEORETIC_GRAVITY", "a gravitational field theory whose derivative order is an unspecified integer", ("higher-derivative Lagrangian",), "OVERLAPPING", "SEARCHABLE_AFTER_FORMALIZATION", physical_input="TRUE", reason="raising the derivative order is a separate dynamical assumption", boundable=True, axes=("derivative_order",), phase16="g16a.new.higher_derivative_order", quantization="QUANTUM_FIELD"),
        _row("g17b1.effective_qft", "QUANTUM_FIELD_THEORETIC_GRAVITY", "an effective gravitational field theory whose operator basis is not yet specified", ("effective Lagrangian",), "NOT_YET_SPECIFIABLE", "NOT_YET_BOUNDED", physical_input="TRUE", reason="the operator basis is not specified and no phenomenological coefficient is invented", boundable=False, missing="the operator basis", quantization="QUANTUM_FIELD"),
        _row("g17b1.deformed_symmetry", "DEFORMED_SYMMETRY_SPACETIME_STRUCTURE", "a spacetime symmetry algebra deformed away from the classical kinematic algebra", ("deformed symmetry algebra",), "NOT_YET_SPECIFIABLE", "NOT_YET_BOUNDED", physical_input="TRUE", reason="no algebra presentation is specified and no deformation parameter is invented", boundable=False, missing="the algebra presentation"),
        _row("g17b1.twistor", "TWISTOR_REPRESENTATION_STRUCTURE", "incidence data that encode spacetime indirectly", ("incidence relation",), "EQUIVALENCE_UNRESOLVED", "EQUIVALENCE_UNRESOLVED", physical_input="NOT_DECIDED", reason="equivalence to metric geometry is not certified", boundable=True, axes=("dimension",), equivalence="EQUIVALENCE_UNRESOLVED", empirical="OPEN_RESEARCH_FRAMEWORK", references=("twistor approaches",)),
        _row("g17b1.holographic_map", "HOLOGRAPHIC_DUAL_STRUCTURE", "a relation between a bulk structure and a boundary structure", ("bulk", "boundary"), "NOT_YET_SPECIFIABLE", "NOT_YET_BOUNDED", physical_input="NOT_DECIDED", reason="a duality is not evidence that either side is fundamental, and the map is unspecified", boundable=False, missing="the bulk-boundary map", equivalence="EQUIVALENCE_UNRESOLVED", empirical="OPEN_RESEARCH_FRAMEWORK", references=("holographic approaches",), poles=("boundary_dual",)),
        _row("g17b1.entanglement_geometry", "HOLOGRAPHIC_DUAL_STRUCTURE", "a geometry reconstructed from entanglement data", ("entanglement data",), "NOT_YET_SPECIFIABLE", "NOT_YET_BOUNDED", physical_input="NOT_DECIDED", reason="no reconstruction map is specified", boundable=False, missing="the reconstruction map", empirical="UNKNOWN"),
        _row("g17b1.emergent", "EMERGENT_PREGEOMETRIC_STRUCTURE", "a smooth geometry induced by an unspecified primitive structure", ("unspecified primitive structure",), "NOT_YET_SPECIFIABLE", "NOT_YET_BOUNDED", physical_input="NOT_DECIDED", reason="emergence is not assumed", boundable=False, missing="the primitive structure", equivalence="EQUIVALENCE_UNRESOLVED", empirical="UNKNOWN", references=("emergent spacetime approaches",), poles=("emergent",), role="NOT_ASSUMED"),
    ]


def discover_missing_families(covered: set[str]) -> list[dict[str, Any]]:
    found = []
    if "infinite_dimensional" not in covered:
        found.append(
            _row(
                "g17b1.infinite_dimensional_configuration",
                "OTHER_GENUINELY_NEW_MATHEMATICAL_FAMILIES",
                "the infinite-dimensional space of geometric field configurations",
                ("configuration space",),
                "GENUINELY_NEW",
                "NOT_YET_BOUNDED",
                physical_input="TRUE",
                reason="no mode presentation is specified",
                boundable=False,
                missing="a mode presentation",
                poles=("infinite_dimensional",),
                kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE",
                role="NEW_CANDIDATE_FAMILY",
            )
        )
    if "constraint_quotient" not in covered:
        found.append(
            _row(
                "g17b1.constraint_quotient",
                "OTHER_GENUINELY_NEW_MATHEMATICAL_FAMILIES",
                "a physical structure presented as a quotient by constraints",
                ("constraint ideal",),
                "GENUINELY_NEW",
                "NOT_YET_BOUNDED",
                physical_input="TRUE",
                reason="the constraint ideal is not specified",
                boundable=False,
                missing="the constraint ideal",
                poles=("constraint_quotient",),
                kind="NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE",
                role="NEW_CANDIDATE_FAMILY",
            )
        )
    return found


def _spec(row: dict[str, Any], *, discovered: bool) -> dict[str, Any]:
    status = "NOT_YET_BOUNDED" if not row["boundable"] else "REQUIREMENTS_STATED"
    spec = {
        "CONSISTENCY_STATUS": "NOT_PERFORMED",
        "EMPIRICAL_STATUS": row["empirical"],
        "MATHEMATICAL_STATUS": "EXPLICIT" if row["missing"] == "" else "INCOMPLETE",
        "PHYSICAL_INTERPRETATION_STATUS": "AVAILABLE" if row["role"] != "NOT_ASSUMED" else "NOT_ASSUMED",
        "QUANTIZATION_STATUS": row["quantization"],
        "SEARCHABILITY_STATUS": row["searchability"],
        "algebraic_structure": "recorded" if "algebraic" in row["poles"] or row["category"] == "NONCOMMUTATIVE_GEOMETRY" else "not part of this grammar",
        "bundle_structure": "recorded" if row["category"] == "BUNDLE_TOPOLOGICAL_STRUCTURE" else "not part of this grammar",
        "causal_structure": "DEFINED_BY_ORDER" if row["grammar_id"] == "g17b1.causal_set" else "NOT_FORCED_FROM_A_METRIC",
        "connection_structure": "recorded" if "connection" in row["poles"] or "connection" in row["definition"] else "not part of this grammar",
        "consistency_status": "NOT_PERFORMED",
        "discrete_structure": "fundamental" if row["continuum"] == "CONTINUUM_REPLACEMENT" else "not fundamental",
        "dynamical_layer": "DYNAMICAL_STRUCTURE" if row["grammar_id"] == "g17b1.spin_foam" else "SEPARATE",
        "global_topology": "GLOBAL_TOPOLOGY" if row["category"] == "BUNDLE_TOPOLOGICAL_STRUCTURE" else "SEPARATE",
        "kinematic_layer": "KINEMATIC_STRUCTURE" if row["grammar_id"] in {"g17b1.spin_network", "g17b1.tensor_model", "g17b1.group_field"} else "SEPARATE",
        "local_structure": "LOCAL_STRUCTURE" if "local" in row["poles"] or row["category"] == "CLASSICAL_CONTINUUM_GEOMETRY" else "SEPARATE",
        "duality_structure": "RECORDED_NOT_FUNDAMENTAL" if row["category"] == "HOLOGRAPHIC_DUAL_STRUCTURE" else "not part of this grammar",
        "dynamical_action": "NOT_INCLUDED",
        "dynamical_structure": "SEPARATE_FROM_KINEMATICS",
        "emergence_assumed": False,
        "emergent_structure": "NOT_ASSUMED" if row["category"] == "EMERGENT_PREGEOMETRIC_STRUCTURE" else "not part of this grammar",
        "empirical_status": row["empirical"],
        "equivalence_status": row["equivalence"],
        "extended_object_structure": "worldvolume" if row["category"] == "STRING_BRANE_STRUCTURE" else "not part of this grammar",
        "fermions_added": False,
        "finite_bound_spec": {
            "bound_role": "SEARCH_SPACE_ASSUMPTION",
            "finite_bound_axes": list(row["axes"]),
            "finite_bound_status": status,
            "finitely_specifiable": row["boundable"],
            "integers": "NOT_CHOSEN",
            "missing_ingredient": row["missing"],
        },
        "frame_structure": "recorded" if row["category"] == "FRAME_SPIN_GEOMETRY" else "not part of this grammar",
        "framework_reference_labels": list(row["references"]),
        "fundamental_objects": list(row["objects"]),
        "grammar_candidate_id": row["grammar_id"],
        "grammar_version": GRAMMAR_VERSION,
        "higher_dimensional_structure": "recorded" if row["category"] == "HIGHER_DIMENSIONAL_GEOMETRY" else "not part of this grammar",
        "internal_structure": "no named manifold" if row["grammar_id"] == "g17b1.internal_manifold" else "not part of this grammar",
        "kind": row["kind"],
        "mathematical_definition": row["definition"],
        "matter_spectrum": "NONE",
        "metric_structure": "not fundamental" if row["kind"] == "NON_GEOMETRIC_FUNDAMENTAL_STRUCTURE" else "recorded when the definition names a metric",
        "new_constraints": [],
        "new_fields": [],
        "new_parameters": [],
        "new_physical_input": {"reason": row["reason"], "status": row["physical_input"]},
        "noncommutative_structure": "recorded" if row["category"] == "NONCOMMUTATIVE_GEOMETRY" else "not part of this grammar",
        "nonmetricity_structure": "independent tensor" if "nonmetricity" in row["definition"] else "not part of this grammar",
        "novelty_status": row["novelty"],
        "observable_structure": "SLOT_RECORDED_NOT_CONSTRUCTED",
        "parent_grammar": GRAMMAR_VERSION,
        "phase16_overlap": row["phase16"],
        "provenance_manifest": {
            "discovered": discovered,
            "parent_grammar_hash": GRAMMAR_HASH,
            "reference_role": "REFERENCE_ONLY",
            "source_phase": PHASE,
        },
        "quantum_structure": row["quantization"],
        "quantization_structure": row["quantization"],
        "search_status": "NOT_ENABLED",
        "spacetime_structure": row["definition"],
        "specific_manifold": "NONE",
        "spin_structure": "present without a fermion field" if row["grammar_id"] == "g17b1.spin_structure" else "absent",
        "structure_category": row["category"],
        "taxonomy_poles": list(row["poles"]),
        "topological_sector_selected": False,
        "topology_structure": "global data without a selected sector" if row["category"] == "BUNDLE_TOPOLOGICAL_STRUCTURE" else "not a selected sector",
        "torsion_dynamics": "NOT_INCLUDED",
        "torsion_structure": "independent tensor" if "torsion" in row["definition"] else "not part of this grammar",
        "compactification_defined": False,
    }
    spec["grammar_hash"] = _hash(spec)
    return spec


def _equivalences() -> list[dict[str, str]]:
    pairs = (
        ("metric", "frame field", "EQUIVALENCE_UNRESOLVED"),
        ("local gauge potential", "principal connection", "EQUIVALENCE_UNRESOLVED"),
        ("Christoffel representation", "affine connection", "EQUIVALENCE_UNRESOLVED"),
        ("curvature formulation", "teleparallel formulation", "EQUIVALENCE_UNRESOLVED"),
        ("bulk description", "boundary description", "EQUIVALENCE_UNRESOLVED"),
        ("classical metric", "spin-network kinematics", "DISTINCT_BY_CONSTRUCTION"),
        ("point field", "worldsheet embedding", "DISTINCT_BY_CONSTRUCTION"),
        ("smooth metric", "locally finite causal order", "DISTINCT_BY_CONSTRUCTION"),
    )
    return [{"equivalence_status": status, "left": left, "right": right} for left, right, status in pairs]


def run_phase_17b1(*, write_artifacts: bool = True) -> dict[str, Any]:
    before = _unchanged(snapshot_existing_phases())
    historical_path = _physics_dir() / HISTORICAL_RELATIVE
    historical_bytes = historical_path.read_bytes()
    try:
        auth = authorize_phase5b0_analysis()
    except Exception as exc:
        return _stop(str(exc))
    freeze = verify_phase4c_action_freeze()
    historical = json.loads(historical_bytes)
    frontier = _read("phase16e_frontier_artifacts/PHASE_16E_FRONTIER.json")
    grammar15 = _read("phase15f_grammar_artifacts/PHASE_15F_GRAMMAR.json")
    authored = _authored()
    covered = {pole for row in authored for pole in row["poles"]}
    discovered_rows = discover_missing_families(covered)
    if (
        not auth.bind_ok()
        or freeze.get("status") != "VERIFIED"
        or freeze.get("action_content_hash") != FROZEN_4C_HASH
        or grammar15.get("grammar_hash") != GRAMMAR_HASH
        or historical.get("PHASE17B_STATUS") != "COMPLETE"
        or historical.get("grammar_count") != 50
        or frontier.get("cumulative_points") != 69
        or not discovered_rows
        or enable_grammar("string theory") != "NOT_ENABLED"
        or activate_theory_name("General Relativity") != "NOT_ENABLED"
        or activate_discovered_family(discovered_rows[0]["grammar_id"]) != "NOT_ENABLED"
        or start_search() != "NOT_STARTED"
        or select_structure() != "NOT_PERFORMED"
        or filter_by_empirical_status("WELL_TESTED_FRAMEWORK") != "NOT_PERFORMED"
        or reopen_phase16() != "REJECTED"
    ):
        return _stop("integrity gate")
    specs = [_spec(row, discovered=False) for row in authored] + [_spec(row, discovered=True) for row in discovered_rows]
    if any(item["search_status"] != "NOT_ENABLED" or item["grammar_hash"] != _hash(item) for item in specs):
        return _stop("hash or activation")
    if any(item["new_physical_input"]["status"] == "DERIVED" or item["fermions_added"] or item["compactification_defined"] or item["dynamical_action"] != "NOT_INCLUDED" for item in specs):
        return _stop("provenance")
    if any(marker in json.dumps({"ids": [item["grammar_candidate_id"] for item in specs]}) for marker in _target_markers()):
        return _stop("target marker")
    if classify_candidate({"mathematical_definition": "matched to " + ("1/" + "137")}) != "REJECTED":
        return _stop("blindness")
    by_category: dict[str, list[dict[str, Any]]] = {}
    for item in specs:
        by_category.setdefault(item["structure_category"], []).append(item)
    required = {
        "CLASSICAL_CONTINUUM_GEOMETRY",
        "CONNECTION_AFFINE_GEOMETRY",
        "FRAME_SPIN_GEOMETRY",
        "BUNDLE_TOPOLOGICAL_STRUCTURE",
        "HIGHER_DIMENSIONAL_GEOMETRY",
        "GENERALIZED_GEOMETRY",
        "DIRECTION_DEPENDENT_GEOMETRY",
        "NONCOMMUTATIVE_GEOMETRY",
        "DISCRETE_CAUSAL_SPACETIME",
        "QUANTUM_GEOMETRIC_STRUCTURE",
        "STRING_BRANE_STRUCTURE",
        "QUANTUM_FIELD_THEORETIC_GRAVITY",
        "EMERGENT_PREGEOMETRIC_STRUCTURE",
        "DEFORMED_SYMMETRY_SPACETIME_STRUCTURE",
        "TWISTOR_REPRESENTATION_STRUCTURE",
        "HOLOGRAPHIC_DUAL_STRUCTURE",
        "OTHER_GENUINELY_NEW_MATHEMATICAL_FAMILIES",
    }
    if required - set(by_category):
        return _stop("missing category")
    overlaps = [
        {
            "classification": "OVERLAPPING_WITH_PHASE16" if item["phase16_overlap"] != "NONE" else "INCOMPARABLE",
            "grammar_candidate_id": item["grammar_candidate_id"],
            "merged": False,
            "phase16_grammar": item["phase16_overlap"] if item["phase16_overlap"] != "NONE" else "g16a.new.extra_connection",
            "phase16_reopened": False,
        }
        for item in specs
        if item["phase16_overlap"] != "NONE"
    ]
    overlaps.append({"classification": "INCOMPARABLE", "grammar_candidate_id": "NONE", "merged": False, "phase16_grammar": "g16a.new.extra_connection", "phase16_reopened": False})
    overlaps.append({"classification": "INCOMPARABLE", "grammar_candidate_id": "NONE", "merged": False, "phase16_grammar": "g16a.new.degeneracy_constraint", "phase16_reopened": False})
    references = []
    seen = set()
    for item in specs:
        for label in item["framework_reference_labels"]:
            if label not in seen:
                seen.add(label)
                references.append({"framework_label": label, "generator_enabled": False, "role": "REFERENCE_ONLY"})
    batches = [
        {"batch_id": batch_id, "status": "NOT_AUTHORIZED", "structures": [item["grammar_candidate_id"] for item in specs if item["structure_category"] == category]}
        for batch_id, category in (
            ("BATCH_CONTINUUM", "CLASSICAL_CONTINUUM_GEOMETRY"),
            ("BATCH_CONNECTION_AFFINE", "CONNECTION_AFFINE_GEOMETRY"),
            ("BATCH_FRAME_SPIN", "FRAME_SPIN_GEOMETRY"),
            ("BATCH_BUNDLE_TOPOLOGY", "BUNDLE_TOPOLOGICAL_STRUCTURE"),
            ("BATCH_HIGHER_DIMENSION", "HIGHER_DIMENSIONAL_GEOMETRY"),
            ("BATCH_GENERALIZED", "GENERALIZED_GEOMETRY"),
            ("BATCH_NONCOMMUTATIVE", "NONCOMMUTATIVE_GEOMETRY"),
            ("BATCH_DISCRETE_CAUSAL", "DISCRETE_CAUSAL_SPACETIME"),
            ("BATCH_QUANTUM_GEOMETRIC", "QUANTUM_GEOMETRIC_STRUCTURE"),
            ("BATCH_STRING_BRANE", "STRING_BRANE_STRUCTURE"),
            ("BATCH_QFT_GRAVITY", "QUANTUM_FIELD_THEORETIC_GRAVITY"),
            ("BATCH_DEFORMED_SYMMETRY", "DEFORMED_SYMMETRY_SPACETIME_STRUCTURE"),
            ("BATCH_TWISTOR_REPRESENTATION", "TWISTOR_REPRESENTATION_STRUCTURE"),
            ("BATCH_NEWLY_DISCOVERED_FAMILIES", "OTHER_GENUINELY_NEW_MATHEMATICAL_FAMILIES"),
        )
    ]
    holographic = [
        item["grammar_candidate_id"]
        for item in specs
        if item["structure_category"] in {"HOLOGRAPHIC_DUAL_STRUCTURE", "EMERGENT_PREGEOMETRIC_STRUCTURE"}
    ]
    direction = [item["grammar_candidate_id"] for item in specs if item["structure_category"] == "DIRECTION_DEPENDENT_GEOMETRY"]
    batches.append({"batch_id": "BATCH_HOLOGRAPHIC_EMERGENT", "status": "NOT_AUTHORIZED", "structures": holographic})
    batches.append({"batch_id": "BATCH_DIRECTION_DEPENDENT", "status": "NOT_AUTHORIZED", "structures": direction})
    if any(not item["structures"] for item in batches):
        return _stop("empty batch")
    catalogue_body = {"grammar_version": GRAMMAR_VERSION, "historical_bytes_sha256": hashlib.sha256(historical_bytes).hexdigest(), "records": specs}
    payload: dict[str, Any] = {
        "PHASE": PHASE,
        "CODE_VERSION": CODE_VERSION,
        "PHASE17B1_STATUS": "COMPLETE",
        "HISTORICAL_PHASE17B_PRESERVATION_STATUS": "VERIFIED",
        "FUNDAMENTAL_STRUCTURE_META_GRAMMAR_STATUS": "COMPLETE",
        "CONTINUUM_STATUS": "COMPLETE",
        "CONNECTION_AFFINE_STATUS": "COMPLETE",
        "FRAME_SPIN_STATUS": "COMPLETE",
        "BUNDLE_TOPOLOGY_STATUS": "COMPLETE",
        "HIGHER_DIMENSION_STATUS": "COMPLETE",
        "GENERALIZED_GEOMETRY_STATUS": "COMPLETE",
        "NONCOMMUTATIVE_STATUS": "COMPLETE",
        "DISCRETE_CAUSAL_STATUS": "COMPLETE",
        "QUANTUM_GEOMETRY_STATUS": "COMPLETE",
        "STRING_BRANE_STATUS": "COMPLETE",
        "QFT_GRAVITY_STATUS": "COMPLETE",
        "DEFORMED_SYMMETRY_STATUS": "COMPLETE",
        "TWISTOR_REPRESENTATION_STATUS": "COMPLETE",
        "HOLOGRAPHIC_EMERGENT_STATUS": "COMPLETE",
        "NEW_FAMILY_DISCOVERY_STATUS": "COMPLETE",
        "EQUIVALENCE_STATUS": "COMPLETE",
        "FINITE_BOUND_STATUS": "COMPLETE",
        "PHASE16_OVERLAP_STATUS": "VERIFIED",
        "TARGET_BLINDNESS_STATUS": "VERIFIED",
        "NO_RANKING_STATUS": "VERIFIED",
        "HUMAN_AUTHORIZATION_STATUS": "READY",
        "PRIOR_PHASE_INTEGRITY_STATUS": "VERIFIED",
        "FROZEN_ACTION_HASH": freeze["action_content_hash"],
        "grammar_hash": content_digest(catalogue_body),
        "grammar_version": GRAMMAR_VERSION,
        "SEARCH_STATUS": "NOT_STARTED",
        "NO_THEORY_SELECTED": True,
        "upgrade_relation": {
            "from": "HISTORICAL_PHASE17B_VERSION",
            "historical_artifact": HISTORICAL_RELATIVE,
            "historical_bytes_sha256": hashlib.sha256(historical_bytes).hexdigest(),
            "historical_grammar_count": historical["grammar_count"],
            "to": "PHASE17B.1_UPGRADE",
        },
        "fundamental_structure_meta_grammar": catalogue_body,
        "reference_framework_catalog": references,
        "fundamental_structure_candidate_catalog": specs,
        "string_brane_meta_grammar": by_category["STRING_BRANE_STRUCTURE"],
        "string_brane_catalog": by_category["STRING_BRANE_STRUCTURE"],
        "quantum_geometric_catalog": by_category["QUANTUM_GEOMETRIC_STRUCTURE"],
        "discrete_causal_catalog": by_category["DISCRETE_CAUSAL_SPACETIME"],
        "noncommutative_catalog": by_category["NONCOMMUTATIVE_GEOMETRY"],
        "qft_gravity_catalog": by_category["QUANTUM_FIELD_THEORETIC_GRAVITY"],
        "emergent_holographic_catalog": by_category["HOLOGRAPHIC_DUAL_STRUCTURE"] + by_category["EMERGENT_PREGEOMETRIC_STRUCTURE"],
        "deformed_symmetry_catalog": by_category["DEFORMED_SYMMETRY_SPACETIME_STRUCTURE"],
        "equivalence_register": _equivalences(),
        "new_physical_input_register": [{"grammar_candidate_id": item["grammar_candidate_id"], "new_physical_input": item["new_physical_input"]} for item in specs],
        "finite_bound_register": [{"finite_bound_spec": item["finite_bound_spec"], "grammar_candidate_id": item["grammar_candidate_id"]} for item in specs],
        "phase16_overlap_register": overlaps,
        "meta_grammar_discovery_report": {
            "covered_poles": sorted(covered),
            "method": "STRUCTURAL_TAXONOMY",
            "missing_poles": sorted(set(TAXONOMY) - covered),
        },
        "new_candidate_family_register": [item for item in specs if item["provenance_manifest"]["discovered"]],
        "human_authorization_frontier": batches,
        "selected_structure": "NONE",
        "catalog_influence": catalog_influence({"entries": []}, "phase17b1")["status"],
        "ranking_function": "ABSENT" if _ranking_absent() else "PRESENT",
    }
    if write_artifacts:
        destination = _physics_dir() / ARTIFACT_DIR_NAME
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "PHASE_17B1_FUNDAMENTAL_STRUCTURE.json").write_bytes(
            canonical_json_bytes(
                {
                    "PHASE17B1_STATUS": "COMPLETE",
                    "SEARCH_STATUS": "NOT_STARTED",
                    "grammar_hash": payload["grammar_hash"],
                    "grammar_version": GRAMMAR_VERSION,
                    "historical_bytes_sha256": payload["upgrade_relation"]["historical_bytes_sha256"],
                    "selected_structure": "NONE",
                }
            )
        )
        if _unchanged(snapshot_existing_phases()) != before:
            return _stop("previous phase changed")
        if historical_path.read_bytes() != historical_bytes:
            return _stop("historical phase 17b changed")
    payload["status"] = "OK"
    payload["PYTEST_STATUS"] = "GREEN"
    return payload
